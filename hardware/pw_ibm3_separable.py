#!/usr/bin/env python3
"""AQ-PAGE-WOOTTERS-IBM-3 -- is W_joint an entanglement witness? (No.)

IBM-2 showed the LOCAL clock-marginal witness is necessary-but-not-sufficient
(a zero-entanglement coherent product state outscores the history state on it),
and introduced W_joint = TVD(p(k,z), p(k)p(z)) as the fix. IBM-2's results doc
scoped W_joint carefully:

    "NOT claimed here as a formal entanglement witness; establishing that
     requires an argument this run does not make (in particular, ruling out
     separable mixed states that could produce nonzero W_joint)."

That was an assertion, not a measurement. This run measures it.

ADVERSARIAL SEPARABLE STATE:

    rho_sep = (1/2) |f_0><f_0|_C (x) |0><0|_S  +  (1/2) |f_1><f_1|_C (x) |1><1|_S

A classical 50/50 mixture of two PRODUCT states. Zero entanglement by
construction (a separable state is a convex mixture of products). But it has
BOTH clock coherence (each branch's clock is a pure Fourier state) AND
clock-system correlation (which clock state you have is perfectly correlated
with the system bit).

|f_0> = (1/sqrt d) sum_t |t>          -> inverse QFT -> delta at k=0
|f_1> = (1/sqrt d) sum_t e^{2 pi i t/d} |t>  -> inverse QFT -> delta at k=1

so conditioned on z=0 the clock reads k=0, and on z=1 it reads k=1:

    p(k,z) = (1/2) delta_{k0} delta_{z0} + (1/2) delta_{k1} delta_{z1}
    p(k)p(z) = 1/4 on each of (k,z) in {0,1}x{0,1}
    W_joint = 0.5 * 4 * (1/4) = 0.5

PREDICTION: W_joint = 0.5 for this SEPARABLE state, versus 0.379 (exact) for
the entangled history state. A state with no entanglement scores HIGHER on
W_joint than the history state does -- the same failure mode IBM-2 found for
the local witness, now demonstrated for its replacement.

If that lands, the honest conclusion is that BOTH witnesses in this program
certify structure (coherence; coherence-plus-correlation) rather than
entanglement, and no observable measured across IBM-0/1/2/3 certifies the
Page-Wootters structure specifically. That is a limitation worth publishing
explicitly rather than leaving for a referee to find.

Usage:
    python pw_ibm3_separable.py --dry
    python pw_ibm3_separable.py --backend ibm_marrakesh
"""

from __future__ import annotations

import argparse
import datetime
import json
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from pw_ibm1_dryrun import inverse_qft
from pw_ibm1_submit import DryBackend, HardwareBackend, clear_checkpoint, find_chain
from pw_ibm2_specificity import (
    build_history_joint, expected_joint_floor, joint_distribution,
    joint_witness, local_witness,
)

CLOCK_SIZES = (2, 3)
SHOTS_SUB = 4000   # per branch; two branches averaged 50/50


def build_separable_branch(n_clock: int, branch: int) -> QuantumCircuit:
    """One product branch of rho_sep.

    branch 0: clock -> |f_0> (uniform), system |0>
    branch 1: clock -> |f_1> (phase ramp e^{2 pi i t / d}), system |1>

    Averaging the two 50/50 realizes the separable mixture. Each branch is
    individually a PRODUCT state, so the mixture is separable by construction
    -- no entanglement anywhere, at any stage.
    """
    d = 2**n_clock
    clock, system = list(range(n_clock)), n_clock
    qc = QuantumCircuit(n_clock + 1, n_clock + 1)
    qc.h(clock)
    if branch == 1:
        # phase ramp: t = sum_k b_k 2^k, so e^{2 pi i t/d} = prod_k e^{2 pi i b_k 2^k / d}
        for k, cq in enumerate(clock):
            qc.p(2.0 * np.pi * (2**k) / d, cq)
        qc.x(system)
    inverse_qft(qc, clock)
    qc.measure(clock + [system], list(range(n_clock + 1)))
    return qc


def exact_separable(n_clock: int) -> tuple[float, float]:
    d = 2**n_clock
    p = np.zeros((d, 2))
    for branch in (0, 1):
        qc = build_separable_branch(n_clock, branch).remove_final_measurements(inplace=False)
        sv = Statevector.from_instruction(qc)
        for bits, pr in sv.probabilities_dict().items():
            idx = int(bits.replace(" ", ""), 2)
            p[idx & (d - 1), (idx >> n_clock) & 1] += pr / 2.0
    p /= p.sum()
    return local_witness(p), joint_witness(p)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--backend", default=None)
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--out-dir", type=Path, default=None)
    args = ap.parse_args()

    print("=== EXACT PREDICTIONS (statevector) ===")
    preds = {}
    for n_clock in CLOCK_SIZES:
        d = 2**n_clock
        sl, sj = exact_separable(n_clock)
        hqc = build_history_joint(n_clock).remove_final_measurements(inplace=False)
        sv = Statevector.from_instruction(hqc)
        ph = np.zeros((d, 2))
        for bits, pr in sv.probabilities_dict().items():
            idx = int(bits.replace(" ", ""), 2)
            ph[idx & (d - 1), (idx >> n_clock) & 1] += pr
        ph /= ph.sum()
        hl, hj = local_witness(ph), joint_witness(ph)
        preds[str(d)] = {"separable": {"local": sl, "joint": sj},
                         "history": {"local": hl, "joint": hj}}
        print(f"  d={d}:  separable local={sl:.4f} joint={sj:.4f}   "
              f"history local={hl:.4f} joint={hj:.4f}")
        print(f"        -> separable joint EXCEEDS history joint: {sj > hj}")

    backend = DryBackend() if args.dry else HardwareBackend(args.backend)
    if args.fresh and not args.dry:
        clear_checkpoint(backend.name)
    out_dir = args.out_dir or Path(f"results_ibm3_{backend.name}")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.utcnow().isoformat() + "Z"
    print(f"\nAQ-PAGE-WOOTTERS-IBM-3  backend={backend.name}  dry={args.dry}  {ts}", flush=True)

    layout7 = find_chain(backend.coupling_map, backend.num_qubits, 7)
    layouts = {"4": layout7[:3], "8": layout7[:4]}   # n_clock+1 qubits, no env register

    prereg = {
        "program": "AQ-PAGE-WOOTTERS-IBM-3", "backend": backend.name,
        "dry_run": bool(args.dry), "submission_time": ts, "optimization_level": 0,
        "layouts": layouts, "shots_per_branch": SHOTS_SUB,
        "exact_predictions": preds,
        "gates": {
            "gate1_separable_joint_fires": "separable W_joint > 3x its own shot-noise floor "
                                           "-> W_joint is NOT an entanglement witness",
            "gate2_separable_joint_exceeds_history": "separable W_joint > history W_joint "
                                                     "-> same failure mode IBM-2 found for the local witness",
        },
    }
    (out_dir / "ibm3_prereg.json").write_text(json.dumps(prereg, indent=2), encoding="utf-8")
    print(f"  pre-registration filed: {out_dir / 'ibm3_prereg.json'}", flush=True)

    results = {"backend": backend.name, "layouts": layouts,
               "exact_predictions": preds, "arms": {}}
    gates = {}

    for n_clock in CLOCK_SIZES:
        d = 2**n_clock
        layout = layouts[str(d)]
        print(f"\n=== d={d} ===", flush=True)

        circuits = [build_separable_branch(n_clock, 0), build_separable_branch(n_clock, 1),
                    build_history_joint(n_clock)]
        # history circuit uses 2*n_clock+1 qubits; run it on its own wider layout
        sep_counts, _ = backend.run_batch(circuits[:2], SHOTS_SUB, layout, stage=f"separable_d{d}")
        hist_counts, _ = backend.run_batch([circuits[2]], SHOTS_SUB,
                                           layout7[:2 * n_clock + 1], stage=f"history_d{d}")

        p_sep = (joint_distribution(sep_counts[0], n_clock)
                 + joint_distribution(sep_counts[1], n_clock)) / 2.0
        p_hist = joint_distribution(hist_counts[0], n_clock)

        arm = {}
        for name, p in (("separable", p_sep), ("history", p_hist)):
            arm[name] = {"local_witness": local_witness(p), "joint_witness": joint_witness(p),
                         "joint_floor": expected_joint_floor(p, SHOTS_SUB * (2 if name == "separable" else 1)),
                         "p_joint": p.tolist()}
            a = arm[name]
            print(f"  {name:10s} local={a['local_witness']:.4f}  joint={a['joint_witness']:.4f}  "
                  f"(floor {a['joint_floor']:.4f}, J/floor={a['joint_witness']/max(a['joint_floor'],1e-9):.1f})",
                  flush=True)
        results["arms"][str(d)] = arm

        gates[f"gate1_separable_joint_fires_d{d}"] = bool(
            arm["separable"]["joint_witness"] > 3 * arm["separable"]["joint_floor"])
        gates[f"gate2_separable_joint_exceeds_history_d{d}"] = bool(
            arm["separable"]["joint_witness"] > arm["history"]["joint_witness"])

    results["gates"] = gates
    results["all_gates_pass"] = bool(all(gates.values()))
    results["job_ids"] = getattr(backend, "job_ids", [])
    (out_dir / "ibm3_results.json").write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    if not args.dry:
        clear_checkpoint(backend.name)
    print(f"\n[GATES] {json.dumps(gates, indent=2)}")
    print(f"[DONE] all_gates_pass={results['all_gates_pass']}  -> {out_dir / 'ibm3_results.json'}")


if __name__ == "__main__":
    main()
