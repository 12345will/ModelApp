import streamlit as st
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
# MATERIAL TABLES (with corrected data structure)
# -------------------------
materials_data = {
    "NMC Cell 1": {
        "materials": {
            "NCM": {"qty": 0.5, "unit": "kg"},
            "Carbon Black": {"qty": 0.5, "unit": "kg"},
            "PVDF": {"qty": 1.0, "unit": "kg"},  # PVDF-1 + PVDF-2
            "NMP Solvent": {"qty": 0.5, "unit": "kg"},
            "Boehmite": {"qty": 0.5, "unit": "kg"},
            "Graphite": {"qty": 0.5, "unit": "kg"},
            "Carbon Nanotube (SWCNT)": {"qty": 0.5, "unit": "kg"},
            "Carbon Nanotube (MWCNT)": {"qty": 0.5, "unit": "kg"},
            "PAA": {"qty": 0.5, "unit": "kg"},
            "SBR Binder": {"qty": 0.5, "unit": "kg"},
            "CMC Binder": {"qty": 0.5, "unit": "kg"},
            "Aluminium Foil": {"qty": 0.5, "unit": "kg"},
            "Copper Foil": {"qty": 0.5, "unit": "kg"},
            "Electrolyte": {"qty": 0.5, "unit": "kg"},
            "Separator": {"qty": 3.5, "unit": "m2"},
            "Tape": {"qty": 1.0, "unit": "m2"},
            "Cell Can": {"qty": 1.0, "unit": "Units"},
            "Positive Top-cap": {"qty": 1.0, "unit": "Units"},
            "Negative Top-cap": {"qty": 1.0, "unit": "Units"},
            "Blue Film": {"qty": 1.0, "unit": "m2"},
            "Positive Vent Cover": {"qty": 1.0, "unit": "Units"},
            "Negative Vent Cover": {"qty": 1.0, "unit": "Units"},
            "Rubber Nail": {"qty": 1.0, "unit": "Units"},
            "Al Nail (Seal Pin)": {"qty": 1.0, "unit": "Units"},
            "Insulation Bracket": {"qty": 1.0, "unit": "Units"},
            "Mylar Stack Wrap": {"qty": 1.0, "unit": "Units"},
            "Mylar Reinforcing Strip": {"qty": 1.0, "unit": "Units"},
            "Plasticiser": {"qty": 0.5, "unit": "kg"},
            "Mylar Tape": {"qty": 0.5, "unit": "m2"},
            "Welding Printing Adhesive": {"qty": 0.5, "unit": "m2"},
            "QR Code Tape": {"qty": 0.5, "unit": "m2"},
            "Battery Core Forming Nail": {"qty": 2.0, "unit": "Units"}
        },
        "co2_water_per_kwh": {
            3: {"co2": 2, "water": 5},
            5: {"co2": 3, "water": 6},
            10: {"co2": 4, "water": 7},
            15: {"co2": 5, "water": 8},
            20: {"co2": 6, "water": 9}
        },
        "base_co2_water_per_kwh": {"co2": 2, "water": 5}
    },

    "NMC Cell 2": {
        "materials": {
            "NCM": {"qty": 0.2, "unit": "kg"},  # Unified from NCM - CAM powder
            "Carbon Black": {"qty": 0.2, "unit": "kg"},
            "PVDF": {"qty": 0.4, "unit": "kg"},  # PVDF-1 Cathode + PVDF-2
            "NMP Solvent": {"qty": 0.2, "unit": "kg"},
            "Boehmite": {"qty": 0.2, "unit": "kg"},
            "Graphite": {"qty": 0.2, "unit": "kg"},
            "Carbon Nanotube (SWCNT)": {"qty": 0.2, "unit": "kg"},
            "Carbon Nanotube (MWCNT)": {"qty": 0.2, "unit": "kg"},
            "PAA": {"qty": 0.2, "unit": "kg"},
            "SBR Binder": {"qty": 0.2, "unit": "kg"},
            "CMC Binder": {"qty": 0.2, "unit": "kg"},
            "Aluminium Foil": {"qty": 0.2, "unit": "kg"},
            "Copper Foil": {"qty": 0.2, "unit": "kg"},
            "Electrolyte": {"qty": 0.2, "unit": "kg"},
            "Separator": {"qty": 5.2, "unit": "m2"},
            "Tape": {"qty": 0.4, "unit": "m2"},
            "Cell Can": {"qty": 1.0, "unit": "Units"},
            "Positive Top-cap": {"qty": 1.0, "unit": "Units"},
            "Negative Top-cap": {"qty": 1.0, "unit": "Units"},
            "Blue Film": {"qty": 0.2, "unit": "m2"},
            "Positive Vent Cover": {"qty": 1.0, "unit": "Units"},
            "Negative Vent Cover": {"qty": 1.0, "unit": "Units"},
            "Rubber Nail": {"qty": 1.0, "unit": "Units"},
            "Al Nail (Seal Pin)": {"qty": 1.0, "unit": "Units"},
            "Insulation Bracket": {"qty": 1.0, "unit": "Units"},
            "Mylar Stack Wrap": {"qty": 1.0, "unit": "Units"},
            "Mylar Reinforcing Strip": {"qty": 1.0, "unit": "Units"},
            "Mylar Tape": {"qty": 0.2, "unit": "m2"},
            "Welding Printing Adhesive": {"qty": 0.2, "unit": "m2"},
            "QR Code Tape": {"qty": 0.2, "unit": "m2"},
            "Terminal Tape": {"qty": 0.2, "unit": "m2"},
            "PET Film": {"qty": 0.2, "unit": "m2"}
        },
        "co2_water_per_kwh": {
            3: {"co2": 2, "water": 3},
            5: {"co2": 3, "water": 4},
            10: {"co2": 4, "water": 5},
            15: {"co2": 5, "water": 6},
            20: {"co2": 6, "water": 7}
        },
        "base_co2_water_per_kwh": {"co2": 1, "water": 2}
    },

    "LFP": {
        "materials": {
            "Polypropylene": {"qty": 0.3, "unit": "kg"},
            "Aluminium Foil": {"qty": 0.3, "unit": "kg"},  # Unified from -Cathode
            "NMP Solvent": {"qty": 0.3, "unit": "kg"},
            "SBR Binder": {"qty": 0.6, "unit": "kg"},  # Cathode + Anode
            "Polyethylene Terephthalate": {"qty": 0.3, "unit": "kg"},
            "Graphite": {"qty": 0.3, "unit": "kg"},
            "PVDF": {"qty": 0.6, "unit": "kg"},  # Binder - Anode + -Cathode
            "Cathode Active Material CAM + pCAM": {"qty": 0.3, "unit": "kg"},
            "Li": {"qty": 0.3, "unit": "kg"},
            "Cell Can": {"qty": 0.3, "unit": "kg"},
            "CMC Binder": {"qty": 0.6, "unit": "kg"},  # Anode + Cathode
            "Carbon Black": {"qty": 0.6, "unit": "kg"},  # Anode + Cathode
            "Electrolyte": {"qty": 0.3, "unit": "kg"},
            "Copper Foil": {"qty": 0.3, "unit": "kg"},
            "Separator": {"qty": 0.3, "unit": "kg"}
        },
        "co2_water_per_kwh": {"co2": 8, "water": 9}
    }
}

# -------------------------
# HELPER FUNCTIONS
# -------------------------
def calculate_site_metrics(lines, power_pct, cell_mix, silicon_pcts, country, energy_mix_name):
    """Calculate energy, cells, emissions, and materials for a site"""
    
    # Calculate energy capacity based on country
    if country == "UK":
        max_gwh_per_line = 50
        max_cells_per_line = 300
    else:  # India
        max_gwh_per_line = 70
        max_cells_per_line = 300
    
    # Calculate actual energy and cell production
    energy_gwh = lines * max_gwh_per_line * (power_pct / 100)
    total_cells = lines * max_cells_per_line * (power_pct / 100)
    
    # Initialize outputs
    site_materials = {}
    total_material_co2 = 0
    total_material_water = 0
    
    # Process each cell type
    for cell_type, mix_percentage in cell_mix.items():
        if mix_percentage <= 0:
            continue
            
        cells_of_this_type = total_cells * (mix_percentage / 100)
        
        if cells_of_this_type <= 0:
            continue
            
        # Get material data
        cell_data = materials_data[cell_type]
        
        # Calculate material requirements
        for material_name, material_info in cell_data["materials"].items():
            material_qty = material_info["qty"] * cells_of_this_type
            material_key = f"{material_name} ({material_info['unit']})"
            
            if material_key in site_materials:
                site_materials[material_key] += material_qty
            else:
                site_materials[material_key] = material_qty
        
        # Calculate CO2 and water for materials (per kWh of energy used)
        if cell_type == "LFP":
            co2_per_kwh = cell_data["co2_water_per_kwh"]["co2"]
            water_per_kwh = cell_data["co2_water_per_kwh"]["water"]
        else:
            silicon_pct = silicon_pcts.get(cell_type, 3)  # Default to 3% if not specified
            co2_per_kwh = cell_data["co2_water_per_kwh"][silicon_pct]["co2"]
            water_per_kwh = cell_data["co2_water_per_kwh"][silicon_pct]["water"]
        
        # Calculate material-related emissions and water usage
        energy_kwh_for_this_cell_type = energy_gwh * (mix_percentage / 100) * 1e6  # Convert GWh to kWh
        total_material_co2 += energy_kwh_for_this_cell_type * co2_per_kwh / 1000  # Convert to tCO2
        total_material_water += energy_kwh_for_this_cell_type * water_per_kwh / 1000  # Convert to m³
    
    # Calculate energy-related CO2 emissions using the energy mix formula
    energy_co2 = ENERGY_MIXES[energy_mix_name](energy_gwh) if energy_gwh > 0 else 0
    
    # Total CO2 is energy emissions plus material emissions
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
            india_power = st.slider(f"Power Utilization (%)", min_value=0, max_value=100, value=0, key=f"india_power_{year}")
            
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
            uk_results = calculate_site_metrics(uk_lines, uk_power, uk_mix, uk_silicon, "UK", energy_mix)
        
        if india_lines > 0 and india_total_mix == 100:
            india_mix = {"NMC Cell 1": india_mix_nmc1, "NMC Cell 2": india_mix_nmc2, "LFP": india_mix_lfp}
            india_results = calculate_site_metrics(india_lines, india_power, india_mix, india_silicon, "India", energy_mix)
        
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
        ])
        
        # Show top 50 materials
        st.dataframe(
            cum_materials_df.head(100),
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
    
    st.write(f"**Material Data Structure Check:**")
    st.write(f"Cell types available: {list(materials_data.keys())}")
    st.write(f"NMC Cell 1 materials count: {len(materials_data['NMC Cell 1']['materials'])}")
    st.write(f"Silicon percentages for NMC Cell 1: {list(materials_data['NMC Cell 1']['co2_water_per_kwh'].keys())}")

if __name__ == "__main__":
    st.markdown("### 🚀 Ready to run!")
    st.markdown("Save this file as `agrata_carbon_model.py` and run with: `streamlit run agrata_carbon_model.py`")
