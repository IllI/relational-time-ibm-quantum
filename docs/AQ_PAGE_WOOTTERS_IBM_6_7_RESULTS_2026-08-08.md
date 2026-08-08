# AQ-PAGE-WOOTTERS IBM-6 and IBM-7 — One Failed Attempt, One Confirmed Resonance

**Executed 2026-08-08 on `ibm_marrakesh`.** IBM-6: 5/8 gates. IBM-7: 14/15
gates. Reported together because IBM-6 is a **failed attempt to close a known
limitation** and that outcome governs how IBM-5 must be read.

---

# IBM-6 — the phase gap is NOT closed

## What it tried to do

IBM-5 certified `|Ψ⟩` as an *eigenvector* of `Ŝ ⊗ U` but, measuring
`|⟨Ψ|A|Ψ⟩|²`, could not certify the **eigenvalue is +1**. That distinction
matters: Wheeler–DeWitt is `Ĥ|Ψ⟩ = 0`, so a nonzero phase would mean an
eigenstate carrying nonzero "energy," not the constraint. A Hadamard test
returns `Re` and `Im` separately and should have settled it.

## What happened

| d | arm | measured Re | measured Im | exact Re | exact Im |
|---|---|---|---|---|---|
| 4 | joint | +0.7610 | **−0.0930** | +1.0000 | 0.0000 |
| 4 | clock_only | +0.3350 | −0.5255 | +0.5000 | −0.5000 |
| 4 | system_only | +0.4755 | +0.3810 | +0.5000 | +0.5000 |
| 8 | **joint** | **+0.5815** | **−0.0995** | +1.0000 | 0.0000 |
| 8 | clock_only | +0.5555 | −0.1290 | +0.8536 | −0.3536 |
| 8 | **system_only** | **+0.8500** | +0.3135 | +0.8536 | +0.3536 |

**Three gates failed, and the run does not support its intended claim.**

**1. The arms are not depth-matched, which invalidates cross-arm comparison.**
Transpiled two-qubit counts:

| d | joint | clock_only | system_only | wrong_way |
|---|---|---|---|---|
| 4 | 13 CX | 11 CX | **6 CX** | 13 CX |
| 8 | 29 CX | 27 CX | **8 CX** | 29 CX |

At d=8 the joint arm carries **3.6× the two-qubit gates** of `system_only`,
because a controlled clock-shift needs a 3-controlled X while a controlled
phase gate is nearly free. `system_only` lands at 0.8500 against its exact
0.8536 — essentially unattenuated — while `joint` falls from 1.0000 to
0.5815. `gate1_joint_real_positive_d8` fails because `system_only` measures
*higher* than `joint`, and that ordering is **a circuit-depth artifact, not
physics**. IBM-5's echo shared this asymmetry but survived it at d=4, where
the physics separation (1.0 vs 0.5) was large enough to dominate; at d=8,
where the true separation is only 0.146, the artifact wins.

**2. The imaginary part is not zero.** Theory says exactly 0 for the joint
arm. Measured −0.0930 (d=4) and −0.0995 (d=8), against a 1σ shot noise of
0.0158 — roughly **6σ from zero at both sizes**. This is almost certainly
coherent gate error accumulating in the controlled-MCX cascade, but with this
data a systematic circuit phase cannot be distinguished from a genuine
eigenvalue phase. That is precisely the discrimination the run existed to
make, and it could not make it.

**3. Consequently `gate3_phase_near_zero_d8` also fails** (|phase| = 0.169 rad
against a 0.15 bar), and passes at d=4 (0.122) only marginally.

## Verdict

**IBM-5's phase-blindness limitation stands, unclosed.** The prepared state's
eigenvalue is exactly +1 by statevector, but **no hardware measurement in this
program establishes it.** Any future attempt must depth-match the arms — pad
the cheap arms with identity-equivalent controlled operations so every arm
carries the same two-qubit count — and would likely need error mitigation and
d=4 only.

The one gate that passed cleanly at both sizes is `gate4`, and it is worth
keeping: **the echo assigns `clock_only` and `system_only` identical modulus
at every d and cannot separate them even in principle, while the Hadamard
test splits them by the sign of Im** (−0.5255 vs +0.3810 at d=4; −0.1290 vs
+0.3135 at d=8), recovering the *direction* of the mismatch. That capability
is demonstrated even though the eigenvalue certification is not.

---

# IBM-7 — commensurability resonance, confirmed on hardware

## The result

Normalised against the α=1 arm (whose exact value is 1.0, calibrating echo
attenuation in-run):

| α | fitted α | R² | matched (norm) | exact | commensurate? |
|---|---|---|---|---|---|
| 0.5 | 0.506 | 0.9951 | 0.5801 | 0.5625 | no |
| 0.75 | 0.742 | 0.9988 | 0.7367 | 0.7812 | no |
| **1.0** | 0.994 | 0.9995 | **1.0000** | 1.0000 | **yes** |
| 1.5 | 1.493 | 0.9992 | 0.5847 | 0.5625 | no |
| **2.0** | 2.000 | 0.9996 | **0.9804** | 1.0000 | **yes** |

**The resonance is measured.** Constraint closure is ~0.98–1.00 at integer
rate ratios and 0.58–0.74 at non-integer ones, tracking the exact prediction
within 0.05 everywhere. The rate itself is recovered to within 0.008 at every
α with R² > 0.995.

This is the substantive physical finding: **the discrete Page–Wootters
constraint closes only for commensurate clock rates.** Over one A-cycle, clock
B advances 2πα and returns to its start only if α ∈ ℤ. Two clocks at different
gravitational potentials have a generically *irrational* rate ratio, so such a
pair admits **no exact joint cyclic constraint at all** — IBM-5's stationarity
is a special property of commensurate clocks, not a generic feature of clocks
running at different rates.

## The one failed gate is a wrong gate, and the data corrects it

`gate2_matched_echo_highest_a0.75` assumed the matched pairing always gives
the largest overlap. **Theory itself says otherwise**: at α=0.75 the exact
values are matched 0.7812 versus compensate-with-1 **0.8005**. The hardware
reproduced that ordering faithfully (0.7367 vs 0.8414). When the pairing does
not *close* the constraint, nothing makes it maximise overlap — that only
holds at commensurate α.

This is the third pre-registered gate in this program to encode an unchecked
assumption (after IBM-4's Schmidt reshape and IBM-6's wrong_way sign claim).
The gate is left as failed in the record and the assumption is corrected here
rather than the threshold being moved.

## A finite-clock resolution limit, found in dry run

The conditional signal is sampled at only d points, so α and d−α alias
exactly: at d=4, α=1 is indistinguishable from α=3. A first fit scanning to
α=3 returned 2.998 for a programmed α=1.0 — the alias, not bad data. **A
d-state clock resolves a rate ratio only within the Nyquist range α ≤ d/2.**

---

## Scope, restated

α is a dimensionless programmable ratio. **No gravity, metric, or physical
constant is simulated here** — putting `G` or `c` into a circuit (or into a
D-LinOSS damping term) does not import the physics, because a qubit register
contains no spacetime. Realistic gravitational dilation (α−1 ≈ 4.5×10⁻¹⁰ at
GPS orbit) sits eight orders of magnitude below this hardware's noise floor;
only the *mechanism* is demonstrated, at ratios corresponding to absurdly
strong fields. Related: Smith & Ahmadi, [arXiv:1904.12390](https://arxiv.org/abs/1904.12390).

## Provenance

`ibm_marrakesh`, 2026-08-08. IBM-6: 2 jobs, 16 circuits. IBM-7: 1 job, 20
circuits. Job IDs in the respective results JSONs. Capture before trial expiry
(~2026-09-01):

```
python pw_ibm_provenance.py --results results_ibm6_ibm_marrakesh/ibm6_results.json --out results_ibm6_ibm_marrakesh/ibm6_provenance.json
python pw_ibm_provenance.py --results results_ibm7_ibm_marrakesh/ibm7_results.json --out results_ibm7_ibm_marrakesh/ibm7_provenance.json
```
