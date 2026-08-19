# From AQ-YINYANG to IBM-16: what carries over, and what does not

*Written after checking both, rather than assuming the analogy holds.*

## Two corrections first

**[arXiv:2507.11676](https://arxiv.org/abs/2507.11676) is not what it looked
like.** It is *Quantum Circuits Are Just a Phase* — a **programming-language**
paper introducing a global phase operation and quantum pattern matching, with
denotational semantics and a prototype compiler. It shifts emphasis "from gates
to eigendecomposition, conjugation, and controlled unitaries" as a
*programming abstraction*. It does **not** introduce unitary descriptors,
invariants, or measurable quantities. Nothing in it improves the descriptors
used here, and building on it for that purpose would be a mistake.

**AQ-YINYANG's headline is a negative result, and a sharp one.** From the
2026-06-03 findings:

```
oracle_psnr    = 80.0000 dB     (codec is lossless before transport)
ifft_psnr      = 21.4153 dB     (after transport)
pixel_ridge_psnr = 21.4213 dB   (a direct pixel decoder does no better)
coeff_mag_cos  = 0.9922
coeff_real_cos = 0.9906
coeff_imag_cos = 0.9847
dc_mae         = 0.3472
```

**Cosine similarity of 0.99 in coefficient space coexists with a 21 dB image.**
Direction is recovered; magnitude is not. A pixel-space decoder reaching the
same 21.4 dB shows the ceiling is in the transported coefficients, not in the
unfolding.

## What carries over — and it is structural, not a new experiment

AQ-YINYANG's key correction was to stop splitting FFT coefficients into
magnitude and phase channels:

```
    x_0[k] = F_k            instead of      F_k = |F_k| exp(i phi_k)
```

because correlated errors in `|F|` and `phi` multiply when recombined, and the
imaginary channel amplifies the product error.

**Ancilla interferometry does that natively.** Reading `⟨X_R⟩` and `⟨Y_R⟩` gives

```
    ⟨X_R⟩ + i⟨Y_R⟩  =  Tr(rho U)
```

as a **complex number measured directly** — never split, never recombined. The
correction AQ-YINYANG had to discover is built into the measurement.

## What does NOT carry over — tested, not assumed

The obvious follow-up is whether the product-error pathology reappears when
estimating `C` from magnitude and phase jointly. It does not. Simulated at
4 000 shots with the errors correlated as the hardware makes them:

```
 C_true   err(phase only)  err(vis only)  err(naive joint)   winner
  0.30      0.0682          0.0470         0.0470          joint
  0.60      0.0229          0.0223         0.0222          joint
  0.80      0.0134          0.0162         0.0160          phase
  0.95      0.0055          0.0119         0.0059          phase
```

The joint estimator tracks the better channel and never amplifies. The reason
is that AQ-YINYANG's failure came from a **product** reconstruction
`|F| exp(i phi)`, while here the estimator is a residual minimisation over a
quantity measured directly as a complex amplitude. **The analogy is real at the
level of encoding and false at the level of error propagation**, and the second
half only became clear by testing it.

## What this means for the programme

There is **no new hardware experiment** in this connection. IBM-16 already has
the right structure, and the AQ-YINYANG lesson explains *why* it does rather
than suggesting something further.

It also sharpens what IBM-16 can honestly claim. Set against the state of the
field:

- Svozil's entangled clock recovers temporal structure only from the **joint
  coincidence record**, certified by multi-setting Bell tests; local marginals
  carry nothing.
- Extended Page–Wootters models recover an **informational arrow** — monotone
  entropy growth across clock readings — not a shared phase or a free signal.
- Timelike-entanglement and energy-time work recovers information from
  **arrival-time or joint-spectral correlations**, not from anything the
  entanglement emits on its own.

This programme reached the same wall from the opposite direction, and IBM-16 is
the honest instrument that survives it: **the recoverable information is the
trajectory along the complementarity budget, not a quantity that escapes it.**
The phase reads `r`; tomography reads `C`; the gap between them witnesses
departure from the pure-state manifold. That is metrology and channel
diagnostics, and it is bounded by Holevo like everything else.

**No claim is made, here or anywhere in this programme, that entanglement emits
a decodable temporal signal.** The measured content is the budget trajectory,
which is exactly what the surrounding literature also finds.
