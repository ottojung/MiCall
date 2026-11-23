# Ray source-only recovery: sibling RayPlatform checkout (NONQUALIFYING)

Source investigation for the frozen-8458 Ray adapter pin
`bench/assembler-ray-frozen-8458f9e5` @ `9e02a9205fc338e1be4f0cd4a8dd4a13b406ae88`,
native Ray pin `621dfe8454dc96d49f405e413cb759d3f48790b2`. No Podman build,
native build, benchmark or pilot was run to produce this document.

## Root cause

The pinned Ray tree has **no `.gitmodules`** (GitHub API returns 404). Its
`RayPlatform` entry is a symlink (git mode `120000`, blob
`5eba77d865da7df4bbf6bf390302cbec0310e264`) with target `../RayPlatform`.
Therefore `git clone --recursive` and `git submodule update --init --recursive`
are no-ops: the symlink stays dangling unless a **sibling** `RayPlatform`
checkout exists next to the `ray` checkout.

That explains both observed failures:

- `make` fails on `RayPlatform/store/CarriageableItem.h: No such file or
  directory` because `-I. -IRayPlatform` (pinned `Makefile`) cannot resolve
  the include through the dangling symlink.
- CMake fails with `No SOURCES given to target: Ray` because the pinned
  `CMakeLists.txt` lists sources as `RayPlatform/RayPlatform/...`, which CMake
  drops when the symlink target is absent.

## Exact legal source versions

| Component | Exact commit | Identity | License | Evidence |
|---|---|---|---|---|
| Ray | `621dfe8454dc96d49f405e413cb759d3f48790b2` | `HEAD` and `refs/heads/master` of `sebhtml/ray`; Makefile reports `2.3.2-devel` | GPL-3.0 (application) | `LICENSE.txt` SHA256 `fc24be5a854af6d2669d9db7f02fdbaf1bab72d16089362fa39f3169666e4956`; `gpl-3.0.txt` blob `94a9ed024d3859793618152ea559a168bbcbb5e2` |
| RayPlatform | `c8d9fe2e1347be299f2e74dd8a0fc278b5a02e16` | `HEAD`, `refs/heads/master`, and peeled tag `v2.0.1^{}` of `sebhtml/RayPlatform` | LGPL-3.0 (framework) | `LICENSE` SHA256 `a9d8d325805dbe2d92390a3f74e310bd92fbfcf1e07c038a42fdc304788d76ee`; `lgpl-3.0.txt` SHA256 `da7eabb7bafdf7d3ae5e9f223aa5bdc1eece45ac569dc21b3b037520b4464768` |

RayPlatform `c8d9fe2e…` is the final upstream commit (2014-02-12) and is the
only version contemporaneous with, and compatible with, the pinned Ray tree;
it contains both files reported missing:

- `RayPlatform/cryptography/crypto.cpp`: git blob
  `16eb21132d91c029c1501991ec5a895d59afc69f`, raw SHA256
  `068ee2b85bfcb7be592b1fd718dcf8f115e0b544d7d28aabf97e9f0f21edf9a2`.
- `RayPlatform/store/CarriageableItem.h`: git blob
  `ec7f5987525040083afe7cdca952a32cd5290e2b`, raw SHA256
  `b119603aee2856331824749bc9f46819056c305c390a83ce18b86a5c0d31cf5d`.

Ray pinned `Makefile` raw SHA256
`21296258ae92958a3d38c815a1bd0af35f32fc52b3bb37918648b216a7d82ae5`.

## Reproducible source layout (no build performed here)

```sh
mkdir -p /src
git clone --quiet https://github.com/sebhtml/ray.git /src/ray
git -C /src/ray checkout --quiet 621dfe8454dc96d49f405e413cb759d3f48790b2
git clone --quiet https://github.com/sebhtml/RayPlatform.git /src/RayPlatform
git -C /src/RayPlatform checkout --quiet c8d9fe2e1347be299f2e74dd8a0fc278b5a02e16
test "$(git -C /src/ray rev-parse HEAD)" = 621dfe8454dc96d49f405e413cb759d3f48790b2
test "$(git -C /src/RayPlatform rev-parse HEAD)" = c8d9fe2e1347be299f2e74dd8a0fc278b5a02e16
test "$(readlink /src/ray/RayPlatform)" = "../RayPlatform"
test -f /src/ray/RayPlatform/RayPlatform/cryptography/crypto.cpp
test -f /src/ray/RayPlatform/RayPlatform/store/CarriageableItem.h
test "$(sha256sum /src/ray/RayPlatform/RayPlatform/cryptography/crypto.cpp | cut -d' ' -f1)" = 068ee2b85bfcb7be592b1fd718dcf8f115e0b544d7d28aabf97e9f0f21edf9a2
test "$(sha256sum /src/ray/RayPlatform/RayPlatform/store/CarriageableItem.h | cut -d' ' -f1)" = b119603aee2856331824749bc9f46819056c305c390a83ce18b86a5c0d31cf5d
```

The sibling directory is required: `-IRayPlatform` resolves to
`/src/ray/RayPlatform` -> `/src/RayPlatform`, and the include directive
`RayPlatform/store/CarriageableItem.h` then resolves to
`/src/RayPlatform/RayPlatform/store/CarriageableItem.h`. Cloning RayPlatform
*inside* `/src/ray` (or replacing the symlink with an unrelated directory) is
not the upstream layout and will not restore the documented paths.

For the native image builder only: after the checks above, build with the
pinned Makefile (`make` from `/src/ray`, which also builds
`RayPlatform/libRayPlatform.a` via the symlink), install the resulting `Ray`
ELF, and independently attest its SHA256 before using it as
`TOOL_BINARY_SHA256`. That binary hash is deliberately **not** asserted here:
this source-only investigation did not compile Ray.

## Scope

This document and its guard test change no executable adapter code, no
clinical MiCall source, no frozen seven branch/image, and no reference or
truth input. Ray remains NONQUALIFYING and source-pinned.
