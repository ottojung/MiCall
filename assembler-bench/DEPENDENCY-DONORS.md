# SAVAGE dependency donor evidence (source-only, 2026-11-25)

This branch is `bench/frozen-8458f9e5-savage-20261123` plus one evidence file.
It is a direct child of frozen MiCall master
`8458f9e5d34c39a6694b1fb6a40e055d7ce89553`; no clinical source is changed and
no image, registry or pilot is claimed here.

## Tool pin

- Upstream: `https://github.com/HaploConduct/HaploConduct` @
  `24e4d9fc35ef6a93e336949a9a8f98ed4ceef362` (GPL-3.0).
- Adapter commit: `0919ffa97f609b6f0b650ce834f0fc79822f18e5`.
- Native asset: `ViralQuasispecies` SHA-256
  `199d97b7330df213f0adf99aaebb8f74d59806dfe90379f15dea28f0aa0c6590`.
  `quick-cliques` was not attested by the donor; do not claim it.

## Python 2.7 donor dependency

HaploConduct's `haploconduct.py` / `savage.py` are Python 2 scripts and require
`python2.7 + scipy` (upstream README, conda env `python=2.7 scipy …`). The
frozen parent has no python2.7; apt `python2.7 python-scipy` is not
source-attested.

- Source: `https://www.python.org/ftp/python/2.7.18/Python-2.7.18.tgz`;
  cpython tag `v2.7.18` →
  `41ca0e7833977c2475722ccc3dd5c16865d96dc1` (verified by `git ls-remote`
  2026-11-25T19:31Z; `Include/patchlevel.h` = `2.7.18`).
- Byte-pinned archives: python.org tarball SHA-256
  `da3080e3b488f648a3d7a4560ddee895284c3380b11d6de75edb986526b9a814`
  (17,539,408 B); GitHub mirror `cpython-v2.7.18.tar.gz` SHA-256
  `aa3822dc1615ccaf88352f1c4f2e5687d708be9a45c4c1c93cec64ee123dbec7`
  (17,517,628 B).
- Licence: PSF-2.0, GPL-compatible; retain the PSF notice.
- scipy: sdist 1.2.3 SHA-256
  `ecbe6413ca90b8e19f8475bfa303ac001e81b04ec600d17fa7f816271f7cca57`
  (23,335,997 B), BSD. 1.2.3 is the last scipy line accepting Python 2.7
  (1.3.0 requires `>=3.5`).
- Donor path (NOT executed; needs guard deployment + free slot): verify the
  tarball, `./configure --prefix=/opt/python27 && make -j2 && make install`,
  install `scipy-1.2.3.tar.gz` into the same prefix, then record exact
  `--version` output and SHA-256 of `/opt/python27/bin/python2.7`.
- Binary SHA-256: **not attested**. Must be produced by a guarded donor job;
  fail closed on mismatch. No image may be built before this exists.

Full cross-tool evidence and the 20/20 source-only verification output are on
`ottojung/ivanka` branch
`px/attest-unicycler-savage-dependency-donors-20261125`.
