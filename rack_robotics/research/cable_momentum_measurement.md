# Cable axial-reaction estimate from momentum balance

Checkpoint: 2026-10-17. The calibrated estimator and all five full-rack traces
are verified on the VM and Mac. These are new
nominal diagnostics, not measurements retroactively added to randomized cohorts.

## Measurement and assumptions

For each cable segment, sample center-of-mass linear velocity immediately before
and after every480 Hz physics step. Subtract the unconstrained gravity/damping
velocity update and **all reported normal plus friction contact impulses**:

```text
v_free = (v_before + gravity * dt) * max(0, 1 - linear_damping * dt)
joint_residual[i] = (mass[i] * (v_after[i] - v_free[i]) - contact_impulse[i]) / dt
reaction_at_joint[j] = sum(joint_residual[i] for i = j ... final_segment)
signed_axial[j] = dot(reaction_at_joint[j], child_axis_toward_parent[j])
```

The distal sum follows linear momentum balance: internal joint reactions cancel
within a free-ended, unbranched distal chain. Internal contacts cancel because
their impulses are assigned with opposite signs to the two actors. Forces from
contacts crossing a segment boundary are explicitly subtracted. Angular spring
torques are not external linear forces; this does not estimate bending torque
or material stress. The baseline linear damping0.15 is included, not ignored.
Positive axial values indicate tension; negative values indicate compression
along the post-step child axis. Each value is a finite-step reaction estimate,
not instantaneous continuum stress.

The implementation uses the installed tensor API with an explicit USD stage ID.
It verifies the36-link topology, expected joint relationships and local cable
axis before recording. It does not write poses, velocities or forces. The
[official rigid-body documentation](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/dev_guide/rigid_bodies_articulations/rigid_bodies.html)
defines reported linear velocity at the center of mass in world coordinates.
The [full contact-report API](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/extensions/runtime/source/omni.physx/docs/api/python.html)
includes friction-anchor impulses; using only the older normal-contact recorder
would leave a missing term. The force reconstruction above is the project's
momentum-balance inference, not a native tension-sensor claim.

## Calibration and failure preservation

`cable-balance-probe001` and002 preserve startup failures from the implicit
tensor-stage lookup. No force result is claimed for them. The installed
SimulationManager explicitly supplies its stage ID; applying that API contract
produced the successful `cable-balance-probe003`.

Probe003 uses128 position/8 velocity iterations,480 Hz,0.15 linear/angular
damping and ordinary D6 constraints. All nine checks pass:

- Free fall: maximum spurious joint-force residual9.55 µN.
- Stationary held mass0.0252 kg: expected gravity/damping support approximately
  0.247135 N, recovered within1 mN.
- Resting contact: maximum residual79.2 nN after contact support is subtracted.
- Sliding/friction contact: maximum residual44.9 µN, with friction anchors
  actually present. This also checks contact-impulse signs.
- Two-link hanging chain: proximal/distal inferred support matches two/one
  weights within2/1 mN respectively.
- All samples finite; no callback/reporting errors.

These are independent physical fixtures with analytically known behavior, not
just formula unit tests. The complete source, scene, sampled vectors and hashes
are retained. Full-rack recording requires this passed calibration, the same
physics timestep and an exact hash match to its balance implementation.

## Verified full-rack observations

| Design / exact version | Samples | Peak axial tension anywhere | Peak at plug–cable joint | Peak resultant reaction | Full cycle |
|---|---:|---:|---:|---:|---:|
| A/A v016 (`cable-force-aa001`) | 15,803 | 8.750812 N | 6.052393 N | 8.813710 N | 32.922917 s |
| B/A v014 (`cable-force-ba001`) | 15,803 | 10.035368 N | 6.860190 N | 10.117805 N | 32.922917 s |
| C/A v021 (`cable-force-ca001`) | 10,328 | 13.435858 N | 8.895501 N | 13.507802 N | 21.516667 s |
| A/C v005 (`cable-force-ac001`) | 18,060 | 0.829453 N | 0.599416 N | 0.836062 N | 37.625000 s |
| B/C v004 (`cable-force-bc001`) | 18,060 | 1.107084 N | 0.728408 N | 1.124602 N | 37.625000 s |

All maxima occur during grasp. AA/BA/CA peak at time5.50625 s, at joints01/03/03
respectively. A/C peaks at joint01, time7.789583 s; B/C at joint01, time7.695833 s.
The largest resultant is at joint00 for all five designs.

The machine-readable [five-design summary](cable_force_comparison001.json)
recomputes every trace and reports total and consecutive exceedance durations.
Thresholds below are descriptive, not hardware-safe limits. Counts refer to
steps with at least one joint above the threshold, not accumulated joint counts.

| Design | Steps above1 N | Longest run above1 N | Steps above5 N | Steps above10 N |
|---|---:|---:|---:|---:|
| A/A |3|2|1|0|
| B/A |3|2|1|1|
| C/A |2|1|1|1|
| A/C |0|0|0|0|
| B/C |1|1|0|0|

Each step is2.083333 ms. Every observed5 N crossing is therefore a **one-step
transient**, not sustained pulling or a statement about manufacturer-rated
cable damage. The specialized-tool systems have lower nominal peaks here;
this does not establish a randomized force distribution or isolate hardware
effects from the different controller/seating behavior.

The separate native break-threshold diagnostics agree directionally: AA/BA/CA
cross5 N but complete at25 N; AC/BC complete at5 N. This cross-check does not make
the two measurement definitions identical: the native break threshold uses a
resultant solver constraint load, while the trace reconstructs net momentum
reaction and projects it onto a segment axis.

All recorded frame records, including body poses, phase and time, exactly match
their corresponding first cycles in `continuous-{aa,ba,ca,ac,bc}001`:
AA988 frames/126 bodies, BA988/143, CA646/126, AC1129/129 and BC1129/146.
Thus adding the read-only recording did not alter those
recorded nominal trajectories. This is not an every-step pose comparison or
proof for untested randomized starts.

`verify_cable_force.py` checks frozen-source/calibration hashes, recomputes every
stored force from saved velocities and full impulses, checks contiguous
per-step timing through task completion, and reconciles per-joint/phase/global
peaks. VM and Mac checks verify all five traces.
Maximum arithmetic disagreement is below5e-16 N. This verifier is an arithmetic
and provenance check, not a second independent physical sensor.

## Reproduction

From `/workspace` in the existing container, use new output paths:

```bash
/isaac-sim/python.sh rack_robotics/scripts/probe_cable_balance.py \
  --output rack_robotics/experiments/cable-balance-probe004 --allow-root

/isaac-sim/python.sh rack_robotics/scripts/run_benchmark_trial.py \
  --environment rack_robotics/environments/robot_c_gripper_a/v021 \
  --condition rack_robotics/experiments/continuous-ca001/condition.json \
  --output rack_robotics/experiments/cable-force-ca002 \
  --cable-force-trace \
  --cable-force-calibration rack_robotics/experiments/cable-balance-probe003/results.json \
  --allow-root

python3 rack_robotics/scripts/verify_cable_force.py \
  rack_robotics/experiments/cable-force-ca002 \
  --output rack_robotics/experiments/cable-force-ca002/verification001.json

python3 -m rack_robotics.scripts.summarize_cable_force \
  --output rack_robotics/research/cable_force_comparison-NEW.json
```

The gzip JSONL contains the raw per-step velocity/impulse/axis inputs and derived
forces, with masses, gravity and damping in its header. Force summaries and
calibration evidence are separate from the30 Hz visual replay trajectory.

## Interpretation limits and next work

The current measurement concerns the original free-ended simulated cable.
Anchoring/snags, alternative routing, real-material compliance and strain-relief
failure loads are not calibrated. Solver projection/stabilization or unreported
external impulses could bias dynamic inference, even when arithmetic verifies.
An observed peak cannot establish a hardware-safe limit. All five working
designs now have nominal force coverage; randomized force distributions and
two-ended/slack-exhaustion cases do not. The [current recommendation](current_design_comparison.md)
includes this new load/reliability tradeoff, but the historical ranking has not
been silently rescored using a new post-hoc force criterion. Final delivery
integration remains open.
