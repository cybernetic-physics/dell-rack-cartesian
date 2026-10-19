# Reproduce and extend the rack robotics experiments

This is the operational guide for the existing VM, not a claim of a tested
fresh-machine installation. The original rack demo remains separate from the
robotics experiments. Do not replace its GUI, container, or shared assets to run
a headless robot trial.

## Separate nominal cable-force diagnostics

The [momentum-measurement report](research/cable_momentum_measurement.md) gives
the calibration and live-run commands. These read-only diagnostics use explicit
480 Hz velocity/contact-impulse samples and the original free-ended D6 cable.
They are not retroactive force measurements for the randomized cohorts, nor
hardware-safe load ratings. The five `cable-force-{aa,ba,ca,ac,bc}001` directories
retain raw gzip traces, calibration, source and per-phase summaries.

To verify and regenerate the five-design summary from collected evidence,
run from the repository root using a new output filename:

```bash
.venv/bin/python -m rack_robotics.scripts.summarize_cable_force \
  --experiments rack_robotics/experiments \
  --output rack_robotics/research/cable_force_comparison-NEW.json
```

This recomputes every force sample, checks frozen-source/calibration hashes,
reports threshold-exceedance durations and compares every recorded nominal
frame with the first corresponding continuous cycle. It never changes the
historical reliability denominators or rubric scores. Its thresholds are
descriptive (1, 5, 10 N), not acceptance limits supplied by a manufacturer.

## Actuator-disabled interlock diagnostics

These are separate from randomized reliability and from physical forced-pull
tests. The normal shared controller is unchanged. A wrapper repeatedly delivers
the existing open-jaw or retracted-latch command instead of the requested action;
real aperture, plug pose and hook-clearance observations are never overridden.
All optional tool properties (including compliant seating) pass through.

Inside the existing container, from `/workspace`, choose a new directory:

```bash
python3 rack_robotics/scripts/screen_actuator_controls.py \
  --output rack_robotics/experiments/actuator-controls-NEW --workers 2
```

This predeclares15 cases across AA v016, BA v014, CA v021, AC v005 and BC v004:
one matched normal cycle, one permanently disabled latch command, and one
permanently open grasp each. Every case runs once; no failed case is retried or
counted as a new reliability trial. `state.json` includes actual child PIDs and
exit codes; an observation timeout is not permission to restart a live case.

`results.json.passed` remains the ordinary task outcome. For a negative control,
the expected task failure must be distinguished from
`results.json.actuator_interlock.passed`. That latter verdict requires three
suppressed requests, two exhausted recoveries, the expected terminal phase,
actual blocking aperture or retracted latch/no hook clearance, no withdrawal,
continued housing retention and intact physics/contact/carrier evidence.
`actuator_trace.jsonl.gz` records the real state at every480 Hz task step.
This checks controller interlocks; it does **not** establish retention force or
prove an open tool could never drag the connector if withdrawal were forced.

After every process is terminal, recompute the trace gates and verify frozen
sources, process exits and matched normal recorded motion (Mac or container):

```bash
.venv/bin/python rack_robotics/scripts/screen_actuator_controls.py \
  --output rack_robotics/experiments/actuator-controls001 --verify-only \
  --reference-experiments rack_robotics/experiments \
  --report rack_robotics/experiments/actuator-controls001/verification_mac_NEW.json
```

Use `python3` instead of `.venv/bin/python` inside the container and a different
new report filename. The recorded-motion comparison checks all30 Hz samples
against each earlier first continuous cycle, not every physics-step pose.
The campaign retains its original `screen_source.py` and all frozen trial code;
the verification report separately identifies the current verifier source.

Campaign001 is terminal: all15 diagnostic verdicts pass; the ten negative
cases remain task failures. VM/Mac reports001 are identical and recompute
177,063 physics-step samples. [Results and limits](research/actuator_interlocks.md).

## Physical pull and open-tool transport challenges

These are diagnostic actuator requests, not normal-controller interlock tests.
Read the [predeclared protocol](research/physical_challenge_protocol001.md).
The unchanged nominal cycle is paired with a5 N-capped unpressed pull after
grasp, and further transport after normal extraction followed by jaw opening.
The latter starts clear of the socket, preventing relatching from confounding
the ineffective-grasp observation. No connector poses or collision settings
are overridden. Every case retains the existing saved geometry/controllers.

Inside the existing container, from `/workspace`, use a new output directory:

```bash
python3 rack_robotics/scripts/screen_physical_controls.py \
  --output rack_robotics/experiments/physical-controls-NEW --workers 2
```

The campaign freezes15 cases, exact package/source/condition identities, the
protocol and the existing passed contact-convention calibration before launch.
`state.json` records live child PIDs and terminal exits. Do not restart a live
case merely because a monitoring request times out. All outcomes are preserved.
Campaign001 is terminal: five nominal and five unpressed-pull diagnostics pass;
AA open-transport passes, BA/CA fail axial-motion gates, AC/BC never reach
transport because opening is insufficient. [Terminal interpretation and
hash-bound evidence](research/physical_challenge_results001.md) retain all four
failures. All127,722 samples reverify identically on VM/Mac.

`physical_trace.jsonl.gz` records every480 Hz step, including normal and
friction impulses grouped by the actual actor/collider pair. The diagnostic
requires measured transmitted pull contact, not merely a changed drive target.
For open-tool transport it requires actual tool motion without corresponding
housing transport. Force estimates are contact impulse/dt, not motor torque,
manufacturer-rated capacity or a hardware-safe load threshold.

Only nominal cases may pass the ordinary complete-cycle task. Challenged cases
have `passed:false`, `full_cycle_attempted:false`, and a separate
`physical_challenge.passed` verdict. They never enter reliability denominators.
After every case is terminal, verify on VM and Mac using new report filenames:

```bash
.venv/bin/python rack_robotics/scripts/screen_physical_controls.py \
  --output rack_robotics/experiments/physical-controls001 --verify-only \
  --reference-experiments rack_robotics/experiments \
  --report rack_robotics/experiments/physical-controls001/verification_mac_NEW.json
```

Use `python3` inside the container. Verification recomputes all raw trace gates,
checks source/process hashes and compares nominal30 Hz poses against each
earlier first continuous cycle. A delivered diagnostic with counterevidence
remains failed; missing preconditions do not establish the expected negative.
This command intentionally exits1 for campaign001's failed diagnostics, while
writing a complete verification report. That is different from a verifier
exception. The exact legacy runner's fast-shutdown zero-on-failure is annotated,
not treated as diagnostic success; future runners supply status to app.close.

### Matched open-command follow-up

Read [matched_release_protocol001.md](research/matched_release_protocol001.md).
The two cases per design share normal extraction and2 s of opening, then either
hold position or request40 mm further withdrawal. An insufficient aperture is
recorded as FAIL without suppressing the bounded request. Pairwise evidence
checks exact pre-intervention matching and all subsequent housing positions;
free-fall/bounce is not equated with tool-driven transport.

```bash
# Inside the existing container, new directory only:
python3 rack_robotics/scripts/screen_physical_controls.py \
  --suite release --output rack_robotics/experiments/matched-release-NEW --workers 2
# After all cases are terminal, on Mac (python3 inside container):
.venv/bin/python rack_robotics/scripts/screen_physical_controls.py \
  --output rack_robotics/experiments/matched-release001 --verify-only \
  --report rack_robotics/experiments/matched-release001/verification_mac_NEW.json
```

The existing matched-release001 campaign is terminal: six cases pass and four
C-tool cases fail because open guide geometry still supports/carries the
housing. All68,388 samples and exact pre-intervention pairs reverify on VM/Mac;
the reports differ only by one ULP in one distance, with identical gates and
verdicts. See [matched results](research/matched_release_results001.md).
Verification intentionally exits1 for the failed diagnostics. No automatic
retry replaces a failed case. Campaign001 remains unchanged.

## Temporal video review

Inside the existing container, decode all selected videos and generate review
sheets into a new directory; existing media are read-only inputs:

```bash
python3 rack_robotics/scripts/screen_video_temporal.py \
  --selection rack_robotics/gallery/media007.json \
  --output artifacts/temporal-review-NEW
python3 rack_robotics/scripts/verify_video_temporal.py \
  --input artifacts/temporal-review-NEW \
  --output artifacts/temporal-review-NEW/verification_vm001.json --timestamps
```

The screen requires ffmpeg/ffprobe and Pillow (already installed on the VM).
It decodes every frame at480x270, excludes the bottom caption band from coarse
metrics, checks native codec/dimensions/frame count, and makes1 Hz plus every
phase's first/middle/last inspection sheets. Macro action phases additionally
receive10 Hz samples. The verifier's `--timestamps` checks every encoded
presentation time, not just average frame rate. The metric/flag thresholds are
review cues, not automatic visual acceptance or physical correctness gates.

Wait for both commands to finish before downloading their entire output
directory. On the Mac, with the referenced source/video files also present:

```bash
.venv/bin/python rack_robotics/scripts/verify_video_temporal.py \
  --input artifacts/temporal-review001 \
  --output artifacts/temporal-review001/verification_mac_NEW.json
```

Without `--timestamps`, this verifies stored metrics/flags, source and sheet
hashes and phase coverage; it is not an independent RGB decode or timestamp
probe. Actual visual decisions must separately record the frames/sheets viewed,
observations and scope. `research/presentation/inspection_review004.json`
records the C/A full-cycle sampled inspection and B/C foreground-camera defect.
The defective rear and dependent edit remain preserved; do not promote them
because they decode or play successfully.

For the corrected B/C rear/edit pair, use
`research/presentation/bc_lowerclear_selection001.json` as the selection and
another unused output directory. The completed evidence is
`artifacts/temporal-review002`; VM verification002 includes every timestamp
after the Mac playback reports were added. The verifier permits later valid
QA annotations while still checking immutable video/source/trajectory identity.
Never edit a frozen review manifest to make later QA evidence fit.

Presentation acceptance001 binds the ten A/A and C/A clips; acceptance002 binds
the five revised B/C clips; acceptance003 binds the ten B/A and A/C clips.
Reviews006/007 record all53 B/C sampled sheets and eight native macro frames;
reviews009/010 add all94 B/A+A/C sheets and15 native frames. All25 working
clips have combined technical/source/systematic-visual/playback acceptance.
Review008 separately accepts four failed-design diagnostics, without implying
successful manipulation. These decisions do not extend to the rejected B/C
camera/edit or the extra A/A1440p macro candidate. Preserve all older records.

## Runtime and files

Run simulation commands **inside the existing `dell-rack-sim` container**, from
`/workspace`. From the Mac, enter it using the existing VM:

```bash
gcloud compute ssh --zone us-central1-b isaac-g4-rtxpro6000x2-flex \
  --project project-512201fe-6308-4879-83c
sudo docker exec -it dell-rack-sim bash
cd /workspace
```

The persistent host directory is
`/mnt/stateful_partition/home/hadjiyiannis_3_gmail_com/dell-rack`.
The local Mac tree contains source and collected evidence; it is not a complete
copy of the large vendor asset pack or every original rendered PNG.

The runtime is Isaac Sim `6.0.1-rc.7+release.42383.32955d8d.gl`, not a final
6.0.1 release. `../infra/Dockerfile` pins its base image to:

```text
nvcr.io/nvidia/isaac-sim@sha256:783444c706538aa76cf5126e911ddc5e618779e6105305ad4af4260362a30aa9
```

Use `/isaac-sim/python.sh` for physics/rendering and
`/opt/rack-usd-tools/bin/python3` (usd-core 26.8) for file-only USD checks.
`rack_robotics/scripts/setup_usd_tools.sh` creates that isolated tool environment if missing;
do not install native modules on the noexec `/workspace` mount. The tested VM
has two RTX PRO 6000 GPUs and NVIDIA driver 580.95.05. Full native Kit plugins,
Python modules, shaders, and compatible GPU/driver are prerequisites.

`experiments/dependency-inventory002/inventory.json` freshly indexes all 83 saved
versions: 8,510 unique files, 11,423,448,523 bytes, with SHA-256 and restore
namespace/path for each file. This is a dependency index, **not an archive**.
It checks package hashes, the immutable baseline, shared assets, and the USD
layer/asset closure. Keep project files at `/workspace` and runtime files at
`/isaac-sim`; authored absolute paths have not been made arbitrarily relocatable.
Do not copy only one `scene.usda`: some versions compose earlier saved layers.
Retain every indexed dependency and the corresponding license notices.

The frozen baseline lives at `assets/shared_rack/baseline-001` (relative to
this guide). Its manifest includes exact hashes and vendor recovery metadata.
The NVIDIA datacenter archive can be recovered with the existing project script:

```bash
bash scripts/fetch_assets.sh
```

That command above is relative to `/workspace`, not `rack_robotics/`.
It resumes the download and checks the expected size and SHA-256
`4972d1a9726b36279d7c26531b4d0a084156b7d512f5340b6e1063a9cf458fd4`.
Its pinned URL is also in the baseline manifest. Custom robot/connector assets
and frozen source must be restored from this project, not that NVIDIA archive.
Read [sources and licenses](research/sources_and_licenses.md) before redistribution;
the private gallery does not confer permission to publish vendor assets.

To repeat the read-only closure check, choose an unused output directory:

```bash
/opt/rack-usd-tools/bin/python3 rack_robotics/scripts/inventory_dependencies.py \
  --audit rack_robotics/experiments/preservation-audit022.json \
  --asset-search-path /isaac-sim/kit/mdl/core/Base \
  --output rack_robotics/experiments/restore-dependencies001
```

The audit must cover every saved version. If new versions have been added,
generate a corresponding preservation audit first; do not remove versions to
make an older audit pass. File integrity does not prove physical task success.
The audit command is `python3 rack_robotics/scripts/audit_preservation.py
--output rack_robotics/experiments/NEW_AUDIT.json`; it summarizes existing
fresh-session evidence, not new physics execution.

## Continuous cycles without reset

Use the common harness for consecutive nominal cycles in one live world:

```bash
/isaac-sim/python.sh -u rack_robotics/scripts/run_benchmark_trial.py \
  --environment rack_robotics/environments/robot_c_gripper_a/v021 \
  --condition rack_robotics/experiments/benchmark-campaign007/plan/control.json \
  --output rack_robotics/experiments/manual-ca-continuous001 \
  --cycles 3 --allow-root
```

Choose an unused output directory. Only the task state is renewed between
cycles; physics and connector seating are not reset. Counts above one require
nominal control conditions and are excluded from randomized reliability.
The harness freezes its own task code separately from the saved environment's
low-level controllers, so this is a new diagnostic, not a reproduction of that
environment's original one-cycle launcher. Inspect `cycle_boundaries.json`,
`results.json`, `physics_integrity.json` and `carrier_metrics.json`, not just the
process exit status. [Measured repeated-cycle evidence](research/continuous_cycles.md)
includes all five current working designs' three-cycle runs.

## Run each saved configuration

Current versions at this checkpoint (all use 480 Hz physics):

| Design | Directory under `rack_robotics/environments/` | Nominal task outcome |
|---|---|---|
| A/A — dual screw / precision parallel | `robot_a_gripper_a/v016` | Complete cycle |
| A/B — dual screw / RG2 | `robot_a_gripper_b/v011` | Bounded initial pickup failure |
| A/C — dual screw / specialized RJ45 | `robot_a_gripper_c/v005` | Complete cycle |
| B/A — telescoping / precision parallel | `robot_b_gripper_a/v014` | Complete cycle |
| B/B — telescoping / RG2 | `robot_b_gripper_b/v007` | Bounded initial pickup failure |
| B/C — telescoping / specialized RJ45 | `robot_b_gripper_c/v004` | Complete cycle |
| C/A — CoreXZ / precision parallel | `robot_c_gripper_a/v021` | Complete cycle |
| C/B — CoreXZ / RG2 | `robot_c_gripper_b/v002` | Bounded initial pickup failure |
| C/C — CoreXZ / specialized RJ45 | `robot_c_gripper_c/v003` | Datum-alignment failure |

Each directory has `demo.py`, `scene.usda`, `config.json`, `manifest.json`,
camera definitions, frozen tested source, and original results/trajectory.
Use the chosen directory's launcher; it selects its own robot, tool, baseline,
saved scene, and physics timestep. For example, a fresh A/A session:

```bash
/isaac-sim/python.sh -u rack_robotics/environments/robot_a_gripper_a/v016/demo.py \
  --output rack_robotics/experiments/manual-aa-reload001 --allow-root
```

Substitute the table's directory to run any of the other eight designs and use
a distinct output directory. These launchers run headlessly and exit after the
task; they do not animate the original noVNC GUI. A failed design should remain
a failed experiment, not be counted as a successful reload cycle.

For an automated fresh-session execution **and** subsequent package/dependency/
outcome check, use the reload wrapper. It selects failure-reproduction validation
for saved failed designs automatically:

```bash
python3 -u rack_robotics/scripts/reload_environments.py \
  --environment rack_robotics/environments/robot_a_gripper_a/v016 \
  --environment rack_robotics/environments/robot_c_gripper_c/v003 \
  --output rack_robotics/experiments/manual-reload-batch001
```

Repeat `--environment` for other versions. The output contains child logs,
numbered checkpoints, `results.json`, `physics_integrity.json`, trajectories,
contacts, and `asset_validation.json`. Inspect `summary.json`; process launch
alone is not acceptance. Existing audit022 verifies 83 independent scene loads
and 80 reproduced declared outcomes. Three historical exceptions remain in that
audit; they are not silently relabeled. Do not edit a frozen package's config
merely to update its original `reload_verified` or trial-count fields: newer
evidence lives outside its immutable manifest.

## Randomized experiments

`evaluate_all.py` freezes the plan and harness, retains every declared condition,
excludes the nominal control from rates, and preserves failed fixture starts.
Each trial records its exact environment manifest and source hashes.

For a **new** A/A experiment with the current working harness:

```bash
python3 rack_robotics/scripts/generate_benchmark_plan.py \
  --seed 20261018 --count 24 \
  --environment AA=robot_a_gripper_a/v016 \
  --output rack_robotics/experiments/manual-plan001
python3 -u rack_robotics/scripts/evaluate_all.py \
  --plan rack_robotics/experiments/manual-plan001/plan.json \
  --designs AA --workers 1 \
  --output rack_robotics/experiments/manual-campaign001
python3 rack_robotics/scripts/summarize_benchmark.py \
  --campaign rack_robotics/experiments/manual-campaign001 \
  --output rack_robotics/experiments/manual-summary001.json
```

To reproduce an existing protocol, use its saved plan and `--harness-from`
pointing to that campaign when creating a **new** campaign. Do not assume the
working harness is the historical one. Campaigns007/008 share the older task
protocol;009 freezes the seating-aware A/C revision. Do not silently pool their
rates or older mechanical versions. Twenty-four declared starts do not guarantee
twenty admissible trials. Summaries report fixture-inclusive protocol success
and conditional manipulation success separately, with Wilson intervals.

On interruption, inspect the parent **and** recorded child PIDs in `/proc`/`ps`,
logs, and persisted results. A timeout while observing is not a stopped job.
Only after confirming no matching process remains, resume via the campaign's
frozen evaluator with `--project-root /workspace --resume`, the same plan,
design list, and output. Do not supply `--harness-from` on resume. An inherited
lock prevents concurrent evaluators while a simulation child is still alive.

## Render measured motion and view it on the Mac

Render an existing tested attempt; no second physics run or hand-authored plug
animation is needed. For example, four full-cycle views plus an edited sequence:

```bash
python3 -u rack_robotics/scripts/render_demos.py \
  --attempt AA=rack_robotics/experiments/a_a_cable_support001 \
  --camera-profile open-frame-v1 --gpu 1 --workers 1 \
  --output rack_robotics/experiments/manual-render001
```

The renderer saves source/trajectory/video hashes, body-pose and camera checks,
original PNGs, and 1920×1080/30 fps H.264 by default. For native higher resolution,
add `--width 2560 --height 1440 --render-subframes 32`. All four cameras retain
the requested native resolution through editing; mixed-resolution inputs are
rejected, not upscaled. Optional `--phase-cameras PATH.json` freezes phase-to-view
choices (for example `{"withdraw":"macro"}`) without dropping or retiming frames.
`--failed-diagnostics` preserves failed
attempts with explicit failure labeling. Full playback and human visual review
are separate from pose/hash verification. A captured frame or successful codec
check does not prove an unobstructed latch view or final showcase quality.

The preceding `open-frame-v1` command is a general development example, not
the final improved latch-camera selection. To recreate the selected C/A
four-view1440p showcase settings from its measured trial, use a new directory:

```bash
python3 rack_robotics/scripts/render_demos.py \
  --attempt CA=rack_robotics/experiments/c_a_cable_support001 \
  --camera-profile latch-inspection-v2 --gpu 1 --workers 1 \
  --width 2560 --height 1440 --render-subframes 32 \
  --phase-cameras rack_robotics/experiments/showcase-campaign001/phase_cameras_input.json \
  --output rack_robotics/experiments/manual-showcase-NEW
```

For exact historical renderer source, the original batch's `state.json`
retains every full capture command. Keep its frozen `source/` tree and explicit
`--baseline` path; change only the command's `--output` to an unused path.
Do not invoke the frozen batch orchestrator as if its nested source tree were
a new project root. The per-view commands already point to the proper frozen
`render_replay.py` and real baseline. Each selected clip's render manifest
records its actual camera/fill/subframe settings. The final B/C rear is the
separately lowered `b_c_rear_lowerclear_cycle001`, not the older batch rear;
selection009 and its acceptance records identify the exact sources for all29
selected clips. A new render still needs its own technical and visual checks;
reusing the physical trajectory does not confer inherited media acceptance.

From the Mac project root:

```bash
bash scripts/connect.sh
.venv/bin/python rack_robotics/scripts/check_video_mac.py PATH_TO_DOWNLOADED_MP4 \
  --full-playback --output NEW_PLAYBACK_REPORT.json
```

Keep the SSH tunnel open. The [private gallery011](http://127.0.0.1:18080/robotics-gallery011/)
contains25 accepted working clips, four reviewed failure diagnostics, both
terminal physical challenge campaigns and environment references. The
[delivery review](FINAL_AUDIT.md) records its Mac served-file/playback checks.
Gallery010 and older snapshots remain unchanged. The
[original live desktop](http://127.0.0.1:16080/vnc.html?autoconnect=1&resize=scale)
and [direct RTX preview](http://127.0.0.1:18080/) show the separate row demo.
Do not kill the artifact HTTP server or replace its supervised container to
refresh a gallery. Bindings remain private/loopback-only.

Rebuild the selected replacement-media snapshot inside the existing container,
from `/workspace`, using an unused output directory:

```bash
python3 rack_robotics/scripts/build_gallery.py \
  --output artifacts/robotics-gallery-NEW \
  --pool rack_robotics/experiments/benchmark-pooled004.json \
  --neighbors rack_robotics/experiments/occupied-summary001.json \
  --audit rack_robotics/experiments/preservation-audit022.json \
  --media rack_robotics/gallery/media009.json \
  --current-benchmark rack_robotics/experiments/benchmark-summary021.json \
  --current-benchmark rack_robotics/experiments/benchmark-summary018.json \
  --current-benchmark rack_robotics/experiments/benchmark-summary019.json \
  --comparison rack_robotics/experiments/comparison005/comparison.json \
  --cable-forces rack_robotics/research/cable_force_comparison001.json \
  --physical-campaign rack_robotics/experiments/physical-controls001 \
  --physical-campaign rack_robotics/experiments/matched-release001
```

The builder rechecks comparison inputs/scores, nominal force traces, selected
media and exact saved-version identities. It copies only explicitly selected
artifacts and does not start or replace a server. Its frozen builder and media
selection are included in the output. Selection009 contains25 accepted working
clips and four reviewed failure diagnostics, replacing the obstructed B/C rear
and dependent edit, and accurately labels the accepted C/A showcase.
The two physical campaigns are recomputed and bound to the exact current
environment manifests; their failed diagnostics remain visibly failed and add
no randomized reliability samples. The optional A/A1440p macro remains preserved but is not
selected. Each selected decision is hash-bound: the builder verifies source
identity, visual sheets, temporal coverage/timestamp evidence and natural Mac
playback before assigning an acceptance label. Original evidence bytes and
their project-relative paths are copied under `presentation/`; each media row's
`presentation.links` maps those paths to gallery URLs. Earlier native AA/CA
inspection references are index-only, not retrospectively hash-bound decisions.
Legacy selections without records remain candidates. Source/video verification
alone does not grant visual acceptance or convert a diagnostic into success.

From the Mac, verify the actual served bytes, video play/seek, filters and layout:

```bash
.venv/bin/python rack_robotics/scripts/check_gallery.py \
  --url http://127.0.0.1:18080/robotics-gallery-NEW/ \
  --output artifacts/robotics-gallery-NEW-mac-qa001
```

## Modify without losing evidence

Edit working modules under `rack_robotics/`, not the frozen baseline or saved
environment source. `run_reference.py --help` lists architecture/tool and
mechanical-revision build flags; do not assume its defaults rebuild the latest
version. For a controller-only candidate, run the working runner with `--scene`
pointing to a saved scene and explicit `--robot`, `--gripper`, `--physics-hz 480`,
and a new `--output`. This is a new experiment, not reproduction of old source.
For geometric changes, build a new assembly using its applicable revision flags.

After a full-rack attempt, preserve it with:

```bash
/opt/rack-usd-tools/bin/python3 rack_robotics/scripts/package_reference.py \
  --attempt rack_robotics/experiments/NEW_ATTEMPT \
  --output rack_robotics/environments/robot_a_gripper_a/NEW_VERSION
```

Use the next unused `vNNN` name for `NEW_VERSION`. Then run a fresh reload,
update the preservation/dependency audit, and create a new declared benchmark
cohort. Keep failed attempts, original logs, old packages, and old media. Do not
change connector poses, disable latch/contact geometry, or add hidden retention
constraints to make a trial pass. Unit tests run from the Mac project root with
`.venv/bin/python -m unittest discover -s tests`; the current suite has398 tests.
Those tests supplement, not replace, Isaac physics and rendered-image checks.

## Recompute the design comparison

After collecting terminal trial snapshots and completed media, run:

```bash
.venv/bin/python rack_robotics/scripts/compare_designs.py \
  --plan rack_robotics/research/comparison-plan001.json \
  --output rack_robotics/experiments/NEW_COMPARISON
```

This Mac-side analysis verifies exact-version evidence and implements the
[declared rubric](research/scoring_method.md). Its output includes normalized
observations, per-trial contextual metrics, hashes, analysis sources and weight
sensitivity. It withholds ranking while required working-design evidence is
pending. Failed designs remain visible but cannot outrank functional designs.
Finish imports and documentation/source edits **before** starting the analysis;
its file signatures deliberately reject inputs changed during verification.
Do not stream an updated render/campaign archive onto files being verified.
The current software suite contains398 tests; this does not replace the physical
or final visual deliverables.

The separate [cable-motion screen](research/cable_motion_and_loads.md) reads
exact saved nominal trajectories with `scripts/screen_cable_motion.py`. It needs
`usd-core`, but not a running Isaac session. Its displacement, anchor-gap and
geometry outputs are explicitly not tensile-force or material-safety evidence.
