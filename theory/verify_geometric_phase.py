#!/usr/bin/env python3
"""AQ-PAGE-WOOTTERS-IBM-15 -- is the geometric phase on the entanglement budget?

The synthesis repository's open question: every correlation MAGNITUDE is drawn
on one conserved unit, so none can be a shared temporal reference between two
good clocks. The Aharonov-Anandan phase is not a magnitude -- it is a property
of the path in projective Hilbert space, reparameterisation-invariant, which is
the invariance a shared time would need. Is it also on the budget?

THE ANSWER IS NEITHER YES NOR NO, AND THAT IS THE RESULT:

    the phase's VALUE is budget-free;  its VISIBILITY is exactly on the budget.

Two systems traversing the same loop agree on a phase that entanglement cannot
touch -- exactly -pi/2 for every C < 1, to machine precision. What entanglement
takes is the visibility with which either can read it, and that obeys the same
complementarity relation as everything else in the programme:

    visibility^2 + C^2 = 1

THE LOOP. A geodesic octant |0> -> |+> -> |+i> -> |0>, each arc a rotation
about an axis PERPENDICULAR to the state throughout, so <H> = 0 along every arc
and the dynamical phase vanishes EXACTLY rather than being subtracted. The
measured interferometric phase is therefore purely geometric, with no echo
construction and no model-dependent correction. Solid angle pi/2, geometric
phase -Omega/2 = -pi/4.

    python theory/verify_geometric_phase.py
"""

from __future__ import annotations

import numpy as np

I2 = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.diag([1, -1]).astype(complex)
PAULI = {"x": X, "y": Y, "z": Z}

ARCS = (("y", np.pi / 2), ("z", np.pi / 2), ("x", np.pi / 2))   # the octant


def rot(axis: str, angle: float) -> np.ndarray:
    return np.cos(angle / 2) * I2 - 1j * np.sin(angle / 2) * PAULI[axis]


def loop(arcs=ARCS, steps: int = 1) -> np.ndarray:
    """The loop, each arc split into `steps` equal sub-rotations.

    Splitting changes the PARAMETERISATION and the circuit depth, never the
    path. A reparameterisation-invariant phase must not move.
    """
    u = np.eye(2, dtype=complex)
    for axis, ang in arcs:
        s = rot(axis, ang / steps)
        for _ in range(steps):
            u = s @ u
    return u


def entangled(chi: float) -> np.ndarray:
    """cos(chi/2)|00> + sin(chi/2)|11>, concurrence C = |sin chi|."""
    psi = np.zeros(4, dtype=complex)
    psi[0], psi[3] = np.cos(chi / 2), np.sin(chi / 2)
    return psi


def check_dynamical_phase() -> bool:
    print("1. THE DYNAMICAL PHASE VANISHES BY CONSTRUCTION")
    print("   Each arc rotates about an axis perpendicular to the state, so")
    print("   <H> = 0 pointwise -- nothing is subtracted, nothing is modelled.\n")
    st = np.array([1, 0], dtype=complex)
    worst, acc = 0.0, 0.0
    for axis, ang in ARCS:
        grid = np.linspace(0, ang, 201)
        vals = [float(np.real((rot(axis, s) @ st).conj()
                              @ PAULI[axis] @ (rot(axis, s) @ st))) for s in grid]
        worst = max(worst, max(abs(v) for v in vals))
        acc += float(np.trapezoid(vals, grid)) / 2
        st = rot(axis, ang) @ st
        print(f"     arc about {axis}:  max |<P>| along the path = "
              f"{max(abs(v) for v in vals):.2e}")
    u = loop()
    psi0 = np.array([1, 0], dtype=complex)
    total = float(np.angle(psi0.conj() @ (u @ psi0)))
    ok = (abs(acc) < 1e-12 and abs(abs(psi0.conj() @ (u @ psi0)) - 1) < 1e-12
          and abs(total + np.pi / 4) < 1e-12)
    print(f"\n     accumulated dynamical phase = {acc:.2e}")
    print(f"     loop is cyclic, total phase = {total:+.9f}  (-pi/4 = {-np.pi/4:+.9f})")
    print(f"   -> the measured phase IS the geometric phase: {ok}\n")
    return ok


def check_rate_invariance() -> bool:
    print("2. REPARAMETERISATION INVARIANCE (exact, and therefore a THEOREM)")
    print("   Same path, different parameterisation and different depth.\n")
    print("     steps   total phase        deviation")
    psi0 = np.array([1, 0], dtype=complex)
    ok = True
    for n in (1, 2, 4, 8, 16, 32):
        ph = float(np.angle(psi0.conj() @ (loop(steps=n) @ psi0)))
        dev = abs(ph + np.pi / 4)
        ok &= dev < 1e-9
        print(f"     {n:5d}   {ph:+.9f}      {dev:.1e}")
    print(f"\n   -> invariant to machine precision: {ok}")
    print("   This is forced. On HARDWARE it is not: more steps means more")
    print("   gates and more decoherence, and whether the phase holds still")
    print("   is the contingent question a run has to answer.\n")
    return ok


def check_budget() -> bool:
    print("3. THE BUDGET QUESTION -- the result")
    print("   Target entangled with a partner; loop driven on ONE party, then")
    print("   on BOTH.\n")
    u = loop()
    print("   (a) LOCAL loop  U (x) I  -- the phase is DESTROYED by entanglement")
    print("       C        phase        visibility")
    local_ok = True
    for k in (0.0, 0.125, 0.25, 0.375, 0.5):
        chi = k * np.pi
        psi = entangled(chi)
        g = complex(psi.conj() @ (np.kron(u, I2) @ psi))
        print(f"       {abs(np.sin(chi)):.4f}   {np.angle(g):+.6f}     {abs(g):.6f}")
    local_ok = abs(np.angle(complex(entangled(np.pi / 2).conj()
                   @ (np.kron(u, I2) @ entangled(np.pi / 2))))) < 1e-9
    print(f"       -> falls from -pi/4 to exactly 0 at C = 1: {local_ok}")
    print("       A one-sided loop reads the subsystem, and the subsystem's")
    print("       phase is spent by entanglement like every other magnitude.\n")

    print("   (b) BOTH-PARTY loop  U (x) U  -- the phase is UNTOUCHED")
    print("       C        phase           visibility   vis^2 + C^2")
    both_ok, comp_ok = True, True
    for k in np.linspace(0, 0.49, 12):
        chi = k * np.pi
        C = abs(np.sin(chi))
        psi = entangled(chi)
        g = complex(psi.conj() @ (np.kron(u, u) @ psi))
        both_ok &= abs(np.angle(g) + np.pi / 2) < 1e-9
        comp_ok &= abs(abs(g) ** 2 + C ** 2 - 1.0) < 1e-9
        if k in (0.0,) or abs(k - 0.223) < 0.02 or abs(k - 0.49) < 0.02:
            print(f"       {C:.4f}   {np.angle(g):+.9f}   {abs(g):.6f}    "
                  f"{abs(g)**2 + C**2:.9f}")
    print(f"\n       phase exactly -pi/2 for every C < 1: {both_ok}")
    print(f"       visibility^2 + C^2 = 1 exactly:      {comp_ok}")
    print("\n   => THE VALUE IS BUDGET-FREE; THE VISIBILITY IS ON THE BUDGET.")
    print("      Two systems traversing the same loop agree on a phase that")
    print("      entanglement cannot move. What entanglement takes is the")
    print("      visibility with which either can read it -- and that obeys the")
    print("      same complementarity relation as the rest of the programme.")
    print("      At C = 1 the visibility is exactly 0 and the phase is not")
    print("      merely small but UNDEFINED, so nothing is claimed there.\n")
    return bool(local_ok and both_ok and comp_ok)


def check_scope() -> bool:
    print("4. SCOPE, STATED AS LIMITS")
    print("   * Two qubits, one loop, pure states. Nothing here is shown for")
    print("     d > 2 clocks, mixed states, or three or more parties.")
    print("   * 'Both-party loop' means the SAME unitary applied to each. Two")
    print("     clocks running at different RATES traverse the same path with")
    print("     different step counts, which section 2 shows is invariant for")
    print("     the ideal loop -- on hardware that is exactly what must be")
    print("     measured, not assumed.")
    print("   * The phase being entanglement-independent does NOT make it a")
    print("     shared time. The loops are externally programmed, as everywhere")
    print("     in this programme, and two systems told to trace the same path")
    print("     agreeing about it is not an observer-free simultaneity.")
    print("   * Whether the -pi/2 value tracks the solid angle across DIFFERENT")
    print("     loops is not established here: a second candidate loop returned")
    print("     the same phase, which needs its cyclicity verified before any")
    print("     solid-angle scaling is claimed. Flagged, not asserted.\n")
    return True


if __name__ == "__main__":
    print("=" * 74)
    print("Is the Aharonov-Anandan phase on the entanglement budget?")
    print("=" * 74 + "\n")
    out = [check_dynamical_phase(), check_rate_invariance(),
           check_budget(), check_scope()]
    print("=" * 74)
    print(f"all checks pass: {all(out)}")
    print("=" * 74)
