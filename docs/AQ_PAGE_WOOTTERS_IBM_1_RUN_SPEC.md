# AQ-PAGE-WOOTTERS-IBM-1 Run Spec — Where Relational Time Stops Being Quantum

*Drafted 2026-08-04. Successor to `AQ_PAGE_WOOTTERS_IBM_0_RESULTS_2026-08-03.md`.
Not yet executed — Gate 0 (Aer dry run with exact statevector predictions) must
pass before any hardware submission, per the discipline that caught three wrong
circuits in the sister OAT program.*

## What IBM-0 established, and what it left open

IBM-0 showed that the clock-marginal coherence of an engineered Page–Wootters
history state is measurable on hardware, scales with clock dimension, vanishes
at a structural null, and — critically — is **not** reproduced by a classical
clock, whereas the conditional evolution usually cited as the signature **is**.

That result is binary: coherent vs. classical, at zero environmental coupling.
It does not say *where the boundary is*. It leaves three questions open:

1. At what clock–environment coupling does the quantum signature of relational
   time disappear?
2. Does the apparent temporal dynamics survive past that point — i.e. does
   "time" keep appearing to flow after its quantum signature is gone?
3. Does the loss follow the functional form recent theory predicts?

Question 3 is now sharply posed by current work. A December 2025 relational-
emergent-time framework (arXiv:2512.15789) predicts local coherence decaying
as `C(E) = C₀·e^{−kE}` in clock–subsystem entanglement `E`, and explicitly
notes it "lacks explicit small-scale quantum processor protocols," suggesting
"clock decoherence monitoring" as the test. A February 2026 extended two-qubit
Page–Wootters model (*Phys. Lett. A*, S0375960126001325) predicts a monotonic
**informational arrow of time**: von Neumann entropy of the conditional system
state rising across successive clock readings once inaccessible degrees of
freedom are traced out.

This run is designed against both.

## Hypothesis

**H1 (threshold).** There exists a finite clock–environment coupling at which
the clock-marginal coherence witness falls to the classical baseline, while
conditional evolution — the apparent flow of time — remains intact. Relational
time therefore has a *quantum regime* and a *classical regime*, separated by a
measurable decoherence threshold, and the usual demonstration of emergent time
cannot distinguish them.

**H2 (functional form).** Across that crossover the witness decays as
`C(E) = C₀·e^{−kE}` in the clock–environment entanglement `E`.

**H3 (arrow).** With an inaccessible degree of freedom coupled to the system,
the conditional-state entropy `S(ρ_S|t)` rises monotonically in clock reading
`t` — and, by the same logic that made IBM-0's Arm B necessary, **this arrow is
expected to be reproduced by a classical clock too.** If so, the informational
arrow of time is, like conditional evolution, not by itself a quantum
signature. That is a falsifiable prediction of this design and worth stating
before the run.

## Design correction (recorded, because it nearly went the wrong way)

The obvious first design — couple an environment qubit to the **system** and
watch the clock coherence degrade — does not work, and the reason is
instructive. The clock marginal depends only on the record overlaps
`⟨χ_t'|χ_t⟩`, and *any* unitary acting on system⊗environment preserves those
overlaps exactly. The clock marginal is therefore completely unchanged by
system–environment coupling, and the witness would be flat across the sweep.

To degrade the coherence of relational time, the environment must couple to
the **clock** itself. This is not a technicality — it is the physical content:
the quantum signature of relational time lives in the clock's record structure,
so only decoherence of the records themselves can destroy it. Coupling the
system to an environment produces an arrow of time (H3) without touching the
clock's quantum structure (H1/H2). The two effects are independent, and this
run measures both.

## Circuits

Registers: clock `C` (`n_c` qubits, `d = 2^n_c`), system `S` (1 qubit),
environment `E` (`n_c` qubits for arm 1A, 1 qubit for arm 1B).

**Shared history-state preparation** (unchanged from IBM-0): Hadamards on the
clock, then a controlled-`Ry(2^k·θ)` ladder from clock qubit `k` to the system,
realizing `Σ_t |t⟩⟨t| ⊗ U^t` with `U = Ry(θ)`.

### 1A — Clock decoherence sweep (primary)

After the history-state ladder, apply `CRY(μ)` from **each clock qubit `k` to
its own environment qubit `E_k`**, then trace out `E` by simply not measuring
it. This gives an analytically clean, uniform dephasing of the clock records:

```
ρ_C[t,t']  =  (1/d)·cos((t−t')·π/d) · cos(μ/2)^{d_H(t,t')}
```

where `d_H` is the Hamming distance between clock-basis labels — the same
Hamming-distance dephasing structure that appeared in the sister OAT program's
Lindblad analysis, arrived at here from a completely different direction.

- `μ = 0` reproduces IBM-0 exactly (the anchor: witness must match the
  previously measured 0.177/0.497 exact values).
- `μ = π` fully dephases the records; the witness must fall to the classical
  baseline.
- Sweep `μ ∈ {0, π/8, π/4, 3π/8, π/2, 5π/8, 3π/4, 7π/8, π}` at `d = 4` and
  `d = 8`.

Measure at each `μ`: the coherence witness (inverse-QFT clock readout, as
IBM-0 Arm C), the conditional evolution `⟨Z_S|t⟩` (as Arm A), and the matched
classical-clock controls (Arms B and D).

### 1B — Informational arrow (secondary)

One environment qubit, coupled to the **system** by a fixed CNOT after the
ladder, with `θ = π/(2(d−1))` so the system traverses only a quarter
revolution across the clock range — keeping the conditional entropy in its
monotonic regime rather than folding back at half revolution.

Conditioned on clock reading `t`, tracing out `E` leaves
`ρ_S(t) = diag(cos²(tθ/2), sin²(tθ/2))`, so

```
S(ρ_S|t)  =  H₂(cos²(tθ/2))        (binary entropy)
```

rising monotonically from 0. **This needs no tomography** — `ρ_S(t)` is
diagonal in the computational basis, so a single Z-basis measurement of the
system conditioned on each clock reading gives the entropy directly.

Controls: no-coupling (`S(t) = 0` flat, proving the arrow requires the
inaccessible degree of freedom) and classical-clock (predicted to reproduce
the arrow — see H3).

## Endpoints and gates

Primary:
```
witness_tvd(mu, d)                    coherence vs clock decoherence
E_clock_env(mu)                       computed analytically, verified in dry run
conditional_evolution_R2(mu)          must stay high across the sweep
mu_threshold                          where witness meets classical baseline
```

Secondary: `S(rho_S|t)` monotonicity and its classical-clock counterpart.

```
Gate 0  Aer dry run: exact statevector predictions match sampled to <0.01;
        mu=0 reproduces IBM-0's measured values within shot noise
Gate 1  Anchor: witness(mu=0) consistent with IBM-0 (0.177 / 0.497 exact)
Gate 2  Monotone decay: witness strictly decreasing in mu at both d
Gate 3  Threshold exists: witness(mu=pi) within 3x the classical baseline
Gate 4  Persistence: conditional-evolution R^2 > 0.95 at ALL mu, including
        where the witness has collapsed  <-- this is H1, the headline
Gate 5  Functional form: fit C(E) = C_0 e^{-kE}; report R^2 and k with CI.
        A poor fit is a reportable negative against arXiv:2512.15789, not a
        failed run.
Gate 6  Arrow: S(rho_S|t) monotonically increasing; and its classical-clock
        control also increasing (H3 — expected, and the point)
```

**Gate 4 is the result.** A run where the witness collapses while conditional
evolution holds at R² > 0.95 demonstrates directly that apparent temporal
dynamics outlives its own quantum signature — which is the sharpest available
statement about what "time from entanglement" does and does not require.

## Budget

`d = 4`: 2 clock + 1 system + 2 env = 5 qubits. `d = 8`: 3 + 1 + 3 = 7 qubits.
Added cost over IBM-0 is `n_c` CRY gates (≈2 CX each), so ≈4–6 extra CX —
comfortably within the depths already shown to survive (IBM-0's d=8 witness ran
at depth 143–158 with 33–36 two-qubit ops and the separation held).

Nine `μ` points × 4 arms × 2 clock sizes at 8000 shots ≈ 100–150k shots, in the
same range as IBM-0's ~102k, which consumed roughly 48 s of QPU. **Recommended
backend: `ibm_marrakesh`** — it served all of IBM-0's primary run and 24 of the
36 archived jobs promptly, whereas `ibm_fez` and `ibm_kingston` queued for hours
on the free tier the following day.

## Claim boundary (inherited, unchanged)

**Would be claimable:** a measured decoherence threshold for the quantum
signature of relational time on superconducting hardware; a hardware test of a
published functional-form prediction; and a demonstration that both the
conditional-evolution signal *and* the informational arrow of time are
classically reproducible while the clock-marginal coherence is not.

**Not claimable, at any result:** that time in nature is emergent; any test of
quantum gravity or the Wheeler–DeWitt equation; realization of a physical
Page–Wootters universe. The history state remains engineered, not found.

## Implementation order

1. Extend `pw_ibm_dryrun.py` with the 1A/1B circuits and exact statevector
   predictions for `ρ_C[t,t']` under the Hamming-distance dephasing above.
   **Do not proceed until `μ=0` reproduces IBM-0 exactly.**
2. Extend `pw_ibm_submit.py` (checkpointing and layout verification already
   present) with the `μ` sweep; file the pre-registration before submitting.
3. Run `--dry` end to end; only then submit to `ibm_marrakesh`.
4. Capture provenance while the account is live (trial expires ~2026-09-01).
