#!/usr/bin/env python3
"""Retrieve and archive RAW COUNTS for completed IBM runs. Consumes no QPU time.

WHY THIS EXISTS. IBM-0 archived its raw counts (pw_ibm_counts_nclock*.json) and
every IBM-0 analysis reproduces from them with no IBM account. That discipline
was NOT carried forward: IBM-1 through IBM-10 archived pre-registrations,
derived results and provenance -- but not the counts themselves. The gap was
found while trying to bootstrap the IBM-4/IBM-10 fidelity confidence intervals
and discovering there was nothing local to resample.

The counts are still recoverable from IBM's servers via the archived job IDs,
so this is fixable -- but ONLY while the account that submitted them is alive.
The trial expires ~2026-09-02. After that the raw data is gone permanently and
those runs become reproducible only from derived numbers, which is a materially
weaker archive.

Counts are stored in SUBMISSION ORDER per job, which is the order the run
script built its circuit list. Each run's analysis knows that order; for
IBM-10 it is documented in the file it writes.

Usage:
    python pw_ibm_fetch_counts.py --results results_ibm10_ibm_marrakesh/ibm10_results.json
    python pw_ibm_fetch_counts.py --all          # every results_ibm*/ dir found
"""

from __future__ import annotations

import argparse
import glob
import json
import os
from pathlib import Path


def fetch_for(service, results_path: Path) -> dict | None:
    results = json.loads(results_path.read_text(encoding="utf-8"))
    job_ids = results.get("job_ids", [])
    if not job_ids:
        print(f"  [skip] no job_ids in {results_path.name}")
        return None

    out = {"source_results": str(results_path), "backend": results.get("backend"),
           "note": ("Counts in circuit-submission order per job -- the order the run "
                    "script built its circuit list. Retrieved post-hoc from IBM via "
                    "archived job IDs; no QPU time consumed."),
           "jobs": []}
    for jid in job_ids:
        rec: dict = {"job_id": jid}
        try:
            job = service.job(jid)
            rec["status"] = str(job.status())
            res = job.result()
            counts = []
            for i in range(len(res)):
                data = res[i].data
                creg = next(iter(data.__dict__)) if hasattr(data, "__dict__") else None
                # SamplerV2: data has one attribute per classical register
                for name in (creg, "c", "meas"):
                    if name and hasattr(data, name):
                        counts.append(getattr(data, name).get_counts())
                        break
                else:
                    counts.append({"_error": "could not locate classical register"})
            rec["n_circuits"] = len(counts)
            rec["counts"] = counts
            print(f"  {jid}  {rec['status']}  {len(counts)} circuits")
        except Exception as exc:                       # noqa: BLE001
            rec["error"] = f"{type(exc).__name__}: {exc}"
            print(f"  {jid}  ERROR {rec['error']}")
        out["jobs"].append(rec)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", type=Path, default=None)
    ap.add_argument("--all", action="store_true",
                    help="process every results_ibm*/*_results.json found")
    args = ap.parse_args()

    token = os.environ.get("QISKIT_IBM_TOKEN")
    if not token:
        raise SystemExit(
            "QISKIT_IBM_TOKEN is not set. Run this in the same shell where you set it:\n"
            '  PowerShell:  $env:QISKIT_IBM_TOKEN = "<token>"'
        )

    targets: list[Path] = []
    if args.all:
        targets = [Path(p) for p in sorted(glob.glob("results_ibm*/*_results.json"))]
    elif args.results:
        targets = [args.results]
    else:
        raise SystemExit("pass --results <file> or --all")

    from qiskit_ibm_runtime import QiskitRuntimeService
    try:
        service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    except Exception:
        service = QiskitRuntimeService(token=token)

    ok = 0
    for t in targets:
        print(f"\n{t}")
        payload = fetch_for(service, t)
        if payload is None:
            continue
        out = t.parent / (t.stem.replace("_results", "") + "_counts.json")
        out.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        n = sum(j.get("n_circuits", 0) for j in payload["jobs"])
        print(f"  -> {out}  ({n} circuits total)")
        ok += 1
    print(f"\n[DONE] {ok}/{len(targets)} runs archived")


if __name__ == "__main__":
    main()
