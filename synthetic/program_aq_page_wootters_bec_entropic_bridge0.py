#!/usr/bin/env python3
"""AQ-PAGE-WOOTTERS-DLINOSS-BEC-ENTROPIC-BRIDGE-0 -- Gate 0.

Single-system entropic-clock observability test for a two-mode Josephson-
junction BEC model with a dark-sector diffusion bath, per
docs/AQ_PAGE_WOOTTERS_DLINOSS_BEC_ENTROPIC_BRIDGE_0_RUN_SPEC_2026-08-03.md.

Generator (bright/dark two-mode dimer):
    dz/dt   = -sqrt(1 - z^2) * sin(phi)
    dphi/dt = Lambda * z + (z / sqrt(1 - z^2)) * cos(phi)
    dphi   += sqrt(2 * D(t) * dt) * dW      (dark-sector phase diffusion)
    D(t)    = D0 * (1 + kappa * |sin(phi)|)
    dSigma/dt = 2 * D(t)                    (monotonic bright-sector reduced-state variance)
    S(t)    = 0.5 * log(2 * pi * e * Sigma(t))
    tau(t)  = S(t) - S(0)                   (entropic-time coordinate, latent)

Bright-sector observable (all a model is allowed to see): z(t), phi(t) only.
Sigma(t)/S(t)/tau(t) are latent regression targets, never inputs.

Gate 0 question: can a recurrent (memory-carrying) D-LinOSS-style integrator
reconstruct tau(t) from z(t), phi(t) alone, better than (a) a bounded-context
ridge baseline with no long-range memory, (b) the same recurrent model
trained on wall-clock step index instead of tau, and (c) shuffled/severed
controls that destroy true temporal order or cross seeds.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import jax
import jax.numpy as jnp
import numpy as np


CONFIGS = (
    {"name": "josephson_low_diff", "Lambda": 0.3, "D0": 0.02, "kappa": 1.0},
    {"name": "josephson_high_diff", "Lambda": 0.3, "D0": 0.08, "kappa": 1.0},
    {"name": "rabi_low_diff", "Lambda": 1.5, "D0": 0.02, "kappa": 1.0},
    {"name": "rabi_high_diff", "Lambda": 1.5, "D0": 0.08, "kappa": 2.0},
    {"name": "fock_selftrap", "Lambda": 3.0, "D0": 0.05, "kappa": 1.5},
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--time-steps", type=int, default=512)
    parser.add_argument("--dt", type=float, default=0.02)
    parser.add_argument("--seeds", nargs="*", type=int, default=[11, 12, 13, 14, 15])
    parser.add_argument("--hidden-dim", type=int, default=16)
    parser.add_argument("--context-steps", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=400)
    parser.add_argument("--learning-rate", type=float, default=5e-3)
    parser.add_argument("--out-dir", type=Path, default=Path("results_page_wootters_bec_entropic_bridge0"))
    args = parser.parse_args()
    return args


def simulate_world(key: jax.Array, world_steps: int, dt: float, Lambda: float, D0: float, kappa: float) -> dict:
    key_z0, key_phi0, key_noise = jax.random.split(key, 3)
    z0 = 0.05 * jax.random.normal(key_z0, ())
    phi0 = jax.random.uniform(key_phi0, (), minval=-0.1, maxval=0.1)
    noise = jax.random.normal(key_noise, (world_steps - 1,))

    def step(carry, w):
        z, phi, Sigma = carry
        zc = jnp.clip(z, -0.995, 0.995)
        dz = -jnp.sqrt(1.0 - zc**2) * jnp.sin(phi)
        dphi_det = Lambda * zc + (zc / jnp.sqrt(1.0 - zc**2)) * jnp.cos(phi)
        d_t = D0 * (1.0 + kappa * jnp.abs(jnp.sin(phi)))
        z_next = jnp.clip(z + dt * dz, -0.999, 0.999)
        phi_next = phi + dt * dphi_det + jnp.sqrt(jnp.maximum(2.0 * d_t * dt, 1e-12)) * w
        sigma_next = Sigma + 2.0 * d_t * dt
        return (z_next, phi_next, sigma_next), (z_next, phi_next, sigma_next, d_t)

    init = (z0, phi0, jnp.asarray(1.0))
    _, (zs, phis, sigmas, ds) = jax.lax.scan(step, init, noise)
    z_full = jnp.concatenate((z0[None], zs))
    phi_full = jnp.concatenate((phi0[None], phis))
    sigma_full = jnp.concatenate((jnp.asarray(1.0)[None], sigmas))
    d_full = jnp.concatenate((jnp.asarray(D0)[None], ds))
    s_full = 0.5 * jnp.log(2.0 * jnp.pi * jnp.e * sigma_full)
    tau_full = s_full - s_full[0]
    return {"z": z_full, "phi": phi_full, "Sigma": sigma_full, "S": s_full, "tau": tau_full, "D": d_full}


def local_variance(x: jax.Array, radius: int = 4) -> jax.Array:
    padded = jnp.pad(x, (radius, radius), mode="edge")
    windows = jnp.stack([padded[i : i + x.shape[0]] for i in range(2 * radius + 1)], axis=1)
    return jnp.var(windows, axis=1)


def build_observable_features(world: dict) -> jax.Array:
    z = world["z"]
    phi_unwrapped = jnp.unwrap(world["phi"])
    z_vel = jnp.concatenate((jnp.zeros((1,)), jnp.diff(z)))
    z_accel = jnp.concatenate((jnp.zeros((1,)), jnp.diff(z_vel)))
    phi_vel = jnp.concatenate((jnp.zeros((1,)), jnp.diff(phi_unwrapped)))
    z_local_var = local_variance(z, radius=4)
    return jnp.stack(
        (z, jnp.sin(world["phi"]), jnp.cos(world["phi"]), z_vel, z_accel, phi_vel, z_local_var),
        axis=1,
    )


def normalize_with_ref(matrix: jax.Array, ref: jax.Array) -> jax.Array:
    mean = jnp.mean(ref, axis=0, keepdims=True)
    std = jnp.maximum(jnp.std(ref, axis=0, keepdims=True), 1e-6)
    return (matrix - mean) / std


def r_squared(pred: jax.Array, true: jax.Array) -> float:
    residual = jnp.sum((pred - true) ** 2)
    total = jnp.sum((true - jnp.mean(true)) ** 2)
    return float(1.0 - residual / jnp.maximum(total, 1e-12))


# --- Recurrent (D-LinOSS-style) integrator: single continuous scan over the
# whole trajectory so the hidden state carries calibration-phase memory into
# the payload phase, unlike a bounded-context ridge baseline. ---

GAMMA_FLOOR = 0.01
WEIGHT_DECAY = 3e-3


def init_integrator_params(key: jax.Array, input_dim: int, hidden_dim: int) -> dict:
    keys = jax.random.split(key, 5)
    input_scale = 0.5 / jnp.sqrt(float(input_dim))
    hidden_scale = 0.5 / jnp.sqrt(float(hidden_dim))
    return {
        "raw_gamma": jnp.full((hidden_dim,), -2.0),
        "omega": 0.30 * jax.random.normal(keys[0], (hidden_dim,)),
        "B_re": input_scale * jax.random.normal(keys[1], (input_dim, hidden_dim)),
        "B_im": input_scale * jax.random.normal(keys[2], (input_dim, hidden_dim)),
        "C_re": hidden_scale * jax.random.normal(keys[3], (hidden_dim, 1)),
        "C_im": hidden_scale * jax.random.normal(keys[4], (hidden_dim, 1)),
        "bias": jnp.zeros((1,)),
    }


def integrator_forward(params: dict, x_seq: jax.Array) -> jax.Array:
    b_matrix = params["B_re"] + 1j * params["B_im"]
    c_matrix = params["C_re"] + 1j * params["C_im"]
    # gamma is floored away from zero so the recurrence is a bounded leaky
    # integrator (memory length ~= 1/gamma), not an unbounded pure
    # accumulator.
    gamma = GAMMA_FLOOR + 0.05 * jax.nn.softplus(params["raw_gamma"])
    lam = jnp.exp(-gamma + 1j * params["omega"])

    def step(h, x_t):
        h_next = h * lam + x_t.astype(jnp.complex64) @ b_matrix
        y = jnp.real(h_next @ c_matrix)[0] + params["bias"][0]
        return h_next, y

    h0 = jnp.zeros((params["omega"].shape[0],), dtype=jnp.complex64)
    _, outputs = jax.lax.scan(step, h0, x_seq)
    return outputs


def integrator_batch_forward(params: dict, x_batch: jax.Array) -> jax.Array:
    return jax.vmap(integrator_forward, in_axes=(None, 0))(params, x_batch)


def integrator_loss_batch(params, x_batch, target_batch):
    pred = integrator_batch_forward(params, x_batch)
    data_term = jnp.mean((pred - target_batch) ** 2)
    penalty = WEIGHT_DECAY * sum(
        jnp.mean(jnp.abs(value) ** 2)
        for key, value in params.items()
        if key in ("B_re", "B_im", "C_re", "C_im")
    )
    return data_term + penalty


def train_integrator(key, x_fit_batch, target_fit_batch, x_val, target_val, hidden_dim, epochs, learning_rate):
    """Adam training on a batch of *independent training-seed trajectories*
    (shared parameters, vmapped), early-stopped on one further held-out
    validation-seed trajectory. The generalization test this supports is
    "does the learned bright-sector -> entropic-time mapping transfer across
    independent noise realizations of the same physical law" -- not
    "can this specific trajectory's unseen future be forecast," which is a
    much harder and less relevant extrapolation task that a noiseless
    mean-field oscillator will fail trivially regardless of the model.
    """
    params = init_integrator_params(key, x_fit_batch.shape[-1], hidden_dim)
    m = jax.tree_util.tree_map(jnp.zeros_like, params)
    v = jax.tree_util.tree_map(jnp.zeros_like, params)

    @jax.jit
    def step(carry, iteration):
        current, first, second = carry
        loss, grads = jax.value_and_grad(integrator_loss_batch)(current, x_fit_batch, target_fit_batch)
        grads = jax.tree_util.tree_map(lambda g: jnp.clip(g, -1.0, 1.0), grads)
        first = jax.tree_util.tree_map(lambda a, g: 0.9 * a + 0.1 * g, first, grads)
        second = jax.tree_util.tree_map(lambda a, g: 0.999 * a + 0.001 * g * g, second, grads)
        t = iteration + 1
        mh = jax.tree_util.tree_map(lambda a: a / (1.0 - 0.9**t), first)
        vh = jax.tree_util.tree_map(lambda a: a / (1.0 - 0.999**t), second)
        current = jax.tree_util.tree_map(
            lambda p, a, b: p - learning_rate * a / (jnp.sqrt(b) + 1e-8), current, mh, vh
        )
        val_pred = integrator_forward(current, x_val)
        val_loss = jnp.mean((val_pred - target_val) ** 2)
        return (current, first, second), (loss, val_loss, current)

    (_, _, _), (fit_losses, val_losses, param_history) = jax.lax.scan(
        step, (params, m, v), jnp.arange(epochs)
    )
    best_epoch = int(jnp.argmin(val_losses))
    best_params = jax.tree_util.tree_map(lambda history: history[best_epoch], param_history)
    return best_params, {
        "initial_loss": float(fit_losses[0]),
        "final_loss": float(fit_losses[-1]),
        "best_epoch": best_epoch,
        "best_val_loss": float(val_losses[best_epoch]),
        "final_val_loss": float(val_losses[-1]),
    }


# --- Bounded-context ridge baseline: only sees a short local window, no
# access to accumulated history before that window. ---

def causal_windows(sequence: np.ndarray, context_steps: int) -> np.ndarray:
    padded = np.pad(sequence, ((context_steps - 1, 0), (0, 0)), mode="edge")
    return np.concatenate([padded[i : i + sequence.shape[0]] for i in range(context_steps)], axis=1)


def fit_ridge(x: np.ndarray, y: np.ndarray, reg: float = 1e-2) -> tuple[np.ndarray, float]:
    x_aug = np.concatenate((x, np.ones((x.shape[0], 1))), axis=1)
    a = x_aug.T @ x_aug + reg * np.eye(x_aug.shape[1])
    b = x_aug.T @ y
    w_aug = np.linalg.solve(a, b)
    return w_aug[:-1], float(w_aug[-1])


def predict_ridge(x: np.ndarray, w: np.ndarray, b: float) -> np.ndarray:
    return x @ w + b


def simulate_and_featurize(seed: int, world_steps: int, dt: float, config: dict) -> dict:
    key = jax.random.PRNGKey(seed)
    world = simulate_world(key, world_steps, dt, config["Lambda"], config["D0"], config["kappa"])
    obs_raw = build_observable_features(world)
    step_index = jnp.arange(world_steps, dtype=jnp.float32)
    return {"world": world, "obs_raw": obs_raw, "tau": world["tau"], "step_index": step_index}


def run_leave_one_out(
    config: dict,
    eval_seed: int,
    other_seeds: list[int],
    cross_config: dict,
    args: argparse.Namespace,
) -> dict:
    """Leave-one-out cross-seed test: train on 3 fit seeds + 1 validation
    seed (for early stopping only), evaluate on a genuinely held-out 5th
    seed. This is the correct generalization test for "does the mapping from
    bright-sector observables to entropic time hold as a general law," as
    opposed to forecasting one trajectory's unseen future, which even a
    perfect model would fail on a near-deterministic oscillator.
    """
    fit_seeds, val_seed = other_seeds[:3], other_seeds[3]
    world_steps = args.time_steps

    fit_data = [simulate_and_featurize(s, world_steps, args.dt, config) for s in fit_seeds]
    val_data = simulate_and_featurize(val_seed, world_steps, args.dt, config)
    eval_data = simulate_and_featurize(eval_seed, world_steps, args.dt, config)

    fit_obs_ref = jnp.concatenate([d["obs_raw"] for d in fit_data], axis=0)
    fit_tau_ref = jnp.concatenate([d["tau"] for d in fit_data], axis=0)
    fit_step_ref = jnp.concatenate([d["step_index"] for d in fit_data], axis=0)
    obs_mean = jnp.mean(fit_obs_ref, axis=0, keepdims=True)
    obs_std = jnp.maximum(jnp.std(fit_obs_ref, axis=0, keepdims=True), 1e-6)
    tau_mean, tau_std = jnp.mean(fit_tau_ref), jnp.maximum(jnp.std(fit_tau_ref), 1e-6)
    step_mean, step_std = jnp.mean(fit_step_ref), jnp.maximum(jnp.std(fit_step_ref), 1e-6)

    def normalize(d):
        return {
            "obs": (d["obs_raw"] - obs_mean) / obs_std,
            "tau": (d["tau"] - tau_mean) / tau_std,
            "step": (d["step_index"] - step_mean) / step_std,
        }

    fit_norm = [normalize(d) for d in fit_data]
    val_norm = normalize(val_data)
    eval_norm = normalize(eval_data)

    obs_fit_batch = jnp.stack([d["obs"] for d in fit_norm], axis=0)
    tau_fit_batch = jnp.stack([d["tau"] for d in fit_norm], axis=0)
    step_fit_batch = jnp.stack([d["step"] for d in fit_norm], axis=0)

    key = jax.random.PRNGKey(eval_seed * 1000 + hash(config["name"]) % 997)

    params_tau, diag_tau = train_integrator(
        key, obs_fit_batch, tau_fit_batch, val_norm["obs"], val_norm["tau"],
        args.hidden_dim, args.epochs, args.learning_rate,
    )
    pred_tau_eval = integrator_forward(params_tau, eval_norm["obs"])
    r2_tau_eval = r_squared(pred_tau_eval, eval_norm["tau"])

    params_wall, diag_wall = train_integrator(
        jax.random.fold_in(key, 5), obs_fit_batch, step_fit_batch, val_norm["obs"], val_norm["step"],
        args.hidden_dim, args.epochs, args.learning_rate,
    )
    pred_wall_eval = integrator_forward(params_wall, eval_norm["obs"])
    r2_wall_eval = r_squared(pred_wall_eval, eval_norm["step"])

    # Shuffled control: the frozen tau model sees the eval trajectory's own
    # observables with time order destroyed.
    shuffle_key = jax.random.fold_in(key, 900)
    shuffle_perm = jax.random.permutation(shuffle_key, world_steps)
    pred_shuffled = integrator_forward(params_tau, eval_norm["obs"][shuffle_perm])
    r2_shuffled_eval = r_squared(pred_shuffled, eval_norm["tau"])

    # Cross-regime control: the frozen tau model (trained on this config's
    # physical regime) is applied to a trajectory from a *different*
    # (Lambda, D0, kappa) regime, evaluated against that trajectory's own
    # tau. Tests whether the learned mapping is a general entropy-production
    # law or specific to this regime's dynamics.
    cross_data = simulate_and_featurize(eval_seed, world_steps, args.dt, cross_config)
    cross_obs = (cross_data["obs_raw"] - obs_mean) / obs_std
    cross_tau = (cross_data["tau"] - tau_mean) / tau_std
    pred_cross = integrator_forward(params_tau, cross_obs)
    r2_cross_regime_eval = r_squared(pred_cross, cross_tau)

    # Bounded-context ridge baseline: pooled fit-seed windows only, no
    # cross-trajectory recurrent memory.
    fit_windowed = np.concatenate(
        [causal_windows(np.asarray(d["obs"]), args.context_steps) for d in fit_norm], axis=0
    )
    fit_tau_np = np.concatenate([np.asarray(d["tau"]) for d in fit_norm], axis=0)
    w_ridge, b_ridge = fit_ridge(fit_windowed, fit_tau_np)
    eval_windowed = causal_windows(np.asarray(eval_norm["obs"]), args.context_steps)
    ridge_pred = predict_ridge(eval_windowed, w_ridge, b_ridge)
    r2_ridge_eval = r_squared(jnp.asarray(ridge_pred), eval_norm["tau"])

    gain_over_wallclock = r2_tau_eval - r2_wall_eval
    return {
        "config": config["name"],
        "eval_seed": eval_seed,
        "fit_seeds": fit_seeds,
        "val_seed": val_seed,
        "diagnostics": {"tau_final_loss": diag_tau["final_loss"], "wall_final_loss": diag_wall["final_loss"]},
        "metrics": {
            "r2_tau_eval": r2_tau_eval,
            "r2_wallclock_eval": r2_wall_eval,
            "gain_over_wallclock": gain_over_wallclock,
            "r2_shuffled_eval": r2_shuffled_eval,
            "r2_cross_regime_eval": r2_cross_regime_eval,
            "r2_ridge_context_eval": r2_ridge_eval,
        },
        "gates": {
            "r2_tau_above_070": bool(r2_tau_eval > 0.70),
            "beats_wallclock_010": bool(gain_over_wallclock >= 0.10),
            "shuffled_fails_020": bool(r2_shuffled_eval < 0.20),
            "cross_regime_fails_020": bool(r2_cross_regime_eval < 0.20),
        },
    }


def main() -> None:
    args = parse_args()
    backend = jax.default_backend()
    print(f"AQ-PAGE-WOOTTERS-DLINOSS-BEC-ENTROPIC-BRIDGE-0 Gate 0 backend={backend}", flush=True)
    if len(args.seeds) < 5:
        raise ValueError("--seeds needs at least 5 entries (3 fit + 1 val + 1 held-out eval)")

    results = []
    for idx, config in enumerate(CONFIGS):
        cross_config = CONFIGS[(idx + 1) % len(CONFIGS)]
        for eval_seed in args.seeds:
            other_seeds = [s for s in args.seeds if s != eval_seed]
            result = run_leave_one_out(config, eval_seed, other_seeds, cross_config, args)
            results.append(result)
            m = result["metrics"]
            g = result["gates"]
            print(
                f"[RESULT] {config['name']} eval_seed={eval_seed} r2_tau={m['r2_tau_eval']:.3f} "
                f"r2_wall={m['r2_wallclock_eval']:.3f} gain={m['gain_over_wallclock']:.3f} "
                f"r2_shuffled={m['r2_shuffled_eval']:.3f} r2_cross_regime={m['r2_cross_regime_eval']:.3f} "
                f"r2_ridge_ctx={m['r2_ridge_context_eval']:.3f} gates={g}",
                flush=True,
            )

    aggregate = {}
    for config in CONFIGS:
        rows = [r for r in results if r["config"] == config["name"]]
        aggregate[config["name"]] = {
            "median_r2_tau": float(np.median([r["metrics"]["r2_tau_eval"] for r in rows])),
            "median_r2_wallclock": float(np.median([r["metrics"]["r2_wallclock_eval"] for r in rows])),
            "median_gain_over_wallclock": float(np.median([r["metrics"]["gain_over_wallclock"] for r in rows])),
            "median_r2_shuffled": float(np.median([r["metrics"]["r2_shuffled_eval"] for r in rows])),
            "median_r2_cross_regime": float(np.median([r["metrics"]["r2_cross_regime_eval"] for r in rows])),
            "median_r2_ridge_context": float(np.median([r["metrics"]["r2_ridge_context_eval"] for r in rows])),
            "gate_pass_rate": {
                gate: float(np.mean([r["gates"][gate] for r in rows])) for gate in rows[0]["gates"]
            },
            "config_passes_gate0": bool(all(np.mean([r["gates"][gate] for r in rows]) >= 0.6 for gate in rows[0]["gates"])),
        }

    configs_passing = sum(1 for v in aggregate.values() if v["config_passes_gate0"])
    print(f"\n[GATE 0 SUMMARY] configs_passing={configs_passing}/{len(CONFIGS)}", flush=True)
    for name, agg in aggregate.items():
        print(f"  {name}: passes={agg['config_passes_gate0']} r2_tau={agg['median_r2_tau']:.3f} "
              f"gain_wallclock={agg['median_gain_over_wallclock']:.3f} "
              f"r2_shuffled={agg['median_r2_shuffled']:.3f} r2_cross_regime={agg['median_r2_cross_regime']:.3f} "
              f"r2_ridge_ctx={agg['median_r2_ridge_context']:.3f}", flush=True)

    payload = {
        "program": "AQ-PAGE-WOOTTERS-DLINOSS-BEC-ENTROPIC-BRIDGE-0-GATE0",
        "backend": backend,
        "config": {k: (v if not isinstance(v, Path) else str(v)) for k, v in vars(args).items()} | {"configs": CONFIGS},
        "aggregate": aggregate,
        "configs_passing": configs_passing,
        "gate0_overall_pass": bool(configs_passing >= 3),
        "results": results,
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    output = args.out_dir / "bec_entropic_bridge0_gate0_results.json"
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[DONE] gate0_overall_pass={payload['gate0_overall_pass']} results={output}", flush=True)


if __name__ == "__main__":
    main()
