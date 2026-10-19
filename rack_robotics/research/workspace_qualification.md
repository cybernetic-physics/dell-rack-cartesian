# Workspace qualification

Passing a port task does not establish rack-wide clearance. The saved C/A v019
assembly passes its single full cycle, independent reload and scoped midstroke
brake probe, but those paths exercise only a fraction of its travel.

`scripts/probe_workspace.py` introduces a separate full-rack **unloaded,
retracted travel probe**. The first supported fixture is C/A; this does not
qualify the other architectures or tools. It loads and hashes the saved package,
freezes the probe source, retains the rack/connector/cable geometry, and derives
the physical joint limits from the saved scene. Before the travel probe it seats
the connector with the baseline fixture and removes that fixture exactly as in
the task runner. All subsequent motion comes from robot joint targets and the
coupled CoreXZ motor efforts. Brakes remain released under motor power. There
are no runtime body-pose or velocity assignments.

The insertion axis stays at its retracted limit. Five height rows each visit
the left limit, midpoint and right limit in a continuous snake path, then return
up the far edge and to the authored park pose. Quintic ramps cap commanded joint
speed at 60 mm/s. The endpoints are the saved joint limits, not new shortened
limits chosen to avoid obstacles. Intermediate heights are sampled corridors,
not a claim about the entire rectangular volume.

Predeclared stop/acceptance gates:

- Any reported robot contact above 0.1 N, including self/carrier/rack/cable
  contacts, stops the probe. No contact allowlist is used. Force is the sum of
  normal contact-impulse magnitudes divided by timestep, not a force sensor.
- Moving joint-target error must stay below 10 mm; after each 0.75 s endpoint
  hold it must be below 2 mm. Measured joint travel has a 1 mm numerical margin.
- Both startup and travel carrier samples must meet the existing finite-state,
  1.5 mm anchor-gap and strict −1..31° angle gates. Sampling is 30 Hz; contacts
  and joint-state checks run every physics step.
- Every planned endpoint and the final park must be reached. An early stop is a
  failed, partially covered probe, not a smaller successful workspace.

Results preserve the planned path, completed endpoints, contact pairs, carrier
samples, measured rigid-body trajectory, joint/motor trace and final snapshot.
No original environment or earlier result is overwritten.

```bash
/isaac-sim/python.sh -u rack_robotics/scripts/probe_workspace.py \
  --environment rack_robotics/environments/robot_c_gripper_a/v019 \
  --output NEW_DIRECTORY --allow-root
```

This test does **not** establish extended-tool clearance, occupied-port access,
all tool/payload compatibility, continuous-volume collision freedom, fastener
strength or convergence. Existing articulation collision filters remain; the
separate unfiltered geometry audit is still necessary. Rack panels can make
some poses inside mechanical travel unusable. Such exclusions must be measured
and documented rather than forcing the robot through them or declaring the
whole rectangle usable.

## First full-rack raster and support correction

`c_a_workspace001` is a preserved **failure**, not pending: C/A v019 reached
9 of17 endpoints before a server collision at75.2 simulated seconds. The
three traverses at nominal TCP heights1.80,1.625 and1.45 m completed. During
the next descent at X≈0.21 m, `Carriage/DepthFrontBearingPost0` contacted
`Servers/XE9680_4/GPUFan10/Housing`. The first over-threshold normal-impulse
estimate was72.4453 N; final measured carriage/TCP height was1.35399985 m.
No subsequent lower-row or return path is qualified.

All startup/travel sampled carrier gates passed up to that collision:
startup120 samples, maxgap0.015905 mm, angles−0.36660..30.08626°;
travel2135 samples, maxgap0.016218 mm, angles−0.41966..30.06949°.
This evidence distinguishes a rack interference from a carrier instability.

The static fan spans Y=.4475..4725 m. The support post spans
Y=.471..479 m, leaving1.5 mm actual depth overlap, even at full tool
retraction. `insertion_stage.move_front_support_rearward` introduces the
separate `rearward_insertion_front_support_v1` candidate: all seven front
bearing, hanger, crossbar, post and bolt parts shift6 mm aft. No part is
deleted or collision-filtered. All masses, rails, shaft, tool and125 mm
insertion travel remain unchanged. The8 mm bearing now lies fully on the
existing shaft, with2 mm shaft protrusion beyond its front face; nominal
post-to-fan depth clearance becomes4.5 mm. This is custom geometry, not a
vendor-certified bearing assembly.

Unit checks retain full insertion travel and clear that specific fan plane.
The candidate must independently pass a task, fresh reload, broad unfiltered
box sweep and this same full raster before being preferred. Do not rewrite
v019's failure or shorten the raster to make the new candidate pass.

## Revised support: hanging-cable contact remains

`c_a_workspace002`, using C/A v020, is also a terminal **failure**. It
reaches 10/17 endpoints at 480 Hz, including the right-hand endpoint at
TCP height 1.275 m, clearing the previously obstructed descent. During the
next horizontal move toward center, cable Link18 touches
`Carriage/DepthFrontBearingHanger`: peak normal-impulse estimate 0.102623 N,
57 contact reports, minimum separation −0.021678 mm. The unchanged 0.1 N
contact gate stops travel at 79.927083 simulated seconds. All sampled startup
and travel carrier gates pass up to the stop. The contact is small but is
not silently excluded or reclassified as a passing full workspace.

The support correction therefore fixes the specific server-fan interference,
not full rack coverage. Hanging cable routing and the raised front support
still need engineering review. The original cable geometry and collisions
remain active. A physical routing solution or explicitly measured unusable
workspace is required before a broader clearance claim.

The probe runner now also supports saved A/A precision-tool assemblies with
motor brakes and service carriers. A uses its original prismatic drives;
C retains coupled CoreXZ forces. Both use the same full-limit raster,
speed, tracking and contact gates. This harness extension is not evidence
that A passes travel, and it does not qualify B or the other tools.

## Further setback candidate

`cable_clearance_insertion_front_support_v2` is an explicit alternative,
selected with `--rearward-insertion-support --cable-clearance-front-support`.
It shifts the same seven parts 11 mm from their original positions, 5 mm
farther than v1. No mass, joint travel, collision, cable, or contact gate changes.
At the retracted pose the hanger front face is Y=0.482 m, approximately
3.9 mm behind the measured cable center plus its nominal 3 mm radius at
the raster002 stop. This is local geometric clearance, not a swept cable bound.

At full 125 mm insertion the bearing plate still clears the hanger by 1 mm;
the support bearing remains on the unchanged shaft with 7 mm front protrusion.
Unit checks cover that gap and all supported box pairs of the saved C/A v020
robot with carrier mounts. Separate full-rack manipulation and raster trials
must establish the candidate's actual behavior; no old result is relabeled.

`a_a_workspace001` on A/A v015 is now terminal: it stops at 79.816667 s,
10/17 endpoints, on the same Link18/hanger pair. Its peak estimate is
0.104452 N and minimum separation −0.134678 mm. All sampled carrier gates
pass. This independently identifies the shared insertion support/cable
interface as an obstruction on both architectures; it does not justify
disabling cable contact or shortening either raster.

`c_a_cable_support001` is a full-rack 480 Hz task pass, preserved as
C/A v021: 21.516667 s, no recovery or seating nudge, maximum cable gap
0.018250 mm, all eight carrier gates passing. The supported robot-box sweep
still passes 4,154 pairs. `reload-campaign024` and `c_a_workspace003` are
separate fresh-session and unchanged-raster checks, launched but not yet
claimed complete at launch. The earlier v020 benchmark continues on its frozen inputs.

## First complete retracted-raster pass

`c_a_workspace003` is terminal and passes all **17/17** endpoints on C/A v021,
including the lower row, far-edge ascent and park return, in 139.25 simulated
seconds at 480 Hz. No robot contact exceeds 0.1 N; all tracking, finite-state,
joint-limit and carrier checks pass. The 120 startup samples have maximum
gap 0.013703 mm and hinge range −0.37766..30.07498°. The 4,057 travel samples
have maximum gap 0.016838 mm and range −0.42493..30.08363°. Earlier failed
rasters remain intact.

Fresh reload024 reproduces v021's manipulation in 21.516667 s without
recovery or seating nudges. All 107 package hashes, 11 layers and 150 asset
dependencies verify with no unresolved references. This qualifies the named
precision-tool task/raster, not arbitrary payloads, extended-tool motion or
continuous-volume clearance.

B/A now has a separate `retracted_independent_boom_raster_v1` plan: each of
five heights visits a 3×3 grid of independent outer/inner positions, followed
by ascent and park (47 endpoints). Summed TCP X alone would miss different
member positions at the same tip location. Each raster leg changes one joint;
contact/tracking/carrier gates and per-joint speed limits remain unchanged.
This is a harness capability, not a B travel result until actually executed.

## A and B terminal travel results

`a_a_workspace002` (A/A v016) now passes 17/17 endpoints in139.25 simulated
seconds at480 Hz. Startup120 samples: maxgap0.017164 mm, angles
−0.36219..30.06324°. Travel4057 samples: maxgap0.018305 mm, angles
−0.43507..30.07703°. All contact, finite-state, limit, tracking and carrier
checks pass. Fresh reload025 independently reproduces its complete task.

`b_a_workspace001` (B/A v014) passes **47/47** endpoints in214.679167 s
at480 Hz. Startup120 samples: maxgap0.015995 mm, angles
−0.37145..30.04039°. Travel6320 samples: maxgap0.017955 mm, angles
−0.34168..30.05344°. All checks pass, including return to park. Reload025
also independently reproduces B/A's task. These complete the three named
precision-tool retracted rasters; they do not establish continuous-volume,
extended-tool, arbitrary payload or other-gripper clearance.

## Specialized-tool coverage

The same probe now supports the saved C-type specialized gripper. It uses
that tool's original reference drives and authored startup state, not the
precision tool's jaw-state initializer. Raster geometry, speed and all gates
are unchanged. This extension does not accept the RG2 assemblies.

`a_c_workspace001` on A/C v005 passes17/17 endpoints in139.25 simulated
seconds at480 Hz. Startup120 samples: maxgap0.015157 mm, hinge range
−0.36357..30.05910°. Travel4057 samples: maxgap0.017097 mm, range
−0.42952..30.07915°. Contact, tracking, finite-state, limit and carrier checks
all pass. This establishes a separate specialized-tool retracted raster,
not a transfer of the precision-tool result.

`b_c_workspace001` is now terminal: B/C v004 passes47/47 endpoints in
214.679167 s at480 Hz, including the upper-edge return and authored park.
Startup120 samples: maxgap0.015584 mm, range−0.36552..30.05626°;
travel6320 samples: maxgap0.017621 mm, range−0.33757..30.05790°.
All contact, tracking, finite-state, limit and carrier gates pass. All five
current nominally successful combinations therefore have independent passing
retracted rasters; this does not establish extended-tool or populated-row
coverage. The separate occupied-port screen remains necessary.
