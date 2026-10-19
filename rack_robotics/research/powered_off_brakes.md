# Powered-off motor brakes — development, not safety qualification

## Current specialized-tool probes (2026-10-17 UTC)

`a_c_frame_brake001` and `b_c_frame_brake001` test the exact current A/C v005
and B/C v004 packages, not a sibling A-tool assembly. Both use480 Hz and the
same−0.24 m lift fixture as the current A-tool tests. Input manifest and
snapshotted source hashes verify. Both remain **overall failures**:

- A/C passes scalar holding:5.590 mm drop,0.006124 mm final-half-second drift,
  and42.033 mm further descent with the brakes released. It reports no robot
  contact above0.1 N, but a carrier hinge reaches−2.6168° during recovery
  velocity arrest and−1.6827° during the recovery ramp, outside the unchanged
  one-degree margin. Startup carrier gates pass.
- B/C passes scalar holding:6.280 mm drop,0.024527 mm final-half-second drift,
  and41.952 mm released-brake descent. Carrier gates pass. The plug body hits
  `Carriage/DepthFrontBearingPost1`, with a5.076 N collider-pair impulse/dt
  peak, failing the robot-contact gate. This is not a net insertion-force or
  injury-load measurement.

These are unloaded, midstroke robot-power-loss diagnostics, separate from
powered RJ45 task reliability. All five current nominally working designs now
have direct fault-probe evidence; none passes every declared power-loss gate.
No source scene, torque cap, carrier tolerance, or contact gate was altered to
turn these results into passes. The comparison assigns the corresponding low
fault-handling score and retains these limitations in the recommendation.

## Latest corrected-frame audit (2026-10-17 UTC)

The new `a_a_frame_brake001`, `b_a_frame_brake001` and
`c_a_frame_brake002` test A/A v016, B/A v014 and C/A v021 at480 Hz and the
same−0.24 m lift fixture. All are **overall failures**, despite passing the
scalar power-off holding, delay, torque-cap and negative-control checks.
Peak drops are5.612 /6.278 /7.105 mm; final-half-second drifts
0.008151 /0.016019 /0.005722 mm; released-brake descent
42.063 /42.064 /42.001 mm. These are not successful full fault-recovery tests.

- A's carrier hinge minimum reaches−2.04978° during velocity arrest and
  −1.35766° during recovery ramp. No robot contact exceeds0.1 N.
- B passes both carrier intervals, but the target plug boot contacts
  `ToolMount/DepthBearingPlate` at4.11648 N during motor-power-off holding.
- C's recovery ramp reaches−1.02587° at a carrier hinge, beyond the unchanged
  strict−1° gate. No robot contact exceeds0.1 N. The older v019 scoped pass
  is not transferred to v021.

The runner now uses the common startup-and-task carrier validator. Older
probe code excluded `initial_settle` hinge angles; that exclusion is removed
for new runs, while original reports/source remain preserved. All three new
startup intervals pass. Final diagnostic rendering pauses physics so it does
not add unrecorded motion. Unit tests cover missing intervals, startup
violations and nonfinite values. No carrier tolerance, contact gate, brake
torque or latch collision was relaxed.

Normal powered manipulation and retracted travel still have their separate
passes. These fault-test failures limit safety/buildability recommendations;
they do not erase the powered-task evidence or establish a safe real robot.

## Hardware basis

The [Nanotec BCD42-0.4-5 drawing](https://www.nanotec.com/fileadmin/files/Datenblaetter/Bremsen/BCD/BRAKE-BCD42-0_4-5.pdf)
specifies a 42 mm chamfered-square housing within a 54 mm circumscribed circle,
45.5 mm body length, 24 mm projecting 5 mm shaft, and 0.28 kg package mass.
The 24 mm dimension is **not** the housing length. The front interface has a
22 mm pilot and four 3.4 mm holes on 31 mm square spacing; the rear threads
are M3. This exact drawing takes precedence over the generic product-page
mounting text. Static holding torque is at least 0.4 N·m, backlash below 1°,
24 V coil power 6.9 W, switch-off time 30 ms and switch-on time 50 ms.
These are not an emergency-stop/dynamic braking rating. The vendor supplies
this brake with a motor; a qualified complete motor combination and price
remain unverified. Local reference: `sources/nanotec-bcd42-brake.pdf`.

`brake_hardware.py` constructs original dimensioned outer-envelope meshes,
not vendor CAD. Two packages serve A's two lift screws, one serves B's lift,
and two serve C's coupled belt motors. Motor bodies are repositioned and
mount plates replaced **before physics** in a stronger scene layer. The
original environments remain unchanged. The packages increase rear/top
space and fixed-frame mass; they are not hidden inside the old motor boxes.
M3 fasteners, pilot openings and A's shaft reducer sleeves are explicit.
The M8 connector housing envelope is an assumption, not a measured part.
The solid hull is a collision proxy; internal discs/bearings and spinning
shafts are not contact-resolved. B's original visual coupler still needs a
verified stepped-bore assembly. Mount strength and final wiring are open.

## Passive model and power removal

`brakes.py` implements delayed, backlash-bearing, torque-limited elastic/
plastic friction memory. Engagement captures the actual shaft coordinate as
an internal friction anchor; it never assigns body poses or controller
position targets. Yielding updates that internal anchor and accumulates
plastic work. A viscous term opposes velocity within the remaining torque
budget. The total torque per brake cannot exceed 0.4 N·m.

The model uses 1° total backlash conservatively. Stiffness/damping are
uncalibrated assumptions: per A brake 0.03 N·m/rad and 0.0004 N·m·s/rad;
B 0.06 and 0.0008; each C brake 0.4 and 0.004. Static holding torque is
used as a dynamic cap, not claimed as a manufacturer stopping rating.
Rotor inertia, thermal limits, wear, supply circuits and failure detection
are absent. This is a feasibility model, not a safety-rated brake system.

Motor coordinates use the existing 8 mm screw lead or C's 20-tooth/2 mm
belt-pulley pitch radius. Generalized force is `Jᵀ × motor torque`, with
equal motor/joint power verified in tests. C requires both motor-coordinate
constraints to hold independent X and Z motion; a single brake leaves a
free diagonal mode. No independent X/Z position servo is substituted.

`brake_runtime.py` zeroes **all robot drive gains** when motor power is
removed and disables both C motor forces, including gravity feedforward.
Passive brake effort and motor effort are summed explicitly. Normal powered
RJ45 trials keep the brakes released; those trials do not prove powered-off
holding. Unit tests cover delay, backlash, caps, energy, virtual work,
drive-gain restoration, force addition, dimensions, mass and mesh normals.

## Preserved physical probes

`scripts/probe_brakes.py` opens a saved full-rack environment in a fresh
session and writes a new overlay, source hashes, hardware report, every-step
effort/position/velocity trace, 30 Hz measured trajectory, carrier metrics,
contacts and result. No post-reset body-position or velocity assignment is
used. A powered move reaches midstroke, motor power is removed, the brake
holds for two seconds, and releasing it while power remains off is a causal
negative control. Powered recovery uses actual joint drives.

Predeclared engineering gates include less than 10 mm power-loss drop,
less than 0.5 mm final-half-second drift, final lift speed below 2 mm/s,
more than 20 mm descent after releasing the brake, and unchanged carrier
anchor/hinge tolerances. These are development thresholds, not certification.

First probes `brakes-aa001` and `brakes-ba001`, both 480 Hz, pass the scalar
brake checks: peak drops 5.401/5.617 mm and final drift 0.00685/0.00840 mm.
Both remain **overall failures**. The deliberately unsupported release hit
server fan housings after 41.6 mm descent (contact impulse/dt estimates
roughly 1.33/1.45 kN), followed by hinge-limit violations during recovery.
B additionally contacts an outer-chain mount during powered-off holding.
Do not interpret the observed final descent as unimpeded free fall or these
tests as successful rack integration.

The contact records also expose a distinct startup issue: unspecified jaw
coordinates collapse both precision jaws to zero at articulation reset,
causing large initial contact impulses. `initialize_prismatic_states` now
derives selected initial joint coordinates from authored geometry before
reset, without altering drive targets, body poses, the plug or collisions.
This is applied only in new brake probes/assemblies; old evidence is intact.

Second probes raise the fixture from lift −0.32 m to −0.28 m, shorten the
unsupported release to 0.14 s (still requiring >20 mm descent), and recover
through measured joint targets and a two-second ramp. They add an explicit
robot-contact gate, including initialization. A/A002 and B/A002 remain overall
failures: A has no robot contact above 0.1 N, but its recovery reaches −2.347°
at a carrier hinge; B reaches −1.023° and still has outer-mount contacts
(8.01 N during holding, 8.71 N during recovery), plus target-cable contacts.
The initialization jaw-collision impulses are absent after the startup fix.
Changes to the test fixture are not evidence of a hardware fix.

C/A001 at 240 Hz has the same first-fixture fan impact. C/A002 at −0.28 m
still hits a fan during recovery: the coupled motors' finite force budget
cannot arrest the unsupported fall within the remaining clearance. It also
violates the carrier gate during holding (−2.063°) and recovery (−4.278°).
The matched C/A003/004 fixtures at −0.24 m avoid robot contacts above 0.1 N
at both 240/480 Hz. Scalar brake checks pass, with maximum drops
6.994/6.825 mm; the unchanged hinge gate still fails. A further 960 Hz probe
is a separate sensitivity test, not permission to declare convergence or
promote the C RJ45 controller to another rate.

The terminal 960 Hz probes A/A003 and C/A005 pass all declared gates,
including carrier angles and robot-contact checks, at their respective
−0.28/−0.24 m fixtures. Peak power-loss drops are 5.559/6.809 mm; releasing
the brakes produces 40.513/40.570 mm further descent with no motor gains.
This is a scoped success for the modeled unloaded midstroke test at 960 Hz,
not convergence, calibrated emergency stopping, full-stroke or payload
acceptance. The lower-rate failures remain part of the results. The normal
task runner now accepts an explicit 960 Hz sensitivity setting while keeping
its 240 Hz default and unchanged physical durations/30 Hz recording cadence.
Separate full-task960 Hz comparisons are terminal: A/A completes32.9104 s
with one insertion recovery; C/A fails grasp after two retries, with measured
aperture15.680 mm and lower-guide/housing contacts. These are preserved as
A/A v011 and C/A v010; do not infer task performance from the probe passes.

`b_a_brake_probe003` tests B/A v011's revised v8 carriers at960 Hz, lift−.28 m.
It passes scalar holding and carrier gates:5.7252 mm maximum drop, about
0.000060 mm final drift and40.5581 mm further descent with released brakes.
It remains an **overall failure**: DepthRail1 hits baseline target-cable links
11/13 during the unsupported release/arrest (0.7773/0.4251 N impulse/dt
estimates). The prior outer-carrier-mount contacts are absent from this run.
This changed route/rate is not a controlled proof of each change's effect,
and removing the cable/contact gate is not a fix. Existing brake geometry is
reused on loading a brake-equipped package, rather than installed twice.

## Powered task integration

`run_reference.py --motor-brakes` installs the geometry before reset and
records the released brake runtime during normal powered manipulation. Saved
brake-equipped scenes automatically bind the runtime on reload. Packaging
includes the hardware report, startup states and tested source. These three
new full-rack trials passed the task and timed carrier gates:

| Saved version | Rate | Cycle | Recovery / seat nudge |
|---|---:|---:|---|
| A/A v010 (`a_a_brakes001`) | 480 Hz | 34.825 s | One insertion recovery / one nudge |
| B/A v009 (`b_a_brakes001`) | 480 Hz | 21.517 s | None / none |
| C/A v009 (`c_a_brakes001`) | 240 Hz | 23.446 s | None / one nudge |

These are three single feasibility trials, not randomized reliability or
power-off acceptance. Neither startup jaw state nor added hardware is present
in the older benchmark cohort; do not silently transfer its rates. Fresh
reload batch010 is terminal: all three reproduce successful tasks and pass
package/dependency validation. This confirms reloadability, not brake safety.

Example new-only power-loss probe on the VM:

```sh
/isaac-sim/python.sh -u rack_robotics/scripts/probe_brakes.py \
  --environment rack_robotics/environments/robot_c_gripper_a/v007 \
  --lift-position=-.24 --physics-hz 480 \
  --output rack_robotics/experiments/UNUSED-BRAKE-PROBE --allow-root
```

Remaining: stable holding/recovery over solver rates, collision-free B mounts,
full-stroke/all-tool/payload trials, brake-equipped task/reload evidence,
clearance/load/fastener/wiring audits and timestep sensitivity. Do not pool
these probes with RJ45 reliability trials or promote existing benchmarks to
the new geometry.
