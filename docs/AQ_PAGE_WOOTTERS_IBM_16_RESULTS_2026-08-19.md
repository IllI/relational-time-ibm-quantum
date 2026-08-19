# AQ-PAGE-WOOTTERS-IBM-16 — The Geometric Phase as an Entanglement Meter

**Executed 2026-08-19 on `ibm_marrakesh`.** 1 job `da30ffu1vhnc73fj85jg`,
103 circuits, 412 000 shots, ~111 s. **3 of 4 gates pass.** Gate 3 fails, and
the failure is the most useful thing in the run after gate 4.

## The inversion

Fifteen runs closed the question of whether anything escapes the entanglement
budget. This run stops asking the phase to be a shared clock and uses it as an
**instrument**: because the trade-off is tight, a measured phase constrains the
residual entanglement.

## The headline: the phase reads `r`, not `C` — confirmed on hardware

```
 idle    C_true (tomography)   C_est (phase)     gap
   0us         0.6454             0.7062       +0.0608
  20us         0.2050             0.6889       +0.4838
  40us         0.0000             0.6667       +0.6667
```

**Entanglement is completely destroyed by 40 µs — `C_true = 0.0000` — and the
phase does not move.** It reads `0.6667` against `0.7062` at zero idle, a drift
of 0.04 while the quantity it is supposed to be reporting fell to nothing.

This was derived before the run and is now measured far more starkly than the
noise model managed (simulation only reached `C_true = 0.474`). The consequence
is the useful part:

> `C_est = √(1−r²)` holds **only on the pure-state manifold**. The phase meters
> the local Bloch length `r`, which dephasing leaves untouched. The **gap**
> between phase-inferred and tomographic `C` is therefore a mixedness witness,
> and it opens by `+0.67` across 40 µs.

Two cheap ancilla settings give `r`; nine tomographic settings give `C`; their
disagreement certifies departure from purity. That is the instrument.

## Gate 3 failed, and the reason matters for anyone building this

The design predicted **complementary sensitivity** — Uhlmann best mid-range,
interferometric best at high `C` — so best-of-two should beat either arm. It
did not:

```
 mean |error|:  interferometric 0.0752   Uhlmann 0.0199   best-of-two 0.0209
```

The interferometric arm is **four times worse**, and worse everywhere, not just
where theory expected. The cause is visibility, not sensitivity:

```
              visibility (mean / min)
 interf         0.767 / 0.608
 uhlmann        0.932 / 0.887
```

**The sensitivity analysis assumed the two arms measure with equal visibility.
On hardware the interferometric interferometer is markedly noisier, and that
wipes out its `dΦ/dC` advantage at high `C`.** At `C = 0.96` both arms return
the same `0.0103` error, where theory predicted the interferometric arm to win
decisively.

The honest conclusion: **the Uhlmann arm is the usable meter on this device;
the interferometric arm is not competitive.** Blind estimation across a
disjoint set the calibration never saw gives `0.0199` mean error from Uhlmann
alone — good enough to be an instrument, using two settings against nine.

The interferometric arm also drifts the *wrong way* under idle
(`C_est` 0.748 → 0.798 → 0.852, rising as entanglement falls), which is
consistent with a low-visibility systematic rather than with the physics.

## Honest ledger

**The backend was in `maintenance` again, and my guard failed to catch it.**
The guard stringified `backend.status()` and matched nothing, so it never
fired — for IBM-15 *or* this run. Two runs into maintenance windows from one
bad line. Now fixed to read `BackendStatus.operational` and `.status_msg`, to
**abort** rather than warn, and to fail closed if the query errors. That fix
arrived one run too late, and these numbers carry the same calibration caveat
IBM-15 does.

**Gate 2 passes, but entirely on Uhlmann's back.** Reporting "blind estimation
works" without saying which arm carries it would misrepresent the run.

**Gate 4's magnitude depends on the idle arm decohering hard**, which it did —
`C_true` reached exactly 0. That is a stronger effect than the noise model
predicted, and on a maintenance-window device it may be stronger than a
well-calibrated one would show. The *direction* of the result is robust; the
size should be replicated before being quoted.

**Nothing here beats Holevo.** This is metrology and channel diagnostics, not
capacity. The programme's applied section already closed that question.

## What this establishes

> The geometric phase functions as a practical entanglement meter, but only in
> the Uhlmann construction on this hardware: blind estimation to `0.0199` mean
> error from two ancilla settings, against nine for tomography. The
> interferometric arm's theoretical sensitivity advantage does not survive its
> lower measured visibility. And because the phase reads the local Bloch length
> rather than the concurrence, it is blind to dephasing — measured here with
> entanglement driven to exactly zero while the phase moved by 0.04 — so the
> gap between phase-inferred and tomographic `C` is a mixedness witness.

## Provenance

`ibm_marrakesh`, 2026-08-19, job `da30ffu1vhnc73fj85jg`, qubits
`[54, 147, 148, 149]`, 103 circuits at 4 000 shots, backend status
`maintenance`. Raw counts in `results_ibm16/raw.json`:

```
python hardware/pw_ibm16_phase_as_meter.py --analyze results_ibm16/raw.json
python hardware/pw_ibm_provenance.py --results results_ibm16/raw.json --out results_ibm16/ibm16_provenance.json
```
