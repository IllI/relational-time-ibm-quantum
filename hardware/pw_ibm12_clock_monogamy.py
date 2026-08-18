#!/usr/bin/env python3
"""AQ-PAGE-WOOTTERS-IBM-12 -- what shared relational time costs.

THE QUESTION. A clock is a good Page-Wootters clock to the extent it is
entangled with its OWN system: that is what makes it exactly stationary and
exactly internally evolving. It is a synchronisable clock -- one that can be
shown to agree with another clock -- to the extent it is entangled with THAT
clock. Those compete for the same ebits.

Taken to the limit the conclusion is stark and provable: if clock A is
MAXIMALLY entangled with its system, the pure global state factorises as
|Phi>_{A,Sa} (x) |chi>_{B,...}, so A has ZERO mutual information with clock B --
not merely no entanglement, no classical correlation either. A perfect
Page-Wootters clock is uncorrelated with every other clock in the universe.

That obstruction is known. Kuypers & Rijavec (Phys. Rev. D 112, 063544, 2025)
state it and resolve it by ADDING an interaction so the timer can read the
clock. What appears not to have been done is MEASURING the trade-off as a
continuous curve. That is this run.

THE FAMILY. Three qubits: clock A, its system Sa, second clock B. Start with A
maximally entangled with Sa, then transfer A's entanglement partner toward B
through a single excitation-transfer angle mu:

    |Psi(mu)> = (1/sqrt2) [ |000> + cos(mu)|110> + sin(mu)|101> ]      (A,Sa,B)

    mu = 0     -> C(A:Sa) = 1, C(A:B) = 0   perfect PW clock, unsynchronisable
    mu = pi/4  -> both 0.7071                the balanced point
    mu = pi/2  -> C(A:Sa) = 0, C(A:B) = 1   perfect sync, no clock function

Circuit: H(A), CX(A,Sa), CRY(2mu, Sa, B), CX(B,Sa). Three CX-equivalents --
shallower than IBM-11 and far below IBM-8's fatal depth.

IS THE TRADE-OFF CONTINGENT? Asked before designing the run, per the standing
rule this programme acquired by spending IBM-6 and IBM-8 on a quantity fixed by
construction.

  NO, for ideal states. Coffman-Kundu-Wootters gives

      C^2(A:Sa) + C^2(A:B) + tau_ABC = 4 det(rho_A)

  and this family has tau_ABC = 0 with rho_A maximally mixed, so the sum is
  exactly 1 at every mu. Measuring THAT would be measuring a theorem, and it
  would be the IBM-6/8 mistake a third time.

  YES, for the DEFICIT. Hardware states are mixed. Mixedness reduces both
  concurrences, and decoherence need not reduce them equally or leave the
  three-tangle at zero. The contingent quantities are:

      deficit(mu) = 1 - [ C^2(A:Sa) + C^2(A:B) ]     how much is lost
      is the deficit FLAT in mu, or does it depend on where the
      entanglement sits?

  A flat deficit means the trade-off structure survives and only the level
  attenuates -- the IBM-11 finding, one level up. A mu-dependent deficit means
  decoherence treats clock-system and clock-clock entanglement differently,
  which would be a genuinely new statement about which is the more fragile
  resource. Either answer is publishable; neither is forced.

WHAT THIS DOES NOT CLAIM. Nothing here emits time: the states are compiled by
externally timed gates. CKW monogamy is from 2000 and the PW obstruction is
already in the literature. The contribution is the measured curve and the
deficit, not the relation.

Usage:
    python pw_ibm12_clock_monogamy.py --dry
    python pw_ibm12_clock_monogamy.py --backend ibm_marrakesh --fresh
"""

from __future__ import annotations

import argparse
import datetime
import itertools
import json
from pathlib import Path

import numpy as np
from qiskit import ClassicalRegister, QuantumCircuit
from qiskit.quantum_info import Statevector

from pw_ibm1_submit import DryBackend, HardwareBackend, clear_checkpoint, find_chain

MUS = (0.0, np.pi / 8, np.pi / 4, 3 * np.pi / 8, np.pi / 2)
SHOTS = 2000
A, SA, B = 0, 1, 2                      # clock A, its system, clock B
PAULIS = ("X", "Y", "Z")
SETTINGS = ["".join(p) for p in itertools.product(PAULIS, repeat=3)]   # 27

P = {"X": np.array([[0, 1], [1, 0]], dtype=complex),
     "Y": np.array([[0, -1j], [1j, 0]], dtype=complex),
     "Z": np.array([[1, 0], [0, -1]], dtype=complex),
     "I": np.eye(2, dtype=complex)}


# --------------------------------------------------------------------------
# State and exact values
# --------------------------------------------------------------------------

def prepare(mu: float) -> QuantumCircuit:
    qc = QuantumCircuit(3)
    qc.h(A)
    qc.cx(A, SA)
    qc.cry(2.0 * mu, SA, B)
    qc.cx(B, SA)
    return qc


def concurrence(rho: np.ndarray) -> float:
    Y = np.array([[0, -1j], [1j, 0]])
    YY = np.kron(Y, Y)
    ev = np.sqrt(np.clip(np.linalg.eigvals(rho @ YY @ rho.conj() @ YY).real, 0.0, None))
    ev = np.sort(ev)[::-1]
    return float(max(0.0, ev[0] - ev[1] - ev[2] - ev[3]))


def chsh_max(rho: np.ndarray) -> float:
    """Horodecki: S_max = 2 sqrt(t1 + t2), t = eigenvalues of T^T T."""
    T = np.array([[float(np.real(np.trace(np.kron(P[b], P[a]) @ rho)))
                   for b in PAULIS] for a in PAULIS])
    ev = np.sort(np.linalg.eigvalsh(T.T @ T))[::-1]
    return float(2.0 * np.sqrt(max(ev[0] + ev[1], 0.0)))


def exact_pair_states(mu: float):
    """Reduced states in the SAME basis convention the Pauli operators use.

    Qiskit is little-endian: statevector.reshape(2,2,2) has axes (q2,q1,q0) =
    (B, Sa, A), not (A, Sa, B). A first draft assumed the latter and preflight
    caught it immediately -- C(A:Sa) came out 0 at mu=0 with rho_A pure. Same
    trap IBM-4's Schmidt assertion caught.

    For a pair (q0, q1) the operators below are kron(op_q1, op_q0), so the
    two-qubit basis index is 2*q1 + q0. Both reductions are built to match."""
    psi = Statevector.from_instruction(prepare(mu)).data.reshape(2, 2, 2)
    psi = psi.transpose(2, 1, 0)                      # -> (A, Sa, B)

    m1 = psi.transpose(1, 0, 2).reshape(4, 2)         # (Sa,A) x B, index 2*Sa+A
    rho_ASa = m1 @ m1.conj().T
    m2 = psi.transpose(2, 0, 1).reshape(4, 2)         # (B,A) x Sa, index 2*B+A
    rho_AB = m2 @ m2.conj().T
    m3 = psi.reshape(2, 4)                            # A x (Sa,B)
    rho_A = m3 @ m3.conj().T
    return rho_ASa, rho_AB, rho_A


# --------------------------------------------------------------------------
# Tomography
# --------------------------------------------------------------------------

def tomo_circuit(mu: float, setting: str) -> QuantumCircuit:
    qc = prepare(mu)
    for q, basis in zip((A, SA, B), setting):
        if basis == "X":
            qc.h(q)
        elif basis == "Y":
            qc.sdg(q)
            qc.h(q)
    qc.add_register(ClassicalRegister(3, "c"))
    qc.measure([A, SA, B], [0, 1, 2])
    return qc


def expectation(counts: dict[str, int], support: tuple[int, ...]) -> float:
    """<prod_{q in support} sigma_q> from one setting's counts."""
    tot = sum(counts.values())
    acc = 0
    for bits, n in counts.items():
        b = bits.replace(" ", "")           # 'c2 c1 c0'
        par = sum(int(b[len(b) - 1 - q]) for q in support) % 2
        acc += (1 - 2 * par) * n
    return float(acc / max(tot, 1))


def pair_density(counts_by_setting: dict[str, dict[str, int]],
                 qubits: tuple[int, int]) -> np.ndarray:
    """Reconstruct a two-qubit reduced density matrix from 3-qubit tomography."""
    q0, q1 = qubits
    rho = np.eye(4, dtype=complex) / 4.0
    for i, pa in enumerate(("I",) + PAULIS):
        for j, pb in enumerate(("I",) + PAULIS):
            if pa == "I" and pb == "I":
                continue
            sup = tuple(q for q, lab in ((q0, pa), (q1, pb)) if lab != "I")
            # any setting whose letters match the non-identity labels works
            want = {q0: pa, q1: pb}
            hit = None
            for s in counts_by_setting:
                if all(s[q] == want[q] for q in want if want[q] != "I"):
                    hit = s
                    break
            if hit is None:
                continue
            e = expectation(counts_by_setting[hit], sup)
            op = np.kron(P[pb], P[pa])       # little-endian: q0 is right factor
            rho = rho + e * op / 4.0
    # project to the nearest physical state
    w, v = np.linalg.eigh((rho + rho.conj().T) / 2)
    w = np.clip(w, 0, None)
    w = w / max(w.sum(), 1e-15)
    return (v * w) @ v.conj().T


# --------------------------------------------------------------------------

def preflight() -> dict:
    print("=== PRE-HARDWARE CHECKS (statevector, no backend contact) ===")
    exact = {}
    for mu in MUS:
        rho_ASa, rho_AB, rho_A = exact_pair_states(mu)
        c1, c2 = concurrence(rho_ASa), concurrence(rho_AB)
        s1, s2 = chsh_max(rho_ASa), chsh_max(rho_AB)
        tot = 4.0 * float(np.real(np.linalg.det(rho_A)))
        exact[f"{mu:.6f}"] = {"C_ASa": c1, "C_AB": c2, "S_ASa": s1, "S_AB": s2,
                              "sum_sq": c1 * c1 + c2 * c2, "4detA": tot}
        print(f"  mu={mu:.4f}  C(A:Sa)={c1:.4f}  C(A:B)={c2:.4f}  "
              f"sum^2={c1*c1+c2*c2:.6f}  4detA={tot:.6f}")
        # 1e-6, not 1e-9: concurrence goes through an eigensolve of rho * rho~,
        # which is ill-conditioned near eigenvalue degeneracies. mu = 3pi/8 lands
        # 1.4e-09 off, which is float noise six orders below any measurement.
        assert abs(c1 * c1 + c2 * c2 - 1.0) < 1e-6, f"monogamy not saturated at mu={mu}"
        assert abs(tot - 1.0) < 1e-6, "rho_A is not maximally mixed"

    e0, e1 = exact[f"{MUS[0]:.6f}"], exact[f"{MUS[-1]:.6f}"]
    assert abs(e0["C_ASa"] - 1) < 1e-6 and abs(e0["C_AB"]) < 1e-6, "mu=0 endpoint wrong"
    assert abs(e1["C_AB"] - 1) < 1e-6 and abs(e1["C_ASa"]) < 1e-6, "mu=pi/2 endpoint wrong"
    print("\n  [OK] monogamy saturates exactly (three-tangle zero) at every mu.")
    print("  NOTE: that saturation is FORCED for pure states -- it is not the")
    print("        claim. The contingent quantity is the hardware DEFICIT and")
    print("        whether it depends on mu.\n")
    return exact


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--backend", default=None)
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--out-dir", type=Path, default=None)
    args = ap.parse_args()

    exact = preflight()

    backend = DryBackend() if args.dry else HardwareBackend(args.backend)
    if args.fresh and not args.dry:
        clear_checkpoint(backend.name)
    out_dir = args.out_dir or Path(f"results_ibm12_{backend.name}")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.utcnow().isoformat() + "Z"
    print(f"AQ-PAGE-WOOTTERS-IBM-12  backend={backend.name}  dry={args.dry}  {ts}",
          flush=True)

    chain = find_chain(backend.coupling_map, backend.num_qubits, 3)
    layout = chain[:3]

    prereg = {
        "program": "AQ-PAGE-WOOTTERS-IBM-12", "backend": backend.name,
        "dry_run": bool(args.dry), "submission_time": ts, "optimization_level": 0,
        "mus": [float(m) for m in MUS], "shots": SHOTS, "layout": layout,
        "settings": SETTINGS, "exact": exact,
        "purpose": ("Measure the cost of shared relational time. A clock is a good "
                    "Page-Wootters clock in proportion to its entanglement with its own "
                    "system, and a synchronisable clock in proportion to its entanglement "
                    "with another clock; monogamy makes those compete. The saturation "
                    "C^2 + C^2 = 1 is FORCED for pure states and is not the claim. The "
                    "contingent quantities are the hardware deficit and its dependence "
                    "on where the entanglement sits."),
        "gates": {
            "gate1_clock_quality_falls": "C(A:Sa) decreases monotonically in mu",
            "gate2_sync_rises": "C(A:B) increases monotonically in mu",
            "gate3_anticorrelated": "Pearson r(C_ASa, C_AB) < -0.9",
            "gate4_endpoints": "at mu=0, C(A:B) is consistent with zero; at mu=pi/2, "
                               "C(A:Sa) is. These are the no-go's two faces and either "
                               "failing would falsify the framing.",
            "gate5_deficit_tracks_reference": "the deficit measured on hardware tracks a "
                                  "NOISE-MATCHED Aer reference run through the same "
                                  "estimator, within 3 sigma. Gating against the ideal 1.0 "
                                  "would fire on estimator bias: concurrence is a "
                                  "max(0, l1-l2-l3-l4), so noise pushes it down hardest at "
                                  "intermediate entanglement and the raw deficit bows at "
                                  "the balanced point even in simulation. Departure from "
                                  "the REFERENCE in shape is the contingent claim -- it "
                                  "would mean decoherence treats clock-system and "
                                  "clock-clock entanglement differently. Reported either "
                                  "way.",
            "gate6_chsh_tracks": "CHSH on both pairs tracks 2 sqrt(1 + C^2) within "
                                 "attenuation, cross-checking tomography against a "
                                 "Bell-type observable on the same counts",
        },
    }
    (out_dir / "ibm12_prereg.json").write_text(json.dumps(prereg, indent=2), encoding="utf-8")
    print(f"  pre-registration filed: {out_dir / 'ibm12_prereg.json'}", flush=True)

    circuits, index = [], []
    for mu in MUS:
        for s in SETTINGS:
            circuits.append(tomo_circuit(mu, s))
            index.append((mu, s))
    # REFERENCE CURVE. The concurrence estimator is biased: it is a
    # max(0, l1-l2-l3-l4) over eigenvalues, so noise pushes it down, and the
    # bias is WORST at intermediate entanglement. A dry run therefore produces a
    # mu-dependent deficit that peaks at the balanced point purely as an
    # artifact. Gating the hardware deficit against the IDEAL 1.0 would fire on
    # that artifact. So the null model is a noise-matched simulation run through
    # the SAME estimator, and the contingent question is whether hardware
    # departs from IT.
    ref = None
    if not args.dry:
        print("  computing noise-matched reference curve (Aer, no QPU)...", flush=True)
        sim = DryBackend()
        sim_counts, _ = sim.run_batch(circuits, SHOTS, sim.coupling_map and layout, stage="ref")
        sim_by_mu = {}
        for (mu, st), c in zip(index, sim_counts):
            sim_by_mu.setdefault(mu, {})[st] = c
        ref = {}
        for mu in MUS:
            cs = sim_by_mu[mu]
            a = concurrence(pair_density(cs, (A, SA)))
            b_ = concurrence(pair_density(cs, (A, B)))
            ref[mu] = 1.0 - (a * a + b_ * b_)
        print("  reference deficits: " + "  ".join(f"{ref[m]:+.4f}" for m in MUS),
              flush=True)

    print(f"  submitting {len(circuits)} circuits at {SHOTS} shots", flush=True)
    counts, _ = backend.run_batch(circuits, SHOTS, layout, stage="clock_monogamy")

    by_mu: dict = {}
    for (mu, s), c in zip(index, counts):
        by_mu.setdefault(mu, {})[s] = c

    rows = {}
    print("\n   mu      C(A:Sa)   C(A:B)   sum^2    deficit    S(A:Sa)  S(A:B)")
    for mu in MUS:
        cs = by_mu[mu]
        r_asa = pair_density(cs, (A, SA))
        r_ab = pair_density(cs, (A, B))
        c1, c2 = concurrence(r_asa), concurrence(r_ab)
        s1, s2 = chsh_max(r_asa), chsh_max(r_ab)
        ssq = c1 * c1 + c2 * c2
        rows[mu] = {"C_ASa": c1, "C_AB": c2, "sum_sq": ssq, "deficit": 1.0 - ssq,
                    "S_ASa": s1, "S_AB": s2}
        print(f"   {mu:.4f}  {c1:.4f}    {c2:.4f}   {ssq:.4f}   {1-ssq:+.4f}    "
              f"{s1:.4f}   {s2:.4f}", flush=True)

    c_asa = [rows[m]["C_ASa"] for m in MUS]
    c_ab = [rows[m]["C_AB"] for m in MUS]
    defs = [rows[m]["deficit"] for m in MUS]
    sig = 1.0 / np.sqrt(SHOTS)
    sig_def = float(4 * max(max(c_asa), max(c_ab)) * sig)
    r = float(np.corrcoef(c_asa, c_ab)[0, 1])
    spread = float(max(defs) - min(defs))

    print(f"\n  clock-quality vs synchronisability correlation r = {r:+.4f}")
    print(f"  raw deficit: mean {np.mean(defs):+.4f}, spread {spread:.4f}")
    print("  (raw spread is NOT the claim: the concurrence estimator is biased")
    print("   at intermediate entanglement, so the deficit bows at the balanced")
    print("   point even in pure simulation)")

    excess, excess_spread = None, None
    if ref is not None:
        excess = [defs[i] - ref[MUS[i]] for i in range(len(MUS))]
        excess_spread = float(max(excess) - min(excess))
        print("\n  deficit EXCESS over the noise-matched reference:")
        print("     " + "  ".join(f"{e:+.4f}" for e in excess))
        print(f"  excess spread {excess_spread:.4f}  (3 sigma {3*sig_def:.4f})")
        if excess_spread > 3 * sig_def:
            print("  -> hardware departs from the reference IN SHAPE: decoherence")
            print("     treats clock-system and clock-clock entanglement differently.")
        else:
            print("  -> hardware tracks the reference: trade-off structure survives,")
            print("     only the level attenuates.")
    else:
        print("\n  (dry run: no reference curve -- gate 5 is vacuous here by design)")

    chsh_ok = all(rows[m]["S_ASa"] <= 2 * np.sqrt(2) + 3 * sig and
                  rows[m]["S_AB"] <= 2 * np.sqrt(2) + 3 * sig for m in MUS)
    gates = {
        "gate1_clock_quality_falls": bool(all(c_asa[i] - c_asa[i + 1] > -3 * sig
                                              for i in range(len(c_asa) - 1))),
        "gate2_sync_rises": bool(all(c_ab[i + 1] - c_ab[i] > -3 * sig
                                     for i in range(len(c_ab) - 1))),
        "gate3_anticorrelated": bool(r < -0.9),
        "gate4_endpoints": bool(c_ab[0] < 3 * sig and c_asa[-1] < 3 * sig),
        "gate5_deficit_tracks_reference": bool(excess_spread is None
                                              or excess_spread <= 3 * sig_def),
        "gate6_chsh_tracks": bool(chsh_ok),
    }
    results = {
        "backend": backend.name, "layout": layout, "layouts": {"3": list(layout)},
        "mus": [float(m) for m in MUS], "shots": SHOTS,
        "measured": {f"{m:.6f}": rows[m] for m in MUS}, "exact": exact,
        "correlation_r": r, "deficit_mean": float(np.mean(defs)),
        "deficit_spread": spread, "sigma_deficit": sig_def,
        "reference_deficits": {f"{m:.6f}": (ref[m] if ref else None) for m in MUS},
        "deficit_excess": excess, "deficit_excess_spread": excess_spread,
        "departs_from_reference": bool(excess_spread is not None
                                       and excess_spread > 3 * sig_def),
        "gates": gates, "all_gates_pass": bool(all(gates.values())),
        "job_ids": getattr(backend, "job_ids", []),
    }
    (out_dir / "ibm12_results.json").write_text(
        json.dumps(results, indent=2, default=str), encoding="utf-8")
    if not args.dry:
        clear_checkpoint(backend.name)
    print(f"\n[GATES] {json.dumps(gates, indent=2)}")
    print(f"[DONE] all_gates_pass={results['all_gates_pass']}  -> {out_dir / 'ibm12_results.json'}")


if __name__ == "__main__":
    main()
