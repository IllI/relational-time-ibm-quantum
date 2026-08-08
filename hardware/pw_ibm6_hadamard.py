#!/usr/bin/env python3
"""AQ-PAGE-WOOTTERS-IBM-6 -- closing the phase-blindness gap in IBM-5.

IBM-5 measured a Loschmidt echo, |<Psi|A|Psi>|^2, and found it consistent
with 1 for A = S (x) U. That certifies |Psi> is an EIGENVECTOR of the joint
operator. It does NOT certify the eigenvalue is +1: a state with
A|Psi> = e^{i phi}|Psi>, phi != 0, returns exactly the same echo.

WHY THE PHASE IS NOT COSMETIC. The Wheeler-DeWitt constraint is H|Psi> = 0 --
ZERO eigenvalue, not an arbitrary one. In generator language a nonzero phi
means J|Psi> = (phi/dtau)|Psi> != 0: an eigenstate of the joint evolution
carrying nonzero "energy", which is NOT the constraint. Relational dynamics
would still work, but the strict WDW analogue would fail. IBM-5's own
limitations section records this.

THE FIX: a Hadamard test. With an ancilla in |+>, a controlled-A, and a
final H on the ancilla,

    P(ancilla = 0) - P(ancilla = 1) = Re <Psi|A|Psi>

and inserting S-dagger on the ancilla before the final H yields Im <Psi|A|Psi>
instead. Together they give the COMPLEX amplitude, hence the eigenvalue's
phase, which the echo discards.

PREDICTION: Re = +1, Im = 0, phase = 0 exactly (verified by statevector in
IBM-5's follow-up: <Psi|(S(x)U)|Psi> = 1.000000 + 0j, |phase| ~ 1e-17).
Controls reuse IBM-5's mismatched pairings, and they expose a genuine blind
spot of the echo. clock_only (S (x) I) and system_only (I (x) U) have
IDENTICAL modulus -- cos^2(theta/2) at every d -- so the echo cannot tell them
apart even in principle. Their amplitudes are complex conjugates:
(1 + e^{-i theta})/2 versus (1 + e^{+i theta})/2. The Hadamard test separates
them by the SIGN of Im<Psi|A|Psi>, which encodes the DIRECTION of the
mismatch (clock ran ahead of the system, or the system ahead of the clock).
That is information the modulus-only echo discards entirely.

(An earlier draft of this file asserted the wrong_way arm has a negative real
part at d=8. That was wrong -- it is +0.5 - 0.5i, verified by statevector --
and the pre-registered gate built on it failed on the first dry run. Recorded
because the gate failing loudly is the discipline working.)

COST NOTE: controlled-(S (x) U) is more expensive than S (x) U, because the
clock increment's MCX cascade gains a control each. At d=4 the ladder is
Toffoli + CX; at d=8 it needs a 3-controlled X. d=4 is the primary case.

Usage:
    python pw_ibm6_hadamard.py --dry
    python pw_ibm6_hadamard.py --backend ibm_marrakesh
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
from pw_ibm5_constraint import prepare_history

CLOCK_SIZES = (2, 3)
SHOTS = 4000
ARMS = (("joint", True, 1), ("clock_only", True, 0),
        ("system_only", False, 1), ("wrong_way", True, -1))


def controlled_clock_shift(qc: QuantumCircuit, ctrl: int, clock: list[int]) -> None:
    """Controlled cyclic increment: every MCX in the ripple gains `ctrl`."""
    n = len(clock)
    for k in range(n - 1, 0, -1):
        qc.mcx([ctrl] + clock[:k], clock[k])
    qc.cx(ctrl, clock[0])


def build_hadamard_test(n_clock: int, shift: bool, evolve: int,
                        imaginary: bool) -> QuantumCircuit:
    """Ancilla |+> -> controlled-(S^shift (x) U^evolve) -> [S-dagger] -> H -> measure.

    <Z_ancilla> = Re <Psi|A|Psi>   (imaginary=False)
                = Im <Psi|A|Psi>   (imaginary=True)
    """
    d = 2**n_clock
    theta = 2.0 * np.pi / d
    clock, system, anc = list(range(n_clock)), n_clock, n_clock + 1
    qc = QuantumCircuit(n_clock + 2)
    qc.compose(prepare_history(n_clock), qubits=list(range(n_clock + 1)), inplace=True)
    qc.h(anc)
    if shift:
        controlled_clock_shift(qc, anc, clock)
    if evolve != 0:
        qc.cp(theta if evolve == 1 else -theta, anc, system)
    if imaginary:
        qc.sdg(anc)
    qc.h(anc)
    qc.add_register(ClassicalRegister(1, "c"))
    qc.measure(anc, 0)
    return qc


def z_expectation(counts: dict[str, int]) -> float:
    total = sum(counts.values())
    p0 = sum(v for k, v in counts.items() if k.replace(" ", "")[-1] == "0")
    return (2.0 * p0 - total) / max(total, 1)


def exact_amplitude(n_clock: int, shift: bool, evolve: int) -> complex:
    """<Psi|A|Psi> by statevector -- the quantity the echo could not access."""
    d = 2**n_clock
    theta = 2.0 * np.pi / d
    psi = Statevector.from_instruction(prepare_history(n_clock)).data
    qc = prepare_history(n_clock).copy()
    if shift:
        from pw_ibm5_constraint import clock_shift
        clock_shift(qc, list(range(n_clock)))
    if evolve != 0:
        qc.p(theta if evolve == 1 else -theta, n_clock)
    return complex(np.vdot(psi, Statevector.from_instruction(qc).data))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--backend", default=None)
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--out-dir", type=Path, default=None)
    args = ap.parse_args()

    print("=== EXACT AMPLITUDES (statevector) -- what the echo threw away ===")
    preds = {}
    for n_clock in CLOCK_SIZES:
        d = 2**n_clock
        block = {}
        for name, sh, ev in ARMS:
            a = exact_amplitude(n_clock, sh, ev)
            block[name] = {"re": a.real, "im": a.imag,
                           "abs2": float(abs(a) ** 2), "phase": float(np.angle(a))}
        preds[str(d)] = block
        print(f"  d={d}:")
        for name in block:
            b = block[name]
            print(f"    {name:12s} Re={b['re']:+.4f}  Im={b['im']:+.4f}  "
                  f"|A|^2={b['abs2']:.4f}  phase={b['phase']:+.3f}")
        j = block["joint"]
        assert abs(j["re"] - 1.0) < 1e-9 and abs(j["im"]) < 1e-9, \
            "joint amplitude is not exactly +1; the constraint claim would be wrong"
        print(f"    -> joint eigenvalue is exactly +1 (WDW-analogue constraint holds)")

    backend = DryBackend() if args.dry else HardwareBackend(args.backend)
    if args.fresh and not args.dry:
        clear_checkpoint(backend.name)
    out_dir = args.out_dir or Path(f"results_ibm6_{backend.name}")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.utcnow().isoformat() + "Z"
    print(f"\nAQ-PAGE-WOOTTERS-IBM-6  backend={backend.name}  dry={args.dry}  {ts}", flush=True)

    chain = find_chain(backend.coupling_map, backend.num_qubits, max(CLOCK_SIZES) + 2)
    prereg = {"program": "AQ-PAGE-WOOTTERS-IBM-6", "backend": backend.name,
              "dry_run": bool(args.dry), "submission_time": ts, "optimization_level": 0,
              "shots": SHOTS, "exact_amplitudes": preds,
              "purpose": "Close IBM-5's phase-blindness limitation: certify the joint "
                         "eigenvalue is +1, not merely that |Psi> is an eigenvector.",
              "gates": {
                  "gate1_joint_real_positive": "Re<Psi|A|Psi> for the joint arm is the largest "
                                               "of the four arms and clearly positive",
                  "gate2_joint_imag_zero": "|Im| for the joint arm is within 3 sigma of 0 "
                                           "-> eigenvalue is REAL",
                  "gate3_phase_near_zero": "|phase| of the joint arm < 0.15 rad after "
                                           "attenuation -> eigenvalue is +1, not e^{i phi}",
                  "gate4_conjugate_pair_split": "clock_only and system_only carry "
                                                "opposite-sign imaginary parts, separating two arms "
                                                "the echo assigns IDENTICAL modulus -- the "
                                                "directional information the echo discards",
              }}
    (out_dir / "ibm6_prereg.json").write_text(json.dumps(prereg, indent=2), encoding="utf-8")
    print(f"  pre-registration filed: {out_dir / 'ibm6_prereg.json'}", flush=True)

    results = {"backend": backend.name, "exact_amplitudes": preds, "arms": {}}
    gates = {}

    for n_clock in CLOCK_SIZES:
        d = 2**n_clock
        layout = chain[:n_clock + 2]
        print(f"\n=== d={d} ===", flush=True)

        circuits, index = [], []
        for name, sh, ev in ARMS:
            for imag in (False, True):
                circuits.append(build_hadamard_test(n_clock, sh, ev, imag))
                index.append((name, imag))
        counts, _ = backend.run_batch(circuits, SHOTS, layout, stage=f"hadamard_d{d}")

        meas = {}
        for (name, imag), c in zip(index, counts):
            meas.setdefault(name, {})["im" if imag else "re"] = z_expectation(c)

        sigma = 1.0 / np.sqrt(SHOTS)
        arm = {}
        for name in meas:
            re, im = meas[name]["re"], meas[name]["im"]
            arm[name] = {"re": re, "im": im, "abs": float(np.hypot(re, im)),
                         "phase": float(np.arctan2(im, re))}
            e = preds[str(d)][name]
            print(f"  {name:12s} Re={re:+.4f}  Im={im:+.4f}  |A|={arm[name]['abs']:.4f}  "
                  f"phase={arm[name]['phase']:+.3f}   (exact Re={e['re']:+.4f} Im={e['im']:+.4f})",
                  flush=True)
        results["arms"][str(d)] = arm

        j = arm["joint"]
        gates[f"gate1_joint_real_positive_d{d}"] = bool(
            j["re"] > 0 and j["re"] == max(a["re"] for a in arm.values()))
        gates[f"gate2_joint_imag_zero_d{d}"] = bool(abs(j["im"]) < 3 * sigma)
        gates[f"gate3_phase_near_zero_d{d}"] = bool(abs(j["phase"]) < 0.15)
        # The echo gives clock_only and system_only the SAME modulus at every d.
        # Only the phase separates them, and it does so by sign.
        gates[f"gate4_conjugate_pair_split_d{d}"] = bool(
            arm["clock_only"]["im"] < -3 * sigma < 3 * sigma < arm["system_only"]["im"])

    results["gates"] = gates
    results["all_gates_pass"] = bool(all(gates.values()))
    results["job_ids"] = getattr(backend, "job_ids", [])
    results["layouts"] = {str(2**nc): chain[:nc + 2] for nc in CLOCK_SIZES}
    (out_dir / "ibm6_results.json").write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    if not args.dry:
        clear_checkpoint(backend.name)
    print(f"\n[GATES] {json.dumps(gates, indent=2)}")
    print(f"[DONE] all_gates_pass={results['all_gates_pass']}  -> {out_dir / 'ibm6_results.json'}")


if __name__ == "__main__":
    main()
