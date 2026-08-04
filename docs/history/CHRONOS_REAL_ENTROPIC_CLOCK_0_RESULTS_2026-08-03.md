# CHRONOS-REAL-ENTROPIC-CLOCK-0 Results - 2026-08-03

## Purpose

`AQ-DLINOSS-CHRONO-0` (2026-06-14) scored the live US/EU TPU pair with a ridge-affine
transition surrogate and returned a clean null (`gate_1_passed = False`). The
Page-Wootters branch later found, entirely on synthetic histories, that a
stationary transition operator cannot exploit relational time at all -- the
mechanism that closed the gap to ridge required (1) a generator with genuine
entropy/event causal-action history (arm `A10_full_global_causal_memory`) and
(2) an **event-damped** D-LinOSS operator whose damping channel is driven by
that history. That confirmed mechanism (`AQ-PAGE-WOOTTERS-DLINOSS-A10-EVENT-DAMPED-CONFIRM-0`,
2026-06-17) was never applied to the real TPU streams -- the real-data branch
had already closed two days earlier. This run closes that gap.

This is a reanalysis of already-archived compact `q_latency` JSON files. No new
TPU collection was performed.

## Method

For each real Alice/Bob pair:

1. Extract the locked `AQ-DLINOSS-CHRONO-0` minimum feature vector (windowed
   mean/std/median/MAD, Schumann/anti/grid/low-drift/high-residual band
   energies, instantaneous phase/velocity/curvature, local entropy) at
   `W=256` samples, `hop=128` samples, exactly as specified in
   `AQ_DLINOSS_CHRONO_0_RUN_SPEC_2026-06-14.md`.
2. Add the one channel that run never computed: **causal_action**, an
   accumulated entropy-production + event-activity integral --
   `causal_action(t) = cumsum(0.6 * entropy_rate + 1.0 * event_activity)` --
   the real-data analog of generator arm A10's causal memory and a direct
   operationalization of `tau(lambda) ~ integral dS` from arXiv:2509.07745.
3. Build global monotone path correspondence between Alice and Bob feature
   streams using the promoted `path_cost` / `path_metrics` machinery from
   `program_aq_page_wootters_path_observability0.py` (unmodified).
4. Train the frozen **event-damped** complex D-LinOSS operator
   (`program_aq_page_wootters_a10_event_damped_confirm0.py`, unmodified,
   `hidden_dim=32`, `context_steps=8`, `epochs=350`) on the calibration half
   to predict Bob's delta-features from Alice's delta-features plus the
   4-channel causal-aux vector (event activity, entropy rate, causal action,
   strain).
5. Score payload-half cosine-similarity gain against five controls:
   shuffled, severed, wrong-lag, block-shuffled, and a **cross-pair** control
   built from a genuinely different real Bob recording (not a synthetic
   surrogate). For the `chrono0_seed14` pair, a sixth control is available
   and included: the already-collected **real** `plus1h` Bob stream from
   `CHRONOS-MARGINAL-DRIFT-1` (same node, +1 hour).
6. Compare against a ridge-affine baseline fit on the same calibration split.

Three real pairs were available (no synthetic seed-resampling is possible on
real hardware data): `seed11`, `rep1`, and `chrono0_seed14`.

Script: `chronos_time_emission/chronos_real_entropic_clock_reanalysis.py`.

## Results

| Pair | path_rank | path_margin/step | dlinoss_gain (mean) | window_frac beating best null | gain CI95 | dlinoss - ridge |
|---|---|---|---|---|---|---|
| seed11 | 1 | 1.574 | -0.0456 | 0.136 | [-0.469, -0.322] | -0.113 |
| rep1 | 1 | 0.574 | +0.0272 | 0.200 | [-0.381, -0.203] | -0.057 |
| chrono0_seed14 | 1 | 1.832 | +0.0333 | 0.168 | [-0.434, -0.292] | -0.220 |

Full JSON and per-pair markdown: `chronos_time_emission/results_real_entropic_clock_0/`.

## Interpretation

**The global path is recoverable.** `path_rank = 1` on all three real pairs,
with strongly positive path-margin-per-step -- the true Alice/Bob
correspondence beats every null (including the real cross-pair and real
plus1h controls) as an aggregate monotone path. This replicates, on real
hardware telemetry, the same "global history is distinguishable" pattern
found throughout the synthetic Page-Wootters branch.

**The window-level prediction task fails clearly, and more decisively than
on synthetic noise.** The bootstrap CI on per-window relational gain is
entirely negative for all three pairs -- not merely non-significant, but
reliably negative. Window fraction beating the best null (0.136-0.200) sits
far below even the worst synthetic noise regime tested (`noise=0.03` still
cleared 0.66-0.68 with this exact mechanism). D-LinOSS underperforms the
ridge baseline by 0.06-0.22, a much larger gap than the confirmed synthetic
result (-0.07 to -0.09).

**The mean-vs-median discrepancy is itself informative.** For `rep1` and
`chrono0_seed14`, the aggregate gain (mean relational score minus mean best-null
score) is slightly positive, while the bootstrap CI on the per-window gain
distribution is fully negative. That pattern means the positive aggregate is
driven by a minority of favorable windows, not a robust signal -- the CI and
window-fraction numbers are the trustworthy readout, and both say no.

**The real plus1h control sharpens the marginal-drift finding.** For
`chrono0_seed14`, the real +1-hour-shifted Bob stream is, on average, the
*best-scoring null* -- the trained transition operator predicts true-time Bob
about as well (badly) as it predicts the same node's stream from an hour
later. This is a stronger statement than the original `CHRONOS-MARGINAL-DRIFT-1`
correlation finding: it is not just that raw feature similarity survives a
temporal offset, but that the actual confirmed relational-clock mechanism
cannot distinguish true-time correspondence from time-shifted correspondence
on the same hardware.

## Standing Conclusion

Applying the exact mechanism that was confirmed on synthetic entropy-bearing
histories (A10 causal-memory generator + event-damped D-LinOSS + path
observability) to the real US/EU TPU streams does not rescue the
`AQ-DLINOSS-CHRONO-0` null -- it sharpens it. The previous null cannot be
attributed to using the wrong operator (ridge instead of D-LinOSS) or the
wrong feature construction (missing the entropic causal-action channel);
both have now been supplied, and the window-level failure is worse, not
better. Combined with the real, previously-collected plus1h control, the
most parsimonious explanation remains structural hardware/provider similarity
rather than any shared temporal geometry between the two datacenters.

This closes the real-data TPU-telemetry question under the strongest
available mechanism. It does not bear on whether the entropic-time
construction itself (arXiv:2509.07745) is a valid model of a physical
cold-atom system -- that is a separate, physically grounded generator
question, addressed in
`AQ_PAGE_WOOTTERS_DLINOSS_BEC_ENTROPIC_BRIDGE_0_RUN_SPEC_2026-08-03.md`.

## Limitations

- N=1 real recording per condition; no seed-resampling is possible on
  archived hardware telemetry, so no cross-seed distribution can be reported
  (unlike the synthetic grid's 5-10 seeds per configuration).
- Hyperparameters (`hidden_dim=32`, `context_steps=8`, `epochs=350`,
  `lr=3e-3`) were carried over unchanged from the synthetic confirmation run;
  no hyperparameter search was performed on real data.
- Window count per pair is modest (~254 windows, ~127/127 calibration/payload
  split), limiting training data for a 32-hidden-dim complex recurrent model.
