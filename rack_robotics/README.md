# Rack robotics laboratory

## Delivered comparison

[Open Gallery011](http://127.0.0.1:18080/robotics-gallery011/) ·
[Watch the1440p showcase](http://127.0.0.1:18080/robotics-gallery011/media/CA/11/demo.mp4) ·
[Reproduce or extend](REPRODUCE.md) · [Requirement-level audit](FINAL_AUDIT.md).

Three mechanically distinct robots, three tools and nine tested combinations
are preserved. Five current systems complete autonomous unplug/replug cycles;
each also completes three consecutive cycles without world reset. Their
randomized cohorts contain110 valid trials/120 declared starts in total.
The gallery includes83 independently loaded saved versions,25 accepted working
videos and four labeled failure diagnostics. Mac QA passes865 served-file
hashes and all29 video play/seek checks with no browser errors.

The recommendation is C/A for the simulation showcase and A/A for the
independent-axis prototype comparison. All current power-loss probes have
unresolved failures, and tool C's open guide pockets can still carry a loose
connector. These are documented design-study results, not qualified hardware.
See the [ranked comparison and limitations](research/current_design_comparison.md).
The existing VM, original rack/GUI, private server and historical snapshots
remain intact. The Sites local-only workflow added no public hosting.

The following sections preserve development checkpoints; their earlier
pending-work wording is superseded by the delivery audit linked above.

## Current experiment — bounded physical challenges

`physical-controls001` is terminal and **not an overall pass**. All five nominal
cycles and five unpressed5 N-capped pulls pass; AA open-transport passes,
BA/CA fail axial displacement gates after falling away from the tool, and
AC/BC never reach transport because the jaws do not open far enough. All127,722
raw480 Hz samples reverify identically on VM/Mac. The five nominal recordings
exactly match the earlier first continuous cycles. [Terminal results](research/physical_challenge_results001.md)
retain the failed gates and distinguish free dynamics from a maintained grasp.

The separately frozen `matched-release001` is terminal: **six pass, four fail**.
All68,388 physics-step samples reverify on VM/Mac. AA/BA/CA released housing
paths are exactly equal with a moving or stationary tool. AC/BC still support
the housing on their open guide pockets and carry it about40 mm; opening alone
is not free-space release. Their normal seated-release cycles remain separate
passing evidence. [Results](research/matched_release_results001.md),
[protocol](research/matched_release_protocol001.md) and
[commands](REPRODUCE.md#matched-open-command-follow-up) retain the counterexample.
No saved environment, randomized denominator, historical score or original GUI
is changed. Current local suite: **398 tests pass**.

The [source review](research/source_review001.md) rechecks key manufacturer,
paper and price evidence, preserves the unresolved RG2 PDF redirect and marks
earlier research statuses as history rather than current results.

## Historical Gallery010 — accepted media checkpoint

[Open the private comparison gallery](http://127.0.0.1:18080/robotics-gallery010/).
It contains all nine designs,83 preserved versions,25 accepted working videos
and four reviewed failure diagnostics. The corrected B/C rear/edit replace
the rejected foreground-obstructed candidates; older snapshots remain intact.
Each clip links its acceptance decision, visual observations and temporal
report. The builder verifies the bound source, coverage, sheet and playback
evidence and copies the selected evidence alongside the media. Sources/licenses
and actuator-interlock documentation are included.

Mac QA001 passes all851 served-file hashes,29 play/seek checks, acceptance
labels/links, score/load values, filters, images and desktop/mobile layout,
with zero browser errors. Focused desktop/mobile and accepted/failed-clip
screenshots were also visually inspected. No new hosting was provisioned;
the Sites local-only workflow retains the existing private server/tunnel.
This is an accepted-media checkpoint, not a completed PLAN_p2 delivery.
Frozen narrative documents retain their build-time checkpoint wording;
the physical challenges identified in the
[causal coverage audit](research/causal_coverage_audit001.md) are now terminal,
with adverse results preserved. A new snapshot will include those results;
final source/document and full requirement closure remain open.

## Current physics diagnostic — actuator interlocks

`experiments/actuator-controls001` is complete: all15 fresh-session diagnostic
cases pass across the five current working designs. The five normal cycles
succeed; the ten permanently retracted-latch/open-grasp cases remain ordinary
task failures and pass the separate expected-failure checks. Each suppresses
three requests, exhausts two recoveries and stops without withdrawal while the
plug remains retained. The177,063 raw480 Hz samples, frozen sources and process
exits reverify on both VM and Mac with identical reports. All nominal recorded
frames match the earlier first continuous cycles exactly. See the
[terminal results and limits](research/actuator_interlocks.md).
Gallery checkpoint suite: **377 tests passed**, including presentation-binding and
later-playback provenance regressions. Adding valid playback evidence no longer falsely changes render
identity; video, trajectory and source identity checks remain mandatory.

The [reproduction guide](REPRODUCE.md#actuator-disabled-interlock-diagnostics)
documents the frozen campaign,480 Hz evidence and separate task/diagnostic
verdicts. These are controller-interlock tests, not forced-pull capacity or
open-tool transport tests. They add no randomized reliability samples and do
not change scores. The original GUI remains untouched.

## Full-video screen and camera correction

`artifacts/temporal-review001` decodes all25,734 frames of the30 gallery009
videos and verifies every encoded presentation timestamp on the VM. Mac
verification checks all saved metrics, source/media hashes and233 review sheets;
it is not a second RGB decode. The coarse screen flags B/C rear approach and
parking. Original approach frames confirm a large foreground actuator blocking
the camera, so `b_c_rear_underbridge_cycle001` and its dependent
`b_c_reviewed_edit001` are rejected for final visual delivery, not deleted.
Gallery009 stays an immutable candidate snapshot.

The [recorded visual review](research/presentation/inspection_review004.json)
binds all27 C/A sheets (312 sampled frames) and seven native macro frames, plus
the B/C rejection and three lower-camera probes. Review005 adds41 A/A sheets
(487 sampled frames) and native latch details. The
[combined acceptance record](research/presentation/presentation_acceptance001.json)
accepts the required A/A1080p and C/A1440p four-view sets and edits, with explicit
inspection coverage, all-frame checks, provenance and full Mac playback.

The lower B/C camera clears the reviewed approach, separation and parking
intervals; its full1,129-frame rear cycle and revised edit002 are complete and
source/video/Mac-playback verified. Temporal-review002 checks all2,258 frames
with no coarse flags. Review006 records all18 sheets/202 sampled frames across
these two videos and corrects probe002's phase label in review004 (withdraw,
not separate/realign). Review007 completes the other35 sheets/399 samples and
eight native latch frames. [Acceptance002](research/presentation/presentation_acceptance002.json)
accepts the revised B/C five-clip set on the combined evidence:53 sheets,
601 samples, all-frame checks, source verification and natural Mac playback.
Review008 accepts the four labeled failed-combination clips only as diagnostic
footage, never as successful cycles. The all-frame metric screen is not proof of
photorealism or every local detail, and sampled visual inspection is not an
exhaustive native-frame review.

Reviews009/010 finish B/A and A/C: all94 sheets/1,088 sampled frames and15
native macro frames inspected. [Acceptance003](research/presentation/presentation_acceptance003.json)
binds their ten1080p clips, including actual seating waits/recoveries and the
A/C final nudge. All25 selected working clips now have combined acceptance
(24,400 encoded frames,215 sheets/2,488 samples), including C/A's1440p showcase.
The video/source, review/sheet and playback bindings reverify locally. This
does not change task outcomes or establish hardware safety. Gallery010 now
integrates this selection; the full requirement/source/document audit remains open.

## Gallery009 checkpoint — preserved candidate snapshot

[Private gallery009](http://127.0.0.1:18080/robotics-gallery009/) now includes
all nine designs,83 preserved versions and30 clips. It adds the native1440p C/A
showcase, improved rear/macro views for the other working designs, four revised
1080p frame-exact edits, the current recommendation and nominal cable-force
comparison. All selected media have source/video hashes and Mac playback
evidence. Mac QA001 passes all484 served-file hashes,30 video play/seek checks,
displayed current score/load values, filters, images and desktop/mobile layout,
with zero browser errors. The exact snapshot manifest is bound in the QA report.

AA/BA edits retain988 frames each; AC/BC retain1129. Withdrawal stays in macro,
and physical seating recoveries are not cut out. The final A/A improved macro
is rendered natively at1080p, not downscaled from its separate1440p candidate.
Sampled observations are in `research/presentation/inspection_review003.json`.
Gallery009 predates the acceptance records above and retains candidate labels,
including the now-rejected B/C rear/edit. The final snapshot must select the
accepted replacements and carry their evidence; gallery009 is not rewritten.

The builder now recomputes score/force evidence and binds exact current saved
versions. Cross-platform comparison allows only eight finite-float ULPs;
counts, outcomes, structure and all file hashes remain exact. Three failed
pre-output build attempts are retained in VM logs (missing audit, numerical
roundoff, missing RJ45 research report); the VM evidence copies are repaired.
Local suite at that gallery checkpoint: **356 tests passed**. Existing server/tunnel and original
live GUI remain intact. The Sites skill retained the established private,
buildless gallery workflow; no hosted service was provisioned.

## Latest checkpoint — axial-force traces for all five working designs

The [calibrated momentum diagnostic](research/cable_momentum_measurement.md)
now records every480 Hz physics step for one complete nominal cycle of each
working design. All five traces pass VM and Mac source/calibration/arithmetic
verification and exactly reproduce every recorded frame of their earlier
continuous first cycle. Peak axial estimates: AA8.75 N, BA10.04 N, CA13.44 N,
AC0.83 N, BC1.11 N. The three5 N crossings last one2.08 ms step each.
The [machine-readable comparison](research/cable_force_comparison001.json)
records exposure durations and unchanged historical scores/reliability counts.
These are force estimates for the free-ended simulated cable, not hardware-safe
load limits or new randomized samples. The [recommendation](research/current_design_comparison.md)
now retains A/C as a lower-peak-load development alternative.

Improved BA rear, AC rear and BC macro1080p full-cycle clips pass video/source
hash checks and Mac natural playback/seek. Sampled visual inspection is retained
in `research/presentation/inspection_review002.json`. BA macro and BC rear
full-cycle candidates are rendering after readable camera probes. Final temporal
visual acceptance, revised edits and gallery integration remain open; gallery008
is unchanged. Latest full local suite: **353 tests pass**.

Earlier checkpoint sections below are historical; the [delivery audit](DELIVERY_AUDIT.md)
retains remaining scope without claiming PLAN_p2 complete.

## New checkpoint — load-threshold evidence and native 1440p showcase

The [delivery audit](DELIVERY_AUDIT.md) still has open requirements; this is not
a completion claim. A [current nine-design CSV](research/current_candidate_matrix001.csv)
now separates exact current versions from the historical screening matrix.

The [cable constraint-load diagnostic](research/cable_constraint_load.md) passes
12 isolated known-weight controls at both32/4 and baseline128/8 solver settings,
and records real PhysX D6 break events in
separate full-rack runs. C/A crosses 1 N during initialization and 5 N during
grasp. Trials abort on delivered events; none enter randomized reliability.
These are resultant constraint-load thresholds, not calibrated axial tension or
manufacturer safety limits. The 0.001 N control exposed an early-reporting bug;
its failed attempt is retained, the guard is fixed, and the fresh rerun saves
the expected abort evidence. The [five-design nominal5 N screen](research/cable_load_screen001.csv)
is complete: AA/BA/CA cross the threshold during grasp; AC/BC complete their
cycles without crossing. C/A also completes at25 N, with all646 recorded
frames exactly matching its earlier continuous-cycle first run. Higher-threshold
AA/BA checks and load interpretation remain in progress.

`showcase-campaign001` has finished all four native2560×1440/30 fps C/A videos
and the frame-exact646-frame edit. All five videos pass actual Mac natural full
playback and seeking with zero dropped frames. Source/video hashes verify.
The renderer-export utility now includes and verifies the frozen phase-camera
input, with missing/changed/external-file regression tests. Sampled visual
inspection is recorded in `research/presentation/inspection_review001.json`;
complete visual/temporal acceptance remains open.

Improved A/A rear and A/C macro full-cycle1080p clips also finish and pass Mac
playback/seek checks. The existing gallery008 has not yet been updated with
these candidates. Latest local suite: **339 tests pass**.

## Current checkpoint — completed cohorts and continuous cycles

The [current-design comparison](research/current_design_comparison.md) now
includes all five completed current-version randomized cohorts: A/A, B/A and
C/A each pass 22/22 valid trials; A/C passes 21/22 and B/C 17/22. Each has two
additional failed fixture starts retained in the 24-start protocol denominator.
`comparison005` verifies 2,645 inputs and scores all eligible designs, preserving
the four failed combinations. C/A and A/A are effectively tied at 70.52/100;
the tiny numeric difference is not meaningful. C/A's lower mass and faster
measured cycles make it the showcase candidate; A/A remains the independent-axis
prototype comparison. Hardware cost and safety limitations remain explicit.

[Continuous physical cycles](research/continuous_cycles.md) now pass three
cycles each for all five working designs in the same live world, without a reset
or fixture re-seating. Source/package hashes, contiguous measured boundaries,
monotonic timestamps, topology and carrier gates verify for all five.
These finite nominal tests are not added to the randomized reliability counts.

All five working designs have four current full-cycle 1080p30 videos and a
frame-exact multi-angle edit; all four failed current designs retain diagnostic
clips. The improved A/A 1440p macro is complete and passes Mac full playback,
but remains a presentation candidate. C/A camera/lighting probes are selecting
the higher-resolution showcase views. Final visual acceptance is still open.

[Gallery008](http://127.0.0.1:18080/robotics-gallery008/) has 30 clips, all nine
designs, 83 preserved versions and separate current/historical statistics.
Mac tunnel/browser QA passes 472 served-file hashes, all 30 play/seek checks,
filters, images and responsive layouts, with no browser errors.
The Sites skill keeps this work on the existing private server/tunnel.
The builder preserves failed browser-checker notes separately from verified
playback reports. The partial failed gallery007 build remains preserved.

The four-camera batch now accepts native 1440p/4K dimensions, explicit render
subframes and frozen phase-camera choices; the editor rejects mixed resolutions
and retains every recorded frame. See [REPRODUCE.md](REPRODUCE.md).
The below-bridge C/A rear probe exposes the tool and withdrawn plug; earlier
obstructed probes remain preserved. `showcase-campaign001` is the four-view
2560×1440/30 fps candidate with 32 subframes and a frame-exact edit, not yet a
completed or visually accepted showcase. Latest full local suite: 333 tests pass.
Earlier sections below are chronological checkpoints, not current status.

## Cable-motion screen and higher-resolution macro candidate

[Cable motion and load interpretation](research/cable_motion_and_loads.md)
reports the five current nominal assemblies' measured cable displacement,
anchor gaps, bending and endpoint chord. The new read-only screen verifies saved
packages and preserves sources/hashes. Free-tip movement is84–87 mm; small
constraint gaps do **not** establish safe tension. Tensile force and a connected,
taut far end remain unmeasured, explicitly—not reported as passes.

Current B/C wide video has1,129 frames/1080p30,164,834 body-pose checks and1,129
camera checks; input/source/video hashes and Mac full playback/seek pass with
zero dropped frames. A/C now has full-playback evidence for all four current
views (macro: one dropped browser frame; other views: zero). Its side checker
persisted the result before teardown; clean teardown was not captured.

A/A macro probes004–007 preserve four actual poses/camera tests at2560×1440.
The opposite-side view004 is rejected for complete obstruction. Left-side005–007
show press, withdrawal and raised latch more clearly with stronger fill. A full
988-frame candidate `a_a_macro_latch_cycle002` is being rendered; it is not yet
final showcase acceptance. Latest local suite: **317 tests pass**.

## Exact-version comparison tooling and completed B/A cohort

`comparison.py` and `scripts/compare_designs.py` implement the declared rubric
and35/45/55 reliability-weight sensitivity. The adapter verifies packages,
regenerates benchmark/occupied summaries, recomputes mechanical geometry from
recorded poses, checks the exact-version workspace/brake reports and binds
rendered-motion evidence. Explicit judgments live in
[comparison-plan001.json](research/comparison-plan001.json). Unknown or unfinished
evidence does not become a pass; incomplete working designs withhold overall
ranking. All nine combinations remain present, including failed nominal designs.
`comparison004` completes the current read-only evidence assembly with2,537
hashed inputs, but deliberately reports no overall ranking while C/A's cohort
and the snapshot's B/C current clip remain pending. Comparison002/003 input-change
rejections are preserved;004 ran only after imports and source edits ended.

B/A v014's randomized cohort is terminal: summary020 verifies22/22 valid
complete cycles and two additional fixture pre-seat failures (22/24 protocol).
Conditional Wilson95% is85.13–100%; mean successful cycle26.840 s. This is
faster than current A/A's32.543 s mean in the paired cohort, but B's greater
overhang/cantilever load and failed power-loss probe remain comparison costs.
C/A's current campaign has started; its final rate and the overall ranking
remain pending.

Direct current A/C and B/C [power-loss probes](research/powered_off_brakes.md)
are now terminal. Both pass holding but fail overall: A/C exceeds carrier
angle limits in recovery; B/C contacts the plug with a front bearing post.
The comparison does not copy an A-tool brake result onto a C-tool assembly.

A/C wide/rear current videos each complete1129 frames at1080p30, with145641
body-pose and1129 camera checks; original-input/source/video hashes verify.
Both pass full Mac playback/seek with zero dropped frames. Sampled frames show
the mounting architecture but fine tooling is obstructed; final visual/showcase
acceptance is still open. Latest local suite: **312 tests pass**.

## Reproduction guide and terminal B/C / crowded-port results

Use [REPRODUCE.md](REPRODUCE.md) for the pinned runtime, dependency restoration,
all nine current version paths, headless saved-scene execution, fresh reload
validation, frozen randomized protocols, rendering, Mac access, and extension
workflow. `dependency-inventory001` passes all83 versions and indexes8,510 unique
files totaling11,423,448,523 bytes. All authored USD dependencies resolve; the
only runtime-namespace asset is installed `OmniPBR.mdl`. The complete Isaac
runtime is still required. This is not a portable archive or a tested fresh-OS
installation. Source and file hashes are retained. Local suite: **300 tests pass**.

B/C v004 campaign008 is now terminal and summary018 verifies its evidence:
17/22 admissible complete cycles,22/22 successful unplugs, five seat-and-latch
timeouts, and two additional fixture-start failures. Conditional completion
is77.27% (95% Wilson56.56–89.88%); full-protocol completion is17/24=70.83%.
Successful cycles average29.921 s. Four of the five manipulation failures are
at port16 and one at port8; measured hooks remain outside the retaining lip.
No failure was replaced with a successful rerun.

A/C v005 campaign009 is also terminal: summary019 verifies21/22 admissible
complete cycles and two additional fixture-start failures (21/24 protocol).
Conditional completion is95.45% (95% Wilson78.20–99.19%), with mean successful
cycle37.885 s. The remaining admissible failure is a port16 withdrawal timeout:
the connector is unplugged but has not met the controller's required withdrawal
clearance. It is not a complete successful unplug/replug. Campaign009's changed
seating-aware task harness remains explicit; these results are not pooled with
the older controller cohorts.

Occupied-screen002 is terminal, with a verified summary002. A/A,B/A,C/A,A/C
each complete4/5 declared starts; B/C completes3/5. Every design fails the
port8 physical pre-seat, and B/C also times out seating at port16. The20 timed
trials report no robot-neighbor or target-neighbor contact. This is a five-port
screen with restrained adjacent housings and dynamic free-ended cables, not
fully populated-rack routing, neighbor retention, or cable-tension validation.

The improved A/A macro candidate is complete:988 frames,1080p30,124,488 body-pose
and988 camera checks; source/video hashes and full Mac playback/seek pass with
zero dropped frames. Sampled frames show withdrawal and returned latch, but
the actuator still obscures part of the press region; it is not accepted as the
final polished macro. B/A's remaining rear/macro/side captures are collected
with verified recorded-motion/source/video hashes; all four B/A views pass full
Mac playback/seek with zero dropped frames. Initial rear/side browser-shutdown
stalls are preserved separately; the checker now saves measured playback before
cleanup, and both repeat checks exited normally. Final visual delivery,
remaining cohorts, ranking and showcase remain open.

## Gallery006 and current four-view A/A media

[Open the updated private gallery](http://127.0.0.1:18080/robotics-gallery006/).
It has actual rendered images for all9 combinations,17 downloadable clips,
all83 saved versions and a separate completed current A/A v016 cohort panel.
Historical statistics remain explicitly historical. A/C's image is labeled
v004FAILED, not the current v005 successful attempt; B/C's current image is a
parked recorded-pose still, not a full-cycle movie. Those successful captures
are still pending. Older gallery snapshots are preserved.

Mac QA002 passes423 served-file hashes,17 play/seek tests, filters, images,
current-cohort labels and desktop/mobile layout, with no browser errors.
QA001's premature-upload404 is retained, not erased. The Sites skill guided
local-only preparation/verification; no public hosting or replacement server.

All four A/A v016 view videos are now complete and source-hash/playback-verified,
each988frames at1080p30. B/A v014's wide view also completes988frames and
Mac natural playback/seek with0 dropped frames. These are current recorded
physics, not a polished-showcase claim; the original macro partly hides the
latch. Two same-pose camera probes are preserved, and the moderately elevated
angle is selected for a separate full-cycle candidate. The batch's synchronized
edits run after its remaining captures finish.

Reproduce gallery006 from the preserved local campaign snapshot using a new
output directory:

```bash
.venv/bin/python rack_robotics/scripts/build_gallery.py \
  --output artifacts/NEW_GALLERY_SNAPSHOT \
  --audit rack_robotics/experiments/preservation-audit020.json \
  --media rack_robotics/gallery/media005.json \
  --current-benchmark rack_robotics/experiments/benchmark-summary017.json
```

If campaign007's downloaded state has advanced, generate a new summary first;
the builder intentionally rejects stale snapshots instead of blending evidence.
Full local test suite: **295 passed**. Final ranking, remaining current media,
showcase and complete reproduction audit are still in progress.

## Current hardware inventory and first completed revised cohort

The [buildability/BOM report](research/buildability_and_bom.md) now derives
component quantities and dimensions from the five current passing saved
assemblies. Hash-bound JSON/CSV inventories preserve custom parts and unknown
prices. [Supplier candidates](research/supplier_costs001.json) include checked
single-component prices, not a claimed complete robot cost. The
[scoring method](research/scoring_method.md) prioritizes reliability/rack fit
and explicitly limits visual-quality weight; final ranking remains pending.

A/A v016's campaign007 cohort is terminal: **22 complete cycles out of24
declared randomized starts**; the other2 fail physical fixture pre-seating
before the timed task. All22 admissible manipulation trials pass, with a
95% Wilson interval of85.13–100% and mean successful cycle32.543 s.
The nominal control passes. This meets20 valid trials for this design, not
100% end-to-end protocol reliability. Summary017 verifies source/condition/
package/result hashes; B/A and C/A in the same campaign remain unfinished.

Campaign008's B/C partial snapshot has7 complete cycles from12 finished
starts: one fixture failure and four seat-and-latch timeouts. No final rate,
rerun or retuning within that frozen cohort is claimed. Summary016 retains
these failures and their measured hook/contact state.

A/A's rear and macro988-frame1080p30 videos have been downloaded and verified
against the actual measured trajectory and renderer source. Both complete natural Mac
playback/seek with0 dropped frames. Sampled original-frame review documents structural/tool occlusion,
not final visual acceptance. Full local unittest suite: **292 passed**.

## Current corrected-frame checkpoint — 2026-10-17 UTC

New evidence supersedes the pending statuses in the dated notes below:

- Preservation-audit020 verifies **83 saved versions,83 independent scene
  loads,80 reproduced declared outcomes**. Reload027 and029 are terminal;
  A/C v005 reproduces its37.625 s cycle,1 recovery/1 nudge. The same three
  historical reproduction exceptions remain explicit, not deleted.
- Current nominal passes are A/A v016,B/A v014,C/A v021,A/C v005,B/C v004.
  C/C v003 fails datum alignment; all three current RG2 variants fail bounded
  initial pickup and their supported-box sweeps contain interference flags.
- A/C v005 now independently passes the17-endpoint retracted raster in
 139.25 s at480 Hz, including startup and travel carrier gates. B/C's47-point
  independent-boom raster also passes in214.679167 s. These are finite unloaded paths, not
  continuous-volume or occupied-port clearance.
- Current reliability campaigns007/008/009 are running on declared24-condition
  plans. Campaign009 adds A/C v005 with its seating-aware controller; it must
  not be silently pooled with campaign007's frozen older task harness.
  Occupied-screen002 separately tests five paired port conditions for each
  of the five current nominal passes. It is not a reliability cohort.
- C/A v021 render-campaign003 is complete: four1080p30 full-cycle views and
  a13-shot synchronized edit, each646 frames. Source, renderer, video and edit
  input hashes verify. All five clips complete natural Mac playback and seek;
  side drops one browser frame, others zero. Sampled visual review preserves
  tool occlusion/dark-background limitations; this is not the polished showcase.
- Render-campaign004 is capturing four views each for the other four current
  successes. Failed-render-campaign001 preserves complete failed recordings;
  all five diagnostics are complete, source-hash checked and Mac playback/seek
  verified. A/C v004 has1312 frames,C/C298,and the three initial-pickup RG2
  failures16 frames each. These short recordings are labeled failures, not
  shortened successful cycles. A/A v016's988-frame wide cycle is also complete
  with verified full Mac playback and zero dropped frames.
- [Gallery005](http://127.0.0.1:18080/robotics-gallery005/) separates current
  nominal outcomes from historical reliability and preserves all83 versions.
  It includes C/A v021's five downloadable clips plus labeled historical
  media. Missing current media stays visibly pending; this is not the final
  gallery or ranked recommendation. Older gallery snapshots remain unchanged.
  Mac QA passes all382 served-file hashes,9 video play/seek checks, current
  outcome filters, loaded images and desktop/mobile layout.
- Full local unittest suite: **289 passed**. The Sites skill guided the gallery
  update as local-only work; no hosted Site, public service or new VM was created.

Rebuild that gallery into a **new** directory with:

```bash
.venv/bin/python rack_robotics/scripts/build_gallery.py \
  --output artifacts/NEW_GALLERY_SNAPSHOT \
  --audit rack_robotics/experiments/preservation-audit020.json \
  --media rack_robotics/gallery/media004.json
```

The following checkpoint paragraphs describe the earlier state and are retained
as development history; use the named packages and newest evidence above.

The historical development passes below are version-specific, not a claim
that every latest hardware combination works. Current precision-tool versions
A/A v016, B/A v014 and C/A v021 complete manipulation and fresh reloads.
Their separate retracted-travel probes pass17/17,47/47 and17/17 checkpoints.
Preservation-audit018 verifies76 saved versions/76 independent loads/73 declared
outcomes before the six additional tool-matrix versions; those new packages
have their own pending/completed reload reports.

The corrected-frame six-tool matrix is terminal: B/C passes37.625 s with one
insertion recovery and one seating nudge. A/C fails re-latching; C/C fails
datum alignment. All three RG2 variants fail bounded initial pickup and have
supported-box swept overlaps (A34,B14,C19), so they are not accepted as
full-workspace-compatible assemblies. Every attempt and failed scene is
preserved; old eight-combination feasibility and reliability evidence is not
transferred to this new cohort.

The latest A/B/C power-loss probes all hold the lift but fail the overall
fault-recovery/contact/carrier gates. See [brake limitations](research/powered_off_brakes.md).
New exact-package [mass/overhang/load screens](research/mechanical_screening.md)
show C/A lightest at7.627 kg, versus A/A10.732 and B/A9.828 kg. B projects
248 mm left and464 mm rearward from the nominal rack references. These are
simulation estimates, not certified hardware loads or door clearances.

Campaign007 tests24 paired conditions on the three precision-tool packages;
plan006/campaign008 extends the same frozen harness and conditions to B/C v004.
No terminal current-cohort reliability ranking is claimed. A separate A/C
controller candidate permits a bounded seating nudge with a measured aligned
housing despite passive-wrist offset; it does not change baseline retention
gates and does not alter either frozen benchmark or the completed tool matrix.
That candidate now passes37.625 s with one recovery/one nudge and all carrier
gates, preserved as A/C v005. Fresh reload029 remains a separate pending check.

Render-campaign003 records C/A v021's complete measured cycle from four views
on GPU1 using the new `open-frame-v1` camera profile. It is a candidate media
batch, not accepted final footage until complete replay/playback/visual review.
The complete local suite has282 passing tests at this checkpoint.
The new C/A wide view has completed646-frame1080p30 playback on Mac with
zero dropped frames and verified replay/video/source hashes. The rear capture
is also complete; the remaining views/edit and final visual review are pending.

This is the separate extension specified by [PLAN_p2.md](../PLAN_p2.md).
The original rack, connector, cable, GUI and infrastructure remain in place.
All three robot architectures now have full-rack feasibility passes with
grippers A and C. The full-size RG2 also completed cycles on architectures A
and C; their saved scenes passed fresh-session reloads (eight combinations in
total). These are development feasibility results, not reliability or safe-force
claims. Earlier failures remain preserved and reproducible.
Randomized simulation evidence is now available (A/A and A/C each pass 20/20),
but hardware reliability and final deliverables remain unproven. The old hand-driven
transfer demonstration is baseline evidence only, not robotic manipulation.

## Acceptance ledger

| Requirement | Evidence required | Current status |
|---|---|---|
| Preserve original rack and physical latch | Read-only snapshot, hashes, dependency recovery, fresh full-rack regression | Passed: baseline-001, 121 checks |
| Existing VM only | Actual installed version, GPU/disk observations; no provisioning | Verified 2026-10-16 |
| Broad and second-order hardware research | Sources, dimensions, CAD/license audit, adaptations, costs or explicit unknowns | Initial reports saved; procurement/CAD gaps explicit |
| Three distinct Cartesian architectures | Dimensioned mounted assemblies, articulated drives, collision/load/coverage checks | A/B/C prototypes pass full-rack cycles; all nine combinations have recorded-motion envelope/gravity screens (B/B partial failed motion), full mechanical audits pending |
| Three distinct grippers | Physical housing grasp, latch tool, secure withdrawal, reinsertion, crowded-port check | A/C feasibility passed; RG2 passes on A/C but impact/final-pose issues remain. Completed40-case neighboring-port screen finds RG2 cable contacts; no full-density certification |
| All compatible 3×3 combinations | Independent scenes, adapters, feasibility evidence or justified incompatibility | All nine have physical attempts; eight have development passes; B/RG2 startup corrected, slow grasp still fails |
| Shared autonomous 12-phase controller | Real joint-driven contact manipulation, fault detection and recovery tests | Full cycles passed; grasp/latch fault recovery passed; C/C campaign002 trial-000 physically recovered from a seating timeout and completed |
| Physics integrity | No trial plug pose override, world hand drive, plug-attached press, or collision bypass | A/A topology audit passed; cross-design audit pending |
| Randomized benchmark | ≥10 valid manipulation trials per feasible passing combination; ≥20 for best; all specified variations/metrics | Trial counts met: A/A 20/20, A/C 20/20, C/A 19/20; B/A and B/C each 10/10, C/C and A/B each 6/10, C/B 2/10. Force/coverage and hardware interpretation gates remain pending |
| Honest ranking | Documented reliability/rack-fit/compactness/buildability/realism score and hardware recommendation | Pending |
| Independent reusable environments | Config, manifest, scene, controller, cameras, results; fresh-session reload of each |Preservation-audit017:74 saved versions,74 independent loads,71 declared outcomes reproduced. Historical B/A v001 and two unstable initial-carrier failure mismatches remain explicit |
| Visuals for every tested combination | Diagnostic footage for failures; four ≥1080p camera views for successes | Pending |
| Videos | Wide, macro, side and multi-angle H.264 from recorded physical trajectories; higher-resolution best showcase | Pending |
| Secure comparison gallery | Existing loopback HTTP + SSH; screenshots, stats, hardware links, downloadable videos and USDs | Development snapshot at `/robotics-gallery005/`:9 designs,83 version records,9 clips;382 file hashes and Mac browser QA pass. Current outcomes distinct from historical trials; representative images/final clips and dependency-download delivery remain incomplete |
| Final reproducibility | Commands, dependencies/licenses, Mac playback/access tests and full requirement audit | Pending |

## Full-rack travel and revised benchmark protocol — 2026-10-17 UTC

The new physical raster `c_a_workspace001` rejects C/A v019's full retracted
vertical workspace:9/17 endpoints reached, then an insertion-stage front post
contacts a server fan at TCP height1.354 m. All sampled carrier gates pass up
to the collision. Its successful port task does not qualify that blocked
workspace. A separate candidate shifts the complete front bearing/support
6 mm rearward without changing the shaft, rails, masses, collisions or travel;
full-rack retesting is required. See
[workspace qualification](research/workspace_qualification.md).

The candidate is now saved as C/A v020:21.5167 s task pass with no recovery
or nudge, all carrier gates and4,154 supported robot-box checks passing.
Fresh reload022 verifies its physical pass and dependencies. The identical
raster002 is now a preserved failure:10/17 endpoints reached, then the
hanging cable contacts the front bearing hanger (0.102623 N) at79.927083 s.
All carrier gates still pass. This corrects the fan collision but does not
qualify the full workspace. A separate11 mm setback candidate (5 mm beyond
v020) retains1 mm nominal full-stroke bearing-plate clearance and is under
physical qualification. Its full-rack task now passes as C/A v021 in21.516667 s
without recovery/nudges; all carrier gates and4,154 supported box pairs pass.
Fresh reload024 now passes physical execution and dependencies. Unchanged
raster003 passes all17/17 endpoints and return to park in139.25 s, including
all startup/travel carrier and contact/tracking gates. This is unloaded,
retracted-path evidence, not arbitrary extended poses or payloads.
The predeclared20-trial campaign006 remains a separate ongoing
check of v020; new geometry is not substituted into that frozen cohort.

`benchmark_harness_v3` preserves saved solver rates and records released brake
runtime plus both startup/timed carrier gates. The old240 Hz harnesses and
their original cohorts remain frozen. New nominal compatibility control
`c_a_benchmark_v3_control001` reproduces C/A v019's full cycle at480 Hz in
21.5167 s, no recovery/nudge, all eight carrier gates passing. Its94 frozen
source hashes verify. This is **not** a randomized reliability estimate; see
[protocol revision](research/benchmark_harness_v3.md).

An optional camera-side fill in `render_replay.py` affects only derived
visualization layers. `c_a_neck_fill_press001` verifies three measured latch
frames with unchanged physical inputs and improved visibility. A full-cycle
macro candidate is separate from final visual acceptance.
That646-frame candidate now passes full Mac playback (0dropped frames), seek,
all recorded-body/camera checks and evidence hashes. It is v019 footage;
foreground tool occlusion and final visual acceptance remain open.

## Dual-screw frame revision — 2026-10-17 UTC

A/A v015 preserves the new open-guide, outboard-lift-screw assembly, connected
traverse motor supports and compatible81-link carriers. Its full-rack480 Hz
cycle passes in32.922917 s with one insertion recovery, no seating nudges,
0.018250 mm maximum cable gap and all startup/task carrier gates passing.
The unfiltered supported-box sweep passes6,791 cross-body pairs over the
unchanged joint limits. Fresh reload023 independently reproduces the same
cycle and passes107 package hashes,11 layers and150 asset dependencies.
These are task and scoped geometry results, not broad buildability or
reliability certification. Preservation audit016 now verifies73 saved scene
loads and70 declared outcomes; the three historical exceptions remain.

`a_a_workspace001` fails the unchanged full retracted travel at79.816667 s,
10/17 endpoints, with the same hanging-cable/front-hanger contact as C/A
(0.104452 N). All carrier gates pass up to the stop. Task success does not
qualify this obstructed workspace.
The two rejected static drafts and old environments are retained. See
[screw frame geometry and evidence](research/screw_guide_frame.md).

## Telescoping frame correction — 2026-10-17 UTC

The B frame now has open guide interfaces, a rearward fixed spine, outboard
lift screw, below-boom nested screw drives and connected bearing/nut/motor
supports. Both200 mm extensions and the tool/body poses remain unchanged.
Compatible passive carriers retain independently attached outer/inner paths.
The supported-box sweep passes11,761 cross-body pairs over all independent
joint intervals. Two rejected static drafts remain preserved. Full-rack task
`b_a_telescoping_frame001` is separate from that static result; see
[geometry, limitations and reproduction](research/telescoping_guide_frame.md).

That full-rack task now passes at480 Hz in32.922917 s with one insertion
recovery, no seating nudge and all carrier gates; saved as B/A v014.
A/A's further support-setback variant also passes the same cycle duration
with one recovery, saved as v016. Reload025 and their respective travel
probes remain separate ongoing checks; C/A v021's completed travel result
must not be generalized to these assemblies.

B's travel probe now exercises all nine outer/inner limit/midpoint pairs at
each of five heights. It does not collapse the two extensions into summed
TCP X. Its47 endpoint plan is not a qualification until executed. There are
269 passing local unit tests; none substitutes for the pending physical checks.

## Revised-harness randomized cohort — terminal snapshot

Campaign006 on **C/A v020** completed all20 declared randomized conditions:
18 complete cycles, two physical-preseat fixture failures (trials006/019,
ports4/12). Thus the full protocol completes18/20; conditional manipulation
is18/18 admissible starts, not20 valid robot trials. The separate nominal
control passes. Summary001 validates the frozen evidence hashes. This cohort
is neither pooled with old harnesses nor attributed to the newer v021 geometry.

Predeclared `benchmark-plan005` selects A/A v016, B/A v014 and C/A v021,
24 paired conditions per design, seed20261018. All declared starts, including
fixture failures, must be retained;24 attempts do not guarantee20 admissible
starts. Campaign007 is now launched with one worker and required nominal
controls. No final result or ranking is claimed from its launch.

## CoreXZ guide/frame and compatible carriers — 2026-10-17 UTC

CoreXZ's supported robot-box full-travel screen is now clear: the v2 frame
uses real open guide channels, a shortened beam, stepped brackets and accessible
block fasteners. C/A v014/v015 both complete21.5375 s cycles and pass fresh
reloads. The stronger v2 box screen checks2,909 cross-body pairs; it explicitly
does not cover rack geometry, non-box shapes, flexible links or structural loads.

Compatible81-link carriers are integrated as C/A v016. Its240 Hz manipulation
and timed carrier gates pass, and reload017 reproduces that result. Startup
still reaches−1.494°, outside the one-degree tolerance. New tests make startup
part of overall carrier acceptance; a480 Hz comparison is separate, not a
global solver-rate promotion. [Geometry, evidence and limits](research/corexz_guide_frame.md).

246 local tests pass. Preservation-audit011 verifies62 saved versions and62
independent loads,59 declared outcomes; subsequent new versions/reloads remain
separately recorded. A/RG2 v010's failed grasp reproduces in reload015.
A/specialized v003 completes37.6625 s with one insertion recovery and one
nudge; its earlier native startup crash remains preserved, with cause unknown.
Whole-robot A/B corrections, complete rack/load/carrier/full-tool qualification,
revised-hardware benchmarks and final visual/gallery/package delivery remain open.

The480 Hz carrier comparison passes startup and timed carrier integrity but
fails latch release. Contact logs show the tool neck pressing on the boot;
using the full existing press stroke still fails. A separate
[forward-neck geometry experiment](research/latch_tool_clearance.md) keeps
the connector, collisions, force cap and success gates unchanged. The new
C/specialized-tool carrier version fails alignment and remains preserved.
The new forward-neck C/A v019 completes21.5167 s at480 Hz with no recovery
or nudge, passing startup and timed carrier gates. Reload021 independently
reproduces it. A matching480 Hz unloaded midstroke power-loss probe passes
with7.0963 mm maximum descent; this does not qualify all payloads/strokes or
emergency-stop safety. Its three macro samples show press/separation/reseating,
but dark lighting and missing full-motion review prevent final visual acceptance.

## Open insertion-stage correction — 2026-10-17 UTC

The new collision-enabled open frame and raised rails clear the entire125 mm
fixed-carriage/moving-tool box sweep without changing TCPs or joint travel.
Corrected A/A v014,B/A v013,C/A v013 complete powered full-rack tasks with no
retries/nudges in21.517/21.517/21.537 s. They isolate the stage correction;
old carrier mounts are incompatible and rejected. Whole-robot audits still
flag52/26/16 box-pair overlaps, so these are not buildability-qualified.
[Geometry, failed first revision and limits](research/open_insertion_stage.md).

The six insertion-stage versions brought the saved total to62. Reload013
and014 have both finished all three physical/dependency checks, including
the corrected versions. RG2 and specialized-tool integration trials remain separate.
The earlier960 Hz failed-grasp video is preserved at1080p30 and passes Mac
playback/seek, but occlusion prevents final visual acceptance.

## Full-travel audit — new mechanical failures, 2026-10-17 UTC

Revised carrier-equipped A/A v012, B/A v011 and C/A v011 complete powered
cycles in32.910/21.517/23.446 s at960/480/240 Hz, respectively. All pass the
new mount-to-mount joint-limit sweep, but the broader mount-to-robot-box
sweep fails16/2/8 pairs. The insertion stage also has adjacent-body solid
interference hidden by its joint collision filter. These models are **not
buildability-qualified**, regardless of task passes. The next mechanical
correction must address the stage cross-section and full stroke, not only
carrier brackets. [Carrier audit details](research/service_carriers.md).

Six additional successful/failed packages brought the saved total to56;
reload-campaign011/012 subsequently completed all declared-outcome/dependency
checks. The B960 Hz brake probe passes holding and
carrier limits but fails its target-cable clearance gate.227 local tests pass;
unit tests do not negate these full-scene failures. No final hardware ranking,
showcase, updated gallery or completion claim is made.

## Passive motor brakes and media checkpoint — 2026-10-17 UTC

Dimensioned brake packages and delayed, torque-limited passive holding are now
implemented, with explicit modeling limits in [powered-off brakes](research/powered_off_brakes.md).
The new A/A v010, B/A v009 and C/A v009 complete powered RJ45 cycles with
brakes released. Lower-rate power-loss probes fail carrier or clearance
gates; separate A/C960 Hz unloaded midstroke probes pass their declared
checks. Neither result establishes full-stroke or powered-off safety.
The before-reset precision-jaw state fix removes the spurious initial jaw
overlap found in the probe contact logs. Old versions and their evidence stay
unchanged. A/A's new cycle uses insertion recovery, which remains reported.

The second rendering batch finished all20 full-cycle1080p30 captures. Its
three specialized-gripper edits initially failed on an unmapped controller
phase; those errors remain in the original batch. Corrected exact-frame edits
are under `experiments/render-edits002/{AC,BC,CC}`. All25 downloaded camera/
edited videos pass Mac playback/seek, with input/source/video hashes checked.
Selected original macro/side frames were inspected: occlusion, dark materials
and older hardware details still prevent final visual acceptance. These are
not renders of the new brake-equipped assemblies. The full B/A replacement
side clip also passes playback; its parked assembly no longer has the prior
right-edge crop. No final showcase or updated gallery is claimed.

## Comparison gallery and revised-hardware checkpoint — 2026-10-17 UTC

Use the existing `bash scripts/connect.sh` tunnel, then open
[the comparison gallery](http://127.0.0.1:18080/robotics-gallery003/).
It is a versioned development snapshot, not a final ranking or live job monitor.
Filter all nine combinations by robot, tool or feasibility; compare original
benchmark rates and the separate neighbor screen; expand each design for
recorded videos, downloads, physical references and all preserved version
paths/commands/configs/results/reload evidence. Missing images/clips stay
explicitly pending. Legacy render provenance and failed historical versions
are visibly distinguished from verified newer replay sources.

`scripts/build_gallery.py` checks evidence identities, package/result hashes,
render source/video hashes where available, and copies only allowlisted files
under the existing artifact HTTP root. No new service, port or cloud hosting
is created. The gallery contains no symlinks to the workspace. Reproduce to a
**new** directory; previous gallery snapshots are preserved:

```sh
.venv/bin/python rack_robotics/scripts/build_gallery.py --output artifacts/robotics-galleryNEW
.venv/bin/python rack_robotics/scripts/check_gallery.py \
  --url http://127.0.0.1:18080/robotics-gallery003/ --output artifacts/gallery-qaNEW
```

Click **Load playable clip** before using video controls. The original Python
artifact server does not honor byte-range requests; direct HTTP seeking stalled
in the first browser audit. Gallery003 explicitly loads just the selected clip
into browser memory, enabling seeking without replacing the live desktop's
server. Clips do not autoplay; changing filters releases loaded video memory.
Direct MP4 download links remain available. The failed first audit is preserved
under `artifacts/gallery-qa001/failure.json`.

The corrected gallery passed the actual Mac/SSH browser audit in
`artifacts/gallery-qa002/report.json`:182 served file hashes, all eight clips
decoded/played/sought, nine cards/rows,34 version records, combined filters,
image loading and mobile horizontal-overflow checks; no browser errors.
Desktop/mobile screenshots were inspected. This verifies the gallery UI and
delivery path, not final visual fidelity or completion of all media.

New drive-connection details add coaxial motors, couplers, nuts, bearing supports,
guide blocks and collision-enabled brackets. Eight new versions preserve real
interference failures and subsequent corrections. A/A v005 and B/A v003 each
pass a21.5375 s cycle; C/A v004 passes in23.4458 s with one nudge. All three
fresh reloads/dependency checks pass. `preservation-audit003.json` reconciles
all34 saved versions, with the historical B/A v001 mismatch unchanged.
See [drive connection evidence](research/drive_connection_revision.md) and
[updated mechanical measurements](research/mechanical_screening.md).

`benchmark-campaign005` finished20 new conditions for each revised A/A, B/A
and C/A model. `benchmark-summary014.json` verifies20/20,20/20 and19/20 complete
cycles respectively, with60 admissible randomized trials and three separate
passing controls. C/A trial016 failed latch release at port08 after two
recoveries; the failure remains counted. This changed-hardware cohort must not
be pooled with the original110 trials. See the version-specific report above.
The completed40-case [occupied-neighbor screen](research/occupied_neighbor_screen.md)
belongs to the original versions: A/A,A/C,B/A5/5 clearance; B/C,C/A4/5;
C/C2/5; A/B,C/B0/5. RG2 contacted neighboring cables in four cases per
architecture; small reported impulses establish contact, not damage.

`render-campaign001` records four1080p30 views for the three revised gripper-A
assemblies. `render-campaign002` does the same for the other five successful
original combinations, using their saved physical trajectories. Each frozen
batch then makes exact phase-aligned multi-angle edits. Check actual PIDs,
state and render manifests before declaring capture complete; composition,
temporal quality and Mac playback remain separate acceptance gates. The older
A/A v001 `multi_angle001` is already a complete647-frame synchronized edit,
with actual Mac decode/play/seek evidence, but is not the revised hardware.

Service carriers are now implemented as passive attached rigid links in new
development versions. A/A v008 and C/A v007 pass full task cycles, timed carrier
integrity checks and fresh reloads. Their startup angle transients and broader
mechanical acceptance remain unresolved. Four B revisions preserve upright,
rack, bracket interference and hinge-limit failures. The same final B geometry
at480 Hz (v008) completes21.51667 s with passing timed carrier checks and
startup traces within those bounds; its fresh reload also passes. This is
timestep-sensitivity evidence, not solver convergence or hardware validation. See the
[carrier development record](research/service_carriers.md). Earlier successful
benchmarks do not include this new hardware.

201 local tests pass. Full PLAN_p2 remains open: cable-carrier validation, powered-off
brakes, detailed rack/fastener/load/buildability and tension/coverage audits,
new-cohort mechanical interpretation, all-design visual acceptance, high-resolution showcase,
complete gallery media/downloads, final scoring/BOM and final audit.

`render-campaign001` is now terminal:12 full-cycle1080p30 captures and three
synchronized multi-angle edits for revised A/A,B/A,C/A. Downloaded video,
manifest, frozen-renderer and physical-input hashes verify; all15 clips passed
Mac decode/play/seek checks. This is not final visual acceptance. Sampled B
side footage crops the mechanism; a wider opposite-side probe contains the
parked assembly and its full-cycle replacement is `b_a_side_composition002`.
A/A macro footage still has actuator occlusion. The second five-design rendering
batch remains separate and active; inspect actual processes before resuming.

Revised A/A v005's wide and rear captures have now completed647 frames each
(21.5667 s at1080p30), and both downloaded videos passed actual Mac decode,
play and seek. `render-campaign001/AA/{wide,rear}` holds their manifests,
playback reports and bounded sampled-frame visual reviews. They are not yet
final-quality accepted: the rear tool partly occludes the latch, fine details
remain soft, and full temporal/macro/side review is pending. Only three selected
frames per view are copied locally; the complete frame sets remain on the VM.

## Current replay/reload checkpoint — 2026-10-16 PDT

The replay pipeline now rejects blank frames, waits for capture completion,
checks the captured camera view matrix against the animated USD camera, and
checks renderer settings again after initialization and every capture. Source
scene/results/trajectory hashes and measured body-pose checks remain mandatory.
These checks are necessary but not sufficient for final visual acceptance.

Probes007/008/010 produced black PathTracing captures. Probe009's manually
swapped viewport product captured the wrong overhead camera despite a correct
USD relationship; it is rejected too. The camera-bound Replicator RGB path
produced the intended macro image in011, with camera matrix residual below
1e-15. Its legacy renderer token was normalized by Kit to RealTimePathTracing;
the011 manifest predates post-initialization mode checks and must not be used as
proof of the requested token. The current default explicitly uses the supported
`RealTimePathTracing` token and eight paused rendering subframes per recorded
sample. Offline PathTracing remains unresolved in this installed configuration.
No physics changes or infrastructure rebuild were made to obtain these captures.

The installed viewport capture and Replicator source were inspected. The
[NVIDIA capture example](https://github.com/isaac-sim/IsaacSim/blob/main/skills/isaac-sim-rendering/scripts/capture_pipeline.py)
also demonstrates a camera-bound RGB annotator. Our replay uses zero time
advance, verifies the recorded timeline, and retains actual capture-camera
checks instead of treating camera selection alone as proof.

Fresh A/B v004/v005/v006/v007 reloads reproduce their failed grasp with matching
packaged source and zero unresolved dependencies (56/56/57/57 hashes respectively,
21 layers and150 dependency assets each). Their audit files are in
`experiments/a_b_reload_v00{4,5,6,7}/asset_validation.json`. They are failure
reproduction evidence, not task passes or randomized reliability trials.
`scripts/reload_environments.py` runs an explicit list in separate Isaac
processes, validates package hashes before and after, freezes its validation
script, and writes numbered checkpoints in a new-only batch directory.
`experiments/reload-campaign001` has completed: all five fresh-session reloads
(A/B v008 and B/B v002–v005) reproduced failures and passed dependency validation.
Its terminal `summary.json` is downloaded locally. These are reusable failed
designs, not manipulation successes. A consolidated all-version ledger remains
to be assembled.

### Occupied-port and full-cycle video checkpoint

`experiments/crowded-aa001` completed a physical cycle in22.0333 s at port04
with adjacent ports03/05 occupied. The timed trial reported no robot/neighbor
contact pairs, maximum neighboring cable-joint gap0.01981 mm, and housing drift
below0.00008 mm. The target latch/plug constraints were unchanged. Neighboring
housings are restrained fixtures, with baseline passive hinges and dynamic,
free-ended cables; this is **not** neighbor-retention or cable-tension validation.
Results are explicitly excluded from the110 sparse-row randomized trials.

`scripts/screen_occupied_ports.py` freezes a paired diagnostic harness and runs
every declared case, retaining task and initialization failures. Batch
`experiments/occupied-screen001` is testing eight feasibility-passing designs
at ports04/08/01/16/12 using plan001 conditions000–004 (40 cases). Check actual
PID/log and `state.json` before any continuation; it has no automatic retry.
The replayer now requires and animates every occupied-neighbor cable jacket
from its own recorded rigid-body poses, rejecting missing recorded links.

A/A full macro013 and wide013 both completed647 frames at1920×1080/30 Hz and
passed Mac Chrome play/seek. Macro sampled contact views show the pressing pad
and returned latch, with actuator occlusion on the left. Wide013 is **rejected
as final footage**: its final frame still has conspicuous ghosting despite
the prior camera/pose/settings checks. See its `visual_review.json`. Rear013
and side013 require their own complete inspection. Supported spatial AA can
now be selected with `--anti-aliasing fxaa` for a diagnostic comparison against
the default DLSS history; no ghosting fix is claimed before rendered evidence.
Probe014 was rejected before capture: this runtime forced FXAA back to DLSS,
which the post-initialization settings check caught. A subsequent diagnostic
uses `--reset-render-history`, calling the installed USD context's
`reset_renderer_accumulation()` immediately before each capture. This follows
[NVIDIA's temporal-reset guidance](https://docs.isaacsim.omniverse.nvidia.com/6.1.0/replicator_tutorials/tutorial_replicator_getting_started.html#dlss-temporal-reset);
the method is also present in this installed `omni.usd-1.16.0` API. It changes
only render history, never the measured trajectory or simulation physics.

`experiments/preservation-audit002.json` reconciles all26 versions against
current package hashes and the original result hashes named by their reload
validators. All26 saved scenes have load/dependency evidence;25 reproduce the
declared outcome. B/A v001 resolves28 packaged files,11 layers and150 assets,
but its physical reload fails and two packaged sources differ from the initial
trial sources. Neither discrepancy is relabelled as success. Use B/A v002 for
the successful preserved/benchmarked design. Rebuild the ledger without Isaac:

```sh
python3 rack_robotics/scripts/audit_preservation.py --output NEW_AUDIT_JSON
```

This ledger rechecks current hashes and historical dependency/reload evidence;
it does not claim to rerun physical simulations or resolve the VM's asset paths
on the Mac. The26-version count includes every intermediate failed revision.

Current render command (choose a **new** output directory):

```sh
/isaac-sim/python.sh rack_robotics/scripts/render_replay.py \
  --attempt rack_robotics/experiments/benchmark-campaign002/AA/control-attempt001 \
  --output NEW_OUTPUT_DIRECTORY --view rear --renderer RealTimePathTracing \
  --capture-backend replicator --render-subframes 8 --no-denoiser \
  --eye -.20 1.3 1.88 --target .08 .5 1.69 --allow-root
```

Full-cycle composition, temporal review, four-camera sets for all successful
designs, the edited showcase and gallery remain required; diagnostic probes do
not satisfy those deliverables.

## Infrastructure observation, 2026-10-16

Existing container `dell-rack-sim`, Isaac Sim
`6.0.1-rc.7+release.42383.32955d8d.gl`. Both RTX PRO 6000 Blackwell
Server Edition GPUs report 97,887 MiB. `/workspace` has 158 GiB available.
The live GUI is `/workspace/run-GzKr1z/demo.py`; it remains running separately.
The latest browser inspection showed the 16-port rack in perspective and another
physical transfer completed. The viewer connection was restored without restart.

## Baseline tools

Inside the existing container, from `/workspace`:

```sh
python3 rack_robotics/scripts/freeze_baseline.py
/isaac-sim/python.sh rack_robotics/scripts/check_baseline.py --allow-root \
  --baseline /workspace/rack_robotics/assets/shared_rack/baseline-001 \
  --output /workspace/rack_robotics/experiments/baseline-001-full-rack
```

The freeze tool refuses to overwrite snapshots. Re-running it verifies hashes.
The regression requires a new output directory and opens the saved full rack in
a fresh Isaac session. It does not write the live viewer's telemetry or images.

Phase 1 result: `experiments/baseline-001-full-rack/results.json` passes all 121
checks after a fresh load of the frozen USD. Sixteen socket transfers including
reversal; all sockets retained under the baseline 5 N pull and physically
released. Worst cable joint gap 0.0537624 mm. Log on VM:
`/workspace/artifacts/logs/p2-baseline-001.log`. Eleven existing local tests pass.
The snapshot contains 53 preserved files and hashes of 1,822 vendor dependencies;
it is also copied to the Mac workspace. Read-only permissions plus hash checking
provide change detection, not hardware-enforced immutable storage.

Phase 2 initial reports: [robots](research/cartesian_robots.md),
[grippers](research/grippers.md), [RJ45 mechanisms](research/rj45_mechanisms.md),
[licenses](research/sources_and_licenses.md), [nine-combination matrix](research/candidate_matrix.csv).
This is a design shortlist, not a reliability ranking. Implementation must still
resolve dimensions, drive calibration and clearances and preserve failed trials.

## Phase 3 — physical reference prototype in development

The first assembly is a fixed-to-rack screw-driven XYZ articulation with an
EGP25-sized tool envelope, independent parallel fingers and a separately driven
latch tongue. This is a dimensioned custom assembly, not a verified SCHUNK CAD
digital twin. The shared task controller commands only robot/gripper joints;
the connector observer cannot issue plug commands.

Every feasibility attempt refuses an existing output directory and preserves a
source snapshot with SHA-256 hashes, initial USD, result or exception report,
and (when physics starts) measured trajectories and a diagnostic image. The
temporary pre-seating actuator is made inactive before robot operation. Its
removal does not reset the connector's already-measured latch state; all baseline
hook-clearance and escape checks continue unchanged.

Experiments so far (all **isolated contact tests**, not rack-integration passes):

| Attempt | Actual outcome |
|---|---|
| `a_a_attempt001` | Stage-loading concurrency error before physics |
| `a_a_attempt002` | Installed API mismatch before physics |
| `a_a_attempt003` | Connector remained physically hooked but observer state was reset at actuator handoff; initialization rejected |
| `a_a_attempt004` | Physical grasp, latch depression, withdrawal and separation succeeded; reinsertion did not re-engage the hook; approximately 4.4° initial plug pitch persisted in flat jaws |
| `a_a_attempt005` | First chamfered guides interfered with the taller cable boot; jaw aperture check rejected the grasp |
| `a_a_attempt006` | Shorter guides restored grasp and withdrawal; approximately 2.5° pitch remained and the hook did not re-engage |
| `a_a_attempt007` | Complete isolated cycle passed after replacing the guide's flat convex-mesh land with an analytic box collider; measured grasp pitch below 1° |

Full-rack `a_a_attempt008_full_rack` passed the complete cycle in 21.5375 simulated
seconds. Maximum cable joint gap was 0.052714 mm. The runtime topology audit found
38 freely dynamic plug/latch/cable bodies and 133 enabled connector/socket
colliders. The only active plug joints connected it to its own latch and cable;
all three original demo-actuator prims were inactive. This is **one feasibility
trial**, not a randomized reliability result or a complete collision/load audit.

The original rack and latch geometry have not been changed. Forty-five local
controller/viewer/connection unit tests pass; mocks are not physics evidence.

`environments/robot_a_gripper_a/v001` preserves the first successful assembly.
Its generated `demo.py` loaded that saved USD (without rebuilding robot geometry)
in `experiments/a_a_reload_v001` and completed the same physical cycle.
`reload_verification.json` confirms 22 packaged file hashes, 11 USD layers and
150 external assets with zero unresolved dependencies. Config/manifest record
the original packaging status; the separate verification file records the later
reload result without rewriting the package. The v001 controller predates the
new recovery code and is deliberately retained unchanged.

Subsequent full-rack recovery tests use the updated shared controller:

- `a_a_fault_latch_001`: the first latch-press command was deliberately withheld.
  The controller waited, reset the press and retried; full cycle passed in
  25.7417 s. Axial tool movement during the wait was approximately 3.6 µm.
- `a_a_fault_grasp_001`: the first jaw-close command was deliberately withheld.
  The controller detected the open aperture, opened/retracted/reapproached and
  completed the full cycle in 27.75 s.
- These are explicit actuator-command fault tests, not randomized reliability
  samples. Observations, collisions and latch mechanics were not overridden.
  Bounded insertion recovery exists but still needs physical fault tests.

Inside the existing VM container:

```sh
/isaac-sim/python.sh -u rack_robotics/scripts/run_reference.py --allow-root \
  --minimal --output /workspace/rack_robotics/experiments/NEW_ATTEMPT
```

Omit `--minimal` for the full frozen rack. `package_reference.py` preserves a
versioned assembly with shared baseline composition, four cameras, config,
manifest, source, trajectory, results and a fresh-session launcher. Packaging
alone is not reload verification.

To execute the preserved environment in the existing VM container:

```sh
/isaac-sim/python.sh -u rack_robotics/environments/robot_a_gripper_a/v001/demo.py \
  --allow-root --output /workspace/rack_robotics/experiments/NEW_RELOAD
```

These prototype runners are headless. The existing interactive desktop still
shows the original rack demo; it has not been replaced with the robot prototype.

`render_replay.py` consumes a recorded attempt with physics stopped and labels
the video as recorded replay. It is under validation: the first replay renders
did not faithfully display the recorded plug transform despite correct USD
values. These videos are marked invalid, not accepted as trajectory evidence.
The newer render-only baked USD layer shows the recorded motion correctly in
sampled full-rack frames. `a_a_attempt008_full_rack/replay_macro_001/demo.mp4`
is a 647-frame, 1920×1080, 30 fps diagnostic. Chrome on the Mac successfully
decoded, played and sought it (`mac_playback.json`). It is **not a final macro
deliverable**: the initial camera obscures the latch behind the actuator housing.
Named, time-sampled cameras and additional inspection lighting are being checked
in `macro_camera_probe*`; a complete multi-phase visual audit remains pending.
No final video deliverable is claimed yet. The reference
prototype still needs a complete rack collision/load audit, insertion-recovery
fault tests, repeatability, contact-force measurements and all alternative designs.

Visual/mechanical inspection follow-up: the initial wide camera crops the rack
and has been widened for the next probe. The simplified motor blocks also need
coaxial shaft/coupler and mounting-plate detail; top/bottom end-stop geometry,
drive nuts and robot cable carriers still require refinement and an assembly
audit. Do not treat the current primitive motor envelopes as finished hardware
CAD. `macro_camera_probe003` makes the plug/latch readable using a baked named
camera and a soft inspection light, but its two-frame sample is not a full-cycle
video validation.

## Phase 4 — second architecture and specialized tool

Architecture B has a rack-side lift, two actual 200 mm prismatic extension
stages with 300 mm members/100 mm overlap, and the shared short insertion axis.
Its parked leftward overhang is approximately 250 mm beyond the rack side;
this is a real clearance disadvantage, not hidden by rescaling the assembly.
`b_a_attempt001` passed the full-rack cycle in 21.5375 s. Its first saved-scene
reload, `b_a_reload_v001`, failed because the released hook rested on the
socket-lip edge; both insertion retries failed. That failure remains preserved.

The shared controller now allows at most two measured, force-limited 0.15 mm
seating advances when the plug is held, aligned and inserted but the hook is
not behind the lip. `b_a_seating002` loaded the same v001 scene and passed with
one advance in 23.4458 s. A fresh assembly `b_a_attempt002` passed without an
advance. B/A v002 is packaged with the exact tested source. Its fresh-session
reload passed in 23.4458 s with one seating advance. Verification passed all 31
packaged hashes, 11 USD layers and 150 assets with no unresolved dependencies.
None of these are randomized reliability samples.

Gripper C (`specialized_tool.py`) is an original parametric adaptation of the
Reis fixed/sliding-jaw principle: fixed datum shoe, rack-driven opposite shoe,
full-size HS-422/PQ12 actuator envelopes, independent tongue and spring-bounded
vertical/pitch wrist. The rack jaw has no linear drive; a PhysX rack-and-pinion
constraint transmits the rotary servo's torque. The 6 mm pitch radius, 0.06 N·m
torque cap and compliance settings are uncalibrated design assumptions. Tooth
compliance/backlash, motor thermal/duty limits and real manufacturing tolerances
are not represented yet.

`tool_c_transmission001` exposed an incorrect transmission sign. The corrected
`tool_c_transmission002` passed seven isolated physical checks: close/reopen,
6 mm pitch-radius relation (worst sampled residual 0.00434 mm), and a negative
control in which the disconnected pinion turns while the jaw remains open.
This proves the drive coupling, not RJ45 manipulation.

Isolated C attempts are preserved: 001 jammed against insertion-stage rails;
002 cleared those rails but the fixed shoe caught the taller boot; 003 used a
lateral approach, then detected the still-open jaw and failed during recovery.
The shared interface now supports a fixed-shoe approach/release offset and
measured compliant-TCP compensation through joint commands. No plug transform,
socket collision or latch-spring parameter is changed by these additions.
End-to-end C feasibility and crowded-cable compatibility remain unproven.

C attempts 004–006 exposed startup-command problems around the upper lift
stop; 006's contact report contained five actual socket/plug/latch pairs and no
reporting errors. The initial trajectory now starts at the measured TCP, and
compliance compensation is bounded to 2.5 mm and saturated at real actuator
limits. Task success still uses actual TCP error; saturation does not count an
unreachable target as reached. Exception recordings now retain their first frame.
Attempt 007 suffered a native Kit crash during physics startup, before the
controller ran. Its dump/logs are preserved and the specific crashed process
was terminated; the original GUI remained running. The crash cause is unknown.
Attempt 008 started physics without that crash, then aborted on the 2.5 mm wrist
deflection guard. Its measured trajectory shows growing startup oscillation
under unfiltered compensation. The next revision filters the equilibrium offset
with a 0.15 s time constant and 3 mm/s rate limit, retaining the raw deflection
guard and joint stops. This is ground-truth pose feedback, not modeled sensing.
The finger roots are now 5 mm wide on their outward side, retaining narrow tips
and boot clearance; see the preliminary beam estimate in the gripper report.

Attempt 009 reached grasp after filtered compensation, but shoe/boot contact
and abrupt closing impulses exceeded the deflection guard. Attempt 010 used
5.7 mm travel, 2.5 mm approach offset, 4.5 mm outward-thickened roots, an
80 N·m/rad pitch spring, 180°/s servo speed limit and 20 mm/s tongue limit.
It grasped/aligned the plug but correctly refused to withdraw: two latch retries
left the hook above clearance. Contact reports identify the cause: the tongue's
neck hit the boot (~4.12 N pair impulse/dt peak), stopping the press at 4.05 mm
instead of the requested 5 mm. The next geometry moves the neck forward 1.5 mm
and narrows its depth, without changing the latch, boot, force cap or clearance
threshold. Transmission probe 003 passed all eight checks for the larger travel,
including a measured sampled peak speed of 180.05°/s and disconnected control.

`a_c_attempt011` then passed the complete **isolated** contact cycle in 23.2833 s
with no recovery or seating advance. Cable maximum gap was 0.08245 mm. Its
29 reported contact pairs had no reporting errors and no cable/robot pair;
this is not a dense-rack clearance audit.

`a_c_attempt012_full_rack` passed in 23.3417 s, cable maximum gap 0.05579 mm.
Its 34 contact pairs had no reporting errors; no robot/cable or robot/rack/server
pair was reported on this trajectory. Peak datum-shoe contact estimate was
17.16 N, so gentler alignment and force-limit calibration remain important.
`b_c_attempt001_full_rack` failed during datum alignment: 2.5024 mm measured
wrist deflection exceeded the 2.5 mm guard; peak datum-shoe estimate 19.28 N.
This is an unresolved control/contact issue, not proof of mounting incompatibility.
Both assemblies are preserved as `robot_a_gripper_c/v001` and
`robot_b_gripper_c/v001`, with saved joint settings, body masses and proper
hardware-reference links. Fresh-session reload checks are in progress.

## Contact-control and third-architecture checkpoint

A/C v001 fresh reload passed in 23.3417 s. B/C v001 fresh reload reproduced
the same deflection failure at datum alignment. Both package checks verified
33 hashes, 11 USD layers and 150 assets; the B/C verifier explicitly records
`task_passed=false`, not a successful manipulation result.

`b_c_attempt002_contact_policy` froze gravity-sag compensation while handling
the connector, slowed datum travel to 1.4 s and limited each serial transverse
drive to 5 N during alignment. It passed in 23.7792 s without retries or seating
advances; maximum cable gap was 0.052714 mm. Its independent B/C v002 reload
also passed, and its file/dependency verification passed. Datum-shoe contact
fell to 6.14 N, but closure still produced a 30.60 N socket pair impulse/dt peak.
This is not a calibrated safety/load measurement.

`b_c_attempt003_soft_close` reduced the pinion speed from 180 to 60 degrees/s,
allowed 1.4 s for grasping, and retained the 5 N transverse drive cap through
grasp/latch release. It passed in 24.6417 s; the largest pair-contact peak was
14.32 N. `a_c_attempt013_soft_close` stalled at nominal alignment despite a
retained connector. The next shared capture gate uses measured housing-relative
offsets (X <1 mm, Y <0.5 mm, Z <0.7 mm) and a separate <1 mm nominal tool error.
The Z bound is inside the 0.8 mm guide lead-in. This permits a compliant wrist
to yield during capture; it does not relax grasp, latch, insertion or retention
success checks. `a_c_attempt014_measured_capture` passed in 24.3458 s with a
10.15 N largest pair-contact peak. Both latest trials had no retries/nudges,
0.052714 mm maximum cable gap and no contact-reporting errors. A/C v002 and
B/C v003 packaging/reloads are in progress.

The original failed B/C alignment now has a labelled 196-frame diagnostic
H.264 replay (1920×1080, 30 fps). Mac Chrome decoding/playback/seek passed;
the actuator obscures part of the wrist, so it is not a final-quality video.
The latest A/C full-cycle macro replay is being rendered. No four-view or
showcase deliverable is claimed yet.

`corexz.py` and `belt_gantry.py` implement the third architecture using two
stationary motor coordinates and power-consistent coupled forces. X/Z guide
joints have zero position/velocity gains. Gravity compensation is inside the
motor force caps. The physical `corexz_transmission002` probe passed six checks:
gravity hold, diagonal tracking, zero independent gains, loss of one motor
disturbing both axes, recovery after restoring it and motor caps. Position
tracking errors were approximately 1 micrometre in this isolated test. Probe
001 lost its report to NumPy scalar JSON serialization; it is preserved and is
not counted as a physics pass. Probe 003 repeats the six checks after correcting
idler-bracket/stop clearances, before the first full-rack C/A trial.

Belts remain an uncalibrated lumped elastic model; actual belt tooth/slack,
rotor inertia, tensioners, brake/counterbalance, cable carriers, detailed CAD,
load/clearance/neighbor-cable audits remain unfinished. Transmission tests do
not prove RJ45 feasibility or reliability. Architecture/gripper alternatives,
all compatible combinations, randomized benchmarks, final videos/gallery and
the complete PLAN_p2 acceptance audit remain required.

CoreXZ probe 003 passed all six transmission checks after the clearance edits.
`c_a_attempt001_full_rack` then completed the actual robot-driven cycle in
21.5375 s, with no retries/nudges and 0.052714 mm maximum cable gap. The topology
audit passed. The 40 contact pairs had no reporting errors; a cable-link/tool
housing pair recorded five contacts, 0.094 N peak estimate and 0.00076 mm maximum
penetration. The largest connector-contact estimate was 31.59 N. This is not a
collision-free/low-force certification. Sampled motor-side force stayed below
7.91 N per motor. C/A v001 packaging and fresh reload are in progress.

The latest A/C v002 and B/C v003 saved-scene reloads both passed at their original
24.3458/24.6417 s cycle times; dependency verifications are in progress. The C/C
trial uses the same specialized-tool capture policy, with its 5 N transverse
cap allocated between the two belt motors while preserving lift support within
their individual force caps. Disabled motors cannot be recreated by the force
allocator. Sixty-one local guard/kinematics/controller tests pass; these tests
are not physical reliability evidence.

The latest A/C v002, B/C v003 and C/A v001 dependency/hash verifications passed
(36, 33 and 36 packaged files respectively; each 11 layers/150 assets). All
three packages contain the exact originally tested source. C/C's initial
full-rack trial passed in 24.3458 s without retries/nudges, maximum cable gap
0.052714 mm, 38 contact pairs/no reporting errors and a largest pair peak
estimate of 23.78 N. Sampled transverse force during datum/grasp/latch phases
stayed at or below its 5 N allocation cap. No robot/cable/rack/server contact
pair was reported on that particular C/C trajectory; dense-cable compatibility
still has not been tested. Its v001 package is undergoing a fresh reload.

The latest A/C diagnostic macro video finished: 731 frames, 1920×1080, 30 fps,
24.3667 s H.264. Mac Chrome play/seek passed. Sampled frames show withdrawal
and reinsertion, but the actuator still occludes the left side. The required
multi-angle final videos remain outstanding.

## File-only tooling and results overview

`scripts/setup_usd_tools.sh` installs pinned `usd-core==26.8` in an isolated
`/opt/rack-usd-tools` environment inside the existing container. It does not
change Isaac's Python, launch a service or provision infrastructure. The
persistent `/workspace` mount is `noexec`, so native USD libraries cannot be
loaded from a virtual environment there. Outputs and source remain persistent
under `/workspace`; the tool environment can be recreated with the script.

Packaging can use `/opt/rack-usd-tools/bin/python3` without starting RTX. For
dependency verification, also pass
`--asset-search-path /isaac-sim/kit/mdl/core/Base`: this explicitly resolves the
installed `OmniPBR.mdl` library. An initial USD-only check without this library
correctly failed and is preserved as `C/A v001/usd_core_verification.json`.
File-only checks never replace the actual fresh Isaac physics reload.

`scripts/summarize_trials.py --experiments rack_robotics/experiments --output NEW.csv`
exports robot development/reload/fault results with result hashes, scope and
contact estimates. It requires complete physical evidence before reporting a
full cycle and never counts these development iterations as randomized
reliability samples. Baseline and isolated transmission probes are excluded.
Sixty-five local tests currently pass, including these summary guards.

C/C v001's fresh Isaac reload (`c_c_reload_v002`) passed in 24.3458 s; its earlier
reload launch did not run because the package had not yet been created, and
that launcher error remains in `artifacts/logs/p2-c-c-reload001.log`. It is not
a physical trial or reliability sample. All 36 packaged C/C file hashes also
match after download to the Mac. `experiments/summary.csv` preserves the first
38-row overview; `summary-002.csv` adds the completed C/C reload.
C/C's final dependency check passed: 36 hashes, 11 layers, 150 assets, exact
tested source and no unresolved references. The latest overview has 39 rows.

## Third gripper: full-size RG2, development checkpoint

`rg2_tool.py` now mounts the original BSD-licensed RG2 linkage without scaling,
with custom narrow shoes, an offset cradle and an independent latch tongue.
Only the vendor motor joint drives its finger linkage. `rg2_kinematics.py`
accounts for closing-induced axial movement; the Cartesian controller corrects
it through insertion-joint targets, never connector or tool pose writes.

Two full-range physical sweeps at 240/480 Hz and a 1 N·m narrow-angle sweep
passed. Their source/asset hashes and measured geometry were independently
checked by `scripts/analyze_rg2_sweep.py`. Seventy-one local tests pass, including
RG2 geometry, inverse aperture mapping, invalid-input guards and depth
compensation across all three robot architectures.

A/B is **not yet feasible**: attempts 001–003 stopped before approach due to
startup mechanical interference. The original A/B v001 environment preserves
the failed design and reproduces that failure in a fresh Isaac session.
Verification passes 51 hashes, 21 USD layers and 150 assets, with exact tested
source and no unresolved dependencies; `task_passed` is explicitly false.
Startup contact logging identified central adapter/housing interference and,
after rerouting the cradle, wide-open shoe/depth-rail interference. Attempt
004 tests a joint-driven setup sequence and revised mass estimates. Full-size
geometry, original connector collisions and physical latch remain intact.

For new RG2 trials, `initialization_trajectory.jsonl` records physical tool
preparation and connector pre-seating separately from the timed task.
`render_replay.py --initialization` labels such footage STARTUP ONLY and never
claims it is a full autonomous cycle. Existing failed attempts and snapshots
are not overwritten. Randomized benchmarks, remaining combinations and final
multi-view deliverables are still outstanding.

Further RG2 tests: attempt 004 completed physical preparation but failed during
approach because its 144 mm cradle hit the upright and the shoe shoulders
contacted the depth rails. That design is saved separately as A/B v002.
Attempt 005 narrowed the cradle/crosshead to 94 mm and the shoulders to 6 mm;
its startup had no reported robot contact pairs, and approach completed.
Insertion-axis alignment then stopped on an actual rear-flange/bridge contact
(largest estimated pair peak 23.88 N). The next revision lowers that flange's
upper edge below the bridge. The narrower mount's current mass estimate is
0.48 kg, with 33 g per custom steel shoe. No A/B full-cycle pass exists yet.

The attempt 003 failed-startup replay is 4.033 s, 1920×1080, 30 fps H.264.
Mac decode/play/seek passed. Visual inspection shows the full RG2/cradle, but
the gantry beam hides the shoe contact, so this is not an adequate final
engineering close-up. Its explicit visual review preserves that limitation.

Attempt 006 lowers the rear-flange top to 25 mm below the tool plane. The
vendor base is also lowered a further 2 mm to clear the carriage plate's
lower edge; the shoe rise increases correspondingly to 67.3 mm, keeping the
same nominal TCP. Its result is pending. A/B v002's fresh reload reproduced
the original approach failure; this is preservation evidence, not feasibility.

Attempt 006 completed and failed alignment on the vendor base/carriage-plate
pair (52.26 N largest impulse/dt estimate), with the previous bridge contact
absent. Its source, initial scene, trajectory and contacts are downloaded.
The next local revision uses a 75 mm base drop, 75.3 mm shoe rise, a lower
rear flange and 36 g shoes. Original convex-decomposition collision meshes
remain unchanged. `rg2_parameters.py` and seven new static-clearance/mass/TCP
tests guard the known geometry regressions; **78 local tests pass**, but the
new revision has not run in physics.

### Remote interruption, 2026-10-17 02:34 UTC

GCP reports the existing VM as `REPAIRING`. Direct SSH and IAP banner exchange
timed out, and the existing desktop/artifact tunnel dropped. No restart,
instance replacement, provisioning or firewall change was requested. The
attempt 007 upload and launch did not connect; do not count it as a simulation
attempt. The front-oblique `replay_startup002` renderer was previously observed
running, but its completion is unknown and its download did not succeed.

Completed A/B trials 001–006, both fresh failure reloads, packages v001/v002,
all three isolated RG2 probes, geometry verification and the first diagnostic
video are preserved locally. Both downloaded packages match their 51/54
manifest hashes; their fresh dependency checks pass 21 layers/150 assets and
correctly report task failure. `experiments/summary-005.csv` has 47 development,
reload and fault rows; these are not randomized reliability samples.

On recovery: inspect the **same** VM/container, process list and existing
render output before starting anything again. Upload the local
`rg2_parameters.py`, `rg2_tool.py`, updated runner/render scripts and progress
files before testing the new geometry. Check whether the attempted output
directory exists and preserve it if so. Do not restart a renderer merely
because observation was interrupted. The original GUI's state must also be
checked before reconnecting the desktop. Full PLAN_p2 scope remains active.

Recovery update: the same instance returned to `RUNNING` with a new start
timestamp of 2026-10-16 19:35:19 PDT. The same container auto-started healthy;
both GPUs and persisted experiment directories were present. Inspection
confirmed no simulation/render process remained, the prior front-oblique
render had completed, and attempt 007 had not launched. After verified upload
of the revised source, attempt 007 was started. The unchanged original
`run-GzKr1z/demo.py --port-row --auto` was also relaunched, and the existing
SSH tunnel restored. Fresh telemetry shows perspective rendering and completed
port transfers again. No infrastructure was rebuilt or replaced.

The recovered front-oblique replay is unfortunately fully occluded by rack
geometry in the inspected frame. It is preserved and explicitly marked as
an unusable view despite passing Mac playback. A revised, centreline camera
is being tested with a single frame before spending another full render.

### RG2 full-matrix checkpoint, 2026-10-17

A/B attempt 007 completed the full cycle in 22.6375 s. It is preserved as
`environments/robot_a_gripper_b/v003`; its fresh physical reload and dependency
verification pass (55 hashes, 21 layers, 150 assets, exact tested source).
C/B attempt 001 also completed, in 24.5458 s with one seating nudge. Its
`robot_c_gripper_b/v001` reload and equivalent dependency check pass.

Both are **impact-sensitive development passes**. The maximum grasp-pair
impulse/dt estimates are 80.24 N (A) and 63.48 N (C), not calibrated contact
forces. After jaw release the connector settles to about 4.4 degrees and
0.44–0.45 mm radial offset while the hook remains behind the lip. The baseline
observer's retained-state hysteresis permits this; its 2-degree/0.22 mm
per-axis entry criteria do not prove the final pose meets those tolerances.
No precision, electrical connectivity, randomized reliability or hardware
safety claim follows. New summary columns expose final angle, lateral offset,
depth and hook position separately from the reported task pass.

B/B attempt 001 collided at initialization: the collapsed cradle/rear flange
overlapped the side lift. B/B v001 preserves and freshly reproduces that failure.
Attempt 002 authored a less-collapsed pose but still failed, because articulated
joint coordinates defaulted to zero on physics startup. Attempt 003 explicitly
authors 30 mm initial extension in each screw stage **before** `World.reset()`.
It has no reported robot self-contact pairs and reaches grasp. This is initial
scene configuration, not runtime joint-position or connector-pose overriding.
See [NVIDIA's articulation initialization documentation](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/dev_guide/rigid_bodies_articulations/articulations.html).
The RG2 park is now X = -140 mm; fully collapsed parking and full-row clearance
are not established for this tool.

A rate-limited 3 deg/s motor setpoint profile replaces the abrupt narrow-angle
step in new trials. Opening and closing each have 1.8 s dwell, and the same
profile is forwarded through actuator-fault wrappers. A/B attempt 008 at 1 N·m
reduced the largest pair estimate to 13.92 N but failed grasp after two retries.
Attempt 009 at 1.5 N·m also failed (14.81 N peak); B/B attempt 003 failed grasp
at that setting too (24.45 N peak). The aperture guard was **not** relaxed.
Failed A/B v004 and B/B v002 are packaged; newer failed attempts retain exact
source, initial scenes, contacts and trajectories pending packaging/reload.

The next trials restore the 1 N·m cap and add model-mass gravity preload through
the existing screw-lift position drive, still bounded by its force/travel limits.
This addresses the measured lift sag without feedback that cancels contact
loads. C already has motor-limited gravity feedforward and does not receive this
additional preload. A/B attempt 010 and B/B attempt 004 test this revision.

`run_reference.py --physics-hz {240,480}` now keeps initialization durations,
controller timestep and 30 Hz recording consistent across both solver rates.
Saved environment configuration/launchers retain the rate. This capability is
unit-tested; a loaded matched-rate comparison is still required.

The useful failed-startup `replay_startup003` is downloaded and passes Mac
decode/play/seek at 1920×1080/30 fps. The centreline view exposes the linkage,
shoes and depth rails; partial actuator occlusion remains. The A/B success macro
probe exposes the plug, tongue and socket but has substantial left-side actuator
occlusion. Neither is a final polished multi-view deliverable.

Follow-up: gravity preload removes the measured sag (A: 0.2897 mm, B: 0.1703 mm),
but A/B 010 and B/B 004 still fail slow grasp. The exact-source A/B 010/011
240/480 Hz pair is recorded in `experiments/rg2_loaded_rate_comparison001.json`.
Both fail, with different first-grasp behavior and contact peaks; this does not
establish numerical convergence. `scripts/compare_solver_rates.py` checks frozen
source hashes, named settings and contact timesteps while explicitly keeping
convergence and reliability unproven.

A/B 012 and B/B 005 test 7.6 mm guide throats instead of 7.3 mm, retaining every
guide collision shape. Both physically grasp/release the latch/withdraw, but
neither completes reinsertion. A exhausts measured insertion recovery and
cannot re-latch; B stops at failed insertion/release recovery. Their preserved
versions are A/B v008 and B/B v005. The tested 480 Hz failure is A/B v007;
other new failures are A/B v005/v006 and B/B v003/v004. Packaging of these
versions is not a fresh-session reload verdict.

The current revision restores the 7.3 mm orientation-support throat and uses
the measured retained housing centre for pickup, bounded to 1 mm and 2 degrees
from the nominal seat. After withdrawal, the original nominal socket target
is restored for reinsertion. This is explicitly simulator ground-truth feedback,
not modeled perception, and does not write connector poses. A/B 013 and B/B 006
test it. Grasp aperture, retention and slip checks remain unchanged.

Latest measured-pickup result: A/B 013 and B/B 006 both still stop at the grasp
guard after two bounded retries. They are not improvements in task outcome.
The known-good developmental RG2 scenes remain A/B v003 and C/B v001, with the
impact/final-pose limitations above. Current working RG2 defaults are an
unsuccessful low-impact research revision, not the recommended demonstration.
All 100 local unit tests pass; that does not establish physical feasibility.

Next diagnosis should distinguish a guide-land corner clamp from a genuine
housing-pad grasp using fresh bilateral contact evidence, rather than merely
relaxing the aperture threshold. The first slow grasp repeatedly stalls near
13.27 mm aperture; later retries encounter a housing already tilted by the
failed attempt. Better fingertip lead-ins/compliance or measured orientation
alignment may be required. The full plan still requires randomized trials,
dense-cable/rack-load/coverage audits, ranking, complete multi-view rendering,
gallery and final hardware/reproducibility delivery.

Latest preservation: A/B 013 is packaged as v009 and B/B 006 as v006; both are
downloaded with all 58 packaged hashes matching. Fresh reload checks for these
new failed revisions remain pending. `experiments/summary-007.csv` contains
64 development/reload/fault rows, explicitly excluding them from randomized
reliability estimates. The original live GUI remains separate and unchanged.

The B/B 005 side-camera probe shows the side lift, booms and RG2 cradle, but the
near rack upright obscures the connector. Its visual review calls it a mechanism
overview only. A full diagnostic replay is launched at
`experiments/b_b_attempt005_guide_clearance/replay_side001`, with log
`/workspace/artifacts/logs/p2-b-b-side-render001.log`. Check that process/output
before resuming; completion and Mac playback have not yet been verified.

## Seeded benchmarking framework

`scripts/run_benchmark_trial.py` loads an existing saved assembly and its frozen
low-level robot/gripper controllers. A separately frozen copy of the current
shared task adds the same bounded recovery policy across designs. The harness
checks the environment file hashes and all 53 immutable baseline file hashes,
and verifies that runtime modules actually come from those frozen directories.
This is a new controlled experiment, not a claim to replay the original saved
controller's feasibility result unchanged.

`experiments/benchmark-plan001/plan.json` predeclares ten paired conditions for
each of the eight development-passing designs. B/B is excluded from randomized
testing because it has no complete-cycle feasibility pass; its diagnostic
failures remain in the design comparison. The same ten conditions are used for
every selected design, with two trials at each of ports 1, 4, 8, 12 and 16.
The highest-ranked candidates will still require at least twenty trials.

| Variation | Declared range | Physical application |
|---|---|---|
| Initial robot pose | X ±2 mm, Y -1–0 mm, Z -2–0 mm | Joint-driven settling before the timed task |
| Calibration offset | X/Z ±0.1 mm | Actual joint commands, with nominal-target error still observed |
| Connector initial alignment | X/Z ±0.08 mm, Y ±0.05 mm; pitch/yaw ±0.5°, roll ±0.25° | Temporary physical pre-seat drive, disabled before task |
| Cable resting shape | ±12° heading, bend begins at segment 4/5/6 | Initial capsule poses with coincident joint endpoints, before physics starts |
| Approach trajectory | 0.85–1.15× approach/alignment duration | Controller timing only; latch dwell is unchanged |
| Friction/contact assumptions | 0.9–1.1× authored physical-material friction/contact offsets | Trial-layer opinions; no collider removal |

All port-specific connector/cable placement is initial scene authoring before
`World.reset()`. During the task only robot joint commands and the physical
latch tongue move the plug. Before/after topology checks enforce removal of the
baseline hand and plug-attached press. Startup and task trajectories are separate;
cable joint-gap maxima in benchmark reports exclude initialization.

The standalone nominal A/A control passed in 21.5375 s. This is a harness control,
not a randomized sample. `benchmark-campaign001` is now running two fresh Isaac
sessions at a time, with log `/workspace/artifacts/logs/p2-benchmark-campaign001.log`.
Each design must pass its nominal control before its randomized cases run. Every
declared failed initialization/manipulation is retained; missing launcher results
leave the campaign incomplete rather than disappearing from the denominator.
Do not tune the frozen campaign while it is running.

From `/workspace` inside the existing container:

```sh
python3 rack_robotics/scripts/evaluate_all.py \
  --plan rack_robotics/experiments/benchmark-plan001/plan.json \
  --output rack_robotics/experiments/benchmark-campaign001 --workers 2

# Use a NEW report filename; summaries never overwrite an earlier snapshot.
python3 rack_robotics/scripts/summarize_benchmark.py \
  --campaign rack_robotics/experiments/benchmark-campaign001 \
  --output rack_robotics/experiments/benchmark-summary001.json
```

The campaign directory above already exists: **do not run the launch command
again**. First inspect the recorded process and log. `--resume` is available only
after the original evaluator and children have stopped; an inherited file lock
and recorded live-PID check reject overlapping runs. Finished results are
hash-checked and never rerun. Incomplete attempts get new attempt directories,
with prior evidence retained. A simulation observation timeout is not a reason
to resume or restart.

`summarize_benchmark.py` checks the plan, conditions, frozen harness and each
finished result/source hash. It records complete/unplug/replug outcomes, contact
estimates by phase, robot/rack contacts, final pose, latch-clear observations,
cable displacement and gap. It withholds success rates and Wilson intervals for
incomplete designs and never supplies a final hardware ranking. Ten successes
out of ten would still have a roughly 72–100% Wilson 95% interval, not certainty.
Cable gap/displacement is not tensile-force measurement; final retained-state
hysteresis is not proof of precise alignment or Ethernet connectivity.

`export_campaign_snapshot.py` streams only finished trials and a matching state
snapshot, avoiding partially written trajectories during Mac downloads. Every
trial's `harness/run_benchmark_trial.py` can reproduce the run in a fresh session
with the same `--environment`, `--condition` and a new `--output` directory.

The B/B 005 diagnostic side video has now completed: 22.633 s, 1920×1080/30 fps,
Mac Chrome decode/play/seek passed. It shows the telescoping mechanism but the
rack upright obscures the connector; it is not a final latch-detail video.

## Benchmark fixture and recovery checkpoint — 2026-10-17 UTC

`benchmark-summary002.json` is a hash-checked snapshot, not the final campaign
report. A/A and A/C each finished their ten predeclared conditions: five complete
cycles and five failed physical pre-seats. That is **five valid manipulation
trials per design**, not ten. Their protocol yield including setup is 50%; a
robot-reliability estimate and ranking remain withheld. B/A and B/C were still
running at that snapshot. Failed setup cases remain preserved, not relabeled as
robot manipulation failures or discarded from the protocol accounting.

The original frozen v1 campaign remains unchanged. Working harness v2 adds:

- Explicit initial positions for existing driven prismatic joints, before
  `World.reset()`. Open jaws now start open, without changing limits, contact
  geometry or runtime joint/body positions.
- At most two 0.15 mm physical pre-seat advances when measured depth/alignment
  place the hook on the socket-lip edge. The existing force-limited hand is used
  only for setup and disabled before the robot task; no latch pose is commanded.
- A saved-CoreXZ controller signature adapter. C/A v001 predates the optional
  transverse-force-limit argument. The adapter preserves its no-argument call
  and rejects unsupported non-null force limits rather than silently dropping
  them. Campaign001's C/A control failed on this harness API mismatch, not on a
  completed physical manipulation attempt.

`benchmark_aa_fixture002` reruns the exact seed/index 002 conditions and frozen
A/A v001 environment. One nudge physically raises the hook from 4.8047 mm to
5.4322 mm above the socket datum and engages it. After hand removal the robot
completes the cycle in 21.1583 s, with maximum cable joint gap 0.12389 mm.
Startup robot self-contact pairs decrease from six to zero; the largest startup
pair impulse/dt estimate decreases from 1294.34 N to 4.45 N. These are
uncalibrated estimates, not safe-load certification. Both fixture changes were
applied together, so this does not isolate their causal effects individually.
The nominal `benchmark_aa_control002` also passes. The revised C/A control,
`benchmark_ca_control002`, passes in 21.5375 s with zero reported robot/rack or
robot self-contact pairs during the timed task and no contact-reporting errors.
Its maximum cable joint gap is 0.04717 mm. These nominal controls are not
randomized samples.

Reproduce the read-only revision comparison with a new output filename:

```sh
python3 rack_robotics/scripts/compare_benchmark_fixture.py \
  --before rack_robotics/experiments/benchmark-campaign001/AA/trial-002-attempt001 \
  --after rack_robotics/experiments/benchmark_aa_fixture002 \
  --output rack_robotics/experiments/benchmark-fixture-comparison002.json
```

`benchmark-fixture-comparison001.json` already preserves matching condition and
environment hashes, source differences, measured outcomes and startup contacts.
Do not pool v1/v2 trials as if they used the same fixture protocol. Final retained
plug tilt remains about 4.4°; physical hook retention is not a claim of precision
seating, electrical connectivity or manufacturer-calibrated behavior.

Working `evaluate_all.py` now adopts valid results left behind by an interrupted
parent after confirming the old process is not live, checking condition,
environment and frozen source hashes. It preserves failed results too and does
not invent an unavailable process exit code. Invalid evidence stops resume;
missing results create another preserved attempt. A frozen evaluator can use
`--project-root /workspace`. Existing campaign001's harness is not rewritten.
Local regression suite: **122 tests pass**; these are software checks, not extra
physical trials.

`benchmark-campaign002` now freezes this revised harness and uses the same
`benchmark-plan001` condition files and eight saved environment identities.
It runs two fresh Isaac sessions at a time under
`/workspace/artifacts/logs/p2-benchmark-campaign002.log`. Each design again needs
its own successful control before its ten randomized conditions. Do not relaunch
this existing directory, change its frozen harness or pool it with campaign001.
Inspect live evaluator/child PIDs and use the consistent snapshot exporter for
downloads. More than ten conditions will still be needed if any fail to establish
an admissible initial state; best candidates additionally need at least twenty
valid trials and the remaining mechanical/force/clearance audits.

## Recorded-motion mechanical screen and benchmark checkpoint

The [mechanical screening report](research/mechanical_screening.md) now records
cooked model masses/COMs and sampled motion envelopes for A/A, B/A, C/A, A/B,
A/C and B/C.
The B/A parked assembly extends **248 mm** beyond the rack's left edge, and its
sampled full-cycle envelope is approximately **764 mm wide**. Its smaller total
modeled mass does not eliminate mounting leverage: the calculated gravity moment
at the mount reference reaches 12.06 N·m, versus 8.59 N·m for A/A. These are
quasi-static model calculations, not bracket/bolt/rack ratings or collision
clearance certificates. A/C and B/C also completed their property queries and
recorded-trajectory screens; C/C, C/B and B/B remain to be screened.

`benchmark-summary006.json` preserves the terminal campaign001 evidence. The
evaluator has exited; it did not satisfy the trial requirement, and its C/A
randomized cases were skipped after the documented controller-API control
failure. Do not resume that frozen, superseded protocol merely to rerun its
known failing control. Every produced failure remains preserved.

`benchmark-summary007.json` is the newer campaign002 snapshot. A/A and A/C each
have ten admissible randomized starts and ten full-cycle successes, two at each
of ports 1, 4, 8, 12 and 16. Their 95% Wilson intervals remain approximately
72–100%; this is not a universal or hardware reliability claim. Campaign002
continues with the other designs and must remain unchanged while running.

A/A's campaign002 nominal control was rendered as
`AA/control-attempt001/replay_wide001` (647 recorded samples, 1080p/30 fps).
The 21.5667 s MP4 passed Mac Chrome decode/play/seek. Frame 180 visibly crops
the rack bottom; the candidate is explicitly marked
diagnostic, not accepted as the final wide view. The working wide-camera preset
now lowers the target and increases distance; `replay_wide002_probe` is the
separate one-frame composition check and must not be counted as a full video.
The corrected frame includes the full rack and feet with margin. Its composition
review is accepted for a new full-cycle render, now running as `replay_wide002`;
the completed video still needs temporal inspection and Mac playback checks.
The snapshot exporter excludes derived render subdirectories, so a video can be
rendered beside a finished trial without copying partially written frame files
into physics-evidence snapshots. Download completed renders separately.

Local software regression suite: **128 tests pass**. Rack ratings, dense-cable
clearance, dynamic/tension loads, final ranking, ≥20-trial finalists, the full
camera/video set, showcase and comparison gallery remain unfinished.

`benchmark-plan002` predeclares ten additional conditions with seed **20261018**.
`benchmark-campaign003` runs them on **A/A and A/C** as provisional finalists,
with its own nominal controls and log
`/workspace/artifacts/logs/p2-benchmark-campaign003.log`. Both already have ten
valid completed trials and compact sampled rack envelopes; this selection is
not the final hardware ranking. Other designs can still merit twenty-trial
extensions after their initial campaigns and mechanical reviews.

The working harness matched every frozen campaign002 source hash before this
extension launched. Verify campaign003's frozen hashes too before pooling.
Pool only identical protocol/environment identities and distinct `(seed,index)`
conditions; nominal controls are excluded. Ten additional declared conditions
do not guarantee twenty admissible starts if any setup fails. Never combine the
superseded campaign001 fixture protocol into those reliability counts.
C/C and C/B cooked-property queries have also been launched; B/B's failed saved
environment still needs its own mechanical screen.

## Twenty-trial checkpoint and complete mechanical-screen matrix

`benchmark-summary010.json` verifies the terminal campaign003; its evaluator
exited successfully. `benchmark-summary011.json` is a later campaign002 snapshot.
`benchmark-pooled003.json` combines those snapshots only after checking all
frozen source hashes, environment identities and distinct `(seed,index)` cases.
The earlier campaign001 remains excluded.

| Configuration | Admissible randomized trials finished | Complete cycles | Mean successful cycle |
|---|---:|---:|---:|
| A/A v001 | 20 / 20 declared | 20 | 21.87 s |
| A/C v002 | 20 / 20 declared | 20 | 31.05 s |
| B/A v002 | 10 / 10 declared | 10 | 21.58 s |
| B/C v003 | 10 / 10 declared | 10 | 28.20 s |
| C/A v001 | 10 / 10 declared | 10 | 22.38 s |
| C/C v001 | 10 / 10 declared | 6 | 28.84 s |
| A/B v003 | 4 / 10 declared at snapshot | 3 | Partial campaign |
| C/B v001 | Not finished at snapshot | — | Partial campaign |

A/A and A/C each have four trials at ports 1, 4, 8, 12 and 16. Their descriptive
95% Wilson intervals are approximately **83.9–100%**, not hardware reliability
guarantees. C/C's four failures occur at `align_datum`; they are valid failed
manipulation trials, not excluded fixture failures. Its trial-000 recovered from
a `seat_and_latch` timeout and completed the actual physical cycle. Reported
success includes the pre-existing retained-state hysteresis, not proof of final
manufacturer seating tolerances or electrical connectivity.

`pool_benchmarks.py` refuses changed protocols/environments, duplicate random
conditions, control contamination and invalid evidence. It withholds aggregate
rates for incomplete declared campaigns. Reproduce with a new output filename:

```sh
python3 rack_robotics/scripts/pool_benchmarks.py \
  --campaign rack_robotics/experiments/benchmark-campaign002 \
  --campaign rack_robotics/experiments/benchmark-campaign003 \
  --output rack_robotics/experiments/benchmark-pooled-next.json
```

C/A's smaller modeled moving mass also merits twenty-trial evaluation despite
its greater rear overhang. `benchmark-campaign004` extends C/A using plan002 and
an exact copy of campaign002's verified frozen harness (`--harness-from`), not
the now-changed working analysis code. Log:
`/workspace/artifacts/logs/p2-benchmark-campaign004.log`. Do not relaunch while its
evaluator/children are alive. A frozen evaluator can resume with `--project-root`
if needed after checking actual process liveness; omit `--harness-from` on resume.

All nine designs now have cooked mass/COM/inertia queries and recorded-motion
mechanical screens; see [mechanical_screening.md](research/mechanical_screening.md).
B/B v006 is explicitly a failed partial trajectory, with a modeled peak gravity
moment of 15.60 N·m at the mount reference—not a rating or safe-load verdict.
Its original package and A/B v009 were each reopened in fresh Isaac sessions;
both reproduced their grasp failures. Each passed 58 package hashes, 21 USD-layer
and 150 asset dependency checks with no unresolved dependencies. Evidence:
`experiments/b_b_reload_v006/asset_validation.json` and
`experiments/a_b_reload_v009/asset_validation.json`. This verifies reusable failed
environments, not successful manipulation.

A/A `replay_wide002` completed 647 frames at 1920×1080/30 fps and passed Mac Chrome
decode/play/seek. Its sampled frames include the full rack. The renderer now
checks recorded timing, body count, finite/unit poses, world translation **and
rotation**, and preserves source/video hashes. It supports PathTracing and
explicit camera/resolution overrides. These checks apply to new renders; they
do not retroactively add metadata to old videos.

Camera probes `rear/macro/side003_probe` remain diagnostics: rails/actuator
obstructed the view. Revised `004_probe` compositions were inspected with
PathTracing requested; see the renderer-override correction below. Rear and side
full-cycle candidates were rendered, while the macro is checked additionally
during latch depression and separation. A probe
is not a full-cycle video. None of this completes the required all-design video
set, multi-angle edits, showcase or gallery. Local software checks now total
150 tests; mechanical ratings, dense-cable clearance, carriers/brakes, coverage,
final ranking and remaining preservation/visual delivery gates remain open.

### Render audit follow-up

The saved baseline contains a per-product `omni:rtx:rendermode` opinion set to
`RealTimePathTracing`. An application launch option alone does not establish
which mode the loaded viewport uses. Thus the `renderer` field in pre-006
manifests records the **requested** mode, not verified offline path tracing.
Preserved A/A wide002/rear004 frames also show apparent ghosting near the parked
bridge; they are not accepted as final temporal-quality deliveries. Rear004 did
pass Mac playback and 29,115 position/rotation checks against its recorded input.

The newer renderer explicitly overrides the actual viewport's USD render
product in the derived replay layer, disables temporal denoising/motion blur,
and records both previous and resolved settings. The immutable baseline and
physics trajectory remain unchanged. Property names/types were checked against
the installed RTX render-settings schema; unit tests verify the weaker source
layer stays unchanged. `replay_rear006_temporal_probe` checks the final 27 samples
under that profile before another full render.

Macro004's separation probe cropped the connector. New `macro_camera.py` moves
only the inspection camera back to fit conservative socket/plug envelopes;
macro005 probes at samples 200 (pressed latch) and 310 (separated) both keep the
subject visible. The full motion still requires temporal review. C/A campaign004's
copied harness has been checked against campaign002 both in its manifest and
actual source files: identical. B/B v006 and A/B v009 fresh failed reloads and
dependency validations are now also downloaded locally.

## Completed initial randomized comparison

Campaign002 and the C/A extension campaign004 have now both terminated; their
parent PIDs are absent and logs report completion. Summaries012–013 verify the
terminal snapshots. `benchmark-pooled004.json` is the current complete comparison:

| Design | Complete cycles / valid randomized trials | Descriptive 95% Wilson interval | Mean successful cycle |
|---|---:|---:|---:|
| A/A v001 | 20 / 20 | 83.9–100% | 21.87 s |
| A/C v002 | 20 / 20 | 83.9–100% | 31.05 s |
| C/A v001 | 19 / 20 | 76.4–99.1% | 23.35 s |
| B/A v002 | 10 / 10 | 72.2–100% | 21.58 s |
| B/C v003 | 10 / 10 | 72.2–100% | 28.20 s |
| C/C v001 | 6 / 10 | 31.3–83.2% | 28.84 s |
| A/B v003 | 6 / 10 | 31.3–83.2% | 32.08 s |
| C/B v001 | 2 / 10 | 5.7–51.0% | 23.08 s |

All **110** randomized starts were admissible. Eleven separate nominal controls
are excluded from these counts. Conditions are paired across designs within
each seed set; only A/A, A/C and C/A received the additional ten cases. Failed
manipulations are included, not replaced with successful retries. C/A's extra
failure is a `release_latch` timeout at port12: the measured hook did not clear,
so the controller correctly refused extraction. Completion-time means include
successful trials only and must not be read as failure-inclusive throughput.

These results meet the numerical trial-count requirement for the eight designs
that passed basic feasibility, including twenty trials for three promising
configurations. They do **not** complete the rack-load/buildability/crowded-cable
audit, final ranking, calibrated force/tension evidence or visual deliverables.
B/B remains a preserved failed-feasibility design, not a missing successful
benchmark entry. A/A is a strong provisional choice, but no final hardware
recommendation is declared from these simulation rates alone.

Renderer006 successfully resolved the actual viewport mode to PathTracing, but
the optional OptiX denoiser then reported missing `/usr/share/nvidia/nvoptix.bin`
weights (also absent at the checked host locations). Its artifacts are diagnostic,
not accepted final footage. Renderer007 tests the same offline mode at256 samples
with denoising disabled; no VM/container rebuild or baseline change is needed.
