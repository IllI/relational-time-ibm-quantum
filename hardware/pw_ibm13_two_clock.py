#!/usr/bin/env python3
"""AQ-PAGE-WOOTTERS-IBM-13 -- two genuine d=4 clocks, each with its own system.

THE GAP. Every run in this programme has used ONE clock. No published hardware
experiment appears to use two clocks with d > 2, an independent evolving system
on each, and conditional dynamics verified against either.

THE DESIGN, and what the derivation already killed. One system driven by two
clocks certifies against NEITHER at any setting (theory/verify_two_clock_
prediction.py, Part 1) -- it restates monogamy and would be IBM-6/IBM-8 a third
time. So: two clocks, TWO systems, one parameter nu coupling the CLOCKS.

    clock A = (A0, A1), t_A = A0 + 2*A1        system S_A driven by A
    clock B = (B0, B1), t_B = B0 + 2*B1        system S_B driven by B
    U = P(2 pi / d),  U^d = +I exactly          (IBM-5's correction)

    prepare(nu):  H(A0); H(A1)
                  Ry((1-nu)pi/2, Bk); CRY(nu pi, Ak, Bk)     k = 0,1
                  H(S_A); H(S_B)
                  CP(theta, A0, S_A); CP(2 theta, A1, S_A)
                  CP(theta, B0, S_B); CP(2 theta, B1, S_B)

    nu = 0 -> clocks independent;  nu = 1 -> clock B is a copy of clock A.

THE MEASURABLE. Both pairs stay certified up to a crossover, past which
coupling the clocks costs each pair its own certification. Locating that
crossover is the run. It is NOT the IBM-11/IBM-12 correlation budget: those
sum to exactly 1, this one does not.

GATE 5 is a NEGATIVE CONTROL and is derived, never fitted. See mimic_circuits.

Every exact value below is asserted from statevector BEFORE any backend
contact, which is how three real design errors were caught in IBM-11 and three
more in IBM-12 without spending a shot.

    python hardware/pw_ibm13_two_clock.py --dry        # zero QPU, zero token
    python hardware/pw_ibm13_two_clock.py --submit     # needs QISKIT_IBM_TOKEN
    python hardware/pw_ibm13_two_clock.py --analyze results_ibm13/raw.json
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
from qiskit.quantum_info import Statevector

D = 4
THETA = 2 * np.pi / D
A0, A1, B0, B1, SA, SB = 0, 1, 2, 3, 4, 5
NUS = (0.0, 0.25, 0.5, 0.65, 0.8)
SHOTS = 2000
PAULIS = ("X", "Y", "Z")
SETTINGS = ["".join(p) for p in itertools.product(PAULIS, repeat=3)]   # 27

P = {"X": np.array([[0, 1], [1, 0]], dtype=complex),
     "Y": np.array([[0, -1j], [1j, 0]], dtype=complex),
     "Z": np.array([[1, 0], [0, -1]], dtype=complex),
     "I": np.eye(2, dtype=complex)}

GATE5_TVD_THRESHOLD = 0.061      # pre-registered; 3 sigma above the
                                 # same-distribution floor at 2000 shots


# --------------------------------------------------------------------------
# state
# --------------------------------------------------------------------------

def prepare(nu: float) -> QuantumCircuit:
    qc = QuantumCircuit(6)
    qc.h(A0); qc.h(A1)                                   # clock A uniform
    for a, b in ((A0, B0), (A1, B1)):                    # clock-clock coupling
        qc.ry((1.0 - nu) * np.pi / 2, b)
        qc.cry(nu * np.pi, a, b)
    qc.h(SA); qc.h(SB)                                   # systems in |+>
    qc.cp(THETA, A0, SA); qc.cp(2 * THETA, A1, SA)       # S_A driven by clock A
    qc.cp(THETA, B0, SB); qc.cp(2 * THETA, B1, SB)       # S_B driven by clock B
    return qc


def state_tensor(nu: float) -> np.ndarray:
    """(tA, tB, sA, sB) from the circuit, correcting Qiskit little-endian.

    reshape gives axes (q5..q0) = (SB, SA, B1, B0, A1, A0). Getting this
    backwards put C(A:Sa) = 0 at mu = 0 in IBM-12's first draft.
    """
    v = Statevector.from_instruction(prepare(nu)).data.reshape([2] * 6)
    v = np.transpose(v, (5, 4, 3, 2, 1, 0))              # -> (A0,A1,B0,B1,SA,SB)
    out = np.zeros((D, D, 2, 2), dtype=complex)
    for a0 in range(2):
        for a1 in range(2):
            for b0 in range(2):
                for b1 in range(2):
                    out[a0 + 2 * a1, b0 + 2 * b1] = v[a0, a1, b0, b1]
    return out


def history_target(rate: float = 1.0) -> np.ndarray:
    """Ideal history state, index 4*s + t to match the tomography basis."""
    h = np.zeros(D * 2, dtype=complex)
    for t in range(D):
        a = np.array([1.0, np.exp(1j * THETA * rate * t)]) / np.sqrt(2.0)
        for s in (0, 1):
            h[4 * s + t] = a[s] / np.sqrt(D)
    return h


def separable_bound(rate: float = 1.0) -> float:
    """lambda_max = largest squared Schmidt coefficient of the target.

    NOT a constant 1/2. The rate-matched target degenerates toward a product
    state as the rate falls, where lambda_max -> 1 and the witness certifies
    nothing. Applying 1/2 outside its domain flipped the Part 1 verdict once.
    """
    h = history_target(rate).reshape(2, D)               # (s, t)
    rho_s = h @ h.conj().T
    return float(max(np.linalg.eigvalsh((rho_s + rho_s.conj().T) / 2)))


# --------------------------------------------------------------------------
# exact observables from the state
# --------------------------------------------------------------------------

def exact_clock_sys(psi: np.ndarray, which: str) -> np.ndarray:
    """rho on (clock, own system), index 4*s + t."""
    m = psi.transpose(0, 2, 1, 3) if which == "A" else psi.transpose(1, 3, 0, 2)
    m = m.reshape(D, 2, -1).transpose(1, 0, 2).reshape(D * 2, -1)
    return m @ m.conj().T


def exact_cond_x(psi: np.ndarray, clock: str) -> np.ndarray:
    """<X_{S_A}> conditioned on each reading of the named clock."""
    ax = {"A": 0, "B": 1}[clock]
    rest = [a for a in range(4) if a not in (ax, 2)]
    t = psi.transpose([ax, 2] + rest).reshape(D, 2, -1)
    out = np.zeros(D)
    for k in range(D):
        r = t[k] @ t[k].conj().T
        p = float(np.real(np.trace(r)))
        out[k] = float(2 * np.real(r[0, 1]) / max(p, 1e-15))
    return out


def fit_amplitude_rate(seq: np.ndarray) -> tuple[float, float]:
    """Least-squares amplitude and rate for seq[t] = V cos(theta*rate*t + phi).

    TWO GUARDS, both added after the live IBM-13 run returned V = 2.92 and
    9.80 at nu = 0 -- values that are impossible, since V is the amplitude of
    an expectation value and cannot exceed 1.

    As rate -> 0 the sine basis column goes to zero, so the design matrix
    becomes rank deficient and least squares can put an unbounded coefficient
    on it while keeping the residual small. That is harmless when there IS a
    signal and catastrophic when there is not -- which is exactly the nu = 0
    structural null, where the true amplitude is 0.

    So: reject rates where the sine column carries too little norm to be
    identifiable from d samples, and enforce the physical bound |V| <= 1.
    """
    ts = np.arange(D)
    best = (0.0, 0.0, np.inf)
    for rate in np.linspace(0.0, 1.0, 1001):
        sin_col = -np.sin(THETA * rate * ts)
        if float(sin_col @ sin_col) < 0.1:          # unidentifiable at d samples
            continue
        basis = np.stack([np.cos(THETA * rate * ts), sin_col]).T
        coef, *_ = np.linalg.lstsq(basis, seq, rcond=None)
        amp = float(np.hypot(*coef))
        if amp > 1.0 + 1e-9:                        # physically impossible
            continue
        resid = float(np.sum((basis @ coef - seq) ** 2))
        if resid < best[2]:
            best = (amp, float(rate), resid)
    if not np.isfinite(best[2]) or best[2] == np.inf:
        # no admissible rate: the sequence carries no identifiable oscillation
        return float(min(np.abs(seq).max(), 1.0)), 0.0
    return best[0], best[1]


def exact_foreign_joint(psi: np.ndarray) -> np.ndarray:
    """p(t_B, x) with S_A read in X. Shape (D, 2), x=0 is the +1 outcome."""
    hx = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
    t = np.einsum("ij,abjd->abid", hx, psi)
    p = np.einsum("abid,abid->bi", t, t.conj()).real
    return p / p.sum()


def mimic_joint(psi: np.ndarray) -> np.ndarray:
    """Gate 5's separable mimic, CONSTRUCTED from the ideal prediction."""
    p = exact_foreign_joint(psi)
    pt = p.sum(axis=1)
    m = np.where(pt > 1e-12, (p[:, 0] - p[:, 1]) / np.maximum(pt, 1e-12), 0.0)
    out = np.zeros((D, 2))
    out[:, 0] = pt * (1 + m) / 2
    out[:, 1] = pt * (1 - m) / 2
    return out


# --------------------------------------------------------------------------
# circuits
# --------------------------------------------------------------------------

def count_two_qubit(qc: QuantumCircuit) -> int:
    return sum(n for g, n in qc.count_ops().items()
               if g in ("cx", "cz", "ecr", "rzz", "cry", "cp", "crz"))


def select_layout(backend, seed: int = 13) -> tuple[list, list]:
    """Pick ONE physical 6-qubit chain and pin every circuit to it.

    IBM-13's first job did not do this: the transpiler chose layouts per
    circuit, the job touched 20 physical qubits for a 6-qubit circuit, and the
    dominant-layout purity drifted from 67% to 76% across the sweep. A changing
    admixture of differently-calibrated qubits shifts fidelity for reasons that
    are not physics, which left the nu = 0.65 point (clearing its bound by only
    0.0215) unresolvable. Paper 1 adopted the same fix after its own layout bug.

    The interaction graph is a 6-CYCLE: SA-A0-B0-SB-B1-A1-SA. Heavy-hex has no
    6-cycles, so one edge must always be routed -- that is unavoidable, and
    fine. What matters is that it is routed the SAME way for every circuit.
    Mapping the cycle onto a physical path leaves 5 of 6 edges native.

    Returns (initial_layout, chain) where initial_layout is indexed by virtual
    qubit [A0, A1, B0, B1, SA, SB].
    """
    edges = {}
    props = backend.properties() if hasattr(backend, "properties") else None
    adj = {}
    for a, b in backend.coupling_map:
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
        err = 1e-2
        if props is not None:
            try:
                err = props.gate_error("cz", [a, b])
            except Exception:
                try:
                    err = props.gate_error("ecr", [a, b])
                except Exception:
                    err = 1e-2
        edges[tuple(sorted((a, b)))] = float(err if err and err > 0 else 1e-2)

    def readout(q):
        try:
            return float(props.readout_error(q))
        except Exception:
            return 1e-2

    best = None
    for start in sorted(adj):
        stack = [(start, [start])]
        while stack:
            node, path = stack.pop()
            if len(path) == 6:
                cost = sum(edges.get(tuple(sorted((path[i], path[i + 1]))), 1.0)
                           for i in range(5))
                cost += sum(readout(q) for q in path)
                if best is None or cost < best[0]:
                    best = (cost, list(path))
                continue
            for nxt in sorted(adj.get(node, ())):
                if nxt not in path:
                    stack.append((nxt, path + [nxt]))
    if best is None:
        raise SystemExit("no 6-qubit chain found on this backend")

    p = best[1]

    # WHICH logical edge gets routed is a free choice, and it matters a lot.
    # The cycle can be laid on the path in 12 ways (6 rotations x 2 directions),
    # each leaving a different edge non-native. Naively taking the first gave
    # max 17 two-qubit gates -- against Paper 1's 18-CX failure bound -- while
    # the best rotation gives 9 on the same qubits. Search rather than guess.
    from qiskit import transpile as _tp

    def n2q(c):
        return sum(n for g, n in c.count_ops().items()
                   if g in ("cz", "cx", "ecr", "rzz"))

    cyc = [SA, A0, B0, SB, B1, A1]
    ranked = []
    # BOTH blocks must be probed. Optimising on block A alone produced an
    # embedding with 9 two-qubit gates on block A and 17 on block B -- the two
    # arms are compared against the same bound and are symmetric by
    # construction, so an asymmetric depth makes any measured F(A) != F(B)
    # instrumental. Which cycle edge gets routed decides this: routing a
    # CLOCK-SYSTEM edge penalises one pair, routing a CLOCK-CLOCK coupling edge
    # penalises both equally and preserves the symmetry.
    probes_a = [tomo_circuit(nu, "A", "XYZ") for nu in nus_for_probe()]
    probes_b = [tomo_circuit(nu, "B", "XYZ") for nu in nus_for_probe()]
    for rot in range(6):
        for direc in (1, -1):
            order = [cyc[(rot + direc * i) % 6] for i in range(6)]
            lay = [0] * 6
            for pos, v in enumerate(order):
                lay[v] = p[pos]
            try:
                ta = _tp(probes_a, backend=backend, optimization_level=3,
                         seed_transpiler=seed, initial_layout=lay)
                tb = _tp(probes_b, backend=backend, optimization_level=3,
                         seed_transpiler=seed, initial_layout=lay)
            except Exception:
                continue
            ma, mb = max(n2q(c) for c in ta), max(n2q(c) for c in tb)
            asym = abs(ma - mb)
            d = max(max(c.depth() for c in ta), max(c.depth() for c in tb))
            ranked.append((asym, max(ma, mb), d, lay, ma, mb))
    if not ranked:
        raise SystemExit("no admissible embedding of the interaction cycle")
    # symmetry first, then depth: an asymmetric arm is a confounder, a deeper
    # symmetric one is only attenuation, and attenuation is reported anyway.
    # Forcing ONE layout to serve both blocks is a bad trade: the shallow
    # embeddings are asymmetric (A=9, B=17) and the symmetric ones are deep
    # (21, above Paper 1's 18-CX failure bound). Neither is acceptable.
    #
    # The way out is that the interaction cycle is INVARIANT under swapping the
    # A and B registers: the edge set {SA-A0, A0-B0, B0-SB, SB-B1, B1-A1,
    # A1-SA} maps to itself under SA<->SB, A0<->B0, A1<->B1. So take the
    # shallowest embedding for block A and apply that swap to get block B's.
    # Both blocks are then shallow, both sit on the SAME physical chain, and
    # block B's measured trio occupies exactly the physical qubits block A's
    # did -- identical error exposure, which is what makes F(A) and F(B)
    # comparable.
    ranked.sort(key=lambda r: (r[4], r[2]))          # shallowest for block A
    lay_a = ranked[0][3]
    swap = {SA: SB, SB: SA, A0: B0, B0: A0, A1: B1, B1: A1}
    lay_b = [0] * 6
    for v in range(6):
        lay_b[swap[v]] = lay_a[v]
    lay = lay_a

    # The mimic's padding CX must sit on a NATIVE edge. Padding on (A0, A1)
    # cost 8 extra two-qubit gates per circuit under the best embedding,
    # because A0 and A1 are opposite ends of the cycle and not adjacent -- the
    # pad meant to equalise depth was inflating it instead.
    cm = set()
    for a, b in backend.coupling_map:
        cm.add((a, b)); cm.add((b, a))
    pad_pair = None
    for u, v in ((SA, A0), (A0, B0), (B0, SB), (SB, B1), (B1, A1), (A1, SA)):
        if (lay_a[u], lay_a[v]) in cm and (lay_b[u], lay_b[v]) in cm:
            pad_pair = (u, v)
            break
    if pad_pair is None:
        raise SystemExit("no native edge available for depth padding")
    return lay_a, lay_b, p, pad_pair


def nus_for_probe():
    return NUS


def transpile_pinned(circs, idx, backend, lay_a, lay_b, seed: int = 13):
    """Transpile each block with its own pinned layout, preserving order.

    Block B uses the A<->B register swap of block A's layout, so both blocks
    are shallow AND block B's measured trio sits on the same physical qubits
    block A's did. The mimic follows block A, since Gate 5 compares it against
    V(Sa|B) which is read from block A circuits.
    """
    out = [None] * len(circs)
    for tag, lay in (("A", lay_a), ("B", lay_b)):
        sel = [i for i, r in enumerate(idx)
               if (r.get("block") == tag) or (r["kind"] == "mimic" and tag == "A")]
        if not sel:
            continue
        tq = transpile([circs[i] for i in sel], backend=backend,
                       optimization_level=3, seed_transpiler=seed,
                       initial_layout=lay)
        for i, c in zip(sel, tq):
            out[i] = c
    assert all(c is not None for c in out), "some circuits were not transpiled"
    return out


def assert_single_layout(tq, expected: list) -> None:
    """Abort rather than archive a run whose circuits drifted across qubits."""
    want = set(expected)
    seen = set()
    for c in tq:
        try:
            seen.update(c.layout.final_index_layout()[:6])
        except Exception:
            pass
    extra = seen - want
    if extra:
        raise SystemExit(
            f"layout not pinned: circuits touched {sorted(extra)} outside the "
            f"selected chain {sorted(want)}. Refusing to submit -- this is the "
            f"defect that left IBM-13's nu = 0.65 point unresolvable.")


def calibrate_mimic_padding(backend, nus=NUS, seed: int = 13) -> dict:
    """Gate 5.5 -- how many padding CX the mimic needs, PER nu, measured against
    the transpiled history-state circuits rather than guessed.

    A fixed logical target does not work: CRY(0) is the identity, so nu = 0
    transpiles to 4-5 two-qubit gates while nu > 0 gives 8-9. A constant pad
    left the mimic shallower than the history arm at every nu > 0, and a
    shallower mimic decoheres less -- which showed up as the mimic's V sitting
    systematically ABOVE the history arm's. That is exactly the confounder
    Gate 5.5 exists to remove.
    """
    from qiskit import transpile as _tp
    targets = {}
    for nu in nus:
        counts = []
        for s in ("ZZZ", "XYZ", "ZZX"):
            t = _tp(tomo_circuit(nu, "A", s), backend=backend,
                    optimization_level=3, seed_transpiler=seed)
            counts.append(sum(n for g, n in t.count_ops().items()
                              if g in ("cz", "cx", "ecr", "rzz")))
        # CX pairs are the identity, so only an EVEN pad preserves the state.
        # Round down; the residual is reported, never hidden.
        med = int(np.median(counts))
        targets[nu] = {"tomo_2q": counts, "pad": (med // 2) * 2,
                       "residual": med - (med // 2) * 2}
    return targets


def pad_two_qubit(qc: QuantumCircuit, n_cx: int, pair=(A0, A1)) -> None:
    """Append n_cx padding gates as CX PAIRS (identity on the state, but they
    accumulate the same decoherence). Barriers stop the transpiler cancelling
    them. n_cx must be even or the padding is not the identity.
    """
    assert n_cx % 2 == 0, f"odd pad {n_cx} would not be the identity"
    u, v = pair
    for _ in range(n_cx // 2):
        qc.barrier()
        qc.cx(u, v)
        qc.barrier()
        qc.cx(u, v)
        qc.barrier()


def _basis_change(qc: QuantumCircuit, q: int, basis: str) -> None:
    if basis == "X":
        qc.h(q)
    elif basis == "Y":
        qc.sdg(q); qc.h(q)


def tomo_circuit(nu: float, block: str, setting: str) -> QuantumCircuit:
    """Block A: Pauli tomography on (A0,A1,S_A), clock B and S_B read in Z.
       Block B: the mirror. Every circuit measures all six qubits."""
    qc = prepare(nu)
    tomo = (A0, A1, SA) if block == "A" else (B0, B1, SB)
    for q, b in zip(tomo, setting):
        _basis_change(qc, q, b)
    qc.add_register(ClassicalRegister(6, "c"))
    qc.measure(range(6), range(6))
    return qc


def mimic_circuits(nu: float, pad: int = 0, pad_pair=(A0, A1)) -> list[QuantumCircuit]:
    """Gate 5. One circuit per clock-B reading t; the classical mixture over t
    with weights p(t) is formed in analysis, never on the device.

    rho = SUM_t p(t) |t><t|_B (x) sigma_t(S_A),  sigma_t = (I + m_t X)/2

    Built from the IDEAL prediction, so it is locked before submission. Fitting
    a separable state to measured results afterwards would be cherry-picking.
    """
    psi = state_tensor(nu)
    p = exact_foreign_joint(psi)
    pt = p.sum(axis=1)
    m = np.where(pt > 1e-12, (p[:, 0] - p[:, 1]) / np.maximum(pt, 1e-12), 0.0)

    out = []
    for t in range(D):
        qc = QuantumCircuit(6)
        if t & 1:
            qc.x(B0)                                     # clock B held at |t>
        if t & 2:
            qc.x(B1)
        # Ry(phi)|0> has <X> = sin(phi), so phi = arcsin(m_t) gives exactly the
        # required X-projection. Only X is ever measured on S_A in this arm, so
        # this reproduces the single-basis distribution exactly -- which is
        # precisely the content of IBM-3's theorem.
        qc.ry(float(np.arcsin(np.clip(m[t], -1.0, 1.0))), SA)
        pad_two_qubit(qc, pad, pad_pair)                 # depth match, Gate 5.5
        _basis_change(qc, SA, "X")
        qc.add_register(ClassicalRegister(6, "c"))
        qc.measure(range(6), range(6))
        out.append(qc)
    return out


def build_all(nus=NUS, padding: dict | None = None, pad_pair=(A0, A1)):
    """Returns (circuits, index). `padding` comes from calibrate_mimic_padding
    against the target backend; without it the mimic is NOT depth-matched and
    Gate 5.5 does not hold."""
    circs, idx = [], []
    for nu in nus:
        for block in ("A", "B"):
            for s in SETTINGS:
                circs.append(tomo_circuit(nu, block, s))
                idx.append({"nu": nu, "kind": "tomo", "block": block, "setting": s})
        pad = (padding or {}).get(nu, {}).get("pad", 0)
        for t, qc in enumerate(mimic_circuits(nu, pad, pad_pair)):
            circs.append(qc)
            idx.append({"nu": nu, "kind": "mimic", "t": t, "pad": pad})
    return circs, idx


# --------------------------------------------------------------------------
# preflight -- everything asserted before any backend contact
# --------------------------------------------------------------------------

def preflight(nus=NUS, verbose=True) -> dict:
    bound = separable_bound(1.0)
    rows = []
    for nu in nus:
        psi = state_tensor(nu)

        # U^d = +I exactly (IBM-5's correction)
        u = np.array([[1, 0], [0, np.exp(1j * THETA)]], dtype=complex)
        ud = np.linalg.matrix_power(u, D)
        assert np.allclose(ud, np.eye(2), atol=1e-12), "U^d != +I"

        h = history_target(1.0)
        fa = float(np.real(h.conj() @ exact_clock_sys(psi, "A") @ h))
        fb = float(np.real(h.conj() @ exact_clock_sys(psi, "B") @ h))
        v_own, r_own = fit_amplitude_rate(exact_cond_x(psi, "A"))
        v_for, _ = fit_amplitude_rate(exact_cond_x(psi, "B"))

        # the two pairs are symmetric by construction
        assert abs(fa - fb) < 1e-9, f"asymmetry at nu={nu}: {fa} vs {fb}"
        # own-clock readout must be perfect and at unit rate -- a calibration
        # channel, not a result
        assert abs(v_own - 1.0) < 1e-9, f"V(Sa|A) != 1 at nu={nu}: {v_own}"
        assert abs(r_own - 1.0) < 1e-3, f"own rate != 1 at nu={nu}: {r_own}"
        # clock B reading marginal uniform -- the mimic construction needs it
        pB = np.einsum("abij,abij->b", psi, psi.conj()).real
        assert np.allclose(pB, 1.0 / D, atol=1e-9), f"clock B not uniform at nu={nu}"
        # Gate 5: the mimic must reproduce the FULL distribution exactly
        pf, pm = exact_foreign_joint(psi), mimic_joint(psi)
        tvd = float(0.5 * np.sum(np.abs(pf - pm)))
        assert tvd < 1e-12, f"mimic TVD != 0 at nu={nu}: {tvd}"

        rows.append({"nu": nu, "F_A": fa, "F_B": fb, "bound": bound,
                     "clears": bool(fa > bound), "V_own": v_own,
                     "V_foreign": v_for, "mimic_tvd": tvd})

    if verbose:
        print("PREFLIGHT -- exact values asserted from statevector")
        print(f"  separable bound lambda_max = {bound:.6f}\n")
        print("   nu     F(A:Sa)   F(B:Sb)   clears   V(Sa|A)   V(Sa|B)   mimic TVD")
        for r in rows:
            print(f"   {r['nu']:.2f}   {r['F_A']:.6f}  {r['F_B']:.6f}   "
                  f"{str(r['clears']):<6}   {r['V_own']:.6f}  {r['V_foreign']:.6f}"
                  f"   {r['mimic_tvd']:.1e}")
        clearing = [r["nu"] for r in rows if r["clears"]]
        print(f"\n  both pairs certified at nu = {clearing}")
        if clearing and len(clearing) < len(rows):
            nxt = [r['nu'] for r in rows if not r['clears']][0]
            print(f"  ideal crossover between nu = {max(clearing):.2f} and {nxt:.2f}")
        print()
    return {"bound": bound, "rows": rows}


# --------------------------------------------------------------------------
# analysis
# --------------------------------------------------------------------------

def expectation(counts: dict, support: tuple[int, ...]) -> float:
    tot = sum(counts.values()); acc = 0
    for bits, n in counts.items():
        b = bits.replace(" ", "")
        par = sum(int(b[len(b) - 1 - q]) for q in support) % 2
        acc += (1 - 2 * par) * n
    return float(acc / max(tot, 1))


def rho_from_block(cbs: dict, qubits: tuple[int, int, int]) -> np.ndarray:
    """8x8 state on (clock qubit0, clock qubit1, system), index 4*s + 2*q1 + q0."""
    q0, q1, qs = qubits
    rho = np.eye(8, dtype=complex) / 8.0
    for pa in ("I",) + PAULIS:
        for pb in ("I",) + PAULIS:
            for pc in ("I",) + PAULIS:
                if pa == pb == pc == "I":
                    continue
                want = {q0: pa, q1: pb, qs: pc}
                hit = next((s for s in cbs
                            if all(s[i] == want[q] for i, q in enumerate((q0, q1, qs))
                                   if want[q] != "I")), None)
                if hit is None:
                    continue
                sup = tuple(q for q, lab in ((q0, pa), (q1, pb), (qs, pc)) if lab != "I")
                e = expectation(cbs[hit], sup)
                rho = rho + e * np.kron(P[pc], np.kron(P[pb], P[pa])) / 8.0
    w, v = np.linalg.eigh((rho + rho.conj().T) / 2)
    w = np.clip(w, 0, None); w = w / max(w.sum(), 1e-15)
    return (v * w) @ v.conj().T


def foreign_from_counts(counts_list: list[dict]) -> np.ndarray:
    """p(t_B, x) pooled over every setting that reads S_A in X."""
    p = np.zeros((D, 2))
    for c in counts_list:
        for bits, n in c.items():
            b = bits.replace(" ", "")
            get = lambda q: int(b[len(b) - 1 - q])
            t = get(B0) + 2 * get(B1)
            p[t, get(SA)] += n
    return p / max(p.sum(), 1)


def analyze(raw: dict, verbose: bool = True) -> dict:
    idx, counts = raw["index"], raw["counts"]
    nus = sorted({r["nu"] for r in idx})
    bound = separable_bound(1.0)
    pre = {r["nu"]: r for r in preflight(nus, verbose=False)["rows"]}
    out = {"bound": bound, "settings": [],
           "job_ids": raw.get("job_ids", []),
           "backend": raw.get("backend"), "shots": raw.get("shots")}

    for nu in nus:
        blk = {"A": {}, "B": {}}
        mim, xset = {}, []
        for r, c in zip(idx, counts):
            if r["nu"] != nu:
                continue
            if r["kind"] == "tomo":
                blk[r["block"]][r["setting"]] = c
                if r["block"] == "A" and r["setting"][2] == "X":
                    xset.append(c)
            else:
                mim[r["t"]] = c

        rho_a = rho_from_block(blk["A"], (A0, A1, SA))
        rho_b = rho_from_block(blk["B"], (B0, B1, SB))
        h = history_target(1.0)
        fa = float(np.real(h.conj() @ rho_a @ h))
        fb = float(np.real(h.conj() @ rho_b @ h))

        p_hist = foreign_from_counts(xset)
        pt = p_hist.sum(axis=1)
        seq = np.where(pt > 1e-12, (p_hist[:, 0] - p_hist[:, 1]) / np.maximum(pt, 1e-12), 0.0)
        v_for, _ = fit_amplitude_rate(seq)

        p_mim = np.zeros((D, 2))
        for t, c in mim.items():
            tot = sum(c.values())
            for bits, n in c.items():
                b = bits.replace(" ", "")
                p_mim[t, int(b[len(b) - 1 - SA])] += n / max(tot, 1) / D
        p_mim = p_mim / max(p_mim.sum(), 1e-15)
        ptm = p_mim.sum(axis=1)
        seq_m = np.where(ptm > 1e-12, (p_mim[:, 0] - p_mim[:, 1]) / np.maximum(ptm, 1e-12), 0.0)
        v_mim, _ = fit_amplitude_rate(seq_m)
        tvd = float(0.5 * np.sum(np.abs(p_hist - p_mim)))

        out["settings"].append({
            "nu": nu, "F_A": fa, "F_B": fb, "clears_A": bool(fa > bound),
            "clears_B": bool(fb > bound), "both": bool(fa > bound and fb > bound),
            "V_foreign_hist": v_for, "V_foreign_mimic": v_mim, "gate5_tvd": tvd,
            "exact_F": pre[nu]["F_A"], "exact_V_foreign": pre[nu]["V_foreign"]})

    s = out["settings"]
    both = [r["nu"] for r in s if r["both"]]
    out["gates"] = {
        "1_non_vacuity": bool(s[-1]["V_foreign_hist"] - s[0]["V_foreign_hist"] > 0.2),
        "3_both_certified_window": bool(len(both) > 0),
        "4_crossover_located": bool(0 < len(both) < len(s)),
        "5_mimic_reproduces": bool(all(r["gate5_tvd"] < GATE5_TVD_THRESHOLD for r in s)),
    }
    out["both_certified_nus"] = both
    out["all_gates_pass"] = all(out["gates"].values())

    if verbose:
        print("\nRESULTS")
        print(f"  separable bound lambda_max = {bound:.6f}\n")
        print("   nu     F(A:Sa)  F(B:Sb)  both?   V(Sa|B)  mimic V  Gate5 TVD  "
              f"(< {GATE5_TVD_THRESHOLD})")
        for r in s:
            print(f"   {r['nu']:.2f}   {r['F_A']:.4f}   {r['F_B']:.4f}   "
                  f"{str(r['both']):<6}  {r['V_foreign_hist']:.4f}   "
                  f"{r['V_foreign_mimic']:.4f}   {r['gate5_tvd']:.4f}   "
                  f"{'PASS' if r['gate5_tvd'] < GATE5_TVD_THRESHOLD else 'FAIL'}")
        print(f"\n  both pairs certified at nu = {both}")
        print("\n  GATES")
        for k, v in out["gates"].items():
            print(f"    {k:28s} {'PASS' if v else 'FAIL'}")
        print(f"\n  all gates pass: {out['all_gates_pass']}")
        print("\n  Gate 5 is a NEGATIVE CONTROL. If it passes, the foreign-clock")
        print("  amplitude does not by itself certify non-classical structure;")
        print("  certification rests only on the fidelity witnesses.")
    return out


# --------------------------------------------------------------------------
# runners
# --------------------------------------------------------------------------

def run_dry(nus=NUS, shots=SHOTS) -> None:
    from qiskit_aer import AerSimulator
    from qiskit_ibm_runtime.fake_provider import FakeMarrakesh

    pre = preflight(nus)
    fake = FakeMarrakesh()
    print(f"FEASIBILITY -- transpiled against {fake.name} "
          f"({fake.num_qubits} qubits, real coupling map)\n")

    lay_a, lay_b, chain, pad_pair = select_layout(fake)
    print(f"  PINNED LAYOUT  chain {chain}")
    print(f"    block A: A0,A1,B0,B1,SA,SB -> {lay_a}")
    print(f"    block B (register swap, same chain) -> {lay_b}")
    print()

    padding = calibrate_mimic_padding(fake, nus)
    print("  GATE 5.5 depth match (mimic padded to the history arm, per nu)")
    print("    nu     tomo 2Q      mimic pad   residual")
    for nu in nus:
        p = padding[nu]
        print(f"    {nu:.2f}   {str(p['tomo_2q']):<12} {p['pad']:<11} {p['residual']}")
    print()

    circs, idx = build_all(nus, padding, pad_pair)
    tq = transpile_pinned(circs, idx, fake, lay_a, lay_b)
    assert_single_layout(tq, chain)
    print("  layout pinned and verified: every circuit on the same qubits\n")
    two_q = [sum(n for g, n in c.count_ops().items()
                 if g in ("cz", "cx", "ecr", "rzz")) for c in tq]
    tom = [q for q, r in zip(two_q, idx) if r["kind"] == "tomo"]
    mim = [q for q, r in zip(two_q, idx) if r["kind"] == "mimic"]
    print(f"  post-transpile 2Q:  tomo {min(tom)}-{max(tom)}   "
          f"mimic {min(mim)}-{max(mim)}")
    depth = [c.depth() for c in tq]
    print(f"  circuits            {len(tq)}")
    print(f"  2-qubit gates       max {max(two_q)}   median {int(np.median(two_q))}")
    print(f"  depth               max {max(depth)}   median {int(np.median(depth))}")
    print(f"  Paper 1's N=6 bound: 18 CX failed decisively (R^2 = -2.0).")
    print(f"  -> {'ABOVE' if max(two_q) > 18 else 'at or below'} that bound\n")

    sim = AerSimulator.from_backend(fake)
    res = sim.run(tq, shots=shots).result()
    raw = {"index": idx, "counts": [res.get_counts(i) for i in range(len(tq))],
           "shots": shots, "backend": f"{fake.name} (noise model)", "dry": True}
    out = analyze(raw)

    print("\n  ATTENUATION vs exact")
    for r in out["settings"]:
        print(f"    nu={r['nu']:.2f}   F {r['exact_F']:.4f} -> {r['F_A']:.4f}"
              f"   ({r['F_A']/max(r['exact_F'],1e-9):.3f})")
    print("\n" + ("SUBMIT-WORTHY: gates evaluable under noise." if out["all_gates_pass"]
                  else "DO NOT SUBMIT AS-IS: report the negative feasibility bound."))
    pathlib.Path("results_ibm13").mkdir(exist_ok=True)
    pathlib.Path("results_ibm13/dry.json").write_text(json.dumps(out, indent=1))
    print("  wrote results_ibm13/dry.json")


def run_submit(nus=NUS, shots=SHOTS, backend_name: str | None = None) -> None:
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

    if not os.environ.get("QISKIT_IBM_TOKEN"):
        sys.exit("QISKIT_IBM_TOKEN not set in this shell.")
    preflight(nus)
    svc = QiskitRuntimeService(channel="ibm_quantum_platform",
                               token=os.environ["QISKIT_IBM_TOKEN"])
    be = svc.backend(backend_name) if backend_name else svc.least_busy(operational=True,
                                                                      simulator=False,
                                                                      min_num_qubits=6)
    print(f"backend: {be.name}")
    lay_a, lay_b, chain, pad_pair = select_layout(be)
    print(f"pinned layout chain {chain}")
    print(f"  block A -> {lay_a}")
    print(f"  block B -> {lay_b}")
    padding = calibrate_mimic_padding(be, nus)
    print("Gate 5.5 depth match:", {k: v["pad"] for k, v in padding.items()})
    circs, idx = build_all(nus, padding, pad_pair)
    tq = transpile_pinned(circs, idx, be, lay_a, lay_b)
    assert_single_layout(tq, chain)      # abort rather than archive a drifted run
    two_q = max(sum(n for g, n in c.count_ops().items()
                    if g in ("cz", "cx", "ecr", "rzz")) for c in tq)
    print(f"{len(tq)} circuits, max 2Q gates {two_q}, layout pinned and verified")
    job = SamplerV2(mode=be).run(tq, shots=shots)
    print(f"job {job.job_id()} submitted")
    res = job.result()
    counts = [r.data.c.get_counts() for r in res]
    pathlib.Path("results_ibm13").mkdir(exist_ok=True)
    # Physical layout, recorded from the circuits actually submitted. Omitting
    # this is what made pw_ibm_provenance.py refuse to write a snapshot for the
    # first IBM-13 job -- the guard fired correctly and the writer was at fault.
    layouts = {"6": sorted(chain)}
    raw = {"index": idx, "counts": counts, "shots": shots,
           "backend": be.name, "job_ids": [job.job_id()], "dry": False,
           "layouts": layouts, "layout": sorted(chain),
           "initial_layout_A": lay_a, "initial_layout_B": lay_b,
           "layout_pinned": True}
    pathlib.Path("results_ibm13/raw.json").write_text(json.dumps(raw, indent=1))
    out = analyze(raw)
    pathlib.Path("results_ibm13/ibm13_results.json").write_text(json.dumps(out, indent=1))
    print("\nwrote results_ibm13/raw.json and ibm13_results.json")


def run_recover(job_id: str, instance: str | None = None,
                nus=NUS, shots: int = SHOTS) -> None:
    """Rebuild raw.json from a COMPLETED job whose results were never saved.

    The submitting machine crashed after the job finished. Nothing is lost: the
    counts live on IBM's servers, and the circuit ORDER is deterministic --
    build_all emits (nu, block A settings, block B settings, mimics) in a fixed
    sequence, and transpile_pinned preserves that order. So the index can be
    regenerated locally and matched to the returned PUBs one for one.

    No QPU time is consumed; this is a download.
    """
    from qiskit_ibm_runtime import QiskitRuntimeService

    kw = {"channel": "ibm_quantum_platform"}
    if instance or os.environ.get("QISKIT_IBM_INSTANCE"):
        kw["instance"] = instance or os.environ["QISKIT_IBM_INSTANCE"]
    if os.environ.get("QISKIT_IBM_TOKEN"):
        kw["token"] = os.environ["QISKIT_IBM_TOKEN"]
    svc = QiskitRuntimeService(**kw)

    job = svc.job(job_id)
    print(f"job {job_id}: {job.status()}")
    res = job.result()
    counts = []
    for pub in res:
        data = pub.data
        reg = getattr(data, "c", None)
        if reg is None:                       # fall back to the only register
            names = [n for n in dir(data) if not n.startswith("_")]
            reg = getattr(data, names[0])
            print(f"  (classical register named '{names[0]}', not 'c')")
        counts.append(reg.get_counts())
    print(f"  recovered {len(counts)} pubs, "
          f"{sum(sum(c.values()) for c in counts)} shots")

    _, idx = build_all(nus)                   # order is deterministic
    if len(idx) != len(counts):
        sys.exit(f"index/pub mismatch: rebuilt {len(idx)} vs returned "
                 f"{len(counts)}. The submitted sweep used different NUS.")

    qubits = set()
    try:
        for pub in (job.inputs.get("pubs") or []):
            circ = pub[0] if isinstance(pub, (list, tuple)) else pub
            qubits.update(circ.layout.final_index_layout()[:6])
    except Exception as exc:
        print(f"  layout recovery failed ({exc}); provenance will need --fixup")

    backend = getattr(job, "backend", None)
    backend_name = backend().name if callable(backend) else str(backend)
    raw = {"index": idx, "counts": counts, "shots": shots,
           "backend": backend_name, "job_ids": [job_id], "dry": False,
           "layouts": {"6": sorted(qubits)} if qubits else {},
           "layout": sorted(qubits), "recovered": True}
    pathlib.Path("results_ibm13").mkdir(exist_ok=True)
    pathlib.Path("results_ibm13/raw.json").write_text(json.dumps(raw, indent=1))
    print(f"  wrote results_ibm13/raw.json (layout: {sorted(qubits)})")

    out = analyze(raw)
    out["job_ids"] = [job_id]
    pathlib.Path("results_ibm13/ibm13_results.json").write_text(json.dumps(out, indent=1))
    print("\nwrote results_ibm13/ibm13_results.json")


def run_fixup(raw_path: str) -> None:
    """Recover the physical layout for an ALREADY-SUBMITTED job and patch it
    into raw.json, so provenance can be written without re-running anything.

    The layout is read back from the job's own submitted circuits -- the same
    discipline Paper 1 adopted after a layout bug: verified post-hoc from what
    was actually run, never assumed from a local re-transpile, which could
    differ from the live coupling map.
    """
    from qiskit_ibm_runtime import QiskitRuntimeService
    if not os.environ.get("QISKIT_IBM_TOKEN"):
        sys.exit("QISKIT_IBM_TOKEN not set in this shell.")
    path = pathlib.Path(raw_path)
    raw = json.loads(path.read_text())
    svc = QiskitRuntimeService(channel="ibm_quantum_platform",
                               token=os.environ["QISKIT_IBM_TOKEN"])
    qubits, per_circuit = set(), []
    for jid in raw.get("job_ids", []):
        job = svc.job(jid)
        pubs = job.inputs.get("pubs") or []
        for pub in pubs:
            circ = pub[0] if isinstance(pub, (list, tuple)) else pub
            try:
                lay = sorted(circ.layout.final_index_layout()[:6])
            except Exception:
                lay = []
            per_circuit.append(lay)
            qubits.update(lay)
        print(f"  {jid}: recovered {len(qubits)} physical qubits "
              f"over {len(per_circuit)} circuits")
    if not qubits:
        sys.exit("could not recover a layout from the job payload")

    # PER-CIRCUIT layouts matter, not just the union. A 6-qubit circuit that
    # reports 20 distinct physical qubits means the transpiler chose different
    # layouts for different circuits -- and if that varies WITH nu, the measured
    # crossover could be a qubit-quality artifact rather than physics. Recorded
    # and grouped so the question is answerable from the archive.
    import collections
    groups = collections.defaultdict(collections.Counter)
    for r, lay in zip(raw.get("index", []), per_circuit):
        groups[(r.get("nu"), r.get("kind"))][tuple(lay)] += 1
    print()
    print("  layout by (nu, arm) -- does it vary with nu?")
    for k in sorted(groups, key=lambda x: (x[1], x[0])):
        top, cnt = groups[k].most_common(1)[0]
        print(f"    nu={k[0]:.2f} {k[1]:5s}: {len(groups[k])} distinct, "
              f"dominant {list(top)} x{cnt}")
    dom = {k: groups[k].most_common(1)[0][0] for k in groups if k[1] == "tomo"}
    nonzero = {k: v for k, v in dom.items() if k[0] > 0}
    same = len(set(nonzero.values())) == 1 if nonzero else False

    # Sharing a DOMINANT layout is weaker than being homogeneous. Report the
    # purity too, and how much it drifts across nu: a changing admixture of
    # differently-calibrated qubits shifts fidelity for reasons that are not
    # physics, and the first version of this check hid that behind a bare True.
    purity = {}
    for k in groups:
        if k[1] != "tomo" or k[0] <= 0:
            continue
        tot = sum(groups[k].values())
        purity[k[0]] = groups[k].most_common(1)[0][1] / tot
    print()
    print(f"  all nu > 0 tomo circuits share ONE dominant layout: {same}")
    if purity:
        lo, hi = min(purity.values()), max(purity.values())
        print("  dominant-layout purity per nu: "
              + "  ".join(f"{n:.2f}:{p:.0%}" for n, p in sorted(purity.items())))
        print(f"  purity drift across nu: {hi - lo:.0%}"
              f"   <- a changing admixture moves F for non-physical reasons")
        if hi - lo > 0.05:
            print("  NOT homogeneous. The crossover BRACKET is still safe (F falls")
            print("  by ~0.14 between the last certified nu and the first failing")
            print("  one, far above any plausible layout effect), but the status")
            print("  of a setting clearing its bound by less than ~0.03 is NOT.")
            print("  Any replication should pin initial_layout explicitly.")

    raw["layouts"] = {"6": sorted(qubits)}
    raw["layout"] = sorted(qubits)
    raw["layouts_per_circuit"] = per_circuit
    raw["layout_uniform_across_nu"] = bool(same)
    path.write_text(json.dumps(raw, indent=1))
    print(f"patched {path} with layout {sorted(qubits)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--submit", action="store_true")
    ap.add_argument("--analyze")
    ap.add_argument("--fixup", help="recover layout for an already-run job")
    ap.add_argument("--recover", help="rebuild raw.json from a COMPLETED job id")
    ap.add_argument("--instance", help="IBM instance CRN (or QISKIT_IBM_INSTANCE)")
    ap.add_argument("--backend")
    ap.add_argument("--shots", type=int, default=SHOTS)
    ap.add_argument("--nus", help="comma-separated nu values, e.g. 0.65,0.70,0.75")
    a = ap.parse_args()
    if a.nus:
        NUS = tuple(float(x) for x in a.nus.split(","))
        globals()["NUS"] = NUS
    if a.recover:
        run_recover(a.recover, instance=a.instance, shots=a.shots)
    elif a.fixup:
        run_fixup(a.fixup)
    elif a.analyze:
        analyze(json.loads(pathlib.Path(a.analyze).read_text()))
    elif a.submit:
        run_submit(nus=NUS, shots=a.shots, backend_name=a.backend)
    elif a.dry:
        run_dry(nus=NUS, shots=a.shots)
    else:
        preflight()
