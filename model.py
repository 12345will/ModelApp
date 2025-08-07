# PART 1: CONFIG & CALCULATION

import streamlit as st
import pandas as pd

GBP_PER_INR = 1 / 105
UK_PRICE_PER_KWH = 0.258
INDIA_PRICE_PER_KWH = 7.38 * GBP_PER_INR

YEARS = list(range(2027, 2036))
SILICON_PCTS = [3, 5, 10, 15, 20]
ENERGY_MIXES = {
    "100% Grid": lambda x: 2777.40274 * (x ** 0.288551),
    "PPA:Grid (70:30)": lambda x: 784.3886 * (x ** 0.396496),
    "Grid+Gas (30% demand)": lambda x: 1460.00464 * (x ** 0.534148)
}

# Placeholder material values
materials_data = {
    "NMC Cell 1": {
        "materials": {"NCM": 0.5, "Graphite": 0.5},
        "co2_water": {3: (2, 5), 5: (3, 6), 10: (4, 7), 15: (5, 8), 20: (6, 9)}
    },
    "NMC Cell 2": {
        "materials": {"NCM - CAM powder": 0.2, "Graphite": 0.2},
        "co2_water": {3: (2, 3), 5: (3, 4), 10: (4, 5), 15: (5, 6), 20: (6, 7)}
    },
    "LFP": {
        "materials": {"Li": 0.3, "Fe": 0.3},
        "co2_water": {None: (8, 9)}
    }
}

def calc_site_from_energy(energy_gwh, total_cells, mix, silicon_pcts):
    site_materials = {}
    total_co2 = 0
    total_water = 0
    for cell_type, pct in mix.items():
        cells = total_cells * (pct / 100)
        if cells <= 0:
            continue
        if "NMC" in cell_type:
            co2_kwh, water_kwh = materials_data[cell_type]["co2_water"][silicon_pcts[cell_type]]
        else:
            co2_kwh, water_kwh = materials_data[cell_type]["co2_water"][None]
        total_co2 += energy_gwh * (pct / 100) * 1e6 * co2_kwh / 1e3
        total_water += energy_gwh * (pct / 100) * 1e6 * water_kwh / 1e3
        for mat, qty in materials_data[cell_type]["materials"].items():
            site_materials[mat] = site_materials.get(mat, 0) + qty * cells
    return energy_gwh, total_cells, total_co2, total_water, site_materials


# PART 2: STREAMLIT UI + CALCULATIONS

st.title("Agratas Carbon Sensitivity Model (2027–2035)")

year_data = []
annual_materials_list = []
cumulative_materials = {}

for year in YEARS:
    with st.expander(f"Year {year} Inputs"):
        # UK
        uk_lines = st.number_input(f"UK Lines ({year})", 0, 10, 0)
        uk_max_gwh = uk_lines * 50
        uk_energy = st.number_input(f"UK Energy Used (GWh) - max {uk_max_gwh}", 0.0, uk_max_gwh, 0.0)
        uk_mix_nmc1 = st.number_input(f"NMC Cell 1 (%) - UK {year}", 0, 100, 0)
        uk_mix_nmc2 = st.number_input(f"NMC Cell 2 (%) - UK {year}", 0, 100, 0)
        uk_mix_lfp = st.number_input(f"LFP (%) - UK {year}", 0, 100, 0)
        uk_valid = (uk_mix_nmc1 + uk_mix_nmc2 + uk_mix_lfp == 100)
        uk_silicon = {}
        if uk_mix_nmc1 > 0:
            uk_silicon["NMC Cell 1"] = st.selectbox(f"UK NMC Cell 1 Silicon % ({year})", SILICON_PCTS, key=f"uks1{year}")
        if uk_mix_nmc2 > 0:
            uk_silicon["NMC Cell 2"] = st.selectbox(f"UK NMC Cell 2 Silicon % ({year})", SILICON_PCTS, key=f"uks2{year}")
        uk_mix = {"NMC Cell 1": uk_mix_nmc1, "NMC Cell 2": uk_mix_nmc2, "LFP": uk_mix_lfp}
        uk_mix_type = st.selectbox(f"UK Energy Mix ({year})", list(ENERGY_MIXES), key=f"ukmix{year}")

        # India
        in_lines = st.number_input(f"India Lines ({year})", 0, 10, 0)
        in_max_gwh = in_lines * 50
        in_energy = st.number_input(f"India Energy Used (GWh) - max {in_max_gwh}", 0.0, in_max_gwh, 0.0)
        in_mix_nmc1 = st.number_input(f"NMC Cell 1 (%) - India {year}", 0, 100, 0)
        in_mix_nmc2 = st.number_input(f"NMC Cell 2 (%) - India {year}", 0, 100, 0)
        in_mix_lfp = st.number_input(f"LFP (%) - India {year}", 0, 100, 0)
        in_valid = (in_mix_nmc1 + in_mix_nmc2 + in_mix_lfp == 100)
        in_silicon = {}
        if in_mix_nmc1 > 0:
            in_silicon["NMC Cell 1"] = st.selectbox(f"India NMC Cell 1 Silicon % ({year})", SILICON_PCTS, key=f"ins1{year}")
        if in_mix_nmc2 > 0:
            in_silicon["NMC Cell 2"] = st.selectbox(f"India NMC Cell 2 Silicon % ({year})", SILICON_PCTS, key=f"ins2{year}")
        in_mix = {"NMC Cell 1": in_mix_nmc1, "NMC Cell 2": in_mix_nmc2, "LFP": in_mix_lfp}
        in_mix_type = st.selectbox(f"India Energy Mix ({year})", list(ENERGY_MIXES), key=f"inmix{year}")

    # Calculate outputs
    uk_cells = uk_lines * 300 * (uk_energy / uk_max_gwh) if uk_max_gwh else 0
    in_cells = in_lines * 300 * (in_energy / in_max_gwh) if in_max_gwh else 0

    uk_energy, uk_cells, uk_co2, uk_water, uk_materials = calc_site_from_energy(
        uk_energy, uk_cells, uk_mix, uk_silicon) if uk_valid else (0, 0, 0, 0, {})
    
    in_energy, in_cells, in_co2, in_water, in_materials = calc_site_from_energy(
        in_energy, in_cells, in_mix, in_silicon) if in_valid else (0, 0, 0, 0, {})

    total_energy = uk_energy + in_energy
    total_cells = uk_cells + in_cells
    total_co2 = uk_co2 + in_co2
    total_water = uk_water + in_water
    total_cost = (uk_energy * 1e6 * UK_PRICE_PER_KWH) + (in_energy * 1e6 * INDIA_PRICE_PER_KWH)

    year_materials = {}
    for m in set(uk_materials) | set(in_materials):
        year_materials[m] = uk_materials.get(m, 0) + in_materials.get(m, 0)
        cumulative_materials[m] = cumulative_materials.get(m, 0) + year_materials[m]

    year_data.append({
        "Year": year,
        "Total Cells": total_cells,
        "Total Energy (GWh)": total_energy,
        "Total CO2 (tCO2)": total_co2,
        "Total Water (m³)": total_water,
        "Total Cost (£)": total_cost
    })

    if year_materials:
        mat_df = pd.DataFrame(year_materials.items(), columns=["Material", f"{year} Qty"])
        annual_materials_list.append(mat_df)


# PART 3: OUTPUT TABLES

df = pd.DataFrame(year_data)

st.subheader("📊 Annual Results")
st.dataframe(df.style.format({
    "Total Cells": "{:,.0f}",
    "Total Energy (GWh)": "{:,.2f}",
    "Total CO2 (tCO2)": "{:,.0f}",
    "Total Water (m³)": "{:,.0f}",
    "Total Cost (£)": "£{:,.2f}"
}))

st.subheader("📦 Annual Material Usage")
if annual_materials_list:
    annual_materials_df = pd.concat(annual_materials_list, axis=1)
    st.dataframe(annual_materials_df)

st.subheader("📈 Cumulative Totals")
cum_df = df.drop(columns=["Year"]).sum(numeric_only=True).to_frame().T
st.dataframe(cum_df.style.format({
    "Total Cells": "{:,.0f}",
    "Total Energy (GWh)": "{:,.2f}",
    "Total CO2 (tCO2)": "{:,.0f}",
    "Total Water (m³)": "{:,.0f}",
    "Total Cost (£)": "£{:,.2f}"
}))

st.subheader("📦 Cumulative Material Usage")
if cumulative_materials:
    cum_mat_df = pd.DataFrame(cumulative_materials.items(), columns=["Material", "Total Qty"])
    st.dataframe(cum_mat_df)

