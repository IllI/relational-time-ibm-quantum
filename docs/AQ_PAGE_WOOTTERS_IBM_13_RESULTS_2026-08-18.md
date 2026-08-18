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

**`V` is positively biased at the null and must not be read as signal there.**
At `ν = 0` the exact value is 0, but fitting an amplitude to noise always
returns something positive: `0.054` on the history arm and `0.180` on the
mimic. This is the same class of estimator bias as concurrence in IBM-12, and
the same rule applies — only differences against a matched reference are
interpretable, never the raw value near zero.

**Gate 5 passes at every `ν` (TVD 0.014–0.049 against 0.061), and it is a
negative control.** The separable mimic — constructed from the ideal
prediction and locked before submission, never fitted to results — reproduces
the full eight-outcome single-basis distribution. **Therefore the
foreign-clock amplitude, while rising with `ν`, does not by itself certify
non-classical structure. Certification rests only on the multi-setting
fidelity witnesses.** This is the third instance of IBM-3's theorem in the
programme.

**The mimic is ~1 two-qubit gate shallower than the history arm at some `ν`**
(CX pairs are the identity only in even numbers, and the tomography circuits
themselves vary 8–9 by setting). A cleaner mimic makes the two distributions
differ *more*, inflating TVD and making Gate 5 harder to pass — so passing is
conservative, not flattered.

**Hardware did not beat its noise model this time**, ending a two-run streak.
The dry run against `FakeMarrakesh` predicted 0.927–0.947 attenuation and the
device delivered ≈0.894. That is not the IBM-11/IBM-12 comparison, though:
those used an in-process reference at the live calibration, while
`FakeMarrakesh` is a stored snapshot. It is a weaker statement and is reported
as one.

**Gate 2 is not evaluated here.** `V(Sₐ|A)` is flat at 1.000 by construction
and is a calibration channel, not a result.

**Two design errors were caught before submission** by the dry run: a broken
depth match (a fixed pad left the mimic shallower than the history arm at every
`ν > 0`, because `CRY(0)` is the identity and `ν = 0` transpiles to 4–5
two-qubit gates against 8–9 elsewhere), and a false alarm of my own about
dropped gates, settled by running the transpiled circuits noiselessly and
recovering the exact preflight values to within 0.005.

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
python hardware/pw_ibm_provenance.py --results results_ibm13/raw.json --out results_ibm13/ibm13_provenance.json
```
