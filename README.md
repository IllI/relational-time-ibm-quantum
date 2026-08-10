# Measuring the Quantum Signature of Relational Time on Superconducting Hardware

**What this is.** An experimental program testing whether *relational time* —
time defined by correlations between a clock and the rest of a system, rather
than by an external parameter — leaves a measurable quantum signature that can
be distinguished from its classical mimic. It runs from three disciplined
nulls on classical substrates, through a simulation campaign on **Google TPU
Research Cloud** hardware that built the hypothesis and the certification
standard, to **eleven pre-registered runs on IBM Quantum Heron processors** (72
jobs) — nine positive, two reported as failures.

**The short version.** The signature usually cited as "time from entanglement"
is classically reproducible, and this program measured that on hardware. It
then spent four runs discovering that its own replacement witnesses were also
insufficient — using adversarial states it constructed against itself — before
reaching an observable that provably cannot be mimicked. What survives is a
hardware-measured account of the Page–Wootters mechanism's defining
properties — **entangled, stationary up to a global phase, internally
evolving, and supporting coherent superposition and interference between two
programmed relational evolution rates** — each certified by a distinct
observable rather than inferred from one tomographic fit.

> [!IMPORTANT]
> **The conjunction is certified on a single preparation (IBM-10,
> 2026-08-09).** Entanglement (IBM-4) and stationarity (IBM-5) were originally
> measured on **orthogonal** states — fidelity 0.000 at `d = 4` — so the
> Page–Wootters mechanism's actual content, *a state that does not change
> globally while its conditioned slices do*, had never been measured on one
> state. IBM-10 puts all three arms on the same `P(2π/d)` cyclic preparation in
> one job: **F = 0.9014** against the separable bound ½, **joint echo 0.8630**
> against mismatched controls at 42σ–143σ, and **`⟨X_S|t⟩` amplitude 0.9193**
> at R² = 0.9942. The single-state discipline is enforced by pre-submission
> assertions, not prose — see
> `docs/AQ_PAGE_WOOTTERS_IBM_10_RESULTS_2026-08-09.md`.

All raw counts, pre-registrations, and provenance are archived here; every
analysis reproduces from counts with no IBM account.

---

## The question

Page and Wootters (1983) proposed that a universe in a globally *static*
entangled state contains apparent dynamics: partition it into a clock `C` and
a system `S`, and conditioning `S` on a clock reading yields an evolving
system state — with no external time parameter anywhere. Moreva *et al.*
(PRA **89**, 052122 (2014)) illustrated this with entangled photons, and the
idea has since been extended to quantum reference frames, relativistic clocks,
and cosmology.

**The standing objection is that the usual demonstration proves nothing
quantum.** A classically correlated clock–system state,
`ρ = (1/d) Σ_t |t⟩⟨t| ⊗ |ψ(t)⟩⟨ψ(t)|`, reproduces the conditional evolution
`⟨Z_S | t⟩` *exactly*. If "time flows relative to the clock" is the whole
signature, a classical clock delivers it too, and nothing has been shown about
quantum time.

## Hypothesis

If relational time in the Page–Wootters sense is genuinely quantum, the
distinguishing structure cannot live in the conditional dynamics. It must live
in the **coherence of the clock marginal**.

Tracing the system out of the history state
`|Ψ⟩ = (1/√d) Σ_t |t⟩_C ⊗ U^t|0⟩_S` gives

```
ρ_C[t,t'] = (1/d) ⟨ψ(t')|ψ(t)⟩ = (1/d) cos((t − t')·π/d)
```

Those off-diagonals are the overlaps between clock records — the degree to
which different "moments" are *not* perfectly distinguishable. The classical
mixture has the identical diagonal and **exactly zero** off-diagonals. So the
hypothesis is concrete and falsifiable:

1. **The clock marginal carries coherence that no classical clock–system
   correlation can reproduce**, and it is measurable by reading the clock in
   its Fourier (energy) basis — the basis conjugate to clock-time, whose
   eigenstates are the eigenstates of the clock's shift generator. A peaked
   Fourier distribution reflects the clock–system constraint structure that
   defines a history state; a classical mixture is exactly uniform there.
   *(This is why the inverse quantum Fourier transform is not incidental
   machinery here — it is the measurement that accesses the constraint.)*
2. **The signature should strengthen with clock dimension `d`**, because
   adjacent records become *less* orthogonal as `d` grows (`cos(π/d) → 1`),
   putting more coherence into `ρ_C`.
3. **It must vanish structurally at `d = 2`**, where the history state is
   exactly a Bell pair and the clock marginal is maximally mixed — a null
   predicted by theory, reachable with the same apparatus by changing nothing
   but the clock size.

### How this hypothesis fared

Stated here rather than buried below, because **the program refuted part of
its own filed hypothesis and that refutation is its main methodological
result.** The three numbered claims are reproduced above exactly as
pre-registered on 2026-08-03, unedited.

| filed claim | verdict | by |
|---|---|---|
| (2) signature grows with `d` | **confirmed** — 0.005 → 0.16–0.21 → 0.33–0.42 | IBM-0, two devices |
| (3) structural null at `d = 2` | **confirmed** — 0.005–0.007 | IBM-0 |
| (1) *"no classical clock–system correlation can reproduce it"* | **confirmed** for the classical mixture | IBM-0 arm D |
| (1) *"a peaked Fourier distribution reflects the clock–system constraint structure that defines a history state"* | **REFUTED** | IBM-2, IBM-3 |

The refuted clause is the italicized one, and it failed hard: a **zero-entanglement product state** scores 4.2× *higher* on that witness than the
history state does (IBM-2), and a **separable** state scores 1.7× higher on
the joint-readout witness built to repair it (IBM-3). A two-line theorem then
generalized the failure — no single **local product-basis distribution** can
certify clock–system entanglement, so every witness in the original design was
entanglement-blind by construction, despite the history state being maximally
entangled. (The theorem is about local product-basis distributions
specifically; it does not rule out that some global entangled measurement
could serve as a witness in a single configuration.)

**The corrected hypothesis, which the rest of the program tests:** the quantum
signature of relational time is not carried by any single distribution. It is
carried by *relationships between complementary measurement settings* — and it
is certifiable, which IBM-4 (fidelity witness), IBM-5 (stationarity), IBM-7
(commensurability), and IBM-9 (rate superposition) then demonstrate. The
original hypothesis identified the right *quantity* (clock-marginal coherence)
and the wrong *epistemic status* for it.

**The witness is neither sufficient nor necessary for clock–system
entanglement**, and the program proves both halves — the second one
accidentally. IBM-2 demonstrates insufficiency directly. Necessity fails at
`d = 2`, which is the very null the hypothesis pre-registered as a
confirmation: that state carries **1.0 ebits, maximal entanglement, while the
local witness reads exactly 0.000000** and the clock marginal is exactly
maximally mixed. Filed claim 3 was therefore confirmed as a prediction *and* is
a counterexample to necessity at the same time. What the witness tracks is
clock coherence, which at `d = 2` is absent from a maximally entangled state.

## What was tested

Eleven runs on IBM Heron r2 processors, each pre-registered before submission.
The program is best read as three movements:

| movement | runs | question |
|---|---|---|
| **I. The witness** | IBM-0, IBM-1 | does relational time leave a signature the classical mixture cannot reproduce, and does it survive decoherence? |
| **II. What the witness certifies** | IBM-2, IBM-3, IBM-4 | can that signature be faked? (twice: yes) — and what, if anything, cannot be? |
| **III. The constraint itself** | IBM-5 … IBM-10 | is the global state stationary, what happens when the clock rates are detuned, and can the *rate of time* be superposed? |

Movement II is the methodological core: each run was an adversarial control
this program built to attack its own previous result.

### Movement I — the four-arm protocol

At clock sizes `d = 2, 4, 8`:

| Arm | Clock prepared | Clock measured in | Tests |
|---|---|---|---|
| **A** | superposition | computational | conditional evolution `⟨Z_S\|t⟩ = cos(2πt/d)` |
| **B** | definite `\|t⟩`, averaged 1/d | computational | *the objection* — must reproduce A exactly |
| **C** | superposition | inverse-QFT | clock-marginal coherence |
| **D** | definite `\|t⟩`, averaged 1/d | inverse-QFT | classical baseline — must be uniform |

Arms B and D are real hardware circuits, not classical post-processing: a
definite clock state averaged over `t` with weight `1/d` realizes the
classical mixture exactly.

### Movements II and III — the observables that followed

Each row is a distinct measurement design, not a re-analysis of the counts
above. The progression is forced: every entry exists because the entry above
it was shown to be insufficient.

| run | observable | why it was built |
|---|---|---|
| **IBM-2** | same witness, adversarial input | tests whether a *product* state (zero entanglement) can score on the arm-C witness |
| **IBM-3** | `W_joint = TVD(p(k,z), p(k)p(z))` | the repair for IBM-2 — and its own adversarial test, a separable mixture |
| **IBM-4** | fidelity witness, 10/20 QWC settings | exceeds the *derived* separable bound `λ_max = ½` — certification is mathematical, not "no adversary happened to beat it" |
| **IBM-5** | Loschmidt echo of `Ŝ ⊗ U` | tests global *stationarity*, the half Page–Wootters is named for |
| **IBM-6/8** | Hadamard test, β-swept | attempts to certify the constraint eigenvalue is exactly `+1` — **both failed** |
| **IBM-7** | two clocks at rate ratio `α` | detunes the pairing; asks when the constraint still closes |
| **IBM-9** | which-rate qubit `G`, read in Z and X | superposes two proper-time histories and looks for interference |
| **IBM-10** | all three arms on ONE preparation, one job | certifies the *conjunction* — IBM-4 and IBM-5 had used orthogonal states |

## Conclusion

**Program-level, stated as narrowly as eleven runs support:**

> In engineered 2–5 qubit history states on superconducting hardware, the
> conditional-evolution signal usually cited as evidence for relational time is
> classically reproducible, and **no single local product-basis distribution
> can do better** — a theorem, not a limitation of this apparatus. (Stated
> precisely: under the local measurement architecture used here, certification
> requires incompatible settings. This is *not* the claim that no
> single-configuration observable whatsoever could certify entanglement — a
> suitable global entangled measurement can be a witness in one configuration.)
> Given that standard, each
> defining property of the Page–Wootters mechanism was measured by a distinct
> observable: **entangled** — a multi-setting fidelity witness *exceeding the
> exact separable bound* `λ_max = ½` (F = 0.94/0.88), **stationary as a ray**
> under the paired operation `Ŝ ⊗ U` and not under the mismatched controls
> (44σ–167σ), **internally evolving** under the same operator that enforces
> that stationarity (R² = 0.994), subject to a **hardware-measured
> commensurability condition for exact cycle closure of a finite cyclic
> clock**, and **supporting coherent superposition and interference between
> two programmed relational evolution rates** (interference 0.2411 where every
> classical rate mixture predicts zero). **The first three hold jointly on a
> single preparation** (IBM-10: F = 0.9014, joint echo 0.8630 at 42σ–143σ,
> conditional amplitude 0.9193 at R² = 0.9942) — which is the mechanism's
> actual content, rather than three properties of three states. What is **not**
> certified is the *phase* of the stationarity eigenvalue, and therefore the
> stronger `+1` constraint condition: attacked twice, failed twice.

The narrow Movement I result, which the above is built on:

> In a 2–4 qubit engineered history state on superconducting hardware, the
> conditional-evolution signal usually cited as "time from entanglement" is
> reproduced by a classical clock control to within shot noise — confirming
> the objection experimentally. The clock-marginal coherence is **not**
> reproduced: it separates the coherent history state from its classical
> mimic by 5–10× on two devices, grows with clock dimension as predicted
> (measured ≈0.005 → 0.16–0.21 → 0.33–0.42 against exact values 0, 0.177,
> 0.497), and vanishes at the `d = 2` structural null.

> [!IMPORTANT]
> **The clock-marginal witness is neither necessary nor sufficient for
> clock–system entanglement — measured, not speculated.** Insufficiency is
> shown here; non-necessity at `d = 2`, where a maximally entangled state
> (1.0 ebits) has a local witness of exactly zero. An adversarial run
> (IBM-2, 2026-08-07) prepared a coherent
> clock–system *product* state `(1/√d)Σ_t|t⟩_C ⊗ |0⟩_S` with **zero**
> entanglement and found it scores **4.2× (d=4) and 1.9× (d=8) higher** on the
> local witness than the actual history state. The witness certifies *clock
> coherence*, not clock–system structure. The statement above — that the
> classical mixture fails to reproduce it — stands; any reading of it as
> certifying the Page–Wootters structure specifically does not.
>
> The same run measured a joint-readout witness
> `W_joint = TVD(p(k,z), p(k)p(z))` from the same counts, which separates the
> history state from **both** adversarial controls (0.300 vs 0.004 and 0.014
> at d=8; 15× its own noise floor). See
> `docs/AQ_PAGE_WOOTTERS_IBM_2_RESULTS_2026-08-07.md`.
>
> **A second adversarial run (IBM-3, same day) then did the same to the fix:**
> a *separable* 50/50 mixture of two coherent product states — zero
> entanglement, but clock coherence plus classical clock–system correlation —
> scores **0.47/0.45 on `W_joint`, 1.7× the history state's value**, exactly
> as statevector predicted (0.500 vs 0.302/0.379). A two-line theorem
> (`docs/AQ_PAGE_WOOTTERS_IBM_3_RESULTS_2026-08-07.md`) generalizes this: any
> single-product-basis distribution is exactly reproducible by a separable
> state, so **no observable measured in this program — local witness, joint
> witness, conditional evolution, the arrow — certifies clock–system
> entanglement, and none could have.** This despite the history state being
> *maximally* entangled across clock|system (Schmidt coefficients exactly
> ½, ½). What the witnesses certify, and certify well, is clock *coherence*
> (local) and coherence-plus-correlation (joint).
>
> **The witness arc closes with IBM-4 (same day): entanglement certified.** The
> multi-setting fidelity witness — 10/20 incompatible measurement settings,
> immune to the diagonal-mimic construction by design — measured
> **F = 0.9419 (d=4) and 0.8829 (d=8) against the derived bound
> λ_max = 0.5**, certifying clock–system entanglement with margins of
> +0.44/+0.38, while the two adversarial states that defeated the earlier
> witnesses were correctly rejected (F = 0.02–0.06, near their exact
> values). Necessary → insufficient → insufficient → sufficient, measured:
> `docs/AQ_PAGE_WOOTTERS_IBM_4_RESULTS_2026-08-07.md`.

> [!NOTE]
> **Both halves of the mechanism are now measured (IBM-5).** Everything above
> concerns the *conditional* half — dynamics appear when you condition on a
> clock reading. The half Page–Wootters is named for, that the global state is
> **stationary**, went untested until IBM-5. A Loschmidt echo shows the state
> is invariant under the joint operation `(Ŝ ⊗ U)|Ψ⟩ = |Ψ⟩` (return
> probability 0.903 at d=4) but **not** under either factor alone (0.461
> clock-only, 0.499 system-only) nor under the mismatched pairing `Ŝ ⊗ U⁻¹`
> (0.024) — separations of 44σ–167σ. Only the correctly *paired* operation
> preserves the state, and that pairing is the constraint. The same `U` that
> compensates the clock shift generates the conditional sequence
> `⟨X_S|t⟩ = cos(2πt/d)` (R² = 0.994), routed through one shared source
> function so the identity is structural rather than numerical.
>
> Designing that run surfaced a property of the state used in IBM-0…IBM-4: its
> generator `Ry(2π/d)` satisfies `U^d = −I`, so **that** state is cyclically
> stationary only up to a sign on the wraparound term — a history state in the
> conditional sense but not exactly stationary. IBM-5 uses `P(2π/d)` with
> `U^d = +I` exactly. One gate failed as written at d=8 (the test's contrast
> degrades as the clock gets finer) and is reported as failed, with the
> corrected statistic separate:
> `docs/AQ_PAGE_WOOTTERS_IBM_5_RESULTS_2026-08-08.md`.

> [!NOTE]
> **The constraint is dilated, and rate superposition interferes (IBM-7,
> IBM-9).** Having established that the *paired* operation `Ŝ ⊗ U` is what
> preserves the state, IBM-7 asks what happens when the pairing is detuned —
> when the system runs at rate `α` against the clock's unit rate. The answer
> is a **commensurability resonance** — scoped to a *finite cyclic* clock,
> where exact return after `d` ticks is what is being demanded, so a branch
> accumulating `2πα` closes only at integer `α`. This is a hardware-measured
> cycle-closure condition, **not** a general Page–Wootters prohibition on
> irrational rate ratios: in continuum or noncyclic models such ratios simply
> generate quasiperiodic, nonrepeating relational trajectories. With that
> scope: the constraint closes only at integer
> `α`, and the measured conditional frequency tracks the programmed rate over
> `α ∈ [0.5, 3]`. One pre-registered gate failed and the failure was
> informative — the matched pairing is *not* maximal at `α = 0.75`, exactly as
> theory says it should not be, so the gate encoded a false assumption and the
> data corrected it. Nyquist aliasing (`α` and `d − α` are indistinguishable
> with `d` clock samples) is a hard resolution limit, not an artifact:
> `docs/AQ_PAGE_WOOTTERS_IBM_7_RESULTS_2026-08-08.md`.
>
> **IBM-9 (2026-08-08) then puts the clock into a superposition of rates** —
> the discrete analogue of Smith & Ahmadi quantum time dilation
> ([arXiv:1904.12390](https://arxiv.org/abs/1904.12390)). A which-rate qubit
> `G` in `|+⟩` selects between `α₁ = 1` and `α₂ = 2`, so the system evolves
> along two proper-time histories at once. Read `G` in **Z** and the result is
> an ordinary classical mixture: the marginal tracks the closed-form
> `[cos(α₁θt) + cos(α₂θt)]/2` (max residual 0.089) and post-selection recovers
> the two branch rates at **0.981 and 1.964**, both R² 0.994. Read `G` in
> **X** and conditioning on `G = +` shifts the dynamics by **0.2411** where
> any mixture predicts exactly zero — **2.32× the 3σ bar**, retaining 91.6% of
> the exact 0.2632, with the sign pattern and relative magnitudes tracking
> prediction across all eight clock readings (shape correlation 0.85). **A
> decohered which-rate qubit is excluded by the data**: were `G` classically
> mixed, an X measurement would return 50/50 independent of everything and the
> `G = +` conditional would equal the marginal identically. It does not. Being
> a *two-setting* claim, this escapes IBM-3's single-setting mimic by the same
> structural route as IBM-4's fidelity witness. All 3 gates pass — the only
> run in the program to **exceed** its own pre-run feasibility estimate:
> `docs/AQ_PAGE_WOOTTERS_IBM_9_RESULTS_2026-08-08.md`.

**What this does not show.** It does not show that time in nature is emergent,
does not test quantum gravity or the Wheeler–DeWitt equation, does not realize
a physical Page–Wootters universe — and, per IBM-3, does not certify the
clock–system *entanglement* of the engineered history state by any measured
observable. What the program establishes is a systematic, hardware-measured
anatomy of relational-time observables: the conditional-evolution signal and
the informational arrow are classically reproducible; the clock-coherence
witness is not, scales with clock dimension, has a structural null, and has a
measured decoherence threshold past which apparent temporal dynamics survives
its own quantum signature; and each witness's certification limit was found
and quantified by this program's own pre-registered adversarial controls —
the local witness by IBM-2, the joint witness by IBM-3 — rather than left for
a referee. The clock's quantumness is certified throughout as *coherence*;
its quantumness as *relational* — genuine clock–system entanglement — is
certified by IBM-4's multi-setting fidelity witness — the one observable in
the program that provably cannot be mimicked by a separable state, tested
against the exact adversarial states that broke its predecessors. IBM-5 then
closes the mechanism by measuring its other half: the global state is
stationary under the joint clock-shift-plus-evolution and under nothing else,
with the operator that makes it stationary being the same one that generates
its conditional dynamics. IBM-7 then detunes that pairing and finds the
finite cyclic constraint closes exactly only at commensurate rates, and IBM-9 puts the rate itself
into superposition and measures the interference between two proper-time
histories — a signature no classical mixture of rates can produce. What the
program delivers is therefore both a hardware-measured anatomy of what
relational-time observables certify, and a hardware measurement of each
defining property of the Page–Wootters mechanism by a distinct observable —
though, as flagged at the top and in limitation 4 below, **across two
orthogonal history states rather than one preparation.** Two of the program's
ten runs are reported as failures (IBM-6, IBM-8), both attacking the same
limitation, which is published unclosed.

### Known limitations, stated plainly

Seven. The first three were identified in review of IBM-5 and are recorded in
full in `docs/AQ_PAGE_WOOTTERS_IBM_5_RESULTS_2026-08-08.md`; 4–7 were
identified in pre-publication review of the whole program and mark the
boundary between a Page–Wootters *realization* and a theory of why time
exists:

1. **Stationarity is certified up to a global phase; the stricter
   zero-generator condition is not.** The Loschmidt echo measures
   `|⟨Ψ|A|Ψ⟩|²`, and a strongly preferential return under the correctly
   paired operation against mismatched controls establishes stationarity **in
   the ordinary physical sense** — `|Ψ⟩ → e^{iφ}|Ψ⟩` is the same ray, so this
   is a real result and not a hedge. (The raw value is 0.903, so it is a
   certification of ray-stationarity *relative to controls*, not a direct
   measurement of unit modulus.) The phase matters only for the stronger
   analogy `(H_C + H_S)|Ψ⟩ = 0`, where a *zero* eigenvalue is a stricter
   condition than *being* an eigenstate — and that stricter, Wheeler–DeWitt-
   analogous condition remains uncertified. This is not
   cosmetic: the Wheeler–DeWitt constraint is `Ĥ|Ψ⟩ = 0` specifically, and a
   nonzero phase would mean an eigenstate carrying nonzero "energy" — not the
   constraint. The prepared state's eigenvalue *is* exactly +1 by statevector
   (phase ≈ 10⁻¹⁷), but the hardware did not measure it.

   **This limitation was attacked twice and remains open.** IBM-6
   (2026-08-08) ran the Hadamard test and failed: its four arms had wildly
   different two-qubit cost (29 CX for the joint arm vs 8 for the control at
   d=8), so the shallow control outscored the joint arm and the comparison was
   confounded by depth rather than physics. IBM-8 fixed that properly — one
   angle swept through one *identical* circuit, with the dry run **asserting**
   equal transpiled cost at every β — and **still failed** (d=8: 0/4 gates,
   43% of signal gone and the curve non-monotone; d=4: 2/4, borderline). That
   is the useful part: IBM-6 had *two* causes and depth asymmetry was the
   lesser one. The dominant cause is that the **controlled clock-shift is too
   expensive for the signal to survive**, which depth-matching cannot address.
   A further trap surfaced: fitting a β-independent offset to separate
   coherent error from a genuine phase can absorb exactly the quantity being
   measured, so even the one gate that passed does not license claiming the
   eigenvalue is real. **Two pre-registered attempts, both reported as
   failures, and the recommendation is to stop rather than tune a third until
   it passes**: `docs/AQ_PAGE_WOOTTERS_IBM_8_RESULTS_2026-08-08.md`.
2. **The clock/system split is chosen, not derived.** Nothing in the state
   designates which qubits are the clock; the bipartition was imposed in the
   circuit design. Every run here demonstrates the mechanism *given* a frame
   we selected, not that a preferred frame emerges. (Note the labels are
   arguably inverted from physical practice — our "clock" is an index, our
   "system" is the oscillator.)
3. **Global stationarity was measured before this work.**
   [Moreva *et al.* (2014)](https://doi.org/10.1103/PhysRevA.89.052122)
   demonstrated external-observer stasis photonically. No priority is claimed
   here; the contribution is methodological — testing invariance under a
   specific joint group element against mismatched controls that quantify how
   the invariance fails.
4. **~~The properties were measured on two different states.~~ CLOSED by
   IBM-10 (2026-08-09).** IBM-4 and IBM-5 used **orthogonal** preparations
   (fidelity 0.000 at `d = 4`, 0.005 at `d = 8`), not related by any
   system-local unitary — they differ by a *clock-conditioned* phase, which is
   precisely the `U^d = −I` vs `U^d = +I` distinction IBM-5 discovered. So the
   conjunction was never measured on one state. IBM-10 measured it: all three
   arms on the same `P(2π/d)` preparation, one job, one calibration epoch.
   Retained here rather than deleted because the gap was real and the record
   of closing it is part of the evidence. **Caveat:** `ibm_marrakesh` was in
   `maintenance` status during that run — every gate passed with large
   margins, and the joint echo (0.8630) replicates IBM-5's (0.9030) to within
   4.4% with the same control structure, but the status is recorded.
5. **The certification is device-dependent.** A fidelity witness assumes the
   measurement operators are what they are labeled. This is not a Bell test
   and no loophole-free claim is made. A CHSH test on the effective
   two-dimensional Schmidt subspace would give a stronger operational
   nonclassicality test, but **would not** make the result
   device-independent: two logical subsystems on the same superconducting
   processor are not spacelike separated. Genuine device-independent
   certification would require physically separated parties, independent
   measurement choices, and the usual loophole controls — a substantially
   larger experiment.
6. **The state is engineered, not found.** Externally timed gates compile it.
   There is no measured Hamiltonian constraint and no autonomous dynamics: the
   *internal description* has Page–Wootters structure, but the preparation is
   a laboratory sequence in ordinary external time, not a universe satisfying
   a timeless constraint.
7. **Commensurability is a finite-cyclic-clock property.** IBM-7's integer
   resonance follows from demanding exact return after `d` ticks. It says
   nothing about continuum or noncyclic Page–Wootters models, and nothing
   about gravitational dilation.

## Where the method came from: TRC TPUs and D-LinOSS

**Not one QPU circuit in this program was designed on a QPU.** The hypothesis,
the observables, the adversarial controls, and the certification standard were
all built on **Google TPU Research Cloud** `v6e` instances with the
**D-LinOSS** damped linear oscillatory state-space model, during the grant
window **2026-04-21 → 2026-06-21** (a one-month grant extended by a second
month specifically on the time-emergence thesis). The lineage is load-bearing,
not ceremonial, and it is worth being precise about *how* a classical
simulation campaign produced a quantum measurement program.

### The TPUs were both instrument and specimen

The program's first movement (CHRONOS, Part I) did not merely *run on* TPUs —
it **measured them**. Two TPU hosts in `us-east1-d` and `europe-west4-a` each
emitted a 128 Hz "now" stream, and the question was whether independent
datacenter hosts share learnable temporal structure. That framing let the
grant hardware serve as the experimental substrate itself, and it is what made
the null decisive rather than inconclusive: the killer control
(`CHRONOS-MARGINAL-DRIFT-1`) found that US/EU feature correlation `r ≈ 0.57`
**survives a one-hour offset** at `r ≈ 0.50`. That is structural hardware
similarity, not shared time — a result only obtainable by having two real,
geographically separated machines under instrumentation.

Establishing that classical telemetry is the *wrong substrate* is what moved
the clock inside the modeled state, and eventually onto a QPU.

### What D-LinOSS is, and why it fits this question

D-LinOSS is a state-space recurrence `x_{k+1} = Λ x_k + B u_k` with **Λ complex
diagonal**, `λ_j = exp((−γ_j + i ω_j) Δt)`. Each mode is a damped oscillator:
a frequency `ω_j` and a decay rate `γ_j`. That is not an incidental
architectural choice for this problem — it is the *same object* as the physics
under test. The Page–Wootters system qubit evolving under `U = P(2πα/d)` is
exactly one D-LinOSS mode with `ω = αθ`, and hardware decoherence supplies the
`γ`. The model class and the physical system are structurally matched, which
is why the model's failures were diagnostic rather than merely disappointing.

### D-LinOSS's negatives carried the information

Three times the informative result was a **failure**, and each one set a
parameter of the hardware program:

1. **Entropy is required.** A projected-harmonic generator proved
   *under-identifiable* — no matcher, metric, or embedding could recover the
   clock correspondence, diagnosed by observability-first decomposition rather
   than tuning. Recovery only became possible once the generator produced
   irreversible, entropy-bearing histories (arm `A10`). This independently
   converged with the entropic-time construction later published for cold
   atoms (arXiv:2509.07745, `τ ∝ ∫dS`).
2. **Physics-damped beats stationary — and where it doesn't, that's data.**
   The *event-damped* D-LinOSS (damping driven by entropy/event observables —
   the original grant thesis, "a state-space model damped by physical
   constraints") closed the ridge gap across ten seeds through noise 0.03. But
   the *entanglement-damped* variant **lost to a stationary model at every
   tested grid density**. That structured loss exposed the wrong functional
   form and pointed at record overlap as the correct independent variable —
   which IBM-1 then confirmed on hardware as a **power law in
   `cos(μ/2)`** (exactly linear at `d = 4`; `p ≈ 1.06–1.21` at `d = 8` —
   density-dependent, so not a universal `p = 1` law). This is a different
   functional form from the exponential-in-entanglement decay of
   arXiv:2512.15789, but deliberately **not** stated as contradicting it: that
   paper's `E` is clock–subsystem entanglement, whereas IBM-1's independent
   variable is environment–(clock+system) coupling. Different quantities, so
   the honest claim is the narrow one about our own.
3. **The certification standard came from a D-LinOSS false positive.**
   D-LinOSS once classified classical random-telegraph noise as a multi-mode
   quantum signal. The lesson — *the model reads spectral morphology, not
   quantum structure* — is the same wall the sister OAT program hit
   (entanglement is not identifiable from PTM anisotropy alone; resolved by
   `V_Q` over Haar-random settings). Written as a standing rule: **single-setting
   observables never certify quantum structure; measurement diversity does.**

That rule is the thesis of this repository. It was learned classically on
TPUs, forgotten, rediscovered the hard way when IBM-2 and IBM-3 broke this
program's own witnesses, and finally executed as IBM-4's 20-setting fidelity
witness. **The convergence of two independent programs on the same epistemic
wall is the strongest methodological claim here.**

### The inversion that connects the two halves

The synthetic campaign characterized finite-clock record overlap as a
**limitation**: local clock records are provably non-orthogonal (overlap
≈ 0.94 on failed windows, Helstrom-style ceiling ≈ 0.60), so relational time
is a *path-level*, not pointwise, observable. The quantity it bounded is

```
ρ_C[t,t'] = (1/d)·cos((t − t')·π/d)
```

which is **precisely the off-diagonal the hardware witness measures**. What
was a ceiling on classical recoverability is the signal on a QPU. That
inversion — the same number, limitation on one substrate and observable on the
other — is the conceptual through-line of the paper.

### A statement worth making: what IBM-9 says about quantum state-space models

This is an interpretation of measured results, flagged as such, and it is the
direction the program points rather than a claim it certifies.

A classical state-space model with an uncertain oscillation rate represents
that uncertainty as a **density** `p(ω)`, and predicts `∫ p(ω) cos(ωt) dω`.
IBM-9's Z-arm is exactly that object, and it behaved exactly that way: the
measured marginal tracked the closed-form two-rate mixture to a maximum
residual of 0.089, and post-selection recovered the two component rates at
0.981 and 1.964 (R² 0.994).

**The X-arm measured something no density `p(ω)` can produce.** Conditioning
on the which-rate qubit in the conjugate basis shifted the dynamics by 0.2411
where *every* mixture over rates predicts identically zero — 2.32× the 3σ bar,
with the shape tracking prediction across all eight clock readings.

The implication for this model class is concrete: **the quantum generalization
of a damped linear oscillatory state-space model is not a prior over `ω`.** It
is a state over *amplitudes* on `ω`, in which rates superpose rather than mix —
and the two are experimentally distinguishable on present-day hardware, by a
two-setting measurement on five qubits. A "quantum D-LinOSS" is therefore a
well-posed object with an operational signature, not a metaphor: its Λ carries
amplitudes, its mixture limit is the classical model, and the gap between them
is measurable at 0.24 on `ibm_marrakesh`.

### The pipeline, stated as a method

The generalizable claim is about the **division of labour**:

> Use a physics-matched classical model on large-scale accelerators as a
> *hypothesis-and-adversary generator*, and use quantum hardware as the
> *arbiter* — because the classical model's failures are structured enough to
> name the quantity the QPU should measure.

Each of this program's four hardware design parameters came out of a TPU-stage
failure rather than a QPU-stage intuition: **the independent variable**
(decoherence, from A10's entropy requirement), **the functional form** (record
overlap, from the entanglement-damped loss), **the certification standard**
(measurement diversity, from the RTN false positive), and **the substrate
itself** (a QPU at all, from the CHRONOS one-hour-offset control). The QPU
runs were cheap — 71 jobs, seconds of QPU each, on a free trial. The expensive,
month-scale work that made them worth submitting was classical, and it was the
TRC grant that made it possible.

Full account: `docs/AQ_PAGE_WOOTTERS_IBM_4_RESULTS_2026-08-07.md` ("Where the
method came from") and the sister repository's `DISCOVERY_NARRATIVE.md`.

**Where this connects to current work.** Two recent results make quantitative
predictions this apparatus is positioned to test, and both note the
small-processor test as an open gap: a December 2025 relational-emergent-time
framework predicts local coherence decaying as `C(E) = C₀e^{−kE}` with
clock–system entanglement `E` (arXiv:2512.15789), and a February 2026 extended
two-qubit Page–Wootters model predicts a monotonic *informational arrow of
time* — von Neumann entropy of the conditional system state increasing across
successive clock readings once an inaccessible auxiliary is traced out
(*Phys. Lett. A*, S0375960126001325). A follow-up run designed against both is
specified in `docs/AQ_PAGE_WOOTTERS_IBM_1_RUN_SPEC.md`.

---

## The research path

The program produced **three disciplined nulls on classical substrates, then
ten hardware runs**, in that order. The nulls are load-bearing: each redirected
the question onto a better substrate until it became well-posed. The two
hardware failures (IBM-6, IBM-8) are load-bearing for the same reason.

**Where the first positive result landed.** On IBM Quantum Heron processors,
the 4-arm protocol above measured the clock-marginal coherence witness of
`|Ψ⟩ = (1/√d) Σ_t |t⟩_C ⊗ U^t|0⟩_S`:

1. Conditional evolution `⟨Z_S|t⟩ = cos(2πt/d)` recovered with R² > 0.99 —
   and **reproduced exactly by a classical-clock control**, demonstrating on
   hardware that conditional evolution alone witnesses nothing quantum.
2. The clock-marginal coherence witness (inverse-QFT readout, TVD from
   uniform) separates the coherent history state from the classical mixture
   by 5–10× at d = 4, 8 — replicated on **two devices** (`ibm_marrakesh`,
   `ibm_fez`) and in a same-day temporal replicate.
3. The witness **grows with clock dimension** (measured ≈0.005 → 0.16–0.21 →
   0.33–0.42 for d = 2, 4, 8 against exact predictions 0, 0.177, 0.497), and
   **vanishes structurally at d = 2** (the history state is then a Bell pair
   with maximally-mixed clock marginal) — an internal null with the same
   apparatus, protocol, and analysis.

The off-diagonals being measured, `ρ_C[t,t'] = (1/d)cos((t−t')π/d)`, are
exactly the finite-clock record overlaps that the synthetic branch of this
program characterized as a *limitation* (locally indistinguishable clock
records). On hardware, that same non-orthogonality is the *signal*. That
inversion is the conceptual through-line of the paper.

**Claim boundary (locked).** This is a set of hardware measurements on
engineered 2–5 qubit states. It is **not** a claim that time is emergent, a
test of quantum gravity or the Wheeler–DeWitt equation, or a realized
Page–Wootters universe. No teleportation/advantage/supremacy claims.

Two boundaries specific to the later runs, since they invite the most
over-reading. **IBM-7 and IBM-9 are not gravitational time dilation.** There is
no metric, no `G`, no `c`; the rate ratios are programmed, dimensionless
circuit parameters. Realistic gravitational dilation between two terrestrial
clocks is of order `10⁻¹⁰` — eight orders of magnitude below this hardware's
floor. What IBM-9 measures is the *interference mechanism* that quantum time
dilation proposals invoke, in a system where the ratio is dialed to 2:1 by
construction. **And IBM-5's stationarity is certified only up to a global
phase** — see limitation 1 below, where two attempts to close it are recorded
as failures.

---

## The arc (what was tried, in order, and what each step established)

### Part I — CHRONOS: cross-datacenter timing telemetry (June 2026, TRC TPUs) → null

Thesis-origin experiments: two TPU hosts (`us-east1-d`, `europe-west4-a`)
each emitting a 128 Hz "now" stream (fixed-probe latency with wall-clock
metadata), asking whether independent hosts share learnable temporal
structure — external carriers (Schumann band), infrastructure clocks, or
relational clocks, under preregistered gates with shuffled/severed/wrong-time
controls.

- `CHRONOS-0/0b`: sequencing artifact found and fixed; active effect only
  borderline (MW p≈0.066). `CHRONOS-SCHUMANN-0a/0b`: a striking first result
  (+0.50 separation, p=0.001) that **failed preregistered replication** —
  reported as such, not promoted.
- `AQ-DLINOSS-CHRONO-0`: learned temporal-geometry test; clean null (true
  heldout score below the strongest null control).
- `CHRONOS-MARGINAL-DRIFT-1`: the killer control — US/EU feature correlation
  (r≈0.57) **survives a one-hour offset** (r≈0.50): structural hardware
  similarity, not shared time. `CHRONO-MERA-STRAIN-0`: no synchronized
  entropy-spike events.
- `CHRONOS-REAL-ENTROPIC-CLOCK-0` (2026-08-03): the strongest-available
  mechanism (see Part II) applied back to the real telemetry — global path
  recoverable (rank 1 on all three pairs) but window-level prediction fails
  *harder* than any synthetic noise level, and the real +1 h stream is the
  best-scoring null. **The telemetry line is closed, not merely stalled.**

Verdict, stated plainly: classical datacenter telemetry was the wrong
substrate for the question — and the controls proved it rather than assumed it.
Real data: `data/telemetry/` (the actual US/EU q-streams). Docs:
`docs/history/CHRONOS_*.md`, analysis in `telemetry/`.

### Part II — Synthetic Page–Wootters ladder (June 2026, TRC TPUs) → one promoted mechanism, sharp bounds

Moving the clock *inside* the modeled state: `|Ψ⟩ = Σ_t |t⟩_C |ψ(t)⟩_S`
histories with a genuine complex-diagonal D-LinOSS recurrence, frozen-operator
scoring, and calibration-only selection. Roughly twenty runs
(`docs/history/AQ_PAGE_WOOTTERS_DLINOSS_0_RESULTS_2026-06-15.md` is the
ladder log). Key findings:

- **Under-identifiability discovery:** in a projected-harmonic generator, the
  internal clock is too degenerate under noise for *any* matcher/metric/
  embedding to recover the correspondence — diagnosed via an
  observability-first decomposition, not endless tuning.
- **Entropy is required:** recovery only became possible after the generator
  produced irreversible, entropy-bearing histories (causal events, bath
  memory, entropy/action integrals — arm `A10`). Independently convergent
  with the entropic-time construction later published for cold atoms
  (arXiv:2509.07745, τ ∝ ∫dS).
- **Physics-damped state spaces win:** a stationary recurrence failed;
  an **event-damped D-LinOSS** (damping driven by entropy/event observables —
  the original grant thesis, "a state-space model damped by physical
  constraints") closed the ridge gap and passed all mechanism gates across
  ten seeds through noise 0.03.
- **Finite-clock bounds:** local clock records are provably non-orthogonal
  (record overlap ≈0.94 on failed windows; Helstrom-style ceiling ≈0.60);
  the *global monotone path* remains perfectly recoverable (rank 1). Promoted
  claim: relational time is a **path-level**, not pointwise, observable in
  these systems.

Programs: `synthetic/`. Compact results: `results/synthetic/`.

### Part III — BEC entropic bridge (2026-08-03) → null, pre-registered stop

A two-mode Josephson BEC generator (inspired by arXiv:2509.07745's
bright/dark-sector construction) tested whether an entropy-derived τ is
recoverable from bright-sector observables across independent noise
realizations. **Gate 0 failed 0/5 regimes** with clean controls (shuffled and
cross-regime nulls fail hard everywhere, so the harness is sound); per the
pre-registered criterion, the two-world bridge was not built. Reported as a
statement about this mean-field proxy and feature set — not about the
published cold-atom result. Docs: `docs/history/*BEC_ENTROPIC_BRIDGE*`.

### Part IV — AQ-PAGE-WOOTTERS-IBM-0: hardware (2026-08-03) → replicated positive result

Full spec: `docs/AQ_PAGE_WOOTTERS_IBM_0_RUN_SPEC_2026-08-03.md`.
Full results incl. all caveats: `docs/AQ_PAGE_WOOTTERS_IBM_0_RESULTS_2026-08-03.md`.

| run | backend | d=2 null | witness d=4 / d=8 | classical arm | separation d=8 | cond R² |
|---|---|---|---|---|---|---|
| primary | ibm_marrakesh | 0.007 ✓ | 0.196 / 0.406 | 0.003–0.023 | **0.383** | 0.995–0.998 |
| cross-device | ibm_fez | 0.005 ✓ | 0.155 / 0.331 | 0.001–0.039 | **0.309** | 0.991–0.997 |
| temporal replicate | ibm_marrakesh | 0.005 ✓ | 0.210 / 0.423 | 0.007–0.045 | **0.377** | 0.998–0.999 |

Pre-registration filed before each submission; raw counts, job IDs, and
backend calibration snapshots archived (`results/hardware/*/`); the entire
analysis reproduces from counts with no IBM dependency.

**Honest ledger for this result (all on record in the results doc):**

1. **Pre-registered Gate 3 failed on both replications.** The classical arm
   was preregistered to sit within 3× the shot-noise floor; it breached that
   once per replication (fez d=4: 0.039; marrakesh-B d=8: 0.045). The gate
   was not relaxed; both replications report `all_gates_pass=False` as
   registered.
2. **Post-hoc readout mitigation does NOT rescue it** (0.039→0.031,
   0.045→0.044) — so the first diagnosis (readout asymmetry) was wrong.
   Revised diagnosis: input-dependent coherent error in the inverse-QFT makes
   the 1/d-averaged classical mixture non-uniform at the 0.03–0.05 level.
   Correct future design: pre-register the *separation* C−D against the
   in-run classical baseline, not D against an idealized uniform floor.
3. **Layout-integrity disclosure (verified):** the submitter computed but
   never passed `initial_layout` to the transpiler (bug found in code
   review). `hardware/pw_ibm_verify_layout.py` retrieved the actual
   transpiled circuits from all 36 archived jobs and confirmed every run
   executed on physical qubits 0-3 of its backend
   (`results/hardware/*/pw_ibm_actual_layouts.json` is the authoritative
   record). The "disjoint layout" run is therefore a *temporal* replicate;
   the evidence is honestly: one cross-device replication + one temporal
   replicate. True on-device depths were also recovered (d=8 witness:
   143-158, 33-36 two-qubit ops -- ~2.5x the basis-only estimate), which
   strengthens the noise-robustness statement since the separation survived
   at those depths.
4. None of the above touches the separation (5–10× everywhere), the
   dimensional scaling, the d=2 structural null, or the classical
   reproducibility of conditional evolution — the four findings that
   constitute the result.

### Part V — AQ-PAGE-WOOTTERS-IBM-1…10: the adversarial and mechanism runs (2026-08-07/09)

Each run has a pre-registration filed before submission and a results document
carrying its own honest ledger. Ten runs, 36 jobs, all on `ibm_marrakesh`.

| run | question | outcome |
|---|---|---|
| **IBM-1** | does the witness survive decoherence? | decoherence threshold measured; witness degrades before conditional evolution does |
| **IBM-2** | can a zero-entanglement product state fake the local witness? | **yes** — scores 4.2×/1.9× *higher*. Local witness certifies coherence, not structure |
| **IBM-3** | can a separable state fake the joint witness? | **yes** — 1.7× higher; two-line theorem shows *no* single-setting observable can certify entanglement |
| **IBM-4** | can anything certify it? | **yes** — multi-setting fidelity witness, F = 0.9419/0.8829 vs λ_max = 0.5 |
| **IBM-5** | is the global state stationary? | yes under `Ŝ ⊗ U` and nothing else, 44σ–167σ (1 gate failed at d=8, reported) |
| **IBM-6** | is the eigenvalue exactly +1? | **FAILED** — arms not depth-matched; comparison confounded |
| **IBM-7** | what if the rates are detuned? | commensurability condition for exact cycle closure of a *finite cyclic* clock; closes only at integer α (1 gate failed — the gate was wrong, the data was right) |
| **IBM-8** | retry IBM-6, depth-matched | **FAILED** — d=8: 0/4, d=4: 2/4. Limitation published unclosed; recommendation is to stop |
| **IBM-9** | superpose the *rate* of time | **3/3** — interference 0.2411 vs 3σ bar 0.1039; classical rate mixture excluded |
| **IBM-10** | all three properties on ONE state | **4/4** — F 0.9014, echo 0.8630 at 42–143σ, R² 0.9942; conjunction certified |

The sequence IBM-2 → IBM-3 → IBM-4 is the methodological core: each
adversarial run broke the previous run's witness with a state the program
constructed against itself, until IBM-4 reached an observable that provably
cannot be mimicked. The standing rule extracted from it — *derive what class
of states can mimic a witness before designing the run around it* — was
learned three times before it was written down.

---

## Repository layout

```
hardware/           16 scripts: the IBM-0 four-arm protocol (dry run against
                    Aer ideal+noisy, submitter), the nine follow-up runs
                    pw_ibm{1..9}_*.py, plus shared infrastructure —
                    provenance capture, post-hoc readout mitigation,
                    layout verification
results/hardware/   per-run: prereg (filed BEFORE submission), raw counts,
                    analysis, provenance incl. backend calibration snapshot,
                    mitigation; plus the Aer dry-run predictions
synthetic/          the promoted-mechanism chain: PW core, A10 causal-memory
                    generator, path observability, event-damped D-LinOSS
                    confirm, finite-clock bound diagnostics, BEC bridge Gate 0
results/synthetic/  compact JSON results for the runs above
telemetry/          CHRONOS collector + the 2026-08-03 real-data reanalysis
data/telemetry/     the actual US/EU TPU q-streams (real data, 128 Hz, ~256 s)
results/telemetry/  real-data reanalysis outputs
docs/               IBM run spec + results (the paper's evidentiary core)
docs/history/       the full research trail: CHRONOS specs/results, the
                    synthetic ladder log, BEC bridge spec/results
```

Note: scripts retain the relative paths of the working research repo they ran
in; they are provenance artifacts first, rerunnable second (adjust paths or
run from a matching layout to reproduce).

## Reproducing

```bash
pip install qiskit qiskit-aer qiskit-ibm-runtime numpy scipy jax

# Verify the design and regenerate predictions locally (no account needed):
python hardware/pw_ibm_dryrun.py

# Smoke-test the full submit/analyze pipeline against Aer (zero QPU).
# Every run supports --dry; each one asserts its own exact predictions from
# statevector BEFORE any backend contact, which is how three real design
# errors were caught without spending a shot:
python hardware/pw_ibm_submit.py --dry          # IBM-0, four-arm protocol
python hardware/pw_ibm4_fidelity.py --dry       # entanglement certification
python hardware/pw_ibm9_superposed_rate.py --dry  # rate superposition

# Hardware resubmission (IBM account; token via env var, never hardcoded):
export QISKIT_IBM_TOKEN=...
python hardware/pw_ibm_submit.py --backend ibm_marrakesh

# Capture server-side provenance + backend calibration for any completed run:
python hardware/pw_ibm_provenance.py \
    --results results/hardware/ibm9/ibm9_results.json \
    --out /tmp/ibm9_provenance.json
```

All hardware analyses reproduce from the archived raw counts in
`results/hardware/*/pw_ibm_counts_nclock*.json` without any IBM access.

## Provenance

- Backends: `ibm_marrakesh`, `ibm_fez` (156-qubit Heron r2), IBM Open Plan
  (trial instance). **72 jobs total** — 36 for IBM-0 across both devices, 36
  for IBM-1…10 on `ibm_marrakesh` — a few seconds of QPU each; all job IDs and
  server-side timestamps in `results/hardware/*/*provenance.json`
  (authoritative for chronology), alongside per-run backend calibration
  snapshots for the physical qubits actually used.
- Simulation stages (CHRONOS, synthetic ladder) ran on Google TPU Research
  Cloud (TRC) `v6e` spot instances during the grant window 2026-04-21 →
  2026-06-21 (initial one-month grant extended a further month on the
  time-emergence thesis). The IBM hardware stage used no TRC resources.
- The views expressed are those of the author and do not reflect the official
  policy or position of IBM, the IBM Quantum team, or Google.

## Acknowledgments

**Google TPU Research Cloud (TRC)**, whose `v6e` grant (2026-04-21 →
2026-06-21, one month extended by a second on the time-emergence thesis)
funded the entire simulation phase — which is to say, it funded the
hypothesis, the observables, the adversarial controls, and the certification
standard. Every design parameter of the quantum program came out of that
window; see *Where the method came from* above. The QPU stage used no TRC
resources and would not have been worth submitting without it.

**IBM Quantum** Open Plan for hardware access (trial instance).

The entropic-time framing of Part III follows arXiv:2509.07745; the
quantum-time-dilation framing of IBM-9 follows Smith & Ahmadi
(arXiv:1904.12390); the Page–Wootters protocol follows Page & Wootters (1983)
and the photonic illustration of Moreva *et al.* (PRA 89, 052122 (2014)), with
the classical-control arms, the adversarial specificity controls, and the
multi-setting certification added here.
