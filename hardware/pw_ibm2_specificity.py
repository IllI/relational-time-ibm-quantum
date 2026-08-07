#!/usr/bin/env python3
"""AQ-PAGE-WOOTTERS-IBM-2 -- adversarial specificity control + joint witness.

Tests the strongest unaddressed criticism of IBM-0/IBM-1: the inverse-QFT
readout depends ONLY on rho_C, so it cannot distinguish clock-system
entanglement from mere local clock coherence.

Adversarial state (arm E):

    |Phi> = (1/sqrt(d)) sum_t |t>_C (x) |0>_S

Coherent clock, ZERO clock-system correlation. Its clock marginal is the pure
state |f_0><f_0| with rho_C[t,t'] = 1/d for every pair -- maximal
off-diagonals. Under inverse QFT it collapses to a delta at k=0, so

    local witness TVD(P(k), uniform) = (d-1)/d   ->  0.75 (d=4), 0.875 (d=8)

versus the history state's 0.177 / 0.497 exact. A state with no entanglement
whatsoever outscores the actual history state. If that lands, the local
witness is demonstrated necessary-but-not-sufficient ON HARDWARE.

The fix, from the same counts: measure BOTH registers each shot (clock in the
Fourier basis, system in Z) and compute

    W_joint = TVD( p(k,z), p(k)p(z) )

which is exactly 0 for the coherent product state (system is |0> always, so
p(k,z) factorizes by construction) and -- verified numerically below -- also
0 for the classical mixture, while being nonzero for the history state.

SCOPE NOTE, stated up front: W_joint certifies clock-system CORRELATION in a
basis where the clock is read coherently. It is NOT claimed here as a formal
entanglement witness; establishing that requires an argument this run does not
make. The defensible claim is that W_joint separates the history state from
both adversarial controls where the local witness fails to.

Usage:
    python pw_ibm2_specificity.py --dry
    python pw_ibm2_specificity.py --backend ibm_marrakesh
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector

from pw_ibm1_dryrun import history_prep, inverse_qft
from pw_ibm1_submit import (
    DryBackend, HardwareBackend, checkpoint_path, clear_checkpoint, find_chain,
)

CLOCK_SIZES = (2, 3)          # d = 4, 8 -- d=2 adds nothing here
SHOTS_MAIN = 4000
SHOTS_CLASSICAL_SUB = 1000    # per definite-|t> sub-circuit


# --------------------------------------------------------------------------
# Circuits. All measure clock (Fourier basis) AND system (Z) in the same shot,
# so both the local and joint witnesses come from one set of counts.
# --------------------------------------------------------------------------

def build_history_joint(n_clock: int, pad_mu: float | None = None) -> QuantumCircuit:
    """Arm C/F: history state, iQFT clock, joint readout."""
    d = 2**n_clock
    clock, system = list(range(n_clock)), n_clock
    qc = QuantumCircuit(2 * n_clock + 1, n_clock + 1)
    history_prep(qc, clock, system, 2.0 * np.pi / d, None)
    if pad_mu is not None:
        for k, cq in enumerate(clock):
            qc.cry(pad_mu, cq, n_clock + 1 + k)
    inverse_qft(qc, clock)
    qc.measure(clock + [system], list(range(n_clock + 1)))
    return qc


def build_classical_joint(n_clock: int, t: int) -> QuantumCircuit:
    """Arm D: definite-|t> clock (classical mixture when averaged 1/d)."""
    d = 2**n_clock
    clock, system = list(range(n_clock)), n_clock
    qc = QuantumCircuit(2 * n_clock + 1, n_clock + 1)
    history_prep(qc, clock, system, 2.0 * np.pi / d, t)
    inverse_qft(qc, clock)
    qc.measure(clock + [system], list(range(n_clock + 1)))
    return qc


def build_product_coherent(n_clock: int, pad_mu: float | None = None) -> QuantumCircuit:
    """Arm E: coherent clock, system left in |0>. Zero clock-system
    correlation. pad_mu adds CRY gates so depth can be matched against the
    history arm rather than letting E win on being shallower."""
    clock, system = list(range(n_clock)), n_clock
    qc = QuantumCircuit(2 * n_clock + 1, n_clock + 1)
    qc.h(clock)
    if pad_mu is not None:
        for k, cq in enumerate(clock):
            qc.cry(pad_mu, cq, n_clock + 1 + k)
    inverse_qft(qc, clock)
    qc.measure(clock + [system], list(range(n_clock + 1)))
    return qc


# --------------------------------------------------------------------------
# Witnesses from joint counts. Bitstring is little-endian: rightmost char is
# clbit 0 = clock qubit 0; leftmost is the system.
# --------------------------------------------------------------------------

def joint_distribution(counts: dict[str, int], n_clock: int) -> np.ndarray:
    d = 2**n_clock
    p = np.zeros((d, 2))
    total = 0
    for bits, n in counts.items():
        b = bits.replace(" ", "")
        z, k = int(b[0]), int(b[1:], 2)
        p[k, z] += n
        total += n
    return p / max(total, 1)


def local_witness(p_joint: np.ndarray) -> float:
    """TVD of the clock marginal from uniform -- the IBM-0/IBM-1 witness."""
    p_k = p_joint.sum(axis=1)
    d = p_k.size
    return float(0.5 * np.sum(np.abs(p_k - 1.0 / d)))


def joint_witness(p_joint: np.ndarray) -> float:
    """TVD( p(k,z), p(k)p(z) ) -- certifies joint structure, not just rho_C."""
    p_k = p_joint.sum(axis=1, keepdims=True)
    p_z = p_joint.sum(axis=0, keepdims=True)
    return float(0.5 * np.sum(np.abs(p_joint - p_k * p_z)))


def expected_joint_floor(p_joint: np.ndarray, shots: int) -> float:
    """Shot-noise floor for the joint witness: TVD is positively biased, so
    a truly factorizing distribution cannot read exactly zero at finite N.
    Same folded-normal approximation used for the local witness elsewhere."""
    var = np.clip(p_joint * (1.0 - p_joint), 0.0, None) / max(shots, 1)
    return float(0.5 * np.sum(np.sqrt(var) * np.sqrt(2.0 / np.pi)))


# --------------------------------------------------------------------------
# Exact predictions, taken from the ACTUAL circuits via statevector -- not
# derived by hand. Hand-derivation is what produced the Fourier-basis bug
# caught in the IBM-0 dry run.
# --------------------------------------------------------------------------

def exact_from_circuit(qc: QuantumCircuit, n_clock: int) -> tuple[float, float]:
    stripped = qc.remove_final_measurements(inplace=False)
    sv = Statevector.from_instruction(stripped)
    probs = sv.probabilities_dict()
    d = 2**n_clock
    p = np.zeros((d, 2))
    for bits, pr in probs.items():
        b = bits.replace(" ", "")
        # statevector keys are over ALL qubits; clock = lowest n_clock, system = next
        idx = int(b, 2)
        k = idx & (d - 1)
        z = (idx >> n_clock) & 1
        p[k, z] += pr
    p = p / p.sum()
    return local_witness(p), joint_witness(p)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--backend", default=None)
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--out-dir", type=Path, default=None)
    args = ap.parse_args()

    # ---- Exact predictions first (free, and gates are set against them) ----
    print("=== EXACT PREDICTIONS (statevector, from the real circuits) ===")
    predictions = {}
    for n_clock in CLOCK_SIZES:
        d = 2**n_clock
        pred = {}
        for name, qc in (
            ("C_history", build_history_joint(n_clock)),
            ("E_product", build_product_coherent(n_clock)),
        ):
            lw, jw = exact_from_circuit(qc, n_clock)
            pred[name] = {"local": lw, "joint": jw}
        # classical mixture: average the d definite-|t> circuits
        p_cls = np.zeros((d, 2))
        for t in range(d):
            stripped = build_classical_joint(n_clock, t).remove_final_measurements(inplace=False)
            sv = Statevector.from_instruction(stripped)
            for bits, pr in sv.probabilities_dict().items():
                idx = int(bits.replace(" ", ""), 2)
                p_cls[idx & (d - 1), (idx >> n_clock) & 1] += pr / d
        p_cls /= p_cls.sum()
        pred["D_classical"] = {"local": local_witness(p_cls), "joint": joint_witness(p_cls)}
        pred["E_local_analytic_(d-1)/d"] = (d - 1) / d
        predictions[str(d)] = pred
        print(f"  d={d}:")
        for k in ("C_history", "D_classical", "E_product"):
            print(f"    {k:14s} local={pred[k]['local']:.4f}  joint={pred[k]['joint']:.4f}")
        print(f"    E local analytic (d-1)/d = {(d-1)/d:.4f}   "
              f"[specificity failure predicted: E_local > C_local = {pred['E_product']['local'] > pred['C_history']['local']}]")

    if args.dry is False and args.backend is None:
        pass

    backend = DryBackend() if args.dry else HardwareBackend(args.backend)
    if args.fresh and not args.dry:
        clear_checkpoint(backend.name)
    out_dir = args.out_dir or Path(f"results_ibm2_{backend.name}")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.utcnow().isoformat() + "Z"
    print(f"\nAQ-PAGE-WOOTTERS-IBM-2  backend={backend.name}  dry={args.dry}  {ts}", flush=True)

    layout8 = find_chain(backend.coupling_map, backend.num_qubits, 7)
    layouts = {"4": layout8[:5], "8": layout8}   # d=4 needs 5, d=8 needs 7

    prereg = {
        "program": "AQ-PAGE-WOOTTERS-IBM-2",
        "backend": backend.name, "dry_run": bool(args.dry), "submission_time": ts,
        "optimization_level": 0, "layouts": layouts,
        "shots_main": SHOTS_MAIN, "shots_classical_sub": SHOTS_CLASSICAL_SUB,
        "exact_predictions": predictions,
        "gates": {
            "gate1_specificity_failure": "arm E local witness > arm C local witness",
            "gate2_E_joint_near_zero": "arm E joint witness < 3x its own shot-noise floor",
            "gate3_F_joint_beats_E": "arm C(=F) joint witness > arm E joint + 3x floor",
            "gate4_separation_vs_inrun_baseline": "C local - D local > 3x floor, measured "
                                                  "against the IN-RUN classical baseline (the "
                                                  "IBM-0 Gate 3 correction), not an idealized uniform",
        },
    }
    (out_dir / "ibm2_prereg.json").write_text(json.dumps(prereg, indent=2), encoding="utf-8")
    print(f"  pre-registration filed: {out_dir / 'ibm2_prereg.json'}", flush=True)

    results: dict = {"backend": backend.name, "layouts": layouts,
                     "exact_predictions": predictions, "arms": {}}
    gates: dict[str, bool] = {}

    for n_clock in CLOCK_SIZES:
        d = 2**n_clock
        layout = layouts[str(d)]
        print(f"\n=== d={d} ===", flush=True)

        singles = [
            build_history_joint(n_clock),          # C / F
            build_product_coherent(n_clock),       # E
            build_product_coherent(n_clock, pad_mu=0.0),   # E depth-padded
        ]
        s_counts, s_tqc = backend.run_batch(singles, SHOTS_MAIN, layout, stage=f"singles_d{d}")

        cls_circuits = [build_classical_joint(n_clock, t) for t in range(d)]
        c_counts, _ = backend.run_batch(cls_circuits, SHOTS_CLASSICAL_SUB, layout, stage=f"classical_d{d}")

        p_C = joint_distribution(s_counts[0], n_clock)
        p_E = joint_distribution(s_counts[1], n_clock)
        p_Epad = joint_distribution(s_counts[2], n_clock)
        p_D = np.zeros((d, 2))
        for t in range(d):
            p_D += joint_distribution(c_counts[t], n_clock) / d

        arm = {}
        for name, p, shots in (("C_history", p_C, SHOTS_MAIN),
                               ("E_product", p_E, SHOTS_MAIN),
                               ("E_product_padded", p_Epad, SHOTS_MAIN),
                               ("D_classical", p_D, SHOTS_CLASSICAL_SUB * d)):
            arm[name] = {
                "local_witness": local_witness(p),
                "joint_witness": joint_witness(p),
                "joint_floor": expected_joint_floor(p, shots),
                "p_joint": p.tolist(),
            }
        results["arms"][str(d)] = arm

        for k in ("C_history", "D_classical", "E_product", "E_product_padded"):
            a = arm[k]
            print(f"  {k:18s} local={a['local_witness']:.4f}  joint={a['joint_witness']:.4f}  "
                  f"(joint floor {a['joint_floor']:.4f})", flush=True)

        gates[f"gate1_specificity_failure_d{d}"] = bool(
            arm["E_product"]["local_witness"] > arm["C_history"]["local_witness"]
        )
        gates[f"gate2_E_joint_near_zero_d{d}"] = bool(
            arm["E_product"]["joint_witness"] < 3 * arm["E_product"]["joint_floor"]
        )
        gates[f"gate3_F_joint_beats_E_d{d}"] = bool(
            arm["C_history"]["joint_witness"]
            > arm["E_product"]["joint_witness"] + 3 * arm["C_history"]["joint_floor"]
        )
        sep = arm["C_history"]["local_witness"] - arm["D_classical"]["local_witness"]
        floor_sep = 3 * (arm["C_history"]["joint_floor"] + arm["D_classical"]["joint_floor"])
        gates[f"gate4_separation_vs_inrun_baseline_d{d}"] = bool(sep > floor_sep)
        results["arms"][str(d)]["separation_C_minus_D"] = sep

    results["gates"] = gates
    results["all_gates_pass"] = bool(all(gates.values()))
    results["job_ids"] = getattr(backend, "job_ids", [])
    (out_dir / "ibm2_results.json").write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    if not args.dry:
        clear_checkpoint(backend.name)
    print(f"\n[GATES] {json.dumps(gates, indent=2)}")
    print(f"[DONE] all_gates_pass={results['all_gates_pass']}  -> {out_dir / 'ibm2_results.json'}")


if __name__ == "__main__":
    main()
