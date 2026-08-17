# Replacement Zenodo abstract — Paper 2

The live abstract on record 21878787 is stale: it describes six runs, stops at
IBM-5, omits IBM-7/9/10, and retains the "necessary but not sufficient"
phrasing since corrected to "neither necessary nor sufficient." Zenodo
metadata is editable in place, so this replaces it without a new DOI.

Paste the plain-text version below into the Description field (Zenodo accepts
basic HTML; the tagged version follows).

---

## Plain text

An experimental program asking a narrow, testable version of a century-old
question: does time defined *relationally* — by correlations between a clock
and the rest of a system, rather than by an external parameter — leave a
quantum signature that a classical system cannot fake?

The answer required first establishing where the question could not be asked.
A cross-datacenter timing campaign on Google TPU Research Cloud hardware
(CHRONOS) instrumented two geographically separated hosts and found that their
apparent temporal correlation survived a one-hour artificial offset — structural
hardware similarity, not shared time. That null closed the classical-substrate
line decisively rather than leaving it ambiguous, and moved the clock inside
the modeled state.

A simulation campaign followed, using D-LinOSS, a damped linear oscillatory
state-space model whose complex-diagonal recurrence matches the physics under
test at the level of the measured phase evolution. Its *failures* set every
design parameter of the hardware program that followed: an under-identifiable
generator established that entropy-bearing histories were required; an
entanglement-damped variant losing to a stationary baseline at every grid
density identified record overlap as the correct independent variable; and a
false positive on classical telegraph noise produced the standing rule that a
single local measurement configuration cannot certify quantum structure.

Eleven pre-registered runs on IBM Quantum Heron processors (72 jobs) then
tested that rule:

- The conditional-evolution signal usually cited as evidence for relational
  time is reproduced by an explicit classical clock control to within shot
  noise, on two devices.
- A clock-coherence witness is not classically reproducible, but a
  zero-entanglement product state scores 4.2x higher on it, and a separable
  state scores 1.7x higher on the joint-readout witness built to repair it.
  Both adversarial states were constructed by this program against its own
  results. A two-line theorem generalizes the failure: within this local
  product-basis architecture, no single measurement configuration certifies
  clock-system entanglement.
- A multi-setting fidelity witness does certify it, exceeding the exact
  separable bound of 1/2 with bootstrap 95% confidence intervals whose lower
  limits clear the bound outright (F = 0.9419, CI [0.9286, 0.9548] at d=4;
  F = 0.8829, CI [0.8709, 0.8945] at d=8).
- On a single preparation, in one job, the state is certified entangled
  (F = 0.9014, CI [0.8913, 0.9113]), stationary as a quantum ray under the
  paired clock-shift-and-evolution operation but not under mismatched controls
  (42-143 sigma), and internally evolving under that same operator
  (R^2 = 0.9942) — the Page-Wootters mechanism's defining conjunction, measured
  on one state rather than inferred across several.
- Detuning the clock rates reveals a commensurability condition for exact cycle
  closure of a finite cyclic clock; superposing the rate itself produces
  interference of 0.2411 where the corresponding incoherent mixture predicts
  identically zero.

Two of the eleven runs are reported as failures. Both attacked the phase of the
stationarity eigenvalue, and a subsequent two-line derivation showed the
quantity was fixed by construction — there was never a phase to measure. That
derivation, and the rule it produced (establish whether a quantity is contingent
before designing a run to measure it), are recorded alongside the failures.

The contribution is a hardware-measured certification threshold for temporal
structure, and it is higher than the observables usually offered as evidence
for relational time can reach. Every limit was found by this program's own
pre-registered adversarial controls rather than left for a referee.

Raw counts, pre-registrations, derived results and server-side provenance
including per-run backend calibration are archived for all eleven runs (518
circuits across 34 jobs); every analysis reproduces from counts with no IBM
account.

CLAIM BOUNDARY. Nothing here claims that time in nature is emergent, tests
quantum gravity or the Wheeler-DeWitt equation, or realizes a physical
Page-Wootters universe. The states are engineered by externally timed gates,
the clock/system split is imposed rather than derived, and the certification is
device-dependent rather than a Bell test. The rate-superposition result is not
gravitational time dilation: there is no metric, and realistic dilation is some
eight orders of magnitude below this hardware's floor.

Research supported with Cloud TPUs from Google's TPU Research Cloud (TRC).
Hardware experiments used IBM Quantum Open Plan access.

---

## What changed from the live version

- six runs -> eleven; adds IBM-7, IBM-9, IBM-10
- "necessary but not sufficient" -> the corrected "neither necessary nor
  sufficient" framing, since d=2 carries 1.0 ebits with a witness of exactly
  zero
- "no functional of a single measurement setting" -> scoped to local
  product-basis distributions, which is what the theorem actually covers
- adds the bootstrap confidence intervals, which turn the entanglement claims
  from point estimates into statistical certifications
- states the TPU/D-LinOSS lineage as load-bearing rather than as an
  acknowledgement line, per the repository's own account of where the method
  came from
- adds the two reported failures and the derivation that retired the question
- TRC wording matches Google's recommended form
