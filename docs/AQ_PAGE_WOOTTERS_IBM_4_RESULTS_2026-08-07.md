# AQ-PAGE-WOOTTERS-IBM-4 — Entanglement Certified: The Sufficient Condition, Measured

**Executed 2026-08-07 on `ibm_marrakesh`.** 8 jobs, 120 circuits, 2000 shots
each. All 6 pre-registered gates pass. Pre-registration (with the derived
bound and exact predictions) filed before submission:
`results/hardware/ibm4/ibm4_prereg.json`.

This run closes the arc that IBM-2 and IBM-3 opened. Those runs proved — by
adversarial measurement, then by a two-line theorem — that **no functional of
a single measurement setting can certify clock–system entanglement**: a
separable diagonal mixture reproduces any single-product-basis distribution
exactly. The escape is measurement *diversity*. This run executes it.

## The witness

The history state's Schmidt coefficients across clock|system are exactly
**(½, ½)** at both d = 4 and d = 8 (a maximally entangled clock–qubit state),
so the standard fidelity witness (Bourennane et al. 2004; Gühne & Tóth 2009)
gives a sharp, derived-in-advance bound:

```
F(ρ, |Ψ⟩) = ⟨Ψ|ρ|Ψ⟩ > λ_max = 0.5   ⟹   ρ entangled across clock|system
```

`F` is estimated as `(1/2ⁿ) Σ_P ⟨Ψ|P|Ψ⟩⟨P⟩_ρ` over the nonzero Pauli terms of
`|Ψ⟩⟨Ψ|`, grouped by greedy qubit-wise-commuting set cover into **10
measurement settings at d=4** (18 Paulis; 27 exhaustive) and **20 at d=8**
(54 Paulis; 81 exhaustive). Ten to twenty incompatible bases is precisely
what makes the diagonal-mimic construction impossible — this observable is
not a functional of any single distribution.

## Hardware results

| | d=4 | d=8 | exact |
|---|---|---|---|
| **F(history)** | **0.9419 — CERTIFIED** | **0.8829 — CERTIFIED** | 1.0000 |
| F(separable) — the state that beat `W_joint` in IBM-3 | 0.0598 ✗ | 0.0348 ✗ | 0.0625 / 0.0322 |
| F(product) — the state that beat the local witness in IBM-2 | 0.0481 ✗ | 0.0207 ✗ | 0.0625 / 0.0156 |
| margin above λ_max = 0.5 | **+0.4419** | **+0.3829** | +0.5 |

Three things worth noting beyond the headline:

1. **The adversarial controls are not merely "below bound" — they are
   measured near their exact values** (0.048–0.060 vs 0.0625; 0.021–0.035 vs
   0.016–0.032). The witness behaves quantitatively, not just directionally,
   on the very states engineered to break its predecessors.
2. **The history-state fidelity (0.94 / 0.88) is a direct estimate of
   prepared-state quality**, and it is *higher* than the witness attenuations
   seen in IBM-0/IBM-1 (~0.87). The fidelity circuits contain no inverse QFT —
   only local basis rotations before readout — so state preparation, not
   readout circuitry, is the limiting factor. This is consistent with the
   cos-attenuation ≈ 0.90 measured for this backend across both papers.
3. **Statistical margin.** Error bars were not among the pre-registered gates;
   an estimate treating per-Pauli estimators as independent (std ≤ 1/√2000 per
   ⟨P⟩; `Σ c_P² = 2ⁿ` for a pure target, giving std(F) ≲ 0.0224/√2ⁿ ≈
   0.006–0.008) puts the margins at very roughly 50σ. Shared-setting
   covariances make this an estimate rather than a strict bound; a bootstrap
   over raw counts belongs in the paper's analysis pass and the counts are
   archived for it.

## Process note: the assertion caught a real bug before hardware

Per the standing rule IBM-3 added ("derive what can mimic a witness before
designing the run"), this script derives λ_max and **asserts it equals 0.5
before contacting any backend**. On the first dry run the assertion fired:
the Schmidt split had been computed with `psi.reshape(d, 2)`, but Qiskit
orders the system qubit as the *highest* index (`index = z·d + t`), so the
correct split is `reshape(2, d)`. The wrong version mixed the system bit into
the clock index and reported λ_max = 0.8536 — a fabricated bound that would
have rendered the certification meaningless had it reached hardware. Fixed,
verified against the independent closed-form calculation, recorded inline.
Theorem-first paid for itself on its first outing.

## The completed arc

| Run | Question | Answer |
|---|---|---|
| IBM-0 | Does a classical clock reproduce the coherence witness? | No (and conditional evolution: yes) |
| IBM-1 | Does the witness have a decoherence threshold? | Yes — power law in record overlap; apparent time survives past it |
| IBM-2 | Does the witness certify clock–system structure? | **No** — a zero-entanglement product state scores 2–4× higher |
| IBM-3 | Does the joint-readout fix certify entanglement? | **No** — a separable mixture scores 1.7× higher; no single-setting observable can |
| **IBM-4** | **Can entanglement be certified at all?** | **Yes — F = 0.94/0.88 > 0.5, with both adversarial states correctly rejected** |

Necessary → insufficient → insufficient → **sufficient, measured** — with
every limitation found by this program's own pre-registered adversarial
controls, and the final certification tested against the exact states that
broke the earlier witnesses.

## Where the method came from: TPUs and D-LinOSS

This run is the terminal point of a methodology that was built somewhere
else entirely — on Google TPU Research Cloud hardware (grant window
2026-04-21 → 2026-06-21, extended one month on the time-emergence thesis),
with the D-LinOSS state-space model as both instrument and object lesson.
The lineage is concrete, not ceremonial:

1. **The hypothesis is a TPU result.** The synthetic Page–Wootters program
   (~20 preregistered TPU runs) established that relational time is
   recoverable only from *entropy-bearing, irreversible* histories, and that
   recovery survives as a global path even where local clock records are
   non-orthogonal. IBM-1's clock-decoherence sweep — degrade the records,
   watch what survives — is that finding transposed to hardware; the
   clock-marginal off-diagonals measured throughout ARE the record-overlap
   quantity the TPU runs characterized numerically.

2. **D-LinOSS's failures pointed at the right variables, twice.** In the TPU
   phase, the event-damped D-LinOSS (the grant's "state-space model damped by
   physical constraints") succeeded on synthetic histories only when damping
   was driven by entropy/event structure — motivating the decoherence-as-
   independent-variable design. In IBM-1's Gate 0, the *entanglement-damped*
   D-LinOSS architecture lost to a stationary one at every grid density, and
   that structured loss is what exposed the published exponential-in-
   entanglement law as the wrong functional form, leading to the
   power-law-in-record-overlap prediction that hardware then confirmed. Both
   times the model functioned as a hypothesis test whose *negative* carried
   the information.

3. **The certification standard itself is a D-LinOSS lesson.** The sister OAT
   program's adversarial suite found (May 2026) that D-LinOSS classified
   classical telegraph noise as a multi-mode quantum signal — "the framework
   reads spectral morphology, not quantum structure per se" — and separately
   that entanglement in OAT boundary states "is not identifiable from PTM
   anisotropy alone," which that program resolved with the basin-volume
   observable V_Q over *Haar-random measurement settings*. IBM-2/IBM-3
   rediscovered the identical wall for relational-time witnesses, and IBM-4's
   multi-setting fidelity witness walks through the identical door. The
   program-wide through-line, learned first from D-LinOSS on TPUs:
   **single-setting observables never certify quantum structure; measurement
   diversity does.**

4. **The discipline was forged on TPUs and executed on QPUs.** Preregistration
   before submission, frozen operators, adversarial controls designed to
   break one's own result, exact-prediction-first dry runs, and honest
   withdrawal of any claim the committed data doesn't support — all of it was
   developed across the TPU simulation campaigns, where iteration was cheap,
   and then applied unchanged on hardware, where it caught three wrong
   circuits (OAT), a Fourier-basis bug (IBM-0), and the Schmidt-reshape bug
   (this run) before any of them could contaminate a result.

The TPUs were the sandbox in which the hypothesis and the epistemic standard
were built; the QPU runs are that standard, executed. Neither paper exists
without that pipeline.

## Claim boundary

**Now claimable:** clock–system entanglement of the engineered Page–Wootters
history state is certified on superconducting hardware by a multi-setting
fidelity witness (F = 0.9419/0.8829 > λ_max = 0.5), with the two adversarial
states that defeat all single-setting witnesses correctly rejected by the
same measurement.

**Still not claimable, unchanged:** that time in nature is emergent; any test
of quantum gravity or the Wheeler–DeWitt equation; a realized physical
Page–Wootters universe. The state is engineered; the clock is 2–3 qubits.
What is now complete is the *anatomy*: what each relational-time observable
certifies, what it cannot certify, why, and what certification actually
requires.

## Provenance

Backend `ibm_marrakesh`, 8 jobs, 2026-08-07T22:54Z. Job IDs in
`ibm4_results.json`. Capture before trial expiry (~2026-09-01):

```
python pw_ibm_provenance.py --results results_ibm4_ibm_marrakesh/ibm4_results.json --out results_ibm4_ibm_marrakesh/ibm4_provenance.json
```
