# Measuring the Quantum Signature of Relational Time on Superconducting Hardware

**What this is.** An experimental program testing whether *relational time* —
time defined by correlations between a clock and the rest of a system, rather
than by an external parameter — leaves a measurable quantum signature that can
be distinguished from its classical mimic. It runs from a set of disciplined
nulls on classical substrates to a replicated positive result on IBM Quantum
Heron processors. All raw counts, pre-registrations, and provenance are
archived here; every analysis reproduces from counts.

---

## The question

Page and Wootters (1983) proposed that a universe in a globally *static*
entangled state contains apparent dynamics: partition it into a clock `C` and
a system `S`, and conditioning `S` on a clock reading yields an evolving
system state — with no external time parameter anywhere. Moreva *et al.*
(PRA **89**, 052122 (2014)) illustrated this with entangled photons, and the
idea has since been extended to quantum reference frames, relativistic clocks,
and cosmology.

**The standing objection is that the usual demonstration proves nothing
quantum.** A classically correlated clock–system state,
`ρ = (1/d) Σ_t |t⟩⟨t| ⊗ |ψ(t)⟩⟨ψ(t)|`, reproduces the conditional evolution
`⟨Z_S | t⟩` *exactly*. If "time flows relative to the clock" is the whole
signature, a classical clock delivers it too, and nothing has been shown about
quantum time.

## Hypothesis

If relational time in the Page–Wootters sense is genuinely quantum, the
distinguishing structure cannot live in the conditional dynamics. It must live
in the **coherence of the clock marginal**.

Tracing the system out of the history state
`|Ψ⟩ = (1/√d) Σ_t |t⟩_C ⊗ U^t|0⟩_S` gives

```
ρ_C[t,t'] = (1/d) ⟨ψ(t')|ψ(t)⟩ = (1/d) cos((t − t')·π/d)
```

Those off-diagonals are the overlaps between clock records — the degree to
which different "moments" are *not* perfectly distinguishable. The classical
mixture has the identical diagonal and **exactly zero** off-diagonals. So the
hypothesis is concrete and falsifiable:

1. **The clock marginal carries coherence that no classical clock–system
   correlation can reproduce**, and it is measurable by reading the clock in
   its Fourier (energy) basis — the basis conjugate to clock-time, whose
   eigenstates are the eigenstates of the clock's shift generator. A peaked
   Fourier distribution reflects the clock–system constraint structure that
   defines a history state; a classical mixture is exactly uniform there.
   *(This is why the inverse quantum Fourier transform is not incidental
   machinery here — it is the measurement that accesses the constraint.)*
2. **The signature should strengthen with clock dimension `d`**, because
   adjacent records become *less* orthogonal as `d` grows (`cos(π/d) → 1`),
   putting more coherence into `ρ_C`.
3. **It must vanish structurally at `d = 2`**, where the history state is
   exactly a Bell pair and the clock marginal is maximally mixed — a null
   predicted by theory, reachable with the same apparatus by changing nothing
   but the clock size.

## What was tested

A four-arm protocol on IBM Heron r2 processors, pre-registered before
submission, at clock sizes `d = 2, 4, 8`:

| Arm | Clock prepared | Clock measured in | Tests |
|---|---|---|---|
| **A** | superposition | computational | conditional evolution `⟨Z_S\|t⟩ = cos(2πt/d)` |
| **B** | definite `\|t⟩`, averaged 1/d | computational | *the objection* — must reproduce A exactly |
| **C** | superposition | inverse-QFT | clock-marginal coherence |
| **D** | definite `\|t⟩`, averaged 1/d | inverse-QFT | classical baseline — must be uniform |

Arms B and D are real hardware circuits, not classical post-processing: a
definite clock state averaged over `t` with weight `1/d` realizes the
classical mixture exactly.

## Conclusion

Stated as narrowly as the evidence supports:

> In a 2–4 qubit engineered history state on superconducting hardware, the
> conditional-evolution signal usually cited as "time from entanglement" is
> reproduced by a classical clock control to within shot noise — confirming
> the objection experimentally. The clock-marginal coherence is **not**
> reproduced: it separates the coherent history state from its classical
> mimic by 5–10× on two devices, grows with clock dimension as predicted
> (measured ≈0.005 → 0.16–0.21 → 0.33–0.42 against exact values 0, 0.177,
> 0.497), and vanishes at the `d = 2` structural null.

**What this does not show.** It does not show that time in nature is emergent,
does not test quantum gravity or the Wheeler–DeWitt equation, and does not
realize a physical Page–Wootters universe. The history state here is
*engineered*, not found. What it establishes is narrower and prior to any of
that: the specific quantum structure the Page–Wootters mechanism requires is
present, measurable, and cleanly separable from its classical imitation on
current hardware — which is the precondition for any stronger claim, and which
had not previously been measured on a gate-based processor.

**Where this connects to current work.** Two recent results make quantitative
predictions this apparatus is positioned to test, and both note the
small-processor test as an open gap: a December 2025 relational-emergent-time
framework predicts local coherence decaying as `C(E) = C₀e^{−kE}` with
clock–system entanglement `E` (arXiv:2512.15789), and a February 2026 extended
two-qubit Page–Wootters model predicts a monotonic *informational arrow of
time* — von Neumann entropy of the conditional system state increasing across
successive clock readings once an inaccessible auxiliary is traced out
(*Phys. Lett. A*, S0375960126001325). A follow-up run designed against both is
specified in `docs/AQ_PAGE_WOOTTERS_IBM_1_RUN_SPEC.md`.

---

## The research path

The program produced **three disciplined nulls and one replicated positive
result**, in that order, and the nulls are load-bearing: each redirected the
question onto a better substrate until it became well-posed.

**Headline result.** On IBM Quantum Heron processors, the 4-arm protocol above
measured the clock-marginal coherence witness of `|Ψ⟩ = (1/√d) Σ_t |t⟩_C ⊗ U^t|0⟩_S`:

1. Conditional evolution `⟨Z_S|t⟩ = cos(2πt/d)` recovered with R² > 0.99 —
   and **reproduced exactly by a classical-clock control**, demonstrating on
   hardware that conditional evolution alone witnesses nothing quantum.
2. The clock-marginal coherence witness (inverse-QFT readout, TVD from
   uniform) separates the coherent history state from the classical mixture
   by 5–10× at d = 4, 8 — replicated on **two devices** (`ibm_marrakesh`,
   `ibm_fez`) and in a same-day temporal replicate.
3. The witness **grows with clock dimension** (measured ≈0.005 → 0.16–0.21 →
   0.33–0.42 for d = 2, 4, 8 against exact predictions 0, 0.177, 0.497), and
   **vanishes structurally at d = 2** (the history state is then a Bell pair
   with maximally-mixed clock marginal) — an internal null with the same
   apparatus, protocol, and analysis.

The off-diagonals being measured, `ρ_C[t,t'] = (1/d)cos((t−t')π/d)`, are
exactly the finite-clock record overlaps that the synthetic branch of this
program characterized as a *limitation* (locally indistinguishable clock
records). On hardware, that same non-orthogonality is the *signal*. That
inversion is the conceptual through-line of the paper.

**Claim boundary (locked).** This is a hardware measurement of the coherence
structure of a 2–4 qubit engineered state. It is **not** a claim that time is
emergent, a test of quantum gravity or the Wheeler–DeWitt equation, or a
realized Page–Wootters universe. No teleportation/advantage/supremacy claims.

---

## The arc (what was tried, in order, and what each step established)

### Part I — CHRONOS: cross-datacenter timing telemetry (June 2026, TRC TPUs) → null

Thesis-origin experiments: two TPU hosts (`us-east1-d`, `europe-west4-a`)
each emitting a 128 Hz "now" stream (fixed-probe latency with wall-clock
metadata), asking whether independent hosts share learnable temporal
structure — external carriers (Schumann band), infrastructure clocks, or
relational clocks, under preregistered gates with shuffled/severed/wrong-time
controls.

- `CHRONOS-0/0b`: sequencing artifact found and fixed; active effect only
  borderline (MW p≈0.066). `CHRONOS-SCHUMANN-0a/0b`: a striking first result
  (+0.50 separation, p=0.001) that **failed preregistered replication** —
  reported as such, not promoted.
- `AQ-DLINOSS-CHRONO-0`: learned temporal-geometry test; clean null (true
  heldout score below the strongest null control).
- `CHRONOS-MARGINAL-DRIFT-1`: the killer control — US/EU feature correlation
  (r≈0.57) **survives a one-hour offset** (r≈0.50): structural hardware
  similarity, not shared time. `CHRONO-MERA-STRAIN-0`: no synchronized
  entropy-spike events.
- `CHRONOS-REAL-ENTROPIC-CLOCK-0` (2026-08-03): the strongest-available
  mechanism (see Part II) applied back to the real telemetry — global path
  recoverable (rank 1 on all three pairs) but window-level prediction fails
  *harder* than any synthetic noise level, and the real +1 h stream is the
  best-scoring null. **The telemetry line is closed, not merely stalled.**

Verdict, stated plainly: classical datacenter telemetry was the wrong
substrate for the question — and the controls proved it rather than assumed it.
Real data: `data/telemetry/` (the actual US/EU q-streams). Docs:
`docs/history/CHRONOS_*.md`, analysis in `telemetry/`.

### Part II — Synthetic Page–Wootters ladder (June 2026, TRC TPUs) → one promoted mechanism, sharp bounds

Moving the clock *inside* the modeled state: `|Ψ⟩ = Σ_t |t⟩_C |ψ(t)⟩_S`
histories with a genuine complex-diagonal D-LinOSS recurrence, frozen-operator
scoring, and calibration-only selection. Roughly twenty runs
(`docs/history/AQ_PAGE_WOOTTERS_DLINOSS_0_RESULTS_2026-06-15.md` is the
ladder log). Key findings:

- **Under-identifiability discovery:** in a projected-harmonic generator, the
  internal clock is too degenerate under noise for *any* matcher/metric/
  embedding to recover the correspondence — diagnosed via an
  observability-first decomposition, not endless tuning.
- **Entropy is required:** recovery only became possible after the generator
  produced irreversible, entropy-bearing histories (causal events, bath
  memory, entropy/action integrals — arm `A10`). Independently convergent
  with the entropic-time construction later published for cold atoms
  (arXiv:2509.07745, τ ∝ ∫dS).
- **Physics-damped state spaces win:** a stationary recurrence failed;
  an **event-damped D-LinOSS** (damping driven by entropy/event observables —
  the original grant thesis, "a state-space model damped by physical
  constraints") closed the ridge gap and passed all mechanism gates across
  ten seeds through noise 0.03.
- **Finite-clock bounds:** local clock records are provably non-orthogonal
  (record overlap ≈0.94 on failed windows; Helstrom-style ceiling ≈0.60);
  the *global monotone path* remains perfectly recoverable (rank 1). Promoted
  claim: relational time is a **path-level**, not pointwise, observable in
  these systems.

Programs: `synthetic/`. Compact results: `results/synthetic/`.

### Part III — BEC entropic bridge (2026-08-03) → null, pre-registered stop

A two-mode Josephson BEC generator (inspired by arXiv:2509.07745's
bright/dark-sector construction) tested whether an entropy-derived τ is
recoverable from bright-sector observables across independent noise
realizations. **Gate 0 failed 0/5 regimes** with clean controls (shuffled and
cross-regime nulls fail hard everywhere, so the harness is sound); per the
pre-registered criterion, the two-world bridge was not built. Reported as a
statement about this mean-field proxy and feature set — not about the
published cold-atom result. Docs: `docs/history/*BEC_ENTROPIC_BRIDGE*`.

### Part IV — AQ-PAGE-WOOTTERS-IBM-0: hardware (2026-08-03) → replicated positive result

Full spec: `docs/AQ_PAGE_WOOTTERS_IBM_0_RUN_SPEC_2026-08-03.md`.
Full results incl. all caveats: `docs/AQ_PAGE_WOOTTERS_IBM_0_RESULTS_2026-08-03.md`.

| run | backend | d=2 null | witness d=4 / d=8 | classical arm | separation d=8 | cond R² |
|---|---|---|---|---|---|---|
| primary | ibm_marrakesh | 0.007 ✓ | 0.196 / 0.406 | 0.003–0.023 | **0.383** | 0.995–0.998 |
| cross-device | ibm_fez | 0.005 ✓ | 0.155 / 0.331 | 0.001–0.039 | **0.309** | 0.991–0.997 |
| temporal replicate | ibm_marrakesh | 0.005 ✓ | 0.210 / 0.423 | 0.007–0.045 | **0.377** | 0.998–0.999 |

Pre-registration filed before each submission; raw counts, job IDs, and
backend calibration snapshots archived (`results/hardware/*/`); the entire
analysis reproduces from counts with no IBM dependency.

**Honest ledger for this result (all on record in the results doc):**

1. **Pre-registered Gate 3 failed on both replications.** The classical arm
   was preregistered to sit within 3× the shot-noise floor; it breached that
   once per replication (fez d=4: 0.039; marrakesh-B d=8: 0.045). The gate
   was not relaxed; both replications report `all_gates_pass=False` as
   registered.
2. **Post-hoc readout mitigation does NOT rescue it** (0.039→0.031,
   0.045→0.044) — so the first diagnosis (readout asymmetry) was wrong.
   Revised diagnosis: input-dependent coherent error in the inverse-QFT makes
   the 1/d-averaged classical mixture non-uniform at the 0.03–0.05 level.
   Correct future design: pre-register the *separation* C−D against the
   in-run classical baseline, not D against an idealized uniform floor.
3. **Layout-integrity disclosure (verified):** the submitter computed but
   never passed `initial_layout` to the transpiler (bug found in code
   review). `hardware/pw_ibm_verify_layout.py` retrieved the actual
   transpiled circuits from all 36 archived jobs and confirmed every run
   executed on physical qubits 0-3 of its backend
   (`results/hardware/*/pw_ibm_actual_layouts.json` is the authoritative
   record). The "disjoint layout" run is therefore a *temporal* replicate;
   the evidence is honestly: one cross-device replication + one temporal
   replicate. True on-device depths were also recovered (d=8 witness:
   143-158, 33-36 two-qubit ops -- ~2.5x the basis-only estimate), which
   strengthens the noise-robustness statement since the separation survived
   at those depths.
4. None of the above touches the separation (5–10× everywhere), the
   dimensional scaling, the d=2 structural null, or the classical
   reproducibility of conditional evolution — the four findings that
   constitute the result.

---

## Repository layout

```
hardware/           IBM protocol: dry run (Aer, ideal+noisy), submitter,
                    provenance capture, post-hoc mitigation, layout verification
results/hardware/   per-run: prereg, raw counts, analysis, provenance,
                    mitigation; plus the Aer dry-run predictions
synthetic/          the promoted-mechanism chain: PW core, A10 causal-memory
                    generator, path observability, event-damped D-LinOSS
                    confirm, finite-clock bound diagnostics, BEC bridge Gate 0
results/synthetic/  compact JSON results for the runs above
telemetry/          CHRONOS collector + the 2026-08-03 real-data reanalysis
data/telemetry/     the actual US/EU TPU q-streams (real data, 128 Hz, ~256 s)
results/telemetry/  real-data reanalysis outputs
docs/               IBM run spec + results (the paper's evidentiary core)
docs/history/       the full research trail: CHRONOS specs/results, the
                    synthetic ladder log, BEC bridge spec/results
```

Note: scripts retain the relative paths of the working research repo they ran
in; they are provenance artifacts first, rerunnable second (adjust paths or
run from a matching layout to reproduce).

## Reproducing

```bash
pip install qiskit qiskit-aer qiskit-ibm-runtime numpy scipy jax

# Verify the design and regenerate predictions locally (no account needed):
python hardware/pw_ibm_dryrun.py

# Smoke-test the full submit/analyze pipeline against Aer (zero QPU):
python hardware/pw_ibm_submit.py --dry

# Hardware resubmission (IBM account; token via env var, never hardcoded):
export QISKIT_IBM_TOKEN=...
python hardware/pw_ibm_submit.py --backend ibm_marrakesh
```

All hardware analyses reproduce from the archived raw counts in
`results/hardware/*/pw_ibm_counts_nclock*.json` without any IBM access.

## Provenance

- Backends: `ibm_marrakesh`, `ibm_fez` (156-qubit Heron r2), IBM Open Plan
  (trial instance). 36 jobs total, ~4 s QPU each; all job IDs and server-side
  timestamps in `results/hardware/*/pw_ibm_provenance.json` (authoritative
  for chronology).
- Simulation stages (CHRONOS, synthetic ladder) ran on Google TPU Research
  Cloud (TRC) `v6e` spot instances during the grant window 2026-04-21 →
  2026-06-21 (initial one-month grant extended a further month on the
  time-emergence thesis). The IBM hardware stage used no TRC resources.
- The views expressed are those of the author and do not reflect the official
  policy or position of IBM, the IBM Quantum team, or Google.

## Acknowledgments

Google TPU Research Cloud (TRC) for TPU access during the simulation phase;
IBM Quantum Open Plan for hardware access. The entropic-time framing of
Part III follows arXiv:2509.07745; the Page–Wootters protocol follows
Page & Wootters (1983) and the photonic illustration of Moreva *et al.*
(PRA 89, 052122 (2014)), with the classical-control and coherence-witness
arms added here.
