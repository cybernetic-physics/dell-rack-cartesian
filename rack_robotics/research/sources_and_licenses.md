# Source and asset provenance

Retrieved/inspected 2026-10-16. Research downloads are not automatically licensed
for redistribution in a public gallery. Retain manufacturer notices; link to
papers/catalogs rather than republishing their full text or illustrations.

| Local directory under `sources/` | Upstream revision | License / disposition |
|---|---|---|
| `onrobot-isaacsim` | `8004a32009cd3bb752791f64d0141522f263e2ba` | [OnRobot](https://github.com/OnRobot/onrobot-isaacsim), BSD-3-Clause; retain LICENSE with any copied asset. LFS geometry downloaded. |
| `robotiq-isaacsim` | `24beb03320bf67483fcaa6059f3f347028ef8827` | [Robotiq](https://github.com/robotiq/isaacsim_assets), BSD-3-Clause plus NVIDIA CC-BY 4.0 portions listed in LICENSE and per-package licenses. LFS downloaded. |
| `openbuildsParts` | `17abbf71892cc630d7250b55da88d297847ef868` | [Matthew Yates/OpenBuilds](https://github.com/matthew-yates/openbuildsParts); repository attribution identifies CC BY-SA 4.0. Preserve credit and share-alike for derived CAD. |
| `schunk_description` | `f88f51309a1d3879a90fe2623bc153c0af835675` | [SCHUNK](https://github.com/SCHUNK-SE-Co-KG/schunk_description), GPL-3.0; not verified as EGP25 dimensions. Not imported into runtime yet. |

Original NVIDIA datacenter dependencies remain on the VM, with every extracted
file hashed by `scripts/freeze_baseline.py`. Recovery URL and archive SHA-256 are
in the baseline manifest. Original connector mesh MIT notice is frozen alongside
the original source. No existing rack or source asset was replaced.

## Research documents

- `reis2021.pdf`: publisher-hosted complete paper, DOI
  [10.1007/s11633-021-1300-5](https://www.mi-research.net/en/article/pdf/preview/10.1007/s11633-021-1300-5.pdf).
  Copyrighted research reference; no CAD reuse grant identified.
- `reis2021.html`: publisher landing page obtained after the bare-domain URL
  failed TLS verification. No TLS bypass used.
- `festo_ehps_2021.pdf`: [Festo's 2021 US catalog](https://ftp.festo.com/Public/PNEUMATIC/SOFTWARE_SERVICE/Documentation/2021/US/EHPS_ENUS.PDF),
  p.15 dimensional drawing visually inspected. Current 2025 values were checked
  separately via [the specified current catalog](https://media.festo.com/media/204394_documentation.pdf).
- `onrobot_rg2_redirect.html`: the old datasheet URL returned HTML, not a PDF.
  Renamed after content inspection; do not use it as a datasheet. Indexed
  manufacturer specifications remain provisional until a current download or
  official support document is obtained.
- EXCM current catalog text/dimensions inspected via web; direct local download
  returned HTTP 403. This is a retrieval limitation, not evidence that CAD is
  unavailable. Vendor CAD portals are distinct from open redistribution grants.

Remaining procurement work: exact purchased actuator variants, fastener/material
certification, CAD redistribution grants where needed, quotations and duty-cycle
validation. Do not fabricate a complete-system price from an actuator-only price.

## Simulation source conventions

Parametric parts must record dimensions, source URL, whether each value is
catalog-derived or a design assumption, collision simplification and inertia
method. Vendor geometry must keep its original units and scale. Every experiment
must record source/configuration hashes so later changes cannot relabel old
results as measurements of the new design.
