# ENAE 483 -- Section 2 auto graphs (anyone can run these for their own design)
# AUTHORS: Shaunn Pavelik (draft -- Greg, merge with yours or replace freely)
#
# Every function takes the dict from S2_1.run_systems_analysis() (or a propellant pair) and
# saves one PNG. Run main_section2.py to make all of them for every teammate's design.

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import utils.TrueConst as TrueConst
from s1.s1_1 import calculate_stage_masses
from s1.s1_3_cost import stage_cost
import S2_1

# one palette for every Section 2 figure
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
STAGE_COLOR = {1: "#2a78d6", 2: "#eb6834"}     # stage 1 blue, stage 2 orange
VL_COLOR, SL_COLOR = "#a8a7a1", "#2a78d6"      # vehicle level = gray reference, system = blue
DISPLAY = {"SOLID": "Solid", "N2O4/UDMH": "N2O4/UDMH", "LOX/LCH4": "LOX/LCH4",
           "LOX/LH2": "LOX/LH2", "LOX/RP1": "LOX/RP1"}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": INK2,
    "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
    "axes.titleweight": "bold", "axes.titlesize": 12, "figure.dpi": 100, "savefig.dpi": 200,
})

SUBSYSTEMS = [
    ("tank_mass", "Propellant tanks"), ("insulation_mass", "Tank insulation"),
    ("engine_mass", "Engines"), ("thrust_structure_mass", "Thrust structure"),
    ("casing_mass", "Solid casing"), ("gimbal_mass", "Gimbals"),
    ("avionics_mass", "Avionics"), ("wiring_mass", "Wiring"),
    ("payload_fairing_mass", "Payload fairing"), ("intertank_mass", "Inter-tank fairing"),
    ("interstage_mass", "Inter-stage fairing"), ("aft_fairing_mass", "Aft fairing"),
    ("margin_mass", "30% margin"),
]


def pair_name(s1, s2):
    return f"{DISPLAY[s1]} / {DISPLAY[s2]}"


def _save(fig, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


# ------------------------------------------------------------------
# Section 1 optimum splits (same model as s1, 1 m/s steps)
# ------------------------------------------------------------------
def section1_splits(stage1, stage2, dv_step=1.0):
    """Vehicle-level min-mass and min-cost delta-V1 for a pair (matches Section 1)."""
    p1, p2 = TrueConst.PROPS[stage1], TrueConst.PROPS[stage2]
    best_m = best_c = None
    dv = 100.0
    while dv < TrueConst.mission_delV_ms:
        r = calculate_stage_masses(dv, p1["inert_mass_fraction"], p2["inert_mass_fraction"],
                                   p1["isp_sea_level_s"], p2["isp_vacuum_s"],
                                   TrueConst.mission_delV_ms, TrueConst.pyld_mass_kg, TrueConst.G0)
        if not any(r["Error"]):
            c = stage_cost(r["m_in_1"]) + stage_cost(r["m_in_2"])
            if best_m is None or r["m_0"] < best_m["m_0"]:
                best_m = dict(dv1=dv, m_0=r["m_0"], cost=c)
            if best_c is None or c < best_c["cost"]:
                best_c = dict(dv1=dv, m_0=r["m_0"], cost=c)
        dv += dv_step
    return best_m, best_c


# ------------------------------------------------------------------
# 1. Subsystem breakdown of one design (S.2.2 table as a picture)
# ------------------------------------------------------------------
def plot_breakdown(res, path):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2))
    for ax, k in zip(axes, (1, 2)):
        st = res[f"stage_{k}"]
        rows = [(lab, st[key] / 1e3) for key, lab in SUBSYSTEMS if st[key] > 0]
        rows.sort(key=lambda t: t[1])
        labels, vals = zip(*rows)
        y = np.arange(len(vals))
        ax.barh(y, vals, height=0.62, color=STAGE_COLOR[k], edgecolor="white", linewidth=1)
        ax.set_yticks(y, labels)
        ax.grid(axis="y", visible=False)
        top = max(vals)
        for yi, v in zip(y, vals):
            ax.text(v + top * 0.015, yi, f"{v:,.1f} t", va="center", fontsize=9.5, color=INK2)
        ax.set_xlim(0, top * 1.22)
        ax.set_xlabel("Mass (t)")
        ax.set_title(f"Stage {k}: {DISPLAY[st['propellant_name']]}  "
                     f"(inert {st['dry_mass_with_margin']/1e3:,.1f} t incl. margin)", loc="left")
    fig.suptitle(f"System-level inert mass breakdown  |  {pair_name(res['stage_1_propellant'], res['stage_2_propellant'])}"
                 f"  |  ΔV₁ = {res['delta_v_1']/1e3:.2f} km/s", x=0.01, ha="left", fontsize=13,
                 fontweight="bold")
    fig.tight_layout()
    return _save(fig, path)


# ------------------------------------------------------------------
# 2. Vehicle level vs system level (mass and cost, never one dual axis)
# ------------------------------------------------------------------
def plot_vl_vs_sl(res, path):
    ideal = res["ideal"]
    vl_m = [(ideal["m_in_1"] + ideal["m_pr_1"]) / 1e3, (ideal["m_in_2"] + ideal["m_pr_2"]) / 1e3,
            ideal["m_0"] / 1e3]
    sl_m = [res["stage_1"]["stage_mass"] / 1e3, res["stage_2"]["stage_mass"] / 1e3,
            res["systems_gross_mass"] / 1e3]
    vl_c = [stage_cost(ideal["m_in_1"]) / 1e3, stage_cost(ideal["m_in_2"]) / 1e3,
            res["ideal_cost_musd"] / 1e3]
    sl_c = [res["stage_costs_musd"][0] / 1e3, res["stage_costs_musd"][1] / 1e3,
            res["systems_cost_musd"] / 1e3]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    x = np.arange(3)
    for ax, vl, sl, unit, ttl in ((axes[0], vl_m, sl_m, "t", "Mass (t)"),
                                  (axes[1], vl_c, sl_c, "$B", "NRE cost ($B, FY2025)")):
        ax.bar(x - 0.19, vl, 0.36, color=VL_COLOR, label="Vehicle level (Section 1, fixed δ)",
               edgecolor="white", linewidth=1.5)
        ax.bar(x + 0.19, sl, 0.36, color=SL_COLOR, label="System level (MERs + 30% margin)",
               edgecolor="white", linewidth=1.5)
        top = max(vl + sl)
        for xi, a, b in zip(x, vl, sl):
            fmt = (lambda v: f"{v:,.0f}") if unit == "t" else (lambda v: f"{v:.2f}")
            ax.text(xi - 0.19, a, fmt(a), ha="center", va="bottom", fontsize=9, color=INK2)
            ax.text(xi + 0.19, b, fmt(b), ha="center", va="bottom", fontsize=9, color=INK)
            ax.text(xi, max(a, b) + top * 0.075, f"{(b - a) / a * 100:+.0f}%", ha="center",
                    fontsize=10, fontweight="bold", color=INK)
        ax.set_xticks(x, ["Stage 1", "Stage 2", "Launch vehicle"])
        ax.set_ylabel(ttl)
        ax.set_ylim(0, top * 1.22)
        ax.grid(axis="x", visible=False)
    axes[0].set_title("Mass (stage = propellant + inert; LV includes 26 t payload)", loc="left")
    axes[1].set_title("Cost (13.52 · m_inert^0.55 per stage)", loc="left")
    axes[0].legend(loc="upper left", frameon=False, fontsize=9.5)
    fig.suptitle(f"Vehicle level vs system level  |  {pair_name(res['stage_1_propellant'], res['stage_2_propellant'])}"
                 f"  |  ΔV₁ = {res['delta_v_1']/1e3:.2f} km/s", x=0.01, ha="left", fontsize=13,
                 fontweight="bold")
    fig.tight_layout()
    return _save(fig, path)


# ------------------------------------------------------------------
# 3. delta-V split sweep at system level (does the Section 1 optimum still hold?)
# ------------------------------------------------------------------
def sweep_dv1(stage1, stage2, dv_step=50.0, enforce_engine_fit=S2_1.ENFORCE_ENGINE_FIT):
    rows = []
    dv = 200.0
    while dv < TrueConst.mission_delV_ms:
        best, _ = S2_1.choose_diameter(stage1, stage2, dv, enforce_engine_fit=enforce_engine_fit)
        p1, p2 = TrueConst.PROPS[stage1], TrueConst.PROPS[stage2]
        vl = calculate_stage_masses(dv, p1["inert_mass_fraction"], p2["inert_mass_fraction"],
                                    p1["isp_sea_level_s"], p2["isp_vacuum_s"],
                                    TrueConst.mission_delV_ms, TrueConst.pyld_mass_kg, TrueConst.G0)
        row = dict(dv1=dv, vl_m0=np.nan, vl_cost=np.nan, sl_m0=np.nan, sl_cost=np.nan, d=np.nan)
        if not any(vl["Error"]):
            row.update(vl_m0=vl["m_0"], vl_cost=stage_cost(vl["m_in_1"]) + stage_cost(vl["m_in_2"]))
        if best is not None:
            row.update(sl_m0=best["systems_gross_mass"], sl_cost=best["systems_cost_musd"],
                       d=best["vehicle_diameter"])
        rows.append(row)
        dv += dv_step
    return rows


def plot_dv1_sweep(stage1, stage2, rows, path):
    dv = np.array([r["dv1"] for r in rows]) / TrueConst.mission_delV_ms
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    for ax, vk, sk, ylab, is_mass in ((axes[0], "vl_m0", "sl_m0", "Gross liftoff mass (t)", True),
                                      (axes[1], "vl_cost", "sl_cost", "NRE cost ($B, FY2025)", False)):
        vl = np.array([r[vk] for r in rows]) / 1e3
        sl = np.array([r[sk] for r in rows]) / 1e3
        ax.plot(dv, vl, color=VL_COLOR, lw=2, ls="--", label="Vehicle level")
        ax.plot(dv, sl, color=SL_COLOR, lw=2, label="System level")
        notes = []
        for arr, col, name in ((vl, VL_COLOR, "Vehicle level"), (sl, SL_COLOR, "System level")):
            if np.isfinite(arr).any():
                i = np.nanargmin(arr)
                ax.plot(dv[i], arr[i], "o", ms=8, color=col, mec="white", mew=2, zorder=5)
                val = f"{arr[i]:,.0f} t" if is_mass else f"${arr[i]:.2f}B"
                notes.append(f"{name} min: {val} at ΔV₁ = {dv[i]*TrueConst.mission_delV_ms/1e3:.2f} km/s")
        ax.text(0.98, 0.97, "\n".join(notes), transform=ax.transAxes, ha="right", va="top",
                fontsize=9, color=INK2, bbox=dict(fc="white", ec=GRID, boxstyle="round,pad=0.4"))
        finite = np.concatenate([vl[np.isfinite(vl)], sl[np.isfinite(sl)]])
        if finite.size:
            ax.set_ylim(finite.min() * 0.85, finite.min() * 2.2)
        ok = np.isfinite(vl) | np.isfinite(sl)
        ax.set_xlim(max(0, dv[ok].min() - 0.03), min(1, dv[ok].max() + 0.03))
        ax.set_xlabel("ΔV₁ / ΔV_total")
        ax.set_ylabel(ylab)
    axes[0].legend(frameon=False, loc="upper left")
    fig.suptitle(f"Where is the best ΔV split once the MERs are in?  |  {pair_name(stage1, stage2)}",
                 x=0.01, ha="left", fontsize=13, fontweight="bold")
    fig.tight_layout()
    return _save(fig, path)


# ------------------------------------------------------------------
# 4. Side-view sketch with dimensions (CAD starting point)
# ------------------------------------------------------------------
def plot_vehicle_sketch(res, path):
    """Side view to scale: shells (aft fairing, inter-tank and inter-stage frustums, payload fairing),
    tanks (cylinder + domes, or spheres), the engine cluster and the 5.2 m x 13 m payload envelope.
    Engine cluster is drawn at the base width it needs (red if wider than the aft fairing)."""
    from matplotlib.patches import Wedge, Rectangle, Polygon, Circle
    D = res["vehicle_diameter"]
    eng = S2_1.ENGINE_LENGTH_M
    fig, ax = plt.subplots(figsize=(5.6, 10))
    y0 = 0.0
    for k in (1, 2):
        st = res[f"stage_{k}"]
        lay, col = st["layout"], STAGE_COLOR[k]
        # shells, bottom -> top
        z = y0
        for name, length, rb, rt, _ in lay["shells"]:
            if name == "payload fairing":
                r_plf = S2_1.PLF_DIAMETER_M / 2
                h_env = TrueConst.fairing["fairing_height_m"]
                nose = S2_1.NOSE_CONE_HEIGHT_TO_D * S2_1.PLF_DIAMETER_M
                za = y0 + eng + lay["tank_length"] - rb          # top tank's upper equator
                pts = [(-rb, za), (-r_plf, za + rb), (-r_plf, za + rb + h_env), (0, za + rb + h_env + nose),
                       (r_plf, za + rb + h_env), (r_plf, za + rb), (rb, za)]
                ax.add_patch(Polygon(pts, closed=True, fc="#f4f3f0", ec=INK2, lw=1.2, zorder=1))
                env = TrueConst.fairing
                ax.add_patch(Rectangle((-env["fairing_diameter_m3"] / 2, za + rb), env["fairing_diameter_m3"],
                                       h_env, fc="none", ec=INK2, lw=1, ls=":", zorder=4))
                ax.text(0, za + rb + h_env / 2, "payload\nenvelope", ha="center", va="center", fontsize=7.5,
                        color=INK2, zorder=4)
                continue
            if name == "aft fairing":
                z0 = y0
            elif name == "inter-tank fairing":
                t0 = lay["shells"][0][2]
                z0 = y0 + eng + st["geometry"]["tanks"][0]["length"] - t0
            else:   # inter-stage over stage 1's top dome
                z0 = y0 + eng + lay["tank_length"] - rb
            ax.add_patch(Polygon([(-rb, z0), (rb, z0), (rt, z0 + length), (-rt, z0 + length)], closed=True,
                                 fc="white", ec=INK2, lw=1.2, zorder=1))
        # tanks
        zt = y0 + eng
        for t in st["geometry"]["tanks"]:
            r, cyl = t["radius"] * 0.97, t["cyl_length"]
            if cyl > 0:
                ax.add_patch(Rectangle((-r, zt + t["radius"]), 2 * r, cyl, fc=col, alpha=0.35, ec="none", zorder=3))
                ax.add_patch(Wedge((0, zt + t["radius"]), r, 180, 360, fc=col, alpha=0.35, ec="none", zorder=3))
                ax.add_patch(Wedge((0, zt + t["radius"] + cyl), r, 0, 180, fc=col, alpha=0.35, ec="none", zorder=3))
            else:
                ax.add_patch(Circle((0, zt + t["radius"]), r, fc=col, alpha=0.35, ec="none", zorder=3))
            zt += t["length"]
        # engine cluster in the engine bay
        need = st["engine_base_diameter_needed"] / 2
        fit_col = INK2 if st["engines_fit"] else "#e34948"
        ax.add_patch(Polygon([(-need, y0), (-need * 0.45, y0 + eng), (need * 0.45, y0 + eng), (need, y0)],
                             fc=fit_col, alpha=0.5, ec="none", zorder=2))
        label = (f"Stage {k}: {DISPLAY[st['propellant_name']]}\n{st['stage_length']:.1f} m long\n"
                 f"{st['number_of_engines']} x {st['engine_name']}\n{st['stage_mass']/1e3:,.0f} t")
        ax.text(D / 2 + 1.0, y0 + st["stage_length"] / 2 - (6 if k == 2 else 0), label, va="center",
                fontsize=9, color=INK)
        y0 += st["stage_length"]
    total = res["vehicle_length"]
    ax.annotate("", (-D / 2 - 1.2, 0), (-D / 2 - 1.2, total), arrowprops=dict(arrowstyle="<->", color=INK, lw=1.2))
    ax.text(-D / 2 - 1.7, total / 2, f"{total:.1f} m\nL/D = {res['length_to_diameter']:.1f}", ha="right",
            va="center", fontsize=10, color=INK)
    ax.annotate("", (-D / 2, -1.8), (D / 2, -1.8), arrowprops=dict(arrowstyle="<->", color=INK, lw=1.2))
    ax.text(0, -3.6, f"D = {D:.1f} m", ha="center", fontsize=10)
    ax.set_xlim(-D / 2 - 11, D / 2 + 12)
    ax.set_ylim(-5, total + 2)
    ax.set_aspect("equal")
    ax.axis("off")
    note = "" if res["engines_fit"] else "\nred: engines need a wider base than the aft fairing"
    ax.set_title(f"{pair_name(res['stage_1_propellant'], res['stage_2_propellant'])}  |  "
                 f"\u0394V\u2081 = {res['delta_v_1']/1e3:.2f} km/s\nsystem-level sketch to scale{note}", fontsize=10.5)
    return _save(fig, path)




# ------------------------------------------------------------------
# 4b. Group graphic: the five individual designs, vehicle vs system level
# ------------------------------------------------------------------
def plot_team_designs(team, path):
    """team: list of dicts with who, s1, s2, kind ('min-mass'/'min-cost'), vl_m0, sl_m0 [kg],
    vl_cost, sl_cost [$M]. Left: gross mass of each min-mass design. Right: cost of each
    min-cost design (each design judged on the thing it was optimized for)."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2))
    for ax, kind, vk, sk, scale, ylab, fmt in (
            (axes[0], "min-mass", "vl_m0", "sl_m0", 1e3, "Gross liftoff mass (t)", "{:,.0f}"),
            (axes[1], "min-cost", "vl_cost", "sl_cost", 1e3, "NRE cost ($B, FY2025)", "{:.2f}")):
        rows = [t for t in team if t["kind"] == kind]
        x = np.arange(len(rows))
        vl = np.array([t[vk] for t in rows]) / scale
        sl = np.array([t[sk] for t in rows]) / scale
        ax.bar(x - 0.19, vl, 0.36, color=VL_COLOR, edgecolor="white", linewidth=1.5,
               label="Vehicle level (Section 1)")
        ax.bar(x + 0.19, sl, 0.36, color=SL_COLOR, edgecolor="white", linewidth=1.5,
               label="System level (MERs + 30% margin)")
        top = max(np.nanmax(vl), np.nanmax(sl))
        best = int(np.nanargmin(sl))
        for xi, a, b in zip(x, vl, sl):
            ax.text(xi + 0.19, b, fmt.format(b), ha="center", va="bottom", fontsize=8.5,
                    color=INK, fontweight="bold" if xi == best else "normal")
            ax.text(xi, max(a, b) + top * 0.07, f"{(b - a) / a * 100:+.0f}%", ha="center",
                    fontsize=10, fontweight="bold", color=INK)
        ax.set_xticks(x, [f"{DISPLAY[t['s1']]}\n/ {DISPLAY[t['s2']]}\n({t['who'].split()[-1]})"
                          for t in rows], fontsize=9)
        ax.set_ylabel(ylab)
        ax.set_ylim(0, top * 1.2)
        ax.grid(axis="x", visible=False)
    axes[0].set_title("Min-mass designs: gross mass", loc="left")
    axes[1].set_title("Min-cost designs: program cost", loc="left")
    axes[0].legend(loc="upper left", frameon=False, fontsize=9)
    fig.suptitle("Team 3 individual designs (stage 1 / stage 2), vehicle level vs system level",
                 x=0.01, ha="left", fontsize=13, fontweight="bold")
    fig.tight_layout()
    return _save(fig, path)


# ------------------------------------------------------------------
# 4c. Group graphic: the ten team designs on mass vs cost (S.2.3), VL -> SL arrows
# ------------------------------------------------------------------
def plot_team_scatter(team, path, picks=(), xlim=(1200, 2250), ylim=(9.8, 12.8)):
    """team: dicts with who, s1, s2, kind, vl_m0, sl_m0 [kg], vl_cost, sl_cost [$M], fit (bool).
    Gray dot = vehicle level, arrow to the system-level point. Hollow = engines don't fit the stage.
    picks: (who, kind) pairs to ring and label as the group's selections. Designs outside the
    window (the solid first stage) are listed in a box instead of squashing the plot."""
    names = list(dict.fromkeys(t["who"] for t in team))
    cols = dict(zip(names, ["#2a78d6", "#1baf7a", "#eb6834", "#8e5bb5", "#e0a526"]))
    fig, ax = plt.subplots(figsize=(11, 6.2))
    off = []
    for t in team:
        c = cols[t["who"]]
        x0, y0 = t["vl_m0"] / 1e3, t["vl_cost"] / 1e3
        x1, y1 = t["sl_m0"] / 1e3, t["sl_cost"] / 1e3
        if not (xlim[0] <= x1 <= xlim[1] and ylim[0] <= y1 <= ylim[1]):
            off.append(f"{DISPLAY[t['s1']]} / {DISPLAY[t['s2']]} {t['kind']}: {x1:,.0f} t, ${y1:.2f}B")
            continue
        ax.annotate("", (x1, y1), (x0, y0), arrowprops=dict(arrowstyle="-|>", color=c, lw=1.3, alpha=0.6))
        ax.plot(x0, y0, "o", ms=6, color=VL_COLOR, zorder=3)
        mk = "o" if t["kind"] == "min-mass" else "s"
        ax.plot(x1, y1, mk, ms=11, mec=c, mew=2.2, mfc=c if t["fit"] else "white", zorder=4)
        if (t["who"], t["kind"]) in picks:
            ax.plot(x1, y1, "o", ms=26, mfc="none", mec=INK, mew=1.6, zorder=5)
            ax.annotate(f"{x1:,.0f} t, ${y1:.2f}B", (x1, y1), xytext=(14, -22), textcoords="offset points",
                        fontsize=10, fontweight="bold", color=INK)
    for w in names:
        s = next(t for t in team if t["who"] == w)
        ax.plot([], [], "o", ms=9, color=cols[w], label=f"{DISPLAY[s['s1']]} / {DISPLAY[s['s2']]} ({w.split()[-1]})")
    ax.plot([], [], "o", ms=6, color=VL_COLOR, label="vehicle level (Section 1)")
    ax.plot([], [], "o", ms=9, mfc="white", mec=INK2, mew=2, label="engines don't fit the stage")
    ax.plot([], [], "s", ms=9, mfc=INK2, mec=INK2, label="square = min-cost, circle = min-mass")
    ax.legend(frameon=False, fontsize=9.5, loc="upper left")
    if off:
        ax.text(0.99, 0.97, "Off the chart:\n" + "\n".join(off), transform=ax.transAxes, ha="right", va="top",
                fontsize=9, color=INK2, bbox=dict(fc="white", ec=GRID, boxstyle="round,pad=0.4"))
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_xlabel("Gross liftoff mass (t)")
    ax.set_ylabel("NRE program cost ($B, FY2025)")
    ax.set_title("Team 3 designs: vehicle level (gray) to system level (color); ringed = group picks", loc="left")
    fig.tight_layout()
    return _save(fig, path)


# ------------------------------------------------------------------
# 5. Group graphic: system-level growth over vehicle level, all 25 pairs
# ------------------------------------------------------------------
def plot_group_matrix(rows, path, key="mass"):
    """rows: list of dicts with stage1, stage2, vl_m0, sl_m0 (None if it does not close)."""
    names = TrueConst.PROPELLANT_NAMES
    grid = np.full((5, 5), np.nan)
    text = [["" for _ in names] for _ in names]
    for r in rows:
        i, j = names.index(r["stage2"]), names.index(r["stage1"])   # rows = stage 2, cols = stage 1
        if r["sl_m0"] is None:
            text[i][j] = "does not\nclose"
            continue
        g = (r["sl_m0"] / r["vl_m0"] - 1) * 100
        grid[i, j] = g
        text[i][j] = f"{r['sl_m0']/1e3:,.0f} t\n{g:+.0f}%"
    fig, ax = plt.subplots(figsize=(8.6, 6.4))
    from matplotlib.colors import TwoSlopeNorm, LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("div", ["#2a78d6", "#f0efec", "#e34948"])
    lim = np.nanmax(np.abs(grid)) if np.isfinite(grid).any() else 1
    lim = 50.0   # cap the color scale so the -15%..+50% spread is readable; labels carry exact values
    im = ax.imshow(np.clip(grid, -lim, lim), cmap=cmap, norm=TwoSlopeNorm(0, -lim, lim))
    for i in range(5):
        for j in range(5):
            ax.text(j, i, text[i][j], ha="center", va="center", fontsize=9,
                    color=INK if np.isfinite(grid[i, j]) else INK2)
            if not np.isfinite(grid[i, j]):
                ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, fc="#f7f6f3", ec="none"))
    ax.set_xticks(range(5), [DISPLAY[n] for n in names])
    ax.set_yticks(range(5), [DISPLAY[n] for n in names])
    ax.set_xlabel("First stage")
    ax.set_ylabel("Second stage")
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, shrink=0.8)
    cb.set_label("Change vs vehicle level (%, color capped at ±50)")
    ax.set_title("System-level gross mass at each pair's Section 1 min-mass ΔV₁", loc="left")
    fig.tight_layout()
    return _save(fig, path)
