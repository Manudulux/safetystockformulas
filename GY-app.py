import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from scipy.stats import norm

# =========================================================
# CONFIG & STYLING
# =========================================================
st.set_page_config(
    page_title="Executive Inventory Optimizer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# HELPER FUNCTIONS
# =========================================================
def get_z_score(service_level_pct: float) -> float:
    """
    Convert a service level percentage into a statistical Z-score.

    Parameters
    ----------
    service_level_pct : float
        Target service level (e.g. 95.0 for 95%).

    Returns
    -------
    float
        Corresponding Z-score from the standard normal distribution.
    """
    return norm.ppf(service_level_pct / 100.0)

# =========================================================
# HEADER
# =========================================================
st.title("🛡️ Strategic Safety Stock Dashboard")
st.markdown(
    "Detailed comparison of working capital requirements across five distinct "
    "inventory risk models."
)

# =========================================================
# SIDEBAR: GLOBAL INPUTS
# =========================================================
st.sidebar.header("📋 Simulation Parameters")

with st.sidebar.expander("1. Demand & Forecast", expanded=True):
    avg_demand = st.sidebar.number_input("Avg Daily Demand (d)", value=100)
    std_demand = st.sidebar.slider("Demand Volatility (σd)", 5, 100, 25)
    forecast_bias = st.sidebar.slider("Forecast Bias (%)", -30, 30, 10)

    # RMSE captures both random error (variance)
    # and systematic error (forecast bias)
    bias_units = avg_demand * (forecast_bias / 100)
    rmse = np.sqrt(std_demand ** 2 + bias_units ** 2)

with st.sidebar.expander("2. Supply & Logistics", expanded=True):
    avg_lead_time = st.sidebar.number_input("Avg Lead Time (L)", value=14)
    std_lead_time = st.sidebar.slider("Lead Time Volatility (σL)", 0.0, 10.0, 3.0)

    # Conservative assumptions for stress testing
    max_demand = avg_demand + (2 * std_demand)
    max_lead_time = avg_lead_time + (2 * std_lead_time)

with st.sidebar.expander("3. Financials & Risk", expanded=True):
    service_level = st.sidebar.slider(
        "Target Service Level (%)", 80.0, 99.9, 95.0, 0.1
    )
    unit_cost = st.sidebar.number_input("Unit Cost ($)", value=50.0)

z_score = get_z_score(service_level)

# =========================================================
# CALCULATIONS
# =========================================================
# Method 1 – Variable Demand
ss_1 = z_score * std_demand * np.sqrt(avg_lead_time)

# Method 2 – Variable Supply
ss_2 = z_score * avg_demand * std_lead_time

# Method 3 – Combined Model
v_dem_comp = avg_lead_time * (std_demand ** 2)
v_sup_comp = (avg_demand ** 2) * (std_lead_time ** 2)
ss_3 = z_score * np.sqrt(v_dem_comp + v_sup_comp)

# Method 4 – Heissig (Max–Avg)
ss_4 = max(
    0,
    (max_demand * max_lead_time) - (avg_demand * avg_lead_time)
)

# Method 5 – Bias-Adjusted
ss_5 = z_score * rmse * np.sqrt(avg_lead_time)

# =========================================================
# 5-COLUMN GRID DISPLAY
# =========================================================
st.markdown("### 🔍 Model-Specific Analysis")
cols = st.columns(5)

# -------------------------
# Method 1
# -------------------------
with cols[0]:
    st.markdown("### Method 1\n**Variable Demand**")
    st.metric("Safety Stock Units", f"{int(ss_1):,}")
    st.metric("Capital Tied Up", f"${int(ss_1 * unit_cost):,}")
    st.markdown("---")
    st.markdown(
        "**Description:** Models demand uncertainty during a stable replenishment "
        "lead time. Useful when suppliers are reliable and lead times are fixed, "
        "but customer demand fluctuates due to promotions, seasonality, or market "
        "volatility. This represents the classic safety stock baseline."
    )
    st.latex(r"Z \cdot \sigma_d \cdot \sqrt{L}")
    st.markdown(
        f"- Z-Score: `{z_score:.2f}`  \n"
        f"- σ Demand: `{std_demand}`  \n"
        f"- Lead Time: `{avg_lead_time}`"
    )

# -------------------------
# Method 2
# -------------------------
with cols[1]:
    st.markdown("### Method 2\n**Variable Supply**")
    st.metric("Safety Stock Units", f"{int(ss_2):,}")
    st.metric("Capital Tied Up", f"${int(ss_2 * unit_cost):,}")
    st.markdown("---")
    st.markdown(
        "**Description:** Isolates supply-side uncertainty under the assumption "
        "of stable demand. Best suited for environments where sales are predictable "
        "but lead times vary due to logistics congestion or supplier reliability."
    )
    st.latex(r"Z \cdot d_{avg} \cdot \sigma_L")
    st.markdown(
        f"- Z-Score: `{z_score:.2f}`  \n"
        f"- Avg Demand: `{avg_demand}`  \n"
        f"- σ Lead Time: `{std_lead_time}`"
    )

# -------------------------
# Method 3
# -------------------------
with cols[2]:
    st.markdown("### Method 3\n**Combined Model**")
    st.metric("Safety Stock Units", f"{int(ss_3):,}")
    st.metric("Capital Tied Up", f"${int(ss_3 * unit_cost):,}")
    st.markdown("---")
    st.markdown(
        "**Description:** Integrates both demand volatility and lead-time variability "
        "into a single statistically correct risk buffer. Recommended as the "
        "default model for complex or global supply chains."
    )
    st.latex(r"Z \cdot \sqrt{L\sigma_d^2 + d^2\sigma_L^2}")
    st.markdown(
        f"- Demand Variance Component: `{int(v_dem_comp)}`  \n"
        f"- Supply Variance Component: `{int(v_sup_comp)}`"
    )

# -------------------------
# Method 4
# -------------------------
with cols[3]:
    st.markdown("### Method 4\n**Heissig (Max–Avg)**")
    st.metric("Safety Stock Units", f"{int(ss_4):,}")
    st.metric("Capital Tied Up", f"${int(ss_4 * unit_cost):,}")
    st.markdown("---")
    st.markdown(
        "**Description:** Deterministic stress-test based on extreme-but-plausible "
        "scenarios. Calculates the buffer needed to survive maximum observed "
        "demand and maximum observed lead time. Best used for resilience planning "
        "rather than daily operations."
    )
    st.latex(r"(D_{max} \cdot L_{max}) - (D_{avg} \cdot L_{avg})")
    st.markdown(
        f"- Max Demand: `{int(max_demand)}`  \n"
        f"- Max Lead Time: `{max_lead_time}`"
    )

# -------------------------
# Method 5
# -------------------------
with cols[4]:
    st.markdown("### Method 5\n**Bias-Adjusted**")
    st.metric("Safety Stock Units", f"{int(ss_5):,}")
    st.metric("Capital Tied Up", f"${int(ss_5 * unit_cost):,}")
    st.markdown("---")
    st.markdown(
        "**Description:** Enhances traditional safety stock by explicitly correcting "
        "for systematic forecast bias. Uses RMSE to capture both noise and directional "
        "error, making it essential when teams chronically under- or over-forecast."
    )
    st.latex(r"Z \cdot RMSE \cdot \sqrt{L}")
    st.markdown(
        f"- Bias (Units): `{bias_units:.1f}`  \n"
        f"- RMSE: `{rmse:.2f}`"
    )

# =========================================================
# CHARTING
# =========================================================
st.markdown("---")
st.subheader("💰 Working Capital Visualizer")

df_plot = pd.DataFrame({
    "Methodology": [
        "M1: Variable Demand",
        "M2: Variable Supply",
        "M3: Combined",
        "M4: Heissig",
        "M5: Bias-Adjusted"
    ],
    "Investment Required ($)": [
        ss_1 * unit_cost,
        ss_2 * unit_cost,
        ss_3 * unit_cost,
        ss_4 * unit_cost,
        ss_5 * unit_cost,
    ]
})

fig = px.bar(
    df_plot,
    x="Methodology",
    y="Investment Required ($)",
    color="Methodology",
    text_auto=".2s"
)
fig.update_layout(showlegend=False, height=400)

st.plotly_chart(fig, use_container_width=True)

