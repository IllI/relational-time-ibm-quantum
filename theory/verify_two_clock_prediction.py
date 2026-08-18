#!/usr/bin/env python3
"""AQ-PAGE-WOOTTERS-IBM-13 -- exact predictions for the two-clock run.

Two genuine d = 4 clocks. The question the programme has not asked: can two
clocks that are each demonstrably good Page-Wootters clocks also read each
other's systems -- and what does that cost?

This script exists to settle on paper everything that CAN be settled on paper,
which is the standing rule this programme acquired by spending IBM-6 and IBM-8
measuring quantities fixed by construction. It closed one design outright.

PART 1 -- the obvious design is dead. One shared system, two clocks: NO
setting certifies both, so it is monogamy restated and not worth a shot.
That result is what forces the two-system design.

PART 2 -- two clocks, each with its OWN system, coupled clock-to-clock by nu.
Both pairs stay certified up to a crossover, past which coupling the clocks
costs each pair its own certification. Locating that crossover is the run.

    python theory/verify_two_clock_prediction.py
"""

from __future__ import annotations

import numpy as np

D = 4                       # clock dimension -- genuinely > 2, which is the point
THETA = 2 * np.pi / D
NUS = (0.0, 0.25, 0.5, 0.75, 1.0)


# --------------------------------------------------------------------------
# shared helpers
# --------------------------------------------------------------------------

def amp(t: float, rate: float = 1.0) -> np.ndarray:
    """U^(rate*t)|+> for U = P(theta)."""
    return np.array([1.0, np.exp(1j * THETA * rate * t)]) / np.sqrt(2.0)


def history_target(rate: float = 1.0) -> np.ndarray:
    """Ideal history state on (clock, system), index 2*t + s."""
    h = np.zeros(D * 2, dtype=complex)
    for t in range(D):
        h[t * 2:t * 2 + 2] = amp(t, rate) / np.sqrt(D)
    return h


def separable_bound(rate: float = 1.0) -> float:
    """lambda_max for a fidelity witness against the rate-matched target.

    IBM-4's bound of 1/2 is the value for a MAXIMALLY entangled target. It is
    NOT a constant: lambda_max is the largest squared Schmidt coefficient of
    whatever target is used, and a rate-matched target degenerates toward a
    PRODUCT state as the rate falls, where lambda_max -> 1 and the witness
    certifies nothing. Applying 1/2 outside its domain is the same class of
    error as IBM-7's failed gate and IBM-11's first gate 7 -- and it flipped
    this script's Part 1 verdict when it was caught.
    """
    h = history_target(rate).reshape(D, 2)
    return float(max(np.linalg.eigvalsh(h.conj().T @ h)))


def fit_amplitude_rate(seq: np.ndarray) -> tuple[float, float]:
    """Least-squares amplitude and rate for seq[t] = V cos(theta*rate*t + phi)."""
    ts = np.arange(D)
    best = (0.0, 0.0, np.inf)
    for rate in np.linspace(0.0, 1.0, 1001):
        basis = np.stack([np.cos(THETA * rate * ts), -np.sin(THETA * rate * ts)]).T
        coef, *_ = np.linalg.lstsq(basis, seq, rcond=None)
        resid = float(np.sum((basis @ coef - seq) ** 2))
        if resid < best[2]:
            best = (float(np.hypot(*coef)), float(rate), resid)
    return best[0], best[1]


def von_neumann(r: np.ndarray) -> float:
    w = np.clip(np.linalg.eigvalsh((r + r.conj().T) / 2), 1e-15, None)
    return float(-np.sum(w * np.log2(w)))


# --------------------------------------------------------------------------
# PART 1 -- one shared system, two clocks
# --------------------------------------------------------------------------

def shared_system_state(nu: float) -> np.ndarray:
    """|Psi> = (1/d) sum_{tA,tB} |tA>|tB> (x) U^(a tA + b tB)|+>,  a=1-nu, b=nu.

    Flat, index ((tA*D) + tB)*2 + s.
    """
    a, b = 1.0 - nu, nu
    psi = np.zeros(D * D * 2, dtype=complex)
    for ta in range(D):
        for tb in range(D):
            v = amp(a * ta + b * tb)
            psi[(ta * D + tb) * 2:(ta * D + tb) * 2 + 2] = v / D
    return psi


def shared_clock_sys(psi: np.ndarray, keep: str) -> np.ndarray:
    t = psi.reshape(D, D, 2)
    m = t.transpose(0, 2, 1) if keep == "A" else t.transpose(1, 2, 0)
    m = m.reshape(D * 2, D)
    return m @ m.conj().T


def part1() -> bool:
    print("-" * 78)
    print("PART 1 -- ONE SHARED SYSTEM, TWO CLOCKS: closed by derivation")
    print("-" * 78)
    print("  IBM-10 certified entangled + stationary + evolving on ONE")
    print("  preparation against ONE clock. The obvious extension is one system")
    print("  driven by both clocks. Monogamy says S cannot be maximally")
    print("  entangled with both -- but a witness only has to CLEAR its bound,")
    print("  not saturate it, so whether both can clear simultaneously is a")
    print("  real question. It resolves on paper:\n")
    print("   nu     F(A:S)   bound_A    F(B:S)   bound_B    both clear?")
    n_both = 0
    for nu in NUS:
        psi = shared_system_state(nu)
        ha, hb = history_target(1.0 - nu), history_target(nu)
        fa = float(np.real(ha.conj() @ shared_clock_sys(psi, "A") @ ha))
        fb = float(np.real(hb.conj() @ shared_clock_sys(psi, "B") @ hb))
        ba, bb = separable_bound(1.0 - nu), separable_bound(nu)
        ok = fa > ba and fb > bb
        n_both += int(ok)
        print(f"   {nu:.2f}   {fa:.6f} {ba:.6f}   {fb:.6f} {bb:.6f}   {ok}")
    print(f"\n  settings certifying BOTH: {n_both} of {len(NUS)}")
    print("  => the shared-system design is DEAD. It restates monogamy and")
    print("     would be IBM-6/IBM-8 a third time. This is why IBM-13 uses two")
    print("     SEPARATE systems. One derivation, zero shots.\n")
    return n_both == 0


# --------------------------------------------------------------------------
# PART 2 -- two clocks, two systems, coupled clock-to-clock
# --------------------------------------------------------------------------

def two_pair_state(nu: float) -> np.ndarray:
    """Shape (tA, tB, sA, sB). Both clocks are uniform-reading clocks at every
    nu; the coupling interpolates the CLOCK PAIR from independent to maximally
    correlated, leaving each system driven by its own clock."""
    c = (1 - nu) * np.ones((D, D)) / D + nu * np.eye(D) / np.sqrt(D)
    c = c / np.linalg.norm(c)
    psi = np.zeros((D, D, 2, 2), dtype=complex)
    for ta in range(D):
        for tb in range(D):
            psi[ta, tb] = c[ta, tb] * np.outer(amp(ta), amp(tb))
    return psi / np.linalg.norm(psi)


def pair_clock_sys(psi: np.ndarray, which: str) -> np.ndarray:
    m = (psi.transpose(0, 2, 1, 3) if which == "A" else psi.transpose(1, 3, 0, 2))
    m = m.reshape(D * 2, -1)
    return m @ m.conj().T


def pair_cond_x(psi: np.ndarray, clock: str, sys: str) -> np.ndarray:
    ax, sx = {"A": 0, "B": 1}[clock], {"A": 2, "B": 3}[sys]
    rest = [a for a in range(4) if a not in (ax, sx)]
    t = psi.transpose([ax, sx] + rest).reshape(D, 2, -1)
    out = np.zeros(D)
    for k in range(D):
        r = t[k] @ t[k].conj().T
        p = float(np.real(np.trace(r)))
        out[k] = float(2 * np.real(r[0, 1]) / max(p, 1e-15))
    return out


def clock_mutual_information(psi: np.ndarray) -> float:
    m = psi.reshape(D, D, 4)
    rab = np.einsum("abk,cdk->abcd", m, m.conj()).reshape(D * D, D * D)
    r4 = rab.reshape(D, D, D, D)
    return (von_neumann(np.trace(r4, axis1=1, axis2=3))
            + von_neumann(np.trace(r4, axis1=0, axis2=2)) - von_neumann(rab))


def part2() -> bool:
    h, bd = history_target(), separable_bound()
    print("-" * 78)
    print("PART 2 -- TWO CLOCKS, TWO SYSTEMS: the run")
    print("-" * 78)
    print(f"  Each clock drives its own system; nu couples the two CLOCKS.")
    print(f"  Fidelity-witness separable bound lambda_max = {bd:.4f}.\n")
    print("   nu   I(A:B)   F(A:Sa) clears   F(B:Sb) clears   V(Sa|A)  V(Sa|B)  rate")
    rows = []
    for nu in NUS:
        psi = two_pair_state(nu)
        fa = float(np.real(h.conj() @ pair_clock_sys(psi, "A") @ h))
        fb = float(np.real(h.conj() @ pair_clock_sys(psi, "B") @ h))
        vo, ro = fit_amplitude_rate(pair_cond_x(psi, "A", "A"))
        vf, _ = fit_amplitude_rate(pair_cond_x(psi, "B", "A"))
        mi = clock_mutual_information(psi)
        rows.append((nu, mi, fa, fb, vo, vf))
        print(f"   {nu:.2f}  {mi:.4f}   {fa:.4f}  {str(fa>bd):<6}   {fb:.4f}  "
              f"{str(fb>bd):<6}   {vo:.4f}   {vf:.4f}   {ro:.3f}")

    both = [r for r in rows if r[2] > bd and r[3] > bd]
    print(f"\n  BOTH pairs stay certified at nu = {[r[0] for r in both]}")
    print(f"  crossover lies between nu = {both[-1][0]:.2f} and "
          f"{rows[len(both)][0]:.2f}  <-- THE MEASURABLE")
    print(f"  foreign-clock readout V(Sa|B):  {rows[0][5]:.4f} -> {rows[-1][5]:.4f}")
    print(f"  own-clock readout     V(Sa|A):  {rows[0][4]:.4f} -> {rows[-1][4]:.4f}"
          f"   (flat, as it must be)")

    print("\n  IS THIS THE SAME BUDGET AS IBM-11/IBM-12? No -- and that is the")
    print("  content. Those trade-offs sum to exactly 1. This one does not:\n")
    print("    nu     F(A:Sa)   V(Sa|B)    F + V^2")
    for nu, _, fa, _, _, vf in rows:
        print(f"    {nu:.2f}   {fa:.4f}    {vf:.4f}     {fa + vf**2:.4f}")
    print("\n  => a good clock CAN be partly read by another clock without")
    print("     losing its own certification, up to a bounded point. That is a")
    print("     weaker no-go than the correlation budget, and locating the")
    print("     boundary on hardware is what the run buys.")
    return len(both) > 0 and len(both) < len(rows)


# --------------------------------------------------------------------------
# PART 3 -- what is contingent
# --------------------------------------------------------------------------

def part3() -> bool:
    print("\n" + "-" * 78)
    print("PART 3 -- WHAT IS ACTUALLY CONTINGENT")
    print("-" * 78)
    print("  Everything above is forced for the ideal state. What hardware")
    print("  decides, and what the gates must therefore be written around:\n")
    print("   1. WHETHER THE CROSSOVER SITS WHERE THEORY PUTS IT. Both")
    print("      fidelities are attenuated by decoherence, so the measured")
    print("      crossover moves toward smaller nu. By how much is a hardware")
    print("      question, and the answer is a decoherence measurement in a")
    print("      new observable.")
    print("   2. WHETHER ANY SETTING CERTIFIES BOTH AT ALL. On a ~12-CX,")
    print("      6-qubit circuit this is not guaranteed. Paper 1's N=6 dry run")
    print("      failed decisively at 18 CX (R^2 = -2.0). If nothing certifies,")
    print("      that is a reportable bound, not a null.")
    print("   3. WHETHER THE FOREIGN-CLOCK SIGNAL IS SEPARABLY REPRODUCIBLE.")
    print("      V(Sa|B) is read from a SINGLE product-basis setting, so")
    print("      IBM-3's theorem applies directly: it is reproducible by a")
    print("      separable state and certifies NOTHING on its own. The run")
    print("      must carry that control explicitly or it overclaims.")
    print("   4. WHETHER THE TWO CLOCKS AGREE ON RATE. The multi-clock")
    print("      literature predicts temporal delocalization. Here both rates")
    print("      are 1.000 by construction, so any measured disagreement is")
    print("      instrumental -- which makes it a calibration channel rather")
    print("      than a result.\n")
    return True


if __name__ == "__main__":
    print("=" * 78)
    print(f"IBM-13 two-clock predictions   d = {D}  (both clocks genuinely > 2)")
    print("=" * 78 + "\n")
    out = [part1(), part2(), part3()]
    print("=" * 78)
    print(f"all structural checks pass: {all(out)}")
    print("=" * 78)
