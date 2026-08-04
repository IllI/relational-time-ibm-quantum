# AQ-PAGE-WOOTTERS-IBM-0 Run Spec - 2026-08-03

> [!NOTE]
> **Executed the same day; all five gates passed on `ibm_marrakesh`.** See
> `AQ_PAGE_WOOTTERS_IBM_0_RESULTS_2026-08-03.md`. Next step is the
> disjoint-layout replication described at the end of that results doc.

## Purpose

Every prior run in the time-emergence line tested emergent relational time on
a substrate that could not carry it: TPU scheduler telemetry
(`CHRONOS-*`, closed as a disciplined null 2026-08-03) or synthetic history
generators (`AQ-PAGE-WOOTTERS-DLINOSS-*`, promoted only as a path-level
mechanism in simulation; the BEC bridge Gate 0 failed 2026-08-03). This run
moves the question onto a real quantum system, where a clock degree of freedom
can actually be entangled with the rest of the state, using hardware and a
pipeline already validated by the OAT PTM work.

The experiment tests the Page-Wootters mechanism directly, and -- more
usefully -- tests the standard objection to it.

## The Scientific Question

Page-Wootters says a globally static entangled state contains apparent
dynamics: conditioning the system on a clock reading yields an evolving
system state, with no external time parameter anywhere. Moreva *et al.* (PRA
89, 052122 (2014)) demonstrated this with photon polarization.

The standing objection is that **conditional evolution alone is not evidence
of anything quantum.** A classically correlated clock-system state
`rho = (1/d) sum_t |t><t| (x) |psi(t)><psi(t)|` reproduces the conditional
statistics exactly. Both give the same `<Z_S | t>`.

So the question this run asks is not "does conditional evolution appear on
hardware" (it will, trivially) but:

```text
What measurement actually distinguishes a coherent Page-Wootters history
state from a classical clock-system correlation, and does that distinction
survive on superconducting hardware?
```

## The Answer This Run Measures

The distinguishing structure lives in the **clock marginal**. For the history
state

```text
|Psi> = (1/sqrt(d)) sum_t |t>_C (x) U^t|0>_S ,   U = Ry(theta), theta = 2*pi/d
```

tracing out the system gives

```text
rho_C[t,t'] = (1/d) <psi(t')|psi(t)> = (1/d) cos((t - t')*pi/d)
```

Those off-diagonal terms *are* the clock-record overlaps -- the same
non-orthogonality quantity this branch characterized numerically in
`AQ-PAGE-WOOTTERS-DLINOSS-QUANTUM-CLOCK-BOUND-0` and
`-MULTICLASS-CLOCK-BOUND-0`. The classical mixture has the identical
diagonal and **zero** off-diagonals.

Measuring the clock in the Fourier basis reads out exactly this coherence:

```text
P(k) = <f_k| rho_C |f_k>,     |f_k> = (1/sqrt(d)) sum_t e^{2*pi*i*k*t/d} |t>
```

- coherent history state: `P(k)` is peaked
- classical clock-system correlation: `P(k)` is **exactly uniform**, `1/d`

Scalar endpoint: total-variation distance from uniform,
`TVD = 0.5 * sum_k |P(k) - 1/d|`.

**The scaling is the interesting part.** Adjacent clock records get *more*
non-orthogonal as `d` grows (`cos(pi/d) -> 1`), so `rho_C` carries more
coherence, so the witness gets *stronger*. What the earlier synthetic runs
found as a limitation -- local clock records being non-orthogonal and
locally indistinguishable -- is the same quantity that makes the coherence
witness measurable here. That inversion is the result worth reporting.

## Claim Boundary (locked before submission)

**CAN claim, if the run passes:**
- Page-Wootters conditional evolution measured on superconducting hardware.
- A hardware demonstration that conditional evolution is reproduced by a
  classical-clock control, i.e. is not by itself a witness of clock coherence.
- Hardware measurement of the clock-marginal coherence witness that does
  separate them, with its predicted growth in clock dimension `d` and a
  structural null at `d = 2`.

**CANNOT claim** (carried forward from FINDINGS.md §135 discipline):
- that time is emergent, or that this bears on physical spacetime;
- that quantum gravity, the Wheeler-DeWitt equation, or the problem of time
  has been tested;
- that a physical Page-Wootters universe has been realized;
- any teleportation, advantage, or supremacy claim.

This is a hardware measurement of the coherence structure of a small
engineered history state. Nothing more.

## Circuits

Clock register `C` of `n_c` qubits (`d = 2^n_c`), system `S` of one qubit.
`theta = 2*pi/d`, so the system makes exactly one revolution across the clock
range (no aliasing).

**History-state preparation** (shared by all arms): Hadamards on the clock,
then a controlled-`Ry(2^k * theta)` ladder from clock qubit `k` to the system.
This realizes `sum_t |t><t| (x) U^t`.

| Arm | Clock prep | Clock measured in | Purpose |
|---|---|---|---|
| **A** conditional evolution | uniform superposition | computational | `<Z_S \| t>` should track `cos(2*pi*t/d)` |
| **B** classical-clock control | definite `\|t>`, `d` circuits averaged 1/d | computational | must reproduce A -- the "not quantum" demonstration |
| **C** coherence witness | uniform superposition | inverse-QFT then computational | peaked `P(k)`, TVD > 0 |
| **D** classical-clock control | definite `\|t>`, `d` circuits averaged 1/d | inverse-QFT then computational | uniform `P(k)`, TVD at shot-noise floor |

Arms B and D are genuine hardware circuits, not post-hoc classical
simulations: preparing the clock in a definite computational basis state and
averaging over `t` with weight `1/d` realizes the classical mixture exactly.

Clock sizes: `n_c = 1, 2, 3` (`d = 2, 4, 8`).

## Pre-Registered Predictions

Verified by local Aer dry run before submission
(`pw_ibm_dryrun.py`, results in `pw_ibm_dryrun_results.json`). Exact values
are statevector-computed, not sampled.

**Witness TVD (primary endpoint):**

| `d` | exact TVD | noisy-sim TVD | noise attenuation | classical arm | null floor @8k shots |
|---|---|---|---|---|---|
| 2 | **0.0000** | 0.013 | -- | 0.002 | 0.0045 |
| 4 | **0.1768** | 0.168 | 0.95 | 0.005 | 0.0077 |
| 8 | **0.4967** | 0.439 | 0.88 | 0.010 | 0.0118 |

**`d = 2` is a structural null and the internal control.** At `d = 2` the
history state is exactly the Bell state `(|00> + |11>)/sqrt(2)`, so the clock
marginal is maximally mixed and the witness must vanish *even for a perfectly
coherent state*. Same apparatus, same protocol, same analysis -- only the
clock size changes. This is the direct analog of the `chi*t = pi` null that
anchored the OAT PTM runs, and it rules out the witness being an artifact of
the inverse-QFT circuit or of readout bias.

**Conditional evolution:** `<Z_S | t> = A * cos(2*pi*t/d)` with hardware
attenuation `A`; dry run gives max residual ~0.03 (ideal, shot-noise limited)
and ~0.14 (noisy) at `d = 8`.

**Arm A vs arm B:** must agree within counting statistics at every `t`. Dry
run max gap 0.073 at `d = 8` with 1000 shots/bin, consistent with pure shot
noise (expected ~0.06). Disagreement beyond ~3 sigma would falsify the
classical-equivalence claim and is the single most informative way this run
could surprise us.

## Pass Gates

```text
Gate 0 (design sanity, already met in dry run):
  ideal-sim TVD matches statevector prediction to < 0.01     [PASSED]
  ideal-sim arms A and B agree within shot noise             [PASSED]

Gate 1 (structural null):
  measured TVD(d=2) < 3 * null_floor(d=2, shots)

Gate 2 (witness present and ordered):
  TVD(d=8) > TVD(d=4) > TVD(d=2)
  TVD(d=4) and TVD(d=8) each exceed their classical-arm value by > 5 sigma

Gate 3 (classical arms are null):
  TVD_classical(d) < 3 * null_floor(d, shots) for all d

Gate 4 (conditional evolution recovered):
  R^2 > 0.95 for <Z_S|t> against A*cos(2*pi*t/d) at d = 4 and d = 8

Gate 5 (the point of the experiment):
  arms A and B agree within 3 sigma at every t, for all d
```

Gates 1, 3, and 5 are the ones that make the result trustworthy; Gate 2 is the
positive finding. A run where Gate 2 passes but Gate 5 fails would mean the
classical control is not doing what the theory says and must be debugged
before anything is claimed.

## Budget

`optimization_level=0` throughout (the Rz-angle transpilation defect
root-caused in FINDINGS.md §123 applies here too -- the controlled-`Ry` ladder
angles must not be merged or re-synthesized).

Transpiled cost (dry run, `rz/sx/x/cx` basis):

| `d` | witness depth | witness CX |
|---|---|---|
| 2 | 16 | 2 |
| 4 | 39 | 9 |
| 8 | 59 | 15 |

Shot budget per clock size: 8000 (arm A) + 8000 (arm B, split over `d`
circuits) + 8000 (arm C) + 8000 (arm D, split) = 32000 shots, plus 2000
readout calibration. Across `d = 2, 4, 8`: ~102k shots total.

For scale, the OAT runs used ~2500 shots for roughly 4 s of QPU time, so this
sits in the low tens of seconds against the 10 min/month Open Plan
allowance -- affordable with room for a disjoint-layout replication, which
should be run if the first pass clears the gates.

## Implementation Plan

1. `pw_ibm_dryrun.py` -- **done**, gates 0 passed, predictions locked above.
2. Add `pw_ibm_submit.py`: reuse the `ibm_run3.py` structure (programmatic
   layout selection on the coupling map, `optimization_level=0`, prereg JSON
   written *before* the first job, readout-matrix calibration, raw counts
   archived). Token via `os.environ["QISKIT_IBM_TOKEN"]` -- never hardcoded.
3. File `pw_ibm_prereg.json` with the table above before submitting anything.
4. Submit calibration first, then arms A-D per clock size.
5. Analyze; if gates pass, replicate on a disjoint qubit chain exactly as
   Run 2 -> Run 3 did for the PTM work.

## Relationship to the Rest of the Program

This does not rescue the CHRONOS telemetry line or the BEC bridge; both
remain closed nulls and should be reported as such. What it does is put the
original grant question -- is time relational, emergent from interactions
between parts of a system -- onto a substrate where the question is
well-posed, using the pre-registration and internal-null discipline that the
OAT PTM work already validated on this hardware.

If it passes, the natural home is a short quantum-foundations note: *the
conditional-evolution signal usually cited as "time from entanglement" is
reproducible with a classical clock; here is the clock-marginal coherence
witness that is not, measured on hardware, with its dimensional scaling and
a structural null.*
