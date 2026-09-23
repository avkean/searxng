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

docker exec -i searxng /usr/local/searxng/.venv/bin/python - < "$app_dir/check-google-adapter.py"

docker exec searxng python -c \
  "import urllib.request; body=urllib.request.urlopen('http://127.0.0.1:8080/', timeout=10).read(); assert b'AVKEAN Search' in body"

docker exec -i searxng /usr/local/searxng/.venv/bin/python - < "$app_dir/check-search-quality.py"

if docker exec searxng /usr/local/searxng/.venv/bin/python -c \
  "import sys,urllib.parse,urllib.request; from lxml import html; body=urllib.request.urlopen('http://127.0.0.1:8080/search?'+urllib.parse.urlencode({'q':'searxng documentation','engines':'google','language':'all'}), timeout=30).read(); dom=html.fromstring(body); results=dom.xpath('//article[contains(@class,\"result\")]'); messages=' '.join(dom.xpath('//*[@id=\"engines_msg\"]//text()')); sys.exit(0 if len(results) >= 5 else 75 if any(reason in messages for reason in ('CAPTCHA','Too many requests','Access denied')) else 1)"; then
  :
elif test "$?" -eq 75; then
  printf '%s\n' 'Google temporarily blocked its smoke-test query; continuing because the application search passed' >&2
else
  printf '%s\n' 'Google smoke-test query failed without a recognized temporary upstream block' >&2
  exit 1
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
