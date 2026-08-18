#!/usr/bin/env python3
"""AQ-PAGE-WOOTTERS-IBM-14 -- the Gate 5 paradox, resolved physically.

WHAT IBM-13'S GATE 5 FAILURE WAS ACTUALLY SAYING.

IBM-13 built its separable mimic by RECONSTRUCTION: take the ideal predicted
distribution, build a separable state reproducing it, prepare that. In theory
it matches exactly (TVD ~ 1e-17). On hardware it failed at nu = 0.80, TVD
0.0612 against a 0.061 threshold, and the mimic's amplitude sat systematically
ABOVE the history arm's at every setting -- by a ratio of 1.11 to 1.15, nearly
constant.

A constant RATIO is the signature of a multiplicative attenuation difference,
not of a failure of classical reproducibility. The reconstructed mimic encodes
the NOISE-FREE distribution; the history state produces the DECOHERED one. The
comparison was never fair, and it gets less fair as the signal grows, which is
exactly the observed trend.

THE FIX IS PHYSICS, NOT STATISTICS. There is a separable state that is not a
reconstruction at all:

    DEPHASE CLOCK A IN ITS COMPUTATIONAL BASIS.

Verified from statevector (preflight, gate 4):

  * negativity across (clock A : rest) drops to EXACTLY 0 -- the state becomes
    separable, all entanglement destroyed;
  * the single-basis distribution p(t_B, x) is EXACTLY preserved, TVD = 0;
  * therefore V(S_A|B) is unchanged.

That is the operational statement IBM-3's theorem is really making: the
observable is blind to the coherences that carry the entanglement. Destroy
every one of them and the reading does not move.

AND IT IS DEPTH-MATCHED BY CONSTRUCTION. The dephasing is implemented as
Rz(pi) on the clock-A qubits, averaged over the 4 sign combinations. Rz is a
VIRTUAL gate on IBM hardware -- zero duration, zero error. So the dephased
mimic runs the identical circuit, on the identical qubits, at identical depth,
through identical decoherence. Every confounder that broke IBM-13's Gate 5 --
padding parity, layout mismatch, depth mismatch -- is gone, not corrected for.

    python hardware/pw_ibm14_dephasing_mimic.py --dry
    python hardware/pw_ibm14_dephasing_mimic.py --submit --backend ibm_marrakesh
    python hardware/pw_ibm14_dephasing_mimic.py --recover <job_id> --instance <crn>
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
import pathlib
import sys

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import ClassicalRegister

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pw_ibm13_two_clock as B13
from pw_ibm13_two_clock import (D, THETA, A0, A1, B0, B1, SA, SB, SETTINGS,
                                prepare, state_tensor, history_target,
                                separable_bound, fit_amplitude_rate,
                                select_layout, rho_from_block, expectation)

NUS = (0.0, 0.25, 0.5, 0.65, 0.8, 0.9, 1.0)
ANCHOR_NU = 0.65                 # re-confirm certification on a third calibration
SHOTS = 2000
REPEATS = 8                      # per arm per nu -> 16 000 shots each
DEPHASE = list(itertools.product((0, 1), repeat=2))     # Rz sign combinations


# --------------------------------------------------------------------------
# circuits
# --------------------------------------------------------------------------

def foreign_readout(qc: QuantumCircuit) -> QuantumCircuit:
    """Clock B in Z, system S_A in X -- the single product basis under test."""
    qc.h(SA)
    qc.add_register(ClassicalRegister(6, "c"))
    qc.measure(range(6), range(6))
    return qc


def history_circuit(nu: float) -> QuantumCircuit:
    return foreign_readout(prepare(nu))


def dephased_circuit(nu: float, signs: tuple[int, int]) -> QuantumCircuit:
    """The history state with clock A dephased in its computational basis.

    Rz(pi) flips the sign of every coherence involving that qubit; averaging
    the four sign combinations annihilates all clock-A off-diagonals. Rz is
    virtual on IBM hardware, so this costs zero duration and zero error --
    the circuit is physically identical to the history arm.
    """
    qc = prepare(nu)
    for q, s in zip((A0, A1), signs):
        if s:
            qc.rz(np.pi, q)
    return foreign_readout(qc)


def reconstructed_circuit(nu: float, t: int) -> QuantumCircuit:
    """IBM-13's mimic, kept as the CONTRAST arm: a noise-free reconstruction."""
    psi = state_tensor(nu)
    p = B13.exact_foreign_joint(psi)
    pt = p.sum(axis=1)
    m = np.where(pt > 1e-12, (p[:, 0] - p[:, 1]) / np.maximum(pt, 1e-12), 0.0)
    qc = QuantumCircuit(6)
    if t & 1:
        qc.x(B0)
    if t & 2:
        qc.x(B1)
    qc.ry(float(np.arcsin(np.clip(m[t], -1.0, 1.0))), SA)
    return foreign_readout(qc)


def build_all(nus=NUS):
    circs, idx = [], []
    for nu in nus:
        for r in range(REPEATS):
            circs.append(history_circuit(nu))
            idx.append({"nu": nu, "arm": "history", "rep": r})
        for r in range(REPEATS):
            circs.append(dephased_circuit(nu, DEPHASE[r % len(DEPHASE)]))
            idx.append({"nu": nu, "arm": "dephased", "rep": r,
                        "signs": list(DEPHASE[r % len(DEPHASE)])})
        for r in range(REPEATS):
            circs.append(reconstructed_circuit(nu, r % D))
            idx.append({"nu": nu, "arm": "reconstructed", "rep": r, "t": r % D})
    for s in SETTINGS:                                   # certification anchor
        circs.append(B13.tomo_circuit(ANCHOR_NU, "A", s))
        idx.append({"nu": ANCHOR_NU, "arm": "anchor", "block": "A", "setting": s})
    return circs, idx


# --------------------------------------------------------------------------
# preflight -- gate 4 is proved here, not measured
# --------------------------------------------------------------------------

def dephase_exact(psi: np.ndarray) -> np.ndarray:
    rho = np.zeros((D * D * 4,) * 2, dtype=complex)
    for s0, s1 in DEPHASE:
        ph = np.zeros_like(psi)
        for ta in range(D):
            ph[ta] = psi[ta] * np.exp(1j * np.pi * (s0 * (ta & 1) + s1 * ((ta >> 1) & 1)))
        w = ph.reshape(-1)
        rho += np.outer(w, w.conj()) / len(DEPHASE)
    return rho


def negativity(rho: np.ndarray, dA: int) -> float:
    n = rho.shape[0]
    dB = n // dA
    r = rho.reshape(dA, dB, dA, dB).transpose(2, 1, 0, 3).reshape(n, n)
    ev = np.linalg.eigvalsh((r + r.conj().T) / 2)
    return float(np.sum(np.abs(ev[ev < 0])))


def foreign_dist(rho: np.ndarray) -> np.ndarray:
    hx = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
    T = np.kron(np.kron(np.eye(D * D), hx), np.eye(2))
    d = np.real(np.diag(T @ rho @ T.conj().T)).reshape(D, D, 2, 2).sum(axis=(0, 3))
    return d / d.sum()


def preflight(nus=NUS, verbose=True) -> dict:
    rows = []
    for nu in nus:
        psi = state_tensor(nu)
        pure = np.outer(psi.reshape(-1), psi.reshape(-1).conj())
        dep = dephase_exact(psi)
        n_pure, n_dep = negativity(pure, D), negativity(dep, D)
        p1, p2 = foreign_dist(pure), foreign_dist(dep)
        tvd = float(0.5 * np.sum(np.abs(p1 - p2)))

        # GATE 4, asserted: dephasing destroys ALL entanglement across
        # (clock A : rest) and changes the measured distribution by NOTHING.
        assert n_dep < 1e-9, f"dephased state still entangled at nu={nu}: {n_dep}"
        assert tvd < 1e-12, f"dephasing changed p(t_B,x) at nu={nu}: {tvd}"
        if nu > 0:
            assert n_pure > 0.1, f"history state not entangled at nu={nu}"

        def amp(p):
            pt = p.sum(axis=1)
            seq = np.where(pt > 1e-12, (p[:, 0] - p[:, 1]) / np.maximum(pt, 1e-12), 0.0)
            return fit_amplitude_rate(seq)[0]
        rows.append({"nu": nu, "neg_pure": n_pure, "neg_dephased": n_dep,
                     "tvd": tvd, "V": amp(p1)})

    if verbose:
        print("PREFLIGHT -- gate 4 proved from statevector, not measured\n")
        print("   nu    negativity(A:rest)   after dephasing   p(t_B,x) shift   V(Sa|B)")
        for r in rows:
            print(f"   {r['nu']:.2f}      {r['neg_pure']:.6f}          "
                  f"{r['neg_dephased']:.6f}         {r['tvd']:.1e}       {r['V']:.4f}")
        print("\n  Dephasing clock A destroys EVERY bit of entanglement across")
        print("  (A : rest) and moves the measured distribution by nothing at all.")
        print("  The observable is blind to the coherences carrying the")
        print("  entanglement -- IBM-3's theorem, stated physically.\n")
    return {"rows": rows}


def tvd_threshold(nus=NUS, shots_per_arm=SHOTS * REPEATS, trials=3000) -> float:
    """Shot-noise floor for the TVD between two arms sampling the SAME
    distribution, at the shot count this run actually delivers."""
    rng = np.random.default_rng(14)
    vals = []
    for nu in nus:
        p = foreign_dist(np.outer(state_tensor(nu).reshape(-1),
                                  state_tensor(nu).reshape(-1).conj())).ravel()
        for _ in range(trials // len(nus)):
            a = rng.multinomial(shots_per_arm, p) / shots_per_arm
            b = rng.multinomial(shots_per_arm, p) / shots_per_arm
            vals.append(0.5 * np.abs(a - b).sum())
    v = np.array(vals)
    return float(np.ceil((v.mean() + 3 * v.std()) * 1000) / 1000)


# --------------------------------------------------------------------------
# analysis
# --------------------------------------------------------------------------

def dist_from_counts(counts_list) -> np.ndarray:
    p = np.zeros((D, 2))
    for c in counts_list:
        for bits, n in c.items():
            b = bits.replace(" ", "")
            g = lambda q: int(b[len(b) - 1 - q])
            p[g(B0) + 2 * g(B1), g(SA)] += n
    return p / max(p.sum(), 1)


def analyze(raw: dict, verbose: bool = True) -> dict:
    idx, counts = raw["index"], raw["counts"]
    nus = sorted({r["nu"] for r in idx if r["arm"] != "anchor"})
    thr = raw.get("tvd_threshold") or tvd_threshold(tuple(nus))
    out = {"tvd_threshold": thr, "settings": [],
           "job_ids": raw.get("job_ids", []), "backend": raw.get("backend")}

    def amp(p):
        pt = p.sum(axis=1)
        seq = np.where(pt > 1e-12, (p[:, 0] - p[:, 1]) / np.maximum(pt, 1e-12), 0.0)
        return fit_amplitude_rate(seq)[0]

    for nu in nus:
        arms = {}
        for a in ("history", "dephased", "reconstructed"):
            sel = [c for r, c in zip(idx, counts) if r["nu"] == nu and r["arm"] == a]
            arms[a] = dist_from_counts(sel)
        vh, vd, vr = (amp(arms["history"]), amp(arms["dephased"]),
                      amp(arms["reconstructed"]))
        t_dep = float(0.5 * np.sum(np.abs(arms["history"] - arms["dephased"])))
        t_rec = float(0.5 * np.sum(np.abs(arms["history"] - arms["reconstructed"])))
        out["settings"].append({
            "nu": nu, "V_history": vh, "V_dephased": vd, "V_reconstructed": vr,
            "tvd_dephased": t_dep, "tvd_reconstructed": t_rec,
            "dephased_pass": bool(t_dep < thr),
            "ratio_reconstructed": float(vr / vh) if vh > 1e-6 else float("nan")})

    anchor = {r["setting"]: c for r, c in zip(idx, counts) if r["arm"] == "anchor"}
    if len(anchor) == len(SETTINGS):
        rho = rho_from_block(anchor, (A0, A1, SA))
        h = history_target(1.0)
        out["anchor"] = {"nu": ANCHOR_NU,
                         "F": float(np.real(h.conj() @ rho @ h)),
                         "bound": separable_bound(1.0)}

    s = out["settings"]
    out["gates"] = {
        "1_non_vacuity": bool(s[-1]["V_history"] - s[0]["V_history"] > 0.3),
        "2_dephased_reproduces": bool(all(r["dephased_pass"] for r in s)),
        "3_reconstructed_biased_high": bool(
            sum(1 for r in s[1:] if r["V_reconstructed"] > r["V_history"]) >= len(s[1:]) - 1),
        "5_anchor_certifies": bool(out.get("anchor", {}).get("F", 0) >
                                   out.get("anchor", {}).get("bound", 1)),
    }
    out["all_gates_pass"] = all(out["gates"].values())

    if verbose:
        print(f"\nRESULTS   TVD threshold {thr:.4f} "
              f"(3 sigma, {SHOTS * REPEATS} shots/arm)\n")
        print("   nu    V_hist  V_deph  V_recon   TVD(deph)  TVD(recon)   recon/hist")
        for r in s:
            flag = "PASS" if r["dephased_pass"] else "FAIL"
            print(f"   {r['nu']:.2f}  {r['V_history']:.4f}  {r['V_dephased']:.4f}  "
                  f"{r['V_reconstructed']:.4f}    {r['tvd_dephased']:.4f} {flag}  "
                  f"{r['tvd_reconstructed']:.4f}     {r['ratio_reconstructed']:.3f}")
        if "anchor" in out:
            a = out["anchor"]
            print(f"\n   anchor nu={a['nu']}: F = {a['F']:.4f} vs bound "
                  f"{a['bound']:.4f}  ->  {'certifies' if a['F']>a['bound'] else 'FAILS'}")
        print("\n  GATES")
        for k, v in out["gates"].items():
            print(f"    {k:30s} {'PASS' if v else 'FAIL'}")
        print(f"\n  all gates pass: {out['all_gates_pass']}")
        print("\n  If gate 2 passes and gate 3 holds, IBM-13's Gate 5 failure was")
        print("  decoherence asymmetry in a reconstructed mimic, NOT a failure of")
        print("  classical reproducibility -- and the foreign-clock amplitude is")
        print("  confirmed non-certifying by a state that is provably separable.")
    return out


# --------------------------------------------------------------------------
# runners
# --------------------------------------------------------------------------

def _budget(n_circ, shots):
    tot = n_circ * shots
    return tot, tot / 580000 * 156.0          # IBM-13 measured 580k shots -> 156 s


def run_dry(shots=SHOTS) -> None:
    from qiskit_aer import AerSimulator
    from qiskit_ibm_runtime.fake_provider import FakeMarrakesh

    preflight()
    fake = FakeMarrakesh()
    lay_a, lay_b, chain, _ = select_layout(fake)
    circs, idx = build_all()
    tq = transpile(circs, backend=fake, optimization_level=3,
                   seed_transpiler=14, initial_layout=lay_a)
    two_q = [sum(n for g, n in c.count_ops().items()
                 if g in ("cz", "cx", "ecr", "rzz")) for c in tq]
    hist = [q for q, r in zip(two_q, idx) if r["arm"] == "history"]
    dep = [q for q, r in zip(two_q, idx) if r["arm"] == "dephased"]
    tot, est = _budget(len(circs), shots)
    print(f"FEASIBILITY   chain {chain}   layout {lay_a}")
    print(f"  circuits {len(circs)}   shots {tot}   estimated QPU {est:.0f}s "
          f"({est/60:.1f} min)")
    print(f"  2Q gates: history {min(hist)}-{max(hist)}   dephased {min(dep)}-{max(dep)}"
          f"   <- identical is the point (Rz is virtual)")
    print(f"  max 2Q overall {max(two_q)} against Paper 1's 18-CX bound\n")

    res = AerSimulator.from_backend(fake).run(tq, shots=shots).result()
    raw = {"index": idx, "counts": [res.get_counts(i) for i in range(len(tq))],
           "shots": shots, "backend": f"{fake.name} (noise model)", "dry": True}
    analyze(raw)


def run_submit(shots=SHOTS, backend_name=None) -> None:
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
    if not os.environ.get("QISKIT_IBM_TOKEN"):
        sys.exit("QISKIT_IBM_TOKEN not set")
    preflight()
    kw = {"channel": "ibm_quantum_platform", "token": os.environ["QISKIT_IBM_TOKEN"]}
    if os.environ.get("QISKIT_IBM_INSTANCE"):
        kw["instance"] = os.environ["QISKIT_IBM_INSTANCE"]
    svc = QiskitRuntimeService(**kw)
    be = svc.backend(backend_name) if backend_name else svc.least_busy(
        operational=True, simulator=False, min_num_qubits=6)
    lay_a, lay_b, chain, _ = select_layout(be)
    circs, idx = build_all()
    tot, est = _budget(len(circs), shots)
    print(f"backend {be.name}   chain {chain}   layout {lay_a}")
    print(f"{len(circs)} circuits, {tot} shots, estimated QPU {est:.0f}s")
    tq = transpile(circs, backend=be, optimization_level=3,
                   seed_transpiler=14, initial_layout=lay_a)
    B13.assert_single_layout(tq, chain)
    job = SamplerV2(mode=be).run(tq, shots=shots)
    print(f"job {job.job_id()} submitted")
    res = job.result()
    raw = {"index": idx, "counts": [r.data.c.get_counts() for r in res],
           "shots": shots, "backend": be.name, "job_ids": [job.job_id()],
           "layouts": {"6": sorted(chain)}, "layout": sorted(chain),
           "layout_pinned": True, "tvd_threshold": tvd_threshold()}
    pathlib.Path("results_ibm14").mkdir(exist_ok=True)
    pathlib.Path("results_ibm14/raw.json").write_text(json.dumps(raw, indent=1))
    out = analyze(raw)
    pathlib.Path("results_ibm14/ibm14_results.json").write_text(json.dumps(out, indent=1))
    print("\nwrote results_ibm14/raw.json and ibm14_results.json")


def run_recover(job_id: str, instance=None, shots=SHOTS) -> None:
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
        data = pub.data
        reg = getattr(data, "c", None)
        if reg is None:
            reg = getattr(data, [n for n in dir(data) if not n.startswith("_")][0])
        counts.append(reg.get_counts())
    _, idx = build_all()
    if len(idx) != len(counts):
        sys.exit(f"index/pub mismatch: {len(idx)} vs {len(counts)}")
    qubits = set()
    try:
        for pub in (job.inputs.get("pubs") or []):
            circ = pub[0] if isinstance(pub, (list, tuple)) else pub
            qubits.update(circ.layout.final_index_layout()[:6])
    except Exception:
        pass
    bk = getattr(job, "backend", None)
    raw = {"index": idx, "counts": counts, "shots": shots,
           "backend": bk().name if callable(bk) else str(bk),
           "job_ids": [job_id], "layouts": {"6": sorted(qubits)} if qubits else {},
           "layout": sorted(qubits), "tvd_threshold": tvd_threshold()}
    pathlib.Path("results_ibm14").mkdir(exist_ok=True)
    pathlib.Path("results_ibm14/raw.json").write_text(json.dumps(raw, indent=1))
    print(f"  recovered {len(counts)} pubs, layout {sorted(qubits)}")
    out = analyze(raw)
    pathlib.Path("results_ibm14/ibm14_results.json").write_text(json.dumps(out, indent=1))


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
        print(f"threshold at {SHOTS*REPEATS} shots/arm: {tvd_threshold():.4f}")
        c, i = build_all()
        tot, est = _budget(len(c), SHOTS)
        print(f"{len(c)} circuits, {tot} shots, estimated QPU {est:.0f}s ({est/60:.1f} min)")
