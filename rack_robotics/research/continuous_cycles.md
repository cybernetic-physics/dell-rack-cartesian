# Consecutive physical cycles

The common trial runner supports `--cycles N` (1–100). Counts above one are
restricted to nominal control conditions and cannot be combined with randomized
conditions or the occupied-neighbor diagnostic. These runs test repeated use of
one live physical scene; they are not independent reliability samples.

Initialization and physical fixture seating happen once. Between cycles only
the task-controller state is renewed. The world, robot, gripper, observer,
connector and cable persist; there is no reset or between-cycle re-seating.
Each cycle must finish the complete unplug/replug task and begin/end with a
measured retained connector and inactive initialization helpers. A failed cycle
stops the run. The ordinary topology, contact-reporting and carrier checks still
apply. Recording and contact timestamps span the entire run monotonically.

## Verified results, 2026-10-17

| Saved design | Evidence directory under `experiments/` | Consecutive complete cycles | Total task time | Recoveries / seating nudges | Maximum timed cable-joint gap |
|---|---|---:|---:|---:|---:|
| A/A v016 | `continuous-aa001` | 3 / 3 | 98.768750 s | 3 / 0 | 0.046901 mm |
| B/A v014 | `continuous-ba001` | 3 / 3 | 98.768750 s | 3 / 0 | 0.058302 mm |
| C/A v021 | `continuous-ca001` | 3 / 3 | 64.550000 s | 0 / 0 | 0.019561 mm |
| A/C v005 | `continuous-ac001` | 3 / 3 | 112.875000 s | 3 / 3 | 0.015637 mm |
| B/C v004 | `continuous-bc001` | 3 / 3 | 112.875000 s | 3 / 3 | 0.015545 mm |

All five use 480 Hz physics. All source hashes and exact environment-manifest
identities verify. Each cycle's saved final measured state exactly equals the
next cycle's initial measured state, with contiguous times. All final topology
audits and all eight startup/timed carrier checks pass. A/A and B/A each use one
bounded seating recovery per cycle; A/C and B/C use one recovery and one nudge per
cycle; C/A uses neither. Three cycles are evidence of this
finite run, not a lifetime or unattended-service guarantee. Cable-joint gap is
not measured tensile force.

`cycle_boundaries.json` contains each initial/final pose, task outcome, local
duration, global start/end times, recoveries and boundary checks. `results.json`
retains the aggregate outcome, global trace and explicit
`randomized_reliability_sample: false`. Frozen `source/`, `harness/` and their
hash manifest preserve the implementation that produced each run.

See [reproduction commands](../REPRODUCE.md#continuous-cycles-without-reset).
