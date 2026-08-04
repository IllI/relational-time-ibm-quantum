#!/usr/bin/env python3
"""CHRONOS-REAL-ENTROPIC-CLOCK-0.

Reanalysis of the already-collected US/EU TPU "now" streams using the
mechanism that was actually confirmed on synthetic histories in the
Page-Wootters/D-LinOSS branch: an accumulated entropy/event causal-action
coordinate (the real-data analog of generator arm A10) scored by a frozen
event-damped complex D-LinOSS operator under global monotone path
observability, instead of the ridge-only pointwise pipeline that
AQ-DLINOSS-CHRONO-0 used.

This does not collect new data and does not require a TPU. It reads the
compact q_latency JSON files already archived under
chronos_time_emission/results0b_independence_remote/.

Motivation (recorded 2026-08-03): the live two-host CHRONOS run
(AQ-DLINOSS-CHRONO-0) scored a ridge-affine transition surrogate and
returned a clean null. The Page-Wootters branch later found, on synthetic
data, that a stationary transition operator cannot exploit relational time
at all -- only a generator with a real entropy/event/causal-action history
(arm A10) plus a *damping* channel driven by that history (the
event-damped D-LinOSS operator) closed the gap to the ridge baseline. That
combination was never applied to the real TPU streams. This script closes
that gap using only local CPU compute.

Claim boundary: a positive result here would say "the real TPU host
telemetry contains a globally recoverable relational-clock path when scored
with the mechanism that worked on synthetic entropy-bearing histories." It
would NOT establish shared physical time, quantum teleportation, or a
physical Page-Wootters realization. The CHRONOS-MARGINAL-DRIFT-1 finding
(r_full stays high across a genuine one-hour offset) is carried in here as
a real, previously-collected control arm (`plus1h_real`), not a synthetic
proxy, because it is the strongest available check against a
structural-similarity confound.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.signal import hilbert

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parent
EQG_DIR = REPO_ROOT / "emergent_quantum_geometries"
sys.path.insert(0, str(EQG_DIR))

import jax  # noqa: E402
import jax.numpy as jnp  # noqa: E402

import program_aq_page_wootters0 as pw  # noqa: E402
import program_aq_page_wootters_path_observability0 as po  # noqa: E402
import program_aq_page_wootters_a10_event_damped_confirm0 as ed  # noqa: E402

DATA_DIR = THIS_DIR / "results0b_independence_remote"

WINDOW = 256
HOP = 128
FS_HZ = 128.0
SCHUMANN_BAND = (6.0, 9.0)
ANTI_BAND = (10.0, 13.0)
GRID_BAND = (45.0, 55.0)
LOW_DRIFT_BAND = (0.0, 2.0)
HIGH_RESIDUAL_BAND = (40.0, 63.0)
PHASE_BAND = (6.0, 40.0)
CONTEXT_STEPS = 8
HIDDEN_DIM = 32
EPOCHS = 350
LEARNING_RATE = 3e-3
BOOTSTRAP_SAMPLES = 400

PAIRS = {
    "seed11": ("alice_us_q", "bob_eu_q"),
    "rep1": ("alice_us_rep1_q", "bob_eu_rep1_q"),
    "chrono0_seed14": ("alice_us_chrono0_q", "bob_eu_chrono0_q"),
}
PLUS1H_FILE = "bob_eu_chrono0_plus1h_q"
PLUS1H_PAIR = "chrono0_seed14"


def load_q(name: str) -> np.ndarray:
    with open(DATA_DIR / f"{name}.json", "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    return np.asarray(payload["q_latency"], dtype=np.float64)


def robust_norm(x: np.ndarray, clip: float = 5.0) -> np.ndarray:
    med = np.median(x)
    mad = np.median(np.abs(x - med)) + 1e-12
    return np.clip((x - med) / mad, -clip, clip)


def fft_band_energy(x: np.ndarray, fs_hz: float, band: tuple[float, float]) -> float:
    centered = x - np.mean(x)
    freqs = np.fft.rfftfreq(centered.size, d=1.0 / fs_hz)
    spec = np.fft.rfft(centered)
    lo, hi = band
    hi = min(hi, fs_hz / 2.0 - 1e-6)
    mask = (freqs >= lo) & (freqs <= hi)
    if not np.any(mask):
        return 0.0
    return float(np.mean(np.abs(spec[mask]) ** 2))


def bandpass(x: np.ndarray, fs_hz: float, band: tuple[float, float]) -> np.ndarray:
    centered = x - np.mean(x)
    freqs = np.fft.rfftfreq(centered.size, d=1.0 / fs_hz)
    spec = np.fft.rfft(centered)
    lo, hi = band
    hi = min(hi, fs_hz / 2.0 - 1e-6)
    mask = (freqs >= lo) & (freqs <= hi)
    return np.fft.irfft(spec * mask, n=centered.size)


def local_entropy(window: np.ndarray, bins: int = 16) -> float:
    norm = robust_norm(window)
    hist, _ = np.histogram(norm, bins=bins, range=(-5.0, 5.0), density=False)
    p = hist.astype(np.float64)
    total = p.sum()
    if total <= 0:
        return 0.0
    p = p / total
    p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))


def event_activity(window: np.ndarray, threshold: float = 3.0) -> float:
    norm = robust_norm(window, clip=1e6)
    return float(np.mean(np.abs(norm) > threshold))


def extract_features(q: np.ndarray, fs_hz: float = FS_HZ) -> dict[str, np.ndarray]:
    """Build the locked CHRONOS-0 minimum feature vector plus the entropic-
    time causal-action channel that AQ-DLINOSS-CHRONO-0 never included.
    """
    n = q.size
    phase_signal = bandpass(q, fs_hz, PHASE_BAND)
    analytic = hilbert(phase_signal)
    inst_phase_full = np.unwrap(np.angle(analytic))

    centers = list(range(WINDOW, n - WINDOW, HOP))
    rows = {
        "mean": [], "std": [], "median": [], "mad": [],
        "schumann_energy": [], "anti_energy": [], "grid_energy": [],
        "low_drift_energy": [], "high_residual_energy": [],
        "phase": [], "phase_velocity": [], "phase_curvature": [],
        "entropy": [], "event_activity": [],
    }
    for center in centers:
        window = q[center - WINDOW : center]
        rows["mean"].append(np.mean(window))
        rows["std"].append(np.std(window))
        rows["median"].append(np.median(window))
        rows["mad"].append(np.median(np.abs(window - np.median(window))))
        rows["schumann_energy"].append(fft_band_energy(window, fs_hz, SCHUMANN_BAND))
        rows["anti_energy"].append(fft_band_energy(window, fs_hz, ANTI_BAND))
        rows["grid_energy"].append(fft_band_energy(window, fs_hz, GRID_BAND))
        rows["low_drift_energy"].append(fft_band_energy(window, fs_hz, LOW_DRIFT_BAND))
        rows["high_residual_energy"].append(fft_band_energy(window, fs_hz, HIGH_RESIDUAL_BAND))
        rows["phase"].append(inst_phase_full[center])
        rows["phase_velocity"].append(inst_phase_full[center] - inst_phase_full[center - HOP])
        rows["phase_curvature"].append(
            inst_phase_full[min(center + HOP, n - 1)]
            - 2.0 * inst_phase_full[center]
            + inst_phase_full[center - HOP]
        )
        rows["entropy"].append(local_entropy(window))
        rows["event_activity"].append(event_activity(window))

    out = {name: np.asarray(values, dtype=np.float64) for name, values in rows.items()}
    entropy_rate = np.concatenate(([0.0], np.abs(np.diff(out["entropy"]))))
    out["entropy_rate"] = entropy_rate
    out["strain"] = np.abs(out["phase_curvature"])

    # Entropic-time coordinate: accumulated entropy-production + event action,
    # the real-data analog of A10's causal_action and of tau(lambda) ~ int dS
    # in arXiv:2509.07745. Never computed in AQ-DLINOSS-CHRONO-0.
    causal_action = np.cumsum(0.6 * entropy_rate + 1.0 * out["event_activity"])
    out["causal_action"] = causal_action
    return out


def robust_scale(train_ref: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    med = np.median(train_ref, axis=0, keepdims=True)
    mad = np.median(np.abs(train_ref - med), axis=0, keepdims=True)
    scale = np.maximum(1.4826 * mad, 1e-6)
    return med, scale


def build_clock_matrix(feat: dict[str, np.ndarray]) -> np.ndarray:
    channels = [
        "mean", "std", "median", "mad",
        "schumann_energy", "anti_energy", "grid_energy",
        "low_drift_energy", "high_residual_energy",
        "phase_velocity", "strain",
        "entropy_rate", "event_activity", "causal_action",
    ]
    return np.stack([feat[c] for c in channels], axis=1)


def build_aux_matrix(feat: dict[str, np.ndarray]) -> np.ndarray:
    return np.stack(
        [
            feat["event_activity"],
            feat["entropy_rate"],
            feat["causal_action"],
            feat["strain"],
        ],
        axis=1,
    )


def normalize_with_ref(matrix: np.ndarray, ref: np.ndarray) -> np.ndarray:
    mean = np.mean(ref, axis=0, keepdims=True)
    std = np.maximum(np.std(ref, axis=0, keepdims=True), 1e-6)
    return (matrix - mean) / std


def run_pair(
    pair_name: str,
    alice_name: str,
    bob_name: str,
    extra_controls: dict[str, np.ndarray] | None = None,
) -> dict:
    q_a = load_q(alice_name)
    q_b = load_q(bob_name)
    feat_a = extract_features(q_a)
    feat_b = extract_features(q_b)
    n_windows = min(len(feat_a["mean"]), len(feat_b["mean"]))
    for feat in (feat_a, feat_b):
        for key in list(feat.keys()):
            feat[key] = feat[key][:n_windows]

    calibration_steps = n_windows // 2

    clock_a_raw = build_clock_matrix(feat_a)
    clock_b_raw = build_clock_matrix(feat_b)
    ref = np.concatenate((clock_a_raw[:calibration_steps], clock_b_raw[:calibration_steps]), axis=0)
    clock_a = normalize_with_ref(clock_a_raw, ref)
    clock_b = normalize_with_ref(clock_b_raw, ref)

    aux_a_raw = build_aux_matrix(feat_a)
    aux_ref = aux_a_raw[:calibration_steps]
    aux_med, aux_scale = robust_scale(aux_ref)
    aux_a = (aux_a_raw - aux_med) / aux_scale

    rng = np.random.default_rng(abs(hash(pair_name)) % (2**32))
    shuffled = clock_b[rng.permutation(n_windows)]
    severed = clock_b[rng.permutation(n_windows)]
    wrong_lag = np.asarray(po.lag_shift(jnp.asarray(clock_b), 8))
    block_shuffled = np.asarray(po.block_shuffle(jnp.asarray(clock_b), jax.random.PRNGKey(int(rng.integers(1 << 30))), block_size=8))

    null_streams = {
        "shuffled_path": jnp.asarray(shuffled),
        "severed_path": jnp.asarray(severed),
        "wrong_lag_path": jnp.asarray(wrong_lag),
        "block_shuffled_path": jnp.asarray(block_shuffled),
    }
    if extra_controls:
        for name, stream in extra_controls.items():
            m = min(len(stream), n_windows)
            null_streams[name] = jnp.asarray(normalize_with_ref(stream[:m], ref)[: n_windows] if m == n_windows else np.resize(normalize_with_ref(stream[:m], ref), (n_windows, clock_a.shape[1])))

    clock_a_j = jnp.asarray(clock_a)
    clock_b_j = jnp.asarray(clock_b)

    calibration_query = jnp.arange(0, calibration_steps - 1)
    payload_query = jnp.arange(calibration_steps, n_windows - 1)

    fit_cost, fit_path = po.path_cost(clock_a_j, clock_b_j, calibration_query)
    rel_cost, rel_path = po.path_cost(clock_a_j, clock_b_j, payload_query)
    fit_match = jnp.asarray(fit_path, dtype=jnp.int32)
    rel_match = jnp.asarray(rel_path, dtype=jnp.int32)

    control_matches = {}
    for name, stream in null_streams.items():
        _, path = po.path_cost(clock_a_j, stream, payload_query)
        control_matches[name] = jnp.asarray(path, dtype=jnp.int32)

    path_metrics = po.path_metrics(clock_a_j, clock_b_j, null_streams, payload_query, rel_match)

    delta_a = clock_a[1:] - clock_a[:-1]
    delta_b = clock_b[1:] - clock_b[:-1]
    delta_a_j = jnp.asarray(delta_a)
    delta_b_j = jnp.asarray(delta_b)

    def windows(seq, indices):
        return ed.causal_windows(seq, indices, CONTEXT_STEPS)

    x_train = windows(delta_a_j, fit_query := jnp.arange(0, calibration_steps - 1))
    aux_train = windows(jnp.asarray(aux_a[:-1]), fit_query)
    y_train = delta_b_j[fit_match]
    weights = jnp.ones((x_train.shape[0],))

    key = jax.random.PRNGKey(int(rng.integers(1 << 30)))
    params, diagnostics = ed.train_model(
        key, x_train, aux_train, y_train, weights, HIDDEN_DIM, "event_damped", EPOCHS, LEARNING_RATE
    )
    pred = ed.predict_all(params, delta_a_j, jnp.asarray(aux_a), "event_damped", CONTEXT_STEPS)

    ridge_op, ridge_bias = pw.ridge_affine_map(delta_a_j[fit_query], y_train, ridge=1e-3)
    ridge_pred = delta_a_j @ ridge_op + ridge_bias

    def score(prediction, query, matches, target):
        rows = pw.cosine_rows(prediction[query], target[matches])
        return float(jnp.mean(rows)), rows

    rel_score, rel_rows = score(pred, payload_query, rel_match, delta_b_j)
    ridge_score, ridge_rows = score(ridge_pred, payload_query, rel_match, delta_b_j)

    control_scores = {}
    control_rows_list = []
    for name, matches in control_matches.items():
        target = delta_b_j if name != "cross_pair_path" else delta_b_j
        s, rows = score(pred, payload_query, matches, target)
        control_scores[name] = s
        control_rows_list.append(rows)
    control_stack = jnp.stack(control_rows_list)
    gains = rel_rows - jnp.max(control_stack, axis=0)
    window_fraction = float(jnp.mean(gains > 0.0))
    fold_key = jax.random.fold_in(key, 999)
    idx = jax.random.randint(fold_key, (BOOTSTRAP_SAMPLES, gains.shape[0]), 0, gains.shape[0])
    boot_vals = jnp.mean(gains[idx], axis=1)
    ci_lo, ci_hi = [float(v) for v in jnp.quantile(boot_vals, jnp.array([0.025, 0.975]))]

    best_null_name = max(control_scores, key=control_scores.get)
    best_null_score = control_scores[best_null_name]

    return {
        "pair": pair_name,
        "n_windows": int(n_windows),
        "calibration_steps": int(calibration_steps),
        "diagnostics": diagnostics,
        "path": {
            "true_path_cost": path_metrics["true_path_cost"],
            "best_null_path_cost": path_metrics["best_null_path_cost"],
            "path_rank": path_metrics["path_rank"],
            "path_margin_per_step": path_metrics["path_margin_per_step"],
            "best_null_type": path_metrics["best_null_type"],
            "segment_margin_w16": path_metrics["segment_margin_w16"],
        },
        "dlinoss": {
            "relational_score": rel_score,
            "best_null_score": best_null_score,
            "best_null_name": best_null_name,
            "relational_gain": rel_score - best_null_score,
            "window_fraction_beating_best_null": window_fraction,
            "gain_ci95": [ci_lo, ci_hi],
            "control_scores": control_scores,
        },
        "ridge": {
            "score": ridge_score,
            "dlinoss_minus_ridge": rel_score - ridge_score,
        },
        "gates": {
            "path_rank1": bool(path_metrics["path_rank"] == 1),
            "gain_positive": bool(rel_score - best_null_score > 0.0),
            "gain_gate_010": bool(rel_score - best_null_score > 0.10),
            "ci_lower_positive": bool(ci_lo > 0.0),
            "window_fraction_070": bool(window_fraction >= 0.70),
        },
    }


def main() -> None:
    print("CHRONOS-REAL-ENTROPIC-CLOCK-0", flush=True)
    results = {}

    # Pre-load Bob streams from the other real pairs so cross_pair_path is a
    # genuinely different real recording, not a synthetic surrogate.
    all_bob_feats = {}
    for pair_name, (_, bob_name) in PAIRS.items():
        q_bob = load_q(bob_name)
        all_bob_feats[pair_name] = build_clock_matrix(extract_features(q_bob))

    plus1h_feat = build_clock_matrix(extract_features(load_q(PLUS1H_FILE)))

    for pair_name, (alice_name, bob_name) in PAIRS.items():
        extra = {}
        other_pairs = [p for p in PAIRS if p != pair_name]
        if other_pairs:
            extra["cross_pair_path"] = all_bob_feats[other_pairs[0]]
        if pair_name == PLUS1H_PAIR:
            extra["plus1h_real_path"] = plus1h_feat
        print(f"[PAIR] {pair_name}: alice={alice_name} bob={bob_name} extra_controls={list(extra)}", flush=True)
        result = run_pair(pair_name, alice_name, bob_name, extra)
        results[pair_name] = result
        d = result["dlinoss"]
        p = result["path"]
        print(
            f"[RESULT] {pair_name} path_rank={p['path_rank']} path_margin_step={p['path_margin_per_step']:.4f} "
            f"best_null={p['best_null_type']} | dlinoss_gain={d['relational_gain']:.4f} "
            f"best_null_name={d['best_null_name']} window_frac={d['window_fraction_beating_best_null']:.3f} "
            f"ci95={d['gain_ci95']} minus_ridge={result['ridge']['dlinoss_minus_ridge']:.4f}",
            flush=True,
        )

    out_dir = THIS_DIR / "results_real_entropic_clock_0"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {"program": "CHRONOS-REAL-ENTROPIC-CLOCK-0", "results": results}
    (out_dir / "results.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = ["# CHRONOS-REAL-ENTROPIC-CLOCK-0 Summary", ""]
    for pair_name, result in results.items():
        d = result["dlinoss"]
        p = result["path"]
        g = result["gates"]
        lines.append(f"## {pair_name}")
        lines.append(f"- path_rank: `{p['path_rank']}` (best_null=`{p['best_null_type']}`)")
        lines.append(f"- path_margin_per_step: `{p['path_margin_per_step']:.4f}`")
        lines.append(f"- dlinoss_relational_score: `{d['relational_score']:.4f}`")
        lines.append(f"- dlinoss_best_null_score: `{d['best_null_score']:.4f}` (`{d['best_null_name']}`)")
        lines.append(f"- dlinoss_relational_gain: `{d['relational_gain']:.4f}`")
        lines.append(f"- window_fraction_beating_best_null: `{d['window_fraction_beating_best_null']:.3f}`")
        lines.append(f"- gain_ci95: `{d['gain_ci95']}`")
        lines.append(f"- dlinoss_minus_ridge: `{result['ridge']['dlinoss_minus_ridge']:.4f}`")
        lines.append(f"- gates: `{g}`")
        lines.append("")
    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"[DONE] results={out_dir}", flush=True)


if __name__ == "__main__":
    main()
