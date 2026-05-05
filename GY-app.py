import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from scipy.stats import norm

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(
    page_title="Strategic Safety Stock & Forecast Bias Simulator",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# HELPERS
# =========================================================
def get_z_score(service_level_pct: float) -> float:
    """
    Convert a service level percentage to a Z-score from the standard normal distribution.
    """
    # Note: ppf(1.0) = inf, so service_level is capped below at 99.9
    return norm.ppf(service_level_pct / 100.0)


def as_float(x, default=0.0) -> float:
    """
    Optional robustness helper: safely cast to float.
    Streamlit inputs are usually numeric already, but this protects against edge cases.
    """
    try:
        return float(x)
    except Exception:
        return float(default)


def clamp(x: float, lo: float, hi: float) -> float:
    """Clamp a value between lo and hi."""
    return max(lo, min(hi, x))


# =========================================================
# HEADER
# =========================================================
st.title("🛡️ Strategic Safety Stock & Forecast Bias Simulator")
st.markdown(
    """
    This app compares multiple safety stock formulas and makes a critical distinction:

    **Bias shifts the baseline (mean demand)**, while **safety stock protects uncertainty around that baseline**.
    """
)

st.info(
    """
    **Quick guide (what you will see):**
    - Methods **M1–M4**: classic demand/supply uncertainty models.
    - **M5**: treats bias as *forecast unreliability* (RMSE). Big bias ⇒ bigger buffer (sign doesn't matter).
    - **M6**: *corrects the baseline first* (mean correction), then sizes safety stock for volatility only.

    ✅ The biggest working capital release from debiasing usually shows up in **Cycle Stock**, not Safety Stock.
    """
)

# =========================================================
# SIDEBAR INPUTS
# =========================================================
st.sidebar.header("📋 Simulation Parameters")

with st.sidebar.expander("1) Demand & Forecast", expanded=True):
    avg_demand = st.sidebar.number_input("Avg Daily Demand (d)", value=100, min_value=0)
    std_demand = st.sidebar.slider("Demand Volatility (σd)", 0, 100, 25)

    forecast_bias = st.sidebar.slider("Forecast Bias (%)", -30, 30, 10)

    st.sidebar.markdown(
        """
        **Forecast Bias (%) — What this means**  
        Systematic (directional) error in the forecast relative to actual demand.

        - **Positive bias** → forecast is higher than sales (**over‑forecasting**)  
        - **Negative bias** → forecast is lower than sales (**under‑forecasting**)

        ✅ Bias is *not* random noise.  
        It should **shift the demand baseline** (mean).  
        Random volatility (σd) is what safety stock is designed to protect.
        """
    )

with st.sidebar.expander("2) Supply & Logistics", expanded=True):
    avg_lead_time = st.sidebar.number_input("Avg Lead Time (L, days)", value=14, min_value=0)
    std_lead_time = st.sidebar.slider("Lead Time Volatility (σL, days)", 0.0, 10.0, 3.0)

with st.sidebar.expander("3) Financials & Risk", expanded=True):
    service_level = st.sidebar.slider("Target Service Level (%)", 80.0, 99.9, 95.0, 0.1)
    unit_cost = st.sidebar.number_input("Unit Cost ($)", value=50.0, min_value=0.0)

# =========================================================
# OPTIONAL ROBUSTNESS: normalize numeric types
# =========================================================
avg_demand = as_float(avg_demand, 0.0)
std_demand = as_float(std_demand, 0.0)
forecast_bias = as_float(forecast_bias, 0.0)
avg_lead_time = as_float(avg_lead_time, 0.0)
std_lead_time = as_float(std_lead_time, 0.0)
service_level = as_float(service_level, 95.0)
unit_cost = as_float(unit_cost, 0.0)

# Guard rails
service_level = clamp(service_level, 0.1, 99.9)  # avoid ppf(0) and ppf(1)
z = get_z_score(service_level)

# =========================================================
# DERIVED INPUTS
# =========================================================
bias_units = avg_demand * (forecast_bias / 100.0)

# RMSE used in Method 5 (bias treated as forecast unreliability; sign is removed via square)
rmse = np.sqrt(std_demand**2 + bias_units**2)

# Stress assumptions for Method 4 (Heissig)
max_demand = avg_demand + (2.0 * std_demand)
max_lead_time = avg_lead_time + (2.0 * std_lead_time)

# =========================================================
# SAFETY STOCK CALCULATIONS
# =========================================================
# Method 1 – Variable Demand (stable lead time)
ss_1 = z * std_demand * np.sqrt(avg_lead_time)

# Method 2 – Variable Supply (stable demand)
ss_2 = z * avg_demand * std_lead_time

# Method 3 – Combined uncertainty
ss_3 = z * np.sqrt(
    avg_lead_time * (std_demand**2) +
    (avg_demand**2) * (std_lead_time**2)
)

# Method 4 – Heissig (Max–Avg) deterministic stress-test
ss_4 = max(
    0.0,
    (max_demand * max_lead_time) - (avg_demand * avg_lead_time)
)

# Method 5 – Bias as risk (RMSE)
ss_5 = z * rmse * np.sqrt(avg_lead_time)

# =========================================================
# METHOD 6 – BIAS‑CORRECTED DEMAND BASELINE (ADVANCED)
# =========================================================
# Debiased demand: remove systematic bias from the mean demand baseline
effective_demand = avg_demand - bias_units
effective_demand = max(0.0, effective_demand)  # baseline cannot be negative

# After debiasing mean, size safety stock only for volatility (σd) over lead time
ss_6 = z * std_demand * np.sqrt(avg_lead_time)

# =========================================================
# CYCLE STOCK + TOTAL STOCK (NEW DISPLAY)
# =========================================================
# Cycle stock (baseline inventory over lead time)
# Assumption: For M1–M5, baseline remains avg_demand.
# For M6, baseline becomes effective_demand after debiasing.
cycle_1 = avg_demand * avg_lead_time
cycle_2 = avg_demand * avg_lead_time
cycle_3 = avg_demand * avg_lead_time
cycle_4 = avg_demand * avg_lead_time
cycle_5 = avg_demand * avg_lead_time
cycle_6 = effective_demand * avg_lead_time

total_1 = cycle_1 + ss_1
total_2 = cycle_2 + ss_2
total_3 = cycle_3 + ss_3
total_4 = cycle_4 + ss_4
total_5 = cycle_5 + ss_5
total_6 = cycle_6 + ss_6

# =========================================================
# METHOD BLOCK DISPLAY (SIX COLUMNS)
# =========================================================
st.markdown("## 🔍 Safety Stock Method Comparison")
cols = st.columns(6)

def method_block(col, title, ss_value, cycle_value, description, latex_formula=None, extra=None):
    with col:
        st.markdown(f"### {title}")
        st.metric("Safety Stock (units)", f"{int(round(ss_value)):,}")
        st.metric("Cycle Stock (units)", f"{int(round(cycle_value)):,}")
        st.metric("Total Stock (units)", f"{int(round(cycle_value + ss_value)):,}")
        st.markdown("---")
        st.markdown(description)
        if latex_formula:
            st.latex(latex_formula)
        if extra:
            st.markdown(extra)

# M1
method_block(
    cols[0],
    "M1 – Variable Demand",
    ss_1, cycle_1,
    """
    **Assumption:** lead time is stable, demand fluctuates.

    Use when supplier performance is reliable but customer demand varies due to promotions,
    seasonality, or market noise. This is the classic baseline safety stock model.
    """,
    latex_formula=r"SS = Z \cdot \sigma_d \cdot \sqrt{L}"
)

# M2
method_block(
    cols[1],
    "M2 – Variable Supply",
    ss_2, cycle_2,
    """
    **Assumption:** demand is stable, lead time fluctuates.

    Use when sales are predictable but replenishment performance is not (logistics congestion,
    customs delays, supplier variability).
    """,
    latex_formula=r"SS = Z \cdot d_{avg} \cdot \sigma_L"
)

# M3
method_block(
    cols[2],
    "M3 – Combined",
    ss_3, cycle_3,
    """
    **Assumption:** demand and lead time are both uncertain.

    Statistically correct default for complex/global networks where both market variability and
    execution variability drive inventory exposure.
    """,
    latex_formula=r"SS = Z \cdot \sqrt{L\sigma_d^2 + d_{avg}^2\sigma_L^2}"
)

# M4
method_block(
    cols[3],
    "M4 – Heissig (Max–Avg)",
    ss_4, cycle_4,
    """
    **Deterministic stress test (conservative).**

    Uses extreme-but-plausible scenarios (max demand and max lead time).
    Best for resilience planning rather than routine parameter setting.
    """,
    latex_formula=r"SS = (D_{max}\cdot L_{max})-(D_{avg}\cdot L_{avg})"
)

# M5
method_block(
    cols[4],
    "M5 – Bias as Risk",
    ss_5, cycle_5,
    """
    **Bias treated as forecast unreliability (RMSE).**

    This answers: *“If the forecast process is structurally wrong, how much buffer do I need
    to hit a given service level anyway?”*

    RMSE includes random error (volatility) and systematic error (bias magnitude).
    Because bias is squared, **positive and negative bias increase safety stock equally**.
    """,
    latex_formula=r"SS = Z \cdot RMSE \cdot \sqrt{L}",
    extra=(
        f"**Bias (units/day):** `{bias_units:.2f}`  \n"
        f"**RMSE:** `{rmse:.2f}`"
    )
)

# M6
method_block(
    cols[5],
    "M6 – Bias‑Corrected Baseline",
    ss_6, cycle_6,
    """
    **Advanced: correct the mean first, then protect variability.**

    This answers: *“If I remove systematic bias from the baseline, what uncertainty buffer
    do I need for the remaining volatility?”*

    **Key principle:**  
    - Safety stock protects uncertainty around the mean  
    - Bias shifts the mean itself

    After debiasing, safety stock is driven by σd and L — while the working-capital release
    mainly appears in **cycle stock**.
    """,
    latex_formula=r"SS = Z \cdot \sigma_d \cdot \sqrt{L}",
    extra=(
        f"**Debiased daily demand:** `{effective_demand:.2f}`  \n"
        f"**Baseline change (units/day):** `{effective_demand - avg_demand:.2f}`"
    )
)

# =========================================================
# EXTENDED COMMENTS / FAQ (NEW "USEFUL COMMENTS")
# =========================================================
st.markdown("---")
with st.expander("🧠 Explanation & Comments (Why results may look counter-intuitive)", expanded=True):
    st.markdown(
        """
        ### Why “positive bias” can increase safety stock in Method 5
        Many planners expect over‑forecasting (forecast > sales) to reduce safety stock because “we sell less than plan.”
        That intuition is operationally correct — **but it is primarily a cycle stock (baseline) correction effect**, not a
        safety stock effect.

        **Two different questions:**
        1. **Forecast reliability (risk problem):**  
           *“How wrong is my forecast process?”*  
           Large bias indicates the forecast cannot be trusted. Method 5 treats this as risk and increases safety stock.
           Direction does not matter because RMSE squares the error.
        2. **Mean correction (baseline problem):**  
           *“My forecast is consistently off in one direction. What is the correct mean demand?”*  
           This is what Method 6 addresses by shifting the baseline first.

        ### Why Method 6 may not change safety stock much (and that is OK)
        Method 6 removes bias from the mean and then sizes safety stock based on **volatility (σd)** and **lead time (L)**.
        If σd and L are unchanged, safety stock remains close to Method 1.

        ✅ The “win” is shown in the **Cycle Stock** (baseline demand × lead time) and therefore **Total Stock**.

        ### What to look at
        - If you want to reveal the cost of poor forecasting discipline → compare **M5 vs M1/M3**
        - If you want to quantify sustainable inventory release from debiasing → compare **Total Stock M6 vs others**
        """
    )

# =========================================================
# CHARTS
# =========================================================
st.markdown("---")
st.subheader("📊 Visuals")

# --- Chart 1: Safety Stock Investment ($)
st.markdown("### 💰 Safety Stock Investment ($) — all methods")

df_ss = pd.DataFrame({
    "Method": [
        "M1 Demand", "M2 Supply", "M3 Combined",
        "M4 Heissig", "M5 Bias Risk", "M6 Bias‑Corrected"
    ],
    "Safety Stock ($)": [ss_1, ss_2, ss_3, ss_4, ss_5, ss_6]
})
df_ss["Safety Stock ($)"] = df_ss["Safety Stock ($)"].astype(float) * float(unit_cost)

fig_ss = px.bar(
    df_ss,
    x="Method",
    y="Safety Stock ($)",
    text_auto=".2s"
)
fig_ss.update_layout(height=420, showlegend=False)
st.plotly_chart(fig_ss, use_container_width=True)

# --- Chart 2: Cycle + Safety Stock (Units) — stacked
st.markdown("### 📦 Total Inventory (Units) = Cycle Stock + Safety Stock")

df_units = pd.DataFrame({
    "Method": [
        "M1 Demand", "M2 Supply", "M3 Combined",
        "M4 Heissig", "M5 Bias Risk", "M6 Bias‑Corrected"
    ],
    "Cycle Stock (units)": [cycle_1, cycle_2, cycle_3, cycle_4, cycle_5, cycle_6],
    "Safety Stock (units)": [ss_1, ss_2, ss_3, ss_4, ss_5, ss_6],
})

df_units_long = df_units.melt(
    id_vars="Method",
    value_vars=["Cycle Stock (units)", "Safety Stock (units)"],
    var_name="Component",
    value_name="Units"
)

fig_units = px.bar(
    df_units_long,
    x="Method",
    y="Units",
    color="Component",
    text_auto=".2s"
)
fig_units.update_layout(height=450)
st.plotly_chart(fig_units, use_container_width=True)

# --- Chart 3: Cycle + Safety Stock ($) — stacked
st.markdown("### 💵 Total Inventory Value ($) = Cycle Stock + Safety Stock")

df_value = pd.DataFrame({
    "Method": df_units["Method"],
    "Cycle Stock ($)": df_units["Cycle Stock (units)"].astype(float) * float(unit_cost),
    "Safety Stock ($)": df_units["Safety Stock (units)"].astype(float) * float(unit_cost),
})

df_value_long = df_value.melt(
    id_vars="Method",
    value_vars=["Cycle Stock ($)", "Safety Stock ($)"],
    var_name="Component",
    value_name="Value ($)"
)

fig_value = px.bar(
    df_value_long,
    x="Method",
    y="Value ($)",
    color="Component",
    text_auto=".2s"
)
fig_value.update_layout(height=450)
st.plotly_chart(fig_value, use_container_width=True)

# =========================================================
# FOOTNOTE / ASSUMPTIONS
# =========================================================
st.caption(
    "Assumption used for Cycle Stock: baseline demand × average lead time. "
    "For M6 only, baseline demand is debiased (effective demand). "
    "All charts and metrics are illustrative and should be validated against your planning policy and item segmentation."
)

