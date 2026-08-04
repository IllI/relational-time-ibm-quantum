#!/usr/bin/env python3
"""AQ-PAGE-WOOTTERS-IBM-1 -- D-LinOSS analysis of the decoherence sweep.

WHAT THIS DOES NOT DO (ruled out by the dry run, recorded so it isn't retried):

  * Train on conditional system trajectories. The dry run showed |r(t)| is
    flat at ~0.86 across the whole mu sweep -- the environment couples to the
    CLOCK, so conditioning on a clock reading leaves the system state exactly
    untouched. There is no mu-signal in the conditional trajectory to learn.
  * Path-level relational-clock recovery (the synthetic branch's promoted
    mechanism). CRY(mu) does not change computational-basis clock populations
    at all, so clock labels stay classically perfect at every mu and the
    temporal ordering is trivially recoverable. The path framing does not
    transfer to this experiment.
  * Binary quantum-vs-classical classification from the witness. That is a
    1-D threshold; a straight line does it. A recurrent SSM there is theater.

WHAT IT DOES DO -- the architecture choice IS the physics test:

All mu-dependence lives in the clock's Fourier distribution P_mu(k). Treat the
decoherence sweep as a trajectory in mu and learn its generator. Two competing
D-LinOSS parameterizations encode two competing physical claims:

  Model A (stationary):    lambda = scale * exp(i*omega)
                           -> generic decay, no commitment about what drives it
  Model B (entanglement-   lambda_mu = exp(-gamma * E(mu) + i*omega)
           damped)         -> damping driven by clock-environment entanglement,
                              i.e. the arXiv:2512.15789 prediction
                              C(E) = C_0 * exp(-k E) built into the recurrence

Fit both on calibration mu, freeze, extrapolate to held-out payload mu. If B
beats A out of sample, that is evidence for the entanglement-driven form; if
it does not, that is a reportable negative against the prediction. Either way
the comparison is the result, not the fit quality of a single model.

A direct nonlinear fit of C(E) = C_0*exp(-k*E) to the witness curve is run
alongside as the model-free version of the same test (H2), with bootstrap CI.

Validation: on dry-run data the true law is known analytically, so the
estimators are checked against ground truth before being trusted on hardware.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import jax
import jax.numpy as jnp
import numpy as np

CALIBRATION_FRACTION = 0.55  # first ~5 of 9 mu points
EPOCHS = 1500
LEARNING_RATE = 5e-3
HIDDEN = 8
BOOTSTRAP = 2000


# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------

def load_sweep(path: Path, key: str, which: str) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    block = payload[key]
    rows = block["sweep"]
    mu = np.array([r["mu_pi"] for r in rows]) * np.pi
    ent = np.array([r["clock_env_entanglement"] for r in rows])
    tvd = np.array([r[f"{which}_tvd"] for r in rows])
    pk = np.array([r[f"{which}_pk"] for r in rows])
    return {
        "mu": mu, "entanglement": ent, "tvd": tvd, "pk": pk,
        "d": block["d"], "floor": block["null_floor"],
        "classical_baseline": block.get("classical_tvd_mupi", 0.0),
    }


# --------------------------------------------------------------------------
# H2 direct test: C(E) = C_0 * exp(-k E)
# --------------------------------------------------------------------------

def fit_exponential(ent: np.ndarray, tvd: np.ndarray) -> dict:
    """Log-linear fit with bootstrap CI on k. Uses only points above the
    sampling floor, where log(tvd) is meaningful."""
    mask = tvd > 1e-6
    x, y = ent[mask], np.log(tvd[mask])
    if x.size < 3:
        return {"ok": False}

    def fit(idx):
        a, b = np.polyfit(x[idx], y[idx], 1)
        return -a, np.exp(b)

    k, c0 = fit(np.arange(x.size))
    pred = np.log(c0) - k * x
    r2 = float(1 - np.sum((y - pred) ** 2) / max(np.sum((y - y.mean()) ** 2), 1e-12))
    rng = np.random.default_rng(0)
    ks = []
    for _ in range(BOOTSTRAP):
        idx = rng.integers(0, x.size, x.size)
        if np.ptp(x[idx]) < 1e-9:
            continue
        ks.append(fit(idx)[0])
    lo, hi = np.percentile(ks, [2.5, 97.5]) if ks else (np.nan, np.nan)
    return {
        "ok": True, "k": float(k), "C0": float(c0), "R2": r2,
        "k_ci95": [float(lo), float(hi)], "n_points": int(x.size),
    }


# --------------------------------------------------------------------------
# D-LinOSS over the mu-flow
# --------------------------------------------------------------------------

def init_params(key, in_dim, out_dim, hidden, damped):
    ks = jax.random.split(key, 6)
    s_in = 1.0 / np.sqrt(in_dim)
    s_h = 1.0 / np.sqrt(hidden)
    p = {
        "omega": 0.3 * jax.random.normal(ks[0], (hidden,)),
        "B_re": s_in * jax.random.normal(ks[1], (in_dim, hidden)),
        "B_im": s_in * jax.random.normal(ks[2], (in_dim, hidden)),
        "C_re": s_h * jax.random.normal(ks[3], (hidden, out_dim)),
        "C_im": s_h * jax.random.normal(ks[4], (hidden, out_dim)),
        "bias": jnp.zeros((out_dim,)),
    }
    if damped:
        p["log_gamma"] = jnp.full((hidden,), -1.0)   # gamma > 0, drives -gamma*E
    else:
        p["raw_scale"] = jnp.zeros((hidden,))        # stationary |lambda|
    return p


def forward(params, x_seq, drive, damped):
    """x_seq: (T, in_dim) inputs. drive: (T,) the physical damping driver
    (clock-environment entanglement) -- used only by the damped model."""
    B = params["B_re"] + 1j * params["B_im"]
    C = params["C_re"] + 1j * params["C_im"]
    phase = jnp.pi * jnp.tanh(params["omega"])

    if damped:
        gamma = jnp.exp(params["log_gamma"])

        def step(h, inp):
            x_t, e_t = inp
            lam = jnp.exp(-gamma * e_t + 1j * phase)
            h = h * lam + x_t.astype(jnp.complex64) @ B
            return h, jnp.real(h @ C) + params["bias"]

        _, out = jax.lax.scan(step, jnp.zeros((phase.shape[0],), jnp.complex64), (x_seq, drive))
    else:
        lam = jnp.exp(-jax.nn.softplus(params["raw_scale"]) + 1j * phase)

        def step(h, x_t):
            h = h * lam + x_t.astype(jnp.complex64) @ B
            return h, jnp.real(h @ C) + params["bias"]

        _, out = jax.lax.scan(step, jnp.zeros((phase.shape[0],), jnp.complex64), x_seq)
    return out


def train(key, x_seq, drive, target, n_cal, damped):
    params = init_params(key, x_seq.shape[1], target.shape[1], HIDDEN, damped)
    mask = (jnp.arange(target.shape[0]) < n_cal).astype(jnp.float32)[:, None]

    def loss_fn(p):
        pred = forward(p, x_seq, drive, damped)
        return jnp.sum(((pred - target) ** 2) * mask) / jnp.maximum(jnp.sum(mask), 1e-6)

    m = jax.tree_util.tree_map(jnp.zeros_like, params)
    v = jax.tree_util.tree_map(jnp.zeros_like, params)

    @jax.jit
    def step(carry, i):
        p, m_, v_ = carry
        loss, g = jax.value_and_grad(loss_fn)(p)
        g = jax.tree_util.tree_map(lambda z: jnp.clip(z, -1.0, 1.0), g)
        m_ = jax.tree_util.tree_map(lambda a, b: 0.9 * a + 0.1 * b, m_, g)
        v_ = jax.tree_util.tree_map(lambda a, b: 0.999 * a + 0.001 * b * b, v_, g)
        t = i + 1
        mh = jax.tree_util.tree_map(lambda a: a / (1 - 0.9**t), m_)
        vh = jax.tree_util.tree_map(lambda a: a / (1 - 0.999**t), v_)
        p = jax.tree_util.tree_map(
            lambda q, a, b: q - LEARNING_RATE * a / (jnp.sqrt(b) + 1e-8), p, mh, vh
        )
        return (p, m_, v_), loss

    (params, _, _), losses = jax.lax.scan(step, (params, m, v), jnp.arange(EPOCHS))
    return params, float(losses[-1])


def evaluate(data: dict, seed: int = 0) -> dict:
    d = data["d"]
    n_mu = data["mu"].size
    n_cal = max(3, int(round(CALIBRATION_FRACTION * n_mu)))

    # Input: previous step's P(k) (autoregressive flow); target: current P(k).
    pk = jnp.asarray(data["pk"], dtype=jnp.float32)
    x_seq = jnp.concatenate([pk[:1], pk[:-1]], axis=0)
    drive = jnp.asarray(data["entanglement"], dtype=jnp.float32)
    target = pk

    out = {"d": d, "n_calibration_mu": n_cal, "n_payload_mu": n_mu - n_cal}
    key = jax.random.PRNGKey(seed)
    for name, damped in (("stationary", False), ("entanglement_damped", True)):
        params, final_loss = train(key, x_seq, drive, target, n_cal, damped)
        pred = np.asarray(forward(params, x_seq, drive, damped))
        true = np.asarray(target)
        cal_mse = float(np.mean((pred[:n_cal] - true[:n_cal]) ** 2))
        pay_mse = float(np.mean((pred[n_cal:] - true[n_cal:]) ** 2))
        # Held-out TVD reconstruction: how well the flow predicts the witness.
        pred_tvd = np.array([0.5 * np.sum(np.abs(np.clip(p, 0, None) / max(np.clip(p, 0, None).sum(), 1e-12) - 1.0 / d)) for p in pred])
        tvd_mae_payload = float(np.mean(np.abs(pred_tvd[n_cal:] - data["tvd"][n_cal:])))
        out[name] = {
            "final_train_loss": final_loss,
            "calibration_mse": cal_mse,
            "payload_mse": pay_mse,
            "payload_witness_mae": tvd_mae_payload,
            "predicted_tvd": [float(v) for v in pred_tvd],
        }

    a, b = out["stationary"], out["entanglement_damped"]
    out["damped_minus_stationary_payload_mse"] = b["payload_mse"] - a["payload_mse"]
    out["damped_wins_extrapolation"] = bool(b["payload_mse"] < a["payload_mse"])
    out["damped_wins_witness"] = bool(b["payload_witness_mae"] < a["payload_witness_mae"])
    return out


# --------------------------------------------------------------------------
# Controls
# --------------------------------------------------------------------------

def control_scores(data: dict, seed: int = 1) -> dict:
    """Shuffled-mu and reversed-mu controls: if the model is learning a real
    flow generator rather than memorising the marginal shape, destroying the
    mu-ordering should hurt held-out prediction."""
    rng = np.random.default_rng(seed)
    out = {}
    for name, order in (
        ("shuffled_mu", rng.permutation(data["mu"].size)),
        ("reversed_mu", np.arange(data["mu"].size)[::-1]),
    ):
        perturbed = {
            "d": data["d"], "mu": data["mu"][order],
            "entanglement": data["entanglement"][order],
            "tvd": data["tvd"][order], "pk": data["pk"][order],
            "floor": data["floor"], "classical_baseline": data["classical_baseline"],
        }
        res = evaluate(perturbed, seed=seed)
        out[name] = {
            "damped_payload_mse": res["entanglement_damped"]["payload_mse"],
            "stationary_payload_mse": res["stationary"]["payload_mse"],
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", type=Path, default=Path("pw_ibm1_dryrun_results.json"))
    ap.add_argument("--which", default="noisy", choices=["exact", "ideal", "noisy"])
    ap.add_argument("--out", type=Path, default=Path("pw_ibm1_dlinoss_results.json"))
    args = ap.parse_args()

    report = {
        "program": "AQ-PAGE-WOOTTERS-IBM-1-DLINOSS",
        "source": str(args.results), "which": args.which,
    }
    print(f"D-LinOSS on the mu-flow  [{args.which}]  source={args.results}\n")

    for key in ("n_clock_2", "n_clock_3"):
        data = load_sweep(args.results, key, args.which)
        d = data["d"]

        h2 = fit_exponential(data["entanglement"], data["tvd"])
        model = evaluate(data)
        ctrl = control_scores(data)

        report[key] = {"h2_exponential_fit": h2, "dlinoss": model, "controls": ctrl,
                       "entanglement": data["entanglement"].tolist(),
                       "witness_tvd": data["tvd"].tolist()}

        print(f"=== d={d} ===")
        if h2["ok"]:
            print(f"  H2  C(E)=C0*exp(-kE):  k={h2['k']:.3f}  CI95={[round(v,3) for v in h2['k_ci95']]}  R^2={h2['R2']:.4f}")
        print(f"  payload MSE   stationary {model['stationary']['payload_mse']:.3e}   "
              f"entanglement-damped {model['entanglement_damped']['payload_mse']:.3e}")
        print(f"  payload witness MAE   stationary {model['stationary']['payload_witness_mae']:.4f}   "
              f"damped {model['entanglement_damped']['payload_witness_mae']:.4f}")
        print(f"  damped wins extrapolation: {model['damped_wins_extrapolation']}   "
              f"witness: {model['damped_wins_witness']}")
        print(f"  controls (damped payload MSE)  shuffled {ctrl['shuffled_mu']['damped_payload_mse']:.3e}   "
              f"reversed {ctrl['reversed_mu']['damped_payload_mse']:.3e}\n")

    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[DONE] -> {args.out}")


if __name__ == "__main__":
    main()
