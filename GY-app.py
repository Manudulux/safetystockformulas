import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from scipy.stats import norm

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Pro Safety Stock Optimizer", layout="wide", initial_sidebar_state="expanded")

# --- HELPER FUNCTIONS ---
def get_z_score(service_level_pct):
    return norm.ppf(service_level_pct / 100.0)

# --- MAIN DASHBOARD HEADER ---
st.title("🛡️ Strategic Safety Stock & Bias Optimizer")
st.markdown("""
Traditional models handle **Volatility** (random noise). This app adds **Bias Analysis** to account for structural forecasting errors—the 'silent killer' of service levels.
""")
st.markdown("---")

# --- SIDEBAR: GLOBAL INPUTS ---
st.sidebar.header("⚙️ Global Parameters")

with st.sidebar.expander("Demand & Forecast", expanded=True):
    avg_demand = st.number_input("Avg Daily Demand (Forecasted)", value=100)
    std_demand = st.slider("Demand Volatility (Std Dev)", 5, 100, 25)
    forecast_bias = st.slider("Structural Bias (%)", -30, 30, 10, help="Positive % means you consistently sell MORE than forecasted.")
    # Calculate RMSE (Root Mean Square Error) as a proxy for volatility + bias
    # Simplified RMSE = sqrt(std_dev^2 + bias_units^2)
    bias_units = avg_demand * (forecast_bias / 100)
    rmse = np.sqrt(std_demand**2 + bias_units**2)

with st.sidebar.expander("Supply & Lead Time", expanded=True):
    avg_lead_time = st.number_input("Avg Lead Time (Days)", value=14)
    std_lead_time = st.slider("Lead Time Volatility (Days)", 0.0, 14.0, 3.0)
    max_demand = avg_demand + (2 * std_demand) # Dynamic guess for Heissig
    max_lead_time = avg_lead_time + (2 * std_lead_time)

with st.sidebar.expander("Strategy & Cost", expanded=True):
    service_level = st.slider("Target Service Level (%)", 80.0, 99.9, 95.0, 0.1)
    unit_cost = st.number_input("Cost per Unit ($)", value=50.0)

z_score = get_z_score(service_level)

# --- COMPARISON LAYOUT ---
# We use two rows for better readability
row1_col1, row1_col2 = st.columns(2)
row2_col1, row2_col2, row2_col3 = st.columns(3)

# --- ROW 1: THE BIAS-ADJUSTED MODEL (NEW) ---
with row1_col1:
    st.info("### 🌟 Recommended: Forecast Error (RMSE) Model")
    st.caption("Best for: Accounting for structural Bias + Volatility")
    # Formula: SS = Z * RMSE * sqrt(L)
    ss_bias = z_score * rmse * np.sqrt(avg_lead_time)
    
    c1, c2 = st.columns(2)
    c1.metric("Safety Stock (Units)", f"{int(ss_bias):,}")
    c2.metric("Capital Tied Up", f"${int(ss_bias * unit_cost):,}")
    
    st.markdown("""
    **How it works:** Instead of just using demand 'noise' ($\sigma$), this uses **RMSE**. 
    If your bias is high, your RMSE increases, automatically padding your safety stock 
    to cover for the consistent forecast miss.
    
    * **Pros:** Only model that protects against a poor forecasting team.
    * **Cons:** Mathematically masks the bias instead of fixing the root cause.
    """)

with row1_col2:
    st.success("### 🚀 The Real-World (Combined) Model")
    st.caption("Best for: Modern, complex supply chains")
    v_dem = avg_lead_time * (std_demand**2)
    v_lt = (avg_demand**2) * (std_lead_time**2)
    ss_real = z_score * np.sqrt(v_dem + v_lt)
    
    c1, c2 = st.columns(2)
    c1.metric("Safety Stock (Units)", f"{int(ss_real):,}")
    c2.metric("Capital Tied Up", f"${int(ss_real * unit_cost):,}")
    
    st.markdown("""
    **How it works:** This is the gold standard. It calculates the statistical 
    interaction between demand swings and late deliveries.
    
    * **Pros:** Most mathematically efficient use of capital.
    * **Cons:** Requires clean data for both sales and actual delivery dates.
    """)

st.markdown("---")

# --- ROW 2: TRADITIONAL & HEURISTIC ---
with row2_col1:
    st.subheader("Variable Demand")
    ss_1 = z_score * std_demand * np.sqrt(avg_lead_time)
    st.metric("Units", f"{int(ss_1):,}")
    st.markdown("**Pros:** Simple to explain.  \n**Cons:** Completely ignores supplier delays.")

with row2_col2:
    st.subheader("Variable Supply")
    ss_2 = z_score * avg_demand * std_lead_time
    st.metric("Units", f"{int(ss_2):,}")
    st.markdown("**Pros:** Great for overseas imports.  \n**Cons:** Ignores sales spikes.")

with row2_col3:
    st.subheader("Heissig (Max-Avg)")
    ss_4 = max(0, (max_demand * max_lead_time) - (avg_demand * avg_lead_time))
    st.metric("Units", f"{int(ss_4):,}")
    st.markdown("**Pros:** No stats needed.  \n**Cons:** Extreme overstocking; very expensive.")

# --- VISUALIZATION ---
st.markdown("---")
st.subheader("📊 Comparison of Total Investment")

data = {
    "Model": ["Bias-Adjusted (RMSE)", "Real-World Combined", "Variable Demand", "Variable Supply", "Heissig Method"],
    "Safety Stock Units": [ss_bias, ss_real, ss_1, ss_2, ss_4],
    "Capital Required ($)": [ss_bias*unit_cost, ss_real*unit_cost, ss_1*unit_cost, ss_2*unit_cost, ss_4*unit_cost]
}
df = pd.DataFrame(data)

fig = px.bar(df, x="Model", y="Capital Required ($)", color="Model", text_auto='.2s',
             title=f"Capital Impact at {service_level}% Service Level")
st.plotly_chart(fig, use_container_width=True)

with st.expander("💡 Management Brief: Why Bias Matters"):
    st.write(f"""
    If your **Structural Bias** is **{forecast_bias}%**, your 'Cycle Stock' (the inventory you expect to sell) 
    is fundamentally wrong. 
    
    - If bias is **Positive ({forecast_bias}%)**: You are selling faster than planned. You will dip into your 
      safety stock almost every cycle, leading to "Phantom Stockouts."
    - If bias is **Negative**: You are over-forecasting. You will accumulate "Dead Stock" that is 
      hidden within your safety stock levels.
    
    **The RMSE Model** (shown above) is the only one that quantifies this risk for the CFO.
    """)


