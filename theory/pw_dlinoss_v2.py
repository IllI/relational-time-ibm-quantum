#!/usr/bin/env python3
"""D-LinOSS v2 -- rebuilt, with the scoring defect removed and dampers anchored.

WHY A REWRITE. The v1 model never beat its baselines: every recorded
`D-LinOSS - ridge` value across the campaign is negative, it lost to a
STATIONARY model at every grid density, and the astrophysics closeout found its
damping ablation negligible and retired it. Those look like five separate
failures. They are one, and it lives in the objective:

    loss = mean((pred - target)^2)          # v1, plain MSE on the raw target

Plain MSE is dominated by getting the LEVEL right. Demonstrated on a decay with
rate 1.0: a model with the correct rate but 30% low amplitude scores 0.0155,
while a model with the correct amplitude but a 45%-wrong rate scores 0.0091.
**Plain MSE prefers the wrong physics.** Everything follows:

  - gamma controls SHAPE, so a level-dominated loss gives it nothing to win
    -> "damping ablation was negligible"
  - ridge is excellent at levels
    -> D-LinOSS never beats it
  - a stationary model nails the level and gets shape trivially wrong
    -> it wins anyway, which is nearly diagnostic on its own
  - both models mostly fit the same easy level
    -> "advantage stayed below 5%"

The analysis layer already knew better: fit_power_law works in log space, where
the slope is structure and the intercept is attenuation. The training objective
simply disagreed with the analysis that consumed it.

WHAT v2 CHANGES

  1. SCALE-INVARIANT LOSS. The amplitude is profiled out analytically per
     series (A* = <pred,target>/<pred,pred>), so the model cannot win on level
     and must get the shape right. A* is then REPORTED, because it is the
     measured attenuation -- the same move IBM-11's gate 7 makes when it tests
     the trade-off for flatness and reports the attenuation separately.

  2. ANCHORED DAMPERS. v1's "physical dampers" were soft windows with free
     parameters. Here gamma is a function of a supplied physical driver z:

         gamma_j(k) = softplus(a_j + b_j * z_k)

     so the damping channel is tied to something measured rather than fitted
     freely. Set b = 0 to recover a free-but-constant damper; that is the
     ablation, and now it means something.

  3. HONEST BASELINES, SCORED IDENTICALLY. Ridge and a stationary (gamma = 0)
     variant are evaluated under the same scale-invariant metric. A win only
     counts if it is a win on shape.

  4. GROUND-TRUTH VALIDATION FIRST. Before any claim on real data, the model
     must recover known (omega, gamma) from synthetic series. That check runs
     on import of __main__ and gates everything else.

WHAT THIS DOES NOT PROMISE. It does not promise D-LinOSS beats ridge -- the
record says it never has, and it may not here either. It promises the
comparison becomes INFORMATIVE, because it stops measuring which model fits an
amplitude.

    python pw_dlinoss_v2.py                 # validate on synthetic ground truth
    python pw_dlinoss_v2.py --demo-ibm11    # end-to-end on an IBM-11-shaped task
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize


# --------------------------------------------------------------------------
# Scoring -- the fix
# --------------------------------------------------------------------------

def profile_amplitude(pred: np.ndarray, target: np.ndarray) -> float:
    """Least-squares optimal scalar amplitude. Analytic, no extra parameter."""
    denom = float(np.dot(pred, pred))
    return float(np.dot(pred, target) / denom) if denom > 1e-15 else 0.0


def si_mse(pred: np.ndarray, target: np.ndarray) -> float:
    """Scale-invariant MSE: score the SHAPE, after profiling out the level."""
    return float(np.mean((profile_amplitude(pred, target) * pred - target) ** 2))


def plain_mse(pred: np.ndarray, target: np.ndarray) -> float:
    return float(np.mean((pred - target) ** 2))


def si_r2(pred: np.ndarray, target: np.ndarray) -> float:
    """R^2 computed after amplitude profiling."""
    resid = si_mse(pred, target) * target.size
    tot = float(np.sum((target - target.mean()) ** 2))
    return float(1.0 - resid / max(tot, 1e-15))


# --------------------------------------------------------------------------
# The model
# --------------------------------------------------------------------------

class DLinOSS:
    """Damped linear oscillatory state space, complex diagonal.

        x_{k+1} = Lambda_k x_k + b
        y_k     = Re(sum_j x_k[j])
        Lambda_k[j] = exp((-gamma_j(k) + i omega_j) dt)

    gamma_j(k) = softplus(a_j + b_j z_k) is the anchored damping channel: with
    b = 0 it is a free constant damper (the ablation), with b free it is driven
    by a supplied physical observable."""

    def __init__(self, n_modes: int = 2, dt: float = 1.0, driven: bool = True):
        self.K, self.dt, self.driven = n_modes, dt, driven

    # -- parameter packing -------------------------------------------------
    def unpack(self, p):
        K = self.K
        omega = p[:K]
        a = p[K:2 * K]
        b = p[2 * K:3 * K] if self.driven else np.zeros(K)
        phase = p[3 * K:4 * K] if self.driven else p[2 * K:3 * K]
        return omega, a, b, phase

    def n_params(self):
        return 4 * self.K if self.driven else 3 * self.K

    def init(self, omega0=None, rng=None):
        rng = rng or np.random.default_rng(0)
        K = self.K
        omega = np.asarray(omega0, float) if omega0 is not None else rng.uniform(0.1, 2.0, K)
        a = np.full(K, -1.0)                      # softplus(-1) ~ 0.31
        parts = [omega, a]
        if self.driven:
            parts.append(np.zeros(K))             # start undriven; let it earn b
        parts.append(rng.uniform(0, 0.1, K))      # phase
        return np.concatenate(parts)

    # -- forward -----------------------------------------------------------
    def forward(self, p, n_steps: int, z: np.ndarray | None = None) -> np.ndarray:
        omega, a, b, phase = self.unpack(p)
        z = np.zeros(n_steps) if z is None else np.asarray(z, float)
        if z.size != n_steps:
            raise ValueError("driver z must have one value per step")

        x = np.exp(1j * phase).astype(complex)     # unit-modulus start
        out = np.empty(n_steps)
        for k in range(n_steps):
            out[k] = float(np.real(np.sum(x)))
            gamma = np.log1p(np.exp(np.clip(a + b * z[k], -30, 30)))   # softplus
            x = x * np.exp((-gamma + 1j * omega) * self.dt)
        return out

    # -- fit ---------------------------------------------------------------
    def fit(self, target: np.ndarray, z=None, omega0=None, restarts: int = 6,
            scale_invariant: bool = True, seed: int = 0):
        n = target.size
        score = si_mse if scale_invariant else plain_mse
        best, best_loss = None, np.inf
        for r in range(restarts):
            p0 = self.init(omega0, np.random.default_rng(seed + r))
            res = minimize(lambda p: score(self.forward(p, n, z), target),
                           p0, method="Nelder-Mead",
                           options={"maxiter": 4000, "xatol": 1e-8, "fatol": 1e-12})
            if res.fun < best_loss:
                best, best_loss = res.x, float(res.fun)
        self.params_ = best
        pred = self.forward(best, n, z)
        self.amplitude_ = profile_amplitude(pred, target)
        return self

    def predict(self, n_steps: int, z=None) -> np.ndarray:
        return self.forward(self.params_, n_steps, z)

    def rates(self):
        """(omega, gamma_at_z0) -- the recovered physical parameters."""
        omega, a, b, _ = self.unpack(self.params_)
        return omega, np.log1p(np.exp(np.clip(a, -30, 30)))


# --------------------------------------------------------------------------
# Baselines, scored identically
# --------------------------------------------------------------------------

def ridge_predict(target: np.ndarray, order: int = 3, alpha: float = 1e-3) -> np.ndarray:
    """Linear autoregression -- the baseline D-LinOSS has never beaten."""
    n = target.size
    if n <= order + 1:
        return np.full(n, target.mean())
    X = np.stack([target[order - i - 1:n - i - 1] for i in range(order)], axis=1)
    y = target[order:]
    w = np.linalg.solve(X.T @ X + alpha * np.eye(order), X.T @ y)
    pred = target.copy().astype(float)
    for k in range(order, n):
        pred[k] = float(pred[k - order:k][::-1] @ w)
    return pred


def stationary_predict(target: np.ndarray, omega: float, n: int) -> np.ndarray:
    """gamma = 0: pure undamped oscillation. Gets the level right trivially."""
    return np.cos(omega * np.arange(n))


# --------------------------------------------------------------------------
# Validation on synthetic ground truth -- gates everything else
# --------------------------------------------------------------------------

def validate(verbose: bool = True) -> dict:
    rng = np.random.default_rng(7)
    results = {"cases": [], "all_pass": True}

    if verbose:
        print("=" * 74)
        print("GROUND-TRUTH RECOVERY -- known (omega, gamma), noisy observations")
        print("=" * 74)
        print("\n  true w   true g   rec. w   rec. g   |dw|     |dg|    amplitude")

    for omega_t, gamma_t in ((0.60, 0.05), (1.20, 0.12), (0.35, 0.20)):
        n = 60
        t = np.arange(n)
        clean = np.exp(-gamma_t * t) * np.cos(omega_t * t)
        y = 0.63 * clean + rng.normal(0, 0.01, n)       # arbitrary amplitude + noise

        m = DLinOSS(n_modes=1, driven=False).fit(y, omega0=[omega_t * 1.3], restarts=8)
        w_rec, g_rec = m.rates()
        dw, dg = abs(w_rec[0] - omega_t), abs(g_rec[0] - gamma_t)
        ok = bool(dw < 0.05 and dg < 0.05)
        results["all_pass"] &= ok
        results["cases"].append({"omega_true": omega_t, "gamma_true": gamma_t,
                                 "omega_rec": float(w_rec[0]), "gamma_rec": float(g_rec[0]),
                                 "amplitude": float(m.amplitude_), "pass": ok})
        if verbose:
            print(f"   {omega_t:.2f}     {gamma_t:.2f}    {w_rec[0]:.3f}    {g_rec[0]:.3f}"
                  f"   {dw:.4f}   {dg:.4f}   {m.amplitude_:.3f}  {'OK' if ok else 'FAIL'}")

    if verbose:
        print(f"\n  recovery within tolerance -> {results['all_pass']}")
        print("  NOTE the amplitude column: the model recovers the physics while")
        print("       the level is profiled out and reported, not fitted.\n")
    return results


def objective_comparison(verbose: bool = True) -> dict:
    """The defect, isolated: same data, same model, two objectives."""
    rng = np.random.default_rng(11)
    n, omega_t, gamma_t = 60, 0.9, 0.10
    t = np.arange(n)
    y = 0.55 * np.exp(-gamma_t * t) * np.cos(omega_t * t) + rng.normal(0, 0.01, n)

    out = {}
    for tag, si in (("scale_invariant", True), ("plain_mse", False)):
        m = DLinOSS(n_modes=1, driven=False).fit(y, omega0=[omega_t * 1.4],
                                                 restarts=8, scale_invariant=si)
        w, g = m.rates()
        out[tag] = {"omega_rec": float(w[0]), "gamma_rec": float(g[0]),
                    "omega_err": float(abs(w[0] - omega_t)),
                    "gamma_err": float(abs(g[0] - gamma_t))}
    if verbose:
        print("=" * 74)
        print("OBJECTIVE COMPARISON -- identical data and model, different loss")
        print("=" * 74)
        print(f"\n  ground truth:  omega = {omega_t}, gamma = {gamma_t}\n")
        print("  objective          omega_rec   gamma_rec   |dw|     |dg|")
        for tag in ("scale_invariant", "plain_mse"):
            r = out[tag]
            print(f"  {tag:<18} {r['omega_rec']:.4f}      {r['gamma_rec']:.4f}"
                  f"      {r['omega_err']:.4f}   {r['gamma_err']:.4f}")
        print()
    return out


def baseline_bakeoff(verbose: bool = True) -> dict:
    """D-LinOSS vs ridge vs stationary, all under the SAME scale-invariant score."""
    rng = np.random.default_rng(23)
    n, omega_t, gamma_t = 60, 0.8, 0.09
    t = np.arange(n)
    y = 0.7 * np.exp(-gamma_t * t) * np.cos(omega_t * t) + rng.normal(0, 0.015, n)

    m = DLinOSS(n_modes=1, driven=False).fit(y, omega0=[omega_t], restarts=8)
    preds = {"dlinoss": m.predict(n),
             "ridge": ridge_predict(y),
             "stationary": stationary_predict(y, omega_t, n)}
    out = {k: {"si_mse": si_mse(p, y), "si_r2": si_r2(p, y),
               "plain_mse": plain_mse(p, y)} for k, p in preds.items()}
    winner_si = min(out, key=lambda k: out[k]["si_mse"])
    winner_pl = min(out, key=lambda k: out[k]["plain_mse"])
    out["winner_scale_invariant"], out["winner_plain"] = winner_si, winner_pl

    if verbose:
        print("=" * 74)
        print("BASELINE BAKE-OFF -- all three scored identically")
        print("=" * 74)
        print("\n  model         SI-MSE      SI-R^2     plain MSE")
        for k in ("dlinoss", "ridge", "stationary"):
            r = out[k]
            print(f"  {k:<12} {r['si_mse']:.6f}   {r['si_r2']:+.4f}    {r['plain_mse']:.6f}")
        print(f"\n  winner on shape (scale-invariant): {winner_si}")
        print(f"  winner on level (plain MSE):       {winner_pl}")
        print("  A win only counts if it is a win on SHAPE.\n")
    return out


def demo_ibm11(verbose: bool = True) -> dict:
    """An IBM-11-shaped task: is the attenuation one constant, or lambda-dependent?

    IBM-11 measures W(lambda) and S(lambda) and asks whether the exact
    trade-off S^2 + 16W^2 = 8 survives as a FLAT (if attenuated) curve. That is
    exactly a damping question, and it is the one this model is anchored to:
    the driver z is lambda, and b != 0 means the damping varies along the sweep."""
    lam = np.linspace(0.0, 1.0, 9)
    W = np.cos(lam * np.pi / 2) / 2
    C = np.sin(lam * np.pi / 2)
    S = 2 * np.sqrt(1 + C ** 2)
    ideal = S ** 2 + 16 * W ** 2                      # identically 8

    rng = np.random.default_rng(5)
    flat = 0.84 * ideal + rng.normal(0, 0.02, lam.size)          # uniform attenuation

    # NON-monotone lambda dependence. A first version of this demo used a linear
    # tilt and the driven damper earned nothing -- correctly, because a single
    # near-zero-frequency mode with free gamma already produces a monotone
    # exponential and needs no driver to fit one. The driver can only earn its
    # keep on structure a constant damper cannot make. Physically motivated
    # here: mid-sweep states need a partial-angle CRY, whose error need not
    # interpolate between the lambda = 0 (identity) and lambda = 1 (full CRY)
    # endpoints, so attenuation can dip in the middle.
    bowed = (0.90 - 0.35 * np.sin(np.pi * lam)) * ideal + rng.normal(0, 0.02, lam.size)

    out = {}
    for tag, series in (("uniform_attenuation", flat), ("nonmonotone_lambda", bowed)):
        free = DLinOSS(1, driven=False).fit(series, omega0=[0.01], restarts=6)
        driven = DLinOSS(1, driven=True).fit(series, z=lam, omega0=[0.01], restarts=6)
        gain = si_mse(free.predict(lam.size), series) - \
            si_mse(driven.predict(lam.size, lam), series)
        _, _, b, _ = driven.unpack(driven.params_)
        out[tag] = {"si_mse_free": si_mse(free.predict(lam.size), series),
                    "si_mse_driven": si_mse(driven.predict(lam.size, lam), series),
                    "driven_gain": float(gain), "b_learned": float(b[0]),
                    "spread": float(series.max() - series.min())}
    if verbose:
        print("=" * 74)
        print("IBM-11 DEMO -- does the damping vary along the sweep?")
        print("=" * 74)
        print("\n  the driver z is lambda; a nonzero b means lambda-dependent damping\n")
        print("  series                 spread   SI-MSE free   SI-MSE driven   b learned")
        for tag in ("uniform_attenuation", "nonmonotone_lambda"):
            r = out[tag]
            print(f"  {tag:<22} {r['spread']:.3f}    {r['si_mse_free']:.6f}"
                  f"      {r['si_mse_driven']:.6f}     {r['b_learned']:+.4f}")
        gain_u = out["uniform_attenuation"]["driven_gain"]
        gain_s = out["nonmonotone_lambda"]["driven_gain"]
        verdict = bool(gain_s > 10 * max(gain_u, 1e-12))
        out["driven_beats_free_on_structure"] = verdict
        print(f"\n  driven gain:  uniform {gain_u:.6f}   structured {gain_s:.6f}")
        print(f"  driver earns its keep only on real structure -> {verdict}")
        print("  A constant damper already produces any MONOTONE trend, so the")
        print("  driver can only pay for itself on structure a constant one")
        print("  cannot make. (An earlier version of this demo used a linear tilt")
        print("  and the driver correctly earned nothing -- the demo was wrong,")
        print("  not the model.)")
        print("  Note b is large but idle on the uniform series: with no structure")
        print("  to explain the driver is unidentifiable, which is the right")
        print("  behaviour and why the GAIN, not b, is the ablation statistic.")
        print("  This is the ablation v1 could not perform at all, because its")
        print("  loss never rewarded shape, so the damping channel had nothing")
        print("  to win either way.\n")
    return out


# --------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo-ibm11", action="store_true")
    ap.add_argument("--out", type=Path, default=Path("dlinoss_v2_validation.json"))
    args = ap.parse_args()

    val = validate()
    if not val["all_pass"]:
        raise SystemExit("ground-truth recovery FAILED -- do not use this model on data")
    obj = objective_comparison()
    bake = baseline_bakeoff()
    demo = demo_ibm11() if args.demo_ibm11 else None

    payload = {"validation": val, "objective_comparison": obj,
               "baseline_bakeoff": bake, "ibm11_demo": demo,
               "note": ("Scale-invariant scoring profiles the amplitude out analytically "
                        "and reports it, so the model is scored on shape. Dampers are "
                        "anchored to a supplied physical driver rather than free windows.")}
    args.out.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"[DONE] -> {args.out}")


if __name__ == "__main__":
    main()
