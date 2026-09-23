#!/usr/bin/env bash
set -euo pipefail

app_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
compose=(docker compose -f "$app_dir/compose.yml")
containers=(searxng searxng-valkey searxng-anubis)

exec 9>/tmp/searxng-update.lock
if ! flock -n 9; then
  printf '%s\n' 'Another SearXNG update is already running'
  exit 0
fi

old_image_ids=()
image_refs=()
for container in "${containers[@]}"; do
  old_image_ids+=("$(docker inspect -f '{{.Image}}' "$container")")
  image_refs+=("$(docker inspect -f '{{.Config.Image}}' "$container")")
done

rollback() {
  local candidate_image_id index
  local -a failed_image_ids=()
  printf '%s\n' 'SearXNG update failed verification; restoring previous images' >&2
  for index in "${!containers[@]}"; do
    candidate_image_id=$(docker image inspect -f '{{.Id}}' "${image_refs[$index]}")
    if [ "$candidate_image_id" != "${old_image_ids[$index]}" ]; then
      failed_image_ids+=("$candidate_image_id")
    fi
    docker image tag "${old_image_ids[$index]}" "${image_refs[$index]}"
  done
  "${compose[@]}" up -d --force-recreate --pull never --wait --wait-timeout 180
  env -u SEARXNG_UPDATE_FORCE_SMOKE_FAILURE "$app_dir/smoke-test.sh"
  if [ "${#failed_image_ids[@]}" -gt 0 ]; then
    docker image rm "${failed_image_ids[@]}" >/dev/null 2>&1 || true
  fi
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

docker image rm "${old_image_ids[@]}" >/dev/null 2>&1 || true

printf '%s\n' 'SearXNG update completed and passed verification'
