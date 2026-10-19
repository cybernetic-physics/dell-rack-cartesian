# Matched release challenge001 — predeclared follow-up

2026-10-17. This is a new experiment, not a revised verdict for physical-controls001.
That campaign's five nominal and five unpressed-pull tests pass; its B/A and
C/A open-transport displacement gates fail after the plug falls away, and its
A/C and B/C open-transport challenges stop at insufficient aperture. Preserve
all four failed diagnostics and their frozen protocol without reruns.

## Question and intervention

For each exact current saved design (AA016, BA014, CA021, AC005, BC004), compare
two fresh-session cases: `released_hold` and `released_transport`. Normal
controller/grasp/latch actuation and axial extraction are unchanged. At the
ordinary `separate` transition, open the jaws and retract the latch tongue.
Hold the tool for2 s, then either hold its measured location or request40 mm
additional outward motion over1.5 s plus0.5 s hold. This longer opening interval
is motivated by the incomplete C-tool aperture in campaign001, not by prior
knowledge of these follow-up outcomes. It does not promise that opening succeeds.

Unlike campaign001, insufficient measured aperture does not abort the motion
request. Deliver the bounded actuator request anyway, and retain a failed
`jaws_physically_open` verdict. This tests an open *command*; it must never be
described as an ineffective grasp if contact/form-fit still supports the plug.
No lateral datum-clearing motion, collider removal, actuator-force increase,
pose setting, grasp joint or baseline helper is introduced. The insertion-axis
target remains within the existing0.55 m workspace, at its original force cap.

## Predeclared gates and measurements

- Fresh nominal conditions,480 Hz full normal/friction connector contact and
  measured-state tracing; all helpers inactive, finite contiguous samples,
  intact topology/carriers and no contact-report exceptions.
- Both references bind to the preceding physics sample. Initial extraction
  must exceed35 mm. Opening lasts2 s; challenge lasts2 s (one/two timestep
  rounding allowance). Record and maintain the actual open jaw-drive targets
  and zero latch target through opening and challenge.
- Transport tool must advance at least35 mm; hold tool must remain within1 mm
  of its reference. Aperture must remain at least13 mm during challenge and
  housing must stay at least25 mm clear of the socket.
- A successfully released housing must be at least20 mm from the TCP for the
  entire challenge, with no reported direct robot–housing/latch contact rows.
  These are conservative release gates, not strength or safety thresholds.
- Compare every pre-intervention sample, including physical state, commands
  and contact records, for exact equality across the matched pair. Challenge
  timestamps/counts must align. Report maximum3D housing-position difference
  across the pair. A difference no greater than1 mm supports no measurable
  transport effect within this bounded matched experiment. A mismatch is
  counterevidence/inconclusive matching, not permission to delete a trial.

Motion in world Y alone is not a grasp proxy: free-fall, bounce and cable motion
can advance a released connector. Pairwise comparisons and direct contact/
separation evidence distinguish those cases; cable/robot aggregate contact
reports remain available for interpretation. Equality within1 mm is not proof
of zero interaction or a general guarantee for other orientations/routing.

## Execution and preservation

Predeclare all10 cases, two workers, no automatic retries/timeouts. Freeze
protocol, runner, common controller, measurement code, condition, calibration
and environment identities before launch. Each result keeps ordinary task
`passed:false` / `full_cycle_attempted:false`; a separate diagnostic records
the gates above. Normal successful controls are the separately verified five
campaign001 cases, not silently re-counted reliability samples.

The runner supplies its diagnostic exit code to SimulationApp.close before
Kit fast shutdown. All failures remain failures even when the experiment is
successfully completed. Recompute terminal sources/traces and matched
comparisons on both VM and Mac. Do not modify existing environment packages,
benchmark scores/denominators, original GUI, or physical-controls001.
