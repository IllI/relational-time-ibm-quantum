# AQ-PAGE-WOOTTERS-0 Run Spec - 2026-06-15

## Purpose

The CHRONOS external-timing branch should be closed as a disciplined null for alignment claims:

```text
CHRONOS-SCHUMANN did not replicate.
AQ-DLINOSS-CHRONO-0 did not find heldout cross-host transition geometry.
CHRONOS-MARGINAL-DRIFT-1 showed broadband similarity persists under a one-hour shift.
CHRONO-MERA-STRAIN-0 found no synchronized multiscale deformation events.
```

`AQ-PAGE-WOOTTERS-0` moves the alignment question into a controlled, Page-Wootters-inspired history-state simulation. The clock degree of freedom is part of the simulated state, not inferred from unstable cloud timing telemetry.

## Core Question

Can D-LinOSS use a designed internal relational clock to align independent tensor-network histories better than external carrier, null drift, wrong-lag, shuffled-clock, severed-clock, and cross-seed controls?

## Model Classes

Compare the following explanations with identical payloads, seeds, and resource budgets:

| Model | Meaning |
| --- | --- |
| internal_relational_clock | Alignment uses a simulated clock register entangled/correlated with system history. |
| sin_cos_only_relational_clock | Uses the same state-coupled relational phase but omits the explicit curvature observable. |
| external_timing_carrier | Alignment uses an injected external sinusoidal/carrier coordinate. |
| null_drift | Alice/Bob histories evolve independently with no usable shared clock. |
| shuffled_clock | Clock labels are permuted while state history is unchanged. |
| wrong_lag_clock | Clock labels are shifted outside the correct transition window. |
| severed_clock | Clock sequence preserves its distribution but is sampled independently of state history. |
| cross_seed_clock | Clock sequence comes from an independently generated history with the same parameters. |

## Two-Level Design

### AQ-PAGE-WOOTTERS-0a - Sanity Mode

Purpose:

```text
Verify that the implementation can recover a deliberately exposed clock coordinate.
```

Use:

```text
tau_0a(t) = omega * t
clock_0a(t) = [sin(tau_0a(t)), cos(tau_0a(t))]
```

Expected result:

```text
internal_relational_clock should beat shuffled, wrong-lag, severed, cross-seed, and null controls.
```

Passing `0a` validates the clock-matching and heldout-evaluation pipeline. It does not establish a meaningful relational clock because the clock is intentionally close to a hidden timestamp.

### AQ-PAGE-WOOTTERS-0b - State-Coupled Mode

Purpose:

```text
Test whether a state-conditioned internal clock improves heldout transition alignment beyond a matched external oscillator.
```

Define latent state curvature:

```text
kappa(t) = ||z(t + 1) - 2 z(t) + z(t - 1)||_2
K(t) = sum_{s=1}^{t-1} kappa(s)
tau_0b(t) = omega * t + beta * K(t)
clock_0b(t) = [sin(tau_0b(t)), cos(tau_0b(t)), normalized_kappa(t)]
```

`normalized_kappa(t)` is normalized using calibration statistics only. Do not include a learned index embedding, one-hot tick identifier, positional encoding, or any feature computed directly from the payload time index.

Treat `kappa(t)` as part of the generated clock channel. Compute it once from the generated latent history, then freeze that series for calibration and payload analysis. Do not recompute it differently for any payload arm.

Use the preregistered sweep:

```text
beta_candidates = [0.0, 0.1, 0.25, 0.5, 1.0]
```

Select `beta` using calibration transition score only, report `selected_beta`, and freeze it before payload matching. The primary scientific result comes from `0b`, not `0a`.

Add the ablation:

```text
sin_cos_only_relational_clock(t)
  = [sin(tau_0b(t)), cos(tau_0b(t))]
```

This arm uses the same selected state-coupled phase but omits `normalized_kappa(t)`. A gain by the full state-coupled clock therefore tests whether the explicit internal deformation observable contributes beyond a clean two-dimensional phase coordinate.

## History-State Construction

Represent each simulated stream as a normalized Page-Wootters-inspired history state:

```text
|Psi> = (1 / sqrt(Z)) sum_t a_t |t>_C |psi(t)>_S
Z = sum_t |a_t|^2 <psi(t)|psi(t)>
```

where:

```text
|t>_C       = internal clock state
|psi(t)>_S  = folded semantic / coefficient / patch state at internal time t
```

Keep two clock objects distinct:

```text
|t>_C          = orthonormal clock-register basis used to construct |Psi>
clock_feature(t) = low-dimensional observable used by the matching algorithm
```

The sine/cosine/state-curvature feature is not itself assumed to be an orthogonal clock basis.

Normalize each conditional system state:

```text
|psi_bar(t)> = |psi(t)> / sqrt(<psi(t)|psi(t)>)
```

Compute the reduced clock state:

```text
rho_C = Tr_S(|Psi><Psi|)
```

and report:

```text
history_state_norm_error = |<Psi|Psi> - 1|
clock_schmidt_entropy = -Tr(rho_C log rho_C)
clock_system_mutual_information = S(rho_C) + S(rho_S) - S(rho_CS)
```

For a pure normalized history state, `S(rho_CS) = 0` up to numerical precision.

For the first run, keep the state small and synthetic:

```text
smoke_time_steps = 32
minimum_real_time_steps = 64
preferred_real_time_steps = 128
state_dim = 32 or 64
latent_dim = 8
noise = 0.00
seed = 11
```

Use 32 steps only for a smoke test. The reported `0b` run uses 128 steps so the 50/50 payload split provides enough windows for the paired bootstrap interval and the 70% win-fraction gate.

## Payload

Use a controlled state trajectory rather than image reconstruction in the first pass:

```text
x_t = B z_t + residual_t
z_{t+1} = exp(A dt) z_t + b + epsilon_t
clock_0a(t) = [sin(omega t), cos(omega t)]
clock_0b(t) = [sin(tau_0b(t)), cos(tau_0b(t)), normalized_kappa(t)]
```

Generate two histories:

```text
Alice: x_A(t), clock_A(t)
Bob:   x_B(t), clock_B(t)
```

The true relational-clock arm receives the correct internal clock coordinate. Controls receive clocks that preserve marginal statistics but break temporal relation.

The external carrier must be matched in frequency and smoothness:

```text
external_tau(t) = omega * t + eta_smooth(t)
external_clock(t) = [sin(external_tau(t)), cos(external_tau(t))]
```

Construct `eta_smooth(t)` by fitting an AR(1) model to the calibration phase increments:

```text
v(t) = tau_0b(t) - tau_0b(t - 1)
v_ext(t) = mu_v + phi_v * (v_ext(t - 1) - mu_v) + epsilon_t
eta_smooth(t) = cumulative_sum(v_ext(t) - omega)
```

Freeze `mu_v`, `phi_v`, and innovation variance after calibration. Generate payload innovations independently with a fixed seed. The external carrier must not use `K(t)`, `kappa(t)`, payload states, or state-derived deformation terms.

## Calibration/Payload Split

Use a fixed chronological split:

```text
calibration = first 50% of time steps
payload = second 50% of time steps
```

Fit or select all of the following on calibration only:

```text
normalization statistics
B / PCA latent basis
transition operator A or T
clock projection
nearest-neighbor clock metric
lag or phase-offset selection
external carrier phase and smoothness
beta
alpha or any gauge strength
```

Freeze every fitted quantity before evaluating payload data.

For `beta`, evaluate only the preregistered candidates on calibration windows, choose the highest calibration transition score with deterministic lowest-beta tie breaking, and print the selected value in the compact summary.

Anti-leak rule:

```text
The relational-clock arm must not use true payload time indices or t_A = t_B.
```

Payload matching must use one preregistered calibration-fitted rule:

```text
nearest neighbor in normalized clock-state space
```

Clock-conditioned distance:

```text
D_W(A_t, B_t') = arccos(|<psi_A(t)|psi_B(t')>|)
```

may be reported as a diagnostic, but it cannot use target payload states to select `t'`.

## D-LinOSS Task

Fit on calibration windows and evaluate on heldout payload windows:

```text
z_B(t') ~= T z_A(t) + c
```

where `t'` is selected by one of:

```text
internal relational clock match
external carrier phase match
wall-clock / index match
wrong-clock match
shuffled-clock match
severed-clock match
cross-seed clock match
```

Keep the transition operator in latent space:

```text
u_t = B^H (x_t - mu)
u_{t+1} = exp(A dt) u_t + b
x_hat_{t+1} = mu + B u_{t+1}
```

Do not use a rank-1 one-sample map as the primary transition operator.

## Primary Endpoint

```text
relational_clock_alignment_gain
  = payload_score(internal_relational_clock)
    - max(payload_score(shuffled_clock),
          payload_score(wrong_lag_clock),
          payload_score(severed_clock),
          payload_score(cross_seed_clock),
          payload_score(null_drift))
```

Recommended score:

```text
payload_score = cosine(delta_z_true, delta_z_pred)
```

where:

```text
delta_z = z(t + 1) - z(t)
```

This makes the endpoint about transition geometry, not static state similarity.

Also report paired payload-window gains:

```text
g_i = score_i(internal_relational_clock) - max_control score_i(control)
paired_transition_gain_mean = mean_i(g_i)
paired_transition_gain_std = std_i(g_i)
fraction_payload_windows_relational_beats_best_null = mean_i(g_i > 0)
paired_transition_gain_bootstrap_ci95 = bootstrap_95_percent_CI({g_i})
```

## Secondary Metrics

Report:

```text
state_recovery_cos
transition_recovery_cos
clock_phase_error
clock_conditioned_distance
operator_cosine_Bspace
T_unitarity_error
B_isometry_error
external_minus_null_gain
relational_minus_external_gain
state_coupled_minus_sin_cos_only_gain
paired_transition_gain_mean
paired_transition_gain_std
paired_transition_gain_bootstrap_ci95
fraction_payload_windows_relational_beats_best_null
history_state_norm_error
clock_schmidt_entropy
clock_system_mutual_information
```

## Required Controls

| Control | Requirement |
| --- | --- |
| shuffled_clock | Permute clock labels while preserving state distribution. |
| sin_cos_only_relational_clock | Preserve the selected relational phase while withholding the explicit curvature observable. |
| wrong_lag_clock | Use clock labels offset outside the correct transition window. |
| severed_clock | Draw a same-distribution clock sequence independently from state history. |
| cross_seed_clock | Use clock labels generated from an independent trajectory with the same model parameters. |
| external_carrier | Match internal-clock frequency, smoothness, and marginal phase velocity without using state curvature. |
| null_drift | Independent Bob trajectory with no shared transition law. |

## Pass Gates

Gate 0 - no harm:

```text
internal relational clock score >= index/wall-clock score - 0.01
history_state_norm_error < 1e-6
clock_schmidt_entropy > 1e-6
clock_system_mutual_information > 2e-6
```

Gate 1 - relational clock beats controls:

```text
relational_clock_alignment_gain >= 0.10
```

Gate 2 - relational clock beats external carrier:

```text
relational_minus_external_gain >= 0.05
```

State-deformation ablation:

```text
state_coupled_minus_sin_cos_only_gain > 0
```

This ablation is required for a claim that the explicit deformation coordinate contributes. A null ablation does not invalidate clock alignment, but it limits the conclusion to relational phase matching.

Gate 3 - payload relevance:

```text
transition_recovery_cos improves over every clock control
paired_transition_gain_mean > 0
paired_transition_gain_bootstrap_ci95.lower > 0
fraction_payload_windows_relational_beats_best_null >= 0.70
```

Optional later gate:

```text
using the internal clock improves folded-state reconstruction or coefficient alignment
```

## Interpretation

If Gates 1-2 pass:

```text
D-LinOSS can use an explicitly modeled internal clock coordinate to align heldout tensor-network histories better than external carriers and null controls.
```

Promote this statement only from `AQ-PAGE-WOOTTERS-0b`. A passing `0a` result establishes implementation sanity only.

If the run is null:

```text
The designed relational clock, as parameterized here, is not sufficient to improve heldout transition alignment. This is a simulation-design result, not evidence for or against physical time models.
```

## Relationship To CHRONOS

This run does not rescue the CHRONOS external-timing branch. It replaces it with a controlled model-selection experiment.

Paper-safe bridge:

```text
CHRONO-MERA-STRAIN-0 applied a multiscale entropy-strain endpoint to existing CHRONOS Alice/Bob compact timing streams. After correcting the MERA contraction to avoid entropy collapse, the analyzer passed sanity checks on all tested pairs, confirming that the entropy statistic was responsive. However, neither simultaneous entropy-spike co-occurrence nor magnitude-only elasticity alignment exceeded null controls in same-window, +1h-shifted, or replication streams. These results further constrain the CHRONOS timing-coupling hypothesis: marginal timing-feature similarity can occur across TPU hosts, but no synchronized representation-level temporal deformation was detected at the tested resolution.
```

Bottom line:

```text
Close the external timing-coupling branch as a disciplined null and move the alignment work into a designed relational-clock simulation.
```

## Implementation Order

1. Generate a stable latent operator `A` and shared reconstruction basis `B`.
2. Generate Alice and Bob trajectories from the same operator family with independent initial conditions and noise.
3. Build and normalize the joint clock-system history states.
4. Run `0a` with the exposed sinusoidal clock and verify all sanity gates.
5. Run `0b` with the state-curvature clock and the matched external carrier.
6. Fit all projections, operators, matching rules, and hyperparameters on calibration only.
7. Evaluate heldout transition geometry and paired payload-window gains.
8. Proceed to folded-state reconstruction only if `0b` passes.
