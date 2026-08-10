#!/usr/bin/env python3
"""Pick a backend by CURRENT queue depth, not by memory. Consumes no QPU time.

Open-plan jobs that sit pending for more than a few minutes often never get
scheduled, so the cheapest thing to do before spending trial seconds is ask
every operational backend how deep its queue is right now.

IBM-10 needs only 3 qubits, so ANY operational device can run it -- the
156-qubit Heron constraint that applied to earlier runs does not apply here.
The conjunction it certifies is self-contained within one job, so whichever
device runs it is scientifically fine; a device other than ibm_marrakesh would
additionally give cross-device evidence for the conjunction.

Usage:
    python pw_ibm_queue_check.py
    python pw_ibm_queue_check.py --min-qubits 3
"""

from __future__ import annotations

import argparse
import os


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-qubits", type=int, default=3,
                    help="smallest device that can hold the circuit (IBM-10 needs 3)")
    args = ap.parse_args()

    token = os.environ.get("QISKIT_IBM_TOKEN")
    if not token:
        raise SystemExit(
            "QISKIT_IBM_TOKEN is not set. Run this in the same shell where you set it:\n"
            '  PowerShell:  $env:QISKIT_IBM_TOKEN = "<token>"'
        )

    from qiskit_ibm_runtime import QiskitRuntimeService

    try:
        service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    except Exception:
        service = QiskitRuntimeService(token=token)

    rows = []
    for b in service.backends(operational=True, simulator=False):
        try:
            st = b.status()
            rows.append((st.pending_jobs, b.name, b.num_qubits,
                         getattr(st, "status_msg", "?")))
        except Exception as exc:                       # a backend can be flaky
            rows.append((10**9, b.name, getattr(b, "num_qubits", 0), f"ERR {exc}"))

    rows = [r for r in rows if r[2] >= args.min_qubits]
    rows.sort()

    if not rows:
        raise SystemExit("no operational backends visible on this instance")

    print(f"{'pending':>8}  {'backend':<20} {'qubits':>7}  status")
    print("-" * 58)
    for pending, name, nq, msg in rows:
        mark = "  <-- shortest queue" if (pending, name) == (rows[0][0], rows[0][1]) else ""
        shown = "ERR" if pending >= 10**9 else str(pending)
        print(f"{shown:>8}  {name:<20} {nq:>7}  {msg}{mark}")

    best = rows[0][1]
    print(f"\nShortest queue: {best}")
    print(f"  python pw_ibm10_single_state.py --backend {best} --fresh")


if __name__ == "__main__":
    main()
