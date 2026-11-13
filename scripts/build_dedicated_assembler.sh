#!/bin/sh
# Only build the exact clean, published, branch-specific fork source.
set -eu
tag=${1:?set output tag}
cd "$(dirname "$0")/.."
repo=$(git remote get-url origin)
case "$repo" in
 https://github.com/ottojung/MiCall|https://github.com/ottojung/MiCall.git|git@github.com:ottojung/MiCall.git) ;;
 *) echo wrong-repository >&2; exit 1 ;;
esac
test -z "$(git status --porcelain)" || { echo dirty-source >&2; exit 1; }
name=$(cat assembler-bench/selected)
branch=$(git symbolic-ref --short HEAD)
test "$branch" = "bench/assembler-$name-v2" || { echo wrong-branch >&2; exit 1; }
sha=$(git rev-parse HEAD)
baseline=$(cat assembler-bench/baseline-commit)
test "${#sha}" -eq 40
test "${#baseline}" -eq 40
git merge-base --is-ancestor "$baseline" HEAD
test "$(git rev-parse "$baseline:micall")" = "$(git rev-parse HEAD:micall)" || { echo downstream-changed >&2; exit 1; }
remote_sha=$(git ls-remote --heads origin "refs/heads/$branch" | awk '{print $1}')
test "$remote_sha" = "$sha" || { echo branch-not-published >&2; exit 1; }
base=${FORK_BASE_IMAGE:?supply exact fork-built common MiCall image ID}
base_id=$(podman image inspect --format '{{.Id}}' "$base")
test "$base" = "$base_id" || { echo mutable-base-reference >&2; exit 1; }
base_repo=$(podman image inspect --format '{{index .Config.Labels "org.opencontainers.image.source"}}' "$base")
base_sha=$(podman image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$base")
test "$base_repo" = "https://github.com/ottojung/MiCall"
test "$base_sha" = "$baseline" || { echo wrong-common-base >&2; exit 1; }
set -- --pull=never --network=host --build-arg "FORK_BASE_IMAGE=$base_id" --build-arg "MICALL_FORK_SOURCE_COMMIT=$sha" --build-arg "MICALL_FORK_BASE_COMMIT=$baseline"
if [ "$name" = ivanka ];then
 donor=${IVANKA_IMAGE:?native Rust ELF donor needed}
 donor_id=$(podman image inspect --format '{{.Id}}' "$donor")
 donor_sha=$(podman image inspect --format '{{index .Config.Labels "org.ottojung.ivanka.source-commit"}}' "$donor")
 donor_kind=$(podman image inspect --format '{{index .Config.Labels "org.ottojung.ivanka.execution"}}' "$donor")
 test "${#donor_sha}" -eq 40
 case "$donor_kind" in rust-direct-*) ;; *) echo unverified-rust-donor >&2; exit 1 ;; esac
 set -- "$@" --build-arg "IVANKA_IMAGE=$donor_id" --build-arg "IVANKA_SOURCE_COMMIT=$donor_sha"
fi
podman build "$@" -f Dockerfile.assembler-bench -t "$tag" .
image_id=$(podman image inspect --format '{{.Id}}' "$tag")
for pair in "org.opencontainers.image.source|https://github.com/ottojung/MiCall" "org.opencontainers.image.revision|$sha" "org.ottojung.micall.common-base|$base_id" "org.ottojung.micall.common-baseline-commit|$baseline" "org.ottojung.micall.source-branch|$branch" "org.ottojung.micall.assembler|$name";do
 key=${pair%%|*}
 expected=${pair#*|}
 actual=$(podman image inspect --format "{{index .Config.Labels \"$key\"}}" "$tag")
 test "$actual" = "$expected" || { echo "image-label-mismatch $key" >&2; exit 1; }
done
echo "DEDICATED_IMAGE_VERIFIED assembler=$name branch=$branch commit=$sha image=$image_id baseline=$baseline"
