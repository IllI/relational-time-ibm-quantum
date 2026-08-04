#!/usr/bin/env python3
"""AQ-PAGE-WOOTTERS-IBM-0 -- post-hoc layout verification.

The submitter recorded a physical chain from find_chain() but did NOT pass
initial_layout to transpile() (bug caught in code review 2026-08-03). This
script retrieves the actual transpiled circuits from the still-queryable jobs
and reports which physical qubits each job really touched and where the
measured clock qubits actually live.

Run in the shell where QISKIT_IBM_TOKEN is set:

    python pw_ibm_verify_layout.py

It reads every results dir given (default: all three runs), fetches each
job's input circuit, and writes pw_ibm_actual_layouts.json next to each
results file. Zero QPU cost -- metadata reads only.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

DEFAULT_RESULTS = [
    Path("results_page_wootters_ibm0/pw_ibm_results.json"),
    Path("results_page_wootters_ibm0_fez/pw_ibm_results.json"),
    Path("results_page_wootters_ibm0_layoutB/pw_ibm_results.json"),
]


def circuit_footprint(circuit) -> dict:
    """Physical qubits touched by any op, and the measurement map."""
    touched: set[int] = set()
    meas_map: dict[int, int] = {}
    for instruction in circuit.data:
        qubits = [circuit.find_bit(q).index for q in instruction.qubits]
        touched.update(qubits)
        if instruction.operation.name == "measure":
            clbit = circuit.find_bit(instruction.clbits[0]).index
            meas_map[clbit] = qubits[0]
    ops = dict(circuit.count_ops())
    return {
        "touched_physical_qubits": sorted(touched),
        "measure_clbit_to_physical_qubit": {str(k): v for k, v in sorted(meas_map.items())},
        "depth": circuit.depth(),
        "two_qubit_ops": int(sum(v for k, v in ops.items() if k in ("cx", "cz", "ecr", "swap"))),
        "op_counts": {k: int(v) for k, v in ops.items()},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", nargs="*", type=Path, default=DEFAULT_RESULTS)
    args = parser.parse_args()

    token = os.environ.get("QISKIT_IBM_TOKEN")
    if not token:
        raise SystemExit("QISKIT_IBM_TOKEN is not set in this shell.")

    from qiskit_ibm_runtime import QiskitRuntimeService

    try:
        service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    except Exception:
        service = QiskitRuntimeService(token=token)

    for results_path in args.results:
        if not results_path.exists():
            print(f"[SKIP] {results_path} not found")
            continue
        results = json.loads(results_path.read_text(encoding="utf-8"))
        job_ids = results.get("job_ids", [])
        recorded = results.get("layouts", {})
        print(f"\n=== {results_path}  backend={results.get('backend')} ===")
        print(f"  recorded (intended) layouts: {recorded}")

        report = {"backend": results.get("backend"), "recorded_layouts": recorded, "jobs": []}
        all_touched: set[int] = set()
        for jid in job_ids:
            try:
                job = service.job(jid)
                circuits = job.inputs.get("pubs", [])
                first = circuits[0][0] if circuits else None
                if first is None:
                    raise ValueError("no circuit in job inputs")
                fp = circuit_footprint(first)
                fp["job_id"] = jid
                fp["n_circuits_in_job"] = len(circuits)
                all_touched.update(fp["touched_physical_qubits"])
                report["jobs"].append(fp)
                print(
                    f"  {jid}: touched={fp['touched_physical_qubits']} "
                    f"meas={fp['measure_clbit_to_physical_qubit']} depth={fp['depth']} "
                    f"2q={fp['two_qubit_ops']}"
                )
            except Exception as exc:
                report["jobs"].append({"job_id": jid, "error": f"{type(exc).__name__}: {exc}"})
                print(f"  {jid}: ERROR {exc}")

        report["union_touched_qubits"] = sorted(all_touched)
        out = results_path.parent / "pw_ibm_actual_layouts.json"
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"  -> {out}")
        print(f"  UNION of touched qubits: {sorted(all_touched)}")


if __name__ == "__main__":
    main()
