# Where D-LinOSS earns a place, and where it does not

*I dismissed this too quickly. The reframing is legitimate and points at a
different experiment, not a different analysis of IBM-17.*

## What I got wrong

I argued D-LinOSS had nothing to attach to because the meter's inversion is a
1-D monotone curve lookup. That is true **of IBM-17** and false as a general
statement. The distinction being drawn — D-LinOSS as a learner of *transition
morphology* rather than as a *detector* of a buried signal — is a different task
from the TRAPPIST/astrophysics usage where it never beat ridge.

## The blocking fact, and the fix

The morphology worth learning is whether the environment has **memory** —
Markovian decay versus non-Markovian recoherence. Tested numerically:

**Dephasing the PURIFIER (IBM-17's ladder) hides it completely.**

```
 step   Markov C   Markov |r|    nonMarkov C   nonMarkov |r|
   0     0.9000     0.4359         0.9000        0.4359
   3     0.7460     0.4359         0.4478        0.4359
   5     0.6583     0.4359         0.1604        0.4359
```

The two trajectories differ sharply in `C` — one monotone, one turning around —
but `|r|` is **identical and constant in both**. Since the phase reads `r`, it
sees two flat lines. A model trained on phase trajectories from this ladder
would have nothing to learn, and the signal would only be reachable through the
nine-setting tomography the meter exists to avoid.

**Dephasing the TARGET instead puts the morphology into the phase.**

```
 step   Markov |r|   phase_M     nonMarkov |r|   phase_N    |dphase|
   0      0.8000     -0.3989       0.8000       -0.3989      0.0000
   3      0.6975     -0.2408       0.4973       -0.0762      0.1646
   5      0.6366     -0.1744       0.0566       -0.0001      0.1743
   6      0.6082     -0.1490       0.1818       -0.0034      0.1456
```

`|r|` now decays, the phase tracks it, and the non-Markovian branch **turns
around** at step 5→6 — recoherence, visible directly in a two-setting readout.
That is a genuine morphological signature, and it is cheap.

**The trade is explicit:** dephasing the target moves `r`, so the instrument
stops being a fixed-`r` entanglement meter and becomes a probe of the
*environment*. Both are real; they are different experiments, and IBM-17 should
not be repurposed into this one.

## IBM-18 sketch, if it is worth running

Target dephasing with a **reused** versus **refreshed** environment qubit —
the standard construction for engineering non-Markovianity, and one
superconducting hardware handles well.

- **Markovian arm**: a fresh environment coupling each step (reset between).
- **Non-Markovian arm**: one environment reused, so information flows back.
- Read the phase at every step in two ancilla settings; tomography only at the
  endpoints, as a cross-check rather than the primary readout.

The physics is established — this is the setting for the BLP and RHP
non-Markovianity measures — so the run must not claim to discover memory
effects. What it would contribute is the phase trajectory as a **cheap probe**
of them.

## What D-LinOSS would have to beat

Stated up front, because the programme's record demands it: **every recorded
`D-LinOSS − ridge` value across the campaign was negative**, and it was retired
from detector duty for that reason.

The baseline here is brutal and one line: the BLP measure is the sum of
positive increments along the trajectory, and it separates the two arms above
trivially. **Binary Markovian/non-Markovian classification is not a task
D-LinOSS should be given** — it would be losing to a sum.

Where a sequence model plausibly has room is **parameter inference from
trajectory shape**: recovering the coupling strength, the environment's
correlation time, or the number of interacting environment modes from the
morphology of the recoherence — a regression over curve shape rather than a
scalar threshold. That is closer to the fMRI usage described, where the value
was learning the geometry of state transitions rather than detecting a signal.

**Pre-registration for any such attempt:** ridge and the BLP scalar are run
first on the same data, and D-LinOSS is reported against them whatever the
outcome. Its documented value in this programme has been diagnostic — its
*structured* failures named the right variables — and that remains a legitimate
result to report.

## Status

Not scheduled. IBM-17 comes first, and this is a separate design that should not
borrow its circuits. Recorded so the reasoning survives rather than being
re-derived.
