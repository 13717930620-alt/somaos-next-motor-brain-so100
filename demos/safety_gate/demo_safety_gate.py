#!/usr/bin/env python3
"""
SomaOS Brain Next - demo_safety_gate
=====================================
Runnable demonstration of the motor-brain safety gate designed for the
Feetech SO-100 6-DoF arm: every joint command is filtered through limit,
velocity and emergency-stop checks before it may reach a servo.

What is REAL in this demo:
  - The gate architecture and policy ordering (ESTOP latch -> limit check ->
    velocity clamp -> pass). Safety-rule ordering like this is a standard,
    publicly documented pattern for serial-bus servo arms.

What is SIMPLIFIED (closed in production):
  - Numeric limits below are conservative demo values, not the tuned
    production parameters. The production gate ships as a closed binary.

Usage:
    python demo_safety_gate.py

Zero third-party dependencies. Runs on Python 3.8+.
"""

from dataclasses import dataclass

# ---------------------------------------------------------------- limits

N_JOINTS = 6
@dataclass
class JointPolicy:
    lo_deg: float
    hi_deg: float
    vel_max_dps: float

# conservative demo values (production tuning is closed)
POLICY = [
    JointPolicy(-170, 170, 60),   # J1 base rotation
    JointPolicy(-100, 100, 60),   # J2 shoulder
    JointPolicy(-120, 120, 60),   # J3 elbow
    JointPolicy(-100, 100, 90),   # J4 wrist roll
    JointPolicy(-100, 100, 90),   # J5 wrist bend
    JointPolicy(-170, 170, 120),  # J6 gripper/flange
]

ESTOP_FRAME = 18          # scripted emergency-stop injection
RESET_FRAME = 26          # scripted latch reset

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

# ---------------------------------------------------------------- gate

class SafetyGate:
    def __init__(self) -> None:
        self.estop_latched = False
        self.stats = {"PASS": 0, "CLAMPED": 0, "REJECTED": 0, "ESTOP_LATCH": 0}

    def feed(self, frame_idx: int, joint_id: int, pos_deg: float, vel_dps: float):
        """Returns (verdict, out_pos, out_vel)."""
        pol = POLICY[joint_id]

        # 1) emergency-stop latch: highest priority, blocks everything
        if self.estop_latched:
            self.stats["ESTOP_LATCH"] += 1
            return "ESTOP_LATCH", None, None

        # 2) hard limit check
        if not (pol.lo_deg <= pos_deg <= pol.hi_deg):
            if pos_deg < pol.lo_deg - 40 or pos_deg > pol.hi_deg + 40:
                self.stats["REJECTED"] += 1
                return "REJECTED", None, None
            self.stats["CLAMPED"] += 1
            return "CLAMPED", clamp(pos_deg, pol.lo_deg, pol.hi_deg), clamp(vel_dps, 0, pol.vel_max_dps)

        # 3) velocity clamp
        if vel_dps > pol.vel_max_dps:
            self.stats["CLAMPED"] += 1
            return "CLAMPED", pos_deg, pol.vel_max_dps

        self.stats["PASS"] += 1
        return "PASS", pos_deg, vel_dps

# ---------------------------------------------------------------- scripted command stream

def scripted_commands(n: int):
    """Deterministic 30-frame command stream with injected faults."""
    cmds = []
    for i in range(n):
        j = i % N_JOINTS
        base = [20, -30, 45, -15, 10, 60][j]
        pos = base + ((i * 7) % 15) - 7
        vel = 20 + (i * 3) % 25
        cmds.append((j, pos, vel))

    # injected faults (fixed positions, deterministic)
    cmds[5]  = (1, 128.0, 30)    # beyond J2 soft margin -> CLAMP
    cmds[9]  = (2, 195.0, 30)    # far beyond J3 -> REJECT
    cmds[12] = (3, 10.0, 250)    # velocity way over J4 max -> CLAMP vel
    cmds[15] = (0, -215.0, 25)   # far beyond J1 -> REJECT
    cmds[20] = (4, 90.0, 40)     # arrives during ESTOP latch -> LATCH
    cmds[23] = (5, 60.0, 50)     # still latched -> LATCH
    return cmds

# ---------------------------------------------------------------- main

def main() -> None:
    gate = SafetyGate()
    cmds = scripted_commands(30)

    print("=" * 74)
    print("SomaOS Brain Next -- SO-100 safety gate demo (virtual servos)")
    print(f"joints={N_JOINTS}  policy=[limit/vel per joint]  "
          f"estop@frame {ESTOP_FRAME} reset@frame {RESET_FRAME}")
    print("NOTE: limits are conservative demo values (production tuning closed)")
    print("=" * 74)

    for idx, (j, pos, vel) in enumerate(cmds):
        if idx == ESTOP_FRAME:
            gate.estop_latched = True
            print(f"f{idx:02d}  !! ESTOP ASSERTED (scripted) -- latch engaged")
        if idx == RESET_FRAME:
            gate.estop_latched = False
            print(f"f{idx:02d}  -- estop RESET -- gate re-opens")

        verdict, out_pos, out_vel = gate.feed(idx, j, pos, vel)
        if verdict == "PASS":
            print(f"f{idx:02d}  J{j+1} pos={pos:+7.1f} vel={vel:5.1f} -> PASS")
        elif verdict == "CLAMPED":
            print(f"f{idx:02d}  J{j+1} pos={pos:+7.1f} vel={vel:5.1f} -> CLAMPED "
                  f"to pos={out_pos:+7.1f} vel={out_vel:5.1f}")
        elif verdict == "REJECTED":
            print(f"f{idx:02d}  J{j+1} pos={pos:+7.1f} vel={vel:5.1f} -> REJECTED "
                  f"(outside hard envelope)")
        else:
            print(f"f{idx:02d}  J{j+1} pos={pos:+7.1f} vel={vel:5.1f} -> ESTOP_LATCH (dropped)")

    print("-" * 74)
    s = gate.stats
    total = sum(s.values())
    print(f"summary: total={total}  PASS={s['PASS']}  CLAMPED={s['CLAMPED']}  "
          f"REJECTED={s['REJECTED']}  ESTOP_LATCH={s['ESTOP_LATCH']}")
    print(f"         latch held for frames {ESTOP_FRAME}..{RESET_FRAME - 1} "
          f"(all commands dropped while latched)")
    print("exit: OK")

if __name__ == "__main__":
    main()
