#!/usr/bin/env python3
"""AQ-PAGE-WOOTTERS-IBM-16 -- the geometric phase as an entanglement METER.

THE INVERSION. Fifteen runs established that no quantity escapes the
entanglement budget. IBM-15 measured the geometric phase sitting on it. The
useful move is to stop asking the phase to be a shared clock and start using it
as an INSTRUMENT: because the trade-off is tight and quantitative, a measured
phase constrains the residual entanglement to a narrow interval.

WHY IT IS WORTH HARDWARE. The two constructions have COMPLEMENTARY sensitivity,
which neither paper on either phase has reason to have noticed:

    C       |dPhi_I/dC|   |dPhi_U/dC|    dC from 4000 shots (I / U)
    0.05      0.034         0.220         0.472 / 0.072
    0.51      0.343         1.382         0.050 / 0.013
    0.74      0.818         1.222         0.024 / 0.016
    0.97      3.553         0.521         0.007 / 0.048

  Uhlmann peaks at C = 0.587; interferometric at C = 0.970.

Each is best where the other is worst, so together they meter the whole range
at dC ~ 0.007-0.03 -- and each uses ONE ancilla setting pair (X, Y) against the
NINE settings a two-qubit tomographic reconstruction needs.

WHAT THIS IS NOT. It is not a channel-capacity result. Holevo bounds what can
be transmitted and nothing here touches that; the programme's own applied
section already closed that question. This is metrology and channel
diagnostics: the phase reports what happened to the entanglement, not more of
it than Holevo allows.

    python hardware/pw_ibm16_phase_as_meter.py --dry
    python hardware/pw_ibm16_phase_as_meter.py --submit --backend ibm_marrakesh
    python hardware/pw_ibm16_phase_as_meter.py --recover <job> --instance <crn>
"""

from __future__ import annotations

import argparse, json, os, pathlib, sys
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import ClassicalRegister
from qiskit.circuit.library import UnitaryGate

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pw_ibm15_two_geometric_phases as G15
from pw_ibm15_two_geometric_phases import (R, T, P, THETA_WORK, THETA_NULL,
                                           tilted, interf_exact, interf_gate,
                                           uhlmann_gate, holonomy)

# calibration grid, and a DISJOINT blind set the calibration never sees
CAL = tuple(np.arcsin(np.linspace(0.15, 0.95, 8)))
BLIND = tuple(np.arcsin(np.array([0.27, 0.52, 0.71, 0.88, 0.96])))
IDLE_US = (0, 20, 40)             # REAL idle, microseconds (T2 ~ 100us)
SHOTS = 4000


def base(chi, th, idle=0):
    qc = QuantumCircuit(3)
    qc.ry(chi, T)
    qc.cx(T, P)
    qc.ry(th, T)
    if idle:
        # REAL idle time. X-X pairs were the first attempt and were useless:
        # the transpiler cancels them, and even uncancelled they are nanoseconds
        # against a ~100 us T2. A delay is not optimised away and actually
        # decoheres, which is the whole point of the arm.
        qc.barrier()
        qc.delay(idle, T, unit="us")
        qc.delay(idle, P, unit="us")
        qc.barrier()
    qc.h(R)
    return qc


PAULI2 = [a + b for a in "XYZ" for b in "XYZ"]


def tomo_circuit(chi, th, idle, setting):
    """Direct 2-qubit tomography on (T, P) -- measures the TRUE concurrence,
    which the phase cannot see under dephasing."""
    qc = base(chi, th, idle)
    qc.data = [d for d in qc.data if d.operation.name != "h"
               or qc.find_bit(d.qubits[0]).index != R]      # no interferometer
    for q, b in zip((T, P), setting):
        if b == "X":
            qc.h(q)
        elif b == "Y":
            qc.sdg(q); qc.h(q)
    qc.add_register(ClassicalRegister(3, "c"))
    qc.measure(range(3), range(3))
    return qc


def readout(qc, basis):
    if basis == "Y":
        qc.sdg(R)
    qc.h(R)
    qc.add_register(ClassicalRegister(3, "c"))
    qc.measure(range(3), range(3))
    return qc


def circuit(chi, th, arm, basis, idle=0, rng=None):
    qc = base(chi, th, idle)
    rho0 = tilted(abs(np.cos(chi)), th)
    if arm == "interf":
        qc.append(UnitaryGate(interf_gate(rho0, th), label="Upt").control(1), [R, T])
    elif arm == "uhlmann":
        qc.append(UnitaryGate(uhlmann_gate(rho0, chi, th), label="B").control(1), [R, P])
    elif arm == "random":
        z = (rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2))) / np.sqrt(2)
        q, rr = np.linalg.qr(z)
        qc.append(UnitaryGate(q @ np.diag(np.diag(rr) / np.abs(np.diag(rr))),
                              label="rand").control(1), [R, P])
    return readout(qc, basis)


def build_all():
    circs, idx = [], []
    rng = np.random.default_rng(16)
    for chi in CAL:                                  # A: calibration curve
        for arm in ("interf", "uhlmann"):
            for b in ("X", "Y"):
                circs.append(circuit(chi, THETA_WORK, arm, b))
                idx.append({"chi": float(chi), "set": "cal", "arm": arm,
                            "basis": b, "idle": 0})
    for chi in BLIND:                                # B: blind estimation
        for arm in ("interf", "uhlmann"):
            for b in ("X", "Y"):
                circs.append(circuit(chi, THETA_WORK, arm, b))
                idx.append({"chi": float(chi), "set": "blind", "arm": arm,
                            "basis": b, "idle": 0})
    chi_d = float(np.arcsin(0.70))                   # C: purity diagnostic
    for d in IDLE_US:
        for arm in ("interf", "uhlmann"):
            for b in ("X", "Y"):
                circs.append(circuit(chi_d, THETA_WORK, arm, b, idle=d))
                idx.append({"chi": chi_d, "set": "idle", "arm": arm,
                            "basis": b, "idle": d})
        for st in PAULI2:                            # TRUE C, for the same states
            circs.append(tomo_circuit(chi_d, THETA_WORK, d, st))
            idx.append({"chi": chi_d, "set": "tomo", "arm": "tomo",
                        "basis": st, "idle": d})
    for chi in CAL[::3]:                             # controls
        for b in ("X", "Y"):
            circs.append(circuit(chi, THETA_NULL, "interf", b))
            idx.append({"chi": float(chi), "set": "null", "arm": "interf",
                        "basis": b, "idle": 0})
            circs.append(circuit(chi, THETA_WORK, "random", b, rng=rng))
            idx.append({"chi": float(chi), "set": "rand", "arm": "random",
                        "basis": b, "idle": 0})
    return circs, idx


# --------------------------------------------------------------------------
# the meter
# --------------------------------------------------------------------------

def exact_phase(C, arm):
    r = float(np.sqrt(max(1 - C * C, 0.0)))
    if arm == "interf":
        return interf_exact(r, THETA_WORK)
    return holonomy(tilted(r, THETA_WORK))[1]


_CURVE_CACHE: dict = {}


def _curve(arm, n=400):
    """Calibration curve, computed ONCE per arm.

    Without this, invert() rebuilt a 400-point grid on every call and each
    Uhlmann point ran an 800-step SVD holonomy -- ~320k SVDs per inversion,
    which stalled the analysis for minutes and looked like a hang.
    """
    key = (arm, n)
    if key not in _CURVE_CACHE:
        grid = np.linspace(0.01, 0.995, n)
        _CURVE_CACHE[key] = (grid, np.array([exact_phase(c, arm) for c in grid]))
    return _CURVE_CACHE[key]


def invert(phase, arm, grid=None):
    """Read C off the calibration curve -- the meter, used in anger."""
    g, pred = _curve(arm)
    return float(g[int(np.argmin(np.abs(pred - phase)))])


def sensitivity_table():
    grid = np.linspace(0.05, 0.97, 25)
    out = {}
    for arm in ("interf", "uhlmann"):
        ph = np.array([exact_phase(c, arm) for c in grid])
        out[arm] = (grid, np.abs(np.gradient(ph, grid)))
    return out


def preflight(verbose=True):
    assert abs(np.cos(np.pi * np.cos(THETA_WORK))) > 0.5, "working theta degenerate"
    assert abs(np.cos(np.pi * np.cos(THETA_NULL))) < 1e-9, "null theta not degenerate"
    s = sensitivity_table()
    gi, si = s["interf"]; gu, su = s["uhlmann"]
    # the meter is only worth running if the two arms are COMPLEMENTARY
    assert gi[int(np.argmax(si))] > 0.85, "interferometric peak not at high C"
    assert 0.4 < gu[int(np.argmax(su))] < 0.8, "Uhlmann peak not mid-range"
    # blind set must be disjoint from calibration
    assert not (set(np.round(np.sin(CAL), 3)) & set(np.round(np.sin(BLIND), 3))), \
        "blind set overlaps calibration"
    if verbose:
        print("PREFLIGHT\n")
        print(f"  degeneracy   work {abs(np.cos(np.pi*np.cos(THETA_WORK))):.4f} > 0.5"
              f"   null {abs(np.cos(np.pi*np.cos(THETA_NULL))):.1e} = 0   PASS")
        print(f"  peaks        interferometric at C = {gi[int(np.argmax(si))]:.3f}"
              f"   Uhlmann at C = {gu[int(np.argmax(su))]:.3f}   COMPLEMENTARY")
        print(f"  blind set    {np.round(np.sin(BLIND),2).tolist()} disjoint from "
              f"calibration  PASS\n")
        print("   C      |dPhi_I/dC|  |dPhi_U/dC|   dC @4000 shots (I / U)")
        for i in range(0, 25, 4):
            c = gi[i]
            r = np.sqrt(1 - c * c)
            V = abs(np.cos(np.pi * np.cos(THETA_WORK))
                    + 1j * r * np.sin(np.pi * np.cos(THETA_WORK)))
            d = 1 / (V * np.sqrt(SHOTS))
            print(f"  {c:.3f}    {si[i]:7.3f}     {su[i]:7.3f}      "
                  f"{d/max(si[i],1e-9):.4f} / {d/max(su[i],1e-9):.4f}")
        print()
    return {"sens": s}


# --------------------------------------------------------------------------
# analysis
# --------------------------------------------------------------------------

SIG = {"X": np.array([[0, 1], [1, 0]], dtype=complex),
       "Y": np.array([[0, -1j], [1j, 0]], dtype=complex),
       "Z": np.diag([1, -1]).astype(complex),
       "I": np.eye(2, dtype=complex)}


def _expect(counts, qs):
    tot = sum(counts.values()); a = 0
    for bits, n in counts.items():
        b = bits.replace(" ", "")
        par = sum(int(b[len(b) - 1 - q]) for q in qs) % 2
        a += (1 - 2 * par) * n
    return a / max(tot, 1)


def concurrence_from_tomo(by_setting):
    """True concurrence of (T, P) from 9-setting Pauli tomography."""
    rho = np.eye(4, dtype=complex) / 4
    for i, pa in enumerate("IXYZ"):
        for j, pb in enumerate("IXYZ"):
            if pa == "I" and pb == "I":
                continue
            hit = next((st for st in by_setting
                        if (pa == "I" or st[0] == pa) and (pb == "I" or st[1] == pb)), None)
            if hit is None:
                continue
            qs = tuple(q for q, lab in ((T, pa), (P, pb)) if lab != "I")
            rho = rho + _expect(by_setting[hit], qs) * np.kron(SIG[pb], SIG[pa]) / 4
    w, v = np.linalg.eigh((rho + rho.conj().T) / 2)
    rho = (v * np.clip(w, 0, None)) @ v.conj().T
    rho = rho / np.trace(rho)
    YY = np.kron(SIG["Y"], SIG["Y"])
    ev = np.sqrt(np.clip(np.linalg.eigvals(rho @ YY @ rho.conj() @ YY).real, 0, None))
    ev = np.sort(ev)[::-1]
    return float(max(0.0, ev[0] - ev[1] - ev[2] - ev[3]))


def anc(counts):
    tot = sum(counts.values()); a = 0
    for bits, n in counts.items():
        b = bits.replace(" ", "")
        a += (1 - 2 * int(b[len(b) - 1 - R])) * n
    return a / max(tot, 1)


def analyze(raw, verbose=True):
    idx, counts = raw["index"], raw["counts"]
    got = {}
    for r_, c in zip(idx, counts):
        k = (round(r_["chi"], 6), r_["set"], r_["arm"], r_["idle"])
        got.setdefault(k, {})[r_["basis"]] = anc(c)
    meas = {}
    for k, d in got.items():
        if "X" in d and "Y" in d:
            z = complex(d["X"], d["Y"])
            meas[k] = {"phase": float(np.angle(z)), "vis": float(abs(z))}

    out = {"job_ids": raw.get("job_ids", []), "backend": raw.get("backend"),
           "blind": [], "idle": [], "cal": []}

    for k, v in sorted(meas.items()):
        chi, st, arm, idle = k
        C = abs(np.sin(chi))
        rec = {"C_true": C, "arm": arm, "idle": idle,
               "phase": v["phase"], "vis": v["vis"],
               "C_est": invert(v["phase"], arm) if arm in ("interf", "uhlmann") else None,
               "phase_exact": exact_phase(C, arm) if arm in ("interf", "uhlmann") else None}
        if st in out:
            out[st].append(rec)

    # GATE: blind estimation error, per arm, using the arm in its GOOD range
    berr = {}
    for arm in ("interf", "uhlmann"):
        e = [abs(r["C_est"] - r["C_true"]) for r in out["blind"] if r["arm"] == arm]
        berr[arm] = float(np.mean(e)) if e else float("nan")
    # best-of-two: pick the arm whose sensitivity is higher at the estimate
    best = []
    for r in out["blind"]:
        if r["arm"] != "interf":
            continue
        u = next((x for x in out["blind"]
                  if x["arm"] == "uhlmann" and abs(x["C_true"] - r["C_true"]) < 1e-9), None)
        if u is None:
            continue
        pick = r if r["C_true"] > 0.75 else u        # pre-registered split
        best.append(abs(pick["C_est"] - pick["C_true"]))
    best_err = float(np.mean(best)) if best else float("nan")

    idle_ph, idle_c = {}, {}
    for arm in ("interf", "uhlmann"):
        srt = sorted([r for r in out["idle"] if r["arm"] == arm],
                     key=lambda r: r["idle"])
        idle_ph[arm] = [(r["idle"], r["phase"], r["vis"]) for r in srt]
        idle_c[arm] = [(r["idle"], r["C_est"]) for r in srt]

    # TRUE concurrence per idle depth, from the tomography arm
    tomo_by_idle = {}
    for r_, c in zip(idx, counts):
        if r_["set"] == "tomo":
            tomo_by_idle.setdefault(r_["idle"], {})[r_["basis"]] = c
    c_true = {d: concurrence_from_tomo(v) for d, v in sorted(tomo_by_idle.items())}

    out["purity_diagnostic"] = [
        {"idle_us": d, "C_true_tomo": c_true.get(d),
         "C_est_interf": dict(idle_c["interf"]).get(d),
         "C_est_uhlmann": dict(idle_c["uhlmann"]).get(d),
         "gap": (dict(idle_c["uhlmann"]).get(d, 0) - c_true.get(d, 0))}
        for d in sorted(c_true)]

    out["gates"] = {
        "1_meter_calibrates": bool(np.mean(
            [abs(r["phase"] - r["phase_exact"]) for r in out["cal"]]) < 0.30),
        "2_blind_estimation": bool(best_err < 0.15),
        "3_complementary_beats_either": bool(
            best_err <= min(berr["interf"], berr["uhlmann"]) + 1e-9),
        # The meter must REPORT the decoherence, i.e. C_est must fall with idle
        # time, and both arms must agree on the fall. A phase-shift test was the
        # first version and was wrong: decoherence mainly costs visibility, and
        # what makes this a channel diagnostic is that the INFERRED C tracks it.
        # THE PURITY DIAGNOSTIC. Derived first, then gated: dephasing destroys
        # C while leaving rho_T diagonal and |r| UNCHANGED, so the phase cannot
        # see it (checked exactly: C 0.70 -> 0.14 with the phase fixed at
        # -0.7535). The meter reads r, and C_est = sqrt(1-r^2) is valid ONLY on
        # the pure-state manifold. So the GAP between C_est and tomographic C
        # is a mixedness witness -- which is the useful statement. An earlier
        # gate demanded C_est FALL with idle time; that was simply wrong.
        "4_purity_gap_opens": bool(
            len(c_true) > 1
            and list(c_true.values())[-1] < list(c_true.values())[0] - 0.05
            and abs(dict(idle_c["uhlmann"]).get(sorted(c_true)[-1], 0)
                    - dict(idle_c["uhlmann"]).get(sorted(c_true)[0], 0)) < 0.08),
    }
    out["blind_error"] = {"interf": berr["interf"], "uhlmann": berr["uhlmann"],
                          "best_of_two": best_err}
    out["all_gates_pass"] = all(out["gates"].values())

    if verbose:
        print("\nRESULTS -- the phase used as a meter\n")
        print("  BLIND ESTIMATION (calibration never saw these C values)")
        print("   C_true    arm         phase      C_est     |error|")
        for r in sorted(out["blind"], key=lambda r: (r["C_true"], r["arm"])):
            print(f"   {r['C_true']:.3f}    {r['arm']:<10}  {r['phase']:+.4f}   "
                  f"{r['C_est']:.3f}     {abs(r['C_est']-r['C_true']):.4f}")
        print(f"\n   mean |error|:  interferometric {berr['interf']:.4f}   "
              f"Uhlmann {berr['uhlmann']:.4f}   best-of-two {best_err:.4f}")
        print("\n  CHANNEL DIAGNOSTIC (same prepared state, real idle time)")
        print("   the meter must REPORT the entanglement loss")
        for arm in ("interf", "uhlmann"):
            row = "  ".join(f"{d}us: C_est={c:.3f}" for d, c in idle_c[arm])
            vis = " ".join(f"{v:.3f}" for _, _, v in idle_ph[arm])
            print(f"   {arm:<12} {row}      [V: {vis}]")
        if out.get("purity_diagnostic"):
            print("\n  PURITY DIAGNOSTIC -- the phase reads r, tomography reads C")
            print("   the GAP is the witness: it opens exactly as the state")
            print("   leaves the pure-state manifold\n")
            print("   idle    C_true (tomo)   C_est (phase)     gap")
            for r_ in out["purity_diagnostic"]:
                print(f"   {r_['idle_us']:>3}us      {r_['C_true_tomo']:.4f}"
                      f"          {r_['C_est_uhlmann']:.4f}         {r_['gap']:+.4f}")
        print("\n  GATES")
        for k, v in out["gates"].items():
            print(f"    {k:30s} {'PASS' if v else 'FAIL'}")
        print(f"\n  all gates pass: {out['all_gates_pass']}")
    return out


# --------------------------------------------------------------------------
# runners
# --------------------------------------------------------------------------

def run_dry(shots=SHOTS):
    from qiskit_aer import AerSimulator
    from qiskit_ibm_runtime.fake_provider import FakeMarrakesh
    preflight()
    fake = FakeMarrakesh()
    circs, idx = build_all()
    tq = transpile(circs, backend=fake, optimization_level=3, seed_transpiler=16,
                   scheduling_method="asap")
    n2 = [sum(n for g, n in c.count_ops().items()
              if g in ("cz", "cx", "ecr", "rzz")) for c in tq]
    print(f"FEASIBILITY  {len(circs)} circuits, {len(circs)*shots} shots, "
          f"est {len(circs)*shots/580000*156:.0f}s;  2Q max {max(n2)}\n")
    res = AerSimulator.from_backend(fake).run(tq, shots=shots).result()
    analyze({"index": idx, "counts": [res.get_counts(i) for i in range(len(tq))],
             "shots": shots, "backend": f"{fake.name} (noise)", "dry": True})


def _service(instance=None):
    from qiskit_ibm_runtime import QiskitRuntimeService
    kw = {"channel": "ibm_quantum_platform"}
    if instance or os.environ.get("QISKIT_IBM_INSTANCE"):
        kw["instance"] = instance or os.environ["QISKIT_IBM_INSTANCE"]
    if os.environ.get("QISKIT_IBM_TOKEN"):
        kw["token"] = os.environ["QISKIT_IBM_TOKEN"]
    return QiskitRuntimeService(**kw)


def run_submit(shots=SHOTS, backend_name=None, instance=None, force=False):
    from qiskit_ibm_runtime import SamplerV2
    if not os.environ.get("QISKIT_IBM_TOKEN"):
        sys.exit("QISKIT_IBM_TOKEN not set")
    preflight()
    svc = _service(instance)
    be = svc.backend(backend_name) if backend_name else svc.least_busy(
        operational=True, simulator=False, min_num_qubits=3)
    # ABORT, not warn. The first version stringified backend.status() and
    # silently matched nothing, so IBM-15 AND IBM-16's first submission both
    # went out during maintenance windows. BackendStatus exposes .operational
    # and .status_msg; use them, and stop by default.
    try:
        stobj = be.status()
        operational = bool(getattr(stobj, "operational", True))
        msg = str(getattr(stobj, "status_msg", "") or "")
    except Exception as exc:                       # never fail open silently
        operational, msg = True, f"status query failed: {exc}"
    if (not operational) or ("maintenance" in msg.lower()):
        print(f"  backend {be.name}: operational={operational}  status={msg!r}")
        if not force:
            sys.exit(
                "ABORTING: backend is not operational. IBM-15 was taken in a "
                "maintenance window and its archived calibration never matched "
                "the job, which made the numbers provisional. Pass --force to "
                "submit anyway, or choose another backend.")
        print("  --force given: submitting into a maintenance window anyway.")
    circs, idx = build_all()
    tq = transpile(circs, backend=be, optimization_level=3, seed_transpiler=16,
                   scheduling_method="asap")
    print(f"backend {be.name}: {len(circs)} circuits, "
          f"est {len(circs)*shots/580000*156:.0f}s")
    job = SamplerV2(mode=be).run(tq, shots=shots)
    print(f"job {job.job_id()} submitted")
    res = job.result()
    lay = set()
    for c in tq:
        try:
            lay.update(c.layout.final_index_layout()[:3])
        except Exception:
            pass
    raw = {"index": idx, "counts": [r.data.c.get_counts() for r in res],
           "shots": shots, "backend": be.name, "job_ids": [job.job_id()],
           "layouts": {"3": sorted(lay)}, "layout": sorted(lay)}
    pathlib.Path("results_ibm16").mkdir(exist_ok=True)
    pathlib.Path("results_ibm16/raw.json").write_text(json.dumps(raw, indent=1))
    out = analyze(raw)
    pathlib.Path("results_ibm16/ibm16_results.json").write_text(json.dumps(out, indent=1))
    print("\nwrote results_ibm16/raw.json and ibm16_results.json")


def run_status(instance=None):
    """List backend status without submitting anything. Zero QPU cost.

    Exists because the maintenance guard was broken and two runs went out into
    maintenance windows before anyone looked.
    """
    svc = _service(instance)
    print(f"{'backend':18s} {'operational':>12s}  {'pending':>8s}  status")
    # NOT operational=False -- that FILTERS TO non-operational backends and
    # returned an empty list. Passing nothing lists everything.
    try:
        backends = svc.backends(simulator=False)
    except Exception:
        backends = svc.backends()
    if not backends:
        print("  (no backends returned -- check the instance/CRN)")
    for be in backends:
        try:
            st = be.status()
            op = bool(getattr(st, "operational", False))
            msg = str(getattr(st, "status_msg", "") or "")
            pend = getattr(st, "pending_jobs", "?")
        except Exception as exc:
            op, msg, pend = False, f"query failed: {exc}", "?"
        flag = "OK" if op and "maintenance" not in msg.lower() else "AVOID"
        print(f"{be.name:18s} {str(op):>12s}  {str(pend):>8s}  {msg}   [{flag}]")


def run_recover(job_id, instance=None, shots=SHOTS):
    svc = _service(instance)
    if str(job_id).lower() in ("latest", "last"):
        # The terminal keeps dying mid-run and job IDs get truncated in the
        # console, so allow recovery without one. Picks the most recent job
        # whose pub count matches this experiment, which also guards against
        # grabbing a different run's data.
        want = len(build_all()[1])
        cand = None
        for j in svc.jobs(limit=25, descending=True):
            try:
                if str(j.status()).upper().endswith("DONE") and len(j.result()) == want:
                    cand = j
                    break
            except Exception:
                continue
        if cand is None:
            sys.exit(f"no recent completed job with {want} pubs found")
        job = cand
        job_id = job.job_id()
        print(f"resolved latest matching job: {job_id}")
    else:
        job = svc.job(job_id)
    print(f"job {job_id}: {job.status()}")
    counts = []
    for pub in job.result():
        d = pub.data
        reg = getattr(d, "c", None) or getattr(d, [n for n in dir(d)
                                                   if not n.startswith("_")][0])
        counts.append(reg.get_counts())
    _, idx = build_all()
    if len(idx) != len(counts):
        sys.exit(f"index/pub mismatch: {len(idx)} vs {len(counts)}")
    lay = set()
    try:
        for pub in (job.inputs.get("pubs") or []):
            c = pub[0] if isinstance(pub, (list, tuple)) else pub
            lay.update(c.layout.final_index_layout()[:3])
    except Exception:
        pass
    bk = getattr(job, "backend", None)
    raw = {"index": idx, "counts": counts, "shots": shots,
           "backend": bk().name if callable(bk) else str(bk),
           "job_ids": [job_id], "layouts": {"3": sorted(lay)}, "layout": sorted(lay)}
    pathlib.Path("results_ibm16").mkdir(exist_ok=True)
    pathlib.Path("results_ibm16/raw.json").write_text(json.dumps(raw, indent=1))
    print(f"  recovered {len(counts)} pubs, layout {sorted(lay)}")
    out = analyze(raw)
    pathlib.Path("results_ibm16/ibm16_results.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--submit", action="store_true")
    ap.add_argument("--analyze")
    ap.add_argument("--recover")
    ap.add_argument("--instance")
    ap.add_argument("--backend")
    ap.add_argument("--shots", type=int, default=SHOTS)
    ap.add_argument("--status", action="store_true",
                    help="list backend status, submit nothing")
    ap.add_argument("--force", action="store_true",
                    help="submit even if the backend is not operational")
    a = ap.parse_args()
    if a.status:
        run_status(a.instance)
    elif a.recover:
        run_recover(a.recover, instance=a.instance, shots=a.shots)
    elif a.analyze:
        _raw = json.loads(pathlib.Path(a.analyze).read_text())
        _out = analyze(_raw)
        # --analyze used to print without writing, so a re-analysis silently
        # left the PREVIOUS run's results file on disk and the two runs got
        # confused when archived.
        _dest = pathlib.Path(a.analyze).with_name("ibm16_results.json")
        _dest.write_text(json.dumps(_out, indent=1))
        print()
        print(f"wrote {_dest}")
    elif a.submit:
        run_submit(shots=a.shots, backend_name=a.backend, instance=a.instance,
                   force=a.force)
    elif a.dry:
        run_dry(shots=a.shots)
    else:
        preflight()
        c, _ = build_all()
        print(f"{len(c)} circuits, {len(c)*SHOTS} shots, "
              f"est {len(c)*SHOTS/580000*156:.0f}s")
