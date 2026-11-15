#!/bin/sh
set -eu
tag=${1:?provide immutable unique tag}
cd "$(dirname "$0")/.."
case "$(git remote get-url origin)" in
  https://github.com/ottojung/MiCall|https://github.com/ottojung/MiCall.git|git@github.com:ottojung/MiCall.git) ;;
  *) echo "requires canonical MiCall fork" >&2; exit 1 ;;
esac
test "$(git symbolic-ref --short HEAD)" = experiment/reject-unphased-long-overlap-20261115
test -z "$(git status --porcelain)"
source_sha=$(git rev-parse HEAD)
test "$(git ls-remote --heads origin refs/heads/experiment/reject-unphased-long-overlap-20261115 |cut -f1)" = "$source_sha"
base=${FORK_BASE_IMAGE:?frozen unmodified fork image ID required}
donor=${IVANKA_IMAGE:?frozen Rust tool donor ID required}
test "$(podman image inspect --format '{{.Id}}' "$base")" = "$base"
test "$(podman image inspect --format '{{.Id}}' "$donor")" = "$donor"
test "$(podman image inspect --format '{{index .Config.Labels "org.opencontainers.image.source"}}' "$base")" = https://github.com/ottojung/MiCall
native_sha=$(podman image inspect --format '{{index .Config.Labels "org.ottojung.ivanka.source-commit"}}' "$donor")
test "${#native_sha}" -eq 40
podman build --pull=never --network=host   --build-arg "FORK_BASE_IMAGE=$base"   --build-arg "IVANKA_IMAGE=$donor"   --build-arg "MICALL_FORK_SOURCE_COMMIT=$source_sha"   --build-arg "IVANKA_SOURCE_COMMIT=$native_sha"   -f Dockerfile.experimental-unphased-stitch -t "$tag" .
id=$(podman image inspect --format '{{.Id}}' "$tag")
test "$(podman image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$id")" = "$source_sha"
test "$(podman image inspect --format '{{index .Config.Labels "org.ottojung.ivanka.source-commit"}}' "$id")" = "$native_sha"
echo "SOURCE_PINNED_EXPERIMENTAL_NOT_QUALIFIED image=$id fork=$source_sha rust=$native_sha base=$base"
