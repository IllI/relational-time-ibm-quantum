#!/usr/bin/env python3
"""Setting-wise multinomial bootstrap of the fidelity witness. No QPU time.

WHY. IBM-4 and IBM-10 both report a fidelity point estimate against the derived
separable bound lambda_max = 1/2, and both deliberately DECLINE to quote an
N-sigma significance. The reason is real: F = (1/2^n) sum_P c_P <P>, and Paulis
recovered from the SAME measurement setting share counts, so they are
correlated. The propagated sigma used to set the pre-registered 3-sigma gate
treats them as independent, which is fine for a bar far below the observed
margin but not fine for a published significance.

The fix costs no hardware. Resample each setting's counts from its own observed
multinomial, recompute F end to end on every resample, and read the confidence
interval off the resulting distribution. Correlations within a setting are
preserved automatically because the whole setting is resampled as one object.

The claim this supports is the publishable form:

    F = 0.9014,  95% CI [lo, hi],  lower bound > 1/2

which is a certification rather than a point estimate.

Requires the raw counts archived by pw_ibm_fetch_counts.py.

Usage:
    python pw_ibm_fidelity_bootstrap.py --run ibm10
    python pw_ibm_fidelity_bootstrap.py --run ibm10 --resamples 20000
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from pw_ibm4_fidelity import expectation


def covered_by(p: str, s: str) -> bool:
    return all(pi == "I" or pi == si for pi, si in zip(p, s))


def fidelity_from(terms: dict[str, float], settings: list[str],
                  counts_by_setting: dict[str, dict[str, int]], n: int) -> float:
    total = 0.0
    for label, c in terms.items():
        if set(label) == {"I"}:
            total += c
            continue
        for s in settings:
            if covered_by(label, s):
                total += c * expectation(counts_by_setting[s], label, n)
                break
    return total / (2**n)


def resample_counts(counts: dict[str, int], rng: np.random.Generator) -> dict[str, int]:
    """Draw a new count dict from the observed multinomial for ONE setting.

    Resampling the whole setting at once is what preserves the correlations
    between Paulis read from it -- the thing the independence estimate misses."""
    keys = list(counts)
    probs = np.array([counts[k] for k in keys], dtype=float)
    n_shots = int(probs.sum())
    probs /= probs.sum()
    draw = rng.multinomial(n_shots, probs)
    return {k: int(v) for k, v in zip(keys, draw)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="ibm10", help="ibm10 or ibm4")
    ap.add_argument("--dir", type=Path, default=None)
    ap.add_argument("--resamples", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=20260810)
    args = ap.parse_args()

    d = args.dir or Path(f"results_{args.run}_ibm_marrakesh")
    res_path = d / f"{args.run}_results.json"
    cnt_path = d / f"{args.run}_counts.json"
    if not cnt_path.exists():
        raise SystemExit(
            f"{cnt_path} not found. The raw counts were never archived for this run.\n"
            "Retrieve them from IBM first (no QPU cost, but only while the account lives):\n"
            f"  python pw_ibm_fetch_counts.py --results {res_path}"
        )

    results = json.loads(res_path.read_text(encoding="utf-8"))
    archive = json.loads(cnt_path.read_text(encoding="utf-8"))
    settings = results["settings"]
    terms = results["pauli_terms"]
    n = results["n_clock"] + 1
    lam = results["lambda_max"]

    # Fidelity circuits were submitted first, one per setting, in `settings` order.
    flat = [c for j in archive["jobs"] for c in j.get("counts", [])]
    if len(flat) < len(settings):
        raise SystemExit(f"expected >= {len(settings)} circuits, found {len(flat)}")
    by_setting = {s: flat[i] for i, s in enumerate(settings)}

    point = fidelity_from(terms, settings, by_setting, n)
    print(f"run={args.run}  d={results['d']}  settings={len(settings)}  "
          f"terms={len(terms)}  bound lambda_max={lam}")
    print(f"  recomputed F from archived counts : {point:.6f}")
    print(f"  F as recorded in results JSON     : {results['fidelity']:.6f}")
    if abs(point - results["fidelity"]) > 1e-9:
        print("  [WARN] recomputation does not match the archived value -- "
              "check the circuit-order assumption before trusting the CI")

    rng = np.random.default_rng(args.seed)
    draws = np.empty(args.resamples)
    for b in range(args.resamples):
        rs = {s: resample_counts(by_setting[s], rng) for s in settings}
        draws[b] = fidelity_from(terms, settings, rs, n)

    lo, hi = np.percentile(draws, [2.5, 97.5])
    lo99, hi99 = np.percentile(draws, [0.5, 99.5])
    frac_above = float(np.mean(draws > lam))
    print(f"\n  bootstrap ({args.resamples} setting-wise multinomial resamples)")
    print(f"    mean {draws.mean():.6f}   std {draws.std(ddof=1):.6f}")
    print(f"    95% CI [{lo:.6f}, {hi:.6f}]")
    print(f"    99% CI [{lo99:.6f}, {hi99:.6f}]")
    print(f"    fraction of resamples above lambda_max: {frac_above:.6f}")
    certified = bool(lo > lam)
    print(f"\n  LOWER 95% BOUND ABOVE {lam}: {certified}")
    print(f"  publishable form: F = {point:.4f}, 95% CI [{lo:.4f}, {hi:.4f}]")

    out = {
        "run": args.run, "d": results["d"], "lambda_max": lam,
        "F_point_recomputed": point, "F_recorded": results["fidelity"],
        "resamples": args.resamples, "seed": args.seed,
        "bootstrap_mean": float(draws.mean()), "bootstrap_std": float(draws.std(ddof=1)),
        "ci95": [float(lo), float(hi)], "ci99": [float(lo99), float(hi99)],
        "fraction_above_bound": frac_above,
        "lower_95_above_bound": certified,
        "method": ("Setting-wise multinomial resampling of the archived raw counts. "
                   "Each measurement setting is resampled as a whole object, so "
                   "correlations between Paulis recovered from the same setting are "
                   "preserved -- the correlation the propagated independence estimate "
                   "ignores."),
    }
    (d / f"{args.run}_fidelity_bootstrap.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")
    print(f"  -> {d / f'{args.run}_fidelity_bootstrap.json'}")


if __name__ == "__main__":
    main()
