# AQ-PAGE-WOOTTERS-IBM-12 — What Shared Relational Time Costs

**Executed 2026-08-17 on `ibm_marrakesh`.** 1 job, 135 circuits, 3 qubits,
2 000 shots each. **All 6 pre-registered gates pass.**

A clock is a good Page–Wootters clock in proportion to its entanglement with
its **own** system — that is what makes it stationary and internally evolving.
It is a *synchronisable* clock in proportion to its entanglement with **another
clock**. Monogamy makes those compete. This run measures the exchange rate.

## Results

Three qubits: clock `A`, its system `Sₐ`, second clock `B`. A single
excitation-transfer angle `μ` moves `A`'s entanglement partner from `Sₐ` to `B`.
Full three-qubit tomography at each setting.

| μ | C(A:Sₐ) | C(A:B) | S(A:Sₐ) | S(A:B) |
|---|---|---|---|---|
| 0.0000 | **0.8980** | **0.0000** | 2.6812 | 0.1239 |
| 0.3927 | 0.8056 | 0.2141 | 2.4368 | 1.0545 |
| 0.7854 | 0.5156 | 0.5315 | 1.8060 | 1.8350 |
| 1.1781 | 0.2282 | 0.7716 | 1.0093 | 2.4146 |
| 1.5708 | **0.0000** | **0.9017** | 0.1022 | 2.6780 |

**Clock-quality vs synchronisability correlation `r = −0.9833`.**

**Both endpoints reach exactly zero.** A clock maximally entangled with its own
system has *no* measurable correlation with the second clock, and the converse
holds at the other end. That is the no-go — a perfect Page–Wootters clock is
uncorrelated with every other clock — measured rather than argued.

The CHSH columns cross cleanly: `2.68 → 0.10` on one pair while `0.12 → 2.68`
on the other. At the balance point **both sit at ≈1.8, below the classical
bound simultaneously**. Where the two clocks share time best, neither pair
violates Bell.

## The deficit, and the gate that could have manufactured a result

The saturation `C²(A:Sₐ) + C²(A:B) = 1` is **forced** for pure states by
Coffman–Kundu–Wootters with `τ_ABC = 0` and `ρ_A` maximally mixed. It is
asserted in preflight and is explicitly *not* the claim — measuring it would be
the IBM-6/IBM-8 mistake a third time. The contingent quantity is the **deficit**
that mixedness introduces, and whether it depends on *where* the entanglement
sits.

Raw deficits bow at the balanced point:

```
raw deficit:  +0.1935  +0.3051  +0.4516  +0.3526  +0.1869     spread 0.2647
```

**That bow is an estimator artifact, not physics.** Concurrence is
`max(0, λ₁−λ₂−λ₃−λ₄)`; noise pushes it down asymmetrically and hardest at
intermediate entanglement, so the deficit bows *even in pure simulation*. A gate
against the ideal `1.0` would have reported a discovery here.

So the null model is a **noise-matched Aer reference run through the same
estimator**, computed in-process before submission:

```
reference:    +0.2651  +0.3806  +0.4540  +0.4080  +0.2652
excess:       −0.0716  −0.0755  −0.0024  −0.0554  −0.0783
              spread 0.0760   against a 3σ bar of 0.2420
```

Against the reference the spread collapses by a factor of 3.5 and sits well
inside tolerance. **The trade-off structure survives; only the level
attenuates.**

**Every excess is negative.** Hardware outperformed its own noise model at all
five settings — the second consecutive run to do so (IBM-11 measured
attenuation 0.891 against a predicted 0.821), consistent with the four-hour-old
calibration both runs drew on.

## Post-hoc: the same structure appears on both pairs

Added after the run, from the archived counts, at zero QPU cost
(`hardware/pw_ibm12_endpoint_structure.py`). The reconstruction reproduces the
reported concurrences to four decimals at all five settings, which is what
licenses the rest.

The run measured *magnitudes*. It did not ask whether the correlation
**structure** at one endpoint is the same object as at the other. It is:

```
rho(A:Sₐ) at μ = 0    vs    rho(A:B) at μ = π/2
  fidelity          0.9852
  trace distance    0.0497
  concurrence       0.8980  vs  0.9017        (differ by 0.0037)
```

**The structure transfers essentially intact.** Both endpoints sit at
`F ≈ 0.945` with `|Φ⁺⟩` in the raw computational basis, both leave the partner
in near-antipodal conditional states (178.1° and 176.1° between the two
outcomes), and the conditional Bloch vectors agree between endpoints to
`0.033` and `0.107`. The clock-marginal witness reads `0.0055` and `0.0186` on
the two — near zero on both, as the complementarity relation requires of a
maximally entangled pair, which is an independent cross-check against IBM-11
using different circuits on a different family.

**The degeneracy this does not escape, stated plainly.** At `d = 2` the
Page–Wootters history state `(1/√2)(|0⟩|ψ₀⟩ + |1⟩U|ψ₀⟩)` **is** a Bell pair, so
"both endpoints are history states" is nearly vacuous — every maximally
entangled two-qubit state qualifies. More importantly, **no `U` appears
anywhere in this run.** The circuit is `H(A); CX(A,Sₐ); CRY(2μ, Sₐ, B);
CX(B,Sₐ)`; there is no evolution operator, no clock dimension above two, and no
conditional-evolution sequence to fit. The 178° between conditional states is
what a Bell pair does, **not** evidence of a system evolving.

So what is established is a **static structural equivalence**: whatever the
first pair was, the second pair becomes, to within 1.5% in fidelity. What is
*not* established is that either pair carries temporal content. Testing that
needs `d > 2`, a real `U` on both systems, and the conditional sequence
`⟨X_S|t⟩` read against *each* clock — none of which this run has.

## Honest ledger

**The relation is not new; the curve is.** Coffman–Kundu–Wootters monogamy is
from 2000. The obstruction for Page–Wootters clocks specifically is stated by
[Kuypers & Rijavec, *Measuring time in a timeless universe*](https://journals.aps.org/prd/pdf/10.1103/qfns-48vq)
(Phys. Rev. D **112**, 063544, 2025), who resolve it by adding an interaction so
the timer can read the clock. What appears not to have been done is measuring
the trade-off as a continuous curve.

**This does not discriminate between generative substrates.** The saturation
holds for *any* pure state — an oscillatory-recurrence construction, an
OAT chain, a randomly compiled circuit — so the result is substrate-blind and
cannot be evidence for a common generative structure underlying different
paradigms. Stated because that reading is tempting and wrong.

**Nothing here emits time.** The states are compiled by externally timed gates,
and the clock/system split is imposed rather than derived. The endpoints
measured at exactly zero are a statement about correlation between engineered
registers, not about simultaneity in nature.

**Concurrence from tomography is a biased estimator**, which is the whole reason
for the reference curve. Absolute deficits should not be quoted as physical
attenuation; only the excess over the matched reference is interpretable.

**Three preflight assertions fired before any shot was spent:** a Qiskit
little-endian reshape error that put `C(A:Sₐ) = 0` at `μ = 0` (the same trap
IBM-4's Schmidt assertion caught), a `1e-9` tolerance tighter than the
concurrence eigensolve's own float noise (`−1.4e-09` at `μ = 3π/8`), and the
estimator-bias gate above.

## What this establishes

> Shared relational time is purchased from the entanglement that makes each
> local clock work, and the exchange rate is measurable. A clock maximally
> entangled with its own system has zero measurable correlation with any other
> clock; the hardware curve traces the full continuum between that limit and
> perfect synchronisation at `r = −0.9833`, and the trade-off structure survives
> decoherence with only its level attenuated.

## Provenance

`ibm_marrakesh`, 2026-08-17, 1 job `da1ra8m3kjvs7387430g`, qubits `[0, 1, 2]`,
135 circuits at 2 000 shots.

```
python pw_ibm_provenance.py --results results_ibm12_ibm_marrakesh/ibm12_results.json --out results_ibm12_ibm_marrakesh/ibm12_provenance.json
python pw_ibm_fetch_counts.py --results results_ibm12_ibm_marrakesh/ibm12_results.json
```
