# Section 2 update (Shaunn, 10/8)

This folder is the whole repo (GitHub commit 6b2c438 + the Section 2 changes), so it runs on its own.

1. Right-click the zip > **Extract All** (don't run files from inside the zip - Windows only
   pulls out the one file you clicked, so the imports fail).
2. One time: `python -m pip install numpy matplotlib` (use the same python VS Code runs).
3. VS Code > File > Open Folder > `SYS-PROJ-1`, open `main_section2.py`, press Run.
   It works from any terminal folder; outputs always land next to the script.

Takes about 2 minutes. It writes `csvs/` and `figs/` for every pair in `CHOSEN_PAIRS`
(right now everyone's Section 1 pair: own column over LOX/LH2), plus the all-25 table and
two group graphics. Change your pair at the top of `main_section2.py` if you switch.

## What you get

| Output | For |
|---|---|
| `csvs/S2_2_table_of_masses_<pair>_dv1_<dv1>.csv` | S.2.2 table, every value with units, 4 s.f. (min-mass and min-cost split) |
| `figs/S2_2_<pair>_<mass/cost>_breakdown.png` | subsystem masses, both stages |
| `figs/S2_2_<pair>_<mass/cost>_vl_vs_sl.png` | system level vs Section 1 vehicle level, mass and cost |
| `figs/S2_2_<pair>_<mass/cost>_sketch.png` | dimensioned side view (CAD starting point) |
| `figs/S2_2_<pair>_dv1_sweep.png` | does the Section 1 split still hold at system level? |
| `figs/S2_group_team_designs.png` | group graphic: our five designs, VL vs SL |
| `figs/S2_group_matrix_mass.png` | group graphic: all 25 pairs |
| `csvs/S2_all25_system_level.csv` | all 25 pairs x both splits: mass, cost, D, L, L/D, engines |

## Files

| File | What changed |
|---|---|
| `S2_1.py` | Fixed the crash, put the real Lecture 8 MERs in, delta-V closure, stage layout and fairings, diameter pick |
| `S2_2.py` | Cost now on inert mass in kg (same as Section 1); units on every row; one CSV per design |
| `S2_auto_graph.py` | New: breakdown, vehicle vs system level, delta-V sweep, vehicle sketch, team + all-25 graphics. Greg: merge with yours or replace |
| `main_section2.py` | New: runs everything |

## Bugs fixed in what was on GitHub (commit 6b2c438)

1. **Crash:** `mer_insulation_mass(geometry["total_tank_area"], info["needs_insulation"])` - the function now takes `(geometry, info)` and liquids had no `total_tank_area` key, so every liquid stage threw `KeyError`.
2. **Placeholder MERs:** engines, thrust structure, solid casing, gimbals, avionics, wiring and every fairing were "TEMPORARY EQUATION"s. All now use Lecture 8 (slide refs in the code).
3. **Delta-V not met:** the loop kept the Section 1 propellant fixed, so once the inert mass changed the vehicle no longer delivered 12.3 km/s (Shaunn's design came out 308 m/s short). Each pass now re-solves propellant from the rocket equation. `close_delta_v=False` still gives the old behavior.
4. **S2_2 cost:** used total stage mass (propellant included) in tonnes. The cost relation is on inert mass in kg -> $M, same as `s1_3_cost.stage_cost`.
5. **Tank geometry:** Greg's domed area kept; length was still a flat cylinder, and tanks smaller than one sphere gave a negative cylinder length. Now consistent, and small tanks become spheres.
6. **Payload fairing** was a 13 m cone at 5.2 m diameter - the payload envelope (5.2 m x 13 m) would not fit. Now a cylinder over the envelope plus a nose cone.
7. **Diameter** was 5.2 m, which is the payload envelope itself. Now 5.6 m minimum (0.2 m clearance), then the lightest diameter that meets L/D <= 13.

## MER check

Lecture 8 (public F24 deck, 483F24L08): tanks slide 7, insulation slide 9, fairings/avionics/wiring
slide 22, areas slide 23, engines/thrust structure/casing slide 27, gimbals slide 28. Check the
slide numbers against our F26 deck before they go on a slide.

Reproduces every number in the Lecture 8 SSTO example: engines 2236 kg, gimbals 81 kg, avionics
744 kg, wiring 886 kg, payload fairing 645 kg, thrust structure 497 kg. The engine MER needs
`sqrt(Ae/At)` and the wiring MER needs `L^0.25` to hit those (the PDF text drops both).

Insulation (Greg's question): the MER is kg per m^2 of tank area (2.88 LH2, 1.123 LOX/LCH4), so
it works for any tank shape. The lecture's spheres were only its first-pass geometry.

## Assumptions now in the code (10/14, after Henry's S2_1_HCR comparison)

| Item | Setting | Why |
|---|---|---|
| LOX/LH2 upper-stage engine | J-2X: 1.307 MN, Isp 448 s, 92:1, O/F 5.5, Pc 9.23 MPa, exit 3.05 m (`TrueConst.J2X`, cited) | Table 2's 0.099 MN engine needed 20-45 engines; team picked J-2X 10/12. `USE_J2X_UPPER_STAGE` |
| Avionics | One set on stage 2, sized on gross liftoff mass | MER is a whole-vehicle relation; per-stage double counted (Henry). `AVIONICS_MODE` |
| Payload fairing | 5.2 m cylinder over the 13 m envelope + adapter frustum over the top dome + cone (h = 5.2 m) | Was a full-diameter cylinder, bigger than needed (Henry). `PAYLOAD_RADIAL_CLEARANCE_M`, `NOSE_CONE_HEIGHT_TO_D` |
| Shells | Aft fairing over the 3 m engine bay + bottom dome; frustum inter-tank; inter-stage over stage 1's top dome; tanks dome to dome | Stage 2's engine bay is already inside its aft fairing. `INTERSTAGE_OVER_UPPER_ENGINE_BAY = True` switches to Henry's 10/14 S2_1_HCR length (top dome + 3 m + stage 2 bottom dome) |
| Diameter | Lightest D (0.1 m steps, from 5.2 m) with L/D <= 13 and engines that fit in the aft fairing; if none fits up to 25 m, lightest L/D-OK design, flagged | CAD needs real engine counts. `ENFORCE_ENGINE_FIT` |

`python S2_crosscheck_HCR.py` runs our tool and Henry's on all ten team designs at the same
diameter with Henry's J-2X inputs: since Henry's 10/14 evening fix to the inter-stage length they
agree to 0.000% in mass and cost on all 8 designs that close in both.

## Two ways to make the S.2.2 tables (pick one for the slides)
`main_section2.py` sizes every design with `S2_1.py`; `S2_2.py` (10/14 night) sizes them with
`S2_1_HCR.py`. Both write the same `csvs/S2_2_table_of_masses_*.csv` names, so whichever ran last is
what's in `csvs/`. The tools agree on the same inputs; the numbers differ only because of:

| | main_section2.py (S2_1) | S2_2.py (S2_1_HCR) |
|---|---|---|
| "Vehicle level" row | Section 1 result (Table 2 Isp 452 s), same as T.4/T.5 | Section 1 relations re-run with the J-2X's 448 s |
| Diameter search | 5.2-25 m; engines must fit under the aft fairing; if none fit, lightest L/D-OK design, flagged | 5.2-13 m; engines checked against D; if none fit, returns the 13 m design |
| J-2X O/F, chamber pressure | 5.5, 9.23 MPa (cited) | 6.03 (Table 2 LOX/LH2), 9.1 MPa |
| LOX/RP1 and solid first stages | 7.0-7.9 m, flagged "engines don't fit" | 13 m, engines don't fit |

The group slides use main_section2.py.

## Still open
- LOX/RP1 and solid first stages (Jacob, Sharan): the Table 2 engines (3.7 m and 6.6 m exits)
  never fit under the stage. Options: cite a smaller-nozzle engine (e.g. Merlin 1D for RP-1), or
  report them as flagged.
- Payload fairing carried for the whole stage 2 burn (conservative) vs dropped early.
