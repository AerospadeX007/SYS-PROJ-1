"""
Cross-check: team system-level tool (S2_1.py) vs Henry's independent version (S2_1_HCR.py).

Runs both on every teammate's min-mass and min-cost design at the diameter Henry's search picks,
with S2_1 set to Henry's inputs (J-2X at Table 2's O/F 6.03 and 9.1 MPa), and prints the
difference in gross mass and cost. Two codes written separately agreeing is our S.2.1 verification.

Two S2_1 columns:
  same inputs : S2_1 with INTERSTAGE_OVER_UPPER_ENGINE_BAY = True (Henry's 10/14 inter-stage length)
  S2_1 default: inter-stage over stage 1's top dome only (what main_section2.py uses)
The first should agree to round-off; the second shows what the inter-stage definition is worth.

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


def s2_1(p1, p2, dv1, D, henry_interstage):
    saved = S2_1.INTERSTAGE_OVER_UPPER_ENGINE_BAY
    S2_1.INTERSTAGE_OVER_UPPER_ENGINE_BAY = henry_interstage
    try:
        return S2_1._size_vehicle(p1, p2, dv1, D, D)
    finally:
        S2_1.INTERSTAGE_OVER_UPPER_ENGINE_BAY = saved


def pct(a, b):
    return (b / a - 1) * 100


if __name__ == "__main__":
    TrueConst.J2X["mixture_ratio"] = 6.03          # Henry's inputs
    TrueConst.J2X["chamber_pressure_MPa"] = 9.1
    print(f"{'design':16s} {'D (m)':>5s} | {'HCR m0 t':>8s} {'same in.':>8s} {'diff':>7s} {'default':>8s} {'diff':>7s} "
          f"| {'HCR $B':>7s} {'same in.':>8s} {'diff':>7s} {'default':>8s} {'diff':>7s}")
    worst_same, spread = 0.0, []
    for who, (p1, p2, dv_m, dv_c) in DESIGNS.items():
        for kind, dv1 in (("min-mass", dv_m), ("min-cost", dv_c)):
            D, h = henry_diameter(p1, p2, dv1)
            if h is None:
                print(f"{who + ' ' + kind:16s}   no diameter <= 25 m fits the engines in HCR's search")
                continue
            s = s2_1(p1, p2, dv1, D, True)
            u = s2_1(p1, p2, dv1, D, False)
            hm, hc = h["M0"], h["total_cost_M"]
            sm, sc = s["systems_gross_mass"], s["systems_cost_musd"]
            um, uc = u["systems_gross_mass"], u["systems_cost_musd"]
            worst_same = max(worst_same, abs(pct(hm, sm)), abs(pct(hc, sc)))
            spread += [pct(hm, um), pct(hc, uc)]
            print(f"{who + ' ' + kind:16s} {D:5.1f} | {hm / 1e3:8.1f} {sm / 1e3:8.1f} {pct(hm, sm):+6.3f}% "
                  f"{um / 1e3:8.1f} {pct(hm, um):+6.2f}% | {hc / 1e3:7.3f} {sc / 1e3:8.3f} {pct(hc, sc):+6.3f}% "
                  f"{uc / 1e3:8.3f} {pct(hc, uc):+6.2f}%")
    print(f"same inputs: largest difference {worst_same:.3f}%")
    print(f"S2_1 default inter-stage: {min(spread):+.2f}% to {max(spread):+.2f}% vs S2_1_HCR")
