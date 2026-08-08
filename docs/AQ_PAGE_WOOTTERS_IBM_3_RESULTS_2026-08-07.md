# AQ-PAGE-WOOTTERS-IBM-3 — W_joint Is Not an Entanglement Witness, and No Single-Setting Observable Could Be

**Executed 2026-08-07 on `ibm_marrakesh`.** 4 jobs, 6 circuits, ~15 s QPU.
All 4 pre-registered gates pass. Pre-registration filed before submission:
`results/hardware/ibm3/ibm3_prereg.json`.

IBM-2 introduced `W_joint = TVD(p(k,z), p(k)p(z))` as the fix for the local
witness's specificity failure, and scoped it as *not* claimed to be a formal
entanglement witness. This run converts that caveat from an assertion into a
measurement — and then into a theorem that closes the question for the whole
observable family used in this program.

---

## The adversarial separable state

```
ρ_sep = ½ |f₀⟩⟨f₀|_C ⊗ |0⟩⟨0|_S  +  ½ |f₁⟩⟨f₁|_C ⊗ |1⟩⟨1|_S
```

A classical 50/50 mixture of two **product** states — zero entanglement by
construction — but with both clock coherence (each branch's clock is a pure
Fourier state) and perfect clock–system correlation (which Fourier state the
clock is in tells you the system bit). Conditioned on `z=0` the Fourier
readout is a delta at `k=0`; on `z=1`, a delta at `k=1`. The joint
distribution cannot factorize, so `W_joint = 0.5` exactly — **higher than the
entangled history state's 0.302 (d=4) / 0.379 (d=8)**.

## Hardware results

| d | arm | local W | joint W | J/floor |
|---|---|---|---|---|
| 4 | **separable** (zero entanglement) | 0.4816 | **0.4731** | **72.8×** |
| 4 | history (maximally entangled) | 0.1603 | 0.2735 | 18.1× |
| 8 | **separable** | 0.6913 | **0.4524** | **49.7×** |
| 8 | history | 0.4043 | 0.2730 | 13.2× |

The separable state beats the entangled history state on the joint witness by
1.7× at both clock sizes (exact prediction: 0.500 vs 0.302/0.379), and its
history-arm re-measurements independently reproduce IBM-2's values (0.2735 vs
0.2665; 0.2730 vs 0.3003 — the d=8 spread reflecting the stale-calibration
window noted in the IBM-2 provenance). Both gates pass at both d.

## The theorem this run made unavoidable

Once the result is in hand, the general fact is two lines:

> For any state ρ measured in one fixed product basis `{|f_k⟩ ⊗ |z⟩}`, define
> `σ = Σ_{k,z} p(k,z) |f_k⟩⟨f_k| ⊗ |z⟩⟨z|`. Then σ is separable (diagonal in
> a product basis) and reproduces `p(k,z)` **exactly**.
>
> Therefore *no functional of a single-setting joint distribution* — not
> `W_joint`, not the local witness, not conditional-evolution R², nothing
> measured in IBM-0 through IBM-3 — can distinguish an entangled state from a
> separable one. Every observable in this program was a single-setting
> observable, and single-setting observables are entanglement-blind, always.

IBM-3's mimic doesn't just match the history state's witness value; the
theorem guarantees a separable state exists that reproduces its *entire*
measured distribution. The hardware run makes the fact vivid and quantitative;
the two-line argument makes it airtight.

**Process lesson, recorded:** this argument was derivable before IBM-2
designed `W_joint`. The IBM-2 scope note ("not claimed as a formal
entanglement witness") hedged correctly but did not derive the no-go, which
would have cost nothing and predicted this run's outcome in advance. The
standing rule this adds to the program's discipline: *before designing a
witness, derive what class of states can mimic it.* The ~15 s of QPU spent
here was not waste — the measured demonstration is far more communicable than
the theorem alone — but the order of operations was wrong.

## The sharpest irony, computed exactly

The history state's Schmidt decomposition across clock|system has
coefficients **exactly (½, ½) at both d=4 and d=8** — it is *maximally
entangled* for a qubit system. Four hardware runs measured a maximally
entangled state with observables that were provably blind to its
entanglement. The witnesses were never weak because the state was; they were
blind by construction.

## What actually stands, program-wide

Nothing measured is retracted. What each result *is* has been progressively
sharpened by the program's own adversarial controls:

| Result | Status after IBM-3 |
|---|---|
| Conditional evolution is classically reproducible (IBM-0, Gate 5) | **Stands, untouched** — a genuine hardware demonstration that the usual "time from entanglement" signal proves nothing quantum |
| Informational arrow is classically reproducible (IBM-1, arm 1B) | **Stands, untouched** |
| Witness decays as a power law in record overlap under clock decoherence, while conditional evolution survives (IBM-1, Gate 4) | **Stands**, re-scoped: it is a measured decoherence threshold for *clock coherence*, with apparent temporal dynamics surviving past it |
| d=2 structural null, dimensional scaling, cross-device replication (IBM-0) | **Stands** — as clock-coherence measurements |
| Local witness certifies clock coherence, not clock–system structure (IBM-2) | **Stands** |
| `W_joint` certifies coherence-plus-correlation, not entanglement (IBM-3) | **Established here** |
| Any measured observable certifies the Page–Wootters structure (clock–system *entanglement*) specifically | **Does not hold, and provably cannot, for any single-setting observable** |

The one genuinely quantum thing certified throughout is **clock coherence**
— the classical mixture demonstrably cannot reproduce the Fourier-basis
interference, and its engineered decoherence dynamics (IBM-1) are real
quantum physics. What is *not* certified is that the clock's quantumness is
*relational* — entangled with the system rather than local to the clock.

## The same wall, hit twice, in both papers

This is not the program's first encounter with this exact epistemic
structure. The sister OAT program (twisted-spin-ptm) recorded, in May:

- *"D-LinOSS cannot distinguish RTN [classical telegraph noise] from a
  6-mode quantum signal — the framework reads spectral morphology, not
  quantum structure per se"* (the adversarial-suite false positive), and
- *"Entanglement in OAT boundary states is not identifiable from PTM
  anisotropy alone"* — a single channel observable (`T_xx`) certifying less
  than it appeared to, resolved there by moving to the basin-volume
  observable `V_Q`, which samples **many Haar-random measurement settings**.

The pattern is identical: a single-setting observable (spectral fingerprint /
PTM element / clock-marginal TVD / joint TVD) never certifies quantum
structure; only measurement *diversity* does. Paper 1 paid for that lesson
with a retracted scrambling claim and bought its way out with `V_Q`. Paper 2
paid with IBM-2/IBM-3 and the exit is the same door:

## What would actually certify the Page–Wootters structure

A multi-setting **fidelity witness**. For the history state, Schmidt
coefficients (½, ½) give the standard bound:

```
F(ρ, |Ψ⟩) = ⟨Ψ|ρ|Ψ⟩ > λ_max = 0.5   ⟹   ρ is entangled across clock|system
```

`F` is estimable by direct fidelity estimation over a set of Pauli settings
(a few tens at d=4), and the program's measured attenuations (~0.8–0.9)
suggest a prepared history state would clear 0.5 with margin. That is a
concrete, standard, pre-registrable IBM-4 — the *sufficient* condition the
program has so far lacked — at an estimated cost comparable to IBM-2/IBM-3
combined.

**Update, same day: IBM-4 was run and the certification succeeded** —
F = 0.9419 (d=4) / 0.8829 (d=8) against the bound 0.5, with this document's
separable state and IBM-2's product state both correctly rejected
(F = 0.02–0.06). See `AQ_PAGE_WOOTTERS_IBM_4_RESULTS_2026-08-07.md`.

## Claim boundary

Unchanged at the outer edge (no claims about time in nature, quantum gravity,
or a realized Page–Wootters universe), and now tightened at the inner edge:
no result in IBM-0 through IBM-3 certifies clock–system entanglement, and
the program's own theorem shows none could have. What the program delivers
instead is a systematic, hardware-measured anatomy of what relational-time
observables do and do not certify — with every limitation found by our own
pre-registered adversarial controls rather than by a referee.

## Provenance

Backend `ibm_marrakesh`, 4 jobs, 2026-08-07T22:40Z. Job IDs in
`ibm3_results.json`. Capture before trial expiry (~2026-09-01):

```
python pw_ibm_provenance.py --results results_ibm3_ibm_marrakesh/ibm3_results.json --out results_ibm3_ibm_marrakesh/ibm3_provenance.json
```
