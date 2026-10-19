# Open insertion stage — scoped correction, not complete robot clearance

The all-travel audit found that the original closed carriage plate overlapped
the tool adapter/bearing plate at retraction and that the bearing plate swept
through the front screw support. Joint collision filtering hid these pairs.
These are physical design errors, not grounds for weakening the audit.

`insertion_stage.py` replaces the closed plate with a dimensioned open frame,
raises the two insertion rails80 mm, spaces them60 mm apart, and uses200 mm
rail length. A90×48×9 mm moving bearing plate and two bolted risers attach the
original tool flange. The front support is205 mm forward of the fixed datum,
beyond the fully extended plate. The motor, screw, nut and bearing supports
are moved together. The TCP, gripper geometry, joint anchors,125 mm travel,
drive forces, controller and connector/latch remain unchanged.

The original fixed plate is replaced by actual collision-enabled frame
members, not merely hidden while its collision is disabled. Additive mass
changes include explicit aluminum/steel volumes; subtraction of the original
plate uses an aluminum volume proxy against its original lumped body mass.
This is still an estimate, not CAD-derived calibrated inertia or a strength
rating. The MGN12H blocks remain catalog envelopes with an abstracted raceway.

The new exact-box tests show no fixed-carriage/moving-tool box intersection
over the entire insertion interval for A/B/C. The stage tests include negative
controls using the original geometry, end-of-travel block support, unchanged
joints/connector, mass accounting and compatibility guards. This is not a
full-robot or rack pass. Other guide/beam/frame/stop/motor interference remains
in the broader sweep, and non-box collision/strength/fastener checks remain.

## Preserved development revisions

The first `*_a_insertion001` trials use `open_insertion_stage_v1`. All three
complete their full-rack RJ45 task at A/B480 Hz and C240 Hz. They are saved as
A/A v013, B/A v012 and C/A v012. A subsequent geometry-transform regression
caught a typeless USD motor-plate grouping prim: an authored translation did
not move its child boxes. Those first versions remain mechanically invalid
even where the physical task passes; their original evidence is unchanged.

`open_insertion_stage_v2` explicitly makes the group an Xform before shifting
it. A regression checks evaluated world bounds, not only the authored
attribute. Risers also provide1 mm nominal lateral clearance from the
specialized tool's backplate. The fresh `*_a_insertion002` runs test this
revision separately. All three are terminal passes: A/B21.5167 s at480 Hz,
C21.5375 s at240 Hz, no retries or seating nudges. Cable maximum gaps are
0.01809/0.01809/0.05271 mm, respectively. Neither startup nor task reports a
robot–robot contact above0.1 N. Saved A/A v014, B/A v013 and C/A v013 include
the evaluated geometry and broader failed box audits. Reload-campaign014
checks fresh-session execution; inspect its actual summary for completion.

The broader robot-only box sweep still flags52/26/16 potential overlaps among
2199/1594/1842 pairs for A/B/C. The insertion Carriage/ToolMount interface is
clear in these reports, but other frame/beam/guide/end-stop/motor interfaces
remain invalid or require bearing-envelope interpretation. No full-rack
buildability acceptance follows from the task passes.

The full-size RG2's94 mm crosshead and160 mm side drops need a larger opening.
`open_insertion_stage_v3_rg2` uses a116 mm frame/backplate and moves the lower
crossbar aft of the drops' swept volume. Precision/specialized tools retain
the v2 geometry; no tool or TCP is scaled. Unit tests include both RG2 mounts
over the complete stroke. New A/B and A/C tool-integration trials use separate
`a_b_insertion001` / `a_c_insertion001` outputs; their physical results remain
separate from the three precision-tool passes.

The trials deliberately isolate this stage correction without the old carrier
brackets, which do not fit the new cross-section. Both API and CLI reject
combining those old brackets with the revised stage. This is an intermediate
integration step: compatible passive carriers, every-tool verification,
whole-robot travel/rack clearance and updated randomized trials are still
required for the final assemblies. Brakes are installed but released during
these powered task trials; no new power-loss acceptance is implied.

Follow-up: [CoreXZ guide/frame revision](corexz_guide_frame.md) corrects C's
remaining supported robot-box intersections and defines a separately gated
compatible carrier route. A/B whole-robot geometry still needs correction.
The A/RG2 open-stage attempt fails measured grasp aperture (15.673 mm), is
preserved as A/B v010, and reproduces that failure in reload-campaign015.
The A/specialized-tool build hits a native allocator crash at startup, before
any task result. Its exact scene/source/log and startup-failure record remain
under `a_c_insertion001`; `a_c_insertion_reload001` separately investigates
that saved scene. Do not classify the native crash as a measured grasp failure.
That saved-scene run and the subsequent fresh `a_c_insertion002` build both
complete37.6625 s with one insertion recovery and one seating nudge. Fresh
build A/C v003 passes reload018. The original native crash remains unexplained.

Example fresh trial (use a new output directory):

```bash
/isaac-sim/python.sh -u rack_robotics/scripts/run_reference.py \
  --robot A --gripper A --physics-hz 480 --hardware-detail \
  --open-insertion-stage --motor-brakes --output NEW_DIRECTORY --allow-root
```

Saved scenes load their authored geometry without rebuilding it. Packaging
includes the insertion revision/report, startup joint states, and broader
box-sweep failures separately from the manipulation status.
