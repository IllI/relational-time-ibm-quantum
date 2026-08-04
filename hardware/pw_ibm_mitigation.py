#!/usr/bin/env python3
"""AQ-PAGE-WOOTTERS-IBM-0 -- POST-HOC readout-error mitigation.

POST-HOC ANALYSIS: this is categorically distinct from the pre-registered
result. The pre-registered Gate 3 (classical arm within 3x shot-noise floor)
FAILED on both replications and that failure stands on record. This script
tests the diagnosis -- that the classical-arm excess is a readout systematic,
not clock coherence -- by applying tensor-product readout-confusion-matrix
inversion built from IBM's backend calibration (captured in the provenance
snapshots), to the archived counts of arms C (coherent) and D (classical).

Mitigation matrices come from backend-reported calibration, NOT from in-run
calibration circuits (the witness pipeline did not run any -- an omission
relative to the OAT PTM runs, noted in the results doc). Calibration
last_update times bracket the runs within ~1 h.

Caveat on qubit identity: pending pw_ibm_verify_layout.py, the physical
qubits are assumed to be the trivial layout 0..n_clock (the submitter never
passed initial_layout -- bug on record), so calibration for qubits 0..3 of
each backend is used for ALL runs, including "layoutB". The layoutB
provenance captured qubits 4-7 by mistake of the same bug; this script pulls
marrakesh 0-3 calibration from the primary run's provenance instead. If
verification shows different measured qubits, rerun with corrected maps.

Runs entirely locally from archived JSON. Zero hardware usage.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from pw_ibm_dryrun import exact_witness_tvd, uniform_tvd_floor

RUNS = {
    "marrakesh_A": {
        "counts_dir": Path("results_page_wootters_ibm0"),
        "calibration_from": Path("results_page_wootters_ibm0/pw_ibm_provenance.json"),
    },
    "fez": {
        "counts_dir": Path("results_page_wootters_ibm0_fez"),
        "calibration_from": Path("results_page_wootters_ibm0_fez/pw_ibm_provenance.json"),
    },
    "marrakesh_B": {
        "counts_dir": Path("results_page_wootters_ibm0_layoutB"),
        # layoutB provenance snapshotted qubits 4-7, but the trivial-layout bug
        # means the run almost certainly executed on 0-3; use the primary run's
        # marrakesh 0-3 calibration (last_update 20:00, run at 20:18).
        "calibration_from": Path("results_page_wootters_ibm0/pw_ibm_provenance.json"),
    },
}
CLOCK_SIZES = (1, 2, 3)
SHOTS_C = 8000


def load_confusion(provenance_path: Path, qubit: int) -> np.ndarray:
    prov = json.loads(provenance_path.read_text(encoding="utf-8"))
    props = prov["calibration"]["qubit_properties"][str(qubit)]
    p10 = float(props["prob_meas1_prep0"])  # measured 1 given prepared 0
    p01 = float(props["prob_meas0_prep1"])  # measured 0 given prepared 1
    # columns = prepared state, rows = measured state
    return np.array([[1.0 - p10, p01], [p10, 1.0 - p01]])


def counts_to_probs(counts: dict[str, int], n_bits: int) -> np.ndarray:
    p = np.zeros(2**n_bits)
    total = 0
    for bits, n in counts.items():
        p[int(bits.replace(" ", ""), 2)] += n
        total += n
    return p / max(total, 1)


def mitigate(p: np.ndarray, confusions: list[np.ndarray]) -> np.ndarray:
    """Invert the tensor-product confusion matrix. Index convention: bitstring
    b_{n-1}..b_1b_0 with bit j = clock qubit j, so M = M_{n-1} (x) .. (x) M_0."""
    m = confusions[-1]
    for c in reversed(confusions[:-1]):
        m = np.kron(m, c)
    p_mit = np.linalg.solve(m, p)
    p_mit = np.clip(p_mit, 0.0, None)
    s = p_mit.sum()
    return p_mit / s if s > 0 else p_mit


def tvd_from_uniform(p: np.ndarray) -> float:
    d = p.size
    return float(0.5 * np.sum(np.abs(p - 1.0 / d)))


def main() -> None:
    print("AQ-PAGE-WOOTTERS-IBM-0 -- POST-HOC readout mitigation (local, no QPU)")
    report: dict = {"program": "AQ-PAGE-WOOTTERS-IBM-0-MITIGATION-POSTHOC", "runs": {}}

    for run_name, cfg in RUNS.items():
        run_block: dict = {}
        print(f"\n=== {run_name} ===")
        for n_clock in CLOCK_SIZES:
            d = 2**n_clock
            counts_file = cfg["counts_dir"] / f"pw_ibm_counts_nclock{n_clock}.json"
            payload = json.loads(counts_file.read_text(encoding="utf-8"))
            counts = payload["counts"]

            confusions = [load_confusion(cfg["calibration_from"], q) for q in range(n_clock)]

            # Arm C: single circuit.
            p_c_raw = counts_to_probs(counts["C"][0], n_clock)
            p_c_mit = mitigate(p_c_raw, confusions)

            # Arm D: d circuits averaged with weight 1/d.
            p_d_raw = np.zeros(d)
            for t in range(d):
                p_d_raw += counts_to_probs(counts["D"][t], n_clock) / d
            p_d_mit = mitigate(p_d_raw, confusions)

            floor = uniform_tvd_floor(d, SHOTS_C)
            exact_tvd, _ = exact_witness_tvd(n_clock)
            row = {
                "d": d,
                "tvd_C_raw": tvd_from_uniform(p_c_raw),
                "tvd_C_mitigated": tvd_from_uniform(p_c_mit),
                "tvd_D_raw": tvd_from_uniform(p_d_raw),
                "tvd_D_mitigated": tvd_from_uniform(p_d_mit),
                "exact_tvd": exact_tvd,
                "null_floor": floor,
                "gate3_raw_pass": bool(tvd_from_uniform(p_d_raw) < 3 * floor),
                "gate3_mitigated_pass": bool(tvd_from_uniform(p_d_mit) < 3 * floor),
                "separation_raw": tvd_from_uniform(p_c_raw) - tvd_from_uniform(p_d_raw),
                "separation_mitigated": tvd_from_uniform(p_c_mit) - tvd_from_uniform(p_d_mit),
            }
            run_block[str(n_clock)] = row
            print(
                f"  d={d}:  D(classical) raw {row['tvd_D_raw']:.4f} -> mit {row['tvd_D_mitigated']:.4f} "
                f"(3x floor {3*floor:.4f})  gate3 {row['gate3_raw_pass']} -> {row['gate3_mitigated_pass']}  | "
                f"C(coherent) raw {row['tvd_C_raw']:.4f} -> mit {row['tvd_C_mitigated']:.4f} "
                f"(exact {exact_tvd:.4f})"
            )
        report["runs"][run_name] = run_block

    # Summary verdict.
    all_pass = all(
        row["gate3_mitigated_pass"]
        for run_block in report["runs"].values()
        for row in run_block.values()
    )
    report["gate3_mitigated_all_pass"] = bool(all_pass)
    out = Path("results_page_wootters_ibm0") / "pw_ibm_mitigation_posthoc.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\n[DONE] gate3_mitigated_all_pass={all_pass}  -> {out}")


if __name__ == "__main__":
    main()
