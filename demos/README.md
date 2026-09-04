# Runnable Demos

Two self-contained demo programs exercise the framework logic of the
SomaOS Brain Next motor brain (Feetech SO-100 target) against virtual
servos. Both are pure Python standard library (zero dependencies,
Python 3.8+), fully deterministic, and print their complete run to stdout.

> **What is real vs simplified**
> Real: the safety-gate architecture and policy ordering (ESTOP latch →
> limit check → velocity clamp → pass) and the execution skeleton
> (waypoint interpolation, velocity cap, first-order servo following,
> RMS error accounting). These are standard, publicly documented
> engineering patterns for serial-bus servo arms.
> Simplified: the numeric limits are conservative demo values; the
> production gate and trajectory optimiser ship as closed binaries inside
> the container and are not included in this repository.

## 1. Safety gate (`safety_gate/`)

Thirty scripted joint commands — including injected over-limit,
over-velocity and emergency-stop faults — are passed through the gate.
Each verdict (PASS / CLAMPED / REJECTED / ESTOP_LATCH) is printed.

```bash
python demos/safety_gate/demo_safety_gate.py
```

Example output (abridged, deterministic):

```
f18  !! ESTOP ASSERTED (scripted) -- latch engaged
f20  J5 pos= +90.0 vel= 40.0 -> ESTOP_LATCH (dropped)
f26  -- estop RESET -- gate re-opens
summary: total=30  PASS=18  CLAMPED=2  REJECTED=2  ESTOP_LATCH=8
exit: OK
```

The latch holds for the scripted interval and every command issued while
latched is dropped.

## 2. Trajectory follow (`traj_follow/`)

Three SO-100 waypoints are interpolated with a per-tick velocity cap and
executed against first-order virtual servos with per-joint tracking-error
reporting.

```bash
python demos/traj_follow/demo_traj_follow.py --seed 3 --hz 20
```

Example output (abridged, deterministic for seed=3):

```
  -> waypoint 3 reached in 64 ticks, seg RMS=1.28deg
summary: waypoints=3  steps=124  overall_RMS=1.35deg  worst_err=2.34deg
exit: OK
```

## Notes

- The same demos run inside the container in `--mode demo`
  (`docker/install.md`).
- Real-hardware bridge (serial bus to actual SO-100 servos) is not part of
  the demo; the production runtime inside the container owns it.
- These demos do not include the production motor core, model weights, or
  any private algorithms.
