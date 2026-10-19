# Final comparison method

Method checkpoint: 2026-10-17, while campaigns007/008/009 are still running.
These criteria are declared before assigning final scores. Earlier historical
cohorts, failed variants and partial results remain visible but do not become
current-design reliability evidence.

## Eligibility and evidence

Compare exact saved versions, not architecture names detached from versions.
Every implemented combination stays in the comparison. Failed nominal designs
form an explicitly nonfunctional group; an attractive render cannot promote
them above a design that completes manipulation. A working design's final score
requires its complete declared cohort, a passing nominal control and at least
10 admissible randomized manipulation trials. Leading candidates need at least
20 admissible trials. Fixture failures stay in the full-protocol denominator
and are also reported separately; never rerun or discard a difficult start.

Keep distinct controller/harness cohorts separate. Campaign009's specialized
seating controller is a design-system difference, not evidence that its hardware
alone is better. Report the paired conditions and this confound with comparisons.
Do not pool old versions to increase a current design's sample size.

Each scored observation must name its report/package and hash. Missing required
observations mean **score pending**, not a guessed pass. A documented limitation
or demonstrated failure is an observation that can receive a low score; the
comparison does not require inventing manufacturer certification, FEA or a
fully purchased prototype as new completion gates.

## 100-point rubric

| Criterion | Points | Method |
|---|---:|---|
| Reliability | 45 | 45×[0.7×Wilson lower bound for complete cycles/admissible trials + 0.3×Wilson lower bound for complete cycles/all planned randomized starts], using the two-sided95% Wilson interval. Publish raw counts, both rates and both intervals alongside the score. |
| Rack compatibility | 20 | 10×occupied-screen complete and interference-free cycles/declared occupied starts; 5 for passing the complete declared retracted workspace raster, otherwise0; 5 for a supported-box frame audit with no detected interference, otherwise0. State finite-path, occupied-fixture and geometric coverage limits; this is not all-pose clearance. |
| Compactness | 10 | 10/[1+(left+right overhang)/0.600+rear overhang/0.600], using nonnegative overhang in metres from the exact-package full-cycle mechanical screen. The600 mm rack width is the fixed reference scale, not a safety limit. Publish actual envelopes/masses too. |
| Mechanical feasibility/buildability | 15 | Three separately justified0/2.5/5-point assessments below. Unknown complete cost receives no invented numerical advantage. |
| Physical realism | 8 | Four separately justified0/1/2-point assessments below. No pose overrides, disabled latch or invented success criteria are accepted as functional manipulation. |
| Visual quality | 2 | 0: missing or misleading motion evidence;1: verified recorded motion but incomplete/obstructed required views;2: four complete, inspected, readable1080p-or-better views plus verified synchronized edit. Mac playback alone does not prove readability. |

Buildability assessments, each0/2.5/5:

1. **Parts and interfaces:** 0 undocumented;2.5 dimensioned model inventory with
   explicit custom/missing interfaces;5 a fully selected compatible mechanical
   parts/interface schedule supported by drawings. A low catalog price is not
   proof of compatibility.
2. **Assembly and servicing:** 0 known unassemblable/intersecting arrangement;
   2.5 plausible documented sequence and access/door/airflow limitations;
   5 assembly/service access demonstrated within the stated installation
   envelope. A door-open design may be feasible if that constraint is explicit.
3. **Power loss and load handling:** 0 current fault test fails or load path is
   absent;2.5 model fault/load checks pass with explicit uncalibrated hardware
   assumptions;5 additionally supported by selected component ratings and
   compatible load/brake interfaces. Do not call the5-point tier certification.

Physical-realism assessments, each0/1/2:

1. **Manipulation causality:** 0 scripted retention/pose-driven manipulation;
   1 contact-driven mechanism without causal checks;2 positive tests and
   negative controls demonstrate robot grasp, latch contact and release.
2. **Transmission:** 0 decorative drives/direct body motion;1 bounded
   articulated drive with documented efficiency/slack/backlash abstractions;
   2 independently tested transmission behavior with relevant identified
   parameters. Current coupled-belt behavior is not automatically a calibrated
   belt just because it uses motor-coordinate efforts.
3. **Cable and contact:** 0 absent/disabled;1 dynamic cable and collision/contact
   evidence with disclosed tension/material limits;2 validated cable/contact
   response over the relevant force and routing range.
4. **Initial-state and observation realism:** 0 invalid initial latch or false
   success;1 physical initialization and measured acceptance using exact scene
   observations;2 additionally modeled realistic sensing/calibration error and
   observation limitations. Pose ground truth must not be described as a
   deployable perception system.

For judgment-based subitems, retain a short rationale and evidence link for
each value. An unknown calibrated tension or complete purchase cost is reported
as unknown; it is neither zero force/cost nor an automatic task failure.

## Reporting and sensitivity

Round only displayed totals, not intermediate calculations. Sort working
eligible designs by total, but do not call small score differences statistically
significant. Repeat the ordering with reliability weight35 and55, scaling all
other weights proportionally to keep the total100. If the preferred design
changes, report the recommendation as preference-sensitive. A visual score can
contribute at most two points and never override the functional eligibility gate.

Also publish cycle time, unplug/replug counts, latch failures, recoveries,
contact-pair peaks, cable displacement, stability, total/moving mass, overhang,
known prices and unknown costs. These contextual metrics are not hidden in a
single score. Contact impulse/dt and cable-joint gap are not net insertion force
or calibrated cable tension. Explain tradeoffs in the final recommendation.

This file specifies the method only. No final winner or complete ranking is
asserted until the current cohorts and supporting reports are terminal and
verified.

## Executable comparison

`rack_robotics/comparison.py` implements the arithmetic, admissible-trial gates,
failed-design separation and35/45/55-weight sensitivity. The report adapter
`scripts/compare_designs.py` verifies exact package files, regenerates randomized
and occupied summaries, recomputes mechanical bounds from the saved measured
trajectory, verifies workspace gates and source snapshots, and binds each
current brake probe and recorded-motion clip. It retains per-trial contextual
metrics as well as scores. Human subitem judgments and references are explicit
in `comparison-plan001.json`; no complete-cost estimate is invented.

From the project root, choose a new output directory:

```bash
.venv/bin/python rack_robotics/scripts/compare_designs.py \
  --plan rack_robotics/research/comparison-plan001.json \
  --output rack_robotics/experiments/NEW_COMPARISON
```

The output preserves normalized observations, input hashes, regenerated
summaries, analysis sources and the comparison. A known unfinished benchmark,
brake probe or current clip leaves that design pending and withholds the overall
ranking. Other missing, changed or internally inconsistent required inputs raise
an error and preserve `failure.json`.
The first checkpoint `comparison001` correctly withholds ranking while the
remaining exact-version evidence is collected. Even a later numeric ranking
does not itself complete the final-quality media/showcase deliverables.
