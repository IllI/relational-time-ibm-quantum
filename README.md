# Measuring the Quantum Signature of Relational Time on Superconducting Hardware

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21878786.svg)](https://doi.org/10.5281/zenodo.21878786)

*The DOI above is the concept DOI — it always resolves to the latest archived
version. Cite this one, not a version-pinned link, so the citation stays
current if the repository is ever re-released.*

**What this is.** An experimental program testing whether *relational time* —
time defined by correlations between a clock and the rest of a system, rather
than by an external parameter — leaves a measurable quantum signature that can
be distinguished from its classical mimic. It runs from three disciplined
nulls on classical substrates, through a simulation campaign on **Google TPU
Research Cloud** hardware that built the hypothesis and the certification
standard, to **thirteen pre-registered runs on IBM Quantum Heron processors** (74
jobs) — eleven positive, two reported as failures.

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
> one job: **F = 0.9014**, bootstrap 95% CI **[0.8913, 0.9113]**, against the
> separable bound ½; **joint echo 0.8630**
> against mismatched controls at 42σ–143σ, and **`⟨X_S|t⟩` amplitude 0.9193**
> at R² = 0.9942. The single-state discipline is enforced by pre-submission
> assertions, not prose — see
> `docs/AQ_PAGE_WOOTTERS_IBM_10_RESULTS_2026-08-09.md`.

> [!NOTE]
> **Companion result — this programme's witness runs backwards, and the sibling
> proves why.** This programme and
> [twisted-spin-ptm](https://github.com/IllI/twisted-spin-ptm) ran
> independently and measure the *same law*: coherence as a product of
> half-angle state overlaps, one factor per informed party — there against
> coupling angle (`T_xx = cos(χt/2)^(N−2)`), here against time
> (`ρ_C = cos(Δt·π/d)`). Exact, not analogical.
>
> The consequence is not neutral. This programme's headline witness reads a
> **marginal**, and for a bipartite pure state the marginal entropy *is* the
> entanglement entropy — so entanglement is exactly what flattens what the
> witness measures. A zero-entanglement product state outscores the maximally
> entangled history state at every `d`, and the exact `d = 4` ratio
> (`0.750 / 0.176777 = 4.24`) **reproduces IBM-2's measured 4.2×**. The
> adversary did not find a loophole; it saturated a quantity that entanglement
> necessarily suppresses.
>
> The sibling supplies what this programme cannot: a *separable* state with
> maximally mixed marginals (`I/4` at `χt = π`, concurrence 0) to pair against
> this programme's maximally entangled `d = 2` null. Independently converged on
> by [arXiv:2512.09100](https://arxiv.org/abs/2512.09100), whose singlet clock
> has uninformative marginals for the same reason:
> [`docs/COMPANION_RESULT.md`](docs/COMPANION_RESULT.md).
>
> **Measured on hardware, 2026-08-17 (IBM-11).** Sweeping a single parameter
> from product state to Bell pair, the witness and CHSH anti-correlate at
> **r = −0.9573**: the witness peaks at 0.4830 where CHSH is **1.8605, below the
> classical bound**, and falls to 0.0100 where CHSH reaches 2.6565. The exact
> trade-off `S² + 16W² = const` survives at 0.891 attenuation with a spread of
> 0.15 against a 1.14 band. 9/9 gates —
> [`docs/AQ_PAGE_WOOTTERS_IBM_11_RESULTS_2026-08-17.md`](docs/AQ_PAGE_WOOTTERS_IBM_11_RESULTS_2026-08-17.md).

Raw counts, pre-registrations, derived results and server-side provenance
(including per-run backend calibration) are archived for **all twelve runs** —
571 circuits of counts across 35 jobs, 73 jobs of provenance in total, zero
records with an empty calibration block. Every analysis reproduces from counts
with no IBM account; the fidelity witnesses are re-derived from raw counts and
bootstrapped in `hardware/pw_ibm_fidelity_bootstrap.py`.

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

Thirteen runs on IBM Heron r2 processors, each pre-registered before submission.
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
| **IBM-11** | witness and CHSH swept together, product → Bell | measures the witness running *backwards*: r = −0.9573 |
| **IBM-12** | clock quality vs synchronisability, three qubits | measures what shared time costs: r = −0.9833, both endpoints exactly zero |

## Conclusion

**Program-level, stated as narrowly as thirteen runs support:**

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
> exact separable bound* `λ_max = ½`, with bootstrap 95% confidence intervals
> whose lower limits clear the bound outright
> (d=4: F = 0.9419, CI [0.9286, 0.9548]; d=8: F = 0.8829, CI [0.8709, 0.8945]), **stationary as a ray**
> under the paired operation `Ŝ ⊗ U` and not under the mismatched controls
> (44σ–167σ), **internally evolving** under the same operator that enforces
> that stationarity (R² = 0.994), subject to a **hardware-measured
> commensurability condition for exact cycle closure of a finite cyclic
> clock**, and **supporting coherent superposition and interference between
> two programmed relational evolution rates** (interference 0.2411 where every
> classical rate mixture predicts zero). **The first three hold jointly on a
> single preparation** (IBM-10: F = 0.9014 with 95% CI [0.8913, 0.9113],
> joint echo 0.8630 at 42σ–143σ,
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
> state, so **no single-configuration observable in IBM-0…IBM-3 — local
> witness, joint witness, conditional evolution, the arrow — certifies
> clock–system entanglement, and none could have.** (The theorem is about
> local product-basis distributions; IBM-4 escapes it by combining
> *incompatible settings*, not by finding a better single distribution.) This
> despite the history state being
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
> values). The arc, measured: local coherence → defeated by a product state →
> joint correlation defeated by a separable state → multi-setting entanglement
> certification:
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
> along two **programmed relational-rate histories** at once (the discrete
> analogue Smith & Ahmadi discuss for proper time; the circuit has no metric). Read `G` in **Z** and the result is
> an ordinary classical mixture: the marginal tracks the closed-form
> `[cos(α₁θt) + cos(α₂θt)]/2` (max residual 0.089) and post-selection recovers
> the two branch rates at **0.981 and 1.964**, both R² 0.994. Read `G` in
> **X** and conditioning on `G = +` shifts the dynamics by **0.2411** where the
> corresponding incoherent mixture of the two programmed rate branches predicts
> exactly zero — **2.32× the 3σ bar**, retaining 91.6% of
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
does not test quantum gravity or the Wheeler–DeWitt equation, and does not
realize a physical Page–Wootters universe. The state is engineered by
externally timed gates, the clock/system split is imposed, and the
certification is device-dependent. Those boundaries are itemized as
limitations 1–7 below and none of them is closed by any run here.

**What it does show**, in one arc:

1. **The signal usually cited is classically reproducible.** Conditional
   evolution and the informational arrow are reproduced by an explicit
   classical clock control to within shot noise (IBM-0, IBM-1).
2. **The natural repair is insufficient, twice, and provably so.** The
   clock-coherence witness is not classically reproducible — it scales with
   clock dimension and has a structural null — but a zero-entanglement product
   state scores *higher* on it (IBM-2), and a separable state scores higher on
   the joint witness built to fix that (IBM-3). A two-line theorem then
   generalizes both: within this local product-basis architecture, no single
   measurement configuration can certify clock–system entanglement.
3. **Certification requires measurement diversity, and then it succeeds.**
   IBM-4's multi-setting fidelity witness exceeds the derived separable bound
   `λ_max = ½` — a bound no separable state can cross, tested against the exact
   adversarial states that broke its predecessors.
4. **The other half of the mechanism is measured.** The global state is
   stationary under the paired clock-shift-plus-evolution and under nothing
   else, with the operator enforcing stationarity being the same one generating
   the conditional dynamics (IBM-5).
5. **The mechanism is then characterized, not just verified.** Detuning the
   pairing reveals a commensurability condition for exact cycle closure of a
   finite cyclic clock (IBM-7), and superposing the rate itself produces
   interference no classical mixture of rates can produce (IBM-9).
6. **The conjunction holds on one preparation.** IBM-10 measures entanglement,
   ray-stationarity and internal evolution on a single state in a single job —
   which is the Page–Wootters mechanism's actual content, rather than three
   properties of three states.

Every certification limit above was found by this program's **own
pre-registered adversarial controls** rather than left for a referee, and two
of eleven runs are reported as failures (IBM-6, IBM-8) on a limitation
published unclosed.

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
   condition than *being* an eigenstate.

   > **The phase is not an open empirical question about this construction —
   > it is fixed by it.** For *any* cyclic history state, the eigenvalue of
   > `Ŝ ⊗ U` is **exactly +1 identically**:
   >
   > ```
   > (Ŝ⊗U)|Ψ⟩ = (1/√d) Σ_t |t+1 mod d⟩ ⊗ U^{t+1}|ψ₀⟩ = |Ψ⟩
   > ```
   >
   > relabelling `t' = t+1`, where the `t = d−1` term closes because
   > `U^d|ψ₀⟩ = |ψ₀⟩`. Verified numerically to 12 decimals for random `U` with
   > `U^d = I`, random `|ψ₀⟩`, system dimensions 2–5 and `d` from 3 to 16.
   > The hypotheses have teeth: with `U^d = −I` (the `Ry` state of IBM-0…4)
   > the state is **not an eigenvector at all** — overlap 0.5 at `d = 4`,
   > 0.75 at `d = 8`.
   >
   > **Consequence.** The Wheeler–DeWitt-analogous condition is *built into*
   > this construction rather than tested by it, and there is no genuine
   > nonzero eigenvalue phase for an experiment to find. A hardware
   > measurement of that phase would report the **circuit's coherent error** —
   > device characterization, not physics. This is the real reason IBM-8's
   > offset/phase fit was degenerate: it was trying to separate an instrumental
   > offset from a signal the construction guarantees is identically zero.
   >
   > This was derived *after* the two failed runs, not before. Recorded as
   > such — see the lesson below.

   **This limitation was attacked twice before that was understood.** IBM-6
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
   failures**: `docs/AQ_PAGE_WOOTTERS_IBM_8_RESULTS_2026-08-08.md`.

   **The lesson, which cost two runs.** This program's standing rule was
   *derive what class of states can mimic a witness before designing a run
   around it* (learned from IBM-2/3). IBM-6 and IBM-8 exposed its sibling:
   **derive whether the quantity is contingent before designing a run to
   measure it.** Both runs were well-built — IBM-8's depth-matching assertion
   worked exactly as intended — and both were measuring something the
   construction had already fixed. A two-line calculation, available before
   either was written, would have retired the question at zero QPU cost.
2. **The clock/system split is chosen, not derived.** *(A follow-up that would
   narrow this — three clocks encoding only mutual relations, with no
   privileged frame — is proposed in
   `docs/AQ_PAGE_WOOTTERS_IBM_11_RELATIONAL_NETWORK_PROPOSAL.md`. Two
   structural results constraining any such run are derived and executable in
   `theory/verify_clock_structure.py`: rate loop closure is automatic rather
   than contingent, so it cannot serve as a physics gate; and a clock can act
   as a reference frame only if `gcd(rate, d) = 1`, which is about resolution
   rather than the cycle closure IBM-7 measured.)* Nothing in the state
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
under test. The Page–Wootters system qubit evolving under `U = P(2πα/d)` **maps
onto a single complex oscillatory mode at the level of the measured phase
evolution**, with `ω = αθ` and hardware decoherence supplying the `γ`. (An
analogy at the level of the observable, not an identity of physical objects —
the classical recurrence and the quantum phase evolution are different things.)
The model class and the measured quantity are structurally matched, which is
why the model's failures were diagnostic rather than merely disappointing.

### D-LinOSS's negatives carried the information

Three times the informative result was a **failure**, and each one set a
parameter of the hardware program:

1. **Entropy-bearing structure was required for recoverability in the tested
   family.** A projected-harmonic generator proved
   *under-identifiable* — no matcher, metric, or embedding could recover the
   clock correspondence, diagnosed by observability-first decomposition rather
   than tuning. Recovery only became possible once the generator produced
   irreversible, entropy-bearing histories (arm `A10`). This is a statement
   about the synthetic generators tested here, **not** a general claim that
   relational time requires entropy. It independently
   converged with the entropic-time construction later published for cold
   atoms (arXiv:2509.07745, `τ ∝ ∫dS`).
2. **D-LinOSS never beat its baselines — and the *shape* of the losses is the
   information.** Stated plainly because an earlier draft of this README
   overstated it: across the entire synthetic campaign, **every measured
   `D-LinOSS − ridge` value is negative.** The event-damped variant (damping
   driven by entropy/event observables — the original grant thesis, "a
   state-space model damped by physical constraints") narrowed the deficit
   from ≈ −0.40 to ≈ −0.07 across ten seeds through noise 0.03, and the
   pre-registered gate it passed was a *competitiveness tolerance*
   (`D-LinOSS − ridge ≥ −0.05`, met in 75% of cases), **not** a superiority
   test. Separately, the *entanglement-damped* variant lost to a stationary
   model at every tested grid density. Those structured losses exposed the
   wrong functional form and pointed at record overlap as the correct
   independent variable —
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
   `V_Q` over Haar-random settings). Written as a standing rule: **a single local
   product-basis distribution does not certify quantum structure; measurement
   diversity does.** (Narrow by design — a global entangled measurement can
   witness in one configuration; what fails is the local single-setting family
   used here and in the sister program.)

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
runs were cheap — 72 jobs, seconds of QPU each, on a free trial. The expensive,
month-scale work that made them worth submitting was classical, and it was the
TRC grant that made it possible.

Full account: `docs/AQ_PAGE_WOOTTERS_IBM_4_RESULTS_2026-08-07.md` ("Where the
method came from") and the sister repository's `DISCOVERY_NARRATIVE.md`.

---

## Every failure, and what it bought

This program's failures are not disclosed reluctantly at the end. **They are
the mechanism by which it arrived at its results**, and every one of them was
eventually explained and converted into a design parameter, a scope
correction, or a theorem. The table is the honest audit and, we would argue,
the most reusable thing here.

| failure | what it looked like | what it bought |
|---|---|---|
| **CHRONOS-SCHUMANN-0a/0b** | striking first result: +0.50 separation, `p = 0.001` | **failed its own pre-registered replication** → reported, not promoted. The single most important discipline in the program, established before it had anything to lose |
| **CHRONOS-MARGINAL-DRIFT-1** | US/EU correlation `r ≈ 0.57` looked like shared time | correlation **survives a one-hour offset** at `r ≈ 0.50` → structural hardware similarity, not time. Closed the telemetry line *decisively* rather than leaving it stalled |
| **BEC entropic bridge, Gate 0** | 0/5 regimes, clean controls | pre-registered stop, executed. No second attempt tuned until it passed |
| **D-LinOSS under-identifiability** | no matcher/metric/embedding could recover the clock | diagnosed by observability-first decomposition → **entropy is required**; produced arm `A10` and IBM-1's independent variable |
| **D-LinOSS entanglement-damped loss** | lost to a *stationary* model at every grid density | the loss was **structured** → exposed the wrong functional form → record overlap as the right variable → IBM-1's measured power law |
| **D-LinOSS RTN false positive** | classified classical telegraph noise as multi-mode quantum | *the model reads spectral morphology, not quantum structure* → the **measurement-diversity certification standard** IBM-4 executes |
| **IBM-0 Gate 3** | classical arm breached its floor on **both** replications | not relaxed; reported `all_gates_pass=False`. Mitigation did **not** rescue it → first diagnosis (readout) was **wrong** → revised to an input-dependent iQFT coherent error, with a corrected design rule for future runs |
| **IBM-0 layout bug** | `initial_layout` computed but never passed to the transpiler | found in code review, verified against all 36 archived jobs → the "disjoint layout" run was honestly re-scoped to a *temporal* replicate |
| **IBM-1 Gate 0 doc/code mismatch** | doc claimed 16/16; committed code disagreed | **all fixed in code first, original results doc formally withdrawn** — plus a 4× shot-budget overrun and a miscalibrated gate slack caught before hardware |
| **IBM-2** | the headline witness **defeated by a zero-entanglement product state** | the witness certifies clock *coherence*, not structure → `W_joint` built as the repair |
| **IBM-3** | the repair **defeated by a separable state** | a two-line theorem generalizing both → forced the multi-setting design that finally worked |
| **IBM-4 Schmidt assertion** | `λ_max` came out 0.8536, not 0.5 | a reshape-ordering bug caught **before hardware contact** by a theorem-first assertion |
| **IBM-5 Gate 2 (d=8)** | failed as written | reported as registered; revealed a crude worst-case σ *and* that the test's contrast degrades with `d` — a design limit, not a statistics problem |
| **IBM-7 Gate 2** | failed | **the gate was wrong and the data was right** — matched pairing is not maximal at `α = 0.75`, exactly as theory says |
| **IBM-6, then IBM-8** | two pre-registered attempts at the eigenvalue phase, both failed | IBM-8's depth-matching worked *and it still failed* → proved depth was the *lesser* cause → and ultimately a **theorem**: the eigenvalue is `+1` by construction, so there was never a phase to find |
| **IBM-9 feasibility assertions** | `d = 4` blocked; σ understated ~25% | reversed the "smaller `d` is safer" heuristic on principled grounds; both caught at zero shot cost |
| **the stitched claim** | README asserted a conjunction never measured on one state | measured the two states to be **orthogonal** → motivated IBM-10, which closed it |
| **"closed the ridge gap"** | this README claimed the event-damped variant caught up to its ridge baseline | traced to source on 2026-08-10: the gate was a ±0.05 *competitiveness tolerance*, and **every `D-LinOSS − ridge` value in the whole campaign is negative** — the deficit narrowed from ≈ −0.40 to ≈ −0.07, it never closed. Corrected in place |

Three patterns are worth naming because they generalize:

- **A failed replication is worth more than an unreplicated success.** The
  Schumann result would have been the program's most exciting number. Killing
  it set the standard everything after had to meet.
- **A *structured* loss is data; an unstructured one is noise.** D-LinOSS
  losing to a stationary baseline *at every grid density* was informative
  precisely because it was systematic — it named the wrong functional form.
- **A failed pre-registered gate is not a failed experiment.** IBM-7's gate
  encoded an assumption the data corrected. IBM-5's revealed a design limit.
  The gate failing is how you learn the gate was wrong.

## The methodology as a transferable protocol

The physics here is specific. The method is not, and it was assembled to be
cheap: **72 jobs, seconds of QPU each, on a free-tier account.** Nothing below
requires privileged hardware access.

| practice | what it cost | what it caught here |
|---|---|---|
| **Pre-register numeric predictions and a pass criterion before submission** | minutes per run | made every failure *reportable* instead of quietly re-scoped; `all_gates_pass=False` appears in the archive four times |
| **Assert exact statevector predictions in the dry run, before any backend contact** | one `assert` per design | a Schmidt reshape bug, an infeasible `d`, a 25%-wrong σ, a 4× shot overrun — **all at zero shot cost** |
| **Build the adversary yourself, and build it to win** | one extra run each | IBM-2 and IBM-3 broke this program's own headline witnesses before a referee could |
| **Derive what can mimic your witness *before* designing around it** | a calculation | learned three times the hard way; now a standing rule |
| **Derive whether a quantity is *contingent* before measuring it** | a calculation | learned at the cost of IBM-6 and IBM-8; a two-line argument would have retired the question |
| **Archive counts + prereg + server-side provenance per run** | one script | makes every analysis reproducible with no vendor account, and caught two silently-empty calibration captures |
| **Report the failed gate as registered, then give the corrected statistic separately** | discipline only | preserves the pre-registration while still reporting the better number honestly |
| **Bootstrap the witness from archived counts rather than propagating a σ** | minutes, no QPU | the independence estimate was **anti-conservative by ~14%** (σ 0.00444 vs bootstrap 0.00507) — correlations *within* a setting inflate the variance rather than cancel |

The division of labour is the part most transferable to other groups:
**a physics-matched classical model on cheap large-scale compute as the
hypothesis-and-adversary generator, and scarce quantum hardware purely as the
arbiter.** Accelerator time is abundant and QPU time is not, so the expensive
month-scale work — deciding *what* to measure, and constructing the states
that would defeat a naive answer — belongs on the accelerator. The design
parameters that survived to hardware here all came from TPU-stage failures.
Any lab with a simulation cluster and a free-tier quantum account can run this
loop; that is the point of documenting it.

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
eleven hardware runs**, in that order. The nulls are load-bearing: each redirected
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
records). On hardware, that same non-orthogonality is the *signal* — the
inversion described under *Where the method came from* above.

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
- **Physics-damped damping helps, but never enough to win:** a stationary
  recurrence failed outright; an **event-damped D-LinOSS** (damping driven by
  entropy/event observables — the original grant thesis, "a state-space model
  damped by physical constraints") passed the gain, external and path-rank
  gates at 100% across ten seeds through noise 0.03 and narrowed its deficit
  against ridge from ≈ −0.40 to ≈ −0.07. It did **not** overtake ridge; the
  ridge gate was a ±0.05 competitiveness tolerance, met 75% of the time.
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

### Part V — AQ-PAGE-WOOTTERS-IBM-1…12: the adversarial and mechanism runs (2026-08-07/17)

Each run has a pre-registration filed before submission and a results document
carrying its own honest ledger. Twelve runs, 38 jobs, all on `ibm_marrakesh`.

| run | question | outcome |
|---|---|---|
| **IBM-1** | does the witness survive decoherence? | decoherence threshold measured; witness degrades before conditional evolution does |
| **IBM-2** | can a zero-entanglement product state fake the local witness? | **yes** — scores 4.2×/1.9× *higher*. Local witness certifies coherence, not structure |
| **IBM-3** | can a separable state fake the joint witness? | **yes** — 1.7× higher; two-line theorem: no single local product-basis distribution can certify entanglement |
| **IBM-4** | can anything certify it? | **yes** — multi-setting fidelity witness, F = 0.9419/0.8829 vs λ_max = 0.5 |
| **IBM-5** | is the global state stationary? | yes under `Ŝ ⊗ U` and nothing else, 44σ–167σ (1 gate failed at d=8, reported) |
| **IBM-6** | is the eigenvalue exactly +1? | **FAILED** — arms not depth-matched; comparison confounded |
| **IBM-7** | what if the rates are detuned? | commensurability condition for exact cycle closure of a *finite cyclic* clock; closes only at integer α (1 gate failed — the gate was wrong, the data was right) |
| **IBM-8** | retry IBM-6, depth-matched | **FAILED** — d=8: 0/4, d=4: 2/4. Limitation published unclosed; recommendation is to stop |
| **IBM-9** | superpose the *rate* of time | **3/3** — interference 0.2411 vs 3σ bar 0.1039; classical rate mixture excluded |
| **IBM-10** | all three properties on ONE state | **4/4** — F 0.9014, echo 0.8630 at 42–143σ, R² 0.9942; conjunction certified |
| **IBM-11** | is the witness anti-correlated with CHSH? | **9/9** — r = −0.9573; max witness sits *below* the Bell bound at CHSH 1.86 |
| **IBM-12** | what does a shared clock cost? | **6/6** — r = −0.9833; a perfect PW clock has *zero* correlation with any other clock |

The sequence IBM-2 → IBM-3 → IBM-4 is the methodological core: each
adversarial run broke the previous run's witness with a state the program
constructed against itself, until IBM-4 reached an observable that provably
cannot be mimicked. The standing rule extracted from it — *derive what class
of states can mimic a witness before designing the run around it* — was
learned three times before it was written down.

---

## Repository layout

```
hardware/           the IBM-0 four-arm protocol (dry run against Aer
                    ideal+noisy, submitter), the ten follow-up runs
                    pw_ibm{1..10}_*.py, plus shared infrastructure —
                    provenance capture, raw-counts retrieval, fidelity
                    bootstrap, post-hoc readout mitigation, layout
                    verification, backend queue selection
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
theory/             finite-clock structural results, executable
                    (verify_clock_structure.py) -- derived, not measured
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

**Reproducibility status.** All eleven runs reproduce from archived raw counts
with no IBM access — IBM-0 from `pw_ibm_counts_nclock*.json`, IBM-1…10 from
`results/hardware/ibm*/ibm*_counts.json` (518 circuits, 34 jobs).

This was not true until 2026-08-10 and the history is worth recording. IBM-0
archived its counts; **IBM-1…10 did not** — the discipline was established once
and not carried forward. The gap surfaced only when a reviewer asked for
bootstrap confidence intervals on the fidelity witnesses and there was nothing
local to resample. It was recoverable because the job IDs were archived and the
submitting account was still live, so `pw_ibm_fetch_counts.py --all` backfilled
every run at zero QPU cost. Had the trial lapsed first (~2026-09-02) the raw
data would have been gone and ten runs would have remained reproducible only
from derived numbers.

The lesson generalizes past this repository: **an archive is only as good as
its least-archived run, and provenance discipline decays silently.** Nothing
failed, no result changed, and the omission was invisible from the outside for
a week.

```bash
python hardware/pw_ibm_fetch_counts.py --all         # re-retrieve (no QPU cost)
python hardware/pw_ibm_fidelity_bootstrap.py --run ibm10
python hardware/pw_ibm_fidelity_bootstrap.py --run ibm4
```

## Provenance

- Backends: `ibm_marrakesh`, `ibm_fez` (156-qubit Heron r2), IBM Open Plan
  (trial instance). **73 jobs total** — 36 for IBM-0 across both devices, 37
  for IBM-1…11 on `ibm_marrakesh` — a few seconds of QPU each; all job IDs and
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

**Research supported with Cloud TPUs from Google's TPU Research Cloud (TRC).**
The TRC allocation supported the simulation and hypothesis-development phase;
the IBM Quantum hardware experiments used separate IBM Open Plan access.

**IBM Quantum** Open Plan for hardware access (trial instance).

### Computational resources

- **TRC allocation:** `v6e` instances, 2026-04-21 → 2026-06-21 — an initial
  one-month allocation extended by one further month.
- **Workloads:** the CHRONOS cross-datacenter telemetry campaign, the synthetic
  Page–Wootters ladder (~20 runs), the D-LinOSS variants and their
  observability-first diagnostics, the finite-clock record-overlap bounds, and
  the BEC entropic-bridge Gate 0. In short: the hypothesis, the observables,
  the adversarial controls, and the certification standard. Every design
  parameter that survived to hardware came out of this window — see *Where the
  method came from*.
- **Separation of stages:** the QPU stage used no TRC resources; the TRC stage
  used no quantum hardware.

The entropic-time framing of Part III follows arXiv:2509.07745; the
quantum-time-dilation framing of IBM-9 follows Smith & Ahmadi
(arXiv:1904.12390); the Page–Wootters protocol follows Page & Wootters (1983)
and the photonic illustration of Moreva *et al.* (PRA 89, 052122 (2014)), with
the classical-control arms, the adversarial specificity controls, and the
multi-setting certification added here.
