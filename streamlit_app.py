import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import os
from datetime import datetime

# --- CONFIG & BRAIN ---
st.set_page_config(page_title="65kg Growth Portal", layout="wide")
API_KEY = "AIzaSyC1fn8hdh0HLDp7gw68ieUGTd9C6v8AgaY" # Put your key here
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-pro')

# --- DATA STORAGE LOGIC ---
DB_FILE = "growth_data.csv"

# Function to load data
def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Date", "Weight", "Glucose", "Trend", "Calories", "Food"])

# Function to save data
def save_entry(weight, glucose, trend, kcal, food):
    df = load_data()
    new_entry = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d"), weight, glucose, trend, kcal, food]], 
                              columns=["Date", "Weight", "Glucose", "Trend", "Calories", "Food"])
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(DB_FILE, index=False)

# Load existing history
history_df = load_data()

# --- SIDEBAR ---
st.sidebar.header("📝 Daily Entry")
weight = st.sidebar.number_input("Weight (kg)", 40.0, 80.0, 55.0, 0.1)
glucose = st.sidebar.number_input("Glucose (mmol/L)", 2.0, 25.0, 10.0, 0.1)
trend = st.sidebar.radio("Trend", ["Flat (→)", "Rising (↑)", "Falling (↓)"], horizontal=True)

# --- MAIN DASHBOARD ---
st.title("🚀 My 65kg Growth Portal")
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Weight Progress")
    if not history_df.empty:
        # Show real data + the goal line
        history_df['Goal'] = 65.0
        fig = px.line(history_df, x="Date", y=["Weight", "Goal"], 
                      color_discrete_map={"Weight": "#00FF00", "Goal": "#FF0000"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data yet. Log your first entry on the right!")

with col2:
    st.subheader("Log Food & Tally")
    food_input = st.text_input("What are you eating?")
    
    if st.button("Calculate & Add"):
        prompt = f"Estimate the calories in {food_input}. Return ONLY the number."
        response = model.generate_content(prompt)
        try:
            kcal = int(response.text.strip())
            st.session_state.current_kcal = st.session_state.get('current_kcal', 0) + kcal
            st.session_state.current_food = st.session_state.get('current_food', "") + f"{food_input}, "
            st.success(f"Added {kcal} kcal!")
        except:
            st.error("Error calculating calories.")

    current_total = st.session_state.get('current_kcal', 0)
    st.metric("Total Calories Today", f"{current_total} kcal")
    
    if st.button("🔒 PERMANENT SAVE FOR TODAY"):
        save_entry(weight, glucose, trend, current_total, st.session_state.get('current_food', ""))
        st.success("Data saved to your history!")
        st.rerun()

# --- CHAT BOX ---
st.divider()
user_msg = st.text_input("💬 Ask me anything (Creon, Sugar, Weight):")
if user_msg:
    ai_response = model.generate_content(f"User is at {glucose} mmol/L. Weight {weight}kg. Question: {user_msg}")
    st.write(f"**Gemini:** {ai_response.text}")
