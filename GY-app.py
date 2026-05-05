import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from scipy.stats import norm

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Safety Stock Optimizer", layout="wide", initial_sidebar_state="expanded")

# --- HELPER FUNCTIONS ---
def get_z_score(service_level_pct):
    """Calculates the exact Z-score for a given service level percentage."""
    return norm.ppf(service_level_pct / 100.0)

# --- MAIN DASHBOARD HEADER ---
st.title("Strategic Safety Stock Optimizer")
st.markdown("Adjust the global parameters on the left to instantly compare the capital impact of each strategy.")
st.markdown("---")

# --- SIDEBAR: GLOBAL INPUTS ---
st.sidebar.header("⚙️ Global Parameters")

st.sidebar.subheader("Demand Assumptions")
avg_demand = st.sidebar.number_input("Average Daily Demand", value=100)
std_demand = st.sidebar.slider("Std Dev of Demand", min_value=5, max_value=100, value=25)
max_demand = st.sidebar.number_input("Maximum Daily Demand", value=150)

st.sidebar.subheader("Supply Assumptions")
avg_lead_time = st.sidebar.number_input("Average Lead Time (Days)", value=14)
std_lead_time = st.sidebar.slider("Std Dev of Lead Time (Days)", min_value=1.0, max_value=14.0, value=4.0)
max_lead_time = st.sidebar.number_input("Maximum Lead Time (Days)", value=21)

st.sidebar.subheader("Strategy & Cost")
service_level = st.sidebar.slider("Target Service Level (%)", min_value=80.0, max_value=99.9, value=95.0, step=0.1)
unit_cost = st.sidebar.number_input("Cost per Unit ($)", min_value=1.0, value=50.0, step=1.0)

# Calculate Z-Score once for all models
z_score = get_z_score(service_level)

# --- 4-COLUMN COMPARISON LAYOUT ---
col1, col2, col3, col4 = st.columns(4)

# 1. Variable Demand Model
with col1:
    st.subheader("1. Variable Demand")
    st.caption("Assumes constant supply")
    safety_stock_1 = z_score * std_demand * np.sqrt(avg_lead_time)
    cost_1 = safety_stock_1 * unit_cost
    
    st.metric(label="Safety Stock (Units)", value=f"{int(safety_stock_1):,}")
    st.metric(label="Capital Tied Up", value=f"${int(cost_1):,}")
    with st.expander("View Formula"):
        st.latex(r"SS = Z \times \sigma_d \times \sqrt{L}")

# 2. Variable Supply Model
with col2:
    st.subheader("2. Variable Supply")
    st.caption("Assumes constant demand")
    safety_stock_2 = z_score * avg_demand * std_lead_time
    cost_2 = safety_stock_2 * unit_cost
    
    st.metric(label="Safety Stock (Units)", value=f"{int(safety_stock_2):,}")
    st.metric(label="Capital Tied Up", value=f"${int(cost_2):,}")
    with st.expander("View Formula"):
        st.latex(r"SS = Z \times d_{avg} \times \sigma_L")

# 3. Combined Real-World Model
with col3:
    st.subheader("3. Real-World Model")
    st.caption("Combined volatility")
    var_demand_comp = avg_lead_time * (std_demand ** 2)
    var_lead_comp = (avg_demand ** 2) * (std_lead_time ** 2)
    safety_stock_3 = z_score * np.sqrt(var_demand_comp + var_lead_comp)
    cost_3 = safety_stock_3 * unit_cost
    
    st.metric(label="Safety Stock (Units)", value=f"{int(safety_stock_3):,}")
    st.metric(label="Capital Tied Up", value=f"${int(cost_3):,}")
    with st.expander("View Formula"):
        st.latex(r"SS = Z \times \sqrt{(L \times \sigma_d^2) + (d_{avg}^2 \times \sigma_L^2)}")

# 4. Heissig (Max-Avg) Method
with col4:
    st.subheader("4. Heissig Method")
    st.caption("Worst-case scenario (Max-Avg)")
    safety_stock_4 = (max_demand * max_lead_time) - (avg_demand * avg_lead_time)
    # Prevent negative safety stock if inputs are illogical
    safety_stock_4 = max(0, safety_stock_4) 
    cost_4 = safety_stock_4 * unit_cost
    
    st.metric(label="Safety Stock (Units)", value=f"{int(safety_stock_4):,}")
    st.metric(label="Capital Tied Up", value=f"${int(cost_4):,}")
    with st.expander("View Formula"):
        st.latex(r"SS = (Max\ D \times Max\ L) - (Avg\ D \times Avg\ L)")

st.markdown("---")

# --- VISUAL COMPARISON CHART ---
st.subheader("📊 Capital Allocation Comparison")
st.markdown("Visualize the working capital required to achieve the target service level under each methodology.")

# Prepare data for Plotly
data = {
    "Methodology": [
        "1. Variable Demand", 
        "2. Variable Supply", 
        "3. Real-World (Combined)", 
        "4. Heissig (Max-Avg)"
    ],
    "Capital Tied Up ($)": [cost_1, cost_2, cost_3, cost_4]
}
df = pd.DataFrame(data)

# Create chart
fig = px.bar(
    df, 
    x="Methodology", 
    y="Capital Tied Up ($)", 
    text_auto='.2s',
    color="Methodology",
    color_discrete_sequence=["#3b82f6", "#10b981", "#8b5cf6", "#f43f5e"] # Blue, Green, Purple, Rose
)

fig.update_layout(
    showlegend=False,
    xaxis_title="",
    yaxis_title="Working Capital ($)",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)"
)
fig.update_traces(textfont_size=14, textangle=0, textposition="outside", cliponaxis=False)

st.plotly_chart(fig, use_container_width=True)


