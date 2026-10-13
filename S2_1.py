# Create a Systems-Level Analysis Tool (Group). Using a first stage ∆V1 value as an
# input variable and the mass estimating relations from class, create a script that returns the masses
# for each sub-system in a stage. This will sum to the mass for each stage. You will be finding the
# two total stage masses separately, summing those to the total gross mass for the launch vehicle,
# and comparing this number to the solutions found in the vehicle-level design section. Again, the
# group must meaningfully collaborate on this tool

# Authors: Jacob Harmon, 


# Authors: Jacob Harmon,

import math

import utils.TrueConst as TrueConst
from s1.s1_1 import calculate_stage_masses


# ============================================================
# 1. USER INPUTS
# ============================================================

# Change these to the selected design.
STAGE_1_PROPELLANT = "LOX/RP1"
STAGE_2_PROPELLANT = "LOX/RP1"

# Selected Stage 1 Delta-V from Section 1.
DELTA_V_1 = 6000.0  # m/s


# ============================================================
# 2. PRELIMINARY DESIGN ASSUMPTIONS
# ============================================================

MASS_MARGIN = 0.30             # Required final design mass margin
ENGINE_LENGTH_M = 3.0          # Assignment: engines are 3 m long
STAGE_1_DIAMETER_M = 5.2       # Preliminary diameters, replace later
STAGE_2_DIAMETER_M = 5.2
INTERTANK_LENGTH_M = 1.0       # Assumed distance between fuel and oxidizer tanks
CONVERGENCE_TOLERANCE = 0.001  # Stop when gross mass changes by less than 0.1%
MAX_ITERATIONS = 50            # Prevent an infinite loop


# ============================================================
# 3. PROPELLANT INFORMATION
# ============================================================

# Most propulsion information already exists in TrueConst.
# This dictionary adds information useful for the systems model.

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
        "tank_coeff_ox": 12.16, "tank_coeff_fuel": 12.16
    },
}


# ============================================================
# 4. BASIC GEOMETRY FUNCTIONS
# ============================================================

# possibly deprecated
def cylinder_length(volume: float, diameter: float) -> float:
    """Length of a cylindrical tank: L = V / (pi * r^2)."""
    radius = diameter / 2
    return volume / (math.pi * radius**2)

# possibly deprecated
def cylinder_side_area(length: float, diameter: float) -> float:
    return math.pi * diameter * length

# possibly deprecated
def cone_side_area(radius: float, height: float) -> float:
    slant_height = math.sqrt(radius**2 + height**2)
    return math.pi * radius * slant_height

def tank_area(volume, diameter):
    """Area of a tank with a cylinder and two dome-shaped endcaps"""
    V = volume
    D = diameter
    r = D / 2

    V_domes = (4 / 3) * math.pi * r**3
    L_cyl = (V - V_domes) / (math.pi * r**2)
    A = math.pi * D * L_cyl + 4 * math.pi * r**2
    return A


# ============================================================
# 5. PROPELLANT MASS AND VOLUME
# ============================================================

def calculate_propellant_geometry(propellant_name, propellant_mass, stage_diameter):

    info = PROPELLANT_INFO[propellant_name]

    # Solid motor
    if info["is_solid"]:
        solid_volume = propellant_mass / info["solid_density"]
        solid_length = cylinder_length(solid_volume, stage_diameter)
        solid_area = cylinder_side_area(solid_length, stage_diameter)

        return {
            "oxidizer_mass": 0, "fuel_mass": 0, "solid_mass": propellant_mass,
            "oxidizer_volume": 0, "fuel_volume": 0, "solid_volume": solid_volume,
            "oxidizer_length": 0, "fuel_length": 0, "solid_length": solid_length,
            "oxidizer_area": 0, "fuel_area": 0, "solid_area": solid_area,
            "total_tank_length": solid_length,
            "total_tank_area": solid_area,
        }

    # Liquid propulsion
    fuel_mass = propellant_mass / (info["mixture_ratio"] + 1)
    oxidizer_mass = propellant_mass - fuel_mass

    oxidizer_volume = oxidizer_mass / info["oxidizer_density"]
    fuel_volume = fuel_mass / info["fuel_density"]

    oxidizer_length = cylinder_length(oxidizer_volume, stage_diameter)
    fuel_length = cylinder_length(fuel_volume, stage_diameter)

    oxidizer_area = tank_area(oxidizer_volume, stage_diameter)
    fuel_area = tank_area(fuel_volume, stage_diameter)

    return {
        "oxidizer_mass": oxidizer_mass, 
        "fuel_mass": fuel_mass, "solid_mass": 0,
        "oxidizer_volume": oxidizer_volume, 
        "fuel_volume": fuel_volume, "solid_volume": 0,
        "oxidizer_length": oxidizer_length, 
        "fuel_length": fuel_length, "solid_length": 0,
        "oxidizer_area": oxidizer_area, 
        "fuel_area": fuel_area, "solid_area": 0,
        "total_tank_length": oxidizer_length + fuel_length, 
        "total_tank_area": oxidizer_area + fuel_area,
    }


# ============================================================
# 6. REQUIRED THRUST AND ENGINE COUNT
# ============================================================

def calculate_engine_count(stage_number, propellant_name, supported_mass):

    propellant_data = PROPELLANT_INFO[propellant_name]["data"]

    if stage_number == 1:
        thrust_to_weight = TrueConst.thrust_weight_ratio_stage_1_min
        thrust_per_engine_mn = propellant_data["thrust_1st_stage_MN"]
    
    elif stage_number == 2:
        thrust_to_weight = TrueConst.thrust_weight_ratio_stage_n_min
        thrust_per_engine_mn = propellant_data["thrust_2nd_stage_MN"]

    required_thrust_n = thrust_to_weight * supported_mass * TrueConst.G0
    thrust_per_engine_n = thrust_per_engine_mn * 1e6
    number_of_engines = math.ceil(required_thrust_n / thrust_per_engine_n)

    return {
        "required_thrust_n": required_thrust_n,
        "required_thrust_mn": required_thrust_n / 1e6,
        "thrust_per_engine_n": thrust_per_engine_n,
        "number_of_engines": number_of_engines,
    }


# ============================================================
# 7. MASS ESTIMATING RELATIONS
# ============================================================
#
# THESE ARE PLACEHOLDERS.
#
# This is the main section that should change once we find the
# actual equations from lecture.
#
# Keep the functions themselves.
# Just replace the equations inside them.
# ============================================================

def mer_tank_mass(geometry, info):  # FINISHED
    if info["is_solid"]:
        return 0
        
    ox_tank_mass = info["tank_coeff_ox"] * geometry["oxidizer_volume"]
    fuel_tank_mass = info["tank_coeff_fuel"] * geometry["fuel_volume"]
    return ox_tank_mass + fuel_tank_mass


def mer_insulation_mass(geometry, info):  # UPDATE TO SPEHRE AREA
    if not info["needs_insulation"]:
        return 0

    ox_ins_mass = info["ins_coeff_ox"] * geometry["oxidizer_area"]
    fuel_ins_mass = info["ins_coeff_fuel"] * geometry["fuel_area"]
    return ox_ins_mass + fuel_ins_mass
    
    
def mer_engine_mass(stage_number, propellant_name, number_of_engines, thrust_per_engine_n):  # FINISHED
    propellant_data = PROPELLANT_INFO[propellant_name]["data"]
    if PROPELLANT_INFO[propellant_name]["is_solid"]:
        return 0
    elif stage_number == 1:
        exp_ratio = propellant_data["expansion_ratio_1st_stage"]
        mass_per_engine = 7.81e4 * thrust_per_engine_n + 3.37e-5 * thrust_per_engine_n * math.sqrt(exp_ratio) + 59
        return number_of_engines * mass_per_engine
    elif stage_number == 2:
        exp_ratio = propellant_data["expansion_ratio_2nd_stage"]
        mass_per_engine = 7.81e4 * thrust_per_engine_n + 3.37e-5 * thrust_per_engine_n * math.sqrt(exp_ratio) + 59
        return number_of_engines * mass_per_engine


def mer_thrust_structure_mass(thrust_per_engine_n, number_of_engines):
    return 2.55e-4 * (thrust_per_engine_n * number_of_engines)
    

def mer_solid_casing_mass(propellant_name, propellant_mass):
    """PLACEHOLDER: solid rocket casing mass. Only applies to solids."""
    if not PROPELLANT_INFO[propellant_name]["is_solid"]:
        return 0
    return 0.08 * propellant_mass  # TEMPORARY EQUATION


def mer_gimbal_mass(propellant_name, number_of_engines, thrust_per_engine_n):
    """PLACEHOLDER: engine gimbal mass. Assume no separate gimbal mass for solids."""
    if PROPELLANT_INFO[propellant_name]["is_solid"]:
        return 0

    thrust_per_engine_kn = thrust_per_engine_n / 1000
    mass_per_gimbal = 0.01 * thrust_per_engine_kn  # TEMPORARY EQUATION
    return number_of_engines * mass_per_gimbal


def mer_avionics_mass(stage_mass_guess):
    """PLACEHOLDER: avionics mass."""
    return 0.005 * stage_mass_guess

#henry: working on these
def mer_wiring_mass(stage_mass_guess, stage_length):
    """PLACEHOLDER: wiring mass."""
    return 0.002 * stage_mass_guess + stage_length


def mer_intertank_mass(propellant_name, stage_diameter):
    """
    PLACEHOLDER: inter-tank fairing/structure.
    A solid stage has no separate fuel and oxidizer tanks.
    """
    if PROPELLANT_INFO[propellant_name]["is_solid"]:
        return 0

    intertank_area = math.pi * stage_diameter * INTERTANK_LENGTH_M
    return 8.0 * intertank_area  # TEMPORARY EQUATION


def mer_interstage_mass(stage_diameter):
    """PLACEHOLDER: inter-stage fairing mass (interstage length ~ one diameter)."""
    interstage_length = stage_diameter
    interstage_area = math.pi * stage_diameter * interstage_length
    return 8.0 * interstage_area  # TEMPORARY EQUATION


def mer_aft_fairing_mass(stage_diameter):
    """PLACEHOLDER: aft fairing mass. Engine section must be at least 3 m long."""
    aft_area = math.pi * stage_diameter * ENGINE_LENGTH_M
    return 8.0 * aft_area  # TEMPORARY EQUATION


def mer_payload_fairing_mass():
    """PLACEHOLDER: payload fairing mass, approximated as a cone."""
    fairing_height = TrueConst.fairing["fairing_height_m"]

    # TrueConst uses the key "fairing_diameter_m3" even though the value is a diameter.
    fairing_radius = TrueConst.fairing["fairing_diameter_m3"] / 2

    fairing_area = cone_side_area(fairing_radius, fairing_height)
    return 8.0 * fairing_area  # TEMPORARY EQUATION


# ============================================================
# 8. CALCULATE ONE STAGE
# ============================================================

def calculate_stage_subsystems(stage_number, propellant_name, propellant_mass,
                               stage_mass_guess, supported_mass, stage_diameter):
    """Calculate the subsystem masses for one stage."""

    info = PROPELLANT_INFO[propellant_name]

    # Propellant geometry
    geometry = calculate_propellant_geometry(propellant_name, propellant_mass, stage_diameter)

    # Solids do not need an intertank section.
    intertank_length = 0 if info["is_solid"] else INTERTANK_LENGTH_M

    # Total approximate stage length (engine region = aft length)
    stage_length = geometry["total_tank_length"] + intertank_length + ENGINE_LENGTH_M

    # Required thrust
    engine_data = calculate_engine_count(stage_number, propellant_name, supported_mass)
    number_of_engines = engine_data["number_of_engines"]
    thrust_per_engine_n = engine_data["thrust_per_engine_n"]
    total_installed_thrust_n = number_of_engines * thrust_per_engine_n

    # Subsystem masses
    tank_mass = mer_tank_mass(geometry, info)
    print(geometry)
    insulation_mass = mer_insulation_mass(geometry, info)
    engine_mass = mer_engine_mass(propellant_name, number_of_engines, thrust_per_engine_n)
    thrust_structure_mass = mer_thrust_structure_mass(total_installed_thrust_n)
    casing_mass = mer_solid_casing_mass(propellant_name, propellant_mass)
    gimbal_mass = mer_gimbal_mass(propellant_name, number_of_engines, thrust_per_engine_n)
    avionics_mass = mer_avionics_mass(stage_mass_guess)
    wiring_mass = mer_wiring_mass(stage_mass_guess, stage_length)
    intertank_mass = mer_intertank_mass(propellant_name, stage_diameter)
    aft_fairing_mass = mer_aft_fairing_mass(stage_diameter)

    # Stage 1 / Stage 2 interstage is carried by Stage 1.
    interstage_mass = mer_interstage_mass(stage_diameter) if stage_number == 1 else 0

    # Payload fairing is carried by Stage 2.
    payload_fairing_mass = mer_payload_fairing_mass() if stage_number == 2 else 0

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
        "required_thrust_mn": engine_data["required_thrust_mn"],
        "number_of_engines": number_of_engines,
        "geometry": geometry,
    }


# ============================================================
# 9. COMPLETE VEHICLE ITERATION
# ============================================================

def run_systems_analysis(stage_1_propellant, stage_2_propellant, delta_v_1):
    """
    Run the full systems-level calculation.

    The Section 1 vehicle-level result is used as the initial mass estimate.
    The systems-level masses are then calculated, and required thrust and
    engine count are recalculated until the gross mass converges.
    """

    propellant_1_data = PROPELLANT_INFO[stage_1_propellant]["data"]
    propellant_2_data = PROPELLANT_INFO[stage_2_propellant]["data"]

    # First pass: Section 1 vehicle-level mass model
    ideal = calculate_stage_masses(
        dV_1=delta_v_1,
        delta_1=propellant_1_data["inert_mass_fraction"],
        delta_2=propellant_2_data["inert_mass_fraction"],
        isp_1=propellant_1_data["isp_sea_level_s"],
        isp_2=propellant_2_data["isp_vacuum_s"],
        dV_tot=TrueConst.mission_delV_ms,
        m_pl=TrueConst.pyld_mass_kg,
        g_0=TrueConst.G0,
    )

    # Make sure the Delta-V split is feasible.
    if any(ideal["Error"]):
        print("ERROR: Selected Delta-V split is not feasible.")
        return None

    # Initial masses
    ideal_gross_mass = ideal["m_0"]
    propellant_mass_1 = ideal["m_pr_1"]
    propellant_mass_2 = ideal["m_pr_2"]
    stage_1_mass_guess = ideal["m_in_1"] + ideal["m_pr_1"]
    stage_2_mass_guess = ideal["m_in_2"] + ideal["m_pr_2"]

    old_gross_mass = ideal_gross_mass
    iteration = 0
    converged = False

    while iteration < MAX_ITERATIONS:

        iteration = iteration + 1

        # Stage 2 accelerates itself plus the payload.
        supported_mass_stage_2 = stage_2_mass_guess + TrueConst.pyld_mass_kg

        stage_2 = calculate_stage_subsystems(
            2, stage_2_propellant, propellant_mass_2,
            stage_2_mass_guess, supported_mass_stage_2, STAGE_2_DIAMETER_M
        )

        # Stage 1 lifts the entire vehicle.
        stage_1 = calculate_stage_subsystems(
            1, stage_1_propellant, propellant_mass_1,
            stage_1_mass_guess, old_gross_mass, STAGE_1_DIAMETER_M
        )

        # New vehicle mass
        new_gross_mass = stage_1["stage_mass"] + stage_2["stage_mass"] + TrueConst.pyld_mass_kg

        # Check convergence
        error = abs(new_gross_mass - old_gross_mass) / old_gross_mass

        print()
        print("Iteration:", iteration)
        print("Gross Mass:", round(new_gross_mass, 2), "kg")
        print("Change:", round(error * 100, 4), "%")

        # Update values
        stage_1_mass_guess = stage_1["stage_mass"]
        stage_2_mass_guess = stage_2["stage_mass"]
        old_gross_mass = new_gross_mass

        if error < CONVERGENCE_TOLERANCE:
            converged = True
            break

    return {
        "converged": converged,
        "iterations": iteration,
        "delta_v_1": delta_v_1,
        "delta_v_2": TrueConst.mission_delV_ms - delta_v_1,
        "ideal": ideal,
        "stage_1": stage_1,
        "stage_2": stage_2,
        "ideal_gross_mass": ideal_gross_mass,
        "systems_gross_mass": new_gross_mass,
    }


# ============================================================
# 10. PRINT ONE STAGE
# ============================================================

def print_stage_results(stage):

    print()
    print("=" * 60)
    print("STAGE", stage["stage_number"], "-", stage["propellant_name"])
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
    print("Number of engines:", stage["number_of_engines"])
    print("Approximate stage length:", round(stage["stage_length"], 2), "m")


# ============================================================
# 11. PRINT VEHICLE RESULTS
# ============================================================

def print_vehicle_results(results):

    if results is None:
        return

    print_stage_results(results["stage_1"])
    print_stage_results(results["stage_2"])

    print()
    print("=" * 60)
    print("VEHICLE SUMMARY")
    print("=" * 60)

    print("Stage 1 Delta-V:", round(results["delta_v_1"], 2), "m/s")
    print("Stage 2 Delta-V:", round(results["delta_v_2"], 2), "m/s")

    print()
    print("Vehicle-level ideal gross mass:", round(results["ideal_gross_mass"], 2), "kg")
    print("Systems-level gross mass:", round(results["systems_gross_mass"], 2), "kg")

    mass_difference = results["systems_gross_mass"] - results["ideal_gross_mass"]
    percent_difference = mass_difference / results["ideal_gross_mass"] * 100

    print("Mass difference:", round(mass_difference, 2), "kg")
    print("Percent difference:", round(percent_difference, 2), "%")

    print()
    if results["converged"]:
        print("Solution converged after", results["iterations"], "iterations.")
    else:
        print("WARNING:")
        print("Solution did not converge after", MAX_ITERATIONS, "iterations.")


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
