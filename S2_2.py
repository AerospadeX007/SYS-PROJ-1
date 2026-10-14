# author: sharan sajiv menon
# edits: shaunn pavelik -- cost now uses inert (dry) mass in kg like Section 1, units on
#        every row, vehicle-level comparison rows, one CSV per design so we don't overwrite,
#        engine model + engine-fit rows (10/14)
import csv
import os

from S2_1 import run_systems_analysis
from s1.s1_3_cost import stage_cost   # same cost function as Section 1: kg in -> $M (FY2025)
from utils.sf import sf

STAGE_1 = "N2O4/UDMH"
STAGE_2 = "LOX/LH2"
DELTA_V_1 = 3750.0  # m/s

# rows that go in the subsystem table, in Table order, with display names
COMPONENTS = [
    ("propellant_mass", "Propellant"),
    ("tank_mass", "Propellant tanks"),
    ("insulation_mass", "Tank insulation"),
    ("engine_mass", "Engines"),
    ("thrust_structure_mass", "Thrust structure"),
    ("casing_mass", "Solid casing"),
    ("gimbal_mass", "Gimbals"),
    ("avionics_mass", "Avionics"),
    ("wiring_mass", "Wiring"),
    ("payload_fairing_mass", "Payload fairing"),
    ("intertank_mass", "Inter-tank fairing"),
    ("interstage_mass", "Inter-stage fairing"),
    ("aft_fairing_mass", "Aft fairing"),
    ("dry_mass_without_margin", "Inert mass before margin"),
    ("margin_mass", "30% mass margin"),
    ("dry_mass_with_margin", "Inert mass with margin"),
    ("stage_mass", "Total stage mass"),
]


### author: sharan sajiv menon
def create_table_of_masses(results: dict, path: str = None):
    # masses of subsystems for each stage
    stage1 = results["stage_1"]
    stage2 = results["stage_2"]

    ## calculate costs -- NRE cost is on INERT mass in kg (payload and propellant are not costed)
    cost1 = stage_cost(stage1["dry_mass_with_margin"])   # $M
    cost2 = stage_cost(stage2["dry_mass_with_margin"])
    total_cost = cost1 + cost2

    if path is None:
        tag = f"{results['stage_1_propellant']}__{results['stage_2_propellant']}".replace("/", "_")
        path = f"csvs/S2_2_table_of_masses_{tag}_dv1_{results['delta_v_1']:.0f}.csv"
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    ## csv columns: stage, component, mass, unit
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Stage", "Component Name", "Value", "Unit"])
        for stage_name, stage in (("Stage 1", stage1), ("Stage 2", stage2)):
            for key, label in COMPONENTS:
                writer.writerow([stage_name, label, sf(stage[key]), "kg"])
            writer.writerow([stage_name, "Engines (count)", stage["number_of_engines"], "-"])
            writer.writerow([stage_name, "Engine model",
                             stage["engine_name"] if stage["engine_name"] != "Table 2"
                             else f"Table 2 {stage['propellant_name']}", "-"])
            writer.writerow([stage_name, "Engines fit in aft fairing", "yes" if stage["engines_fit"]
                             else f"no (need {sf(stage['engine_base_diameter_needed'])} m)", "-"])
            writer.writerow([stage_name, "Stage length", sf(stage["stage_length"]), "m"])
            writer.writerow([stage_name, "Stage cost", sf((cost1 if stage is stage1 else cost2) / 1e3),
                             "$B (FY2025)"])
        writer.writerow(["LV", "Payload", sf(26000), "kg"])
        writer.writerow(["LV", "Total Mass (system level)", sf(results["systems_gross_mass"]), "kg"])
        writer.writerow(["LV", "Total Mass (vehicle level)", sf(results["ideal_gross_mass"]), "kg"])
        writer.writerow(["LV", "Total Cost (system level)", sf(total_cost / 1e3), "$B (FY2025)"])
        writer.writerow(["LV", "Total Cost (vehicle level)", sf(results["ideal_cost_musd"] / 1e3),
                         "$B (FY2025)"])
        writer.writerow(["LV", "Diameter", sf(results["vehicle_diameter"]), "m"])
        writer.writerow(["LV", "Length", sf(results["vehicle_length"]), "m"])
        writer.writerow(["LV", "L/D", sf(results["length_to_diameter"]), "-"])
    return path


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))   # csvs/ next to this file
    # pick your propellant combo
    analysis_data = run_systems_analysis(STAGE_1, STAGE_2, DELTA_V_1)
    print("wrote", create_table_of_masses(analysis_data))
