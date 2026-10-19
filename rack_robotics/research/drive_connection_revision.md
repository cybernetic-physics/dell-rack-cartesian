# Drive-connection revision — development evidence

The first benchmarked assemblies use dimensioned guide/drive envelopes but omit
several connections. They remain immutable. `hardware_detail.py` adds a new,
explicitly identified revision before physics initialization; it never changes
the connector, latch, target sockets, controller commands or runtime poses.
Use `run_reference.py --hardware-detail --output NEW_DIRECTORY` to test it.

## Geometry and mass changes

- A's two lift motors are moved onto the existing screw axes. Raised mounting
  plates, upright extensions, couplers, bearing supports, bridge-mounted lead
  nuts and brackets supply the previously missing connection geometry.
- A's traverse motor is made coaxial with its screw, with a motor plate,
  coupler, bearing supports and a carriage-mounted nut/bracket.
- A/C receive two transverse bearing blocks at50 mm center spacing and a
  backing plate. The transverse rail is520 mm long:420 mm travel plus the
 95.4 mm combined block envelope requires at least515.4 mm of rail.
- The common depth slide receives two MGN12H-envelope blocks and an adapter
  plate. Its rails grow from160 to180 mm and shift forward15 mm. A125 mm stroke
  plus45.4 mm block length does not fit fully on the original160 mm rails.
- The depth screw receives a nut, rear motor plate/coupler and a front bearing
  hanger. The hanger leaves an open channel for the fingers and latch tongue.

All lengths are custom design dimensions, not a newly claimed commercial
assembly. The MGN12H envelope and54 g/block mass are from the previously reviewed
HIWIN catalog in `cartesian_robots.md`. Other new masses are additive estimates
from authored volume and2700/7850 kg/m³ aluminum/steel density. The per-attempt
`hardware_detail.json` records every part, parent and mass contribution. These
are not weighed BOM totals. Existing lumped body masses remain estimates.

New solid brackets/plates use collision geometry and the baseline50 µm contact
offset. Clearance openings are real openings made from separate solid pieces.
Annular bearing/nut/coupler meshes have visible bores, but are non-colliding
visual proxies: existing prismatic constraints model the guide/thread motion.
No shaft-rotation, bearing-race or screw-thread contact simulation is claimed.
Neither motor torque-speed curves nor fastener/rack strength are certified.
Cable carriers and powered-off brakes still require implementation/evaluation.

## Preserved mechanical failures

| Attempt / saved version | Measured failure | Correction tested next |
|---|---|---|
| A/A hardware001 → v002; C/A hardware001 → v002 | Depth blocks/adapter intersect bridge; traverse locked during approach | Shift blocks/adapter forward and retain full guide engagement |
| A/A hardware002 → v003 | Front bearing plate physically blocks upper fingertips during alignment | Replace solid front plate with an overhead bearing hanger |
| C/A hardware002 → v003 | Traverse block contacts fixed vertical guide | Move block/backing plate forward of fixed-guide envelope |
| A/A hardware003 → v004 | Wide backing plate intersects upper lift stop | Reduce backing-plate height from40 to28 mm, retaining bearing support |

The very large impulse/dt figures in interpenetrating attempts are solver
responses to invalid initial geometry, **not physical load ratings**. Every
failed scene is retained and separately reloaded, not sanitized by suppressing
contacts. `reload-campaign002` reproduced the first four failures with matching
package/dependency checks. Later versions have their own reload evidence.

C/A hardware003 (`drive_connections_v3`, saved v004) completed a full physical
cycle in23.4458 s with one seating nudge, no recovery, cable gap0.052714 mm and
no reported robot–robot contact pair in the timed cycle. Added modeled mass is
0.275807 kg on the carriage and0.205971 kg on the tool mount. This is one
feasibility pass, not randomized reliability. Its fresh saved-scene reload is
tracked separately in `reload-campaign003`.

Current source revision is `drive_connections_v4`. A/A hardware004 (saved v005)
and B/A hardware001 (saved v003) each completed the physical cycle in21.5375 s
without a recovery or seating nudge. `reload-campaign004` independently loaded
both saved scenes, repeated successful cycles and passed package/dependency
checks. `reload-campaign003` likewise verified C/A v004's success and A/A v004's
preserved failure. All eight new successful/failed versions are included in
`preservation-audit003.json`:34 total versions load,33 reproduce their declared
outcomes; the historical B/A v001 exception remains explicit.

`benchmark-plan003` selects A/A v005, B/A v003 and C/A v004 with20 new randomized
conditions each (seed20261019). `benchmark-campaign005` uses the exact original
frozen test harness, but these changed environment identities form a separate
cohort, not an extension of the original110 trials. The campaign is now terminal;
`benchmark-summary014.json` verifies all60 randomized trials and three passing
nominal controls, with no fixture failures or evidence-hash errors:

| Saved assembly | Complete cycles | Descriptive95% Wilson interval | Mean successful cycle |
|---|---:|---:|---:|
| A/A v005 |20/20|83.89–100%|23.76375 s|
| B/A v003 |20/20|83.89–100%|21.95708 s|
| C/A v004 |19/20|76.39–99.11%|22.15351 s|

Each design has four randomized conditions at each of ports01/04/08/12/16.
C/A trial016 at port08 failed latch release after two recoveries: the measured
hook remained at4.80163 mm and never satisfied clearance. It did not unplug;
the failure is retained in the denominator. These are simulation protocol
results, not hardware reliability or calibrated safe-force claims. None of
these three assemblies includes the subsequently developed service carriers.

Do not transfer any old version's benchmark
rate, swept envelope or cooked inertia measurement onto these changed models.
Seven local geometry tests check new part ownership/mass, bore openings,
guide engagement and the three measured clearance regressions. They are not
a substitute for full-rack collision or load tests.
