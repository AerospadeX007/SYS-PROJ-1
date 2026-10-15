"""
Author: Shaunn Pavelik (9/21/2026), Jacob Harmon (9/26/2026)
Heat map colors and labels updated for the TA's Submission 1 comment: Shaunn Pavelik (10/15/2026)
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, LogNorm
from matplotlib.patches import Rectangle
from matplotlib.ticker import NullFormatter

import TrueConst as T
from s1_make_csv import analyze_propellants_matrix
# from s1_format import sf

NAMES = T.PROPELLANT_NAMES
INITIALS = {"Gregory Kahn": "GK", "Henry Rowley": "HR", "Jacob Harmon": "JH",
            "Sharan Menon": "SM", "Shaunn Pavelik": "SP"}
SECOND_COLORS = {"LOX/LCH4": "#2a9d8f", "LOX/LH2": "#1f5fa8", "LOX/RP1": "#e76f51",
                 "SOLID": "#6b6b6b", "N2O4/UDMH": "#9b5de5"}
N_TOP = 3


def ranked(results, design="mass", key="m0_t"):
    """All 25 (first, second, value) sorted ascending."""
    rows = [(n1, n2, results[n1][n2][design][key]) for n1 in NAMES for n2 in NAMES]
    return sorted(rows, key=lambda r: r[2])


def _style():
    plt.rcParams.update({"font.size": 15, "axes.titlesize": 19, "axes.titleweight": "bold",
                         "axes.labelsize": 17, "savefig.dpi": 250, "savefig.bbox": "tight",
                         "font.family": "serif",
        # Palatino family to match the ENAE 483 lecture slides (falls back to any serif)
        "font.serif": ["Palatino Linotype", "Palatino", "TeX Gyre Pagella", "Book Antiqua", "DejaVu Serif"],
        "mathtext.fontset": "stix"})


def _sf3(v):
    """3 significant figures with thousands separators (1,270 / 10.1 / 111)."""
    r = float(f"{v:.3g}")
    return f"{r:,.0f}" if r >= 100 else f"{r:#.3g}"


def _cmap(name, lo=0.18):
    """Colormap without its near-white low end, so the cheapest/lightest cells still show color."""
    return LinearSegmentedColormap.from_list(f"{name}_from_{lo}", plt.get_cmap(name)(np.linspace(lo, 1.0, 256)))


def _show(n):
    return "Solid" if n == "SOLID" else n


def heatmaps(results, path):
    """Graphic 1 -- matrix heat maps with values printed in every cell."""
    _style()
    fig, axes = plt.subplots(1, 2, figsize=(20, 8.6))
    panels = [("mass", "m0_t", "Minimum-mass designs: gross LV mass (t)", "YlOrRd"),
              ("cost", "cost_B", "Minimum-cost designs: program NRE cost ($B2025)", "YlGnBu")]
    # cost map was PuBu: its pale low end washed out every design under ~$20B (TA comment on Sub 1).
    # Both maps now skip their white end (_cmap) so the low values stay visible.
    for ax, (design, key, title, cmap) in zip(axes, panels):
        # grid[row = second stage, col = first stage]
        grid = np.array([[results[n1][n2][design][key] for n1 in NAMES] for n2 in NAMES])
        im = ax.imshow(grid, cmap=_cmap(cmap), norm=LogNorm(grid.min(), grid.max()))
        for r in range(5):
            for c in range(5):
                v = grid[r, c]
                dark = np.log(v / grid.min()) > 0.6 * np.log(grid.max() / grid.min())
                ax.text(c, r, _sf3(v), ha="center", va="center", fontsize=15,
                        fontweight="bold", color="white" if dark else "black")
        top = ranked(results, design, key)[:N_TOP]
        # for rank, (n1, n2, _) in enumerate(top, 1): # we chose to remove this ranking thing
        #     c, r = NAMES.index(n1), NAMES.index(n2)
        #     ax.add_patch(Rectangle((c - .5, r - .5), 1, 1, fill=False, ec="#00a651", lw=4.5))
        #     ax.text(c + .42, r - .40, f"#{rank}", ha="right", va="top", fontsize=12,
        #             fontweight="bold", color="#00a651")
        ax.set_xticks(range(5), [f"{_show(n)}\n({INITIALS[T.COLUMN_OWNER[n]]})" for n in NAMES])
        ax.set_yticks(range(5), [_show(n) for n in NAMES])
        ax.set_xlabel("First-stage propellant (analyst)")
        ax.set_ylabel("Second-stage propellant")
        ax.set_title(title, pad=12)
        cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
        ticks = [t for t in (2e3, 5e3, 1e4, 2e4, 5e4, 1e5) if design == "mass"] or [10, 15, 20, 30, 50, 100]
        cb.set_ticks([t for t in ticks if grid.min() <= t <= grid.max()])
        cb.set_ticklabels([f"{t:,.0f}" for t in ticks if grid.min() <= t <= grid.max()])
        cb.minorticks_off()
        cb.ax.tick_params(labelsize=12)
    fig.suptitle("Vehicle-level trade study: all 25 propellant combinations",
                 fontsize=21, fontweight="bold", y=1.0)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


# Author Jacob Harmon
# 10/15/2026 (Pavelik): bigger fonts, dpi 300 and 'Solid' labels so the bars can be read on the slide
def ranked_designs(results, path):



    _style()
    # Top 10 by minimum mass
    top_mass = ranked(results, "mass", "m0_t")[:10]
    # Top 10 by minimum cost
    top_cost = ranked(results, "cost", "cost_B")[:10]
    fig, axes = plt.subplots(1, 2, figsize=(16, 8.4))
    fig.subplots_adjust(
        left=0.16,
        right=0.97,
        top=0.86,
        bottom=0.10,
        wspace=0.72
    )

    ax = axes[0]
    y = np.arange(len(top_mass))

    masses = []
    labels = []

    for i in range(len(top_mass)):

        n1 = top_mass[i][0]
        n2 = top_mass[i][1]
        m0 = top_mass[i][2]
        cost = results[n1][n2]["mass"]["cost_B"]

        masses.append(m0)
        labels.append(f"#{i+1}   {_show(n1)} / {_show(n2)}")

        if i < 3:
            color = "#2a9d55"
            edge = "#126b32"
            lw = 2.2
            weight = "bold"
        else:
            color = "#4472C4"
            edge = "black"
            lw = 0.8
            weight = "normal"

        ax.barh(
            i,
            m0,
            color=color,
            edgecolor=edge,
            linewidth=lw,
            height=0.72
        )

        ax.text(
            m0 * 1.05,
            i,
            f"{m0:,.0f} t   |   ${cost:.2f}B",
            va="center",
            ha="left",
            fontsize=16,
            fontweight=weight
        )

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=16)
    ax.invert_yaxis()
    for i in range(min(3, len(top_mass))):
        tick = ax.get_yticklabels()[i]
        tick.set_fontweight("bold")
        tick.set_color("#126b32")
    ax.set_xscale("log")
    ax.set_xlim(min(masses) * 0.8, max(masses) * 2.2)
    ax.set_xticks([1500, 2000, 3000, 5000], [f"{v:,}" for v in [1500, 2000, 3000, 5000]])      # plain labels, not 2x10^3
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.grid(axis="x", which="both", linestyle="--", alpha=0.25)
    ax.tick_params(axis="x", labelsize=14)
    ax.tick_params(axis="y", length=0)
    ax.set_title(
        "Top 10 Minimum-Mass Designs",
        fontsize=19,
        fontweight="bold",
        pad=10
    )
    ax.set_xlabel(
        "Minimum Gross Launch Vehicle Mass (t)  [log scale]",
        fontsize=16,
        fontweight="bold"
    )
    ax.set_ylabel(
        "Stage 1 / Stage 2 Propellant",
        fontsize=16,
        fontweight="bold"
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax = axes[1]

    y = np.arange(len(top_cost))
    costs = []
    labels = []
    for i in range(len(top_cost)):

        n1 = top_cost[i][0]
        n2 = top_cost[i][1]
        cost = top_cost[i][2]
        m0 = results[n1][n2]["cost"]["m0_t"]

        costs.append(cost)
        labels.append(f"#{i+1}   {_show(n1)} / {_show(n2)}")

        if i < 3:
            color = "#2a9d55"
            edge = "#126b32"
            lw = 2.2
            weight = "bold"
        else:
            color = "#4472C4"
            edge = "black"
            lw = 0.8
            weight = "normal"

        ax.barh(
            i,
            cost,
            color=color,
            edgecolor=edge,
            linewidth=lw,
            height=0.72
        )

        ax.text(
            cost * 1.05,
            i,
            f"${cost:.2f}B   |   {m0:,.0f} t",
            va="center",
            ha="left",
            fontsize=16,
            fontweight=weight
        )

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=16)
    ax.invert_yaxis()
    for i in range(min(3, len(top_cost))):
        tick = ax.get_yticklabels()[i]
        tick.set_fontweight("bold")
        tick.set_color("#126b32")
    ax.set_xscale("log")
    ax.set_xlim(min(costs) * 0.8, max(costs) * 2.2)
    ax.set_xticks([10, 12, 15, 20, 30], [f"{v:,}" for v in [10, 12, 15, 20, 30]])      # plain labels, not 2x10^3
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.grid(axis="x", which="both", linestyle="--", alpha=0.25)
    ax.tick_params(axis="x", labelsize=14)
    ax.tick_params(axis="y", length=0)
    ax.set_title(
        "Top 10 Minimum-Cost Designs",
        fontsize=19,
        fontweight="bold",
        pad=10
    )
    ax.set_xlabel(
        "Minimum Program Cost ($B2025)  [log scale]",
        fontsize=16,
        fontweight="bold"
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # The title
    fig.suptitle(
        "Top Launch Vehicle Designs by Mass and Cost",
        fontsize=23,
        fontweight="bold",
        y=0.99
    )

    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def section2_preview(results, n=5):
    """Rough look at what Section 2 will stress for the leading designs."""
    rho = {"LOX/LCH4": (3.6, T.LOX_rho_kg_m3, T.LCH4_rho_kg_m3),
           "LOX/LH2": (6.03, T.LOX_rho_kg_m3, T.LH2_rho_kg_m3),
           "LOX/RP1": (2.72, T.LOX_rho_kg_m3, T.RP1_rho_kg_m3),
           "N2O4/UDMH": (2.67, T.N2O4_rho_kg_m3, T.UDMH_rho_kg_m3)}
    out = []
    for n1, n2, m0 in ranked(results)[:n]:
        raw = results[n1][n2]["mass"]["raw"]
        thrust_req = T.thrust_weight_ratio_stage_1_min * raw["m_0"] * T.G0 / 1e6     # MN
        engines = int(np.ceil(thrust_req / T.PROPS[n1]["thrust_1st_stage_MN"]))
        if n1 == "Solid":
            vol = raw["m_pr_1"] / T.SOLID_rho_kg_m3
        else:
            of, rox, rfu = rho[n1]
            vol = raw["m_pr_1"] * (of / (of + 1)) / rox + raw["m_pr_1"] / (of + 1) / rfu
        out.append((n1, n2, m0, engines, vol))
    return out


if __name__ == "__main__":
    os.makedirs("figs", exist_ok=True)
    res = analyze_propellants_matrix()
    heatmaps(res, "figs/S1_5_graphic1_heatmaps.png")
    ranked_designs(res, "figs/S1_5_graphic2_ranked_designs.png")
    print("Top min-mass:", [(a, b, round(v)) for a, b, v in ranked(res)[:5]])
    print("Top min-cost:", [(a, b, round(v, 2)) for a, b, v in ranked(res, "cost", "cost_B")[:5]])
    for row in section2_preview(res):
        print("S2 preview %-9s/%-9s m0=%6.0f t  stage-1 engines=%2d  stage-1 prop vol=%6.0f m^3" % row)
