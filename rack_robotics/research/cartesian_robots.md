# Cartesian hardware research and architecture selection

This file preserves discovery and implementation checkpoints. For current
tested versions use the [recommendation](current_design_comparison.md); for
the latest primary-source checks see [source review001](source_review001.md).

Research date: 2026-10-16. Catalog specifications below are not measurements of
our proposed assemblies. Unknown prices and licenses remain unknown.

## Broad discovery and second-order findings

| Candidate | Verified specifications / assets | Rack adaptation and disposition |
|---|---|---|
| [igus DLE-RG-0001](https://www.igus.com/product/dle-rg-0001?artnr=DLE-RG-0001) XYZ | 500×500×100 mm workspace; 2.5 kg load; approximately 0.8 mm precision; 0.5 m/s maximum. ZLW-1040/1080 belt axes, GRW rack-and-pinion boom, NEMA23/17 motors; dryve D1/robot controller options. CAD download offered, redistribution license not verified; price not exposed. | Catalog accuracy is coarser than our 0.22 mm seating tolerance. Shorter configured axes, local alignment/compliance and rack adapters are necessary; do not treat stock unit as drop-in. No matching official gantry USD found in targeted search. |
| [Festo EXCM-30/40](https://www.festo.com/media/catalog/204451_documentation.pdf) coupled-belt planar gantry | EXCM-30: X 90–700 mm, Y 110–526 mm, ±0.05 mm repeatability; 2 kg vertical / 3 kg horizontal rated load. Vertical mounting requires brakes. Two fixed motors; MUE mounts, EADC-E11 adjustment, EAHT-E9 insertion-axis adapter, EADH-U-3D carrier. At 400/360 mm strokes, envelope L1=533, B1=490, H1=58.8 mm. Vertical mounting below 500 mm X requires four mounts per profile. CAD offered; license/price unknown. EXCM-40 is horizontal-only in this catalog. | EXCM-30 is promising; larger 40 is not accepted simply by rotating it. Motor/brake, depth-stage and tool masses consume load allowance. External stand-offs needed behind rack. A custom CoreXY frame offers similar low-moving-motor benefit with controllable envelope, but is not a certified EXCM replica. |
| [OpenBuilds C-Beam XL](https://builds.openbuilds.com/builds/c-beam%C2%AE-xlarge-linear-actuator.7424/) modular screw gantry | 250/500/1000 mm variants give 115/365/885 mm travel. Wheel-guided, NEMA23, external wide wheel spacing; XY assembly instructions and SketchUp drawings linked. [Control documentation](https://docs.openbuilds.com/doku.php?id=docs%3Ablox%3Aexamples-actuator) identifies TR8×8 four-start lead screw and BLOX integration. Price not verified. | 500 mm XL travel misses the 375 mm port-center span. Longer cut-to-length rail or non-XL carriage fixes coverage; larger wheels/plates consume space. Good buildable independent-axis reference, but not automatically submillimetric under load. |
| [OpenBuilds parametric parts](https://github.com/matthew-yates/openbuildsParts) | Downloaded OpenSCAD rail, motor, plate, wheel, spacer and nut models. CC BY-SA 4.0 attribution in repository. Geometry library, not articulated simulator. | Reusable frame/drive geometry; requires our own joints, inertia, mounts and collision setup. Useful for custom rear gantry A. |
| [HIWIN MG miniature guides](https://www.hiwin.com/wp-content/uploads/Linear_Guideway-E.pdf) | MGN/MGW miniature ball guides; manufacturer dimension/load tables and [CAD portal](https://hiwin.com/products/linear-guideways/). Guide alone supplies no actuator, controller or positioning accuracy. No product price verified. | Compact guides permit a nested boom and slimmer carriages. Use two spaced blocks and compute cantilever moments; never substitute load capacity for positional accuracy. Proposed B needs screws/belts, motors and end stops in addition. |
| [Zaber X-LSM](https://www.zaber.com/products/linear-stages/X-LSM/specs) | X-LSM100A-S: 101.6 mm travel, 0.37 kg, <3 µm repeatability, 35 µm unidirectional accuracy, 26 mm/s, 55 N peak/25 N continuous thrust. Series centered load 250 N, pitch/yaw moment limit 4 N·m. Built-in controller. [Manufacturer price page](https://www.zaber.com/products/linear-stages/X-LSM) lists X-LSM100A(-S) from USD 2,610; accessories/tax excluded. | Strong short insertion-axis alternative; too short for full row transverse motion. Do not apply the 55 N peak force to a connector; software and compliant force limiting needed. Drawings route did not resolve in this pass; exact mounting CAD license unresolved. |
| [igus SLN variants](https://www.igus.eu/drive-technology/linear-axes-with-spindle/linear-modules/sln) | SLN-27 offers adjustable or spring-preloaded carriages; up to 250 mm stroke in listed variants, 10 N static axial / 40 N radial capacity. Motorized version has NEMA11, 28×28 mm interface; optional IK-0052/53 inductive switches. | Light short insertion alternative, but 10 N capacity is a material constraint. Preloaded variant preferable to basic econ slide; cannot carry a large gripper cantilever without separate moment validation. Price/CAD reuse rights unverified. |
| [IAI modular Cartesian](https://www.iai-automation.com/en/cartesian-robots.html) / [ICSB drawings](https://www.iai-automation.com/files/content/downloads/brochures/ICSB_Part2_3-Axis-System_eng.pdf) | Industrial 2–6 axis combinations, ball-screw modules, controllers and cable tracks; detailed model-dependent mounting drawings. | Professionally integrated option but not selected without a compact exact BOM and complete envelope. Smaller IK/ICSB variants are alternatives to oversized stock ICSA assemblies; accuracy/load cannot be assigned at family level. Quote/CAD licensing unresolved. |
| [Lexium PAS42](https://product-help.schneider-electric.com/Machine%20Expert/V2.1/en/PAS4XBHG/PAS4XBHG/ROBOTICS_Technical_Data/ROBOTICS_Technical_Data-5.htm) / [CAS cantilever](https://download.schneider-electric.com/files?p_File_Id=8641840577&p_File_Name=CAS3x_manual+V3.00_EN_07-2012.pdf&p_Reference=CAS3x_manual%2BV3.00_EN_07-2012&p_enDocType=User+guide) | PAS42 variants have substantial non-travel length (e.g. 396+stroke mm); CAS manual documents payload mounting/dowels. | Commercial cantilever concept is useful, but these envelopes are costly in a 600 mm rack. Nested miniature guides are the compact derivative to evaluate rather than shrinking vendor geometry. |
| [CoreXY reference mechanism](https://corexy.com/theory.html) | Two stationary motors and crossed belt paths; same-direction and opposite-direction motor motions produce orthogonal carriage motion. Reference drawings explain routing. No rack payload or accuracy certification. | Selected C: rear-plane CoreXZ plus short Y insertion. Requires tensioners, belt guards, gravity brake/counterbalance and force-coupled control, not two decorative motors on ordinary independently driven axes. |

## Proposed architectures: dimensions are design choices

Coordinates use the unchanged rack's X across, +Y rearward, Z up. The active
row has 25 mm pitch, X=±187.5 mm, Y=429 mm, Z=1660 mm. Rack frame is
600×1200 mm. These come from the frozen model, not a fresh rack survey.

**A — dual-supported screw gantry.** Two rear upright guide rails support a
horizontal bridge; a carriage traverses the bridge and carries a short insertion
slide. Target travel: X 420 mm, Z 650 mm, Y 120 mm. Use 20/40 mm extrusion,
miniature guides, screw/nut drives, NEMA17/23 motors, bearing supports and bolted
corner plates. Independent axis drives are the defining mechanism. Both rack
sides take bridge load; bridge can park above the active row. Derive motor limits
from chosen transmission; no catalog speed/accuracy claim for the custom build.

**B — side rail with nested boom.** A vertical carriage on one rear upright
carries two translating horizontal members, each approximately 300 mm long with
200 mm travel and 100 mm residual overlap, then a short Y slide. The 400 mm
combined X travel covers the row. Two spaced guide blocks per sliding interface
are necessary: one small block is not an adequate cantilever support. Model
each telescoping section separately. Retraction reduces the occupied span,
but does not make the entire mechanism disappear into a zero-width side bay.
Calculate bearing and rack-bracket moments using actual assembled tool mass.

**C — stationary-motor belt gantry.** A rear perimeter frame, two vertical guides,
moving transverse beam and carriage implement CoreXZ, with belt-driven coordinates
`a=x+z`, `b=x-z` and a short Y insertion stage. Model pulley/belt routes and
coupled generalized forces. Belts may be a documented lumped spring/transmission
approximation; independent X/Z servo drives disguised as belts are not accepted.
Target travel matches A. Fixed motors reduce moving mass; gravity holding and
cross-coupled compliance are its distinct costs.

## Shared integration gates

Selected miniature-guide dimensional reference: HIWIN catalog printed p.86
(PDF p.89), visually inspected. MGN12H assembly height 13 mm, block width 27 mm,
length 45.4 mm, mass 54 g; rail 12×8 mm, 0.65 kg/m, M3 mounting at 25 mm pitch.
Its listed static pitch/yaw moment is 36.26 N·m. These are guide ratings, not the
rating of an entire telescoping stage, its brackets, fasteners or rack.

All three must bolt to the rack structure using multi-point rear-rail brackets,
not the server sheet-metal lids. Include real screw heads, clearance holes,
spacers, mounting plates, stop blocks and serviceable motor/guide connections.
Place structural members rearward of existing power leads; long tool fingers
reach forward into the row. Exact Y stand-off follows the collision sweep and
tool depth, not aesthetic preference. The model has no verified closed rear-door
envelope: report the required envelope and treat operation as rear-door-open
unless a measured door-clearance check proves otherwise.

For each scene measure: X/Z reach; minimum body/tool clearance throughout motion;
rearward projection; blocked access/airflow area; parked envelope; mount reaction
and cantilever moment estimates; mass/payload budget; cable carrier sweep. Cable
guides must not make neighboring ports unreachable. The 16-port row is the first
task, not proof that all recessed server ports are reachable.

Finalists are provisional. A is the simplest reference build, B probes compact
parking versus cantilever stiffness, C probes coupled-belt dynamics and lighter
moving mass. No simulated reliability ranking exists yet.
# Architecture B prototype geometry checkpoint

The implemented B prototype uses two 300 mm nested members with separate 200 mm
prismatic travel, leaving 100 mm overlap at full extension. Two MGN12H-sized
blocks per horizontal interface have 50 mm center spacing and a combined
95.4 mm longitudinal envelope. This is a custom assembly using manufacturer
guide dimensions, not a vendor-qualified telescoping actuator.

The tool datum spans X=-200…+200 mm. At the parked X=-190 mm position, the
members and motor mounts project to approximately X=-550 mm: about 250 mm
beyond the 600 mm rack's left envelope. The parked mechanism does **not** vanish
into the side post. This is a real lateral-clearance and adjacent-rack constraint
to include in scoring. The depth slide/tool geometry is shared with A; the
booms are vertically offset 50 mm above the tool datum to clear its depth motor.

Assumed moving masses are 0.8 kg lift, 0.75 kg intermediate member and 0.65 kg
terminal member/depth stage, plus the selected tool. These are model estimates,
not weighed BOMs. Beam bending, bearing clearance, screw efficiency/backlash,
motor torque-speed curves and fastener/rack load ratings remain to be audited.
The axis drives are force-limited abstractions, not thread-contact simulation.
`b_a_attempt001` passed one full-rack cycle; this does not establish reliability,
dense-cable compatibility or the real hardware's structural performance.

## Architecture C transmission implementation assumptions

The CoreXZ prototype uses `a=x+z, b=x-z`, consistent with the same/opposite
motor motion described by the [original mechanism author](https://corexy.com/theory.html).
Its prismatic X/Z guide joints have **zero** position/velocity-drive gains.
The two elastic motor transmissions compute independently capped forces in
motor coordinates, mapped to carriage generalized force by the transpose
Jacobian: `Fx=Fa+Fb, Fz=Fa-Fb`. This conserves instantaneous mechanical power.
Gravity compensation is included inside the motor caps, not applied as an
unlimited separate upward force. Losing either motor therefore affects both
Cartesian axes; a physical negative-control test is required.

The controller applies joint **efforts**, not joint positions or body poses.
The installed Isaac Sim `SingleArticulation.set_joint_efforts` documentation
requires absent drives or zero stiffness/damping; this also agrees with
[NVIDIA's drive documentation](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/dev_guide/rigid_bodies_articulations/joints.html).

Prototype assumptions: 20-tooth/2 mm-pitch pulley (6.366 mm pitch radius),
8,000 N/m effective elastic stiffness and 90 N·s/m damping per motor path,
25 N motor-side force limit (0.159 N·m pulley torque). These are chosen model
parameters, **not verified belt or motor catalog ratings**. Motor position
commands are ideal; rotor inertia, tooth meshing, belt pretension/slack,
thermal limits and powered-off brakes are not modeled. The current belt
polylines show routing centerlines, not accurate pulley-wrap CAD or collision
geometry. A deployable vertical machine needs a verified holding brake or
counterbalance; motor gravity compensation alone is not a safety mechanism.

The custom frame retains 420×700 mm X/Z travel and 125 mm insertion travel;
stationary motors replace the moving traverse motor and dual lift screws.
The moving bridge is assigned 0.9 kg versus A's 1.3 kg. Masses and inertia
remain lumped design estimates. Detailed belt clamps, tensioner adjustment,
brake geometry, cable carrier and rack-load checks remain unfinished.

