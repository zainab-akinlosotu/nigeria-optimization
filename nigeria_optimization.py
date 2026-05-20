# ============================================================
# Nigeria Energy & Water Access Optimization
# Author: Zainab Akinlosotu
# Salisbury University - Perdue School of Business
# Tool: Python PuLP (Linear Programming)
# SDGs: Goal 6 (Clean Water) | Goal 7 (Clean Energy)
# ============================================================
 
from pulp import (
    LpProblem, LpVariable, LpMaximize, lpSum,
    LpStatus, value, PULP_CBC_CMD
)
 
# ── DATA ────────────────────────────────────────────────────
# Sources:
# Population: NBS estimates (2006 census base, scaled to 2023 total of 227.9M)
# Electricity access %: World Bank SDG7 2023 + NBS zone customer share
# Water access %: UNICEF WASHNORM 2021 Nigeria Report
# Cost per beneficiary: ESMAP 2025 + World Bank WASH estimates
 
zones = [
    "North West",
    "North East",
    "North Central",
    "South West",
    "South East",
    "South South",
]
 
population = {
    "North West":   55.2,
    "North East":   22.1,
    "North Central": 33.8,
    "South West":   47.3,
    "South East":   22.8,
    "South South":  28.5,
}
 
elec_access = {
    "North West":   0.30,
    "North East":   0.25,
    "North Central": 0.52,
    "South West":   0.82,
    "South East":   0.68,
    "South South":  0.65,
}
 
water_access = {
    "North West":   0.18,
    "North East":   0.15,
    "North Central": 0.32,
    "South West":   0.48,
    "South East":   0.35,
    "South South":  0.38,
}
 
# Cost per beneficiary in USD (plain dollars)
cost_energy = {
    "North West":   320,
    "North East":   350,
    "North Central": 280,
    "South West":   200,
    "South East":   230,
    "South South":  250,
}
 
cost_water = {
    "North West":   110,
    "North East":   120,
    "North Central":  95,
    "South West":    65,
    "South East":    75,
    "South South":   80,
}
 
# People currently without access (millions)
without_energy = {z: population[z] * (1 - elec_access[z]) for z in zones}
without_water  = {z: population[z] * (1 - water_access[z]) for z in zones}
 
# ── MODEL ASSUMPTIONS ───────────────────────────────────────
TOTAL_BUDGET   = 500    # USD million
ENERGY_BUDGET  = TOTAL_BUDGET * 0.60   # 300M
WATER_BUDGET   = TOTAL_BUDGET * 0.40   # 200M
MIN_ENERGY     = 5      # USD million per zone (equity constraint)
MIN_WATER      = 5      # USD million per zone (equity constraint)
MAX_ENERGY     = 150    # USD million per zone (cap)
MAX_WATER      = 100    # USD million per zone (cap)
 
 
# ── BUILD LP PROBLEM ────────────────────────────────────────
model = LpProblem("Nigeria_Resource_Allocation", LpMaximize)
 
# Decision variables: investment per zone in $M
E = {z: LpVariable(f"Energy_{z.replace(' ','_')}", lowBound=MIN_ENERGY, upBound=MAX_ENERGY) for z in zones}
W = {z: LpVariable(f"Water_{z.replace(' ','_')}",  lowBound=MIN_WATER,  upBound=MAX_WATER)  for z in zones}
 
# People reached per zone (in millions)
# Investment ($M) / cost per person ($) = people reached (M)
people_energy = {z: E[z] / cost_energy[z] for z in zones}
people_water  = {z: W[z] / cost_water[z]  for z in zones}
 
# ── OBJECTIVE: Maximize total people reached ─────────────────
model += lpSum(people_energy[z] + people_water[z] for z in zones), "Total_People_Reached"
 
# ── CONSTRAINTS ─────────────────────────────────────────────
model += lpSum(E[z] for z in zones) <= ENERGY_BUDGET, "Energy_Budget"
model += lpSum(W[z] for z in zones) <= WATER_BUDGET,  "Water_Budget"
model += lpSum(E[z] + W[z] for z in zones) <= TOTAL_BUDGET, "Total_Budget"
 
 
# ── SOLVE ────────────────────────────────────────────────────
model.solve(PULP_CBC_CMD(msg=0))
 
 
# ── RESULTS ─────────────────────────────────────────────────
print("=" * 62)
print("  NIGERIA ENERGY & WATER ACCESS OPTIMIZATION RESULTS")
print("=" * 62)
print(f"  Status: {LpStatus[model.status]}")
print(f"  Total Budget: ${TOTAL_BUDGET}M")
print(f"  Energy Budget: ${ENERGY_BUDGET}M | Water Budget: ${WATER_BUDGET}M")
print("=" * 62)
 
print(f"\n{'Zone':<16} {'E Invest($M)':>12} {'W Invest($M)':>12} {'E Reached(M)':>13} {'W Reached(M)':>13} {'Total(M)':>10}")
print("-" * 78)
 
total_people = 0
total_e_invest = 0
total_w_invest = 0
 
for z in zones:
    ei = value(E[z])
    wi = value(W[z])
    pe = ei / cost_energy[z]
    pw = wi / cost_water[z]
    tot = pe + pw
    total_people   += tot
    total_e_invest += ei
    total_w_invest += wi
    print(f"{z:<16} {ei:>12.2f} {wi:>12.2f} {pe:>13.4f} {pw:>13.4f} {tot:>10.4f}")
 
print("-" * 78)
print(f"{'TOTAL':<16} {total_e_invest:>12.2f} {total_w_invest:>12.2f} {'':>13} {'':>13} {total_people:>10.4f}")
print(f"\n  >> Total People Reached: {total_people:.4f} million")
print(f"  >> Total Investment Used: ${total_e_invest + total_w_invest:.1f}M of ${TOTAL_BUDGET}M budget")
 
 
# ── SCENARIO ANALYSIS ────────────────────────────────────────
print("\n" + "=" * 62)
print("  SCENARIO ANALYSIS - Budget Sensitivity")
print("=" * 62)
print(f"{'Scenario':<28} {'Budget($M)':>10} {'People Reached(M)':>18}")
print("-" * 58)
 
scenarios = [
    ("Low Budget",           250),
    ("Baseline",             500),
    ("High Budget",          750),
    ("Maximum Impact",      1000),
    ("Water Priority 50/50", 500),
    ("Energy Priority 70/30",500),
]
 
for label, budget in scenarios:
    m2 = LpProblem(f"Scenario_{label.replace(' ','_')}", LpMaximize)
 
    if label == "Water Priority 50/50":
        eb, wb2 = budget * 0.50, budget * 0.50
    elif label == "Energy Priority 70/30":
        eb, wb2 = budget * 0.70, budget * 0.30
    else:
        eb, wb2 = budget * 0.60, budget * 0.40
 
    E2 = {z: LpVariable(f"E2_{z.replace(' ','_')}_{label[:3]}", lowBound=MIN_ENERGY, upBound=MAX_ENERGY) for z in zones}
    W2 = {z: LpVariable(f"W2_{z.replace(' ','_')}_{label[:3]}",  lowBound=MIN_WATER,  upBound=MAX_WATER)  for z in zones}
 
    m2 += lpSum(E2[z]/cost_energy[z] + W2[z]/cost_water[z] for z in zones)
    m2 += lpSum(E2[z] for z in zones) <= eb
    m2 += lpSum(W2[z] for z in zones) <= wb2
    m2 += lpSum(E2[z] + W2[z] for z in zones) <= budget
 
    m2.solve(PULP_CBC_CMD(msg=0))
    result = sum(value(E2[z])/cost_energy[z] + value(W2[z])/cost_water[z] for z in zones)
    print(f"{label:<28} {budget:>10} {result:>18.4f}")
 
print("\n" + "=" * 62)
print("  Sources:")
print("  - World Bank SDG7 Electrification Dataset 2023")
print("  - UNICEF WASHNORM 2021 Nigeria Report")
print("  - NBS Population Estimates (2006 census base)")
print("  - ESMAP Tracking SDG7 Report 2025")
print("  - World Bank / UNICEF WASH cost estimates")
print("=" * 62)