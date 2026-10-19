# Cable motion and load interpretation

Historical geometry-only nominal-cycle screen, 2026-10-17. This separates measured motion,
numerical constraint integrity, and the **tensile load unmeasured by this screen**. It does
not claim that a successful unplug/replug cycle is safe for a physical cable.

Subsequent work now supplies separately recorded per-step axial-reaction
estimates: see [cable momentum measurement](cable_momentum_measurement.md).
Those new runs do not retroactively turn these geometry measurements into force
measurements or qualify a safe real-hardware load.

## Current assemblies

`experiments/cable-screen001/report.json` verifies the exact saved packages,
extracts the cable anchors from their composed USD scenes, and transforms those
anchors using each package's measured 30 Hz rigid-body recording. The report
contains 1,013 input-file hashes and frozen analysis sources. Only the cable and
plug are populated for this analysis; it is not another scene reload or collision
test. Coordinates are the metre-based simulation recordings, not the default USD
metadata of an unopened runtime stage.

An independent run on the VM (`cable-screen002`) reproduces the Mac analysis:
all five geometry/identity/sample/phase records and analysis-source hashes match;
the largest scalar difference is2.22e-16. Its1,013 input hashes also verify
against local copies. `cross_platform_check001.json` binds both reports. This
checks analysis reproducibility, not another physical trial.

All five cables have 36 rigid links and a nominal anchor-chain length of 540 mm.
The far end is free. Maxima below occur at different times; they must not be
combined into an invented simultaneous worst-case configuration.

| Exact saved design | Largest segment-centre displacement | Free-end displacement | Largest sampled anchor gap | Largest adjacent-link bend |
|---|---:|---:|---:|---:|
| A/A v016 |85.722 mm|85.994 mm|0.007364 mm|40.044°|
| B/A v014 |85.858 mm|86.134 mm|0.007512 mm|40.064°|
| C/A v021 |86.278 mm|86.556 mm|0.008206 mm|40.052°|
| A/C v005 |84.414 mm|84.678 mm|0.009230 mm|40.052°|
| B/C v004 |84.156 mm|84.416 mm|0.007691 mm|40.047°|

The free-end/segment movement peaks during realignment in these recordings.
The largest endpoint chord is about 99.213% of nominal chain length, early in
initialization. A hanging free-ended chain can be almost straight under its own
weight; that fraction is **not** a measurement of tensile force or available
routing slack. The bend angle is between capsule axes, not measured jacket
curvature or a certified minimum bend radius.

All sampled anchor gaps are below the existing 1.5 mm numerical-integrity gate.
The physics-step reports, which also include initialization and can see peaks
between render samples, give larger maxima: 0.018250 mm for A/A, C/A, A/C and
0.018353 mm for B/A, B/C. Keep those original full-rate maxima; the smaller
sampled values do not replace them. A locked-translation D6 joint does not have
a calibrated axial stiffness, so converting this solver error to force or
material strain would be unjustified.

## What is and is not evaluated

Observed: the cable moves with the actual connector; its free tip follows the
withdrawal/return; the sampled chain stays connected; its bend limits are
approached. Existing trial contact reports additionally record cable/rack
contacts, but their collider-pair impulse/dt peaks omit friction-anchor impulses
and are not a net axial load cell. No manufacturer-specific conductor/jacket,
strain relief, far-end retention, or fatigue model is present.

**This geometry screen does not measure excessive tensile force or pass it.** Neither these nominal
cycles nor the restrained-neighbor screen tests a target cable with its far end
connected and its routing slack exhausted. A final recommendation must state
that the demonstrated task is free-ended cable manipulation, not safe handling
of arbitrary installed two-ended patch cables. The current physical-realism
score stays partial; no extra score is awarded for this geometry screen.

The [NVIDIA tensor API](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/extensions/runtime/source/omni.physics.tensors/docs/api/python.html)
documents incoming joint forces for **articulations**. Those calls do not by
themselves supply force data for this existing regular-D6 cable chain.
[NVIDIA's PhysX discussion](https://github.com/NVIDIA-Omniverse/PhysX/discussions/101)
points to native constraint-force access; a validated binding or independently
calibrated load sensor would be needed before reporting cable tension here.
Changing the cable to an articulation merely to obtain that API would change
the tested model and require fresh dynamics validation, not retroactive force
claims for these recordings.

## Reproduce

From the project root, using Python with `usd-core` installed:

```sh
.venv/bin/python rack_robotics/scripts/screen_cable_motion.py \
  --plan rack_robotics/research/comparison-plan001.json \
  --output rack_robotics/experiments/cable-screen002
```

Use a new output directory. This reads the existing nominal packages and does
not command a robot, alter a scene, pool randomized trials, or infer force from
appearance. The pure geometry tests explicitly cover straight-but-force-unknown
cables, rigid translation, rotated anchors, opened joints and invalid recordings.
