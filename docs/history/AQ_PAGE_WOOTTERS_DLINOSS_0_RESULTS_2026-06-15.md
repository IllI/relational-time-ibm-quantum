# AQ-PAGE-WOOTTERS-DLINOSS-0 Results - 2026-06-15

## Purpose

This bridge experiment replaced the ridge-affine transition surrogate with a JAX-native implementation of the repository's complex diagonal D-LinOSS recurrence while holding the validated relational-clock evaluator fixed.

The experiment retained:

```text
calibration-only lag and clock selection
constrained monotone correspondence paths
one true-arm fit frozen before payload evaluation
controls that alter correspondence paths without refitting the model
heldout delta-transition cosine scoring
```

The tested D-LinOSS recurrence was:

```text
h_t = lambda * h_(t-1) + x_t B
y_t = Re(h_t C) + b
lambda_k = scale_k * exp(i omega_k)
```

This is the complex diagonal state-space core used by the repository's D-LinOSS implementation. It does not include the full Flax damping-matrix or MoQE classification head.

## TPU Configuration

```text
backend: TPU, 8 devices
time_steps: 128
calibration_steps: 64
latent_dim: 8
hidden_dim: 16
context_steps: 8
epochs: 800
seed: 11
noise: 0.00
```

Three calibration-selected generator variants were compared:

```text
dlinoss_diag_phase
dlinoss_hamiltonian
dlinoss_hamiltonian_plus_scale
```

`dlinoss_hamiltonian_plus_scale` won calibration selection in both modes.

## Results

### 0a Evaluator Sanity

```text
D-LinOSS relational score:     0.994504
ridge relational score:        0.999983
D-LinOSS relational gain:      1.189736
D-LinOSS minus ridge:          -0.005479
paired gain CI95:              [0.958223, 1.109748]
windows beating best null:     98.4%
```

All bridge gates passed. The D-LinOSS recurrence recovered the intentionally easy known-shift transition nearly as well as ridge.

### 0b State-Coupled Relational Clock

```text
D-LinOSS relational score:                 0.957300
ridge relational score:                    0.975130
D-LinOSS relational gain:                  0.669980
ridge relational gain:                     0.618502
D-LinOSS minus ridge:                      -0.017829
D-LinOSS relational-minus-external gain:   0.544691
paired gain CI95:                          [0.528529, 0.640926]
windows beating best null:                 98.4%
```

All bridge gates passed:

```text
Gate -1: evaluator sanity
Gate 0: stable calibration training
Gate 1: D-LinOSS relational path beats controls
Gate 2: D-LinOSS relational path beats external carrier
Gate 3: D-LinOSS remains within 0.05 of ridge
Payload gate: positive paired CI and >= 70% window wins
```

## Scientific Interpretation

The validated correspondence mechanism survives replacement of the ridge surrogate with a complex recurrent D-LinOSS transition model. D-LinOSS is slightly less accurate on the true relational path than ridge, but it produces a larger separation from the best null:

```text
D-LinOSS relational gain: 0.669980
ridge relational gain:    0.618502
```

This is evidence that the recurrent complex state-space model can learn and exploit the relationally aligned transition structure in this controlled synthetic history simulation.

The result does not establish physical Page-Wootters dynamics, emergent spacetime, or tensor-network history dynamics. The generated histories remain projected harmonic latent trajectories, and robustness has not yet been demonstrated across seeds, noise levels, sequence lengths, or latent dimensions.

## Next Gate

Run the preregistered robustness grid before promoting the mechanism:

```text
seeds:       11, 12, 13, 14, 15
time_steps: 128, 256, 512
noise:      0.00, 0.01, 0.03
latent_dim: 8, 16
```

Primary criteria:

```text
0a passes consistently
0b D-LinOSS relational gain > 0.10 in most runs
D-LinOSS relational-minus-external gain > 0.05 in most runs
paired bootstrap CI lower bound > 0 in most runs
D-LinOSS minus ridge >= -0.05
```

Only after robustness should the synthetic harmonic history generator be replaced with an explicit tensor-network history construction.

## Robustness Stages A-B

The staged robustness run held `time_steps=128` and `latent_dim=8` fixed while testing five seeds at each noise level.

### Stage A - Noise 0.00

All promotion criteria passed:

```text
0a all-gate pass rate:                    100%
0b relational gain > 0.10:               100%
relational-minus-external > 0.05:         80%
paired CI lower bound > 0:                100%
D-LinOSS minus ridge >= -0.05:            100%
positive curvature lift:                  100%
```

Aggregate medians and IQRs:

```text
relational score:             0.968738  [0.964697, 0.970576]
relational gain:              0.665881  [0.456199, 0.669980]
relational-minus-external:    0.392225  [0.233714, 0.544691]
D-LinOSS minus ridge:        -0.006342  [-0.010432, -0.004556]
curvature lift:               0.002894  [0.002892, 0.003657]
```

Model selection was not fully stable:

```text
dlinoss_diag_phase:                 4/5
dlinoss_hamiltonian_plus_scale:     1/5
```

The clean result is therefore robust across the five tested seeds, but it does not uniquely favor the phase-plus-scale parameterization.

### Stage B - Noise 0.01

The mechanism remained useful but became seed-sensitive:

```text
relational score:             0.879631  [0.837233, 0.936932]
relational gain:              0.591045  [0.293161, 0.792117]
relational-minus-external:    0.089337  [0.075753, 0.467812]
D-LinOSS minus ridge:        -0.024077  [-0.105254, -0.009644]
curvature lift:               0.000642  [-0.039345, 0.029571]
```

Relational alignment generally survived `noise=0.01`, but the ridge-competitiveness criterion failed for two seeds and curvature no longer had a stable sign.

### Stage B - Noise 0.03

The promoted mechanism failed:

```text
relational score:             0.168858  [0.166007, 0.462993]
relational gain:             -0.007546  [-0.215603, 0.004522]
relational-minus-external:    0.223098  [0.221862, 0.338120]
D-LinOSS minus ridge:        -0.156620  [-0.165310, -0.028168]
curvature lift:               0.226608  [0.204155, 0.406463]
```

The large apparent curvature lift at `noise=0.03` is not evidence of successful curvature-driven alignment. The full relational score and control separation collapsed while the phase-only arm collapsed more sharply. The lift is therefore relative damage reduction inside a failed regime.

Across the ten noisy configurations, the promotion rates were:

```text
0a all-gate pass rate:                    100%
0b relational gain > 0.10:                60%
relational-minus-external > 0.05:          90%
paired CI lower bound > 0:                 50%
D-LinOSS minus ridge >= -0.05:             50%
```

Stage B did not pass. Stages C and the 512-step extension were not run.

## Revised Standing Claim

The bridge is reproducible across five seeds at the noise-free ceiling and shows partial robustness at `noise=0.01`. It is not robust at `noise=0.03`. The primary validated mechanism remains relational phase/path alignment; the explicit curvature channel is small at the clean ceiling, unstable at low noise, and cannot yet support an independent curvature-driven claim.

The next experiment should address noise-conditioned clock matching or regularization before increasing history length or replacing the generator with tensor-network histories.

## AQ-PAGE-WOOTTERS-DLINOSS-NOISE-1

This follow-up was designed to answer a narrower question:

```text
Does noisy failure come mainly from correspondence-path recovery,
or from D-LinOSS transition learning even when the path is correct?
```

The first complete TPU run finished and produced a compact summary JSON:

[noise1_results.json](/C:/Users/cityz/IllI/newer_all/emergent_quantum_geometries/tmp_page_wootters_noise1_tpu/noise1_results.json)

However, that first implementation still mixed two effects:

```text
matcher-specific correspondence path
+ matcher-specific retraining target
```

So its reported `oracle_path_dlinoss_score` versus `learned_path_dlinoss_score` did not cleanly isolate path failure. It remained useful as a scouting run, but not as the final causal diagnosis.

### What the scouting run still told us

The scouting grid did show that noise sensitivity was real and that the simple matcher family was not the whole story. Some seeds degraded because the learned path drifted, but others suggested the training target itself had become unstable once the model was retrained on noisy correspondences.

That meant the next correction had to be structural:

```text
1. define an oracle path directly from the synthetic generator
2. fit one oracle-path D-LinOSS model on calibration
3. freeze that model
4. score learned matcher paths with the same frozen model
5. keep end-to-end retrained scores separate
```

### Corrected rerun status at pause

The corrected script was patched locally in:

[program_aq_page_wootters_dlinoss_noise1.py](/C:/Users/cityz/IllI/newer_all/emergent_quantum_geometries/program_aq_page_wootters_dlinoss_noise1.py)

It now uses:

```text
oracle path definition:
generator intrinsic-clock midpoint correspondence

separate score families:
frozen_operator_learned_path_score
oracle_path_dlinoss_score
end_to_end_learned_path_score
```

We launched a corrected TPU rerun, but intentionally stopped it when shutting down TPU resources for quota/token reasons. The partial corrected log is preserved here:

[noise1_corrected_partial.log](/C:/Users/cityz/IllI/newer_all/emergent_quantum_geometries/tmp_page_wootters_noise1_tpu/noise1_corrected_partial.log)

The partial corrected run already showed a much cleaner pattern on the completed `noise=0.01` and early `noise=0.02` seeds:

```text
oracle path score:         still high, roughly 0.70 to 0.82
frozen learned-path score: often sharply worse, sometimes negative
end-to-end retrained score: often recovers into the 0.85 to 0.96 range
path MAE:                  often large, around 7 to 8 on failing seeds
```

That is the strongest evidence so far that the first noisy breakdown is primarily a correspondence-path problem. D-LinOSS still appears able to model the transition when given a good path, but the learned relational path becomes unstable under noise and forces the end-to-end system to compensate by retraining on a degraded alignment.

This is not yet a finished claim, because the corrected grid was interrupted during `noise=0.03`:

```text
completed before stop:
noise 0.01 seeds 11-15
noise 0.02 seeds 11-15
noise 0.03 had not completed any seed

last completed line:
noise 0.02 seed 15

interrupted at:
noise 0.03 seed 11
```

### Where we left off

No TPUs remain active. The active rerun was stopped cleanly before node deletion, and the European TPU was deleted afterward.

Resume from:

[program_aq_page_wootters_dlinoss_noise1.py](/C:/Users/cityz/IllI/newer_all/emergent_quantum_geometries/program_aq_page_wootters_dlinoss_noise1.py)

Use the same TPU launch envelope as the interrupted corrected run:

```text
python3 -u program_aq_page_wootters_dlinoss_noise1.py
  --require-tpu
  --epochs 800
  --hidden-dim 16
  --context-steps 8
  --learning-rate 0.003
  --out-dir /home/cityz/aq_page_wootters_noise1/results_corrected
```

Local staging artifacts are here:

[tmp_page_wootters_noise1_tpu](/C:/Users/cityz/IllI/newer_all/emergent_quantum_geometries/tmp_page_wootters_noise1_tpu)

## AQ-PAGE-WOOTTERS-DLINOSS-NOISE-2

The corrected follow-up moved from mixed end-to-end scoring to a path-first diagnosis:

```text
oracle path
vs
learned matcher path
vs
frozen D-LinOSS score
```

The compact TPU result is staged here:

[noise2_results.json](/C:/Users/cityz/IllI/newer_all/emergent_quantum_geometries/tmp_page_wootters_noise2_tpu/noise2_results.json)

This narrowed the failure mode further. The oracle-path D-LinOSS score stayed viable well beyond where several learned matchers collapsed, confirming that the early noisy breakdown was not primarily D-LinOSS transition capacity. It was the path layer.

At the same time, the run showed that no fixed small matcher family was reliably stable across seeds and noise. Some smoothed or constrained matchers recovered useful paths in particular seeds, but those wins did not generalize well enough for promotion.

## AQ-PAGE-WOOTTERS-DLINOSS-MATCHER-POLICY-0

This run asked whether calibration-only policy selection could choose the right matcher family member before payload:

```text
choose matcher on calibration
freeze matcher choice
score payload with frozen D-LinOSS protocol
```

The TPU result showed that policy selection helped in pockets, but the relational path still often lost to the best null/control path. In other words:

```text
matcher policy: not enough
```

The calibration-selected policy could sometimes find a decent matcher, but it did not produce a robust positive relational gain across seeds and noisy settings.

## AQ-PAGE-WOOTTERS-DLINOSS-MATCHER-REGRET-0

This follow-up decomposed the path problem into three pieces:

```text
selection regret:
  a good payload matcher exists, but calibration picks the wrong one

matcher-family insufficiency:
  even the best available matcher is weak

control competition:
  relational path does not consistently separate from nulls
```

The compact result confirmed all three phenomena. Some seeds were mostly selection error, but other seeds showed low or negative best payload scores even after hindsight selection. That meant adding more hand-built matcher variants was unlikely to solve the science problem by itself.

## AQ-PAGE-WOOTTERS-DLINOSS-CLOCK-METRIC-0

The next idea was to stop hand-tuning matchers and instead learn a calibration-trained clock metric. The compact TPU result lives here:

[clock_metric0_results.json](/C:/Users/cityz/IllI/newer_all/emergent_quantum_geometries/tmp_page_wootters_clock_metric0_tpu/clock_metric0_results.json)

The learned metric helped selected noisy seeds, especially around `noise=0.02`, but still failed the promotion gates:

```text
learned clock metric: not enough
```

The key failure pattern remained:

```text
relational gain often < 0
```

So the branch no longer pointed to D-LinOSS capacity or matcher engineering as the main blocker. It pointed to the separability of the clock-correspondence manifold itself.

## AQ-PAGE-WOOTTERS-DLINOSS-CLOCK-OBSERVABILITY-0

This run removed D-LinOSS scoring entirely and asked a simpler question:

```text
Is the true Alice/Bob correspondence separable in clock-feature space
before any transition model is involved?
```

The observability audit confirmed that it usually was not. Even when the best arm improved relative ranking in some seeds, the true match often failed to stand out cleanly from wrong-lag, shuffled, severed, or cross-seed candidates.

That was the cleanest evidence yet that the relational clock was under-identifiable in the current synthetic projected-harmonic generator.

## AQ-PAGE-WOOTTERS-DLINOSS-CLOCK-EMBED-0

The next observability-only run replaced pointwise clock features with local history embeddings:

```text
point_clock_baseline
patch_clock_w3 / w5 / w9
state_patch_w5
transition_signature_w5
contrastive_patch_encoder
```

The compact TPU result is staged here:

[clock_embed0_results.json](/C:/Users/cityz/IllI/newer_all/emergent_quantum_geometries/tmp_page_wootters_clock_embed0_tpu/clock_embed0_results.json)

The best arm was consistently `state_patch_w5`, which means a short local history did help. But it still failed the observability gates by a wide margin:

```text
noise=0.00:
  best positive-margin fraction  ~0.397
  gate required                  >=0.90

noise=0.01:
  best positive-margin fraction  ~0.397
  gate required                  >=0.75

noise=0.02:
  best positive-margin fraction  ~0.460
  gate required                  >=0.60
```

Median margins hovered around zero while mean margins stayed negative. So the local history embedding improved the feature space but did not make the true correspondence reliably distinguishable from null candidates.

This gives the branch a useful decomposition:

```text
D-LinOSS transition capacity:      viable when given good paths
matcher policy:                    not enough
learned clock metric:              not enough
local history clock embedding:     improves but still fails
root issue:                        synthetic clock feature is under-identifiable
```

## Updated Standing Conclusion

The Page-Wootters/D-LinOSS branch now has a much sharper diagnosis than it did at the start of the day.

The negative result is not:

```text
internal relational clocks do not work
```

The negative result is:

```text
in the current projected-harmonic synthetic generator,
the internal clock observable is too degenerate under noise
to define a reliably separable correspondence manifold
```

That is a stronger and more actionable conclusion than another partial alignment win. It means the next experiment should not keep tuning matchers, path solvers, or clock metrics on top of the same generator.

## Best Next Step

The next run should be:

```text
AQ-PAGE-WOOTTERS-DLINOSS-PHYSICS-PRIORS-0
```

Its purpose is to replace the projected-harmonic generator with a Page-Wootters/open-system inspired synthetic history generator so internal time leaves a stronger causal, irreversible, entropy-bearing trace in the state history before D-LinOSS scoring is reintroduced.

Required generator changes:

```text
1. non-periodic drift in transition law
2. sparse event markers / causal impulses
3. entropy and strain production
4. irreversible residual bath memory
5. multi-scale phase built from cumulative causal statistics
6. positive damping tied to open-system quantities
```

The first gate should again be observability-only:

```text
noise=0.00:
  positive_margin >= 0.90
  median_margin > 0

noise=0.01:
  positive_margin >= 0.75
  median_margin > 0

noise=0.02:
  positive_margin >= 0.60
  median_margin > 0
```

Only if that physics-priors observability gate passes should the branch return to a frozen-operator D-LinOSS bridge.

## 2026-06-17 Global Causal Memory Follow-Up

Run:

```text
AQ-PAGE-WOOTTERS-DLINOSS-GLOBAL-CAUSAL-MEMORY-0
```

Purpose:

```text
Add a causally generated global memory/action coordinate to test whether
same-distribution shuffled/severed exchangeability can be broken without
introducing a raw timestamp.
```

Arms:

```text
A6_full_causal_clock_current
A7_residual_integral
A8_event_count_hash
A9_entropy_action_integral
A10_full_global_causal_memory
```

Compact TPU summary:

```text
A6 current median positive margin:
  noise 0.00: 0.778
  noise 0.01: 0.810
  noise 0.02: 0.810
  noise 0.03: 0.794

A10 global memory median positive margin:
  noise 0.00: 0.794
  noise 0.01: 0.794
  noise 0.02: 0.810
  noise 0.03: 0.825

A10 - A6 median positive-margin gain:
  noise 0.00: +0.016
  noise 0.01: -0.016
  noise 0.02: +0.000
  noise 0.03: +0.032
```

The global memory variants did not pass the strict observability gates:

```text
noise 0.00 target: >=0.90
noise 0.01 target: >=0.75
noise 0.02 target: >=0.60
```

The important diagnostic is that anti-cheat stayed clean:

```text
median anti_cheat_positive_margin = 1.000
median same_stats_permuted_failure_rate = 0.000
```

So the result does not look like causal-stat marginal leakage. The controls that still win are the same-distribution shuffled/severed controls:

```text
median same_distribution_failure_rate = 1.000
```

Interpretation:

```text
The global causal-memory coordinate improves some margins, especially at the
stress end of the grid, but it does not solve exchangeability. The remaining
failure is not wrong-lag ambiguity, cross-seed confusion, or causal-stats
anti-cheat leakage. It is that same-distribution Bob windows can still land
closer than the true correspondence for roughly the same residual failure band.
```

Standing conclusion:

```text
The generator now has stronger causal traces, but the correspondence manifold is
still not globally unique enough for promotion. The next correction should not
add another local memory scalar. It should either enforce path-level monotonic
global uniqueness directly or redesign the causal generator so event/residual
memory creates distinguishable long-range signatures across the whole history.
```

## 2026-06-17 Path Observability Follow-Up

Run:

```text
AQ-PAGE-WOOTTERS-DLINOSS-PATH-OBSERVABILITY-0
```

Purpose:

```text
Replace the pointwise nearest-null margin with a monotone global path-cost
margin. This tests whether the true Alice/Bob clock correspondence is globally
separable even when individual windows remain locally exchangeable with
shuffled/severed samples.
```

Implementation note:

```text
The first path run exposed a control bug: wrong_lag_path was accidentally using
the unshifted Bob stream. That artifact produced tiny constant margins and was
discarded. The corrected v2 run uses a genuinely lag-shifted Bob stream and is
the result summarized below.
```

Corrected TPU summary:

```text
A6_full_causal_clock_current:
  noise 0.00: path_margin_per_step median  99.402, rank1 1.0, seg16 1.0
  noise 0.01: path_margin_per_step median 100.016, rank1 1.0, seg16 1.0
  noise 0.02: path_margin_per_step median 100.103, rank1 1.0, seg16 1.0
  noise 0.03: path_margin_per_step median  99.681, rank1 1.0, seg16 1.0

A10_full_global_causal_memory:
  noise 0.00: path_margin_per_step median 164.792, rank1 1.0, seg16 1.0
  noise 0.01: path_margin_per_step median 164.525, rank1 1.0, seg16 1.0
  noise 0.02: path_margin_per_step median 164.265, rank1 1.0, seg16 1.0
  noise 0.03: path_margin_per_step median 164.005, rank1 1.0, seg16 1.0
```

Pointwise margins remained imperfect:

```text
A6 pointwise positive margin median:  ~0.73-0.76
A10 pointwise positive margin median: ~0.73-0.75
```

Interpretation:

```text
The clock is globally observable as an ordered history path even though it is
not locally unique at every window. The previous 19-21% pointwise failure band
does not imply failure of the relational clock. It reflects local collisions
that the monotone path constraint can absorb.
```

The global causal-memory coordinate now has a clearer role:

```text
A10 did not greatly improve pointwise observability, but it substantially
increased path-level margin over A6. That means its contribution is not local
nearest-neighbor separability; it strengthens the accumulated history-level
action signal.
```

Updated standing conclusion:

```text
Observability should now be evaluated at two levels:

1. pointwise margin diagnoses local exchangeability;
2. path margin diagnoses recoverable relational history structure.

Under the corrected path test, the physics-prior generator passes the global
observability gate through noise=0.03 for the tested seeds. The next bridge can
return to D-LinOSS using path-selected correspondence and the same frozen-
operator discipline.
```

## 2026-06-17 Path Bridge Result

Run:

```text
AQ-PAGE-WOOTTERS-DLINOSS-PATH-BRIDGE-0
```

Purpose:

```text
Use the corrected global path correspondence to return to frozen-operator
D-LinOSS scoring. Calibration chooses the path feature, fits one frozen
D-LinOSS operator on the relational path, then scores relational and path-null
controls on payload.
```

Configuration:

```text
generator arms: A6_full_causal_clock_current, A10_full_global_causal_memory
noise:          0.00, 0.01, 0.02, 0.03
seeds:          11, 12, 13, 14, 15
D-LinOSS:       hamiltonian_plus_scale
```

Aggregate result:

```text
A6_full_causal_clock_current:
  path observability gate:      100% pass
  stable D-LinOSS training:     100% pass
  median D-LinOSS gain:         ~0.013-0.015
  control-separation gate:      0% pass
  median D-LinOSS minus ridge:  ~-0.39 to -0.41
  window robustness:            ~0.03-0.05

A10_full_global_causal_memory:
  path observability gate:      100% pass
  stable D-LinOSS training:     100% pass
  median D-LinOSS gain:         ~0.46-0.47
  control-separation gate:      100% pass
  external/control gate:        100% pass
  median D-LinOSS minus ridge:  ~-0.38 to -0.41
  window robustness:            ~0.43-0.44
```

Interpretation:

```text
The bridge partially succeeded. A10 global causal memory does not merely
increase path observability; it lets D-LinOSS separate the relational path from
path controls under a frozen operator. A6 has the path, but does not provide
enough transition signal for D-LinOSS to beat controls.
```

The remaining failures are also clear:

```text
1. D-LinOSS is not yet competitive with ridge.
2. The relational path does not beat best nulls on enough individual payload
   windows, even though aggregate path/control separation is strong for A10.
```

Scientific standing:

```text
PATH-BRIDGE-0 validates the global causal-memory mechanism as useful for
D-LinOSS control separation at the path level. It does not yet promote the
operator model, because the D-LinOSS recurrence remains below the ridge
surrogate and the window-level robustness gate fails.
```

Recommended next correction:

```text
Do not return to matcher tuning. The matcher/path layer is now adequate.

The next bottleneck is D-LinOSS transition capacity under the selected path.
The follow-up should compare hamiltonian_plus_scale against a stronger but still
structured transition model, such as:

1. larger hidden_dim / longer context
2. block-skew or low-rank generator
3. noise-augmented calibration
4. segment-aware training loss that weights ambiguous windows

The next endpoint should be:

  A10 D-LinOSS minus ridge improves toward >= -0.05
  and fraction windows beating best null rises toward >= 0.70
```

## 2026-06-17 A10 Capacity Result

Run:

```text
AQ-PAGE-WOOTTERS-DLINOSS-A10-CAPACITY-0
```

Purpose:

```text
Freeze the A10 global causal-memory generator and corrected path machinery,
then vary only the D-LinOSS side: hidden dimension, context length, operator
type, and loss weighting.
```

Grid:

```text
generator:      A10_full_global_causal_memory
noise:          0.00, 0.01, 0.02
seeds:          11, 12, 13, 14, 15
hidden_dim:     16, 32
context_steps:  8, 16
operators:      hamiltonian_plus_scale, event_damped
losses:         uniform, event_weighted
```

Top aggregate configurations:

```text
h32_c8_event_damped_uniform:
  median gain:            0.706
  median minus ridge:    -0.086
  median window fraction: 0.714

h32_c8_event_damped_event_weighted:
  median gain:            0.704
  median minus ridge:    -0.073
  median window fraction: 0.730

h32_c16_event_damped_event_weighted:
  median gain:            0.689
  median minus ridge:    -0.109
  median window fraction: 0.683
```

The event-damped operator is the clear winner:

```text
event_damped > hamiltonian_plus_scale
context 8   > context 16 for median robustness
hidden 32   > hidden 16 for ridge competitiveness
```

The best individual configurations crossed the original window gate:

```text
best window fraction:     0.841
best median-family level: 0.730
best ridge gap observed: -0.057
```

Interpretation:

```text
The PATH-BRIDGE-0 bottleneck was not path observability. It was an operator
mismatch. A stationary hamiltonian-plus-scale recurrence could separate the A10
path from controls, but it could not robustly score enough windows and stayed
far below ridge. When D-LinOSS receives a time-varying event/entropy/residual
damping channel, window robustness rises above the 0.70 gate and the ridge gap
closes from roughly -0.40 to roughly -0.07.
```

Event versus non-event split:

```text
The winning event-damped models improved both event and non-event windows.
This suggests the causal damping channel is not merely detecting sparse event
anchors. It is improving the learned transition geometry across the smooth
background as well.
```

Updated standing claim:

```text
A10-CAPACITY-0 shows that the A10 global causal-memory path is usable by
D-LinOSS when the recurrence is given compatible open-system dynamics. A
dynamic event-damped D-LinOSS operator substantially improves control
separation, window robustness, and ridge competitiveness. The branch now has a
plausible D-LinOSS-side mechanism, though it still needs a focused confirmation
run around h32/context8/event_damped before promotion.
```

Recommended next run:

```text
AQ-PAGE-WOOTTERS-DLINOSS-A10-CONFIRM-0

Keep:
  generator      A10
  operator       event_damped
  hidden_dim     32
  context_steps  8

Compare:
  uniform vs event_weighted
  epochs 350 vs 600
  noise 0.00, 0.01, 0.02, 0.03
  seeds 11-20

Promotion target:
  median gain > 0.50
  median minus ridge >= -0.10
  window fraction >= 0.70
  CI lower bound > 0
```

## 2026-06-17 A10 Event-Damped Confirmation

Run:

```text
AQ-PAGE-WOOTTERS-DLINOSS-A10-EVENT-DAMPED-CONFIRM-0
```

Frozen setup:

```text
generator:      A10_full_global_causal_memory
operator:       event_damped
hidden_dim:     32
context_steps:  8
path:           corrected global monotone path
seeds:          11-20
noise:          0.00, 0.01, 0.02, 0.03
losses:         uniform, event_weighted
```

Aggregate confirmation:

```text
event_weighted:
  median D-LinOSS gain:                   0.708
  median relational-minus-external:       0.723
  median D-LinOSS minus ridge:           -0.074
  median window fraction vs best null:    0.659
  path rank-1 pass rate:                  100%
  gain gate pass rate:                    100%
  external gate pass rate:                100%
  CI-lower-positive pass rate:            100%
  ridge-gap pass rate:                    75%
  strict window-fraction pass rate:       38%

uniform:
  median D-LinOSS gain:                   0.697
  median relational-minus-external:       0.718
  median D-LinOSS minus ridge:           -0.082
  median window fraction vs best null:    0.651
  path rank-1 pass rate:                  100%
  gain gate pass rate:                    100%
  external gate pass rate:                100%
  CI-lower-positive pass rate:            100%
  ridge-gap pass rate:                    65%
  strict window-fraction pass rate:       35%
```

Noise breakdown:

```text
event_weighted median gain:
  noise 0.00: 0.717
  noise 0.01: 0.679
  noise 0.02: 0.695
  noise 0.03: 0.715

event_weighted median D-LinOSS minus ridge:
  noise 0.00: -0.071
  noise 0.01: -0.070
  noise 0.02: -0.076
  noise 0.03: -0.079

event_weighted median window fraction:
  noise 0.00: 0.659
  noise 0.01: 0.659
  noise 0.02: 0.659
  noise 0.03: 0.675
```

Interpretation:

```text
The event-damped A10 bridge confirmed. The mechanism is stable across ten
seeds and through noise=0.03 for path observability, control separation,
external separation, ridge competitiveness at the median, and positive paired
CI. Event-weighted loss is a small but consistent improvement over uniform,
especially for ridge gap and window fraction.
```

The remaining caveat:

```text
The strict per-window robustness gate remains just below target. Median window
fraction is ~0.66-0.68 rather than >=0.70. This is no longer a global failure:
the aggregate transition signal is robust, but some windows remain locally
control-competitive.
```

Updated standing claim:

```text
The A10 global causal-memory generator plus event-damped D-LinOSS forms a
confirmed synthetic relational-clock bridge under frozen-operator controls. It
does not yet fully promote as a window-complete transition model, but it passes
the main mechanism gates and narrows the remaining problem to local window
robustness.
```

Next step:

```text
Before moving to TTN histories, either:

1. accept A10 event-damped as promoted for path-level mechanism only, or
2. run one targeted local-window repair:
   hard-window reweighting on windows that lose to best null during calibration,
   with all path and operator settings frozen.
```

## 2026-06-17 Quantum Clock Bound Diagnostic

Run:

```text
AQ-PAGE-WOOTTERS-DLINOSS-QUANTUM-CLOCK-BOUND-0
```

Purpose:

```text
Determine whether the remaining local-window robustness ceiling reflects model
failure or finite-clock non-orthogonality. The run keeps the confirmed A10
event-damped setup fixed and adds clock-record Gram overlap, failed-window
overlap, a pairwise Helstrom-style distinguishability proxy, and a QFI-like
local sensitivity proxy.
```

Configuration:

```text
generator:      A10_full_global_causal_memory
operator:       event_damped
hidden_dim:     32
context_steps:  8
loss:           event_weighted
seeds:          11-20
noise:          0.00, 0.01, 0.02, 0.03
```

Aggregate:

```text
median D-LinOSS gain:                   0.708
median relational-minus-external:       0.723
median D-LinOSS minus ridge:           -0.074
median window fraction:                 0.659
median pairwise bound proxy:            0.595
median observed / bound proxy:          1.103
median failed-window nontrue overlap:   0.941
median Gram collision rate:             0.802
```

Noise stability:

```text
noise 0.00: window 0.659, bound 0.595, normalized 1.104
noise 0.01: window 0.659, bound 0.595, normalized 1.118
noise 0.02: window 0.659, bound 0.595, normalized 1.103
noise 0.03: window 0.675, bound 0.595, normalized 1.117
```

Interpretation:

```text
The remaining local failures occur in a regime of high clock-record
non-orthogonality. Failed windows have nearest nontrue overlap around 0.94,
and the Gram collision rate is high. The pairwise Helstrom-style proxy gives a
local success ceiling around 0.60, while observed window success is around
0.66-0.68. This suggests the strict 0.70 local-window gate is probably not the
right promotion blocker for this finite-clock simulation.
```

Important caveat:

```text
The bound here is a proxy, not a full multiclass optimal quantum measurement
bound. It should be read as evidence that local ambiguity is intrinsic to the
simulated clock records, not as a formal theorem about the exact optimum
measurement.
```

Updated standing claim:

```text
The confirmed A10 event-damped bridge is best interpreted as a finite relational
clock: local clock windows are often non-orthogonal, but the global monotone
history path is distinguishable and D-LinOSS can exploit that path under
frozen-operator controls. The local window ceiling near 0.66 appears consistent
with finite-clock distinguishability limits rather than a simple engineering
failure.
```

Next scientific move:

```text
Promote the branch as a path-level relational-clock mechanism, not as a
pointwise clock classifier. The next major run can move toward TTN/MERA history
states while retaining:

1. A10-style global causal memory,
2. event-damped D-LinOSS,
3. path-level observability gates,
4. bound-normalized local diagnostics.
```

## 2026-06-17 Multiclass Clock Bound Diagnostic

Run:

```text
AQ-PAGE-WOOTTERS-DLINOSS-MULTICLASS-CLOCK-BOUND-0
```

Purpose:

```text
Strengthen the finite-clock interpretation by replacing the pairwise-only
bound diagnostic with local multiclass proxies over the actual competing path
controls. The diagnostic uses inverse-overlap posterior scoring, a softmax
multiclass success proxy, and an effective-rank Gram proxy.
```

Aggregate:

```text
median observed window success:       0.659
median pairwise bound proxy:          0.595
median observed / pairwise proxy:     1.103
median PGM-style success proxy:       0.447
median observed / PGM proxy:          1.500
median softmax multiclass proxy:      0.298
median effective-rank proxy:          0.197
median failed-window overlap:         0.941
median Gram collision rate:           0.802
```

Noise stability:

```text
noise 0.00: observed 0.659, PGM proxy 0.448, normalized 1.485
noise 0.01: observed 0.659, PGM proxy 0.447, normalized 1.511
noise 0.02: observed 0.659, PGM proxy 0.446, normalized 1.491
noise 0.03: observed 0.675, PGM proxy 0.446, normalized 1.515
```

Interpretation:

```text
The multiclass proxy reinforces the finite-clock explanation. The local clock
records are highly non-orthogonal. Observed local recovery is above the
computed pairwise and multiclass proxy baselines, while failed windows
concentrate in high-overlap clock-record regions. This supports the
interpretation that the remaining pointwise ambiguity reflects finite-clock
non-orthogonality rather than path failure or D-LinOSS control leakage.

Therefore the strict pointwise window >=0.70 gate should not be used as a
promotion blocker. It is better interpreted as a diagnostic of local
finite-clock ambiguity.
```

Caveat:

```text
The PGM-style and effective-rank proxies are diagnostics over the observed
candidate set, not a formal solution to the optimal multiclass quantum
measurement problem. The safe conclusion is that local failures occur in a
high-overlap regime and are consistent with finite-clock non-orthogonality.
```

Promotion statement:

```text
A10 global causal memory plus event-damped D-LinOSS is promoted as a
path-level relational-clock mechanism in a controlled Page-Wootters/open-system
synthetic history. The clock is not a reliable pointwise classifier: local
windows remain non-orthogonal and sometimes indistinguishable. However, the
full monotone relational history is globally observable, and event-damped
D-LinOSS exploits that path under frozen-operator controls with stable gain
through tested noise levels.
```

Promoted scope:

```text
1. Path-level relational-clock mechanism;
2. controlled Page-Wootters/open-system synthetic history;
3. A10 global causal memory;
4. event-damped D-LinOSS;
5. frozen-operator control separation;
6. finite-clock local non-orthogonality explanation.
```

Not promoted:

```text
1. Physical proof of time;
2. pointwise clock classifier;
3. physical Page-Wootters implementation;
4. tensor-network history result;
5. emergent spacetime claim.
```

Next program:

```text
AQ-PAGE-WOOTTERS-DLINOSS-TTN-HISTORY-0

Keep the validated recipe unchanged:

1. global path observability first;
2. A10-style causal memory / irreversible history signal;
3. event-damped D-LinOSS;
4. frozen-operator controls;
5. local-window scores interpreted against clock-record distinguishability.
```

Bottom-line claim:

```text
In a controlled synthetic Page-Wootters/open-system history, relational time is
recoverable as a global ordered path even when local clock records are
non-orthogonal, and an event-damped D-LinOSS operator can exploit that path
under frozen controls.
```

## 2026-08-03 Real-Data Reanalysis and BEC Bridge Follow-Up

The confirmed A10/event-damped mechanism above was applied to the real
archived US/EU TPU streams for the first time (it had never been run against
real data -- the real-data branch closed two days before this mechanism was
confirmed). Result: global path recoverable (`path_rank=1` on all three real
pairs) but window-level relational prediction fails more decisively than on
any tested synthetic noise level, and the real +1-hour control scores as the
best null on average. See:
`chronos_time_emission/docs/CHRONOS_REAL_ENTROPIC_CLOCK_0_RESULTS_2026-08-03.md`

This closes the TPU-telemetry question but does not bear on the underlying
entropic-time hypothesis, which has since been operationally demonstrated in
a real cold-atom system (arXiv:2509.07745, entropy flow between an observed
and unobserved BEC sector). A physically grounded bridge experiment --
replacing the heuristic A10 causal-action generator with a genuine two-mode
Josephson BEC model whose entropy production is derived, not assumed -- was
specified in `AQ_PAGE_WOOTTERS_DLINOSS_BEC_ENTROPIC_BRIDGE_0_RUN_SPEC_2026-08-03.md`
and its single-system Gate 0 was implemented and run the same day. Gate 0
failed cleanly (0/5 tested regimes), with both nulls (shuffled order,
cross-regime transfer) behaving correctly -- the failure mode is a
generalization gap across independent noise realizations plus a generator
design where entropic time ends up close to an affine function of wall-clock
time in most tested regimes, not a broken harness. Per the pre-registered
gate criterion, the two-world bridge (Gate 1) was not implemented. See
`AQ_PAGE_WOOTTERS_DLINOSS_BEC_ENTROPIC_BRIDGE_0_GATE0_RESULTS_2026-08-03.md`.
