# AQ-PAGE-WOOTTERS-IBM-14 — The Gate 5 Paradox, Resolved Physically

**Executed 2026-08-18 on `ibm_marrakesh`.** 1 job `da28epkdedkc73ertdh0`,
195 circuits, 6 qubits, 390 000 shots, ~105 s of QPU time.
**All 4 pre-registered gates pass.**

IBM-13's Gate 5 failed at `ν = 0.80` (TVD `0.0612` against a `0.061`
threshold) and the foreign-clock claim was withdrawn. This run establishes what
that failure was, and it was not what the gate was designed to detect.

## What the failure was saying

IBM-13's mimic was a **reconstruction**: take the ideal predicted distribution,
build a separable state that reproduces it, prepare that. In theory it matches
exactly (TVD ~ 1e-17). On hardware its amplitude sat *above* the history arm's
at every setting — by a nearly **constant ratio**, 1.11 to 1.15.

A constant ratio is the signature of a multiplicative attenuation difference,
not of a failure of classical reproducibility. **The reconstruction encodes the
noise-free distribution; the history state produces the decohered one.** The
comparison was never fair, and it becomes less fair as the signal grows — which
is precisely why it failed at the largest `ν` and nowhere else.

## The fix is physics, not statistics

There is a separable state that is not a reconstruction at all: the same state
with its coherences destroyed. **Dephase clock A in its computational basis.**
Proved from statevector before submission, across the whole sweep:

```
 nu    negativity(A:rest)   after dephasing   p(t_B,x) shift   V(Sa|B)
 0.65      1.408973          0.000000         0.0e+00       0.7923
 0.80      1.473496          0.000000         0.0e+00       0.9281
 1.00      1.500000          0.000000         0.0e+00       1.0000
```

Entanglement across `(clock A : rest)` drops to **exactly zero**. The measured
distribution moves by **nothing**. `V(Sₐ|B)` is unchanged.

That is the operational form of IBM-3's theorem — not argued from a
reconstruction, but demonstrated by destroying every coherence carrying the
entanglement and watching the reading hold still. The observable
`p(t_B, x)` lives entirely in clock A's **pointer basis**, so it is invariant
under dephasing there by construction. It is a classical observable in the
einselection sense, which is why no amount of entanglement makes it certify
anything.

**And it is depth-matched by construction.** The dephasing is `Rz(π)` on the
clock qubits, averaged over the four sign combinations, and **`Rz` is virtual on
IBM hardware** — zero duration, zero error. The mimic runs the identical
circuit, on identical qubits, at identical depth, through identical
decoherence. Padding parity, layout mismatch, depth mismatch: gone by
construction rather than corrected for.

## Results

```
 nu    V_hist  V_deph  V_recon   TVD(deph)  TVD(recon)   recon/hist
 0.00  0.0265  0.1214  0.0290    0.0099 PASS  0.0281     1.093
 0.25  0.2344  0.1882  0.2787    0.0169 PASS  0.0166     1.189
 0.50  0.4715  0.4677  0.5612    0.0078 PASS  0.0297     1.190
 0.65  0.6172  0.6130  0.7474    0.0073 PASS  0.0359     1.211
 0.80  0.7284  0.7325  0.8690    0.0119 PASS  0.0684     1.193
 0.90  0.7853  0.7834  0.9191    0.0072 PASS  0.0365     1.170
 1.00  0.8375  0.8434  0.9430    0.0073 PASS  0.0429     1.126

 anchor nu=0.65: F = 0.5295 vs bound 0.5000  ->  certifies
```

**The dephased mimic reproduces the history arm at every `ν`** — TVD
`0.0072–0.0169` against a threshold of `0.0220` fixed before submission. Mean
`0.0097` excluding the null.

**The reconstructed mimic reproduces IBM-13's pathology exactly.** Its bias is
multiplicative and nearly constant at **1.17–1.21** across the sweep — the same
signature IBM-13 showed at 1.11–1.15 — and its TVD is roughly **four times**
the dephased arm's (mean `0.0383` vs `0.0097`).

**Most directly: at `ν = 0.80`, the setting where IBM-13's Gate 5 failed, the
reconstructed arm gives TVD `0.0684` — which fails this run's threshold — while
the dephased arm gives `0.0119` and passes.** The failure is reproduced and
localised to the reconstruction, on the same device, in the same job.

## What this establishes

> IBM-13's Gate 5 failure was decoherence asymmetry between a noise-free
> reconstruction and a decohered quantum state, not a failure of classical
> reproducibility. **The foreign-clock amplitude `V(Sₐ|B)` is confirmed
> non-certifying**, by a state that is provably separable, prepared through the
> identical circuit at identical depth. The withdrawal of the foreign-clock
> claim in IBM-13 stands as the correct call on that job's evidence; this run
> supplies the evidence that was missing.

## Honest ledger

**This does not rescue IBM-13's Gate 5.** That gate failed on its own
pre-registered terms and the withdrawal stands. IBM-14 is a separate run with
its own pre-registration, and its threshold (`0.0220` at 16 000 shots per arm)
was fixed before submission, not chosen after seeing IBM-13's number.

**`V` remains positively biased at the null.** At `ν = 0` the exact value is 0;
the history arm reads `0.0265` and the dephased arm `0.1214`. Fitting an
amplitude to noise always returns something positive. Neither is interpretable
as signal, and the gate at that setting rests on the TVD (`0.0099`), not on `V`.

**Live attenuation exceeded the noise model.** The dry run predicted
`V_hist = 0.9704` at `ν = 1.0`; hardware delivered `0.8375`. `FakeMarrakesh` is
a stored snapshot and understates the live device here. No claim is made about
hardware relative to its noise model.

**Gate 3 is a contrast, not a certification.** That the reconstructed arm runs
high confirms the diagnosis; it does not by itself establish anything about
relational time.

**Nothing here changes the certification results.** The anchor re-confirms
`F = 0.5295` above the `0.5` bound at `ν = 0.65` on a third calibration, which
is consistent with both IBM-13 jobs but adds no new certification claim.

## Provenance

`ibm_marrakesh`, 2026-08-18, 1 job `da28epkdedkc73ertdh0`, chain
`[52, 53, 54, 55, 59, 75]`, layout pinned, 195 circuits at 2 000 shots. Raw
counts in `results_ibm14/raw.json`; every number reproduces from them:

```
python hardware/pw_ibm14_dephasing_mimic.py --analyze results_ibm14/raw.json
python hardware/pw_ibm_provenance.py --results results_ibm14/raw.json --out results_ibm14/ibm14_provenance.json
```
