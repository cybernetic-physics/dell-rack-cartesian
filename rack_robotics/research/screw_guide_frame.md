# Architecture A: open guide and screw-drive frame

`screw_frame.py` adds the optional `dual_screw_open_guide_frame_v1`
geometry revision after open insertion-stage and brake installation, before
service carriers and physics startup. Joint anchors, limits, drive parameters,
TCP body poses, connector, latch and controller are unchanged.

The earlier A/A v014 box sweep identified 52 possible cross-body overlaps.
The corrected frame uses the same documented MGN12H open-channel abstraction
as [the CoreXZ frame](corexz_guide_frame.md), not solid blocks enclosing solid
rails. The 0.1 mm channel clearance is a simulation assumption; bearing races,
preload and compliance remain abstracted by prismatic joints.

## Dimensioned custom assembly

- A 470 mm bridge fits between the uprights. Lift blocks sit 50 mm above
  the bridge on stepped arms, 6 mm plates and a 20×20 mm M3 bolt pattern.
  Rail backing strips are 1 mm thick.
- Uprights retain X=±260 mm, with 40×40×980 mm sections. Lift rails are
  12×8×920 mm. Custom 12 mm wide stops leave 1 mm nominal clearance at
  the unchanged lift limits. Rack attachment centers move to Z=0.960 and
  1.925 m, retaining standoffs, clamps and bolts.
- Both lift screw axes are now outboard at X=±278 mm. Shafts span
  Z=1.010–1.900 m. Each motor/brake stack moves up 60 mm; the left stack,
  bearings, nut and supports also move outward 36 mm. Open nut blocks
  and forward connecting arms avoid crossing the guide rails. Superseded
  motor bolts are replaced by the existing brake mounting bolts.
- The traverse screw is 498 mm long, centered at bridge-local
  (9, −30, −80) mm. The motor, coupling and plate shift 6 mm outward.
  A modeled 5 mm output shaft and reducer connect the motor to the screw.
  These are custom coupling assumptions, not selected vendor hardware.
- A 6×48×50 mm open motor plate uses a 31 mm bolt pattern. Connected
  motor braces route in front of the guide. Open bearing blocks, a nut
  housing and connecting webs replace solid intersecting supports.
- `passive_service_carriers_screw_open_v1` reuses the open CoreXZ routing
  topology: 81 passive links, three independently anchored paths, unchanged
  0–30° hinge stops and connected-pair-only collision filtering.

Volume-based aluminum/steel mass deltas are applied to the original lumped
body masses. This is not a stiffness model, certified motor/brake selection,
manufacturing drawing, fastener strength calculation or verified inertia.
Those remain separate acceptance work.

## Preserved evidence

`a_frame_draft001` and `a_frame_draft002` preserve rejected **static** geometry
with 17 and 5 possible overlaps, respectively. They are not physical full-rack
tests. No previous configuration is overwritten.

`a_a_screw_frame001` is a full-rack A/A task at 480 Hz, saved as **A/A v015**.
It completes in 32.922917 simulated seconds with one insertion recovery and
no seating nudges. The first seating attempt remains in the trace; it is not
reported as first-attempt success. Maximum cable anchor gap is 0.018250 mm.
All eight startup/task carrier gates pass, and the integrity audit retains
38 dynamic connector/cable bodies and 133 connector/socket colliders, with
no scripted plug-retention joint.

The saved scene's full-joint-limit box sweep passes 6,791 cross-body pairs
across 138 supported parts, including 17 carrier-mount parts. It excludes
non-box geometry, dynamic carrier links, rack and tool articulation; it is
not a complete collision or buildability certificate. Fresh reload, full
travel, power-loss holding, other tools and randomized reliability are
independent gates, not implied by this single successful task.

`reload-campaign023` has now independently reproduced the complete task with
the same 32.922917 s duration and single insertion recovery. Its validator
checks 107 package file hashes, 11 USD dependency layers and 150 assets,
finds no unresolved dependencies, and verifies packaged source against the
original trial. Preservation audit016 includes this version: 73 saved scenes
independently loaded, 70 declared outcomes reproduced, with the same three
historical exceptions. This does not establish randomized reliability.

The further front-support setback is tested separately as
`a_a_cable_support001`, saved A/A v016. It also passes in 32.922917 s with one
insertion recovery, no seating nudges, maximum cable gap 0.018250 mm and all
startup/task carrier gates. The supported-box sweep retains 6,791 clear pairs.
Reload025 and `a_a_workspace002` test this version independently; v015's
failed travel is retained rather than relabeled.

Reproduce a new development attempt (never reuse an existing output):

```bash
/isaac-sim/python.sh -u rack_robotics/scripts/run_reference.py \
  --robot A --gripper A --physics-hz 480 --hardware-detail \
  --open-insertion-stage --open-screw-frame --service-carriers \
  --motor-brakes --forward-latch-neck --rearward-insertion-support \
  --output NEW_DIRECTORY --allow-root
```
