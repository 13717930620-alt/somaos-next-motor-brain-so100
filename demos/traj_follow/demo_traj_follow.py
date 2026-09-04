#!/usr/bin/env python3
"""
SomaOS Brain Next - demo_traj_follow
=====================================
Runnable demonstration of SO-100 6-joint trajectory following with
virtual servos: waypoint interpolation, per-tick velocity-capped execution,
and closed-loop tracking-error reporting.

What is REAL in this demo:
  - The execution skeleton: waypoint interpolation, velocity cap,
    first-order servo-following model, RMS error accounting.
    These are standard, publicly known engineering patterns.

What is SIMPLIFIED (closed in production):
  - The production trajectory optimiser and servo telemetry pipeline ship
    as closed binaries and are NOT included.
  - Real-hardware bridge is not part of this demo (virtual servos only).

Usage:
    python demo_traj_follow.py [--seed 3] [--hz 20]

Zero third-party dependencies. Runs on Python 3.8+.
"""

import argparse
import math
import random

N_JOINTS = 6
VEL_CAP_DPS = 60.0        # demo velocity cap (production tuning closed)
FOLLOW_GAIN = 0.35        # first-order virtual-servo following gain

# scripted SO-100 waypoints, degrees (deterministic)
HOME   = [0, -20, 40, 0, 25, 0]
PICK   = [35, -55, 75, -20, 40, 0]
LIFT   = [35, -25, 55, -10, 20, 0]
PLACE  = [-30, -45, 65, -15, 35, 45]
WAYPOINTS = [HOME, PICK, LIFT, PLACE]

def lerp(a, b, t):
    return a + (b - a) * t

def next_target(current, goal, vel_cap, dt):
    """Velocity-capped step toward the goal (per joint)."""
    out = []
    for c, g in zip(current, goal):
        delta = g - c
        step = max(-vel_cap * dt, min(vel_cap * dt, delta))
        out.append(c + step)
    return out

# ---------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser(description="SomaOS SO-100 trajectory-follow demo")
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--hz", type=int, default=20, help="control rate (demo)")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    dt = 1.0 / args.hz

    current = list(HOME)
    sq_err_sum = 0.0
    n_steps = 0
    worst = 0.0
    per_wp_rms = []

    print("=" * 74)
    print("SomaOS Brain Next -- SO-100 trajectory follow demo (virtual servos)")
    print(f"joints={N_JOINTS}  hz={args.hz}  vel_cap={VEL_CAP_DPS}dps  "
          f"waypoints={[w[0] for w in [(x, 0) for x in ('HOME','PICK','LIFT','PLACE')]]}".replace("[(", "("))
    print("NOTE: servo model = first-order + noise (production pipeline closed)")
    print("NOTE: real-hardware bridge not included -- run with virtual servos only")
    print("=" * 74)

    for wp_idx, goal in enumerate(WAYPOINTS[1:], start=1):
        seg_sq = 0.0
        seg_n = 0
        print(f"-- waypoint {wp_idx}: {goal}")
        tick = 0
        while True:
            target = next_target(current, goal, VEL_CAP_DPS, dt)
            # first-order servo follow + small measurement noise
            actual = [
                c + FOLLOW_GAIN * (t - c) + rng.uniform(-0.4, 0.4)
                for c, t in zip(current, target)
            ]
            errs = [abs(a - t) for a, t in zip(actual, target)]
            max_err = max(errs)
            sq_err_sum += sum(e * e for e in errs)
            seg_sq += sum(e * e for e in errs)
            n_steps += N_JOINTS
            seg_n += N_JOINTS
            worst = max(worst, max_err)
            current = actual

            if tick % 10 == 0:
                print(f"  t={tick * dt:4.2f}s tgt[{target[0]:+6.1f},{target[1]:+6.1f},"
                      f"{target[2]:+6.1f}] act[{actual[0]:+6.1f},{actual[1]:+6.1f},"
                      f"{actual[2]:+6.1f}] max_err={max_err:4.1f}deg")
            done = all(abs(c - g) < 1.0 for c, g in zip(current, goal))
            tick += 1
            if done or tick > 400:
                break
        per_wp_rms.append(math.sqrt(seg_sq / max(seg_n, 1)))
        print(f"  -> waypoint {wp_idx} reached in {tick} ticks, "
              f"seg RMS={per_wp_rms[-1]:.2f}deg")

    print("-" * 74)
    overall_rms = math.sqrt(sq_err_sum / max(n_steps, 1))
    print(f"summary: waypoints={len(WAYPOINTS) - 1}  steps={n_steps // N_JOINTS}  "
          f"overall_RMS={overall_rms:.2f}deg  worst_err={worst:.2f}deg")
    print(f"         per-waypoint RMS={['%.2f' % r for r in per_wp_rms]}deg")
    print("exit: OK")

if __name__ == "__main__":
    main()
