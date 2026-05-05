import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from scipy.stats import norm

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Executive Inventory Optimizer", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for a "Pro" look
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 8px; border: 1px solid #e9ecef; }
    .method-card { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); min-height: 500px; border-top: 5px solid #007bff; }
    .component-val { font-size: 0.85rem; color: #6c757d; font-family: monospace; }
    </style>
    """, unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def get_z_score(service_level_pct):
    return norm.ppf(service_level_pct / 100.0)

# --- HEADER ---
st.title("🛡️ Strategic Safety Stock Dashboard")
st.markdown("Detailed comparison of working capital requirements across five distinct mathematical models.")

# --- SIDEBAR: GLOBAL INPUTS ---
st.sidebar.header("📋 Simulation Parameters")

with st.sidebar.expander("1. Demand & Forecast", expanded=True):
    avg_demand = st.sidebar.number_input("Avg Daily Demand (d)", value=100)
    std_demand = st.sidebar.slider("Demand Volatility (σd)", 5, 100, 25)
    forecast_bias = st.sidebar.slider("Forecast Bias (%)", -30, 30, 10)
    
    # Calculate RMSE to account for Bias
    bias_units = avg_demand * (forecast_bias / 100)
    rmse = np.sqrt(std_demand**2 + bias_units**2)

with st.sidebar.expander("2. Supply & Logistics", expanded=True):
    avg_lead_time = st.sidebar.number_input("Avg Lead Time (L)", value=14)
    std_lead_time = st.sidebar.slider("Lead Time Volatility (σL)", 0.0, 10.0, 3.0)
    max_demand = avg_demand + (2 * std_demand) 
    max_lead_time = avg_lead_time + (2 * std_lead_time)

with st.sidebar.expander("3. Financials & Risk", expanded=True):
    service_level = st.sidebar.slider("Target Service Level (%)", 80.0, 99.9, 95.0, 0.1)
    unit_cost = st.sidebar.number_input("Unit Cost ($)", value=50.0)

z_score = get_z_score(service_level)

# --- CALCULATIONS ---
ss_1 = z_score * std_demand * np.sqrt(avg_lead_time)
ss_2 = z_score * avg_demand * std_lead_time
v_dem_comp = avg_lead_time * (std_demand ** 2)
v_sup_comp = (avg_demand ** 2) * (std_lead_time ** 2)
ss_3 = z_score * np.sqrt(v_dem_comp + v_sup_comp)
ss_4 = max(0, (max_demand * max_lead_time) - (avg_demand * avg_lead_time))
ss_5 = z_score * rmse * np.sqrt(avg_lead_time)

# --- 5-COLUMN GRID DISPLAY ---
st.markdown("### 🔍 Model-Specific Analysis")
cols = st.columns(5)

# Method 1
with cols[0]:
    st.markdown("### Method 1\n**Variable Demand**")
    st.metric("Safety Stock Units", f"{int(ss_1):,}")
    st.metric("Capital Tied Up", f"${int(ss_1 * unit_cost):,}")
    st.markdown("---")
    st.markdown("**Description:** Protects against sales spikes when the supplier is 100% reliable.")
    st.latex(r"Z \cdot \sigma_d \cdot \sqrt{L}")
    st.markdown("**Component Values:**")
    st.markdown(f"- Z-Score: `{z_score:.2f}`\n- σ Demand: `{std_demand}`\n- Lead Time: `{avg_lead_time}`")

# Method 2
with cols[1]:
    st.markdown("### Method 2\n**Variable Supply**")
    st.metric("Safety Stock Units", f"{int(ss_2):,}")
    st.metric("Capital Tied Up", f"${int(ss_2 * unit_cost):,}")
    st.markdown("---")
    st.markdown("**Description:** Ideal for products with steady demand but erratic transit times.")
    st.latex(r"Z \cdot d_{avg} \cdot \sigma_L")
    st.markdown("**Component Values:**")
    st.markdown(f"- Z-Score: `{z_score:.2f}`\n- Avg Demand: `{avg_demand}`\n- σ Lead Time: `{std_lead_time}`")

# Method 3
with cols[2]:
    st.markdown("### Method 3\n**Combined Model**")
    st.metric("Safety Stock Units", f"{int(ss_3):,}")
    st.metric("Capital Tied Up", f"${int(ss_3 * unit_cost):,}")
    st.markdown("---")
    st.markdown("**Description:** Accounts for the risk of a high-sales day and a late delivery occurring together.")
    st.latex(r"Z \cdot \sqrt{L\sigma_d^2 + d^2\sigma_L^2}")
    st.markdown("**Component Values:**")
    st.markdown(f"- σ-Dem Comp: `{int(v_dem_comp)}`\n- σ-Lead Comp: `{int(v_sup_comp)}`\n- Combined σ: `{int(np.sqrt(v_dem_comp + v_sup_comp))}`")

# Method 4
with cols[3]:
    st.markdown("### Method 4\n**Heissig (Max-Avg)**")
    st.metric("Safety Stock Units", f"{int(ss_4):,}")
    st.metric("Capital Tied Up", f"${int(ss_4 * unit_cost):,}")
    st.markdown("---")
    st.markdown("**Description:** A conservative stress-test assuming worst-case demand and delay.")
    st.latex(r"(D_{max} \cdot L_{max}) - (D_{avg} \cdot L_{avg})")
    st.markdown("**Component Values:**")
    st.markdown(f"- Max Scenario: `{int(max_demand * max_lead_time)}`\n- Avg Scenario: `{int(avg_demand * avg_lead_time)}` \n- Max Lead Time: `{max_lead_time}`")

# Method 5
with cols[4]:
    st.markdown("### Method 5\n**Bias-Adjusted**")
    st.metric("Safety Stock Units", f"{int(ss_5):,}")
    st.metric("Capital Tied Up", f"${int(ss_5 * unit_cost):,}")
    st.markdown("---")
    st.markdown("**Description:** Adjusts for structural bias. Essential if the team consistently under-forecasts.")
    st.latex(r"Z \cdot RMSE \cdot \sqrt{L}")
    st.markdown("**Component Values:**")
    st.markdown(f"- Z-Score: `{z_score:.2f}`\n- Bias (Units): `{bias_units:.1f}`\n- RMSE: `{rmse:.2f}`")

# --- CHARTING ---
st.markdown("---")
st.subheader("Working Capital Visualizer")

df_plot = pd.DataFrame({
    "Methodology": ["M1: Variable Demand", "M2: Variable Supply", "M3: Combined", "M4: Heissig", "M5: Bias-Adjusted"],
    "Investment Required ($)": [ss_1 * unit_cost, ss_2 * unit_cost, ss_3 * unit_cost, ss_4 * unit_cost, ss_5 * unit_cost]
})

fig = px.bar(df_plot, x="Methodology", y="Investment Required ($)", color="Methodology", text_auto='.2s')
fig.update_layout(showlegend=False, height=400)
st.plotly_chart(fig, use_container_width=True)

