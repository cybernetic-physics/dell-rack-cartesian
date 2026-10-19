# CoreXZ guide/frame correction

The original full-travel screen found 16 box intersections in C/A's revised
insertion-stage assembly. In particular, the 540 mm bridge crossed the two
uprights, solid guide-block envelopes enclosed solid rails, and the raised
insertion plate could reach an upper rack standoff. Adjacent-body collision
filtering does not make these physically valid interfaces.

## Cross-section and attachment

`gantry_frame.py` implements an explicit, optional geometry revision for
architecture C. It does not change joint anchors, travel, drive/controller
parameters, CoreXZ motor coupling, the tool TCP, connector or latch.

The [HIWIN MGN block table](https://www.hiwin.de/en/Products/Linear-guideways/Blocks/Miniature-guides/MGN-HIRES-series/c/4500)
gives MGN12H overall assembly height 13 mm, width 27 mm, length 45.4 mm,
bottom clearance H1=3 mm, and a 20×20 mm M3 mounting pattern with 3.5 mm
thread depth. The full [HIWIN guide catalog](https://www.hiwin.com/wp-content/uploads/HIWIN-Linear-Guideway-Catalog.pdf)
lists the 12×8 mm rail section and 54 g block mass used by the existing model.
An earlier catalog copy is preserved at `sources/hiwin_linear_guideway.pdf`.

The replacement block comprises three collision-enabled solids with an open
12.2 mm channel over the rail. Its 0.1 mm nominal clearance is a simulation
assumption, **not** a vendor bearing clearance. Recirculating balls, preload,
grooves and elastic stiffness remain abstracted by the existing prismatic
joint; this is not detailed vendor CAD. Existing allocated bearing/lumped-body
mass is retained rather than adding three new bearing masses.

The rear bridge is shortened to 470 mm. Connected stepped brackets reach
the lift blocks, which sit 50 mm above the beam to expose the actual mounting
pattern without obstructing the traverse blocks. Four nominal M3 bolts per
block pass through a 6 mm plate and engage 3.5 mm into its crown. Bolt holes,
threads, preload and joint strength are not resolved contact geometry.
One-millimetre rail backing strips close the previous mounting gaps. Stops
sit behind the traverse path with 1 mm nominal clearance at the unchanged
lift limits. The complete upper rack attachment (standoff, clamp and bolts)
moves up 25 mm to the top-crossmember region.

Beam-volume mass changes use an explicit aluminum proxy against the original
lumped mass. New bracket/shim/bolt volumes add mass. These calculations are
not validated inertias, structural ratings or rack fastener qualification.

## Preserved physical evidence

`c_a_frame001` / C/A v014 uses `corexz_open_guide_frame_v1`. It fixes the guide
cross-sections and beam but retains a lower-block connection without the final
accessible bolt pattern. The full supported robot-box sweep checks 2,625
cross-body pairs and passes. Keep this as a development variant, not final
manufacturing acceptance.

`c_a_frame002` / C/A v015 uses `corexz_open_guide_frame_v2`, including the
raised blocks, mounting plates, bolts and stepped brackets. Its full supported
robot-box sweep checks 2,909 pairs and passes over all independent Cartesian
joint limits. A first bracket candidate crossed the belt-clamp plate; reducing
its depth to 5 mm creates 1 mm nominal clearance. The regression includes that
previously omitted clamp plate.

Both full-rack 240 Hz tasks pass in 21.5375 s without recoveries or seating
nudges. Maximum cable anchor gap is 0.052714 mm; neither startup nor task
records a robot–robot contact above 0.1 N. They are separate preserved scenes
with separate source snapshots. `reload-campaign016` checks fresh physical
execution and dependencies; its terminal summary verifies both passes.

These screens cover axis-aligned boxes on the Cartesian bodies only. Meshes,
cylinders, tool articulation, the original rack, dynamic chain links and
elastic deformation remain explicitly outside this screen. Passing it does
not establish full collision clearance or buildability.

## Compatible carrier integration

The old carrier routes remain unchanged for old assemblies. The new
`passive_service_carriers_corexz_open_v1` route is enabled explicitly only for
the v2 CoreXZ frame. It retains 81 passive links and the same bending limits,
mass assumptions and connected-pair-only exclusions.

The lift mount leaves the raised block plate sideways before descending, so
it does not cross the traverse block sweep. The traverse moving support rises
from the center of the new top bar and crosses rearward at +115 mm, inside the
uprights and below the top crossmember. The insertion loop is raised to
125 mm over the carriage datum; its moving mount stays within 24 mm of the
tool centerline, clear of the upper standoffs. The full assembly preflight
passes all 4,154 supported box pairs including the 17 bracket solids.

`c_a_frame_carriers001` / C/A v016 completes the integrated 240 Hz task in
21.5375 s without recovery/nudge. Timed carrier gaps peak at 0.01811 mm and
hinges span −0.66723–30.15447°. Startup reaches −1.49353°, outside the existing
one-degree tolerance; its 0.03166 mm gap is small. No startup/task robot–robot
contact above 0.1 N is recorded. Its historical overall pass uses the earlier
timed-only gate and is NOT full carrier acceptance.

New runs use `carrier_validation.py`: both startup and timed samples must
pass the same gates. Missing/non-finite data fails closed. Existing results
are not rewritten. `c_a_frame_carriers480_001` tests the same geometry at
480 Hz under this stronger combined gate. Both startup and task carrier checks
pass, but physical latch release fails; it is preserved as C/A v017. The
specialized-tool480 Hz integration `c_c_frame_carriers001` / C/C v002 also
passes the combined carrier gates but fails alignment. Its supported
robot-box sweep passes; neither failure is waived. The precision-tool contact
diagnosis and isolated geometry experiment are in
[latch_tool_clearance.md](latch_tool_clearance.md).
No convergence or global solver-rate promotion is implied. Further all-tool testing, full-travel dynamics,
power-loss, rack/non-box/fastener/load audits and randomized benchmarks remain.

```bash
/isaac-sim/python.sh -u rack_robotics/scripts/run_reference.py \
  --robot C --gripper A --physics-hz 240 --hardware-detail \
  --open-insertion-stage --open-gantry-frame --service-carriers --motor-brakes \
  --output NEW_DIRECTORY --allow-root
```
