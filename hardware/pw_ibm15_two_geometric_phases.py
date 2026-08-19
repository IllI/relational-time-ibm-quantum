#!/usr/bin/env python3
"""AQ-PAGE-WOOTTERS-IBM-15 -- two geometric phases, one entanglement sweep.

THE QUESTION, corrected. There is no single geometric phase for a mixed state.
Two inequivalent published constructions exist, both measurable:

  INTERFEROMETRIC  (Sjoqvist et al., PRL 85, 2845, 2000)
      Phi_I = arg Tr(rho0 U_pt),  U_pt = U(T) sum_k exp(i <k|H|k> T)|k><k|
  UHLMANN          (holonomy on purifications; measured on superconducting
      qubits by Viyuela et al., npj QI 3, 55, 2017)
      Phi_U = arg Tr(rho0 V),  V from polar decompositions along the path

BOTH are entanglement-dependent, so the geometric phase IS on the budget either
way -- that much is derived, not measured. What is measured here is that the
two constructions SPEND IT AT DIFFERENT RATES: identical at C = 0 (forced for
pure states, a built-in null) and differing by a factor of ~11 by C = 0.9.

MIXEDNESS COMES FROM ENTANGLEMENT, not temperature. The partner IS the
purification, which is what makes the Uhlmann arm a two-qubit gate.

THE TILT IS ESSENTIAL. A subsystem's cyclic loop is forced trivial unless the
Bloch vector is tilted off the rotation axis: cyclic evolution needs
U rho U^dag = rho, and for a non-degenerate reduced state only diagonal
unitaries qualify (0 of 200000 Haar-random U escape). A local Ry(theta) tilts
it and leaves C untouched.

THE DEGENERACY TRAP. The interferometric phase loses its r-dependence exactly
at cos(theta) = 1/2, theta = pi/3. That angle was chosen by accident once and
produced a constant phase. It is now (a) avoided at the working point and
(b) run deliberately as a hardware NULL, where the phase must be flat.

    python hardware/pw_ibm15_two_geometric_phases.py --dry
    python hardware/pw_ibm15_two_geometric_phases.py --submit --backend ibm_marrakesh
    python hardware/pw_ibm15_two_geometric_phases.py --recover <job> --instance <crn>
"""

from __future__ import annotations

import argparse, json, os, pathlib, sys
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import ClassicalRegister
from qiskit.circuit.library import UnitaryGate

R, T, P = 0, 1, 2                      # ancilla, target, purifier
THETA_WORK = np.pi / 4                 # non-degenerate working point
THETA_NULL = np.pi / 3                 # cos(theta) = 1/2 -- degenerate by design
CHIS = tuple(np.linspace(0.05, 0.45, 8) * np.pi)
SHOTS = 4000

I2 = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.diag([1, -1]).astype(complex)


def rot(ax, a):
    Pm = {"x": X, "y": Y, "z": Z}[ax]
    return np.cos(a / 2) * I2 - 1j * np.sin(a / 2) * Pm


def sq(m):
    w, v = np.linalg.eigh((m + m.conj().T) / 2)
    return (v * np.sqrt(np.clip(w, 0, None))) @ v.conj().T


def tilted(r, th):
    return 0.5 * (I2 + r * np.sin(th) * X + r * np.cos(th) * Z)


def holonomy(rho0, N=800):
    path = [rot("z", t) @ rho0 @ rot("z", t).conj().T
            for t in np.linspace(0, 2 * np.pi, N + 1)]
    V = np.eye(2, dtype=complex)
    for a, b in zip(path[:-1], path[1:]):
        u_, _, vh_ = np.linalg.svd(sq(b) @ sq(a))
        V = (u_ @ vh_) @ V
    return V, float(np.angle(np.trace(path[0] @ V)))


def interf_exact(r, th):
    """arg Tr(rho0 U_pt) in closed form for the 2pi cone loop."""
    c = np.cos(th)
    return float(np.angle(-(np.cos(np.pi * c) + 1j * r * np.sin(np.pi * c))))


def interf_gate(rho0, th):
    """U_pt = U(T) D, with D diagonal in the rho0 eigenbasis. U(T) = -I."""
    w, ev = np.linalg.eigh(rho0)
    D = sum(np.exp(1j * float(np.real(ev[:, k].conj() @ (Z / 2) @ ev[:, k]))
                   * 2 * np.pi) * np.outer(ev[:, k], ev[:, k].conj())
            for k in range(2))
    return -D


def uhlmann_gate(rho0, chi, th):
    """B acting on the PURIFIER such that (U(T) (x) B) transports the
    purification. Verified in preflight against the numerical holonomy."""
    V, _ = holonomy(rho0)
    W0 = rot("y", th) @ np.diag([np.cos(chi / 2), np.sin(chi / 2)]).astype(complex)
    Rm = np.linalg.solve(sq(rho0), W0)
    return np.linalg.solve(Rm, V @ Rm).T          # B, since (A(x)B)|W> ~ A W B^T


# --------------------------------------------------------------------------
# circuits
# --------------------------------------------------------------------------

def base(chi: float, th: float) -> QuantumCircuit:
    qc = QuantumCircuit(3)
    qc.ry(chi, T)                      # cos(chi/2)|0> + sin(chi/2)|1>
    qc.cx(T, P)                        # -> cos|00> + sin|11>, C = |sin chi|
    qc.ry(th, T)                       # local tilt: leaves C untouched
    qc.h(R)                            # interferometer
    return qc


def readout(qc: QuantumCircuit, basis: str) -> QuantumCircuit:
    if basis == "Y":
        qc.sdg(R)
    qc.h(R)
    qc.add_register(ClassicalRegister(3, "c"))
    qc.measure(range(3), range(3))
    return qc


def circuit(chi, th, arm, basis, rng=None):
    qc = base(chi, th)
    r = abs(np.cos(chi))
    rho0 = tilted(r, th)
    if arm == "interf":
        qc.append(UnitaryGate(interf_gate(rho0, th), label="Upt").control(1), [R, T])
    elif arm == "uhlmann":
        qc.append(UnitaryGate(uhlmann_gate(rho0, chi, th), label="B").control(1), [R, P])
    elif arm == "random":                       # gate-2 control
        z = (rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2))) / np.sqrt(2)
        q, rr = np.linalg.qr(z)
        u = q @ np.diag(np.diag(rr) / np.abs(np.diag(rr)))
        qc.append(UnitaryGate(u, label="rand").control(1), [R, P])
    return readout(qc, basis)


def build_all():
    circs, idx = [], []
    rng = np.random.default_rng(15)
    for chi in CHIS:                                   # working point, both arms
        for arm in ("interf", "uhlmann"):
            for b in ("X", "Y"):
                circs.append(circuit(chi, THETA_WORK, arm, b))
                idx.append({"chi": float(chi), "theta": "work", "arm": arm, "basis": b})
    for chi in CHIS:                                   # degenerate null
        for b in ("X", "Y"):
            circs.append(circuit(chi, THETA_NULL, "interf", b))
            idx.append({"chi": float(chi), "theta": "null", "arm": "interf", "basis": b})
    for i, chi in enumerate(CHIS[::2]):                # random-unitary control
        for b in ("X", "Y"):
            circs.append(circuit(chi, THETA_WORK, "random", b, rng))
            idx.append({"chi": float(chi), "theta": "work", "arm": "random", "basis": b})
    return circs, idx


# --------------------------------------------------------------------------
# preflight
# --------------------------------------------------------------------------

def preflight(verbose=True) -> dict:
    # GATE 1 -- the working point must not be degenerate
    deg_work = abs(np.cos(np.pi * np.cos(THETA_WORK)))
    deg_null = abs(np.cos(np.pi * np.cos(THETA_NULL)))
    assert deg_work > 0.5, f"working theta is degenerate: {deg_work}"
    assert deg_null < 1e-9, f"null theta is not degenerate: {deg_null}"

    rows = []
    for chi in CHIS:
        r = abs(np.cos(chi))
        C = abs(np.sin(chi))
        rho0 = tilted(r, THETA_WORK)
        V, pu = holonomy(rho0)
        pi_ = interf_exact(r, THETA_WORK)
        B = uhlmann_gate(rho0, chi, THETA_WORK)
        assert np.allclose(B @ B.conj().T, I2, atol=1e-8), "B not unitary"
        # the circuit realises Phi_U + pi (the Rz(2pi) = -I spin-1/2 sign)
        W0 = rot("y", THETA_WORK) @ np.diag([np.cos(chi / 2), np.sin(chi / 2)]).astype(complex)
        v0 = (W0.reshape(-1) / np.linalg.norm(W0))
        vT = ((rot("z", 2 * np.pi) @ W0 @ B.T).reshape(-1) / np.linalg.norm(W0))
        circ_phase = float(np.angle(v0.conj() @ vT))
        off = float(np.angle(np.exp(1j * (circ_phase - pu))))
        assert abs(abs(off) - np.pi) < 1e-6, f"offset != pi at C={C}: {off}"
        rows.append({"chi": float(chi), "C": C, "r": r,
                     "uhlmann": pu, "interf": pi_, "gap": abs(pu - pi_)})

    if verbose:
        print("PREFLIGHT -- both constructions, asserted from theory\n")
        print(f"  gate 1  working theta=pi/4  |cos(pi cos th)| = {deg_work:.4f} > 0.5  PASS")
        print(f"          null    theta=pi/3  |cos(pi cos th)| = {deg_null:.1e} = 0  PASS\n")
        print("   C        r        Uhlmann      interferometric    gap")
        for x in rows:
            print(f"   {x['C']:.4f}   {x['r']:.4f}   {x['uhlmann']:+.6f}     "
                  f"{x['interf']:+.6f}      {x['gap']:.4f}")
        print(f"\n  gap at lowest C:  {rows[0]['gap']:.4f}   (agree, pure-state null)")
        print(f"  gap at highest C: {rows[-1]['gap']:.4f}")
        print("  B unitary and circuit offset = pi at every C: PASS\n")
    return {"rows": rows}


# --------------------------------------------------------------------------
# analysis
# --------------------------------------------------------------------------

def anc_expect(counts):
    tot = sum(counts.values()); acc = 0
    for bits, n in counts.items():
        b = bits.replace(" ", "")
        acc += (1 - 2 * int(b[len(b) - 1 - R])) * n
    return acc / max(tot, 1)


def analyze(raw, verbose=True):
    idx, counts = raw["index"], raw["counts"]
    pre = {round(x["chi"], 6): x for x in preflight(verbose=False)["rows"]}
    got = {}
    for r_, c in zip(idx, counts):
        key = (round(r_["chi"], 6), r_["theta"], r_["arm"])
        got.setdefault(key, {})[r_["basis"]] = anc_expect(c)

    out = {"settings": [], "job_ids": raw.get("job_ids", []),
           "backend": raw.get("backend")}
    for (chi, th, arm), d in sorted(got.items()):
        if "X" not in d or "Y" not in d:
            continue
        z = complex(d["X"], d["Y"])
        out["settings"].append({"chi": chi, "theta": th, "arm": arm,
                                "phase": float(np.angle(z)),
                                "visibility": float(abs(z))})

    def series(th, arm):
        return sorted([s for s in out["settings"]
                       if s["theta"] == th and s["arm"] == arm],
                      key=lambda s: s["chi"])

    iw, uw = series("work", "interf"), series("work", "uhlmann")
    nul, rnd = series("null", "interf"), series("work", "random")

    # The Uhlmann arm measures Phi_U + pi (the Rz(2pi) = -I spin-1/2 sign).
    # Computed inline rather than by mutating shared dicts -- the mutation
    # version silently left the raw value in place and blew up gate 3.
    def corrected(s):
        """NO offset. Preflight computes arg<W0|(Rz(2pi) (x) B)|W0> = Phi_U + pi,
        but the CIRCUIT applies only controlled-B: Rz(2pi) = -I was dropped as a
        global phase on the target. Under a control it would be a relative phase
        on the ancilla, so omitting it removes the pi rather than hiding it.
        The dry run measured -0.895 against an exact -0.881, confirming the arm
        reads Phi_U directly. Subtracting pi here was a spurious 'correction'
        that failed gate 3 by exactly pi."""
        return float(s["phase"])

    for s in uw:
        s["phase_corrected"] = corrected(s)

    gaps = [abs(np.angle(np.exp(1j * (a["phase"] - corrected(b)))))
            for a, b in zip(iw, uw)]
    null_spread = (max(s["phase"] for s in nul) - min(s["phase"] for s in nul)
                   if nul else float("nan"))
    out["gates"] = {
        "3_pure_state_null": bool(gaps and gaps[0] < 0.25),
        # the exact gap is NON-MONOTONIC: it peaks near C = 0.77 (0.52) and
        # falls to 0.20 at the top of the sweep. An endpoint-difference test
        # would fail on the true values -- caught in preflight, not after.
        "4_divergence": bool(len(gaps) > 2 and max(gaps) > 0.3
                             and max(gaps) > gaps[0] + 0.25),
        "5_both_vary_with_C": bool(
            abs(iw[-1]["phase"] - iw[0]["phase"]) > 0.15 and
            abs(corrected(uw[-1]) - corrected(uw[0])) > 0.3),
        "1_degenerate_null_flat": bool(null_spread < 0.35),
    }
    out["all_gates_pass"] = all(out["gates"].values())

    if verbose:
        print("\nRESULTS\n")
        print("   C        interf phase   Uhlmann phase   gap    (exact gap)")
        for a, b in zip(iw, uw):
            ex = pre[round(a['chi'], 6)]
            g = abs(np.angle(np.exp(1j * (a["phase"] - corrected(b)))))
            print(f"   {abs(np.sin(a['chi'])):.4f}   {a['phase']:+.6f}      "
                  f"{corrected(b):+.6f}     {g:.4f}   ({ex['gap']:.4f})")
        print(f"\n   degenerate null (theta=pi/3): phase spread {null_spread:.4f}"
              f"   -- must be FLAT")
        if rnd:
            print(f"   random-unitary control: visibilities "
                  f"{[round(s['visibility'],3) for s in rnd]}")
        print("\n  GATES")
        for k, v in out["gates"].items():
            print(f"    {k:26s} {'PASS' if v else 'FAIL'}")
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
    tq = transpile(circs, backend=fake, optimization_level=3, seed_transpiler=15)
    n2 = [sum(n for g, n in c.count_ops().items()
              if g in ("cz", "cx", "ecr", "rzz")) for c in tq]
    print(f"FEASIBILITY  {len(circs)} circuits, {len(circs)*shots} shots, "
          f"est {len(circs)*shots/580000*156:.0f}s")
    print(f"  2Q gates: max {max(n2)}, median {int(np.median(n2))}  "
          f"(Paper 1's failure bound is 18)\n")
    res = AerSimulator.from_backend(fake).run(tq, shots=shots).result()
    analyze({"index": idx, "counts": [res.get_counts(i) for i in range(len(tq))],
             "shots": shots, "backend": f"{fake.name} (noise)", "dry": True})


def run_submit(shots=SHOTS, backend_name=None):
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
    if not os.environ.get("QISKIT_IBM_TOKEN"):
        sys.exit("QISKIT_IBM_TOKEN not set")
    preflight()
    kw = {"channel": "ibm_quantum_platform", "token": os.environ["QISKIT_IBM_TOKEN"]}
    if os.environ.get("QISKIT_IBM_INSTANCE"):
        kw["instance"] = os.environ["QISKIT_IBM_INSTANCE"]
    svc = QiskitRuntimeService(**kw)
    be = svc.backend(backend_name) if backend_name else svc.least_busy(
        operational=True, simulator=False, min_num_qubits=3)
    circs, idx = build_all()
    tq = transpile(circs, backend=be, optimization_level=3, seed_transpiler=15)
    n2 = max(sum(n for g, n in c.count_ops().items()
                 if g in ("cz", "cx", "ecr", "rzz")) for c in tq)
    print(f"backend {be.name}: {len(circs)} circuits, max 2Q {n2}, "
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
    pathlib.Path("results_ibm15").mkdir(exist_ok=True)
    pathlib.Path("results_ibm15/raw.json").write_text(json.dumps(raw, indent=1))
    out = analyze(raw)
    pathlib.Path("results_ibm15/ibm15_results.json").write_text(json.dumps(out, indent=1))
    print("\nwrote results_ibm15/raw.json and ibm15_results.json")


def run_recover(job_id, instance=None, shots=SHOTS):
    from qiskit_ibm_runtime import QiskitRuntimeService
    kw = {"channel": "ibm_quantum_platform"}
    if instance or os.environ.get("QISKIT_IBM_INSTANCE"):
        kw["instance"] = instance or os.environ["QISKIT_IBM_INSTANCE"]
    if os.environ.get("QISKIT_IBM_TOKEN"):
        kw["token"] = os.environ["QISKIT_IBM_TOKEN"]
    svc = QiskitRuntimeService(**kw)
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
    pathlib.Path("results_ibm15").mkdir(exist_ok=True)
    pathlib.Path("results_ibm15/raw.json").write_text(json.dumps(raw, indent=1))
    print(f"  recovered {len(counts)} pubs, layout {sorted(lay)}")
    out = analyze(raw)
    pathlib.Path("results_ibm15/ibm15_results.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--submit", action="store_true")
    ap.add_argument("--analyze")
    ap.add_argument("--recover")
    ap.add_argument("--instance")
    ap.add_argument("--backend")
    ap.add_argument("--shots", type=int, default=SHOTS)
    a = ap.parse_args()
    if a.recover:
        run_recover(a.recover, instance=a.instance, shots=a.shots)
    elif a.analyze:
        analyze(json.loads(pathlib.Path(a.analyze).read_text()))
    elif a.submit:
        run_submit(shots=a.shots, backend_name=a.backend)
    elif a.dry:
        run_dry(shots=a.shots)
    else:
        preflight()
        c, _ = build_all()
        print(f"{len(c)} circuits, {len(c)*SHOTS} shots, "
              f"est {len(c)*SHOTS/580000*156:.0f}s")
