# AQ-PAGE-WOOTTERS-IBM-13 — Two Clocks, Each With Its Own System

**Executed 2026-08-18 on `ibm_marrakesh`.** 1 job `da1ui86g52gs73cm4li0`,
290 circuits, 6 qubits, 2 000 shots each, 580 000 shots archived.
**All 4 evaluable gates pass.**

Two genuine `d = 4` clocks, each driving its own system, with one parameter `ν`
coupling the **clocks**. The question: can two clocks that are each
demonstrably good Page–Wootters clocks also read each other's systems, and what
does that cost?

## Results

```
 nu     F(A:Sa)  F(B:Sb)  both?   V(Sa|B)  mimic V  Gate5 TVD  (< 0.061)
 0.00   0.9066   0.9087   True    0.0536   0.1798   0.0140   PASS
 0.25   0.8195   0.8236   True    0.2653   0.2461   0.0265   PASS
 0.50   0.6454   0.6661   True    0.5381   0.5520   0.0158   PASS
 0.65   0.5215   0.5287   True    0.7089   0.7315   0.0321   PASS
 0.80   0.3813   0.4038   False   0.8104   0.8596   0.0489   PASS
```

**Both pairs stay certified through `ν = 0.65` and fail at `ν = 0.80`** against
the separable bound `λ_max = 0.5`. The measured crossover sits **exactly where
the ideal prediction put it** — between `0.65` and `0.80` — which was not
guaranteed, since every fidelity is attenuated and the `ν = 0.65` point clears
by only `0.0215`.

At `ν = 0.65` the foreign clock reads the other's system at `V = 0.709` while
*both* pairs remain certified history states. **Two good clocks, each still
certified, partly reading each other.**

Attenuation is flat across the sweep at **0.886–0.907** (mean ≈ 0.894),
consistent with IBM-11's measured 0.891.

## Honest ledger

**Gate 1 failed on the first analysis pass, and the fault was the estimator,
not the hardware.** It returned `V(Sₐ|B) = 2.9241` and a mimic value of
`9.8040` at `ν = 0` — impossible, since `V` is the amplitude of an expectation
value and cannot exceed 1. As the fitted rate goes to zero the sine basis
column vanishes, the design matrix goes rank deficient, and least squares puts
an unbounded coefficient on it while keeping the residual small. Harmless where
there is signal; catastrophic at the `ν = 0` structural null, where the true
amplitude is exactly 0. Fixed by rejecting rates whose sine column carries too
little norm to be identifiable from `d` samples, and enforcing `|V| ≤ 1`.
**No re-run was needed** — the archived counts were re-analysed at zero QPU
cost.

**`V` is positively biased at the null.** When the true amplitude is zero,
least squares — or any magnitude estimator — returns a positive number. The
values `0.054` (history arm) and `0.180` (mimic) at `ν = 0` are therefore
**upper bounds on residual bias, not measurements of signal**. The same
pathology appeared with concurrence in IBM-12.

> Near the structural null the fitted amplitudes are positively biased by
> construction; the reported values at `ν = 0` are not interpretable as
> residual foreign-clock signal.

**Gate 5 is a negative control, and it is the load-bearing caveat:**

> Gate 5 passes at every `ν`. The foreign-clock amplitude `V(S_A|B)` rises with
> coupling but is fully reproduced by a separable mimic (TVD < 0.05). It
> therefore certifies nothing on its own. All non-classical claims rest
> exclusively on the multi-setting fidelity witnesses `F(A:S_A)` and
> `F(B:S_B)`.

The mimic was constructed from the ideal prediction and locked before
submission, never fitted to results. This is the third instance of IBM-3's
theorem in the programme, and the paragraph above prevents the exact overclaim
that sank IBM-2.

**The mimic is ~1 two-qubit gate shallower than the history arm at some `ν`**
(CX pairs are the identity only in even numbers, and the tomography circuits
themselves vary 8–9 by setting). A cleaner mimic makes the two distributions
differ *more*, inflating TVD and making Gate 5 harder to pass — so passing is
conservative, not flattered.

**No noise-model comparison is claimed for this job.** `FakeMarrakesh` is a
stored snapshot, not the live in-process calibration reference IBM-11 and
IBM-12 used, and a stored model cannot be treated as a fair head-to-head. The
accurate statement is:

> Attenuation was flat at 0.886–0.907, consistent with the previous two runs on
> the same device family. No claim is made that hardware outperformed the noise
> model on this job.

**The circuits did not all run on the same physical qubits, and this bounds
what the `ν = 0.65` point supports.** The job used **20 distinct physical
qubits for a 6-qubit circuit** — the transpiler chose layouts per circuit.
Recovered from the job's own payload:

```
 nu=0.25 tomo : 3 distinct, dominant [10,11,12,13,14,15] x36 / 54
 nu=0.50 tomo : 3 distinct, dominant [10,11,12,13,14,15] x37 / 54
 nu=0.65 tomo : 3 distinct, dominant [10,11,12,13,14,15] x40 / 54
 nu=0.80 tomo : 3 distinct, dominant [10,11,12,13,14,15] x41 / 54
 nu=0.00 tomo : 2 distinct, dominant [53,54,109,139,154,155] x48 / 54
 mimic (all)  : 1 distinct, [1,19,53,54,139,152]
```

All four `ν > 0` settings share the **same dominant layout**, so the crossover
comparison is anchored on the same qubits and is not a gross artifact. But
purity is only 67–76% and **drifts with `ν` (36 → 41 of 54)**, so the admixture
of differently-calibrated qubits changes across the sweep.

> **The crossover bracket is robust; the status of `ν = 0.65` is not.** `F`
> falls from `0.5215` to `0.3813` between the last certified setting and the
> first failing one — a gap of `0.14`, far above any plausible layout effect.
> But `ν = 0.65` clears its bound by only `0.0215`, which is the same order as
> the systematic a drifting layout admixture can produce. That single point
> should be treated as unresolved until a replication pins `initial_layout`.

Measured attenuation is flat at 0.886–0.907 with no monotonic trend tracking
the purity drift, which argues the effect is small — but it is not a
substitute for pinning the layout.

**The mimic ran on a different layout entirely** (`[1,19,53,54,139,152]` versus
the history arm's `[10..15]`), so Gate 5's two arms differ in qubit quality as
well as in the residual depth mismatch. Both push the measured TVD **up**, so
Gate 5 passing remains conservative — but neither the depth matching nor the
seven conditions governing that gate anticipated a layout mismatch, and a
replication should pin the layout for both arms.

**Gate 2 is not evaluated here.** `V(Sₐ|A)` is flat at 1.000 by construction
and is a calibration channel, not a result.

**Two design errors were caught before submission** by the dry run: a broken
depth match (a fixed pad left the mimic shallower than the history arm at every
`ν > 0`, because `CRY(0)` is the identity and `ν = 0` transpiles to 4–5
two-qubit gates against 8–9 elsewhere), and a false alarm of my own about
dropped gates, settled by running the transpiled circuits noiselessly and
recovering the exact preflight values to within 0.005.

## Second job: layout pinned — the fidelity result reproduces, Gate 5 fails

**`da214p2ein7c73be0kvg`, 2026-08-18, 290 circuits, 580 000 shots, 2m36s.**
Re-run with `initial_layout` pinned per block, to settle the qubit-drift
caveat above. The submitting machine crashed before the results were saved;
they were recovered from the job with `--recover` at zero QPU cost.

**The layout fix worked.** The job touched **6 physical qubits**
(`[52, 53, 54, 55, 59, 75]`) against 20 in the first, and the two arms are now
depth-symmetric — both blocks at 9 two-qubit gates on the same chain, with
block B on the register-swapped image of block A's layout so its measured trio
sits on exactly the qubits block A's did.

```
 nu     F(A:Sa)  F(B:Sb)  both?   V(Sa|B)  mimic V  Gate5 TVD  (< 0.061)
 0.00   0.8469   0.8614   True    0.1220   0.0159   0.0264   PASS
 0.25   0.8095   0.8106   True    0.2543   0.2900   0.0258   PASS
 0.50   0.6302   0.6356   True    0.5001   0.5769   0.0337   PASS
 0.65   0.5214   0.5136   True    0.6459   0.7428   0.0371   PASS
 0.80   0.3813   0.3874   False   0.7939   0.8810   0.0612   FAIL
```

**The physics result reproduces on a clean layout.** Both pairs certified
through `ν = 0.65`, failing at `0.80` — the same window and the same crossover
as the first job and as the derivation. `F(A:Sₐ)` and `F(B:S_b)` now agree to
within 0.015 at every setting, where before the two arms were not guaranteed
comparable. **This is what the re-run was for, and it closes the qubit-drift
caveat on the crossover.**

> The `ν = 0.65` point still clears its bound by only `0.0214`. Pinning removes
> the *layout* systematic; it does not make a thin margin thick. That point
> remains the weakest link in the claim.

**Gate 5 FAILED at `ν = 0.80`: TVD `0.0612` against the pre-registered
threshold of `0.061`.**

> Per the pre-registration: *"If it fails, the run remains valid and the
> foreign-clock claim is withdrawn — the fidelity witnesses stand
> independently of this arm."*
>
> **The foreign-clock claim is therefore withdrawn for this job.** Nothing is
> asserted here about `V(Sₐ|B)` beyond its being measured. The certification
> results above do not depend on it.

The margin is `0.0002`, and it would be easy to call that a tie. It is not
being called a tie. The threshold was fixed before submission precisely so that
this decision could not be made after seeing the number.

**What went wrong, stated as diagnosis rather than defence.** Pinning bought
layout homogeneity at a cost in fidelity: mean `F` fell from `0.655` to
`0.639`, because one fixed chain cannot match what a per-circuit transpiler
finds by roaming. Mean Gate 5 TVD rose from `0.0275` to `0.0368`. The mimic
carries 8 two-qubit gates against the tomography arm's 8–9, and on a noisier
chain that residual one-gate parity gap costs more — the mimic is
systematically *less* attenuated, and the gap between `V` mimic and `V` history
roughly doubled.

Two fixes were tried and rejected. Padding to an odd count is impossible, since
CX pairs are the identity only in even numbers. Freezing the preparation with a
barrier does make every tomography circuit identical at 20 two-qubit gates —
but 20 is above Paper 1's 18-CX failure bound, which trades a small systematic
for a large one.

**The remaining fix is Gate 6, and it is not applied here.** The
pre-registration says all margins should be evaluated as excess over a
noise-matched Aer reference; `analyze()` compares raw distributions instead. A
matched reference would absorb the depth systematic. Implementing it now, after
seeing that the gate failed by 0.0002, would be changing the statistic to
rescue the result — the precise move this programme's discipline exists to
prevent. **It belongs in the next run's pre-registration, not in a re-analysis
of this one.**

## Third job: the crossover bracketed, and `ν = 0.65` confirmed a third time

**`da2eb861vhnc73fiiqc0`, 2026-08-18, 174 circuits, 348 000 shots, 1m35s.**
A focused three-point sweep at `ν ∈ {0.65, 0.70, 0.75}`, layout pinned, on a
third physical chain `[146, 147, 148, 149, 150, 151]`.

```
 nu     F(A:Sa)  F(B:Sb)  both?
 0.65   0.5463   0.5365   True
 0.70   0.4929   0.4861   False
 0.75   0.4425   0.4502   False
```

**The crossover narrows from `[0.65, 0.80]` to `[0.65, 0.70]`** — a factor of
three, and the tightest localisation the programme has.

**`ν = 0.65` now has three independent measurements on three different physical
chains:**

| job | chain | `F(A:Sₐ)` | margin over `λ_max` |
|---|---|---|---|
| 1 | 20 qubits, drifting | 0.5215 | +0.0215 |
| 2 | pinned `[52…75]` | 0.5214 | +0.0214 |
| 3 | pinned `[146…151]` | **0.5463** | **+0.0463** |

All three clear the bound. The third clears it by **more than double** the
earlier margin, which says the thin `0.0214` was partly the quality of those
chains rather than a property of the state. The claim that both pairs stay
certified at `ν = 0.65` is correspondingly firmer than it was.

**Gate 1 failed, and it should never have been evaluated.** It requires
`V(Sₐ|B)` to rise by more than `0.2` across the sweep — a test of the *whole*
sweep from `ν = 0`, which is vacuous on a three-point bracket where the span is
only `0.1072` by construction. That is a pre-registration error on my part: the
gate was inapplicable to this run's design and should have been excluded before
submission rather than reported as a failure afterwards. Gates 3, 4 and 5 are
meaningful here and all pass.

**Gate 5 passes at all three settings** (TVD 0.0267–0.0450 against 0.061) using
the *reconstructed* mimic. IBM-14 shows that arm carries a multiplicative bias,
so these passes are weaker evidence than the dephased construction — they are
reported, not leaned on.

## Which job is the result

Neither supersedes the other, and both are archived.

| | first job `da1ui86g52gs73cm4li0` | second job `da214p2ein7c73be0kvg` |
|---|---|---|
| layout | 20 qubits, drifting with `ν` | **6 qubits, pinned, arms symmetric** |
| Gate 5 | **PASS** (TVD 0.014–0.049) | FAIL at `ν = 0.80` (0.0612) |
| both certified | `ν ≤ 0.65` | `ν ≤ 0.65` |
| crossover | 0.65 → 0.80 | 0.65 → 0.80 |
| mean `F` | **0.655** | 0.639 |

The certification window and the crossover **agree across both**, on different
physical qubits and with different layout discipline. That agreement is the
strongest evidence in this run, and it does not depend on Gate 5 in either job.

## What this establishes

> Two Page–Wootters clocks with `d = 4`, each carrying its own evolving system,
> can both remain certified against a separable bound while their clock
> registers are coupled strongly enough for each to partly read the other's
> system — up to a measured crossover between `ν = 0.65` and `ν = 0.80`, where
> certification fails. The foreign-clock reading is separably reproducible at
> every coupling and certifies nothing on its own.

## What it does not establish

The clocks and their evolution are **externally programmed**, as everywhere in
this programme. Two clocks agreeing about a system they were each independently
wired to track is not a shared time in any observer-free sense. The
clock/system splits are imposed rather than derived, and the certification is
device-dependent — limitations 1 and 5, neither closed by this run.

## Provenance

`ibm_marrakesh`, 2026-08-18, 1 job `da1ui86g52gs73cm4li0`, 290 circuits at
2 000 shots. Raw counts in `results_ibm13/raw.json`; every number above
reproduces from them with no IBM access:

```
python hardware/pw_ibm13_two_clock.py --analyze results_ibm13/raw.json
python hardware/pw_ibm13_two_clock.py --fixup results_ibm13/raw.json
python hardware/pw_ibm_provenance.py --results results_ibm13/raw.json --out results_ibm13/ibm13_provenance.json
```

**The first provenance attempt was refused**, correctly: the results writer did
not record a physical layout, and `pw_ibm_provenance.py` declines to write an
empty calibration snapshot rather than archive a hollow record. The writer now
records `layouts` at submission, and `--fixup` recovers the layout for this
already-submitted job by reading it back from the job's own payload — the same
discipline Paper 1 adopted after a layout bug: verified post-hoc from what was
actually run, never assumed from a local re-transpile.
