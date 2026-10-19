# Occupied-port clearance screen

## Current versions — screen002, 2026-10-17

`occupied-summary002.json` binds the terminal 25-case `occupied-screen002`
experiment to A/A v016, B/A v014, C/A v021, A/C v005 and B/C v004. The same
five target-port conditions and restrained-neighbor fixture are used for each.

| Current design | Complete and clearance-passing / planned cases | Failed fixture starts | Timed robot–neighbor contact cases |
|---|---:|---:|---:|
| A/A v016 | 4 / 5 | 1 | 0 |
| B/A v014 | 4 / 5 | 1 | 0 |
| C/A v021 | 4 / 5 | 1 | 0 |
| A/C v005 | 4 / 5 | 1 | 0 |
| B/C v004 | 3 / 5 | 1 | 0 |

All five port8 cases fail fixture pre-seating before the timed manipulation;
these are retained failed starts, not evidence of contact-free execution.
B/C additionally fails seating at port16. The 20 timed cases report no
robot–neighbor or target–neighbor contacts. This finite restrained-fixture
screen does not establish arbitrary dense cable routing, neighbor retention
under load or safe cable tension. Current-version comparison005 regenerates
this summary from the original evidence rather than transferring old results.

## Historical screen001 — earlier saved versions

Terminal evidence: `experiments/occupied-screen001`, verified by
`scripts/summarize_occupied_screen.py` into `occupied-summary001.json`.
All40 declared cases finished; all had a stable timed neighbor fixture.
The input source, frozen conditions, saved environment identities and result
hashes were checked. This screen is separate from the110 randomized trials.

## Fixture and acceptance

The five paired conditions target ports4,8,1,16,12, with each available immediate
neighbor occupied. Neighbor housings are restrained to the rack; each retains
its passive latch and36 dynamic cable capsules/D6 joints. The target connector,
latch and cable are unchanged. This is an obstacle/clearance screen, **not a
neighbor retention or full-density bundled-cable test**.

Clearance acceptance requires a successful complete task, a stable timed
fixture, no contact-reporting errors and zero positive robot–neighbor contact
pair impulses. No positive target plug/latch/cable–neighbor pair was reported
in these40 cases; that separate check does not redefine the robot-only gate.

| Original saved design | Task passes | Clearance passes | Cases with robot–neighbor contact |
|---|---:|---:|---:|
| A/A v001 |5/5|5/5|0|
| A/C v002 |5/5|5/5|0|
| B/A v002 |5/5|5/5|0|
| B/C v003 |4/5|4/5|0|
| C/A v001 |4/5|4/5|0|
| C/C v001 |2/5|2/5|0|
| A/B v003 |4/5|0/5|4|
| C/B v001 |2/5|0/5|4|

The RG2 base/proximal finger links touched neighboring cable links04/05.
Reported pair impulse/dt peaks are only about0.02–0.04 N: these are real
reported clearance contacts, **not evidence of damaging force**. A/B completed
four manipulations while making those contacts. C/B completed two while making
contacts; two additional grasp failures also touched neighbors. Thus task
success alone must not certify rack clearance.

B/C's fifth condition failed alignment. C/A's port1 case failed latch release
without clearing the socket lip, so extraction was withheld. C/C failed three
tasks. Read each preserved result/error and contact list rather than assuming
that every failed task was caused by a neighboring cable.

A/B's port16 failure reports only robot self-contact: RG2 base geometry touches
the left fixed upright, with a10.48 N peak pair impulse/dt estimate. The tool
misses its approach target by about109 mm. The sparse-row benchmark also has
0/2 complete cycles at port16 for both A/B and C/B. This is a physical workspace
obstruction, not evidence that the nominal prismatic stroke alone guarantees
access to every port. It reinforces the need for a swept-volume coverage audit.

No rates from this five-case diagnostic establish hardware reliability.
The added-drive-connection A/A v005, B/A v003 and C/A v004 have different
envelopes/masses and have **not** inherited these clearance passes.
