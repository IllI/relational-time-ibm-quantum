# AQ-PAGE-WOOTTERS-DLINOSS-BEC-ENTROPIC-BRIDGE-0 -- Gate 0 Results (2026-08-03)

## Outcome

**Gate 0 fails.** 0 of 5 configurations pass. This closes the BEC bridge
line for now: per the pre-registered plan in
`AQ_PAGE_WOOTTERS_DLINOSS_BEC_ENTROPIC_BRIDGE_0_RUN_SPEC_2026-08-03.md`,
Gate 1 (the two-world bridge) is not implemented, since it required at
least 3 of 5 Gate 0 configurations to pass first.

Script: `program_aq_page_wootters_bec_entropic_bridge0.py`. Full run:
`results_page_wootters_bec_entropic_bridge0/bec_entropic_bridge0_gate0_results.json`
(`time_steps=512`, `hidden_dim=16`, `epochs=400`, `context_steps=8`,
`seeds=[11,12,13,14,15]`).

## Method (as specified, one revision made during implementation)

Generator: two-mode Josephson-junction BEC dimer with a dark-sector
diffusion bath, exactly as specified -- `dz/dt`, `dphi/dt` deterministic
Josephson dynamics, `D(t) = D0*(1+kappa*|sin(phi)|)` driving both a phase
diffusion term and `dSigma/dt = 2*D(t)`, with `tau(t) = 0.5*log(Sigma(t)/Sigma(0))`
computed directly from the (latent) accumulated variance -- not a heuristic.

**Revision from the original spec:** the spec's Gate 0 design (fit on the
first half of one trajectory, evaluate on the unseen second half of the
*same* trajectory) was tried first and produced numerically unusable
results (payload R^2 in the -100s to -6000s). Diagnosis: the generator is
close to noiseless in `z, phi` (only `phi`'s diffusion term carries
randomness), so a flexible recurrent model drives calibration loss to
~0 and then extrapolates catastrophically on a genuinely unseen future
time range it never saw during training -- a much harder and less relevant
task than the paper's actual claim, which is about reconstructing time from
ongoing entropy production, not forecasting a chaotic-adjacent oscillator's
distant future. The design was corrected to a leave-one-out cross-seed test:
train on 3 seeds + 1 validation seed (early stopping only), evaluate on a
genuinely held-out 5th seed's *entire* trajectory. This tests the paper's
actual claim -- does the bright-sector-to-entropic-time mapping hold as a
general law across independent noise realizations -- and is consistent with
how every other gate in this branch (A6/A10, path-observability, etc.)
evaluates on independent trials rather than forecasting a single trajectory
forward. The severed/cross-regime and shuffled controls were adjusted to match
(see script docstring).

## Results

| Config | Lambda | D0 | kappa | median r2_tau | median gain vs wallclock | median r2_shuffled | median r2_cross_regime | median r2_ridge |
|---|---|---|---|---|---|---|---|---|
| josephson_low_diff | 0.3 | 0.02 | 1.0 | -0.035 | -0.119 | -1.966 | -3.062 | 0.108 |
| josephson_high_diff | 0.3 | 0.08 | 1.0 | 0.232 | 0.152 | -1.373 | -3.947 | 0.257 |
| rabi_low_diff | 1.5 | 0.02 | 1.0 | -0.129 | 0.205 | -0.846 | -2.475 | -0.027 |
| rabi_high_diff | 1.5 | 0.08 | 2.0 | -0.620 | 0.444 | -1.495 | -0.738 | -0.003 |
| fock_selftrap | 3.0 | 0.05 | 1.5 | 0.310 | -0.200 | -1.891 | -6.260 | 0.077 |

R^2 computed on the fully held-out eval seed's whole trajectory, median
over the 5 leave-one-out rotations per config.

## Interpretation

**The controls work correctly, which is what makes the failure trustworthy.**
Both nulls behave exactly as they should: the shuffled control (frozen
tau-model fed a time-shuffled version of the eval trajectory) fails hard in
every single trial (R^2 always strongly negative), and the cross-regime
control (frozen tau-model applied to a trajectory from a different
Lambda/D0/kappa regime) fails even harder. This rules out a broken harness
or a trivial always-predict-the-mean model passing by accident -- when the
recurrent model does extract signal, it is regime- and order-specific, as
intended.

**The primary reconstruction fails to clear the bar, and inconsistently.**
Median r2_tau ranges from -0.62 to +0.31 across the five configs -- never
close to the 0.70 target, and the sign itself is unstable (negative medians
for 3 of 5 configs mean the leave-one-out model does *worse* than predicting
the mean tau, on the typical held-out seed). Individual eval-seed rows swing
from r2_tau=0.9 down to r2_tau=-46 within the same config
(`josephson_high_diff`, seed 14), indicating the learned mapping does not
transfer reliably across independent noise realizations of the same
physical law -- exactly the generalization gap Gate 0 was designed to
detect.

**Wall-clock time is often almost as recoverable as tau, which blunts the
central comparison.** In several configs (`josephson_low_diff` seed 11:
r2_wall=0.675; `fock_selftrap` seed 14: r2_wall=0.721) the wall-clock null
scores nearly as high as, or higher than, tau itself. This traces to a
generator limitation: with `D0` dominating over the `kappa*|sin(phi)|`
modulation in most tested regimes, `Sigma(t)` grows close to linearly in
`t`, so `tau(t)` is close to an affine function of elapsed time and does not
carry much information beyond it. A recurrent model with an approximately
constant per-step drive learns to approximate elapsed time fairly well
regardless of target, which is why "beats wall-clock by >=0.10 R^2" fails
even in configs where r2_tau itself is not terrible.

## Standing Conclusion

The two-mode Josephson-junction generator, as specified, does not produce a
bright-sector-only observable stream from which an entropic-time coordinate
is reliably recoverable across independent noise realizations, under the
event-damped-style recurrent D-LinOSS integrator tested here. This is a
statement about **this synthetic generator and this observability test**,
not about the underlying physical claim in arXiv:2509.07745 -- their
demonstration used real measured center-of-mass dynamics with a richer
observable channel (interference fringe contrast, atom-number statistics)
and a full entropic-time Schrodinger-equation fit, not a mean-field two-mode
proxy with 7 hand-built local features.

Per the pre-registered plan, **Gate 1 (the two-world bridge) is not
implemented.** Proceeding to it would not be a meaningful test given that
the single-system mechanism it depends on does not work yet.

## What Would Need to Change Before Retrying

1. **Make tau genuinely distinguishable from wall-clock.** Increase `kappa`
   and use configs where the dark-sector diffusion rate swings over a wider
   dynamic range relative to `D0` (e.g., `kappa >> 1` with `D0` small), so
   `Sigma(t)` growth is driven by bursty, phi-dependent activity rather than
   an almost-constant rate.
2. **Add real bright-sector observation noise.** The current `z, phi`
   channels are the exact state, not a noisy measurement of it; the paper's
   actual experiment reconstructs time from noisy interference/expansion
   data, which changes the identifiability problem substantially (and may
   make the fit *easier* by making the wall-clock null less trivially
   learnable while tau, driven by real reduced-state entropy, may still
   leave a distinguishable signature).
3. **More training data per config.** 3 fit trajectories x 512 steps is
   thin for a cross-seed generalization claim; a larger seed pool (10-20)
   would tighten the leave-one-out variance seen here (single-config swings
   from r2_tau=0.9 to r2_tau=-46 across seeds).
4. **Reconsider the observable feature set.** The current 7 hand-built
   channels (value/velocity/acceleration/local-variance style, matching the
   locked CHRONOS convention) were carried over from the TPU-telemetry
   branch without being re-derived for this specific dynamical system;
   features tied to the Josephson dynamics directly (e.g., estimated local
   oscillation frequency, envelope amplitude) may carry more information
   about `D(t)` than local variance does.

None of these are implemented here. This result stands as a clean,
controlled null for the specific generator and feature set tested.
