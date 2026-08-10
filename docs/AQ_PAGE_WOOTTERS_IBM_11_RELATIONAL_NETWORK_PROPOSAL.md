# AQ-PAGE-WOOTTERS-IBM-11 — Proposal: is temporal order carried by the *network*?

**Status: proposed, NOT specified in runnable form, NOT executed.** Filed
2026-08-10. This is deliberately *not* part of the current paper — see
*Scoping* at the end.

## The question

Every run in this program picks a clock. Even IBM-7, which detunes two clocks
against each other, has a designated reference. That is limitation 2: *the
clock/system split is chosen, not derived.*

The proposal is to stop giving any subsystem special status. Encode only mutual
relations among three clocks `A, B, C` and a system `S`:

```
|Ψ⟩ = (1/√d) Σ_t |t⟩_A |αt⟩_B |βt⟩_C |ψ(t)⟩_S
```

where `t` is a summation label only — **no external `t` register is ever
measured.** The hardware is asked only relational questions: what does `B` read
when `A` reads this; what accompanies a given `C` reading; and does using `B`
as the clock instead of `A` give a compatible description?

## Two structural results derived before designing anything

Recorded first, because this program has twice paid for measuring quantities
that were fixed by construction (see the IBM-8 postscript).

### 1. Rate loop closure is automatic, not contingent

For the state above, the pairwise rates telescope:

```
α_AB = α        α_BC = β/α        α_CA = 1/β
α_AB · α_BC · α_CA = α · (β/α) · (1/β) = 1     identically, for all α, β
```

Numerically confirmed over many `(α, β)` at `d = 12`. **A run that
pre-registers "the loop closes" as a gate would be measuring a theorem** — the
same error as IBM-6/IBM-8, which spent two runs on an eigenvalue that was `+1`
by construction.

The contingent content is elsewhere, and the run must be built around *that*:

- whether the **prepared hardware state** actually realizes the intended
  relations (a fidelity-like question);
- whether **control networks admit any consistent assignment at all** — this is
  the discriminating test;
- whether the **three frame-reconstructions agree** with one another.

Framed correctly, the claim is a comparison — *the coherent network yields a
consistent temporal ordering and the rewired one does not* — not a
verification of closure.

### 2. A clock can only serve as a reference frame if `gcd(α, d) = 1`

Using B as the clock requires recovering the shared label from B's readings,
which requires `t ↦ αt mod d` to be **injective**, i.e. `gcd(α, d) = 1`.
Equivalently, `B→C` is expressible as a rate only if `β = m·α (mod d)` is
solvable, which again needs `α` invertible. At `d = 12` only **4 of 11** rates
qualify (`α ∈ {1, 5, 7, 11}`).

*Precision note:* an earlier draft of this section said "no pairwise rate
exists" when `gcd(α,d) ≠ 1`. That is wrong in one direction — the rate *from*
the summation label *to* B is always defined, being `α` by construction. What
fails is the reverse, which is what "use B as the clock" actually requires. The
corrected statement is verified executably in Program 3's
`theory/verify_structural_results.py`.

This is a *new* structural condition and is **not** the same as IBM-7's
commensurability. IBM-7's integer resonance is about exact cycle closure after
`d` ticks; this is about invertibility — whether a clock has the resolution to
serve as a frame at all. Both are finite-clock artifacts, and both would need
scoping in any write-up.

## What would actually be tested

| test | contingent? | notes |
|---|---|---|
| pairwise relations `A→B`, `B→C`, `C→A` recovered | yes | the IBM-7 measurement, three times |
| rate composition = 1 | **no — theorem** | use as a *consistency check on the prepared state*, never as a physics gate |
| three frame-reconstructions mutually predict | **yes** | the real content |
| controls admit no consistent ordering | **yes** | the discriminating test |
| network correlations certified entangled | yes | multi-setting fidelity, per IBM-4 |
| coherent superposition of *which subsystem is the frame* | yes | the IBM-9 construction applied to frame choice |

**Controls, following IBM-2→4.** Each must leave every local marginal
`ρ_A, ρ_B, ρ_C` unchanged while altering the network: shuffle the `A↔B`
pairing; sever `B↔C`; reverse one edge; replace quantum correlations with a
classical correlated mixture; detune one rate; randomly rewire clock labels.
If the local states are identical before and after but only the coherent
network yields a consistent ordering, the temporal information demonstrably was
not in any clock individually.

**The superposed-frame extension** is the most novel piece: a control qubit `G`
with `|0⟩_G → A is the reference`, `|1⟩_G → B is the reference`. Z on `G` gives
the two ordinary relational descriptions; X on `G` tests whether the two
*reference-frame descriptions* interfere — exactly IBM-9's discriminator moved
from rates to frames.

## Feasibility, honestly

- **Qubits:** three `d = 4` clocks (6) + system (1) = **7**, or 8 with `G`.
- **Depth:** preparing `|αt⟩_B` requires modular multiplication — a controlled
  permutation, roughly **30 CX before any measurement**. That is IBM-8's fatal
  depth (29 CX), survivable only because this design has no Loschmidt echo and
  no `V†`. IBM-9 ran clean at 24 CX, so this is plausible but not comfortable.
- **Circuits:** 3 pairwise relations + 3 frame reconstructions + 6 controls +
  network fidelity settings (7 qubits ⇒ many QWC groups) + 2 superposed-frame
  settings ≈ **50–100 circuits**, versus IBM-10's 19.
- **Budget:** roughly 2–3 minutes of QPU, against a trial with ~3 minutes left
  and **no margin for the retry this program has repeatedly needed.**

## What it could and could not claim

If every test passed, the defensible claim is:

> In this engineered system all experimentally recoverable temporal information
> is carried by a self-consistent network of relations among subsystems: no
> single subsystem contains the ordering, no privileged master clock is needed
> to reconstruct it, and rewiring the relations destroys the common temporal
> description while leaving every local marginal unchanged.

That is a real advance over *"one subsystem can be used as a clock."*

**What it would still not do is derive the clock.** It would show that no
*unique* master clock is required among three that we chose and engineered.
Limitation 2 would be narrowed, not closed. And the state would still be
prepared by externally timed gates in ordinary laboratory time (limitation 6),
so nothing here bears on whether time in nature is emergent.

## Scoping: why this is not in the current paper

1. **It is a different question.** The current program asks what relational-time
   observables certify. This asks whether temporal order is carried by a
   network — a quantum-reference-frame question, and a separate paper.
2. **The current arc is complete and consistent at 11 runs.** Appending a 12th
   of unrelated design would blur both stories.
3. **The headline test needs redesign** before it is worth submitting, per
   structural result 1 above.
4. **The trial cannot fund it properly**, and this program's own record says a
   rushed pre-registration produces gates encoding false assumptions.

Recommendation: publish the current program as it stands, and treat this as the
opening of a second line — with structural results 1 and 2 above as its first
contributions, already derived at zero QPU cost.

**That second line now exists** as its own repository, Program 3
(*Relational Clock Networks and Self-Timed Quantum States*), which carries this
proposal forward as Run A of four and adds two further structural results: that
relativistic time dilation trades local throughput for Earth-frame storage
rather than accelerating computation, and that Holevo/superdense bounds require
any "semantic compression" to be earned in the classical layer.
