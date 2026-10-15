# author: sharan sajiv menon
# edits: shaunn pavelik -- cost now uses inert (dry) mass in kg like Section 1, units on
#        every row, vehicle-level comparison rows, one CSV per design so we don't overwrite,
#        engine model + engine-fit rows (10/14)
import csv
import os

from S2_1_HCR import run_systems_analysis
from s1.s1_3_cost import stage_cost   # same cost function as Section 1: kg in -> $M (FY2025)
from utils.sf import sf

# Assigned designs from Section 1 for each team member:
# teammate: (stage_1, stage_2, min-mass dV1, min-cost dV1)
ASSIGNED_DESIGNS = {
    "Gregory Kahn":   ("LOX/LCH4", "LOX/LH2", 4266, 5270),
    "Henry Rowley":   ("LOX/LH2",  "LOX/LH2", 4710, 5749),
    "Jacob Harmon":   ("LOX/RP1",  "LOX/LH2", 4095, 5092),
    "Sharan Menon":   ("SOLID",    "LOX/LH2", 3230, 3835),
    "Shaunn Pavelik": ("N2O4/UDMH", "LOX/LH2", 3750, 4666),
}

# Default single-run configuration (Sharan's design)
STAGE_1 = "SOLID"
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
def create_table_of_masses(results: dict, path: str = None, person_name: str = None):
    # masses of subsystems for each stage
    stage1 = results["stage_1"]
    stage2 = results["stage_2"]

    person = person_name or results.get("person") or results.get("name")

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
        if person:
            writer.writerow(["LV", "Team Member", person, "-"])
    return path


#author: sharan sajiv menon
def generate_all_tables(person_name: str = None):
    """Run systems analysis and generate S.2.2 CSV mass tables.
    """
    if person_name:
        targets = {k: v for k, v in ASSIGNED_DESIGNS.items() if person_name.lower() in k.lower()} or ASSIGNED_DESIGNS
    else:
        targets = ASSIGNED_DESIGNS

    created_files = []
    for person, (s1, s2, dv_min_mass, dv_min_cost) in targets.items():
        for kind, dv in (("min-mass", dv_min_mass), ("min-cost", dv_min_cost)):
            analysis_data = run_systems_analysis(s1, s2, dv)
            if analysis_data is None or not analysis_data.get("converged", True):
                print(f"Skipping {person} {kind} ({s1}/{s2} @ {dv} m/s): did not converge")
                continue
            path = create_table_of_masses(analysis_data, person_name=person)
            created_files.append(path)
            print(f"wrote {path} ({person} - {kind})")
    return created_files


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))   # csvs/ next to this file
    print("== Generating S.2.2 mass and cost tables for all team members (10 designs) ==")
    files = generate_all_tables()
    print(f"\nSuccessfully generated {len(files)} CSV files in csvs/")
