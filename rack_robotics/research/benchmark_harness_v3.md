# Revised-hardware benchmark protocol

## Current completed cohorts — 2026-10-17

Current A/A v016, B/A v014 and C/A v021 are in campaign007 (summary021);
B/C v004 is in campaign008 (summary018); A/C v005 is in campaign009
(summary019). Each cohort has 24 finished planned starts, 22 admissible trials
and two fixture failures. Complete valid cycles are 22/22 for AA/BA/CA,
21/22 for AC and 17/22 for BC. All use their saved 480 Hz physics settings.
The campaign009 seating-task change remains a system-level confound: these
are not pooled estimates of a hardware-only effect.

See [current comparison](current_design_comparison.md) and the
[current version matrix](current_candidate_matrix001.csv). The original
`candidate_matrix.csv` is a historical screening/development table, not current
reliability or compatibility evidence. Consecutive nominal cycles use a separate
diagnostic and are never counted as randomized trials.

The sections below preserve the earlier protocol development and controls.

## Historical protocol development

Earlier randomized cohorts remain immutable. Their frozen harnesses force
240 Hz and predate the passive carrier/brake acceptance checks. They cannot
be silently reused as evidence for the480 Hz C/A v019 assembly.

`benchmark_harness_v3` now reads the saved physics timestep, passes it to the
low-level Cartesian controller, and scales every initialization, task and
recording interval by physical time. Old controllers without a configurable
timestep are accepted only at their original240 Hz. A changed rate is not
silently ignored. The common timing and carrier-validation modules are frozen
inside each harness and included in its source hashes.

Carrier-equipped/open-stage assemblies derive startup Cartesian coordinates
from their authored joint anchors. Precision-tool startup coordinates are
likewise initialized for brake-equipped assemblies, before physics begins.
Brake geometry is never added twice: the saved scene is used, with brakes
released under motor power and their runtime efforts recorded. The CoreXZ
motor coupling is retained. Both startup and timed carrier samples contribute
to the overall result; missing samples or reporting errors fail acceptance.

No physical success criterion, latch force/stroke, connector collision or
runtime plug pose is changed. Randomized perturbation definitions remain
unchanged. A new protocol/design cohort must not be pooled into the earlier
110 original or60 revised-drive trials.

`c_a_benchmark_v3_control001` exercises the unperturbed control condition on
saved C/A v019. It is a protocol compatibility check, not a randomized sample
or a new reliability percentage. Further campaigns require their own frozen
plans, controls, input hashes and complete predeclared outcomes.

The terminal compatibility control passes at480 Hz in21.5167 s, with no
recovery/nudge, all eight carrier gates and0.010996 mm maximum timed cable
anchor gap. All94 frozen source hashes verify after download.

`benchmark-plan004` predeclares20 conditions (seed20261017) for the separately
saved C/A v020 front-support revision. `benchmark-campaign006` uses that plan
and the frozen v3 protocol with one worker. It must first pass its own nominal
control; all randomized failures remain part of the resulting cohort. This
campaign is independent of the raster clearance and reload checks; task
reliability cannot erase a failed workspace or mechanical audit.
