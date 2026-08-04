#!/usr/bin/env python3
"""AQ-PAGE-WOOTTERS-DLINOSS-PATH-OBSERVABILITY-0.

Observability-only path gate for the Page-Wootters/D-LinOSS branch. The prior
pointwise gate showed that roughly one fifth of windows can be locally
exchangeable with shuffled/severed same-distribution controls. This run asks
whether the true Alice/Bob correspondence still wins as a coherent monotone
history path.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import jax
import jax.numpy as jnp
import numpy as np

import program_aq_page_wootters_global_causal_memory0 as gm


DEFAULT_ARMS = (
    "A6_full_causal_clock_current",
    "A10_full_global_causal_memory",
)

PATH_NULLS = (
    "wrong_lag_path",
    "shuffled_path",
    "severed_path",
    "cross_seed_path",
    "same_stats_permuted_path",
    "block_shuffled_path",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--time-steps", type=int, default=128)
    parser.add_argument("--state-dim", type=int, default=64)
    parser.add_argument("--latent-dim", type=int, default=8)
    parser.add_argument("--true-lag", type=int, default=5)
    parser.add_argument("--seeds", nargs="*", type=int, default=[11, 12, 13, 14, 15])
    parser.add_argument("--noise-values", nargs="*", type=float, default=[0.0, 0.01, 0.02, 0.03])
    parser.add_argument("--generator-arms", nargs="*", default=list(DEFAULT_ARMS))
    parser.add_argument("--out-dir", type=Path, default=Path("aq_page_wootters_path_observability0"))
    parser.add_argument("--require-tpu", action="store_true")
    args = parser.parse_args()
    unknown = sorted(set(args.generator_arms) - set(gm.GENERATOR_ARMS))
    if unknown:
        parser.error(f"unknown --generator-arms values: {unknown}")
    return args


def block_shuffle(features: jax.Array, key: jax.Array, block_size: int = 8) -> jax.Array:
    n = features.shape[0]
    pad = (-n) % block_size
    padded = jnp.pad(features, ((0, pad), (0, 0)), mode="edge")
    blocks = padded.reshape((-1, block_size, features.shape[1]))
    order = jax.random.permutation(key, blocks.shape[0])
    return blocks[order].reshape((-1, features.shape[1]))[:n]


def lag_shift(features: jax.Array, shift: int) -> jax.Array:
    if shift <= 0:
        return features
    head = jnp.repeat(features[:1], shift, axis=0)
    return jnp.concatenate((head, features[:-shift]), axis=0)


def path_cost(
    alice_features: jax.Array,
    bob_features: jax.Array,
    query_indices: jax.Array,
    *,
    lam_velocity: float = 0.60,
    lam_accel: float = 0.12,
    max_lag: int = 18,
) -> tuple[float, list[int]]:
    """Monotone dynamic-programming path cost over a Bob feature stream."""
    query = np.asarray(alice_features[query_indices])
    bob = np.asarray(bob_features)
    qn = query.shape[0]
    bn = bob.shape[0]
    expected = np.asarray(query_indices, dtype=np.int32)
    allowed = []
    costs = []
    for row, idx in enumerate(expected):
        # Leave enough tail room for a monotone path and keep a lag prior.
        remaining = qn - row - 1
        lo = max(0, int(idx) - max_lag)
        hi = min(bn - remaining, int(idx) + max_lag + 1)
        if hi <= lo:
            hi = min(bn, lo + 1)
        candidates = np.arange(lo, hi, dtype=np.int32)
        allowed.append(candidates)
        diff = bob[candidates] - query[row][None, :]
        costs.append(np.sum(diff * diff, axis=1))

    inf = 1e30
    prev = costs[0].astype(np.float64)
    parents: list[np.ndarray] = [np.full_like(allowed[0], -1, dtype=np.int32)]
    prev_step = np.zeros_like(prev)
    for row in range(1, qn):
        cur = np.full_like(costs[row], inf, dtype=np.float64)
        parent = np.full_like(allowed[row], -1, dtype=np.int32)
        cur_step = np.zeros_like(cur)
        for j_pos, j_val in enumerate(allowed[row]):
            valid = allowed[row - 1] <= j_val
            if not np.any(valid):
                continue
            prev_positions = np.flatnonzero(valid)
            step = j_val - allowed[row - 1][prev_positions]
            velocity_penalty = lam_velocity * np.abs(step - 1.0)
            accel_penalty = lam_accel * np.abs(step - prev_step[prev_positions])
            candidate_cost = prev[prev_positions] + velocity_penalty + accel_penalty
            best_local = int(np.argmin(candidate_cost))
            best_pos = int(prev_positions[best_local])
            cur[j_pos] = costs[row][j_pos] + candidate_cost[best_local]
            parent[j_pos] = best_pos
            cur_step[j_pos] = step[best_local]
        prev = cur
        prev_step = cur_step
        parents.append(parent)

    end_pos = int(np.argmin(prev))
    best_cost = float(prev[end_pos])
    path = [int(allowed[-1][end_pos])]
    pos = end_pos
    for row in range(qn - 1, 0, -1):
        pos = int(parents[row][pos])
        path.append(int(allowed[row - 1][pos]))
    path.reverse()
    return best_cost, path


def fixed_path_cost(
    alice_features: jax.Array,
    bob_features: jax.Array,
    query_indices: jax.Array,
    matches: jax.Array,
) -> float:
    query = alice_features[query_indices]
    distance = jnp.sum((query - bob_features[matches]) ** 2, axis=1)
    return float(jnp.sum(distance))


def segment_positive_fraction(
    alice: jax.Array,
    bob: jax.Array,
    null_streams: dict[str, jax.Array],
    query_indices: jax.Array,
    oracle_matches: jax.Array,
    segment: int,
) -> float:
    total = 0
    positive = 0
    for start in range(0, int(query_indices.shape[0]) - segment + 1, segment):
        q = query_indices[start : start + segment]
        m = oracle_matches[start : start + segment]
        true_cost = fixed_path_cost(alice, bob, q, m)
        best_null = min(path_cost(alice, stream, q)[0] for stream in null_streams.values())
        positive += int(best_null > true_cost)
        total += 1
    return float(positive / max(total, 1))


def path_metrics(
    alice: jax.Array,
    bob: jax.Array,
    null_streams: dict[str, jax.Array],
    query_indices: jax.Array,
    oracle_matches: jax.Array,
) -> dict:
    true_cost = fixed_path_cost(alice, bob, query_indices, oracle_matches)
    null_costs = {}
    null_paths = {}
    for name, stream in null_streams.items():
        cost, path = path_cost(alice, stream, query_indices)
        null_costs[name] = cost
        null_paths[name] = path
    ordered = sorted(null_costs.items(), key=lambda item: item[1])
    best_name, best_cost = ordered[0]
    all_costs = [true_cost] + [cost for _, cost in ordered]
    path_rank = 1 + sum(cost < true_cost for _, cost in ordered)
    payload_len = int(query_indices.shape[0])
    return {
        "true_path_cost": float(true_cost),
        "best_null_path_cost": float(best_cost),
        "path_margin": float(best_cost - true_cost),
        "path_margin_per_step": float((best_cost - true_cost) / max(payload_len, 1)),
        "path_positive_margin": bool(best_cost > true_cost),
        "best_null_type": best_name,
        "path_rank": int(path_rank),
        "segment_margin_w8": segment_positive_fraction(alice, bob, null_streams, query_indices, oracle_matches, 8),
        "segment_margin_w16": segment_positive_fraction(alice, bob, null_streams, query_indices, oracle_matches, 16),
        "segment_margin_w32": segment_positive_fraction(alice, bob, null_streams, query_indices, oracle_matches, 32),
        "null_path_costs": null_costs,
        "path_costs_sorted": sorted(all_costs),
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
    key = jax.random.PRNGKey(seed)
    calibration_steps = time_steps // 2
    histories = gm.physics_priors_histories(
        key, time_steps, state_dim, latent_dim, true_lag, noise, generator_arm
    )
    calibration_query = jnp.arange(0, calibration_steps - 1)
    payload_query = jnp.arange(calibration_steps, time_steps - 1)
    oracle_calibration = gm.intrinsic_oracle_path(histories, calibration_query)
    oracle_payload = gm.intrinsic_oracle_path(histories, payload_query)

    feature_results = {}
    for index, spec in enumerate(gm.FEATURE_SPECS):
        alice, bob, nulls = gm.feature_bundle(
            spec,
            histories,
            jax.random.fold_in(key, 200 + index),
            calibration_steps,
            calibration_query,
            oracle_calibration,
        )
        block = block_shuffle(bob, jax.random.fold_in(key, 900 + index))
        wrong_lag = lag_shift(bob, true_lag + 4)
        path_nulls = {
            "wrong_lag_path": wrong_lag,
            "shuffled_path": nulls["shuffled_clock"],
            "severed_path": nulls["severed_clock"],
            "cross_seed_path": nulls["cross_seed_clock"],
            "same_stats_permuted_path": nulls["causal_stats_permuted_clock"],
            "block_shuffled_path": block,
        }
        point_payload = gm.observability_metrics(
            alice, bob, nulls, payload_query, oracle_payload, window=12
        )
        path_payload = path_metrics(alice, bob, path_nulls, payload_query, oracle_payload)
        feature_results[spec["name"]] = {
            "spec": spec,
            "point_payload": point_payload,
            "path_payload": path_payload,
        }
    best_name = max(
        feature_results,
        key=lambda name: (
            feature_results[name]["path_payload"]["path_positive_margin"],
            -feature_results[name]["path_payload"]["path_rank"],
            feature_results[name]["path_payload"]["path_margin_per_step"],
        ),
    )
    return {
        "config": {"seed": seed, "noise": noise, "generator_arm": generator_arm},
        "best_feature": best_name,
        "features": feature_results,
    }


def aggregate(results: list[dict]) -> dict:
    grouped: dict[str, dict[str, list[dict]]] = {}
    for result in results:
        arm = result["config"]["generator_arm"]
        noise = f"{result['config']['noise']:.2f}"
        grouped.setdefault(arm, {}).setdefault(noise, []).append(result)

    summary = {}
    for arm, noise_map in grouped.items():
        summary[arm] = {}
        for noise, rows in noise_map.items():
            best_rows = [row["features"][row["best_feature"]] for row in rows]
            margins = [row["path_payload"]["path_margin_per_step"] for row in best_rows]
            ranks = [row["path_payload"]["path_rank"] for row in best_rows]
            seg16 = [row["path_payload"]["segment_margin_w16"] for row in best_rows]
            point = [row["point_payload"]["fraction_positive_margin"] for row in best_rows]
            best_null_counts = {}
            for row in best_rows:
                name = row["path_payload"]["best_null_type"]
                best_null_counts[name] = best_null_counts.get(name, 0) + 1
            summary[arm][noise] = {
                "median_path_margin_per_step": float(np.median(margins)),
                "min_path_margin_per_step": float(np.min(margins)),
                "path_positive_rate": float(np.mean([value > 0 for value in margins])),
                "median_path_rank": float(np.median(ranks)),
                "path_rank1_rate": float(np.mean([rank == 1 for rank in ranks])),
                "median_segment_margin_w16": float(np.median(seg16)),
                "median_pointwise_positive_margin": float(np.median(point)),
                "best_null_counts": best_null_counts,
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
        f"AQ-PAGE-WOOTTERS-DLINOSS-PATH-OBSERVABILITY-0 backend={backend} "
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
        metrics = result["features"][result["best_feature"]]["path_payload"]
        point = result["features"][result["best_feature"]]["point_payload"]
        print(
            f"[RESULT] arm={arm} noise={noise:.2f} seed={seed} "
            f"best={result['best_feature']} "
            f"path_margin_step={metrics['path_margin_per_step']:.6f} "
            f"path_rank={metrics['path_rank']} "
            f"seg16={metrics['segment_margin_w16']:.3f} "
            f"point_pos={point['fraction_positive_margin']:.3f} "
            f"best_null={metrics['best_null_type']}",
            flush=True,
        )

    payload = {
        "program": "AQ-PAGE-WOOTTERS-DLINOSS-PATH-OBSERVABILITY-0",
        "backend": backend,
        "config": {
            "time_steps": args.time_steps,
            "state_dim": args.state_dim,
            "latent_dim": args.latent_dim,
            "true_lag": args.true_lag,
            "generator_arms": args.generator_arms,
            "path_nulls": PATH_NULLS,
            "feature_specs": gm.FEATURE_SPECS,
        },
        "aggregate": aggregate(results),
        "results": results,
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    output = args.out_dir / "path_observability0_results.json"
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[DONE] results={output}", flush=True)


if __name__ == "__main__":
    main()
