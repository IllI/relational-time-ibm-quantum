# AQ-PAGE-WOOTTERS-IBM-13 — Two clocks, each with its own system

**Proposal. Not run.** Predictions executable at
[`theory/verify_two_clock_prediction.py`](../theory/verify_two_clock_prediction.py) —
numpy only, no QPU, under a second.

---

## The gap this fills

Every run in this programme has used **one** clock. The multi-clock
Page–Wootters literature is theoretically active — clock switching, frame
dependence, temporal delocalization — but no published hardware experiment
appears to have simultaneously used **two genuine `d > 2` clocks**, attached an
**independent evolving system to each**, and verified that the conditional
dynamics appears cleanly when read against **either**.

IBM-12 does not close this. Its post-hoc analysis shows the correlation
structure transfers intact between pairs (`F = 0.9852`), but at `d = 2` the
history state *is* a Bell pair and **no `U` appears anywhere in that circuit**.
What was measured is a static structural equivalence, not temporal content.

## What the derivation already settled — and what it killed

The obvious design is **one system driven by two clocks**. It is dead, and it
died on paper:

```
 nu     F(A:S)   bound_A    F(B:S)   bound_B    both clear?
 0.00   1.000000 0.500000   0.500000 1.000000   False
 0.25   0.876709 0.659095   0.468962 0.953064   False
 0.50   0.625000 0.826641   0.625000 0.826641   False
 0.75   0.468962 0.953064   0.876709 0.659095   False
 1.00   0.500000 1.000000   1.000000 0.500000   False
```

**No setting certifies both.** The shared-system design restates monogamy and
would be IBM-6/IBM-8 a third time. One derivation, zero shots — and it is what
forces the two-system design below.

> **A bound applied outside its domain flipped this verdict once already.**
> The first pass used `λ_max = ½` as a constant. It is not: `λ_max` is the
> largest squared Schmidt coefficient of *whatever target is used*, and the
> rate-matched target degenerates toward a product state as the rate falls,
> where `λ_max → 1` and the witness certifies nothing. With the constant bound,
> `ν = 0.5` appeared to certify both at `F = 0.625`. With the correct
> per-setting bound of `0.827` it fails by `0.20`. Same class of error as
> IBM-7's failed gate and IBM-11's first gate 7.

## The design

Six qubits. Clock `A` and clock `B` are two-qubit registers (`d = 4`); each
drives its **own** system qubit through `U = P(2π/d)`, which satisfies
`U^d = +I` exactly (IBM-5's correction). A single parameter `ν` couples the two
**clocks** — not the systems — from independent to maximally correlated.

At every `ν` both clocks remain uniform-reading clocks, so neither is degraded
into a non-clock by the sweep. Measured at each setting:

- **`F(A:Sₐ)` and `F(B:S_b)`** — multi-setting fidelity witnesses against
  `λ_max`, the IBM-4/IBM-10 standard.
- **`V(Sₐ|A)`** — conditional-evolution amplitude of `Sₐ` read against its
  **own** clock.
- **`V(Sₐ|B)`** — the same system read against the **foreign** clock.
- **`I(A:B)`** — clock–clock mutual information, the coupling actually achieved.

## Exact predictions

```
 nu   I(A:B)   F(A:Sa) clears   F(B:Sb) clears   V(Sa|A)  V(Sa|B)  rate
 0.00  0.0000   1.0000  True     1.0000  True     1.0000   0.0000   1.000
 0.25  0.5051   0.9423  True     0.9423  True     1.0000   0.3077   1.000
 0.50  1.4750   0.7500  True     0.7500  True     1.0000   0.6667   1.000
 0.75  2.2436   0.4808  False    0.4808  False    1.0000   0.9231   1.000
 1.00  2.5000   0.2500  False    0.2500  False    1.0000   1.0000   1.000
```

**Both pairs stay certified at `ν ≤ 0.5`, and fail by `ν = 0.75`. The crossover
is the measurable.** At `ν = 0.5` the foreign clock reads the other's system at
`V = 0.667` while *both* pairs remain certified history states — two good
clocks that can partly read each other.

**This is not the correlation budget.** IBM-11 and IBM-12 measured trade-offs
summing to exactly 1. This one does not:

```
 nu     F(A:Sa)   V(Sa|B)    F + V^2
 0.00   1.0000    0.0000     1.0000
 0.50   0.7500    0.6667     1.1944
 0.75   0.4808    0.9231     1.3328
 1.00   0.2500    1.0000     1.2500
```

A weaker no-go than the correlation budget — which is exactly why it is worth
measuring. Where the budget says *never*, this says *up to a point*, and the
point is empirical.

## Pre-registered gates

1. **Non-vacuity (must pass first).** `I(A:B)` must actually rise across the
   sweep, and `V(Sₐ|B)` must rise with it. If the clocks are not measurably
   coupled, every later gate is meaningless.
2. **Own-clock invariance.** `V(Sₐ|A)` is flat at `1.000` by construction, so
   any measured drift is instrumental. This is a **calibration channel, not a
   result**, and is reported as such.
3. **Both-certified window.** At least one setting has `F(A:Sₐ) > λ_max` **and**
   `F(B:S_b) > λ_max`, with bootstrap 95% lower limits clearing the bound
   outright — the IBM-4 standard, not point estimates.
4. **Crossover located.** The largest `ν` clearing gate 3 is identified, with
   the next setting failing beyond bootstrap error.
5. **Separable mimic — the control that stops the overclaim.** Specified in
   full below, because this is the last place the programme's recurring
   mistake can still hide.
6. **Noise-matched reference.** All margins evaluated as excess over an Aer
   reference at the live calibration, computed in-process before submission —
   the IBM-11/IBM-12 pattern, never against ideal values.

## Gate 5 in full

`V(Sₐ|B)` is read from a **single product-basis setting** (clock `B` in `Z`,
system `Sₐ` in `X`), so IBM-3's theorem applies directly: it is reproducible by
a separable state and certifies *nothing* on its own. Seven conditions govern
this arm, and all of them bind before submission.

**1 — The mimic is derived, never fitted.** It is constructed from the *ideal*
prediction at each `ν`, not from measured data:

```
rho_mimic(nu) = SUM_t  p(t) |t><t|_B  (x)  sigma_t(S_A),   sigma_t = (I + m_t X)/2
```

with `p(t)` the ideal clock-`B` reading marginal (verified uniform at `1/d` at
every `ν`, not assumed) and `m_t` the ideal conditional `⟨X_Sₐ | t_B = t⟩`. Zero
clock–system coherence by construction, diagonal in the reading basis. Because
nothing in it depends on the run, **it is locked before the job is submitted.**
Measuring first and then hunting for a matching separable state would be
cherry-picking.

**2 — Match the whole distribution, not the scalar.** A separable state can
match one number and fail the probability vector. This one does not:

```
 nu    V(Sa|B) hist   V(Sa|B) mimic   TVD(full 8-outcome dist)
 0.00     0.000000        0.000000        6.94e-18
 0.25     0.307692        0.307692        2.78e-17
 0.50     0.666667        0.666667        6.59e-17
 0.75     0.923077        0.923077        1.30e-17
 1.00     1.000000        1.000000        4.16e-17
```

Exact to machine precision across all eight outcomes, which is the statement
IBM-3's theorem actually makes. Reported quantities are the scalar `V`, the
full-distribution TVD, **and both for the history-state arm.**

**3 — Same noise-matched reference for both arms.** The mimic's excess is
evaluated against the *identical* calibrated Aer model used for the fidelity
witnesses. Comparing the mimic to ideal theory while comparing the history arm
to noisy simulation would reintroduce precisely the estimator asymmetry that
IBM-11 and IBM-12 had to correct for.

**4 — The pass/fail criterion, pre-registered numerically.** From a Monte Carlo
of two independent 2 000-shot draws from the *same* distribution — the null
that mimic and history arm agree — the pooled floor is `mean 0.03118,
sd 0.00962`:

> **Gate 5 passes if `TVD < 0.061` at every `ν`**, 3σ above the
> same-distribution shot-noise floor. If it passes, the foreign-clock amplitude
> is declared **non-certifying on its own**. If it fails, the run remains valid
> and the foreign-clock claim is **withdrawn** — the fidelity witnesses stand
> independently of this arm.

**5 — Depth matched.** The mimic circuit is padded to the same two-qubit gate
count as the history-state preparation, including any SWAPs routing inserts.
Depth mismatch was among the confounders behind IBM-6/IBM-8; matching it
removes the excuse.

**6 — Reported as a negative control.** The results document must read:

> *Gate 5: the separable mimic reproduces `V(Sₐ|B)` to within shot noise
> (TVD = …, threshold 0.061). Therefore the foreign-clock amplitude, while
> rising with `ν`, does not by itself certify non-classical structure.
> Certification continues to rest only on the multi-setting fidelity
> witnesses.*

Not as a finding. It is the third instance of a theorem this programme already
proved, and its job is to prevent a single-basis visibility from being read as
evidence of quantum relational structure.

**7 — Run at every `ν`, not one point.** Same settings, only a different
classical mixture, so the cost is one extra arm rather than one extra run. A
single `ν` would leave open that the mimic works only at that coupling; the
full sweep shows the foreign-clock signal is classically reproducible
*wherever it appears*, which closes the residual loophole.

## Feasibility, honestly

**This is the largest circuit the programme has proposed, and it may not
survive.** Roughly 12 CX before routing: two clock–clock couplings and four
controlled phases. Each system must reach both qubits of its own clock, and the
clock registers must reach each other — more connectivity than a heavy-hex
neighbourhood supplies, so SWAP insertion is likely.

The bound to respect is Paper 1's: its `N = 6` extension failed decisively
under the calibrated noise model at 18 CX, `R² = −2.0`, with the null landing at
21σ instead of ~0. **That bound was established at zero shot cost, and this run
must clear the same check before submission** — transpiled two-qubit depth
verified against the live coupling map, and the full gate set run against a
calibrated Aer model. If the noisy simulator cannot certify at *any* `ν`, the
run is not submitted and the negative feasibility bound is reported instead.

Circuit budget: two fidelity witnesses (~20 settings), the conditional arm, and
the separable control at **every** `ν` per Gate 5.7, across 5 settings of `ν` —
roughly 200–220 circuits at 2 000 shots, one job. Comparable to IBM-12's 135.
The mimic arm is cheap because it reuses the same measurement settings and
changes only the classical mixture prepared.

**Fallback if routing is prohibitive:** `d = 4` for clock `A` and `d = 2` for
clock `B` (5 qubits, ~8 CX). This weakens the headline claim, since the gap
specifically concerns two clocks with `d > 2`, and should be reported as a
partial result rather than the experiment.

## Both outcomes are informative

**If a both-certified window exists**, this is the first hardware
demonstration of two simultaneously certified Page–Wootters clocks with `d > 2`
and independent systems, plus a measured bound on how much mutual readability
they can afford. That is the shared-time question in its sharpest experimental
form, and the answer is a bounded yes.

**If nothing certifies at any `ν`**, the result is a decoherence bound on
multi-clock relational structure at this circuit depth — reportable, and it
tells the next attempt to buy shallower preparation rather than more shots.

## What it would still not show

The clocks and their evolution are **externally programmed**, as everywhere in
this programme. Two clocks agreeing about a system they were each independently
wired to track is not a shared time in an observer-free sense. The
clock/system splits are imposed, not derived, and the certification remains
device-dependent — limitations 1 and 5, neither closed by this run.

It also says nothing about the **geometric-phase** question. That concerns
whether a non-magnitude quantity escapes the correlation budget and is a
separate proposal, held in the synthesis repository
([relational-entanglement-network](https://github.com/IllI/relational-entanglement-network)).
This run and that one are independent and can be ordered either way; this one
has the cleaner readout and the confirmed literature gap.
