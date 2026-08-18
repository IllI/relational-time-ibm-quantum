"""Post-hoc, zero-QPU: does IBM-12's archived tomography show the SAME structure
on (A:Sa) at mu=0 as on (A:B) at mu=pi/2?

Reconstructs every pair state from the archived 135 circuits of counts using the
run script's own reconstruction, then asks three things the run did not ask:

  1. Are the two endpoint states the same state?  F(rho_ASa(0), rho_AB(pi/2))
  2. Is either one a d=2 Page-Wootters history state?  (at d=2 that IS a Bell
     pair, which is exactly why the question is partly degenerate)
  3. Does the conditional structure match -- i.e. does conditioning on clock A
     leave the partner in the same two states at both endpoints?
"""
import itertools, json, pathlib, sys
import numpy as np

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "hardware"))

PAULIS = ("X", "Y", "Z")
SETTINGS = ["".join(p) for p in itertools.product(PAULIS, repeat=3)]
P = {"X": np.array([[0, 1], [1, 0]], dtype=complex),
     "Y": np.array([[0, -1j], [1j, 0]], dtype=complex),
     "Z": np.array([[1, 0], [0, -1]], dtype=complex),
     "I": np.eye(2, dtype=complex)}
A, SA, B = 0, 1, 2


def expectation(counts, support):
    tot = sum(counts.values()); acc = 0
    for bits, n in counts.items():
        b = bits.replace(" ", "")
        par = sum(int(b[len(b) - 1 - q]) for q in support) % 2
        acc += (1 - 2 * par) * n
    return float(acc / max(tot, 1))


def pair_density(cbs, qubits):
    q0, q1 = qubits
    rho = np.eye(4, dtype=complex) / 4.0
    for pa in ("I",) + PAULIS:
        for pb in ("I",) + PAULIS:
            if pa == "I" and pb == "I":
                continue
            sup = tuple(q for q, lab in ((q0, pa), (q1, pb)) if lab != "I")
            want = {q0: pa, q1: pb}
            hit = next((s for s in cbs if all(s[q] == want[q] for q in want if want[q] != "I")), None)
            if hit is None:
                continue
            rho = rho + expectation(cbs[hit], sup) * np.kron(P[pb], P[pa]) / 4.0
    w, v = np.linalg.eigh((rho + rho.conj().T) / 2)
    w = np.clip(w, 0, None); w = w / max(w.sum(), 1e-15)
    return (v * w) @ v.conj().T


def concurrence(rho):
    Y = np.array([[0, -1j], [1j, 0]]); YY = np.kron(Y, Y)
    ev = np.sqrt(np.clip(np.linalg.eigvals(rho @ YY @ rho.conj() @ YY).real, 0.0, None))
    ev = np.sort(ev)[::-1]
    return float(max(0.0, ev[0] - ev[1] - ev[2] - ev[3]))


def sqrtm_psd(m):
    w, v = np.linalg.eigh((m + m.conj().T) / 2)
    return (v * np.sqrt(np.clip(w, 0, None))) @ v.conj().T


def fidelity(r, s):
    sr = sqrtm_psd(r)
    return float(np.real(np.trace(sqrtm_psd(sr @ s @ sr))) ** 2)


def trace_distance(r, s):
    return float(0.5 * np.sum(np.abs(np.linalg.eigvalsh((r - s + (r - s).conj().T) / 2))))


def clock_marginal_witness(rho):
    """The programme's d=2 witness on q0 (the clock): TVD from uniform in the
    Fourier (Hadamard) basis, which for one qubit is |Re rho_01| ... using the
    full off-diagonal magnitude as in verify_companion_result."""
    m = rho.reshape(2, 2, 2, 2)             # (q1,q0,q1',q0')
    rc = np.trace(m, axis1=0, axis2=2)      # trace out q1 -> clock q0
    return float(abs(rc[0, 1]))


def conditional_partner(rho, outcome):
    """State of q1 given q0 measured in Z with the given outcome."""
    idx = [2 * b + outcome for b in (0, 1)]
    blk = rho[np.ix_(idx, idx)]
    return blk / max(np.real(np.trace(blk)), 1e-15)


def bloch(rho1):
    return np.array([np.real(np.trace(P[p] @ rho1)) for p in PAULIS])


# ---------------------------------------------------------------- load ----
counts = json.loads((REPO / "results/hardware/ibm12/ibm12_counts.json").read_text(encoding="utf-8"))
res = json.loads((REPO / "results/hardware/ibm12/ibm12_results.json").read_text(encoding="utf-8"))
MUS = res["mus"]
flat = counts["jobs"][0]["counts"]
assert len(flat) == len(MUS) * len(SETTINGS), (len(flat), len(MUS) * len(SETTINGS))

by_mu = {}
k = 0
for mu in MUS:
    by_mu[mu] = {s: flat[k + i] for i, s in enumerate(SETTINGS)}
    k += len(SETTINGS)

print("=" * 78)
print("IBM-12 post-hoc: is the endpoint structure the same on both pairs?")
print("=" * 78)
print(f"\nreconstructed from {len(flat)} archived circuits, job "
      f"{counts['jobs'][0]['job_id']}, no QPU time\n")

rho_ASa = {mu: pair_density(by_mu[mu], (A, SA)) for mu in MUS}
rho_AB = {mu: pair_density(by_mu[mu], (A, B)) for mu in MUS}

print("  mu        C(A:Sa)   C(A:B)     [run reported]")
for i, mu in enumerate(MUS):
    print(f"  {mu:.4f}    {concurrence(rho_ASa[mu]):.4f}    {concurrence(rho_AB[mu]):.4f}"
          f"       {res['measured'][f'{mu:.6f}']['C_ASa']:.4f} / {res['measured'][f'{mu:.6f}']['C_AB']:.4f}")

lo, hi = MUS[0], MUS[-1]
r0, r1 = rho_ASa[lo], rho_AB[hi]

print("\n--- 1. ARE THE TWO ENDPOINT STATES THE SAME STATE? ---")
print(f"  rho_ASa at mu={lo:.4f}   vs   rho_AB at mu={hi:.4f}")
print(f"    fidelity        {fidelity(r0, r1):.4f}")
print(f"    trace distance  {trace_distance(r0, r1):.4f}")
print(f"    concurrence     {concurrence(r0):.4f}  vs  {concurrence(r1):.4f}"
      f"   (differ by {abs(concurrence(r0)-concurrence(r1)):.4f})")

print("\n--- 2. IS EITHER A d=2 PAGE-WOOTTERS HISTORY STATE? ---")
print("  At d=2 the history state (1/sqrt2)(|0>|psi0> + |1>U|psi0>) with")
print("  U = Ry(pi), psi0 = |0> IS the Bell pair |Phi+>. The test is therefore")
print("  partly degenerate -- every maximally entangled 2-qubit state qualifies.")
bell = np.zeros(4, dtype=complex); bell[0] = bell[3] = 1 / np.sqrt(2)
rho_bell = np.outer(bell, bell.conj())
best0 = fidelity(r0, rho_bell)
best1 = fidelity(r1, rho_bell)
print(f"\n    F(rho_ASa(mu=0),    |Phi+>)  = {best0:.4f}")
print(f"    F(rho_AB (mu=pi/2), |Phi+>)  = {best1:.4f}")
print("  (raw computational-basis overlap; no local-basis optimisation, so")
print("   these are lower bounds on the maximally-entangled-class fidelity)")

print("\n--- 3. THE WITNESS ON BOTH ENDPOINTS (cross-check vs IBM-11) ---")
print("  The budget says a maximally entangled pair has a clock-marginal")
print("  witness of ~0. Both endpoints should therefore read near zero.")
print(f"    W(clock A | partner Sa) at mu=0     = {clock_marginal_witness(r0):.4f}")
print(f"    W(clock A | partner B)  at mu=pi/2  = {clock_marginal_witness(r1):.4f}")

print("\n--- 4. CONDITIONAL STRUCTURE: what does clock A leave its partner in? ---")
print("  For a history state, conditioning on clock reading t leaves the")
print("  partner in U^t|psi0>. At d=2 that is two states, one per outcome.\n")
print("     endpoint            outcome 0 Bloch vec        outcome 1 Bloch vec")
for lab, r in ((f"(A:Sa) mu={lo:.2f} ", r0), (f"(A:B)  mu={hi:.2f} ", r1)):
    b0 = bloch(conditional_partner(r, 0)); b1 = bloch(conditional_partner(r, 1))
    print(f"     {lab}  [{b0[0]:+.3f} {b0[1]:+.3f} {b0[2]:+.3f}]"
          f"    [{b1[0]:+.3f} {b1[1]:+.3f} {b1[2]:+.3f}]")
b0a, b1a = bloch(conditional_partner(r0, 0)), bloch(conditional_partner(r0, 1))
b0b, b1b = bloch(conditional_partner(r1, 0)), bloch(conditional_partner(r1, 1))
print(f"\n     |Delta| between the two endpoints:  outcome 0 -> "
      f"{np.linalg.norm(b0a-b0b):.4f}   outcome 1 -> {np.linalg.norm(b1a-b1b):.4f}")
print(f"     angle swept by the partner, endpoint 1: "
      f"{np.degrees(np.arccos(np.clip(np.dot(b0a,b1a)/max(np.linalg.norm(b0a)*np.linalg.norm(b1a),1e-12),-1,1))):.1f} deg")
print(f"     angle swept by the partner, endpoint 2: "
      f"{np.degrees(np.arccos(np.clip(np.dot(b0b,b1b)/max(np.linalg.norm(b0b)*np.linalg.norm(b1b),1e-12),-1,1))):.1f} deg")
print("\n" + "=" * 78)
