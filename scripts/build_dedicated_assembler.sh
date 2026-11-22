#!/bin/sh
# Build exactly one clean, published, branch-specific exploratory fork source.
# The tool binary SHA must come from independent attestation; nothing is inferred here.
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
test "$name" = "fermi-lite" || { echo wrong-tool >&2; exit 1; }
branch=$(git symbolic-ref --short HEAD)
test "$branch" = "bench/assembler-$name" || { echo wrong-branch >&2; exit 1; }
sha=$(git rev-parse HEAD)
baseline=$(cat assembler-bench/baseline-commit)
test "${#sha}" -eq 40
test "${#baseline}" -eq 40
git merge-base --is-ancestor "$baseline" HEAD
# Clinical source is frozen, but adapter-specific modules/tests MUST differ
# from baseline. Fail closed on every non-allowlisted file change instead.
for path in $(git diff --name-only "$baseline" HEAD); do
  case "$path" in
    Dockerfile.assembler-bench|assembler-bench/README.md|assembler-bench/baseline-commit|assembler-bench/selected|docs/assembler-bench-integrations.md|micall/core/assembler_commands.py|micall/core/assembler_dispatch.py|micall/tests/test_assembler_integrations.py|scripts/build_dedicated_assembler.sh) ;;
    *) echo "downstream-changed: $path" >&2; exit 1 ;;
  esac
done
remote_sha=$(git ls-remote --heads origin "refs/heads/$branch" | awk '{print $1}')
test "$remote_sha" = "$sha" || { echo branch-not-published >&2; exit 1; }
base=${FORK_BASE_IMAGE:?supply exact fork-built common MiCall image ID}
base_id=$(podman image inspect --format '{{.Id}}' "$base")
test "$base" = "$base_id" || { echo mutable-base-reference >&2; exit 1; }
base_repo=$(podman image inspect --format '{{index .Config.Labels "org.opencontainers.image.source"}}' "$base")
base_sha=$(podman image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$base")
test "$base_repo" = "https://github.com/ottojung/MiCall"
test "$base_sha" = "$baseline" || { echo wrong-common-base >&2; exit 1; }
tool_sha=${TOOL_SOURCE_COMMIT:-85f159e5a2e15a4c4fb41cdfce91ba0c9b68d2e1}
test "$tool_sha" = "85f159e5a2e15a4c4fb41cdfce91ba0c9b68d2e1" || { echo wrong-tool-source >&2; exit 1; }
license_sha=e8051edd873472ad73df648dc7bf74d917d90057ae46bf6f3b021c4fff8069e8
commands_sha=$(sha256sum micall/core/assembler_commands.py | cut -d' ' -f1)
dispatch_sha=$(sha256sum micall/core/assembler_dispatch.py | cut -d' ' -f1)
tool_bin_sha=${TOOL_BINARY_SHA256:?supply independently attested tool binary SHA256}
test "${#tool_bin_sha}" -eq 64
set -- --pull=never --network=host \
  --build-arg "FORK_BASE_IMAGE=$base_id" \
  --build-arg "MICALL_FORK_SOURCE_COMMIT=$sha" \
  --build-arg "MICALL_FORK_BASE_COMMIT=$baseline" \
  --build-arg "TOOL_SOURCE_REPO=https://github.com/lh3/fermi-lite" \
  --build-arg "TOOL_SOURCE_COMMIT=$tool_sha" \
  --build-arg "TOOL_LICENSE_SHA256=$license_sha" \
  --build-arg "MICALL_ADAPTER_COMMANDS_SHA256=$commands_sha" \
  --build-arg "MICALL_ADAPTER_DISPATCH_SHA256=$dispatch_sha" \
  --build-arg "TOOL_BINARY_SHA256=$tool_bin_sha"
podman build "$@" -f Dockerfile.assembler-bench -t "$tag" .
image_id=$(podman image inspect --format '{{.Id}}' "$tag")
for pair in \
  "org.opencontainers.image.source|https://github.com/ottojung/MiCall" \
  "org.opencontainers.image.revision|$sha" \
  "org.ottojung.micall.common-base|$base_id" \
  "org.ottojung.micall.common-baseline-commit|$baseline" \
  "org.ottojung.micall.source-branch|$branch" \
  "org.ottojung.micall.assembler|$name" \
  "org.ottojung.exploratory.tool-source-commit|$tool_sha" \
  "org.ottojung.exploratory.tool-binary-sha256|$tool_bin_sha" \
  "org.ottojung.exploratory.tool-license|MIT" \
  "org.ottojung.exploratory.tool-license-sha256|$license_sha" \
  "org.ottojung.exploratory.nonqualifying|true" \
  "org.ottojung.micall.adapter-commands-sha256|$commands_sha" \
  "org.ottojung.micall.adapter-dispatch-sha256|$dispatch_sha";do
 key=${pair%%|*}
 expected=${pair#*|}
 actual=$(podman image inspect --format "{{index .Config.Labels \"$key\"}}" "$tag")
 test "$actual" = "$expected" || { echo "image-label-mismatch $key" >&2; exit 1; }
done
echo "DEDICATED_IMAGE_VERIFIED assembler=$name branch=$branch commit=$sha image=$image_id baseline=$baseline"
