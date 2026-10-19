# Matched open-command hold/move results001

2026-10-17. All10 fresh-session cases are terminal. All68,388 raw480 Hz
samples, source/condition identities, process records and paired trajectories
reverify on VM and Mac. **Six cases pass; four fail.** Both campaign-level
verdicts remain false. This is a useful physical finding, not grounds to change
the [predeclared protocol](matched_release_protocol001.md) or replace failures.

## Result

Each pair has exactly identical pre-intervention state, commands and contact
records. After normal extraction and2 s opening, one tool holds position while
the other requests40 mm outward travel. The measured hold motion is below1 mm
and transport is approximately39.99 mm for every design. All jaws reach the
required13 mm aperture; all bounded motion requests are actually delivered.

| Design | Hold / move diagnostics | Minimum aperture during move | Minimum housing–TCP separation during move | Maximum housing-path difference, hold vs move |
|---|---|---:|---:|---:|
| AA016 | PASS / PASS |16.5999 mm |1.57318 m |0 m, exactly identical recorded positions |
| BA014 | PASS / PASS |16.6000 mm |1.65046 m |0 m, exactly identical recorded positions |
| CA021 | PASS / PASS |16.5998 mm |1.65546 m |0 m, exactly identical recorded positions |
| AC005 | FAIL / FAIL |16.8994 mm |4.88437 mm |40.010965 mm |
| BC004 | FAIL / FAIL |16.8998 mm |4.75312 mm |40.018828 mm |

AA/BA/CA have no direct tool–housing/latch contact rows during the challenge.
Their released housing paths are exactly the same with a moving or stationary
tool. That resolves the earlier world-Y proxy confound for these bounded cases:
the housing can move after release without being transported by the tool.
Original BA/CA campaign001 gates remain FAIL; this is new matched evidence,
not a retroactive passing classification.

## C-tool counterevidence: open aperture is not disengagement

AC/BC retain actual contact through `/World/Robot/RightJaw/LowerGuide`,
`LowerGuideLand`, `UpperGuide` and `UpperGuideLand` against `/World/Plug/Body`.
BC also has LowerGuide–Boot contact. The moving-jaw pocket/guide surfaces,
not an invisible grasp joint or observer override, continue supporting the
connector even at approximately16.9 mm jaw aperture. AC has3,844 contact rows
in each challenge; BC has4,805 holding and4,488 moving. The signed contact
impulse/dt sum supplies about0.332 N mean upward support during both arms,
so these are not merely zero-impulse contact notifications. Force estimates
are simulation impulses, not calibrated motor sensors or hardware ratings.

The tool moves the connector about40 mm relative to the matched stationary
case. Both `housing_separated_from_tool` and
`no_direct_tool_connector_contacts` fail. The pair's
`no_measurable_transport_effect` is also false. Opening alone is therefore
**not a reliable free-space release for the current C tool**. Do not call its
open command an ineffective grasp, nor claim that its original precondition
failure proved non-transport. This is a genuine limitation to carry into the
hardware comparison and any future release controller.

The normal task releases only after socket seating, checks continued retention,
and performs its lateral datum-clearing/retraction sequence. Those separate
successful nominal and continuous cycles remain valid within that task; they
do not establish arbitrary free-space release. No new geometry, lateral
clearing, increased force, collider filtering or reset was introduced here.
No additional experiment is needed to turn this counterexample into a pass.

## Provenance and recomputation

Directory: `../experiments/matched-release001/`. Manifest SHA256:
`673538ba43cd849e3e59d27894323c5c21b65719ea49593cc6412271a4a62c79`.

- `verification_vm001.json` SHA256:
  `da11d9abf6d434327c64d679ab701a261e51f76a9c07188baefde6afeb70c319`.
- `verification_mac001.json` SHA256:
  `2234ef5132063cbdb898c28fbda7ca694dc9ea2fc20afa8babcff6fcfdc8d93e`.
- Preserved `verification_source001.py` SHA256:
  `18be77b0020e940badb939ac195bee2a5fa1250709e48208970c7d9bdfb6783c`.

The verification reports differ only in A/C's maximum matched distance:
0.040010964595436765 m on VM versus0.04001096459543676 m on Mac, one ULP
(6.94×10⁻¹⁸ m). All gates, verdicts, counts and input identities are identical.
Two per-case math.dist metrics permit at most4 ULP during recomputation across
Python3.9/3.12; every boolean gate/verdict remains exact. No millimetre-scale
tolerance is used to conceal a disagreement at the declared pass threshold.

The six passing cases exit0 and all four failed cases exit1 through the
corrected SimulationApp shutdown path. Every case remains ordinary
`passed:false`, `full_cycle_attempted:false`; diagnostic success is separate.
These tests add no randomized samples and do not rescore comparison005.

Reproduction/verification commands are in
[REPRODUCE](../REPRODUCE.md#matched-open-command-follow-up). Keep the original
physical-controls001, its four failed diagnostics and its legacy-exit annotation
alongside this follow-up. Do not pool their different opening durations/gates.
