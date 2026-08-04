# AQ-PAGE-WOOTTERS-IBM-1 — Gate 0 Results and a Corrected Functional Form

**2026-08-04. All 16 Gate 0 checks pass; the run is cleared for hardware.**
Along the way the dry run overturned the published functional form the run was
designed to test, and ruled out the D-LinOSS analysis it was designed to use.
Both are reported here, because both are results.

Artifacts: `hardware/pw_ibm1_dryrun.py`, `hardware/pw_ibm1_dlinoss_analysis.py`,
`results/hardware/pw_ibm1_dryrun_results.json`.

## Gate 0: design verified

| Check | d=4 | d=8 |
|---|---|---|
| Anchor: μ=0 reproduces IBM-0 exactly | 0.00e+00 gap | 0.00e+00 gap |
| Sampling matches exact statevector | < 0.015 | < 0.015 |
| Witness decays monotonically in μ (exact) | ✓ | ✓ |
| Witness decays monotonically (noisy) | ✓ | ✓ |
| Threshold reached: witness(π) → classical baseline | ✓ | ✓ |
| **Gate 4: conditional evolution survives all μ** | **R² 0.998** | **R² 0.998** |

Exact witness across the sweep, d=8: `0.497 → 0.485 → 0.450 → 0.395 → 0.324 →
0.244 → 0.159 → 0.077 → 0.000`. Under the calibrated noise model:
`0.435 → … → 0.019`, against a classical baseline of 0.017.

**Gate 4 is the headline and it holds cleanly.** Conditional evolution — the
apparent flow of time — is measured at R² = 0.998 at *every* μ, including
μ = π where the coherence witness has collapsed to the classical baseline.
This is exact, not incidental: the environment couples only to the clock, so
conditioning on a clock reading leaves the system state untouched. Apparent
temporal dynamics provably outlives its own quantum signature.

**H3 confirmed in simulation.** The informational arrow of time is reproduced
by the classical-clock control (entropy `0.166 → 0.999` across clock readings,
versus `0.224 → 1.000` coherent). So the arrow, like conditional evolution, is
not by itself a quantum signature — the same lesson IBM-0 established for
conditional evolution, now extended to entropy production.

## The corrected functional form (primary scientific result of Gate 0)

IBM-1 was designed to test the prediction `C(E) = C₀·e^{−kE}` from
arXiv:2512.15789, with `E` the clock–environment entanglement. Fitting the
exact analytic witness curve against that form:

| Form | d=4 | d=8 |
|---|---|---|
| `C = C₀·e^{−kE}` (exponential in entanglement) | R² = **0.535** | R² = **0.573** |
| `C = C₀·cos(μ/2)^p` (power law in record overlap) | R² = **1.0000**, p = 1.000 | R² = **0.9982**, p = 1.087 |

The exponential-in-entanglement form is a poor description of this channel.
The witness instead follows, to numerical precision, a **power law in the
clock-record overlap `cos(μ/2)` with exponent p ≈ 1** — i.e. the coherence
witness is essentially *linear in the overlap between adjacent clock records*.

This follows directly from the exact clock marginal,

```
ρ_C[t,t'] = (1/d)·cos((t−t')·π/d)·cos(μ/2)^{d_H(t,t')}
```

where the decay enters as a Hamming-weighted power of the record overlap, not
as an exponential in an entanglement measure. The two forms are strongly
distinguishable on hardware (R² ≈ 0.55 vs ≈ 1.00), so this is a sharp,
falsifiable, pre-registered prediction rather than a matter of fit taste.

**Revised H2, pre-registered:** the measured witness will follow
`C ∝ cos(μ/2)^p` with `p ≈ 1`, and the exponential-in-entanglement form will
fit visibly worse. A hardware result favouring the exponential would falsify
this and support the published form instead.

## D-LinOSS: ruled out here, and why that was the useful outcome

The intended analysis was to learn the μ-flow with a D-LinOSS recurrence,
comparing a stationary parameterization against an entanglement-damped one
(`λ_μ = exp(−γ·E(μ) + iω)`) whose architecture encodes the published
prediction. The model comparison was meant to *be* the physics test. It
returned a negative, in three stages:

1. **Conditional trajectories carry no μ-signal at all.** Tomographic
   conditional Bloch readout gives `|r(t)| ≈ 0.86`, flat across the entire
   sweep (the 0.86 is hardware noise, not decoherence). Training on
   conditional trajectories would be training on a signal that provably isn't
   there.
2. **Path-level relational-clock recovery does not transfer.** `CRY(μ)` leaves
   computational-basis clock populations exactly unchanged, so clock labels
   stay classically perfect at every μ and temporal ordering is trivially
   recoverable. The synthetic branch's promoted path-observability mechanism
   has no purchase on this experiment.
3. **The μ-flow needs ≥33 points before a recurrent model learns anything
   ordering-dependent.** Measured directly by sweeping grid density against
   shuffled-μ and reversed-μ controls:

   | μ points | beats shuffled/reversed controls? | damped beats stationary? |
   |---|---|---|
   | 9 | no | no |
   | 17 | no | no |
   | 33 | **yes** | no |
   | 65 | **yes** | no |

   Below 33 points the model fits marginals, not a flow — the controls score
   *better* than the true ordering, which is the diagnostic. And even at 65
   points the entanglement-damped parameterization never beats the stationary
   one.

That last row is the informative one: the damped architecture loses because
the damping genuinely is not exponential in the entanglement — the same fact
the direct fit shows. **The D-LinOSS model comparison worked exactly as a
hypothesis test is supposed to: it returned a negative on H2, and the negative
pointed at the right variable** (record overlap rather than entanglement),
which is how the corrected power law above was found.

**Standing recommendation:** do not run D-LinOSS on IBM-1. The witness curve
is a 9-point 1-D relationship with a known analytic form; the correct
estimator is the direct two-form fit with bootstrap CIs, which is what the
hardware analysis will use. The D-LinOSS pipeline is retained in the
repository as the record of the ruled-out approach and as a reusable μ-flow
analysis should a future run use a dense (≥33 point) sweep where sequence
modelling is warranted.

## What Gate 0 changed about the hardware run

- **H2 is replaced** by the power-law-in-overlap prediction above; both forms
  will be fit and compared on the hardware data.
- **Conditional tomography is added** (3 bases instead of 1) — it is what
  established the μ-independence of the conditional trajectory, and it is
  cheap.
- **The μ grid stays at 9 points.** Densifying to 33+ would only serve the
  D-LinOSS analysis that has now been ruled out; the direct fit does not need
  it, and the shots are better spent on statistics per point.
- Backend recommendation unchanged: `ibm_marrakesh`.

## Claim boundary (unchanged)

Nothing here claims time is emergent in nature, tests quantum gravity, or
realizes a physical Page–Wootters universe. The history state is engineered.
What Gate 0 establishes is that the planned measurement is sound, that its
headline (Gate 4) is theoretically exact and noise-robust, and that one
published functional-form prediction is already contradicted analytically
before any hardware time is spent.
