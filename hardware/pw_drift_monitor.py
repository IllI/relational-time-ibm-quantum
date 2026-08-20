#!/usr/bin/env python3
"""Per-qubit drift monitor -- NEGATIVE RESULT. It does not work.

VERDICT FIRST. Validated against the one labelled matched pair available --
IBM-16 run 1 in a maintenance window and run 2 not, same script, same 103
circuits -- the monitor CANNOT TELL THEM APART:

    ibm16  MAINTENANCE   consistency 12.63   max|slope| 0.10601
    ibm16b operational   consistency 10.66   max|slope| 0.10797

By slope magnitude the OPERATIONAL run drifts slightly more. An earlier
--compare run appeared to separate maintenance from operational, but that was
driven entirely by including ibm13c, a different experiment with 174
tomography-heavy circuits, so the statistic was comparing circuit structure
rather than device health. Confounded, not evidence.

WHY, and it is probably physics rather than a bad statistic. These jobs run for
about two minutes. "Maintenance" does not mean the qubits drift DURING that
window -- it means the archived CALIBRATION is stale or mismatched. IBM-15's
snapshot post-dated its job by three hours. There may simply be no within-run
drift to detect, in which case no monitor of this kind can help.

THE RIGHT INSTRUMENT for the actual failure is a timestamp comparison, not a
learned model: check that the calibration snapshot brackets the job. That is
provenance_freshness() below, and it is four lines.

Kept rather than deleted because the negative is the useful part: it says where
NOT to spend effort, and the same statistic tuned until it separated would have
been exactly the failure mode that produced this programme's retraction.

--- original intent, unchanged below ---

Per-qubit drift monitor -- instrumentation, NOT a witness.

WHAT THIS IS FOR. IBM-15 and IBM-16 are both provisional because they ran in
maintenance windows and their archived calibration never described the device.
Nothing in either run could tell, at the time, that anything was wrong. This
watches each qubit's marginal across a run's circuit list and flags one that
drifts out of family -- mid-run, not hours later in provenance.

WHAT THIS IS NOT. It does not certify anything and must never enter a
certification chain. A learned or fitted model has no separable bound, and this
programme has three runs showing what happens to observables that lack one:
IBM-2 (a zero-entanglement product state scored 4.2x higher than the history
state), IBM-3 (a separable mixture scored 1.7x higher on the joint witness built
to fix it), and the two-line theorem that generalises both. Certification stays
with the multi-setting fidelity witness and its proven bound lambda_max.

It is also why a per-qubit learner cannot substitute for the witness: on
IBM-17's own ladder the per-qubit marginals are IDENTICAL from C = 0.85 down to
C = 0, so a per-qubit layer sees the same data at every rung and an observer
over it has nothing to aggregate.

THE SIGNAL. For each qubit, P(outcome 1) is regressed against circuit position
WITHIN each matched configuration group, so legitimate circuit-to-circuit
variation is differenced away and only a systematic trend survives. A drifting
qubit shows a consistent nonzero slope across groups.

    python hardware/pw_drift_monitor.py results/hardware/ibm16/raw.json
    python hardware/pw_drift_monitor.py --compare
"""

from __future__ import annotations

import argparse, json, pathlib, sys
import numpy as np


def per_circuit_p1(counts, nq):
    """P(qubit == 1) for every qubit, from one circuit's counts."""
    tot = sum(counts.values())
    p = np.zeros(nq)
    for bits, n in counts.items():
        b = bits.replace(" ", "")
        for q in range(nq):
            if q < len(b) and b[len(b) - 1 - q] == "1":
                p[q] += n
    return p / max(tot, 1)


def group_key(rec):
    """Circuits that should behave identically apart from device drift."""
    if not isinstance(rec, dict):
        return ("all",)
    return tuple(str(rec.get(k)) for k in ("set", "arm", "basis", "block")
                 if rec.get(k) is not None) or ("all",)


def drift_report(raw, verbose=True):
    counts = raw["counts"]
    idx = raw.get("index") or [{} for _ in counts]
    nq = max(len(next(iter(c)).replace(" ", "")) for c in counts if c)
    p1 = np.array([per_circuit_p1(c, nq) for c in counts])

    groups = {}
    for i, rec in enumerate(idx):
        groups.setdefault(group_key(rec), []).append(i)

    # slope of P(1) against position within each group, aggregated per qubit
    slopes = {q: [] for q in range(nq)}
    for _, ii in groups.items():
        if len(ii) < 4:                       # too short to see a trend
            continue
        x = np.arange(len(ii), dtype=float)
        x = (x - x.mean()) / max(x.std(), 1e-9)
        for q in range(nq):
            y = p1[ii, q]
            if y.std() < 1e-12:
                continue
            slopes[q].append(float(np.polyfit(x, y, 1)[0]))

    out = {"n_qubits": nq, "n_circuits": len(counts),
           "backend": raw.get("backend"), "layout": raw.get("layout"),
           "job_ids": raw.get("job_ids"), "qubits": []}
    for q in range(nq):
        s = np.array(slopes[q]) if slopes[q] else np.array([0.0])
        # a drifting qubit trends the SAME way in every group; noise does not
        consistency = float(abs(s.mean()) / max(s.std(), 1e-9)) if len(s) > 1 else 0.0
        out["qubits"].append({"qubit": q, "n_groups": len(slopes[q]),
                              "mean_slope": float(s.mean()),
                              "slope_sd": float(s.std()),
                              "consistency": consistency})
    out["drift_score"] = float(max(x["consistency"] for x in out["qubits"]))
    out["worst_qubit"] = int(max(out["qubits"], key=lambda x: x["consistency"])["qubit"])

    if verbose:
        print(f"  {raw.get('backend')}  {len(counts)} circuits  "
              f"layout {raw.get('layout')}")
        print("   qubit   groups   mean slope    sd       consistency")
        for x in out["qubits"]:
            flag = "  <- drifting" if x["consistency"] > 2.0 else ""
            print(f"     {x['qubit']}       {x['n_groups']:>3}     "
                  f"{x['mean_slope']:+.5f}   {x['slope_sd']:.5f}    "
                  f"{x['consistency']:.2f}{flag}")
        print(f"   drift score (max consistency): {out['drift_score']:.2f}"
              f"   worst qubit {out['worst_qubit']}")
    return out


def compare():
    """Validate against the one labelled pair we have: IBM-16 run 1 ran in a
    maintenance window, run 2 did not. If the monitor is worth anything it
    should say so without being told."""
    base = pathlib.Path("results/hardware")
    cases = [("ibm16  (MAINTENANCE)", base / "ibm16" / "raw.json"),
             ("ibm16b (operational)", base / "ibm16b" / "raw.json"),
             ("ibm15  (MAINTENANCE)", base / "ibm15" / "raw.json"),
             ("ibm13c (operational)", base / "ibm13c" / "raw.json")]
    print("VALIDATION -- does the monitor separate known-bad from known-good?\n")
    rows = []
    for label, path in cases:
        if not path.exists():
            print(f"  {label:22s} (missing {path})")
            continue
        r = drift_report(json.loads(path.read_text()), verbose=False)
        rows.append((label, r["drift_score"], r["worst_qubit"], r["n_circuits"]))
        print(f"  {label:22s} drift score {r['drift_score']:6.2f}   "
              f"worst qubit {r['worst_qubit']}   ({r['n_circuits']} circuits)")
    mt = [s for l, s, _, _ in rows if "MAINT" in l]
    op = [s for l, s, _, _ in rows if "operational" in l]
    if mt and op:
        print(f"\n  mean drift score:  maintenance {np.mean(mt):.2f}   "
              f"operational {np.mean(op):.2f}")
        if np.mean(mt) > np.mean(op):
            print("  -> separates them in the right direction.")
        else:
            print("  -> DOES NOT separate them. The monitor is not earning its")
            print("     place on this evidence and should not be trusted to")
            print("     flag a bad run. Reported rather than tuned away.")
    return rows


def provenance_freshness(prov_path, raw_path=None):
    """Does the archived calibration actually describe the job?

    This is the check that would have caught IBM-15 and IBM-16 at the time.
    IBM-15's snapshot carried last_update 2026-08-19T00:27:30-05:00 for a job
    that ran at 2026-08-18T21:34 -- three hours later, across a maintenance
    window, so the calibration described a different device.
    """
    from datetime import datetime

    def parse(t):
        try:
            return datetime.fromisoformat(str(t).replace("Z", "+00:00"))
        except Exception:
            return None

    prov = json.loads(pathlib.Path(prov_path).read_text())
    cal = prov.get("calibration") or {}
    cal_t = parse(cal.get("last_update_date") or cal.get("last_update"))
    rows = []
    for j in prov.get("jobs", []):
        ts = ((j.get("metrics") or {}).get("timestamps") or {})
        job_t = parse(ts.get("created") or ts.get("running"))
        if cal_t is None or job_t is None:
            rows.append((j.get("job_id"), None, "timestamps unavailable"))
            continue
        dt = (cal_t - job_t).total_seconds() / 3600.0
        verdict = ("calibration POST-DATES the job" if dt > 0.5 else
                   "stale by more than a day" if dt < -24 else "brackets the job")
        rows.append((j.get("job_id"), dt, verdict))
    print(f"  {pathlib.Path(prov_path).parent.name}")
    for jid, dt, v in rows:
        d = f"{dt:+.1f} h" if dt is not None else "  n/a "
        flag = "  <- UNUSABLE for noise modelling" if dt is not None and dt > 0.5 else ""
        print(f"    {jid}   cal - job = {d}   {v}{flag}")
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?")
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--freshness", help="provenance json: does the cal match the job?")
    a = ap.parse_args()
    if a.freshness:
        provenance_freshness(a.freshness)
    elif a.compare:
        compare()
    elif a.path:
        drift_report(json.loads(pathlib.Path(a.path).read_text()))
    else:
        sys.exit("give an archived raw.json, or --compare")
