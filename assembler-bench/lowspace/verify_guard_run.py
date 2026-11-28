#!/usr/bin/env python3
"""Verify a guarded exploratory_runtime run from durable artifacts.

This is not a new guard protocol: it only reads the shared CLI's status
output, the durable run receipt, the hashed run log and the append-only lease
journal produced by the deployed guard.
"""
import argparse
import ast
import hashlib
import json
import re
from pathlib import Path

CLOSED = {"released", "reconciled"}
HASH64 = re.compile(r"\A[0-9a-f]{64}\Z")


def parse_status(path):
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    for line in reversed(text.splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                value = ast.literal_eval(line)
            except (ValueError, SyntaxError):
                continue
            if isinstance(value, dict):
                return value
    raise ValueError("guarded CLI status dict not found")


def find_receipt(root, marker, tool):
    baseline = {Path(line).name for line in
                Path(marker).read_text(encoding="utf-8").splitlines() if line.strip()}
    found = []
    for path in sorted(Path(root).glob("run-" + tool + "-*.json")):
        if (path.is_file() and not path.is_symlink()
                and path.name not in baseline):
            found.append(path)
    if len(found) != 1:
        raise ValueError("expected exactly one new run receipt, got %d" % len(found))
    return found[0]


def lease_last(root, ident):
    journal = Path(root) / ".worker-lease.jsonl"
    if not journal.exists() or journal.is_symlink():
        return None
    last = None
    for line in journal.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if event.get("lease") == ident:
            last = event
    return last


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", required=True)
    ap.add_argument("--marker", required=True)
    ap.add_argument("--status", required=True)
    ap.add_argument("--tool", default="savage-denovo")
    ap.add_argument("--label", required=True)
    ap.add_argument("--expect-token", action="append", default=[])
    ap.add_argument("--require-hash-lines", type=int, default=0)
    args = ap.parse_args()

    status = parse_status(args.status)
    receipt_path = find_receipt(args.root, args.marker, args.tool)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    log_path = receipt_path.with_suffix(".log")

    if status.get("status") != "finished" or status.get("exit_code") != 0:
        raise ValueError("guard status not finished/zero: %s %s" % (
            status.get("status"), status.get("exit_code")))
    if receipt.get("tool") != args.tool or receipt.get("mode") != "build":
        raise ValueError("wrong receipt identity")
    if receipt.get("status") != "finished" or receipt.get("exit_code") != 0:
        raise ValueError("receipt not finished/zero: %s %s" % (
            receipt.get("status"), receipt.get("exit_code")))
    if receipt.get("reason") or receipt.get("lease_state") == "active_unreleased":
        raise ValueError("guarded run carries failure or active lease")
    if not isinstance(receipt.get("orphan_cleanup"), dict):
        raise ValueError("missing build orphan-cleanup proof")
    if (receipt.get("job_temp_cleanup") or {}).get("removed") is not True:
        raise ValueError("job temp not verified removed")

    if not log_path.is_file() or log_path.is_symlink():
        raise ValueError("run log unavailable")
    log_bytes = log_path.read_bytes()
    digest = hashlib.sha256(log_bytes).hexdigest()
    if digest != receipt.get("log_sha256"):
        raise ValueError("run log hash mismatch")
    if status.get("log_sha256") not in (None, digest):
        raise ValueError("CLI status log hash mismatch")
    log_text = log_bytes.decode("utf-8", "replace")

    for token in args.expect_token:
        if token not in log_text:
            raise ValueError("expected log token missing: " + token)
    hash_lines = {line.strip() for line in log_text.splitlines() if HASH64.fullmatch(line.strip())}
    if len(hash_lines) < args.require_hash_lines:
        raise ValueError("too few hashed attestation lines")

    ident = receipt_path.stem[len("run-" + args.tool + "-"):]
    lease = lease_last(args.root, ident)
    if lease is None or lease.get("state") not in CLOSED:
        raise ValueError("lease not closed for " + ident)

    print("GUARD_OK label=%s receipt=%s log=%s log_sha256=%s lease_state=%s" % (
        args.label, receipt_path.name, log_path.name, digest, lease.get("state")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
