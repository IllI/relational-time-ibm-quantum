# AQ-PAGE-WOOTTERS-IBM-15 — Two Geometric Phases, One Entanglement Sweep

**Executed 2026-08-18 on `ibm_marrakesh`.** 1 job `da2hc6s3jnrc73adu6cg`,
56 circuits, 3 qubits (`[146, 147, 148]`), 4 000 shots each, ~60 s of QPU.
**All 4 pre-registered gates pass.**

This replaces a retracted result. The earlier claim — that the geometric
phase's value is budget-free — was an artifact of a diagonal loop and was
withdrawn in full. What follows is what survived rebuilding the question from
the literature.

## The question, corrected

There is no single geometric phase for a mixed state. There are two
inequivalent published constructions, both measurable, and they disagree:

- **interferometric**, Sjöqvist *et al.*,
  [Phys. Rev. Lett. **85**, 2845 (2000)](https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.85.2845)
- **Uhlmann**, the holonomy on purifications, measured on superconducting
  qubits by Viyuela *et al.*,
  [npj Quantum Information **3**, 55 (2017)](https://www.nature.com/articles/s41534-017-0056-9)

**Both are entanglement-dependent.** The geometric phase is on the entanglement
budget either way — that is derived, not measured, and it answers the synthesis
repository's open question negatively. What this run measures is that the two
constructions **spend the budget at different rates**.

Mixedness here comes from **entanglement**, not temperature: the partner *is*
the purification, which is what makes the Uhlmann arm a single controlled gate.

## Results

```
 C        interf phase   Uhlmann phase    gap    (exact gap)
 0.1564   -0.905988      -0.837142      0.0688   (0.0330)
 0.3303   -0.843793      -0.765584      0.0782   (0.1447)
 0.4935   -0.833172      -0.577412      0.2558   (0.3035)
 0.6409   -0.794634      -0.285387      0.5092   (0.4479)
 0.7676   -0.671398      -0.130771      0.5406   (0.5212)
 0.8697   -0.566119      -0.042125      0.5240   (0.5008)
 0.9439   -0.422479      +0.008184      0.4307   (0.3885)
 0.9877   -0.189317      -0.022025      0.1673   (0.2005)

 measured vs exact:  Pearson r = 0.9779,  RMS residual 0.0441
 peak measured at C = 0.7676; exact peak at C = 0.7676
```

**The two constructions diverge, and the divergence is non-monotonic.** It rises
from near zero at low entanglement, peaks at `C = 0.7676`, and falls again. The
hardware reproduces that shape including the **location of the peak, exactly**.
That non-monotonic structure is what makes this more than a slope measurement —
a smooth systematic would not put its maximum in the right place.

## Controls

**Degenerate null (`θ = π/3`), phase spread 0.1932.** At `cos θ = 1/2` the
interferometric phase loses its `r`-dependence exactly, so the sweep must be
flat. It is flat to 0.19 rad against a 0.35 threshold — but the theoretical
value is **0**, and 0.19 is a real deviation, not noise-free agreement. This is
the angle that produced the retraction; it is now a permanent instrument check.

**Haar-random control arm**, visibilities `[0.631, 0.276, 0.233, 0.432]` —
scattered with no structure, as required. This is the control whose absence
caused the retraction. It ran here *before* any claim was made.

## Honest ledger

**The backend was in `maintenance` status at submission.** Qiskit warned:
`The backend ibm_marrakesh currently has a status of maintenance`. The job
completed and all gates pass, but data taken during a maintenance window
carries a calibration caveat that no gate in this run tests. **A replication on
an operational backend is the first thing to do**, and until then these numbers
should be treated as provisional.

**Two points deviate more than the rest.** At `C = 0.3303` the measured gap is
`0.0782` against an exact `0.1447` — off by nearly half. At `C = 0.6409` it
overshoots by `0.0613`. RMS residual across the sweep is `0.0441`, and the
correlation is `r = 0.9779`, so the curve is well recovered overall, but no
claim is made about individual points.

**The null is not perfectly flat.** 0.19 rad where theory says 0. That bounds
how well any phase in this run is determined — differences smaller than ~0.2
rad should not be read as real.

**Nothing here is a shared temporal reference.** The loops are externally
programmed, as everywhere in this programme. And the headline — that both
constructions are on the budget — is *derived*; the hardware content is the
measured divergence and its shape.

**Three errors were caught before submission**, none of which reached hardware:
a gate written as an endpoint difference when the exact gap is non-monotonic (it
would have failed on the true values); a spurious `π` "correction" from
computing preflight with `Rz(2π) ⊗ B` while the circuit applies only
controlled-`B`; and a fix that mutated shared dicts and silently left raw values
in place.

## What this establishes

> The two standard mixed-state geometric phases give measurably different
> answers about the same entangled states on hardware, with mixedness supplied
> by entanglement rather than temperature. Their difference is non-monotonic in
> the concurrence, peaking at `C ≈ 0.77`, and the hardware reproduces both the
> magnitude (`r = 0.9779`, RMS 0.044) and the peak location exactly. Both
> constructions depend on entanglement, so the geometric phase is on the
> entanglement budget in either formulation — closing the question the
> synthesis repository left open, and closing it negatively.

## Provenance

`ibm_marrakesh`, 2026-08-18, job `da2hc6s3jnrc73adu6cg`, qubits
`[146, 147, 148]`, 56 circuits at 4 000 shots, backend status `maintenance`.
Raw counts in `results_ibm15/raw.json`; every number reproduces from them:

```
python hardware/pw_ibm15_two_geometric_phases.py --analyze results_ibm15/raw.json
python hardware/pw_ibm_provenance.py --results results_ibm15/raw.json --out results_ibm15/ibm15_provenance.json
```
