# Current-design comparison and prototype recommendation

2026-10-17 checkpoint. This completes the numeric comparison of the current
saved designs, not physical-hardware qualification. Subsequent presentation
acceptance001/002/003 now covers25 working clips, including the native1440p
C/A showcase. The [final requirement-level review](../FINAL_AUDIT.md) records
delivery closure and Gallery011 QA; presentation acceptance does not certify
real hardware. Frozen gallery copies of this report retain their build-time wording.

## Results and ranking

The [current CSV matrix](current_candidate_matrix001.csv) identifies all nine
exact versions. The older `candidate_matrix.csv` remains the original
screening/development record; its early statuses are not current results.

All five nominally functional designs have 24 planned randomized starts and
22 admissible manipulation trials. Two fixture-initialization failures per
design remain in the full-protocol denominator. No failed start was replaced.

| Design / saved version | Complete / valid trials | Complete / all starts | Mean successful cycle | Rubric / 100 | Practical placement |
|---|---:|---:|---:|---:|---|
| C/A v021, CoreXZ + precision parallel | 22 / 22 | 22 / 24 | 22.943 s | 70.523389 | Joint leading tier |
| A/A v016, dual screw + precision parallel | 22 / 22 | 22 / 24 | 32.543 s | 70.523350 | Joint leading tier |
| B/A v014, telescoping + precision parallel | 22 / 22 | 22 / 24 | 26.840 s | 69.400954 | Next alternative |
| A/C v005, dual screw + specialized tool | 21 / 22 | 21 / 24 | 37.885 s | 67.643233 | Specialized-tool alternative |
| B/C v004, telescoping + specialized tool | 17 / 22 | 17 / 24 | 29.921 s | 55.251947 | Lower-reliability alternative |

The C/A–A/A difference is only 0.000038 points, caused by tiny measured envelope
differences. It is not a meaningful win or evidence of statistical superiority.
Their conditional 95% Wilson intervals are both 85.13–100%; A/C is
78.20–99.19% and B/C is 56.56–89.88%. Intervals overlap. The 35/45/55-point
reliability-weight sensitivity retains the same numeric ordering, but it does
not resolve this practical tie. Visual scores remain the historical1/2 for all
five: at scoring time some required views were obstructed or under review.
Later camera corrections and presentation acceptance have not retroactively
changed the frozen comparison005 inputs or scores.

A/C uses campaign009's changed task/seating harness; A/A, B/A and C/A use007,
and B/C uses008. They share declared randomized conditions but are system-level
comparisons, not a controlled estimate of hardware-only effects. Historical
versions and the new consecutive-cycle diagnostics are not pooled into these
rates. A/C's one valid failure is withdrawal-clearance timeout at port16;
B/C has five seating failures (four at port16 and one at port8).

A/B v011, B/B v007 and C/B v002 fail bounded initial pickup with the full-size
RG2. C/C v003 fails datum alignment. They are preserved nonfunctional designs,
not assigned misleading success scores or ranked above functional systems.

## Recommendation and tradeoffs

**Select C/A for the higher-resolution simulation showcase.** It shares the
leading reliability tier, has the shortest successful mean cycle here, and
has the lowest measured total/moving mass: 7.627/2.797 kg. Its three-cycle
continuous diagnostic also passes without a recovery or re-seating. This choice
is based on those observed advantages, not the negligible score difference.

**Keep A/A as the preferred independent-axis hardware prototype comparison.**
Its screw/guide architecture has fewer unresolved coupled-belt transmission
assumptions, and its current valid-trial reliability matches C/A. It is heavier
(10.732/3.632 kg total/moving) and slower; three continuous cycles each need one
bounded seating recovery. Neither recommendation is permission to operate an
unvalidated machine around live equipment.

B/A is useful when one-sided mounting is essential and adjacent service space
is available. Its longer projection and cantilever load make it a weaker dense-
rack default despite 22/22 valid cycles. The specialized C tool demonstrates
that a connector-specific mechanism is feasible, but the tested A/C and B/C
systems do not outperform precision-tool A on reliability or cycle time.

The new [nominal cable-force diagnostics](cable_momentum_measurement.md) add
a countervailing advantage for the specialized tool. Estimated peak axial cable
reactions are AA8.75 N, BA10.04 N, CA13.44 N, AC0.83 N and BC1.11 N. All occur
during grasp; each precision-tool5 N crossing lasts one480 Hz step (2.08 ms).
These separately calibrated momentum estimates include friction impulses and
reproduce the earlier nominal recorded motion. They are not a randomized force
distribution or manufacturer damage limits. Thus **retain A/C as a lower-peak
load development alternative**, while its slower cycle and21/22 valid reliability
remain visible. C/A remains the simulation-showcase choice, not a hardware-safe
winner. This post-hoc diagnostic changes the engineering discussion, not the
predeclared rubric or its historical scores.

The [matched open-command challenge](matched_release_results001.md) adds an
important C-tool limitation: even after reaching approximately16.9 mm aperture,
its guide surfaces support and carry the extracted housing. A/C and B/C move
it about40 mm relative to a matched stationary tool. Opening alone is not a
free-space release. The normal socket-supported release and lateral clearing
cycles remain separately demonstrated; do not generalize them to arbitrary
release poses. The three A-tool systems release the housing and show identical
housing paths with a holding versus moving open tool. All five current systems
also pass the [unpressed retained-pull challenge](physical_challenge_results001.md).
These are physical diagnostics with preserved failures, not added reliability
samples, hardware qualifications or a revised score.

## Dimensions, components and cost status

| Architecture | Modeled travel X / Z / insertion | Rear projection | Side projection | Gravity mount moment, sampled nominal motion |
|---|---|---:|---|---:|
| A | 420 / 700 / 125 mm | about 345 mm | about 54 mm each side | about 13.4 N·m |
| B | two 200 mm extensions / 700 / 125 mm | about 464 mm | about 248 mm left | about 20.2 N·m |
| C | 420 / 700 / 125 mm | about 345 mm | about 54 mm each side | about 10.0 N·m |

These are rear-door-open service concepts, not demonstrated closed-door fits.
A/C architecture rails have 12×8 mm sections and lengths 2×920, 520, 2×200 mm;
B uses 2×940, 2×310, 2×200 mm. C removes three modeled screw shafts using
coupled X/Z drives; actual belt pretension, routing and engagement still need
engineering. A uses four axis motors, C three, and each uses two brake packages.

Tool A's reference is SCHUNK EGP25-N-N-B (310900): a 26.5×18×72.7 mm, 0.11 kg
commercial envelope, with custom fingertips and a separate latch-release tool.
The saved assembly is dimensioned from the reference, not claimed exact EGP25
manufacturer CAD. Tool C is a custom rack/pinion datum-jaw and compliant wrist.
Tool B uses the full-size official OnRobot RG2 asset; it was not shrunk to fit.

Complete physical costs remain **unknown**, not zero or an invented range.
The dated [supplier evidence and BOM](buildability_and_bom.md) identifies
verified candidate subtotals only: PQ12 plus LAC $95; adding an HS-422 gives
$115.99 for those three C-tool candidates, not a finished gripper. Commercial
EGP25/RG2 prices, machined axes, brake/motor stacks, guides, frame/clamps,
carriers, controls, sensing and assembly remain unpriced. Part references,
dimensions, asset licenses and unresolved interfaces are in that report and
[mechanism](cartesian_robots.md)/[gripper](grippers.md) research. Do not use
partial prices to claim one complete robot is cheaper.

## Limits that change the interpretation

- Current occupied-port screens complete 4/5 cases for AA/BA/CA/AC and 3/5 for BC;
  restrained neighboring plugs and free-ended cables do not represent arbitrary
  dense installed routing. All designs fail the port 8 fixture start.
- Retracted unloaded finite workspace rasters pass, not every loaded trajectory.
- None of the five current power-loss probes passes every gate: carrier-angle
  failures affect A/A, C/A and A/C; bearing/tool contacts affect B/A and B/C.
- The dynamic cable has a free far end. Motion/joint gaps and newly recorded
  nominal axial-reaction estimates are measured separately. Two-ended slack
  exhaustion and real-material safe limits are not validated. See the
  [cable-motion report](cable_motion_and_loads.md) and
  [force diagnostic](cable_momentum_measurement.md).
- Simulator pose feedback, approximate drives/materials and a spring-hinged
  rigid latch do not establish physical reliability, calibrated insertion
  forces, thermal/airflow performance, or safe unattended service.

## Reproducible evidence

The declared [scoring method](scoring_method.md) and `comparison-plan001.json`
produce `../experiments/comparison005/comparison.json`. Its 2,645 input hashes,
frozen analysis sources, regenerated cohort summaries and observation hashes
were reverified locally. `complete_evidence: true` means the scoring adapter has
its declared inputs, not that every PLAN_p2 deliverable is complete.

Terminal cohort summaries are `benchmark-summary021.json` (AA/BA/CA),018 (BC)
and019 (AC). [Continuous-cycle results](continuous_cycles.md) are separate.
To recompute without altering any saved design, use an unused output path:

```bash
.venv/bin/python rack_robotics/scripts/compare_designs.py \
  --plan rack_robotics/research/comparison-plan001.json \
  --output rack_robotics/experiments/comparison-NEW
```
