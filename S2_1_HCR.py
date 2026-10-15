import numpy as np
from s1.s1_1 import calculate_stage_masses
from s1.s1_3_cost import stage_cost
import utils.TrueConst as TrueConst


#AUTHOR: Henry Rowley
#Created: 10/13/2026
#Note all masses in kg, velocities in m/s, g0 in m/s^2, thrust in N, etc. Final costs in M$


#gometry helpers

def tank_geometry(V: float, D: float): 
    r = D/2.0 #radius
    V_domes=(4.0/3.0)*np.pi*r**3 #get dome volumes using hemispherical caps
    if V >= V_domes: #cylindrical case
        L_cyl=(V-V_domes)/(np.pi*r**2) #cylinder length
        L_total=L_cyl+D #total length of cylinder + caps
        A_total=np.pi*D*L_cyl+4.0*np.pi*r**2
    else: #volume of caps > needed volume, model as a pure sphere
        r=((3.0*V/4.0)/np.pi)**(1.0/3.0)
        L_cyl=0.0
        L_total=2*r
        A_total=4.0*np.pi*r**2
    return L_cyl, A_total, L_total

def payload_fairing_geometry(r_top: float):
    d_plf=TrueConst.fairing["fairing_diameter_m3"] # 5.2m requirement
    h_plf=TrueConst.fairing["fairing_height_m"] # 13.0m cylinder height requirement
    r_plf=d_plf/2.0

    #frustum adapter from top tank equator to 5.2m cylinder over top dome height
    slant_adapter=np.sqrt((r_top-r_plf)**2+r_top**2)
    A_adapter=np.pi*(r_top+r_plf)*slant_adapter

    #straight 5.2m cylinder for 13m payload + nose cone on top
    A_barrel=np.pi*d_plf*h_plf
    h_cone=d_plf
    slant_cone=np.sqrt(r_plf**2+h_cone**2)
    A_cone=np.pi*r_plf*slant_cone

    A_total=A_adapter+A_barrel+A_cone
    L_total=h_plf+h_cone
    m_fairing=shell_fairing_mass(A_total)

    return L_total, m_fairing

def shell_fairing_mass(A: float): #input is area in m^2, output in kg
    return 4.95 * A**1.15

def engine_pack_diameter(N: int, De: float):
    PACK_RATIOS=[1.0, 2.0, 2.155, 2.414, 2.701, 3.0] #can calculate more if need >6 engines
    #use circular packing ratios for various numbers of engines
    if N <= len(PACK_RATIOS):
        k = PACK_RATIOS[N - 1]
    else: 
        k=1.15*np.sqrt(float(N)) #past N=6, can use this formula for a general approximation 
    return k*De #get ratio of outer/inner * inner diameter to get diameter needed for engines

#propellant helper for easier access 
def get_stage_prop_specs(prop_name: str, stage_num: int):
    data=TrueConst.PROPS[prop_name]

    if stage_num==1:
        p="1st"
        Isp=data["isp_sea_level_s"]
    else:
        p="2nd"
        Isp=data["isp_vacuum_s"]

    is_solid=(prop_name=="SOLID")
    T_motor=data[f"thrust_{p}_stage_MN"]*1e6
    De=data[f"exhaust_diameter_{p}_stage_m"]
    Pc=data[f"chamber_pressure_{p}_stage_MPa"]*1e6
    eps=data[f"expansion_ratio_{p}_stage"]

    if is_solid: #simpler case
        MR=0.0
        rho_ox=0.0
        rho_fuel=0.0
        rho_solid=TrueConst.SOLID_rho_kg_m3
        ins_ox=0.0
        ins_fuel=0.0
        tank_ox=0.0
        tank_fuel=0.0
    else:
        MR=float(data["fuel_mass_ratio"].split(":")[0]) #get fuel mass ratio(formatted as string in trueconst)
        rho_solid=0.0

        if "LOX" in prop_name:
            rho_ox=TrueConst.LOX_rho_kg_m3
            ins_ox=1.123
        else:
            rho_ox=TrueConst.N2O4_rho_kg_m3
            ins_ox=0.0

        tank_ox=12.16

        if "LH2" in prop_name:
            rho_fuel=TrueConst.LH2_rho_kg_m3
            tank_fuel=9.09
            ins_fuel=2.88 #constant for mer
        elif "RP1" in prop_name:
            rho_fuel=TrueConst.RP1_rho_kg_m3
            tank_fuel=12.16
            ins_fuel=0.0
        elif "LCH4" in prop_name:
            rho_fuel=TrueConst.LCH4_rho_kg_m3
            tank_fuel=12.16
            ins_fuel=1.123 #constant for mer
        else:  # UDMH
            rho_fuel=TrueConst.UDMH_rho_kg_m3
            tank_fuel=12.16
            ins_fuel=0.0

    #temporary j-2x check(TODO: PUT REFERENCE IN SLIDES FOR THESE NUMBERS)
    if prop_name=="LOX/LH2":
        if stage_num==2:
            T_motor=1.307e6
            De=3.05
            Pc=9.1e6
            eps=92.0
            Isp=448.0

    return {
        "is_solid": is_solid, "T_motor": T_motor, "De": De, "Pc": Pc, "eps": eps, "Isp": Isp,
        "MR": MR, "rho_ox": rho_ox, "rho_fuel": rho_fuel, "rho_solid": rho_solid,
        "ins_ox": ins_ox, "ins_fuel": ins_fuel, "tank_ox": tank_ox, "tank_fuel": tank_fuel
    }

#stage sizing
def size_stage(stage_num: int, prop_name: str, m_pr: float, m_supported: float, D: float, M0: float, r_s2_bot: float=0.0):
    specs=get_stage_prop_specs(prop_name, stage_num)

    if stage_num==1: #twr needed depends on stage
        tw_req=1.30
    else:
        tw_req=0.76

    T_req=tw_req*m_supported*TrueConst.G0 #determine required thrust

    N_eng=int(np.ceil(T_req/specs["T_motor"])) #determine number of engines(round up)

    T_total=N_eng*specs["T_motor"] #total thrust 
    base_needed=engine_pack_diameter(N_eng, specs["De"])
    engines_fit=(base_needed<=D)

    #propellant tanks and casing/interstage shells
    if specs["is_solid"]:
        V_solid=m_pr/specs["rho_solid"] #volume of solid fuel
        L_cyl, A_tank, L_tank=tank_geometry(V_solid, D) #get tank geometry
        r_bot=(L_tank-L_cyl)/2.0
        r_top=r_bot
        r_f=r_ox=L_cyl_f=L_tank_f=L_cyl_ox=L_tank_ox=0.0
        tank_order="Solid_Single"
        m_tank=0.0
        m_ins=0.0
        m_casing=0.135*m_pr #casing accounts for everything(why other m 0 for solids)
        m_eng=0.0
        m_intertank=0.0
        tank_len_total=L_tank
    else:
        m_fuel=m_pr/(specs["MR"]+1.0)
        m_ox=m_pr-m_fuel
        V_fuel=m_fuel/specs["rho_fuel"]
        V_ox=m_ox/specs["rho_ox"]
        L_cyl_f, A_tank_f, L_tank_f=tank_geometry(V_fuel, D)
        L_cyl_ox, A_tank_ox, L_tank_ox=tank_geometry(V_ox, D)
        m_tank=specs["tank_ox"]*V_ox+specs["tank_fuel"]*V_fuel
        m_ins=specs["ins_ox"]*A_tank_ox+specs["ins_fuel"]*A_tank_f #insulation mass
        m_casing=0.0
        m_eng=N_eng*(7.81e-4*specs["T_motor"]+3.37e-5*specs["T_motor"]*np.sqrt(specs["eps"])+59.0) #note eps is the expansion ratio
        tank_len_total=L_tank_f+L_tank_ox

        #figure out tank diameters and determine placement and furstum shell between tanks
        r_f=(L_tank_f-L_cyl_f)/2.0
        r_ox=(L_tank_ox-L_cyl_ox)/2.0
        if r_f>=r_ox:
            r_bot, r_top=r_f, r_ox
            tank_order="Fuel_Bot_Ox_Top"
        else:
            r_bot, r_top=r_ox, r_f
            tank_order="Ox_Bot_Fuel_Top"

        L_intertank=r_bot+r_top
        slant_it=np.sqrt((r_bot-r_top)**2+L_intertank**2)
        m_intertank=shell_fairing_mass(np.pi*(r_bot+r_top)*slant_it)

    #presumably needed for any engine(solids and non-solids)
    m_gimbal=N_eng*237.8*(specs["T_motor"]/specs["Pc"])**0.9375
    m_thrust_struct=2.55e-4*T_total
    #note assumptions that aft shells are vertical, and interstage shell can slant 
    #note IS refers to interstage

    L_aft=3.0
    h_aft_shell=r_bot+L_aft
    m_aft=shell_fairing_mass(2.0*np.pi*r_bot*h_aft_shell)

    if stage_num==1:
        L_IS=0.0 #3m engine bay already counted in stage 2 L_aft
        slant_is=np.sqrt((r_top-r_s2_bot)**2+(r_top)**2)
        m_IS=shell_fairing_mass(np.pi*(r_top+r_s2_bot)*slant_is)
        L_PLF=0.0
        m_PLF=0.0
    else:
        L_IS=0.0
        m_IS=0.0
        L_PLF, m_PLF=payload_fairing_geometry(r_top)

    #avionics and wiring
    if stage_num==2:
        m_avionics=10.0*(M0**0.361)
    else:
        m_avionics=0.0

    #calculate stage length
    stage_length=tank_len_total+L_aft+L_PLF+L_IS 
    
    m_wiring=1.058*np.sqrt(m_supported)*(stage_length**0.25)

    dry_raw=(m_tank+m_ins+m_casing+m_eng+m_thrust_struct+m_gimbal+
             m_intertank+m_aft+m_IS+m_PLF+m_avionics+m_wiring)
    dry_budgeted=1.30*dry_raw #add 30% mass margin 
    stage_mass=dry_budgeted+m_pr

    return {
        "stage_num": stage_num, "m_pr": m_pr, "dry_raw": dry_raw,
        "dry_budgeted": dry_budgeted, "stage_mass": stage_mass,
        "stage_length": stage_length, "N_eng": N_eng, "T_total": T_total,
        "engines_fit": engines_fit, "m_tank": m_tank, "m_ins": m_ins,
        "m_casing": m_casing, "m_eng": m_eng, "m_thrust_struct": m_thrust_struct,
        "m_gimbal": m_gimbal, "m_intertank": m_intertank, "m_aft": m_aft,
        "m_IS": m_IS, "m_PLF": m_PLF, "m_avionics": m_avionics, "m_wiring": m_wiring,
        "delta_stage": dry_budgeted/m_supported, "epsilon_stage": dry_budgeted/stage_mass,
        "tank_order": tank_order, "r_f": r_f, "r_ox": r_ox,
        "r_bot": r_bot, "r_top": r_top,
        "L_tank_f": L_tank_f, "L_cyl_f": L_cyl_f, "L_tank_ox": L_tank_ox, "L_cyl_ox": L_cyl_ox
    }

def solve_vehicle(prop1: str, prop2: str, dV1: float, D: float=5.2): #for now let's assume set stage diam of 5.2m
    #get delta v values and other parameters
    dV_total=TrueConst.mission_delV_ms 
    dV2=dV_total-dV1
    m_pl=TrueConst.pyld_mass_kg
    g0=TrueConst.G0 #m/s^2

    #get propellant values we need for stage sizing in loop
    specs1=get_stage_prop_specs(prop1, 1)
    specs2=get_stage_prop_specs(prop2, 2)

    #parametric stage mass ratios from rocket eqn
    r1=np.exp(-dV1/(g0*specs1["Isp"]))
    r2=np.exp(-dV2/(g0*specs2["Isp"]))

    #inert mass fractions for section 1 code call for initial guess
    del1=TrueConst.PROPS[prop1]["inert_mass_fraction"]
    del2=TrueConst.PROPS[prop2]["inert_mass_fraction"]

    #call section 1
    initial_guess=calculate_stage_masses(dV_1=dV1, delta_1=del1, delta_2=del2, isp_1=specs1["Isp"], isp_2=specs2["Isp"], dV_tot=dV_total, m_pl=m_pl, g_0=g0)

    #get initial mass guess parameters(we don't need the inert mass explicitly for any of the MERs)
    M0=initial_guess["m_0"]
    m_0_2=initial_guess["m_0_2"]
    m_pr_1=initial_guess["m_pr_1"]
    m_pr_2=initial_guess["m_pr_2"]

    tol=1e-6 #0.01% change in M0 between iterations = converged
    max_iter=100
    converged=False

    for iteration in range(1, max_iter+1):
        #start by sizing stage 2
        s2=size_stage(2, prop2, m_pr_2, m_0_2, D, M0)
        m_f_2=m_pl+s2["dry_budgeted"] #the final mass of stage 2, including 30% inert mass margin
        m_0_2_new=m_f_2/r2 # use mass ratio for given isp/dv to get new gross mass of stage 2
        m_pr_2=m_0_2_new-m_f_2 #updated stage 2 prop mass

        #size stage 1
        M0_curr=M0-m_0_2+m_0_2_new
        s1=size_stage(1, prop1, m_pr_1, M0_curr, D, M0_curr, r_s2_bot=s2["r_bot"]) #note r_s2_bot is the radius of the bottom fuel tank of stage 2
        m_f_1=m_0_2_new+s1["dry_budgeted"] #final mass will include updated stage 2 gross mass plus stage 1inert mass(w/ 30% mass margin)
        M0_new=m_f_1/r1 #calculate gross liftoff mass to get dv1
        m_pr_1=M0_new-m_f_1 #new stage 1 prop mass

        #check gross mass diff and update masses
        err=abs(M0_new-M0)/M0
        M0=M0_new
        m_0_2=m_0_2_new

        #check for convergence
        if err<tol:
            converged=True
            break

    #once we converge, we can easily extract all needed information:
    s2=size_stage(2, prop2, m_pr_2, m_0_2, D, M0)
    m_0_2=m_pl+s2["stage_mass"]
    s1=size_stage(1, prop1, m_pr_1, M0, D, M0, r_s2_bot=s2["r_bot"])
    M0=m_0_2+s1["stage_mass"]

    #calculate vehicle L and L/D ratio
    L_total=s1["stage_length"]+s2["stage_length"]
    ld_ratio=L_total/D
    ld_ok=(ld_ratio<=TrueConst.L_D) #will return true if L/D less than or equa lto 13

    #calculate nre cost
    cost_s1=stage_cost(s1["dry_budgeted"])
    cost_s2=stage_cost(s2["dry_budgeted"])
    total_cost_M=cost_s1+cost_s2

    return {
            "converged": converged,
            "iterations": iteration,
            "prop1": prop1,
            "prop2": prop2,
            "dV1": dV1,
            "dV2": dV2,
            "M0": M0,
            "ideal_M0": initial_guess["m_0"],
            "mass_diff_pct": ((M0-initial_guess["m_0"])/initial_guess["m_0"])*100.0,
            "L_total": L_total,
            "ld_ratio": ld_ratio,
            "ld_ok": ld_ok,
            "cost_s1_M": cost_s1,
            "cost_s2_M": cost_s2,
            "total_cost_M": total_cost_M,
            "s1": s1,
            "s2": s2
        }


if __name__=="__main__": #just quick example of how to call, need to iterate through this in 2.2 to get the values we want
    d=5.2
    while d<=13.0:
        res=solve_vehicle("N2O4/UDMH", "LOX/LH2", 3750, D=round(d, 2))
        s1_fit=res["s1"]["engines_fit"]
        s2_fit=res["s2"]["engines_fit"]
        ld_ok=res["ld_ok"]

        print(f"D={d:.1f}m | L={res['L_total']:.1f}m | L/D={res['ld_ratio']:.1f} (OK={ld_ok}) | S1: {res['s1']['N_eng']} eng (fit={s1_fit}) | S2: {res['s2']['N_eng']} eng (fit={s2_fit})")

        if ld_ok:
            if s1_fit:
                if s2_fit:
                    print(f"\nFeasible configuration closed at D={d:.1f}m")
                    print(f"M0: {res['M0']:,.0f} kg | L_tot: {res['L_total']:.1f}m | Cost: ${res['total_cost_M']/1000.0:.3f}B FY2025")
                    break
        d+=0.2
