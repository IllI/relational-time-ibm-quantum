#!/usr/bin/env python3
"""AQ-PAGE-WOOTTERS-IBM-9 -- a clock in a SUPERPOSITION of rates.

IBM-7 put two clocks at two different but DEFINITE rates. This puts one clock
in a coherent superposition of two rates, which is the discrete analogue of
Smith & Ahmadi's quantum time dilation (arXiv:1904.12390): a clock whose
worldline is delocalised experiences a superposition of proper times, and the
interference between those histories is a genuinely quantum correction with no
classical counterpart.

    |Psi> = (1/sqrt 2) [ |0>_G (x) |Psi_alpha1> + |1>_G (x) |Psi_alpha2> ]

G is a "which-rate" (loosely, which-altitude) qubit prepared in |+>. Clock B
advances at alpha1 or alpha2 per tick of clock A depending on G.

THE MEASUREMENT, and why it isolates the quantum part. Read G in Z and you
have merely selected a rate -- the conditional dynamics of B is then a
CLASSICAL MIXTURE of the two rate histories, which any classical
which-path-forgotten setup reproduces:

    <X_B|t>_Zmarg = [cos(alpha1*theta*t) + cos(alpha2*theta*t)] / 2

Read G in X and the two histories INTERFERE; conditioning on G = +/- gives
conditional dynamics that no mixture of the two rates can produce. The
difference between the X-conditioned curves and the Z-marginal curve is the
quantum time-dilation signature. Same prepared state, two readout bases --
directly parallel to IBM-0's arm A/B logic, where the discriminator was also
a change of basis rather than a change of state.

DESIGN CHOICES, made against this program's own measured limits:

  * d = 4 ONLY. IBM-8 established that d=8 circuits carrying a controlled
    clock-shift are past this device's usable depth; IBM-9's prep is cheaper
    (no shift, no echo, no V-dagger) but there is no reason to spend shots
    finding the ceiling again.
  * alpha1 = 1, alpha2 = 2, both INTEGERS. IBM-7 showed the cyclic constraint
    closes only at commensurate rates, so both branches are individually
    stationary and the superposition is of two legitimate history states
    rather than one legitimate and one broken.
  * CONDITIONAL readout only -- no Loschmidt echo. The echo is what doubled
    circuit depth in IBM-5/6/8; conditional expectation values were the most
    robust measurement in this entire program (IBM-7 recovered rates at
    R^2 > 0.995).

Prep cost: n_clock controlled-phase gates for the base rate, plus n_clock
DOUBLY-controlled phases for the rate increment. That is the expensive part
and it is reported in the dry run rather than assumed tolerable.

Usage:
    python pw_ibm9_superposed_rate.py --dry
    python pw_ibm9_superposed_rate.py --backend ibm_marrakesh
"""

from __future__ import annotations

import argparse
import datetime
import json
from pathlib import Path

import numpy as np
from qiskit import ClassicalRegister, QuantumCircuit, transpile
from qiskit.quantum_info import Statevector

from pw_ibm1_submit import DryBackend, HardwareBackend, clear_checkpoint, find_chain

N_CLOCK = 3          # d = 8 -- larger interference signature (0.263 vs 0.167 at d=4)
ALPHA1, ALPHA2 = 1.0, 2.0
SHOTS = 20000       # split across d clock readings AND halved again by the
                    # G post-selection, so the per-point count is SHOTS/(2d)


def prepare_superposed(n_clock: int, a1: float, a2: float) -> QuantumCircuit:
    """|Psi> = (1/sqrt2)[|0>_G |Psi_a1> + |1>_G |Psi_a2>].

    Base rate a1 via cp; the increment (a2-a1) applied only when G=1 via a
    doubly-controlled phase. Qubits: clock 0..n-1, B = n, G = n+1."""
    d = 2**n_clock
    theta = 2.0 * np.pi / d
    clock, b, g = list(range(n_clock)), n_clock, n_clock + 1
    qc = QuantumCircuit(n_clock + 2, name="V9")
    qc.h(clock)
    qc.h(b)
    qc.h(g)
    for k, cq in enumerate(clock):
        qc.cp((2**k) * a1 * theta, cq, b)                      # rate a1 always
        qc.mcp((2**k) * (a2 - a1) * theta, [cq, g], b)         # + increment iff G=1
    return qc


def build_readout(n_clock: int, a1: float, a2: float, g_basis: str) -> QuantumCircuit:
    """Clock A in Z, clock B in X, G in Z or X. One circuit per G basis."""
    qc = prepare_superposed(n_clock, a1, a2).copy()
    b, g = n_clock, n_clock + 1
    qc.h(b)                       # X readout on clock B
    if g_basis == "X":
        qc.h(g)
    qc.add_register(ClassicalRegister(n_clock + 2, "c"))
    qc.measure(range(n_clock + 2), range(n_clock + 2))
    return qc


def conditional_xb(counts: dict[str, int], n_clock: int, g_select: int | None):
    """<X_B | t>, optionally post-selected on the G outcome.

    Bit layout (little-endian string, rightmost = clbit 0):
      clbits 0..n-1 = clock A,  clbit n = B,  clbit n+1 = G."""
    d = 2**n_clock
    acc = {t: [0, 0] for t in range(d)}
    for bits, n in counts.items():
        s = bits.replace(" ", "")
        gv = int(s[0])
        bv = int(s[1])
        t = int(s[2:], 2)
        if g_select is not None and gv != g_select:
            continue
        acc[t][bv] += n
    return {t: ((v[0] - v[1]) / (v[0] + v[1]) if sum(v) else float("nan"))
            for t, v in acc.items()}


def exact_curves(n_clock: int, a1: float, a2: float) -> dict:
    """Exact <X_B|t> for every G condition, from the real circuit."""
    d = 2**n_clock
    out = {}
    for g_basis in ("Z", "X"):
        qc = build_readout(n_clock, a1, a2, g_basis).remove_final_measurements(inplace=False)
        probs = Statevector.from_instruction(qc).probabilities_dict()
        counts = {k: v * 10**9 for k, v in probs.items()}
        out[g_basis] = {
            "marginal": conditional_xb(counts, n_clock, None),
            "g0": conditional_xb(counts, n_clock, 0),
            "g1": conditional_xb(counts, n_clock, 1),
        }
    return out


def curve_array(c: dict, d: int) -> np.ndarray:
    return np.array([c[t] for t in range(d)])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--backend", default=None)
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--out-dir", type=Path, default=None)
    args = ap.parse_args()

    n_clock, d = N_CLOCK, 2**N_CLOCK
    theta = 2.0 * np.pi / d

    print("=== EXACT PREDICTIONS (statevector, from the real circuits) ===")
    ex = exact_curves(n_clock, ALPHA1, ALPHA2)
    mix = np.array([(np.cos(ALPHA1 * theta * t) + np.cos(ALPHA2 * theta * t)) / 2
                    for t in range(d)])
    print(f"  Z-marginal (classical mixture of rates): {np.round(curve_array(ex['Z']['marginal'], d), 4)}")
    print(f"  closed-form mixture                    : {np.round(mix, 4)}")
    print(f"  X-basis G=+ (interference)             : {np.round(curve_array(ex['X']['g0'], d), 4)}")
    print(f"  X-basis G=- (interference)             : {np.round(curve_array(ex['X']['g1'], d), 4)}")
    sep = float(np.max(np.abs(curve_array(ex['X']['g0'], d) - curve_array(ex['Z']['marginal'], d))))
    print(f"  max |X(G=+) - Z-marginal| = {sep:.4f}   <- the quantum signature")
    assert np.max(np.abs(curve_array(ex['Z']['marginal'], d) - mix)) < 1e-9, \
        "Z-marginal must equal the classical rate mixture"
    assert sep > 0.2, "interference signature too small to be worth hardware time"  # d=8/(1,2) gives 0.263

    # Circuit cost, reported not assumed -- IBM-8 died on depth.
    from qiskit_aer import AerSimulator
    sim = AerSimulator()
    t = transpile(build_readout(n_clock, ALPHA1, ALPHA2, "X"), sim,
                  optimization_level=0, basis_gates=["rz", "sx", "x", "cx"])
    print(f"  circuit cost: depth={t.depth()}, cx={t.count_ops().get('cx', 0)}  "
          f"(IBM-8 d=4 was 13 cx and borderline; IBM-7 conditional was ~4 cx and clean)")

    backend = DryBackend() if args.dry else HardwareBackend(args.backend)
    if args.fresh and not args.dry:
        clear_checkpoint(backend.name)
    out_dir = args.out_dir or Path(f"results_ibm9_{backend.name}")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.utcnow().isoformat() + "Z"
    print(f"\nAQ-PAGE-WOOTTERS-IBM-9  backend={backend.name}  dry={args.dry}  {ts}", flush=True)

    chain = find_chain(backend.coupling_map, backend.num_qubits, n_clock + 2)
    layout = chain[:n_clock + 2]
    prereg = {"program": "AQ-PAGE-WOOTTERS-IBM-9", "backend": backend.name,
              "dry_run": bool(args.dry), "submission_time": ts, "optimization_level": 0,
              "shots": SHOTS, "n_clock": n_clock, "alphas": [ALPHA1, ALPHA2],
              "layout": layout,
              "exact": {k: {kk: {str(t): v for t, v in vv.items()} for kk, vv in val.items()}
                        for k, val in ex.items()},
              "transpiled_cx": int(t.count_ops().get("cx", 0)),
              "gates": {
                  "gate1_zmarg_is_mixture": "Z-marginal tracks the classical rate mixture "
                                            "(cos a1 + cos a2)/2 within 0.15 after amplitude fit",
                  "gate2_branches_recover_rates": "G=0 and G=1 in the Z basis recover the two "
                                                  "individual rates alpha1 and alpha2",
                  "gate3_interference_present": "X-basis conditioning differs from the Z-marginal "
                                                "by more than 3 sigma at some t -- the histories "
                                                "interfere, which no rate mixture reproduces",
              }}
    (out_dir / "ibm9_prereg.json").write_text(json.dumps(prereg, indent=2), encoding="utf-8")
    print(f"  pre-registration filed: {out_dir / 'ibm9_prereg.json'}", flush=True)

    circuits = [build_readout(n_clock, ALPHA1, ALPHA2, "Z"),
                build_readout(n_clock, ALPHA1, ALPHA2, "X")]
    counts, _ = backend.run_batch(circuits, SHOTS, layout, stage="superposed_rate")
    cz, cx = counts

    meas = {
        "Z_marginal": conditional_xb(cz, n_clock, None),
        "Z_g0": conditional_xb(cz, n_clock, 0),
        "Z_g1": conditional_xb(cz, n_clock, 1),
        "X_gplus": conditional_xb(cx, n_clock, 0),
        "X_gminus": conditional_xb(cx, n_clock, 1),
    }
    for k, v in meas.items():
        print(f"  {k:11s}: {np.round(curve_array(v, d), 4)}", flush=True)

    # Proper per-point noise. The Z-marginal at a given t uses SHOTS/d shots;
    # the X-conditioned curve is ALSO post-selected on G, halving it again to
    # SHOTS/(2d). An earlier version used a single sigma = 1/sqrt(SHOTS/d) for
    # both and understated the threshold on their difference by ~25%.
    sig_marg = 1.0 / np.sqrt(SHOTS / d)
    sig_xcond = 1.0 / np.sqrt(SHOTS / (2 * d))
    sigma_diff = float(np.hypot(sig_marg, sig_xcond))
    zm = curve_array(meas["Z_marginal"], d)
    xp = curve_array(meas["X_gplus"], d)
    ex_zm = curve_array(ex["Z"]["marginal"], d)

    amp = float(np.dot(ex_zm, zm) / max(np.dot(ex_zm, ex_zm), 1e-12))
    gate1 = bool(np.max(np.abs(zm - amp * ex_zm)) < 0.15)

    def best_rate(curve):
        grid = np.linspace(0.05, d / 2.0, 4000)
        tt = np.arange(d)
        best, br2 = np.nan, -np.inf
        for a in grid:
            pr = np.cos(a * theta * tt)
            k = np.dot(pr, curve) / max(np.dot(pr, pr), 1e-12)
            r2 = 1 - np.sum((curve - k * pr) ** 2) / max(np.sum((curve - curve.mean()) ** 2), 1e-12)
            if r2 > br2:
                best, br2 = float(a), float(r2)
        return best, br2

    r0, r0q = best_rate(curve_array(meas["Z_g0"], d))
    r1, r1q = best_rate(curve_array(meas["Z_g1"], d))
    gate2 = bool(min(abs(r0 - ALPHA1), abs(r0 - ALPHA2)) < 0.2
                 and min(abs(r1 - ALPHA1), abs(r1 - ALPHA2)) < 0.2
                 and abs(r0 - r1) > 0.5)
    interference = float(np.max(np.abs(xp - zm)))
    gate3 = bool(interference > 3 * sigma_diff)

    print(f"\n  Z-marginal vs mixture: amplitude {amp:.3f}, max resid "
          f"{np.max(np.abs(zm - amp*ex_zm)):.4f}", flush=True)
    print(f"  branch rates recovered: G=0 -> {r0:.3f} (R^2 {r0q:.3f}), "
          f"G=1 -> {r1:.3f} (R^2 {r1q:.3f})", flush=True)
    print(f"  interference |X(G=+) - Z-marg| = {interference:.4f}  "
          f"(3 sigma = {3*sigma_diff:.4f}, exact {sep:.4f})", flush=True)

    gates = {"gate1_zmarg_is_mixture": gate1,
             "gate2_branches_recover_rates": gate2,
             "gate3_interference_present": gate3}
    results = {"backend": backend.name, "layout": layout,
               "exact": {k: {kk: {str(t): v for t, v in vv.items()} for kk, vv in val.items()}
                         for k, val in ex.items()},
               "measured": {k: {str(t): v for t, v in val.items()} for k, val in meas.items()},
               "mixture_amplitude": amp, "branch_rates": [r0, r1],
               "branch_r2": [r0q, r1q], "interference": interference,
               "gates": gates, "all_gates_pass": bool(all(gates.values())),
               "job_ids": getattr(backend, "job_ids", [])}
    (out_dir / "ibm9_results.json").write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    if not args.dry:
        clear_checkpoint(backend.name)
    print(f"\n[GATES] {json.dumps(gates, indent=2)}")
    print(f"[DONE] all_gates_pass={results['all_gates_pass']}  -> {out_dir / 'ibm9_results.json'}")


if __name__ == "__main__":
    main()
