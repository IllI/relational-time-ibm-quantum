# AQ-PAGE-WOOTTERS-IBM-10 — Run Spec: the three properties on ONE preparation

**Status: specified, dry-run verified, NOT executed on hardware.**
Filed 2026-08-09. Script: `hardware/pw_ibm10_single_state.py`.

## Why this run exists

The program can currently say *"the history state is entangled"* (IBM-4) and
*"the history state is stationary"* (IBM-5) — **but not of the same state.**

| run | preparation | generator | property certified |
|---|---|---|---|
| IBM-4 | `cry` ladder onto `\|0⟩_S` | `U = Ry(2π/d)`, `U^d = −I` | entanglement, F = 0.9419 |
| IBM-5 | `cp` ladder onto `\|+⟩_S` | `U = P(2π/d)`, `U^d = +I` | ray-stationarity, 44σ–167σ |

Those two states are **orthogonal**:

```
fidelity(Ry-state, P-state) = 0.0000  (d=4)
                              0.0046  (d=8)
```

and they are **not related by any system-local unitary** — a least-squares
solve for a 2×2 `V` with `V·A = B` returns a non-unitary, non-exact matrix at
both `d`. The reason is structural: the two states differ by a
**clock-conditioned** phase, which is a controlled operation, not a local one.
That is precisely the `U^d = −I` versus `U^d = +I` distinction IBM-5
discovered.

Both are maximally entangled by construction (Schmidt spectrum exactly ½,½;
`ρ_S = I/2`), so the *theory* transfers. **The measurement does not.** The
state shown entangled was never shown stationary, and the state shown
stationary was never hardware-certified as entangled. Since the Page–Wootters
mechanism's actual content is the **conjunction** — a state that does not
change globally while its conditioned slices do — stitching two orthogonal
preparations is the single most attackable claim in the paper.

## Design

One preparation `V` at `d = 4` (3 qubits), three arms, one job:

| arm | observable | certifies |
|---|---|---|
| **A** | multi-setting fidelity witness, 14 settings over 26 Pauli terms | entanglement, `F > λ_max = ½` |
| **B** | Loschmidt echo of `Ŝ ⊗ U` vs 3 mismatched controls | ray-stationarity |
| **C** | clock in Z, system in X | internal evolution, `⟨X_S\|t⟩ = cos(2πt/d)` |

`d = 4` is chosen, not inherited: IBM-5 showed the echo's contrast *degrades*
as `d` grows (at `d = 8`, `cos²(θ/2) = 0.854` caps the joint-vs-system-only gap
at 0.146 even on perfect hardware), and IBM-8 showed `d = 8` is out of reach
for anything carrying a controlled clock-shift. `d = 4` is where all three arms
are simultaneously well-conditioned.

### The single-state discipline is asserted, not claimed

`check_single_state_discipline()` runs before any backend contact and fails the
run rather than the paper:

1. Arm C's circuit, with its readout rotation undone, is **statevector-identical**
   to arm A/B's preparation (`atol = 1e-12`).
2. `U^d = +I` exactly — the property IBM-0…4's state lacked.
3. `λ_max = ½` is re-derived from *this* state's Schmidt spectrum, not
   inherited from IBM-4. (IBM-4's equivalent assertion caught a real reshape
   bug before hardware.)
4. Overlap with IBM-4's state is `< 0.01`, confirming this is genuinely the
   untested conjunction and not duplicated work.

The echo's `U` and the conditional dynamics' `U` are the same `system_step()`
source function, so "one operator does both jobs" is structural rather than
numerically coincidental.

## Pre-registered gates

| gate | criterion |
|---|---|
| 1 | `F > ½` by more than 3σ (propagated, see caveat) |
| 2 | joint echo exceeds **every** mismatched control by > 3σ, using binomial σ at the measured `p` — not the worst-case `1/√N` that IBM-5 mis-used |
| 3 | `⟨X_S\|t⟩` fits `cos(2πt/d)` with R² > 0.90 |
| 4 | gates 1–3 all hold **on the same prepared state** |

## Dry-run projection (noisy Aer, 3 independent runs)

```
F        = 0.8965 – 0.8968   (bound 0.5, 3σ = 0.0133, margin ≈ +0.397)
joint    = 0.8918 – 0.8940   vs clock_only 0.459, system_only 0.478, wrong_way 0.033
                             separations 47σ – 163σ
⟨X_S|t⟩  amplitude 0.870 – 0.900, R² = 0.994 – 0.9999
```

All four gates pass in all three runs. Cost: **19 circuits, 76 000 shots, ≤ 9
two-qubit gates per circuit** — well under IBM-8's fatal 29, and comparable to
IBM-1's committed budget.

## Caveats recorded in advance

1. **The fidelity σ is an independence estimate.** Paulis read from the same
   setting share counts and are correlated; `fidelity_sigma()` ignores that.
   It is used only to set a 3σ bar far below the observed margin. **Do not
   quote an N-sigma significance from it without bootstrapping the
   covariance** — IBM-4 made the same choice and deferred the bootstrap.
2. **Arm C is thin at `d = 4`.** The exact sequence is `[1, 0, −1, 0]`, so two
   of four points are zero by construction and R² is carried by `t = 0, 2`.
   The *amplitude* is the informative quantity; a high R² here should not be
   read as a rich fit.
3. **Arm B's raw joint value will not be 1.0.** A return probability near 0.89
   certifies ray-stationarity *relative to the mismatched controls*; it is not
   a direct measurement of unit modulus, and the eigenvalue phase remains
   uncertified (IBM-6 and IBM-8 both failed at it).

## What a pass would earn, stated exactly

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

The defensible central claim would be **an experimental realization and
certification of finite quantum relational dynamics** — *not* an experimental
demonstration that time emerges. The distinction is limitations 6 and 7 in the
README: nothing here derives the clock from the state or Hamiltonian, and the
state comes into existence through an externally timed laboratory sequence.
Its *internal description* has Page–Wootters structure; its *preparation* is
not an autonomous universe satisfying a timeless constraint.

Note also that a CHSH test on the effective two-dimensional Schmidt subspace
would strengthen the operational nonclassicality claim but would **not** make
it device-independent: two logical subsystems on one superconducting processor
are not spacelike separated.

## Run command

```bash
python pw_ibm10_single_state.py --dry                      # verify locally, 0 QPU
python pw_ibm10_single_state.py --backend ibm_marrakesh    # ~19 circuits, one job
```
