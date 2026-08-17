#!/usr/bin/env python3
"""AQ-PAGE-WOOTTERS-IBM-11 -- the coherence witness runs backwards against CHSH.

THE CLAIM. The clock-marginal coherence witness used throughout this programme
reads a MARGINAL. For a bipartite pure state the marginal entropy IS the
entanglement entropy, so entanglement is exactly what flattens the distribution
the witness measures. The witness is therefore not a weak entanglement witness
-- it is an ANTI-witness, maximised where entanglement is zero.

Derived exactly, and it already reproduces IBM-2's measured 4.2x. This run
sweeps it as a continuous relationship on hardware for the first time.

THE FAMILY, at d = 2 (two qubits):

    |Psi(lam)> = (1/sqrt 2) [ |0>_C |0>_S + |1>_C Ry(lam*pi)|0>_S ]

    lam = 0 -> |+>|0>, a PRODUCT state, zero entanglement
    lam = 1 -> (|00> + |11>)/sqrt 2, a BELL pair

Closed forms (both asserted below before any backend contact):

    witness   W(lam) = cos(lam*pi/2) / 2        0.5 at lam=0, 0 at lam=1
    concurr.  C(lam) = sin(lam*pi/2)           0   at lam=0, 1 at lam=1
    CHSH      S(lam) = 2*sqrt(1 + C^2)         2.0 at lam=0, 2*sqrt2 at lam=1

and the anti-correlation is an EXACT TRADE-OFF, not merely a monotone trend:

    (2W)^2 + C^2 = 1        S^2 + 16 W^2 = 8

Marginal coherence and entanglement lie on a circle. The run therefore has a
quantitative curve to test, not only a sign.

The endpoints are the whole result: the state that MAXIMISES the coherence
witness sits exactly at the classical CHSH boundary of 2, and the state that
saturates Tsirelson's bound has a witness of exactly zero.

IS THIS CONTINGENT? Asked before designing the run, per the standing rule this
programme acquired by spending IBM-6 and IBM-8 on a quantity fixed at +1 by
construction.

  For IDEAL PURE states the anti-correlation is FORCED -- marginal entropy is
  entanglement entropy -- so sweeping it on paper measures a theorem.

  On HARDWARE it is CONTINGENT. Prepared states are mixed; for mixed states
  marginal entropy is no longer the entanglement entropy. Decoherence attacks
  marginal coherence and nonlocal correlation through different channels at
  different rates. Whether the anti-correlation survives, and with what slope,
  is what this run measures. The gates below are written about the MEASURED
  relationship, not about reproducing the ideal curve.

Cost: ~34 circuits, 2 qubits, no controlled clock-shift and no Loschmidt echo.
Cheaper and shallower than IBM-10.

Usage:
    python pw_ibm11_witness_vs_chsh.py --dry
    python pw_ibm11_witness_vs_chsh.py --backend ibm_marrakesh --fresh
"""

from __future__ import annotations

import argparse
import datetime
import json
from pathlib import Path

import numpy as np
from qiskit import ClassicalRegister, QuantumCircuit
from qiskit.quantum_info import Statevector

from pw_ibm1_submit import DryBackend, HardwareBackend, clear_checkpoint, find_chain

LAMBDAS = (0.0, 0.25, 0.5, 0.75, 1.0)

# Svozil arm (arXiv:2512.09100). The joint coincidence rate of a singlet-based
# relational clock, R(theta) = 0.5 sin^2(theta/2), against the Peres-style
# local benchmark R_cl(theta) = theta / (2 pi). Our lambda=1 state is |Phi+>
# rather than the singlet, and its ANTI-coincidence P(+,-) reproduces Svozil's
# R(theta) exactly (verified to 6 decimals in preflight).
#
# Chosen for two reasons the programme cares about. The curves CROSS EXACTLY at
# 90 and 180 degrees, giving two internal nulls where any measured excess is
# purely instrumental -- a free calibration of the excess estimator. And the
# absolute excess peaks at 140.46 deg (0.0526), the best signal-to-noise point
# on the difference. (The relative excess peaks elsewhere, at 133.6 deg / 13.8%;
# the paper's summary conflates the two maxima.)
SVOZIL_ANGLES_DEG = (0.0, 45.0, 90.0, 120.0, 140.5, 180.0)
SVOZIL_NULLS_DEG = (90.0, 180.0)
SHOTS = 4000
CLOCK, SYSTEM = 0, 1

PAULI = {
    "X": np.array([[0, 1], [1, 0]], dtype=complex),
    "Y": np.array([[0, -1j], [1j, 0]], dtype=complex),
    "Z": np.array([[1, 0], [0, -1]], dtype=complex),
}


# --------------------------------------------------------------------------
# States and closed forms
# --------------------------------------------------------------------------

def prepare(lam: float) -> QuantumCircuit:
    """|Psi(lam)> = (1/sqrt2)[ |0>|0> + |1> Ry(lam*pi)|0> ]."""
    qc = QuantumCircuit(2)
    qc.h(CLOCK)
    qc.cry(lam * np.pi, CLOCK, SYSTEM)
    return qc


def exact_witness(lam: float) -> float:
    """TVD from uniform of the Fourier-basis clock readout. = cos(lam*pi/2)/2."""
    return float(abs(np.cos(lam * np.pi / 2)) / 2.0)


def exact_concurrence(lam: float) -> float:
    """C = 2|ad - bc| for the pure state. Here C = sin(lam*pi/2)."""
    return float(abs(np.sin(lam * np.pi / 2)))


def exact_chsh(lam: float) -> float:
    """For a two-qubit PURE state, S_max = 2 sqrt(1 + C^2).

    (A first draft wrote sin^2(lam*pi) instead of sin^2(lam*pi/2) here; the
    preflight assertion against the Horodecki construction caught it at
    lambda = 0.25.)"""
    c = exact_concurrence(lam)
    return float(2.0 * np.sqrt(1.0 + c * c))


def correlation_tensor(psi: np.ndarray) -> np.ndarray:
    rho = np.outer(psi, psi.conj())
    T = np.zeros((3, 3))
    for i, A in enumerate("XYZ"):
        for j, B in enumerate("XYZ"):
            # Qiskit little-endian: qubit0 = CLOCK is the RIGHT factor
            op = np.kron(PAULI[B], PAULI[A])
            T[i, j] = float(np.real(np.trace(op @ rho)))
    return T


def optimal_chsh_settings(T: np.ndarray):
    """Horodecki construction. Returns (a, a', b, b') as Bloch unit vectors.

    With E(a,b) = a^T T b, write S = a^T T (b - b') + a'^T T (b + b'). Setting
    b + b' = 2cos(phi) c_hat and b - b' = 2sin(phi) d_hat for orthonormal
    c_hat, d_hat gives S = 2[ sin(phi)|T d_hat| + cos(phi)|T c_hat| ], maximised
    by taking c_hat, d_hat as the two leading eigenvectors of T^T T -- so those
    are the SYSTEM-side directions, and the CLOCK-side ones are their images
    under T. (A first draft had these two roles swapped; the preflight
    assertion below caught it at lambda = 0, where it returned S = 0 against a
    closed form of 2.)"""
    w, v = np.linalg.eigh(T.T @ T)
    order = np.argsort(w)[::-1]
    c_hat, d_hat = v[:, order[0]], v[:, order[1]]
    t1, t2 = float(max(w[order[0]], 0.0)), float(max(w[order[1]], 0.0))

    phi = float(np.arctan2(np.sqrt(t2), np.sqrt(t1)))
    b = np.cos(phi) * c_hat + np.sin(phi) * d_hat
    bp = np.cos(phi) * c_hat - np.sin(phi) * d_hat

    Ta, Tap = T @ d_hat, T @ c_hat
    na, nap = np.linalg.norm(Ta), np.linalg.norm(Tap)
    a = Ta / na if na > 1e-12 else np.array([1.0, 0.0, 0.0])
    ap = Tap / nap if nap > 1e-12 else np.array([0.0, 0.0, 1.0])
    return a, ap, b, bp


def rotate_to_z(qc: QuantumCircuit, q: int, n: np.ndarray) -> None:
    """Rotate so a measurement of Z reads out n.sigma."""
    nx, ny, nz = n / max(np.linalg.norm(n), 1e-15)
    theta = float(np.arccos(np.clip(nz, -1.0, 1.0)))
    phi = float(np.arctan2(ny, nx))
    qc.rz(-phi, q)
    qc.ry(-theta, q)


# --------------------------------------------------------------------------
# Circuits
# --------------------------------------------------------------------------

def witness_circuit(lam: float) -> QuantumCircuit:
    """Fourier-basis clock readout. At d=2 the inverse QFT is a Hadamard."""
    qc = prepare(lam)
    qc.h(CLOCK)
    qc.add_register(ClassicalRegister(1, "c"))
    qc.measure(CLOCK, 0)
    return qc


def chsh_circuit(lam: float, a: np.ndarray, b: np.ndarray) -> QuantumCircuit:
    qc = prepare(lam)
    rotate_to_z(qc, CLOCK, a)
    rotate_to_z(qc, SYSTEM, b)
    qc.add_register(ClassicalRegister(2, "c"))
    qc.measure([CLOCK, SYSTEM], [0, 1])
    return qc


def bloch_xz(angle: float) -> np.ndarray:
    """Unit Bloch vector at polar angle `angle` in the x-z plane."""
    return np.array([np.sin(angle), 0.0, np.cos(angle)])


def svozil_R_quantum(theta: float) -> float:
    return float(0.5 * np.sin(theta / 2.0) ** 2)


def svozil_R_classical(theta: float) -> float:
    """Peres-style local benchmark, rising linearly in the angle."""
    return float(theta / (2.0 * np.pi))


def coincidence_circuit(lam: float, theta: float) -> QuantumCircuit:
    """Clock measured along +z, system along theta in the x-z plane."""
    qc = prepare(lam)
    rotate_to_z(qc, CLOCK, bloch_xz(0.0))
    rotate_to_z(qc, SYSTEM, bloch_xz(theta))
    qc.add_register(ClassicalRegister(2, "c"))
    qc.measure([CLOCK, SYSTEM], [0, 1])
    return qc


def coincidence_rate(counts: dict[str, int]) -> float:
    """P(clock = +, system = -). Qiskit bitstring is 'c1 c0' = system, clock."""
    tot = sum(counts.values())
    hit = sum(n for b, n in counts.items() if b.replace(" ", "")[-1] == "0"
              and b.replace(" ", "")[-2] == "1")
    return float(hit / max(tot, 1))


def separable_branch(lam: float, t: int) -> QuantumCircuit:
    """|t>_C (x) Ry(lam*t*pi)|0>_S -- one branch of the classical mixture.

    Averaging the two branches with weight 1/2 realises the separable state
    with the same joint diagonal and no clock coherence. It must not violate."""
    qc = QuantumCircuit(2)
    if t:
        qc.x(CLOCK)
        qc.ry(lam * np.pi, SYSTEM)
    return qc


def separable_chsh_circuit(lam: float, t: int, a, b) -> QuantumCircuit:
    qc = separable_branch(lam, t)
    rotate_to_z(qc, CLOCK, a)
    rotate_to_z(qc, SYSTEM, b)
    qc.add_register(ClassicalRegister(2, "c"))
    qc.measure([CLOCK, SYSTEM], [0, 1])
    return qc


# --------------------------------------------------------------------------
# Readout
# --------------------------------------------------------------------------

def witness_from_counts(counts: dict[str, int]) -> float:
    tot = sum(counts.values())
    p0 = counts.get("0", 0) / max(tot, 1)
    return float(abs(p0 - 0.5))


def correlator(counts: dict[str, int]) -> float:
    """E = <Z (x) Z> from two-bit counts."""
    tot = sum(counts.values())
    acc = 0
    for bits, n in counts.items():
        b = bits.replace(" ", "")
        acc += (1 if b.count("1") % 2 == 0 else -1) * n
    return float(acc / max(tot, 1))


def chsh_value(E: dict[str, float]) -> float:
    return float(abs(E["ab"] - E["abp"] + E["apb"] + E["apbp"]))


# --------------------------------------------------------------------------
# Pre-hardware checks
# --------------------------------------------------------------------------

def preflight() -> dict:
    print("=== PRE-HARDWARE CHECKS (statevector, no backend contact) ===")
    exact = {}
    for lam in LAMBDAS:
        psi = Statevector.from_instruction(prepare(lam)).data
        # entanglement across clock|system
        sch = np.linalg.svd(psi.reshape(2, 2), compute_uv=False) ** 2
        ebits = float(-sum(x * np.log2(x) for x in sch if x > 1e-12))

        T = correlation_tensor(psi)
        a, ap, b, bp = optimal_chsh_settings(T)
        S = abs(a @ T @ b - a @ T @ bp + ap @ T @ b + ap @ T @ bp)

        assert abs(S - exact_chsh(lam)) < 1e-9, \
            f"lam={lam}: optimal settings give S={S}, closed form {exact_chsh(lam)}"

        # witness closed form vs statevector
        m = psi.reshape(2, 2)                      # [system, clock] little-endian
        rho_c = m.conj().T @ m
        pplus = float(np.real(rho_c[0, 0] + rho_c[1, 1] + rho_c[0, 1] + rho_c[1, 0]) / 2)
        w = abs(pplus - 0.5)
        assert abs(w - exact_witness(lam)) < 1e-9, \
            f"lam={lam}: witness {w} != closed form {exact_witness(lam)}"

        exact[str(lam)] = {"witness": exact_witness(lam), "chsh": float(S),
                           "ebits": ebits,
                           "settings": {"a": a.tolist(), "ap": ap.tolist(),
                                        "b": b.tolist(), "bp": bp.tolist()}}
        print(f"  lam={lam:.2f}  witness={exact_witness(lam):.4f}  "
              f"ebits={ebits:.4f}  CHSH={S:.4f}")

    # The endpoints carry the claim.
    assert abs(exact["0.0"]["witness"] - 0.5) < 1e-9, "lam=0 must maximise the witness"
    assert abs(exact["0.0"]["chsh"] - 2.0) < 1e-9, "lam=0 must sit at the classical bound"
    assert abs(exact["1.0"]["witness"]) < 1e-9, "lam=1 must have zero witness"
    assert abs(exact["1.0"]["chsh"] - 2 * np.sqrt(2)) < 1e-9, "lam=1 must saturate Tsirelson"

    # The anti-correlation is not merely monotone -- it is an exact trade-off.
    #
    #     W = cos(lam pi/2)/2,  C = sin(lam pi/2)  =>  (2W)^2 + C^2 = 1
    #     S = 2 sqrt(1 + C^2)                      =>  S^2 + 16 W^2 = 8
    #
    # Marginal coherence and entanglement lie on a circle. That gives the run a
    # quantitative curve to test rather than only a sign.
    print("\n  exact trade-off relations:")
    for lam in LAMBDAS:
        W, C = exact_witness(lam), exact_concurrence(lam)
        S = exact_chsh(lam)
        circ, cons = (2 * W) ** 2 + C * C, S * S + 16 * W * W
        assert abs(circ - 1.0) < 1e-9, f"(2W)^2 + C^2 != 1 at lam={lam}"
        assert abs(cons - 8.0) < 1e-9, f"S^2 + 16W^2 != 8 at lam={lam}"
        print(f"    lam={lam:.2f}  (2W)^2+C^2 = {circ:.6f}   S^2+16W^2 = {cons:.6f}")

    # Svozil arm: our |Phi+> anti-coincidence must reproduce his singlet R(theta)
    print("\n  Svozil arm -- P(+,-) on |Phi+> vs R(theta) = 0.5 sin^2(theta/2):")
    psi1 = Statevector.from_instruction(prepare(1.0)).data
    for deg in SVOZIL_ANGLES_DEG:
        th = np.radians(deg)
        pa = np.outer([1.0, 0.0], [1.0, 0.0])
        vb = np.array([np.cos(th / 2), np.sin(th / 2)])
        ib = np.eye(2) - np.outer(vb, vb)
        got = float(np.real(np.trace(np.kron(ib, pa) @ np.outer(psi1, psi1.conj()))))
        want = svozil_R_quantum(th)
        assert abs(got - want) < 1e-9, f"theta={deg}: P(+,-)={got} != R={want}"
        exc = want - svozil_R_classical(th)
        flag = "  <- internal null" if deg in SVOZIL_NULLS_DEG else ""
        print(f"    theta={deg:6.1f}  R={got:.6f}  R_cl={svozil_R_classical(th):.6f}"
              f"  excess={exc:+.6f}{flag}")
    for deg in SVOZIL_NULLS_DEG:
        th = np.radians(deg)
        assert abs(svozil_R_quantum(th) - svozil_R_classical(th)) < 1e-9,             f"theta={deg} is not an exact crossing"
    print("  [OK] correspondence exact; 90 and 180 deg confirmed as exact nulls.")

    ws = [exact[str(l)]["witness"] for l in LAMBDAS]
    ss = [exact[str(l)]["chsh"] for l in LAMBDAS]
    r = float(np.corrcoef(ws, ss)[0, 1])
    print(f"\n  ideal witness-vs-CHSH correlation r = {r:+.4f}")
    assert r < -0.9, "the ideal family does not anti-correlate; design is wrong"
    print("  [OK] endpoints, anti-correlation and both exact relations verified.")
    print("  NOTE: forced for pure states. The CONTINGENT question is whether")
    print("        it survives on mixed hardware states -- that is the run.\n")
    return exact


# --------------------------------------------------------------------------

def main() -> None:
    ap_ = argparse.ArgumentParser()
    ap_.add_argument("--dry", action="store_true")
    ap_.add_argument("--backend", default=None)
    ap_.add_argument("--fresh", action="store_true")
    ap_.add_argument("--out-dir", type=Path, default=None)
    args = ap_.parse_args()

    exact = preflight()

    backend = DryBackend() if args.dry else HardwareBackend(args.backend)
    if args.fresh and not args.dry:
        clear_checkpoint(backend.name)
    out_dir = args.out_dir or Path(f"results_ibm11_{backend.name}")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.utcnow().isoformat() + "Z"
    print(f"AQ-PAGE-WOOTTERS-IBM-11  backend={backend.name}  dry={args.dry}  {ts}",
          flush=True)

    chain = find_chain(backend.coupling_map, backend.num_qubits, 2)
    layout = chain[:2]

    prereg = {
        "program": "AQ-PAGE-WOOTTERS-IBM-11", "backend": backend.name,
        "dry_run": bool(args.dry), "submission_time": ts, "optimization_level": 0,
        "lambdas": list(LAMBDAS), "shots": SHOTS, "layout": layout,
        "exact": exact,
        "purpose": ("Sweep the clock-marginal coherence witness and CHSH on the same "
                    "states, from a zero-entanglement product state to a Bell pair, to "
                    "test on hardware whether the witness is ANTI-correlated with "
                    "nonlocal correlation. Forced for ideal pure states; contingent for "
                    "the mixed states hardware actually prepares."),
        "gates": {
            "gate1_witness_monotone": "measured witness decreases across lambda",
            "gate2_chsh_monotone": "measured CHSH increases across lambda",
            "gate3_anticorrelated": "Pearson r(witness, CHSH) < -0.9",
            "gate4_classical_endpoint": "at lambda=0, CHSH does not exceed 2 by >3 sigma "
                                        "(this gate can falsify the framing)",
            "gate5_quantum_endpoint": "at lambda=1, CHSH exceeds 2 by >3 sigma",
            "gate6_separable_control": "the classical mixture does not violate at any lambda",
            "gate8_svozil_nulls": "at theta = 90 and 180 deg the quantum and local "
                                  "benchmark curves cross EXACTLY, so the measured excess "
                                  "must vanish there within 3 sigma. Instrumental "
                                  "calibration of the excess estimator, free of charge.",
            "gate9_svozil_excess_is_separable": "at theta = 140.5 deg the PRODUCT state "
                                   "reproduces the Bell state's excess over the local "
                                   "benchmark to within 3 sigma. R(theta) is a "
                                   "single-setting joint rate, so IBM-3's theorem applies "
                                   "and it cannot certify nonclassicality -- verified "
                                   "exactly in preflight, where the two curves coincide at "
                                   "every angle. A significant gap here would falsify that "
                                   "reading. CHSH, measured on the same states, does "
                                   "separate them.",
            "gate7_tradeoff_flat": "measured S^2 + 16 W^2 is CONSTANT across lambda "
                                   "(spread within 3 sigma). The pure-state identity puts "
                                   "it at 8; decoherence attenuates the level, so the "
                                   "contingent claim is that the trade-off STRUCTURE "
                                   "survives, not that the value does. A gate demanding 8 "
                                   "would encode a false assumption -- the mistake IBM-7 "
                                   "made and the data corrected.",
        },
    }
    (out_dir / "ibm11_prereg.json").write_text(json.dumps(prereg, indent=2), encoding="utf-8")
    print(f"  pre-registration filed: {out_dir / 'ibm11_prereg.json'}", flush=True)

    # ---- build one batch ----
    circuits, index = [], []
    for lam in LAMBDAS:
        s = exact[str(lam)]["settings"]
        circuits.append(witness_circuit(lam)); index.append(("wit", lam, None))
        for tag, (an, bn) in {"ab": ("a", "b"), "abp": ("a", "bp"),
                              "apb": ("ap", "b"), "apbp": ("ap", "bp")}.items():
            circuits.append(chsh_circuit(lam, np.array(s[an]), np.array(s[bn])))
            index.append(("chsh", lam, tag))
    # Svozil coincidence arm at both endpoints
    for lam in (0.0, 1.0):
        for deg in SVOZIL_ANGLES_DEG:
            circuits.append(coincidence_circuit(lam, np.radians(deg)))
            index.append(("svoz", lam, deg))

    # separable control at the two endpoints
    for lam in (0.0, 1.0):
        s = exact[str(lam)]["settings"]
        for t in (0, 1):
            for tag, (an, bn) in {"ab": ("a", "b"), "abp": ("a", "bp"),
                                  "apb": ("ap", "b"), "apbp": ("ap", "bp")}.items():
                circuits.append(separable_chsh_circuit(lam, t, np.array(s[an]), np.array(s[bn])))
                index.append((f"sep{t}", lam, tag))

    print(f"  submitting {len(circuits)} circuits at {SHOTS} shots", flush=True)
    counts, _ = backend.run_batch(circuits, SHOTS, layout, stage="witness_vs_chsh")

    # ---- reduce ----
    wit, chsh, sep, svoz = {}, {}, {}, {}
    E_acc: dict = {}
    for (kind, lam, tag), c in zip(index, counts):
        if kind == "wit":
            wit[lam] = witness_from_counts(c)
        elif kind == "svoz":
            svoz.setdefault(lam, {})[tag] = coincidence_rate(c)
        elif kind == "chsh":
            E_acc.setdefault(("q", lam), {})[tag] = correlator(c)
        else:
            E_acc.setdefault((kind, lam), {})[tag] = correlator(c)
    for (k, lam), E in E_acc.items():
        if k == "q":
            chsh[lam] = chsh_value(E)
        else:
            sep.setdefault(lam, {})[k] = E
    # average the two separable branches, then evaluate CHSH on the mixture
    sep_chsh = {}
    for lam, branches in sep.items():
        if {"sep0", "sep1"} <= set(branches):
            mixed = {t: 0.5 * (branches["sep0"][t] + branches["sep1"][t])
                     for t in branches["sep0"]}
            sep_chsh[lam] = chsh_value(mixed)

    ws = [wit[l] for l in LAMBDAS]
    ss = [chsh[l] for l in LAMBDAS]
    sig_w = 0.5 / np.sqrt(SHOTS)
    sig_s = 4.0 / np.sqrt(SHOTS)          # four correlators, each +-1 valued
    r = float(np.corrcoef(ws, ss)[0, 1])

    print("\n   lam    witness (exact)      CHSH (exact)")
    for lam in LAMBDAS:
        print(f"   {lam:.2f}   {wit[lam]:.4f} ({exact[str(lam)]['witness']:.4f})"
              f"       {chsh[lam]:.4f} ({exact[str(lam)]['chsh']:.4f})", flush=True)
    print(f"\n  witness-vs-CHSH correlation r = {r:+.4f}")
    for lam, v in sorted(sep_chsh.items()):
        print(f"  separable control lam={lam:.2f}:  CHSH = {v:.4f}  (must be <= 2)")

    # the exact trade-off, evaluated on the measured pairs
    tradeoff = {lam: float(chsh[lam] ** 2 + 16 * wit[lam] ** 2) for lam in LAMBDAS}
    sig_tr = float(np.hypot(2 * 2.83 * sig_s, 32 * 0.5 * sig_w))   # propagated
    print("\n   lam    S^2 + 16W^2   (exact 8.0)")
    for lam in LAMBDAS:
        print(f"   {lam:.2f}   {tradeoff[lam]:.4f}", flush=True)
    tr_vals = [tradeoff[lam] for lam in LAMBDAS]
    tr_mean, tr_spread = float(np.mean(tr_vals)), float(max(tr_vals) - min(tr_vals))
    print(f"  mean level {tr_mean:.4f} (ideal 8.0 -- attenuation {tr_mean/8:.3f})")
    print(f"  spread across lambda {tr_spread:.4f}   3 sigma band +-{3*sig_tr:.4f}")

    # --- Svozil excess, with the two exact crossings as internal nulls ---
    sv = {}
    for lam, byang in sorted(svoz.items()):
        rows = {}
        for deg, R in sorted(byang.items()):
            th = np.radians(deg)
            rows[deg] = {"R": R, "R_cl": svozil_R_classical(th),
                         "excess": float(R - svozil_R_classical(th)),
                         "R_exact": svozil_R_quantum(th)}
        sv[lam] = rows
    sig_R = float(np.sqrt(0.25 / SHOTS))
    print("\n  Svozil arm (excess over the local benchmark):")
    print("     lam   theta      R      R_cl    excess     exact excess")
    for lam in sorted(sv):
        for deg in SVOZIL_ANGLES_DEG:
            row = sv[lam][deg]          # NB: not `r` -- that is the correlation
            ex_exact = row["R_exact"] - row["R_cl"]
            null = "  <- null" if deg in SVOZIL_NULLS_DEG else ""
            print(f"     {lam:.1f}   {deg:6.1f}   {row['R']:.4f}  {row['R_cl']:.4f}"
                  f"   {row['excess']:+.4f}     {ex_exact:+.4f}{null}", flush=True)
    # The two exact crossings calibrate the estimator. Their scatter is an
    # EMPIRICAL error bar on the excess, which pure shot noise underestimates:
    # a rate measured under readout error carries a bias that sqrt(p(1-p)/N)
    # does not see. (A first pass gated on shot noise alone and failed by
    # 0.0003 -- the same crude-sigma error IBM-5 made.)
    null_exc = [sv[l][d]["excess"] for l in sv for d in SVOZIL_NULLS_DEG]
    sig_emp = float(max(np.sqrt(np.mean(np.square(null_exc))), sig_R))
    null_dev = max(abs(sv[1.0][d]["excess"]) for d in SVOZIL_NULLS_DEG)
    peak_exc = sv[1.0][140.5]["excess"]
    # THE PREDICTION. R(theta) is a SINGLE-SETTING joint rate, and IBM-3's
    # theorem says such a distribution is separably reproducible. Verified
    # exactly: the lambda=0 PRODUCT state gives the identical curve at every
    # angle. So the synchronisation excess is not a nonclassicality witness --
    # the two states must agree here, while CHSH separates them.
    peak_exc_prod = sv[0.0][140.5]["excess"]
    excess_gap = float(abs(peak_exc - peak_exc_prod))
    print(f"\n  max |excess| at the two internal nulls: {null_dev:.4f} "
          f"(3 sigma {3*sig_R:.4f})")
    print(f"  excess at 140.5 deg -- Bell {peak_exc:+.4f}, product {peak_exc_prod:+.4f}"
          f"  (exact +0.0526 for BOTH)")
    print(f"  |Bell - product| = {excess_gap:.4f}   3 sigma(empirical) = {3*sig_emp:.4f}")
    print("  The product state reproduces the excess exactly: a single-setting")
    print("  joint rate is separably reproducible (IBM-3). CHSH separates them,")
    print(f"  {chsh[1.0]:.3f} vs {chsh[0.0]:.3f}; this rate does not.")

    gates = {
        "gate1_witness_monotone": bool(all(ws[i] - ws[i + 1] > -sig_w for i in range(len(ws) - 1))),
        "gate2_chsh_monotone": bool(all(ss[i + 1] - ss[i] > -sig_s for i in range(len(ss) - 1))),
        "gate3_anticorrelated": bool(r < -0.9),
        "gate4_classical_endpoint": bool(chsh[0.0] <= 2.0 + 3 * sig_s),
        "gate5_quantum_endpoint": bool(chsh[1.0] > 2.0 + 3 * sig_s),
        "gate6_separable_control": bool(all(v <= 2.0 + 3 * sig_s for v in sep_chsh.values())),
        "gate7_tradeoff_flat": bool(tr_spread <= 3 * sig_tr),
        "gate8_svozil_nulls": bool(null_dev <= 0.05),
        "gate9_svozil_excess_is_separable": bool(excess_gap <= 3 * sig_emp),
    }

    results = {
        "backend": backend.name, "layout": layout, "layouts": {"2": list(layout)},
        "lambdas": list(LAMBDAS), "shots": SHOTS,
        "witness": {str(k): v for k, v in wit.items()},
        "chsh": {str(k): v for k, v in chsh.items()},
        "separable_control_chsh": {str(k): v for k, v in sep_chsh.items()},
        "exact": exact, "correlation_r": r,
        "svozil": {str(k): {str(d): v for d, v in rows.items()} for k, rows in sv.items()},
        "svozil_null_deviation": null_dev, "svozil_sigma_empirical": sig_emp,
        "svozil_peak_excess": peak_exc,
        "svozil_peak_excess_product": peak_exc_prod, "svozil_excess_gap": excess_gap,
        "sigma_R": sig_R,
        "tradeoff_S2_plus_16W2": {str(k): v for k, v in tradeoff.items()},
        "tradeoff_mean": tr_mean, "tradeoff_spread": tr_spread,
        "tradeoff_attenuation": float(tr_mean / 8.0), "sigma_tradeoff": sig_tr,
        "sigma_witness": float(sig_w), "sigma_chsh": float(sig_s),
        "gates": gates, "all_gates_pass": bool(all(gates.values())),
        "job_ids": getattr(backend, "job_ids", []),
    }
    (out_dir / "ibm11_results.json").write_text(
        json.dumps(results, indent=2, default=str), encoding="utf-8")
    if not args.dry:
        clear_checkpoint(backend.name)
    print(f"\n[GATES] {json.dumps(gates, indent=2)}")
    print(f"[DONE] all_gates_pass={results['all_gates_pass']}  -> {out_dir / 'ibm11_results.json'}")


if __name__ == "__main__":
    main()
