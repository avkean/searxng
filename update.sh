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

# Searches depend on outside engines. If they already fail on the running
# images, the new ones can't be blamed, so only the local checks decide.
if ! docker exec -i searxng /usr/local/searxng/.venv/bin/python - < "$app_dir/check-search-quality.py"; then
  printf '%s\n' 'Searches already fail before the update; judging it on the local checks only' >&2
  export SKIP_SEARCH=1
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
# settings.yml and the other mounted files are replaced by git pull, and a
# running container keeps the old copy, so SearXNG is always recreated
if ! "${compose[@]}" up -d --wait --wait-timeout 180 --force-recreate --no-deps searxng ||
  ! "${compose[@]}" up -d --wait --wait-timeout 180; then
  rollback
  exit 1
fi

changed=false
for index in "${!containers[@]}"; do
  if [ "$(docker inspect -f '{{.Image}}' "${containers[$index]}")" != "$(docker image inspect -f '{{.Id}}' "searxng-rollback:${containers[$index]}")" ]; then
    changed=true
  fi
done

update_ok=true
if [ "${SEARXNG_UPDATE_FORCE_SMOKE_FAILURE:-0}" = 1 ]; then
  update_ok=false
elif ! "$app_dir/smoke-test.sh"; then
  update_ok=false
fi

if [ "$update_ok" = false ]; then
  if [ "$changed" = false ] && [ "${SEARXNG_UPDATE_FORCE_SMOKE_FAILURE:-0}" != 1 ]; then
    printf '%s\n' 'SearXNG smoke test failed, but the images are unchanged, so there is nothing to roll back' >&2
    exit 1
  fi
  rollback
  exit 1
fi

for container in "${containers[@]}"; do
  docker image rm "searxng-rollback:$container" >/dev/null 2>&1 || true
done
docker image prune -f --filter label=com.docker.compose.project=searxng >/dev/null

printf '%s\n' 'SearXNG update completed and passed verification'
