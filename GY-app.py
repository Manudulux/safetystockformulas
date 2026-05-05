import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from scipy.stats import norm

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Executive Inventory Optimizer", layout="wide", initial_sidebar_state="expanded")

# --- CUSTOM CSS FIX ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { 
        background-color: #ffffff; 
        padding: 15px; 
        border-radius: 10px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
    }
    div[data-testid="stExpander"] { 
        background-color: #ffffff; 
        border: none; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
    }
    </style>
    """, unsafe_allow_html=True) # Changed from stdio to html

# --- HELPER FUNCTIONS ---
def get_z_score(service_level_pct):
    return norm.ppf(service_level_pct / 100.0)

# --- HEADER ---
st.title("🛡️ Strategic Safety Stock Dashboard")
st.markdown("Comparing five calculation methodologies to optimize working capital vs. service level risk.")

# --- SIDEBAR: GLOBAL INPUTS ---
st.sidebar.header("📋 Simulation Parameters")

with st.sidebar.expander("1. Demand & Forecast", expanded=True):
    avg_demand = st.number_input("Avg Daily Demand", value=100)
    std_demand = st.slider("Demand Volatility (Std Dev)", 5, 100, 25)
    forecast_bias = st.slider("Forecast Bias (%)", -30, 30, 10, 
                             help="Positive % means sales are consistently HIGHER than forecast.")
    
    # Calculate RMSE to account for Bias
    bias_units = avg_demand * (forecast_bias / 100)
    rmse = np.sqrt(std_demand**2 + bias_units**2)

with st.sidebar.expander("2. Supply & Logistics", expanded=True):
    avg_lead_time = st.number_input("Avg Lead Time (Days)", value=14)
    std_lead_time = st.slider("Lead Time Std Dev (Days)", 0.0, 10.0, 3.0)
    # Conservative assumptions for the Heissig Method
    max_demand = avg_demand + (2 * std_demand) 
    max_lead_time = avg_lead_time + (2 * std_lead_time)

with st.sidebar.expander("3. Financials & Risk", expanded=True):
    service_level = st.slider("Target Service Level (%)", 80.0, 99.9, 95.0, 0.1)
    unit_cost = st.number_input("Unit Cost ($)", value=50.0)

z_score = get_z_score(service_level)

# --- CALCULATIONS ---
# 1. Variable Demand
ss_v_dem = z_score * std_demand * np.sqrt(avg_lead_time)

# 2. Variable Supply
ss_v_sup = z_score * avg_demand * std_lead_time

# 3. Combined Real-World
v_dem_comp = avg_lead_time * (std_demand ** 2)
v_sup_comp = (avg_demand ** 2) * (std_lead_time ** 2)
ss_combined = z_score * np.sqrt(v_dem_comp + v_sup_comp)

# 4. Heissig (Max-Avg)
ss_heissig = max(0, (max_demand * max_lead_time) - (avg_demand * avg_lead_time))

# 5. RMSE / Bias-Adjusted
ss_rmse = z_score * rmse * np.sqrt(avg_lead_time)

# --- 5-COLUMN GRID DISPLAY ---
st.markdown("### 📊 Methodology Comparison")
cols = st.columns(5)

models = [
    {"name": "Variable Demand", "ss": ss_v_dem, "formula": r"Z \cdot \sigma_d \cdot \sqrt{L}", "pros": "Simple; focuses on sales noise.", "cons": "Ignores supplier delays."},
    {"name": "Variable Supply", "ss": ss_v_sup, "formula": r"Z \cdot d_{avg} \cdot \sigma_L", "pros": "Critical for long lead times.", "cons": "Ignores sales fluctuations."},
    {"name": "Combined Model", "ss": ss_combined, "formula": r"Z \cdot \sqrt{L\sigma_d^2 + d^2\sigma_L^2}", "pros": "Most capital efficient.", "cons": "Requires high data quality."},
    {"name": "Heissig (Max-Avg)", "ss": ss_heissig, "formula": r"(D_{max} \cdot L_{max}) - (D_{avg} \cdot L_{avg})", "pros": "Extreme safety; no stats.", "cons": "Very expensive; overstocks."},
    {"name": "Bias-Adjusted", "ss": ss_rmse, "formula": r"Z \cdot RMSE \cdot \sqrt{L}", "pros": "Accounts for poor forecasting.", "cons": "Masks root cause bias issues."}
]

for i, model in enumerate(models):
    with cols[i]:
        st.markdown(f"**{model['name']}**")
        st.metric("Units", f"{int(model['ss']):,}")
        st.metric("Capital", f"${int(model['ss'] * unit_cost):,}")
        with st.expander("Details"):
            st.latex(model['formula'])
            st.write(f"**Pros:** {model['pros']}")
            st.write(f"**Cons:** {model['cons']}")

# --- CHARTING ---
st.markdown("---")
st.subheader("Working Capital Impact Analysis")

df_plot = pd.DataFrame({
    "Methodology": [m['name'] for m in models],
    "Investment Required ($)": [m['ss'] * unit_cost for m in models]
})

fig = px.bar(df_plot, x="Methodology", y="Investment Required ($)", 
             color="Methodology", text_auto='.2s',
             color_discrete_sequence=px.colors.qualitative.Bold)

fig.update_layout(showlegend=False, height=450, margin=dict(t=20, b=20, l=20, r=20))
st.plotly_chart(fig, use_container_width=True)

# --- EXECUTIVE SUMMARY ---
st.info(f"**Strategic Insight:** At a **{forecast_bias}% bias**, the **Bias-Adjusted (RMSE)** model suggests an additional investment of **${int((ss_rmse - ss_v_dem) * unit_cost):,}** is required compared to a standard model just to maintain your **{service_level}%** service target.")

