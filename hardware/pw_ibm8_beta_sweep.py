#!/usr/bin/env python3
"""AQ-PAGE-WOOTTERS-IBM-8 -- depth-matched phase certification (fixes IBM-6).

IBM-6 tried to certify that the joint eigenvalue is +1 and FAILED, for a
design flaw: its four arms had wildly different two-qubit costs (29 CX for
the joint arm vs 8 for system_only at d=8), so cross-arm comparison was
confounded by circuit depth and the shallow control arm measured higher than
the joint arm. Its imaginary part also came in ~6 sigma from the zero theory
demands, and a systematic circuit phase could not be told apart from a genuine
eigenvalue phase.

THE FIX: sweep ONE parameter through ONE circuit.

    A(beta) = S_A (x) P(beta * theta)

Every beta uses the IDENTICAL circuit -- same controlled clock-shift, same
controlled-phase gate -- differing only in the ANGLE fed to that phase gate.
At optimization_level=0 the transpiled gate count is therefore identical for
every beta (asserted in the dry run). Any depth-induced attenuation is a
COMMON factor across the sweep, so it cannot distort the SHAPE of the curve,
which is what carries the physics. beta = 1 is the constraint-preserving
pairing; beta = 0 is clock-only; beta = -1 is the reversed pairing.

WHY THIS SEPARATES A REAL PHASE FROM A COHERENT ERROR -- the thing IBM-6 could
not do. The exact amplitude is t-independent and closed-form:

    <Psi|A(beta)|Psi> = (1 + e^{i (beta-1) theta}) / 2

so Re(beta) = (1 + cos((beta-1) theta))/2 and Im(beta) = sin((beta-1) theta)/2,
with Im vanishing exactly at beta = 1. A coherent gate error adds a
beta-INDEPENDENT offset to the measured phase, while the genuine signal varies
with beta in a known way. Fitting

    Im_measured(beta) = A * sin((beta - 1) * theta) / 2 + c

separates them: c is the systematic, and c ~ 0 certifies the eigenvalue is
real. IBM-6 measured a single point and had no way to make that distinction.

Usage:
    python pw_ibm8_beta_sweep.py --dry
    python pw_ibm8_beta_sweep.py --backend ibm_marrakesh
"""

from __future__ import annotations

import argparse
import datetime
import json
from pathlib import Path

import numpy as np
from qiskit import ClassicalRegister, QuantumCircuit, transpile
from qiskit.quantum_info import Statevector

from pw_ibm1_submit import DryBackend, HardwareBackend, clear_checkpoint, find_chain
from pw_ibm5_constraint import clock_shift, prepare_history
from pw_ibm6_hadamard import controlled_clock_shift, z_expectation

CLOCK_SIZES = (2, 3)
BETAS = (-1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0)
SHOTS = 4000


def build_beta_test(n_clock: int, beta: float, imaginary: bool) -> QuantumCircuit:
    """Hadamard test of A(beta) = S (x) P(beta*theta).

    Structure is IDENTICAL for every beta -- only the cp angle changes."""
    d = 2**n_clock
    theta = 2.0 * np.pi / d
    clock, system, anc = list(range(n_clock)), n_clock, n_clock + 1
    qc = QuantumCircuit(n_clock + 2)
    qc.compose(prepare_history(n_clock), qubits=list(range(n_clock + 1)), inplace=True)
    qc.h(anc)
    controlled_clock_shift(qc, anc, clock)          # always present
    qc.cp(beta * theta, anc, system)                # always present; angle varies
    if imaginary:
        qc.sdg(anc)
    qc.h(anc)
    qc.add_register(ClassicalRegister(1, "c"))
    qc.measure(anc, 0)
    return qc


def exact_amplitude(n_clock: int, beta: float) -> complex:
    d = 2**n_clock
    theta = 2.0 * np.pi / d
    psi = Statevector.from_instruction(prepare_history(n_clock)).data
    qc = prepare_history(n_clock).copy()
    clock_shift(qc, list(range(n_clock)))
    qc.p(beta * theta, n_clock)
    return complex(np.vdot(psi, Statevector.from_instruction(qc).data))


def fit_offset(betas: np.ndarray, im: np.ndarray, theta: float) -> tuple[float, float, float]:
    """Im(beta) = A*sin((beta-1)*theta)/2 + c  -> (A, c, R^2).

    c is a beta-independent coherent-error offset; A is the genuine amplitude."""
    basis = np.sin((betas - 1.0) * theta) / 2.0
    M = np.column_stack([basis, np.ones_like(basis)])
    coef, *_ = np.linalg.lstsq(M, im, rcond=None)
    pred = M @ coef
    r2 = 1.0 - np.sum((im - pred) ** 2) / max(np.sum((im - im.mean()) ** 2), 1e-12)
    return float(coef[0]), float(coef[1]), float(r2)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--backend", default=None)
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--out-dir", type=Path, default=None)
    args = ap.parse_args()

    print("=== EXACT AMPLITUDES AND DEPTH-MATCH CHECK ===")
    preds, sim = {}, None
    from qiskit_aer import AerSimulator
    sim = AerSimulator()
    for n_clock in CLOCK_SIZES:
        d = 2**n_clock
        theta = 2.0 * np.pi / d
        block = {}
        for b in BETAS:
            a = exact_amplitude(n_clock, b)
            block[str(b)] = {"re": a.real, "im": a.imag, "phase": float(np.angle(a))}
        preds[str(d)] = block
        # Depth-match assertion: identical cost at every beta, by construction.
        costs = set()
        for b in BETAS:
            t = transpile(build_beta_test(n_clock, b, False), sim,
                          optimization_level=0, basis_gates=["rz", "sx", "x", "cx"])
            costs.add((t.depth(), t.count_ops().get("cx", 0)))
        assert len(costs) == 1, f"arms are NOT depth-matched at d={d}: {costs}"
        depth, cx = costs.pop()
        print(f"  d={d}: every beta -> depth={depth}, cx={cx}  [DEPTH-MATCHED]")
        for b in BETAS:
            e = block[str(b)]
            print(f"    beta={b:+.1f}  Re={e['re']:+.4f}  Im={e['im']:+.4f}")
        j = block["1.0"]
        assert abs(j["re"] - 1.0) < 1e-9 and abs(j["im"]) < 1e-9, "beta=1 must be exactly +1"

    backend = DryBackend() if args.dry else HardwareBackend(args.backend)
    if args.fresh and not args.dry:
        clear_checkpoint(backend.name)
    out_dir = args.out_dir or Path(f"results_ibm8_{backend.name}")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.utcnow().isoformat() + "Z"
    print(f"\nAQ-PAGE-WOOTTERS-IBM-8  backend={backend.name}  dry={args.dry}  {ts}", flush=True)

    chain = find_chain(backend.coupling_map, backend.num_qubits, max(CLOCK_SIZES) + 2)
    prereg = {"program": "AQ-PAGE-WOOTTERS-IBM-8", "backend": backend.name,
              "dry_run": bool(args.dry), "submission_time": ts, "optimization_level": 0,
              "shots": SHOTS, "betas": list(BETAS), "exact_amplitudes": preds,
              "purpose": "Fix IBM-6's depth-confounded comparison by sweeping one angle "
                         "through one identical circuit, and separate a genuine eigenvalue "
                         "phase from a coherent-error offset by fitting Im(beta).",
              "gates": {
                  "gate1_peak_at_beta1": "Re(beta) is maximal at beta = 1",
                  "gate2_shape_matches": "normalised Re(beta) tracks (1+cos((beta-1)theta))/2 "
                                         "within 0.10 across the sweep",
                  "gate3_offset_small": "the beta-independent offset c in the Im fit is within "
                                        "3 sigma of 0 -> no coherent-error phase, eigenvalue REAL",
                  "gate4_im_zero_at_beta1": "Im(beta=1), after subtracting the fitted offset c, "
                                            "is within 3 sigma of 0",
              }}
    (out_dir / "ibm8_prereg.json").write_text(json.dumps(prereg, indent=2), encoding="utf-8")
    print(f"  pre-registration filed: {out_dir / 'ibm8_prereg.json'}", flush=True)

    results = {"backend": backend.name, "exact_amplitudes": preds, "arms": {}}
    gates = {}
    sigma = 1.0 / np.sqrt(SHOTS)

    for n_clock in CLOCK_SIZES:
        d = 2**n_clock
        theta = 2.0 * np.pi / d
        layout = chain[:n_clock + 2]
        print(f"\n=== d={d} ===", flush=True)

        circuits, index = [], []
        for b in BETAS:
            for imag in (False, True):
                circuits.append(build_beta_test(n_clock, b, imag))
                index.append((b, imag))
        counts, _ = backend.run_batch(circuits, SHOTS, layout, stage=f"beta_d{d}")

        meas = {}
        for (b, imag), c in zip(index, counts):
            meas.setdefault(b, {})["im" if imag else "re"] = z_expectation(c)

        betas = np.array(BETAS)
        re = np.array([meas[b]["re"] for b in BETAS])
        im = np.array([meas[b]["im"] for b in BETAS])
        amp, offset, r2 = fit_offset(betas, im, theta)
        peak = float(re.max())
        norm_re = re / max(peak, 1e-9)
        exact_re = np.array([(1 + np.cos((b - 1) * theta)) / 2 for b in BETAS])

        results["arms"][str(d)] = {
            "betas": list(BETAS), "re": re.tolist(), "im": im.tolist(),
            "im_fit_amplitude": amp, "im_fit_offset": offset, "im_fit_r2": r2,
            "re_normalised": norm_re.tolist(),
            "im_at_beta1_offset_corrected": float(meas[1.0]["im"] - offset),
        }
        for b in BETAS:
            e = preds[str(d)][str(b)]
            print(f"  beta={b:+.1f}  Re={meas[b]['re']:+.4f}  Im={meas[b]['im']:+.4f}   "
                  f"(exact Re={e['re']:+.4f} Im={e['im']:+.4f})", flush=True)
        print(f"  Im fit: amplitude={amp:+.4f}  OFFSET c={offset:+.4f}  R^2={r2:.4f}", flush=True)
        print(f"  Im(beta=1) offset-corrected = {meas[1.0]['im'] - offset:+.4f}  "
              f"(3 sigma = {3*sigma:.4f})", flush=True)

        gates[f"gate1_peak_at_beta1_d{d}"] = bool(BETAS[int(np.argmax(re))] == 1.0)
        gates[f"gate2_shape_matches_d{d}"] = bool(
            np.max(np.abs(norm_re - exact_re)) < 0.10)
        gates[f"gate3_offset_small_d{d}"] = bool(abs(offset) < 3 * sigma)
        gates[f"gate4_im_zero_at_beta1_d{d}"] = bool(
            abs(meas[1.0]["im"] - offset) < 3 * sigma)

    results["gates"] = gates
    results["all_gates_pass"] = bool(all(gates.values()))
    results["job_ids"] = getattr(backend, "job_ids", [])
    results["layouts"] = {str(2**nc): chain[:nc + 2] for nc in CLOCK_SIZES}
    (out_dir / "ibm8_results.json").write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    if not args.dry:
        clear_checkpoint(backend.name)
    print(f"\n[GATES] {json.dumps(gates, indent=2)}")
    print(f"[DONE] all_gates_pass={results['all_gates_pass']}  -> {out_dir / 'ibm8_results.json'}")


if __name__ == "__main__":
    main()
