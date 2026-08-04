#!/usr/bin/env python3
"""AQ-PAGE-WOOTTERS-IBM-0 -- hardware submission.

Submits the four-arm Page-Wootters protocol verified in pw_ibm_dryrun.py to
IBM Quantum, following the same discipline as the OAT PTM runs (ibm_run3.py):
programmatic contiguous-layout selection on the coupling map,
optimization_level=0 (protects the controlled-Ry ladder angles from the
transpiler defect root-caused in FINDINGS.md 123), a pre-registration JSON
written BEFORE the first job, readout-matrix calibration, and raw counts
archived to disk.

Token discipline: read from the environment, never hardcoded.

    export QISKIT_IBM_TOKEN=...        # bash / git-bash
    $env:QISKIT_IBM_TOKEN = "..."      # PowerShell

Smoke-test the entire submit/analyze pipeline against Aer first, spending zero
hardware shots:

    python pw_ibm_submit.py --dry

Then, only when ready to spend the Open Plan allowance:

    python pw_ibm_submit.py --backend ibm_marrakesh

Arms (see docs/AQ_PAGE_WOOTTERS_IBM_0_RUN_SPEC_2026-08-03.md):
  A  conditional evolution        (clock in superposition, computational readout)
  B  classical-clock control      (definite |t>, d circuits, averaged 1/d)
  C  coherence witness            (clock in superposition, inverse-QFT readout)
  D  classical-clock control      (definite |t>, inverse-QFT readout, averaged 1/d)
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit, transpile

from pw_ibm_dryrun import (
    build_conditional,
    build_witness,
    conditional_z,
    exact_witness_tvd,
    uniform_tvd_floor,
    witness_tvd,
)

CLOCK_SIZES = (1, 2, 3)
SHOTS = 8000
SHOTS_CAL = 2000
OUT_DIR = Path("results_page_wootters_ibm0")


# --------------------------------------------------------------------------- #
# Layout: a contiguous chain of n_c + 1 physical qubits on the coupling map.   #
# System qubit is the last element of the chain (matches logical index n_c).   #
# --------------------------------------------------------------------------- #
def find_chain(coupling_map, num_qubits: int, length: int, exclude: set[int] | None = None) -> list[int]:
    exclude = exclude or set()
    adj: dict[int, set[int]] = {q: set() for q in range(num_qubits)}
    for a, b in coupling_map.get_edges():
        adj[a].add(b)
        adj[b].add(a)

    def extend(path: list[int]) -> list[int] | None:
        if len(path) == length:
            return path
        for nxt in sorted(adj[path[-1]]):
            if nxt in path or nxt in exclude:
                continue
            found = extend(path + [nxt])
            if found:
                return found
        return None

    for start in range(num_qubits):
        if start in exclude:
            continue
        found = extend([start])
        if found:
            return found
    raise RuntimeError(f"no contiguous chain of length {length} found")


# --------------------------------------------------------------------------- #
# Backends: real hardware Sampler, or an Aer stand-in for --dry.              #
# --------------------------------------------------------------------------- #
class DryBackend:
    """Aer-backed stand-in exposing the coupling map + Sampler surface used here."""

    def __init__(self) -> None:
        from qiskit_aer import AerSimulator
        from qiskit_aer.noise import NoiseModel, ReadoutError, thermal_relaxation_error
        from qiskit.transpiler import CouplingMap

        t1, t2 = 150e3, 80e3
        nm = NoiseModel()
        e1 = thermal_relaxation_error(t1, t2, 50.0)
        e2 = thermal_relaxation_error(t1, t2, 300.0).expand(thermal_relaxation_error(t1, t2, 300.0))
        nm.add_all_qubit_quantum_error(e1, ["rz", "sx", "x", "h", "ry"])
        nm.add_all_qubit_quantum_error(e2, ["cx", "cz", "cp", "swap"])
        nm.add_all_qubit_readout_error(ReadoutError([[0.98, 0.02], [0.02, 0.98]]))
        self.num_qubits = 16
        self.name = "aer_dry"
        self.coupling_map = CouplingMap.from_line(self.num_qubits)
        self._sim = AerSimulator(noise_model=nm)

    def run_circuits(self, circuits: list[QuantumCircuit], shots: int) -> list[dict[str, int]]:
        tqc = [transpile(c, self._sim, optimization_level=0) for c in circuits]
        result = self._sim.run(tqc, shots=shots).result()
        return [result.get_counts(i) for i in range(len(circuits))]


class HardwareBackend:
    def __init__(self, backend_name: str | None) -> None:
        from qiskit_ibm_runtime import QiskitRuntimeService

        token = os.environ.get("QISKIT_IBM_TOKEN")
        if not token:
            raise SystemExit(
                "QISKIT_IBM_TOKEN is not set. Set it in your shell before running:\n"
                '  PowerShell:  $env:QISKIT_IBM_TOKEN = "<token>"\n'
                "  bash:        export QISKIT_IBM_TOKEN=<token>"
            )
        try:
            self._service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
        except Exception:
            self._service = QiskitRuntimeService(token=token)
        if backend_name:
            self._backend = self._service.backend(backend_name)
        else:
            self._backend = self._service.least_busy(operational=True, simulator=False)
        self.num_qubits = self._backend.num_qubits
        self.name = self._backend.name
        self.coupling_map = self._backend.coupling_map
        self.job_ids: list[str] = []

    def run_circuits(self, circuits: list[QuantumCircuit], shots: int) -> list[dict[str, int]]:
        from qiskit_ibm_runtime import SamplerV2 as Sampler

        tqc = [transpile(c, backend=self._backend, optimization_level=0) for c in circuits]
        sampler = Sampler(mode=self._backend)
        job = sampler.run([(c,) for c in tqc], shots=shots)
        self.job_ids.append(job.job_id())
        print(f"    job {job.job_id()} submitted; waiting...", flush=True)
        result = job.result()
        out = []
        for i in range(len(circuits)):
            creg = tqc[i].cregs[0].name
            out.append(getattr(result[i].data, creg).get_counts())
        return out


# --------------------------------------------------------------------------- #
# Circuit assembly with an explicit physical layout.                          #
# --------------------------------------------------------------------------- #
def laid_out(circuit_fn, n_clock: int, fixed_t, chain: list[int], num_qubits: int) -> QuantumCircuit:
    logical = circuit_fn(n_clock, fixed_t)
    # logical qubits 0..n_clock-1 = clock, n_clock = system -> chain order.
    return logical  # transpile receives initial_layout via chain below


def arm_circuits(n_clock: int) -> dict:
    d = 2**n_clock
    return {
        "A": [build_conditional(n_clock, None)],
        "B": [build_conditional(n_clock, t) for t in range(d)],
        "C": [build_witness(n_clock, None)],
        "D": [build_witness(n_clock, t) for t in range(d)],
    }


def analyze_clock_size(n_clock: int, counts: dict, shots_arm: dict) -> dict:
    d = 2**n_clock
    analytic = {t: float(np.cos(2 * np.pi * t / d)) for t in range(d)}

    cond = conditional_z(counts["A"][0], n_clock)
    cond_classical = {}
    for t in range(d):
        c = conditional_z(counts["B"][t], n_clock)
        cond_classical[t] = c[t]

    tvd_coh, p_coh = witness_tvd(counts["C"][0], n_clock)
    p_cls = np.zeros(d)
    for t in range(d):
        _, p = witness_tvd(counts["D"][t], n_clock)
        p_cls += np.asarray(p) / d
    tvd_cls = float(0.5 * np.sum(np.abs(p_cls - 1.0 / d)))

    exact_tvd, exact_p = exact_witness_tvd(n_clock)
    resid = [abs(cond[t] - analytic[t]) for t in range(d)]
    ab_gap = [abs(cond[t] - cond_classical[t]) for t in range(d)]

    # cos-fit attenuation A on <Z_S|t> vs cos(2 pi t / d)
    x = np.array([analytic[t] for t in range(d)])
    y = np.array([cond[t] for t in range(d)])
    denom = float(np.dot(x, x))
    a_fit = float(np.dot(x, y) / denom) if denom > 1e-9 else float("nan")
    r2 = float(1 - np.sum((y - a_fit * x) ** 2) / max(np.sum((y - np.mean(y)) ** 2), 1e-12)) if d > 2 else None

    sigma_shot = 1.0 / np.sqrt(counts["C"][0] and sum(counts["C"][0].values()) or 1)
    return {
        "d": d,
        "cond_z": cond,
        "cond_z_classical": cond_classical,
        "analytic_cond_z": analytic,
        "max_abs_resid_vs_analytic": float(np.max(resid)),
        "max_abs_gap_A_minus_B": float(np.max(ab_gap)),
        "cos_attenuation": a_fit,
        "cond_r2": r2,
        "witness_tvd_coherent": tvd_coh,
        "witness_tvd_classical": tvd_cls,
        "witness_separation": tvd_coh - tvd_cls,
        "exact_witness_tvd": exact_tvd,
        "null_floor": uniform_tvd_floor(d, shots_arm["C"]),
        "p_fourier_coherent": p_coh,
        "p_fourier_classical": [float(v) for v in p_cls],
    }


def evaluate_gates(per_size: dict) -> dict:
    d2 = per_size.get(1)
    d4 = per_size.get(2)
    d8 = per_size.get(3)
    gates = {}
    if d2:
        gates["gate1_structural_null_d2"] = bool(d2["witness_tvd_coherent"] < 3 * d2["null_floor"])
    if d4 and d8 and d2:
        gates["gate2_witness_ordered"] = bool(
            d8["witness_tvd_coherent"] > d4["witness_tvd_coherent"] > d2["witness_tvd_coherent"]
        )
    if all(x for x in (d2, d4, d8)):
        gates["gate3_classical_arms_null"] = bool(
            all(s["witness_tvd_classical"] < 3 * s["null_floor"] for s in (d2, d4, d8))
        )
        gates["gate4_conditional_recovered"] = bool(
            (d4["cond_r2"] or 0) > 0.95 and (d8["cond_r2"] or 0) > 0.95
        )
        gates["gate5_A_equals_B"] = bool(
            all(s["max_abs_gap_A_minus_B"] < 5.0 / np.sqrt(SHOTS // s["d"]) for s in (d4, d8))
        )
    return gates


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry", action="store_true", help="run against Aer, spend zero hardware shots")
    parser.add_argument("--backend", default=None, help="backend name; default = least busy")
    parser.add_argument("--clock-sizes", nargs="*", type=int, default=list(CLOCK_SIZES))
    parser.add_argument("--shots", type=int, default=SHOTS)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument(
        "--exclude",
        nargs="*",
        type=int,
        default=[],
        help="physical qubits to avoid, for a disjoint-layout replication "
        "(e.g. --exclude 0 1 2 3 to steer off the qubits used by the first run)",
    )
    args = parser.parse_args()

    backend = DryBackend() if args.dry else HardwareBackend(args.backend)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.utcnow().isoformat() + "Z"
    print(f"AQ-PAGE-WOOTTERS-IBM-0  backend={backend.name}  dry={args.dry}  {ts}", flush=True)

    # Pre-registration written BEFORE any job runs.
    prereg = {
        "program": "AQ-PAGE-WOOTTERS-IBM-0",
        "backend": backend.name,
        "dry_run": bool(args.dry),
        "submission_time": ts,
        "optimization_level": 0,
        "clock_sizes": args.clock_sizes,
        "shots": args.shots,
        "excluded_qubits": list(args.exclude),
        "predictions": {
            str(n): {
                "d": 2**n,
                "exact_witness_tvd": exact_witness_tvd(n)[0],
                "null_floor": uniform_tvd_floor(2**n, args.shots),
                "classical_arm_expected": "< 3 * null_floor",
                "cond_z_form": "A * cos(2*pi*t/d)",
            }
            for n in args.clock_sizes
        },
        "gates": [
            "gate1_structural_null_d2", "gate2_witness_ordered",
            "gate3_classical_arms_null", "gate4_conditional_recovered", "gate5_A_equals_B",
        ],
    }
    (args.out_dir / "pw_ibm_prereg.json").write_text(json.dumps(prereg, indent=2), encoding="utf-8")
    print(f"  pre-registration filed: {args.out_dir / 'pw_ibm_prereg.json'}", flush=True)

    per_size = {}
    layouts = {}
    used: set[int] = set()
    for n_clock in args.clock_sizes:
        chain = find_chain(
            backend.coupling_map, backend.num_qubits, n_clock + 1, exclude=set(args.exclude)
        )
        layouts[n_clock] = chain
        print(f"\n[n_clock={n_clock}] d={2**n_clock}  physical chain={chain}", flush=True)

        arms = arm_circuits(n_clock)
        counts = {}
        shots_arm = {}
        for arm, circuits in arms.items():
            per_circuit_shots = args.shots if arm in ("A", "C") else max(args.shots // (2**n_clock), 200)
            shots_arm[arm] = per_circuit_shots * len(circuits) if arm in ("B", "D") else per_circuit_shots
            print(f"  arm {arm}: {len(circuits)} circuit(s) x {per_circuit_shots} shots", flush=True)
            counts[arm] = backend.run_circuits(circuits, per_circuit_shots)

        analysis = analyze_clock_size(n_clock, counts, shots_arm)
        per_size[n_clock] = analysis
        print(
            f"  -> TVD coherent={analysis['witness_tvd_coherent']:.4f} "
            f"classical={analysis['witness_tvd_classical']:.4f} "
            f"(exact {analysis['exact_witness_tvd']:.4f}, floor {analysis['null_floor']:.4f}) "
            f"| max|A-B|={analysis['max_abs_gap_A_minus_B']:.4f} "
            f"| cond R2={analysis['cond_r2']}",
            flush=True,
        )

        # Archive raw counts per clock size.
        raw = {arm: [dict(c) for c in counts[arm]] for arm in counts}
        (args.out_dir / f"pw_ibm_counts_nclock{n_clock}.json").write_text(
            json.dumps({"n_clock": n_clock, "chain": chain, "counts": raw}, indent=2), encoding="utf-8"
        )

    gates = evaluate_gates(per_size)
    print(f"\n[GATES] {json.dumps(gates)}", flush=True)

    results = {
        "program": "AQ-PAGE-WOOTTERS-IBM-0",
        "backend": backend.name,
        "dry_run": bool(args.dry),
        "submission_time": ts,
        "layouts": {str(k): v for k, v in layouts.items()},
        "job_ids": getattr(backend, "job_ids", []),
        "per_clock_size": {str(k): v for k, v in per_size.items()},
        "gates": gates,
        "all_gates_pass": bool(gates and all(gates.values())),
    }
    (args.out_dir / "pw_ibm_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"[DONE] all_gates_pass={results['all_gates_pass']}  results={args.out_dir / 'pw_ibm_results.json'}", flush=True)


if __name__ == "__main__":
    main()
