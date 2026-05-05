import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from scipy.stats import norm

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(
    page_title="Strategic Safety Stock Simulator",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# HELPER FUNCTIONS
# =========================================================
def get_z_score(service_level_pct: float) -> float:
    """Convert service level percentage to Z-score."""
    return norm.ppf(service_level_pct / 100.0)

# =========================================================
# HEADER
# =========================================================
st.title("🛡️ Strategic Safety Stock & Forecast Bias Simulator")
st.markdown(
    """
    This tool compares multiple safety stock formulations and explicitly separates:
    **forecast bias correction** from **uncertainty protection**.
    """
)

# =========================================================
# SIDEBAR INPUTS
# =========================================================
st.sidebar.header("📋 Simulation Parameters")

with st.sidebar.expander("1. Demand & Forecast", expanded=True):
    avg_demand = st.number_input("Avg Daily Demand (d)", value=100)
    std_demand = st.slider("Demand Volatility (σd)", 5, 100, 25)

    forecast_bias = st.slider("Forecast Bias (%)", -30, 30, 10)
    st.markdown(
        """
        **Forecast Bias (%)**  
        Structural error in the forecast relative to actual demand.

        • **Positive bias** → Forecast is higher than sales (over‑forecasting)  
        • **Negative bias** → Forecast is lower than sales (under‑forecasting)

        Bias is *directional* and should adjust the demand baseline —  
        it is *not* random uncertainty.
        """
    )

    bias_units = avg_demand * (forecast_bias / 100)

    # RMSE used in Method 5 (bias treated as forecast unreliability)
    rmse = np.sqrt(std_demand**2 + bias_units**2)

with st.sidebar.expander("2. Supply & Logistics", expanded=True):
    avg_lead_time = st.number_input("Avg Lead Time (L)", value=14)
    std_lead_time = st.slider("Lead Time Volatility (σL)", 0.0, 10.0, 3.0)

    max_demand = avg_demand + (2 * std_demand)
    max_lead_time = avg_lead_time + (2 * std_lead_time)

with st.sidebar.expander("3. Financials & Risk", expanded=True):
    service_level = st.slider(
        "Target Service Level (%)", 80.0, 99.9, 95.0, 0.1
    )
    unit_cost = st.number_input("Unit Cost ($)", value=50.0)

z = get_z_score(service_level)

# =========================================================
# CALCULATIONS
# =========================================================
# Method 1 – Variable Demand
ss_1 = z * std_demand * np.sqrt(avg_lead_time)

# Method 2 – Variable Supply
ss_2 = z * avg_demand * std_lead_time

# Method 3 – Combined
ss_3 = z * np.sqrt(
    avg_lead_time * std_demand**2 +
    avg_demand**2 * std_lead_time**2
)

# Method 4 – Heissig
ss_4 = max(
    0,
    (max_demand * max_lead_time) -
    (avg_demand * avg_lead_time)
)

# Method 5 – Bias as Forecast Risk (RMSE)
ss_5 = z * rmse * np.sqrt(avg_lead_time)

# =========================================================
# METHOD 6 – BIAS‑CORRECTED DEMAND BASELINE (ADVANCED)
# =========================================================
effective_demand = avg_demand - bias_units

# Safety stock protects variability ONLY (bias removed from mean)
ss_6 = z * std_demand * np.sqrt(avg_lead_time)

planned_stock_std = avg_demand * avg_lead_time
planned_stock_bias_corrected = effective_demand * avg_lead_time

# =========================================================
# DISPLAY – SIX METHODS
# =========================================================
st.markdown("## 🔍 Safety Stock Method Comparison")
cols = st.columns(6)

def method_block(col, title, ss_value, description, extra=None):
    with col:
        st.markdown(f"### {title}")
        st.metric("Safety Stock Units", f"{int(ss_value):,}")
        st.metric("Capital ($)", f"{int(ss_value * unit_cost):,}")
        st.markdown("---")
        st.markdown(description)
        if extra:
            st.markdown(extra)

# --- Method 1
method_block(
    cols[0],
    "M1 – Variable Demand",
    ss_1,
    """
    **Assumption:** Stable supply, volatile demand.  
    Baseline probabilistic safety stock used in most mature supply chains.
    """
)

# --- Method 2
method_block(
    cols[1],
    "M2 – Variable Supply",
    ss_2,
    """
    **Assumption:** Stable demand, unreliable lead times.  
    Highlights exposure driven by logistics and supplier variability.
    """
)

# --- Method 3
method_block(
    cols[2],
    "M3 – Combined",
    ss_3,
    """
    **Assumption:** Demand and supply both uncertain.  
    Statistically correct default for complex, global networks.
    """
)

# --- Method 4
method_block(
    cols[3],
    "M4 – Heissig",
    ss_4,
    """
    **Deterministic stress test.**  
    Designed for resilience planning, not probability‑based service levels.
    """
)

# --- Method 5
method_block(
    cols[4],
    "M5 – Bias as Risk",
    ss_5,
    """
    **Bias treated as forecast unreliability.**

    RMSE captures *how wrong* the forecast is, regardless of direction.
    Positive and negative bias both increase safety stock because they indicate
    structural planning instability.
    """
)

# --- Method 6 (Advanced)
method_block(
    cols[5],
    "M6 – Bias‑Corrected Baseline",
    ss_6,
    """
    **Bias removed from the demand mean BEFORE sizing buffers.**

    This method separates two fundamentally different effects:

    1. **Bias (systematic error)** → Should shift the demand baseline  
    2. **Uncertainty (volatility)** → Should drive safety stock

    Once the forecast is debiased, safety stock only protects *residual variability*.
    """,
    extra=f"""
    **Debiased Daily Demand:** `{effective_demand:.1f}`  
    **Planned Stock During LT (Before):** `{planned_stock_std:,.0f}` units  
    **Planned Stock During LT (After):** `{planned_stock_bias_corrected:,.0f}` units  

    ✅ Safety stock may remain similar  
    ✅ **Total inventory drops significantly**
    """
)

# =========================================================
# EXECUTIVE EXPLANATION
# =========================================================
st.markdown("---")
st.markdown(
    """
    ## 🧠 Why Method 6 Matters

    Many planners expect over‑forecasting to *automatically* reduce safety stock.
    That intuition is operationally correct — but only **after bias is removed from
    the demand baseline**.

    **Key distinction:**

    • **Safety stock protects uncertainty around the mean**  
    • **Bias shifts the mean itself**

    If bias is left untreated:
    - Cycle stock is inflated  
    - Forecast error metrics worsen  
    - Safety stock may increase (Method 5)

    If bias is corrected properly (Method 6):
    - Planned inventory drops immediately  
    - Safety stock reflects true volatility  
    - Working capital is released sustainably  

    **Bottom line:**  
    Bias correction is a *planning hygiene problem* — not a safety stock problem.
    """
)

# =========================================================
# CHART
# =========================================================
st.subheader("💰 Working Capital Comparison")

df = pd.DataFrame({
    "Method": [
        "M1 Demand", "M2 Supply", "M3 Combined",
        "M4 Heissig", "M5 Bias Risk", "M6 Bias‑Corrected"
    ],
    "Safety Stock Investment ($)": [
        ss_1, ss_2, ss_3, ss_4, ss_5, ss_6
    ]
}) * unit_cost

fig = px.bar(
    df,
    x="Method",
    y="Safety Stock Investment ($)",
    text_auto=".2s"
)
fig.update_layout(height=450, showlegend=False)

st.plotly_chart(fig, use_container_width=True)

