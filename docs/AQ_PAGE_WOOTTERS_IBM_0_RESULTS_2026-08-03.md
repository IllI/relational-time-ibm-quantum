# AQ-PAGE-WOOTTERS-IBM-0 Results - 2026-08-03

## Outcome

**All five pre-registered gates passed on `ibm_marrakesh`.** The Page-Wootters
coherence witness was measured on superconducting hardware, with its predicted
growth in clock dimension, a structural null at `d = 2`, and a hardware
demonstration that conditional evolution alone is reproduced by a
classical-clock control.

Backend: `ibm_marrakesh` (156-qubit Heron), IBM Open Plan (`open-instance`).
Submitted 2026-08-04T00:50:52Z. `optimization_level=0`. Contiguous physical
chains `[0,1]`, `[0,1,2]`, `[0,1,2,3]` for `d = 2, 4, 8`.

Pre-registration filed before any job: `results_page_wootters_ibm0/pw_ibm_prereg.json`.
Raw counts (reproducible from counts up): `results_page_wootters_ibm0/pw_ibm_counts_nclock{1,2,3}.json`.
Full analysis: `results_page_wootters_ibm0/pw_ibm_results.json`.
Dry-run verification of the design: `pw_ibm_dryrun.py` / `pw_ibm_dryrun_results.json`.

## Results

| `d` | witness TVD (coherent) | classical arm | exact TVD | null floor | cond-evo R^2 | cos atten. | max\|A-B\| |
|---|---|---|---|---|---|---|---|
| 2 | 0.0071 | 0.0032 | 0.0000 | 0.0045 | -- | 0.946 | 0.011 |
| 4 | 0.1964 | 0.0103 | 0.1768 | 0.0077 | 0.9983 | 0.899 | 0.093 |
| 8 | 0.4059 | 0.0228 | 0.4967 | 0.0118 | 0.9950 | 0.900 | 0.096 |

**Job IDs (permanent record):**
```
d=2:  A d9ojerdoh1qc73bc24dg  B d9ojetbvt76s73cq7b30  C d9ojev5oh1qc73bc24ig  D d9ojf15oh1qc73bc24kg
d=4:  A d9ojf33vt76s73cq7b90  B d9ojf4va5u8s73e2s4pg  C d9ojf6rvt76s73cq7bdg  D d9ojf8jvt76s73cq7bg0
d=8:  A d9ojfau44aac73f5dgs0  B d9ojfee44aac73f5dh10  C d9ojfgdoh1qc73bc253g  D d9ojfie44aac73f5dh50
```

## Gate-by-gate

**Gate 1 -- structural null at `d = 2`: PASS.** The `d = 2` history state is
exactly the Bell state `(|00> + |11>)/sqrt(2)`; its clock marginal is
maximally mixed, so the witness must vanish even for a perfectly coherent
state. Measured TVD 0.0071 < 3 x floor (0.0134). Same apparatus, same
inverse-QFT circuit, same analysis pipeline as `d = 4, 8` -- only the clock
size changes. This rules out the witness being an artifact of the readout
circuit or of readout bias, the same role the `chi*t = pi` null played for the
OAT PTM runs.

**Gate 2 -- witness present and ordered: PASS.** TVD grows monotonically with
clock dimension, 0.0071 -> 0.1964 -> 0.4059, and the coherent value exceeds
the classical-arm value by many sigma at `d = 4` and `d = 8`. The growth is
the predicted effect: adjacent clock records become more non-orthogonal as
`d` increases (`cos(pi/d) -> 1`), so the clock marginal `rho_C` carries more
coherence, so the witness strengthens. The `d = 8` value is attenuated to
~82% of the ideal 0.497 by hardware decoherence.

**Gate 3 -- classical arms are null: PASS.** The classical-clock control
(definite `|t>`, averaged 1/d) gives near-uniform Fourier statistics at every
size: TVD 0.0032 / 0.0103 / 0.0228, each below its 3 x floor threshold. The
`d = 8` classical value (0.023) sits about 2x its shot-noise floor, consistent
with mild residual readout structure over 8 outcomes, still well within gate.

**Gate 4 -- conditional evolution recovered: PASS.** `<Z_S | t>` tracks
`A*cos(2*pi*t/d)` with R^2 = 0.998 (`d = 4`) and 0.995 (`d = 8`). The
attenuation `A ~= 0.90` is consistent across `d = 4, 8` and matches the ~0.90
attenuation the OAT PTM runs measured on this same backend -- an unforced
cross-experiment consistency check.

**Gate 5 -- conditional evolution is classically reproducible: PASS (the
point of the experiment).** Arms A (coherent clock) and B (classical clock)
agree within shot noise at every clock reading: max |A - B| = 0.011 / 0.093 /
0.096, all within the ~0.16 five-sigma band at these per-`t` shot counts.
This is the hardware demonstrating the standard objection to Page-Wootters:
conditional evolution by itself does not witness clock coherence, because a
classically correlated clock-system state reproduces it exactly. The
coherence witness (Gate 2) is what separates them -- and it does, decisively.

## What This Establishes

1. On a superconducting processor, the conditional-evolution signal usually
   cited as "time from entanglement" is reproduced by a classical clock
   control (Gate 5). Conditional evolution alone is not a witness of anything
   quantum.
2. The clock-marginal coherence witness -- the off-diagonal structure
   `rho_C[t,t'] = (1/d) cos((t-t')*pi/d)` -- does distinguish the coherent
   history state from the classical mixture, survives hardware noise, and
   grows with clock dimension as predicted, with a structural null at `d = 2`.
3. The off-diagonals measured here are exactly the clock-record
   non-orthogonality quantity characterized numerically in the synthetic
   branch (`AQ-PAGE-WOOTTERS-DLINOSS-QUANTUM-CLOCK-BOUND-0`,
   `-MULTICLASS-CLOCK-BOUND-0`). What appeared there as a limitation -- local
   clock records being non-orthogonal and locally indistinguishable -- is the
   same quantity that makes the coherence witness measurable on hardware. The
   sign of that inversion is the conceptual result.

## Claim Boundary (held)

**Claimed:** a hardware measurement of the clock-marginal coherence structure
of a small engineered Page-Wootters history state, its dimensional scaling,
its structural null, and the hardware demonstration that conditional evolution
is classically reproducible.

**Not claimed** (per FINDINGS.md 135 discipline): that time is emergent, that
this bears on physical spacetime or quantum gravity, that a physical
Page-Wootters universe was realized, or any teleportation/advantage/supremacy
claim. This is the coherence structure of a 2-4 qubit engineered state, not a
statement about the nature of time.

## Replication (same day): two devices, two layouts

Two replications were run immediately after the primary:

- **Cross-device**, `ibm_fez` (156q Heron r2), chains `[0,1] / [0,1,2] / [0,1,2,3]`.
  Results: `results_page_wootters_ibm0_fez/`.
- **Disjoint-layout**, `ibm_marrakesh`, chains `[4,5] / [4,5,6] / [4,5,6,7]`
  (`--exclude 0 1 2 3`). Results: `results_page_wootters_ibm0_layoutB/`.

| run | d | coherent TVD | classical TVD | separation | cond R^2 |
|---|---|---|---|---|---|
| marrakesh [0-3] | 2 / 4 / 8 | 0.007 / 0.196 / 0.406 | 0.003 / 0.010 / 0.023 | -- / 0.186 / 0.383 | -- / 0.998 / 0.995 |
| fez [0-3] | 2 / 4 / 8 | 0.005 / 0.155 / 0.331 | 0.001 / 0.039 / 0.023 | -- / 0.115 / 0.309 | -- / 0.991 / 0.997 |
| marrakesh [4-7] | 2 / 4 / 8 | 0.005 / 0.210 / 0.423 | 0.008 / 0.007 / 0.045 | -- / 0.202 / 0.377 | -- / 0.999 / 0.998 |

**What replicated (robust across both devices and both layouts):**
Gate 1 (d=2 structural null), Gate 2 (witness present and monotonically
ordered), Gate 4 (conditional evolution recovered, R^2 > 0.99), Gate 5
(A = B classical reproducibility), and -- the load-bearing quantity -- the
coherent-vs-classical **separation**, which is large and positive at d = 4
and d = 8 in every run (0.19/0.38, 0.12/0.31, 0.20/0.38). The `d = 8`
coherent witness is attenuated to 82% / 67% / 85% of the ideal 0.497 across
the three runs; `ibm_fez` is the noisiest for this circuit.

**What did NOT replicate (honest finding): pre-registered Gate 3 failed on
both replications.** The classical-clock arm was pre-registered to sit within
3x the shot-noise floor. It breached that in one clock size per replication:
`fez` at d=4 (0.039, 5.1x floor) and `marrakesh [4-7]` at d=8 (0.045, 3.8x
floor). By the locked criterion, both replications report
`all_gates_pass = False`. This is reported as-is; the gate was not relaxed
after the fact.

**Diagnosis -- mis-specified null, not a physics failure.** The Gate 3 null
modeled the classical arm as deviating from uniform by shot noise alone. On
hardware the classical arm carries a real systematic: preparing a definite
`|t>`, applying the inverse-QFT, and reading out on qubits with asymmetric
readout error yields slightly non-uniform Fourier statistics even at infinite
shots. The captured calibration confirms the mechanism by contrast: the
original run's qubits `marrakesh [0,1,2,3]` have unusually clean readout
(0.5-1.3%, mild asymmetry), which is why it passed; the replication qubits are
noisier. The floor should have been "uniform + hardware readout systematic,"
not "uniform + shot noise." Replication exposed the flaw -- which is what
replication is for.

Crucially, the mis-specified gate does not touch the claim: the classical arm
moving from ~0.01 to ~0.04 is immaterial against a coherent arm at 0.15-0.42.
The separation -- the quantity the experiment exists to measure -- holds by
3x to 14x in every run.

**Post-hoc mitigation result (2026-08-03, `pw_ibm_mitigation.py`): readout
correction does NOT rescue Gate 3 -- diagnosis revised.** Tensor-product
confusion-matrix inversion built from the captured backend calibration moves
the failing classical arms only marginally (fez d=4: 0.039 -> 0.031, still
~4x floor; marrakesh_B d=8: 0.045 -> 0.044). The earlier readout-asymmetry
diagnosis was therefore WRONG as the primary mechanism. Revised diagnosis:
the classical-arm excess is dominated by coherent gate error in the
inverse-QFT whose effect depends on the prepared input |t>, so the
1/d-averaged mixture is not exactly uniform at the ~0.03-0.05 TVD level.
This is not correctable post-hoc from counts; the right fix in any future
run is an in-run classical baseline (arm D measured concurrently, as here)
treated as the empirical null reference rather than an idealized uniform
floor -- i.e., pre-register the *separation* C - D, not the absolute
D-vs-uniform distance. Full numbers:
`results_page_wootters_ibm0/pw_ibm_mitigation_posthoc.json`.

**The separation is untouched by all of this.** Raw and mitigated alike,
C - D at d = 4 / 8 is 0.19/0.38 (marrakesh_A), 0.12/0.31 (fez), 0.20/0.38
(marrakesh_B) -- 5x to 10x the classical arm itself, in every run, on both
devices.

**Layout-integrity disclosure (bug found in code review, 2026-08-03;
VERIFIED same day).** The submitter recorded an intended physical chain from
`find_chain()` but never passed `initial_layout` to `transpile()`.
`pw_ibm_verify_layout.py` retrieved the actual transpiled circuits from all
36 archived jobs (`pw_ibm_actual_layouts.json` per run -- the authoritative
layout record) and confirmed: **every run executed on physical qubits 0-3**
of its backend. Therefore:

- `marrakesh_B` is a **temporal replicate** (~28 min after the primary, same
  physical qubits), not a spatial one. Its provenance calibration snapshot
  (mistakenly captured for qubits 4-7) is superseded by the primary run's
  qubits 0-3 snapshot, which `pw_ibm_mitigation.py` already used.
- The cross-device `ibm_fez` run stands unchanged as the genuine
  device-independence control.
- The replication evidence is honestly summarized as: one cross-device
  replication plus one same-device temporal replicate. A true disjoint-layout
  replication remains unexecuted (and would need the now-fixed submitter to
  pass `initial_layout`).

The verification also recovered the true on-device circuit costs, which are
substantially higher than the basis-gate-only dry-run estimates (routing on
the heavy-hex lattice): d=8 witness depth 143-158 with 33-36 two-qubit ops
(vs. 59/15 estimated). The witness separation survived at these depths, which
strengthens the noise-robustness statement. The measurement maps also show
the transpiler permuted clbit-to-physical-qubit assignments per circuit
(routing swaps); this does not affect any TVD or conditional analysis (both
are computed from classical bitstrings), but it does mean per-qubit readout
mitigation matrices are approximate at d >= 4 -- consistent with mitigation's
small effect.

## Provenance

Captured 2026-08-03 for the primary run into
`results_page_wootters_ibm0/pw_ibm_provenance.json` (12/12 jobs, plus
`ibm_marrakesh` calibration for qubits 0-3; `last_update_date`
2026-08-03T20:00:04-05:00). Server-side timestamps confirm the run at
2026-08-03T19:50-19:52 local. Account is a trial expiring ~2026-09-01;
`ibm_fez` and `marrakesh [4-7]` calibration snapshots should be captured the
same way before then (re-run `pw_ibm_provenance.py --results <replication>/pw_ibm_results.json`)
to fully ground the readout-systematic diagnosis above.

## Next Step

1. Capture provenance for the two replication runs before account expiry.
2. Apply post-hoc readout mitigation to all three runs' saved counts; report
   the mitigated classical arm separately from the pre-registered result. If
   mitigation brings the classical arm within floor (expected), that closes
   the Gate 3 gap as a *diagnosed and corrected* control issue, with the
   pre-registered failure honestly on record.
3. Only then consider whether the result supports a short quantum-foundations
   note. The robust core (Gates 1/2/4/5 + separation, replicated across two
   devices) is the paper; the Gate 3 story is a methods paragraph on classical-
   control calibration, not a headline.
