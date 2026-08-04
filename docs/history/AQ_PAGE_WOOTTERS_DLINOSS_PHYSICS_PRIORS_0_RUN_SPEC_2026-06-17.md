# AQ-PAGE-WOOTTERS-DLINOSS-PHYSICS-PRIORS-0 Run Spec - 2026-06-17

## Purpose

The previous Page-Wootters/D-LinOSS branch established a useful decomposition:

```text
D-LinOSS transition capacity:      viable when given good paths
matcher policy:                    not enough
learned clock metric:              not enough
local history clock embedding:     improves but still fails
root issue:                        synthetic clock feature is under-identifiable
```

`AQ-PAGE-WOOTTERS-DLINOSS-PHYSICS-PRIORS-0` shifts the next experiment away from matcher tuning and toward a redesigned synthetic universe. The clock should become observable because time leaves causal, irreversible, entropy-bearing traces in the state history, not because a fragile pointwise phase feature happens to be recoverable.

## Core Question

Can a Page-Wootters/open-system inspired synthetic history generator produce an internal relational clock whose true correspondence is separable from null paths before any D-LinOSS transition scoring is attempted?

## Conceptual Shift

Do not treat the next branch as:

```text
harmonic phase + a few extra drift terms
```

Treat it as:

```text
clock-system-environment synthetic history
+ open-system damping
+ sparse causal events
+ irreversible residual memory
+ entropy/strain production
```

The observability claim must come from correlations among these quantities, not from local periodic phase alone.

## Generator Structure

Represent each history as a synthetic Page-Wootters/open-system state:

```text
|Psi> = sum_t |t>_C |psi(t)>_S |epsilon(t)>_E
```

where:

```text
|t>_C         = clock register
|psi(t)>_S    = system state
|epsilon(t)>_E = environment / residual bath state
```

Use the latent update:

```text
z_{t+1} = exp((JH_t - Gamma_t) Delta t) z_t
        + event_drive_t
        + residual_bath_t
```

with:

```text
JH_t      = Hamiltonian / phase-rotation component
Gamma_t   = positive damping / decoherence component
event_t   = sparse causal impulse
residual_t = irreversible bath / memory state
```

The previous projected-harmonic world was too symmetric. This generator must carry a real causal arrow.

## Physics-Constrained Operator Mechanics

The recurrence should not interpret damping as arbitrary scale shrinkage. Use:

```text
lambda_k(t) = exp((-gamma_k(t) + i omega_k(t)) Delta t)
gamma_k(t) >= 0
```

Tie damping to open-system quantities:

```text
gamma_k(t) = gamma0
           + gamma1 * entropy_rate(t)
           + gamma2 * transition_residual_energy(t)
           + gamma3 * event_activity(t)
```

This makes loss of phase coherence interpretable as local strain, residual memory, or event-driven decoherence rather than a free learned scalar.

## Required Causal Ingredients

The new generator must include at least the following:

```text
1. non-periodic drift
2. sparse event markers
3. entropy / strain events
4. irreversible residual accumulation
5. multi-scale phase / cumulative causal time
6. positive damping tied to open-system observables
```

### Non-periodic drift

```text
z(t+1) = A(t) z(t) + b(t)
```

where `A(t)` changes slowly and non-cyclically.

### Event markers

Sparse latent events `e_t` perturb the transition law and should be detectable in local state history.

### Entropy / strain events

Introduce local changes in variance, curvature, or low-rank structure so time carries a deformation signature, not only a phase signature.

### Residual bath memory

Use an irreversible auxiliary process such as:

```text
r(t+1) = gamma_r * r(t) + event_t + noise_t
```

with `0 < gamma_r < 1`, so residual memory becomes part of the internal clock state.

Use a vector residual bath for the run:

```text
r(t) in R^d
d = latent_dim / 2
r(t+1) = gamma_r r(t) + W_event event_t + residual_energy_t + noise_t
```

A scalar bath is not sufficient for this gate because it can become either too easy as a timestamp or too weak as a memory channel.

## Ablation Ladder

Do not test only the full causal generator. Run the following generator arms:

```text
A0: projected_harmonic_baseline
A1: + non_periodic_drift
A2: + sparse_events
A3: + residual_bath_memory
A4: + entropy_strain_events
A5: + damping_tied_to_observables
A6: full_causal_clock
```

The key interpretation metric is whether observability improves as causal ingredients are added. A pass by `A6` alone is useful but incomplete; the ladder tells us why it passes.

## Shared Observable Formulas

Use the same entropy, strain, and residual definitions everywhere: damping, clock construction, feature arms, and diagnostics.

For a local window around time `t`:

```text
local_cov_t = covariance(z[t-w : t+w])
entropy_proxy(t) = log det(local_cov_t + eps I)
entropy_rate(t) = |entropy_proxy(t) - entropy_proxy(t-1)|
strain(t) = ||z(t+1) - 2 z(t) + z(t-1)||_2
transition_residual_energy(t) = ||z(t+1) - A_slow(t) z(t)||_2^2
```

Do not let the clock channel, damping channel, and diagnostic channel each invent separate versions of entropy or strain.

## Clock Construction

The old clock:

```text
clock(t) = [sin tau(t), cos tau(t), kappa(t)]
```

was too degenerate. Replace it with a clock built from cumulative causal statistics:

```text
tau(t) = omega t
       + beta1 * cumulative_curvature(t)
       + beta2 * cumulative_entropy_production(t)
       + beta3 * cumulative_event_count(t)
       + beta4 * residual_bath_memory(t)
```

The pointwise clock observable may still expose sine/cosine of `tau(t)`, but the underlying `tau(t)` must now depend on the same causal variables that reshape the history.

## Anti-Cheat Control

Add:

```text
causal_stats_permuted_clock
```

This control keeps the same marginal distributions of event count, residual memory, entropy rate, and strain, but permutes their time association with `z(t)`.

Report this as a separate anti-cheat diagnostic, not as part of the ordinary null pool used for the main positive-margin gate:

```text
anti_cheat_positive_margin
anti_cheat_margin_median
anti_cheat_margin_mean
```

If the full causal clock passes the ordinary observability gate and the permuted causal-stats diagnostic also looks strong, then the run is using marginal fingerprints rather than true causal temporal correspondence.

## First Gate: Observability Only

Before any D-LinOSS bridge is run, execute only:

```text
AQ-PAGE-WOOTTERS-DLINOSS-PHYSICS-PRIORS-OBSERVABILITY-0
```

Do not run transition scoring until this gate passes.

### Candidate feature arms

Compare:

```text
point_clock_baseline
patch_clock_w3
patch_clock_w5
patch_clock_w9
state_patch_w5
transition_signature_w5
contrastive_patch_encoder
```

The local-history arms should now benefit from genuinely causal local signatures instead of trying to rescue a degenerate phase process.

### Primary observability metrics

Report:

```text
fraction_positive_margin
median_margin
mean_margin
true_path_rank_median
true_path_rank_p90
collision_rate
payload_margin_generalization_gap
```

where:

```text
margin = nearest_null_distance - true_pair_distance
```

### Pass gates

```text
noise=0.00:
  fraction_positive_margin >= 0.90
  median_margin > 0

noise=0.01:
  fraction_positive_margin >= 0.75
  median_margin > 0

noise=0.02:
  fraction_positive_margin >= 0.60
  median_margin > 0

noise=0.03:
  stress diagnostic only
```

If these fail, stop. The generator still does not produce an observable relational clock.

## Bridge Back To D-LinOSS

Only after observability passes:

```text
AQ-PAGE-WOOTTERS-DLINOSS-PHYSICS-PRIORS-BRIDGE-0
```

Use the same frozen-operator discipline:

```text
1. calibration-only clock/path selection
2. fit true-arm D-LinOSS operator
3. freeze operator
4. controls alter correspondence only
5. heldout delta-transition scoring
```

### D-LinOSS operator interpretations

Interpret the D-LinOSS variants physically:

```text
diag_phase:
  closed phase evolution only

hamiltonian:
  constrained unitary-like rotation

hamiltonian_plus_scale:
  open-system phase rotation plus damping

event_damped:
  damping conditioned on entropy / residual / event statistics
```

## Resource Shape

For the first observability run:

```text
time_steps = 128
state_dim = 64
latent_dim = 8
seeds = 11, 12, 13, 14, 15
noise = 0.00, 0.01, 0.02, 0.03
```

Do not scale time history or latent dimension until the observability gate passes.

## Promotion Rule

The branch should not be promoted based on partial matcher wins or isolated seed behavior. The next honest milestone is:

```text
the causal / physics-priors synthetic history makes the true clock correspondence
separable from null candidates under the observability gates
```

Only then does it make sense to ask whether D-LinOSS can exploit that clock.
