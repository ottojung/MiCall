#!/bin/sh
# Reproduce the common MiCall runtime from a clean, exact ottojung fork commit.
set -eu
target=${1:?output OCI tag required}
cd "$(dirname "$0")/.."
repo=$(git remote get-url origin)
case "$repo" in
  https://github.com/ottojung/MiCall|https://github.com/ottojung/MiCall.git|git@github.com:ottojung/MiCall.git) ;;
  *) echo "refusing non-fork MiCall source" >&2; exit 1 ;;
esac
test -z "$(git status --porcelain)" || {
  echo "refusing dirty fork tree" >&2; exit 1;
}
sha=$(git rev-parse HEAD)
test "${#sha}" -eq 40
podman build --network=host --pull=never \
  --build-arg MICALL_FORK_SOURCE_COMMIT="$sha" \
  --target production -f Dockerfile -t "$target" .
revision=$(podman image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$target")
source=$(podman image inspect --format '{{index .Config.Labels "org.opencontainers.image.source"}}' "$target")
test "$revision" = "$sha"
test "$source" = "https://github.com/ottojung/MiCall"
podman image inspect --format '{{.Id}} {{index .Config.Labels "org.opencontainers.image.revision"}}' "$target"
