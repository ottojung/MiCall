#!/bin/sh
# Guarded, low-footprint SAVAGE donor + adapter image build.
# No build/container is permitted until the named coordinator grant and all
# PX guards are satisfied. This script never changes a guard, registry, STOP,
# frozen image or coordinator state; it only builds/attests its own artifacts.
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

# Required host-local inputs; no private paths are embedded in this repo file.
: "${PX_PODMAN_STORE:?set to the bound podman graphroot}"
: "${PX_BUILD_CONTEXT:?set to the isolated verified donor build context}"
: "${PX_ADAPTER_CHECKOUT:?set to the pinned frozen SAVAGE adapter checkout}"
: "${PX_RECEIPT_PATH:?set to a host-local receipt output path}"
: "${PX_STOP_FILE:?set to the live PX STOP path}"
: "${PX_GLOBAL_LOCK:?set to the live PX global worker lock path}"
: "${PX_NAMED_GRANT:?set to the exact named slot grant}"
: "${PX_P1_REMAP_CLEAR:?set to yes only after coordinator confirms P1/remap priority}"

EXPECTED_GRANT='savage-lowspace-UNZbwJhfujc2BbDNDtWgYq-practices-V9ro-lOL3'
EXPECTED_ADAPTER='0919ffa97f609b6f0b650ce834f0fc79822f18e5'
BASE_IMAGE='sha256:da795bbdbfbdd3c735c59d0ee008dae1781c68268b24298235e6b2cfe50a23ad'
PY27_SHA='da3080e3b488f648a3d7a4560ddee895284c3380b11d6de75edb986526b9a814'
HAPLO_ARCHIVE_SHA='09cad6b864206300caaa543d7df1aab6ac80ba63c80ff66d99bfdba67b87f19e'
HAPLO_MANIFEST_SHA='f1a05a2c077624736118e0d16b2d9514e1ee24f1b02086a6a021ecbb595859ef'
HAPLO_PROVENANCE_SHA='5be07d4848307eb0613380cfc27f342fed8292e3e3ac8c4733f71d4a830f410f'
VQ_DONOR_SHA='199d97b7330df213f0adf99aaebb8f74d59806dfe90379f15dea28f0aa0c6590'
QC_SOURCE_MANIFEST_SHA='ec45769285aaafe1068fc7ac164777343c11a508b1dae34b15aac2d83ed08876'

RESERVE_KB=$((32 * 1024 * 1024))
# Conservative new-disk budget: Python layer ~70MB, donor/source layer ~30MB,
# final adapter layer ~50MB, build transient ~350MB, podman metadata margin.
NEEDED_KB=$((2 * 1024 * 1024))
S1_TAG='localhost/savage-py27:lowspace-savage'
S2_TAG='localhost/savage-tool-donor:lowspace-savage'
FINAL_TAG='localhost/ivanka-exploratory-savage-denovo:0919ffa9-lowspace'

PODMAN="podman --root $PX_PODMAN_STORE"

die() { echo "FAIL $*" >&2; exit 1; }

# --- Guard and grant gates -------------------------------------------------
test "$PX_NAMED_GRANT" = "$EXPECTED_GRANT" || die 'named grant mismatch'
test "$PX_P1_REMAP_CLEAR" = 'yes' || die 'P1/remap priority not cleared by coordinator'
test ! -e "$PX_STOP_FILE" || die 'PX STOP present'
if [ -e "$PX_GLOBAL_LOCK" ]; then
    grep -q "$EXPECTED_GRANT" "$PX_GLOBAL_LOCK" || die 'global lock not bound to this grant'
fi
test -z "$($PODMAN ps -q)" || die 'containers active in bound store'

CONTEXT_FREE_KB=$(df -k "$PX_BUILD_CONTEXT" | awk 'NR==2{print $4}')
STORE_FREE_KB=$(df -k "$PX_PODMAN_STORE" | awk 'NR==2{print $4}')
test $((CONTEXT_FREE_KB - RESERVE_KB)) -ge "$NEEDED_KB" || die "context headroom insufficient"
test $((STORE_FREE_KB - RESERVE_KB)) -ge "$NEEDED_KB" || die "store headroom insufficient"
echo "PREFLIGHT context_free_kb=$CONTEXT_FREE_KB store_free_kb=$STORE_FREE_KB usable_min_kb=$NEEDED_KB"

# --- Exact context and checkout verification -------------------------------
check_context_hash() {
    printf '%s  %s\n' "$2" "$1" | (cd "$PX_BUILD_CONTEXT" && sha256sum -c -) \
        || die "context hash mismatch: $1"
}
check_context_hash Python-2.7.18.tgz "$PY27_SHA"
check_context_hash haploconduct-24e4d9fc.tar.gz "$HAPLO_ARCHIVE_SHA"
check_context_hash haploconduct-source-manifest.sha256 "$HAPLO_MANIFEST_SHA"
check_context_hash haploconduct-source-provenance.txt "$HAPLO_PROVENANCE_SHA"
check_context_hash ViralQuasispecies "$VQ_DONOR_SHA"

test "$(git -C "$PX_ADAPTER_CHECKOUT" rev-parse HEAD)" = "$EXPECTED_ADAPTER" \
    || die 'adapter checkout head mismatch'
test -z "$(git -C "$PX_ADAPTER_CHECKOUT" status --porcelain)" \
    || die 'adapter checkout dirty'
test -f "$PX_ADAPTER_CHECKOUT/Containerfile.assembler-bench" \
    || die 'missing frozen adapter Containerfile'
$PODMAN image inspect "$BASE_IMAGE" >/dev/null 2>&1 || die 'pinned base image absent'

# --- Bounded build helper --------------------------------------------------
build_image() {
    timeout 2400s podman --root "$PX_PODMAN_STORE" build \
        --pull=never --network=none --layers=false --force-rm \
        --memory=4g --cpuset-cpus=0-1 "$@"
}

STARTED_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Stage 1: Python 2.7.18 runtime only.
build_image \
    --build-arg BASE_IMAGE="$BASE_IMAGE" \
    --build-arg PYTHON27_ARCHIVE_SHA256="$PY27_SHA" \
    -f "$SCRIPT_DIR/Dockerfile.savage-py27" \
    -t "$S1_TAG" "$PX_BUILD_CONTEXT" || die 'stage1 build failed'
S1_ID=$($PODMAN image inspect "$S1_TAG" --format '{{.Id}}')
echo "STAGE1 $S1_ID"

# Stage 2: donor ViralQuasispecies + quick-cliques from exact pinned source.
build_image \
    --build-arg BASE_IMAGE="$S1_ID" \
    --build-arg HAPLOCONDUCT_COMMIT=24e4d9fc35ef6a93e336949a9a8f98ed4ceef362 \
    --build-arg QUICKCLIQUES_SOURCE_TREE_SHA1=4b41a2badc29877c28a0e903fe7df29a6666a220 \
    --build-arg HAPLOCONDUCT_ARCHIVE_SHA256="$HAPLO_ARCHIVE_SHA" \
    --build-arg HAPLOCONDUCT_MANIFEST_SHA256="$HAPLO_MANIFEST_SHA" \
    --build-arg HAPLOCONDUCT_PROVENANCE_SHA256="$HAPLO_PROVENANCE_SHA" \
    --build-arg VIRAL_QUASISPECIES_SHA256="$VQ_DONOR_SHA" \
    -f "$SCRIPT_DIR/Dockerfile.savage-tool-donor" \
    -t "$S2_TAG" "$PX_BUILD_CONTEXT" || die 'stage2 build failed'
S2_ID=$($PODMAN image inspect "$S2_TAG" --format '{{.Id}}')
echo "STAGE2 $S2_ID"

QC_BUNDLE_SHA=$($PODMAN run --rm --network=none --entrypoint /bin/cat \
    "$S2_ID" /attestation/qc-bundle-sha256.txt | tr -d '\r\n')
case "$QC_BUNDLE_SHA" in
    *[!0-9a-f]*|'') die 'invalid QC bundle digest' ;;
esac
test "${#QC_BUNDLE_SHA}" -eq 64 || die 'QC bundle digest length'
IMAGE_VQ_SHA=$($PODMAN run --rm --network=none --entrypoint /bin/sh "$S2_ID" \
    -c 'sha256sum /opt/savage/bin/ViralQuasispecies | cut -d" " -f1' | tr -d '\r\n')
test "$IMAGE_VQ_SHA" = "$VQ_DONOR_SHA" || die 'in-image donor binary hash mismatch'
$PODMAN run --rm --network=none --entrypoint /bin/sh "$S2_ID" \
    -c 'grep -q "/opt/python27/bin/python2.7" /usr/local/bin/savage \
        && test -x /usr/local/bin/savage \
        && test -x /opt/savage/quick-cliques/bin/qc \
        && test -x /opt/savage/quick-cliques/bin/printnm \
        && test -x /opt/savage/quick-cliques/bin/compdegen' \
    || die 'stage2 runtime artifacts missing'

# Stage 3: final frozen SAVAGE adapter over the attested donor image.
build_image \
    --build-arg ASSEMBLER_TOOL_IMAGE="$S2_ID" \
    --build-arg MICALL_BASE_COMMIT=8458f9e5d34c39a6694b1fb6a40e055d7ce89553 \
    --build-arg MICALL_SOURCE_COMMIT="$EXPECTED_ADAPTER" \
    --build-arg TOOL_IMAGE_ID="$S2_ID" \
    -f "$PX_ADAPTER_CHECKOUT/Containerfile.assembler-bench" \
    -t "$FINAL_TAG" "$PX_ADAPTER_CHECKOUT" || die 'final adapter build failed'
FINAL_ID=$($PODMAN image inspect "$FINAL_TAG" --format '{{.Id}}')
FINAL_REV=$($PODMAN image inspect "$FINAL_TAG" \
    --format '{{index .Config.Labels "org.opencontainers.image.revision"}}')
FINAL_TOOL=$($PODMAN image inspect "$FINAL_TAG" \
    --format '{{index .Config.Labels "org.ottojung.micall.native-tool-image"}}')
test "$FINAL_REV" = "$EXPECTED_ADAPTER" || die 'final image adapter revision'
test "$FINAL_TOOL" = "$S2_ID" || die 'final image tool donor binding'

FINISHED_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)
FREE_AFTER_KB=$(df -k "$PX_PODMAN_STORE" | awk 'NR==2{print $4}')

# Receipt is host-local; public artifacts contain digests only.
mkdir -p "$(dirname "$PX_RECEIPT_PATH")"
cat > "$PX_RECEIPT_PATH" <<EOF
{
  "schema": "ivanka.px.savage.lowspace-build-receipt.v1",
  "started_utc": "$STARTED_UTC",
  "finished_utc": "$FINISHED_UTC",
  "grant": "$EXPECTED_GRANT",
  "p1_remap_clear": "yes",
  "base_image": "$BASE_IMAGE",
  "adapter_commit": "$EXPECTED_ADAPTER",
  "python27_archive_sha256": "$PY27_SHA",
  "haploconduct_archive_sha256": "$HAPLO_ARCHIVE_SHA",
  "haploconduct_source_manifest_sha256": "$HAPLO_MANIFEST_SHA",
  "haploconduct_provenance_sha256": "$HAPLO_PROVENANCE_SHA",
  "quickcliques_tree_sha1": "4b41a2badc29877c28a0e903fe7df29a6666a220",
  "quickcliques_source_manifest_sha256": "$QC_SOURCE_MANIFEST_SHA",
  "viral_quasispecies_donor_sha256": "$VQ_DONOR_SHA",
  "qc_binaries_bundle_build_sha256": "$QC_BUNDLE_SHA",
  "stage1_image": "$S1_ID",
  "stage2_image": "$S2_ID",
  "final_image": "$FINAL_ID",
  "free_kb_before": "$CONTEXT_FREE_KB",
  "store_free_kb_before": "$STORE_FREE_KB",
  "store_free_kb_after": "$FREE_AFTER_KB",
  "reserve_kb": "$RESERVE_KB",
  "qualifying": false,
  "seven_way_inclusion": false
}
EOF

# Retire only this job's explicitly labelled stage images.
retire_stage() {
    image_id=$1
    stage_name=$2
    label=$($PODMAN image inspect "$image_id" \
        --format '{{index .Config.Labels "org.ottojung.exploratory.savage-lowspace-stage"}}')
    test "$label" = "$stage_name" || die "refusing to retire unlabelled $image_id"
    test "$image_id" != "$FINAL_ID" || die 'refusing to retire final image'
    users=$($PODMAN ps -aq --filter "ancestor=$image_id" || true)
    test -z "$users" || die "stage image in use: $image_id"
    $PODMAN image rm "$image_id" >/dev/null || die "retire failed: $image_id"
    echo "RETIRED $stage_name $image_id"
}
retire_stage "$S1_ID" py27
retire_stage "$S2_ID" tool-donor

echo "READY_BUILD_DONE final_image=$FINAL_ID receipt=$PX_RECEIPT_PATH"
