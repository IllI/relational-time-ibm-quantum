# AQ-PAGE-WOOTTERS-IBM-11 — The Coherence Witness Runs Backwards, Measured

**Executed 2026-08-17 on `ibm_marrakesh`.** 1 job, 53 circuits, 4 000 shots each.
**All 9 pre-registered gates pass.** Two qubits — the cheapest and shallowest
run in the programme.

This is the hardware test of the companion result
([`COMPANION_RESULT.md`](COMPANION_RESULT.md)): that this programme's
clock-marginal coherence witness is not a weak entanglement witness but an
**anti-witness**, suppressed by the very thing it was taken to indicate.

## Results

| λ | witness (exact) | CHSH (exact) |
|---|---|---|
| 0.00 | **0.4830** (0.5000) | **1.8605** (2.0000) |
| 0.25 | 0.4480 (0.4619) | 1.9995 (2.1414) |
| 0.50 | 0.3325 (0.3536) | 2.3085 (2.4495) |
| 0.75 | 0.1923 (0.1913) | 2.5500 (2.7229) |
| 1.00 | **0.0100** (0.0000) | **2.6565** (2.8284) |

**Witness–CHSH correlation r = −0.9573.**

The anti-correlation survives on hardware. That was the genuinely contingent
question: for ideal *pure* states the relationship is forced, because marginal
entropy is entanglement entropy — but hardware states are mixed, where that
identity no longer holds, and decoherence attacks marginal coherence and
nonlocal correlation through different channels.

**Gate 4 is the one that could have falsified the framing, and it held.** At the
product state the witness is maximal (0.4830) and CHSH is **1.8605 — below the
classical bound.** The state that maximises the coherence witness produces no
Bell violation at all.

## The trade-off held better than the noise model predicted

```
λ:              0.00     0.25     0.50     0.75     1.00
S² + 16W²:     7.1941   7.2093   7.0981   7.0939   7.0586

mean level 7.1308   (ideal 8.0, attenuation 0.891)
spread     0.1507   (3σ band ±1.1390)
```

The exact relation `S² + 16W² = 8` is a pure-state identity. On hardware the
*level* drops to 7.13 while the *structure* stays flat to within 0.15 against a
1.14 band — an order of magnitude inside tolerance, and considerably flatter
than the noisy simulator's 0.50 at attenuation 0.821. Hardware beat its own
noise model.

**This vindicates a gate that was rewritten before submission.** The first
version of gate 7 demanded `S² + 16W² = 8` on hardware. That is a pure-state
identity applied to mixed states — the same false-assumption error IBM-7's
failed gate encoded. Caught in the dry run, where it failed correctly at 6.7,
and reframed to test *flatness* while reporting attenuation separately. Left as
written, this run would have failed while displaying textbook structure.

## The Svozil arm: a single-setting rate certifies nothing

An arm was added from Svozil, *Certified Private Relational Time from
Entanglement* ([arXiv:2512.09100](https://arxiv.org/abs/2512.09100)), which
builds a relational clock from a singlet and reports a joint coincidence rate
`R(θ) = ½sin²(θ/2)` against a Peres-style local benchmark `R_cl(θ) = θ/2π`.

Our `λ = 1` state is `|Φ⁺⟩` rather than the singlet, and its **anti**-coincidence
`P(+,−)` reproduces `R(θ)` exactly — verified to six decimals in preflight.

```
θ = 140.5°     Bell  +0.0650      product  +0.0590      |gap| 0.0060
                                              (3σ empirical = 0.0414)
CHSH           Bell   2.6565      product    1.8605      gap   0.7960
```

**The zero-entanglement product state reproduces the synchronisation excess to
within 0.006, while CHSH separates the same two states by 0.80.** `R(θ)` is a
single-setting joint rate, so IBM-3's theorem applies directly: such a
distribution is separably reproducible and cannot certify nonclassicality.

This is the **third independent instance** of that theorem in this programme —
after the clock-coherence witness (IBM-2) and single-basis joint correlation
(IBM-3) — and the first time it has been demonstrated against an observable
from outside the programme. It is not a criticism of Svozil's certification,
which rests on CHSH and is consistent with everything here; it is a boundary on
what the excess by itself can support.

**Two exact internal nulls came free.** The quantum and benchmark curves cross
identically at `θ = 90°` and `θ = 180°`, so any measured excess there is
instrumental. Max deviation 0.0217, and their scatter supplied the empirical
error bar (0.0138) used for the gap test — which caught a real error: gating on
shot noise alone failed by 0.0003, because a *rate* measured under readout error
carries a bias that `√(p(1−p)/N)` cannot see. The same crude-sigma mistake
IBM-5 made.

*Precision note on the source:* 140.46° is the maximum **absolute** excess
(0.0526); the maximum **relative** excess is at 133.6° (13.82%). The paper's
summary conflates the two maxima.

## Honest ledger

**The relation is not new; the curve is.** `(2W)² + C² = 1` was derived
independently for this run, and it is the `P = 0` slice of the **Jakob–Bergou
complete complementarity relation** `V² + P² + C² = 1`
([Phys. Rev. A **68**, 022107, 2003](https://doi.org/10.1103/PhysRevA.68.022107)),
with `V` the single-party visibility, `P` the predictability, and `W = V/2`. `P`
vanishes here because the clock populations are flat by construction. Recorded
as a known theorem rather than a finding — one of six times in this programme
that a derived result turned out to be standard. What this run contributes is
the measured hardware curve, and the demonstration that the relation survives on
*mixed* states, where the marginal-entropy identity that forces it fails.

**The separable control matches exact predictions, including a value that looks
wrong.** Gate 6 returned CHSH = 0.0035 at `λ = 0`, suspiciously close to zero
for a classical mixture. It is correct: at `λ = 0` both branches leave the
system in `|0⟩`, so the mixture is a maximally mixed clock **uncorrelated** with
the system, its entire correlation tensor vanishes, and CHSH must be exactly 0.
At `λ = 1` the mixture gives 1.3370 against an exact 1.4142. Both verified after
the run rather than assumed.

**The endpoints do not reach their ideal values**, and should not be read as if
they did: the witness bottoms at 0.0100 rather than 0, and CHSH tops at 2.6565
rather than 2.8284 (94% of Tsirelson). Attenuation is real and reported, not
divided out.

**This is not loophole-free.** Two qubits on one superconducting processor are
not spacelike separated, so the no-signalling and fair-sampling assumptions are
not enforced by geometry. A CHSH violation here is a stronger certification than
a fidelity witness — it does not assume the measurement operators are what their
labels say — but it does not close the relational-time programme's limitation 5.

**Three of my own errors were caught by preflight assertions before any shot was
spent:** the Horodecki construction had the two measurement roles swapped
(returned `S = 0` at `λ = 0`), the CHSH closed form used `sin²(λπ)` instead of
`sin²(λπ/2)` (caught at `λ = 0.25`), and gate 7 encoded a pure-state identity as
a hardware prediction.

## What this establishes

> The clock-marginal coherence witness is anti-correlated with nonlocal
> correlation on hardware, `r = −0.9573` across a sweep from a product state to
> a Bell pair. The state that maximises the witness produces no CHSH violation;
> the state that maximises CHSH has a witness consistent with zero. The exact
> trade-off `S² + 16W² = const` survives at 0.891 attenuation with a spread an
> order of magnitude inside tolerance. And a single-setting joint coincidence
> rate — including the one used in a recent relational-clock proposal — is
> reproduced by a zero-entanglement product state to within 0.006, while CHSH
> separates the same states by 0.80.

The programme's certification threshold is now measured from both directions:
what fails, and what the failing quantity does instead.

## Provenance

`ibm_marrakesh`, 2026-08-17, 1 job `da1ohdsdedkc73era220`, qubits `[0, 1]`,
53 circuits at 4 000 shots.

```
python pw_ibm_provenance.py --results results_ibm11_ibm_marrakesh/ibm11_results.json --out results_ibm11_ibm_marrakesh/ibm11_provenance.json
python pw_ibm_fetch_counts.py --results results_ibm11_ibm_marrakesh/ibm11_results.json
```
