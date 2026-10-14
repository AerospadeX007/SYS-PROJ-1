"""
Cross-check: team system-level tool (S2_1.py) vs Henry's independent version (S2_1_HCR.py).

Runs both on every teammate's min-mass and min-cost design at the diameter Henry's search picks,
with S2_1 set to Henry's inputs (J-2X at Table 2's O/F 6.03 and 9.1 MPa), and prints the
difference in gross mass and cost. Two codes written separately agreeing is our S.2.1 verification.

    python S2_crosscheck_HCR.py      (from the repo root)

Author: Shaunn Pavelik (10/14/2026); S2_1_HCR.py by Henry Rowley
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
sys.path.insert(0, HERE)

import utils.TrueConst as TrueConst
import S2_1
import S2_1_HCR as HCR

DESIGNS = {  # teammate: (stage 1, stage 2, min-mass dV1, min-cost dV1) from Section 1
    "Kahn": ("LOX/LCH4", "LOX/LH2", 4266, 5270),
    "Rowley": ("LOX/LH2", "LOX/LH2", 4710, 5749),
    "Harmon": ("LOX/RP1", "LOX/LH2", 4095, 5092),
    "Menon": ("SOLID", "LOX/LH2", 3230, 3835),
    "Pavelik": ("N2O4/UDMH", "LOX/LH2", 3750, 4666),
}


def henry_diameter(p1, p2, dv1):
    """Henry's search: first D from 5.2 m in 0.2 m steps with L/D <= 13 and engines that fit."""
    d = 5.2
    while d <= 25.0:
        r = HCR.solve_vehicle(p1, p2, dv1, D=round(d, 2))
        if r["converged"] and r["ld_ok"] and r["s1"]["engines_fit"] and r["s2"]["engines_fit"]:
            return round(d, 2), r
        d += 0.2
    return None, None


if __name__ == "__main__":
    TrueConst.J2X["mixture_ratio"] = 6.03          # Henry's inputs
    TrueConst.J2X["chamber_pressure_MPa"] = 9.1
    print(f"{'design':16s} {'D (m)':>6s} {'HCR m0 (t)':>11s} {'S2_1 m0 (t)':>11s} {'diff':>8s} "
          f"{'HCR ($B)':>9s} {'S2_1 ($B)':>9s} {'diff':>8s}")
    worst = 0.0
    for who, (p1, p2, dv_m, dv_c) in DESIGNS.items():
        for kind, dv1 in (("min-mass", dv_m), ("min-cost", dv_c)):
            D, h = henry_diameter(p1, p2, dv1)
            if h is None:
                print(f"{who + ' ' + kind:16s}   no diameter <= 25 m fits the engines in HCR's search")
                continue
            u = S2_1._size_vehicle(p1, p2, dv1, D, D)
            dm = (u["systems_gross_mass"] / h["M0"] - 1) * 100
            dc = (u["systems_cost_musd"] / h["total_cost_M"] - 1) * 100
            worst = max(worst, abs(dm), abs(dc))
            print(f"{who + ' ' + kind:16s} {D:6.1f} {h['M0'] / 1e3:11.1f} {u['systems_gross_mass'] / 1e3:11.1f} "
                  f"{dm:+7.3f}% {h['total_cost_M'] / 1e3:9.3f} {u['systems_cost_musd'] / 1e3:9.3f} {dc:+7.3f}%")
    print(f"largest difference: {worst:.3f}%")
