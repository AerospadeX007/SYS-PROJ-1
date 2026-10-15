# Author: Jacob Harmon
# Date: 9/16/2026
# Update: 9/22/2026 - Jacob Harmon

# List of true constants for propelant mixures


# LOX/LCH4
LOX_LCH4 = {
    "fuel_mass_ratio": "3.6:1",
    "inert_mass_fraction": 0.067,
    "isp_sea_level_s": 327,
    "isp_vacuum_s": 380,
    "thrust_1st_stage_MN": 2.26,
    "thrust_2nd_stage_MN": 0.745,
    "exhaust_diameter_1st_stage_m": 2.4,
    "exhaust_diameter_2nd_stage_m": 1.5,
    "chamber_pressure_1st_stage_MPa": 35.16,
    "chamber_pressure_2nd_stage_MPa": 10.1,
    "expansion_ratio_1st_stage": 34.34,
    "expansion_ratio_2nd_stage": 45,
}

# LOX/LH2
LOX_LH2 = {
    "fuel_mass_ratio": "6.03:1",
    "inert_mass_fraction": 0.075,
    "isp_sea_level_s": 366,
    "isp_vacuum_s": 452,
    "thrust_1st_stage_MN": 1.86,
    "thrust_2nd_stage_MN": 0.099,
    "exhaust_diameter_1st_stage_m": 2.4,
    "exhaust_diameter_2nd_stage_m": 2.15,
    "chamber_pressure_1st_stage_MPa": 20.64,
    "chamber_pressure_2nd_stage_MPa": 4.2,
    "expansion_ratio_1st_stage": 78,
    "expansion_ratio_2nd_stage": 84,
}

# LOX/RP1
LOX_RP1 = {
    "fuel_mass_ratio": "2.72:1",
    "inert_mass_fraction": 0.063,
    "isp_sea_level_s": 311,
    "isp_vacuum_s": 337,
    "thrust_1st_stage_MN": 1.92,
    "thrust_2nd_stage_MN": 0.061,
    "exhaust_diameter_1st_stage_m": 3.7,
    "exhaust_diameter_2nd_stage_m": 0.92,
    "chamber_pressure_1st_stage_MPa": 25.8,
    "chamber_pressure_2nd_stage_MPa": 6.77,
    "expansion_ratio_1st_stage": 37,
    "expansion_ratio_2nd_stage": 14.5,
}

# Solid
SOLID = {
    "fuel_mass_ratio": None,  # N/A
    "inert_mass_fraction": 0.087,
    "isp_sea_level_s": 269,
    "isp_vacuum_s": 279,
    "thrust_1st_stage_MN": 4.5,
    "thrust_2nd_stage_MN": 2.94,
    "exhaust_diameter_1st_stage_m": 6.6,
    "exhaust_diameter_2nd_stage_m": 2.34,
    "chamber_pressure_1st_stage_MPa": 10.5,
    "chamber_pressure_2nd_stage_MPa": 5,
    "expansion_ratio_1st_stage": 16,
    "expansion_ratio_2nd_stage": 56,
}

# N204:UDMH
N2O4_UDMH = {
   "fuel_mass_ratio": "2.67:1",
    "inert_mass_fraction": 0.061,
    "isp_sea_level_s": 285,
    "isp_vacuum_s": 316,
    "thrust_1st_stage_MN": 1.75,
    "thrust_2nd_stage_MN": 0.067,
    "exhaust_diameter_1st_stage_m": 1.5,
    "exhaust_diameter_2nd_stage_m": 1.13,
    "chamber_pressure_1st_stage_MPa": 15.7,
    "chamber_pressure_2nd_stage_MPa": 14.7,
    "expansion_ratio_1st_stage": 26.2,
    "expansion_ratio_2nd_stage": 81.3, 
}


mission_delV_ms = 12300 
pyld_mass_kg = 26000
fairing = {
    'fairing_height_m': 13,
    'fairing_diameter_m3': 5.2,    
}
L_D = 13
thrust_weight_ratio_stage_1_min = 1.3
thrust_weight_ratio_stage_n_min = 0.76
stage_count_min = 2

LH2_rho_kg_m3 = 71
LOX_rho_kg_m3 = 1140
RP1_rho_kg_m3 = 820
LCH4_rho_kg_m3 = 423
SOLID_rho_kg_m3 = 1680
N2O4_rho_kg_m3 = 1442
UDMH_rho_kg_m3 = 791

G0 = 9.8

PROPELLANTS = [LOX_LCH4, LOX_LH2, LOX_RP1, SOLID, N2O4_UDMH]
PROPELLANT_NAMES = ["LOX/LCH4", "LOX/LH2", "LOX/RP1", "SOLID", "N2O4/UDMH"]
PROPS = dict(zip(PROPELLANT_NAMES, PROPELLANTS))


# J-2X: researched LOX/LH2 upper-stage engine (Table 2 caption allows a cited swap).
# Team decision 10/12 (Henry): Table 2's 0.099 MN LOX/LH2 2nd-stage engine needs 20-45 engines
# for T/W >= 0.76. Added 10/14 by Shaunn Pavelik (values Henry used in S2_1_HCR, checked to NASA).
# Sources: T. Byrd, "From Concept to Design: Progress on the J-2X Upper Stage Engine", AIAA JPC 2008
#          (NTRS 20080036837): 294,000 lbf vac, Isp 448 s, area ratio 92:1, O/F 5.5 primary mode
#          X.-Y. Wang et al., TFAWS08-1013, NASA GRC 2008: chamber pressure 1,338 psia, O/F 5.5
#          Nozzle exit diameter ~3 m (Wikipedia "J-2X"); Henry used 3.05 m
J2X = {
    "name": "J-2X",
    "thrust_vac_MN": 1.307,             # 294,000 lbf
    "isp_vacuum_s": 448,
    "chamber_pressure_MPa": 9.23,       # 1,338 psia
    "expansion_ratio": 92,
    "exhaust_diameter_m": 3.05,
    "mixture_ratio": 5.5,               # O/F primary mode
    "length_m": 4.7,                    # real length; the handout still says assume 3 m engines
}

COLUMN_OWNER = {
    "LOX/LCH4": "Gregory Kahn",
    "LOX/LH2": "Henry Rowley",
    "LOX/RP1": "Jacob Harmon",
    "SOLID": "Sharan Menon",
    "N2O4/UDMH": "Shaunn Pavelik",
}
N204_UDMH = N2O4_UDMH  

