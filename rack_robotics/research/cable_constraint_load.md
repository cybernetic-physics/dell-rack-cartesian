# Cable constraint-load diagnostic

Status: 2026-10-17, isolated sensor controls passed; full-rack threshold
crossings detected. Five-design nominal5 N screening is complete; further
load interpretation remains open. This is new
evidence, not a reinterpretation of historical benchmarks.

## What is measured

The baseline cable uses ordinary D6 joints, not an articulation with an incoming
joint-force tensor. Small anchor errors and normal contact impulses do not
measure cable tension. PhysX supports a separate **break-force threshold** on
ordinary joints: an event is generated when the resultant constraint force
exceeds the threshold. Drive actuation forces are excluded from this accounting.
See the primary [PhysX joint force/breakage documentation](https://nvidia-omniverse.github.io/PhysX/physx/5.1.1/docs/Joints.html).

The installed Isaac Sim extension's `PhysicsJoint.py` regression uses
`get_physx_interface().get_simulation_event_stream_v2()` and decodes the
`SimulationEvent.JOINT_BREAK` payload with `PhysicsSchemaTools.decodeSdfPath`.
The project's monitor follows that installed API, rather than assuming a
regular-joint force tensor exists.

This gives a threshold-crossing diagnostic, **not a continuous force trace or
an axial tensile-force measurement**. A break changes the physical system, so
the task is aborted at the first delivered cable event. No broken-cable task
can be called successful. Events are polled at the existing render/update
cadence (30 Hz for the 480 Hz trials); the reported context is delivery time,
not the exact solver instant. Subsequent steps before event delivery are not
claimed as intact-cable evidence.

## Isolated calibration controls

`experiments/joint-break-sensor001` preserves the exact probe source, pre-run
USD, hashes, all events and sampled body positions. Twelve independent fixtures
use three masses: 0.0007 kg (one baseline cable segment), 0.0252 kg (all 36
segments), and 0.1 kg. Each is held at its center by a world-attached D6 with
all translations locked and the baseline angular limit/drive settings.
There is no contact support or other translational drive.

For each mass, the force thresholds are 0.5, 0.9, 1.1 and 2.0 times `mass ×
9.81 m/s²`. All six sub-weight thresholds generated the expected joint event
and a falling body; all six super-weight thresholds retained the body and
generated no event. All samples were finite. Source and scene hashes were
verified again after downloading the result. This validates threshold behavior
for static gravitational loading; it is not a falling-time calibration or a
proof of the exact dynamic peak in a cable chain.

The original probe001 uses32 position/4 velocity solver iterations. Probe002
repeats all12 controls with the baseline cable's exact128/8 settings; all pass
again, and downloaded source/scene hashes verify. The two independent reports
are retained rather than overwriting the initial calibration.

## Full-rack protocol

`run_benchmark_trial.py --cable-load-threshold-n VALUE` authors only the
threshold on the 36 existing cable joints in a new experiment overlay. The
baseline, saved environment, low-level robot controller, cable masses, limits,
angular drives, socket collision geometry and latch remain unchanged. It
retains the existing physical fixture initialization, common controller and
trajectory/contact recording.

The diagnostic is restricted to a one-cycle nominal control, explicitly marked
`randomized_reliability_sample=false`. It cannot be combined with randomized,
occupied-neighbor or continuous-cycle cohorts. Thresholds apply during both
initialization and manipulation; these intervals are labeled separately.
Reporting errors fail the trial. An interrupted/incomplete task cannot establish
a full-cycle no-crossing result.

Initial full-rack evidence:

| Case | Threshold | Observation |
|---|---|---|
| `cable-load-ca-negative001` | 0.001 N | Early-abort reporting error; no physical outcome claimed. Original directory and failure note retained. |
| `cable-load-ca-negative002` | 0.001 N | Fresh rerun: cable break events at the first delivered update; abort saved correctly; no robot task began. |
| `cable-load-ca-1n001` | 1 N | Joint00 event during physical initialization, delivered at 3.020833 s; no robot task began. |
| `cable-load-ca-5n001` | 5 N | Timed task began; first delivered event names Joint29 during grasp at 5.50625 s. Thirty cable events were delivered together; their order does not establish the first physical break. Task aborted. |
| `cable-load-ca-25n001` | 25 N | Full21.516667 s cycle completed, no cable break events or reporting errors. All646 recorded frame records for126 bodies exactly match the first cycle of `continuous-ca001`; see `trajectory_comparison001.json`. |
| `cable-load-aa-25n001` | 25 N | Full32.922917 s cycle completed with no cable break events; downloaded frozen-source hashes verify. |
| `cable-load-ba-25n001` | 25 N | Full32.922917 s cycle completed with no cable break events; downloaded frozen-source hashes verify. |

These are diagnostic values, not cable/connector allowable loads. The separate
25 N C/A run extends the range; the lower-threshold failures are not discarded
or turned into passes by raising the threshold. All five current working designs
now have a nominal5 N screen, recorded in
[cable_load_screen001.csv](cable_load_screen001.csv). AA v016, BA v014 and CA v021
abort during grasp at the same event-delivery time5.50625 s. AC v005 and BC v004
each complete37.625 s cycles with no threshold event. Source hashes verify for
all five (on the VM where locally collected snapshots omit source files).
Higher-threshold AA/BA runs are separate follow-ups, not replacements. Both
25 N follow-ups are complete. For each, all988 recorded frame records exactly
match the corresponding first cycle of `continuous-aa001` / `continuous-ba001`,
including phase, time and126 body poses. Thus the nonbreaking threshold did not
change the recorded nominal trajectory in these comparisons.

This is one nominal control per design, not randomized load reliability or a
manufacturer allowable-load comparison. The observed tool-associated difference
is a useful risk signal, not a hardware-only causal conclusion. Later events may be consequences
of earlier breaks within the callback interval, so the event count is not the
number of independently overloaded joints on the original intact cable.

Example from `/workspace` in the existing container (choose unused outputs):

```bash
/isaac-sim/python.sh rack_robotics/scripts/probe_joint_break_sensor.py \
  --output rack_robotics/experiments/joint-break-sensor002 --allow-root

/isaac-sim/python.sh rack_robotics/scripts/run_benchmark_trial.py \
  --environment rack_robotics/environments/robot_c_gripper_a/v021 \
  --condition rack_robotics/experiments/continuous-ca001/condition.json \
  --output rack_robotics/experiments/cable-load-ca-1n002 \
  --cable-load-threshold-n 1 --allow-root
```

## Remaining interpretation gap

A free-ended cable can have low load without demonstrating safety for a cable
anchored at its other end, snagged or densely routed. Resultant constraint-load
thresholds do not identify axial versus transverse components. Material,
connector strain-relief and installed-routing limits are not calibrated. Thus
this diagnostic advances the excessive-load evaluation, but cannot alone close
the plan's full cable-tension requirement or certify hardware safety.
