# Passive service-carrier development

This is additional mechanical hardware, not the manipulated Ethernet cable.
`service_carriers.py` adds attached, dynamic, collision-enabled carrier chains
to new drive-connected robot versions before physics starts. It does not edit
the immutable baseline or previously benchmarked environments.

The corrected CoreXZ open-frame assembly now has an explicit separate route,
documented in [corexz_guide_frame.md](corexz_guide_frame.md). Old A/C v4 and B
v8 routes remain unchanged; they are still rejected on incompatible raised
insertion stages. The new route requires `corexz_open_guide_frame_v2` and
must pass its own dynamic/startup/full-travel tests.

## Dimensional reference and limitations

The [igus Series06 catalog](https://igus.partcommunity.com/3d-cad-models/FileService/File/igus/e_ketten/system_e2micro_e_ketten/serie_06/series_06_english.pdf)
identifies06.20.038.0 with20 mm pitch,20×10.5 mm internal passage,
27×15 mm outer section,38 mm bend radius and approximately0.17 kg/m chain
mass. It lists060.20.12PZ end mounts. Its clearance guidance includes camber;
our ideal rigid links do not reproduce this behavior. No vendor CAD, current
price, qualified installation or commercial performance is claimed.

Original simplified ring links have four solid collision walls and an open
wire passage. A six-link bend has38.637 mm polygon radius. Revolute stops
permit0–30° bending; each end is fixed to the appropriate actual robot body.
Only directly connected link/attachment collision pairs are excluded. No
carrier drives, kinematic links or runtime pose overrides are used. Fill mass
is an explicit assumed0.04 kg/m; individual service wires, their friction and
tension are **not** simulated. Brackets are custom8 mm square aluminum struts
with volume-derived additive mass, not rated fastened assemblies.

A/C each have81 links:38 lift,28 traverse,15 insertion. B has97 links:38 lift,
22 for each independent telescopic stage,15 insertion. Full-stroke/rack
clearance, repeated task validation and full mounting/load
audits are still required.

## Preserved experiments

| Attempt | Saved version | Outcome |
|---|---|---|
| A/A carriers001 | A/A v006 | Failed approach; initialization carrier gaps78 mm and gross hinge violations |
| C/A carriers001 | C/A v005 | Failed approach; initialization carrier gaps64 mm and gross hinge violations |
| A/A carriers002 | A/A v007 | Startup corrected; blocked insertion by its own carrier mount; lift mount crosses opposite carrier leg |
| C/A carriers002 | C/A v006 | Same insertion/lift interference; upper traverse mount also contacts fixed top crossmember |
| A/A carriers003 | A/A v008 | Full cycle and timed carrier checks pass; fresh reload passes |
| C/A carriers003 | C/A v007 | Full cycle and timed carrier checks pass; fresh reload passes |
| B/A carriers001 | B/A v004 | Rear fixed bracket intersects lift upright; carrier routes interfere |
| B/A carriers002 | B/A v005 | Front route strikes rack side panel/post/standoff; mount crossings interfere |
| B/A carriers003 | B/A v006 | Manipulation completes; hinge-limit gate fails; initial mount screen finds two3 mm overlaps |
| B/A carriers004 | B/A v007 | Initial mount screen passes; manipulation completes but hinge-limit gate still fails |
| B/A carriers480_001 | B/A v008 | Same geometry at480 Hz passes task and timed carrier checks; startup also within the same numerical bounds; fresh reload passes |

The first revision left Cartesian startup coordinates unspecified. The
authored traverse pose is150 mm, while a reduced-coordinate articulation can
initialize unspecified state at zero. Revision2 explicitly authors only
initial Cartesian joint states from measured USD joint anchors, before physics
starts. A/A's first recorded initialization gap fell to0.01523 mm and maximum
hinge angle to30.124°. This is evidence of improved startup, not a successful
carrier system: later collision-driven hinge failures remained.

Revision3 routes moving brackets outside each chain's bending plane and moves
the A/C traverse chain below the bridge, behind the motors. Unit geometry tests
cover the insertion mount against the fixed first link throughout125 mm travel
and the traverse moving mount against C's two crossmembers throughout700 mm
lift travel. These narrow tests do not replace full dynamic collision checks.
`a_a_carriers003` and `c_a_carriers003` completed in21.5375 s and23.4458 s
respectively. A/A required no seating nudge; C/A required one. Neither required
recovery. Their timed carrier anchor gaps remain below0.01704/0.01860 mm,
hinge ranges are−0.7046–30.1670° /−0.6583–30.1721°, and neither reports positive
robot–robot contacts during the task. `reload-campaign006` repeats both physical
passes with package/dependency verification. Each adds0.3402 kg chain/fill plus
approximately0.27075 kg modeled brackets to its drive-connected predecessor.

These are **timed task** passes, not full carrier acceptance. Startup traces
reach minimum hinge angles−1.303° /−1.456°, outside the timed gate's one-degree
tolerance. Do not omit those startup transients from a final stability assessment.
Neither version has randomized carrier-equipped trials or complete stroke/door
clearance, load, wire-tension, brake or fastening validation.

B's front route was rejected after actual rack contact. Its later rear routes
use separate planes atY=.92/1.02 m and longer brackets, increasing rear service
space requirements. Bracket offsets and staggered crossings avoid the initial
mount overlaps, but the full stroke remains a separate check. The new
`audit_carrier_mounts.py` screens actual saved initial USD solids, **including
collision-filtered adjacent robot bodies**. It finds two3 mm overlaps in
carriers003; carriers004 passes317 distinct-body bracket-pair checks. Audits and
their source snapshots are packaged. This is not a full rack/chain clearance test.

B/A carriers004's task completes but its minimum sampled hinge angle is−1.21156°,
so the overall result remains failed. Carrier mount/link contacts occur during
approach, including a16.69 N pair impulse/dt estimate; this is not a calibrated
physical force. `b_a_carriers480_001` tests the same saved v007 geometry at480 Hz
instead of240 Hz, without loosening the limit gate. It completes21.51667 s with
no recovery or seating nudge, max timed carrier gap0.01116 mm and hinge range
−0.33861–30.04878°. Startup gap is below0.00986 mm with angles−0.32269–30.04381°.
No positive robot-self contact pairs are reported during the timed cycle.
The static317-pair mount screen passes unchanged geometry. This is a favorable
paired timestep-sensitivity result, **not** a convergence, strength or hardware
reliability claim. The new480 Hz version is preserved as B/A v008 and its
fresh reload passes in `reload-campaign008`, with intact package/dependencies.
Matching A/C480 Hz comparisons are terminal: `a_a_carriers480_001` reports a
pass, while `c_a_carriers480_001` fails latch release after retries (measured
hook height4.97564 mm, not clear). Detailed trace review, packaging and reload
are pending. Do not infer universal task improvement or promote480 Hz globally.

`reload-campaign005` loads all four first A/C failures with intact dependencies.
The second-revision failures reproduce; the unstable first-revision failures
remain failures but do not satisfy the strict same-phase/error validator.
For A/A v006, reload reaches alignment rather than failing approach. Do not
count these as reproduced outcomes or rewrite their original evidence.
B's four saved failures all reproduce and pass dependency/package checks in
the completed `reload-campaign007`.

Each attempt freezes its exact source, initial/final USD, measured trajectory,
contact records and carrier metrics. Revision2 onward also records startup
body trajectories. Task success is gated on finite carrier state, sampled
anchor gaps below1.5 mm and hinge angles within one degree of their limits.
Sampling is30 Hz; it is not a continuous-time strength/stability certificate.
The failed scenes require fresh-session reload verification as well as packaging.
Large impulses in invalid configurations are solver responses, not load ratings.

## Full-travel bracket audit and remaining stage interference

`audit_carrier_mounts.py --sweep` now checks exact axis-aligned bracket overlap
existence over every independent Cartesian joint interval, without moving
the stage. It derives the initial coordinates from joint anchors and rejects
unsupported/rotated geometry. It includes pairs whose joint disables contact.
The original A/C v3 routes have three possible bracket overlaps; B v7 has one.
These were missed by an initial-position-only screen.

A/C v4 lifts the traverse crossing above the bridge. B v8 separates the
telescopic crossings laterally and lowers the moving crossings below the
chain legs. All three move the insertion moving attachment away from the
fixed vertical post. New immutable full-rack trials and saved packages:

| Attempt / saved version | Rate | Cycle | Timed carrier gap / hinge range |
|---|---:|---:|---|
| `a_a_carriers004` / A/A v012 | 960 Hz | 32.9104 s, one insertion recovery | 0.01248 mm / −0.1112–30.0429° |
| `b_a_carriers006` / B/A v011 | 480 Hz | 21.5167 s, no recovery/nudge | 0.01115 mm / −0.3196–30.0419° |
| `c_a_carriers004` / C/A v011 | 240 Hz | 23.4458 s, one nudge | 0.01732 mm / −0.6512–30.1777° |

All pass the **mount-to-mount** travel screen (91/357/91 pairs), powered task
and timed carrier gates. Startup A/B also stays within those numerical
bounds, but C still reaches −1.4569°. No task robot–robot pair exceeds0.1 N.
Reload-campaign012 checks these three packages separately; inspect its actual
summary before claiming fresh-session acceptance.

The broader `--sweep --robot-boxes` screen disproves full-travel integration:
A/B/C have16/2/8 possible bracket-to-robot-box overlaps, checking936/1718/863
pairs. Frozen evidence is `mount_robot_box_sweep001.json` and its source folder
inside each attempt. The narrower passed screen must **not** override this
failure. Cylinders, meshes, unsupported owners, dynamic links, rack geometry,
deflection and fastener strength are explicitly outside this exact-box check.
`--all-robot-box-pairs` adds non-carrier stage-to-stage box pairs; its separate
reports are `robot_box_sweep001.json`.
Those broader reports check2499/2905/2156 pairs and flag83/45/50 possible
overlaps for A/B/C. Some pairs involve simplified guide/bearing envelopes;
they require explicit geometric interpretation, not automatic clearance
exemptions. The insertion adapter/plate/post intersections below are solid
body interference, not a rail deliberately passing through a bearing bore.

Further inspection finds actual insertion-stage solid overlap at full
retraction: Carriage/Plate (A/C) or ToolSupport (B) shares volume with the
moving adapter and bearing plate. The74 mm bearing plate also sweeps across
the front hanger's posts at x=±31 mm. Both are between adjacent rigid bodies,
so absence of contact reports cannot establish clearance. A proper open
carriage/support cross-section and revised bearing/hanger arrangement are
required before a buildability claim. `carrier_route_draft001` preserves a
rejected pre-physics bracket-only attempt; it is not promoted to the builder.
Current tested builder revisions remain A/C v4 and B v8, with known failures.

The earlier960 Hz comparisons remain separate: A/A `a_a_brakes960_001`→v011
passes32.9104 s; C/A `c_a_brakes960_001`→v010 and B/A
`b_a_carriers005`→v010 fail grasp at approximately15.680 mm aperture after
two retries. Contacts show the lower guide ramps bearing against the housing,
not jaws reaching a secure grasp. The closed command is present throughout;
do not relax the aperture gate or infer that960 Hz universally improves
manipulation. Reload-campaign011 preserves those declared outcomes.
