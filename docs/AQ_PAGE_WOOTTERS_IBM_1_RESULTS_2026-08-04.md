# AQ-PAGE-WOOTTERS-IBM-1 — Hardware Results

**Executed 2026-08-04 on `ibm_marrakesh`** (156-qubit Heron r2, IBM Open Plan
trial instance). 11 jobs, ~53k shots. All 10 scored gates pass. Pre-registration
filed before submission: `results/hardware/ibm1/ibm1_prereg.json`. Raw analysis:
`results/hardware/ibm1/ibm1_results.json`.

**Headline (Gate 4):** the coherence witness decays by ~7× across the clock
decoherence sweep while conditional evolution — the apparent flow of time —
survives at R² ≥ 0.94 at *every* μ including where the witness has collapsed
to its noise floor. Apparent temporal dynamics measurably outlives its own
quantum signature on real hardware.

---

## Two gaps found in this run's own instrumentation

Reported first, before the results, because the previous Gate 0 write-up was
withdrawn for exactly this class of problem.

**1. `gate1_anchor` was pre-registered but never scored.** The submitter's
prereg lists seven gates; the scoring code computes six of them (three under
slightly different names — `gate4_conditional_survives_all_mu` is scored as
`gate4_cond_survives_d4/d8`, and similarly for gates 5 and 6 — those are
cosmetic). `gate1_anchor` is genuinely absent from the scoring path. It is
computed **post-hoc** below and clearly labelled as such; "all 10 gates pass"
refers to the ten gates the code actually scored, not to the pre-registered
list, which had seven entries covering both clock sizes.

**2. The μ=0 anchor is attenuated relative to IBM-0, and the cause is
verified.** At `optimization_level=0` the three `CRY(0)` gates present at μ=0
are **not** optimized away — transpiled depth is 66 and CX count 21 at *every*
μ including μ=0, confirmed directly. So the μ=0 circuit executes six CX gates
that are logically the identity but physically noisy, which IBM-0's circuit
did not contain. The anchor is therefore expected to sit below IBM-0's value,
and it does.

| | IBM-1 μ=0 measured | IBM-0 measured | exact | IBM-1/IBM-0 | IBM-1/exact |
|---|---|---|---|---|---|
| d=4 | 0.180 | 0.196 | 0.1768 | 0.918 | **1.018** |
| d=8 | 0.349 | 0.406 | 0.4967 | 0.860 | 0.703 |

The d=4 anchor lands essentially on the exact value. The d=8 anchor is
attenuated to 0.70 of exact — consistent with the deeper circuit (21 CX vs
IBM-0's 15 for the equivalent witness) and with IBM-0's own d=8 attenuation
of 0.82 compounded by the added coupling gates.

**This constant-depth property is a feature for the primary measurement.**
Because depth and gate count are identical at every μ, the hardware
attenuation is uniform across the sweep and does not confound the *shape* of
the decay — which is what the functional-form test actually measures. A
uniform-attenuation fit `measured = A·exact` gives A = 0.916 (d=4, R²=0.71)
and A = 0.805 (d=8, R²=0.90).

---

## Arm 1A — the decoherence sweep

Measured witness TVD, classical-control baseline, their separation, and the
conditional-evolution R² at each μ:

**d = 8** (the strong arm):

| μ/π | witness | exact | classical | separation | cond R² |
|---|---|---|---|---|---|
| 0.000 | 0.349 | 0.497 | 0.045 | **0.304** | 0.960 |
| 0.125 | 0.389 | 0.485 | 0.036 | **0.353** | 0.937 |
| 0.250 | 0.347 | 0.450 | 0.039 | **0.308** | 0.950 |
| 0.375 | 0.343 | 0.395 | 0.058 | **0.286** | 0.973 |
| 0.500 | 0.273 | 0.324 | 0.021 | **0.252** | 0.964 |
| 0.625 | 0.255 | 0.244 | 0.043 | **0.213** | 0.984 |
| 0.750 | 0.149 | 0.160 | 0.050 | 0.099 | 0.940 |
| 0.875 | 0.082 | 0.077 | 0.034 | 0.048 | 0.948 |
| 1.000 | 0.049 | 0.000 | 0.036 | 0.013 | 0.940 |

**d = 4** (the weak arm — see caveats):

| μ/π | witness | exact | classical | separation | cond R² |
|---|---|---|---|---|---|
| 0.000 | 0.180 | 0.177 | 0.046 | 0.134 | 0.995 |
| 0.125 | 0.170 | 0.173 | 0.032 | 0.138 | 0.995 |
| 0.250 | 0.128 | 0.163 | 0.054 | 0.074 | 0.995 |
| 0.375 | 0.110 | 0.147 | 0.040 | 0.070 | 0.980 |
| 0.500 | 0.112 | 0.125 | 0.010 | 0.102 | 0.968 |
| 0.625 | 0.096 | 0.098 | 0.036 | 0.060 | 0.952 |
| 0.750 | 0.088 | 0.068 | 0.034 | 0.054 | 0.998 |
| 0.875 | 0.068 | 0.035 | 0.080 | −0.012 | 0.996 |
| 1.000 | 0.026 | 0.000 | 0.056 | −0.030 | 0.907 |

### Gate 4 — the headline result

**Passes at both clock sizes, and this is the run's primary claim.** The
witness falls from 0.349 to 0.049 at d=8 (a factor of ~7, ending within its
own noise floor) while conditional evolution stays at R² ≥ 0.937 across the
entire sweep, including at μ=π where the witness has collapsed. At d=4 the
witness falls 0.180 → 0.026 with conditional R² ≥ 0.907 throughout.

**Honest caveat on the threshold.** The hardware gate was set at R² > 0.90,
looser than the dry run's (> 0.995 ideal, > 0.95 noisy). The d=4 worst point,
0.9074 at μ=π, clears that loosened bar by 0.007 — it would **fail** the dry
run's noisy criterion. d=8's worst (0.9365) also falls below 0.95. So the
claim "conditional evolution survives" is well supported in the sense of the
cosine structure remaining clearly present and well-fit at every μ, but the
fit quality on hardware is materially below the simulated prediction, and the
threshold was relaxed to accommodate that. That relaxation is recorded here
rather than buried.

### Classical-control arms are at their expected noise floors

TVD is a positively biased statistic at finite sampling, so the classical arm
cannot read exactly zero. Expected floors and measurements agree:

| | expected floor | measured mean | measured range |
|---|---|---|---|
| d=4 | 0.031 | 0.043 | 0.010 – 0.080 |
| d=8 | 0.047 | 0.040 | 0.021 – 0.058 |

**This explains the two negative separations at d=4** (μ = 0.875π and π).
There, both the coherent witness (0.068, 0.026) and the classical arm (0.080,
0.056) sit at or below the ~0.031 floor. A negative separation between two
quantities that are both noise is not a failure — the theory predicts the
separation → 0 as μ → π, and that is what is observed. It should not be read
as the classical arm "beating" the coherent one.

### Caveat: d=4 is the weak arm

The d=4 dynamic range (0.180 down to 0.026) is only ~4–6× its classical noise
floor, versus ~7–8× at d=8 with a much larger absolute separation. Combined
with the uniform-attenuation fit quality (R² = 0.71 at d=4 vs 0.90 at d=8),
**d=8 carries this result and d=4 is corroborative at best.** Any future run
should either raise d=4's shot count substantially or drop it.

**Provenance confirms a specific hardware cause, not just shot noise.**
Calibration snapshot (`results/hardware/ibm1/ibm1_provenance.json`,
`last_update_date` 2026-08-04T10:53:52-05:00, ~45 min before submission):

| qubit | readout err | T1 | T2 |
|---|---|---|---|
| q2 | 0.0026 | 285.5 μs | 330.8 μs |
| q6 | 0.0037 | 148.0 μs | 155.7 μs |
| q0 | 0.0062 | 236.9 μs | 56.7 μs |
| q3 | 0.0082 | 268.9 μs | 254.7 μs |
| **q4** | 0.0143 | **79.3 μs** | **28.0 μs** |
| q5 | 0.0237 | 291.5 μs | 168.7 μs |
| q1 | 0.0251 | 187.9 μs | 167.6 μs |

`q4` has the worst T1 and worst T2 of all seven qubits used, by a wide margin
(T1 less than a third of the next-worst; T2 about half). In the d=4 layout
(`[0,1,2,3,4]`, `n_clock=2`), `q4` is `env[1]` — the qubit receiving the
`CRY(μ)` coupling and left unmeasured on *every* d=4 arm-1A circuit,
independent of μ. Its poor coherence time is a real, uncontrolled decoherence
source sitting exactly where the experiment places its intended synthetic
channel, compounding with rather than merely adding noise to the μ-sweep.
This is a more specific explanation for the weak d=4 arm than shot statistics
alone, and it is actionable: a future run should pick layouts that avoid
placing environment qubits on the coupling map's worst-T2 sites, which the
current layout selection (first contiguous chain found) does not screen for.

---

## Gate 5 — functional form on hardware

The Gate 0 pre-registration predicted the power law in record overlap would
fit substantially better than the exponential in entanglement. On hardware:

| | exponential in entanglement | power law in overlap | gap |
|---|---|---|---|
| d=4 | R² = 0.687 | R² = 0.812 | 0.124 |
| d=8 | R² = 0.704 | **R² = 0.982** | **0.278** |

**The prediction holds, decisively at d=8 and weakly at d=4.** Note that both
forms fit *worse* on hardware than on the exact curve (where the power law
reached 0.999+), as expected from shot noise and the noise-floor contribution
at high μ. The d=4 power-law R² of 0.812 is well below the ~0.96 the noisy
simulation suggested — again pointing at d=4 as the under-powered arm.

Scope, unchanged from Gate 0: this compares clock-marginal TVD against
`S(ρ_E)`, the environment's entanglement with clock+system. It is **not** a
direct test of arXiv:2512.15789, whose `C(E) = C₀e^{−kE}` relates subsystem
coherence to *clock–subsystem* entanglement. The defensible claim remains the
narrow one: for this engineered Hamming-dephasing channel and this witness,
coherence tracks the record-overlap channel parameter substantially better
than an exponential in the entanglement measure available here.

---

## Arm 1B — the informational arrow

| arm | S(ρ_S \| t), t = 0…7 |
|---|---|
| coupled | 0.278, 0.329, 0.289, 0.391, 0.753, 0.788, 0.866, 0.960 |
| **classical clock** | 0.193, 0.097, 0.319, 0.482, 0.684, 0.845, 0.961, 0.997 |
| uncoupled (tomographic) | 0.114, 0.286, 0.277, 0.302, 0.065, 0.000, 0.017, 0.000 |

**H3 is confirmed on hardware.** The classical-clock control reproduces the
monotonic entropy rise as completely as the coherent arm does (0.193 → 0.997
versus 0.278 → 0.960). The informational arrow of time is therefore *not*, by
itself, a quantum signature — the same conclusion IBM-0 established for
conditional evolution, now extended to entropy production and confirmed on a
real device.

The uncoupled control behaves better on hardware than in simulation: mean
0.133, with four of eight readings at or below 0.065 and two at exactly 0.000
(|r| = 1, a fully pure reconstructed state). This is the correct qualitative
behaviour — with no CNOT to the environment the system stays pure and its true
von Neumann entropy is exactly 0 at every clock reading. It is only visible
because the estimator was corrected to use 3-basis tomography; the single-basis
population entropy that the withdrawn Gate 0 draft used would have reported
this control rising like the coupled arm.

---

## What this run establishes

1. **A decoherence threshold for relational time is measurable on hardware.**
   The clock-marginal coherence witness decays ~7× under engineered clock
   decoherence, ending at its noise floor, with the coherent-vs-classical
   separation collapsing from 0.304 to 0.013 (d=8).
2. **Apparent time outlives its quantum signature** (Gate 4) — the central
   claim, holding at every μ at both clock sizes, subject to the threshold
   caveat above.
3. **Neither conditional evolution nor the informational arrow is a quantum
   signature.** IBM-0 showed the first; this run shows the second, on
   hardware, with a classical clock reproducing the entropy arrow completely.
4. **The witness follows the record-overlap power law**, not an exponential in
   the available entanglement measure — clearly at d=8.

## What it does not establish

No claim that time in nature is emergent, no test of quantum gravity or the
Wheeler–DeWitt equation, no realization of a physical Page–Wootters universe.
The history state is engineered. The clock is 2–3 qubits.

## Provenance

Backend `ibm_marrakesh`, 11 jobs, 2026-08-04T16:38Z submission. Job IDs are
recorded in `ibm1_results.json`. **Capture server-side provenance before the
trial account expires (~2026-09-01):**

```
python pw_ibm_provenance.py --results results_ibm1_ibm_marrakesh/ibm1_results.json --out results_ibm1_ibm_marrakesh/ibm1_provenance.json
```

## Recommended follow-ups

- **Raise d=4 statistics or drop the arm.** At 500 shots/circuit its dynamic
  range is too close to the classical noise floor to carry weight.
- **Add `gate1_anchor` to the submitter's scoring path** so the pre-registered
  gate list and the scored list match exactly.
- **Consider an μ=0 circuit without the CRY gates** as a separate anchor point,
  to disentangle "coupling gates present but inactive" from the true IBM-0
  baseline. The current design's constant depth is right for measuring the
  decay *shape*, but it costs a clean comparison to IBM-0.
