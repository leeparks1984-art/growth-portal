import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
from datetime import datetime

# --- SETTINGS ---
st.set_page_config(page_title="65kg Growth Portal", layout="wide")

# --- API KEY (Sidebar) ---
API_KEY = st.sidebar.text_input("Gemini API Key", type="password")

# --- DATA INITIALIZATION ---
if 'history' not in st.session_state:
    # Starting baseline: Monday and Tuesday
    st.session_state.history = pd.DataFrame([
        {"Date": "2026-01-12", "Weight": 55.0, "Kcal": 3217, "Glucose": 10.3},
        {"Date": "2026-01-13", "Weight": 55.2, "Kcal": 2560, "Glucose": 13.6}
    ])
if 'current_kcal' not in st.session_state:
    st.session_state.current_kcal = 0

# --- GEMINI CALORIE & CHAT ENGINE ---
def gemini_engine(prompt, mode="chat"):
    if not API_KEY: return "Enter API Key"
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        if mode == "calories":
            # Strict instruction to prevent the 400,000 kcal error
            full_prompt = f"Give me ONLY the numeric calorie count for: {prompt}. No text, no ranges."
        else:
            full_prompt = prompt
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# --- SIDEBAR: LOGGING ---
st.sidebar.header("📝 Daily Entry")
w_in = st.sidebar.number_input("Weight (kg)", 40.0, 80.0, 55.2, 0.1)
g_in = st.sidebar.number_input("Glucose (mmol/L)", 2.0, 25.0, 13.6, 0.1)

if st.sidebar.button("💾 SAVE DATA"):
    new_row = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), 
                              "Weight": w_in, "Kcal": st.session_state.current_kcal, "Glucose": g_in}])
    st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True)
    st.sidebar.success("Saved!")

# --- MAIN DASHBOARD ---
st.title("🚀 My 65kg Growth Portal")
col1, col2 = st.columns([2, 1])

with col1:
    # --- WEIGHT GRAPH ---
    st.subheader("Weight Progress (Goal: 65kg)")
    df = st.session_state.history
    fig_w = px.line(df, x='Date', y='Weight', markers=True)
    fig_w.add_hline(y=65.0, line_dash="dash", line_color="red", annotation_text="Goal 65kg")
    fig_w.update_traces(line_color='#00FF00')
    st.plotly_chart(fig_w, width="stretch")

    # --- NEW: GLUCOSE RANGE GRAPH ---
    st.subheader("Glucose Range (Libre Style)")
    fig_g = go.Figure()
    # Add 'In-Range' Green Zone (4.0 to 10.0 mmol/L)
    fig_g.add_hrect(y0=4.0, y1=10.0, fillcolor="green", opacity=0.2, line_width=0, annotation_text="Target Range")
    # Plot Glucose Points
    fig_g.add_trace(go.Scatter(x=df['Date'], y=df['Glucose'], mode='lines+markers', name='Glucose', line=dict(color='blue')))
    fig_g.update_layout(yaxis_range=[0, 20], yaxis_title="mmol/L")
    st.plotly_chart(fig_g, width="stretch")

with col2:
    st.subheader("Food & Calorie Tally")
    food_in = st.text_input("Add food (e.g., 'Omelette')")
    if st.button("Add & Calculate"):
        res = gemini_engine(food_in, mode="calories")
        try:
            # Filters for only digits to prevent 400,000 error
            val = int(''.join(filter(str.isdigit, res)))
            if val < 5000: # Safety cap
                st.session_state.current_kcal += val
                st.success(f"Added {val} kcal!")
            else:
                st.error("AI returned an unrealistic number.")
        except:
            st.error("AI failed. Enter manually below.")
            
    manual = st.number_input("Manual kcal", 0, 1500, 0)
    if st.button("Add Manual"):
        st.session_state.current_kcal += manual

    st.metric("Today's Total", f"{st.session_state.current_kcal} kcal")
    st.progress(min(st.session_state.current_kcal / 2400, 1.0))

# --- CHAT INTEGRATION ---
st.divider()
st.subheader("💬 Growth Partner Chat")
user_q = st.text_input("Ask about Creon, Sugars, or your 65kg goal:")
if user_q:
    context = f"User is {w_in}kg. Glucose is {g_in} mmol/L. Total calories today: {st.session_state.current_kcal}."
    answer = gemini_engine(context + " Question: " + user_q)
    st.write(f"**Gemini:** {answer}")
