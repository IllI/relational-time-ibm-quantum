#!/usr/bin/env python3
"""AQ-PAGE-WOOTTERS-IBM-4 -- the sufficient condition, measured.

IBM-2 and IBM-3 established, by hardware measurement and then by a two-line
theorem, that NO functional of a single-setting joint distribution can
certify clock-system entanglement. The escape is measurement diversity: a
MULTI-SETTING fidelity witness.

THEOREM FIRST (the discipline IBM-3 said this program was missing):

  The history state |Psi> = (1/sqrt d) sum_t |t>_C (x) U^t|0>_S has Schmidt
  coefficients across clock|system of exactly (1/2, 1/2) at every d tested
  (the system is a qubit, and the two Schmidt vectors are the |0>/|1>
  components of the ladder). So lambda_max = 0.5, and the standard fidelity
  witness (Bourennane et al. 2004; Guehne & Toth 2009) gives

      F(rho, |Psi>) = <Psi|rho|Psi>  >  lambda_max = 0.5   ==>   rho ENTANGLED
                                                                across clock|system

  This is sufficient, not merely necessary. A separable rho cannot exceed
  lambda_max. Unlike W_joint, no diagonal product-basis mimic exists, because
  F is not a functional of one measurement setting -- it requires the full
  Pauli decomposition of |Psi><Psi|, i.e. many incompatible bases.

MEASUREMENT: F = (1/2^n) sum_P <Psi|P|Psi> <P>_rho over n-qubit Paulis P.
Paulis are grouped into qubit-wise-commuting measurement settings by greedy
set cover, so one circuit per setting yields <P> for every P it covers.

ADVERSARIAL CONTROLS (the same two states that defeated the earlier
witnesses, now expected to FAIL to be certified -- which is the point):
  * separable mixture (IBM-3): 1/2 |f_0><f_0|(x)|0><0| + 1/2 |f_1><f_1|(x)|1><1|
  * coherent product (IBM-2):  (1/sqrt d) sum_t |t> (x) |0>
Both must land below 0.5. A witness that certified them would be broken.

Usage:
    python pw_ibm4_fidelity.py --dry
    python pw_ibm4_fidelity.py --backend ibm_marrakesh
"""

from __future__ import annotations

import argparse
import datetime
import itertools
import json
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, SparsePauliOp, Statevector

from pw_ibm1_dryrun import history_prep
from pw_ibm1_submit import DryBackend, HardwareBackend, clear_checkpoint, find_chain

CLOCK_SIZES = (2,)      # d=4 primary; --with-d8 adds the 4-qubit case
SHOTS = 2000
COEFF_CUTOFF = 1e-9
LAMBDA_MAX = 0.5        # derived above; verified numerically in main()


# --------------------------------------------------------------------------
# State preparations (system qubit is index n_clock; no environment register)
# --------------------------------------------------------------------------

def prep_history(n_clock: int) -> QuantumCircuit:
    d = 2**n_clock
    qc = QuantumCircuit(n_clock + 1)
    history_prep(qc, list(range(n_clock)), n_clock, 2.0 * np.pi / d, None)
    return qc


def prep_product(n_clock: int) -> QuantumCircuit:
    qc = QuantumCircuit(n_clock + 1)
    qc.h(range(n_clock))
    return qc


def prep_separable_branch(n_clock: int, branch: int) -> QuantumCircuit:
    d = 2**n_clock
    qc = QuantumCircuit(n_clock + 1)
    qc.h(range(n_clock))
    if branch == 1:
        for k in range(n_clock):
            qc.p(2.0 * np.pi * (2**k) / d, k)
        qc.x(n_clock)
    return qc


# --------------------------------------------------------------------------
# Pauli decomposition and qubit-wise-commuting grouping
# --------------------------------------------------------------------------

def pauli_terms(n_clock: int) -> dict[str, float]:
    """{pauli_label: <Psi|P|Psi>} for the target history state, nonzero only.
    Qiskit label convention: leftmost char = highest qubit index."""
    psi = Statevector.from_instruction(prep_history(n_clock))
    rho = Operator(np.outer(psi.data, psi.data.conj()))
    sp = SparsePauliOp.from_operator(rho)
    n = n_clock + 1
    out = {}
    for label, coeff in zip(sp.paulis.to_labels(), sp.coeffs):
        c = float(np.real(coeff)) * (2**n)   # from_operator returns c_P / 2^n
        if abs(c) > COEFF_CUTOFF:
            out[label] = c
    return out


def covering_settings(labels: list[str], n: int) -> list[str]:
    """Greedy set cover: minimal-ish list of full {X,Y,Z}^n settings such that
    every Pauli agrees with some setting on its support."""
    def covered_by(p: str, s: str) -> bool:
        return all(pi == "I" or pi == si for pi, si in zip(p, s))

    remaining = {p for p in labels if set(p) != {"I"}}
    settings: list[str] = []
    candidates = ["".join(c) for c in itertools.product("XYZ", repeat=n)]
    while remaining:
        best = max(candidates, key=lambda s: sum(covered_by(p, s) for p in remaining))
        settings.append(best)
        remaining = {p for p in remaining if not covered_by(p, best)}
    return settings


def measure_circuit(prep: QuantumCircuit, setting: str) -> QuantumCircuit:
    """Rotate each qubit into the setting's basis, then measure all in Z."""
    n = prep.num_qubits
    qc = prep.copy()
    qc.add_register(__import__("qiskit").ClassicalRegister(n, "c"))
    for q in range(n):
        basis = setting[n - 1 - q]          # label is reversed vs qubit index
        if basis == "X":
            qc.h(q)
        elif basis == "Y":
            qc.sdg(q)
            qc.h(q)
    qc.measure(range(n), range(n))
    return qc


def expectation(counts: dict[str, int], label: str, n: int) -> float:
    """<P> from Z-basis counts taken in a compatible setting."""
    supp = [n - 1 - i for i, ch in enumerate(label) if ch != "I"]  # qubit indices
    total = sum(counts.values())
    acc = 0.0
    for bits, cnt in counts.items():
        b = bits.replace(" ", "")
        parity = sum(int(b[n - 1 - q]) for q in supp) % 2
        acc += (1 - 2 * parity) * cnt
    return acc / max(total, 1)


def fidelity_from_counts(terms: dict[str, float], settings: list[str],
                         counts_by_setting: dict[str, dict[str, int]], n: int) -> float:
    """F = (1/2^n) sum_P <Psi|P|Psi> <P>_rho, each <P> taken from the first
    setting that covers it."""
    def covered_by(p: str, s: str) -> bool:
        return all(pi == "I" or pi == si for pi, si in zip(p, s))

    total = 0.0
    for label, c in terms.items():
        if set(label) == {"I"}:
            total += c * 1.0
            continue
        for s in settings:
            if covered_by(label, s):
                total += c * expectation(counts_by_setting[s], label, n)
                break
    return total / (2**n)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--backend", default=None)
    ap.add_argument("--with-d8", action="store_true", help="also run the 4-qubit d=8 case")
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--out-dir", type=Path, default=None)
    args = ap.parse_args()

    sizes = (2, 3) if args.with_d8 else CLOCK_SIZES

    # ---- Theorem check + circuit budget, before any backend contact ----
    print("=== WITNESS BOUND (derived, then verified numerically) ===")
    plan = {}
    for n_clock in sizes:
        d, n = 2**n_clock, n_clock + 1
        # Qiskit index = sum_q bit_q * 2^q, and the system is qubit n_clock --
        # the HIGHEST index -- so index = z*d + t and the clock|system split is
        # reshape(2, d), NOT reshape(d, 2). Getting this backwards mixes the
        # system bit into the clock index and yields a bogus lambda_max of
        # 0.8536; the assertion below caught exactly that during the dry run.
        psi = Statevector.from_instruction(prep_history(n_clock)).data.reshape(2, d)
        schmidt = np.linalg.svd(psi, compute_uv=False) ** 2
        terms = pauli_terms(n_clock)
        settings = covering_settings(list(terms), n)
        plan[str(d)] = {"n_qubits": n, "schmidt": schmidt.tolist(),
                        "lambda_max": float(schmidt.max()),
                        "n_pauli_terms": len(terms), "n_settings": len(settings),
                        "settings": settings}
        print(f"  d={d} ({n} qubits): Schmidt^2 = {np.round(schmidt, 4)}  "
              f"lambda_max = {schmidt.max():.4f}")
        print(f"      {len(terms)} nonzero Paulis -> {len(settings)} measurement settings "
              f"(vs 3^{n} = {3**n} exhaustive)")
        assert abs(schmidt.max() - LAMBDA_MAX) < 1e-9, "lambda_max != 0.5; re-derive the bound"

    # ---- Exact fidelities (statevector) for all three states ----
    print("\n=== EXACT FIDELITIES vs |Psi> (statevector) ===")
    exact = {}
    for n_clock in sizes:
        d = 2**n_clock
        psi = Statevector.from_instruction(prep_history(n_clock)).data
        rho_sep = np.zeros((len(psi), len(psi)), dtype=complex)
        for br in (0, 1):
            v = Statevector.from_instruction(prep_separable_branch(n_clock, br)).data
            rho_sep += 0.5 * np.outer(v, v.conj())
        prod = Statevector.from_instruction(prep_product(n_clock)).data
        e = {"history": 1.0,
             "separable": float(np.real(psi.conj() @ rho_sep @ psi)),
             "product": float(abs(psi.conj() @ prod) ** 2)}
        exact[str(d)] = e
        print(f"  d={d}: history={e['history']:.4f}  separable={e['separable']:.4f}  "
              f"product={e['product']:.4f}   [bound {LAMBDA_MAX}]")
        print(f"        -> controls correctly below bound: "
              f"{e['separable'] < LAMBDA_MAX and e['product'] < LAMBDA_MAX}")

    backend = DryBackend() if args.dry else HardwareBackend(args.backend)
    if args.fresh and not args.dry:
        clear_checkpoint(backend.name)
    out_dir = args.out_dir or Path(f"results_ibm4_{backend.name}")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.utcnow().isoformat() + "Z"
    print(f"\nAQ-PAGE-WOOTTERS-IBM-4  backend={backend.name}  dry={args.dry}  {ts}", flush=True)

    chain = find_chain(backend.coupling_map, backend.num_qubits, max(sizes) + 1)
    prereg = {"program": "AQ-PAGE-WOOTTERS-IBM-4", "backend": backend.name,
              "dry_run": bool(args.dry), "submission_time": ts, "optimization_level": 0,
              "shots": SHOTS, "lambda_max": LAMBDA_MAX, "plan": plan,
              "exact_fidelities": exact,
              "gates": {
                  "gate1_history_certified": "F(history) > lambda_max = 0.5 -> entanglement CERTIFIED",
                  "gate2_separable_not_certified": "F(separable) < 0.5 (control must fail)",
                  "gate3_product_not_certified": "F(product) < 0.5 (control must fail)",
              }}
    (out_dir / "ibm4_prereg.json").write_text(json.dumps(prereg, indent=2), encoding="utf-8")
    print(f"  pre-registration filed: {out_dir / 'ibm4_prereg.json'}", flush=True)

    results = {"backend": backend.name, "plan": plan, "exact_fidelities": exact, "arms": {}}
    gates = {}

    for n_clock in sizes:
        d, n = 2**n_clock, n_clock + 1
        layout = chain[:n]
        terms = pauli_terms(n_clock)
        settings = plan[str(d)]["settings"]
        print(f"\n=== d={d} ({n} qubits, {len(settings)} settings) ===", flush=True)

        preps = {"history": prep_history(n_clock),
                 "product": prep_product(n_clock),
                 "sep0": prep_separable_branch(n_clock, 0),
                 "sep1": prep_separable_branch(n_clock, 1)}

        counts = {}
        for name, prep in preps.items():
            circuits = [measure_circuit(prep, s) for s in settings]
            c, _ = backend.run_batch(circuits, SHOTS, layout, stage=f"{name}_d{d}")
            counts[name] = dict(zip(settings, c))

        f_hist = fidelity_from_counts(terms, settings, counts["history"], n)
        f_prod = fidelity_from_counts(terms, settings, counts["product"], n)
        f_sep = 0.5 * (fidelity_from_counts(terms, settings, counts["sep0"], n)
                       + fidelity_from_counts(terms, settings, counts["sep1"], n))

        arm = {"F_history": f_hist, "F_separable": f_sep, "F_product": f_prod,
               "lambda_max": LAMBDA_MAX,
               "margin_history": f_hist - LAMBDA_MAX}
        results["arms"][str(d)] = arm
        for k, v in (("history", f_hist), ("separable", f_sep), ("product", f_prod)):
            flag = "CERTIFIED" if v > LAMBDA_MAX else "not certified"
            print(f"  F({k:10s}) = {v:.4f}   [{flag}]", flush=True)
        print(f"  margin above bound: {f_hist - LAMBDA_MAX:+.4f}", flush=True)

        gates[f"gate1_history_certified_d{d}"] = bool(f_hist > LAMBDA_MAX)
        gates[f"gate2_separable_not_certified_d{d}"] = bool(f_sep < LAMBDA_MAX)
        gates[f"gate3_product_not_certified_d{d}"] = bool(f_prod < LAMBDA_MAX)

    results["gates"] = gates
    results["all_gates_pass"] = bool(all(gates.values()))
    results["job_ids"] = getattr(backend, "job_ids", [])
    results["layouts"] = {str(2**nc): chain[:nc + 1] for nc in sizes}
    (out_dir / "ibm4_results.json").write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    if not args.dry:
        clear_checkpoint(backend.name)
    print(f"\n[GATES] {json.dumps(gates, indent=2)}")
    print(f"[DONE] all_gates_pass={results['all_gates_pass']}  -> {out_dir / 'ibm4_results.json'}")


if __name__ == "__main__":
    main()
