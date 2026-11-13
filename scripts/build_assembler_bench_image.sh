#!/bin/sh
# Build images only from a clean exact revision of the writable MiCall fork.
set -eu
assembler=${1:?assembler name required}
target=${2:?output OCI tag required}
base=${FORK_BASE_IMAGE:?set exact fork-built base image identifier}
ivanka=${IVANKA_IMAGE:?set the pinned Ivanka ELF source image identifier}
case "$assembler" in
  iva|ivanka|haploflow|megahit|abyss|spades|velvet) ;;
  *) echo "unsupported assembler" >&2; exit 1 ;;
esac
cd "$(dirname "$0")/.."
source_repo=$(git remote get-url origin)
case "$source_repo" in
  https://github.com/ottojung/MiCall|https://github.com/ottojung/MiCall.git|git@github.com:ottojung/MiCall.git) ;;
  *) echo "MiCall source must be the ottojung fork, never upstream" >&2; exit 1 ;;
esac
test -z "$(git status --porcelain)" || {
  echo "refusing dirty fork tree" >&2; exit 1;
}
sha=$(git rev-parse HEAD)
test "${#sha}" -eq 40
storage_command=podman
actual_base=$($storage_command image inspect --format '{{.Id}}' "$base")
base_source=$($storage_command image inspect --format '{{index .Config.Labels "org.opencontainers.image.source"}}' "$base")
base_commit=$($storage_command image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$base")
test "$base_source" = "https://github.com/ottojung/MiCall" || {
  echo "refusing non-fork MiCall base" >&2; exit 1;
}
test "$base_commit" = "$sha" || {
  echo "refusing different fork base commit" >&2; exit 1;
}
tool_image=$($storage_command image inspect --format '{{.Id}}' "$ivanka")
tool_commit=$($storage_command image inspect --format '{{index .Config.Labels "org.ottojung.ivanka.source-commit"}}' "$ivanka")
tool_execution=$($storage_command image inspect --format '{{index .Config.Labels "org.ottojung.ivanka.execution"}}' "$ivanka")
test "${#tool_commit}" -eq 40 || {
  echo "Ivanka ELF donor lacks exact source commit" >&2; exit 1;
}
case "$tool_execution" in
  rust-direct-*) ;;
  *) echo "refusing Ivanka donor without verified direct Rust execution" >&2; exit 1 ;;
esac
"$storage_command" build --pull=never --network=host \
  --build-arg FORK_BASE_IMAGE="$actual_base" \
  --build-arg IVANKA_IMAGE="$tool_image" \
  --build-arg IVANKA_SOURCE_COMMIT="$tool_commit" \
  --build-arg MICALL_FORK_SOURCE_COMMIT="$sha" \
  --build-arg MICALL_DENOVO_ASSEMBLER="$assembler" \
  -f Dockerfile.assembler-bench -t "$target" .
"$storage_command" image inspect --format '{{.Id}} {{index .Config.Labels "org.opencontainers.image.revision"}}' "$target"
