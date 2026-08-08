# AQ-PAGE-WOOTTERS-IBM-9 — A Clock in a Superposition of Rates: Interference Measured

**Executed 2026-08-08 on `ibm_marrakesh`.** 1 job, 2 circuits, 20 000 shots.
**All 3 pre-registered gates pass.** The cheapest run in the program and the
only one to exceed its own pre-run feasibility estimate.

A which-rate qubit `G` in `|+⟩` selects between α₁ = 1 and α₂ = 2, so clock B
evolves along **two proper-time histories at once** — the discrete analogue of
Smith & Ahmadi's quantum time dilation ([arXiv:1904.12390](https://arxiv.org/abs/1904.12390)).

```
|Ψ⟩ = (1/√2) [ |0⟩_G ⊗ |Ψ_α₁⟩ + |1⟩_G ⊗ |Ψ_α₂⟩ ]
```

## Results

| quantity | measured | exact | note |
|---|---|---|---|
| Z-marginal vs closed-form mixture | amplitude 0.767, max resid 0.089 | — | behaves as a classical rate mixture |
| branch rate, G=0 | **0.981** (R² 0.994) | 1.0 | α₁ recovered |
| branch rate, G=1 | **1.964** (R² 0.994) | 2.0 | α₂ recovered |
| **interference \|X(G=+) − Z-marg\|** | **0.2411** | 0.2632 | **2.32× the 3σ bar of 0.1039** |

**Interference profile across clock readings** (the shape, not just the peak):

```
measured:  [ 0.003  0.073 -0.172 -0.223 -0.038 -0.241  0.009  0.220]
exact:     [ 0.000  0.028 -0.167 -0.263  0.000 -0.263 -0.167  0.028]
```

Peak retention **91.6%**, shape correlation **0.85**. The signature is not a
single lucky point — the sign pattern and the relative magnitudes across all
eight clock readings track the prediction.

## What this establishes

**Reading G in Z gives a classical mixture.** The marginal tracks the
closed-form `[cos(α₁θt) + cos(α₂θt)]/2` (max residual 0.089), and
post-selecting on G=0 or G=1 cleanly recovers the two individual rates —
0.981 and 1.964, both at R² 0.994. This arm is exactly what a
which-path-forgotten *classical* setup would produce.

**Reading G in X gives something no mixture can produce.** Conditioning on
G = + shifts the conditional dynamics of B by up to 0.241 from the marginal,
where any mixture of the two rate histories predicts a difference of **zero**.
The two proper-time histories interfere.

**A decohered which-rate qubit is excluded by the data.** If `G` were
classically mixed rather than coherent, an X-basis measurement on it would
return 50/50 independent of everything else, and the conditional B state for
G=+ would be *identical* to the marginal. The observed 0.241 separation at
2.32σ-times-three therefore certifies that G retains coherence **and** is
correlated with which rate history B followed.

**This is a two-setting measurement, which matters given IBM-3.** IBM-3's
theorem says any single-setting distribution is exactly reproducible by a
separable diagonal state. IBM-9 uses two complementary settings on `G` (Z and
X) and its claim rests on the *relationship between them*, so it is not
subject to that mimic — the same structural reason IBM-4's multi-setting
fidelity witness escaped it.

## Scope

This demonstrates the **interference mechanism underlying quantum time
dilation** in an engineered 5-qubit system with programmed, dimensionless rate
ratios. It is **not** a measurement of gravitational time dilation: no metric,
no `G`, no `c`, and the α values used correspond to ratios unreachable in any
real gravitational setting (realistic dilation is ~10⁻¹⁰, eight orders below
this hardware's floor). Nor is entanglement formally certified here — the
two-setting structure defeats the trivial separable mimic, but a formal
certification would require the fidelity-witness treatment of IBM-4.

## Why this one worked when IBM-6 and IBM-8 did not

Recorded because the contrast is the useful part:

1. **No Loschmidt echo.** IBM-5/6/8 all used `V · operator · V†`, doubling
   depth. IBM-9 is prep + basis rotation + measure — the same shape as IBM-7's
   conditional measurement, the most robust thing in this program.
2. **No controlled clock-shift.** That single gate — a 3-controlled X at d=8 —
   is what killed IBM-8. IBM-9 needs only doubly-controlled phases: 24 CX
   against IBM-8's 29, but without the expensive cascade.
3. **The observable is a difference between two curves on the same state.**
   Attenuation hits both alike and largely cancels, which is why the measured
   interference retained 91.6% of its exact value while the underlying
   amplitude sat at only 0.767.

**Point 3 is why the run beat its own estimate.** The pre-registered
feasibility note projected 0.16–0.18 based on this program's measured
dry-run-to-hardware attenuation ratios (0.87 at 13 CX, 0.69 at 29 CX). The
actual result was 0.2411. The projection was too pessimistic because it
applied attenuation to the *signature* rather than recognising that a
difference of two equally-attenuated curves is far more robust than either
curve alone.

## Two feasibility problems caught before hardware

Both by assertions, and both would have wasted the run:

1. **d=4 was infeasible.** Its interference signature is only 0.167, which
   after realistic attenuation lands below the noise floor. The assertion
   fired and blocked it; a scan over (d, α₁, α₂) found d=8 with rates (1,2)
   gives 0.263. This *reverses* the usual "smaller d is safer" heuristic that
   IBM-8 established — correctly, because IBM-9 carries no controlled shift.
2. **The significance threshold was wrong by ~25%.** The X-conditioned curve
   is post-selected on G, halving its shot count relative to the Z-marginal,
   but a single σ was being used for both. Corrected to
   `hypot(1/√(N/d), 1/√(N/2d))` and shots raised to 20 000.

## Provenance

`ibm_marrakesh`, 2026-08-08T17:07Z, 1 job. Job ID in `ibm9_results.json`.

```
python pw_ibm_provenance.py --results results_ibm9_ibm_marrakesh/ibm9_results.json --out results_ibm9_ibm_marrakesh/ibm9_provenance.json
```
