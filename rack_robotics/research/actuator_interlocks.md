# Current-tool actuator interlock diagnostics

All15 predeclared cases in `experiments/actuator-controls001` are terminal and
pass their separate diagnostic verdicts. These are five nominal controls plus
ten expected task failures, not15 successful manipulation cycles or additional
randomized reliability trials. Saved packages: AA v016, BA v014, CA v021,
AC v005 and BC v004. No score or historical denominator changes.

The command wrapper permanently delivers the existing retracted-latch or
open-jaw command while preserving real observations and every optional tool
property. It does not override body poses, joint states, collisions, force
limits, hook clearance or aperture. The unchanged shared task must detect the
missing action, exhaust its bounded recovery and stop before withdrawal.

| Design | Nominal cycle (s) | Latch-disabled maximum axial drift (mm) | Open-grasp maximum axial drift (mm) | Minimum open aperture during grasp (mm) |
|---|---:|---:|---:|---:|
| AA |32.922917|0.070125|0.000030|16.599823|
| BA |32.922917|0.096738|0.000060|16.599957|
| CA |21.516667|0.140727|0.000060|16.599853|
| AC |37.625000|0.118047|0.117153|16.897429|
| BC |37.625000|0.211209|0.184566|16.896475|

Every negative case suppresses three requests and exhausts two recoveries.
Latch-disabled cases stop in `release_latch`, with the drive retracted and the
hook never clear during that phase. Open-grasp cases stop in `grasp` with
measured open aperture. None enters withdrawal or reports extraction; the
housing stays within1 mm axially, never falls below10.3 mm insertion depth,
and remains retained at termination. All cases retain inactive initialization
helpers, intact topology/carriers and clean contact reporting. The controller
reports the expected task error; the diagnostic does not relabel it task success.

## Evidence and reproduction

The15 traces contain177,063 contiguous480 Hz samples. Each case preserves its
`results.json`, `actuator_trace.jsonl.gz`, command events, source manifest and
frozen harness. Campaign `state.json` records each actual child PID, terminal
exit and result hash. VM and Mac verification recompute the gates from every
sample, verify frozen sources and require matching process/result evidence.
Their reports are byte-identical, SHA256:

`cca22ede301368e33df37303348819e842b02c38177aad01deb70903262b7b75`

Reports: `experiments/actuator-controls001/verification_vm001.json` and
`verification_mac001.json`. Campaign manifest SHA256:

`021b6d9100eb06b2bc577d03b1d2271cf304424232139c7442e6e7db43109dcc`

The five nominal trajectories exactly match every30 Hz recorded body sample
of the corresponding first continuous cycle: AA988 frames/126 bodies,
BA988/143, CA646/126, AC1129/129, BC1129/146. This comparison does not assert
identity of every unrecorded physics-step body pose.

Use the commands in [REPRODUCE](../REPRODUCE.md#actuator-disabled-interlock-diagnostics),
choosing a new report filename when verifying again. Original campaign code
and results are retained; later verifier source is separately identified.

## Scope limits

This proves that the normal controller does not advance when either required
actuator action is missing under the tested nominal conditions. Because the
interlock prevents withdrawal, it does **not** prove physical retention under
an imposed pull or that an open tool cannot drag an already released connector.
Those require a separate physical challenge protocol. It also does not
establish manufacturer force ratings, installed-cable safety or general fault
tolerance. Baseline latch contact tests and nominal tool-contact motion are
separate evidence, not silently substituted for these stronger controls.
