import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="65kg Growth Portal", layout="wide")

# --- GEMINI SETUP ---
# Update: Changed model to 'gemini-1.5-flash' to fix the 404 error
API_KEY = st.sidebar.text_input("API_Key", type="password")

def ask_gemini(prompt):
    if not API_KEY:
        return "Missing API Key"
    try:
        genai.configure(api_key=API_KEY)
        # Use 1.5-flash: it is faster and more reliable for calorie counting
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# --- SESSION STATE (Memory for the session) ---
if 'history' not in st.session_state:
    # Starting with a baseline for your Monday/Tuesday progress
    st.session_state.history = pd.DataFrame([
        {"Date": "2026-01-12", "Weight": 55.0, "Kcal": 3217},
    ])
if 'current_kcal' not in st.session_state:
    st.session_state.current_kcal = 0

# --- SIDEBAR: LOGGING ---
st.sidebar.header("📝 Daily Entry")
weight_input = st.sidebar.number_input("Weight today (kg)", 40.0, 80.0, 55.2, 0.1)
bg_val = st.sidebar.number_input("Glucose (mmol/L)", 2.0, 25.0, 8.0, 0.1)
trend = st.sidebar.radio("Trend", ["→", "↑", "↓"], horizontal=True)

if st.sidebar.button("💾 SAVE TODAY'S DATA"):
    new_data = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), 
                              "Weight": weight_input, 
                              "Kcal": st.session_state.current_kcal}])
    st.session_state.history = pd.concat([st.session_state.history, new_data], ignore_index=True)
    st.sidebar.success("Saved to session!")

# --- MAIN DASHBOARD ---
st.title("🚀 My 65kg Growth Portal")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Weight Progress to 65kg")
    df = st.session_state.history
    df['Goal'] = 65.0
    # Updated 'use_container_width' to 'width="stretch"' to fix log warning
    fig = px.line(df, x='Date', y=['Weight', 'Goal'], 
                  color_discrete_map={"Weight": "#00FF00", "Goal": "#FF0000"})
    fig.update_traces(mode='lines+markers')
    st.plotly_chart(fig, width="stretch")

with col2:
    st.subheader("Food & Calorie Tally")
    food_in = st.text_input("Add food (e.g., 'Italian Meats', 'Muffin')")
    
    if st.button("Calculate Calorie"):
        res = ask_gemini(f"Estimate calories in {food_in}. Return ONLY the number.")
        try:
            val = int(''.join(filter(str.isdigit, res)))
            st.session_state.current_kcal += val
            st.success(f"Added {val} kcal!")
        except:
            st.error("AI couldn't find a number. Try manual entry.")
            
    manual_kcal = st.number_input("Manual kcal entry", 0, 1500, 0)
    if st.button("Add Manual"):
        st.session_state.current_kcal += manual_kcal

    st.metric("Total Today", f"{st.session_state.current_kcal} kcal", delta=f"{st.session_state.current_kcal - 2400} vs Target")
    st.progress(min(st.session_state.current_kcal / 2400, 1.0))

# --- AI CHAT BOX ---
st.divider()
st.subheader("💬 Chat with Growth Partner")
user_q = st.text_input("Ask about Creon doses or sugar trends...")
if user_q:
    context = f"User is {weight_input}kg. Glucose is {bg_val} {trend}. Goal is 65kg."
    answer = ask_gemini(context + " Question: " + user_q)
    st.write(f"**Gemini:** {answer}")

# --- PERMANENCE HACK ---
st.sidebar.divider()
st.sidebar.write("### 📥 Backup Data")
st.sidebar.write("Since Streamlit Cloud resets, copy this if you want to save your progress for tomorrow:")
st.sidebar.dataframe(st.session_state.history)
