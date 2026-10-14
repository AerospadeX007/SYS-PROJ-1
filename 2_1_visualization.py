import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, RadioButtons
from matplotlib.patches import Polygon, Rectangle, Wedge
import utils.TrueConst as TrueConst
from S2_1_HCR import solve_vehicle, get_stage_prop_specs, engine_pack_diameter

def get_tank_dims(stage_dict, D):
    if stage_dict["tank_order"] == "Solid_Single":
        L_t = stage_dict["stage_length"] - 3.0 - (18.2 if stage_dict["stage_num"] == 2 else 0.0)
        r = stage_dict.get("r_bot", min(D / 2.0, L_t / 2.0))
        L_c = max(0.0, L_t - 2.0 * r)
        return [(r, L_c, L_t, "SOLID", "#b5651d")]
    
    f_tup = (stage_dict["r_f"], stage_dict["L_cyl_f"], stage_dict["L_tank_f"], "Fuel", "#e63946")
    ox_tup = (stage_dict["r_ox"], stage_dict["L_cyl_ox"], stage_dict["L_tank_ox"], "Oxidizer", "#457b9d")
    if stage_dict["tank_order"] == "Fuel_Bot_Ox_Top":
        return [f_tup, ox_tup]
    return [ox_tup, f_tup]

def draw_tank(ax, z_base, r, L_cyl, color, label):
    w_bot = Wedge((0, z_base + r), r, 180, 360, facecolor=color, edgecolor="black", alpha=0.85, lw=1.2)
    ax.add_patch(w_bot)
    if L_cyl > 0:
        rect = Rectangle((-r, z_base + r), 2 * r, L_cyl, facecolor=color, edgecolor="black", alpha=0.85, lw=1.2)
        ax.add_patch(rect)
    w_top = Wedge((0, z_base + r + L_cyl), r, 0, 180, facecolor=color, edgecolor="black", alpha=0.85, lw=1.2)
    ax.add_patch(w_top)
    ax.text(0, z_base + r + L_cyl / 2.0, f"{label}\n(r={r:.2f}m)", ha="center", va="center", color="white", fontsize=8, fontweight="bold")

def draw_frustum(ax, z1, r1, z2, r2, color="#8d99ae"):
    poly = Polygon([(-r1, z1), (r1, z1), (r2, z2), (-r2, z2)], closed=True, facecolor=color, edgecolor="black", alpha=0.35, lw=1.5)
    ax.add_patch(poly)

def draw_engines(ax, z_exit, N_eng, De, D_Compare):
    w_pack = engine_pack_diameter(int(N_eng), De)
    fit_color = "#2a9d8f" if w_pack <= D_Compare else "#d62828"
    poly = Polygon([(-w_pack / 2.0, z_exit), (w_pack / 2.0, z_exit),
                    (w_pack / 3.0, z_exit + 3.0), (-w_pack / 3.0, z_exit + 3.0)],
                   closed=True, facecolor=fit_color, edgecolor="black", alpha=0.75, lw=1.2)
    ax.add_patch(poly)
    ax.text(0, z_exit + 1.5, f"{N_eng}x Eng\n(Pack={w_pack:.1f}m)", ha="center", va="center", color="white", fontsize=7.5, fontweight="bold")

fig, (ax_schem, ax_info) = plt.subplots(1, 2, figsize=(12, 8.5), gridspec_kw={"width_ratios": [1.3, 1]})
plt.subplots_adjust(left=0.08, right=0.96, bottom=0.25, top=0.93, wspace=0.25)

prop_list = TrueConst.PROPELLANT_NAMES
state = {"prop1": "LOX/LH2", "prop2": "LOX/LH2", "D": 9.2, "dV1": 5749.0}

def update_plot(_=None):
    ax_schem.clear()
    ax_info.clear()
    ax_info.axis("off")

    D = state["D"]
    try:
        res = solve_vehicle(state["prop1"], state["prop2"], state["dV1"], D=D)
    except Exception:
        res = {"converged": False, "M0": 0.0}

    if not res.get("converged", False) or not np.isfinite(res.get("M0", 0.0)) or res["M0"] <= 0 or res["M0"] > 1e9:
        ax_schem.set_xlim(-10, 10)
        ax_schem.set_ylim(0, 100)
        ax_schem.text(0, 50, "INFEASIBLE / DIVERGED\n(Adjust dV1 Split)", ha="center", va="center", fontsize=13, color="#d62828", fontweight="bold")
        fig.canvas.draw_idle()
        return

    s1, s2 = res["s1"], res["s2"]
    specs1 = get_stage_prop_specs(state["prop1"], 1)
    specs2 = get_stage_prop_specs(state["prop2"], 2)

    tanks1 = get_tank_dims(s1, D)
    tanks2 = get_tank_dims(s2, D)
    r_bot1, L_c_bot1, L_t_bot1, lbl_bot1, col_bot1 = tanks1[0]
    r_bot2, L_c_bot2, L_t_bot2, lbl_bot2, col_bot2 = tanks2[0]

    # --- STAGE 1 DRAWING ---
    z = 0.0
    draw_engines(ax_schem, z, s1["N_eng"], specs1["De"], D)

    # S1 Aft Fairing (straight cylinder of radius r_bot1 from z=0 to z=3 + r_bot1)
    draw_frustum(ax_schem, 0.0, r_bot1, 3.0 + r_bot1, r_bot1)
    z = 3.0
    draw_tank(ax_schem, z, r_bot1, L_c_bot1, col_bot1, f"S1 {lbl_bot1}")

    if len(tanks1) > 1:
        r_top1, L_c_top1, L_t_top1, lbl_top1, col_top1 = tanks1[1]
        z_eq_bot1 = z + r_bot1 + L_c_bot1
        z_eq_top1 = z + L_t_bot1 + r_top1
        draw_frustum(ax_schem, z_eq_bot1, r_bot1, z_eq_top1, r_top1)
        z += L_t_bot1
        draw_tank(ax_schem, z, r_top1, L_c_top1, col_top1, f"S1 {lbl_top1}")
        z_eq_top1_end = z + r_top1 + L_c_top1
        z += L_t_top1
    else:
        r_top1 = r_bot1
        z_eq_top1_end = z + r_bot1 + L_c_bot1
        z += L_t_bot1

    # S1 Interstage Skirt (slopes from S1 top tank equator r_top1 to S2 aft cylinder r_bot2)
    draw_frustum(ax_schem, z_eq_top1_end, r_top1, z, r_bot2, color="#adb5bd")

    # --- STAGE 2 DRAWING ---
    draw_engines(ax_schem, z, s2["N_eng"], specs2["De"], D)

    # S2 Aft Fairing (straight cylinder of radius r_bot2 from staging plane to S2 bottom tank equator)
    draw_frustum(ax_schem, z, r_bot2, z + 3.0 + r_bot2, r_bot2)
    z += 3.0
    draw_tank(ax_schem, z, r_bot2, L_c_bot2, col_bot2, f"S2 {lbl_bot2}")

    if len(tanks2) > 1:
        r_top2, L_c_top2, L_t_top2, lbl_top2, col_top2 = tanks2[1]
        z_eq_bot2 = z + r_bot2 + L_c_bot2
        z_eq_top2 = z + L_t_bot2 + r_top2
        draw_frustum(ax_schem, z_eq_bot2, r_bot2, z_eq_top2, r_top2)
        z += L_t_bot2
        draw_tank(ax_schem, z, r_top2, L_c_top2, col_top2, f"S2 {lbl_top2}")
        z_eq_top2_end = z + r_top2 + L_c_top2
        z += L_t_top2
    else:
        r_top2 = r_bot2
        z_eq_top2_end = z + r_bot2 + L_c_bot2
        z += L_t_bot2

    # --- PAYLOAD FAIRING ---
    r_plf = 2.6
    draw_frustum(ax_schem, z_eq_top2_end, r_top2, z, r_plf, color="#ced4da")
    draw_frustum(ax_schem, z, r_plf, z + 13.0, r_plf, color="#e9ecef")
    p_box = Rectangle((-2.2, z + 0.5), 4.4, 12.0, facecolor="#ffb703", edgecolor="black", ls="--", alpha=0.6)
    ax_schem.add_patch(p_box)
    ax_schem.text(0, z + 6.5, "Payload\n26,000 kg\n(5.2m x 13m)", ha="center", va="center", fontsize=8, fontweight="bold")
    draw_frustum(ax_schem, z + 13.0, r_plf, z + 18.2, 0.0, color="#e9ecef")

    ax_schem.set_xlim(-max(D, 10.0) * 0.85, max(D, 10.0) * 0.85)
    ax_schem.set_ylim(-3, res["L_total"] + 5)
    ax_schem.set_aspect("equal")
    ax_schem.set_title(f"2D Stack Cross-Section (L={res['L_total']:.1f}m, D={D:.1f}m)", fontweight="bold")
    ax_schem.set_xlabel("Radius (m)")
    ax_schem.set_ylabel("Height z (m)")
    ax_schem.grid(True, ls=":", alpha=0.5)

    # --- TELEMETRY & MASS SUMMARY PANEL ---
    feas = res["ld_ok"] and s1["engines_fit"] and s2["engines_fit"]
    status_str = "FEASIBLE CONFIGURATION" if feas else "CONSTRAINT VIOLATION"
    status_col = "#2a9d8f" if feas else "#d62828"

    info_text = (
        f"STATUS: {status_str}\n"
        f"{'='*42}\n"
        f"Gross Mass (M0):     {res['M0']/1000:,.1f} t  (Ideal: {res['ideal_M0']/1000:,.1f} t)\n"
        f"Mass Growth vs S1:   {res['mass_diff_pct']:+.1f}%\n"
        f"Total NRE Cost:      ${res['total_cost_M']/1000:.3f} B (FY2025)\n"
        f"  - Stage 1 NRE:     ${res['cost_s1_M']:,.0f} M\n"
        f"  - Stage 2 NRE:     ${res['cost_s2_M']:,.0f} M\n\n"
        f"GEOMETRY & CONSTRAINTS\n"
        f"{'='*42}\n"
        f"Total Length:        {res['L_total']:.1f} m\n"
        f"L/D Ratio:           {res['ld_ratio']:.2f} / 13.0  [{'OK' if res['ld_ok'] else 'FAIL'}]\n"
        f"S1 Engines ({s1['N_eng']:2d}):     Fit = {s1['engines_fit']}\n"
        f"S2 Engines ({s2['N_eng']:2d}):     Fit = {s2['engines_fit']}\n\n"
        f"SUBSYSTEM MASS BREAKDOWN (kg)\n"
        f"{'='*42}\n"
        f"Component            Stage 1          Stage 2\n"
        f"------------------------------------------\n"
        f"Propellant:     {s1['m_pr']:12,.0f}     {s2['m_pr']:12,.0f}\n"
        f"Tanks:          {s1['m_tank']:12,.0f}     {s2['m_tank']:12,.0f}\n"
        f"Insulation:     {s1['m_ins']:12,.0f}     {s2['m_ins']:12,.0f}\n"
        f"Casing (Solid): {s1['m_casing']:12,.0f}     {s2['m_casing']:12,.0f}\n"
        f"Engines:        {s1['m_eng']:12,.0f}     {s2['m_eng']:12,.0f}\n"
        f"Thrust Struct:  {s1['m_thrust_struct']:12,.0f}     {s2['m_thrust_struct']:12,.0f}\n"
        f"Gimbals:        {s1['m_gimbal']:12,.0f}     {s2['m_gimbal']:12,.0f}\n"
        f"Intertank:      {s1['m_intertank']:12,.0f}     {s2['m_intertank']:12,.0f}\n"
        f"Aft Fairing:    {s1['m_aft']:12,.0f}     {s2['m_aft']:12,.0f}\n"
        f"Interstage:     {s1['m_IS']:12,.0f}     {s2['m_IS']:12,.0f}\n"
        f"Payload Fair:   {s1['m_PLF']:12,.0f}     {s2['m_PLF']:12,.0f}\n"
        f"Avionics:       {s1['m_avionics']:12,.0f}     {s2['m_avionics']:12,.0f}\n"
        f"Wiring:         {s1['m_wiring']:12,.0f}     {s2['m_wiring']:12,.0f}\n"
        f"------------------------------------------\n"
        f"Dry Budgeted:   {s1['dry_budgeted']:12,.0f}     {s2['dry_budgeted']:12,.0f}\n"
        f"Inert Frac (d): {s1['delta_stage']:12.4f}     {s2['delta_stage']:12.4f}"
    )
    ax_info.text(0.02, 0.98, info_text, va="top", ha="left", family="monospace", fontsize=9,
                 bbox=dict(boxstyle="round,pad=0.5", facecolor="#f8f9fa", edgecolor=status_col, lw=2))
    fig.canvas.draw_idle()

ax_d = plt.axes([0.12, 0.14, 0.45, 0.03])
ax_dv = plt.axes([0.12, 0.09, 0.45, 0.03])
s_d = Slider(ax_d, "Core Diam D (m)", 3.0, 14.0, valinit=state["D"], valstep=0.1)
s_dv = Slider(ax_dv, "Stage 1 dV1 (m/s)", 2500.0, 8500.0, valinit=state["dV1"], valstep=1.0)

ax_p1 = plt.axes([0.65, 0.03, 0.14, 0.16], facecolor="#f1faee")
ax_p2 = plt.axes([0.81, 0.03, 0.14, 0.16], facecolor="#f1faee")
ax_p1.set_title("Stage 1 Prop", fontsize=9, fontweight="bold")
ax_p2.set_title("Stage 2 Prop", fontsize=9, fontweight="bold")
r_p1 = RadioButtons(ax_p1, prop_list, active=1)
r_p2 = RadioButtons(ax_p2, prop_list, active=1)

def on_slider(_):
    state["D"] = s_d.val
    state["dV1"] = s_dv.val
    update_plot()

def on_p1(label):
    state["prop1"] = label
    update_plot()

def on_p2(label):
    state["prop2"] = label
    update_plot()

s_d.on_changed(on_slider)
s_dv.on_changed(on_slider)
r_p1.on_clicked(on_p1)
r_p2.on_clicked(on_p2)

update_plot()
plt.show()