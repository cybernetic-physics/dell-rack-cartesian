# Physical challenge campaign001 — terminal results

2026-10-17. All15 cases are terminal. All127,722 raw480 Hz samples, source
hashes, reference states and actual process records reverify on VM and Mac.
The campaign is **not an overall pass**: five nominal and five unpressed-pull
diagnostics pass; only A/A passes the original open-transport gates. B/A and
C/A fail the axial displacement proxy, while A/C and B/C stop before transport
because their measured aperture is insufficient. No failed case was replaced.

The byte-identical `verification_vm001.json` / `verification_mac001.json` in
`../experiments/physical-controls001/` have SHA256
`05276c7f83099cc5560741957faa122638991331963fe2cb52ed5309f30b9a96`.
Their verifier is preserved as `verification_source001.py`, SHA256
`884e96c08677403dcdb7d35a640c8b6a8d08a7ee691cc68f75ee07b26abca92d`.

The [predeclared protocol](physical_challenge_protocol001.md) is frozen in
`../experiments/physical-controls001/protocol.md`. Campaign manifest SHA256:

`38557a3c83887a484b5ddb2f5ff9c38b105cebfb5dcf92099685ecc8cff26bfc`

| A/A case | Ordinary full-cycle task | Separate diagnostic |480 Hz samples | Main observation |
|---|---|---|---:|---|
| Nominal | PASS,32.922917 s | PASS |15,803| All988 recorded30 Hz frames/126 bodies exactly match the earlier first continuous cycle |
| Unpressed pull | Not a full-cycle attempt | PASS |3,699|1.502083 s challenge; maximum absolute axial drift0.474155 mm;1.433333 s of both positive tool loading and opposing socket contact above their declared thresholds |
| Open transport after extraction | Not a full-cycle attempt | PASS |5,813|2.002083 s transport challenge; tool moves39.9915 mm; maximum signed housing forward advance−0.0335 mm; final relative axial shortfall56.7961 mm |

All25,315 raw samples reverify on the Mac with the frozen-source hashes and
recorded references. Both challenged cases deliberately retain `passed:false`
and `full_cycle_attempted:false`; the positive result is only
`physical_challenge.passed`. No benchmark denominator or score changes.

During the A/A unpressed-pull interval, mean signed axial contact estimates
are+4.6776 N from the tool and−4.6871 N from the socket. Instantaneous step
estimates reach+10.6809/−10.8538 N despite the5 N insertion-drive cap. This is
why the cap must not be presented as a bound on all contact transients, a
material strength measurement or a hardware-safe load. The hook remains
blocked and latch command retracted; topology, carrier and contact-reporting
gates pass. No baseline hand/clip-press helper is active.

The open-tool case starts only after normal secure extraction. It permits
gravity/cable motion and observes whether the housing follows further tool
motion, with the socket already clear. It is not a claim about every possible
orientation, accidental contact or grasp failure.

## Bound terminal A/A results

- Nominal results SHA256:
  `6fdb27bcc8a7457093bdd91a187c349563a14d9db058af7d8ebc5d2752a9491a`;
  raw trace `f552d91f20bcba21dbcd201ca1b9deb4affdd996b05a6aa51fe2fc09e7cc679f`.
- Unpressed-pull results SHA256:
  `2c11fbf6ba41490a21fbfbd320ace3c7caff4e9b81304fefdfb01ff42cc5da42`;
  raw trace `e0a56314e4956237ed058f9989dd4b3057a074c07b7718c4ad57fe1d3f37a230`.
- Open-transport results SHA256:
  `c1c691e8b94ea62c8c7840d7cbf0d653e03bd2a24ea9f055c184552caf04d0a4`;
  raw trace `61a75e787f2a4f5ee041b801962e99c3514ad2da38eacaa71612aceb5a4892fe`.

## All five designs

| Design | Nominal cycle | Unpressed-pull maximum axial drift | Open-transport original diagnostic |
|---|---:|---:|---|
| AA v016 | PASS32.922917 s | PASS0.474155 mm | PASS |
| BA v014 | PASS32.922917 s | PASS0.467628 mm | FAIL: housing advances97.5012 mm; final relative axial shortfall−18.3578 mm |
| CA v021 | PASS21.516667 s | PASS0.544548 mm | FAIL: housing advances110.8429 mm; final relative axial shortfall−28.1358 mm |
| AC v005 | PASS37.625000 s | PASS0.507206 mm | FAIL: opening precondition; final aperture12.6852 mm, no transport challenge |
| BC v004 | PASS37.625000 s | PASS0.601977 mm | FAIL: opening precondition; final aperture12.7329 mm, no transport challenge |

Every nominal recorded trajectory exactly matches all frames of the earlier
continuous first cycle: AA988, BA988, CA646, AC1129 and BC1129 frames. These
are30 Hz recorded-body comparisons, not a claim of bitwise480 Hz trajectory
identity. Every pull case has at least1.429 s actual positive tool loading
and opposing socket contact, with blocked hook and retained depth. No nominal
or diagnostic case changes randomized reliability denominators or comparison005.

### Interpretation of failed open-transport gates

For AA/BA/CA, the connector falls substantially during the0.7 s opening wait.
At transport start the housing–TCP3D distances are1.2024/1.1832/1.1397 m;
minimum distances during transport are1.2055/1.1858/1.1415 m. Raw full-contact
traces have **zero direct tool–housing/latch rows** during that interval.
The aggregate contact reports also contain no robot–connector/latch/cable
pair for `challenge_transport`. These measurements support release and free
dynamics, rather than a maintained tool grasp. Forward world-Y drift is not
by itself proof that the tool carried the housing. Nevertheless the frozen
BA/CA axial gates failed and remain failed; this interpretation is post-hoc,
not a new passing verdict.

AC/BC are different: housing stays within about0.77 mm of the TCP and jaws
open only to12.7 mm, below the13 mm requirement. The protocol's interlock
therefore prevents the transport challenge. Neither this incomplete test nor
the earlier normal-controller interlock proves that an open C tool cannot
carry the connector. The fixed form-fit shoe also makes an open command
different from a demonstrated ineffective grasp.

The separately predeclared [matched-release follow-up](matched_release_protocol001.md)
compares holding versus moving after a2 s open command. It delivers the
bounded request even if aperture remains insufficient, keeps that condition
failed, and compares identical pre-intervention evidence and entire housing
trajectories. It does not change any campaign001 result or geometry.

### Process exit correction, not a physics correction

All15 original wrapper exits were0, including the four failed diagnostics.
The exact frozen runner SHA256 is
`77d4ca701af7ed07d0f2693a1afb92d857897666dc3db67e91702edb40bdf7e6`.
It called `app.close()` before computing/raising the diagnostic status.
Installed SimulationApp uses fast shutdown, which can terminate inside close.
Its supported `close(exit_code=...)` argument preserves failure status before
the native shutdown path. Installed implementation SHA256:
`6af5372bb0cdda6e665a30cd285ff724b3e5bd012dbdd4df458e0726173fc903`.

The working runner now computes the verdict before close and supplies its
exit code. Frozen runners/results/state remain unchanged. Verification accepts
zero-on-failure only for that exact known legacy runner, explicitly records
`legacy_fast_shutdown_zero_on_failed_diagnostic`, and retains diagnosticFAIL
and overallFAIL. Unknown runners, missing statuses and signal exits are not
accepted by this exception. The original reports are completed evidence of
failed gates, not software exit-code passes misrepresented as physics passes.
