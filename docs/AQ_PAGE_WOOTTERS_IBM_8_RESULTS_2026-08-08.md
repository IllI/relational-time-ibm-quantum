# AQ-PAGE-WOOTTERS-IBM-8 — The Phase Certification Does Not Close on This Hardware

**Executed 2026-08-08 on `ibm_marrakesh`.** 2 jobs, 28 circuits. **d=4: 2/4
gates. d=8: 0/4 gates.** This is the second consecutive failed attempt to
close IBM-5's phase-blindness limitation, and it is reported as a failure.

**The limitation stands. Two attempts, both unsuccessful. The recommendation
is now to stop trying on this hardware, not to try a third time.**

---

## What was fixed, and what that revealed

IBM-6 failed for what I diagnosed as one cause: arms with unequal two-qubit
cost (29 CX vs 8 at d=8), confounding the cross-arm comparison. IBM-8 fixed
that properly — it sweeps a single angle through a single circuit,
`A(β) = Ŝ ⊗ P(βθ)`, and the dry run **asserts** identical transpiled cost at
every β before touching a backend:

```
d=4: every beta -> depth=33, cx=13   [DEPTH-MATCHED]
d=8: every beta -> depth=54, cx=29   [DEPTH-MATCHED]
```

That confound is genuinely gone. **And the run still failed** — which is the
useful information. IBM-6 had *two* causes and the depth asymmetry was the
lesser one. The dominant cause is simply that **the controlled clock-shift is
too expensive for the signal to survive**, and no amount of matching addresses
that. Depth-matching made the comparison fair; it did not make the circuit
shallow enough to measure.

## Results

| d | β=1 measured Re | exact | attenuation | monotone to β=1? | Im-fit R² | fitted offset c |
|---|---|---|---|---|---|---|
| 4 | 0.7770 | 1.0000 | 0.78 | **yes** | 0.9811 | −0.0480 |
| 8 | 0.5670 | 1.0000 | **0.57** | **no** | **0.7367** | −0.0695 |

**d=8 is a clear failure.** The measured curve is not merely attenuated but
structurally distorted: it is non-monotone approaching β=1 (β=0.5 reads 0.386,
*below* β=0.0 at 0.482, where theory demands a rise from 0.854 to 0.962), the
peak lands at β=1.5 rather than β=1, and the Im fit reaches only R² = 0.74.
With 29 two-qubit gates including a 3-controlled X, 43% of the signal is gone
and what remains does not track the predicted shape. No gate passes.

**d=4 is borderline, not passing.** The curve rises monotonically to a correct
peak at β=1 (gate 1 passes) and the Im fit is good (R² = 0.98), but the shape
misses at β=0 by 0.127 against a 0.10 tolerance, and the fitted coherent-error
offset is −0.0480 against a 3σ bar of 0.0474 — over, if barely.

## The one thing that did work, and why it is weaker than it looks

`gate4_im_zero_at_beta1_d4` **passes**: after subtracting the fitted offset,
Im at β=1 is −0.0155, inside 3σ = 0.0474. The offset-fitting machinery did
what it was designed to do — separate a β-independent systematic from the
β-varying signal — and IBM-6 could not do this at all with a single point.

**But this is a weaker result than the gate suggests, and the weakness is
structural.** The fit attributes *everything β-independent* to circuit error.
A genuine nonzero eigenvalue phase is not guaranteed to be β-dependent, so the
subtraction can absorb exactly the quantity the run was built to detect. The
separation rests on a modelling assumption, not a derivation. **Reporting
"eigenvalue certified real at d=4" on this basis would be overclaiming**, and
the gate passing does not license it.

Note also that `gate3` was conceptually misframed on my part: it demanded the
offset be *small*, when the purpose of the fit is to *measure* the offset.
A nonzero offset is information (there is a −0.048 coherent phase in this
circuit), not a failure of method. But since the offset cannot be cleanly
separated from a real phase, measuring it does not rescue the certification
either way.

## Standing conclusion

**IBM-5's limitation is unclosed after two attempts and should be published as
such.** The honest statement remains: *global stationarity is certified up to
a global phase; the prepared state's eigenvalue is exactly +1 by statevector,
but no hardware measurement in this program establishes it.*

What would be required, and why it is not attempted here:

- **d=8 is out of reach.** A controlled 3-controlled-X cascade is beyond this
  device's coherent depth for this signal. This is not a tuning problem.
- **d=4 might close with error mitigation and higher shot counts**, but the
  offset/phase degeneracy above means even a clean d=4 result would need an
  independent argument that the fitted offset is instrumental — which this
  design does not provide.
- A fundamentally cheaper phase-sensitive construction would be needed.
  Extracting a relative phase requires interference against a reference, which
  requires *some* controlled operation; the controlled clock-shift is the
  expensive part and it is not obviously avoidable.

**Recommendation: stop. Publish the limitation.** Two pre-registered attempts,
both reported, is a stronger record than a third attempt tuned until it
passes.

## Provenance

`ibm_marrakesh`, 2026-08-08, 2 jobs. Job IDs in `ibm8_results.json`.

```
python pw_ibm_provenance.py --results results_ibm8_ibm_marrakesh/ibm8_results.json --out results_ibm8_ibm_marrakesh/ibm8_provenance.json
```

---

## Postscript, 2026-08-09: why this could not have succeeded

Added after the fact. The recommendation above — *stop, publish the limitation*
— was right, but the reason given for it was wrong. It said the controlled
clock-shift is too expensive for the signal to survive. That is true, and it is
not the binding constraint.

**For any cyclic history state the constraint eigenvalue is exactly +1 by
construction**, not as a contingent fact:

```
|Ψ⟩      = (1/√d) Σ_t |t⟩ ⊗ U^t|ψ₀⟩
(Ŝ⊗U)|Ψ⟩ = (1/√d) Σ_t |t+1 mod d⟩ ⊗ U^{t+1}|ψ₀⟩ = |Ψ⟩
```

relabelling `t' = t+1`, where the wraparound term closes because
`U^d|ψ₀⟩ = |ψ₀⟩`. Verified numerically to 12 decimal places for random `U`
satisfying `U^d = I`, random `|ψ₀⟩`, system dimension 2–5, and `d ∈ {3,…,16}`:
the result is `+1.000000000000` in every case. The hypotheses are not vacuous —
with `U^d = −I` (IBM-0…4's `Ry` state) the state is not an eigenvector at all,
with overlap 0.5 at `d = 4` and 0.75 at `d = 8`.

**So there was never a genuine eigenvalue phase to detect.** IBM-6 and IBM-8
were both built to separate a β-independent instrumental offset from a genuine
eigenvalue phase. The genuine phase is identically zero by construction, so
that separation problem is degenerate by definition — which is exactly the
"further trap" noted above, now with its cause identified. Whatever offset a
clean run had measured would have been the circuit's coherent error: useful
device characterization, and no information about the constraint.

**This does not weaken IBM-5 or IBM-10.** Ray-stationarity — that `|Ψ⟩` is
invariant under the correctly paired operation and not under the mismatched
ones — is a real, contingent, measured property, and the controls quantify how
the invariance fails. What is *not* contingent, and therefore not measurable,
is which eigenvalue an exactly-cyclic construction lands on.

**The honest framing for the paper** is therefore stronger than "we tried and
failed": the Wheeler–DeWitt-analogous condition `(H_C + H_S)|Ψ⟩ = 0` is
**assumed by this construction rather than tested by it**. An experiment that
tested it would need a constraint that is not built in by fiat — which means a
system whose Hamiltonian is given rather than compiled, i.e. limitation 6, not
a better Hadamard test.

**Lesson.** The program's standing rule was *derive what class of states can
mimic a witness before designing a run around it*. Its sibling, which these two
runs paid for: **derive whether the quantity is contingent before designing a
run to measure it.** Two well-built runs, one of them with a working
depth-matching assertion, spent on a theorem.
