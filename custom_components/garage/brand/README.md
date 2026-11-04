# Garage brand assets

An original geometric garage bay and vehicle silhouette icon drawn by
`scripts/generate_brand.py` on a dark navy rounded square, with a matching gold
`Garage` wordmark for the landscape logo. No third-party artwork is used.

| File | Size | Purpose |
| --- | --- | --- |
| `icon.png` | 256 × 256 | Home Assistant and HACS icon |
| `icon@2x.png` | 512 × 512 | High-resolution icon |
| `logo.png` | 966 × 256 | Landscape integration logo; README artwork |
| `logo@2x.png` | 1932 × 512 | High-resolution landscape logo |

All images are RGBA PNGs with transparent outer corners and backgrounds. These
sizes follow the [HA brand image guidelines](https://contributors.home-assistant.io/core/integrations/brands/).
Home Assistant 2026.3 and later serves these assets from the integration's local
`brand/` directory. The gold wordmark works against light and dark backgrounds,
so separate dark variants are not required.

## Source and permission

The icon is drawn from geometric primitives in this repository's
`scripts/generate_brand.py` and is covered by the repository's MIT license
(Copyright (c) 2026 eigger). The wordmark is rendered with Pillow's bundled
Aileron Regular via
[`ImageFont.load_default`](https://pillow.readthedocs.io/en/stable/reference/ImageFont.html#PIL.ImageFont.load_default).
[Aileron](https://dotcolon.net/font/aileron/) permits commercial use and is
released with no rights reserved. No font file is redistributed or loaded from
the system. The Garage server's own branding is not reused.

## Reproduce

Use Python 3.10 or newer and Pillow 12.3.0 (also supplied by HA 2026.10.2):

```sh
python -m pip install Pillow==12.3.0
python scripts/generate_brand.py
```

The script needs no network access and produces the same PNG bytes on every
run with that Pillow version.

SHA256 (Pillow 12.3.0):

- `icon@2x.png`: `61c8f1ff23ab579523dd82b2014b6d9e09d1c44b4885ef3f8ea88a5cdcc3e5a1`
- `icon.png`: `4bd8ea8b85e02c57d77dddd99b63c880812f37de94dbe20b74f1900b6df86c36`
- `logo@2x.png`: `8df32b74a151a427b7cff36b11f117d7e2501faa3303cb26ed4f9fb99b142035`
- `logo.png`: `5af117de2a717632dfb3c805945da6e246c01ceec1048c04d53372a4343cd9e4`

The local `brand/icon.png` is used by the
[HACS brands check](https://hacs.xyz/docs/publish/include/#check-brands).
These files do not imply inclusion in the HACS default list or HA brands
repository. README pages use `custom_components/garage/brand/logo.png`.
