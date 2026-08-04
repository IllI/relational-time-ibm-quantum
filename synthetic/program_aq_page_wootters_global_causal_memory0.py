#!/usr/bin/env python3
"""AQ-PAGE-WOOTTERS-DLINOSS-GLOBAL-CAUSAL-MEMORY-0.

Observability-first gate that adds a causally generated global memory/action
coordinate to the physics-priors generator. The target failure mode is
same-distribution exchangeability: shuffled/severed windows occasionally beat
the true correspondence even when wrong-lag and anti-cheat controls are clean.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import jax
import jax.numpy as jnp
import numpy as np

import program_aq_page_wootters0 as pw


GENERATOR_ARMS = (
    "A6_full_causal_clock_current",
    "A7_residual_integral",
    "A8_event_count_hash",
    "A9_entropy_action_integral",
    "A10_full_global_causal_memory",
)

FEATURE_SPECS = (
    {"name": "point_clock_baseline", "kind": "clock", "radius": 0, "contrastive": False},
    {"name": "patch_clock_w3", "kind": "clock", "radius": 1, "contrastive": False},
    {"name": "patch_clock_w5", "kind": "clock", "radius": 2, "contrastive": False},
    {"name": "patch_clock_w9", "kind": "clock", "radius": 4, "contrastive": False},
    {"name": "state_patch_w5", "kind": "state", "radius": 2, "contrastive": False},
    {"name": "transition_signature_w5", "kind": "transition", "radius": 2, "contrastive": False},
    {"name": "contrastive_patch_encoder", "kind": "rich", "radius": 2, "contrastive": True},
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--time-steps", type=int, default=128)
    parser.add_argument("--state-dim", type=int, default=64)
    parser.add_argument("--latent-dim", type=int, default=8)
    parser.add_argument("--true-lag", type=int, default=5)
    parser.add_argument("--seeds", nargs="*", type=int, default=[11, 12, 13, 14, 15])
    parser.add_argument("--noise-values", nargs="*", type=float, default=[0.0, 0.01, 0.02, 0.03])
    parser.add_argument("--generator-arms", nargs="*", default=list(GENERATOR_ARMS))
    parser.add_argument("--out-dir", type=Path, default=Path("aq_page_wootters_physics_priors_observability0"))
    parser.add_argument("--require-tpu", action="store_true")
    args = parser.parse_args()
    if args.time_steps < 32 or args.time_steps % 2:
        parser.error("--time-steps must be an even integer >= 32")
    if args.latent_dim < 4 or args.latent_dim % 2:
        parser.error("--latent-dim must be an even integer >= 4")
    if args.state_dim < args.latent_dim:
        parser.error("--state-dim must be >= --latent-dim")
    if args.true_lag < 1 or args.true_lag >= args.time_steps // 4:
        parser.error("--true-lag must be >= 1 and comfortably below the half-split")
    unknown = sorted(set(args.generator_arms) - set(GENERATOR_ARMS))
    if unknown:
        parser.error(f"unknown --generator-arms values: {unknown}")
    return args


def derivatives(features: jax.Array) -> tuple[jax.Array, jax.Array]:
    velocity = jnp.gradient(features, axis=0)
    acceleration = jnp.gradient(velocity, axis=0)
    return velocity, acceleration


def history_embed(features: jax.Array, radius: int) -> jax.Array:
    if radius <= 0:
        return features
    padded = jnp.pad(features, ((radius, radius), (0, 0)), mode="edge")
    windows = [
        padded[offset : offset + features.shape[0]]
        for offset in range(0, 2 * radius + 1)
    ]
    return jnp.concatenate(windows, axis=1)


def complex_to_real(z_complex: jax.Array) -> jax.Array:
    return jnp.stack((jnp.real(z_complex), jnp.imag(z_complex)), axis=-1).reshape(
        z_complex.shape[0], z_complex.shape[1] * 2
    )


def normalize_track(track: jax.Array, calibration_steps: int) -> jax.Array:
    center = jnp.median(track[:calibration_steps])
    mad = jnp.median(jnp.abs(track[:calibration_steps] - center))
    scale = jnp.maximum(1.4826 * mad, 1e-6)
    return (track - center) / scale


def local_entropy_proxy(z_real: jax.Array, radius: int = 2) -> jax.Array:
    """Log-det local covariance proxy used consistently by clock and diagnostics."""
    eye = jnp.eye(z_real.shape[1], dtype=z_real.dtype)
    values = []
    for index in range(z_real.shape[0]):
        start = max(0, index - radius)
        stop = min(z_real.shape[0], index + radius + 1)
        window = z_real[start:stop]
        centered = window - jnp.mean(window, axis=0, keepdims=True)
        cov = (centered.T @ centered) / jnp.maximum(window.shape[0] - 1, 1)
        sign, logdet = jnp.linalg.slogdet(cov + 1e-3 * eye)
        values.append(jnp.where(sign > 0, logdet, 0.0))
    return jnp.asarray(values)


def causal_observables(
    z_real: jax.Array,
    nominal_real: jax.Array,
    event_activity: jax.Array,
    residual_vec: jax.Array,
) -> dict[str, jax.Array]:
    entropy_proxy = local_entropy_proxy(z_real)
    entropy_rate = jnp.concatenate(
        (jnp.zeros((1,), dtype=z_real.dtype), jnp.abs(jnp.diff(entropy_proxy)))
    )
    strain = pw.curvature(z_real)
    step_residual = jnp.linalg.norm(z_real[1:] - nominal_real, axis=1) ** 2
    transition_residual_energy = jnp.concatenate(
        (step_residual[:1], step_residual), axis=0
    )
    residual_memory = jnp.linalg.norm(residual_vec, axis=1)
    return {
        "entropy_proxy": entropy_proxy,
        "entropy_rate": entropy_rate,
        "event_activity": event_activity,
        "residual_memory": residual_memory,
        "transition_residual_energy": transition_residual_energy,
        "strain": strain,
    }


def generate_causal_world(
    key: jax.Array,
    world_steps: int,
    pair_count: int,
    noise: float,
    generator_arm: str,
) -> dict[str, jax.Array]:
    include_drift = True
    include_events = True
    include_residual = True
    include_entropy_clock = True
    include_damping_observables = True
    full_clock = True
    use_global_memory = generator_arm != "A6_full_causal_clock_current"
    use_residual_memory = generator_arm in (
        "A7_residual_integral",
        "A10_full_global_causal_memory",
    )
    use_event_memory = generator_arm in (
        "A8_event_count_hash",
        "A10_full_global_causal_memory",
    )
    use_entropy_memory = generator_arm in (
        "A9_entropy_action_integral",
        "A10_full_global_causal_memory",
    )
    use_damping_action = generator_arm == "A10_full_global_causal_memory"
    (
        key_init_phase,
        key_omega_rw,
        key_event_mask,
        key_event_phase,
        key_event_scale,
        key_bath_phase,
        key_bath_noise,
        key_entropy_drive,
    ) = jax.random.split(key, 8)

    base_omega = jnp.linspace(0.08, 0.31, pair_count)
    init_phase = jax.random.uniform(key_init_phase, (pair_count,), minval=-jnp.pi, maxval=jnp.pi)
    z0 = jnp.exp(1j * init_phase)

    omega_rw = 0.004 * jnp.cumsum(
        jax.random.normal(key_omega_rw, (world_steps - 1, pair_count)), axis=0
    )
    omega_rw = jnp.where(include_drift, omega_rw, jnp.zeros_like(omega_rw))
    event_mask = jax.random.bernoulli(key_event_mask, p=0.085, shape=(world_steps - 1, pair_count))
    event_scale = event_mask * (0.12 + 0.18 * jax.nn.softplus(jax.random.normal(key_event_scale, (world_steps - 1, pair_count))))
    event_phase = jax.random.uniform(key_event_phase, (world_steps - 1, pair_count), minval=-jnp.pi, maxval=jnp.pi)
    event_drive = event_scale * jnp.exp(1j * event_phase)
    event_drive = jnp.where(include_events, event_drive, jnp.zeros_like(event_drive))
    bath_phase = jax.random.uniform(key_bath_phase, (world_steps - 1, pair_count), minval=-jnp.pi, maxval=jnp.pi)
    bath_dir = jnp.exp(1j * bath_phase)
    bath_noise = noise * 0.05 * (
        jax.random.normal(key_bath_noise, (world_steps - 1, pair_count))
        + 1j * jax.random.normal(jax.random.fold_in(key_bath_noise, 1), (world_steps - 1, pair_count))
    )
    entropy_drive = 0.04 * jax.random.normal(key_entropy_drive, (world_steps - 1,))

    def step(carry, inputs):
        z_prev, residual_prev, entropy_cum_prev, event_cum_prev, memory_prev, action_prev = carry
        omega_delta_t, event_drive_t, bath_dir_t, bath_noise_t, entropy_drive_t = inputs
        event_activity = jnp.mean(jnp.abs(event_drive_t))
        residual_activity = jnp.mean(jnp.abs(residual_prev))
        drift_energy = jnp.mean(jnp.abs(omega_delta_t))
        entropy_rate_raw = jax.nn.softplus(
            0.035
            + 0.70 * event_activity
            + 0.28 * residual_activity
            + 0.18 * drift_energy
            + entropy_drive_t
        )
        gamma_observable = (
            0.010
            + 0.060 * entropy_rate_raw
            + 0.045 * residual_activity
            + 0.160 * event_activity
        )
        memory_drive = jnp.zeros_like(residual_prev)
        memory_drive = memory_drive + jnp.where(use_residual_memory, 0.55 * residual_prev, 0.0)
        memory_drive = memory_drive + jnp.where(use_event_memory, 1.30 * jnp.abs(event_drive_t), 0.0)
        memory_drive = memory_drive + jnp.where(use_entropy_memory, 0.45 * entropy_rate_raw, 0.0)
        memory_next = jnp.where(
            use_global_memory,
            0.985 * memory_prev + memory_drive,
            jnp.zeros_like(memory_prev),
        )
        action_increment = jnp.where(
            use_global_memory,
            0.022 * jax.nn.softplus(jnp.mean(memory_next)),
            jnp.array(0.0, dtype=jnp.float32),
        )
        action_next = action_prev + action_increment
        gamma_t = jnp.where(include_damping_observables, gamma_observable, 0.018)
        gamma_t = gamma_t + jnp.where(use_damping_action, 0.035 * action_increment, 0.0)
        omega_t = base_omega + omega_delta_t + 0.020 * residual_activity + 0.006 * event_cum_prev
        omega_t = omega_t + jnp.where(use_global_memory, 0.004 * action_next, 0.0)
        lam = jnp.exp((-gamma_t + 1j * omega_t))
        bath_memory = jnp.where(
            include_residual,
            0.030 * residual_prev * bath_dir_t,
            jnp.zeros_like(event_drive_t),
        )
        z_next = lam * z_prev + 0.22 * event_drive_t + bath_memory + bath_noise_t
        nominal = jnp.exp(1j * base_omega) * z_prev
        transition_residual = jnp.mean(jnp.abs(z_next - nominal))
        strain = jnp.mean(jnp.abs(jnp.abs(z_next) - jnp.abs(z_prev)))
        residual_drive = jnp.abs(event_drive_t) + transition_residual + 0.08 * entropy_rate_raw
        residual_next = jnp.where(
            include_residual,
            0.91 * residual_prev + residual_drive,
            jnp.zeros_like(residual_prev),
        )
        entropy_cum_next = entropy_cum_prev + entropy_rate_raw
        event_cum_next = event_cum_prev + event_activity
        output = {
            "z": z_next,
            "nominal": nominal,
            "residual_vec": residual_next,
            "causal_memory": memory_next,
            "causal_action_increment": action_increment,
            "causal_action": action_next,
            "entropy_rate_raw": entropy_rate_raw,
            "event_activity": event_activity,
            "transition_residual_energy": transition_residual,
            "strain": strain,
            "gamma_mean": jnp.mean(gamma_t),
            "omega_mean": jnp.mean(omega_t),
            "entropy_cumulative": entropy_cum_next,
            "event_cumulative": event_cum_next,
        }
        return (z_next, residual_next, entropy_cum_next, event_cum_next, memory_next, action_next), output

    scan_inputs = (omega_rw, event_drive, bath_dir, bath_noise, entropy_drive)
    (_, _, _, _, _, _), outputs = jax.lax.scan(
        step,
        (
            z0,
            jnp.zeros((pair_count,), dtype=jnp.float32),
            jnp.array(0.0, dtype=jnp.float32),
            jnp.array(0.0, dtype=jnp.float32),
            jnp.zeros((pair_count,), dtype=jnp.float32),
            jnp.array(0.0, dtype=jnp.float32),
        ),
        scan_inputs,
    )

    def prepend_initial(series: jax.Array, initial: float | jax.Array) -> jax.Array:
        initial_value = jnp.asarray(initial, dtype=series.dtype)
        initial_value = jnp.broadcast_to(initial_value, series.shape[1:]) if series.ndim > 1 else initial_value
        return jnp.concatenate((initial_value[None, ...], series), axis=0)

    z_complex = prepend_initial(outputs["z"], z0)
    nominal_complex = outputs["nominal"]
    residual_vec = prepend_initial(outputs["residual_vec"], jnp.zeros((pair_count,), dtype=jnp.float32))
    causal_memory = prepend_initial(outputs["causal_memory"], jnp.zeros((pair_count,), dtype=jnp.float32))
    causal_action_increment = prepend_initial(outputs["causal_action_increment"], 0.0)
    causal_action = prepend_initial(outputs["causal_action"], 0.0)
    entropy_rate_raw = prepend_initial(outputs["entropy_rate_raw"], 0.0)
    event_activity = prepend_initial(outputs["event_activity"], 0.0)
    gamma_mean = prepend_initial(outputs["gamma_mean"], 0.0)
    omega_mean = prepend_initial(outputs["omega_mean"], float(jnp.mean(base_omega)))
    entropy_cumulative = prepend_initial(outputs["entropy_cumulative"], 0.0)
    event_cumulative = prepend_initial(outputs["event_cumulative"], 0.0)

    z_real = complex_to_real(z_complex)
    nominal_real = complex_to_real(nominal_complex)
    observables = causal_observables(z_real, nominal_real, event_activity, residual_vec)
    entropy_rate = jnp.where(
        include_entropy_clock, observables["entropy_rate"], entropy_rate_raw
    )
    residual_memory = observables["residual_memory"]
    transition_residual_energy = observables["transition_residual_energy"]
    strain = observables["strain"]
    curvature = strain
    entropy_cumulative = jnp.cumsum(entropy_rate)
    tau = (
        0.33 * jnp.arange(world_steps, dtype=jnp.float32)
        + 0.12 * jnp.cumsum(curvature)
        + jnp.where(include_entropy_clock, 0.20 * entropy_cumulative, 0.0)
        + jnp.where(include_events, 0.26 * event_cumulative, 0.0)
        + jnp.where(full_clock, 0.14 * residual_memory, 0.0)
        + jnp.where(use_global_memory, 0.31 * causal_action, 0.0)
    )
    return {
        "z_complex": z_complex,
        "z_real": z_real,
        "entropy_proxy": observables["entropy_proxy"],
        "entropy_rate": entropy_rate,
        "event_activity": event_activity,
        "residual_memory": residual_memory,
        "causal_memory_norm": jnp.linalg.norm(causal_memory, axis=1),
        "causal_action": causal_action,
        "causal_action_increment": causal_action_increment,
        "transition_residual_energy": transition_residual_energy,
        "strain": strain,
        "gamma_mean": gamma_mean,
        "omega_mean": omega_mean,
        "curvature": curvature,
        "tau": tau,
        "intrinsic": tau,
    }


def build_point_clock(
    tau: jax.Array,
    entropy_rate: jax.Array,
    residual_memory: jax.Array,
    event_activity: jax.Array,
    strain: jax.Array,
    causal_action: jax.Array,
    calibration_steps: int,
) -> jax.Array:
    q_entropy = normalize_track(entropy_rate, calibration_steps)
    q_residual = normalize_track(residual_memory, calibration_steps)
    q_event = normalize_track(event_activity, calibration_steps)
    q_strain = normalize_track(strain, calibration_steps)
    q_action = normalize_track(causal_action, calibration_steps)
    return jnp.stack(
        (
            jnp.sin(tau),
            jnp.cos(tau),
            q_entropy,
            q_residual,
            q_event,
            q_strain,
            q_action,
        ),
        axis=1,
    )


def slice_world(world: dict[str, jax.Array], start: int, stop: int) -> dict[str, jax.Array]:
    return {name: value[start:stop] for name, value in world.items()}


def physics_priors_histories(
    key: jax.Array,
    time_steps: int,
    state_dim: int,
    latent_dim: int,
    true_lag: int,
    noise: float,
    generator_arm: str,
) -> dict[str, jax.Array]:
    key_basis, key_world, key_cross, key_obs, key_stats_perm = jax.random.split(key, 5)
    pair_count = latent_dim // 2
    world_steps = time_steps + true_lag
    basis_raw = jax.random.normal(key_basis, (state_dim, latent_dim))
    basis, _ = jnp.linalg.qr(basis_raw, mode="reduced")

    world = generate_causal_world(key_world, world_steps, pair_count, noise, generator_arm)
    cross_world = generate_causal_world(key_cross, world_steps, pair_count, noise, generator_arm)

    obs_phase = jax.random.uniform(key_obs, (pair_count,), minval=-0.18, maxval=0.18)
    obs_scale = jnp.exp(0.06 * jax.random.normal(jax.random.fold_in(key_obs, 1), (pair_count,)))
    observer = obs_scale * jnp.exp(1j * obs_phase)

    alice_world = slice_world(world, 0, time_steps)
    bob_world = slice_world(world, true_lag, true_lag + time_steps)
    cross_slice = slice_world(cross_world, true_lag, true_lag + time_steps)

    z_a_complex = alice_world["z_complex"]
    z_b_complex = bob_world["z_complex"] * observer[None, :]
    z_cross_complex = cross_slice["z_complex"]

    z_a = complex_to_real(z_a_complex)
    z_b = complex_to_real(z_b_complex)
    z_cross = complex_to_real(z_cross_complex)

    x_a = z_a @ basis.T
    x_b = z_b @ basis.T
    x_cross = z_cross @ basis.T

    point_clock_a = build_point_clock(
        alice_world["tau"],
        alice_world["entropy_rate"],
        alice_world["residual_memory"],
        alice_world["event_activity"],
        alice_world["strain"],
        alice_world["causal_action"],
        time_steps // 2,
    )
    point_clock_b = build_point_clock(
        bob_world["tau"],
        bob_world["entropy_rate"],
        bob_world["residual_memory"],
        bob_world["event_activity"],
        bob_world["strain"],
        bob_world["causal_action"],
        time_steps // 2,
    )
    point_clock_cross = build_point_clock(
        cross_slice["tau"],
        cross_slice["entropy_rate"],
        cross_slice["residual_memory"],
        cross_slice["event_activity"],
        cross_slice["strain"],
        cross_slice["causal_action"],
        time_steps // 2,
    )
    stats_perm = jax.random.permutation(key_stats_perm, time_steps)
    point_clock_statsperm = build_point_clock(
        bob_world["tau"],
        bob_world["entropy_rate"][stats_perm],
        bob_world["residual_memory"][stats_perm],
        bob_world["event_activity"][stats_perm],
        bob_world["strain"][stats_perm],
        bob_world["causal_action"][stats_perm],
        time_steps // 2,
    )

    return {
        "generator_arm": generator_arm,
        "basis": basis,
        "x_a": x_a,
        "x_b": x_b,
        "x_cross": x_cross,
        "z_a": z_a,
        "z_b": z_b,
        "z_cross": z_cross,
        "z_statsperm": z_b,
        "clock_a": point_clock_a,
        "clock_b": point_clock_b,
        "clock_cross": point_clock_cross,
        "clock_statsperm": point_clock_statsperm,
        "entropy_rate_a": alice_world["entropy_rate"],
        "entropy_rate_b": bob_world["entropy_rate"],
        "entropy_rate_cross": cross_slice["entropy_rate"],
        "entropy_rate_statsperm": bob_world["entropy_rate"][stats_perm],
        "event_activity_a": alice_world["event_activity"],
        "event_activity_b": bob_world["event_activity"],
        "event_activity_cross": cross_slice["event_activity"],
        "event_activity_statsperm": bob_world["event_activity"][stats_perm],
        "residual_memory_a": alice_world["residual_memory"],
        "residual_memory_b": bob_world["residual_memory"],
        "residual_memory_cross": cross_slice["residual_memory"],
        "residual_memory_statsperm": bob_world["residual_memory"][stats_perm],
        "causal_action_a": alice_world["causal_action"],
        "causal_action_b": bob_world["causal_action"],
        "causal_action_cross": cross_slice["causal_action"],
        "causal_action_statsperm": bob_world["causal_action"][stats_perm],
        "transition_residual_a": alice_world["transition_residual_energy"],
        "transition_residual_b": bob_world["transition_residual_energy"],
        "transition_residual_cross": cross_slice["transition_residual_energy"],
        "transition_residual_statsperm": bob_world["transition_residual_energy"][stats_perm],
        "strain_a": alice_world["strain"],
        "strain_b": bob_world["strain"],
        "strain_cross": cross_slice["strain"],
        "strain_statsperm": bob_world["strain"][stats_perm],
        "intrinsic_a": alice_world["intrinsic"],
        "intrinsic_b": bob_world["intrinsic"],
        "intrinsic_cross": cross_slice["intrinsic"],
        "true_lag": true_lag,
    }


def intrinsic_oracle_path(histories: dict[str, jax.Array], query_indices: jax.Array) -> jax.Array:
    intrinsic_a = np.asarray(histories["intrinsic_a"])
    intrinsic_b = np.asarray(histories["intrinsic_b"])
    midpoint_a = 0.5 * (intrinsic_a[:-1] + intrinsic_a[1:])
    midpoint_b = 0.5 * (intrinsic_b[:-1] + intrinsic_b[1:])
    query = np.asarray(query_indices, dtype=np.int32)
    matches = []
    previous = -1
    for row, index in enumerate(query):
        remaining = len(query) - row - 1
        start = previous + 1
        stop = len(midpoint_b) - remaining
        candidates = np.arange(start, stop, dtype=np.int32)
        selected = candidates[np.argmin(np.abs(midpoint_b[candidates] - midpoint_a[index]))]
        matches.append(int(selected))
        previous = int(selected)
    return jnp.asarray(matches, dtype=jnp.int32)


def one_step_residual(z: jax.Array, calibration_steps: int) -> jax.Array:
    source = z[: calibration_steps - 1]
    target = z[1:calibration_steps]
    matrix, bias = pw.ridge_affine_map(source, target, ridge=1e-3)
    predicted = z[:-1] @ matrix + bias
    residual = jnp.linalg.norm(z[1:] - predicted, axis=1)
    return jnp.concatenate((residual, residual[-1:]), axis=0)


def stream_base(spec_kind: str, histories: dict[str, jax.Array], prefix: str) -> jax.Array:
    clock = histories[f"clock_{prefix}"]
    z = histories[f"z_{prefix}"]
    entropy_rate = histories[f"entropy_rate_{prefix}"][:, None]
    event_activity = histories[f"event_activity_{prefix}"][:, None]
    residual_memory = histories[f"residual_memory_{prefix}"][:, None]
    causal_action = histories[f"causal_action_{prefix}"][:, None]
    transition_residual = histories[f"transition_residual_{prefix}"][:, None]
    strain = histories[f"strain_{prefix}"][:, None]
    velocity, acceleration = derivatives(z)
    curvature = pw.curvature(z)[:, None]
    local_residual = one_step_residual(z, z.shape[0] // 2)[:, None]
    if spec_kind == "clock":
        return clock
    if spec_kind == "state":
        return jnp.concatenate((z, velocity, curvature, entropy_rate, residual_memory, causal_action), axis=1)
    if spec_kind == "transition":
        return jnp.concatenate(
            (
                velocity,
                acceleration,
                local_residual,
                transition_residual,
                event_activity,
                strain,
                causal_action,
            ),
            axis=1,
        )
    if spec_kind == "rich":
        return jnp.concatenate(
            (
                clock,
                z,
                velocity,
                acceleration,
                curvature,
                entropy_rate,
                event_activity,
                residual_memory,
                causal_action,
                transition_residual,
                strain,
            ),
            axis=1,
        )
    raise ValueError(f"unknown feature kind: {spec_kind}")


def build_raw_stream(spec: dict, histories: dict[str, jax.Array], prefix: str) -> jax.Array:
    return history_embed(stream_base(spec["kind"], histories, prefix), spec["radius"])


def normalize_streams(
    alice: jax.Array,
    bob: jax.Array,
    cross: jax.Array,
    calibration_steps: int,
) -> tuple[jax.Array, jax.Array, jax.Array]:
    reference = jnp.concatenate((alice[:calibration_steps], bob[:calibration_steps]), axis=0)
    mean = jnp.mean(reference, axis=0, keepdims=True)
    std = jnp.maximum(jnp.std(reference, axis=0, keepdims=True), 1e-6)
    return (alice - mean) / std, (bob - mean) / std, (cross - mean) / std


def normalize_with_reference(
    reference_a: jax.Array,
    reference_b: jax.Array,
    features: jax.Array,
    calibration_steps: int,
) -> jax.Array:
    reference = jnp.concatenate(
        (reference_a[:calibration_steps], reference_b[:calibration_steps]), axis=0
    )
    mean = jnp.mean(reference, axis=0, keepdims=True)
    std = jnp.maximum(jnp.std(reference, axis=0, keepdims=True), 1e-6)
    return (features - mean) / std


def contrastive_weights(
    alice: jax.Array,
    bob: jax.Array,
    cross: jax.Array,
    shuffled: jax.Array,
    calibration_query: jax.Array,
    oracle_calibration: jax.Array,
) -> jax.Array:
    query = alice[calibration_query]
    positive = (query - bob[oracle_calibration]) ** 2
    wrong = bob[jnp.clip(oracle_calibration + 7, 0, bob.shape[0] - 1)]
    negatives = jnp.concatenate(
        (
            (query - wrong) ** 2,
            (query - shuffled[calibration_query]) ** 2,
            (query - cross[calibration_query]) ** 2,
        ),
        axis=0,
    )
    separation = jnp.mean(negatives, axis=0) - jnp.mean(positive, axis=0)
    weights = jnp.clip(separation, 0.0, None)
    weights = weights / jnp.maximum(jnp.mean(weights), 1e-6)
    return jnp.sqrt(jnp.clip(weights, 0.05, 8.0))


def feature_bundle(
    spec: dict,
    histories: dict[str, jax.Array],
    permutation_key: jax.Array,
    calibration_steps: int,
    calibration_query: jax.Array,
    oracle_calibration: jax.Array,
) -> tuple[jax.Array, jax.Array, dict[str, jax.Array]]:
    alice_raw = build_raw_stream(spec, histories, "a")
    bob_raw = build_raw_stream(spec, histories, "b")
    cross_raw = build_raw_stream(spec, histories, "cross")
    statsperm_raw = build_raw_stream(spec, histories, "statsperm")
    alice, bob, cross = normalize_streams(alice_raw, bob_raw, cross_raw, calibration_steps)
    statsperm = normalize_with_reference(
        alice_raw, bob_raw, statsperm_raw, calibration_steps
    )

    shuffle_key, sever_key = jax.random.split(permutation_key)
    shuffled = bob[jax.random.permutation(shuffle_key, bob.shape[0])]
    severed = bob[jax.random.permutation(sever_key, bob.shape[0])]

    if spec["contrastive"]:
        weights = contrastive_weights(
            alice, bob, cross, shuffled, calibration_query, oracle_calibration
        )
        alice = alice * weights
        bob = bob * weights
        cross = cross * weights
        shuffled = shuffled * weights
        severed = severed * weights

    nulls = {
        "shuffled_clock": shuffled,
        "cross_seed_clock": cross,
        "severed_clock": severed,
        "causal_stats_permuted_clock": statsperm,
    }
    return alice, bob, nulls


def observability_metrics(
    alice_features: jax.Array,
    bob_features: jax.Array,
    null_features: dict[str, jax.Array],
    query_indices: jax.Array,
    oracle_matches: jax.Array,
    window: int,
) -> dict[str, float]:
    query = alice_features[query_indices]
    true_distance = jnp.sum((query - bob_features[oracle_matches]) ** 2, axis=1)
    offsets = jnp.arange(-window, window + 1)
    local_candidates = jnp.clip(
        oracle_matches[:, None] + offsets[None, :], 0, bob_features.shape[0] - 1
    )
    local_distance = jnp.sum(
        (query[:, None, :] - bob_features[local_candidates]) ** 2, axis=2
    )
    local_wrong = jnp.where(local_candidates == oracle_matches[:, None], jnp.inf, local_distance)

    main_null_names = ["wrong_lag_clock"]
    null_distances = [jnp.min(local_wrong, axis=1)]
    per_null = {"nearest_wrong_lag_distance": float(jnp.mean(null_distances[0]))}
    anti_cheat_distance = None
    for name, features in null_features.items():
        candidates = jnp.clip(
            query_indices[:, None] + offsets[None, :], 0, features.shape[0] - 1
        )
        distance = jnp.sum((query[:, None, :] - features[candidates]) ** 2, axis=2)
        nearest = jnp.min(distance, axis=1)
        per_null[f"nearest_{name}_distance"] = float(jnp.mean(nearest))
        if name == "causal_stats_permuted_clock":
            anti_cheat_distance = nearest
        else:
            main_null_names.append(name)
            null_distances.append(nearest)

    stacked_nulls = jnp.stack(null_distances, axis=1)
    nearest_null = jnp.min(stacked_nulls, axis=1)
    margin = nearest_null - true_distance
    winner_id = jnp.argmin(stacked_nulls, axis=1)
    failed = margin <= 0.0
    failed_count = jnp.maximum(jnp.sum(failed), 1)
    shuffled_index = main_null_names.index("shuffled_clock")
    severed_index = main_null_names.index("severed_clock")
    same_distribution_winner = (winner_id == shuffled_index) | (winner_id == severed_index)
    shuffled_failed_winner_rate = jnp.sum(failed & (winner_id == shuffled_index)) / failed_count
    severed_failed_winner_rate = jnp.sum(failed & (winner_id == severed_index)) / failed_count
    same_distribution_failure_rate = jnp.sum(failed & same_distribution_winner) / failed_count
    if anti_cheat_distance is None:
        anti_cheat_distance = nearest_null
    anti_cheat_margin = anti_cheat_distance - true_distance
    rank = 1 + jnp.sum(stacked_nulls < true_distance[:, None], axis=1)
    collision_threshold = 0.05 * jnp.maximum(true_distance, 1e-6)
    collisions = jnp.any(
        jnp.abs(stacked_nulls - true_distance[:, None]) <= collision_threshold[:, None],
        axis=1,
    )
    return {
        "true_pair_distance": float(jnp.mean(true_distance)),
        "nearest_null_distance": float(jnp.mean(nearest_null)),
        "clock_margin_mean": float(jnp.mean(margin)),
        "clock_margin_median": float(jnp.median(margin)),
        "fraction_positive_margin": float(jnp.mean(margin > 0.0)),
        "clock_collision_rate": float(jnp.mean(collisions)),
        "true_path_rank_mean": float(jnp.mean(rank)),
        "true_path_rank_median": float(jnp.median(rank)),
        "true_path_rank_p90": float(jnp.quantile(rank, 0.90)),
        "anti_cheat_positive_margin": float(jnp.mean(anti_cheat_margin > 0.0)),
        "anti_cheat_margin_median": float(jnp.median(anti_cheat_margin)),
        "anti_cheat_margin_mean": float(jnp.mean(anti_cheat_margin)),
        "same_distribution_failure_rate": float(same_distribution_failure_rate),
        "shuffled_failed_winner_rate": float(shuffled_failed_winner_rate),
        "severed_failed_winner_rate": float(severed_failed_winner_rate),
        "same_stats_permuted_failure_rate": float(jnp.mean(anti_cheat_margin <= 0.0)),
        **per_null,
    }


def run_configuration(
    seed: int,
    noise: float,
    generator_arm: str,
    time_steps: int,
    state_dim: int,
    latent_dim: int,
    true_lag: int,
) -> dict:
    calibration_steps = time_steps // 2
    query_stop = time_steps - 1
    key = jax.random.PRNGKey(seed)
    histories = physics_priors_histories(
        key, time_steps, state_dim, latent_dim, true_lag, noise, generator_arm
    )
    calibration_query = jnp.arange(0, calibration_steps - 1)
    payload_query = jnp.arange(calibration_steps, query_stop)
    oracle_calibration = intrinsic_oracle_path(histories, calibration_query)
    oracle_payload = intrinsic_oracle_path(histories, payload_query)

    results = {}
    for index, spec in enumerate(FEATURE_SPECS):
        alice, bob, nulls = feature_bundle(
            spec,
            histories,
            jax.random.fold_in(key, 200 + index),
            calibration_steps,
            calibration_query,
            oracle_calibration,
        )
        calibration_metrics = observability_metrics(
            alice, bob, nulls, calibration_query, oracle_calibration, window=12
        )
        payload_metrics = observability_metrics(
            alice, bob, nulls, payload_query, oracle_payload, window=12
        )
        results[spec["name"]] = {
            "spec": spec,
            "calibration": calibration_metrics,
            "payload": payload_metrics,
            "payload_margin_generalization_gap": (
                calibration_metrics["clock_margin_mean"] - payload_metrics["clock_margin_mean"]
            ),
        }
    return {
        "config": {"seed": seed, "noise": noise, "generator_arm": generator_arm},
        "features": results,
    }


def aggregate(results: list[dict], noise_values: list[float], generator_arms: list[str]) -> dict:
    summary = {}
    for arm in generator_arms:
        summary[arm] = {}
        for noise in noise_values:
            noise_key = f"{noise:.2f}"
            subset = [
                result
                for result in results
                if result["config"]["noise"] == noise
                and result["config"]["generator_arm"] == arm
            ]
            summary[arm][noise_key] = {}
            for spec in FEATURE_SPECS:
                rows = [result["features"][spec["name"]] for result in subset]
                summary[arm][noise_key][spec["name"]] = {
                    "median_payload_fraction_positive_margin": float(
                        np.median([row["payload"]["fraction_positive_margin"] for row in rows])
                    ),
                    "median_payload_margin": float(
                        np.median([row["payload"]["clock_margin_median"] for row in rows])
                    ),
                    "mean_payload_margin": float(
                        np.median([row["payload"]["clock_margin_mean"] for row in rows])
                    ),
                    "median_payload_collision_rate": float(
                        np.median([row["payload"]["clock_collision_rate"] for row in rows])
                    ),
                    "median_payload_true_path_rank": float(
                        np.median([row["payload"]["true_path_rank_median"] for row in rows])
                    ),
                    "payload_true_path_rank_p90": float(
                        np.median([row["payload"]["true_path_rank_p90"] for row in rows])
                    ),
                    "median_anti_cheat_positive_margin": float(
                        np.median([row["payload"]["anti_cheat_positive_margin"] for row in rows])
                    ),
                    "median_anti_cheat_margin": float(
                        np.median([row["payload"]["anti_cheat_margin_median"] for row in rows])
                    ),
                    "median_same_distribution_failure_rate": float(
                        np.median([row["payload"]["same_distribution_failure_rate"] for row in rows])
                    ),
                    "median_same_stats_permuted_failure_rate": float(
                        np.median([row["payload"]["same_stats_permuted_failure_rate"] for row in rows])
                    ),
                    "median_generalization_gap": float(
                        np.median([row["payload_margin_generalization_gap"] for row in rows])
                    ),
                }
    return summary


def main() -> None:
    args = parse_args()
    backend = jax.default_backend()
    if args.require_tpu and backend != "tpu":
        raise RuntimeError(f"TPU required, got {backend}: {jax.devices()}")
    configs = [
        (arm, seed, noise)
        for arm in args.generator_arms
        for noise in args.noise_values
        for seed in args.seeds
    ]
    print(
        f"AQ-PAGE-WOOTTERS-DLINOSS-GLOBAL-CAUSAL-MEMORY-0 backend={backend} "
        f"configs={len(configs)}",
        flush=True,
    )
    results = []
    for index, (arm, seed, noise) in enumerate(configs):
        print(
            f"[CONFIG {index + 1}/{len(configs)}] arm={arm} seed={seed} noise={noise:.2f}",
            flush=True,
        )
        result = run_configuration(
            seed, noise, arm, args.time_steps, args.state_dim, args.latent_dim, args.true_lag
        )
        results.append(result)
        best = max(
            FEATURE_SPECS,
            key=lambda spec: result["features"][spec["name"]]["payload"]["fraction_positive_margin"],
        )
        metrics = result["features"][best["name"]]["payload"]
        print(
            f"[RESULT] arm={arm} noise={noise:.2f} seed={seed} "
            f"best={best['name']} "
            f"positive_margin={metrics['fraction_positive_margin']:.3f} "
            f"median_margin={metrics['clock_margin_median']:.6f} "
            f"anti_cheat={metrics['anti_cheat_positive_margin']:.3f} "
            f"same_dist_fail={metrics['same_distribution_failure_rate']:.3f} "
            f"rank_p90={metrics['true_path_rank_p90']:.3f} "
            f"collision={metrics['clock_collision_rate']:.3f}",
            flush=True,
        )

    payload = {
        "program": "AQ-PAGE-WOOTTERS-DLINOSS-GLOBAL-CAUSAL-MEMORY-0",
        "backend": backend,
        "config": {
            "time_steps": args.time_steps,
            "state_dim": args.state_dim,
            "latent_dim": args.latent_dim,
            "true_lag": args.true_lag,
            "generator_arms": args.generator_arms,
            "feature_specs": FEATURE_SPECS,
        },
        "aggregate": aggregate(results, args.noise_values, args.generator_arms),
        "results": results,
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    output = args.out_dir / "global_causal_memory0_results.json"
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[DONE] results={output}", flush=True)


if __name__ == "__main__":
    main()
