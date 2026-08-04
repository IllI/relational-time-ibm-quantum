#!/usr/bin/env python3
"""AQ-PAGE-WOOTTERS-DLINOSS-QUANTUM-CLOCK-BOUND-0.

Estimate whether the remaining local-window failures are close to a clock-state
distinguishability bound. This freezes the A10 event-damped bridge and adds
Gram-overlap / Helstrom-style diagnostics for the clock-history records.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import jax
import jax.numpy as jnp
import numpy as np

import program_aq_page_wootters0 as pw
import program_aq_page_wootters_global_causal_memory0 as gm
import program_aq_page_wootters_path_observability0 as po


CONTROL_NAMES = (
    "wrong_lag_path",
    "shuffled_path",
    "severed_path",
    "cross_seed_path",
    "same_stats_permuted_path",
    "block_shuffled_path",
)
FEATURE_NAME = "contrastive_patch_encoder"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--time-steps", type=int, default=128)
    parser.add_argument("--state-dim", type=int, default=64)
    parser.add_argument("--latent-dim", type=int, default=8)
    parser.add_argument("--true-lag", type=int, default=5)
    parser.add_argument("--seeds", nargs="*", type=int, default=[11, 12, 13, 14, 15, 16, 17, 18, 19, 20])
    parser.add_argument("--noise-values", nargs="*", type=float, default=[0.0, 0.01, 0.02, 0.03])
    parser.add_argument("--hidden-dims", nargs="*", type=int, default=[32])
    parser.add_argument("--context-steps", nargs="*", type=int, default=[8])
    parser.add_argument("--operators", nargs="*", default=["event_damped"])
    parser.add_argument("--losses", nargs="*", default=["event_weighted"])
    parser.add_argument("--epochs", type=int, default=350)
    parser.add_argument("--learning-rate", type=float, default=3e-3)
    parser.add_argument("--bootstrap-samples", type=int, default=400)
    parser.add_argument("--out-dir", type=Path, default=Path("aq_page_wootters_quantum_clock_bound0"))
    parser.add_argument("--require-tpu", action="store_true")
    return parser.parse_args()


def causal_aux(histories: dict[str, jax.Array], prefix: str) -> jax.Array:
    tracks = [
        histories[f"event_activity_{prefix}"],
        histories[f"entropy_rate_{prefix}"],
        histories[f"residual_memory_{prefix}"],
        histories[f"strain_{prefix}"],
        histories[f"causal_action_{prefix}"],
    ]
    raw = jnp.stack(tracks, axis=1)
    center = jnp.median(raw[: raw.shape[0] // 2], axis=0, keepdims=True)
    mad = jnp.median(jnp.abs(raw[: raw.shape[0] // 2] - center), axis=0, keepdims=True)
    scale = jnp.maximum(1.4826 * mad, 1e-6)
    return (raw - center) / scale


def causal_windows(sequence: jax.Array, indices: jax.Array, context_steps: int) -> jax.Array:
    padded = jnp.pad(sequence, ((context_steps - 1, 0), (0, 0)), mode="edge")
    offsets = jnp.arange(context_steps)
    return padded[indices[:, None] + offsets[None, :]]


def init_params(key: jax.Array, input_dim: int, aux_dim: int, hidden_dim: int, output_dim: int) -> dict:
    keys = jax.random.split(key, 8)
    input_scale = 1.0 / jnp.sqrt(float(input_dim))
    hidden_scale = 1.0 / jnp.sqrt(float(hidden_dim))
    return {
        "raw_gamma": jnp.full((hidden_dim,), -3.0),
        "raw_scale": jnp.zeros((hidden_dim,)),
        "omega": 0.35 * jax.random.normal(keys[0], (hidden_dim,)),
        "gamma_aux": 0.02 * jax.random.normal(keys[1], (aux_dim, hidden_dim)),
        "omega_aux": 0.02 * jax.random.normal(keys[2], (aux_dim, hidden_dim)),
        "B_re": input_scale * jax.random.normal(keys[3], (input_dim, hidden_dim)),
        "B_im": input_scale * jax.random.normal(keys[4], (input_dim, hidden_dim)),
        "C_re": hidden_scale * jax.random.normal(keys[5], (hidden_dim, output_dim)),
        "C_im": hidden_scale * jax.random.normal(keys[6], (hidden_dim, output_dim)),
        "bias": jnp.zeros((output_dim,)),
    }


def forward(params: dict, x_seq: jax.Array, aux_seq: jax.Array, operator: str) -> jax.Array:
    b_matrix = params["B_re"] + 1j * params["B_im"]
    c_matrix = params["C_re"] + 1j * params["C_im"]
    base_phase = jnp.pi * jnp.tanh(params["omega"])
    if operator == "hamiltonian_plus_scale":
        lam = jnp.exp(0.08 * jnp.tanh(params["raw_scale"])) * jnp.exp(1j * base_phase)

        def step(state, x_t):
            next_state = state * lam + x_t.astype(jnp.complex64) @ b_matrix
            output = jnp.real(next_state @ c_matrix) + params["bias"]
            return next_state, output

        _, outputs = jax.lax.scan(
            step, jnp.zeros((lam.shape[0],), dtype=jnp.complex64), x_seq
        )
        return outputs
    if operator != "event_damped":
        raise ValueError(f"unknown operator: {operator}")

    base_gamma = 0.030 * jax.nn.softplus(params["raw_gamma"])
    gamma_aux = 0.018 * jax.nn.softplus(params["gamma_aux"])
    omega_aux = 0.055 * jnp.tanh(params["omega_aux"])

    def step(state, inputs):
        x_t, aux_t = inputs
        gamma_t = base_gamma + jnp.clip(aux_t @ gamma_aux, 0.0, 0.40)
        phase_t = base_phase + aux_t @ omega_aux
        lam_t = jnp.exp(-gamma_t + 1j * phase_t)
        next_state = state * lam_t + x_t.astype(jnp.complex64) @ b_matrix
        output = jnp.real(next_state @ c_matrix) + params["bias"]
        return next_state, output

    _, outputs = jax.lax.scan(
        step,
        jnp.zeros((params["omega"].shape[0],), dtype=jnp.complex64),
        (x_seq, aux_seq),
    )
    return outputs


def loss_fn(params, x_train, aux_train, y_train, weights, operator):
    pred = jax.vmap(forward, in_axes=(None, 0, 0, None))(params, x_train, aux_train, operator)[:, -1, :]
    row_mse = jnp.mean((pred - y_train) ** 2, axis=1)
    row_cos = 1.0 - pw.cosine_rows(pred, y_train)
    weighted = jnp.mean(weights * (row_mse + 0.25 * row_cos)) / jnp.maximum(jnp.mean(weights), 1e-6)
    penalty = 1e-5 * sum(jnp.mean(value * value) for key, value in params.items() if key.startswith(("B_", "C_", "gamma_aux", "omega_aux")))
    return weighted + penalty


def train_model(key, x_train, aux_train, y_train, weights, hidden_dim, operator, epochs, learning_rate):
    params = init_params(key, x_train.shape[2], aux_train.shape[2], hidden_dim, y_train.shape[1])
    m = jax.tree_util.tree_map(jnp.zeros_like, params)
    v = jax.tree_util.tree_map(jnp.zeros_like, params)

    @jax.jit
    def step(carry, iteration):
        current, first, second = carry
        loss, grads = jax.value_and_grad(loss_fn)(current, x_train, aux_train, y_train, weights, operator)
        grads = jax.tree_util.tree_map(lambda g: jnp.clip(g, -1.0, 1.0), grads)
        first = jax.tree_util.tree_map(lambda a, g: 0.9 * a + 0.1 * g, first, grads)
        second = jax.tree_util.tree_map(lambda a, g: 0.999 * a + 0.001 * g * g, second, grads)
        t = iteration + 1
        mh = jax.tree_util.tree_map(lambda a: a / (1.0 - 0.9**t), first)
        vh = jax.tree_util.tree_map(lambda a: a / (1.0 - 0.999**t), second)
        current = jax.tree_util.tree_map(lambda p, a, b: p - learning_rate * a / (jnp.sqrt(b) + 1e-8), current, mh, vh)
        return (current, first, second), loss

    (params, _, _), losses = jax.lax.scan(step, (params, m, v), jnp.arange(epochs))
    pred = jax.vmap(forward, in_axes=(None, 0, 0, None))(params, x_train, aux_train, operator)[:, -1, :]
    return params, {
        "initial_loss": float(losses[0]),
        "final_loss": float(losses[-1]),
        "calibration_cosine": float(jnp.mean(pw.cosine_rows(pred, y_train))),
    }


def predict_all(params, delta_a, aux_a, operator, context_steps):
    indices = jnp.arange(delta_a.shape[0])
    return jax.vmap(forward, in_axes=(None, 0, 0, None))(
        params,
        causal_windows(delta_a, indices, context_steps),
        causal_windows(aux_a[:-1], indices, context_steps),
        operator,
    )[:, -1, :]


def build_paths(histories, key, calibration_steps):
    spec = next(spec for spec in gm.FEATURE_SPECS if spec["name"] == FEATURE_NAME)
    calibration_query = jnp.arange(0, calibration_steps - 1)
    oracle_calibration = gm.intrinsic_oracle_path(histories, calibration_query)
    alice, bob, nulls = gm.feature_bundle(spec, histories, key, calibration_steps, calibration_query, oracle_calibration)
    path_nulls = {
        "wrong_lag_path": po.lag_shift(bob, int(histories["true_lag"]) + 4),
        "shuffled_path": nulls["shuffled_clock"],
        "severed_path": nulls["severed_clock"],
        "cross_seed_path": nulls["cross_seed_clock"],
        "same_stats_permuted_path": nulls["causal_stats_permuted_clock"],
        "block_shuffled_path": po.block_shuffle(bob, jax.random.fold_in(key, 900)),
    }
    return alice, bob, path_nulls


def select_path(alice, stream, query):
    _, path = po.path_cost(alice, stream, query)
    return jnp.asarray(path, dtype=jnp.int32)


def score(pred, query, matches, target_delta):
    rows = pw.cosine_rows(pred[query], target_delta[matches])
    return float(jnp.mean(rows)), rows


def bootstrap_ci(key, gains, samples):
    idx = jax.random.randint(key, (samples, gains.shape[0]), 0, gains.shape[0])
    vals = jnp.mean(gains[idx], axis=1)
    q = jnp.quantile(vals, jnp.array([0.025, 0.975]))
    return float(q[0]), float(q[1])


def normalized_rows(x):
    return x / jnp.maximum(jnp.linalg.norm(x, axis=1, keepdims=True), 1e-8)


def clock_bound_metrics(alice, bob, path_nulls, query, rel_match, control_matches, gains):
    a_state = normalized_rows(alice)[query]
    b_state = normalized_rows(bob)
    true_state = b_state[rel_match]
    true_similarity = jnp.sum(a_state * true_state, axis=1) ** 2

    null_similarities = []
    false_overlaps = []
    for name, matches in control_matches.items():
        if name == "cross_seed_path":
            stream_state = normalized_rows(path_nulls[name])
        else:
            stream_state = normalized_rows(path_nulls[name])
        candidate_state = stream_state[matches]
        null_similarities.append(jnp.sum(a_state * candidate_state, axis=1) ** 2)
        false_overlaps.append(jnp.sum(true_state * candidate_state, axis=1) ** 2)

    null_stack = jnp.stack(null_similarities)
    false_stack = jnp.stack(false_overlaps)
    nearest_null_similarity = jnp.max(null_stack, axis=0)
    nearest_nontrue_overlap = jnp.max(false_stack, axis=0)
    helstrom_success_bound = 0.5 * (1.0 + jnp.sqrt(jnp.clip(1.0 - nearest_nontrue_overlap, 0.0, 1.0)))
    observed_success = gains > 0.0
    failed = ~observed_success

    gram = normalized_rows(bob[payload_query_like(query, bob.shape[0])])
    gram_matrix = gram @ gram.T
    offdiag = gram_matrix - jnp.eye(gram_matrix.shape[0], dtype=gram_matrix.dtype)
    velocity = jnp.diff(b_state, axis=0)
    qfi_proxy = jnp.sum(velocity * velocity, axis=1)
    qfi_query = qfi_proxy[jnp.clip(rel_match, 0, qfi_proxy.shape[0] - 1)]

    mean_bound = jnp.mean(helstrom_success_bound)
    return {
        "true_similarity_mean": float(jnp.mean(true_similarity)),
        "nearest_null_similarity_mean": float(jnp.mean(nearest_null_similarity)),
        "nearest_nontrue_overlap_mean": float(jnp.mean(nearest_nontrue_overlap)),
        "nearest_nontrue_overlap_failed_mean": float(jnp.mean(jnp.where(failed, nearest_nontrue_overlap, 0.0)) / jnp.maximum(jnp.mean(failed), 1e-6)),
        "mean_offdiag_overlap": float(jnp.mean(jnp.abs(offdiag))),
        "collision_rate_from_gram": float(jnp.mean(nearest_nontrue_overlap > 0.90)),
        "helstrom_success_bound_mean": float(mean_bound),
        "helstrom_success_bound_median": float(jnp.median(helstrom_success_bound)),
        "observed_window_success": float(jnp.mean(observed_success)),
        "bound_normalized_window_score": float(jnp.mean(observed_success) / jnp.maximum(mean_bound, 1e-6)),
        "qfi_proxy_mean": float(jnp.mean(qfi_query)),
        "qfi_proxy_failed_mean": float(jnp.mean(jnp.where(failed, qfi_query, 0.0)) / jnp.maximum(jnp.mean(failed), 1e-6)),
        "qfi_proxy_passed_mean": float(jnp.mean(jnp.where(observed_success, qfi_query, 0.0)) / jnp.maximum(jnp.mean(observed_success), 1e-6)),
    }


def payload_query_like(query, n):
    return jnp.clip(query, 0, n - 1)


def run_config(seed, noise, hidden_dim, context_steps, operator, loss_name, args):
    key = jax.random.PRNGKey(seed)
    calibration_steps = args.time_steps // 2
    histories = gm.physics_priors_histories(
        key, args.time_steps, args.state_dim, args.latent_dim, args.true_lag, noise, "A10_full_global_causal_memory"
    )
    alice, bob, path_nulls = build_paths(histories, jax.random.fold_in(key, 20), calibration_steps)
    fit_query = jnp.arange(0, calibration_steps - 1)
    fit_match = select_path(alice, bob, fit_query)
    payload_query = jnp.arange(calibration_steps, args.time_steps - 1)
    rel_match = select_path(alice, bob, payload_query)
    control_matches = {name: select_path(alice, stream, payload_query) for name, stream in path_nulls.items()}

    delta_a = histories["z_a"][1:] - histories["z_a"][:-1]
    delta_b = histories["z_b"][1:] - histories["z_b"][:-1]
    delta_cross = histories["z_cross"][1:] - histories["z_cross"][:-1]
    aux_a = causal_aux(histories, "a")
    weight_signal = jnp.mean(jnp.abs(aux_a[fit_query]), axis=1)
    weights = jnp.ones_like(weight_signal)
    if loss_name == "event_weighted":
        weights = 1.0 + 1.5 * (weight_signal - jnp.min(weight_signal)) / jnp.maximum(jnp.max(weight_signal) - jnp.min(weight_signal), 1e-6)

    x_train = causal_windows(delta_a, fit_query, context_steps)
    aux_train = causal_windows(aux_a[:-1], fit_query, context_steps)
    y_train = delta_b[fit_match]
    params, diagnostics = train_model(
        jax.random.fold_in(key, 100), x_train, aux_train, y_train, weights, hidden_dim, operator, args.epochs, args.learning_rate
    )
    pred = predict_all(params, delta_a, aux_a, operator, context_steps)
    ridge_op, ridge_bias = pw.ridge_affine_map(delta_a[fit_query], delta_b[fit_match], ridge=1e-3)
    ridge_pred = delta_a @ ridge_op + ridge_bias

    target_map = {name: delta_b for name in CONTROL_NAMES} | {"cross_seed_path": delta_cross}
    rel_score, rel_rows = score(pred, payload_query, rel_match, delta_b)
    ridge_score, ridge_rows = score(ridge_pred, payload_query, rel_match, delta_b)
    control_rows = []
    control_scores = {}
    ridge_control_rows = []
    for name in CONTROL_NAMES:
        target = target_map[name]
        s, rows = score(pred, payload_query, control_matches[name], target)
        rs, rrows = score(ridge_pred, payload_query, control_matches[name], target)
        control_scores[name] = s
        control_rows.append(rows)
        ridge_control_rows.append(rrows)
    control_stack = jnp.stack(control_rows)
    ridge_control_stack = jnp.stack(ridge_control_rows)
    gains = rel_rows - jnp.max(control_stack, axis=0)
    ridge_gains = ridge_rows - jnp.max(ridge_control_stack, axis=0)
    ci = bootstrap_ci(jax.random.fold_in(key, 999), gains, args.bootstrap_samples)
    path_metrics = po.path_metrics(alice, bob, path_nulls, payload_query, gm.intrinsic_oracle_path(histories, payload_query))
    bound = clock_bound_metrics(alice, bob, path_nulls, payload_query, rel_match, control_matches, gains)
    ext_score = control_scores["same_stats_permuted_path"]
    high_event = jnp.abs(aux_a[payload_query, 0]) > jnp.median(jnp.abs(aux_a[payload_query, 0]))
    high_strain = jnp.abs(aux_a[payload_query, 3]) > jnp.median(jnp.abs(aux_a[payload_query, 3]))
    gain_ci_low, gain_ci_high = ci
    return {
        "config": {
            "seed": seed,
            "noise": noise,
            "hidden_dim": hidden_dim,
            "context_steps": context_steps,
            "operator": operator,
            "loss": loss_name,
        },
        "diagnostics": diagnostics,
        "metrics": {
            "dlinoss_relational_score": rel_score,
            "dlinoss_best_null_score": max(control_scores.values()),
            "dlinoss_relational_gain": rel_score - max(control_scores.values()),
            "dlinoss_relational_minus_external_gain": rel_score - ext_score,
            "ridge_score": ridge_score,
            "dlinoss_minus_ridge": rel_score - ridge_score,
            "fraction_windows_beating_best_null": float(jnp.mean(gains > 0.0)),
            "ridge_fraction_windows_beating_best_null": float(jnp.mean(ridge_gains > 0.0)),
            "ci95": list(ci),
            "event_window_gain": float(jnp.mean(gains[high_event])),
            "non_event_window_gain": float(jnp.mean(gains[~high_event])),
            "high_strain_window_gain": float(jnp.mean(gains[high_strain])),
            "low_strain_window_gain": float(jnp.mean(gains[~high_strain])),
            "path_margin_per_step": path_metrics["path_margin_per_step"],
            "path_rank": path_metrics["path_rank"],
            "segment_margin_w16": path_metrics["segment_margin_w16"],
            "ci_lower": gain_ci_low,
            "ci_upper": gain_ci_high,
            **bound,
        },
        "gates": {
            "path_observability_rank1": bool(path_metrics["path_rank"] == 1),
            "gain": bool(rel_score - max(control_scores.values()) > 0.10),
            "external": bool(rel_score - ext_score > 0.05),
            "ridge_gap": bool(rel_score - ridge_score >= -0.10),
            "window_fraction": bool(float(jnp.mean(gains > 0.0)) >= 0.70),
            "ci_lower": bool(gain_ci_low > 0.0),
        },
    }


def aggregate(results):
    grouped = {}
    for r in results:
        c = r["config"]
        key = f"h{c['hidden_dim']}_c{c['context_steps']}_{c['operator']}_{c['loss']}"
        grouped.setdefault(key, []).append(r)
    out = {}
    for key, rows in grouped.items():
        out[key] = {
            "median_gain": float(np.median([r["metrics"]["dlinoss_relational_gain"] for r in rows])),
            "median_relational_minus_external": float(np.median([r["metrics"]["dlinoss_relational_minus_external_gain"] for r in rows])),
            "median_minus_ridge": float(np.median([r["metrics"]["dlinoss_minus_ridge"] for r in rows])),
            "median_window_fraction": float(np.median([r["metrics"]["fraction_windows_beating_best_null"] for r in rows])),
            "median_bound": float(np.median([r["metrics"]["helstrom_success_bound_mean"] for r in rows])),
            "median_bound_normalized_window_score": float(np.median([r["metrics"]["bound_normalized_window_score"] for r in rows])),
            "median_failed_overlap": float(np.median([r["metrics"]["nearest_nontrue_overlap_failed_mean"] for r in rows])),
            "median_collision_rate_from_gram": float(np.median([r["metrics"]["collision_rate_from_gram"] for r in rows])),
            "median_qfi_failed": float(np.median([r["metrics"]["qfi_proxy_failed_mean"] for r in rows])),
            "median_qfi_passed": float(np.median([r["metrics"]["qfi_proxy_passed_mean"] for r in rows])),
            "median_event_gain": float(np.median([r["metrics"]["event_window_gain"] for r in rows])),
            "median_non_event_gain": float(np.median([r["metrics"]["non_event_window_gain"] for r in rows])),
            "gate_pass_rates": {
                gate: float(np.mean([r["gates"][gate] for r in rows]))
                for gate in rows[0]["gates"]
            },
        }
    return dict(sorted(out.items(), key=lambda kv: kv[1]["median_gain"], reverse=True))


def main():
    args = parse_args()
    backend = jax.default_backend()
    if args.require_tpu and backend != "tpu":
        raise RuntimeError(f"TPU required, got {backend}: {jax.devices()}")
    configs = [
        (seed, noise, hidden, context, operator, loss)
        for noise in args.noise_values
        for seed in args.seeds
        for hidden in args.hidden_dims
        for context in args.context_steps
        for operator in args.operators
        for loss in args.losses
    ]
    print(f"AQ-PAGE-WOOTTERS-DLINOSS-QUANTUM-CLOCK-BOUND-0 backend={backend} configs={len(configs)}", flush=True)
    results = []
    for index, (seed, noise, hidden, context, operator, loss) in enumerate(configs):
        print(f"[CONFIG {index+1}/{len(configs)}] seed={seed} noise={noise:.2f} hidden={hidden} context={context} operator={operator} loss={loss}", flush=True)
        result = run_config(seed, noise, hidden, context, operator, loss, args)
        results.append(result)
        m = result["metrics"]
        print(f"[RESULT] gain={m['dlinoss_relational_gain']:.6f} minus_ridge={m['dlinoss_minus_ridge']:.6f} windows={m['fraction_windows_beating_best_null']:.3f} bound={m['helstrom_success_bound_mean']:.3f} norm={m['bound_normalized_window_score']:.3f} ci_low={m['ci_lower']:.6f}", flush=True)
    payload = {
        "program": "AQ-PAGE-WOOTTERS-DLINOSS-QUANTUM-CLOCK-BOUND-0",
        "backend": backend,
        "config": vars(args) | {"out_dir": str(args.out_dir)},
        "aggregate": aggregate(results),
        "results": results,
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    output = args.out_dir / "quantum_clock_bound0_results.json"
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[DONE] results={output}", flush=True)


if __name__ == "__main__":
    main()
