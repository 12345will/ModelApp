import streamlit as st
import pandas as pd

# -------------------------
# CONFIG
# -------------------------
GBP_PER_INR = 1 / 105
UK_PRICE_PER_KWH = 0.258  # GBP
INDIA_PRICE_PER_KWH = 7.38 * GBP_PER_INR

YEARS = list(range(2027, 2036))
ENERGY_MIXES = {
    "100% Grid": lambda x: 2777.40274 * (x ** 0.288551),
    "PPA:Grid (70:30)": lambda x: 784.3886 * (x ** 0.396496),
    "Grid+Gas (30% demand)": lambda x: 1460.00464 * (x ** 0.534148)
}
CELL_TYPES = ["NMC Cell 1", "NMC Cell 2", "LFP"]
SILICON_PCTS = [3, 5, 10, 15, 20]

# -------------------------
# MATERIAL TABLES (placeholders)
# -------------------------
materials_data = {
    "NMC Cell 1": {
        "materials": {
            "NCM": 0.5, "SP-01": 0.5, "PVDF-1": 0.5, "NMP": 0.5, "Boehmite": 0.5,
            "PVDF-2": 0.5, "Graphite": 0.5, "SWCNT": 0.5, "PAA": 0.5, "Anoder Binder": 0.5,
            "Thickener": 0.5, "Al Foil": 0.5, "Cu Foil": 0.5, "LT Electrolyte": 0.5,
            "Separator": 3.5, "Tape": 1.0, "Aluminium Can": 1, "Positive Top-cap": 1,
            "Negative Top-cap": 1, "Blue Film": 1, "Positive Vent Cover": 1,
            "Negative Vent Cover": 1, "Rubber Nail": 1, "Al Nail": 1,
            "Insulation Bracket": 1, "Mylar Stack Wrap": 1, "Mylar Reinforcing Strip": 1,
            "MWCNT": 0.5, "Plasticiser": 0.5, "Mylar Tape": 0.5,
            "Welding Printing Adhesive": 0.5, "QR Code Tape": 0.5,
            "Battery Core Forming Nail": 2
        },
        "co2_water": {3: (2, 5), 5: (3, 6), 10: (4, 7), 15: (5, 8), 20: (6, 9)}
    },
    "NMC Cell 2": {
        "materials": {
            "NCM - CAM powder": 0.2, "SP-01": 0.2, "PVDF-1": 0.2, "NMP": 0.2, "Boehmite": 0.2,
            "PVDF-2": 0.2, "Graphite": 0.2, "SWCNT": 0.2, "MWCNT": 0.2, "PAA": 0.2,
            "Anoder Binder": 0.2, "Thickener": 0.2, "Al Foil": 0.2, "Cu Foil": 0.2,
            "LT Electrolyte": 0.2, "Separator": 5.2, "Tape": 0.4,
            "Aluminium Can": 1, "Positive Top-cap": 1, "Negative Top-cap": 1,
            "Blue Film": 0.2, "Positive Vent Cover": 1, "Negative Vent Cover": 1,
            "Rubber Nail": 1, "Al Nail": 1, "Insulation Bracket": 1,
            "Mylar Stack Wrap": 1, "Mylar Reinforcing Strip": 1,
            "Mylar Tape": 0.2, "Welding Printing Adhesive": 0.2, "QR Code Tape": 0.2,
            "Terminal Tape": 0.2, "PET Film": 0.2
        },
        "co2_water": {3: (2, 3), 5: (3, 4), 10: (4, 5), 15: (5, 6), 20: (6, 7)}
    },
    "LFP": {
        "materials": {
            "Polypropylene": 0.3, "Aluminium Foil": 0.3, "NMP Solvent - Cathode": 0.3,
            "SBR Binder - Cathode": 0.3, "Polyethylene Terephthalate": 0.3,
            "Anode Syn Graphite AAM": 0.3, "PVDF Binder - Anode": 0.3,
            "Cathode Active Material CAM + pCAM": 0.3, "Li": 0.3, "Can": 0.3,
            "NMP Solvent - Anode": 0.3, "CMC Binder - Anode": 0.3,
            "Carbon Black - Anode": 0.3, "SBR Binder - Anode": 0.3,
            "PVDF Binder - Cathode": 0.3, "Electrolyte": 0.3,
            "Copper Foil - Anode": 0.3, "Polyethylene - Separator": 0.3,
            "CMC Binder - Cathode": 0.3, "Carbon Black - Cathode": 0.3
        },
        "co2_water": {None: (8, 9)}
    }
}

# -------------------------
# CALCULATIONS
# -------------------------
def calc_site(lines, power_pct, mix, silicon_pcts):
    energy_gwh = lines * 50 * (power_pct / 100)
    total_cells = lines * 300 * (power_pct / 100)
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

# -------------------------
# STREAMLIT APP
# -------------------------
st.title("Agratas Corporate Carbon Sensitivity Model (2027–2035)")

year_data = []
annual_materials_list = []
cumulative_materials = {}

for year in YEARS:
    with st.expander(f"Year {year} Inputs"):
        # UK Inputs
        uk_lines = st.number_input(f"UK Lines ({year})", 0, 10, 0)
        uk_power = st.slider(f"UK % Power ({year})", 0, 100, 0)
        st.markdown("**UK Cell Mix (%)** (must sum to 100%)")
        uk_mix_nmc1 = st.number_input(f"NMC Cell 1 (%) - UK {year}", 0, 100, 0)
        uk_mix_nmc2 = st.number_input(f"NMC Cell 2 (%) - UK {year}", 0, 100, 0)
        uk_mix_lfp = st.number_input(f"LFP (%) - UK {year}", 0, 100, 0)
        uk_valid = (uk_mix_nmc1 + uk_mix_nmc2 + uk_mix_lfp == 100)

        uk_silicon = {}
        if uk_mix_nmc1 > 0:
            uk_silicon["NMC Cell 1"] = st.selectbox(f"UK NMC Cell 1 Silicon % ({year})", SILICON_PCTS, key=f"uks1{year}")
        if uk_mix_nmc2 > 0:
            uk_silicon["NMC Cell 2"] = st.selectbox(f"UK NMC Cell 2 Silicon % ({year})", SILICON_PCTS, key=f"uks2{year}")

        # India Inputs
        in_lines = st.number_input(f"India Lines ({year})", 0, 10, 0)
        in_power = st.slider(f"India % Power ({year})", 0, 210, 0)
        st.markdown("**India Cell Mix (%)** (must sum to 100%)")
        in_mix_nmc1 = st.number_input(f"NMC Cell 1 (%) - India {year}", 0, 100, 0)
        in_mix_nmc2 = st.number_input(f"NMC Cell 2 (%) - India {year}", 0, 100, 0)
        in_mix_lfp = st.number_input(f"LFP (%) - India {year}", 0, 100, 0)
        in_valid = (in_mix_nmc1 + in_mix_nmc2 + in_mix_lfp == 100)

        in_silicon = {}
        if in_mix_nmc1 > 0:
            in_silicon["NMC Cell 1"] = st.selectbox(f"India NMC Cell 1 Silicon % ({year})", SILICON_PCTS, key=f"ins1{year}")
        if in_mix_nmc2 > 0:
            in_silicon["NMC Cell 2"] = st.selectbox(f"India NMC Cell 2 Silicon % ({year})", SILICON_PCTS, key=f"ins2{year}")

        energy_mix = st.selectbox(f"Energy Mix ({year})", list(ENERGY_MIXES.keys()), key=f"mix{year}")

    uk_energy = uk_cells = uk_co2 = uk_water = 0
    uk_materials = {}
    if uk_valid:
        uk_energy, uk_cells, uk_co2, uk_water, uk_materials = calc_site(
            uk_lines, uk_power,
            {"NMC Cell 1": uk_mix_nmc1, "NMC Cell 2": uk_mix_nmc2, "LFP": uk_mix_lfp},
            uk_silicon
        )
    else:
        if uk_lines > 0:
            st.warning(f"UK mix for {year} does not sum to 100%. Skipping UK calculations.")

    in_energy = in_cells = in_co2 = in_water = 0
    in_materials = {}
    if in_valid:
        in_energy, in_cells, in_co2, in_water, in_materials = calc_site(
            in_lines, in_power,
            {"NMC Cell 1": in_mix_nmc1, "NMC Cell 2": in_mix_nmc2, "LFP": in_mix_lfp},
            in_silicon
        )
    else:
        if in_lines > 0:
            st.warning(f"India mix for {year} does not sum to 100%. Skipping India calculations.")

    total_energy = uk_energy + in_energy
    total_cells = uk_cells + in_cells
    total_co2 = uk_co2 + in_co2
    total_water = uk_water + in_water
    total_cost = (uk_energy * 1e6 * UK_PRICE_PER_KWH) + (in_energy * 1e6 * INDIA_PRICE_PER_KWH)

    # Merge material dicts
    year_materials = {}
    for m in set(uk_materials) | set(in_materials):
        year_materials[m] = uk_materials.get(m, 0) + in_materials.get(m, 0)

    # Update cumulative materials
    for m, v in year_materials.items():
        cumulative_materials[m] = cumulative_materials.get(m, 0) + v

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

# -------------------------
# OUTPUTS
# -------------------------
df = pd.DataFrame(year_data)

st.subheader("Annual Results")
st.dataframe(df.style.format({
    "Total Cells": "{:,.0f}",
    "Total Energy (GWh)": "{:,.2f}",
    "Total CO2 (tCO2)": "{:,.0f}",
    "Total Water (m³)": "{:,.0f}",
    "Total Cost (£)": "£{:,.2f}"
}))

st.subheader("Annual Material Usage")
if annual_materials_list:
    annual_materials_df = pd.concat(annual_materials_list, axis=1)
    st.dataframe(annual_materials_df)
else:
    st.info("No valid annual material usage data to display.")

st.subheader("Cumulative Totals (2027–2035)")
cum = df.drop(columns=["Year"]).sum(numeric_only=True)
cum_df = cum.to_frame(name="Total").T
st.dataframe(cum_df.style.format({
    "Total Cells": "{:,.0f}",
    "Total Energy (GWh)": "{:,.2f}",
    "Total CO2 (tCO2)": "{:,.0f}",
    "Total Water (m³)": "{:,.0f}",
    "Total Cost (£)": "£{:,.2f}"
}))

st.subheader("Cumulative Material Usage")
if cumulative_materials:
    cum_mat_df = pd.DataFrame(cumulative_materials.items(), columns=["Material", "Total Qty"])
    st.dataframe(cum_mat_df)
else:
    st.info("No material usage data available.")

st.subheader("Annual CO₂ Emissions (tCO₂)")
if not df.empty:
    st.bar_chart(df.set_index("Year")["Total CO2 (tCO2)"])

st.subheader("Cumulative CO₂ Emissions (tCO₂)")
if not df.empty:
    df["Cumulative CO2 (tCO2)"] = df["Total CO2 (tCO2)"].cumsum()
    st.line_chart(df.set_index("Year")["Cumulative CO2 (tCO2)"])
