# Research source review — 2026-10-17

This supplements, rather than rewrites, the dated discovery reports and frozen
comparison005. Read [current outcomes and recommendation](current_design_comparison.md)
for the tested versions. Early “not integrated” or “not yet reliable” passages
in the research reports are development history, not the current matrix.
No newly located component has been silently substituted into a saved model.

## Rechecked primary evidence

| Source | Check and consequence |
|---|---|
| [igus DLE-RG-0001](https://www.igus.com/product/dle-rg-0001?artnr=DLE-RG-0001) | Current manufacturer page supports500×500×100 mm,2.5 kg, approximately0.8 mm precision and0.5 m/s, plus its belt/rack axes and motor/control options. This remains an architecture reference, not the simulated custom gantry's accuracy rating. |
| [Festo EXCM catalog](https://www.festo.com/media/catalog/204451_documentation.pdf) | Current2026/02 PDF pp.3,8,13 supports EXCM-30 strokes90–700/110–526 mm,±0.05 mm repetition,2/3 kg vertical/horizontal load, vertical brakes and four profile mounts below500 mm X stroke. EXCM-40 is horizontal-only in the selection table. Vertical load curves still require vendor engineering. |
| [SCHUNK EGP25,310900](https://schunk.com/de/en/gripping-systems/parallel-gripper/egp/egp-25-n-n-b/p/000000000000310900) | Current page supports26.5×18×72.7 mm,0.11 kg,3 mm per jaw,20–40 N summed force,32 mm maximum finger length and20 g per finger. The custom long-finger tool is not thereby manufacturer-qualified; exact CAD and price remain unverified. |
| [Festo EHPS catalog](https://www.festo.com/media/catalog/204394_documentation.pdf) | Current2025/05 PDF pp.6,9 supports154 N for EHPS-16 under the tabulated conditions, with strong lever-arm dependence. Do not substitute this for a force rating at the custom robot's fingertips or mix it with the old50 N brochure summary. |
| [Zaber X-LSM specifications](https://www.zaber.com/products/linear-stages/X-LSM/specs) | Current series and part tables distinguish travel/accuracy variants;25 N continuous thrust,250 N centered load and4 N·m pitch/yaw limits remain separate from peak thrust. A guide/load rating does not establish whole-rack accuracy or safe connector force. |
| [igus SLN](https://www.igus.de/antriebstechnik/linearachsen-mit-spindel/miniatur-linearmodule/sln) | Manufacturer table supports10 N axial/40 N radial static capacity for listed SLN-27 variants. Different screw/carriage variants must not be conflated. |
| [CoreXY mechanism](https://corexy.com/theory.html) | Original mechanism reference remains accessible. The implementation's coupled motor coordinates and generalized forces are custom simulation assumptions, not a commercial gantry certification. |
| [IAI Cartesian families](https://www.iai-automation.com/en/cartesian-robots.html) | Manufacturer page confirms 2–6-axis families, IK2/IK3/IK4 and ICSB catalogs, and its CAD portal. This is family/asset-discovery evidence, not a verified configured rack assembly or price. |
| [SMC LEHZ](https://www.smcworld.com/products/pickup/en-sg/electric_actuator/gripper_prod_lehz.html) | Size10 table distinguishes 4 mm both-side stroke, 6–14 N basic versus 2–6 N compact force, and 5–80 mm/s. CADENAS exports require registration; no downloaded CAD or redistribution license is invented. |
| [Robotiq Hand-E sheet](https://robotiq.com/hubfs/Hand-E_Adaptive_Gripper_ProductSheet_EN_2024-11_WEB.pdf) | The URL still says2024, but the current sheet says updated June2026 and includes Hand-E C10 variants. The Hand-E figures remain50 mm,1 kg,20–185 N per finger/40–370 N total. The filename is not a publication date; do not mix C10 columns into the original candidate. |
| [Reis et al. full paper](https://www.mi-research.net/en/article/pdf/preview/10.1007/s11633-021-1300-5.pdf) | Rechecked §§2.4,3.2–3.3: one moving finger,HS-422,rack/pinion and dovetail;90 supervised automatic cycles. This supports mechanism inspiration, not author CAD, arbitrary connector compatibility or a separately calibrated latch actuator. |
| [Industrial Cabling in Constrained Environments](https://arxiv.org/html/2404.10829v1) | Full text remains accessible and supports the connector-specific form-fit/Scott–Russell adaptation and clearance limitations. Its connectors and tasks are not evidence of RJ45 latch release. |
| [Gu et al.,2026](https://ieeexplore.ieee.org/abstract/document/11397151) | Direct fetch failed in this review; indexed publisher metadata/abstract still identifies RA-L11(4),4593–4600, DOI10.1109/LRA.2026.3665078. Full mechanism drawings remain unverified; no dimensions or CAD claims are added. |

## Prices and download limitations

The retained HIWIN catalog `sources/hiwin_linear_guideway.pdf`, PDF page89
(printed86), was reopened with PyMuPDF. Its MGN12H row supports13 mm assembly
height,27 mm block width,45.4 mm block length,12×8 mm rail and0.054 kg block
mass. These dimension references do not certify the custom gantry's stiffness
or its assembled accuracy. The previous online OpenBuilds C-Beam page returned
502 during source review; that is a retrieval limitation, not evidence of
product discontinuation or a reason to alter the retained repository assets.

Rechecked current single-unit listings: [PQ12-30-12-P](https://www.actuonix.com/pq12-30-12-p)
$65, [LAC](https://www.actuonix.com/lac) $30, [HS-422](https://hitecrcd.com/hs-422-deluxe-standard-servo/)
$20.99, [17HS15-1504S1](https://www.omc-stepperonline.com/nema-17-bipolar-45ncm-63-74oz-in-1-5a-42x42x39mm-4-wires-w-1m-cable-connector-17hs15-1504s1)
$9.13 and [DM542T](https://www.omc-stepperonline.com/digital-stepper-driver-1-0-4-2a-20-50vdc-for-nema-17-23-24-stepper-motor-dm542t)
$19.65. These exclude shipping/tax/integration and remain candidate prices,
not complete-system estimates or verified drop-in interfaces. The documented
39 mm motor versus B's38 mm envelope mismatch remains. No order was placed.

The newer indexed [OnRobot RG2 datasheet route](https://onrobot.com/storage/datasheets/datasheet_rg2.pdf)
supports the earlier indexed110 mm,3–40 N,0.78 kg and213×149×36 mm figures,
but a direct local download again returned HTML, not a PDF. The response is
retained as `sources/onrobot_rg2_current001_redirect.html`, SHA256
`599190cf5d167d95e5425eae285f210ef1a355813e6ea45a63f7f385b1ced5e2`.
It is not treated as a datasheet. Exact saved geometry still comes from the
official licensed USD repository; catalog dimensions and authored asset
envelopes/mass are different measurements and remain separately labeled.

## Local source identities

Read the local repository HEADs again; all four match the recorded provenance:

| Repository | Verified revision |
|---|---|
| OnRobot Isaac assets | `8004a32009cd3bb752791f64d0141522f263e2ba` |
| Robotiq Isaac assets | `24beb03320bf67483fcaa6059f3f347028ef8827` |
| OpenBuilds parametric parts | `17abbf71892cc630d7250b55da88d297847ef868` |
| SCHUNK description | `f88f51309a1d3879a90fe2623bc153c0af835675` |

Revision identity is not a new redistribution grant or proof that every working
tree file is pristine; the package/dependency manifests separately bind used
asset bytes. Preserve notices and the distinctions in
[sources_and_licenses.md](sources_and_licenses.md). Manufacturer drawings and
papers are linked in the gallery, not republished as freely licensed CAD.

## Engineering interpretation

The research covers broad architecture discovery, derivative alternatives,
component/drawing/asset investigation and tested integration. The three robots
are custom dimensioned mechanisms; the grippers are a reference-envelope
precision tool, a full-size vendor RG2 linkage and an original specialized
form-fit tool. None is claimed to be a fabrication-ready certified machine.
Unpriced complete assemblies, exact motor/brake interfaces, material/thermal
ratings and perception calibration remain disclosed engineering limitations.
They must not be replaced by invented procurement facts to close an audit.

This review checks the key selection/specification/price sources above. It is
not a new exhaustive audit of every historical hyperlink, nor a completion
certificate for the whole plan. The terminal physical follow-up is documented
in [matched_release_results001.md](matched_release_results001.md); final gallery
and requirement-level verification remain separate from this source review.
