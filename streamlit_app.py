import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- SETTINGS ---
st.set_page_config(page_title="My 65kg Journey", layout="wide")
st.title("🚀 My 65kg Growth Portal")

# --- SIDEBAR: QUICK LOGGING ---
st.sidebar.header("📝 Quick Log")

# 1. Weight Tracker (Your Key Goal)
with st.sidebar.expander("⚖️ Weight Entry", expanded=True):
    current_w = st.number_input("Weight today (kg)", 40.0, 80.0, 55.0, 0.1)
    if st.button("Save Weight"):
        st.success(f"Weight {current_w}kg saved!")

# 2. Food & Creon
with st.sidebar.expander("🍞 Food Entry"):
    food = st.text_input("What did you eat?")
    if st.button("Calculate Creon"):
        if any(word in food.lower() for word in ["muffin", "stir fry", "chilli", "meat", "egg"]):
            st.warning("Take 6-7 Creon (25,000)")
        else:
            st.info("Take 3-5 Creon (25,000)")

# --- MAIN DASHBOARD ---
col1, col2 = st.columns([2, 1])

# NEW: GLUCOSE ENTRY BOX (Replacing Screenshot)
with col2:
    st.subheader("🩸 Libre Manual Entry")
    with st.container(border=True):
        bg_val = st.number_input("Current mmol/L", 2.0, 25.0, 10.0, step=0.1)
        
        st.write("**Trend Arrow:**")
        # Radio buttons are faster than checkboxes for single choice
        trend = st.radio("Select Trend", 
                         ["Flat (→)", "Rising (↑/↗)", "Falling (↓/↘)"], 
                         horizontal=True)
        
        if st.button("Log Reading"):
            st.success(f"Logged: {bg_val} {trend} at {datetime.now().strftime('%H:%M')}")

with col1:
    st.subheader("Weight Progress to 65kg")
    # Example growth data
    data = pd.DataFrame({
        'Day': ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        'Weight': [55.1, 55.3, 55.2, 55.5, 55.8, 56.1, 56.4],
        'Goal': [65.0] * 7
    })
    fig = px.line(data, x='Day', y=['Weight', 'Goal'], 
                  color_discrete_map={"Weight": "#00FF00", "Goal": "#FF0000"})
    st.plotly_chart(fig, use_container_width=True)

# CALORIE TALLY (Bottom section)
st.divider()
st.subheader("🔥 Daily Calorie Target")
kcal = st.number_input("Calories so far today", 0, 4000, 2560)
st.progress(min(kcal/2400, 1.0))
if kcal >= 2400:
    st.success("Target Smashed! You are in the Growth Zone.")
