# Create a Systems-Level Analysis Tool (Group). Using a first stage ∆V1 value as an
# input variable and the mass estimating relations from class, create a script that returns the masses
# for each sub-system in a stage. This will sum to the mass for each stage. You will be finding the
# two total stage masses separately, summing those to the total gross mass for the launch vehicle,
# and comparing this number to the solutions found in the vehicle-level design section. Again, the
# group must meaningfully collaborate on this tool
#
# Authors: Jacob Harmon   (structure, iteration loop, printing)
#          Gregory Kahn   (tank area with domed end caps, tank + insulation + engine MERs)
#          Henry Rowley   (shell geometry: frustum inter-tank/inter-stage, payload fairing sized to the
#                          payload envelope, one avionics set, J-2X upper stage -- from S2_1_HCR.py)
#          Sharan Menon   (S2_2 table of masses that reads this file's output)
#          Shaunn Pavelik (Lecture 8 MERs, delta-V closure, diameter pick with engine fit, merging)
#
# MER source: ENAE 483 Lecture 8, Mass Estimating Relations. Slide numbers below are from the
# public F24 deck (483F24L08) -- check them against our F26 slides before they go on a slide.
#
# to run: python S2_1.py   (from the repo root)

import math

import utils.TrueConst as TrueConst
from s1.s1_1 import calculate_stage_masses
from s1.s1_3_cost import stage_cost


# ============================================================
# 1. USER INPUTS
# ============================================================

# Change these to the selected design.
STAGE_1_PROPELLANT = "N2O4/UDMH"
STAGE_2_PROPELLANT = "LOX/LH2"

# Selected Stage 1 Delta-V from Section 1 (min-mass split for this pair, g0 = 9.8).
DELTA_V_1 = 3750.0  # m/s


# ============================================================
# 2. PRELIMINARY DESIGN ASSUMPTIONS  (team decisions, 10/12-10/14)
# ============================================================

MASS_MARGIN = 0.30             # Required 30 % margin on every MER-estimated inert mass
ENGINE_LENGTH_M = 3.0          # Assignment: engines are 3 m long (engine bay in each stage's aft fairing)

# Researched engine swap (Table 2 caption): J-2X replaces the 0.099 MN Table 2 engine on LOX/LH2
# upper stages. False = use Table 2 for everything.
USE_J2X_UPPER_STAGE = True
UPPER_STAGE_ENGINES = {"LOX/LH2": TrueConst.J2X}

# Avionics MER is a whole-vehicle relation (slide 22, M0 = gross mass). "vehicle" = one avionics
# set, carried by stage 2, sized on gross liftoff mass (no double counting). "per_stage" = each
# stage sized on its own ignition mass (our first version).
AVIONICS_MODE = "vehicle"

# Payload fairing: cylinder over the 5.2 m x 13 m payload envelope, an adapter frustum over stage 2's
# top dome, and a cone nose of height = fairing diameter. Radial clearance adds to each side.
PAYLOAD_RADIAL_CLEARANCE_M = 0.0
NOSE_CONE_HEIGHT_TO_D = 1.0     # cone height / fairing diameter

# Vehicle diameter. None = pick automatically (choose_diameter below): the lightest
# diameter that meets L/D <= 13 and fits the engines in the aft fairing.
STAGE_1_DIAMETER_M = None
STAGE_2_DIAMETER_M = None
ENFORCE_ENGINE_FIT = True       # if no diameter fits, falls back to L/D only and flags it

PLF_DIAMETER_M = TrueConst.fairing["fairing_diameter_m3"] + 2 * PAYLOAD_RADIAL_CLEARANCE_M
D_MIN_M = PLF_DIAMETER_M        # stages at least as wide as the payload fairing (no hammerhead)
D_MAX_M = 25.0
D_STEP_M = 0.1

CONVERGENCE_TOLERANCE = 1e-9   # stop when gross mass changes by less than this fraction
MAX_ITERATIONS = 500           # prevent an infinite loop
DIVERGED_MASS_KG = 1e10        # anything heavier than this never closes


# ============================================================
# 3. PROPELLANT INFORMATION
# ============================================================

# Most propulsion information already exists in TrueConst.
# This dictionary adds information useful for the systems model.
# tank_coeff  [kg/m^3]  Lecture 8 slide 7:  LH2 9.09, everything else 12.16
# ins_coeff   [kg/m^2]  Lecture 8 slide 9:  LH2 2.88, LOX and LCH4 1.123, others none

PROPELLANT_INFO = {
    "LOX/LCH4": {
        "data": TrueConst.LOX_LCH4, "mixture_ratio": 3.6,
        "oxidizer_density": TrueConst.LOX_rho_kg_m3, "fuel_density": TrueConst.LCH4_rho_kg_m3,
        "is_solid": False, "needs_insulation": True,
        "ins_coeff_ox": 1.123, "ins_coeff_fuel": 1.123,
        "tank_coeff_ox": 12.16, "tank_coeff_fuel": 12.16
    },
    "LOX/LH2": {
        "data": TrueConst.LOX_LH2, "mixture_ratio": 6.03,
        "oxidizer_density": TrueConst.LOX_rho_kg_m3, "fuel_density": TrueConst.LH2_rho_kg_m3,
        "is_solid": False, "needs_insulation": True,
        "ins_coeff_ox": 1.123, "ins_coeff_fuel": 2.88,
        "tank_coeff_ox": 12.16, "tank_coeff_fuel": 9.09
    },
    "LOX/RP1": {
        "data": TrueConst.LOX_RP1, "mixture_ratio": 2.72,
        "oxidizer_density": TrueConst.LOX_rho_kg_m3, "fuel_density": TrueConst.RP1_rho_kg_m3,
        "is_solid": False, "needs_insulation": True,
        "ins_coeff_ox": 1.123, "ins_coeff_fuel": 0.0,
        "tank_coeff_ox": 12.16, "tank_coeff_fuel": 12.16
    },
    "SOLID": {
        "data": TrueConst.SOLID, "mixture_ratio": None,
        "solid_density": TrueConst.SOLID_rho_kg_m3,
        "is_solid": True, "needs_insulation": False,
    },
    "N2O4/UDMH": {
        "data": TrueConst.N2O4_UDMH, "mixture_ratio": 2.67,
        "oxidizer_density": TrueConst.N2O4_rho_kg_m3, "fuel_density": TrueConst.UDMH_rho_kg_m3,
        "is_solid": False, "needs_insulation": False,
        "ins_coeff_ox": 0.0, "ins_coeff_fuel": 0.0,
        "tank_coeff_ox": 12.16, "tank_coeff_fuel": 12.16
    },
}


def stage_engine(propellant_name, stage_number):
    """Engine used on this stage: Table 2, or the researched upper-stage engine.

    Returns thrust [N], Isp [s] (sea level for stage 1, vacuum for stage 2), chamber pressure [Pa],
    expansion ratio, exit diameter [m], O/F mixture ratio and a name for tables.
    """
    if stage_number == 2 and USE_J2X_UPPER_STAGE and propellant_name in UPPER_STAGE_ENGINES:
        e = UPPER_STAGE_ENGINES[propellant_name]
        return {"name": e["name"], "thrust_n": e["thrust_vac_MN"] * 1e6, "isp_s": e["isp_vacuum_s"],
                "chamber_pressure_pa": e["chamber_pressure_MPa"] * 1e6,
                "expansion_ratio": e["expansion_ratio"], "exit_diameter_m": e["exhaust_diameter_m"],
                "mixture_ratio": e["mixture_ratio"]}
    data = PROPELLANT_INFO[propellant_name]["data"]
    k = "1st" if stage_number == 1 else "2nd"
    return {"name": "Table 2", "thrust_n": data[f"thrust_{k}_stage_MN"] * 1e6,
            "isp_s": data["isp_sea_level_s"] if stage_number == 1 else data["isp_vacuum_s"],
            "chamber_pressure_pa": data[f"chamber_pressure_{k}_stage_MPa"] * 1e6,
            "expansion_ratio": data[f"expansion_ratio_{k}_stage"],
            "exit_diameter_m": data[f"exhaust_diameter_{k}_stage_m"],
            "mixture_ratio": PROPELLANT_INFO[propellant_name]["mixture_ratio"]}


# ============================================================
# 4. BASIC GEOMETRY FUNCTIONS  (Lecture 8 slide 23 areas)
# ============================================================

def cylinder_side_area(length: float, diameter: float) -> float:
    """Slide 23: A = 2 pi r h."""
    return math.pi * diameter * length


def cone_side_area(radius: float, height: float) -> float:
    """Slide 23: A = pi r sqrt(r^2 + h^2)."""
    slant_height = math.sqrt(radius**2 + height**2)
    return math.pi * radius * slant_height


def frustum_side_area(radius_1: float, radius_2: float, height: float) -> float:
    """Slide 23: A = pi (r1 + r2) sqrt((r1 - r2)^2 + h^2). Equals the cylinder when r1 = r2."""
    return math.pi * (radius_1 + radius_2) * math.sqrt((radius_1 - radius_2)**2 + height**2)


def tank_shape(volume, diameter):
    """Tank = cylinder with two hemispherical end caps (no flat end caps, per the CAD section).

    If the propellant fits in less than one sphere of the stage diameter, the tank is a
    smaller sphere instead (a negative cylinder length would otherwise give a negative area).

    Returns volume, wetted area, cylinder length, radius, total length (dome apex to apex).
    """
    r = diameter / 2
    v_sphere = (4 / 3) * math.pi * r**3
    if volume >= v_sphere:
        cyl = (volume - v_sphere) / (math.pi * r**2)
        return {"volume": volume, "area": math.pi * diameter * cyl + 4 * math.pi * r**2,
                "cyl_length": cyl, "radius": r, "end_height": r, "length": cyl + diameter,
                "diameter": diameter, "shape": "cylinder + domes"}
    d = (6 * volume / math.pi) ** (1 / 3)
    return {"volume": volume, "area": math.pi * d**2, "cyl_length": 0.0, "radius": d / 2,
            "end_height": d / 2, "length": d, "diameter": d, "shape": "sphere"}


def tank_area(volume, diameter):
    """Area of a tank with a cylinder and two dome-shaped endcaps"""
    return tank_shape(volume, diameter)["area"]


# Smallest circle that holds n equal circles, as (enclosing radius / circle radius).
# Known optimal packings for n = 1..20; beyond that ~1.15 sqrt(n).
_PACK_RATIO = [1.0, 2.0, 2.1547, 2.4142, 2.7013, 3.0, 3.0, 3.3048, 3.6131, 3.8130,
               3.9238, 4.0296, 4.2361, 4.3284, 4.5214, 4.6154, 4.7920, 4.8637, 4.8637, 5.1223]


def engine_base_diameter(number_of_engines, exit_diameter):
    """Diameter needed to fit n nozzle exits side by side in the stage base."""
    n = number_of_engines
    k = _PACK_RATIO[n - 1] if n <= len(_PACK_RATIO) else 1.15 * math.sqrt(n)
    return k * exit_diameter


# ============================================================
# 5. PROPELLANT MASS AND VOLUME
# ============================================================

def calculate_propellant_geometry(propellant_name, propellant_mass, stage_diameter,
                                  mixture_ratio=None):
    """Split propellant, size each tank. tanks[] is ordered bottom -> top: the wider tank goes on
    the bottom (fuel first if they're the same width), so shells only narrow going up."""

    info = PROPELLANT_INFO[propellant_name]

    # Solid motor: the grain fills a cylinder-with-domes case
    if info["is_solid"]:
        solid_volume = propellant_mass / info["solid_density"]
        case = tank_shape(solid_volume, stage_diameter)
        return {
            "oxidizer_mass": 0, "fuel_mass": 0, "solid_mass": propellant_mass,
            "oxidizer_volume": 0, "fuel_volume": 0, "solid_volume": solid_volume,
            "oxidizer_length": 0, "fuel_length": 0, "solid_length": case["length"],
            "oxidizer_area": 0, "fuel_area": 0, "solid_area": case["area"],
            "total_tank_length": case["length"],
            "total_tank_area": case["area"],
            "tanks": [dict(case, contents="solid grain")],
        }

    # Liquid propulsion
    mr = info["mixture_ratio"] if mixture_ratio is None else mixture_ratio
    fuel_mass = propellant_mass / (mr + 1)
    oxidizer_mass = propellant_mass - fuel_mass

    oxidizer_volume = oxidizer_mass / info["oxidizer_density"]
    fuel_volume = fuel_mass / info["fuel_density"]

    fuel_tank = dict(tank_shape(fuel_volume, stage_diameter), contents="fuel")
    oxidizer_tank = dict(tank_shape(oxidizer_volume, stage_diameter), contents="oxidizer")
    tanks = ([fuel_tank, oxidizer_tank] if fuel_tank["radius"] >= oxidizer_tank["radius"]
             else [oxidizer_tank, fuel_tank])

    return {
        "oxidizer_mass": oxidizer_mass, "fuel_mass": fuel_mass, "solid_mass": 0,
        "oxidizer_volume": oxidizer_volume, "fuel_volume": fuel_volume, "solid_volume": 0,
        "oxidizer_length": oxidizer_tank["length"], "fuel_length": fuel_tank["length"],
        "solid_length": 0,
        "oxidizer_area": oxidizer_tank["area"], "fuel_area": fuel_tank["area"], "solid_area": 0,
        "total_tank_length": oxidizer_tank["length"] + fuel_tank["length"],
        "total_tank_area": oxidizer_tank["area"] + fuel_tank["area"],
        "mixture_ratio": mr,
        "tanks": tanks,
    }


def stage_layout(stage_number, geometry, upper_bottom_radius=None):
    """Axial layout of one stage and the fairing (shell) area of each section, bottom -> top.

    Both stages:  aft fairing = cylinder at the bottom tank's radius over the 3 m engine bay plus the
                  bottom dome | bottom tank | inter-tank frustum from the bottom tank's equator to the
                  top tank's equator | top tank
    Stage 1 top:  inter-stage frustum over stage 1's top dome, out to stage 2's aft fairing radius
                  (dropped with stage 1)
    Stage 2 top:  payload fairing = adapter frustum over the top dome, cylinder over the 13 m payload
                  envelope, cone nose of height = fairing diameter
    Tanks touch dome to dome, so stage length = engine bay + tank lengths (+ fairing on stage 2).
    """
    tanks = geometry["tanks"]
    r_bot, r_top = tanks[0]["radius"], tanks[-1]["radius"]
    tank_length = sum(t["length"] for t in tanks)
    shells = []   # (name, length, r_bottom, r_top, area), bottom -> top

    aft_length = ENGINE_LENGTH_M + r_bot
    shells.append(("aft fairing", aft_length, r_bot, r_bot,
                   cylinder_side_area(aft_length, 2 * r_bot)))

    intertank_length = 0.0
    if len(tanks) == 2:
        intertank_length = r_bot + r_top
        shells.append(("inter-tank fairing", intertank_length, r_bot, r_top,
                       frustum_side_area(r_bot, r_top, intertank_length)))

    if stage_number == 1:
        r_up = upper_bottom_radius if upper_bottom_radius else r_top
        top_length = r_top
        shells.append(("inter-stage fairing", top_length, r_top, r_up,
                       frustum_side_area(r_top, r_up, top_length)))
        added_length = 0.0                      # inter-stage covers the top dome only
    else:
        r_plf = PLF_DIAMETER_M / 2
        nose = NOSE_CONE_HEIGHT_TO_D * PLF_DIAMETER_M
        h_env = TrueConst.fairing["fairing_height_m"]
        adapter = frustum_side_area(r_top, r_plf, r_top)
        barrel = cylinder_side_area(h_env, PLF_DIAMETER_M)
        cone = cone_side_area(r_plf, nose)
        shells.append(("payload fairing", r_top + h_env + nose, r_top, 0.0, adapter + barrel + cone))
        added_length = h_env + nose             # adapter sits over the top dome
        top_length = r_top + h_env + nose

    stage_length = ENGINE_LENGTH_M + tank_length + added_length
    area = {name: a for name, _, _, _, a in shells}
    return {
        "aft_length": aft_length,
        "aft_area": area["aft fairing"],
        "intertank_length": intertank_length,
        "intertank_area": area.get("inter-tank fairing", 0.0),
        "top_length": top_length,
        "top_area": area.get("inter-stage fairing", area.get("payload fairing", 0.0)),
        "tank_length": tank_length,
        "bottom_radius": r_bot,
        "top_radius": r_top,
        "shells": shells,
        "stage_length": stage_length,
    }


# ============================================================
# 6. REQUIRED THRUST AND ENGINE COUNT
# ============================================================

def calculate_engine_count(stage_number, propellant_name, supported_mass):
    """Engines needed so T/W >= 1.3 (stage 1) or 0.76 (stage 2) at ignition (M5)."""

    if stage_number == 1:
        thrust_to_weight = TrueConst.thrust_weight_ratio_stage_1_min
    else:
        thrust_to_weight = TrueConst.thrust_weight_ratio_stage_n_min
    thrust_per_engine_n = stage_engine(propellant_name, stage_number)["thrust_n"]

    required_thrust_n = thrust_to_weight * supported_mass * TrueConst.G0
    number_of_engines = math.ceil(required_thrust_n / thrust_per_engine_n)

    return {
        "required_thrust_n": required_thrust_n,
        "required_thrust_mn": required_thrust_n / 1e6,
        "thrust_per_engine_n": thrust_per_engine_n,
        "number_of_engines": number_of_engines,
    }


# ============================================================
# 7. MASS ESTIMATING RELATIONS  (Lecture 8)
# ============================================================
# All masses in kg, thrust in N, pressure in Pa, area in m^2, volume in m^3, length in m.

def mer_tank_mass(geometry, info):
    """Slide 7: M = 9.09 V (LH2), M = 12.16 V (all other liquids)."""
    if info["is_solid"]:
        return 0

    ox_tank_mass = info["tank_coeff_ox"] * geometry["oxidizer_volume"]
    fuel_tank_mass = info["tank_coeff_fuel"] * geometry["fuel_volume"]
    return ox_tank_mass + fuel_tank_mass


def mer_insulation_mass(geometry, info):
    """Slide 9: M = 2.88 A (LH2), M = 1.123 A (LOX, LCH4). Per unit of tank wetted area, so it
    works for any tank shape -- the lecture's spheres were only the first-pass geometry."""
    if not info["needs_insulation"]:
        return 0

    ox_ins_mass = info["ins_coeff_ox"] * geometry["oxidizer_area"]
    fuel_ins_mass = info["ins_coeff_fuel"] * geometry["fuel_area"]
    return ox_ins_mass + fuel_ins_mass


def mer_engine_mass(propellant_name, number_of_engines, thrust_per_engine_n, expansion_ratio):
    """Slide 27: M = 7.81e-4 T + 3.37e-5 T sqrt(Ae/At) + 59, per engine.
    (The square root reproduces the lecture example: 6 x 324.9 kN at Ae/At = 30 -> 2236 kg.)
    Solid stages have no separate engine mass (the casing MER covers the motor)."""
    if PROPELLANT_INFO[propellant_name]["is_solid"]:
        return 0

    T = thrust_per_engine_n
    mass_per_engine = 7.81e-4 * T + 3.37e-5 * T * math.sqrt(expansion_ratio) + 59
    return number_of_engines * mass_per_engine


def mer_thrust_structure_mass(total_installed_thrust_n):
    """Slide 27: M = 2.55e-4 T, T = total installed thrust."""
    return 2.55e-4 * total_installed_thrust_n


def mer_solid_casing_mass(propellant_name, propellant_mass):
    """Slide 27: M = 0.135 M_propellant. Only applies to solids."""
    if not PROPELLANT_INFO[propellant_name]["is_solid"]:
        return 0
    return 0.135 * propellant_mass


def mer_gimbal_mass(number_of_engines, thrust_per_engine_n, chamber_pressure_pa):
    """Slide 28: M = 237.8 (T / P0)^0.9375, per engine. Applied to solids too:
    a solid still needs thrust vector control (moving nozzle)."""
    mass_per_gimbal = 237.8 * (thrust_per_engine_n / chamber_pressure_pa) ** 0.9375
    return number_of_engines * mass_per_gimbal


def mer_avionics_mass(initial_mass):
    """Slide 22: M = 10 M0^0.361, M0 = gross mass (the lecture example uses gross liftoff mass)."""
    return 10 * initial_mass ** 0.361


def mer_wiring_mass(stage_initial_mass, stage_length):
    """Slide 22: M = 1.058 sqrt(M0) L^0.25, M0 = mass this stage lifts, L = stage length."""
    return 1.058 * math.sqrt(stage_initial_mass) * stage_length ** 0.25


def mer_fairing_mass(area):
    """Slide 22: M = 4.95 A^1.15 -- payload, inter-tank, inter-stage and aft fairings."""
    return 4.95 * area ** 1.15 if area > 0 else 0.0


def mer_intertank_mass(layout):
    return mer_fairing_mass(layout["intertank_area"])


def mer_interstage_mass(layout):
    return mer_fairing_mass(layout["top_area"])


def mer_aft_fairing_mass(layout):
    return mer_fairing_mass(layout["aft_area"])


def mer_payload_fairing_mass(layout):
    return mer_fairing_mass(layout["top_area"])


# ============================================================
# 8. CALCULATE ONE STAGE
# ============================================================

def calculate_stage_subsystems(stage_number, propellant_name, propellant_mass,
                               stage_initial_mass, stage_diameter, upper_bottom_radius=None,
                               gross_mass=None):
    """Subsystem masses for one stage.

    stage_initial_mass : mass at this stage's ignition (this stage + everything above it).
                         Sets the engine count (T/W) and the wiring MER.
    gross_mass         : gross liftoff mass of the whole vehicle (avionics, AVIONICS_MODE "vehicle").
    """
    info = PROPELLANT_INFO[propellant_name]
    engine = stage_engine(propellant_name, stage_number)

    geometry = calculate_propellant_geometry(propellant_name, propellant_mass, stage_diameter,
                                             engine["mixture_ratio"])
    layout = stage_layout(stage_number, geometry, upper_bottom_radius)
    stage_length = layout["stage_length"]

    # Required thrust
    engine_data = calculate_engine_count(stage_number, propellant_name, stage_initial_mass)
    number_of_engines = engine_data["number_of_engines"]
    thrust_per_engine_n = engine_data["thrust_per_engine_n"]
    total_installed_thrust_n = number_of_engines * thrust_per_engine_n
    base_needed = engine_base_diameter(number_of_engines, engine["exit_diameter_m"])
    aft_diameter = 2 * layout["bottom_radius"]

    # Subsystem masses
    tank_mass = mer_tank_mass(geometry, info)
    insulation_mass = mer_insulation_mass(geometry, info)
    engine_mass = mer_engine_mass(propellant_name, number_of_engines, thrust_per_engine_n,
                                  engine["expansion_ratio"])
    thrust_structure_mass = mer_thrust_structure_mass(total_installed_thrust_n)
    casing_mass = mer_solid_casing_mass(propellant_name, propellant_mass)
    gimbal_mass = mer_gimbal_mass(number_of_engines, thrust_per_engine_n,
                                  engine["chamber_pressure_pa"])
    if AVIONICS_MODE == "vehicle":     # one set, in stage 2, sized on gross liftoff mass
        avionics_mass = (mer_avionics_mass(gross_mass if gross_mass else stage_initial_mass)
                         if stage_number == 2 else 0.0)
    else:
        avionics_mass = mer_avionics_mass(stage_initial_mass)
    wiring_mass = mer_wiring_mass(stage_initial_mass, stage_length)
    intertank_mass = mer_intertank_mass(layout)
    aft_fairing_mass = mer_aft_fairing_mass(layout)

    # Stage 1 / Stage 2 interstage is carried (and dropped) by Stage 1.
    interstage_mass = mer_interstage_mass(layout) if stage_number == 1 else 0

    # Payload fairing is carried by Stage 2 (conservative: kept for the whole burn).
    payload_fairing_mass = mer_payload_fairing_mass(layout) if stage_number == 2 else 0

    # Dry mass
    dry_mass_without_margin = (
        tank_mass + insulation_mass + engine_mass + thrust_structure_mass
        + casing_mass + gimbal_mass + avionics_mass + wiring_mass
        + payload_fairing_mass + intertank_mass + interstage_mass + aft_fairing_mass
    )

    # 30% mass margin
    margin_mass = MASS_MARGIN * dry_mass_without_margin
    dry_mass_with_margin = dry_mass_without_margin + margin_mass

    # Total stage mass
    stage_mass = dry_mass_with_margin + propellant_mass

    return {
        "stage_number": stage_number,
        "propellant_name": propellant_name,
        "engine_name": engine["name"],
        "propellant_mass": propellant_mass,
        "tank_mass": tank_mass,
        "insulation_mass": insulation_mass,
        "engine_mass": engine_mass,
        "thrust_structure_mass": thrust_structure_mass,
        "casing_mass": casing_mass,
        "gimbal_mass": gimbal_mass,
        "avionics_mass": avionics_mass,
        "wiring_mass": wiring_mass,
        "payload_fairing_mass": payload_fairing_mass,
        "intertank_mass": intertank_mass,
        "interstage_mass": interstage_mass,
        "aft_fairing_mass": aft_fairing_mass,
        "dry_mass_without_margin": dry_mass_without_margin,
        "margin_mass": margin_mass,
        "dry_mass_with_margin": dry_mass_with_margin,
        "stage_mass": stage_mass,
        "stage_length": stage_length,
        "stage_diameter": stage_diameter,
        "required_thrust_mn": engine_data["required_thrust_mn"],
        "installed_thrust_mn": total_installed_thrust_n / 1e6,
        "number_of_engines": number_of_engines,
        "engine_base_diameter_needed": base_needed,
        "engines_fit": base_needed <= aft_diameter + 1e-9,
        "geometry": geometry,
        "layout": layout,
    }


# ============================================================
# 9. COMPLETE VEHICLE ITERATION
# ============================================================

def _size_vehicle(stage_1_propellant, stage_2_propellant, delta_v_1, d1, d2,
                  close_delta_v=True, verbose=False):
    """Converged system-level vehicle for one delta-V split and fixed diameters.

    close_delta_v=True : every pass re-solves the propellant from the rocket equation with
        the new MER inert mass, so the finished vehicle still delivers 12.3 km/s.
    close_delta_v=False: keeps the Section 1 propellant masses fixed (the original loop).
        Faster to explain but the vehicle no longer delivers the required delta-V.
    """
    p1 = PROPELLANT_INFO[stage_1_propellant]["data"]
    p2 = PROPELLANT_INFO[stage_2_propellant]["data"]
    m_pl = TrueConst.pyld_mass_kg
    g0 = TrueConst.G0
    delta_v_2 = TrueConst.mission_delV_ms - delta_v_1

    # First pass: Section 1 vehicle-level mass model (Table 2 Isp and delta)
    ideal = calculate_stage_masses(
        dV_1=delta_v_1,
        delta_1=p1["inert_mass_fraction"],
        delta_2=p2["inert_mass_fraction"],
        isp_1=p1["isp_sea_level_s"],
        isp_2=p2["isp_vacuum_s"],
        dV_tot=TrueConst.mission_delV_ms,
        m_pl=m_pl,
        g_0=g0,
    )
    if any(ideal["Error"]):
        return None  # split is infeasible even at vehicle level

    # mass ratio r = m_final / m_initial each stage must reach (rocket equation), with the Isp of
    # the engine each stage actually uses (J-2X: 448 s vs Table 2's 452 s)
    isp_1 = stage_engine(stage_1_propellant, 1)["isp_s"]
    isp_2 = stage_engine(stage_2_propellant, 2)["isp_s"]
    r1 = math.exp(-delta_v_1 / (g0 * isp_1))
    r2 = math.exp(-delta_v_2 / (g0 * isp_2))

    m_pr_1, m_pr_2 = ideal["m_pr_1"], ideal["m_pr_2"]
    m_0_2, m_0 = ideal["m_0_2"], ideal["m_0"]

    converged = diverged = False
    iteration = 0
    while iteration < MAX_ITERATIONS:
        iteration += 1

        # Stage 2 pushes itself plus the payload.
        stage_2 = calculate_stage_subsystems(2, stage_2_propellant, m_pr_2, m_0_2, d2,
                                             gross_mass=m_0)
        if close_delta_v:
            m_f_2 = m_pl + stage_2["dry_mass_with_margin"]
            m_0_2_new = m_f_2 / r2
            m_pr_2 = m_0_2_new - m_f_2
        else:
            m_0_2_new = m_pl + stage_2["stage_mass"]

        # Stage 1 lifts the entire vehicle.
        stage_1 = calculate_stage_subsystems(1, stage_1_propellant, m_pr_1, m_0, d1,
                                             stage_2["layout"]["bottom_radius"], gross_mass=m_0)
        if close_delta_v:
            m_f_1 = m_0_2_new + stage_1["dry_mass_with_margin"]
            m_0_new = m_f_1 / r1
            m_pr_1 = m_0_new - m_f_1
        else:
            m_0_new = m_0_2_new + stage_1["stage_mass"]

        error = abs(m_0_new - m_0) / m_0
        if verbose:
            print(f"Iteration {iteration:3d}: gross mass {m_0_new:,.1f} kg  change {error*100:.2e} %")
        m_0, m_0_2 = m_0_new, m_0_2_new

        if not math.isfinite(m_0) or m_0 > DIVERGED_MASS_KG or m_pr_1 <= 0 or m_pr_2 <= 0:
            diverged = True
            break
        if error < CONVERGENCE_TOLERANCE:
            converged = True
            break

    if diverged or not converged:
        return {"converged": False, "diverged": diverged, "iterations": iteration,
                "delta_v_1": delta_v_1, "ideal": ideal}

    # Final pass so every reported number comes from the converged masses
    stage_2 = calculate_stage_subsystems(2, stage_2_propellant, m_pr_2, m_0_2, d2, gross_mass=m_0)
    stage_1 = calculate_stage_subsystems(1, stage_1_propellant, m_pr_1, m_0, d1,
                                         stage_2["layout"]["bottom_radius"], gross_mass=m_0)
    systems_gross_mass = stage_1["stage_mass"] + stage_2["stage_mass"] + m_pl

    # delta-V the finished vehicle actually delivers (check on the closure)
    m02 = stage_2["stage_mass"] + m_pl
    dv2_check = g0 * isp_2 * math.log(m02 / (m02 - m_pr_2))
    dv1_check = g0 * isp_1 * math.log(systems_gross_mass / (systems_gross_mass - m_pr_1))
    vehicle_length = stage_1["stage_length"] + stage_2["stage_length"]
    cost_1 = stage_cost(stage_1["dry_mass_with_margin"])   # $M (FY2025), inert mass in kg
    cost_2 = stage_cost(stage_2["dry_mass_with_margin"])
    ideal_cost = stage_cost(ideal["m_in_1"]) + stage_cost(ideal["m_in_2"])

    return {
        "converged": True,
        "diverged": False,
        "iterations": iteration,
        "stage_1_propellant": stage_1_propellant,
        "stage_2_propellant": stage_2_propellant,
        "delta_v_1": delta_v_1,
        "delta_v_2": delta_v_2,
        "delta_v_delivered": dv1_check + dv2_check,
        "ideal": ideal,
        "stage_1": stage_1,
        "stage_2": stage_2,
        "ideal_gross_mass": ideal["m_0"],
        "systems_gross_mass": systems_gross_mass,
        "ideal_cost_musd": ideal_cost,
        "systems_cost_musd": cost_1 + cost_2,
        "stage_costs_musd": (cost_1, cost_2),
        "effective_inert_fraction": (stage_1["dry_mass_with_margin"] / systems_gross_mass,
                                     stage_2["dry_mass_with_margin"] / m02),
        "vehicle_length": vehicle_length,
        "vehicle_diameter": max(d1, d2),
        "length_to_diameter": vehicle_length / max(d1, d2),
        "ld_ok": vehicle_length / max(d1, d2) <= TrueConst.L_D,
        "engines_fit": stage_1["engines_fit"] and stage_2["engines_fit"],
        "close_delta_v": close_delta_v,
    }


def choose_diameter(stage_1_propellant, stage_2_propellant, delta_v_1,
                    enforce_engine_fit=ENFORCE_ENGINE_FIT, close_delta_v=True):
    """Sweep one vehicle diameter from the payload fairing diameter up, keep designs that close and
    meet L/D <= 13 (and fit their engines, if enforced), and return the lightest. If no diameter
    up to D_MAX fits the engines, return the lightest L/D-feasible design with fit_fallback=True.
    Also returns the whole sweep for plotting."""
    sweep = []
    d = D_MIN_M
    while d <= D_MAX_M + 1e-9:
        res = _size_vehicle(stage_1_propellant, stage_2_propellant, delta_v_1, d, d,
                            close_delta_v)
        if res is not None and res["converged"]:
            sweep.append(res)
        d = round(d + D_STEP_M, 6)

    ld = [r for r in sweep if r["ld_ok"]]
    if not ld:
        return None, sweep
    fit = [r for r in ld if r["engines_fit"]]
    if enforce_engine_fit and fit:
        best = dict(min(fit, key=lambda r: r["systems_gross_mass"]), fit_fallback=False)
    else:
        best = dict(min(ld, key=lambda r: r["systems_gross_mass"]),
                    fit_fallback=enforce_engine_fit and not fit)
    return best, sweep


def run_systems_analysis(stage_1_propellant, stage_2_propellant, delta_v_1,
                         stage_1_diameter=STAGE_1_DIAMETER_M,
                         stage_2_diameter=STAGE_2_DIAMETER_M,
                         close_delta_v=True, verbose=False):
    """
    Run the full systems-level calculation.

    The Section 1 vehicle-level result is the starting guess. Each pass recomputes every
    subsystem with the MERs, adds the 30 % margin, re-solves the propellant for the
    required delta-V, and recounts engines for T/W, until the gross mass stops changing.

    Diameters of None -> pick the lightest diameter that meets L/D and engine fit.
    Returns None if the split is infeasible, or a dict with converged=False if it diverges.
    """
    fallback = False
    if stage_1_diameter is None or stage_2_diameter is None:
        best, _ = choose_diameter(stage_1_propellant, stage_2_propellant, delta_v_1,
                                  close_delta_v=close_delta_v)
        if best is None:
            return None
        stage_1_diameter = stage_2_diameter = best["vehicle_diameter"]
        fallback = best["fit_fallback"]

    res = _size_vehicle(stage_1_propellant, stage_2_propellant, delta_v_1,
                        stage_1_diameter, stage_2_diameter, close_delta_v, verbose)
    if res is not None and res["converged"]:
        res["fit_fallback"] = fallback
    return res


# ============================================================
# 10. PRINT ONE STAGE
# ============================================================

def print_stage_results(stage):

    print()
    print("=" * 60)
    print("STAGE", stage["stage_number"], "-", stage["propellant_name"],
          f"({stage['engine_name']} engines)")
    print("=" * 60)

    print("Propellant:", round(stage["propellant_mass"], 2), "kg")
    print("Propellant tanks:", round(stage["tank_mass"], 2), "kg")
    print("Tank insulation:", round(stage["insulation_mass"], 2), "kg")
    print("Engines:", round(stage["engine_mass"], 2), "kg")
    print("Thrust structure:", round(stage["thrust_structure_mass"], 2), "kg")
    print("Solid casing:", round(stage["casing_mass"], 2), "kg")
    print("Gimbals:", round(stage["gimbal_mass"], 2), "kg")
    print("Avionics:", round(stage["avionics_mass"], 2), "kg")
    print("Wiring:", round(stage["wiring_mass"], 2), "kg")
    print("Payload fairing:", round(stage["payload_fairing_mass"], 2), "kg")
    print("Inter-tank fairing:", round(stage["intertank_mass"], 2), "kg")
    print("Inter-stage fairing:", round(stage["interstage_mass"], 2), "kg")
    print("Aft fairing:", round(stage["aft_fairing_mass"], 2), "kg")

    print("-" * 60)

    print("Dry mass before margin:", round(stage["dry_mass_without_margin"], 2), "kg")
    print("30% mass margin:", round(stage["margin_mass"], 2), "kg")
    print("Dry mass with margin:", round(stage["dry_mass_with_margin"], 2), "kg")

    print()
    print("TOTAL STAGE MASS:", round(stage["stage_mass"], 2), "kg")

    print()
    print("Required thrust:", round(stage["required_thrust_mn"], 3), "MN")
    print("Number of engines:", stage["number_of_engines"],
          f"(need {stage['engine_base_diameter_needed']:.2f} m of base,",
          "fits)" if stage["engines_fit"] else "DOES NOT FIT)")
    print("Stage length:", round(stage["stage_length"], 2), "m")


# ============================================================
# 11. PRINT VEHICLE RESULTS
# ============================================================

def print_vehicle_results(results):

    if results is None:
        print("ERROR: no feasible design (split infeasible, or no diameter meets L/D).")
        return
    if not results["converged"]:
        print("WARNING: the MER inert mass is too heavy for this split -- the design diverges.")
        return

    print_stage_results(results["stage_1"])
    print_stage_results(results["stage_2"])

    print()
    print("=" * 60)
    print("VEHICLE SUMMARY")
    print("=" * 60)

    print("Stage 1 Delta-V:", round(results["delta_v_1"], 2), "m/s")
    print("Stage 2 Delta-V:", round(results["delta_v_2"], 2), "m/s")
    print("Delta-V delivered by the sized vehicle:", round(results["delta_v_delivered"], 2), "m/s")

    print()
    print("Vehicle-level ideal gross mass:", round(results["ideal_gross_mass"], 2), "kg")
    print("Systems-level gross mass:", round(results["systems_gross_mass"], 2), "kg")

    mass_difference = results["systems_gross_mass"] - results["ideal_gross_mass"]
    percent_difference = mass_difference / results["ideal_gross_mass"] * 100

    print("Mass difference:", round(mass_difference, 2), "kg")
    print("Percent difference:", round(percent_difference, 2), "%")
    print("Vehicle-level cost:", round(results["ideal_cost_musd"] / 1e3, 3), "$B (FY2025)")
    print("Systems-level cost:", round(results["systems_cost_musd"] / 1e3, 3), "$B (FY2025)")

    print()
    print("Diameter:", round(results["vehicle_diameter"], 2), "m   Length:",
          round(results["vehicle_length"], 2), "m   L/D:", round(results["length_to_diameter"], 2),
          "(OK)" if results["ld_ok"] else "(EXCEEDS 13)")
    if results.get("fit_fallback"):
        print("NOTE: no diameter up to", D_MAX_M, "m fits the engines; shown at the lightest L/D-OK diameter.")
    print("Solution converged after", results["iterations"], "iterations.")


# ============================================================
# 12. RUN PROGRAM
# ============================================================

if __name__ == "__main__":

    results = run_systems_analysis(
        stage_1_propellant=STAGE_1_PROPELLANT,
        stage_2_propellant=STAGE_2_PROPELLANT,
        delta_v_1=DELTA_V_1,
    )

    print_vehicle_results(results)
