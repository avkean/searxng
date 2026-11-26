#!/usr/bin/env bash
set -euo pipefail

app_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
compose=(docker compose -f "$app_dir/compose.yml")

"${compose[@]}" config --quiet

for container in searxng searxng-valkey searxng-anubis; do
  test "$(docker inspect -f '{{.State.Running}}' "$container")" = true
  test -z "$(docker port "$container")"
done

for container in searxng searxng-valkey; do
  test "$(docker inspect -f '{{.State.Health.Status}}' "$container")" = healthy
done

test "$(docker exec searxng-valkey valkey-cli -n 0 ping)" = PONG
test "$(docker exec searxng-valkey valkey-cli -n 1 ping)" = PONG

docker exec searxng python -c \
  "import urllib.request; body=urllib.request.urlopen('http://127.0.0.1:8080/', timeout=10).read(); assert b'AVKEAN Search' in body"

# the theme hooks in the Dockerfile rely on lines in SearXNG's base.html
docker exec searxng python -c \
  "import urllib.request; body=urllib.request.urlopen('http://127.0.0.1:8080/', timeout=10).read(); assert b'/avkean.css' in body, 'avkean.css is not linked'; assert b'/avkean.js' in body, 'avkean.js is not linked'; css=urllib.request.urlopen('http://127.0.0.1:8080/static/themes/simple/avkean.css', timeout=10).read(); assert b'avkean search' in css; js=urllib.request.urlopen('http://127.0.0.1:8080/static/themes/simple/avkean.js', timeout=10).read(); assert b'avk-sub' in js"

# settings.yml replaces SearXNG's plugin list, so check the defaults are still on
docker exec searxng /usr/local/searxng/.venv/bin/python -c \
  "from searx import settings; p={k.split('.')[2]: v['active'] for k, v in settings['plugins'].items()}; assert all(p.get(x) for x in ('calculator', 'unit_converter', 'tracker_url_remover', 'hostnames', 'infinite_scroll')), p"

# update.sh skips these when outside engines already fail on the running
# images. Outside engines turn away the odd request, so a failure gets a
# second try.
search_check() {
  docker exec -i searxng /usr/local/searxng/.venv/bin/python - < "$app_dir/check-search-quality.py"
}
if [ "${SKIP_SEARCH:-0}" != 1 ]; then
  search_check || { sleep 30; search_check; }
fi

anubis_ip=$(docker inspect -f '{{(index .NetworkSettings.Networks "proxy_net").IPAddress}}' searxng-anubis)
browser_response=$(curl -fsS -i --max-time 15 -H 'X-Real-IP: 203.0.113.10' -A 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' "http://$anubis_ip:8080/")
grep -qi 'anubis' <<<"$browser_response"

denied_status=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 15 -H 'X-Real-IP: 203.0.113.10' -A 'curl/8.0' "http://$anubis_ip:8080/search?q=test")
test "$denied_status" = 403

if [ "${SKIP_PUBLIC:-0}" != 1 ]; then
  public_body=$(curl -fsS --max-time 20 https://searxng.avkean.com/healthz)
  grep -q 'AVKEAN Search' <<<"$public_body"
fi

printf '%s\n' 'SearXNG smoke test passed'
