#!/bin/sh
# SAVAGE low-space build/attestation commands.
# Execute ONLY inside a named UNZbw slot after P1/remap release. Every OCI
# build/run below goes through the shared exploratory_runtime CLI, which owns
# the shared worker lock, durable lease, watchdog contract, storage.conf
# binding, reserved space admission, wall/RSS guard, exact teardown and
# job-temp cleanup. No new guard protocol, no direct podman build/run and no
# prune command is used by this script.
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

: "${PX_DONOR_DIR:?host-local donor/context directory}"
: "${PX_ADAPTER_CHECKOUT:?pinned frozen SAVAGE adapter checkout}"
: "${PX_CONTROL_ROOT:?deployed PX control root}"
: "${PX_ROOT:?exploratory project root owning storage.conf}"
: "${PX_REGISTRY:?absolute path to exploratory_candidates.json}"
: "${PX_BASELINE:?absolute path to budget-baseline.json}"
: "${PX_RECEIPT_PATH:?host-local receipt output path}"
: "${PX_NAMED_GRANT:?exact named slot grant}"
: "${PX_P1_REMAP_CLEAR:?set to yes only after coordinator confirms priority}"

EXPECTED_GRANT='savage-lowspace-UNZbwJhfujc2BbDNDtWgYq-practices-V9ro-lOL3'
EXPECTED_ADAPTER='0919ffa97f609b6f0b650ce834f0fc79822f18e5'
BASE_IMAGE='sha256:da795bbdbfbdd3c735c59d0ee008dae1781c68268b24298235e6b2cfe50a23ad'
PY27_SHA='da3080e3b488f648a3d7a4560ddee895284c3380b11d6de75edb986526b9a814'
HAPLO_ARCHIVE_SHA='09cad6b864206300caaa543d7df1aab6ac80ba63c80ff66d99bfdba67b87f19e'
HAPLO_MANIFEST_SHA='f1a05a2c077624736118e0d16b2d9514e1ee24f1b02086a6a021ecbb595859ef'
HAPLO_PROVENANCE_SHA='5be07d4848307eb0613380cfc27f342fed8292e3e3ac8c4733f71d4a830f410f'
VQ_DONOR_SHA='199d97b7330df213f0adf99aaebb8f74d59806dfe90379f15dea28f0aa0c6590'
QC_SOURCE_MANIFEST_SHA='ec45769285aaafe1068fc7ac164777343c11a508b1dae34b15aac2d83ed08876'
S1_TAG='localhost/savage-py27:lowspace-savage'
S2_TAG='localhost/savage-tool-donor:lowspace-savage'
FINAL_TAG='localhost/ivanka-exploratory-savage-denovo:0919ffa9-lowspace'
PY="$PX_CONTROL_ROOT:$PX_CONTROL_ROOT/benchmarks"

test "$PX_NAMED_GRANT" = "$EXPECTED_GRANT" || { echo 'grant mismatch' >&2; exit 1; }
test "$PX_P1_REMAP_CLEAR" = 'yes' || { echo 'P1/remap not cleared' >&2; exit 1; }
test "$(git -C "$PX_ADAPTER_CHECKOUT" rev-parse HEAD)" = "$EXPECTED_ADAPTER" \
    || { echo 'adapter head mismatch' >&2; exit 1; }
test -z "$(git -C "$PX_ADAPTER_CHECKOUT" status --porcelain)" \
    || { echo 'adapter checkout dirty' >&2; exit 1; }
test -f "$PX_ROOT/storage.conf" || { echo 'storage.conf missing' >&2; exit 1; }
test -f "$PX_ADAPTER_CHECKOUT/Containerfile.assembler-bench" \
    || { echo 'adapter Containerfile missing' >&2; exit 1; }
test -f "$SCRIPT_DIR/verify_guard_run.py" || { echo 'guard verifier missing' >&2; exit 1; }

# 0) staged provenance before any OCI action (read-only, like Unicycler).
python3 - "$PX_DONOR_DIR/PROVENANCE.json" "$PX_DONOR_DIR/context" "$SCRIPT_DIR" <<'PY'
import hashlib, json, os, sys
doc = json.load(open(sys.argv[1])); base = sys.argv[2]; scripts = sys.argv[3]
assert doc['base_image'] == 'sha256:da795bbdbfbdd3c735c59d0ee008dae1781c68268b24298235e6b2cfe50a23ad'
assert doc['viral_quasispecies_sha256'] == '199d97b7330df213f0adf99aaebb8f74d59806dfe90379f15dea28f0aa0c6590'
assert doc['quickcliques_tree_sha1'] == '4b41a2badc29877c28a0e903fe7df29a6666a220'
for rel, meta in doc['files'].items():
    root = scripts if rel.startswith('Dockerfile.') else base
    p = os.path.join(root, rel)
    assert hashlib.sha256(open(p, 'rb').read()).hexdigest() == meta['sha256'], rel
print('staged provenance OK:', len(doc['files']), 'entries')
PY

# Guard stage runner: redirect the CLI status dict without a pipeline, then
# verify durable status/exit_code/lease/log-hash artifacts before continuing.
guard_and_verify() {
    label=$1
    hash_lines=$2
    shift 2
    marker="$PX_DONOR_DIR/$label.marker"
    status_file="$PX_DONOR_DIR/$label.guard.txt"
    find "$PX_ROOT" -maxdepth 1 -type f -name 'run-savage-denovo-*.json' -print > "$marker"
    if PYTHONPATH="$PY" python3 -m assembler_bench.exploratory_runtime.cli \
        --registry "$PX_REGISTRY" --baseline "$PX_BASELINE" \
        --tool savage-denovo --mode build --reserve-bytes 1073741824 -- \
        "$@" > "$status_file" 2>&1; then
        summary=$(python3 "$SCRIPT_DIR/verify_guard_run.py" \
            --root "$PX_ROOT" --marker "$marker" --status "$status_file" \
            --tool savage-denovo --label "$label" \
            --require-hash-lines "$hash_lines") || {
            cat "$status_file" >&2
            exit 1
        }
    else
        rc=$?
        cat "$status_file" >&2
        exit "$rc"
    fi
    printf '%s\n' "$summary"
    case "$summary" in
        *" log="*) rest=${summary#*" log="}; GUARD_LOG="$PX_ROOT/${rest%% *}" ;;
        *) echo 'guarded log path missing' >&2; exit 1 ;;
    esac
    test -f "$GUARD_LOG" || { echo 'guarded log unavailable' >&2; exit 1; }
}

# 1) Python 2.7.18 donor stage from the exact cached archive.
guard_and_verify stage1 0 \
    podman build --pull=never --network=none --layers=false \
    --build-arg BASE_IMAGE="$BASE_IMAGE" \
    -f "$SCRIPT_DIR/Dockerfile.savage-py27" \
    --tag "$S1_TAG" "$PX_DONOR_DIR/context"
S1_ID=$(CONTAINERS_STORAGE_CONF="$PX_ROOT/storage.conf" \
    podman image inspect "$S1_TAG" --format '{{.Id}}')
echo "STAGE1 $S1_ID"

# 2) Tool donor stage: donor binary + quick-cliques from exact pinned source.
guard_and_verify stage2 0 \
    podman build --pull=never --network=none --layers=false \
    --build-arg BASE_IMAGE="$S1_ID" \
    --build-arg HAPLOCONDUCT_COMMIT=24e4d9fc35ef6a93e336949a9a8f98ed4ceef362 \
    --build-arg QUICKCLIQUES_SOURCE_TREE_SHA1=4b41a2badc29877c28a0e903fe7df29a6666a220 \
    --build-arg HAPLOCONDUCT_ARCHIVE_SHA256="$HAPLO_ARCHIVE_SHA" \
    --build-arg HAPLOCONDUCT_MANIFEST_SHA256="$HAPLO_MANIFEST_SHA" \
    --build-arg HAPLOCONDUCT_PROVENANCE_SHA256="$HAPLO_PROVENANCE_SHA" \
    --build-arg VIRAL_QUASISPECIES_SHA256="$VQ_DONOR_SHA" \
    -f "$SCRIPT_DIR/Dockerfile.savage-tool-donor" \
    --tag "$S2_TAG" "$PX_DONOR_DIR/context"
S2_ID=$(CONTAINERS_STORAGE_CONF="$PX_ROOT/storage.conf" \
    podman image inspect "$S2_TAG" --format '{{.Id}}')
echo "STAGE2 $S2_ID"

# 3) In-image attestation through the same guarded CLI. The run log hash and
#    two hashed attestation lines are verified before parsing their values.
guard_and_verify attestation 2 \
    podman run --pull=never --network=none --rm --entrypoint /bin/sh \
    "$S2_TAG" -c 'set -eu
sha256sum /opt/savage/bin/ViralQuasispecies
cat /attestation/qc-bundle-sha256.txt
test -x /opt/savage/quick-cliques/bin/qc
test -x /opt/savage/quick-cliques/bin/printnm
test -x /opt/savage/quick-cliques/bin/compdegen
test -x /usr/local/bin/savage
grep -q "/opt/python27/bin/python2.7" /usr/local/bin/savage'
VQ_IN_IMAGE=$(awk -v want="$VQ_DONOR_SHA" \
    '$1==want && $2=="/opt/savage/bin/ViralQuasispecies" {print $1}' "$GUARD_LOG")
QC_BUNDLE_SHA=$(awk 'length($0)==64 && $0 ~ /^[0-9a-f]+$/ {print $0}' "$GUARD_LOG")
test "$VQ_IN_IMAGE" = "$VQ_DONOR_SHA" || { echo 'in-image donor hash mismatch' >&2; exit 1; }
test "${#QC_BUNDLE_SHA}" -eq 64 || { echo 'QC bundle hash missing' >&2; exit 1; }

# 4) Final frozen SAVAGE adapter image over the attested donor image.
guard_and_verify final 0 \
    podman build --pull=never --network=none --layers=false \
    -f "$PX_ADAPTER_CHECKOUT/Containerfile.assembler-bench" \
    --tag "$FINAL_TAG" \
    --build-arg ASSEMBLER_TOOL_IMAGE="$S2_ID" \
    --build-arg MICALL_BASE_COMMIT=8458f9e5d34c39a6694b1fb6a40e055d7ce89553 \
    --build-arg MICALL_SOURCE_COMMIT="$EXPECTED_ADAPTER" \
    --build-arg TOOL_IMAGE_ID="$S2_ID" \
    "$PX_ADAPTER_CHECKOUT"
FINAL_ID=$(CONTAINERS_STORAGE_CONF="$PX_ROOT/storage.conf" \
    podman image inspect "$FINAL_TAG" --format '{{.Id}}')
FINAL_REV=$(CONTAINERS_STORAGE_CONF="$PX_ROOT/storage.conf" \
    podman image inspect "$FINAL_TAG" \
    --format '{{index .Config.Labels "org.opencontainers.image.revision"}}')
FINAL_TOOL=$(CONTAINERS_STORAGE_CONF="$PX_ROOT/storage.conf" \
    podman image inspect "$FINAL_TAG" \
    --format '{{index .Config.Labels "org.ottojung.micall.native-tool-image"}}')
test "$FINAL_REV" = "$EXPECTED_ADAPTER" || { echo 'final adapter revision mismatch' >&2; exit 1; }
test "$FINAL_TOOL" = "$S2_ID" || { echo 'final tool binding mismatch' >&2; exit 1; }

# Host-local receipt only; no public/private path is embedded in this repo file.
mkdir -p "$(dirname "$PX_RECEIPT_PATH")"
python3 - "$PX_RECEIPT_PATH" "$FINAL_ID" "$S1_ID" "$S2_ID" "$QC_BUNDLE_SHA" \
    "$EXPECTED_GRANT" <<'PY'
import json, sys
path, final, s1, s2, qc, grant = sys.argv[1:7]
doc = {
    "schema": "ivanka.px.savage.guarded-lowspace-build-receipt.v1",
    "grant": grant,
    "base_image": "sha256:da795bbdbfbdd3c735c59d0ee008dae1781c68268b24298235e6b2cfe50a23ad",
    "adapter_commit": "0919ffa97f609b6f0b650ce834f0fc79822f18e5",
    "viral_quasispecies_donor_sha256": "199d97b7330df213f0adf99aaebb8f74d59806dfe90379f15dea28f0aa0c6590",
    "qc_binaries_bundle_build_sha256": qc,
    "quickcliques_tree_sha1": "4b41a2badc29877c28a0e903fe7df29a6666a220",
    "stage1_image": s1, "stage2_image": s2, "final_image": final,
    "qualifying": False, "seven_way_inclusion": False,
}
with open(path, 'w') as f:
    json.dump(doc, f, indent=2, sort_keys=True); f.write('\n')
PY

echo "GUARDED_BUILD_DONE final_image=$FINAL_ID receipt=$PX_RECEIPT_PATH"
