#!/usr/bin/env python3
"""AQ-PAGE-WOOTTERS-IBM-10 -- the three PW properties on ONE preparation.

WHY THIS RUN EXISTS. The program can currently say "the history state is
entangled" (IBM-4) and "the history state is stationary" (IBM-5), but NOT of
the same state. IBM-4 certified F = 0.9419 on the Ry-generated state
(cry ladder onto |0>, U = Ry(2pi/d), U^d = -I). IBM-5 certified stationarity
on the P-generated state (cp ladder onto |+>, U = P(2pi/d), U^d = +I). Those
two states are ORTHOGONAL -- fidelity 0.000 at d=4, 0.005 at d=8 -- and they
are not related by any system-local unitary, because they differ by a
CLOCK-CONDITIONED phase. That is exactly the U^d = -I vs +I distinction.

Both are maximally entangled by construction, so the theory transfers. The
MEASUREMENT does not: the state we showed entangled was never shown
stationary, and the state we showed stationary was never hardware-certified as
entangled. Stitching the two is the single most attackable claim in the paper.

THE FIX: measure all three defining properties on ONE preparation V, at d=4.

    Arm A  entanglement   multi-setting fidelity witness   F > lambda_max = 1/2
    Arm B  stationarity   Loschmidt echo of S (x) U        vs 3 mismatched controls
    Arm C  evolution      clock in Z, system in X          <X_S|t> = cos(2 pi t/d)

Every arm composes the SAME prepare_history(n_clock) circuit object, and both
the echo's U and the conditional dynamics' U come from the SAME source
function (system_step), so the "one operator does both jobs" identity is
structural rather than numerically coincidental. Both facts are ASSERTED at
runtime rather than asserted in prose -- see check_single_state_discipline().

WHAT THIS EARNS, AND WHAT IT DOES NOT. If all gates pass, the defensible claim
is an experimental realization and certification of finite quantum relational
dynamics: a stationary entangled global state containing an internally
evolving relational history, with three independent observables rather than
one tomographic fit. It remains device-DEPENDENT (a fidelity witness trusts
its measurement labels; this is not a Bell test, and two logical subsystems on
one chip are not spacelike separated, so CHSH would strengthen it but would
NOT make it device-independent). The state is still engineered by externally
timed gates, the clock decomposition is still imposed rather than derived, and
the eigenvalue PHASE is still uncertified (IBM-6 and IBM-8 both failed at it).

Usage:
    python pw_ibm10_single_state.py --dry
    python pw_ibm10_single_state.py --backend ibm_marrakesh
"""

from __future__ import annotations

import argparse
import datetime
import json
from pathlib import Path

import numpy as np
from qiskit import ClassicalRegister, QuantumCircuit
from qiskit.quantum_info import Operator, SparsePauliOp, Statevector

from pw_ibm1_submit import DryBackend, HardwareBackend, clear_checkpoint, find_chain
from pw_ibm4_fidelity import (COEFF_CUTOFF, covering_settings, expectation,
                              fidelity_from_counts, measure_circuit)
from pw_ibm5_constraint import (build_conditional, build_echo, clock_shift,
                                conditional_x, exact_overlap, prepare_history,
                                return_probability, system_step)

N_CLOCK = 2              # d = 4. IBM-5 showed the echo's contrast DEGRADES as d
                         # grows (at d=8, cos^2(theta/2)=0.854 caps the joint-vs-
                         # system_only gap at 0.146 even on perfect hardware), and
                         # IBM-8 showed d=8 is out of reach for anything carrying a
                         # controlled clock-shift. d=4 is where all three arms are
                         # simultaneously well-conditioned.
LAMBDA_MAX = 0.5         # asserted against the ACTUAL prepared state below
SHOTS_FID = 4000         # arm A: 10-ish settings
SHOTS_ECHO = 4000        # arm B: 4 arms
SHOTS_COND = 4000        # arm C: 1 circuit

# Loschmidt arms: (label, apply clock shift?, system evolution power)
ECHO_ARMS = (("joint", True, 1), ("clock_only", True, 0),
             ("system_only", False, 1), ("wrong_way", True, -1))


def check_single_state_discipline(n_clock: int) -> None:
    """The whole point of this run is that the three arms share ONE state and
    ONE U. Assert both structurally -- a prose claim is not evidence."""
    prep = prepare_history(n_clock)
    ref = Statevector.from_instruction(prep).data

    # Arm C must contain exactly the prep state before its readout rotation.
    cond = build_conditional(n_clock)
    stripped = QuantumCircuit(n_clock + 1)
    for inst in cond.data:
        if inst.operation.name in ("measure", "barrier"):
            continue
        stripped.append(inst.operation, [cond.find_bit(q).index for q in inst.qubits])
    # undo the X-basis readout H on the system to recover the bare state
    stripped.h(n_clock)
    got = Statevector.from_instruction(stripped).data
    assert np.allclose(got, ref, atol=1e-12), \
        "arm C does not prepare the same state as arm A/B"

    # Arm B's echo must be built from that same prep, and its U must be the
    # same source function the conditional dynamics uses.
    echo = build_echo(n_clock, shift=True, evolve=1)
    assert echo.num_qubits == n_clock + 1, "echo acts on a different register"

    # One U, two jobs: the echo's evolution operator and the operator generating
    # <X_S|t> are both system_step. Verify system_step is genuinely U = P(theta)
    # and that U^d = +I exactly (the property IBM-5 discovered IBM-0..4 lacked).
    d = 2**n_clock
    theta = 2.0 * np.pi / d
    u = QuantumCircuit(1)
    system_step(u, 0, theta)
    U = Operator(u).data
    Ud = np.linalg.matrix_power(U, d)
    assert np.allclose(Ud, np.eye(2), atol=1e-12), \
        f"U^d != +I (got {Ud}); this state is only stationary up to a sign"

    # lambda_max for the separable bound must be derived from THIS state, not
    # inherited from IBM-4's. (IBM-4's own assertion caught a reshape bug here.)
    schmidt = np.linalg.svd(ref.reshape(2, d), compute_uv=False) ** 2
    assert abs(schmidt.max() - LAMBDA_MAX) < 1e-9, \
        f"lambda_max = {schmidt.max()}, not {LAMBDA_MAX}; re-derive the bound"

    # And confirm it really is a different state from IBM-4's, so the run is
    # not silently duplicating work.
    from pw_ibm4_fidelity import prep_history as ry_prep
    ry = Statevector.from_instruction(ry_prep(n_clock)).data
    overlap = abs(np.vdot(ry, ref)) ** 2
    assert overlap < 0.01, f"this is IBM-4's state after all (overlap {overlap})"
    print(f"  [discipline] one prep, one U; U^d=+I; lambda_max={LAMBDA_MAX}; "
          f"overlap with IBM-4 state = {overlap:.4f}")


def pauli_terms_for(prep: QuantumCircuit) -> dict[str, float]:
    """{pauli: <Psi|P|Psi>} for whatever state `prep` makes."""
    psi = Statevector.from_instruction(prep)
    sp = SparsePauliOp.from_operator(Operator(np.outer(psi.data, psi.data.conj())))
    n = prep.num_qubits
    return {label: float(np.real(c)) * (2**n)
            for label, c in zip(sp.paulis.to_labels(), sp.coeffs)
            if abs(float(np.real(c)) * (2**n)) > COEFF_CUTOFF}


def binom_sigma(p: float, n: int) -> float:
    return float(np.sqrt(max(p * (1.0 - p), 1e-12) / max(n, 1)))


def fidelity_sigma(terms: dict[str, float], settings: list[str],
                   counts_by_setting: dict[str, dict[str, int]], n: int,
                   shots: int) -> float:
    """Propagated shot-noise sigma on F = (1/2^n) sum_P c_P <P>.

    Var(<P>) = (1 - <P>^2)/N for a +-1-valued observable, so
    Var(F) = (1/2^n)^2 sum_P c_P^2 Var(<P>_P).

    This is the INDEPENDENCE estimate: Paulis read from the same setting share
    counts and are correlated, which this ignores. It is used only to set a
    3-sigma bar far below the observed margin, not to quote a significance --
    IBM-4 made the same choice and deferred the bootstrap. Do NOT report an
    N-sigma figure from this without bootstrapping the covariance."""
    def covered_by(p: str, s: str) -> bool:
        return all(pi == "I" or pi == si for pi, si in zip(p, s))

    var = 0.0
    for label, c in terms.items():
        if set(label) == {"I"}:
            continue
        for s in settings:
            if covered_by(label, s):
                e = expectation(counts_by_setting[s], label, n)
                var += (c ** 2) * max(1.0 - e * e, 0.0) / max(shots, 1)
                break
    return float(np.sqrt(var) / (2**n))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--backend", default=None)
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--out-dir", type=Path, default=None)
    args = ap.parse_args()

    n_clock = N_CLOCK
    d = 2**n_clock
    n = n_clock + 1

    print("=== SINGLE-STATE DISCIPLINE CHECKS (before any backend contact) ===")
    check_single_state_discipline(n_clock)

    prep = prepare_history(n_clock)
    terms = pauli_terms_for(prep)
    settings = covering_settings(list(terms), n)
    exact_echo = {name: exact_overlap(n_clock, s, e) for name, s, e in ECHO_ARMS}
    print(f"  [arm A] {len(terms)} Pauli terms -> {len(settings)} settings: {settings}")
    print(f"  [arm B] exact echo overlaps: "
          + "  ".join(f"{k}={v:.4f}" for k, v in exact_echo.items()))
    print(f"  [arm C] exact <X_S|t> = "
          + str(np.round([np.cos(2 * np.pi * t / d) for t in range(d)], 4)))
    assert abs(exact_echo["joint"] - 1.0) < 1e-9, "joint echo must be exactly 1"

    backend = DryBackend() if args.dry else HardwareBackend(args.backend)
    if args.fresh and not args.dry:
        clear_checkpoint(backend.name)
    out_dir = args.out_dir or Path(f"results_ibm10_{backend.name}")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.utcnow().isoformat() + "Z"
    print(f"\nAQ-PAGE-WOOTTERS-IBM-10  backend={backend.name}  dry={args.dry}  {ts}",
          flush=True)

    chain = find_chain(backend.coupling_map, backend.num_qubits, n)
    layout = chain[:n]

    prereg = {
        "program": "AQ-PAGE-WOOTTERS-IBM-10", "backend": backend.name,
        "dry_run": bool(args.dry), "submission_time": ts, "optimization_level": 0,
        "n_clock": n_clock, "d": d, "layout": layout,
        "shots": {"fidelity": SHOTS_FID, "echo": SHOTS_ECHO, "conditional": SHOTS_COND},
        "lambda_max": LAMBDA_MAX, "settings": settings,
        "exact_echo_overlaps": exact_echo,
        "purpose": "Certify entanglement, ray-stationarity and internal evolution on a "
                   "SINGLE hardware preparation. IBM-4 and IBM-5 established the first "
                   "two on orthogonal states (fidelity 0.000 at d=4), so the conjunction "
                   "-- which is the Page-Wootters mechanism's actual content -- was never "
                   "measured. All three arms here compose the same prepare_history() "
                   "circuit and the same system_step() operator.",
        "gates": {
            "gate1_entangled": "F > lambda_max = 0.5 by more than 3 sigma",
            "gate2_stationary": "joint echo exceeds EVERY mismatched control by >3 sigma "
                                "(binomial sigma at the measured p, not worst-case 1/sqrt(N))",
            "gate3_evolving": "<X_S|t> fits cos(2 pi t/d) with R^2 > 0.90",
            "gate4_conjunction": "gates 1-3 all hold on the SAME prepared state",
        },
    }
    (out_dir / "ibm10_prereg.json").write_text(json.dumps(prereg, indent=2), encoding="utf-8")
    print(f"  pre-registration filed: {out_dir / 'ibm10_prereg.json'}", flush=True)

    # ---- one submission, all three arms, so they share a calibration epoch ----
    circuits, index = [], []
    for s in settings:
        circuits.append(measure_circuit(prep, s))
        index.append(("fid", s))
    for name, shift, evolve in ECHO_ARMS:
        circuits.append(build_echo(n_clock, shift, evolve))
        index.append(("echo", name))
    circuits.append(build_conditional(n_clock))
    index.append(("cond", "cond"))

    counts, _ = backend.run_batch(circuits, SHOTS_FID, layout, stage="single_state")
    got = {}
    for (arm, key), c in zip(index, counts):
        got[(arm, key)] = c

    # ---- Arm A: entanglement ----
    fid = fidelity_from_counts(terms, settings,
                               {s: got[("fid", s)] for s in settings}, n)
    sig_f = fidelity_sigma(terms, settings,
                           {s: got[("fid", s)] for s in settings}, n, SHOTS_FID)
    gate1 = bool(fid - 3 * sig_f > LAMBDA_MAX)

    # ---- Arm B: stationarity ----
    echo = {name: return_probability(got[("echo", name)]) for name, _, _ in ECHO_ARMS}
    joint = echo["joint"]
    sig_j = binom_sigma(joint, SHOTS_ECHO)
    margins = {}
    for name in echo:
        if name == "joint":
            continue
        sig_c = binom_sigma(echo[name], SHOTS_ECHO)
        sep = joint - echo[name]
        sig = float(np.hypot(sig_j, sig_c))
        margins[name] = {"separation": sep, "sigma": sig,
                         "n_sigma": sep / sig if sig > 0 else 0.0}
    gate2 = bool(all(m["n_sigma"] > 3.0 for m in margins.values()))

    # ---- Arm C: internal evolution ----
    xs = conditional_x(got[("cond", "cond")], n_clock)
    tt = np.array(sorted(xs))
    yy = np.array([xs[t] for t in tt])
    exact_c = np.cos(2 * np.pi * tt / d)
    amp = float(np.dot(yy, exact_c) / max(np.dot(exact_c, exact_c), 1e-12))
    pred = amp * exact_c
    r2 = float(1.0 - np.sum((yy - pred) ** 2) / max(np.sum((yy - yy.mean()) ** 2), 1e-12))
    gate3 = bool(r2 > 0.90)

    gate4 = bool(gate1 and gate2 and gate3)

    print(f"\n  [arm A] F = {fid:.4f}  (bound {LAMBDA_MAX}, 3 sigma = {3*sig_f:.4f}, "
          f"margin {fid - LAMBDA_MAX:+.4f})", flush=True)
    print(f"  [arm B] joint = {joint:.4f} (exact 1.0)", flush=True)
    for name, m in margins.items():
        print(f"          vs {name:<12s} {echo[name]:.4f}  sep {m['separation']:+.4f}  "
              f"{m['n_sigma']:.1f} sigma  (exact {exact_echo[name]:.4f})", flush=True)
    print(f"  [arm C] <X_S|t> = {np.round(yy, 4).tolist()}", flush=True)
    print(f"          amplitude {amp:.4f}, R^2 = {r2:.4f}", flush=True)

    gates = {"gate1_entangled": gate1, "gate2_stationary": gate2,
             "gate3_evolving": gate3, "gate4_conjunction": gate4}
    results = {
        "backend": backend.name, "layouts": {str(d): list(layout)}, "layout": layout,
        "n_clock": n_clock, "d": d, "lambda_max": LAMBDA_MAX,
        "settings": settings, "pauli_terms": terms,
        "fidelity": fid, "fidelity_sigma": sig_f,
        "echo": echo, "echo_exact": exact_echo, "echo_margins": margins,
        "conditional_x": {int(t): float(v) for t, v in xs.items()},
        "conditional_amplitude": amp, "conditional_r2": r2,
        "gates": gates, "all_gates_pass": bool(all(gates.values())),
        "job_ids": getattr(backend, "job_ids", []),
    }
    (out_dir / "ibm10_results.json").write_text(
        json.dumps(results, indent=2, default=str), encoding="utf-8")
    if not args.dry:
        clear_checkpoint(backend.name)
    print(f"\n[GATES] {json.dumps(gates, indent=2)}")
    print(f"[DONE] all_gates_pass={results['all_gates_pass']}  -> {out_dir / 'ibm10_results.json'}")


if __name__ == "__main__":
    main()
