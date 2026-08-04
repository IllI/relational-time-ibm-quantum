#!/usr/bin/env python3
"""AQ-PAGE-WOOTTERS-0: controlled relational-clock model selection."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Dict, Tuple

import jax
import jax.numpy as jnp
import numpy as np


BETA_CANDIDATES = (0.0, 0.1, 0.25, 0.5, 1.0)
SANITY_SHIFT = 5
MATCH_WINDOW = 6
MODEL_NAMES = (
    "internal_relational_clock",
    "sin_cos_only_relational_clock",
    "curvature_only_relational_clock",
    "external_timing_carrier",
    "index_clock",
    "shuffled_clock",
    "wrong_lag_clock",
    "severed_clock",
    "cross_seed_clock",
    "null_drift",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("0a", "0b", "both"), default="both")
    parser.add_argument("--time-steps", type=int, default=128)
    parser.add_argument("--state-dim", type=int, default=64)
    parser.add_argument("--latent-dim", type=int, default=8)
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--noise", type=float, default=0.0)
    parser.add_argument("--bootstrap-samples", type=int, default=1000)
    parser.add_argument("--out-dir", type=Path, default=Path("aq_page_wootters_results"))
    parser.add_argument("--require-tpu", action="store_true")
    args = parser.parse_args()
    if args.time_steps < 32 or args.time_steps % 2:
        parser.error("--time-steps must be an even integer >= 32")
    if args.latent_dim < 4 or args.latent_dim % 2:
        parser.error("--latent-dim must be an even integer >= 4")
    if args.state_dim < args.latent_dim:
        parser.error("--state-dim must be >= --latent-dim")
    return args


def cosine_rows(a: jax.Array, b: jax.Array) -> jax.Array:
    denom = jnp.linalg.norm(a, axis=1) * jnp.linalg.norm(b, axis=1)
    return jnp.sum(a * b, axis=1) / jnp.maximum(denom, 1e-8)


def normalize_features(
    a: jax.Array, b: jax.Array, calibration_steps: int
) -> Tuple[jax.Array, jax.Array]:
    calibration = jnp.concatenate((a[:calibration_steps], b[:calibration_steps]), axis=0)
    mean = jnp.mean(calibration, axis=0)
    scale = jnp.std(calibration, axis=0)
    scale = jnp.where(scale < 1e-6, 1.0, scale)
    return (a - mean) / scale, (b - mean) / scale


def learn_lag(
    a_features: jax.Array,
    b_features: jax.Array,
    start: int,
    stop: int,
    max_lag: int,
) -> Tuple[int, Dict[str, float]]:
    scores: Dict[str, float] = {}
    best_lag = 0
    best_score = math.inf
    for lag in range(-max_lag, max_lag + 1):
        query = jnp.arange(start, stop)
        target = query + lag
        valid = (target >= 0) & (target < b_features.shape[0])
        distance = jnp.sum((a_features[query] - b_features[jnp.clip(target, 0, b_features.shape[0] - 1)]) ** 2, axis=1)
        score = float(
            jnp.sum(jnp.where(valid, distance, 0.0))
            / jnp.maximum(jnp.sum(valid), 1)
        )
        scores[str(lag)] = score
        if score < best_score:
            best_score = score
            best_lag = lag
    return best_lag, scores


def constrained_monotone_match(
    a_features: jax.Array,
    b_features: jax.Array,
    query_indices: jax.Array,
    candidate_indices: jax.Array,
    lag_prior: int,
    window: int,
) -> jax.Array:
    query = a_features[query_indices]
    candidates = b_features[candidate_indices]
    costs = jnp.sum((query[:, None, :] - candidates[None, :, :]) ** 2, axis=-1)

    def choose(previous: jax.Array, row: Tuple[jax.Array, jax.Array]):
        query_index, row_cost = row
        allowed = (
            (candidate_indices > previous)
            & (jnp.abs(candidate_indices - query_index - lag_prior) <= window)
        )
        fallback = jnp.clip(
            query_index + lag_prior,
            candidate_indices[0],
            candidate_indices[-1],
        )
        masked = jnp.where(allowed, row_cost, jnp.inf)
        chosen = candidate_indices[jnp.argmin(masked)]
        chosen = jnp.where(jnp.any(allowed), chosen, fallback)
        return chosen, chosen

    initial = candidate_indices[0] - 1
    _, matches = jax.lax.scan(choose, initial, (query_indices, costs))
    return matches


def ridge_affine_map(
    source: jax.Array, target: jax.Array, ridge: float = 1e-3
) -> Tuple[jax.Array, jax.Array]:
    design = jnp.concatenate(
        (source, jnp.ones((source.shape[0], 1), dtype=source.dtype)), axis=1
    )
    gram = design.T @ design
    penalty = ridge * jnp.eye(design.shape[1], dtype=source.dtype)
    penalty = penalty.at[-1, -1].set(0.0)
    fitted = jnp.linalg.solve(gram + penalty, design.T @ target)
    return fitted[:-1], fitted[-1]


def curvature(z: jax.Array) -> jax.Array:
    center = z[1:-1]
    values = jnp.linalg.norm(z[2:] - 2.0 * center + z[:-2], axis=1)
    return jnp.concatenate((values[:1], values, values[-1:]), axis=0)


def cumulative_curvature(kappa: jax.Array) -> jax.Array:
    return jnp.concatenate((jnp.zeros((1,), dtype=kappa.dtype), jnp.cumsum(kappa[:-1])))


def stable_latent_histories(
    key: jax.Array,
    time_steps: int,
    state_dim: int,
    latent_dim: int,
    noise: float,
) -> Dict[str, jax.Array]:
    (
        key_basis,
        key_phase,
        key_noise_a,
        key_noise_b,
        key_cross_phase,
        key_cross_amplitude,
    ) = jax.random.split(key, 6)
    basis_raw = jax.random.normal(key_basis, (state_dim, latent_dim))
    basis, _ = jnp.linalg.qr(basis_raw, mode="reduced")

    pair_count = latent_dim // 2
    frequencies = jnp.linspace(0.13, 0.57, pair_count)
    phases = jax.random.uniform(key_phase, (pair_count,), minval=-jnp.pi, maxval=jnp.pi)
    t = jnp.arange(time_steps, dtype=jnp.float32)

    speed_a = 1.0 + 0.18 * jnp.sin(2.0 * jnp.pi * t / 37.0)
    speed_b = 1.0 + 0.18 * jnp.sin(2.0 * jnp.pi * (t + 5.0) / 37.0)
    intrinsic_a = jnp.cumsum(speed_a)
    intrinsic_b = jnp.cumsum(speed_b)

    def make_latent(intrinsic: jax.Array, local_phases: jax.Array) -> jax.Array:
        angles = intrinsic[:, None] * frequencies[None, :] + local_phases[None, :]
        paired = jnp.stack((jnp.cos(angles), jnp.sin(angles)), axis=-1)
        return paired.reshape(time_steps, latent_dim)

    z_a = make_latent(intrinsic_a, phases)
    z_b = make_latent(intrinsic_b, phases + 0.04)
    cross_phases = jax.random.uniform(
        key_cross_phase, (pair_count,), minval=-jnp.pi, maxval=jnp.pi
    )
    z_cross = make_latent(intrinsic_b, cross_phases)
    cross_amplitudes = jnp.exp(
        0.35 * jax.random.normal(key_cross_amplitude, (pair_count,))
    )
    z_cross = (
        z_cross.reshape(time_steps, pair_count, 2)
        * cross_amplitudes[None, :, None]
    ).reshape(time_steps, latent_dim)

    if noise:
        z_a = z_a + noise * jax.random.normal(key_noise_a, z_a.shape)
        z_b = z_b + noise * jax.random.normal(key_noise_b, z_b.shape)

    x_a = z_a @ basis.T
    x_b = z_b @ basis.T
    return {
        "basis": basis,
        "z_a": z_a,
        "z_b": z_b,
        "z_cross": z_cross,
        "x_a": x_a,
        "x_b": x_b,
        "intrinsic_a": intrinsic_a,
        "intrinsic_b": intrinsic_b,
    }


def sanity_latent_histories(
    key: jax.Array,
    time_steps: int,
    state_dim: int,
    latent_dim: int,
    noise: float,
    shift: int = SANITY_SHIFT,
) -> Dict[str, jax.Array]:
    key_basis, key_phase, key_rotation, key_cross, key_noise = jax.random.split(key, 5)
    basis_raw = jax.random.normal(key_basis, (state_dim, latent_dim))
    basis, _ = jnp.linalg.qr(basis_raw, mode="reduced")
    rotation_raw = jax.random.normal(key_rotation, (latent_dim, latent_dim))
    rotation, _ = jnp.linalg.qr(rotation_raw)

    pair_count = latent_dim // 2
    frequencies = jnp.linspace(0.11, 0.53, pair_count)
    phases = jax.random.uniform(key_phase, (pair_count,), minval=-jnp.pi, maxval=jnp.pi)
    t = jnp.arange(time_steps + shift, dtype=jnp.float32)
    speed = 1.0 + 0.15 * jnp.sin(2.0 * jnp.pi * t / 41.0)
    intrinsic = jnp.cumsum(speed)
    angles = intrinsic[:, None] * frequencies[None, :] + phases[None, :]
    base = jnp.stack((jnp.cos(angles), jnp.sin(angles)), axis=-1).reshape(
        time_steps + shift, latent_dim
    )

    z_a = base[:time_steps]
    z_b = base[shift : shift + time_steps] @ rotation
    cross_phases = jax.random.uniform(
        key_cross, (pair_count,), minval=-jnp.pi, maxval=jnp.pi
    )
    cross_angles = intrinsic[:time_steps, None] * frequencies[None, :] + cross_phases[None, :]
    z_cross = jnp.stack(
        (jnp.cos(cross_angles), jnp.sin(cross_angles)), axis=-1
    ).reshape(time_steps, latent_dim)
    if noise:
        noise_a, noise_b = jax.random.split(key_noise)
        z_a = z_a + noise * jax.random.normal(noise_a, z_a.shape)
        z_b = z_b + noise * jax.random.normal(noise_b, z_b.shape)

    return {
        "basis": basis,
        "z_a": z_a,
        "z_b": z_b,
        "z_cross": z_cross,
        "x_a": z_a @ basis.T,
        "x_b": z_b @ basis.T,
        "clock_tick_a": jnp.arange(time_steps, dtype=jnp.float32),
        "clock_tick_b": jnp.arange(time_steps, dtype=jnp.float32) + shift,
        "true_lag": -shift,
        "true_operator": rotation,
    }


def history_metrics(states: jax.Array) -> Dict[str, float]:
    normalized = states / jnp.maximum(jnp.linalg.norm(states, axis=1, keepdims=True), 1e-8)
    amplitude = normalized / jnp.sqrt(float(states.shape[0]))
    amplitude = amplitude / jnp.maximum(jnp.linalg.norm(amplitude), 1e-8)
    norm = jnp.sum(amplitude * amplitude)
    rho_clock = amplitude @ amplitude.T
    rho_system = amplitude.T @ amplitude

    def entropy(rho: jax.Array) -> jax.Array:
        eigenvalues = jnp.linalg.eigvalsh((rho + rho.T) * 0.5)
        eigenvalues = jnp.clip(eigenvalues, 1e-12, 1.0)
        return -jnp.sum(eigenvalues * jnp.log(eigenvalues))

    s_clock = entropy(rho_clock)
    s_system = entropy(rho_system)
    return {
        "history_state_norm_error": float(jnp.abs(norm - 1.0)),
        "clock_schmidt_entropy": float(s_clock),
        "clock_system_mutual_information": float(s_clock + s_system),
    }


def external_carrier(
    key: jax.Array,
    tau_a: jax.Array,
    tau_b: jax.Array,
    calibration_steps: int,
) -> Tuple[jax.Array, jax.Array]:
    increments = jnp.diff(jnp.concatenate((tau_a[:1], tau_a[:calibration_steps])))
    mu = jnp.mean(increments)
    centered = increments - mu
    phi = jnp.sum(centered[1:] * centered[:-1]) / jnp.maximum(
        jnp.sum(centered[:-1] ** 2), 1e-8
    )
    phi = jnp.clip(phi, -0.95, 0.95)
    innovation_scale = jnp.maximum(jnp.std(centered[1:] - phi * centered[:-1]), 1e-3)
    innovations = innovation_scale * jax.random.normal(key, (2, tau_a.shape[0]))

    def generate(eps: jax.Array, start: jax.Array) -> jax.Array:
        def step(previous: jax.Array, innovation: jax.Array):
            current = mu + phi * (previous - mu) + innovation
            return current, current

        _, velocity = jax.lax.scan(step, mu, eps)
        return start + jnp.cumsum(velocity)

    return generate(innovations[0], tau_a[0]), generate(innovations[1], tau_b[0])


def make_sanity_clock_arms(
    key: jax.Array,
    histories: Dict[str, jax.Array],
    calibration_steps: int,
) -> Dict[str, Tuple[jax.Array, jax.Array]]:
    tick_a = histories["clock_tick_a"]
    tick_b = histories["clock_tick_b"]
    omega = 2.0 * jnp.pi / 19.0
    calibration_ticks = jnp.concatenate(
        (tick_a[:calibration_steps], tick_b[:calibration_steps])
    )
    tick_mean = jnp.mean(calibration_ticks)
    tick_scale = jnp.maximum(jnp.std(calibration_ticks), 1e-6)

    def exposed(tick: jax.Array) -> jax.Array:
        tau = omega * tick
        return jnp.stack(
            (jnp.sin(tau), jnp.cos(tau), (tick - tick_mean) / tick_scale), axis=1
        )

    full_a = exposed(tick_a)
    full_b = exposed(tick_b)
    sincos_a = full_a[:, :2]
    sincos_b = full_b[:, :2]
    kappa_a = curvature(histories["z_a"])
    kappa_b = curvature(histories["z_b"])
    calibration_kappa = jnp.concatenate(
        (kappa_a[:calibration_steps], kappa_b[:calibration_steps])
    )
    kappa_mean = jnp.mean(calibration_kappa)
    kappa_scale = jnp.maximum(jnp.std(calibration_kappa), 1e-6)
    curvature_a = ((kappa_a - kappa_mean) / kappa_scale)[:, None]
    curvature_b = ((kappa_b - kappa_mean) / kappa_scale)[:, None]
    key_external, key_shuffle, key_sever, key_cross = jax.random.split(key, 4)
    ext_tau_a, ext_tau_b = external_carrier(
        key_external, omega * tick_a, omega * tick_b, calibration_steps
    )
    external_a = jnp.stack((jnp.sin(ext_tau_a), jnp.cos(ext_tau_a)), axis=1)
    external_b = jnp.stack((jnp.sin(ext_tau_b), jnp.cos(ext_tau_b)), axis=1)
    shuffled_b = full_b[jax.random.permutation(key_shuffle, full_b.shape[0])]
    wrong_lag_b = jnp.roll(full_b, shift=max(7, full_b.shape[0] // 6), axis=0)
    severed_b = full_b[jax.random.permutation(key_sever, full_b.shape[0])]

    cross_velocity = (
        0.62
        + 0.18
        * jnp.sin(
            2.0
            * jnp.pi
            * jnp.arange(full_b.shape[0], dtype=jnp.float32)
            / 29.0
        )
        + 0.08 * jax.random.normal(key_cross, (full_b.shape[0],))
    )
    cross_tick = jnp.cumsum(jnp.maximum(cross_velocity, 0.1))
    cross_b = exposed(cross_tick)
    index = (
        jnp.arange(full_b.shape[0], dtype=jnp.float32)
        / max(full_b.shape[0] - 1, 1)
    )[:, None]
    return {
        "internal_relational_clock": (full_a, full_b),
        "sin_cos_only_relational_clock": (sincos_a, sincos_b),
        "curvature_only_relational_clock": (curvature_a, curvature_b),
        "external_timing_carrier": (external_a, external_b),
        "index_clock": (index, index),
        "shuffled_clock": (full_a, shuffled_b),
        "wrong_lag_clock": (full_a, wrong_lag_b),
        "severed_clock": (full_a, severed_b),
        "cross_seed_clock": (full_a, cross_b),
        "null_drift": (index, index),
    }


def make_clock_arms(
    key: jax.Array,
    z_a: jax.Array,
    z_b: jax.Array,
    z_cross: jax.Array,
    beta: float,
    calibration_steps: int,
    mode: str,
) -> Tuple[Dict[str, Tuple[jax.Array, jax.Array]], Dict[str, jax.Array]]:
    time_steps = z_a.shape[0]
    t = jnp.arange(time_steps, dtype=jnp.float32)
    omega = 2.0 * jnp.pi / 18.0
    kappa_a = curvature(z_a)
    kappa_b = curvature(z_b)
    kappa_cross = curvature(z_cross)

    calibration_kappa = jnp.concatenate(
        (kappa_a[:calibration_steps], kappa_b[:calibration_steps])
    )
    kappa_median = jnp.median(calibration_kappa)
    kappa_mad = jnp.median(jnp.abs(calibration_kappa - kappa_median))
    kappa_scale = jnp.maximum(1.4826 * kappa_mad, 1e-6)
    q_a = (kappa_a - kappa_median) / kappa_scale
    q_b = (kappa_b - kappa_median) / kappa_scale
    q_cross = (kappa_cross - kappa_median) / kappa_scale

    if mode == "0a":
        tau_a = omega * t
        tau_b = omega * t
        tau_cross = omega * t
    else:
        tau_a = omega * t + beta * cumulative_curvature(kappa_a)
        tau_b = omega * t + beta * cumulative_curvature(kappa_b)
        tau_cross = omega * t + beta * cumulative_curvature(kappa_cross)

    sincos_a = jnp.stack((jnp.sin(tau_a), jnp.cos(tau_a)), axis=1)
    sincos_b = jnp.stack((jnp.sin(tau_b), jnp.cos(tau_b)), axis=1)
    if mode == "0a":
        full_a = sincos_a
        full_b = sincos_b
    else:
        full_a = jnp.concatenate((sincos_a, q_a[:, None]), axis=1)
        full_b = jnp.concatenate((sincos_b, q_b[:, None]), axis=1)

    key_external, key_shuffle, key_sever = jax.random.split(key, 3)
    ext_tau_a, ext_tau_b = external_carrier(
        key_external, tau_a, tau_b, calibration_steps
    )
    external_a = jnp.stack((jnp.sin(ext_tau_a), jnp.cos(ext_tau_a)), axis=1)
    external_b = jnp.stack((jnp.sin(ext_tau_b), jnp.cos(ext_tau_b)), axis=1)

    permutation = jax.random.permutation(key_shuffle, time_steps)
    shuffled_b = full_b[permutation]
    wrong_lag_b = jnp.roll(full_b, shift=max(5, time_steps // 8), axis=0)
    sever_permutation = jax.random.permutation(key_sever, time_steps)
    severed_b = full_b[sever_permutation]
    cross_sincos = jnp.stack((jnp.sin(tau_cross), jnp.cos(tau_cross)), axis=1)
    cross_b = (
        cross_sincos
        if mode == "0a"
        else jnp.concatenate((cross_sincos, q_cross[:, None]), axis=1)
    )
    index = (t / max(time_steps - 1, 1))[:, None]

    arms = {
        "internal_relational_clock": (full_a, full_b),
        "sin_cos_only_relational_clock": (sincos_a, sincos_b),
        "curvature_only_relational_clock": (q_a[:, None], q_b[:, None]),
        "external_timing_carrier": (external_a, external_b),
        "index_clock": (index, index),
        "shuffled_clock": (full_a, shuffled_b),
        "wrong_lag_clock": (full_a, wrong_lag_b),
        "severed_clock": (full_a, severed_b),
        "cross_seed_clock": (full_a, cross_b),
        "null_drift": (index, index),
    }
    frozen = {
        "kappa_a": kappa_a,
        "kappa_b": kappa_b,
        "tau_a": tau_a,
        "tau_b": tau_b,
    }
    return arms, frozen


def path_metrics(
    query_indices: jax.Array,
    matches: jax.Array,
    expected_lag: int,
) -> Dict[str, float]:
    expected = query_indices + expected_lag
    errors = jnp.abs(matches - expected)
    jumps = jnp.diff(matches)
    return {
        "clock_path_mean_abs_error": float(jnp.mean(errors)),
        "clock_path_median_abs_error": float(jnp.median(errors)),
        "clock_path_max_jump": float(jnp.max(jnp.abs(jumps))) if matches.shape[0] > 1 else 0.0,
        "clock_path_monotonicity_violations": int(jnp.sum(jumps <= 0)),
        "fraction_matches_within_1_step": float(jnp.mean(errors <= 1)),
        "fraction_matches_within_2_steps": float(jnp.mean(errors <= 2)),
    }


def fit_true_operator(
    features: Tuple[jax.Array, jax.Array],
    z_a: jax.Array,
    z_b: jax.Array,
    calibration_steps: int,
    lag_prior: int,
) -> Tuple[jax.Array, jax.Array, jax.Array, jax.Array]:
    a_features, b_features = normalize_features(
        features[0], features[1], calibration_steps
    )
    delta_a = z_a[1:] - z_a[:-1]
    delta_b = z_b[1:] - z_b[:-1]
    fit_query = jnp.arange(max(0, -lag_prior), calibration_steps - 1)
    fit_candidates = jnp.arange(0, calibration_steps - 1)
    fit_match = constrained_monotone_match(
        a_features,
        b_features,
        fit_query,
        fit_candidates,
        lag_prior,
        MATCH_WINDOW,
    )
    operator, intercept = ridge_affine_map(
        delta_a[fit_query], delta_b[fit_match]
    )
    return operator, intercept, fit_query, fit_match


def evaluate_frozen_arm(
    features: Tuple[jax.Array, jax.Array],
    z_a: jax.Array,
    target_z: jax.Array,
    calibration_steps: int,
    lag_prior: int,
    operator: jax.Array,
    intercept: jax.Array,
    expected_lag: int,
) -> Dict[str, object]:
    a_features, b_features = normalize_features(
        features[0], features[1], calibration_steps
    )
    delta_a = z_a[1:] - z_a[:-1]
    delta_b = target_z[1:] - target_z[:-1]
    payload_query = jnp.arange(calibration_steps, z_a.shape[0] - 1)
    candidate_start = max(0, calibration_steps + lag_prior - MATCH_WINDOW)
    payload_candidates = jnp.arange(candidate_start, target_z.shape[0] - 1)
    payload_match = constrained_monotone_match(
        a_features,
        b_features,
        payload_query,
        payload_candidates,
        lag_prior,
        MATCH_WINDOW,
    )
    predictions = delta_a[payload_query] @ operator + intercept
    payload_scores = cosine_rows(predictions, delta_b[payload_match])
    phase_residual = jnp.linalg.norm(
        a_features[payload_query] - b_features[payload_match], axis=1
    )
    return {
        "payload_score": float(jnp.mean(payload_scores)),
        "payload_scores": payload_scores,
        "clock_phase_residual_mean": float(jnp.mean(phase_residual)),
        "clock_phase_residual_std": float(jnp.std(phase_residual)),
        **path_metrics(payload_query, payload_match, expected_lag),
    }


def calibration_score_for_beta(
    key: jax.Array,
    features: Tuple[jax.Array, jax.Array],
    z_a: jax.Array,
    z_b: jax.Array,
    calibration_steps: int,
) -> float:
    validation_start = calibration_steps * 3 // 4
    a_features, b_features = normalize_features(
        features[0], features[1], calibration_steps
    )
    lag_prior, _ = learn_lag(
        a_features, b_features, 0, validation_start - 1, max_lag=12
    )
    delta_a = z_a[1:] - z_a[:-1]
    delta_b = z_b[1:] - z_b[:-1]
    fit_query = jnp.arange(max(0, -lag_prior), validation_start - 1)
    fit_candidates = jnp.arange(0, validation_start - 1)
    fit_match = constrained_monotone_match(
        a_features,
        b_features,
        fit_query,
        fit_candidates,
        lag_prior,
        MATCH_WINDOW,
    )
    operator, intercept = ridge_affine_map(
        delta_a[fit_query], delta_b[fit_match]
    )
    validation_query = jnp.arange(validation_start, calibration_steps - 1)
    validation_candidates = jnp.arange(
        max(0, validation_start + lag_prior - MATCH_WINDOW),
        calibration_steps - 1,
    )
    validation_match = constrained_monotone_match(
        a_features,
        b_features,
        validation_query,
        validation_candidates,
        lag_prior,
        MATCH_WINDOW,
    )
    return float(
        jnp.mean(
            cosine_rows(
                delta_a[validation_query] @ operator + intercept,
                delta_b[validation_match],
            )
        )
    )


def select_beta(
    key: jax.Array,
    z_a: jax.Array,
    z_b: jax.Array,
    z_cross: jax.Array,
    calibration_steps: int,
) -> Tuple[float, Dict[str, float]]:
    scores: Dict[str, float] = {}
    best_beta = BETA_CANDIDATES[0]
    best_score = -math.inf
    for index, beta in enumerate(BETA_CANDIDATES):
        arms, _ = make_clock_arms(
            jax.random.fold_in(key, index),
            z_a,
            z_b,
            z_cross,
            beta,
            calibration_steps,
            "0b",
        )
        score = calibration_score_for_beta(
            jax.random.fold_in(key, 100 + index),
            arms["internal_relational_clock"],
            z_a,
            z_b,
            calibration_steps,
        )
        scores[str(beta)] = score
        if score > best_score + 1e-10:
            best_score = score
            best_beta = beta
    return best_beta, scores


def bootstrap_ci(
    key: jax.Array, gains: jax.Array, samples: int
) -> Tuple[float, float]:
    indices = jax.random.randint(key, (samples, gains.shape[0]), 0, gains.shape[0])
    means = jnp.mean(gains[indices], axis=1)
    bounds = jnp.quantile(means, jnp.array((0.025, 0.975)))
    return float(bounds[0]), float(bounds[1])


def run_mode(
    key: jax.Array,
    histories: Dict[str, jax.Array],
    mode: str,
    bootstrap_samples: int,
) -> Dict[str, object]:
    time_steps = histories["z_a"].shape[0]
    calibration_steps = time_steps // 2
    selected_beta = 0.0
    beta_scores: Dict[str, float] = {"0.0": 0.0}
    if mode == "0a":
        arms = make_sanity_clock_arms(
            jax.random.fold_in(key, 200), histories, calibration_steps
        )
        frozen = {
            "kappa_a": curvature(histories["z_a"]),
            "kappa_b": curvature(histories["z_b"]),
            "tau_a": histories["clock_tick_a"],
            "tau_b": histories["clock_tick_b"],
        }
    else:
        selected_beta, beta_scores = select_beta(
            jax.random.fold_in(key, 101),
            histories["z_a"],
            histories["z_b"],
            histories["z_cross"],
            calibration_steps,
        )
        arms, frozen = make_clock_arms(
            jax.random.fold_in(key, 202),
            histories["z_a"],
            histories["z_b"],
            histories["z_cross"],
            selected_beta,
            calibration_steps,
            mode,
        )

    true_a, true_b = normalize_features(
        arms["internal_relational_clock"][0],
        arms["internal_relational_clock"][1],
        calibration_steps,
    )
    selected_lag, lag_scores = learn_lag(
        true_a, true_b, 0, calibration_steps - 1, max_lag=12
    )
    operator, intercept, fit_query, fit_match = fit_true_operator(
        arms["internal_relational_clock"],
        histories["z_a"],
        histories["z_b"],
        calibration_steps,
        selected_lag,
    )

    expected_lag = (
        int(histories["true_lag"]) if mode == "0a" else selected_lag
    )
    results: Dict[str, Dict[str, object]] = {}
    for name in MODEL_NAMES:
        target_z = (
            histories["z_cross"] if name == "null_drift" else histories["z_b"]
        )
        arm_lag = (
            selected_lag + 2 * MATCH_WINDOW + 1
            if name == "wrong_lag_clock"
            else selected_lag
        )
        results[name] = evaluate_frozen_arm(
            arms[name],
            histories["z_a"],
            target_z,
            calibration_steps,
            arm_lag,
            operator,
            intercept,
            expected_lag,
        )

    primary = jnp.asarray(results["internal_relational_clock"]["payload_scores"])
    control_names = (
        "shuffled_clock",
        "wrong_lag_clock",
        "severed_clock",
        "cross_seed_clock",
        "null_drift",
    )
    controls = jnp.stack(
        [jnp.asarray(results[name]["payload_scores"]) for name in control_names],
        axis=0,
    )
    gains = primary - jnp.max(controls, axis=0)
    ci_low, ci_high = bootstrap_ci(
        jax.random.fold_in(key, 303), gains, bootstrap_samples
    )
    primary_score = float(results["internal_relational_clock"]["payload_score"])
    max_control = max(float(results[name]["payload_score"]) for name in control_names)
    external_score = float(results["external_timing_carrier"]["payload_score"])
    null_score = float(results["null_drift"]["payload_score"])
    sincos_score = float(
        results["sin_cos_only_relational_clock"]["payload_score"]
    )
    index_score = float(results["index_clock"]["payload_score"])
    history = history_metrics(histories["x_a"])
    operator_identity_cos = float(
        jnp.mean(
            cosine_rows(
                operator.T,
                jnp.eye(operator.shape[0], dtype=operator.dtype),
            )
        )
    )
    oracle_score = None
    if mode == "0a":
        payload_query = jnp.arange(calibration_steps, time_steps - 1)
        oracle_match = payload_query + int(histories["true_lag"])
        oracle_predictions = (
            histories["z_a"][1:] - histories["z_a"][:-1]
        )[payload_query] @ histories["true_operator"]
        oracle_targets = (
            histories["z_b"][1:] - histories["z_b"][:-1]
        )[oracle_match]
        oracle_score = float(jnp.mean(cosine_rows(oracle_predictions, oracle_targets)))

    metrics = {
        "selected_beta": float(selected_beta),
        "selected_lag": int(selected_lag),
        "selected_lag_error": (
            int(selected_lag - int(histories["true_lag"]))
            if mode == "0a"
            else None
        ),
        "lag_calibration_scores": lag_scores,
        "beta_calibration_scores": beta_scores,
        "calibration_steps": calibration_steps,
        "payload_windows": int(primary.shape[0]),
        "oracle_T_score": oracle_score,
        "frozen_true_T_payload_score": primary_score,
        "operator_cosine_Bspace": operator_identity_cos,
        "relational_clock_alignment_gain": primary_score - max_control,
        "relational_minus_external_gain": primary_score - external_score,
        "external_minus_null_gain": external_score - null_score,
        "state_coupled_minus_sin_cos_only_gain": primary_score - sincos_score,
        "paired_transition_gain_mean": float(jnp.mean(gains)),
        "paired_transition_gain_std": float(jnp.std(gains)),
        "paired_transition_gain_bootstrap_ci95": [ci_low, ci_high],
        "fraction_payload_windows_relational_beats_best_null": float(
            jnp.mean(gains > 0)
        ),
        **history,
    }
    debug_gate_clock = bool(
        results["internal_relational_clock"]["fraction_matches_within_1_step"] >= 0.90
        and results["internal_relational_clock"]["clock_path_mean_abs_error"] <= 1.0
        and results["internal_relational_clock"][
            "clock_path_monotonicity_violations"
        ]
        == 0
    )
    debug_gate_oracle = bool(oracle_score is None or oracle_score >= 0.95)
    debug_gate_fitted = bool(
        mode != "0a"
        or (
            primary_score >= 0.90
            and max_control <= 0.50
            and metrics["relational_clock_alignment_gain"] >= 0.50
        )
    )
    gates = {
        "gate_minus_1_clock_path": debug_gate_clock,
        "debug_gate_oracle": debug_gate_oracle,
        "debug_gate_fitted_transition": debug_gate_fitted,
        "gate_0_no_harm": bool(
            primary_score >= index_score - 0.01
            and history["history_state_norm_error"] < 1e-6
            and history["clock_schmidt_entropy"] > 1e-6
            and history["clock_system_mutual_information"] > 2e-6
        ),
        "gate_1_controls": bool(metrics["relational_clock_alignment_gain"] >= 0.10),
        "gate_2_external": bool(metrics["relational_minus_external_gain"] >= 0.05),
        "deformation_ablation_positive": bool(
            metrics["state_coupled_minus_sin_cos_only_gain"] > 0
        ),
        "gate_3_payload": bool(
            metrics["paired_transition_gain_mean"] > 0
            and ci_low > 0
            and metrics["fraction_payload_windows_relational_beats_best_null"]
            >= 0.70
        ),
    }

    serializable_results = {}
    for name, result in results.items():
        serializable_results[name] = {
            key_name: value
            for key_name, value in result.items()
            if key_name != "payload_scores"
        }
    return {
        "mode": mode,
        "metrics": metrics,
        "gates": gates,
        "calibration_path": {
            **path_metrics(fit_query, fit_match, expected_lag),
        },
        "models": serializable_results,
        "frozen_clock_summary": {
            "kappa_a_mean": float(jnp.mean(frozen["kappa_a"])),
            "kappa_b_mean": float(jnp.mean(frozen["kappa_b"])),
            "tau_a_final": float(frozen["tau_a"][-1]),
            "tau_b_final": float(frozen["tau_b"][-1]),
        },
    }


def main() -> None:
    args = parse_args()
    backend = jax.default_backend()
    devices = [str(device) for device in jax.devices()]
    if args.require_tpu and backend != "tpu":
        raise RuntimeError(f"TPU required, but JAX backend is {backend}: {devices}")

    print("AQ-PAGE-WOOTTERS-0 ACTIVE", flush=True)
    print(
        f"backend={backend} devices={len(devices)} time_steps={args.time_steps} "
        f"calibration={args.time_steps // 2} payload={args.time_steps // 2}",
        flush=True,
    )
    print(f"beta_candidates={list(BETA_CANDIDATES)}", flush=True)
    print("payload_index_matching=disabled clock_space_nn=enabled", flush=True)

    key = jax.random.PRNGKey(args.seed)
    sanity_histories = sanity_latent_histories(
        jax.random.fold_in(key, 1),
        args.time_steps,
        args.state_dim,
        args.latent_dim,
        args.noise,
    )
    relational_histories = stable_latent_histories(
        jax.random.fold_in(key, 2),
        args.time_steps,
        args.state_dim,
        args.latent_dim,
        args.noise,
    )
    jax.block_until_ready(sanity_histories["x_b"])
    jax.block_until_ready(relational_histories["x_b"])

    mode_results = {}
    print("[RUN] mode=0a", flush=True)
    sanity_result = run_mode(
        jax.random.fold_in(key, 1000),
        sanity_histories,
        "0a",
        args.bootstrap_samples,
    )
    mode_results["0a"] = sanity_result
    metrics = sanity_result["metrics"]
    print(
        f"[RESULT] mode=0a selected_lag={metrics['selected_lag']} "
        f"oracle={metrics['oracle_T_score']:.6f} "
        f"score={metrics['frozen_true_T_payload_score']:.6f} "
        f"alignment_gain={metrics['relational_clock_alignment_gain']:.6f}",
        flush=True,
    )
    print(f"[GATES] mode=0a {sanity_result['gates']}", flush=True)

    sanity_passed = all(
        sanity_result["gates"][name]
        for name in (
            "gate_minus_1_clock_path",
            "debug_gate_oracle",
            "debug_gate_fitted_transition",
        )
    )
    if args.mode in ("0b", "both") and sanity_passed:
        print("[RUN] mode=0b", flush=True)
        relational_result = run_mode(
            jax.random.fold_in(key, 1001),
            relational_histories,
            "0b",
            args.bootstrap_samples,
        )
        mode_results["0b"] = relational_result
        metrics = relational_result["metrics"]
        print(
            f"[RESULT] mode=0b selected_beta={metrics['selected_beta']:.3f} "
            f"selected_lag={metrics['selected_lag']} "
            f"alignment_gain={metrics['relational_clock_alignment_gain']:.6f} "
            f"external_gain={metrics['relational_minus_external_gain']:.6f} "
            f"sincos_gain={metrics['state_coupled_minus_sin_cos_only_gain']:.6f}",
            flush=True,
        )
        print(f"[GATES] mode=0b {relational_result['gates']}", flush=True)
    elif args.mode in ("0b", "both"):
        print("[HALT] 0a debug gates failed; 0b was not executed.", flush=True)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "program": "AQ-PAGE-WOOTTERS-0",
        "backend": backend,
        "device_count": len(devices),
        "config": {
            "mode": args.mode,
            "time_steps": args.time_steps,
            "state_dim": args.state_dim,
            "latent_dim": args.latent_dim,
            "seed": args.seed,
            "noise": args.noise,
            "bootstrap_samples": args.bootstrap_samples,
            "beta_candidates": list(BETA_CANDIDATES),
            "sanity_shift": SANITY_SHIFT,
            "match_window": MATCH_WINDOW,
        },
        "results": mode_results,
    }
    result_path = args.out_dir / "aq_page_wootters0_results.json"
    result_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    summary_lines = [
        "AQ-PAGE-WOOTTERS-0",
        f"backend={backend}",
        f"time_steps={args.time_steps}",
    ]
    for mode, result in mode_results.items():
        metrics = result["metrics"]
        summary_lines.extend(
            (
                f"{mode}.selected_beta={metrics['selected_beta']:.6f}",
                f"{mode}.relational_clock_alignment_gain="
                f"{metrics['relational_clock_alignment_gain']:.6f}",
                f"{mode}.relational_minus_external_gain="
                f"{metrics['relational_minus_external_gain']:.6f}",
                f"{mode}.state_coupled_minus_sin_cos_only_gain="
                f"{metrics['state_coupled_minus_sin_cos_only_gain']:.6f}",
                f"{mode}.bootstrap_ci95="
                f"{metrics['paired_transition_gain_bootstrap_ci95']}",
                f"{mode}.gates={result['gates']}",
            )
        )
    (args.out_dir / "summary.txt").write_text(
        "\n".join(summary_lines) + "\n", encoding="utf-8"
    )
    print(f"[DONE] results={result_path}", flush=True)


if __name__ == "__main__":
    main()
