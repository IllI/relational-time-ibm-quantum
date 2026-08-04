# CHRONO-MERA-STRAIN-0 Run Spec - 2026-06-15

## Purpose

`CHRONO-MERA-STRAIN-0` tests whether independent CHRONOS timing streams show synchronized multiscale entropy deformation events, without selecting Schumann, grid, infrastructure timing, or a relational-clock model in advance.

The endpoint asks:

```text
Do both systems undergo representation-level phase transitions at the same time?
```

This is deliberately different from asking whether raw timing streams correlate in a selected band.

## Inputs

Use existing compact CHRONOS Q streams only:

```text
alice_us_chrono0_q.json
bob_eu_chrono0_q.json
bob_eu_chrono0_plus1h_q.json
alice_us_rep1_q.json
bob_eu_rep1_q.json
```

No new TPU run is required.

## Analyzer

Implementation:

```text
chronos_time_emission/chronos_mera_strain_0.py
```

Core parameters:

```text
WINDOW_SIZE = 256
HOP = 128
BOND_DIM = 16
CONTEXT_LEAVES = 16
MIN_COARSE_SITES = 8
N_NULL = 1000
```

The required fix is:

```text
MIN_COARSE_SITES = 8
```

This stops the contraction at:

```text
16 leaves -> 8 coarse sites
```

The left/right entropy split therefore has 4 sites per side, avoiding the rank collapse seen when contracting to 4 coarse sites.

## Controls

Primary null controls:

```text
shuffle
block shuffle
phase surrogate
same-distribution AR(1) surrogate
wrong-time shift
```

The same-distribution surrogate preserves:

```text
empirical marginal distribution
approximate AR(1) persistence
```

It destroys:

```text
event timing
Alice/Bob phase relation
```

The phase surrogate pins DC and Nyquist phases while preserving power spectrum and destroying phase timing.

## Endpoints

Primary:

```text
simultaneous_entropy_spike_gain
  = true_paired_spike_score_f1 - max(null_99, wrong_time_score)
```

Secondary:

```text
elasticity_alignment_gain
  = corr(|dS_A/dt|, |dS_B/dt|)
    - (null_mean + 2 * null_std)
```

Also report signed elasticity:

```text
corr(dS_A/dt, dS_B/dt)
```

## Gates

Gate 0 - Analyzer sanity:

```text
entropy_range_sanity > 1e-4
severed_spike_score_sanity < 0.5
```

Gate 1 - Shared deformation event:

```text
true_paired_spike_score_f1 > null_99
p_phase <= 0.01
p_same_dist <= 0.01
```

Gate 2 - Elasticity alignment:

```text
elasticity_alignment_gain > 0
elasticity_p_mag <= 0.01
```

## Results

Three offline analyses were run with `N_NULL = 1000`.

| pair | Gate 0 | Gate 1 | Gate 2 | entropy range | spike gain | r_mag elasticity | elasticity gain | p_mag |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| chrono0 same-window | PASS | FAIL | FAIL | 0.584368 | +0.0000 | -0.0186 | -0.1953 | 0.5920 |
| chrono0 plus1h Bob | PASS | FAIL | FAIL | 0.584368 | +0.0000 | -0.0505 | -0.2544 | 0.6570 |
| rep1 same-window | PASS | FAIL | FAIL | 0.740030 | +0.0000 | +0.0261 | -0.1812 | 0.4200 |

## Interpretation

Gate 0 passed in all tested pairs, so the MERA entropy statistic is responsive after the `MIN_COARSE_SITES = 8` fix. The analyzer did not collapse to a constant entropy series.

Gates 1 and 2 failed in all tested pairs. There was no evidence for synchronized multiscale entropy spike events or magnitude-only elasticity alignment at the current 256-second scale.

Current standing claim:

```text
The CHRONOS streams can show raw/band-level similarity, but the tested MERA strain endpoint does not detect synchronized representation-level deformation events. This further supports treating external timing correlations as diagnostic context rather than as an alignment key.
```

Recommended next move:

```text
Do not proceed to twistor/spinor embedding from these data. That branch should remain conditional on a replicated positive MERA strain or elasticity endpoint.
```

