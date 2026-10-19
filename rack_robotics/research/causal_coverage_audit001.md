# Causal-control coverage audit — remaining physical challenges

2026-10-17. This audit distinguishes existing evidence from the stronger
controls explicitly requested by `rj45_mechanisms.md`. It does not change any
benchmark outcome, saved environment, acceptance record or historical score.

## Evidence inspected

- `rj45_mechanisms.md`, SHA256
  `06f1bbf875f3a48a09646f8ade3bfa4b98fb911d9d01af40e392497fe511cfc9`:
  final section requires retained pulling before release, ineffective latch
  actuation, ineffective grasp transport and retention after tool opening.
- `../../artifacts/latch-probe-2.json`, SHA256
  `acc99ed266b656e2360e2de0ee4534ab7a8b646f759a973ac46ad8803966bd79`:
  all13 reported checks pass. The baseline includes5 N retained pulling,
  physical tab depression/extraction, return/re-engagement and a lip-disabled
  negative control. This turn inspected the report, not a new physical run or
  an independent recomputation of all baseline trace samples.
- `../experiments/actuator-controls001/verification_mac001.json`, SHA256
  `cca22ede301368e33df37303348819e842b02c38177aad01deb70903262b7b75`:
  all15 current-tool diagnostic cases pass their separate gates. The preceding
  campaign audit recomputed all177,063 samples on VM and Mac. Its scope is
  explicitly normal-controller interlocks, not imposed physical challenges.
- `actuator_interlocks.md`, current common campaign runner and isolated
  `probe_rack_tool.py`: command suppression preserves observed state and
  bounds retries; the disconnected pinion probe establishes empty-tool
  transmission, not connector transport causality.

## Coverage and next experiment

| Required distinction | What existing evidence establishes | Remaining scope |
|---|---|---|
| Retention before latch release | Baseline tooth/lip resists5 N; current-tool controller refuses withdrawal with a retracted latch actuator | Impose a bounded withdrawal command through each current robot/tool while grasped and unpressed; verify actual applied effort and retention, not simply absence of a motion request |
| Disabled latch does not unlock | All five current systems exhaust bounded release retries, hook stays blocked and plug retained | Existing interlock evidence covers the normal task; pair it with the physical pull challenge above |
| Ineffective grasp does not transport | All five normal controllers reject open aperture and stop before withdrawal | Physically clear the latch with real tooling, keep jaws open, then command bounded tool withdrawal; observe whether the housing is transported, without a controller interlock preventing the challenge |
| Opening after seating leaves retention | Full nominal and continuous trajectories, plus native macro and full-video review, show seated connector after the tool retracts | Preserve existing evidence; do not count repeated video views as additional physical trials |

The next campaign must use the five exact saved working packages (AA v016,
BA v014, CA v021, AC v005, BC v004), fresh sessions, frozen source/conditions,
actual joint/effort commands and explicit diagnostic-only outcomes. It must
not teleport the housing, alter connector/latch/socket colliders, add a grasp
or retention joint, or enable baseline hand/clip-press helpers. Preserve the
normal successful control alongside each challenged design. Record the
delivered commands, measured tool/housing/latch states and relevant contact
evidence at physics-step resolution. A challenge that was never delivered is
inconclusive, not a passing negative control.

Specify force/travel/time limits and gates before running. Keep failures and
unexpected physical transport, rather than changing the requested gate after
seeing the result. A bounded simulation challenge is not a connector strength
rating, hardware safety certification or randomized reliability sample.

No physical challenge campaign was launched by this audit. This identifies
concrete remaining validation work; it does not mark PLAN_p2 complete.

## Subsequent closure evidence — 2026-10-17

The preceding text is the pre-experiment audit. Subsequent campaigns are now
terminal and independently recomputed: [physical-controls001](physical_challenge_results001.md)
and [matched-release001](matched_release_results001.md). All five retained-pull
cases pass under actual opposed loading; disabled-latch interlocks were already
verified. Matched open-command challenges are delivered for all five designs.
AA/BA/CA show no measurable transport effect, while AC/BC refute the assumption
that jaw opening alone disengages the connector: their guide surfaces still
carry it. That counterexample is retained, not mislabeled as an ineffective
grasp or erased through a post-hoc gate change. Normal after-seating release
remains separately evidenced by the full and continuous cycles.

The remaining work is final evidence/document/gallery integration and complete
PLAN-level audit, not rerunning these controls until every diagnostic is green.
