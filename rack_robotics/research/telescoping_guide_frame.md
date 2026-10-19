# Architecture B: open nested-boom interfaces

`telescoping_frame.py` adds `telescoping_open_guide_frame_v1` without changing
body/TCP poses, joint attributes, two independent 200 mm extensions, 700 mm
lift or 125 mm insertion travel. Dimensions below are custom design choices,
not certified vendor-stage specifications.

The B/A v013 sweep found 26 possible cross-body overlaps: the upright and
guide envelopes crossed the lift boom, solid blocks enclosed rails, and
nested stops/motor plates crossed moving members. Collision exclusions did
not resolve those physical intersections.

## Dimensioned correction

- Fixed spine and lift rails move 20 mm rearward. Two 2 mm backing strips
  meet the rails; a 100×6×160 mm lift plate joins four open MGN12H-envelope
  blocks with mounting bolts. Block dimensions and assumed 0.1 mm channel
  clearance reuse the [documented guide model](corexz_guide_frame.md).
  Stops leave 1 mm nominal travel margin. Rack standoffs extend 20 mm while
  rack-side clamps and bolts stay fixed.
- Lift screw axis moves to X=−320 mm, Y=815 mm. Open bearing/nut housings
  and connected arms join the spine and lift plate. The motor/brake stack
  rises 14 mm on a connecting bridge. The 946 mm screw ends at Z=1.946 m;
  the brake shaft starts at 1.948 m. Both engage the open coupling, with a
  reducer for the 5 mm shaft and a 2 mm gap between shaft ends.
- Each driving boom/rail is 310 mm long, supporting the complete two-block
  95.4 mm bearing envelope at full extension. The terminal boom remains
  300 mm. Horizontal blocks, 1 mm shims and 4 mm backplates form open
  guide interfaces. Stops at local X=−296.7/+6.7 mm leave 1 mm block clearance.
- Horizontal screws move below the booms to local Z=−60 mm. Open bearing
  blocks/webs and nut housings/webs connect successive stages. Connected
  6×48×50 mm motor plates clear the neighboring member. Separate shaft
  ends have a 4 mm gap inside each coupling, with motor-side reducers.

Volume-based mass deltas before carriers: Frame +0.53980 kg,
LiftCarriage +0.21942 kg, MiddleBoom +0.64336 kg, Carriage +0.22371 kg.
These are aluminum/steel proxies against prior lumped masses, not weighed
hardware or validated inertia/stiffness models. Shafts, couplings and mounts
remain proposed custom interfaces, not approved manufacturer assemblies.

## Carriers and evidence

`passive_service_carriers_telescoping_open_v1` retains four passive paths:
lift, independent outer and inner extensions, insertion. The lift bracket
leaves the plate sideways/rearward before dropping. The inner fixed bracket
crosses below the raised insertion motor before rising at its far endpoint.
Insertion uses the raised open-stage mounts. Old B v8 routing is unchanged.

Preserved static drafts:001 fails with 15 overlaps;002 with carriers fails
with two bracket/motor overlaps;003 passes **11,761** supported cross-body
box pairs across all independent joint limits, including carrier mounts.
These copied root layers and frozen sources are not full-rack physics trials.

Six regressions cover original/revised interference, unchanged joints/body
poses, full-travel block support, compatible carrier mounts, coaxial separated
shaft ends, positive masses and guards. The box screen excludes rack,
non-box parts, dynamic links and articulated tools. Full-rack task, travel,
brake behavior and load estimates remain separate evidence. Threads, races,
preload, fastener compliance and beam bending are explicit model limitations.
The mechanism still needs substantial side/rear service space; it does not
disappear into a rack post or establish closed-door compatibility.

## First full-rack task

`b_a_telescoping_frame001` passes at 480 Hz in 32.922917 simulated seconds,
with one insertion recovery and no seating nudges. All eight startup/task
carrier gates pass; maximum cable anchor gap is 0.018353 mm. The actual full
scene's supported-box sweep passes the same 11,761 pairs. Saved B/A v014
includes the tested source, scene, hardware/carrier reports and recorded
trajectory. Reload025 and the independent-extension workspace probe are
separate ongoing tests; task success alone does not qualify them.

```bash
/isaac-sim/python.sh -u rack_robotics/scripts/run_reference.py \
  --robot B --gripper A --physics-hz 480 --hardware-detail \
  --open-insertion-stage --open-telescoping-frame --service-carriers \
  --motor-brakes --forward-latch-neck --rearward-insertion-support \
  --cable-clearance-front-support --output NEW_DIRECTORY --allow-root
```
