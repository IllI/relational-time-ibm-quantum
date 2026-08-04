# AQ-PAGE-WOOTTERS-IBM-1 — Gate 0 Results (Corrected 2026-08-04)

> [!IMPORTANT]
> **This document replaces the same-day first version, which was withdrawn
> after review.** Three claims in it did not match the committed code and
> data: the sampling-check threshold quoted in text (`<0.01`) did not match
> the implementation (`<0.015`), "Gate 4 tested at every μ" was written
> against a 3-point loop rather than the 9-point grid, and the reported
> R² values for the exponential fit did not match the committed JSON's own
> numbers because they came from an uncommitted scratch computation. All
> three are fixed here — in the code first, then in this text, verified
> against the regenerated JSON before being written down. A fourth issue
> (population entropy quoted as von Neumann entropy for the uncoupled arrow
> control) was also found and fixed; it changes the qualitative story for
> that control, for the better.

Artifacts: `hardware/pw_ibm1_dryrun.py`, `hardware/pw_ibm1_dlinoss_analysis.py`,
`results/hardware/pw_ibm1_dryrun_results.json`,
`results/hardware/pw_ibm1_dlinoss_results.json`. Every number below is read
directly from those two committed JSON files; none is transcribed from a
terminal session.

## Gate 0: design verified, 16/16, against a stated and reproducible criterion

The sampling-check gate (does Aer's finite-shot output match the exact
statevector prediction) previously used an unexplained round number. It now
uses **3× the theoretically expected shot-noise floor for the TVD statistic
at each μ's own exact distribution** — `expected_tvd_shot_noise()` in
`pw_ibm1_dryrun.py`, a direct generalization of the `uniform_tvd_floor()`
convention `pw_ibm_dryrun.py` already uses for Gate 3 in the IBM-0 line, here
extended from a uniform to an arbitrary reference distribution via a
per-outcome folded-normal approximation. This is the same style of criterion
already used elsewhere in this program, not a new standard invented for this
gate.

| Check | d=4 | d=8 |
|---|---|---|
| Anchor: μ=0 reproduces IBM-0 exactly | 0.00e+00 gap | 0.00e+00 gap |
| Sampling vs. exact, worst point (gap / 3×floor ratio) | **0.305** | **0.332** |
| Witness decays monotonically in μ (exact) | ✓ | ✓ |
| Witness decays monotonically (noisy) | ✓ | ✓ |
| Threshold reached: witness(π) → classical baseline | ✓ | ✓ |
| **Gate 4: conditional evolution, all 9 μ points** | **worst R² = 0.9990 (ideal) / 0.9961 (noisy)** | **worst R² = 0.9983 (ideal) / 0.9955 (noisy)** |

Both sampling-check ratios are well under 1.0 (worst case at 33–30% of the
allowed floor), not a marginal pass. Gate 4 is now genuinely tested at every
point on the 9-point μ grid — `conditional_n_mu_tested: 9` in the JSON — not
a 3-point subsample, so "survives every μ" is now a claim the committed code
actually makes and checks.

**Gate 4 is the headline and it holds cleanly across the full grid.**
Conditional evolution — the apparent flow of time — stays above R² = 0.995
at *every* μ from 0 to π, including where the coherence witness has
collapsed to the classical baseline. This is exact, not incidental: the
environment couples only to the clock, so conditioning on a clock reading
leaves the system state provably untouched regardless of μ.

Exact witness across the sweep, d=8: `0.497 → 0.485 → 0.450 → 0.395 → 0.324 →
0.244 → 0.159 → 0.077 → 0.000`. Under the calibrated noise model:
`0.431 → 0.420 → 0.392 → 0.348 → 0.282 → 0.206 → 0.147 → 0.065 → 0.010`,
against a classical baseline of 0.008–0.019 depending on μ.

## The corrected functional form — scope narrowed on review

**What changed from the withdrawn version:** the earlier draft described this
as contradicting arXiv:2512.15789. That overstated it. Their proposed
`C(E) = C₀e^{−kE}` relates subsystem coherence to *clock–subsystem*
entanglement. This dry run measures Fourier-basis TVD of the clock marginal
against `S(ρ_E)` — the entanglement of the **environment** with clock+system
jointly, a related but not identical quantity, computed by construction here
(the environment couples to the clock, so this is the entanglement generated
by that specific coupling). The defensible statement is narrower:

> For this engineered Hamming-dephasing channel and this clock-marginal
> witness, coherence tracks the record-overlap channel parameter
> substantially better than an exponential in the entanglement measure
> available in this construction.

Two forms, fit on the **primary 9-point grid that matches the planned
hardware measurement** (`pw_ibm1_dlinoss_results.json`, `primary_9point`):

| Form | d=4 | d=8 |
|---|---|---|
| `C = C₀·e^{−kE}` (exponential in entanglement) | R² = 0.786 | R² = 0.805 |
| `C = C₀·cos(μ/2)^p` (power law in record overlap) | R² = 1.0000, p = 1.00 [CI95 1.00, 1.00] | R² = 0.9994, p = 1.148 [CI95 1.131, 1.214] |

The same two forms, fit on a **dense 400-point exact grid** (`dense_asymptotic_400point`
in the same JSON, reported separately and never merged with the row above —
the earlier version's error was exactly this merge):

| Form | d=4 | d=8 |
|---|---|---|
| exponential in entanglement | R² = 0.553 | R² = 0.590 |
| power law in overlap | R² = 1.0000 | R² = 0.9983 |

**d = 4 is exactly linear in the record overlap `c = cos(μ/2)`** — not an
approximation. `TVD(μ)/c` is constant to 11 significant figures across the
sweep (verified directly, `ratio.std()/ratio.mean() ≈ 1.7×10⁻¹¹`), which
follows from the fact that at `d=4` every pair of clock labels has Hamming
distance exactly 1 or 2, and the aggregation into a single Fourier-basis TVD
statistic happens to collapse to a single power exactly for this case.

**d = 8 is not exactly linear**, and the 9-point fit (`p = 1.148`,
CI95 `[1.131, 1.214]`, which does not contain 1) says so honestly — this is
a genuinely good but *not exact* power-law approximation, distinguishable
from a strict `p=1` law on the actual measurement grid. At `d=8`, clock
labels span Hamming distances 1, 2, and 3, so the TVD is a mixture of three
different powers of `c`, and a single effective exponent is a fit to that
mixture, not a derived law. The dense-grid fit (`p ≈ 1.06` by direct
log-log regression away from the discrete 9-point set) and the primary
9-point fit (`p = 1.148`) legitimately disagree by more than either's
individual noise, because they are fits of the same approximate form to
different samples of the same non-power-law curve — this is expected, not
an error, and both numbers are reported rather than reconciled to a single
"true" value that doesn't exist for this quantity.

**Both forms remain strongly distinguishable on hardware regardless of which
grid is used** — R² ≈ 0.55–0.81 versus ≈ 0.998–1.00 in every version of the
comparison above — so the pre-registration below is unaffected by the
grid-dependence of the d=8 exponent.

**Revised H2, pre-registered:** the measured witness will follow
`C ∝ cos(μ/2)^p` far better than `C ∝ exp(−kE)`; at d=4 with `p` statistically
indistinguishable from 1, at d=8 with `p` in the range 1.06–1.21 depending on
estimator. A hardware result favoring the exponential form, or finding the
power-law fit no longer dominant, would falsify this.

## D-LinOSS: ruled out here, now with the ruling-out fully reproducible

The model comparison (stationary vs. entanglement-damped D-LinOSS recurrence
on the μ-flow of the clock's Fourier distribution) is committed in
`pw_ibm1_dlinoss_analysis.py` and returns a negative in three stages, each
now backed by a saved JSON rather than a terminal transcript:

1. **Conditional trajectories carry no μ-signal.** Tomographic conditional
   Bloch readout gives `|r(t)| ≈ 0.86` at every tested μ (0, π/2, π shown;
   full sweep in `conditional_bloch`), flat to within hardware noise. The
   environment couples to the clock, not the system, so this is exact in
   theory and confirmed in simulation.
2. **Path-level relational-clock recovery does not transfer.** `CRY(μ)`
   leaves computational-basis clock populations exactly unchanged.
3. **The μ-flow needs a denser grid before a recurrent model beats its own
   shuffled/reversed controls, and even then the damped architecture never
   wins** — now measured on the committed `density_sweep()` function, run at
   `n_μ ∈ {9, 17, 33, 65}` on the exact curve:

   | n_μ | d=4 damped beats stationary? | d=4 beats best control? | d=8 damped beats stationary? | d=8 beats best control? |
   |---|---|---|---|---|
   | 9 | no | no | no | no |
   | 17 | no | no | no | no |
   | 33 | no | **yes** | no | **yes** |
   | 65 | no | no | no | **yes** |

   The "beats best control" column is not perfectly monotone (d=4 wins its
   control comparison at 33 points but not at 65) — that non-monotonicity is
   itself informative: it means the sparse-grid wins are a property of the
   specific control realization at that density, not a stable trend, and
   should not be read as "the flow becomes learnable past 33 points." The
   one column that **is** stable across every density tested is
   `damped beats stationary`: **no, at every density from 9 to 65 points, for
   both d.** The entanglement-damped architecture never wins, at any grid
   density — consistent with the direct finding above that the true decay
   law is a power in record overlap, not an exponential in entanglement, so
   an architecture built to fit the latter is structurally mismatched
   regardless of how much data it gets.

**Standing recommendation unchanged: do not run D-LinOSS on the actual
hardware measurement.** The 9-point witness curve is a 1-D relationship with
a known analytic form; the direct two-form fit with bootstrap CIs (now also
committed, `fit_exponential()` / `fit_power_law()`) is the correct estimator
and is what the hardware analysis will use.

## Arm 1B (informational arrow): entropy estimator corrected

The withdrawn version reported the "uncoupled" control's entropy as
`H2(p1)` — the Shannon entropy of a single-basis (Z) measurement outcome.
That is **not** the von Neumann entropy of the conditional system state in
general; the two coincide only when the state is Z-diagonal. For the coupled
and classical-clock arrow arms, CNOT-then-trace genuinely dephases the system
into a Z-diagonal state, so `H2(p1)` happened to be correct there. For the
**uncoupled** control, no CNOT is ever applied — the system stays in a pure
coherent superposition for every clock reading, with zero entanglement to
anything, so its true von Neumann entropy is exactly 0 at every `t`. `H2(p1)`
cannot see this: it reports rising "entropy" purely from measuring a
superposition in the wrong basis.

Fixed by adding 3-basis tomography (`build_arrow_tomo`) and computing the
true entropy from the reconstructed Bloch vector,
`S = H2((1+|r(t)|)/2)`:

| Arm | population entropy `H2(p1)`, t=0..7 | von Neumann entropy (tomography), t=0..7 |
|---|---|---|
| coupled | 0.22, 0.27, 0.39, 0.51, 0.73, 0.85, 0.97, 1.00 | 0.25, 0.25, 0.42, 0.56, 0.73, 0.87, 0.98, 0.99 |
| **uncoupled** | 0.22, 0.29, 0.47, 0.58, 0.73, 0.86, 0.95, 1.00 | **0.26, 0.23, 0.14, 0.19, 0.19, 0.26, 0.26, 0.20** |
| classical clock | 0.15, 0.26, 0.40, 0.54, 0.69, 0.88, 0.99, 1.00 | 0.09, 0.23, 0.38, 0.58, 0.72, 0.88, 0.97, 1.00 |

The corrected picture is qualitatively different from, and better than, the
withdrawn one. The coupled and classical-clock arms both show a real
monotonic entropy rise under the correct estimator (`gate6_arrow_monotone_vn`,
`gate6_arrow_classical_too_H3_vn`, both pass) — H3 is confirmed by the right
measurement, not the wrong one. The uncoupled control now sits flat at
`0.14–0.26` — consistent with the theoretical prediction of exactly 0, with
the residual explained by hardware noise in a 4-circuit tomographic
reconstruction rather than by real entanglement (`gate6_uncoupled_stays_near_pure`
passes, threshold `<0.3`). This is a *cleaner* control than the withdrawn
version reported: "the arrow requires the inaccessible environment; without
it, the state stays provably near-pure" is a sharper and more correct
statement than the flat-but-still-rising curve previously shown.

## What Gate 0 changed about the hardware run

- **H2 is replaced** by the power-law-in-overlap prediction above, on the
  primary 9-point grid, with the dense-grid asymptotic behavior reported as
  an explicitly separate secondary check.
- **Conditional tomography is added** (3 bases instead of 1) — it established
  the μ-independence of the conditional trajectory and is reused for the
  arrow controls.
- **Arm 1B's entropy estimator uses tomographic von Neumann entropy**, not
  single-basis population entropy, for all three arrow variants.
- **The μ grid stays at 9 points** for the actual hardware submission. The
  density sweep above is a simulation-only diagnostic of the ruled-out
  D-LinOSS approach; densifying the real measurement would only serve an
  analysis that has been dropped, and the direct fit does not need it.
- Backend recommendation unchanged: `ibm_marrakesh`.

## Claim boundary (unchanged)

Nothing here claims time is emergent in nature, tests quantum gravity, or
realizes a physical Page–Wootters universe. The history state is engineered.
What Gate 0 establishes is that the planned measurement is sound under a
stated and reproducible statistical criterion, that its headline (Gate 4) is
theoretically exact and noise-robust across the full measurement grid, and
that the run's H2 prediction has been narrowed to a form the exact data
actually supports — before any hardware time is spent.
