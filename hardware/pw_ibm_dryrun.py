#!/usr/bin/env python3
"""AQ-PAGE-WOOTTERS-IBM-0 -- local dry run.

Verifies the Page-Wootters circuit design on Aer (ideal + noisy) before any
hardware submission, following the same dry-run-first discipline used for the
OAT PTM runs.

Construction. Clock register C of n_c qubits (d = 2^n_c levels), system S of
one qubit. The history state is

    |Psi> = (1/sqrt(d)) sum_t |t>_C (x) U^t |0>_S ,   U = Ry(theta), theta = 2*pi/d

built by Hadamards on the clock followed by a controlled-Ry(2^k * theta)
ladder from clock qubit k. The global state carries no external time
parameter; "evolution" appears only when the system is conditioned on a clock
reading.

Three measurements, each with a matched classical-clock control in which the
clock is prepared in a definite computational basis state |t> (d separate
circuits, averaged with weight 1/d) rather than in superposition:

  A  conditional evolution   <Z_S | t>  ->  expected cos(2*pi*t/d)
  B  classical-clock control ->  expected IDENTICAL to A
  C  clock coherence witness: inverse-QFT the clock, measure it, take the
     total-variation distance of P(k) from uniform
  D  classical-clock control for C -> expected TVD exactly 0

A and B agreeing is the point, not a bug: conditional evolution alone does not
distinguish a coherent history state from a classically correlated mixture.
C vs D is the measurement that does.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError, thermal_relaxation_error

CLOCK_SIZES = (1, 2, 3)
SHOTS_COND = 8000
SHOTS_WITNESS = 8000

T1_US, T2_US = 150.0, 80.0
GATE_1Q_NS, GATE_2Q_NS = 50.0, 300.0
READOUT_ERR = 0.02


def inverse_qft(qc: QuantumCircuit, qubits: list[int]) -> None:
    n = len(qubits)
    for i in range(n // 2):
        qc.swap(qubits[i], qubits[n - 1 - i])
    for j in range(n):
        for m in range(j):
            qc.cp(-np.pi / float(2 ** (j - m)), qubits[m], qubits[j])
        qc.h(qubits[j])


def controlled_u_ladder(qc: QuantumCircuit, clock: list[int], system: int, theta: float) -> None:
    """sum_t |t><t| (x) U^t  with U = Ry(theta), clock qubit k carrying weight 2^k."""
    for k, cq in enumerate(clock):
        qc.cry((2**k) * theta, cq, system)


def build_conditional(n_clock: int, fixed_t: int | None) -> QuantumCircuit:
    """Circuit A (fixed_t=None) or its classical-clock control (fixed_t=t)."""
    d = 2**n_clock
    theta = 2.0 * np.pi / d
    clock = list(range(n_clock))
    system = n_clock
    qc = QuantumCircuit(n_clock + 1, n_clock + 1)
    if fixed_t is None:
        qc.h(clock)
    else:
        for k in range(n_clock):
            if (fixed_t >> k) & 1:
                qc.x(clock[k])
    controlled_u_ladder(qc, clock, system, theta)
    qc.measure(clock + [system], list(range(n_clock + 1)))
    return qc


def build_witness(n_clock: int, fixed_t: int | None) -> QuantumCircuit:
    """Circuit C (fixed_t=None) or its classical-clock control (fixed_t=t)."""
    d = 2**n_clock
    theta = 2.0 * np.pi / d
    clock = list(range(n_clock))
    system = n_clock
    qc = QuantumCircuit(n_clock + 1, n_clock)
    if fixed_t is None:
        qc.h(clock)
    else:
        for k in range(n_clock):
            if (fixed_t >> k) & 1:
                qc.x(clock[k])
    controlled_u_ladder(qc, clock, system, theta)
    inverse_qft(qc, clock)
    qc.measure(clock, list(range(n_clock)))
    return qc


def noise_model() -> NoiseModel:
    nm = NoiseModel()
    t1, t2 = T1_US * 1e3, T2_US * 1e3
    err1 = thermal_relaxation_error(t1, t2, GATE_1Q_NS)
    err2 = thermal_relaxation_error(t1, t2, GATE_2Q_NS).expand(
        thermal_relaxation_error(t1, t2, GATE_2Q_NS)
    )
    nm.add_all_qubit_quantum_error(err1, ["rz", "sx", "x", "h", "ry"])
    nm.add_all_qubit_quantum_error(err2, ["cx", "cz", "cp", "swap"])
    nm.add_all_qubit_readout_error(
        ReadoutError([[1 - READOUT_ERR, READOUT_ERR], [READOUT_ERR, 1 - READOUT_ERR]])
    )
    return nm


def conditional_z(counts: dict[str, int], n_clock: int) -> dict[int, float]:
    """<Z_S | t> for each clock reading t. Qiskit bitstrings are little-endian:
    rightmost char is classical bit 0 = clock qubit 0; system is the leftmost."""
    per_t: dict[int, list[int]] = {t: [0, 0] for t in range(2**n_clock)}
    for bits, n in counts.items():
        b = bits.replace(" ", "")
        s = int(b[0])
        t = int(b[1:], 2)
        per_t[t][s] += n
    out = {}
    for t, (n0, n1) in per_t.items():
        total = n0 + n1
        out[t] = float((n0 - n1) / total) if total else float("nan")
    return out


def witness_tvd(counts: dict[str, int], n_clock: int) -> tuple[float, list[float]]:
    d = 2**n_clock
    total = sum(counts.values())
    p = np.zeros(d)
    for bits, n in counts.items():
        p[int(bits.replace(" ", ""), 2)] += n
    p = p / max(total, 1)
    return float(0.5 * np.sum(np.abs(p - 1.0 / d))), [float(v) for v in p]


def run(sim: AerSimulator, qc: QuantumCircuit, shots: int) -> dict[str, int]:
    return sim.run(transpile(qc, sim, optimization_level=0), shots=shots).result().get_counts()


def exact_witness_tvd(n_clock: int) -> tuple[float, list[float]]:
    """Exact P(k) and TVD from the clock marginal, no sampling.

    rho_C = (1/d) sum_{t,t'} <psi(t')|psi(t)> |t><t'|, and for U = Ry(theta)
    with theta = 2*pi/d the overlaps are <psi(t')|psi(t)> = cos((t-t')*pi/d) --
    i.e. exactly the clock-record non-orthogonality. P(k) = <f_k|rho_C|f_k>.
    """
    d = 2**n_clock
    t = np.arange(d)
    overlaps = np.cos(np.subtract.outer(t, t) * np.pi / d)  # [t', t]
    rho_c = overlaps / d
    f = np.exp(2j * np.pi * np.outer(np.arange(d), t) / d) / np.sqrt(d)  # f[k, a] = <a|f_k>
    p = np.real(np.einsum("ka,ab,kb->k", f.conj(), rho_c, f))
    p = np.clip(p, 0.0, None)
    p = p / p.sum()
    return float(0.5 * np.sum(np.abs(p - 1.0 / d))), [float(v) for v in p]


def uniform_tvd_floor(d: int, shots: int) -> float:
    """Expected TVD-from-uniform of a truly uniform distribution sampled with
    `shots` draws. TVD is positively biased at finite sampling, so the
    classical-clock arm cannot read exactly zero; this is the null floor a
    measured coherent TVD must be compared against."""
    sigma = np.sqrt((1.0 / d) * (1.0 - 1.0 / d) / shots)
    return float(0.5 * d * np.sqrt(2.0 / np.pi) * sigma)


def main() -> None:
    ideal = AerSimulator()
    noisy = AerSimulator(noise_model=noise_model())
    report: dict = {"program": "AQ-PAGE-WOOTTERS-IBM-0-DRYRUN", "clock_sizes": list(CLOCK_SIZES)}

    for n_clock in CLOCK_SIZES:
        d = 2**n_clock
        analytic = {t: float(np.cos(2.0 * np.pi * t / d)) for t in range(d)}
        exact_tvd, exact_p = exact_witness_tvd(n_clock)
        block: dict = {
            "d": d,
            "analytic_cond_z": analytic,
            "exact_witness_tvd": exact_tvd,
            "exact_p_fourier": exact_p,
            "uniform_tvd_floor_at_shots": uniform_tvd_floor(d, SHOTS_WITNESS),
        }

        for label, sim in (("ideal", ideal), ("noisy", noisy)):
            cond = conditional_z(run(sim, build_conditional(n_clock, None), SHOTS_COND), n_clock)

            # Classical-clock control: d definite-clock circuits, weight 1/d.
            acc: dict[int, list[float]] = {t: [] for t in range(d)}
            for t in range(d):
                c = conditional_z(run(sim, build_conditional(n_clock, t), SHOTS_COND // d), n_clock)
                acc[t].append(c[t])
            cond_classical = {t: float(np.mean(v)) for t, v in acc.items()}

            tvd_coh, p_coh = witness_tvd(run(sim, build_witness(n_clock, None), SHOTS_WITNESS), n_clock)
            p_cls = np.zeros(d)
            for t in range(d):
                _, p = witness_tvd(run(sim, build_witness(n_clock, t), SHOTS_WITNESS // d), n_clock)
                p_cls += np.asarray(p) / d
            tvd_cls = float(0.5 * np.sum(np.abs(p_cls - 1.0 / d)))

            resid = [abs(cond[t] - analytic[t]) for t in range(d)]
            ab_gap = [abs(cond[t] - cond_classical[t]) for t in range(d)]
            block[label] = {
                "cond_z": cond,
                "cond_z_classical_clock": cond_classical,
                "max_abs_resid_vs_analytic": float(np.max(resid)),
                "max_abs_gap_A_minus_B": float(np.max(ab_gap)),
                "witness_tvd_coherent": tvd_coh,
                "witness_tvd_classical": tvd_cls,
                "witness_separation": tvd_coh - tvd_cls,
                "p_fourier_coherent": p_coh,
                "p_fourier_classical": [float(v) for v in p_cls],
            }

        tq = transpile(
            build_witness(n_clock, None),
            basis_gates=["rz", "sx", "x", "cx"],
            optimization_level=0,
        )
        block["witness_transpiled_depth"] = int(tq.depth())
        block["witness_transpiled_cx"] = int(tq.count_ops().get("cx", 0))
        report[f"n_clock_{n_clock}"] = block

        i, n = block["ideal"], block["noisy"]
        print(f"\n=== n_clock={n_clock} (d={d}) ===")
        print(f"  EXACT  witness TVD (statevector)= {exact_tvd:.4f}")
        print(f"  null floor at {SHOTS_WITNESS} shots      = {block['uniform_tvd_floor_at_shots']:.4f}")
        print(f"  ideal  max|cond_z - analytic|   = {i['max_abs_resid_vs_analytic']:.4f}")
        print(f"  ideal  max|A - B| (must be ~0)  = {i['max_abs_gap_A_minus_B']:.4f}")
        print(f"  ideal  TVD coherent / classical = {i['witness_tvd_coherent']:.4f} / {i['witness_tvd_classical']:.4f}")
        print(f"  noisy  max|cond_z - analytic|   = {n['max_abs_resid_vs_analytic']:.4f}")
        print(f"  noisy  TVD coherent / classical = {n['witness_tvd_coherent']:.4f} / {n['witness_tvd_classical']:.4f}")
        print(f"  noisy  witness separation       = {n['witness_separation']:.4f}")
        print(f"  transpiled depth / cx           = {block['witness_transpiled_depth']} / {block['witness_transpiled_cx']}")

    out = Path("pw_ibm_dryrun_results.json")
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\n[DONE] {out}")


if __name__ == "__main__":
    main()
