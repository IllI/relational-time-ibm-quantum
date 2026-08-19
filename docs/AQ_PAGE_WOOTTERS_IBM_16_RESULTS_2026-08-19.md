# AQ-PAGE-WOOTTERS-IBM-16 — The Geometric Phase as an Entanglement Meter

**Two runs on `ibm_marrakesh`, 2026-08-19.** 103 circuits each, 412 000 shots,
~117 s apiece.

| | run 1 `da30ffu1vhnc73fj85jg` | run 2 `da3356u1vhnc73fjb67g` |
|---|---|---|
| chain | `[54, 147, 148, 149]` | `[139, 153, 154, 155]` |
| backend status | **maintenance** | operational |
| blind error, interferometric | 0.0752 | **0.0228** |
| blind error, Uhlmann | **0.0199** | 0.0234 |
| best-of-two | 0.0209 | **0.0140** |
| gate 3 (complementarity) | **FAIL** | PASS |
| gate 4 (purity gap) | PASS | **FAIL** |

**Each run passes the gate the other fails.** Neither alone would have been
readable; together they separate a real effect from a device artifact.

## The inversion

Fifteen runs closed the question of whether anything escapes the entanglement
budget. This one stops asking the phase to be a shared clock and uses it as an
**instrument**: a measured phase constrains the residual entanglement.

## Gate 3: the complementarity is real, and run 1 was the artifact

The design predicted the two constructions cover each other's blind spots —
Uhlmann best mid-range, interferometric best at high `C`. Run 1 said no. Run 2
says yes, decisively:

```
 C_true    interferometric    Uhlmann
  0.270        0.0576         0.0116     <- Uhlmann wins
  0.710        0.0011         0.0184     <- interferometric wins
  0.880        0.0039         0.0261
  0.960        0.0103         0.0350
  mean         0.0228         0.0234      best-of-two 0.0140
```

The interferometric arm's error fell **3.3×** between runs (0.0752 → 0.0228) on
a different chain. Its visibility was the cause: `0.767` mean in run 1 against
Uhlmann's `0.932`, and the earlier writeup concluded from that single run that
"the interferometric arm is not competitive on this device." **That conclusion
was wrong, and run 2 retracts it.** The arm is chain-sensitive, not broken.

Best-of-two beating both arms (0.0140 against 0.0228 and 0.0234) is the
complementarity doing real work: **two ancilla settings estimate concurrence to
0.014, against nine settings for a tomographic reconstruction.**

## Gate 4: the effect is real, my threshold was not

The phase reads the local Bloch length `r`, which dephasing leaves untouched,
so it should barely move while `C` collapses. Both runs show that — but not as
absolutely as the gate demanded:

```
 run 1:  C_true falls 0.645   C_est falls 0.039   suppression 16.3x   gap +0.667
 run 2:  C_true falls 0.418   C_est falls 0.089   suppression  4.7x   gap +0.399
```

Gate 4 required `|ΔC_est| < 0.08`. Run 2 gives `0.089` and **fails**.

> **The gate encoded a claim stronger than the physics supports.** The phase is
> not *blind* to dephasing; it is **suppressed by 5–16×** relative to the
> concurrence. That is enough for the mixedness witness — the gap opens by
> `+0.40` and `+0.67` in the two runs — but "the phase is pinned" was my
> phrasing, not a result, and the earlier writeup overstated it.

The threshold is **not** being relaxed after the fact. Gate 4 failed as
pre-registered, and the correct statement is the suppression ratio, which is
robust across both runs and both chains.

## What survives, stated at the strength the data supports

> The Uhlmann and interferometric geometric phases together meter concurrence to
> `0.014` mean error on states the calibration never saw, using two ancilla
> settings against nine for tomography, with each construction covering the
> other's insensitive range. Because both read the local Bloch length rather
> than the concurrence, they are suppressed 5–16× relative to `C` under
> dephasing, so the gap between phase-inferred and tomographic `C` opens as the
> state leaves the pure-state manifold and witnesses mixedness.

## Honest ledger

**Run 1 was taken in a maintenance window because my guard was broken.** It
stringified `backend.status()` and matched nothing, so it never fired for
IBM-15 either — two runs into maintenance from one bad line. Now reads
`BackendStatus.operational` and `.status_msg`, **aborts** rather than warns, and
fails closed. Fixed one run late.

**The earlier single-run writeup of this experiment was wrong in one place** and
is corrected above: it declared the interferometric arm non-competitive on the
strength of run 1 alone. One chain is not a device.

**The two runs used different chains**, which was not the plan — I intended to
hold qubits fixed and vary only maintenance status. It turned out more useful,
since it separates chain quality from arm physics, but it means the two runs
differ in *two* variables, and neither is a controlled replication of the other.

**Nothing here beats Holevo.** Metrology and channel diagnostics, not capacity.

## Provenance

Both jobs on `ibm_marrakesh`, 2026-08-19, 103 circuits at 4 000 shots. Raw
counts and provenance archived under `results/hardware/ibm16/` (run 1) and
`results/hardware/ibm16b/` (run 2); every number reproduces from counts:

```
python hardware/pw_ibm16_phase_as_meter.py --analyze results/hardware/ibm16b/raw.json
```
