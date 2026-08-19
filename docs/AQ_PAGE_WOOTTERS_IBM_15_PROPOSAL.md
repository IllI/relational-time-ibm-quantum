# AQ-PAGE-WOOTTERS-IBM-15 — Two geometric phases, one entanglement sweep

**Proposal. Not run.** Predictions at
[`theory/verify_geometric_phase.py`](../theory/verify_geometric_phase.py).
This replaces the retracted design; read
[the retraction](../theory/verify_geometric_phase.py) first.

---

## What the retraction taught, and what changed

The previous attempt asked whether *the* geometric phase escapes the
entanglement budget. That question was malformed in two ways, and both are now
fixed:

**There is no single geometric phase for a mixed state.** There are at least
two inequivalent constructions, both published, both measurable, and they
disagree:

- the **interferometric** phase (Sjöqvist *et al.*,
  [Phys. Rev. Lett. **85**, 2845, 2000](https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.85.2845)),
  `arg Tr(ρ₀ U)` under per-eigenvector parallel transport;
- the **Uhlmann** phase, the holonomy of the Uhlmann connection on
  purifications — measured on superconducting qubits by
  [Viyuela *et al.*, npj Quantum Information **3**, 55 (2017)](https://www.nature.com/articles/s41534-017-0056-9),
  using an ancilla to carry the purification.

**A subsystem's cyclic loop is forced to be trivial unless the state is
tilted.** Cyclic evolution requires `U ρ U† = ρ`, and for a non-degenerate
reduced state the only such unitaries are diagonal in the Schmidt basis — 0 of
200 000 Haar-random `U` escape this. The retracted design died there. The fix
is to **tilt** the Bloch vector off the rotation axis by a local rotation, which
leaves `C` untouched and makes the cone loop genuinely cyclic and non-trivial.

## The design

Three qubits: interferometric ancilla `R`, target `T`, purifying partner `P`.

1. Entangle `T` with `P` by angle `χ`: `cos(χ/2)|00⟩ + sin(χ/2)|11⟩`, giving
   concurrence `C = |sin χ|` and target Bloch length `r = |cos χ| = √(1−C²)`.
   **Mixedness comes from entanglement, not temperature** — which is the point,
   and what distinguishes this from the thermal Uhlmann experiments.
2. Tilt by a local `Ry(θ)` on `T`. Local, so `C` is unchanged.
3. Drive the cone loop: a full `2π` rotation about `ẑ`, so the Bloch vector
   traces a cone of half-angle `θ`.
4. Read both phases — the interferometric one from the ancilla directly, the
   Uhlmann one via the holonomy acting on the purification.

## Predictions, at `θ = π/4`

```
   C        r        Uhlmann       interferometric
 0.0000   1.0000   -0.920141      -0.920151
 0.3681   0.9298   -0.706553      -0.884747
 0.6845   0.7290   -0.282449      -0.763757
 0.9048   0.4258   -0.046316      -0.509983
 0.9980   0.0628   -0.000138      -0.082300
```

**Both phases are entanglement-dependent — so the geometric phase is on the
budget, both ways.** That already answers the synthesis repository's question,
negatively, and at zero QPU cost.

**But they spend it at different rates, and that is the measurement.** They
agree at `C = 0` to six decimals, as they must for a pure state — a built-in
null. By `C = 0.905` they differ by a factor of **11** (`0.046` vs `0.510`).
That gap is far above any plausible hardware noise.

## The degeneracy trap — do not repeat my mistake

The `r`-dependence of the interferometric phase vanishes exactly when
`cos(π cos θ) = 0`, i.e. **`cos θ = 1/2`, `θ = π/3`**:

```
 theta/pi   cos(pi cos th)   phase spread over r
  0.200      -0.8253          0.558966
  0.250      -0.6057          0.841493
  0.333      -0.0000          0.000000   <- DEGENERATE
  0.400      +0.5646          0.883326
```

I picked `θ = π/3` by accident and got a constant phase, for the *third* time in
this line of work after two other degenerate choices. **`θ = π/4` is the
proposed working point**, and any re-parameterisation must re-check this map
before running.

## Pre-registered gates

1. **Degeneracy check (must pass first, in preflight).** `|cos(π cos θ)| > 0.5`
   at the chosen `θ`. If the working point is degenerate every later gate is
   vacuous — the failure mode that produced the retraction.
2. **Random-unitary control (preflight, before any claim).** The predicted
   separation must not survive when the loop is replaced by Haar-random
   unitaries. If a "result" appears for arbitrary loops it is arithmetic, not
   geometry. **This control runs first, not after a pleasing number appears.**
3. **Pure-state null.** At `C = 0` the two phases must agree to within
   measurement error. They coincide exactly in theory; disagreement here is
   instrumental and calibrates everything else.
4. **Divergence.** The two phases differ by more than `3σ` at `C ≥ 0.68`, with
   bootstrap confidence intervals, and the gap grows monotonically with `C`.
5. **Both curves entanglement-dependent.** Each phase individually varies with
   `C` beyond noise — establishing that the budget claim holds for both
   constructions, not just one.
6. **Noise-matched reference.** All margins as excess over a calibrated Aer
   model at the live calibration, per IBM-11/12/14.

## What still needs verifying before submission

**The Uhlmann circuit is not yet designed.** The holonomy must be implemented
as a two-qubit unitary on `(T, P)` — the partner *is* the purification, which is
what makes this tractable — but the specific transport unitary has to be
derived and asserted in preflight against the numerical holonomy above. Until
that is done this proposal is incomplete, and I am not claiming otherwise.

Estimated cost once designed: 3 qubits, one ancilla-interferometry circuit per
`(C, phase-type)`, roughly 8 values of `C` × 2 constructions × tomography of the
ancilla ≈ 100–150 circuits, comparable to IBM-14's 195 at ~105 s.

## What it would and would not show

**Would:** that the two standard mixed-state geometric phases give measurably
different answers about the same entangled states, on hardware, with mixedness
supplied by entanglement rather than temperature. And that both are on the
entanglement budget, closing the synthesis repository's question.

**Would not:** identify either as *the* geometric phase, or as a shared temporal
reference. The loops remain externally programmed. And the budget answer is
derived here — the hardware content is the divergence and its survival under
decoherence, not the fact of entanglement dependence.
