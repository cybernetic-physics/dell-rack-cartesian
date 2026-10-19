# Recorded-motion mechanical screening

Checkpoint: 2026-10-17 UTC. These are simulation-model measurements and
quasi-static calculations, **not structural qualification or safe payloads**.

## All nine robot–gripper combinations

Bounds include authored rigid-body visual and collision geometry at the recorded
30 Hz poses. Overhang is relative to the model's 600 mm rack width and rear
plane Y=600 mm; it is not measured clearance to a closed door.

| Saved design | Total modeled mass | Moving mass | Left / right / rear overhang | Largest sampled gravity moment at mount reference |
|---|---:|---:|---:|---:|
| A/A v001 | 6.892 kg | 1.892 kg | 5 / 12.5 / 156 mm | 8.59 N·m |
| B/A v002 | 6.412 kg | 2.412 kg | 248 / 0 / 235.5 mm | 12.06 N·m |
| C/A v001 | 5.692 kg | 1.492 kg | 5 / 5 / 238 mm | 7.32 N·m |
| A/B v003, full-size RG2 | 7.953 kg | 2.953 kg | 5 / 12.5 / 197 mm | 10.33 N·m |
| A/C v002 | 6.871 kg | 1.871 kg | 5 / 12.5 / 156 mm | 8.59 N·m |
| B/C v003 | 6.391 kg | 2.391 kg | 248 / 0 / 235.5 mm | 12.03 N·m |
| C/C v001 | 5.671 kg | 1.471 kg | 5 / 5 / 238 mm | 7.32 N·m |
| C/B v001, full-size RG2 | 6.753 kg | 2.553 kg | 5 / 5 / 238 mm | 8.98 N·m |
| B/B v006, **failed partial motion** | 7.473 kg | 3.473 kg | 248 / 0 / 235.5 mm | 15.60 N·m |

“Moving mass” excludes the fixed robot frame and includes its attached moving
stages/tool. These authored masses are estimates, not weighed complete BOMs.
The mount reference is the centroid of the modeled `PostClamp` centers.
Reported moment magnitude is the norm of the gravity-load moment about that
reference, including the fixed frame's weight. It is neither a measured joint
reaction nor an individual bolt load.

The telescoping B/A model has a 386 mm-wide final parked envelope, but it is
shifted left: X=-548…-162 mm. Thus “compact parked width” does not imply fitting
within the rack. Its sampled full-cycle envelope spans about **764 mm** in X.
Its 248 mm lateral overhang occupies space beside/behind the neighboring rack;
this calculation alone does not establish a surface collision. Rear service
access and aisle occupation must be scored separately from manipulation success.

B/A's calculated gravity moments about the outer/inner telescoping joint
anchors peak at approximately **2.66 / 0.92 N·m**, supporting downstream masses
of **1.612 / 0.862 kg** respectively. The report lists the exact supported body
sets. These anchors are not guide-block centroids. Do not compare these numbers
directly with a catalog moment rating to declare the complete stage safe:
block spacing, load sharing, combined moments, brackets, fasteners, beam bending,
drive compliance, braking and dynamic loads remain unevaluated.

B/B's larger RG2 tool increases its calculated mount moment and the load on the
telescoping stages: outer/inner joint-anchor moments reach **6.93 / 3.12 N·m**
with downstream masses **2.673 / 1.923 kg**. This record ends in failed grasping;
it cannot establish a complete-cycle swept envelope, a successful park, or a
safe physical installation. It is retained as a comparison of the actual failed
design, not silently excluded because it did not complete manipulation.

## Method and evidence

`extract_mechanical_properties.py` verifies the saved environment package and
opens it in a separate Isaac session. After physics initialization it reads
cooked body masses, centers of mass and inertia tensors from the stage-attached
simulation view. It does not issue manipulation commands or save to the source
environment. Geometry bounds and joint anchors are extracted in body-local
coordinates. The original A/A query attempts 001 and 002 are preserved API
failures; successful queries are `mechanical_aa003`, `mechanical_ba001`,
`mechanical_ca001`, `mechanical_ab001`, `mechanical_ac001`, `mechanical_bc001`,
`mechanical_cc001`, `mechanical_cb001` and `mechanical_bb001`.
All 117 robot body frames across these nine packages were checked for scale,
shear and reflection: none were found. The extractor now rejects such frames,
because recorded xyz/quaternion poses alone cannot reproduce non-rigid frames.

The API reports center-of-mass translation in the rigid-body frame; its inertia
matrix is taken about the COM but expressed in body-frame axes, not necessarily
the principal axes. The extraction field name states that distinction. See the
[NVIDIA tensor API reference](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/109.0/extensions/runtime/source/omni.physics.tensors/docs/api/python.html).
Installed Isaac source also confirms that its simulation manager supplies an
explicit stage ID; the legacy implicit-stage tensor call failed in query 002.

`mechanical_screen.py` transforms each local COM and local geometry box through
the corresponding **recorded** world pose. Gravity force is `m × (0,0,-9.81)`;
the summed moment is `(COM - reference) × force`. There are no USD pose writes
or simulator control calls in the analysis. Inertia tensors are preserved but
not used to invent dynamic loads from undersampled motion.

Machine-readable reports under `experiments/`:

- `mechanical-screen-aa001.json`: campaign002 A/A nominal control.
- `mechanical-screen-ba001.json`: campaign001 B/A nominal control.
- `mechanical-screen-ca001.json`: standalone revised C/A control002.
- `mechanical-screen-ab001.json`: campaign001 A/B nominal control.
- `mechanical-screen-ac001.json`: campaign002 A/C nominal control.
- `mechanical-screen-bc001.json`: campaign002 B/C nominal control.
- `mechanical-screen-cc001.json`: campaign001 C/C nominal control.
- `mechanical-screen-cb001.json`: campaign001 C/B nominal control.
- `mechanical-screen-bb001.json`: B/B v006's packaged failed development motion.

The newer analysis supports two explicit provenance paths: a benchmark result
with the matching saved environment identity, or the trajectory/results inside
that exact saved environment with every packaged hash verified. Failed property
queries, changed packages and unrelated motion are rejected. B/B uses the latter
path because it has no successful benchmark control; its report explicitly says
"Partial failed task only; not a full-cycle workspace."

Each report identifies the saved environment hash and hashes the property query,
trajectory, result and analysis source. These are geometry/load screens of
specific recorded cycles, **not pooled cross-protocol reliability trials**.

Example reproduction, from the project root with a new output filename:

```sh
python3 rack_robotics/scripts/screen_mechanical_trajectory.py \
  --properties rack_robotics/experiments/mechanical_ba001/properties.json \
  --attempt rack_robotics/experiments/benchmark-campaign001/BA/control-attempt001 \
  --environment rack_robotics/environments/robot_b_gripper_a/v002 \
  --output rack_robotics/experiments/mechanical-screen-ba002.json
```

## Remaining gates

Each combination now has a recorded-motion screen, but these figures exclude
acceleration, contact/extraction, cable-tension and fault loads.
Thirty-hertz sampled boxes are not continuous swept-volume collision tests.
Non-rigid decorative belt curves and absent cable carriers are not included.
The ideal root joint does not model rack/bolt flexibility. Full workspace,
neighboring occupied connectors/cables, door opening, airflow/service access,
holding brakes, detailed manufacturable connections and verified component/rack
ratings remain required. No final hardware recommendation follows from this
table alone.

## Drive-connection revisions — separate measurements

Fresh Isaac property queries `mechanical_aa004`, `mechanical_ba002` and
`mechanical_ca002` read the revised saved scenes and passed the cooked-property
checks. The matching `mechanical-screen-{aa,ba,ca}002.json` reports use the
trajectory/results packaged inside each exact environment, not an older control.

| Revised saved design | Total modeled mass | Moving mass | Left / right / rear overhang | Largest sampled gravity moment |
|---|---:|---:|---:|---:|
| A/A v005 |8.252 kg|2.621 kg|5 /12.5 /155 mm|10.142 N·m|
| B/A v003 |6.678 kg|2.678 kg|248 /0 /235.5 mm|12.705 N·m|
| C/A v004 |6.174 kg|1.974 kg|5 /5 /238 mm|7.808 N·m|

The connection details materially increase moving mass. B/A's outer/inner
telescoping joint-anchor gravity moments now reach3.713 /1.464 N·m, supporting
1.878 /1.128 kg. These remain quasi-static calculations, not certified guide,
beam, brake or bracket capacities. Added geometrically estimated masses and
collision parts are documented in `drive_connection_revision.md`.

## Corrected open frames, brakes and passive carriers

The latest cooked-property queries `mechanical_aa005`, `mechanical_ba003`
and `mechanical_ca003` pass for A/A v016, B/A v014 and C/A v021 respectively.
`mechanical-screen-{aa,ba,ca}003.json` verifies each package manifest and uses
that exact package's complete measured task trajectory. The earlier tables
are historical designs, not estimates for these heavier assemblies.

| Saved design | Total modeled mass | Moving mass | Left / right / rear overhang | Largest sampled gravity mount moment |
|---|---:|---:|---:|---:|
| A/A v016 |10.732 kg|3.632 kg|54.0 /54.2 /345.2 mm|13.432 N·m|
| B/A v014 |9.828 kg|4.986 kg|248.0 /0 /464.0 mm|20.293 N·m|
| C/A v021 |7.627 kg|2.797 kg|54.0 /54.2 /345.2 mm|9.978 N·m|
| A/C v005 |10.711 kg|3.611 kg|54.0 /54.3 /345.2 mm|13.427 N·m|
| B/C v004 |9.807 kg|4.965 kg|248.0 /0 /464.0 mm|20.229 N·m|

The specialized-tool rows use terminal successful queries`mechanical_ac002`
and`mechanical_bc002`, analyzed as`mechanical-screen-ac002.json` and
`mechanical-screen-bc002.json`. Each verifies its exact saved package and
packaged measured full-cycle trajectory; precision-tool masses are not reused.
B/C's outer/inner extension joint-anchor gravity moments are6.599 /2.393 N·m,
supporting3.570 /1.913 kg. Changing to the specialized tool has little effect
on B's envelope; the long side structure and carriers dominate its rack fit.

B's outer/inner extension joint-anchor moments are6.687 /2.450 N·m,
supporting3.591 /1.934 kg in this model. This is materially larger than the
early lightweight design. Its lateral and rear projection make adjacent-rack
space, rear-door removal and service-aisle occupation significant tradeoffs.
Neither A nor C fits entirely within the nominal600 mm rack width once
carriers/brackets are included. None can be claimed to clear a closed rear
door from these bounds; the model contains no surveyed closed-door envelope.

These are conservative sampled rigid-geometry bounds and gravity-only
calculations, not bolt reactions, fatigue/airflow analysis or component load
ratings. C/A is the lightest of these five measured assemblies; final ranking
still needs current reliability, crowded-port and buildability evidence.
