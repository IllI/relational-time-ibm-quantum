# AQ-PAGE-WOOTTERS-IBM-2 — Witness Specificity: A Reported Limitation and Its Fix

> [!IMPORTANT]
> **The "fix" has its own measured limitation — see IBM-3 (same day).**
> `W_joint` separates the history state from the two controls measured here,
> but a *separable* classically-correlated state (a 50/50 mixture of two
> coherent product states) scores **0.47/0.45 on hardware — 1.7× the history
> state** — so `W_joint` certifies coherence-plus-correlation, not
> entanglement. A two-line argument in the IBM-3 doc shows no functional of
> a single-setting joint distribution could ever certify entanglement. The
> scope note at the bottom of this document was correct, and IBM-3 measured
> it. See `AQ_PAGE_WOOTTERS_IBM_3_RESULTS_2026-08-07.md`.

**Executed 2026-08-07 on `ibm_marrakesh`.** 4 jobs, 22 circuits, ~30k shots.
All 8 pre-registered gates pass. Pre-registration filed before submission:
`results/hardware/ibm2/ibm2_prereg.json`.

**This run was designed to attack our own primary result, and it succeeded.**
The clock-marginal coherence witness used as the headline observable in IBM-0
and IBM-1 is demonstrated on hardware to be **necessary but not sufficient**:
a state with *zero* clock–system entanglement scores up to 4× higher on it
than the actual Page–Wootters history state. A joint-readout witness that
survives the attack is measured in the same run, from the same counts.

---

## The criticism

The inverse-QFT readout depends only on `ρ_C`. It therefore cannot, even in
principle, distinguish clock–system entanglement from *local clock coherence*.
IBM-0 and IBM-1 both established that a classical mixture fails to reproduce
the witness — true, and still true — but never tested the other direction: a
state that is coherent in the clock while having no clock–system structure
at all.

## The adversarial state (arm E)

```
|Φ⟩ = (1/√d) Σ_t |t⟩_C ⊗ |0⟩_S
```

Coherent clock, system parked in `|0⟩`, zero correlation between them. Its
clock marginal is the *pure* state `|f₀⟩⟨f₀|` with `ρ_C[t,t'] = 1/d` for every
pair — maximal off-diagonals, larger than the history state's
`(1/d)cos((t−t')π/d)`. Under inverse QFT it collapses to a delta at `k=0`:

```
local witness = TVD(P(k), uniform) = (d−1)/d
```

exactly 0.75 at d=4 and 0.875 at d=8 — confirmed analytically by statevector
before any QPU time was spent.

## Hardware results

| d | arm | local W | joint W | joint floor | J/floor |
|---|---|---|---|---|---|
| 4 | C history | 0.1695 | **0.2665** | 0.0151 | **17.6** |
| 4 | D classical | 0.0195 | 0.0209 | 0.0167 | 1.26 |
| 4 | **E product** | **0.7177** | **0.0001** | 0.0034 | **0.04** |
| 4 | E padded | 0.6910 | 0.0074 | 0.0056 | 1.33 |
| 8 | C history | 0.4345 | **0.3003** | 0.0200 | **15.0** |
| 8 | D classical | 0.0261 | 0.0143 | 0.0173 | 0.83 |
| 8 | **E product** | **0.8213** | **0.0042** | 0.0067 | **0.63** |
| 8 | E padded | 0.7648 | 0.0152 | 0.0098 | 1.55 |

### Gate 1 — specificity failure, confirmed

**The zero-entanglement product state outscores the history state on the local
witness by 4.23× at d=4 and 1.89× at d=8.** Measured 0.7177 / 0.8213 against
exact 0.75 / 0.875 — within the expected hardware attenuation.

The local witness, on its own, does not certify anything about clock–system
structure. It certifies *clock coherence*. Those are different claims, and
IBM-0/IBM-1 measured the second while the framing invited the first.

### Gates 2–3 — the joint witness survives the attack

Measuring both registers in the same shot (clock in Fourier basis, system in
Z) and computing `W_joint = TVD(p(k,z), p(k)p(z))`:

- **Arm E: 0.0001 (d=4) and 0.0042 (d=8)** — 0.04× and 0.63× their own
  shot-noise floors, i.e. indistinguishable from zero, exactly as predicted
  (the product state's joint distribution factorizes by construction).
- **Arm C: 0.2665 and 0.3003** — 17.6× and 15.0× floor.
- Separation ratio **C/E = 2066× (d=4)** and **71× (d=8)**.

The joint witness separates the history state from the adversarial control by
one to three orders of magnitude, where the local witness got it backwards.

### Gate 4 — the IBM-0 Gate 3 correction, retired

Separation measured as `C − D` against the **in-run** classical baseline
rather than an idealized uniform floor. Passes at both d. This is the design
the IBM-0 results doc identified as correct after its Gate 3 failed on both
replications; it is now measured and passing.

---

## Honest caveats

**1. The classical mixture's joint witness is slightly above its floor at
d=4** (0.0209 vs 0.0167, ratio 1.26). Exact theory says 0. At d=8 it is
within floor (0.83). This is the same residual-systematic pattern documented
in the IBM-0 ledger (readout asymmetry plus input-dependent coherent iQFT
error), and it was **not gated** — no gate was pre-registered on arm D's joint
witness, only on arm E's. Reported here rather than passed over. It does not
threaten the conclusion (C/D joint ratio is still ~13–21×) but a future run
should gate it.

**2. The depth-padded product control shows a small spurious joint signal**
(0.0074 and 0.0152, i.e. 1.33× and 1.55× floor) where the unpadded version
shows essentially none. The `CRY(0)` gates are logically identity but
physically noisy, and they inject weak correlation. Both remain 20–36× below
arm C. The padded arm's *local* witness is also lower than unpadded (0.691 vs
0.718; 0.765 vs 0.821) — depth costs coherence, as expected. The specificity
failure holds in both versions, so it is not an artifact of E being a
shallower circuit.

**3. Attenuation is consistent with the rest of the program.** Arm C's local
witness is at 0.959 (d=4) and 0.875 (d=8) of exact; its joint witness at 0.883
and 0.792. The d=8 local value of 0.4345 independently reproduces IBM-0's
0.406 measurement of the same quantity on the same backend.

---

## What this changes

**Retained.** IBM-0's and IBM-1's measurements stand as recorded. The
classical mixture genuinely does not reproduce the coherence witness; the
decoherence threshold of IBM-1 is genuinely measured; Gate 4 of IBM-1
(apparent time outliving its quantum signature) is untouched by this result,
since it concerns conditional evolution rather than the witness's specificity.

**Narrowed.** Any reading of the local witness as certifying the
*Page–Wootters structure* — clock–system entanglement specifically — is not
supported. It certifies clock coherence. The correct statement of the IBM-0
result is:

> The clock-marginal coherence witness separates a coherent history state from
> its classical mixture, but does not distinguish it from a coherent
> clock–system *product* state, which scores higher still. It is necessary,
> not sufficient, for the Page–Wootters structure.

**Added.** `W_joint` is measured, from the same counts at no extra cost, and
separates the history state from *both* adversarial controls — the classical
mixture (no clock coherence) and the coherent product state (no correlation).

**Scope, stated as narrowly as the evidence supports.** `W_joint` certifies
clock–system correlation *read in a coherent clock basis*. It is **not**
claimed here as a formal entanglement witness; establishing that requires an
argument this run does not make (in particular, ruling out separable mixed
states that could produce nonzero `W_joint`). What is demonstrated is that it
separates the three specific states measured, where the local witness does not.

---

## Provenance

Backend `ibm_marrakesh`, 4 jobs, 2026-08-07T22:19Z. Job IDs in
`ibm2_results.json`. Capture server-side provenance before the trial account
expires (~2026-09-01):

```
python pw_ibm_provenance.py --results results_ibm2_ibm_marrakesh/ibm2_results.json --out results_ibm2_ibm_marrakesh/ibm2_provenance.json
```

## Recommended follow-ups

- **Gate arm D's joint witness** in any future run; it was measured but not
  pre-registered as a gate here.
- **The clock-ambiguity test** (two inequivalent clock decompositions of the
  same global state) remains the other open item on the critique roadmap. It
  needs more circuits and more design work than this run did.
- ~~**A formal treatment of `W_joint`** — whether it can be promoted from
  "separates these three states" to a certified correlation witness with a
  bound on separable states — is theory work, not hardware work.~~
  **Answered by IBM-3, negatively:** a separable mixture of two coherent
  product states scores 0.5 exactly (0.47/0.45 measured), exceeding the
  history state. No single-setting observable can bound separable states —
  see the diagonal-mimic theorem in `AQ_PAGE_WOOTTERS_IBM_3_RESULTS_2026-08-07.md`.
