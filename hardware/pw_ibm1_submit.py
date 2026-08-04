#!/usr/bin/env python3
"""AQ-PAGE-WOOTTERS-IBM-1 -- hardware submission.

Submits the design verified in pw_ibm1_dryrun.py (Gate 0: 16/16, see
docs/AQ_PAGE_WOOTTERS_IBM_1_GATE0_RESULTS_2026-08-04.md in the paper2 repo).
Reuses the exact circuit-builder functions from that dry run -- nothing here
redefines the physics, only the plumbing to run it on hardware.

Structure (faithful to the run spec's Circuits/Budget sections):

  Arm 1A, per clock size d in {4, 8}, per mu in the 9-point grid:
    witness (coherent, inverse-QFT readout)
    witness classical control (definite |t>, d sub-circuits, averaged 1/d)
    conditional (coherent, Z-basis only -- Gate 4 only needs <Z_S|t>)
    conditional classical control (definite |t>, d sub-circuits)
  Arm 1B (d=8 only):
    coupled (Z-basis only -- rho_S(t) is diagonal, single-basis suffices)
    uncoupled (X,Y,Z tomography -- REQUIRED per the Gate-0 correction: a
               pure superposition needs the Bloch vector, not population)
    classical-clock coupled control (Z-basis, one circuit per t)
  Calibration: one job, all physical qubits touched, prep|0>/|1> per qubit.

Circuits are batched into ~11 jobs (grouped by role), not one job per
circuit, matching the pattern used throughout this program.

Resilience: same checkpoint-per-stage + transient-network-retry discipline
as ibm_run4_crossdevice.py (Paper 1) -- job IDs are saved to disk the instant
they're returned, before blocking on results, so a dropped connection cannot
strand a submitted job with no way to find it again.

Usage:
    python pw_ibm1_submit.py --dry                     # Aer smoke test, zero QPU
    export QISKIT_IBM_TOKEN=...                        # never hardcoded
    python pw_ibm1_submit.py --backend ibm_marrakesh    # real hardware
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import time
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit, transpile

from pw_ibm1_dryrun import (
    MU_GRID,
    binary_entropy,
    build_arrow_tomo,
    build_conditional_dec,
    build_witness_dec,
    clock_env_entanglement,
    exact_pk,
    exact_tvd,
    expected_tvd_shot_noise,
    von_neumann_from_bloch,
    witness_tvd,
)
from pw_ibm1_dlinoss_analysis import fit_exponential, fit_power_law

CLOCK_SIZES = (2, 3)  # d = 4, 8

# Shot budget: the run spec estimates 100-150k shots total. At the dry run's
# per-circuit SHOTS=8000 (copied uncritically from IBM-0, which measured a
# single mu point per circuit), the actual 9-mu x 4-circuit-role x 2-d sweep
# built here comes to 576k shots -- almost 4x the documented budget. Fixed by
# following Paper 1's own precedent instead: ibm_run2/run3 swept 9 points at
# 500 shots/point and still fit the predicted curve at R^2=0.986 on real
# hardware. 500 shots/sweep-circuit brings the total to ~36k for the arm-1A
# sweep, comfortably under budget with margin for arm 1B and calibration.
SHOTS_SWEEP = 500
SHOTS_ARROW_MAIN = 2000
SHOTS_ARROW_CLASSICAL = 250  # 8 circuits (one per t), matches 2000/d at d=8
SHOTS_CAL = 500
CHECKPOINT_DIR = Path(".pw_ibm1_checkpoints")

TRANSIENT_MARKERS = (
    "NameResolutionError", "getaddrinfo", "ConnectionError", "MaxRetryError",
    "Connection aborted", "RemoteDisconnected", "ConnectionResetError",
    "Timeout", "TimeoutError",
)


# --------------------------------------------------------------------------
# Checkpointing (same discipline as Paper 1's ibm_run4_crossdevice.py)
# --------------------------------------------------------------------------

def checkpoint_path(backend_name: str) -> Path:
    CHECKPOINT_DIR.mkdir(exist_ok=True)
    return CHECKPOINT_DIR / f"{backend_name}.json"


def load_checkpoint(backend_name: str) -> dict:
    path = checkpoint_path(backend_name)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save_checkpoint(backend_name: str, stage: str, job_id: str) -> None:
    path = checkpoint_path(backend_name)
    data = load_checkpoint(backend_name)
    data[stage] = job_id
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def clear_checkpoint(backend_name: str) -> None:
    path = checkpoint_path(backend_name)
    if path.exists():
        path.unlink()


def wait_with_retry(job, max_wait_hours: float = 8.0):
    deadline = time.time() + max_wait_hours * 3600
    backoff = 10.0
    while True:
        try:
            return job.result()
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            if not any(m in message for m in TRANSIENT_MARKERS) or time.time() > deadline:
                raise
            print(f"    [network hiccup: {type(exc).__name__}] retrying in {backoff:.0f}s "
                  f"(job still safely queued)...", flush=True)
            time.sleep(backoff)
            backoff = min(backoff * 1.5, 300.0)


# --------------------------------------------------------------------------
# Backends
# --------------------------------------------------------------------------

class DryBackend:
    def __init__(self) -> None:
        from qiskit_aer import AerSimulator
        from qiskit_aer.noise import NoiseModel, ReadoutError, thermal_relaxation_error
        from qiskit.transpiler import CouplingMap

        t1, t2 = 150e3, 80e3
        nm = NoiseModel()
        e1 = thermal_relaxation_error(t1, t2, 50.0)
        e2 = thermal_relaxation_error(t1, t2, 300.0).expand(thermal_relaxation_error(t1, t2, 300.0))
        nm.add_all_qubit_quantum_error(e1, ["rz", "sx", "x"])
        nm.add_all_qubit_quantum_error(e2, ["cx"])
        nm.add_all_qubit_readout_error(ReadoutError([[0.98, 0.02], [0.02, 0.98]]))
        self.num_qubits = 20
        self.name = "aer_dry"
        self.coupling_map = CouplingMap.from_line(self.num_qubits)
        self._sim = AerSimulator(noise_model=nm)

    def run_batch(self, circuits: list[QuantumCircuit], shots: int, layout: list[int], stage: str):
        tqc = [transpile(c, self._sim, optimization_level=0, initial_layout=layout) for c in circuits]
        result = self._sim.run(tqc, shots=shots).result()
        return [result.get_counts(i) for i in range(len(circuits))], tqc


class HardwareBackend:
    def __init__(self, backend_name: str | None) -> None:
        from qiskit_ibm_runtime import QiskitRuntimeService

        token = os.environ.get("QISKIT_IBM_TOKEN")
        if not token:
            raise SystemExit(
                "QISKIT_IBM_TOKEN is not set. Set it in this shell before running:\n"
                '  PowerShell:  $env:QISKIT_IBM_TOKEN = "<token>"'
            )
        try:
            self._service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
        except Exception:
            self._service = QiskitRuntimeService(token=token)
        self._backend = self._service.backend(backend_name) if backend_name else self._service.least_busy(
            operational=True, simulator=False
        )
        self.num_qubits = self._backend.num_qubits
        self.name = self._backend.name
        self.coupling_map = self._backend.coupling_map
        self.job_ids: list[str] = []

    def run_batch(self, circuits: list[QuantumCircuit], shots: int, layout: list[int], stage: str):
        from qiskit_ibm_runtime import SamplerV2 as Sampler
        from qiskit_ibm_runtime.exceptions import RuntimeInvalidStateError

        tqc = [transpile(c, backend=self._backend, optimization_level=0, initial_layout=layout) for c in circuits]

        def submit_fresh():
            sampler = Sampler(mode=self._backend)
            new_job = sampler.run([(c,) for c in tqc], shots=shots)
            print(f"    job {new_job.job_id()} submitted ({len(circuits)} circuits, stage='{stage}'); waiting...", flush=True)
            save_checkpoint(self.name, stage, new_job.job_id())
            self.job_ids.append(new_job.job_id())
            return new_job

        existing = load_checkpoint(self.name).get(stage)
        if existing:
            print(f"    resuming previously submitted job {existing} (stage '{stage}')...", flush=True)
            job = self._service.job(existing)
            self.job_ids.append(existing)
        else:
            job = submit_fresh()

        try:
            result = wait_with_retry(job)
        except RuntimeInvalidStateError:
            if not existing:
                raise
            print(f"    checkpointed job {existing} is dead -- resubmitting fresh...", flush=True)
            job = submit_fresh()
            result = wait_with_retry(job)

        counts = []
        for i in range(len(circuits)):
            creg = tqc[i].cregs[0].name
            counts.append(getattr(result[i].data, creg).get_counts())
        return counts, tqc


# --------------------------------------------------------------------------
# Layout selection (contiguous chain on the coupling map)
# --------------------------------------------------------------------------

def find_chain(coupling_map, num_qubits: int, length: int) -> list[int]:
    adj: dict[int, set[int]] = {q: set() for q in range(num_qubits)}
    for a, b in coupling_map.get_edges():
        adj[a].add(b)
        adj[b].add(a)

    def extend(path: list[int]):
        if len(path) == length:
            return path
        for nxt in sorted(adj[path[-1]]):
            if nxt not in path:
                found = extend(path + [nxt])
                if found:
                    return found
        return None

    for start in range(num_qubits):
        found = extend([start])
        if found:
            return found
    raise RuntimeError(f"no contiguous chain of length {length} found")


def verify_layout(transpiled: QuantumCircuit, intended: list[int]) -> bool:
    touched = {transpiled.find_bit(q).index for instr in transpiled.data for q in instr.qubits}
    return touched.issubset(set(intended))


# --------------------------------------------------------------------------
# Analysis helpers (mirror pw_ibm1_dryrun.py's readout conventions exactly)
# --------------------------------------------------------------------------

def conditional_p1(counts: dict[str, int], n_clock: int) -> dict[int, float]:
    per_t: dict[int, list[int]] = {t: [0, 0] for t in range(2**n_clock)}
    for bits, n in counts.items():
        b = bits.replace(" ", "")
        s, t = int(b[0]), int(b[1:], 2)
        per_t[t][s] += n
    return {t: (v[1] / (v[0] + v[1]) if (v[0] + v[1]) else float("nan")) for t, v in per_t.items()}


def cond_r2(p1: dict[int, float], n_clock: int) -> float:
    d = 2**n_clock
    z_meas = np.array([1.0 - 2.0 * p1[t] for t in range(d)])
    z_pred = np.array([np.cos(2.0 * np.pi * t / d) for t in range(d)])
    a = float(np.dot(z_pred, z_meas) / np.dot(z_pred, z_pred))
    resid = z_meas - a * z_pred
    return float(1.0 - np.sum(resid**2) / max(np.sum((z_meas - z_meas.mean()) ** 2), 1e-12))


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry", action="store_true")
    parser.add_argument("--backend", default=None)
    parser.add_argument("--fresh", action="store_true", help="ignore checkpoints, resubmit from scratch")
    parser.add_argument("--out-dir", type=Path, default=None)
    args = parser.parse_args()

    if args.fresh and not args.dry:
        clear_checkpoint(args.backend or "least_busy")

    backend = DryBackend() if args.dry else HardwareBackend(args.backend)
    out_dir = args.out_dir or Path(f"results_ibm1_{backend.name}")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.utcnow().isoformat() + "Z"
    print(f"AQ-PAGE-WOOTTERS-IBM-1  backend={backend.name}  dry={args.dry}  {ts}", flush=True)
    if not args.dry:
        print(f"  checkpoint file: {checkpoint_path(backend.name)} (delete or pass --fresh for a clean resubmit)", flush=True)

    # Layouts: d=8 needs the largest register (3 clock + 1 system + 3 env = 7);
    # d=4 uses a disjoint prefix-free chain so both fit without overlap if run
    # in the same session, and each is independently checkpointed by stage name.
    layout8 = find_chain(backend.coupling_map, backend.num_qubits, 7)
    layout4 = find_chain(backend.coupling_map, backend.num_qubits, 5)
    print(f"  layout d=4: {layout4}   layout d=8: {layout8}", flush=True)

    # --- Pre-registration, filed before any job ---
    prereg = {
        "program": "AQ-PAGE-WOOTTERS-IBM-1",
        "backend": backend.name, "dry_run": bool(args.dry), "submission_time": ts,
        "optimization_level": 0, "mu_grid_pi": (MU_GRID / np.pi).tolist(),
        "layouts": {"4": layout4, "8": layout8},
        "predictions": {
            str(2**n): {
                "exact_witness_curve": [exact_tvd(n, mu) for mu in MU_GRID],
                "h2_primary": "power law C = C0*cos(mu/2)^p fits far better than exponential C0*exp(-kE); "
                              "see AQ_PAGE_WOOTTERS_IBM_1_GATE0_RESULTS_2026-08-04.md for exact CI targets",
            }
            for n in CLOCK_SIZES
        },
        "gates": [
            "gate1_anchor", "gate2_monotone_decay", "gate3_threshold",
            "gate4_conditional_survives_all_mu", "gate5_h2_power_beats_exponential",
            "gate6_arrow_monotone_vn", "gate6_uncoupled_stays_near_pure",
        ],
    }
    (out_dir / "ibm1_prereg.json").write_text(json.dumps(prereg, indent=2), encoding="utf-8")
    print(f"  pre-registration filed: {out_dir / 'ibm1_prereg.json'}", flush=True)

    # --- Calibration: every physical qubit touched, prep|0>/|1> ---
    all_qubits = sorted(set(layout4) | set(layout8))
    n_cal_reg = max(all_qubits) + 1

    def cal_circuit(q: int, state: int) -> QuantumCircuit:
        qc = QuantumCircuit(n_cal_reg, 1)
        if state == 1:
            qc.x(q)
        qc.measure(q, 0)
        return qc

    cal_specs = [(q, s) for q in all_qubits for s in (0, 1)]
    cal_circuits = [cal_circuit(q, s) for q, s in cal_specs]
    print("\n--- JOB: CALIBRATION ---", flush=True)
    cal_counts, _ = backend.run_batch(cal_circuits, SHOTS_CAL, list(range(n_cal_reg)), stage="calibration")
    calib = {}
    for (q, s), counts in zip(cal_specs, cal_counts):
        total = sum(counts.values())
        calib[f"q{q}_prep{s}"] = counts.get("1", 0) / total if total else float("nan")
    print(f"  calibrated {len(all_qubits)} qubits", flush=True)

    results: dict = {"calibration": calib, "arms_1a": {}, "arm_1b": {}}

    # --- Arm 1A per clock size ---
    for n_clock in CLOCK_SIZES:
        d = 2**n_clock
        layout = layout4 if n_clock == 2 else layout8
        print(f"\n=== Arm 1A, d={d} ===", flush=True)

        witness_circuits = [build_witness_dec(n_clock, float(mu)) for mu in MU_GRID]
        w_counts, _ = backend.run_batch(witness_circuits, SHOTS_SWEEP, layout, stage=f"witness_d{d}")

        wc_circuits, wc_index = [], []
        for i, mu in enumerate(MU_GRID):
            for t in range(d):
                wc_circuits.append(build_witness_dec(n_clock, float(mu), fixed_t=t))
                wc_index.append((i, t))
        wc_counts, _ = backend.run_batch(wc_circuits, max(SHOTS_SWEEP // d, 100), layout, stage=f"witness_classical_d{d}")

        cond_circuits = [build_conditional_dec(n_clock, float(mu)) for mu in MU_GRID]
        c_counts, _ = backend.run_batch(cond_circuits, SHOTS_SWEEP, layout, stage=f"conditional_d{d}")

        # Conditional classical control needs a definite-|t> clock prep at
        # the SAME mu as its coherent counterpart; build_conditional_dec has
        # no fixed_t argument, so construct it directly here (same shape as
        # build_conditional_dec, only the clock prep line differs).
        from pw_ibm1_dryrun import history_prep
        cc_circuits = []
        for mu in MU_GRID:
            for t in range(d):
                qc = QuantumCircuit(2 * n_clock + 1, n_clock + 1)
                clock, system = list(range(n_clock)), n_clock
                env = list(range(n_clock + 1, 2 * n_clock + 1))
                history_prep(qc, clock, system, 2.0 * np.pi / d, fixed_t=t)
                for k, cq in enumerate(clock):
                    qc.cry(float(mu), cq, env[k])
                qc.measure(clock + [system], list(range(n_clock + 1)))
                cc_circuits.append(qc)
        cc_counts, _ = backend.run_batch(cc_circuits, max(SHOTS_SWEEP // d, 100), layout, stage=f"conditional_classical_d{d}")

        # --- Reduce to per-mu quantities ---
        rows = []
        for i, mu in enumerate(MU_GRID):
            tvd_meas, pk_meas = witness_tvd(w_counts[i], n_clock)
            p_cls = np.zeros(d)
            for j, t in enumerate(range(d)):
                _, p = witness_tvd(wc_counts[i * d + j], n_clock)
                p_cls += np.asarray(p) / d
            tvd_cls = float(0.5 * np.sum(np.abs(p_cls - 1.0 / d)))

            p1_meas = conditional_p1(c_counts[i], n_clock)
            r2_meas = cond_r2(p1_meas, n_clock)

            rows.append({
                "mu_pi": float(mu / np.pi),
                "witness_tvd": tvd_meas,
                "witness_classical_tvd": tvd_cls,
                "exact_tvd": exact_tvd(n_clock, float(mu)),
                "entanglement": clock_env_entanglement(n_clock, float(mu)),
                "conditional_r2": r2_meas,
            })
        results["arms_1a"][str(d)] = {"sweep": rows}
        print(f"  witness TVD: {[round(r['witness_tvd'], 4) for r in rows]}", flush=True)
        print(f"  cond R2:     {[round(r['conditional_r2'], 4) for r in rows]}", flush=True)

    # --- Arm 1B (d=8) ---
    # build_arrow_tomo uses n_clock+2 qubits (clock + system + ONE env
    # qubit, unlike arm 1A's n_clock env qubits) -- a strict prefix of the
    # 7-qubit arm-1A chain, and prefixes of a contiguous chain are
    # themselves contiguous, so this reuses the same physical qubits rather
    # than hunting for a second disjoint layout.
    n_clock = 3
    d = 8
    layout = layout8[: n_clock + 2]
    print(f"\n=== Arm 1B (arrow, d={d}) ===  layout: {layout}", flush=True)

    theta = np.pi / (2.0 * (d - 1))
    coupled_circ = [build_arrow_tomo(n_clock, couple=True, basis="Z")]
    uncoupled_circ = [build_arrow_tomo(n_clock, couple=False, basis=b) for b in ("X", "Y", "Z")]
    main_circuits = coupled_circ + uncoupled_circ
    main_counts, _ = backend.run_batch(main_circuits, SHOTS_ARROW_MAIN, layout, stage="arrow_main")

    classical_circuits = [build_arrow_tomo(n_clock, couple=True, basis="Z", fixed_t=t) for t in range(d)]
    classical_counts, _ = backend.run_batch(classical_circuits, SHOTS_ARROW_CLASSICAL, layout, stage="arrow_classical")

    p1_coupled = conditional_p1(main_counts[0], n_clock)
    arrow_coupled_vn = [binary_entropy(p1_coupled[t]) for t in range(d)]  # Z-diagonal, H2(p1) is exact here

    axes_unc = {}
    for basis, counts in zip(("X", "Y", "Z"), main_counts[1:]):
        axes_unc[basis] = conditional_p1(counts, n_clock)
    arrow_uncoupled_vn = []
    for t in range(d):
        r = np.array([1 - 2 * axes_unc["X"][t], 1 - 2 * axes_unc["Y"][t], 1 - 2 * axes_unc["Z"][t]])
        arrow_uncoupled_vn.append(von_neumann_from_bloch(r))

    arrow_classical_vn = []
    for t in range(d):
        p1 = conditional_p1(classical_counts[t], n_clock)
        arrow_classical_vn.append(binary_entropy(p1[t]) if not np.isnan(p1[t]) else 0.0)

    results["arm_1b"] = {
        "theta_pi": float(theta / np.pi),
        "coupled_von_neumann": arrow_coupled_vn,
        "uncoupled_von_neumann": arrow_uncoupled_vn,
        "classical_von_neumann": arrow_classical_vn,
    }
    print(f"  coupled S(t)  : {[round(v, 3) for v in arrow_coupled_vn]}", flush=True)
    print(f"  uncoupled S(t): {[round(v, 3) for v in arrow_uncoupled_vn]}  <- should stay near 0", flush=True)
    print(f"  classical S(t): {[round(v, 3) for v in arrow_classical_vn]}", flush=True)

    # --- H2 fits on the measured witness curves ---
    fits = {}
    for n_clock in CLOCK_SIZES:
        d = 2**n_clock
        rows = results["arms_1a"][str(d)]["sweep"]
        mu = np.array([r["mu_pi"] for r in rows]) * np.pi
        ent = np.array([r["entanglement"] for r in rows])
        tvd = np.array([r["witness_tvd"] for r in rows])
        exp_fit = fit_exponential(ent, tvd)
        pow_fit = fit_power_law(mu, tvd)
        fits[str(d)] = {"exponential_in_entanglement": exp_fit, "power_law_in_overlap": pow_fit}
        print(f"\n  d={d} measured fits: exp R2={exp_fit.get('R2', float('nan')):.4f}   "
              f"power R2={pow_fit.get('R2', float('nan')):.4f}", flush=True)
    results["h2_fits"] = fits

    # --- Gate scoring ---
    gates = {}
    for n_clock in CLOCK_SIZES:
        d = 2**n_clock
        rows = results["arms_1a"][str(d)]["sweep"]
        tvd = [r["witness_tvd"] for r in rows]
        # Slack must scale with the actual shot-noise floor at THIS shot
        # count, not a fixed number -- a hardcoded 0.05 was calibrated
        # against the dry run's 8000-shot circuits and silently became too
        # tight once the sweep circuits were cut to 500 shots to fit budget
        # (3x floor at d=8, 500 shots is ~0.11, not 0.05). Same principled
        # criterion as Gate 0/3, applied consistently here too.
        mu_floors = [3.0 * expected_tvd_shot_noise(exact_pk(n_clock, np.pi * r["mu_pi"]), SHOTS_SWEEP) for r in rows]
        gates[f"gate2_monotone_decay_d{d}"] = bool(
            all(tvd[i + 1] <= tvd[i] + mu_floors[i] + mu_floors[i + 1] for i in range(len(tvd) - 1))
        )
        gates[f"gate3_threshold_d{d}"] = bool(tvd[-1] < rows[-1]["witness_classical_tvd"] + 3 * expected_tvd_shot_noise(exact_pk(n_clock, np.pi), SHOTS_SWEEP))
        worst_r2 = min(r["conditional_r2"] for r in rows)
        gates[f"gate4_cond_survives_d{d}"] = bool(worst_r2 > 0.90)
        gates[f"gate5_power_beats_exp_d{d}"] = bool(
            fits[str(d)]["power_law_in_overlap"].get("R2", -1) > fits[str(d)]["exponential_in_entanglement"].get("R2", 2)
        )
    gates["gate6_arrow_monotone"] = bool(all(
        arrow_coupled_vn[i + 1] >= arrow_coupled_vn[i] - 0.1 for i in range(len(arrow_coupled_vn) - 1)
    ))
    gates["gate6_uncoupled_stays_near_pure"] = bool(max(arrow_uncoupled_vn) < 0.5)
    results["gates"] = gates
    results["all_gates_pass"] = bool(all(gates.values()))
    results["job_ids"] = getattr(backend, "job_ids", [])

    (out_dir / "ibm1_results.json").write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    if not args.dry:
        clear_checkpoint(backend.name)
    print(f"\n[GATES] {json.dumps(gates, indent=2)}", flush=True)
    print(f"[DONE] all_gates_pass={results['all_gates_pass']}  -> {out_dir / 'ibm1_results.json'}", flush=True)


if __name__ == "__main__":
    main()
