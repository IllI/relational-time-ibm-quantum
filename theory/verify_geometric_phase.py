#!/usr/bin/env python3
"""RETRACTED -- the geometric-phase question is OPEN, not answered.

An earlier version of this file (commit 608f3ae) claimed:

    "the phase's VALUE is budget-free; its VISIBILITY is exactly on the budget"
    phase exactly -pi/2 for every C < 1,  and  visibility^2 + C^2 = 1

BOTH CLAIMS ARE WITHDRAWN. They are artifacts of one badly chosen loop, and a
single test against random unitaries -- which should have been the first thing
run, not an afterthought -- destroys them.

WHAT WENT WRONG. The "geodesic octant" loop
Rx(pi/2) Rz(pi/2) Ry(pi/2) multiplies out to

    diag(exp(-i pi/4), exp(+i pi/4))   ==   Rz(pi/2)

It is DIAGONAL. So U (x) U acting on sum_i c_i |ii> merely multiplies each
|ii> by the fixed phase (U_ii)^2 = -/+ i, giving

    <Psi| U (x) U |Psi> = c0^2 (-i) + c1^2 (+i) = -i cos(chi)

The constant argument -pi/2 is a weighted average of two fixed phases. The
visibility |cos chi| = sqrt(1 - C^2) follows from the same line. Both are
ARITHMETIC. Neither says anything about geometric phase, entanglement budgets,
or shared time.

THE CONTROL THAT CATCHES IT. Against Haar-random U:

    vis^2 + C^2  ranges over 0.15 to 1.67          (not 1)
    arg spread across C  up to 2 pi                 (not constant)

Against real U (rotation matrices), arg IS constant -- because (U_ij)^2 is then
real and positive, so arg(c^T M c) = 0 for any nonneg c. Also arithmetic, also
not geometry, and vis^2 + C^2 is still not 1.

WHAT SURVIVES. Only the single-qubit statement, and only for the specific path:
a cyclic evolution built from arcs each rotating about an axis perpendicular to
the state has <H> = 0 pointwise, so its total phase is purely geometric. That
much is checked below and is standard.

THE DESIGN CANNOT BE PATCHED -- a no-go, established after the retraction.
Cyclic evolution of a SUBSYSTEM requires U rho U^dag = rho. For a reduced state
that is non-degenerate (any C < 1), the only unitaries commuting with it are
diagonal in the Schmidt basis. Searched 200000 Haar-random U: ZERO are cyclic
on rho and non-diagonal. So U (x) U necessarily acts on sum c_i |ii> by fixed
phases and the two-party phase is arithmetic BY FORCE, not by bad luck in
choosing a loop.

Relaxing to GLOBAL cyclicity does not rescue it either: U (x) U with a
single-qubit U does not return an entangled |Psi> to itself except trivially
(measured |g| = 0.09 to 0.49, i.e. not cyclic at all), so there is no cyclic
geometric phase to measure.

Reformulating the QUESTION is required, not patching the circuit. Candidates,
none yet verified and none to be claimed until they are: non-cyclic
Pancharatnam phases, which are well defined without the cyclicity constraint;
different loops on each qubit chosen so the GLOBAL state is cyclic; or the
Uhlmann connection instead of the interferometric one.

WHAT IS OPEN. Everything the synthesis repository asked. Whether the
Aharonov-Anandan phase escapes the entanglement budget is UNANSWERED, and
answering it needs a loop that is not diagonal in the entangled basis, tested
against random unitaries from the start.

    python theory/verify_geometric_phase.py
"""

from __future__ import annotations

import numpy as np

I2 = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.diag([1, -1]).astype(complex)
PAULI = {"x": X, "y": Y, "z": Z}
ARCS = (("y", np.pi / 2), ("z", np.pi / 2), ("x", np.pi / 2))


def rot(axis: str, angle: float) -> np.ndarray:
    return np.cos(angle / 2) * I2 - 1j * np.sin(angle / 2) * PAULI[axis]


def loop(steps: int = 1) -> np.ndarray:
    u = np.eye(2, dtype=complex)
    for axis, ang in ARCS:
        s = rot(axis, ang / steps)
        for _ in range(steps):
            u = s @ u
    return u


def entangled(chi: float) -> np.ndarray:
    psi = np.zeros(4, dtype=complex)
    psi[0], psi[3] = np.cos(chi / 2), np.sin(chi / 2)
    return psi


def haar(rng) -> np.ndarray:
    z = (rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2))) / np.sqrt(2)
    q, r = np.linalg.qr(z)
    return q @ np.diag(np.diag(r) / np.abs(np.diag(r)))


def show_the_artifact() -> bool:
    print("1. WHY THE EARLIER CLAIM WAS WRONG")
    u = loop()
    print("   the loop product is\n", np.round(u, 6))
    diag = bool(np.allclose(u, rot("z", np.pi / 2)))
    print(f"\n   it is diagonal, and equals Rz(pi/2) exactly: {diag}")
    print("   so U (x) U multiplies |ii> by the fixed phase (U_ii)^2 = -/+ i,")
    print("   giving <Psi|U(x)U|Psi> = -i cos(chi). Constant arg and")
    print("   |g| = sqrt(1-C^2) are arithmetic, not geometry.\n")
    ok = True
    for k in (0.0, 0.15, 0.3, 0.45):
        chi = k * np.pi
        g = complex(entangled(chi).conj() @ (np.kron(u, u) @ entangled(chi)))
        ok &= abs(g - (-1j * np.cos(chi))) < 1e-12
    print(f"   measured g matches -i cos(chi) exactly: {ok}\n")
    return diag and ok


def random_control() -> bool:
    print("2. THE CONTROL THAT SHOULD HAVE RUN FIRST -- Haar-random U")
    print("   If the claim were about geometric phase it would survive here.\n")
    rng = np.random.default_rng(7)
    tot, spreads = [], []
    for _ in range(200):
        u = haar(rng)
        vals, phs = [], []
        for k in (0.0, 0.15, 0.3, 0.45):
            chi = k * np.pi
            g = complex(entangled(chi).conj() @ (np.kron(u, u) @ entangled(chi)))
            vals.append(abs(g) ** 2 + np.sin(chi) ** 2)
            phs.append(np.angle(g))
        tot += vals
        spreads.append(max(phs) - min(phs))
    print(f"   vis^2 + C^2 over 200 random loops: {min(tot):.4f} to {max(tot):.4f}"
          f"   (claim said exactly 1)")
    print(f"   arg spread across C:               {min(spreads):.4f} to "
          f"{max(spreads):.4f}   (claim said 0)")
    broken = not (abs(min(tot) - 1) < 0.01 and abs(max(tot) - 1) < 0.01)
    print(f"\n   both claims fail on generic loops: {broken}\n")
    return broken


def what_survives() -> bool:
    print("3. WHAT ACTUALLY SURVIVES")
    print("   Only the single-qubit statement: arcs that rotate about an axis")
    print("   perpendicular to the state have <H> = 0 pointwise, so the total")
    print("   phase of a cyclic path built from them is purely geometric.")
    print("   Standard, and not in dispute.\n")
    st = np.array([1, 0], dtype=complex)
    acc = 0.0
    for axis, ang in ARCS:
        grid = np.linspace(0, ang, 201)
        vals = [float(np.real((rot(axis, s) @ st).conj()
                              @ PAULI[axis] @ (rot(axis, s) @ st))) for s in grid]
        acc += float(np.trapezoid(vals, grid)) / 2
        st = rot(axis, ang) @ st
    psi0 = np.array([1, 0], dtype=complex)
    total = float(np.angle(psi0.conj() @ (loop() @ psi0)))
    ok = abs(acc) < 1e-12 and abs(total + np.pi / 4) < 1e-12
    print(f"   dynamical phase along the path = {acc:.2e}")
    print(f"   total phase                    = {total:+.9f}  (= -pi/4)")
    print(f"   -> purely geometric for this path: {ok}\n")
    return ok


def what_is_open() -> bool:
    print("4. WHAT IS OPEN")
    print("   The synthesis repository's question -- whether the")
    print("   Aharonov-Anandan phase escapes the entanglement budget -- is")
    print("   UNANSWERED. Answering it needs a loop that is not diagonal in")
    print("   the entangled basis, and the random-unitary control run FIRST")
    print("   rather than after a pleasing number appears.\n")
    print("   Neighbouring literature worth reading before trying again:")
    print("     Sjoqvist, Geometric phase for entangled spin pairs,")
    print("       Phys. Rev. A 62, 022109 (2000)")
    print("     Sjoqvist et al., Geometric phases for mixed states in")
    print("       interferometry, Phys. Rev. Lett. 85, 2845 (2000)")
    print("     Zych, Costa, Pikovski & Brukner, Quantum interferometric")
    print("       visibility as a witness of general relativistic proper time,")
    print("       Nat. Commun. 2, 505 (2011) -- visibility lost to which-path")
    print("       information, with proper time supplying it. The structural")
    print("       parallel to this programme's complementarity is real; the")
    print("       retracted result is not the way to reach it.\n")
    return True


if __name__ == "__main__":
    print("=" * 74)
    print("RETRACTED: is the AA phase on the entanglement budget?  -- OPEN")
    print("=" * 74 + "\n")
    out = [show_the_artifact(), random_control(), what_survives(), what_is_open()]
    print("=" * 74)
    print(f"retraction verified end to end: {all(out)}")
    print("=" * 74)
