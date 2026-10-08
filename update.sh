#!/usr/bin/env bash
set -euo pipefail

app_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
compose=(docker compose -f "$app_dir/compose.yml")

# Anubis is pinned by digest, so an update never changes it.
containers=(searxng searxng-valkey)

exec 9>/tmp/searxng-update.lock
if ! flock -n 9; then
  printf '%s\n' 'Another SearXNG update is already running'
  exit 0
fi

# Docker deletes an untagged image as soon as nothing uses it, so keep the
# running images under a rollback tag until the new ones pass.
image_refs=()
for container in "${containers[@]}"; do
  image_refs+=("$(docker inspect -f '{{.Config.Image}}' "$container")")
  docker image tag "$(docker inspect -f '{{.Image}}' "$container")" "searxng-rollback:$container"
done

rollback() {
  local index
  printf '%s\n' 'SearXNG update failed verification; restoring previous images' >&2
  for index in "${!containers[@]}"; do
    docker image tag "searxng-rollback:${containers[$index]}" "${image_refs[$index]}"
  done
  "${compose[@]}" up -d --force-recreate --pull never --wait --wait-timeout 180
  env -u SEARXNG_UPDATE_FORCE_SMOKE_FAILURE "$app_dir/smoke-test.sh"
}

"${compose[@]}" pull --ignore-buildable
"${compose[@]}" build --pull
if ! "${compose[@]}" up -d --wait --wait-timeout 180; then
  rollback
  exit 1
fi

update_ok=true
if [ "${SEARXNG_UPDATE_FORCE_SMOKE_FAILURE:-0}" = 1 ]; then
  update_ok=false
elif ! "$app_dir/smoke-test.sh"; then
  update_ok=false
fi

if [ "$update_ok" = false ]; then
  rollback
  exit 1
fi

for container in "${containers[@]}"; do
  docker image rm "searxng-rollback:$container" >/dev/null 2>&1 || true
done

printf '%s\n' 'SearXNG update completed and passed verification'
