"""
Section 2 driver: every S.2 table and graph in one run.

    python main_section2.py          (from the repo root)

Writes csvs/ and figs/. Add your own pair to CHOSEN_PAIRS and rerun to get your S.2.2 set.

Author: Shaunn Pavelik (10/8/2026)
"""
import csv
import json
import os
import sys

# Run from the repo folder no matter where VS Code / the terminal starts, so the imports
# below find S2_1, s1/ and utils/, and csvs/ + figs/ land next to this file.
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
sys.path.insert(0, HERE)

try:
    import matplotlib  # noqa: F401
    import numpy  # noqa: F401
except ModuleNotFoundError as e:
    sys.exit(f"Missing package '{e.name}'. Install it once with:\n"
             f"    \"{sys.executable}\" -m pip install numpy matplotlib")

import S2_1
import S2_2
import S2_auto_graph as G
import utils.TrueConst as TrueConst

# (stage 1, stage 2) each teammate carries into S.2.2 -- same pairs as our Section 1
# individual slides (own Table 4 column over LOX/LH2). Change yours here if you switch.
CHOSEN_PAIRS = {
    "Gregory Kahn":   ("LOX/LCH4", "LOX/LH2"),
    "Henry Rowley":   ("LOX/LH2", "LOX/LH2"),
    "Jacob Harmon":   ("LOX/RP1", "LOX/LH2"),
    "Sharan Menon":   ("SOLID", "LOX/LH2"),
    "Shaunn Pavelik": ("N2O4/UDMH", "LOX/LH2"),
}


def tag_of(s1, s2):
    return f"{s1}__{s2}".replace("/", "_")


def summary(res):
    """Flat numbers for tables and the review page."""
    st1, st2 = res["stage_1"], res["stage_2"]
    return dict(
        dv1=res["delta_v_1"], dv_delivered=res["delta_v_delivered"],
        vl_m0=res["ideal_gross_mass"], sl_m0=res["systems_gross_mass"],
        vl_cost=res["ideal_cost_musd"], sl_cost=res["systems_cost_musd"],
        d=res["vehicle_diameter"], length=res["vehicle_length"], ld=res["length_to_diameter"],
        n1=st1["number_of_engines"], n2=st2["number_of_engines"],
        base1=st1["engine_base_diameter_needed"], base2=st2["engine_base_diameter_needed"],
        fit=res["engines_fit"], fit_fallback=res.get("fit_fallback", False), iters=res["iterations"],
        engine1=st1["engine_name"], engine2=st2["engine_name"],
        inert1=st1["dry_mass_with_margin"], inert2=st2["dry_mass_with_margin"],
        prop1=st1["propellant_mass"], prop2=st2["propellant_mass"],
        vl_inert1=res["ideal"]["m_in_1"], vl_inert2=res["ideal"]["m_in_2"],
        vl_prop1=res["ideal"]["m_pr_1"], vl_prop2=res["ideal"]["m_pr_2"],
        eff_delta1=res["effective_inert_fraction"][0], eff_delta2=res["effective_inert_fraction"][1],
        len1=st1["stage_length"], len2=st2["stage_length"],
        breakdown={k: {key: st[key] for key, _ in G.SUBSYSTEMS + [("propellant_mass", "")]}
                   for k, st in (("1", st1), ("2", st2))},
    )


if __name__ == "__main__":
    os.makedirs("csvs", exist_ok=True)
    os.makedirs("figs", exist_ok=True)
    report = {"people": {}, "all25": []}

    print("\n== S.2.2 individual sets ==")
    for who, (s1, s2) in CHOSEN_PAIRS.items():
        tag = tag_of(s1, s2)
        best_m, best_c = G.section1_splits(s1, s2)
        entry = {"pair": [s1, s2], "designs": {}}
        for kind, split in (("min-mass", best_m), ("min-cost", best_c)):
            res = S2_1.run_systems_analysis(s1, s2, split["dv1"])
            if res is None or not res["converged"]:
                print(f"{who} {kind}: does not close at system level")
                continue
            S2_2.create_table_of_masses(res)
            k = kind.replace("min-", "")
            G.plot_breakdown(res, f"figs/S2_2_{tag}_{k}_breakdown.png")
            G.plot_vl_vs_sl(res, f"figs/S2_2_{tag}_{k}_vl_vs_sl.png")
            G.plot_vehicle_sketch(res, f"figs/S2_2_{tag}_{k}_sketch.png")
            entry["designs"][kind] = summary(res)
            print(f"{who} {kind}: dv1 {split['dv1']:.0f} m/s  "
                  f"VL {res['ideal_gross_mass']/1e3:,.1f} t -> SL {res['systems_gross_mass']/1e3:,.1f} t, "
                  f"${res['systems_cost_musd']/1e3:.2f}B, D {res['vehicle_diameter']:.1f} m")

        # sensitivities on the min-mass design
        dv = best_m["dv1"]
        fixed = S2_1.run_systems_analysis(s1, s2, dv, close_delta_v=False)
        fit, _ = S2_1.choose_diameter(s1, s2, dv, enforce_engine_fit=False)   # L/D only
        S2_1.USE_J2X_UPPER_STAGE = False                 # what the J-2X swap bought us
        table2 = S2_1.run_systems_analysis(s1, s2, dv)
        S2_1.USE_J2X_UPPER_STAGE = True
        entry["sensitivity"] = {
            "table2_upper_engine": None if table2 is None or not table2["converged"] else summary(table2),
            "fixed_propellant": None if fixed is None else summary(fixed),
            "engine_fit_not_enforced": None if fit is None else summary(fit),
        }

        # where the best split moves once the MERs are in
        rows = G.sweep_dv1(s1, s2, dv_step=25.0)
        G.plot_dv1_sweep(s1, s2, rows, f"figs/S2_2_{tag}_dv1_sweep.png")
        ok = [r for r in rows if r["sl_m0"] == r["sl_m0"]]
        sl_best_m = min(ok, key=lambda r: r["sl_m0"])
        sl_best_c = min(ok, key=lambda r: r["sl_cost"])
        entry["system_optimum"] = {
            "mass": {"dv1": sl_best_m["dv1"], "m0": sl_best_m["sl_m0"], "cost": sl_best_m["sl_cost"],
                     "d": sl_best_m["d"]},
            "cost": {"dv1": sl_best_c["dv1"], "m0": sl_best_c["sl_m0"], "cost": sl_best_c["sl_cost"],
                     "d": sl_best_c["d"]},
        }
        report["people"][who] = entry

    print("\n== all 25 pairs at their Section 1 splits ==")
    rows_out, grid_rows = [], []
    for s2 in TrueConst.PROPELLANT_NAMES:
        for s1 in TrueConst.PROPELLANT_NAMES:
            best_m, best_c = G.section1_splits(s1, s2)
            for kind, split in (("min-mass", best_m), ("min-cost", best_c)):
                res = S2_1.run_systems_analysis(s1, s2, split["dv1"])
                ok = res is not None and res["converged"]
                row = dict(stage1=s1, stage2=s2, design=kind, dv1_ms=split["dv1"],
                           vl_m0_t=split["m_0"] / 1e3, vl_cost_B=split["cost"] / 1e3,
                           sl_m0_t=res["systems_gross_mass"] / 1e3 if ok else None,
                           sl_cost_B=res["systems_cost_musd"] / 1e3 if ok else None,
                           diameter_m=res["vehicle_diameter"] if ok else None,
                           length_m=res["vehicle_length"] if ok else None,
                           LD=res["length_to_diameter"] if ok else None,
                           engines_1=res["stage_1"]["number_of_engines"] if ok else None,
                           engines_2=res["stage_2"]["number_of_engines"] if ok else None,
                           engines_fit=res["engines_fit"] if ok else None,
                           engine_2=res["stage_2"]["engine_name"] if ok else None)
                rows_out.append(row)
                if kind == "min-mass":
                    grid_rows.append(dict(stage1=s1, stage2=s2, vl_m0=split["m_0"],
                                          sl_m0=res["systems_gross_mass"] if ok else None))
    with open("csvs/S2_all25_system_level.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_out[0]))
        w.writeheader()
        w.writerows(rows_out)
    G.plot_group_matrix(grid_rows, "figs/S2_group_matrix_mass.png")
    report["all25"] = rows_out

    # group graphic: the five individual designs side by side, vehicle vs system level
    team = []
    for who, (s1, s2) in CHOSEN_PAIRS.items():
        for kind, d in report["people"][who]["designs"].items():
            team.append(dict(who=who, s1=s1, s2=s2, kind=kind, **{k: d[k] for k in
                             ("vl_m0", "sl_m0", "vl_cost", "sl_cost")}))
    G.plot_team_designs(team, "figs/S2_group_team_designs.png")

    with open("csvs/S2_report.json", "w") as f:
        json.dump(report, f, indent=1, default=float)
    print("done -- see csvs/ and figs/")
