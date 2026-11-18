"""The index must skip only impossible overlaps, without dropping any input."""

import random

import pytest

from micall.utils import referenceless_contig_stitcher as stitcher


@pytest.mark.parametrize("kmer_size", [1, 8, 30])
def test_candidate_index_is_exact_kmer_necessary_condition(monkeypatch, kmer_size):
    monkeypatch.setattr(stitcher, "KMER_SIZE", kmer_size)
    random_generator = random.Random(42)
    sequences = [
        "", "A", "A" * 29, "A" * 30, "A" * 31, "C" * 40,
        "G" * 150, "ACGT" * 20, "TGCA" * 20,
        "A" * 40 + "C" * 40, "C" * 40 + "A" * 40,
        "N" * 40, "T" * 40, "A" * 40,
    ]
    sequences += [
        "".join(random_generator.choices("ACGT", k=length))
        for length in [2, 7, 29, 30, 31, 50, 80, 120, 200]
    ]
    contigs = [
        stitcher.ContigWithAligner(name=f"candidate{i}", seq=seq,
                                  reads_count=None)
        for i, seq in enumerate(sequences)
    ]
    cache = {}
    is_short, short_indices, postings = stitcher._build_kmer_candidate_index(
        contigs, cache
    )
    for i, query in enumerate(contigs):
        candidates = stitcher._candidate_indices_for_query(
            query, is_short, short_indices, postings, cache
        )
        for j, other in enumerate(contigs):
            if min(len(query.seq), len(other.seq)) < kmer_size:
                assert candidates is None or j in candidates
            else:
                shared = not stitcher.get_kmers(cache, query.seq).isdisjoint(
                    stitcher.get_kmers(cache, other.seq)
                )
                assert candidates is not None
                assert (j in candidates) == shared
        if candidates is not None:
            assert list(sorted(candidates)) == sorted(candidates)
    assert len(contigs) == len(sequences)


def test_candidate_index_does_not_discard_short_contigs():
    contigs = [
        stitcher.ContigWithAligner(name="left", seq="C" * 100, reads_count=None),
        stitcher.ContigWithAligner(name="short", seq="A" * 12, reads_count=None),
        stitcher.ContigWithAligner(name="right", seq="A" * 90, reads_count=None),
    ]
    cache = {}
    is_short, short_indices, postings = stitcher._build_kmer_candidate_index(
        contigs, cache
    )
    assert stitcher._candidate_indices_for_query(
        contigs[0], is_short, short_indices, postings, cache
    ) == {0, 1}
    assert stitcher._candidate_indices_for_query(
        contigs[1], is_short, short_indices, postings, cache
    ) is None
