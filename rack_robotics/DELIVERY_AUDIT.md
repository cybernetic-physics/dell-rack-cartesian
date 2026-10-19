# PLAN_p2 development audit — superseded by final review

The requirement-level [FINAL_AUDIT.md](FINAL_AUDIT.md) closes this development
checklist after Gallery011's865-file/29-video Mac QA, terminal physical
challenge integration, fresh83-environment dependency closure and final
documentation checks. The checkpoint text below is retained as history,
including what was still open at the time. No failed experiment was reclassified.

Checkpoint: 2026-10-17. Gallery010 integrates the accepted media,1440p
showcase, recommendation, nominal force comparison, licenses and bound
presentation evidence. MacQA001 verifies851 served-file hashes,29 video
play/seek checks, acceptance labels/links, score/load values, filters and
desktop/mobile layout with no browser errors. Gallery009 remains intact.
A/A and C/A's ten required clips
now have combined presentation acceptance in `presentation_acceptance001.json`:
full-frame technical screening/timestamps, all phase/time review sheets, native
latch-detail inspection and natural Mac playback. Acceptance002 adds the five
corrected B/C clips after53 sheets/601 samples and eight native macro frames.
Review008 accepts four failed-design videos only as labeled diagnostics.
Acceptance003 adds all ten B/A and A/C clips after94 sheets/1,088 samples and15
native macro frames. All25 selected working clips now have combined acceptance;
the previous B/C rear and dependent edit are rejected for foreground occlusion.
This is a working requirement/evidence map, **not a
completion certificate**. It retains the original scope of `../PLAN_p2.md`.
An existing report or passing codec check is not automatically sufficient for
the broader requirement. Final completion still needs the open evidence below
and a fresh examination of every referenced input.

## Final deliverables (§13)

| Required deliverable | Current authoritative evidence | Assessment / remaining work |
|---|---|---|
| 1. Comprehensive hardware research | `research/cartesian_robots.md`, `grippers.md`, `rj45_mechanisms.md`, `sources_and_licenses.md`, `buildability_and_bom.md`; locally retained vendor repositories/papers | Broad and second-level investigation are present, including actual Reis mechanism and rejected asset/size assumptions. Catalog facts, proposed geometry and unknowns are distinguished. Final source-by-source review remains part of closing this audit. |
| 2. Three distinct robot architectures | Current A dual-supported screw, B independently driven nested booms, C coupled CoreXZ; frozen environment sources and exact-package mechanical reports | Implemented and tested. Distinction is mechanical, not color/appearance. Model drive/transmission and manufacturing assumptions remain explicit. |
| 3. Three end-effectors | Precision parallel with custom tips/latch tongue; full-size official RG2 linkage; specialized rack/pinion datum-jaw with passive compliance | Implemented. Current RG2 combinations fail; failure does not erase implementation or become success. |
| 4. Comparative compatible configurations | All nine current versions in `research/current_candidate_matrix001.csv`, comparison005 and preservation-audit021 | All nine assembled and tested; five current nominal passes, four failures. Historical screening matrix is retained separately. |
| 5. Functional autonomous manipulation | Exact current AA/BA/CA/AC/BC packages, fresh reloads, benchmark007/008/009 controls, continuous-{aa,ba,ca,ac,bc}001 | Five nominally functional systems. Each also completes three cycles in one live world without reset/re-seating; current reliability remains conditional on valid fixture starts. |
| 6. Automated benchmarking with reliability | Frozen plans/harnesses, summary021 (AA/BA/CA),018 (BC),019 (AC), comparison005; cable_force_comparison001 | 24 declared starts and22 valid trials per working design; raw failures retained. All required perturbation fields exist. Separate nominal axial-reaction traces now cover all five; no randomized force distribution or hardware-safe load pass is claimed. |
| 7. Independent reloadable environments | preservation-audit021:83/83 independent scene loads,80/83 declared outcomes; dependency-inventory001 | Scene-load requirement has evidence for all83. Three historical outcome exceptions stay visible; no claim that all83 reproduce their declared task. Restore/reload commands and exact runtime/dependencies documented. |
| 8. Photorealistic multi-angle videos / diagnostics | Current wide/side render003/004, improved rear/macro views, revised1080p edits, failed-render001; acceptance001/002/003, review008 and gallery010 | Four full-cycle views and edits for all five working designs have combined acceptance:25 clips,24,400 frames,215 sheets/2,488 samples. All four failed-design diagnostics are reviewed. Gallery010 exposes the accepted selection and bound evidence; historical rejected views remain preserved. |
| 9. Polished higher-resolution best showcase | C/A selected on equal leading observed reliability, shorter cycle and lower mass; `showcase-campaign001`, gallery009, presentation_acceptance001 | Native1440p four-view batch and edit accepted on combined all-frame technical and systematic visual review, plus native latch detail and natural Mac playback. Coverage is explicit; no exhaustive manual native-frame inspection is claimed. Final gallery must carry the bound acceptance record. A/A1440macro002 is not a substitute. |
| 10. Secure remotely accessible gallery | gallery010 and MacQA001:851 file hashes,29 video play/seek checks, acceptance labels/links, displayed score/load values, filters, images, desktop/mobile layout | Private SSH-tunnel gallery includes accepted media, licenses, recommendation and force evidence. **Open:** final narrative/document closure and the final audited snapshot; no new public service required. |
| 11. Ranked recommendation with dimensions/cost/parts/tradeoffs | comparison005 with2,645 verified inputs; `research/current_design_comparison.md`, exact hardware inventories, supplier_costs001 | Numeric ranking and practical AA/CA tie are documented. Verified component subtotals are not complete-system prices. Unknown totals/interfaces remain explicit; no unsupported cost range or hardware safety claim. Final delivery must bind the accepted media/evidence snapshot. |
| 12. Reproduction/modification/extension documentation | `REPRODUCE.md`, version launchers, source manifests, pinned Docker runtime, baseline/dependency manifests, test suite | Operational commands exist for all9 current packages and continuous cycles, benchmark, render, verification and extension. **Open:** command/link review against the final snapshot and full requirement closure. |

## Engineering and experimental requirements (§§1–8)

### Existing environment and baseline

The original rack, contact-driven latch and36-link cable are retained as
`assets/shared_rack/baseline-001`; robot code is a separate extension. The prior
baseline fresh-session test passes121 checks. Existing VM, container, GPU
runtime and private desktop/tunnel are reused. None of the new camera or
benchmark work replaces the live row GUI. Its separately reported rectangle
display issue is still unreproduced and is not claimed fixed by this audit.

### Research and mechanical realism

The reports cover Cartesian/gantry, modular stage, telescoping and coupled-belt
options; commercial precision/adaptive tools and connector-specific mechanisms;
manufacturer dimensions/forces/travel, CAD/license findings, interface/motor/
guide/controller choices, derivative alternatives and rack-fit limitations.
Exact asset rejection matters: generic SCHUNK meshes were not labeled EGP25;
RG2 was not rescaled to fit. Missing quotes/CAD grants/full paper details are
explicit rather than invented. The current CSV and narrative distinguish the
initial candidate screening priorities from measured current outcomes.

Saved models include rack clamps, guides/blocks, motors, screws or belt coupling,
limits, carriers, adapter geometry and masses/inertias. Exact-package property
queries and recorded-motion screens measure geometry, moving/total mass and
gravity moments. These are not FEA, individual fastener loads or purchased-
hardware ratings. Manufacturing gaps are limitations to the recommendation,
not permission to claim a fabrication-ready machine.

### Mounting, reach, surroundings and failure

Workspace probes cover finite unloaded retracted paths: AA/CA/AC17 endpoints,
BA/BC47. Occupied-screen002 has25 planned starts: AA/BA/CA/AC4/5 complete and
clearance-passing, BC3/5; all five port8 fixture starts fail, and BC also fails
port16 seating. The20 timed cases report no robot/target–neighbor contact.
The fixture restrains neighbor housings and uses free-ended cables; it is not
a full-density installed-routing result.

Overhang, rear-door-open operation, neighboring-rack occupation, parking,
mount moments, assembly/service access and airflow limitations are documented.
None of the five current power-loss probes passes every gate. These adverse
findings remain in scoring and recommendation; a powered nominal pass does not
establish unpowered safety or a closed-door installation.

### Task controller and physics integrity

The shared interface executes initialization, approach/alignment, grasp,
latch release, axial withdrawal, visible separation, realignment/insertion,
seating/latching, tool release and parked retraction. Specialized tools add
datum and bounded seating states, without replacing the core Cartesian system.
Recovery/error evidence covers grasp, latch and seating failures; the preserved
failed designs and all failed randomized starts remain available.

The measured-state observer does not actuate the plug. Initialization helpers
are disabled before timing; robot/gripper joint commands move the housing and
spring-hinged latch through contact. Topology, source and motion checks support
this claim for tested trials. Renderer pose writes exist only in explicitly
nonphysical replay layers; those layers are never task-success evidence.
Baseline latch negative controls are present. `actuator-controls001` is terminal:
all15 normal/interlock cases across the five working designs pass their separate
diagnostic gates. All177,063 physics-step samples, frozen sources and actual
process exits reverify identically on VM and Mac. All five normal trajectories
match every30 Hz frame of their earlier continuous first cycles. Every negative
case suppresses three requests, exhausts two recoveries, stays retained and
stops without withdrawal; ordinary task success remains false. See
`research/actuator_interlocks.md`. A controller refusing withdrawal is not proof of physical
retention under an imposed pull, nor of open-tool inability to drag a released
connector. `research/causal_coverage_audit001.md` maps the explicit research
requirements to existing evidence: baseline5 N retention does not replace
current-tool imposed-pull/open-jaw challenges. Those challenges are now terminal
with the preserved counterevidence below, not reclassified to manufacture success.
`physical-controls001` is terminal: all127,722 raw480 Hz samples reverify on
VM/Mac with byte-identical verification001 reports. Five nominal and five
unpressed-pull diagnostics pass; AA open-transport passes; BA/CA fail axial
motion gates after release/free-fall; AC/BC stop at insufficient opening.
All original failures remain. Exact normal trajectories match earlier first
continuous cycles. `research/physical_challenge_results001.md` documents the
evidence and the exact legacy fast-shutdown zero-on-failure exception; a zero
exit never promotes a failed physical verdict. Future runners supply status
inside app.close. Frozen original code/results remain unchanged.

`matched-release001` is terminal: six diagnostic passes and four failures,
68,388 physics-step samples reverified on VM/Mac. Every pre-intervention pair
matches exactly. AA/BA/CA housing paths are equal under hold versus motion;
AC/BC's open guide pockets keep physical contact and carry the housing about
40 mm. Open aperture is not disengagement for tool C. The nominal controller's
seated release/lateral clearing remains separately valid; arbitrary free-space
release is unsupported. See `research/matched_release_results001.md` for gates,
contact evidence and hashes. Reports differ only by one ULP in one pair distance;
all verdicts/inputs agree. Real failure exits are now1. Current full local
suite398PASS is software evidence, not a substitute for these physical cases.

Continuous-cycle boundaries verify retained poses and inactive helpers, exact
final-to-next-initial measured-state equality and contiguous global time. This
supports three nominal cycles per system, not indefinite unattended operation,
real perception/calibration or independent statistical samples.

### Experimental metrics and scoring

The plans vary robot/calibration and connector pose, cable yaw/resting routing,
approach timing, friction/contact assumptions and target port. All five working
designs have at least20 valid trials and separately reported fixture failures.
AA/BA/CA22/22, AC21/22 and BC17/22 are conditional rates; all-start denominators
remain24. Campaign009's changed seating harness prevents hardware-only or
cross-harness pooled causal conclusions.

The reports include unplug/replug/full-cycle counts, timing, measured alignment,
latch clearance, contact failures and per-phase collider-pair impulse/dt peaks,
cable displacement, stability, finite-path coverage and buildability context.
Contact impulse/dt is not calibrated actuator effort or cable tension.
The geometry screen cannot infer tensile force from a nearly straight
free-ended chain or tiny D6 anchor gaps. Subsequent work in
`research/cable_constraint_load.md` validates ordinary-D6 force-threshold
events against 12 known gravitational-load controls. A separately labeled
full-rack threshold screen records C/A crossings at1 N during initialization
and5 N during grasp, and a successful low-threshold event/abort control. All five
working designs now have nominal5 N coverage: AA/BA/CA cross during grasp,
AC/BC complete without crossing. AA/BA/CA complete at25 N with recorded motion
identical to their earlier first continuous cycles. This measures resultant
constraint-load crossings, not axial tension or material safety.

`research/cable_momentum_measurement.md` now supplies a separate, read-only
480 Hz axial-reaction estimate using all normal/friction impulses and distal
momentum balance. Nine known-behavior calibration gates pass; all five nominal
full-rack cycles finish and every force sample is recomputed on both VM and Mac.
The machine-readable `cable_force_comparison001.json` binds source/trace hashes,
threshold durations and exact recorded-motion comparisons. AA/BA/CA peaks are
8.75/10.04/13.44 N, with5 N exceeded for one2.08 ms step each; AC/BC peaks are
0.83/1.11 N. The recommendation now includes this lower nominal peak versus
reliability tradeoff for tool C. This is meaningful nominal force evidence,
not a calibrated material-damage model, a randomized force distribution, or a
two-ended installed-cable safety pass. Final evidence/gallery integration and
the final requirement-level review remain open.

The predeclared reliability/rack-fit/compactness/buildability/physics/visual
rubric and35/45/55 reliability sensitivity retain all9 designs. CA–AA's tiny
numeric difference is treated as a practical tie. A score adapter's
`complete_evidence` flag covers its own declared inputs, not this whole plan.

## Visual, preservation and delivery requirements (§§9–12)

For each working design, final acceptance must inspect the full actual cycle
from wide rack, rear manipulation, macro latch and side/isometric views; verify
lighting/material readability, cable motion, lack of clipping/flicker/noise and
useful composition; then verify the synchronized edit. Native resolution must
be at least1080p,30fps H.264, with the best-design showcase at higher resolution.
Current frame-exact editors preserve all source frames and never mix different
physical trials or upscale mismatched camera inputs. Sampled frames alone are
not complete temporal acceptance. The combined review adds all-frame decoding/
coarse metrics and every encoded timestamp, source trajectory checks and full
natural Mac playback. `temporal-review001` covers25,734 frames/30 clips; all233
inspection sheets are preserved, with only the explicitly recorded subsets
claimed visually reviewed. `inspection_review004` covers27 C/A sheets/312 samples
and seven original macro frames; `inspection_review005` covers41 A/A sheets/487
samples and three additional original macro frames. `presentation_acceptance001`
accepts these ten videos on the combined evidence, not a claim that every
native-resolution frame was manually inspected. Reviews006/007 add all53 B/C
sheets/601 samples and eight original macro frames; acceptance002 accepts its
corrected five-clip set. VM temporal002 verification002 also passes after later
playback evidence, without modifying the frozen review. Reviews009/010 cover
all94 B/A and A/C sheets/1,088 samples and15 native macro frames; acceptance003
accepts their ten clips on the same combined evidence. All25 accepted working
clips' video/source/review/sheet/playback bindings reverify locally, including
verification-report identities. Review008 inspects all five diagnostic sheets for
the four failed designs and accepts them only as labeled failure footage.

Failed designs retain labeled diagnostics. Historical versions, reports and
failed render/checker attempts are not overwritten to manufacture completion.
The83 saved environments preserve source/configuration/cameras, rack/tool/cable
composition and outcomes. The three historical declared-outcome exceptions are
AA v006, BA v001 and CA v005; each loads, but its task/outcome/source evidence has
an explicit validator discrepancy. Dependency closure records8,510 files and
the pinned installed OmniPBR/runtime dependency, not a fictional portable scene
file without its shared/vendor assets.

The final gallery must expose design names, hardware references, representative
screenshots, honest outcome/current statistics, accepted downloadable videos,
versioned USD/reproduction links and the recommendation. Its current private
server has no byte-range support, so user-requested Blob loading enables seeking
without replacing the supervised service. Final QA must bind the actual served
bytes and inspect desktop/mobile presentation. Reproduction documentation must
continue to distinguish one-cycle frozen launchers, separately frozen harness
diagnostics, measured replay and the live baseline GUI.

## Next closure work

Current audit checks added2026-10-17: preservation-audit022 rechecks current
package/result hashes and historical independent-load/dependency evidence for
all83 versions (80 reproduced declared outcomes, the same three exceptions).
SHA256 `3615099902779737c7a260144db43dc545bceb0a7f6553c63fcbdddba8365d48`.
All2,645 comparison005 input bytes still match. Actual `--help` checks pass
for16 reproduction-guide scripts and all9 version launchers; this checks entry
points, not fresh execution of every documented workflow. Local links in
REPRODUCE/README/current_design_comparison/source_review001 total72, none
missing. `research/source_review001.md` records primary catalog/paper/price
rechecks and vendor revisions, with the RG2 HTML redirect explicitly retained.
These checks advance closure but do not by themselves certify the entire plan.

1. Gallery010 completes accepted-media/evidence integration and Mac QA. Keep
   it and earlier snapshots immutable. Finish source/narrative closure before
   the final audited snapshot: the frozen comparison narrative still contains
   earlier visual-review wording, and the C/A edit's selection description
   still calls it a candidate even though its explicit status is accepted.
   The source recommendation now explains historical scores without changing
   comparison005. Use a new selection/snapshot for final wording corrections.
2. Carry the new supported nominal force evidence and its explicit coverage
   limits into final delivery. Do not convert it into hardware-safe thresholds
   or pretend the historical randomized trials measured cable force.
3. Integrate the completed physical challenge controls identified in
   `research/causal_coverage_audit001.md`, including tool C's free-space-release
   failure, separate from normal-controller interlocks and randomized trials.
   Finish documentation/link and research
   source checks, then revisit every requirement above against authoritative
   artifacts. Gallery010 now includes sources_and_licenses.md; its earlier
   omission from gallery009 is no longer an open integration gap.
4. Only after all open requirements are resolved perform the final completion
   audit. No completion or blocked-goal claim is warranted at this checkpoint.
