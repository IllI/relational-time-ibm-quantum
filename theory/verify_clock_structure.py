#!/usr/bin/env python3
"""Finite-clock structural results. No QPU, no dependencies beyond numpy.

Two properties of finite cyclic clocks, derived rather than measured, that
sharpen IBM-7's commensurability result and constrain any follow-up run that
uses more than one clock.

They live here rather than in a successor repository because they are about
*this* programme's clocks. IBM-7 established that a finite cyclic constraint
closes exactly only at commensurate rates; these say what else is forced once
more than one clock is in play.

Both exist because this programme spent two hardware runs (IBM-6, IBM-8)
measuring a quantity its own construction had fixed at +1. The rule that came
out of it:

    DERIVE WHETHER A QUANTITY IS CONTINGENT BEFORE DESIGNING A RUN TO MEASURE IT.

    python theory/verify_clock_structure.py
"""

from __future__ import annotations

import numpy as np


def rate_between(x: np.ndarray, y: np.ndarray, d: int) -> int | None:
    """Multiplier m with y = m*x (mod d), or None if no such m exists."""
    for m in range(d):
        if np.all((m * x) % d == y % d):
            return m
    return None


def result1_loop_closure() -> bool:
    """Rate loop closure is AUTOMATIC, not contingent.

    For |Psi> = (1/sqrt d) sum_t |t>_A |a t>_B |b t>_C the pairwise rates are
    a, b/a and 1/b, whose product telescopes to 1 identically.

    Consequence for run design: a future multi-clock run that pre-registers
    "the loop closes" as a physics gate would be measuring a theorem. The
    contingent content is whether CONTROL networks -- rewired, severed,
    classically correlated -- admit any consistent assignment at all. The claim
    has to be a comparison, not a verification."""
    print("RESULT 1 -- rate loop closure alpha_AB * alpha_BC * alpha_CA")
    print("  symbolically: a * (b/a) * (1/b) = 1  for ALL a, b\n")
    ok = True
    for d in (8, 12, 16):
        t = np.arange(d)
        for a in range(1, d):
            for b in range(1, d):
                A, B, C = t % d, (a * t) % d, (b * t) % d
                rAB, rBC, rCA = (rate_between(A, B, d), rate_between(B, C, d),
                                 rate_between(C, A, d))
                if None in (rAB, rBC, rCA):
                    continue                     # undefined -- see result 2
                if (rAB * rBC * rCA) % d != 1:
                    print(f"    COUNTEREXAMPLE d={d} a={a} b={b}")
                    ok = False
    print(f"  checked d in (8,12,16), all (a,b): product == 1 wherever defined -> {ok}")
    print("  => NOT a physics gate. Use only as a prep consistency check.\n")
    return ok


def result2_frame_invertibility() -> bool:
    """A clock is a usable REFERENCE FRAME only if gcd(rate, d) = 1.

    Using clock B as the frame means recovering the shared label from B's
    readings, which requires t -> a*t mod d to be injective.

    Distinct from IBM-7's commensurability, which is about exact cycle closure
    after d ticks. This is about RESOLUTION -- whether a clock can index the
    others at all. Both are finite-clock artifacts and both need scoping in any
    write-up.

    (A first draft of this check tested the wrong direction: the rate FROM the
    summation label TO B is always defined, being `a` by construction. What can
    fail is the reverse. Written executably is how that surfaced.)"""
    print("RESULT 2 -- a clock is a usable frame only if gcd(rate, d) = 1")
    ok = True
    for d in (8, 12, 16):
        t = np.arange(d)
        for a in range(1, d):
            readings = (a * t) % d
            injective = len(set(readings.tolist())) == d
            recoverable = rate_between(readings, t, d) is not None
            coprime = int(np.gcd(a, d)) == 1
            if not (injective == recoverable == coprime):
                print(f"    MISMATCH d={d} a={a}")
                ok = False
        usable = [a for a in range(1, d) if np.gcd(a, d) == 1]
        print(f"  d={d:>2}: usable frame rates {usable}  ({len(usable)} of {d-1})")
    print(f"  injective <=> label-recoverable <=> coprime, exactly -> {ok}")
    print("  => a finite clock cannot serve as a frame at every rate.")
    print("     A THEORY constraint on run design, not a gate.\n")
    return ok


if __name__ == "__main__":
    print("=" * 74)
    print("Finite-clock structure -- derived before any multi-clock run exists")
    print("=" * 74 + "\n")
    results = [result1_loop_closure(), result2_frame_invertibility()]
    print("=" * 74)
    print(f"all structural checks pass: {all(results)}")
    print("=" * 74)
