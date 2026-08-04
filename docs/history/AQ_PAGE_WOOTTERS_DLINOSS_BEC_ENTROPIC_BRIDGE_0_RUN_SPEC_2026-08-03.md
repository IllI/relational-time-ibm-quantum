# AQ-PAGE-WOOTTERS-DLINOSS-BEC-ENTROPIC-BRIDGE-0 Run Spec - 2026-08-03

> [!IMPORTANT]
> **Gate 0 was run the same day and failed (0/5 configs).** Gate 1 below was
> not implemented, per the pass criterion in this spec. See
> `AQ_PAGE_WOOTTERS_DLINOSS_BEC_ENTROPIC_BRIDGE_0_GATE0_RESULTS_2026-08-03.md`
> for the full result, including a revision made to the Gate 0 evaluation
> design during implementation (leave-one-out cross-seed testing replaced
> same-trajectory forecasting, for reasons explained there).

## Purpose

`CHRONOS-REAL-ENTROPIC-CLOCK-0` closed the real-TPU-telemetry question: the
confirmed A10/event-damped mechanism, applied to real US/EU hardware streams,
fails more decisively than it did on any synthetic noise level. That result
should not be read as evidence against the entropic-time hypothesis itself --
it is evidence that two TPU datacenters do not share a physical entropic
clock, which was never the strongest test of the hypothesis.

A stronger test is available. Buccino, Vovrosh *et al.* (arXiv:2509.07745)
recently demonstrated entropic time operationally in a real cold-atom system:
a rubidium-87 BEC bisected into an "observed" bright sector and an
"unobserved" dark sector, with `tau(lambda) = (sigma/k_B) * integral (dS/dphi) dphi`
constructed from entropy flow between sectors, and an entropic-time
Schrodinger equation reproducing the measured expansion/collapse cycles. This
run tests whether the D-LinOSS/path-observability pipeline built in this
branch can recover *that* construction from a physically grounded generator,
rather than the more ad hoc residual/event/entropy causal-action generator
(A10) invented for the TPU-telemetry bridge.

## Paper-Safe Claim Target

```text
An event-damped D-LinOSS operator, evaluated under the same frozen-operator
and path-observability discipline used throughout this branch, can recover
an entropy-flow-defined internal clock from bright-sector-only observables
of a synthetic two-sector Josephson-junction BEC model, and -- if a two-world
bridge gate also passes -- can align independent realizations of that model
using the entropic clock rather than wall-clock time.
```

This deliberately avoids claiming:

- a physical Page-Wootters realization,
- a replication of the arXiv:2509.07745 experiment itself (this is a
  mean-field synthetic model inspired by it, not their data or their GPE
  simulation),
- any bearing on the closed TPU cross-datacenter question, which
  `CHRONOS-REAL-ENTROPIC-CLOCK-0` already answered independently.

## Why This Is a Different Experiment From A10

| | A10 (TPU bridge, closed) | BEC bridge (this spec) |
|---|---|---|
| System | Two independent hosts, no shared physics | One physically motivated two-sector model |
| Entropy source | Ad hoc residual/event/entropy heuristics | Genuine reduced-state entropy from tracing out the dark sector |
| Clock definition | `tau = weighted sum of heuristic channels` | `tau(t) = S(t) - S(0)`, monotonic by construction |
| Observable | Raw latency-derived features | Bright-sector population imbalance (the paper's center-of-mass analog) |
| Question | Do two datacenters share time? (answered: no) | Can D-LinOSS recover a genuine entropic clock from partial observations? |

## Generator: Two-Mode Josephson BEC With a Dark-Sector Bath

Model the paper's barrier-split condensate as a driven-dissipative two-mode
(bosonic Josephson junction) system -- the standard mean-field model for two
weakly linked BEC regions (Smerzi-type dimer), extended with a dark-sector
bath coupling so that tracing out the dark sector produces genuine,
monotonic entropy production in the bright sector's reduced state.

**Closed bright/dark dynamics** (population imbalance `z in [-1,1]`, relative
phase `phi`, coupling `Lambda`):

```text
dz/dt   = -sqrt(1 - z^2) * sin(phi)
dphi/dt = Lambda * z + (z / sqrt(1 - z^2)) * cos(phi)
```

**Dark-sector leakage** (unobserved further partitioning of the dark mode,
representing the paper's "mini-universe" construction where the dark sector
is itself not fully accessible): add a stochastic phase-diffusion term to
`phi` with rate `D(t)` driven by the instantaneous coupling energy, and track
the second moment `Sigma(t)` of the bright-sector reduced state under this
diffusion:

```text
dphi        += sqrt(2 * D(t)) * dW_t          (Wiener increment)
dSigma/dt    = 2 * D(t)                       (monotonic by construction)
D(t)         = D0 * (1 + kappa * |sin(phi(t))|)   (activity-dependent diffusion)
```

**Entropic-time coordinate** (direct operationalization of the paper's
`tau(lambda) ~ integral dS`, not a heuristic):

```text
S(t)   = 0.5 * log(2 * pi * e * Sigma(t))     (Gaussian differential entropy proxy)
tau(t) = S(t) - S(0)
```

`tau(t)` is monotonic non-decreasing by construction (`Sigma` is
non-decreasing), which is the paper's central structural claim -- unlike
wall-clock time, which is assumed, `tau` is *derived* from entropy flow and
happens to be monotonic for the same reason the paper's arrow of time is
monotonic.

**Bright-sector observable** (what an experimentalist actually measures, and
the only signal the model is allowed to see in Gate 0): `z(t)` and `phi(t)`
only. `Sigma(t)` and `S(t)` are latent -- known to the generator, hidden from
the recovery model, exactly as the dark sector is hidden from the bright-sector
observer in the real experiment.

## Gate 0: Single-System Entropic-Clock Observability (run first, no bridge)

This is the direct, single-host test of the paper's claim and should be run
and gated before any two-world bridge work.

**Question:** can `tau(t)` be reconstructed from `z(t), phi(t)` alone, better
than assuming wall-clock time or a shuffled/severed control?

**Method:**

1. Simulate one bright/dark trajectory, `time_steps=512`, several `Lambda`
   regimes spanning the Josephson (`Lambda < 1`) and Rabi/Fock (`Lambda > 1`)
   regimes, several `D0`/`kappa` values.
2. Build the observable feature stream from `z(t), phi(t)` only: value,
   velocity, acceleration, local variance in a short window (a legitimate
   bright-sector-only entropy *proxy*, distinct from the true latent `S(t)`).
3. Fit a regression (ridge first, then event-damped D-LinOSS if ridge shows
   signal) from the observable stream to the true latent `tau(t)`, calibration
   half only.
4. Score payload-half reconstruction: `cosine(tau_pred, tau_true)` and
   `R^2`, against:
   - `wall_clock_null`: fit the same regression to raw step index instead of
     `tau`.
   - `shuffled_null`: observable stream time-shuffled before fitting.
   - `severed_null`: fit on one trajectory, evaluate on an independent
     trajectory with a different seed.

**Pass Gate 0:**

```text
tau reconstruction R^2 > 0.70 on payload half
tau reconstruction beats wall_clock_null by >= 0.10 R^2
shuffled and severed nulls fail (R^2 < 0.20)
```

Do not proceed to the two-world bridge unless Gate 0 passes across at least
3 of 5 tested `(Lambda, D0, kappa)` configurations. If Gate 0 fails, the
finding is that this particular mean-field synthetic model does not carry
enough bright-sector signal about dark-sector entropy production to make the
paper's construction recoverable from partial observation alone -- a valid
and reportable result about the model, not about the paper.

## Gate 1: Two-World Entropic-Clock Bridge (only if Gate 0 passes)

Reuses the existing promoted machinery unchanged: `path_cost` / `path_metrics`
from `program_aq_page_wootters_path_observability0.py`, and the event-damped
operator shape from `program_aq_page_wootters_a10_event_damped_confirm0.py`.
Only the generator changes.

**Construction:** simulate two independent bright/dark realizations
("world A", "world B") with independent noise seeds and a preregistered
integer lag between them (matching the existing `true_lag` convention). Each
world produces its own `tau_A(t)`, `tau_B(t)` from its own entropy production
-- there is no shared physical clock by construction, only the same
*generative law*. This directly parallels `AQ-DLINOSS-CHRONO-0`'s Model 3
(relational clock) versus Model 0 (null independent drift), but the
clock is now genuinely entropy-derived rather than a heuristic causal-action
sum.

**Feature vector per world** (replaces A10's `causal_aux`):

```text
clock channels: sin(tau), cos(tau), z, phi, entropy_rate = dS/dt, Sigma
aux channels (drive the event-damped operator's gamma/omega):
  entropy_rate, |dphi/dt| (activity), Sigma, D(t)
```

**Required arms** (identical structure to `AQ-DLINOSS-CHRONO-0` /
`A10-EVENT-DAMPED-CONFIRM-0`):

| Arm | Purpose |
|---|---|
| `true_A_B` | True world-A-to-world-B transition prediction, entropic-clock-aligned path |
| `wall_clock_path` | Alignment by step index instead of `tau` |
| `shuffled_path` | Bob temporal order destroyed |
| `severed_path` | Bob distribution preserved, phase relation severed |
| `cross_seed_path` | Independent third-world realization |
| `wrong_lag_path` | Bob shifted outside the true preregistered lag |
| `block_shuffled_path` | Bob block-permuted |

**Primary endpoints** (same family as the confirmed A10 run, so results are
directly comparable):

```text
path_rank (global path observability)
dlinoss_relational_gain (mean and bootstrap CI on per-window gain)
dlinoss_relational_minus_external_gain (entropic clock vs wall-clock alignment)
window_fraction_beating_best_null
dlinoss_minus_ridge
```

**Pass Gates** (unchanged thresholds from `A10-EVENT-DAMPED-CONFIRM-0`, so a
pass here is directly comparable to the promoted TPU-generator result):

```text
Gate -1: path_rank == 1 across tested seeds/noise
Gate 1:  median dlinoss_relational_gain > 0.10, CI lower bound > 0
Gate 2:  median relational_minus_external (entropic clock beats wall-clock) > 0.05
Gate 3:  median dlinoss_minus_ridge >= -0.10
Gate 4:  median window_fraction_beating_best_null >= 0.70
```

## Expected Outcomes

**Outcome A -- Gate 0 fails.** The bright-sector-only observable does not
carry enough information about dark-sector entropy production in this
mean-field model. Recommended follow-up: add richer bright-sector
observables (e.g., higher moments of `z`, cross-correlation with a known
drive), or accept that a two-mode mean-field model is too coarse and move to
a multi-mode (few-site Bose-Hubbard) generator before re-attempting.

**Outcome B -- Gate 0 passes, Gate 1 fails.** The entropic clock is
recoverable within a single system but does not transfer to a two-world
alignment problem. This would mirror the TPU result's shape (recoverable
locally, not alignable across independent systems) but for a genuinely
different, physically motivated reason worth documenting on its own.

**Outcome C -- Both gates pass.** This is the first result that would
justify claiming the event-damped D-LinOSS mechanism generalizes from an ad
hoc causal-action heuristic (A10) to a first-principles entropy-flow
construction anchored in a published cold-atom result. It still would not
establish anything about the real experiment beyond "our pipeline can learn
the same functional relationship in a mean-field synthetic version of it."

## Launch Discipline

This is pure CPU/JAX simulation -- no TPU required, no TRC resources, no
data collection. Gate 0 should take under an hour on a laptop; Gate 1 reuses
existing training loops at the same cost as `A10-EVENT-DAMPED-CONFIRM-0`
(minutes per configuration on CPU, faster on TPU if available).

## Immediate Implementation Plan

1. Add `program_aq_page_wootters_bec_entropic_bridge0.py` implementing the
   two-mode Josephson generator with dark-sector diffusion above, in the same
   module style as `program_aq_page_wootters_global_causal_memory0.py`.
2. Implement Gate 0 (single-system `tau` observability) first as a standalone
   check; do not build the two-world bridge until Gate 0 results are in.
3. If Gate 0 passes on at least 3 of 5 `(Lambda, D0, kappa)` configurations,
   implement Gate 1 by importing `path_cost`, `path_metrics`, and the
   `forward`/`init_params`/`train_model` event-damped operator unchanged from
   the existing modules, swapping only the generator and feature-construction
   functions.
4. Report using the same JSON/summary.md convention as every other run in
   this branch.
