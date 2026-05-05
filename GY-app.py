import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from scipy.stats import norm

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Supply Chain Strategic Optimizer", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 8px; border: 1px solid #e9ecef; }
    .method-header { color: #1e3a8a; border-bottom: 2px solid #e2e8f0; padding-bottom: 5px; margin-bottom: 10px; }
    .perspective-box { background-color: #f1f5f9; padding: 10px; border-radius: 5px; font-size: 0.9rem; margin-top: 10px; border-left: 4px solid #3b82f6; }
    </style>
    """, unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def get_z_score(service_level_pct):
    return norm.ppf(service_level_pct / 100.0)

# --- HEADER ---
st.title("🛡️ Executive Safety Stock & Risk Dashboard")
st.markdown("A multi-perspective tool to quantify inventory investment vs. supply chain reliability.")

# --- SIDEBAR: GLOBAL INPUTS ---
st.sidebar.header("📋 Simulation Parameters")

with st.sidebar.expander("1. Demand & Forecast", expanded=True):
    avg_demand = st.sidebar.number_input("Avg Daily Demand (d)", value=100)
    std_demand = st.sidebar.slider("Demand Volatility (σd)", 5, 100, 25)
    forecast_bias = st.sidebar.slider("Forecast Bias (%)", -30, 30, 10, help="Structural error: selling more (+) or less (-) than planned.")
    
    bias_units = avg_demand * (forecast_bias / 100)
    rmse = np.sqrt(std_demand**2 + bias_units**2)

with st.sidebar.expander("2. Supply & Logistics", expanded=True):
    avg_lead_time = st.sidebar.number_input("Avg Lead Time (L)", value=14)
    std_lead_time = st.sidebar.slider("Lead Time Volatility (σL)", 0.0, 10.0, 3.0)
    # Heuristic markers
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
ss_heissig = max(0, (max_demand * max_lead_time) - (avg_demand * avg_lead_time))
ss_bias = z_score * rmse * np.sqrt(avg_lead_time)

# --- 5-COLUMN GRID DISPLAY ---
st.markdown("### 🔍 Strategic Method Comparison")
cols = st.columns(5)

# Method 1
with cols[0]:
    st.markdown("<h3 class='method-header'>Method 1</h3>", unsafe_allow_html=True)
    st.markdown("**Variable Demand**")
    st.metric("Safety Stock Units", f"{int(ss_1):,}")
    st.metric("Capital Tied Up", f"${int(ss_1 * unit_cost):,}")
    st.markdown("**Operational Perspective:** Focuses on Sales Volatility. Use this when your factory/supplier is next door, but consumer behavior is erratic.")
    with st.expander("Strategic Details"):
        st.write("Calculates risk based on demand standard deviation relative to the time the stock is in transit.")
        st.latex(r"Z \cdot \sigma_d \cdot \sqrt{L}")
        st.info(f"σ Demand: {std_demand}\nL: {avg_lead_time}")

# Method 2
with cols[1]:
    st.markdown("<h3 class='method-header'>Method 2</h3>", unsafe_allow_html=True)
    st.markdown("**Variable Supply**")
    st.metric("Safety Stock Units", f"{int(ss_2):,}")
    st.metric("Capital Tied Up", f"${int(ss_2 * unit_cost):,}")
    st.markdown("**Logistics Perspective:** Focuses on Transit Risk. Essential for global sourcing where port delays or shipping lanes are the main source of stockouts.")
    with st.expander("Strategic Details"):
        st.write("Translates lead time uncertainty into a volume buffer based on average consumption.")
        st.latex(r"Z \cdot d_{avg} \cdot \sigma_L")
        st.info(f"Avg D: {avg_demand}\nσ Lead: {std_lead_time}")

# Method 3
with cols[2]:
    st.markdown("<h3 class='method-header'>Method 3</h3>", unsafe_allow_html=True)
    st.markdown("**Combined Model**")
    st.metric("Safety Stock Units", f"{int(ss_3):,}")
    st.metric("Capital Tied Up", f"${int(ss_3 * unit_cost):,}")
    st.markdown("**Finance Perspective:** Maximum Efficiency. It recognizes that demand spikes and supply delays don't always happen at the same time.")
    with st.expander("Strategic Details"):
        st.write("Aggregates variance components to prevent over-buffering. This is the industry standard for S&OP optimization.")
        st.latex(r"Z \cdot \sqrt{L\sigma_d^2 + d^2\sigma_L^2}")
        st.info(f"Dem Var: {int(v_dem_comp)}\nSup Var: {int(v_sup_comp)}")

# Method 4
with cols[3]:
    st.markdown("<h3 class='method-header'>Method 4</h3>", unsafe_allow_html=True)
    st.markdown("**Heissig (Max-Avg)**")
    st.metric("Safety Stock Units", f"{int(ss_heissig):,}")
    st.metric("Capital Tied Up", f"${int(ss_heissig * unit_cost):,}")
    st.markdown("**Risk Perspective:** Worst-Case Protection. Used for critical components where the cost of a stockout is higher than the cost of storage.")
    with st.expander("Strategic Details"):
        st.write("A non-statistical method that assumes both max demand and max delay occur simultaneously.")
        st.latex(r"(D_{max} \cdot L_{max}) - (D_{avg} \cdot L_{avg})")
        st.info(f"Max Scene: {int(max_demand * max_lead_time)}")

# Method 5
with cols[4]:
    st.markdown("<h3 class='method-header'>Method 5</h3>", unsafe_allow_html=True)
    st.markdown("**Bias-Adjusted (RMSE)**")
    st.metric("Safety Stock Units", f"{int(ss_bias):,}")
    st.metric("Capital Tied Up", f"${int(ss_bias * unit_cost):,}")
    st.markdown("**Planning Perspective:** Process Governance. Highlights how much cash is 'wasted' by consistently poor forecasting.")
    with st.expander("Strategic Details"):
        st.write("Uses RMSE to account for structural bias. If bias is high, this model forces inventory to cover for the planning gap.")
        st.latex(r"Z \cdot RMSE \cdot \sqrt{L}")
        st.info(f"Bias Units: {bias_units:.1f}\nRMSE: {rmse:.2f}")

# --- COMPARISON CHART ---
st.markdown("---")
st.subheader("Working Capital Visualizer: Investment by Methodology")

df_plot = pd.DataFrame({
    "Methodology": ["M1: Var Demand", "M2: Var Supply", "M3: Combined", "M4: Heissig", "M5: Bias-Adj"],
    "Investment ($)": [ss_1 * unit_cost, ss_2 * unit_cost, ss_3 * unit_cost, ss_heissig * unit_cost, ss_bias * unit_cost]
})

fig = px.bar(df_plot, x="Methodology", y="Investment ($)", color="Methodology", text_auto='.2s', 
             color_discrete_sequence=px.colors.qualitative.Prism)
fig.update_layout(showlegend=False, height=400, plot_bgcolor='rgba(0,0,0,0)')
st.plotly_chart(fig, use_container_width=True)

# --- FINAL PERSPECTIVE ---
st.warning(f"""
**Strategic Insight:** If you transition from Method 4 (Heissig) to Method 3 (Combined Statistical), you could potentially reallocate **${int((ss_heissig - ss_3) * unit_cost):,}** in working capital elsewhere in the business while maintaining the same **{service_level}%** service level.
""")

