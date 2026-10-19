# Predeclared current-tool physical challenges

2026-10-17. Separate diagnostic campaign, not randomized reliability or hardware
qualification. No results were available when this protocol was written.
Cases: AA v016, BA v014, CA v021, AC v005 and BC v004, each with an unchanged
nominal cycle, unpressed pull and open-tool transport (15 fresh sessions).

The normal shared task performs physical initialization, approach, alignment
and grasp. No connector poses, latch spring targets, collisions, attachment
joints or observations are overridden. Baseline hand and clip-press helpers
remain inactive throughout timing. The saved low-level controllers, geometry
and environment packages are unchanged. The harness, conditions, protocol and
exact package identities are frozen before launch; every case runs once.

## Unpressed pull

After the shared task verifies grasp aperture, retract the latch tool before
the next physics step. Cap only the insertion-axis drive at the lower of its
existing cap and5 N. Request10 mm outward motion over0.5 s and hold1 s.
The normal task's latch interlock is not used to prevent this diagnostic motion
request. The request still acts through the actual force-limited joint drive.

Require at least0.2 s of measured positive axial tool-to-connector contact
impulse/dt of0.5 N or more, and at least0.2 s of opposing socket contact of
0.25 N or more. This distinguishes actual loading from a request with no
delivered contact force. Require the full bounded challenge duration, retracted
latch target, blocked hook, grasp aperture10.5–13 mm, insertion depth at least
10.3 mm and maximum absolute axial drift below1 mm. The5 N drive cap is not a
claim that all instantaneous contact peaks are below5 N.

## Open-tool transport

Refinement of the earlier coverage-audit proposal: first extract normally with
closed jaws and a physically pressed latch. The shared task must measure depth
below−35 mm and housing-to-TCP distance below2 mm before the challenge begins.
Open the jaws, retract the latch tool, hold0.7 s, then command40 mm further
outward over1.5 s and hold0.5 s, inside the existing550 mm Y workspace limit.

Testing outside the socket removes the confound that a spring-returned latch
might restrain a connector after an open-jaw request. The connector is free to
fall or move under gravity/cable forces; it is not required to remain fixed in
world position. Require open aperture at least13 mm, actual tool advance at
least35 mm, socket clearance throughout (depth below−25 mm), housing forward
advance below10 mm, and final relative axial shortfall at least25 mm. All
distances during transport are relative to the measured post-opening state.
Record both the extraction/opening reference and transport reference, checking
each against the immediately preceding physics sample.

A fixed jaw, shoulder or latch tool might still transport the housing despite
an open aperture. That is counterevidence to the expected negative control,
not permission to alter the gate or erase a trial. This experiment tests the
whole open tool, not a claim that only opposed jaw friction can ever carry a
connector. Preserve and explain any unexpected contact-mediated transport.

## Evidence and interpretation

Record measured housing/TCP/target, aperture, latch target, hook/depth/retention,
insertion-drive cap, helper status and relevant actor/collider contact vectors
at every480 Hz step. Contact vectors include normal and friction-anchor
impulses, with actor-order signs matching the independently validated
`cable-balance-probe003` convention. They measure transmitted contact load,
not a native actuator torque sensor, calibrated physical load cell or material
strength. Unit tests additionally check pair classification and signs.

Require finite/contiguous samples, actual delivered challenge duration,
unchanged topology, carrier integrity, clean contact reporting and no runner
exception. Raw traces, process exits, source hashes and separately recomputed
verdicts are preserved. Compare nominal30 Hz trajectories against the previous
first continuous cycles to check that read-only recording did not alter them.

Only nominal cases can pass the ordinary full-cycle task. Challenged cases
report `passed:false` and `full_cycle_attempted:false`, with a separate physical
diagnostic verdict. Missing preconditions or undelivered loading do not pass.
No diagnostic sample is added to a reliability denominator or historical score.
