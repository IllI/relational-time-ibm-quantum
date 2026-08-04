#!/usr/bin/env python3
"""AQ-PAGE-WOOTTERS-IBM-0 -- provenance capture.

Pulls server-side job metadata and the backend calibration snapshot for the
12 jobs of the 2026-08-03 hardware run and writes them into the local archive.

Why this is time-critical: the raw counts are already saved locally and the
whole analysis reproduces from them, but job timestamps, per-job usage, and
the device calibration at time of run live only on IBM's servers. The account
is a trial that expires ~2026-09-01, so this metadata should be captured well
before then. Server-side timestamps are the authoritative record for
chronology (a lesson carried from the OAT PTM archive, where local session
dates proved unreliable).

Run in the same shell where QISKIT_IBM_TOKEN is set:

    python pw_ibm_provenance.py

Reads job IDs from results_page_wootters_ibm0/pw_ibm_results.json by default.
Writes results_page_wootters_ibm0/pw_ibm_provenance.json. Never overwrites
counts or results; purely additive.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

OUT_DIR = Path("results_page_wootters_ibm0")


def jsonable(value):
    """Best-effort conversion of qiskit/date objects to JSON-safe values."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    for attr in ("isoformat", "to_dict"):
        if hasattr(value, attr):
            try:
                return jsonable(getattr(value, attr)())
            except Exception:
                pass
    return str(value)


def capture_job(service, job_id: str) -> dict:
    record: dict = {"job_id": job_id}
    try:
        job = service.job(job_id)
    except Exception as exc:  # expired, purged, or wrong account
        record["error"] = f"{type(exc).__name__}: {exc}"
        return record

    for field, getter in (
        ("status", lambda: str(job.status())),
        ("backend", lambda: job.backend().name),
        ("creation_date", lambda: job.creation_date),
        ("metrics", lambda: job.metrics()),
        ("usage_estimation", lambda: getattr(job, "usage_estimation", None)),
        ("program_id", lambda: getattr(job, "program_id", None)),
        ("tags", lambda: getattr(job, "tags", None)),
        ("session_id", lambda: getattr(job, "session_id", None)),
    ):
        try:
            record[field] = jsonable(getter())
        except Exception as exc:
            record[f"{field}_error"] = f"{type(exc).__name__}: {exc}"
    return record


def capture_calibration(service, backend_name: str, qubits: list[int]) -> dict:
    """Snapshot T1/T2/readout error for the physical qubits actually used,
    plus two-qubit gate errors on the edges between them."""
    snapshot: dict = {"backend": backend_name, "qubits_of_interest": qubits}
    try:
        backend = service.backend(backend_name)
    except Exception as exc:
        snapshot["error"] = f"{type(exc).__name__}: {exc}"
        return snapshot

    try:
        snapshot["num_qubits"] = backend.num_qubits
        snapshot["processor_type"] = jsonable(getattr(backend, "processor_type", None))
    except Exception:
        pass

    # Preferred path: BackendProperties (has last_update_date = calibration time).
    try:
        props = backend.properties()
        if props is not None:
            snapshot["last_update_date"] = jsonable(props.last_update_date)
            per_qubit = {}
            for q in qubits:
                entry = {}
                for name in ("T1", "T2", "frequency", "readout_error",
                             "prob_meas0_prep1", "prob_meas1_prep0"):
                    try:
                        entry[name] = props.qubit_property(q, name)[0]
                    except Exception:
                        pass
                per_qubit[str(q)] = jsonable(entry)
            snapshot["qubit_properties"] = per_qubit

            gates = {}
            for gate in props.gates:
                if len(gate.qubits) == 2 and all(q in qubits for q in gate.qubits):
                    try:
                        gates[f"{gate.gate}_{'_'.join(map(str, gate.qubits))}"] = {
                            p.name: p.value for p in gate.parameters
                        }
                    except Exception:
                        pass
            snapshot["two_qubit_gate_errors"] = jsonable(gates)
    except Exception as exc:
        snapshot["properties_error"] = f"{type(exc).__name__}: {exc}"

    # Fallback: Target-derived qubit properties (newer backends).
    if "qubit_properties" not in snapshot:
        try:
            per_qubit = {}
            for q in qubits:
                qp = backend.qubit_properties(q)
                per_qubit[str(q)] = jsonable(
                    {"t1": getattr(qp, "t1", None),
                     "t2": getattr(qp, "t2", None),
                     "frequency": getattr(qp, "frequency", None)}
                )
            snapshot["qubit_properties_from_target"] = per_qubit
        except Exception as exc:
            snapshot["target_error"] = f"{type(exc).__name__}: {exc}"

    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=OUT_DIR / "pw_ibm_results.json")
    parser.add_argument("--out", type=Path, default=OUT_DIR / "pw_ibm_provenance.json")
    args = parser.parse_args()

    token = os.environ.get("QISKIT_IBM_TOKEN")
    if not token:
        raise SystemExit(
            "QISKIT_IBM_TOKEN is not set. Run this in the same shell where you set it:\n"
            '  PowerShell:  $env:QISKIT_IBM_TOKEN = "<token>"'
        )

    results = json.loads(args.results.read_text(encoding="utf-8"))
    job_ids = results.get("job_ids", [])
    backend_name = results.get("backend")
    layouts = results.get("layouts", {})
    qubits = sorted({q for chain in layouts.values() for q in chain})
    if not job_ids:
        raise SystemExit(f"no job_ids found in {args.results}")

    from qiskit_ibm_runtime import QiskitRuntimeService

    try:
        service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    except Exception:
        service = QiskitRuntimeService(token=token)

    print(f"Capturing provenance for {len(job_ids)} jobs on {backend_name}", flush=True)
    jobs = []
    for jid in job_ids:
        rec = capture_job(service, jid)
        flag = "ERR" if "error" in rec else rec.get("status", "?")
        print(f"  {jid}  {flag}", flush=True)
        jobs.append(rec)

    print(f"Capturing calibration snapshot for qubits {qubits}", flush=True)
    calibration = capture_calibration(service, backend_name, qubits)

    payload = {
        "program": "AQ-PAGE-WOOTTERS-IBM-0-PROVENANCE",
        "source_results": str(args.results),
        "backend": backend_name,
        "layouts": layouts,
        "jobs": jobs,
        "calibration": calibration,
        "note": (
            "Server-side timestamps are authoritative for chronology. Raw counts "
            "in pw_ibm_counts_nclock*.json remain the reproducible record and do "
            "not depend on this metadata."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    ok = sum(1 for j in jobs if "error" not in j)
    print(f"\n[DONE] {ok}/{len(jobs)} jobs captured -> {args.out}", flush=True)
    if ok < len(jobs):
        print("  Some jobs could not be retrieved; counts archive is unaffected.", flush=True)


if __name__ == "__main__":
    main()
