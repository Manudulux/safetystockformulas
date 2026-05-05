import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import norm

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Safety Stock Optimizer", layout="wide", initial_sidebar_state="expanded")

# --- HELPER FUNCTIONS ---
def get_z_score(service_level_pct):
    """Calculates the exact Z-score for a given service level percentage."""
    return norm.ppf(service_level_pct / 100.0)

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("⚙️ Optimization Models")
st.sidebar.markdown("Select a calculation model to explore:")
model_choice = st.sidebar.radio(
    "",
    [
        "1. Variable Demand (Constant Supply)",
        "2. Variable Supply (Constant Demand)",
        "3. The Real-World Model (Combined)",
        "4. The Heissig Method (Max-Avg)"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Global Assumptions**")
unit_cost = st.sidebar.number_input("Cost per Unit ($)", min_value=1.0, value=50.0, step=1.0)

# --- MAIN DASHBOARD ---
st.title("Strategic Safety Stock Optimizer")
st.markdown("Interactive scenario modeling for supply chain resilience and working capital optimization.")

# --- MODEL 1: VARIABLE DEMAND ---
if "Variable Demand" in model_choice:
    st.header("1. Variable Demand Model")
    st.markdown("Use when supplier lead times are highly reliable, but customer demand fluctuates.")
    
    col1, col2, col3 = st.columns([1, 1, 1.5])
    
    with col1:
        st.subheader("Demand Inputs")
        avg_demand = st.number_input("Average Daily Demand", value=100)
        std_demand = st.slider("Std Dev of Demand (Volatility)", min_value=5, max_value=100, value=20)
        
    with col2:
        st.subheader("Supply & Risk")
        lead_time = st.number_input("Lead Time (Days)", value=14)
        service_level = st.slider("Target Service Level (%)", min_value=80.0, max_value=99.9, value=95.0, step=0.1)
        z_score = get_z_score(service_level)
        
    with col3:
        st.subheader("Results")
        # Formula: SS = Z * std_demand * sqrt(lead_time)
        safety_stock = z_score * std_demand * np.sqrt(lead_time)
        working_capital = safety_stock * unit_cost
        
        st.metric(label="Required Safety Stock (Units)", value=f"{int(safety_stock):,}")
        st.metric(label="Capital Tied Up", value=f"${int(working_capital):,}")
        st.caption(f"Calculated Z-Score: {z_score:.3f}")
        
    with st.expander("View Mathematical Formula"):
        st.latex(r"SS = Z \times \sigma_d \times \sqrt{L}")

# --- MODEL 2: VARIABLE SUPPLY ---
elif "Variable Supply" in model_choice:
    st.header("2. Variable Lead Time Model")
    st.markdown("Use when customer demand is highly predictable, but shipping/logistics are erratic.")
    
    col1, col2, col3 = st.columns([1, 1, 1.5])
    
    with col1:
        st.subheader("Demand Inputs")
        avg_demand = st.number_input("Average Daily Demand", value=100)
        
    with col2:
        st.subheader("Supply & Risk")
        avg_lead_time = st.number_input("Average Lead Time (Days)", value=14)
        std_lead_time = st.slider("Std Dev of Lead Time (Days)", min_value=1.0, max_value=14.0, value=3.0)
        service_level = st.slider("Target Service Level (%)", min_value=80.0, max_value=99.9, value=95.0, step=0.1)
        z_score = get_z_score(service_level)
        
    with col3:
        st.subheader("Results")
        # Formula: SS = Z * avg_demand * std_lead_time
        safety_stock = z_score * avg_demand * std_lead_time
        working_capital = safety_stock * unit_cost
        
        st.metric(label="Required Safety Stock (Units)", value=f"{int(safety_stock):,}")
        st.metric(label="Capital Tied Up", value=f"${int(working_capital):,}")
        st.caption(f"Calculated Z-Score: {z_score:.3f}")

    with st.expander("View Mathematical Formula"):
        st.latex(r"SS = Z \times d_{avg} \times \sigma_L")

# --- MODEL 3: COMBINED REAL-WORLD ---
elif "Real-World" in model_choice:
    st.header("3. The Real-World Model (Combined)")
    st.markdown("The most robust statistical approach. Accounts for unpredictable customers AND unpredictable suppliers.")
    
    col1, col2, col3 = st.columns([1, 1, 1.5])
    
    with col1:
        st.subheader("Demand Variability")
        avg_demand = st.number_input("Average Daily Demand", value=100)
        std_demand = st.slider("Std Dev of Demand", min_value=5, max_value=100, value=25)
        
    with col2:
        st.subheader("Supply Variability & Risk")
        avg_lead_time = st.number_input("Average Lead Time (Days)", value=14)
        std_lead_time = st.slider("Std Dev of Lead Time", min_value=1.0, max_value=14.0, value=4.0)
        service_level = st.slider("Target Service Level (%)", min_value=80.0, max_value=99.9, value=98.0, step=0.1)
        z_score = get_z_score(service_level)
        
    with col3:
        st.subheader("Results")
        # Formula: SS = Z * sqrt((L * std_d^2) + (d_avg^2 * std_L^2))
        demand_variance_component = avg_lead_time * (std_demand ** 2)
        lead_time_variance_component = (avg_demand ** 2) * (std_lead_time ** 2)
        
        safety_stock = z_score * np.sqrt(demand_variance_component + lead_time_variance_component)
        working_capital = safety_stock * unit_cost
        
        st.metric(label="Required Safety Stock (Units)", value=f"{int(safety_stock):,}")
        st.metric(label="Capital Tied Up", value=f"${int(working_capital):,}")
        
    with st.expander("View Mathematical Formula"):
        st.latex(r"SS = Z \times \sqrt{(L \times \sigma_d^2) + (d_{avg}^2 \times \sigma_L^2)}")

# --- MODEL 4: HEISSIG METHOD ---
elif "Heissig" in model_choice:
    st.header("4. The Heissig (Max-Average) Method")
    st.markdown("A simple heuristic rule for worst-case scenario planning. Often results in massive overstocking.")
    
    col1, col2, col3 = st.columns([1, 1, 1.5])
    
    with col1:
        st.subheader("Demand Inputs")
        avg_demand = st.number_input("Average Daily Demand", value=100)
        max_demand = st.number_input("Maximum Daily Demand", value=150)
        
    with col2:
        st.subheader("Supply Inputs")
        avg_lead_time = st.number_input("Average Lead Time (Days)", value=14)
        max_lead_time = st.number_input("Maximum Lead Time (Days)", value=21)
        
    with col3:
        st.subheader("Results")
        # Formula: SS = (Max D * Max L) - (Avg D * Avg L)
        max_scenario = max_demand * max_lead_time
        avg_scenario = avg_demand * avg_lead_time
        
        safety_stock = max_scenario - avg_scenario
        working_capital = safety_stock * unit_cost
        
        st.metric(label="Required Safety Stock (Units)", value=f"{int(safety_stock):,}")
        st.metric(label="Capital Tied Up", value=f"${int(working_capital):,}")
        
    st.warning("⚠️ **Management Note:** This method assumes the worst-case sales day and worst-case shipping delay happen simultaneously. It ties up significantly more cash than statistical models.")
    
    with st.expander("View Mathematical Formula"):
        st.latex(r"SS = (Max\ Demand \times Max\ Lead\ Time) - (Avg\ Demand \times Avg\ Lead\ Time)")

st.markdown("---")
st.caption("Developed for Internal Supply Chain Strategy & Working Capital Optimization.")


