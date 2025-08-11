# -------------------------
# Material sourcing configuration (only for NMC cells) — REPLACE THIS WHOLE SECTION
# -------------------------
uk_material_sourcing = {}
india_material_sourcing = {}

def render_material_sourcing(country_prefix, year, mix_nmc1, mix_nmc2, label_prefix):
    material_sourcing = {}
    if mix_nmc1 > 0 or mix_nmc2 > 0:
        with st.expander(f"🔬 {label_prefix} Material Sourcing Configuration ({year})", expanded=False):
            # Toggle between unique selection (single source) and % mix (multiple)
            sourcing_mode = st.radio(
                "Selection mode",
                options=["Unique source per category", "Percent mix across sources"],
                index=0,
                key=f"{country_prefix}_sourcing_mode_{year}",
                horizontal=True,
                help="Pick one source per category, or distribute percentages that sum to 100%."
            )

            def render_for_cell(cell_key, cell_title):
                st.markdown(f"**{cell_title} Material Sources**")
                material_sourcing[cell_key] = {}

                for material_category, sources in MATERIAL_SOURCES.items():
                    st.markdown(f"*{material_category}*")
                    material_sourcing[cell_key][material_category] = {}

                    if sourcing_mode == "Unique source per category":
                        # Single select — assigns 100% to the chosen one, 0% to others
                        selected = st.selectbox(
                            "Select source",
                            options=list(sources.keys()),
                            key=f"{country_prefix}_{cell_key}_{material_category}_{year}_unique",
                        )
                        for src in sources.keys():
                            material_sourcing[cell_key][material_category][src] = 100 if src == selected else 0
                        st.success("✅ Using a single source (100%) for this category")
                    else:
                        # Percent mode — show inputs for each source, require sum = 100 or 0
                        source_cols = st.columns(min(3, len(sources)))
                        col_idx = 0
                        total_pct = 0
                        for source_name, source_data in sources.items():
                            with source_cols[col_idx % len(source_cols)]:
                                pct = st.number_input(
                                    f"{source_name[:50]}..." if len(source_name) > 50 else source_name,
                                    min_value=0, max_value=100, value=0,
                                    key=f"{country_prefix}_{cell_key}_{material_category}_{source_name}_{year}",
                                    help=f"CO₂: +{source_data['co2']} kg/kWh, Water: +{source_data['water']} m³/kWh"
                                )
                                material_sourcing[cell_key][material_category][source_name] = pct
                                total_pct += pct
                            col_idx += 1

                        if total_pct > 0 and total_pct != 100:
                            st.warning(f"{material_category} percentages sum to {total_pct}% (should be 100% or 0%)")
                        elif total_pct == 100:
                            st.success(f"✅ {material_category} sourcing configured")

            if mix_nmc1 > 0:
                render_for_cell("NMC Cell 1", "NMC Cell 1")
            if mix_nmc2 > 0:
                render_for_cell("NMC Cell 2", "NMC Cell 2")

    return material_sourcing

# Call the renderer right after you collect the UK/India mixes for each year (inside the year tab)
# Example usage in your loop (keep near where you already compute uk_mix_nmc1, etc.):

# UK
if uk_lines > 0 and (uk_mix_nmc1 > 0 or uk_mix_nmc2 > 0):
    uk_material_sourcing = render_material_sourcing(
        country_prefix="uk",
        year=year,
        mix_nmc1=uk_mix_nmc1,
        mix_nmc2=uk_mix_nmc2,
        label_prefix="UK"
    )
else:
    uk_material_sourcing = {}

# India
if india_lines > 0 and (india_mix_nmc1 > 0 or india_mix_nmc2 > 0):
    india_material_sourcing = render_material_sourcing(
        country_prefix="india",
        year=year,
        mix_nmc1=india_mix_nmc1,
        mix_nmc2=india_mix_nmc2,
        label_prefix="India"
    )
else:
    india_material_sourcing = {}


import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# -------------------------
# CONFIG
# -------------------------
GBP_PER_INR = 1 / 105
UK_PRICE_PER_KWH = 0.258  # GBP
INDIA_PRICE_PER_KWH = 7.38 * GBP_PER_INR

YEARS = list(range(2027, 2036))

# Energy mix formulas for CO2 emissions based on GWh
ENERGY_MIXES = {
    "100% Grid": lambda x: 2777.40274 * (x ** 0.288551) if x > 0 else 0,
    "PPA:Grid (70:30)": lambda x: 784.3886 * (x ** 0.396496) if x > 0 else 0,
    "Grid+Gas (30% demand)": lambda x: 1460.00464 * (x ** 0.534148) if x > 0 else 0
}

CELL_TYPES = ["NMC Cell 1", "NMC Cell 2", "LFP"]
SILICON_PCTS = [3, 5, 10, 15, 20]

# -------------------------
# MATERIAL SOURCING OPTIONS
# -------------------------
MATERIAL_SOURCES = {
    "pCam Nickel": {
        "Nickel sulfate hexahydrate produced via carbonyl in Canada from nickel sulfate ore from Canada": {"co2": 3.81, "water": 9.22},
        "Nickel sulfate hexahydrate produced via heap leaching in Finland from MSP from Finland": {"co2": 4.73, "water": 5.46},
        "Nickel sulfate hexahydrate produced via HPAL in Brazil from MSP from Brazil": {"co2": 9.06, "water": 2.31},
        "Nickel sulfate hexahydrate produced via HPAL in China from Nickel laterite ore from Australia": {"co2": 10.81, "water": 10.39},
        "Nickel sulfate hexahydrate produced via ammonia refining in Australia from sulfide ore from Australia": {"co2": 12.92, "water": 3.44},
        "Nickel sulfate hexahydrate from global average": {"co2": 13.25, "water": 0},
        "Nickel sulfate hexahydrate produced via electrorefining in China from nickel sulfide ore from China": {"co2": 13.60, "water": -1.44},
        "Nickel sulfate produced via pyrometallurgy in Canada from nickel sulfide ore from Canada": {"co2": 18.32, "water": 19.53},
        "Nickel sulfate hexahydrate produced via HPAL in China from MHP from New Caledonia": {"co2": 20.82, "water": 4.86},
        "Nickel sulfate hexahydrate produced via RKEF in Indonesia (hydro electricity) from nickel laterite ore from Indonesia": {"co2": 40.04, "water": 30.33},
        "Nickel sulfate hexahydrate produced via HPAL in China from nickel laterite ore from Madagascar": {"co2": 41.00, "water": 0.58},
        "Nickel sulfate produced via HPAL in Brazil from nickel laterite ore from Brazil": {"co2": 41.20, "water": 10.50},
        "Nickel sulfate produced via pyrometallurgy in China from nickel sulfide ore from China": {"co2": 61.82, "water": -6.55},
    },
    "Synthetic Graphite": {
        "Anode-grade synthetic graphite in Sichuan, China from petroleum coke (powder)": {"co2": 5.74, "water": 0.61},
        "Anode-grade synthetic graphite in US - SERC from Petroleum Coke (powder)": {"co2": 8.76, "water": 1.45},
        "Anode-grade synthetic graphite in Sichuan (Calcination) and Taiwan (Graphitisation) from petroleum coke (powder)": {"co2": 12.05, "water": 1.23},
        "Synthetic Graphite - Freyr Custom Route": {"co2": 12.90, "water": 0},
        "Anode-grade synthetic graphite in Inner Mongolia (Calcination) and Taiwan (Graphitisation) from petroleum coke (powder)": {"co2": 13.83, "water": 2.03},
        "Anode-grade synthetic graphite from global average": {"co2": 15.28, "water": 3.41},
    },
    "pCam Manganese": {
        "Manganese sulfate monohydrate from global average (EF3.0)": {"co2": 0.32, "water": 0.07},
        "HPMSM produced via direct ore processing in Gabon with manganese ore from Gabon": {"co2": 0.90, "water": 0.80},
        "HPMSM produced via direct ore processing (calcination not included) in South Africa with manganese ore from South Africa": {"co2": 0.92, "water": 0.82},
        "HPMSM produced via EMM Dissolution in China with manganese ore from China": {"co2": 1.00, "water": 0.19},
        "HPMSM produced via direct ore processing in Australia with manganese ore from Australia": {"co2": 1.10, "water": 0.81},
        "HPMSM produced via direct ore processing in China with manganese ore from Australia": {"co2": 1.14, "water": 0.83},
        "HPMSM produced via direct ore processing in China with manganese ore from India": {"co2": 1.15, "water": 0.83},
        "HPMSM produced via direct ore processing in China with manganese ore from Gabon": {"co2": 1.21, "water": 0.83},
        "HPMSM produced via direct ore processing in China with manganese ore from Brazil": {"co2": 1.22, "water": 0.82},
        "HPMSM produced via direct ore processing in Australia with manganese ore from Gabon": {"co2": 1.28, "water": 0.82},
        "HPMSM produced via direct ore processing in China with manganese ore from South Africa": {"co2": 1.28, "water": 0.84},
    },
    "CAM Lithium": {
        "Lithium hydroxide monohydrate produced via evaporation and processing brine of salar brine in Chile": {"co2": 4.19, "water": 1.22},
        "Lithium hydroxide monohydrate produced via processing in Canada of spodumene concentrate from Canada": {"co2": 5.25, "water": 3.34},
        "Lithium hydroxide monohydrate from global average": {"co2": 9.02, "water": 1.93},
        "Lithium hydroxide monohydrate produced via processing in US of spodumene ore from US": {"co2": 9.18, "water": 1.73},
        "Lithium hydroxide - Freyr Custom Route": {"co2": 9.88, "water": 0},
        "Lithium hydroxide monohydrate produced via processing in China of spodumene concentrate from Australia": {"co2": 10.04, "water": 1.91},
        "Lithium hydroxide monohydrate produced via processing in the US of sedimentary clays from US": {"co2": 12.59, "water": 1.43},
    },
    "pCam Cobalt": {
        "Cobalt sulfate heptahydrate from global average": {"co2": 1.80, "water": 2.35},
        "Cobalt sulfate heptahydrate produced in China via HPAL from MHP with laterite ore from Indonesia": {"co2": 2.43, "water": 2.35},
        "Cobalt sulfate heptahydrate produced in Indonesia via HPAL from MHP with laterite ore from Indonesia": {"co2": 2.84, "water": 2.35},
    }
}

# -------------------------
# MATERIAL TABLES — CLEANED
# -------------------------
materials_data = {
    "NMC Cell 1": {
        "materials": {
            "NCM": {"qty": 0.5, "unit": "kg"},
            "SP-01": {"qty": 0.5, "unit": "kg"},
            "PVDF-1": {"qty": 0.5, "unit": "kg"},
            "NMP": {"qty": 0.5, "unit": "kg"},
            "Boehmite": {"qty": 0.5, "unit": "kg"},
            "PVDF-2": {"qty": 0.5, "unit": "kg"},
            "Graphite": {"qty": 0.5, "unit": "kg"},
            "SWCNT": {"qty": 0.5, "unit": "kg"},
            "PAA": {"qty": 0.5, "unit": "kg"},
            "Anoder Binder": {"qty": 0.5, "unit": "kg"},
            "Thickener (CMC)": {"qty": 0.5, "unit": "kg"},
            "Al Foil (Cell 1)": {"qty": 0.5, "unit": "kg"},
            "Cu Foil (Cell 1)": {"qty": 0.5, "unit": "kg"},
            "LT Electrolyte": {"qty": 0.5, "unit": "kg"},
            "Separator": {"qty": 3.5, "unit": "m2"},
            "Tape": {"qty": 1.0, "unit": "m2"},
            "Aluminium Can (Cell 1)": {"qty": 1.0, "unit": "Units"},
            "Positive Top-cap (Cell 1)": {"qty": 1.0, "unit": "Units"},
            "Negative Top-cap (Cell 1)": {"qty": 1.0, "unit": "Units"},
            "Blue Film (Cell 1)": {"qty": 1.0, "unit": "m2"},
            "Positive Vent Cover (Cell 1)": {"qty": 1.0, "unit": "Units"},
            "Negative Vent Cover (Cell 1)": {"qty": 1.0, "unit": "Units"},
            "Rubber Nail": {"qty": 1.0, "unit": "Units"},
            "Al Nail (Seal Pin)": {"qty": 1.0, "unit": "Units"},
            "Insulation Bracket (Cell 1)": {"qty": 1.0, "unit": "Units"},
            "Mylar Stack Wrap (Cell 1)": {"qty": 1.0, "unit": "Units"},
            "Mylar Reinforcing Strip (Cell 1)": {"qty": 1.0, "unit": "Units"},
            "MWCNT": {"qty": 0.5, "unit": "kg"},
            "Plasticiser": {"qty": 0.5, "unit": "kg"},
            "Mylar Tape": {"qty": 0.5, "unit": "m2"},
            "Welding Printing Adhesive": {"qty": 0.5, "unit": "m2"},
            "QR Code Tape": {"qty": 0.5, "unit": "m2"},
            "Battery Core Forming Nail": {"qty": 2.0, "unit": "Units"}
        },
        "base_co2_water_per_kwh": {"co2": 68.85, "water": 24.14},
        "silicon_co2_water_per_kwh": {
            3: {"co2": 2, "water": 5},
            5: {"co2": 3, "water": 6},
            10: {"co2": 4, "water": 7},
            15: {"co2": 5, "water": 8},
            20: {"co2": 6, "water": 9}
        }
    },
    "NMC Cell 2": {
        "materials": {
            "NCM - CAM powder": {"qty": 0.2, "unit": "kg"},
            "SP-01 - carbon black cam": {"qty": 0.2, "unit": "kg"},
            "PVDF-1 Cathode": {"qty": 0.2, "unit": "kg"},
            "NMP - solvent": {"qty": 0.2, "unit": "kg"},
            "Boehmite": {"qty": 0.2, "unit": "kg"},
            "PVDF-2": {"qty": 0.2, "unit": "kg"},
            "Graphite - 100% synthetic": {"qty": 0.2, "unit": "kg"},
            "SWCNT Single wall Carbon Nano tube": {"qty": 0.2, "unit": "kg"},
            "MWCNT Multiwall carbon nano tube": {"qty": 0.2, "unit": "kg"},
            "PAA - anode binder": {"qty": 0.2, "unit": "kg"},
            "Anoder Binder - SBR": {"qty": 0.2, "unit": "kg"},
            "Thickener (CMC)": {"qty": 0.2, "unit": "kg"},
            "Al Foil (Cell 2)": {"qty": 0.2, "unit": "kg"},
            "Cu Foil (Cell 2)": {"qty": 0.2, "unit": "kg"},
            "LT Electrolyte": {"qty": 0.2, "unit": "kg"},
            "Separator": {"qty": 5.2, "unit": "m2"},
            "Tape": {"qty": 0.4, "unit": "m2"},
            "Aluminium Can (Cell 2)": {"qty": 1.0, "unit": "Units"},
            "Positive Top-cap (Cell 2)": {"qty": 1.0, "unit": "Units"},
            "Negative Top-cap (Cell 2)": {"qty": 1.0, "unit": "Units"},
            "Blue Film (Cell 2)": {"qty": 0.2, "unit": "m2"},
            "Positive Vent Cover (Cell 2)": {"qty": 1.0, "unit": "Units"},
            "Negative Vent Cover (Cell 2)": {"qty": 1.0, "unit": "Units"},
            "Rubber Nail": {"qty": 1.0, "unit": "Units"},
            "Al Nail (Seal Pin)": {"qty": 1.0, "unit": "Units"},
            "Insulation Bracket (Cell 2)": {"qty": 1.0, "unit": "Units"},
            "Mylar Stack Wrap (Cell 2)": {"qty": 1.0, "unit": "Units"},
            "Mylar Reinforcing Strip (Cell 2)": {"qty": 1.0, "unit": "Units"},
            "Mylar Tape": {"qty": 0.2, "unit": "m2"},
            "Welding Printing Adhesive": {"qty": 0.2, "unit": "m2"},
            "QR Code Tape": {"qty": 0.2, "unit": "m2"},
            "Terminal Tape": {"qty": 0.2, "unit": "m2"},
            "PET Film": {"qty": 0.2, "unit": "m2"}
        },
        "base_co2_water_per_kwh": {"co2": 68.85, "water": 24.14},
        "silicon_co2_water_per_kwh": {
            3: {"co2": 2, "water": 3},
            5: {"co2": 3, "water": 4},
            10: {"co2": 4, "water": 5},
            15: {"co2": 5, "water": 6},
            20: {"co2": 6, "water": 7}
        }
    },
    "LFP": {
        "materials": {
            "Polypropylene": {"qty": 0.3, "unit": "kg"},
            "Aluminium Foil - Cathode": {"qty": 0.3, "unit": "kg"},
            "NMP Solvent - Cathode": {"qty": 0.3, "unit": "kg"},
            "SBR Binder - Cathode": {"qty": 0.3, "unit": "kg"},
            "Polyethylene Terephthalate": {"qty": 0.3, "unit": "kg"},
            "Anode Syn Graphite AAM": {"qty": 0.3, "unit": "kg"},
            "PVDF Binder - Anode": {"qty": 0.3, "unit": "kg"},
            "Cathode Active Material CAM + pCAM": {"qty": 0.3, "unit": "kg"},
            "Li": {"qty": 0.3, "unit": "kg"},
            "Can": {"qty": 0.3, "unit": "kg"},
            "NMP Solvent - Anode": {"qty": 0.3, "unit": "kg"},
            "CMC Binder - Anode": {"qty": 0.3, "unit": "kg"},
            "Carbon Black - Anode": {"qty": 0.3, "unit": "kg"},
            "SBR Binder - Anode": {"qty": 0.3, "unit": "kg"},
            "PVDF Binder - Cathode": {"qty": 0.3, "unit": "kg"},
            "Electrolyte": {"qty": 0.3, "unit": "kg"},
            "Copper Foil - Anode": {"qty": 0.3, "unit": "kg"},
            "Polyethylene - Separator": {"qty": 0.3, "unit": "kg"},
            "CMC Binder - Cathode": {"qty": 0.3, "unit": "kg"},
            "Carbon Black - Cathode": {"qty": 0.3, "unit": "kg"}
        },
        "base_co2_water_per_kwh": {"co2": 68.85 + 8, "water": 24.14 + 9}
    }
}


# -------------------------
# HELPER FUNCTIONS
# -------------------------
def calculate_material_sourcing_impact(cell_type, material_sourcing_mix):
    """Calculate the additional CO2 and water impact from material sourcing choices"""
    total_co2_addition = 0
    total_water_addition = 0
    
    for material_category, sources in material_sourcing_mix.items():
        if material_category not in MATERIAL_SOURCES:
            continue
            
        category_co2 = 0
        category_water = 0
        total_percentage = 0
        
        for source_name, percentage in sources.items():
            if percentage > 0 and source_name in MATERIAL_SOURCES[material_category]:
                source_data = MATERIAL_SOURCES[material_category][source_name]
                category_co2 += source_data["co2"] * (percentage / 100)
                category_water += source_data["water"] * (percentage / 100)
                total_percentage += percentage
        
        # Only add if the percentages sum to 100% for this category
        if total_percentage == 100:
            total_co2_addition += category_co2
            total_water_addition += category_water
    
    return total_co2_addition, total_water_addition

def calculate_material_sourcing_impact(material_sourcing_mix):
    """Calculate the additional CO2 and water impact from material sourcing choices"""
    total_co2_addition = 0
    total_water_addition = 0

    for material_category, sources in material_sourcing_mix.items():
        if material_category not in MATERIAL_SOURCES:
            continue

        category_co2 = 0
        category_water = 0
        total_percentage = 0

        for source_name, percentage in sources.items():
            if percentage > 0 and source_name in MATERIAL_SOURCES[material_category]:
                source_data = MATERIAL_SOURCES[material_category][source_name]
                category_co2 += source_data["co2"] * (percentage / 100)
                category_water += source_data["water"] * (percentage / 100)
                total_percentage += percentage

        # Only add if the percentages sum to 100% for this category
        if total_percentage == 100:
            total_co2_addition += category_co2
            total_water_addition += category_water

    return total_co2_addition, total_water_addition


def calculate_site_metrics(lines, power_pct, cell_mix, silicon_pcts, material_sourcing, country, energy_mix_name):
    """Calculate energy, cells, emissions, and materials for a site"""

    # Capacity
    if country == "UK":
        max_gwh_per_line = 50
        max_cells_per_line = 300
    else:
        max_gwh_per_line = 70
        max_cells_per_line = 300

    energy_gwh = lines * max_gwh_per_line * (power_pct / 100)
    total_cells = lines * max_cells_per_line * (power_pct / 100)

    site_materials = {}
    total_material_co2 = 0
    total_material_water = 0

    for cell_type, mix_percentage in cell_mix.items():
        if mix_percentage <= 0:
            continue

        cells_of_this_type = total_cells * (mix_percentage / 100)
        if cells_of_this_type <= 0:
            continue

        cell_data = materials_data[cell_type]

        # BOM aggregation
        for material_name, material_info in cell_data["materials"].items():
            material_qty = material_info["qty"] * cells_of_this_type
            material_key = f"{material_name} ({material_info['unit']})"
            site_materials[material_key] = site_materials.get(material_key, 0) + material_qty

        # Base per-kWh impacts
        co2_per_kwh = cell_data["base_co2_water_per_kwh"]["co2"]
        water_per_kwh = cell_data["base_co2_water_per_kwh"]["water"]

        # Silicon adjustments (for NMCs)
        if cell_type != "LFP":
            silicon_pct = silicon_pcts.get(cell_type, 3)
            co2_per_kwh += cell_data["silicon_co2_water_per_kwh"][silicon_pct]["co2"]
            water_per_kwh += cell_data["silicon_co2_water_per_kwh"][silicon_pct]["water"]

            # Material sourcing increments (only if provided for this cell)
            if cell_type in material_sourcing:
                sourcing_co2, sourcing_water = calculate_material_sourcing_impact(material_sourcing[cell_type])
                co2_per_kwh += sourcing_co2
                water_per_kwh += sourcing_water

        energy_kwh_for_this_cell_type = energy_gwh * (mix_percentage / 100) * 1e6  # GWh -> kWh
        total_material_co2 += energy_kwh_for_this_cell_type * co2_per_kwh / 1000  # -> tCO2
        total_material_water += energy_kwh_for_this_cell_type * water_per_kwh / 1000  # -> m³

    energy_co2 = ENERGY_MIXES[energy_mix_name](energy_gwh) if energy_gwh > 0 else 0
    total_co2 = energy_co2 + total_material_co2

    return {
        "energy_gwh": energy_gwh,
        "total_cells": total_cells,
        "total_co2": total_co2,
        "energy_co2": energy_co2,
        "material_co2": total_material_co2,
        "total_water": total_material_water,
        "materials": site_materials
    }

def calculate_costs(uk_energy_gwh, india_energy_gwh):
    """Calculate energy costs"""
    uk_cost = uk_energy_gwh * 1e6 * UK_PRICE_PER_KWH  # Convert GWh to kWh
    india_cost = india_energy_gwh * 1e6 * INDIA_PRICE_PER_KWH
    return uk_cost + india_cost

# -------------------------
# STREAMLIT APP
# -------------------------
st.set_page_config(
    page_title="Agrata Carbon Sensitivity Model",
    page_icon="🔋",
    layout="wide"
)

st.title("🔋 Agrata Corporate Carbon Sensitivity Model (2027–2035)")
st.markdown("**Comprehensive CO₂ emissions and material analysis for battery manufacturing operations**")

# Initialize session state for data storage
if 'year_data' not in st.session_state:
    st.session_state.year_data = []

if 'cumulative_materials' not in st.session_state:
    st.session_state.cumulative_materials = {}

# Sidebar for global settings
st.sidebar.header("Global Settings")
st.sidebar.markdown("### Energy Pricing")
st.sidebar.write(f"UK Price: £{UK_PRICE_PER_KWH} per kWh")
st.sidebar.write(f"India Price: £{INDIA_PRICE_PER_KWH:.4f} per kWh")
st.sidebar.markdown("### Production Capacity")
st.sidebar.write("UK: 50 GWh per line (max)")
st.sidebar.write("India: 70 GWh per line (max)")
st.sidebar.write("Both: 300 cells per line (max)")

# Main input section
st.header("📊 Annual Production Planning")

year_data = []
annual_materials_list = []
cumulative_materials = {}

# Create tabs for each year
year_tabs = st.tabs([str(year) for year in YEARS])

for i, year in enumerate(YEARS):
    with year_tabs[i]:
        st.subheader(f"Year {year} Configuration")
        
        # Create two columns for UK and India
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🇬🇧 UK Operations")
            uk_lines = st.number_input(f"Number of Lines", min_value=0, max_value=10, value=0, key=f"uk_lines_{year}")
            uk_power = st.slider(f"Power Utilization (%)", min_value=0, max_value=100, value=0, key=f"uk_power_{year}")
            
            st.markdown("**Cell Production Mix (%)**")
            uk_mix_nmc1 = st.number_input("NMC Cell 1 (%)", min_value=0, max_value=100, value=0, key=f"uk_nmc1_{year}")
            uk_mix_nmc2 = st.number_input("NMC Cell 2 (%)", min_value=0, max_value=100, value=0, key=f"uk_nmc2_{year}")
            uk_mix_lfp = st.number_input("LFP (%)", min_value=0, max_value=100, value=0, key=f"uk_lfp_{year}")
            
            uk_total_mix = uk_mix_nmc1 + uk_mix_nmc2 + uk_mix_lfp
            if uk_lines > 0 and uk_total_mix != 100:
                st.error(f"Cell mix must sum to 100% (currently {uk_total_mix}%)")
            elif uk_lines > 0:
                st.success(f"✅ Cell mix sums to 100%")
            
            uk_silicon = {}
            if uk_mix_nmc1 > 0:
                uk_silicon["NMC Cell 1"] = st.selectbox("NMC Cell 1 Silicon %", SILICON_PCTS, key=f"uk_si1_{year}")
            if uk_mix_nmc2 > 0:
                uk_silicon["NMC Cell 2"] = st.selectbox("NMC Cell 2 Silicon %", SILICON_PCTS, key=f"uk_si2_{year}")
        
        with col2:
            st.markdown("### 🇮🇳 India Operations")
            india_lines = st.number_input(f"Number of Lines", min_value=0, max_value=10, value=0, key=f"india_lines_{year}")
            india_power = st.slider(f"Power Utilization (%)", min_value=0, max_value=210, value=0, key=f"india_power_{year}")
            
            st.markdown("**Cell Production Mix (%)**")
            india_mix_nmc1 = st.number_input("NMC Cell 1 (%)", min_value=0, max_value=100, value=0, key=f"india_nmc1_{year}")
            india_mix_nmc2 = st.number_input("NMC Cell 2 (%)", min_value=0, max_value=100, value=0, key=f"india_nmc2_{year}")
            india_mix_lfp = st.number_input("LFP (%)", min_value=0, max_value=100, value=0, key=f"india_lfp_{year}")
            
            india_total_mix = india_mix_nmc1 + india_mix_nmc2 + india_mix_lfp
            if india_lines > 0 and india_total_mix != 100:
                st.error(f"Cell mix must sum to 100% (currently {india_total_mix}%)")
            elif india_lines > 0:
                st.success(f"✅ Cell mix sums to 100%")
            
            india_silicon = {}
            if india_mix_nmc1 > 0:
                india_silicon["NMC Cell 1"] = st.selectbox("NMC Cell 1 Silicon %", SILICON_PCTS, key=f"india_si1_{year}")
            if india_mix_nmc2 > 0:
                india_silicon["NMC Cell 2"] = st.selectbox("NMC Cell 2 Silicon %", SILICON_PCTS, key=f"india_si2_{year}")
        
        # Energy mix selection (applies to both countries)
        energy_mix = st.selectbox("Energy Mix", list(ENERGY_MIXES.keys()), key=f"energy_mix_{year}")
        
        # Calculate results for this year
        uk_results = {"energy_gwh": 0, "total_cells": 0, "total_co2": 0, "energy_co2": 0, "material_co2": 0, "total_water": 0, "materials": {}}
        india_results = {"energy_gwh": 0, "total_cells": 0, "total_co2": 0, "energy_co2": 0, "material_co2": 0, "total_water": 0, "materials": {}}
        
        if uk_lines > 0 and uk_total_mix == 100:
            uk_mix = {"NMC Cell 1": uk_mix_nmc1, "NMC Cell 2": uk_mix_nmc2, "LFP": uk_mix_lfp}
            uk_results = calculate_site_metrics(uk_lines, uk_power, uk_mix, uk_silicon, uk_material_sourcing, "UK", energy_mix)
        
        if india_lines > 0 and india_total_mix == 100:
            india_mix = {"NMC Cell 1": india_mix_nmc1, "NMC Cell 2": india_mix_nmc2, "LFP": india_mix_lfp}
            india_results = calculate_site_metrics(india_lines, india_power, india_mix, india_silicon, india_material_sourcing, "India", energy_mix)
        
        # Combine results
        total_energy = uk_results["energy_gwh"] + india_results["energy_gwh"]
        total_cells = uk_results["total_cells"] + india_results["total_cells"]
        total_co2 = uk_results["total_co2"] + india_results["total_co2"]
        total_energy_co2 = uk_results["energy_co2"] + india_results["energy_co2"]
        total_material_co2 = uk_results["material_co2"] + india_results["material_co2"]
        total_water = uk_results["total_water"] + india_results["total_water"]
        total_cost = calculate_costs(uk_results["energy_gwh"], india_results["energy_gwh"])
        
        # Combine materials
        year_materials = {}
        for materials_dict in [uk_results["materials"], india_results["materials"]]:
            for material, qty in materials_dict.items():
                if material in year_materials:
                    year_materials[material] += qty
                else:
                    year_materials[material] = qty
        
        # Update cumulative materials
        for material, qty in year_materials.items():
            if material in cumulative_materials:
                cumulative_materials[material] += qty
            else:
                cumulative_materials[material] = qty
        
        # Store year data
        year_data.append({
            "Year": year,
            "Total Cells": total_cells,
            "Total Energy (GWh)": total_energy,
            "Total CO2 (tCO2)": total_co2,
            "Energy CO2 (tCO2)": total_energy_co2,
            "Material CO2 (tCO2)": total_material_co2,
            "Total Water (m³)": total_water,
            "Total Cost (£)": total_cost,
            "UK Energy (GWh)": uk_results["energy_gwh"],
            "UK Cells": uk_results["total_cells"],
            "India Energy (GWh)": india_results["energy_gwh"],
            "India Cells": india_results["total_cells"]
        })
        
        # Add materials data
        if year_materials:
            mat_df = pd.DataFrame([(k, v) for k, v in year_materials.items()], columns=["Material", f"Qty_{year}"])
            annual_materials_list.append(mat_df)
        
        # Display year summary
        if total_cells > 0:
            st.markdown("### 📈 Year Summary")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Cells", f"{total_cells:,.0f}")
            with col2:
                st.metric("Total Energy", f"{total_energy:.1f} GWh")
            with col3:
                st.metric("Total CO₂", f"{total_co2:,.0f} tCO₂")
            with col4:
                st.metric("Total Cost", f"£{total_cost:,.0f}")

# -------------------------
# RESULTS AND ANALYSIS
# -------------------------
if year_data:
    df = pd.DataFrame(year_data)
    
    st.header("📊 Results & Analysis")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_cells_all = df["Total Cells"].sum()
        st.metric("Total Cells (2027-2035)", f"{total_cells_all:,.0f}")
    with col2:
        total_energy_all = df["Total Energy (GWh)"].sum()
        st.metric("Total Energy", f"{total_energy_all:.1f} GWh")
    with col3:
        total_co2_all = df["Total CO2 (tCO2)"].sum()
        st.metric("Total CO₂ Emissions", f"{total_co2_all:,.0f} tCO₂")
    with col4:
        total_cost_all = df["Total Cost (£)"].sum()
        st.metric("Total Cost", f"£{total_cost_all:,.0f}")
    
    # Annual results table
    st.subheader("Annual Results Summary")
    display_df = df.copy()
    st.dataframe(
        display_df,
        use_container_width=True,
        column_config={
            "Total Cells": st.column_config.NumberColumn(format="%.0f"),
            "Total Energy (GWh)": st.column_config.NumberColumn(format="%.2f"),
            "Total CO2 (tCO2)": st.column_config.NumberColumn(format="%.0f"),
            "Energy CO2 (tCO2)": st.column_config.NumberColumn(format="%.0f"),
            "Material CO2 (tCO2)": st.column_config.NumberColumn(format="%.0f"),
            "Total Water (m³)": st.column_config.NumberColumn(format="%.0f"),
            "Total Cost (£)": st.column_config.NumberColumn(format="£%.0f"),
            "UK Energy (GWh)": st.column_config.NumberColumn(format="%.2f"),
            "India Energy (GWh)": st.column_config.NumberColumn(format="%.2f"),
        }
    )
    
    # Visualizations
    st.subheader("📈 Visualizations")
    
    # CO2 emissions breakdown
    fig_co2 = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Annual CO₂ Emissions", "Cumulative CO₂ Emissions", 
                       "CO₂ Breakdown by Source", "Energy Production by Country"),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Annual CO2
    fig_co2.add_trace(
        go.Bar(x=df["Year"], y=df["Total CO2 (tCO2)"], name="Total CO₂"),
        row=1, col=1
    )
    
    # Cumulative CO2
    df["Cumulative CO2"] = df["Total CO2 (tCO2)"].cumsum()
    fig_co2.add_trace(
        go.Scatter(x=df["Year"], y=df["Cumulative CO2"], mode='lines+markers', name="Cumulative CO₂"),
        row=1, col=2
    )
    
    # CO2 breakdown
    fig_co2.add_trace(
        go.Bar(x=df["Year"], y=df["Energy CO2 (tCO2)"], name="Energy CO₂"),
        row=2, col=1
    )
    fig_co2.add_trace(
        go.Bar(x=df["Year"], y=df["Material CO2 (tCO2)"], name="Material CO₂"),
        row=2, col=1
    )
    
    # Energy by country
    fig_co2.add_trace(
        go.Bar(x=df["Year"], y=df["UK Energy (GWh)"], name="UK Energy"),
        row=2, col=2
    )
    fig_co2.add_trace(
        go.Bar(x=df["Year"], y=df["India Energy (GWh)"], name="India Energy"),
        row=2, col=2
    )
    
    fig_co2.update_layout(height=800, showlegend=True, title_text="Carbon Emissions & Energy Analysis")
    st.plotly_chart(fig_co2, use_container_width=True)
    
    # Material sourcing impact analysis
    if any(year_data):
        st.subheader("🔬 Material Sourcing Impact Analysis")
        
        # Create a summary of material sourcing choices
        sourcing_summary = []
        for year_info in year_data:
            year = year_info["Year"]
            # This would need to be stored during the calculation phase
            # For now, we'll show a placeholder
            sourcing_summary.append({
                "Year": year,
                "Note": "Material sourcing impact included in calculations"
            })
        
        if sourcing_summary:
            st.info("Material sourcing selections are factored into the CO₂ and water calculations above. Configure material sources in the year tabs to see the impact.")
    
    # Enhanced material breakdown
    if cumulative_materials:
        st.subheader("📊 Enhanced Material Analysis")
        
        # Create material categories
        material_categories = {
            "Active Materials": ["NCM", "CAM", "Graphite", "Li"],
            "Binders & Solvents": ["PVDF", "NMP", "PAA", "SBR", "CMC"],
            "Structural Components": ["Al Foil", "Cu Foil", "Separator", "Can", "Top-cap"],
            "Additives": ["Carbon Black", "SWCNT", "MWCNT", "Boehmite"]
        }
        
        categorized_materials = {}
        for category, keywords in material_categories.items():
            categorized_materials[category] = {}
            for material, qty in cumulative_materials.items():
                if any(keyword.lower() in material.lower() for keyword in keywords):
                    categorized_materials[category][material] = qty
        
        # Display categorized materials
        category_cols = st.columns(len(material_categories))
        for i, (category, materials) in enumerate(categorized_materials.items()):
            with category_cols[i]:
                st.markdown(f"**{category}**")
                if materials:
                    total_qty = sum(materials.values())
                    st.metric("Total Quantity", f"{total_qty:,.1f}")
                    
                    # Show top materials in this category
                    sorted_materials = sorted(materials.items(), key=lambda x: x[1], reverse=True)[:5]
                    for material, qty in sorted_materials:
                        material_name = material.split("(")[0].strip()
                        st.write(f"• {material_name}: {qty:,.1f}")
    
    # Cost-benefit analysis section
    st.subheader("💰 Cost-Benefit Analysis")
    
    if any(year_data):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Cost Summary**")
            total_energy_cost = df["Total Cost (£)"].sum()
            avg_cost_per_gwh = total_energy_cost / df["Total Energy (GWh)"].sum() if df["Total Energy (GWh)"].sum() > 0 else 0
            avg_cost_per_tco2 = total_energy_cost / df["Total CO2 (tCO2)"].sum() if df["Total CO2 (tCO2)"].sum() > 0 else 0
            
            st.metric("Total Energy Cost", f"£{total_energy_cost:,.0f}")
            st.metric("Cost per GWh", f"£{avg_cost_per_gwh:,.0f}")
            st.metric("Cost per tCO₂", f"£{avg_cost_per_tco2:,.0f}")
        
        with col2:
            st.markdown("**Efficiency Metrics**")
            total_cells = df["Total Cells"].sum()
            total_energy = df["Total Energy (GWh)"].sum()
            
            cells_per_gwh = total_cells / total_energy if total_energy > 0 else 0
            co2_per_cell = df["Total CO2 (tCO2)"].sum() / total_cells if total_cells > 0 else 0
            energy_per_cell = total_energy * 1000 / total_cells if total_cells > 0 else 0  # MWh per cell
            
            st.metric("Cells per GWh", f"{cells_per_gwh:,.0f}")
            st.metric("CO₂ per Cell", f"{co2_per_cell:.4f} tCO₂")
            st.metric("Energy per Cell", f"{energy_per_cell:.3f} MWh")
        
        # Combine all material data
        materials_combined = pd.concat(annual_materials_list, axis=1).fillna(0)
        
        # Show top 10 materials by total usage
        if not materials_combined.empty:
            # Calculate total usage for each material
            materials_combined['Total'] = materials_combined.select_dtypes(include=[np.number]).sum(axis=1)
            top_materials = materials_combined.nlargest(10, 'Total')
            
            st.write("**Top 10 Materials by Total Usage (2027-2035)**")
            st.dataframe(
                top_materials,
                use_container_width=True,
                column_config={col: st.column_config.NumberColumn(format="%.2f") for col in top_materials.columns if col != 'Material'}
            )
            
            # Material usage chart
            fig_materials = go.Figure()
            for year in YEARS:
                col_name = f"Qty_{year}"
                if col_name in top_materials.columns:
                    fig_materials.add_trace(
                        go.Bar(
                            name=str(year),
                            x=top_materials.index,
                            y=top_materials[col_name]
                        )
                    )
            
            fig_materials.update_layout(
                title="Top 10 Materials Usage by Year",
                xaxis_title="Materials",
                yaxis_title="Quantity",
                barmode='stack',
                height=500
            )
            st.plotly_chart(fig_materials, use_container_width=True)
    
    # Cumulative totals
    st.subheader("📊 Cumulative Totals (2027–2035)")
    cumulative_df = pd.DataFrame({
        "Metric": ["Total Cells", "Total Energy (GWh)", "Total CO₂ (tCO₂)", "Energy CO₂ (tCO₂)", 
                  "Material CO₂ (tCO₂)", "Total Water (m³)", "Total Cost (£)"],
        "Value": [
            df["Total Cells"].sum(),
            df["Total Energy (GWh)"].sum(),
            df["Total CO2 (tCO2)"].sum(),
            df["Energy CO2 (tCO2)"].sum(),
            df["Material CO2 (tCO2)"].sum(),
            df["Total Water (m³)"].sum(),
            df["Total Cost (£)"].sum()
        ]
    })
    
    st.dataframe(
        cumulative_df,
        use_container_width=True,
        column_config={
            "Value": st.column_config.NumberColumn(format="%.2f")
        }
    )
    
    # Cumulative materials
    if cumulative_materials:
        st.subheader("🔧 Cumulative Material Requirements (2027-2035)")
        cum_materials_df = pd.DataFrame([
            {"Material": material, "Total Quantity": qty, "Unit": material.split("(")[-1].replace(")", "") if "(" in material else ""}
            for material, qty in cumulative_materials.items()
        ]).sort_values("Total Quantity", ascending=False)
        
        # Show top 20 materials
        st.dataframe(
            cum_materials_df.head(20),
            use_container_width=True,
            column_config={
                "Total Quantity": st.column_config.NumberColumn(format="%.2f")
            }
        )
        
        # Download buttons
        st.subheader("📥 Download Data")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            csv_annual = df.to_csv(index=False)
            st.download_button(
                label="📊 Download Annual Data",
                data=csv_annual,
                file_name="agrata_annual_data.csv",
                mime="text/csv"
            )
        
        with col2:
            csv_materials = cum_materials_df.to_csv(index=False)
            st.download_button(
                label="🔧 Download Materials Data",
                data=csv_materials,
                file_name="agrata_materials_data.csv",
                mime="text/csv"
            )
        
        with col3:
            # Create summary report
            summary_data = {
                "Summary": ["Peak Annual CO₂", "Average Annual CO₂", "Peak Annual Energy", "Average Annual Energy"],
                "Value": [
                    f"{df['Total CO2 (tCO2)'].max():.0f} tCO₂",
                    f"{df['Total CO2 (tCO2)'].mean():.0f} tCO₂",
                    f"{df['Total Energy (GWh)'].max():.1f} GWh",
                    f"{df['Total Energy (GWh)'].mean():.1f} GWh"
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            csv_summary = summary_df.to_csv(index=False)
            st.download_button(
                label="📋 Download Summary",
                data=csv_summary,
                file_name="agrata_summary.csv",
                mime="text/csv"
            )

else:
    st.info("👆 Please configure production parameters for at least one year to see results.")

# Footer
st.markdown("---")
st.markdown("""
### 📝 Model Information
- **Energy Capacity**: UK (50 GWh/line), India (70 GWh/line)
- **Cell Capacity**: Both countries (300 cells/line at 100% power)
- **Energy Pricing**: UK (£0.258/kWh), India (£0.070/kWh)
- **CO₂ Calculations**: Based on energy mix formulas and material-specific emissions
- **Materials**: Comprehensive bill-of-materials for each cell type with silicon percentage variations

*Model uses placeholder values for materials and emissions - update with actual data as needed.*
""")

# Debugging section (can be removed in production)
with st.expander("🔧 Debug Information", expanded=False):
    st.write("**Energy Mix Formulas:**")
    for name, formula in ENERGY_MIXES.items():
        st.write(f"- {name}: Test with 1 GWh = {formula(1):.2f} tCO₂")

    st.write("**Material Data Structure Check:**")
    st.write(f"Cell types available: {list(materials_data.keys())}")
    st.write(f"NMC Cell 1 materials count: {len(materials_data['NMC Cell 1']['materials'])}")
    st.write(f"Silicon percentages for NMC Cell 1: {list(materials_data['NMC Cell 1']['silicon_co2_water_per_kwh'].keys())}")

if __name__ == "__main__":
    st.markdown("### 🚀 Ready to run!")
    st.markdown("Save this file as `agrata_carbon_model.py` and run with: `streamlit run agrata_carbon_model.py`")
