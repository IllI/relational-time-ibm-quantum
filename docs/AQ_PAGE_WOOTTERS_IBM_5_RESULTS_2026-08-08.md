# AQ-PAGE-WOOTTERS-IBM-5 — Global Stationarity Measured, and One Gate Failed As Written

**Executed 2026-08-08 on `ibm_marrakesh`.** 2 jobs, 10 circuits, 4000 shots
each. **7 of 8 pre-registered gates pass**; `gate2_beats_controls_d8` fails as
written and is reported as a failure, with the post-hoc statistical analysis
below given separately and clearly labelled.

This run measures the half of the Page–Wootters mechanism that IBM-0 through
IBM-4 never touched: that the global state is **stationary**. Everything prior
established that conditioning yields dynamics and that the state is entangled;
none of it tested the "without evolution" in *evolution without evolution*.

---

## The constraint, and the state change it forced

A Page–Wootters history state must satisfy

```
(Ŝ ⊗ U) |Ψ⟩ = |Ψ⟩
```

where `Ŝ|t⟩ = |t+1 mod d⟩` is the cyclic clock shift and `U` the system's
one-tick evolution — the discrete, finite-dimensional analogue of the
Wheeler–DeWitt constraint `Ĵ|Ψ⟩ = 0` with `Ĵ = H_C + H_S`. Advancing the clock
is exactly compensated by evolving the system, so nothing about the global
state changes, while conditioning on a clock reading still yields
`|ψ(t)⟩ = Uᵗ|ψ(0)⟩`.

**Technical discovery, recorded because it changed the prepared state.** The
history state used throughout IBM-0…IBM-4 takes `U = Ry(2π/d)`, for which

```
U^d = Ry(2π) = −I     (not +I)
```

so **that state is invariant under the joint shift only up to a sign on the
single wraparound term** — a Page–Wootters history state in the conditional
sense, but *not* exactly cyclically stationary. This was not previously
noticed. IBM-5 therefore uses the phase generator `U = P(2π/d)` with
`U^d = +I` exactly, the system prepared in `|+⟩`, giving the same cosine
conditional signature (now read in X rather than Z) with the constraint
closing exactly. Same construction; generator chosen so the cycle closes.

## Measurement

Loschmidt echo: prepare with `V`, apply the operator, un-prepare with `V†`,
read the probability of returning to `|0…0⟩`, which equals
`|⟨Ψ|A⊗B|Ψ⟩|²`. One circuit per arm, no tomography. All four arms are the
*same circuit* differing only in the middle operator.

## Results

| d | arm | operator | measured | normalised | exact | σ vs joint |
|---|---|---|---|---|---|---|
| 4 | **joint** | Ŝ ⊗ U | **0.9030** | 1.0000 | 1.0000 | — |
| 4 | clock_only | Ŝ ⊗ I | 0.4605 | 0.5100 | 0.5000 | 48.3 |
| 4 | system_only | I ⊗ U | 0.4985 | 0.5520 | 0.5000 | 44.0 |
| 4 | wrong_way | Ŝ ⊗ U⁻¹ | 0.0243 | 0.0269 | 0.0000 | 166.6 |
| 8 | **joint** | Ŝ ⊗ U | **0.7885** | 1.0000 | 1.0000 | — |
| 8 | clock_only | Ŝ ⊗ I | 0.6482 | 0.8221 | 0.8536 | 14.1 |
| 8 | system_only | I ⊗ U | 0.7328 | 0.9293 | 0.8536 | **5.9** |
| 8 | wrong_way | Ŝ ⊗ U⁻¹ | 0.3713 | 0.4708 | 0.5000 | 41.7 |

Conditional evolution from the same state: `⟨X_S|t⟩` tracks `cos(2πt/d)` at
**R² = 0.9940 (d=4)** and **0.9988 (d=8)**, amplitudes 0.945 / 0.895.

**At d=4 the result is unambiguous.** Only the correctly *paired* operation
preserves the state: advancing the clock alone or evolving the system alone
each drops the return probability to ~0.5, and pairing the clock forward with
the system backward destroys it entirely (0.024). The joint operation returns
0.903 — the echo's own attenuation, since its exact value is 1.0. That
pairing is the constraint, and it is measured.

## The failed gate, reported as failed

`gate2_beats_controls_d8` required the joint arm to exceed **every** control
by more than 3× the combined shot noise. Against `system_only` the gap is
0.0557 and the pre-registered bar was 0.0671. **It fails.**

**Why, and what the correct statistic says.** The gate estimated shot noise as
`1/√N = 0.0158`, the *worst-case* binomial standard deviation (attained at
p = 0.5). The actual binomial σ at the measured probabilities (p ≈ 0.79 and
0.73) is 0.0095, and the true significance of the 0.0557 gap is **5.9σ**, not
sub-threshold. The pre-registered criterion used a noise model that was
wrong in the conservative direction.

This is reported rather than silently corrected because the gate is what was
registered. The corrected statistic is offered as post-hoc analysis, and the
crude-σ bug is fixed in the committed script for future runs — the same class
of error as IBM-1's hardcoded gate slack, and caught the same way.

**The deeper issue is a design limitation, not a statistical one.** At d=8 the
per-tick mismatch is intrinsically small: `θ = π/4`, so
`cos²(θ/2) = 0.854`, and even *perfect* hardware would separate the joint arm
from `system_only` by only 0.146. **The constraint test's discriminating power
degrades as d grows**, because advancing a finer-grained clock by one tick
changes the state less. d=4 (θ = π/2, exact separation 0.5) is where this test
has teeth.

**The fix for any future run**, identified but not executed: use `Ŝ^(d/2) ⊗ I`
as the clock-only control instead of `Ŝ¹ ⊗ I`. Its exact overlap is 0 at every
d, giving full contrast independent of clock size. The `wrong_way` arm already
demonstrates this — it separates by 41.7σ even at d=8.

## What this establishes

- **The global state is stationary under the joint clock-shift-plus-evolution
  operation**, and *not* under either factor alone — measured directly, with
  the correctly-paired operator distinguished from all three mismatched
  alternatives by 44σ–167σ at d=4.
- **The same operator does both jobs.** The `U` that compensates the clock
  shift in the echo and the `U` generating the conditional sequence
  `⟨X_S|t⟩ = cos(2πt/d)` are the same gate, routed through one shared
  function in the source — structural identity, not numerical coincidence.
  Both are measured on the same prepared state in the same run.
- Together with IBM-4's entanglement certification, the Page–Wootters
  mechanism is now measured on hardware in both of its halves: a stationary,
  entangled global state whose conditional slices evolve under the operator
  that makes it stationary.

## Known limitations (added 2026-08-08 after review)

Three limitations were identified after the run and are recorded here rather
than left for a referee. None invalidates a measured number; all three narrow
what the numbers mean.

### 1. The echo is phase-blind, and the phase is not cosmetic

The Loschmidt echo measures `|⟨Ψ|A|Ψ⟩|²`. That certifies **|Ψ⟩ is an
eigenvector** of `Ŝ ⊗ U` — it does **not** certify that the eigenvalue is
+1. A state with `(Ŝ⊗U)|Ψ⟩ = e^{iφ}|Ψ⟩`, φ ≠ 0, returns 1.0 on this test.

This matters for the constraint interpretation specifically. The
Wheeler–DeWitt constraint is `Ĥ|Ψ⟩ = 0` — *zero* eigenvalue, not an arbitrary
one. In generator language, a nonzero φ means `Ĵ|Ψ⟩ = (φ/Δτ)|Ψ⟩ ≠ 0`: an
eigenstate of the joint evolution carrying nonzero "energy," which is
**not** the constraint. Relational dynamics would still work, but the strict
WDW analogue would fail.

For the state actually prepared here the eigenvalue **is** exactly +1 —
verified by statevector, `⟨Ψ|(Ŝ⊗U)|Ψ⟩ = 1.000000 + 0j`, phase ≈ 10⁻¹⁷ at both
d. But that is an analytic fact about the target state, **not** something this
run's hardware measured. The measured claim is "stationary up to a global
phase."

*Attempted and NOT closed.* A Hadamard test (IBM-6, same day) measured
`Re` and `Im` separately and **failed to certify the eigenvalue**. Its arms
were not depth-matched — the joint arm carries 29 two-qubit gates at d=8
against 8 for `system_only`, because a controlled clock-shift needs a
3-controlled X — so cross-arm comparison is confounded by circuit depth, and
at d=8 the shallow control arm measured *higher* than the joint arm. The
measured imaginary part was ~6σ from the zero theory requires, most likely
coherent error in the controlled-MCX cascade, which is exactly the systematic
that cannot be told apart from a genuine eigenvalue phase with this data.
**This limitation therefore stands, unclosed.** See
`AQ_PAGE_WOOTTERS_IBM_6_7_RESULTS_2026-08-08.md`; any future attempt must
depth-match the arms.

### 2. The clock/system bipartition is chosen, not derived

Nothing in the prepared state designates which qubits are "the clock." The
split was imposed in the circuit design and dynamics were then measured
relative to it. **Every run in this program — IBM-0 through IBM-5 —
demonstrates the Page–Wootters mechanism *given* a bipartition we selected,
not that a preferred bipartition emerges from the structure.**

The labelling is also arguably inverted relative to physical practice: our
"clock" register is an *index* over moments, while the single-qubit "system"
is the thing that *oscillates* (`⟨X_S|t⟩ = cos(2πt/d)`). In an atomic clock
the oscillator is the clock. There is a dimensional asymmetry that partly
justifies the choice — the Schmidt rank is 2, capped by the qubit system, so
inverting the roles would give a 2-state clock able to resolve only two
moments — but that is a consequence of the register sizes chosen, not a
derivation.

Testing this properly (the "clock ambiguity" problem) requires a state
admitting two inequivalent clock/system decompositions. Note that a
deliberately *symmetric* two-register state would beg the question: real
clock–system pairs are asymmetric precisely because a good clock has many
stable states and the timed system does not, so engineering the symmetry and
then observing it would be circular.

### 3. Prior art: stationarity has been measured before

[Moreva *et al.* (2014)](https://doi.org/10.1103/PhysRevA.89.052122)
demonstrated the Page–Wootters mechanism photonically and **explicitly
measured the external-observer stasis** — conditioning on a clock photon
yields dynamics while the global state remains static and pure. **This run is
therefore not the first experimental test of global stationarity, and no
priority claim should be made.**

What is different here is methodological: stationarity is tested as
invariance under a specific joint group element `Ŝ ⊗ U`, against three
mismatched controls (clock-only, system-only, and the reversed pairing) that
quantify *how* the invariance fails when the pairing is broken, on a
gate-based processor with pre-registered gates. That is a contribution to
method, not a first observation.

Related work on defining time observables in this setting:
[Favalli & Smerzi (2020)](https://quantum-journal.org/wp-content/uploads/2020/10/q-2020-10-29-354.pdf),
[*Measuring time in a timeless universe* (2024)](https://arxiv.org/abs/2406.14642).

## What it does not establish

Invariance under a discrete joint shift on 3–4 qubits is a **finite-dimensional
analogue** of the Wheeler–DeWitt constraint, not a test of quantum gravity, not
a continuum constraint, and not a claim that time in nature is emergent. The
history state is engineered; the clock has 4 or 8 states. The `Ĵ = H_C + H_S`
correspondence is structural — this run measures invariance under the group
element `Ŝ ⊗ U`, not the vanishing of a Hamiltonian constraint operator.

## Provenance

Backend `ibm_marrakesh`, 2 jobs, 2026-08-08T05:26Z. Job IDs in
`ibm5_results.json`. Capture before trial expiry (~2026-09-01):

```
python pw_ibm_provenance.py --results results_ibm5_ibm_marrakesh/ibm5_results.json --out results_ibm5_ibm_marrakesh/ibm5_provenance.json
```
