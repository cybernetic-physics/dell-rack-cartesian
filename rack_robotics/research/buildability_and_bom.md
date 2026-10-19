# Current assemblies: model inventory, buildability and cost

Checked 2026-10-17. This report concerns A/A v016, B/A v014, C/A v021,
A/C v005 and B/C v004, not the lighter early prototypes. These five designs
complete nominal powered manipulation and independently reload. This is a
simulation design comparison, **not a fabrication-ready purchase list**.

## Inventory tied to the saved geometry

`experiments/hardware-inventory-{aa,ba,ca,ac,bc}001/` contains `inventory.json`
and `components.csv`. Each record binds the environment manifest, verified
cooked-property query and analysis source by SHA-256. Composite guide-block
solids and carrier-link solids count as one component each. Dimensions are
body-aligned bounds; holes, threads, tolerances and bearings are not inferred.

| Model component | A/A and A/C | B/A and B/C | C/A |
|---|---:|---:|---:|
| Axis motor envelopes, excluding tool actuators | 4 | 4 | 3 |
| Modeled brake packages | 2 | 1 | 2 |
| Linear rails / guide blocks | 5 / 6 | 6 / 10 | 5 / 6 |
| Total modeled rail length | 2.760 m | 2.900 m | 2.760 m |
| Screw shafts | 4 | 4 | 1 |
| Passive service-carrier links | 81 | 97 | 81 |
| Rack-clamp solids | 4 | 2 | 4 |
| Fastener markers, **not complete fastener BOM** | 34 | 54 | 30 |

Additional custom/tool geometry records are 146/169/114/161/184 for
AA/BA/CA/AC/BC respectively. These records are not independent purchase parts:
the CSV preserves them for inspection instead of treating them as free.

| Architecture | Useful modeled travel | Rail lengths | Screw-shaft envelopes |
|---|---|---|---|
| A, dual-supported screw gantry | X 420, Z 700, insertion Y 125 mm | 2×920, 1×520, 2×200 mm | 2×890 and 1×498 mm at Ø8; insertion 221 mm at Ø6 |
| B, independent nested booms | 2×200 mm horizontal extensions, Z 700, Y 125 mm | 2×940, 2×310, 2×200 mm | Lift 946 and 2×288 mm at Ø8; insertion 221 mm at Ø6 |
| C, coupled CoreXZ | X 420, Z 700, Y 125 mm | Same as A | Insertion only: 221 mm at Ø6 |

Rail cross-sections are 12×8 mm. Lengths include non-travel material; do not
order a 420 mm rail merely because X travel is 420 mm. The model uses guide
envelopes based on [HIWIN miniature-guide research](cartesian_robots.md),
not catalog assemblies verified for these custom screws and mounting holes.
Actual rail cutting, hole pitch, end machining, lead/nut selection and
matching bearing preload remain engineering choices with unknown cost.

## Mechanical integration and assembly assessment

**A — straightforward independent-axis prototype, larger moving bridge.**
Four rack clamps support an open rear frame. The two lift screws require
squaring/synchronization and accessible bearing/motor mounts; mounting the
rails, bridge blocks and screw nuts before closing the support brackets is a
plausible assembly sequence, not a demonstrated technician-access study.
Three axis motors have 42×42×45 mm envelopes; the insertion motor is
28×28×35 mm. The dual lift drives and two brakes add hardware and control
channels compared with C. The current powered-off probe fails a carrier-angle
gate, despite passing its scalar holding measurements.

**B — narrower parked mechanism does not mean better rack fit.**
The nested booms need ten guide blocks, four independent axis motors and four
carrier paths. Both horizontal motor bodies are only 38 mm long in the
model; a 39 mm catalog motor cannot be declared a drop-in. Assemble and square
the nested guides, blocks, screw nuts and carrier anchors before mounting the
tool. Cantilever alignment and access to the inner member are disadvantages.
The current brake hold produces a boot/bearing-plate collision. B is useful
where one-sided mounting is required and adjacent space is available, but is
not the compact default for a dense rack row.

**C — lowest measured moving mass, more transmission assumptions.**
Two fixed 42×42×40 mm motor envelopes drive the coupled X/Z transmission;
the same small insertion motor supplies Y. There is one screw rather than
four, but belt routing, pretension, clamps, pulley engagement and slack are
less resolved than A's independent drives. The implemented elastic coupling
is not a belt tooth/contact model. Both motor-side brakes are required by the
coupled layout; the current fault recovery fails a carrier-angle gate.
The powered-cycle and travel passes do not establish a safe unpowered machine.

All designs use real articulated joints, rack-mounted geometry and the
unchanged contact-driven latch/cable. Screw forces and motor commands remain
actuation abstractions rather than measured torque-speed/efficiency models.
See [frame A](screw_guide_frame.md), [frame B](telescoping_guide_frame.md),
[frame C](corexz_guide_frame.md), [carriers](service_carriers.md) and
[powered-off tests](powered_off_brakes.md) for implementation and limitations.

### Rack/service-space consequences

The exact-package [mechanical screens](mechanical_screening.md) show:

- A/A: 10.732 kg total, 3.632 kg moving; A/C: 10.711 / 3.611 kg.
- B/A: 9.828 / 4.986 kg; B/C: 9.807 / 4.965 kg.
- C/A: 7.627 / 2.797 kg, the lightest of these five assemblies.
- A/C architectures project approximately 54 mm beyond each rack side and
  345 mm behind the nominal rear plane. B projects 248 mm left and 464 mm rear.
  Tool substitution A→C barely changes these structural envelopes.

Treat these as **rear-door-open service concepts**: no surveyed door envelope
supports a closed-door fit claim. A/C's frame and carriers still occupy side
space. B's greater projection and approximately 20.2 N·m sampled gravity mount
moment, versus about 13.4 for A and 10.0 for C, are clear comparison penalties.
These are gravity moments about a reference, not individual fastener loads.
Open frames reduce solid obstruction relative to plates, but no airflow/thermal
simulation proves adequate cooling. Neighbor-port screens and retracted finite
rasters are separate evidence, not certification of every possible cable layout.

## Supplier candidates and verified partial costs

Prices below are single-unit USD listings checked 2026-10-17, before shipping,
tax, machining or integration. They are **candidate component prices**, not
the cost of a working robot. `supplier_costs001.json` stores the same evidence
with unknown complete costs represented as `null`.

| Candidate | Listed unit price | Integration status |
|---|---:|---|
| [Actuonix PQ12-30-12-P](https://www.actuonix.com/pq12-30-12-p) | $65.00 | 20 mm stroke, 12 V, 30:1; 18 N maximum, 28 mm/s no-load, 42 mm closed hole spacing. Candidate latch actuator, not a calibrated 4 N tongue drive. |
| [Actuonix LAC](https://www.actuonix.com/lac) | $30.00 | One board per P-series actuator; external compatible supply required. Not for S/I/R variants. |
| [Hitec HS-422, 31422S](https://hitecrcd.com/hs-422-deluxe-standard-servo/) | $20.99 | C-tool actuator candidate: 40.6×19.8×36.6 mm, 45.5 g, 4.8–6 V, nylon gears/24T output. Maximum torque is not continuous capacity. |
| [StepperOnline 17HS15-1504S1](https://www.omc-stepperonline.com/nema-17-bipolar-45ncm-63-74oz-in-1-5a-42x42x39mm-4-wires-w-1m-cable-connector-17hs15-1504s1) | $9.13 | 42×42×39 mm, 1.5 A/phase, 0.45 N·m holding torque. Envelope candidate for larger axes, not the insertion motor or a qualified brake/motor assembly. |
| [StepperOnline DM542T V4](https://www.omc-stepperonline.com/digital-stepper-driver-1-0-4-2a-20-50vdc-for-nema-17-23-24-stepper-motor-dm542t) | $19.65 | 18–50 V supply, selectable 1–4.5 A peak (3.2 A maximum RMS), pulse input. No encoder-feedback or brake output; requires separate control and brake switching. |

PQ12 plus LAC is a **$95 actuator/control subtotal**. Adding one HS-422 yields
**$115.99 for those three C-tool candidate components only**. The C-tool's
rack, pinion, jaw, compliant wrist, adapter, sensor, supply and machining remain
unpriced. This subtotal must not be presented as a complete gripper price or
used to rank it as cheaper than commercial tools.

The PQ12 product page lists 21 g while the inspected datasheet distinguishes
19 g P/S and 21 g R. Retain this discrepancy for procurement; do not silently
change the tested model mass. The datasheet duty-cycle/backlash limitations
are recorded in [gripper research](grippers.md); no indefinitely repeated
hardware operation follows from the simulator running continuously.

The 39 mm stepper body fits within the larger A/C axis envelopes by size only,
but exceeds B's 38 mm horizontal bodies by 1 mm. Shafts, cables, screws,
brakes and torque-speed margins still require an exact interface selection.
Do not multiply $9.13 by every modeled motor and call that an axis BOM.
The DM542T peak/RMS current distinction must be respected when configuring
a motor. It is not the simulated force controller or a safety controller.

The [Nanotec brake drawing](https://www.nanotec.com/fileadmin/files/Datenblaetter/Bremsen/BCD/BRAKE-BCD42-0_4-5.pdf)
underlies the BCD42-0.4-5 envelopes. The vendor supplies a motor/brake
combination; its matched motor, exact mounting stack and complete price are
unknown. The separate low-cost stepper above is **not** a verified substitute.

PQ12 and stepper/driver vendors offer STEP downloads, but redistribution rights
are not established here. They have not been silently added to saved scenes.
The existing official RG2 asset provenance remains in
[sources and licenses](sources_and_licenses.md); catalog facts alone do not
confer a CAD redistribution license.

### Unpriced parts and controls — not zero

The model inventory identifies the approximate mechanical scope, but a complete
estimate still needs rails/blocks, machined screws/nuts/bearings, drive couplers,
matched brake motors, frame stock, rack clamps, custom adapters, carrier chains,
cabling, end switches, power distribution, enclosure and machining/assembly.
A-tool EGP25 and B-tool full RG2 complete purchase prices are unverified.
All tools need latch tooling and application-specific interfaces.

The simulation uses exact scene observations. A physical implementation would
need a selected perception/calibration method, connector/force sensing and
homing/interlocks; these have neither a selected complete BOM nor a cost.
Unknown totals are an explicit result of this study, not a claim that the
prototype is ready to purchase. No hardware has been ordered.

## Reproduce the inventory

From the repository root, choose a new output directory:

```bash
.venv/bin/python rack_robotics/scripts/export_hardware_inventory.py \
  --properties rack_robotics/experiments/mechanical_aa005/properties.json \
  --environment rack_robotics/environments/robot_a_gripper_a/v016 \
  --output rack_robotics/experiments/hardware-inventory-aa-NEW
```

The other exact property/package pairs are `mechanical_ba003` / B/A v014,
`mechanical_ca003` / C/A v021, `mechanical_ac002` / A/C v005 and
`mechanical_bc002` / B/C v004. The exporter rejects changed package files,
changed extraction source, failed property queries and invalid/duplicate
geometry. It does not alter a simulation or a saved package.

Final recommendation must combine current randomized reliability, occupied-port
results and these physical tradeoffs. C/A's lower mass is a provisional
advantage, not sufficient evidence to declare the final winner.
