# AQ-PAGE-WOOTTERS-IBM-17 — Fixed Chain, Controlled Dephasing Ladder

**Executed 2026-08-19 on `ibm_marrakesh`.** 1 job `da3660u1vhnc73fjejdg`,
113 circuits, 452 000 shots, ~122 s, chain `[134, 135, 139, 155]` **pinned and
verified**. **3 of 4 gates pass.**

**This is the first run in the IBM-15/16/17 sequence with valid provenance:**
the calibration snapshot brackets the job at `−1.1 h`. IBM-15's post-dated its
job by `+3 h`, IBM-14's by `+1.4 h`, and both are unusable for noise modelling.
This one is not.

## What it was for

IBM-16 produced two runs, each passing the gate the other failed, differing in
**two** variables — chain and backend status. This holds the chain fixed, runs
on an operational backend, and varies one knob.

## The separable control — the result that matters

Coupling the purifier to an environment by `δ` multiplies the T–P coherence by
`cos δ` while leaving `|r|` **exactly** fixed (verified to `1.1e-16` in
preflight). At `δ = π/2` entanglement is gone entirely:

```
 delta/pi   C_true (tomography)   C_est (phase)
  0.00           0.7539              0.9358
  0.15           0.6436              0.8765
  0.30           0.4361              0.8296
  0.40           0.2361              0.8839
  0.50           0.0000              0.8568   <- separable control
```

**`C_true = 0.0000` — no entanglement at all — and the phase still reads
`0.8568` against `0.9358` at `δ = 0`.** The phase is measuring the local Bloch
length and nothing else, demonstrated on a state with provably zero
entanglement, on one fixed chain, with a calibration that describes the device.

Suppression ratio `|ΔC_true|/|ΔC_est| = 9.54`, inside the pre-registered `≥ 5`
window. Far below the dry run's `107` because hardware scatter moves `C_est` by
`0.106` across the ladder, which is what sets the ratio.

## Gate 3 failed, narrowly, and the structural claim survives

```
 C_true   interf   uhlmann   best    rule       |err_best|
 0.310    0.188    0.346    0.346   uhlmann     0.0357
 0.580    0.541    0.607    0.607   uhlmann     0.0274
 0.790    0.805    0.800    0.805   interf      0.0149   <- rule missed
 0.930    0.923    0.995    0.923   interf      0.0066

 mean:  interf 0.0457   uhlmann 0.0345   BEST-OF-TWO 0.0212   (gate <= 0.02)
```

**Best-of-two beats both arms** — `0.0212` against `0.0457` and `0.0345` — so
the complementarity does real work. But the gate demanded `≤ 0.02` and it came
in `0.0012` over.

> **The threshold was set from a dry run that gave `0.0011`.** Hardware is ~20×
> worse. Setting an absolute performance bar from a noise-model simulation was
> the mistake; the simulation systematically understates error. The gate is
> **not** being relaxed — it failed as pre-registered — but the lesson is that
> future performance gates should be stated *relative* to the single-arm
> baselines, which is a claim the physics supports, rather than to an absolute
> number a simulator produced.

The switching rule chose correctly at three of four points. At `C = 0.790` it
picked interferometric where Uhlmann was marginally better (`0.010` vs `0.015`)
— the computed crossover sits at `0.798`, so that point falls essentially on the
boundary.

## The meter carries a systematic offset

```
 delta   C_true    C_est    bias
  0.00   0.7539   0.9358   +0.1818
```

At zero dephasing the phase-inferred concurrence overestimates by `0.18`, and
the prepared value was `0.85` while tomography read `0.7539` — so preparation
loss and meter bias push in opposite directions. **The meter is not calibrated
in absolute terms on this chain**, and the blind-estimation numbers above are
the honest measure of its accuracy, not the ladder's `δ = 0` point.

## Honest ledger

**Three of four gates pass, and the one that failed is mine, not the device's.**
That is the third gate in this programme whose threshold encoded something the
physics does not support — after IBM-13's vacuous non-vacuity gate and IBM-16's
absolute purity threshold.

**The chain was pinned and verified**, so unlike IBM-16 the arms cannot have
landed on different qubits. The submit path aborts if any circuit drifts off the
chain; it did not fire.

**Nothing here beats Holevo**, and nothing certifies. The certification chain
remains the multi-setting fidelity witness with its proven bound.

## What this establishes

> On a single pinned chain with valid provenance, a controlled ladder drives
> entanglement from `C = 0.754` to exactly zero while the geometric phase moves
> by `0.08` — a suppression ratio of `9.54`. The phase therefore reports the
> local Bloch length rather than the concurrence, demonstrated against a
> provably separable state rather than inferred. Combining the two phase
> constructions with a switching rule fixed at the computed sensitivity
> crossover estimates concurrence to `0.0212` mean error on states the
> calibration never saw, better than either construction alone, using two
> ancilla settings against nine for tomography.

## Provenance

`ibm_marrakesh`, 2026-08-19, job `da3660u1vhnc73fjejdg`, chain
`[134, 135, 139, 155]` pinned, 113 circuits at 4 000 shots, backend
operational, calibration brackets the job at `−1.1 h`. Archived at
`results/hardware/ibm17/`.

```
python hardware/pw_ibm17_fixed_chain_ladder.py --analyze results/hardware/ibm17/raw.json
python hardware/pw_drift_monitor.py --freshness results/hardware/ibm17/ibm17_provenance.json
```
