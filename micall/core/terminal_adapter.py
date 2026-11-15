"""Detect unexpected technical tails using paired-read evidence alone."""
from collections import Counter
from pathlib import Path


def sample_mates(path, limit=2000):
    rows = []
    with Path(path).open() as stream:
        for _ in range(limit):
            header = stream.readline()
            if not header:
                break
            sequence = stream.readline().strip().upper()
            plus = stream.readline()
            quality = stream.readline().strip()
            if not header.startswith('@') or not plus.startswith('+'):
                return []
            if len(sequence) != len(quality):
                return []
            rows.append((header.split()[0], sequence))
    return rows


def shared_terminal_adapter(path1, path2):
    """Require 90% dual-mate prevalence and diverse upstream contexts."""
    first = sample_mates(path1)
    second = sample_mates(path2)
    n = len(first)
    if n < 100 or len(second) != n:
        return None
    if any(a[0] != b[0] for a, b in zip(first, second)):
        return None
    reads = ([seq for _, seq in first], [seq for _, seq in second])
    for width in range(24, 17, -1):
        frequencies = [Counter(s[-width:] for s in mate
                               if len(s) >= width + 31) for mate in reads]
        candidates = set(frequencies[0]) & set(frequencies[1])
        for tail in sorted(candidates):
            if any(c[tail] * 10 < 9 * n for c in frequencies):
                continue
            contexts = {s[-width-16:-width] for mate in reads
                        for s in mate if s.endswith(tail) and len(s)>=width+16}
            if len(contexts) >= 64:
                return tail
    return None
