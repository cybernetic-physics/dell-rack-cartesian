# Precision tool: boot interference during latch depression

The corrected carrier-equipped CoreXZ passes sampled startup/carrier integrity
at 480 Hz, but `c_a_frame_carriers480_001` fails physical latch release after
two retries. The final hook height is 4.94577 mm; the existing clearance
criterion remains unchanged. The gripper holds the housing and the connector
remains retained throughout this failed attempt.

Contact evidence gives a specific mechanical lead: the tongue **neck**, not
its orange tip, contacts the cable boot with a peak pair force of 3.90256 N.
Neck/latch-arm contact peaks at 0.89193 N; the tip/arm pair reports no positive
impulse. These are simulator pair-force observations, not calibrated hardware
forces. The plausible obstruction is the neck landing on the taller boot
before it can depress the latch sufficiently.

`c_a_frame_press001` tests a −5.5 mm command instead of −5.0 mm, using the
existing −5.5 mm joint limit and unchanged 4 N drive cap. It still times out;
the final hook is 4.94705 mm. More commanded travel alone does not resolve
the obstruction. Both failures are preserved, as C/A v017 and v018.

`--latch-press-target-mm` is now an explicit, preserved configuration choice.
It validates against the actual tool-joint limits; sub-nanometre USD float32
roundoff is clamped into those limits, never used to extend travel. Existing
scenes without a custom setpoint retain the original −5.0 mm command.

## Tool-only geometry experiment

`latch_tool_detail.py` / `--forward-latch-neck` changes only the precision
tool's neck translation: local Y=2.0 mm becomes0.5 mm. The neck is still a
collision-enabled 3×2×7 mm solid; it overlaps the unchanged tip and raised arm
by0.5 mm nominally. The TCP-to-tongue Y offset is6 mm, so the new neck ends at
7.5 mm instead of9 mm, before the boot's nominal9 mm front.

The connector, latch, boot collision, gripper jaws, tool joint limits, drive
cap, housing grip, controller clearance gates and success criteria are
unchanged. No collision pair is removed. This is an original manufactured
tool shape, not a vendor-qualified accessory; small bracket overlap, bending
stiffness, fasteners, material and fatigue remain engineering assumptions.

`c_a_latch_neck001` tests this geometry at480 Hz with the **original −5.0 mm
command**, separating geometry from the unsuccessful deeper-command test.
It completes the full cycle in21.51667 s without recovery or seating nudge;
all startup and task carrier gates pass, and cable gap peaks at0.021245 mm.
This supports the boot-contact diagnosis without changing connector physics
or force/clearance gates. It is one development trial, not a reliability claim.
No tongue/boot contact pair is reported in the revised task. Neck/arm and
tip/arm peaks are1.55071 N and0.38083 N respectively. Startup carrier gaps
peak at0.015817 mm and hinges span−0.36859–30.07429°; timed gaps peak at
0.014516 mm and angles span−0.22469–30.06839°. Neither startup nor task has
a robot–robot pair force above0.1 N. C/A v019 preserves the exact assembly.
The matching480 Hz midstroke unloaded power-loss probe `c_a_frame_brake001`
passes its declared checks:7.0963 mm maximum descent after power loss,
0.007287 mm final hold drift and42.0062 mm descent with brakes deliberately
released. Carrier and collision-report gates pass. This is only one modeled
midstroke condition, not emergency-stop safety, all-payload/all-stroke testing
or calibrated brake qualification. Reload021 independently reproduces the
v019 task pass and verifies its dependencies. Repeated alignment/friction/port
variations and force qualification remain separate.
