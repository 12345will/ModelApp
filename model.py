import streamlit as st
import pandas as pd
import numpy as np

# -------------------------
# CONFIG
# -------------------------
GBP_PER_INR = 1 / 105
UK_PRICE_PER_KWH = 0.258  # GBP
INDIA_PRICE_PER_KWH = 7.38 * GBP_PER_INR

YEARS = list(range(2027, 2036))
CELL_TYPES = ["NMC Cell 1", "NMC Cell 2", "LFP"]
SILICON_PCTS = [3, 5, 10, 15, 20]
ENERGY_MIXES = {
    "100% Grid": lambda x: 2777.40274 * (x ** 0.288551),
    "PPA:Grid (70:30)": lambda x: 784.3886 * (x ** 0.396496),
    "Grid+Gas (30% demand)": lambda x: 1460.00464 * (x ** 0.534148)
}

# -------------------------
# MATERIAL TABLES (placeholders)
# -------------------------
materials_data = {
    "NMC Cell 1": {
        "unit": "kg",
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
        "unit": "kg",
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
        "unit": "kg",
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
        "co2_water": {None: (8, 9)}  # no silicon %
    }
}

# -------------------------
# CALCULATIONS
# -------------------------
def calculate_year(year, uk_lines, uk_power_pct, uk_cell, uk_silicon_pct,
                   in_lines, in_power_pct, in_cell, in_silicon_pct, energy_mix):
    results = {}
    # UK Production
    uk_energy_gwh = uk_lines * 50 * (uk_power_pct / 100)
    uk_cells = uk_lines * 300 * (uk_power_pct / 100)
    uk_emissions = ENERGY_MIXES[energy_mix](uk_energy_gwh)
    if "NMC" in uk_cell:
        co2_kwh, water_kwh = materials_data[uk_cell]["co2_water"][uk_silicon_pct]
    else:
        co2_kwh, water_kwh = materials_data[uk_cell]["co2_water"][None]
    uk_co2 = uk_energy_gwh * 1e6 * co2_kwh / 1e3  # tCO2
    uk_water = uk_energy_gwh * 1e6 * water_kwh / 1e3  # m³
    uk_cost = uk_energy_gwh * 1e6 * UK_PRICE_PER_KWH

    # India Production
    in_energy_gwh = in_lines * 50 * (in_power_pct / 100)
    in_cells = in_lines * 300 * (in_power_pct / 100)
    in_emissions = ENERGY_MIXES[energy_mix](in_energy_gwh)
    if "NMC" in in_cell:
        co2_kwh_i, water_kwh_i = materials_data[in_cell]["co2_water"][in_silicon_pct]
    else:
        co2_kwh_i, water_kwh_i = materials_data[in_cell]["co2_water"][None]
    in_co2 = in_energy_gwh * 1e6 * co2_kwh_i / 1e3
    in_water = in_energy_gwh * 1e6 * water_kwh_i / 1e3
    in_cost = in_energy_gwh * 1e6 * INDIA_PRICE_PER_KWH

    # Materials
    total_materials = {}
    for site_cell, cell_count in [(uk_cell, uk_cells), (in_cell, in_cells)]:
        for mat, qty in materials_data[site_cell]["materials"].items():
            total_materials[mat] = total_materials.get(mat, 0) + qty * cell_count

    results.update({
        "Year": year,
        "UK Cells": uk_cells,
        "India Cells": in_cells,
        "Total Cells": uk_cells + in_cells,
        "UK Energy (GWh)": uk_energy_gwh,
        "India Energy (GWh)": in_energy_gwh,
        "Total Energy (GWh)": uk_energy_gwh + in_energy_gwh,
        "UK CO2 (t)": uk_co2,
        "India CO2 (t)": in_co2,
        "Total CO2 (t)": uk_co2 + in_co2,
        "UK Water (m³)": uk_water,
        "India Water (m³)": in_water,
        "Total Water (m³)": uk_water + in_water,
        "UK Cost (£)": uk_cost,
        "India Cost (£)": in_cost,
        "Total Cost (£)": uk_cost + in_cost
    })
    return results, total_materials

# -------------------------
# STREAMLIT UI
# -------------------------
st.title("Agratas Corporate Carbon Sensitivity Model (2027–2035)")

year_data = []
material_totals_cumulative = {}

for year in YEARS:
    st.sidebar.subheader(f"Year {year}")
    uk_lines = st.sidebar.number_input(f"UK Lines ({year})", 0, 10, 0)
    uk_power_pct = st.sidebar.slider(f"UK % Power ({year})", 0, 100, 0)
    uk_cell = st.sidebar.selectbox(f"UK Cell Type ({year})", CELL_TYPES, key=f"ukcell{year}")
    uk_silicon_pct = st.sidebar.selectbox(f"UK NMC Silicon % ({year})", SILICON_PCTS, key=f"uksil{year}") if "NMC" in uk_cell else None

    in_lines = st.sidebar.number_input(f"India Lines ({year})", 0, 10, 0)
    in_power_pct = st.sidebar.slider(f"India % Power ({year})", 0, 210, 0)
    in_cell = st.sidebar.selectbox(f"India Cell Type ({year})", CELL_TYPES, key=f"incell{year}")
    in_silicon_pct = st.sidebar.selectbox(f"India NMC Silicon % ({year})", SILICON_PCTS, key=f"insil{year}") if "NMC" in in_cell else None

    energy_mix = st.sidebar.selectbox(f"Energy Mix ({year})", list(ENERGY_MIXES.keys()), key=f"mix{year}")

    results, materials = calculate_year(year, uk_lines, uk_power_pct, uk_cell, uk_silicon_pct,
                                        in_lines, in_power_pct, in_cell, in_silicon_pct, energy_mix)
    year_data.append(results)
    for m, qty in materials.items():
        material_totals_cumulative[m] = material_totals_cumulative.get(m, 0) + qty

df = pd.DataFrame(year_data)

st.subheader("Annual Results")
st.dataframe(df)

st.subheader("Cumulative Totals (2027–2035)")
cum = df.sum(numeric_only=True)
st.write(cum)

st.subheader("Cumulative Material Usage")
materials_df = pd.DataFrame(material_totals_cumulative.items(), columns=["Material", "Total Qty"])
st.dataframe(materials_df)

st.subheader("Annual CO₂ Emissions (t)")
st.bar_chart(df.set_index("Year")["Total CO2 (t)"])

st.subheader("Cumulative CO₂ Emissions (t)")
df["Cumulative CO2 (t)"] = df["Total CO2 (t)"].cumsum()
st.line_chart(df.set_index("Year")["Cumulative CO2 (t)"])
