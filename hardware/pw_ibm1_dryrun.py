#!/usr/bin/env python3
"""AQ-PAGE-WOOTTERS-IBM-1 -- Gate 0 dry run.

Verifies the IBM-1 design (docs/AQ_PAGE_WOOTTERS_IBM_1_RUN_SPEC.md in the
paper2 repo) on Aer before any hardware submission.

Arm 1A -- clock decoherence sweep. After the history-state ladder, each clock
qubit k is coupled to its own environment qubit by CRY(mu); the environment is
never measured. Exact prediction for the clock marginal:

    rho_C[t,t'] = (1/d) * cos((t-t')*pi/d) * cos(mu/2)^{hamming(t,t')}

so mu=0 must reproduce IBM-0 exactly (the anchor), and mu=pi kills every
off-diagonal (records fully decohered -> classical baseline). Crucially the
conditional evolution <Z_S|t> is exactly mu-independent: the environment
couples only to the clock, so conditioning on a clock reading leaves the
system state untouched. Gate 4's hardware question is whether that exact
theoretical independence survives real noise.

Arm 1B -- informational arrow. theta = pi/(2(d-1)) quarter-revolution ladder,
system copied to one environment qubit by CNOT, entropy of the conditional
system state S(rho_S|t) = H2(sin^2(t*theta/2)) rising monotonically in t.
The classical-clock control is predicted to reproduce the arrow (H3): the
arrow, like conditional evolution, is not by itself a quantum signature.

Everything here is exact-statevector-checked before sampling, in the same
style that caught the Fourier-basis bug in pw_ibm_dryrun.py.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError, thermal_relaxation_error

from pw_ibm_dryrun import (
    exact_witness_tvd,
    inverse_qft,
    uniform_tvd_floor,
    witness_tvd,
)

CLOCK_SIZES = (2, 3)  # d = 4, 8
MU_GRID = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8]) * np.pi / 8
SHOTS = 8000

T1_US, T2_US = 150.0, 80.0
GATE_1Q_NS, GATE_2Q_NS = 50.0, 300.0
READOUT_ERR = 0.02


# ---------------------------------------------------------------------------
# Exact predictions (no sampling)
# ---------------------------------------------------------------------------

def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def exact_rho_c(n_clock: int, mu: float) -> np.ndarray:
    d = 2**n_clock
    t = np.arange(d)
    overlaps = np.cos(np.subtract.outer(t, t) * np.pi / d)
    deph = np.array([[np.cos(mu / 2.0) ** hamming(a, b) for b in t] for a in t])
    return overlaps * deph / d


def exact_pk(n_clock: int, mu: float) -> np.ndarray:
    d = 2**n_clock
    t = np.arange(d)
    f = np.exp(2j * np.pi * np.outer(np.arange(d), t) / d) / np.sqrt(d)
    p = np.real(np.einsum("ka,ab,kb->k", f.conj(), exact_rho_c(n_clock, mu), f))
    p = np.clip(p, 0.0, None)
    return p / p.sum()


def exact_tvd(n_clock: int, mu: float) -> float:
    p = exact_pk(n_clock, mu)
    d = p.size
    return float(0.5 * np.sum(np.abs(p - 1.0 / d)))


def clock_env_entanglement(n_clock: int, mu: float) -> float:
    """S(rho_E) of the global pure state. Clock states are orthogonal, so
    rho_E = (1/d) sum_t |e_t><e_t| with |e_t> = prod_k (|0> or Ry(mu)|0>).
    Entropy from the eigenvalues of the Gram matrix / d."""
    d = 2**n_clock
    c, s = np.cos(mu / 2.0), np.sin(mu / 2.0)
    gram = np.array(
        [[c ** hamming(a, b) for b in range(d)] for a in range(d)]
    )  # <e_a|e_b> real
    evals = np.linalg.eigvalsh(gram / d)
    evals = np.clip(evals, 1e-300, None)
    return float(-np.sum(evals * np.log2(evals)))


def binary_entropy(p: float) -> float:
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return float(-p * np.log2(p) - (1 - p) * np.log2(1 - p))


def von_neumann_from_bloch(r: np.ndarray) -> float:
    """S = H2((1+|r|)/2) for a single-qubit state with Bloch vector r. This
    is the physically correct conditional-system entropy; it requires the
    full 3-basis Bloch vector, not a single-basis population, because a
    coherent (pure) superposition can have arbitrary Z-population while its
    true von Neumann entropy is exactly zero."""
    norm = float(np.clip(np.linalg.norm(r), 0.0, 1.0))
    return binary_entropy(0.5 * (1.0 + norm))


def expected_tvd_shot_noise(p: np.ndarray, n_shots: int) -> float:
    """Generalizes uniform_tvd_floor (pw_ibm_dryrun.py) to a non-uniform
    reference distribution: E[TVD] ~= 0.5 * sum_k E[|phat_k - p_k|], with
    each term approximated by the folded-normal mean sigma_k*sqrt(2/pi),
    sigma_k = sqrt(p_k(1-p_k)/N). This is the same normal approximation
    already used for the uniform case, extended componentwise; it is the
    principled shot-noise floor for a TVD statistic against ANY exact
    reference distribution, not an arbitrary round number."""
    sigma = np.sqrt(np.clip(p * (1.0 - p), 0.0, None) / max(n_shots, 1))
    return float(0.5 * np.sum(sigma * np.sqrt(2.0 / np.pi)))


# ---------------------------------------------------------------------------
# Circuits
# ---------------------------------------------------------------------------

def history_prep(qc: QuantumCircuit, clock: list[int], system: int, theta: float,
                 fixed_t: int | None) -> None:
    if fixed_t is None:
        qc.h(clock)
    else:
        for k in range(len(clock)):
            if (fixed_t >> k) & 1:
                qc.x(clock[k])
    for k, cq in enumerate(clock):
        qc.cry((2**k) * theta, cq, system)


def build_witness_dec(n_clock: int, mu: float, fixed_t: int | None = None) -> QuantumCircuit:
    """Arm 1A witness: history state, CRY(mu) clock_k -> env_k, iQFT clock,
    measure clock only. Environment traced out by non-measurement."""
    d = 2**n_clock
    theta = 2.0 * np.pi / d
    clock = list(range(n_clock))
    system = n_clock
    env = list(range(n_clock + 1, 2 * n_clock + 1))
    qc = QuantumCircuit(2 * n_clock + 1, n_clock)
    history_prep(qc, clock, system, theta, fixed_t)
    for k, cq in enumerate(clock):
        qc.cry(mu, cq, env[k])
    inverse_qft(qc, clock)
    qc.measure(clock, list(range(n_clock)))
    return qc


def build_conditional_dec(n_clock: int, mu: float) -> QuantumCircuit:
    """Arm 1A conditional: same prep + clock-env coupling, computational
    readout of clock + system. Prediction: identical to mu=0 exactly."""
    d = 2**n_clock
    theta = 2.0 * np.pi / d
    clock = list(range(n_clock))
    system = n_clock
    env = list(range(n_clock + 1, 2 * n_clock + 1))
    qc = QuantumCircuit(2 * n_clock + 1, n_clock + 1)
    history_prep(qc, clock, system, theta, None)
    for k, cq in enumerate(clock):
        qc.cry(mu, cq, env[k])
    qc.measure(clock + [system], list(range(n_clock + 1)))
    return qc


def build_conditional_tomo(n_clock: int, mu: float, basis: str,
                           fixed_t: int | None = None) -> QuantumCircuit:
    """Arm 1A-T: conditional single-qubit tomography. Same prep + clock-env
    coupling, but rotate the system into the chosen Pauli basis before Z
    readout, giving the full conditional Bloch vector r(t) per clock reading.

    A scalar <Z_S|t> per clock step is too thin to fit a transition law to;
    the Bloch trajectory {r(t)} is the object the relational-clock path
    machinery (and D-LinOSS) actually operates on. Costs 3x the conditional
    circuits -- still small against the shot budget."""
    d = 2**n_clock
    theta = 2.0 * np.pi / d
    clock = list(range(n_clock))
    system = n_clock
    env = list(range(n_clock + 1, 2 * n_clock + 1))
    qc = QuantumCircuit(2 * n_clock + 1, n_clock + 1)
    history_prep(qc, clock, system, theta, fixed_t)
    for k, cq in enumerate(clock):
        qc.cry(mu, cq, env[k])
    if basis == "X":
        qc.h(system)
    elif basis == "Y":
        qc.sdg(system)
        qc.h(system)
    qc.measure(clock + [system], list(range(n_clock + 1)))
    return qc


def build_arrow(n_clock: int, couple: bool, fixed_t: int | None = None) -> QuantumCircuit:
    """Arm 1B: quarter-revolution ladder theta = pi/(2(d-1)), optional CNOT
    system -> env, measure clock + system in Z."""
    d = 2**n_clock
    theta = np.pi / (2.0 * (d - 1))
    clock = list(range(n_clock))
    system = n_clock
    env = n_clock + 1
    qc = QuantumCircuit(n_clock + 2, n_clock + 1)
    history_prep(qc, clock, system, theta, fixed_t)
    if couple:
        qc.cx(system, env)
    qc.measure(clock + [system], list(range(n_clock + 1)))
    return qc


def build_arrow_tomo(n_clock: int, couple: bool, basis: str,
                     fixed_t: int | None = None) -> QuantumCircuit:
    """Arm 1B-T: full conditional Bloch tomography of the system, so the
    conditional entropy can be computed as the true von Neumann entropy
    H2((1+|r(t)|)/2) rather than the Z-basis population entropy H2(p1).

    The distinction matters most for the uncoupled control: with no CNOT to
    the environment, the system stays in a PURE coherent superposition for
    every clock reading (no entanglement, no mixedness), so its true von
    Neumann entropy is exactly zero at every t -- even though its Z-basis
    population entropy rises just like the coupled case, since population
    entropy conflates superposition with mixedness. The coupled and
    classical-clock arms both dephase the system into a Z-diagonal state via
    the CNOT-then-trace mechanism, so H2(p1) happens to equal the true
    entropy there; only the uncoupled control needs the fix."""
    d = 2**n_clock
    theta = np.pi / (2.0 * (d - 1))
    clock = list(range(n_clock))
    system = n_clock
    env = n_clock + 1
    qc = QuantumCircuit(n_clock + 2, n_clock + 1)
    history_prep(qc, clock, system, theta, fixed_t)
    if couple:
        qc.cx(system, env)
    if basis == "X":
        qc.h(system)
    elif basis == "Y":
        qc.sdg(system)
        qc.h(system)
    qc.measure(clock + [system], list(range(n_clock + 1)))
    return qc


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------

def noise_model() -> NoiseModel:
    nm = NoiseModel()
    t1, t2 = T1_US * 1e3, T2_US * 1e3
    e1 = thermal_relaxation_error(t1, t2, GATE_1Q_NS)
    e2 = thermal_relaxation_error(t1, t2, GATE_2Q_NS).expand(
        thermal_relaxation_error(t1, t2, GATE_2Q_NS)
    )
    nm.add_all_qubit_quantum_error(e1, ["rz", "sx", "x"])
    nm.add_all_qubit_quantum_error(e2, ["cx"])
    nm.add_all_qubit_readout_error(
        ReadoutError([[1 - READOUT_ERR, READOUT_ERR], [READOUT_ERR, 1 - READOUT_ERR]])
    )
    return nm


def run(sim: AerSimulator, qc: QuantumCircuit, shots: int) -> dict[str, int]:
    tqc = transpile(qc, sim, optimization_level=0, basis_gates=["rz", "sx", "x", "cx"])
    return sim.run(tqc, shots=shots).result().get_counts()


def conditional_p1(counts: dict[str, int], n_clock: int) -> dict[int, float]:
    """P(system=1 | clock=t). System is the leftmost bit (last clbit)."""
    per_t: dict[int, list[int]] = {t: [0, 0] for t in range(2**n_clock)}
    for bits, n in counts.items():
        b = bits.replace(" ", "")
        s = int(b[0])
        t = int(b[1:], 2)
        per_t[t][s] += n
    return {
        t: (v[1] / (v[0] + v[1]) if (v[0] + v[1]) else float("nan"))
        for t, v in per_t.items()
    }


def cond_r2(p1: dict[int, float], n_clock: int) -> float:
    d = 2**n_clock
    z_meas = np.array([1.0 - 2.0 * p1[t] for t in range(d)])
    z_pred = np.array([np.cos(2.0 * np.pi * t / d) for t in range(d)])
    a = float(np.dot(z_pred, z_meas) / np.dot(z_pred, z_pred))
    resid = z_meas - a * z_pred
    return float(1.0 - np.sum(resid**2) / max(np.sum((z_meas - z_meas.mean()) ** 2), 1e-12))


def main() -> None:
    ideal = AerSimulator()
    noisy = AerSimulator(noise_model=noise_model())
    report: dict = {"program": "AQ-PAGE-WOOTTERS-IBM-1-DRYRUN", "mu_grid_pi": (MU_GRID / np.pi).tolist()}
    gates: dict[str, bool] = {}

    for n_clock in CLOCK_SIZES:
        d = 2**n_clock
        floor = uniform_tvd_floor(d, SHOTS)
        ibm0_exact, _ = exact_witness_tvd(n_clock)
        block: dict = {"d": d, "null_floor": floor, "ibm0_exact_tvd": ibm0_exact}

        # --- Gate 1 anchor: mu=0 must equal IBM-0's exact witness ---
        anchor_gap = abs(exact_tvd(n_clock, 0.0) - ibm0_exact)
        block["anchor_gap_exact"] = anchor_gap
        gates[f"gate1_anchor_d{d}"] = bool(anchor_gap < 1e-9)

        rows = []
        prev_exact = np.inf
        monotone_exact = True
        for mu in MU_GRID:
            ex_tvd = exact_tvd(n_clock, mu)
            ent = clock_env_entanglement(n_clock, mu)
            if ex_tvd > prev_exact + 1e-12:
                monotone_exact = False
            prev_exact = ex_tvd

            tvd_i, pk_i = witness_tvd(run(ideal, build_witness_dec(n_clock, mu), SHOTS), n_clock)
            tvd_n, pk_n = witness_tvd(run(noisy, build_witness_dec(n_clock, mu), SHOTS), n_clock)
            pk = exact_pk(n_clock, mu)
            rows.append({
                "mu_pi": float(mu / np.pi),
                "exact_tvd": ex_tvd,
                "ideal_tvd": tvd_i,
                "noisy_tvd": tvd_n,
                "clock_env_entanglement": ent,
                "exact_pk": [float(v) for v in pk],
                "ideal_pk": [float(v) for v in pk_i],
                "noisy_pk": [float(v) for v in pk_n],
            })
        block["sweep"] = rows

        # Classical arm at mu = 0 and pi: definite |t> averaged 1/d, must be uniform.
        for mu_label, mu in (("0", 0.0), ("pi", float(np.pi))):
            p_cls = np.zeros(d)
            for t in range(d):
                _, p = witness_tvd(
                    run(noisy, build_witness_dec(n_clock, mu, fixed_t=t), SHOTS // d), n_clock
                )
                p_cls += np.asarray(p) / d
            block[f"classical_tvd_mu{mu_label}"] = float(0.5 * np.sum(np.abs(p_cls - 1.0 / d)))

        exact_curve = [r["exact_tvd"] for r in rows]
        # Gate 0 threshold: 3x the expected shot-noise floor for the TVD
        # statistic at THIS mu's own exact distribution -- not an arbitrary
        # round number. Generalizes the uniform_tvd_floor convention already
        # used for Gate 3 in pw_ibm_dryrun.py to a non-uniform reference.
        per_point_floor = [expected_tvd_shot_noise(exact_pk(n_clock, mu), SHOTS) for mu in MU_GRID]
        per_point_gap = [abs(r["ideal_tvd"] - r["exact_tvd"]) for r in rows]
        per_point_ratio = [gap / max(3.0 * fl, 1e-9) for gap, fl in zip(per_point_gap, per_point_floor)]
        ideal_gap = max(per_point_gap)
        worst_ratio = max(per_point_ratio)
        block["max_ideal_vs_exact_gap"] = ideal_gap
        block["gate0_per_point_floor_x3"] = [3.0 * f for f in per_point_floor]
        block["gate0_per_point_gap"] = per_point_gap
        block["gate0_worst_gap_over_3x_floor_ratio"] = worst_ratio
        gates[f"gate0_sampling_matches_exact_d{d}"] = bool(worst_ratio < 1.0)
        gates[f"gate2_monotone_decay_exact_d{d}"] = monotone_exact
        noisy_curve = [r["noisy_tvd"] for r in rows]
        gates[f"gate2_monotone_decay_noisy_d{d}"] = bool(
            all(noisy_curve[i + 1] <= noisy_curve[i] + 3 * floor for i in range(len(noisy_curve) - 1))
        )
        gates[f"gate3_threshold_d{d}"] = bool(noisy_curve[-1] < 3 * floor + block["classical_tvd_mupi"])

        # --- Gate 4: conditional evolution must survive EVERY mu on the
        # actual measurement grid (all 9 points), not a 3-point subsample.
        # Free in Aer, so there is no reason to under-test this -- it is the
        # headline claim of the whole run. ---
        cond_block = {}
        worst_ideal, worst_noisy = 1.0, 1.0
        for mu in MU_GRID:
            p1_i = conditional_p1(run(ideal, build_conditional_dec(n_clock, float(mu)), SHOTS), n_clock)
            p1_n = conditional_p1(run(noisy, build_conditional_dec(n_clock, float(mu)), SHOTS), n_clock)
            r2_i, r2_n = cond_r2(p1_i, n_clock), cond_r2(p1_n, n_clock)
            cond_block[f"mu_{mu/np.pi:.3f}pi"] = {"ideal_r2": r2_i, "noisy_r2": r2_n}
            worst_ideal, worst_noisy = min(worst_ideal, r2_i), min(worst_noisy, r2_n)
        block["conditional"] = cond_block
        block["conditional_n_mu_tested"] = len(MU_GRID)
        gates[f"gate4_cond_survives_ideal_d{d}"] = bool(worst_ideal > 0.995)
        gates[f"gate4_cond_survives_noisy_d{d}"] = bool(worst_noisy > 0.95)

        report[f"n_clock_{n_clock}"] = block
        print(f"\n=== d={d} ===")
        print(f"  anchor gap vs IBM-0 exact: {anchor_gap:.2e}")
        print(f"  exact TVD over mu:  {['%.3f' % v for v in exact_curve]}")
        print(f"  noisy TVD over mu:  {['%.3f' % v for v in noisy_curve]}")
        print(f"  classical arm (noisy): mu=0 {block['classical_tvd_mu0']:.4f}  mu=pi {block['classical_tvd_mupi']:.4f}")
        print(f"  cond-evo R2 worst: ideal {worst_ideal:.4f}  noisy {worst_noisy:.4f}")

    # --- Arm 1B: informational arrow (d=8) ---
    # Two entropy estimators are reported side by side and are NOT
    # interchangeable:
    #   population entropy   H2(p1)                 -- single-basis Z read,
    #                                                   what a naive hardware
    #                                                   measurement gives
    #   von Neumann entropy  H2((1+|r(t)|)/2)        -- true entropy of the
    #                                                   conditional state,
    #                                                   requires 3-basis
    #                                                   tomography
    # These coincide whenever rho_S(t) is Z-diagonal (true for the coupled
    # and classical-clock arms, where CNOT-then-trace dephases the system),
    # and diverge sharply for the uncoupled control, where no CNOT is ever
    # applied: the system stays PURE for every t (zero entanglement with
    # anything), so its true von Neumann entropy is exactly 0 at every clock
    # reading even though its Z-population entropy rises just like the
    # coupled case. Reporting only H2(p1) for that control was wrong -- it
    # measures superposition, not mixedness.
    n_clock = 3
    d = 2**n_clock
    theta = np.pi / (2.0 * (d - 1))
    arrow_exact = [binary_entropy(float(np.sin(t * theta / 2.0) ** 2)) for t in range(d)]

    def population_entropy_from_counts(counts):
        p1 = conditional_p1(counts, n_clock)
        return [binary_entropy(p1[t]) if not np.isnan(p1[t]) else 0.0 for t in range(d)]

    def bloch_and_vn_entropy(couple: bool, fixed_t: int | None = None) -> tuple[list, list]:
        axes = {}
        for basis in ("X", "Y", "Z"):
            circuits = (
                [build_arrow_tomo(n_clock, couple, basis, fixed_t)]
                if fixed_t is not None
                else [build_arrow_tomo(n_clock, couple, basis)]
            )
            shots = SHOTS // d if fixed_t is not None else SHOTS
            p1 = conditional_p1(run(noisy, circuits[0], shots), n_clock)
            axes[basis] = p1
        vecs = [
            np.array([1.0 - 2.0 * axes["X"][t], 1.0 - 2.0 * axes["Y"][t], 1.0 - 2.0 * axes["Z"][t]])
            for t in range(d)
        ]
        vn = [von_neumann_from_bloch(v) for v in vecs]
        return [v.tolist() for v in vecs], vn

    arrow_coupled_pop = population_entropy_from_counts(run(noisy, build_arrow(n_clock, couple=True), SHOTS))
    arrow_uncoupled_pop = population_entropy_from_counts(run(noisy, build_arrow(n_clock, couple=False), SHOTS))
    arrow_classical_pop = []
    for t in range(d):
        counts = run(noisy, build_arrow(n_clock, couple=True, fixed_t=t), SHOTS // d)
        p1 = conditional_p1(counts, n_clock)
        arrow_classical_pop.append(binary_entropy(p1[t]) if not np.isnan(p1[t]) else 0.0)

    coupled_bloch, arrow_coupled_vn = bloch_and_vn_entropy(couple=True)
    uncoupled_bloch, arrow_uncoupled_vn = bloch_and_vn_entropy(couple=False)
    classical_bloch, classical_vn_by_t = [], []
    for t in range(d):
        vecs, vn = bloch_and_vn_entropy(couple=True, fixed_t=t)
        classical_bloch.append(vecs[t])
        classical_vn_by_t.append(vn[t])

    def mostly_monotone(seq, slack=0.05):
        return all(seq[i + 1] >= seq[i] - slack for i in range(len(seq) - 1))

    gates["gate6_arrow_monotone_vn"] = bool(mostly_monotone(arrow_coupled_vn))
    gates["gate6_arrow_classical_too_H3_vn"] = bool(mostly_monotone(classical_vn_by_t))
    gates["gate6_uncoupled_stays_near_pure"] = bool(max(arrow_uncoupled_vn) < 0.3)
    report["arrow"] = {
        "theta_pi": float(theta / np.pi),
        "exact_von_neumann": arrow_exact,
        "population_entropy": {
            "coupled": arrow_coupled_pop,
            "uncoupled": arrow_uncoupled_pop,
            "classical_clock": arrow_classical_pop,
        },
        "von_neumann_entropy_from_tomography": {
            "coupled": arrow_coupled_vn,
            "uncoupled": arrow_uncoupled_vn,
            "classical_clock": classical_vn_by_t,
        },
        "bloch_vectors": {
            "coupled": coupled_bloch,
            "uncoupled": uncoupled_bloch,
            "classical_clock": classical_bloch,
        },
    }
    print(f"\n=== arrow (d=8, theta={theta/np.pi:.4f}pi) ===")
    print(f"  exact (von Neumann)      : {['%.3f' % v for v in arrow_exact]}")
    print(f"  coupled   pop / vN       : {['%.3f' % v for v in arrow_coupled_pop]}")
    print(f"                             {['%.3f' % v for v in arrow_coupled_vn]}")
    print(f"  uncoupled pop / vN       : {['%.3f' % v for v in arrow_uncoupled_pop]}")
    print(f"                             {['%.3f' % v for v in arrow_uncoupled_vn]}  <- should stay near 0 (pure)")
    print(f"  classical pop / vN       : {['%.3f' % v for v in arrow_classical_pop]}")
    print(f"                             {['%.3f' % v for v in classical_vn_by_t]}")

    # --- Conditional Bloch trajectories per mu (input to the D-LinOSS /
    # path-observability analysis; also the hardware artifact format) ---
    bloch: dict = {}
    for n_clock in CLOCK_SIZES:
        d = 2**n_clock
        per_mu = []
        for mu in MU_GRID:
            axes = {}
            for basis in ("X", "Y", "Z"):
                p1 = conditional_p1(
                    run(noisy, build_conditional_tomo(n_clock, mu, basis), SHOTS), n_clock
                )
                axes[basis] = [float(1.0 - 2.0 * p1[t]) for t in range(d)]
            per_mu.append({
                "mu_pi": float(mu / np.pi),
                "r": [[axes["X"][t], axes["Y"][t], axes["Z"][t]] for t in range(d)],
            })
        bloch[f"n_clock_{n_clock}"] = per_mu
    report["conditional_bloch"] = bloch
    n3 = bloch["n_clock_3"]
    print("\n=== conditional Bloch trajectory (d=8, noisy) ===")
    for row in (n3[0], n3[4], n3[8]):
        norms = [float(np.linalg.norm(v)) for v in row["r"]]
        print(f"  mu={row['mu_pi']:.3f}pi  |r(t)|: {['%.3f' % v for v in norms]}")

    report["gates"] = gates
    report["all_gates_pass"] = bool(all(gates.values()))
    out = Path("pw_ibm1_dryrun_results.json")
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\n[GATES] {json.dumps(gates, indent=2)}")
    print(f"[DONE] all_gates_pass={report['all_gates_pass']}  -> {out}")


if __name__ == "__main__":
    main()
