# PLAN_p2 requirement-level delivery review

2026-10-17. This review retains the full scope of [PLAN_p2](../PLAN_p2.md),
including failed designs, all three architectures/tools, randomized trials,
four-view media, independent environments and Mac access. It is not a claim
of fabrication readiness, physical-hardware reliability or safety certification.

Status: **delivery requirements verified**. Gallery011 Mac QA passes all865
served-file hashes and29 video play/seek checks, with zero browser errors;
documentation file links pass. The table below records the inspected evidence.
Earlier `DELIVERY_AUDIT.md` checkpoints and documents frozen inside gallery
snapshots retain their build-time status and are superseded by this review.

## Scope-to-evidence map

Paths below are relative to `rack_robotics/` unless prefixed by `../`.
Current exact packages are AA v016, AB v011, AC v005, BA v014, BB v007,
BC v004, CA v021, CB v002 and CC v003. No result from an earlier version is
silently substituted for these packages.

| Plan requirement | Inspected authoritative evidence and result |
|---|---|
| §1: existing VM, Isaac/IsaacAutomator, GPU/storage, original scene and baseline | Existing `isaac-g4-rtxpro6000x2-flex` / `dell-rack-sim`, pinned Isaac6.0.1-rc.7 runtime and original GUI PID135 retained. `assets/shared_rack/baseline-001/manifest.json`, `experiments/baseline-001-full-rack/results.json`:121 passing checks on the original loaded rack. `dependency-inventory002` freshly resolves all preserved layers/assets. The module extension does not replace the baseline; no infrastructure was provisioned. |
| §2.1–3: rack attachment, practical workspace and hardware clearance | Dimensioned clamps/brackets and fixed rack-root joints in saved scenes; exact cooked-property reports and `mechanical-screen-*` records. Finite retracted workspace probes:17 endpoints for AA/CA/AC,47 for BA/BC. Current occupied-screen002:4/5 AA/BA/CA/AC,3/5 BC. These evaluate rather than assume reach; fixture and seating failures remain visible. |
| §2.4–10: grasp, latch depression, axial withdrawal, controlled cable, original-socket realignment/insertion, release and retraction | Exact nominal package results and `continuous-{aa,ba,ca,ac,bc}001`:all five complete three cycles in one live scene. Measured retained initial/final states, helper disablement, full task phases, unchanged boundary poses and contiguous times checked again. Five systems work; AB/BB/CB pickup and CC datum failures remain nonfunctional. |
| §3 broad Cartesian discovery | `research/cartesian_robots.md`:igus XYZ, Festo EXCM, OpenBuilds screw modules, HIWIN guides/nested booms, Zaber stages, igus SLN, IAI modular robots, Lexium cantilevers and CoreXY. Commercial, open-source and hybrid options are compared. |
| §3 broad tool discovery | `research/grippers.md`:EGP, EHPS, RG2/2FG alternatives, Hand-E/2F assets, SMC LEHZ and custom connector-specific/compliant tooling. Standard jaw grasp is explicitly distinguished from latch release. |
| §3 level2.1–3: documentation/drawings, CAD availability, GitHub/Isaac implementations | Manufacturer links/dimensional tables; downloaded and revision-bound OnRobot, Robotiq, OpenBuilds and SCHUNK repositories. Actual RG2 USD imported unscaled. SCHUNK's generic EGP mesh is rejected as unverified EGP25 CAD. CAD offered behind a portal is not represented as downloaded/licensed. `sources_and_licenses.md` and `source_review001.md` retain provenance and retrieval limits. |
| §3 level2.4–8: articulation/control, components/controllers, variants, mounts, comparable connector work | Inspected vendor linkage/mimic drives; `rg2_geometry_verification001.json` checks2,175 samples. CoreXZ and rack/pinion probes establish their distinct coupling. `buildability_and_bom.md` covers guide/motor/brake/controller/actuator candidates and interface gaps. Narrow tips, longer/shorter stages, motor/force variants and adapters are evaluated. Reis full mechanism, constrained-cabling adaptation and accessible Gu metadata are distinguished in `rj45_mechanisms.md`; inaccessible drawings are not invented. |
| §3 level2.9–10 and research output | Dimensions, travel, payload, accuracy and force conventions are sourced per candidate; assembled-model measurements remain separate from catalog ratings. Rack fit, advantages/disadvantages, simulation support, links, licenses, verified partial prices and unknown complete costs are reported. `candidate_matrix.csv` preserves early selection; `current_candidate_matrix001.csv` identifies measured current outcomes. |
| §4: three substantially different implemented robots | A:dual-supported independently driven screw gantry. B:side lift and two separately driven nested horizontal members. C:two stationary coupled CoreXZ transmissions and short insertion stage; passive X/Z guide joints have no hidden position drives. Source, saved geometry and transmission/negative-control evidence establish mechanical—not cosmetic—differences. |
| §4 mechanical elements | Saved scene composition and `hardware-inventory-{aa,ba,ca,ac,bc}001` include rails/blocks, carriages, motors/drives, brackets/fasteners, hard bounds/stops, passive carriers, rack connection, estimated mass/inertia and collision shapes. `screw_guide_frame.md`, `telescoping_guide_frame.md`, `corexz_guide_frame.md`, `service_carriers.md` and exact cooked properties explain approximations. Actual prismatic joints/finite drives move the tool; no floating hand substitute. |
| §4 rack constraints | `buildability_and_bom.md`, exact mechanical/workspace/neighbor reports evaluate frame attachment, server interference, rear projection/door limits, neighboring cables, open-frame airflow/service access, reach, park/retraction, mount moments and assembly sequence. Rear-door-open operation and neighboring-rack overhang are limitations. No closed-door fit, airflow certification or bolt-strength rating is claimed. |
| §5 three end effectors and six capability checks | A:reference-envelope precision parallel tool with custom fingers/tongue. B:full-size articulated RG2 with custom shoes/tongue. C:fixed datum plus rack-driven moving pocket, independent tongue and bounded passive compliance. `grippers.md` explicitly considers body grasp, latch access, retained grip, withdrawal, reinsertion and neighboring cables for each. Full task, occupied-port and failed-feasibility evidence determine the outcome; a proposed capability is not scored as achieved. |
| §5 latch integrity and special-tool release | Spring-hinged baseline latch/socket colliders are retained. Five current unpressed-pull challenges resist transmitted loading; disabled-latch controls never unlock. Matched release reveals AC/BC guide-pocket contact after jaw opening. That free-space release failure is preserved; normal seated release/lateral clearing succeeds separately. No collar removal, connector pose override or hidden retention joint manufactures a pass. |
| §6 all compatible combinations and modular interfaces | All nine assembled and physically attempted, with realistic adapter/attachment layers and shared Cartesian/gripper interfaces. All nine current outcomes reproduce on fresh load, including four failures. All have saved scenes/results and current diagnostic or working media. Earlier versions and rejected attempts remain preserved. |
| §7 all twelve task stages | `controllers/rj45_task.py` and recorded events implement initialize, approach, align, grasp, release latch, withdraw, separate, realign, insert, seat/latch, release tool and retract/park. Current C/A events explicitly contain every stage; specialized datum/seating phases extend rather than replace the sequence. Retention and helper state are checked at cycle boundaries. |
| §7 control, feedback, faults/recovery and physics integrity | Joint targets and CoreXZ generalized efforts, bounded smooth trajectories, measured pose/aperture/hook feedback, collision reporting, finite retries and aborts. Grasp/latch/insertion recovery has physical evidence in nominal/repeated and disabled-actuator cases. Every timed topology audit retains dynamic connector/cable bodies and active colliders while disabling baseline hand/press helpers. Render-only pose replay is never task evidence. Ground-truth observations are explicitly not perception. |
| §8 feasibility and randomized counts | `benchmark-summary021.json` (AA/BA/CA),018(BC),019(AC):24 declared starts and22 valid trials per working design. Full cycles22/22,22/22,22/22,17/22,21/22 respectively; each also has two fixture failures, retained in the24-start denominator. Failed designs have feasibility diagnostics, not fictitious successful cohorts. |
| §8 all variation categories and common conditions | Frozen plans vary initial robot/calibration offset, connector position/orientation, cable yaw/bend, approach timing, friction/contact offset and ports1/4/8/12/16. Plans, seeds, conditions, harnesses, process states and raw outcomes are preserved. A/C's separately revised seating harness is disclosed; results compare systems and are not pooled as hardware-only causal effects. |
| §8 all requested metrics and ranking | Per-trial records/summaries cover unplug, replug and full-cycle rates, timing, measured alignment, contact/impulse peaks, cable displacement, hook/latch reliability, finite coverage, stability and buildability. Separate calibrated480 Hz momentum estimates and D6 threshold probes address nominal cable loads with explicit measurement scope. `comparison005` implements35/45/55 sensitivity around the45/20/10/15/8/2 rubric. All2,645 input hashes checked again; reliability, fit, compactness, buildability and physics dominate visual quality. |
| §9 four views and video outputs for every working combination | Gallery selection009:wide, rear, macro, side/isometric and synchronized edit for each of AA/BA/CA/AC/BC:25 accepted working clips. Four current failures have labeled diagnostic videos. Every clip binds its tested trajectory/environment and replay sources; phase cuts preserve all frames and do not retime physics. |
| §9 renderer, quality, format and best showcase | Installed RTX renderer; native1080p30 H.264 for working presentations and native2560×1440/30 C/A four-view/showcase set. Acceptance001/002/003 bind24,400 frames,215 reviewed sheets/2,488 sampled frames, native latch details, timestamp/source checks and natural Mac playback. Obstructed B/C rear/edit were replaced, not relabeled. Review008 accepts the four failures only as diagnostics. No claim of exhaustive manual native-frame inspection. |
| §10 all environments and required contents | `preservation-audit022.json`:83 packages,83 independent loads,80 declared outcomes reproduced. Three historical discrepancies AA006/BA001/CA005 remain explicit. All nine current packages reproduce their declared outcome. Package hashes cover assembly, tool/rack/cable/socket composition, physics/controller config, camera definitions, parameters/initial conditions, launchers, results and measured trajectory. Shared references avoid duplicating the rack. |
| §10 dependency recovery and no temporary references | Fresh `dependency-inventory002`:83 environments,8,510 files,11,423,448,523 bytes, with layer/asset resolution and content hashes. `/workspace` and pinned `/isaac-sim` layouts/runtime/driver prerequisites, NVIDIA archive URL/hash and licenses are documented. This is a recoverable dependency index, not a standalone portable USD or tested new-machine installer. |
| §11 gallery fields and comparison/download workflow | Gallery011 contains architecture/tool names, screenshots, hardware references, descriptions, exact success/failure, current and historical statistics, downloadable playable media and every version's scene/config/result/command links. Filters compare nine designs. Accepted media, scores and new physical diagnostics remain distinct. Mac QA001 passes865 served hashes,29 play/seek checks, filters, evidence/acceptance labels, images and desktop/mobile layout, with no browser errors. |
| §11 security/remote access | Existing private artifact server and SSH tunnel only, no new/public hosting. `scripts/connect.sh` reuses the live tunnel. Actual gallery bytes and playback are checked through `127.0.0.1:18080`; original noVNC/RTX feeds are separate. Browser Blob loading supports seeking without replacing the supervised HTTP server. |
| §12 phases1–7 and checkpoints | `../PROGRESS.md`, research history, immutable baseline,83 versions, benchmark campaigns, render/review records, gallery snapshots and this delivery review preserve the complete progression. `REPRODUCE.md` supplies exact VM/runtime, per-version, reload, benchmark, render, gallery, diagnostic and extension commands, including the final1440p showcase settings. CLI help checks cover17 guide scripts and9 launchers; actual historical runs/reloads verify the applicable workflows, not merely parser success. |

## Final deliverables (§13)

1. Hardware research: Cartesian, gripper, RJ45, license, BOM and source-review
   reports above, including explicit assumptions and unverified procurement facts.
2. Three implemented architectures: A screw, B nested boom and C coupled CoreXZ.
3. Three implemented tools: precision parallel, official RG2 and specialized RJ45.
4. Nine tested combinations, all retained; five current nominal passes/four fails.
5. Five autonomous systems and three continuous no-reset cycles each.
6. Shared frozen benchmarking framework;110 current valid randomized trials,
  120 total starts, complete outcome metrics and conditional intervals.
7. 83 independently loaded environments with exact recoverable dependency index.
8. 25 accepted working presentations and four reviewed failure diagnostics.
9. Native1440p C/A showcase selected on the leading reliability tier, speed and
   mass—not its negligible score difference from AA.
10. Gallery011 built and Mac served-byte/playback/browser QA passed.
11. `research/current_design_comparison.md`: ranked practical recommendation,
    exact versions/dimensions, part references, verified partial costs and
    unknown totals; CA showcase, AA independent-axis prototype comparison,
    AC lower nominal cable-peak development alternative.
12. `REPRODUCE.md`, all version launchers and working scripts/tests support
    reproduction/modification/extension; local file-link check passes.

## Limits that remain results, not undisclosed passing claims

- Four current designs fail feasibility. No successful RG2 manipulation is
  inferred from an earlier lighter or differently controlled version.
- All five current power-loss probes fail at least one gate. No real machine
  is certified for unattended operation, emergency stopping or live equipment.
- Neighbor screens restrain neighboring housings and use free-ended cables;
  finite retracted rasters are not full loaded rack coverage or installed routing.
- Tool C opening alone is not free-space release; normal after-seating clearing
  is separately demonstrated. Failed challenges never add reliability samples.
- Cable-force diagnostics are nominal simulation estimates, not randomized
  load distributions, material-damage limits or two-ended cable safety.
- CAD/license/price/interface unknowns, actuator thermal limits, belt mechanics,
  perception/calibration and complete fabrication details remain explicit.
- The user's separate two-rectangle viewer report remains unreproduced and
  unresolved; the comparison gallery does not claim to fix that client view.

The plan requests a comparative reusable simulation laboratory and explicitly
requires preserving unsuccessful designs and unresolved limitations. These
adverse findings therefore stay in the delivered research; they are not removed
or silently expanded into promises of qualified hardware.

## Closure evidence identities

- Gallery011 manifest SHA256:
  `958d56b56885d9c0d14f090633bbb9edb524c6e705c5b4c58fae7a47ce6e2d55`;
 865 allowlisted files. Builder SHA256
  `401544e9400dea0b6caa6f4a9ca3a424abd72f47ab45b8c31219d9fa3f4c2127`;
  selection009 SHA256
  `dd92c8d0cc8fa4faf5c942015dbe4055320beb43aa394c6296cddfd7d00ab4ad`.
- Mac QA001 `../artifacts/robotics-gallery011-macqa001/report.json` SHA256:
  `3d9d5406d706d48299fb2a52eb65f6295d7d977beca1e9f014e58e9b079ede21`.
 865 published hashes,29 play/seek checks, no browser errors. These served-byte
  and UI checks complement—not replace—the bound physics/media review above.
- Fresh dependency-inventory002 `inventory.json` SHA256:
  `bd69d8102921394de945055e139f37d10c4f895debd7a8dc8ff185cb21e22a86`.
 83 environments,8,510 files/11,423,448,523 bytes; independently resolved on VM.
- Preservation-audit022 SHA256:
  `3615099902779737c7a260144db43dc545bceb0a7f6553c63fcbdddba8365d48`.
- Software suite:398 passing tests in
  `../artifacts/logs/p2-final-gallery-tests001.log`; targeted gallery/physical/
  release suite40/40 on both VM and Mac after the new gallery integration.
- `../artifacts/robotics-gallery011-visual001/`:desktop introduction, physical
  challenge section on desktop/mobile, loaded C/A accepted-design and A/B
  failed-design cards personally inspected. The first C/A screenshot was taken
  before its lazy image loaded; corrected `showcase-card-loaded002.png` is the
  inspected loaded image, not a silently replaced screenshot.
- Final local Markdown target check:93 existing targets across root README,
  robotics README/REPRODUCE/FINAL_AUDIT/DELIVERY_AUDIT/current recommendation/source review;
  no missing file targets. This is not an external-web availability guarantee.
- Existing Docker mappings verified:6080/8080 bind host127.0.0.1 only. Mac
  16080/18080 are the existing loopback SSH forwards; no service was replaced.
