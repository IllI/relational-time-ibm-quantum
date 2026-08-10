# AQ-PAGE-WOOTTERS-IBM-10 — The Conjunction, Certified on One Preparation

**Executed 2026-08-09 on `ibm_marrakesh`.** 1 job, 19 circuits, 4 000 shots each.
**All 4 pre-registered gates pass.**

This closes the program's most attackable gap. Until now the paper could say
*"the history state is entangled"* (IBM-4) and *"the history state is
stationary"* (IBM-5) — but not of the same state, because those two runs used
**orthogonal** preparations (fidelity 0.000 at `d = 4`). The Page–Wootters
mechanism's actual content is the *conjunction*: a state that does not change
globally while its conditioned slices do. That conjunction had never been
measured. It has now.

## Results

One preparation `V` (the `P(2π/d)`-generated cyclic history state on `|+⟩_S`,
`d = 4`, qubits `[0, 1, 2]`), three arms, one job:

| arm | quantity | measured | exact | verdict |
|---|---|---|---|---|
| **A** entangled | `F` vs separable bound `λ_max = ½` | **0.9014** | 1.0 | **+0.4014 over the bound** |
| **B** stationary | joint echo | **0.8630** | 1.0 | — |
| | vs `clock_only` | 0.3990 | 0.5 | **+0.4640, 49.0σ** |
| | vs `system_only` | 0.4607 | 0.5 | **+0.4022, 42.0σ** |
| | vs `wrong_way` (`Ŝ ⊗ U⁻¹`) | 0.0210 | 0.0 | **+0.8420, 142.9σ** |
| **C** evolving | `⟨X_S\|t⟩` amplitude | **0.9193** | 1.0 | R² = **0.9942** |

```
conditional trajectory:  [ 0.8759  -0.0477  -0.9626  -0.0608]
exact cos(2 pi t/d):     [ 1.0000   0.0000  -1.0000   0.0000]
```

**Gate 4 — the conjunction — passes:** gates 1–3 all hold on the *same*
prepared state, in the same job, under the same calibration.

## Why this is not three results stapled together

The single-state discipline is enforced by assertions that run before any
backend contact, so the claim is structural rather than editorial:

1. Arm C's circuit, with its readout rotation undone, is
   **statevector-identical** to arm A/B's preparation (`atol = 1e-12`).
2. `U^d = +I` exactly — the cyclic property IBM-0…4's state lacked.
3. `λ_max = ½` is **re-derived from this state's** Schmidt spectrum, not
   inherited from IBM-4.
4. Overlap with IBM-4's state is `< 0.01`, confirming this is the untested
   conjunction rather than duplicated work.

The echo's `U` and the conditional dynamics' `U` are the same `system_step()`
source function, so *one operator does both jobs* is a property of the code
path, not a numerical coincidence.

## Honest ledger

**The backend was in `maintenance` status when this job ran.** Qiskit emitted
`UserWarning: The backend ibm_marrakesh currently has a status of maintenance.`
The job completed normally and every gate passed with large margins, but this
is recorded because it is exactly the kind of detail that is convenient to
omit. The one visible consequence is below.

**The joint echo is 4.4% lower than IBM-5's on the same state and backend**
(0.8630 here vs **0.9030** in IBM-5, 2026-08-08). The control structure
replicates closely (IBM-5: 0.4605 / 0.4985 / 0.0243; here: 0.3990 / 0.4607 /
0.0210), so this reads as calibration drift, not a different physical result.

The provenance capture supports that reading with a specific number rather
than a guess: the backend's **last calibration update was
`2026-08-06T22:19:40-05:00`** — three days before this run, and the same
snapshot IBM-9 ran against on 2026-08-08. So the device executed this job in
`maintenance` status against a three-day-old calibration. That is a plausible
and *documented* source of the drift, and it is why the calibration snapshot
is archived per run rather than described in prose.

Taken together with IBM-5 this is also an **independent replication of the
stationarity measurement on a different day and a different calibration
epoch**, which was not a design goal of this run but is a real bonus: the
separations survive at 42σ–143σ despite the degraded conditions.

**The fidelity σ is an independence estimate.** `fidelity_sigma()` propagates
`Var(F) = (1/2ⁿ)² Σ c_P²(1−⟨P⟩²)/N` but ignores the correlation between Paulis
read from the same setting. It is used only to set a 3σ bar (0.0133) far below
the observed margin (0.4014). **No N-sigma significance is quoted for arm A**,
and none should be without bootstrapping the covariance — IBM-4 made the same
choice and deferred the bootstrap.

**Arm C is thin at `d = 4`, as pre-registered.** The exact sequence is
`[1, 0, −1, 0]`, so two of four points are zero by construction and R² is
carried by `t = 0, 2`. The **amplitude** (0.9193) is the informative quantity;
the high R² should not be read as a rich fit.

**Arm B's raw joint value is not 1.0.** A return probability of 0.863
certifies ray-stationarity *relative to the mismatched controls*; it is not a
direct measurement of unit modulus, and the eigenvalue phase remains
uncertified (IBM-6 and IBM-8 both failed at that, and both stay in the record).

## What this earns, stated exactly

> On superconducting hardware we prepare a finite Page–Wootters history state
> and certify, on the same state and in one pre-registered protocol, that it is
> entangled across the clock–system cut, stationary as a quantum ray under the
> paired clock-shift-and-evolution operation but not under the corresponding
> mismatched operations, and internally evolving under the same system
> operator. We further establish experimentally that the weaker observables
> tested in this program — conditional evolution, local clock coherence, and
> single-basis joint correlation — do not suffice to certify relational
> entanglement, each being reproduced by an explicitly constructed classical or
> separable adversary; the multi-setting fidelity measurement instead exceeds
> the exact separable bound. The phase of the stationarity eigenvalue, and
> therefore the stronger `+1` constraint condition, remains uncertified; the
> state is externally engineered, the clock decomposition is imposed rather
> than derived, and no claim is made that time in nature is emergent or that
> the Wheeler–DeWitt constraint has been experimentally tested.

The defensible central claim is **an experimental realization and
certification of finite quantum relational dynamics** — *not* an experimental
demonstration that time emerges. Nothing here derives the clock from the state
or Hamiltonian, and the state comes into existence through an externally timed
laboratory sequence. Its *internal description* has Page–Wootters structure;
its *preparation* is not an autonomous universe satisfying a timeless
constraint.

## Provenance

`ibm_marrakesh` (status: maintenance), 2026-08-09, 1 job
`d9sh2u7pemts73ctnea0`, qubits `[0, 1, 2]`.

```
python pw_ibm_provenance.py --results results_ibm10_ibm_marrakesh/ibm10_results.json --out results_ibm10_ibm_marrakesh/ibm10_provenance.json
```
