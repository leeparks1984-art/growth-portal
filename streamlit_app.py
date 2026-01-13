import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
import re
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="65kg Growth Portal", layout="wide")

# --- API KEY ---
API_KEY = st.sidebar.text_input("Gemini API Key", type="password")

# --- DATA INITIALIZATION ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame([
        {"Timestamp": "2026-01-12 08:30", "Weight": 55.0, "Kcal": 3217, "Glucose": 10.2, "Trend": "→"},
        {"Timestamp": "2026-01-13 09:30", "Weight": 55.2, "Kcal": 2560, "Glucose": 13.6, "Trend": "↑"}
    ])
if 'current_kcal' not in st.session_state:
    st.session_state.current_kcal = 0

# --- GEMINI ENGINE ---
def gemini_engine(prompt, mode="chat"):
    if not API_KEY: return "Enter API Key"
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        system_msg = "User aiming for 65kg with PI and Diabetes. HATES tuna and coleslaw. Suggest high-calorie options."
        
        if mode == "calories":
            full_prompt = f"Provide ONLY the numeric integer calorie count for: {prompt}."
        else:
            full_prompt = system_msg + " Context: " + prompt
            
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"AI Error: {str(e)}"

# --- SIDEBAR: ENTRY ---
st.sidebar.header("📝 Real-Time Entry")
w_in = st.sidebar.number_input("Weight (kg)", 40.0, 80.0, 55.2, 0.1)
g_in = st.sidebar.number_input("Glucose (mmol/L)", 2.0, 25.0, 13.6, 0.1)
trend_in = st.sidebar.selectbox("Trend Arrow", ["→ (Stable)", "↑ (Rising)", "↗ (Slow)", "↓ (Falling)", "↘ (Slow)"])

if st.sidebar.button("💾 SAVE DATA NOW"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_row = pd.DataFrame([{"Timestamp": now, "Weight": w_in, "Kcal": st.session_state.current_kcal, "Glucose": g_in, "Trend": trend_in}])
    st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True)
    st.sidebar.success(f"Saved at {now}!")

# --- MAIN DASHBOARD ---
st.title("🚀 My 65kg Growth Portal")
df = st.session_state.history
df['Timestamp'] = pd.to_datetime(df['Timestamp'])

# 1. THE MISSING WEIGHT TRACKER (At the top)
st.subheader("⚖️ Weight Journey to 65kg")
fig_w = px.line(df, x='Timestamp', y='Weight', markers=True)
fig_w.add_hline(y=65.0, line_dash="dash", line_color="red", annotation_text="Goal 65kg")
fig_w.update_traces(line_color='#00FF00', line_width=4)
fig_w.update_layout(height=300)
st.plotly_chart(fig_w, use_container_width=True)

st.divider()

col1, col2 = st.columns([2, 1])

with col1:
    # 2. GLUCOSE GRAPH
    st.subheader("🩸 Glucose Trends (Libre Style)")
    fig_g = go.Figure()
    fig_g.add_hrect(y0=3.9, y1=10.0, fillcolor="green", opacity=0.15, line_width=0)
    fig_g.add_trace(go.Scatter(x=df['Timestamp'], y=df['Glucose'], mode='lines+markers', name='Glucose'))
    fig_g.update_layout(height=350, yaxis_range=[0, 22])
    st.plotly_chart(fig_g, use_container_width=True)

    # 3. MEAL PLANNER
    st.write("### 🍽️ AI Meal Suggestions (No Tuna/Coleslaw)")
    m1, m2, m3 = st.columns(3)
    meal = None
    if m1.button("🍳 Breakfast"): meal = "Breakfast"
    if m2.button("🥪 Lunch"): meal = "Lunch"
    if m3.button("🍲 Dinner"): meal = "Dinner"
    
    if meal:
        rec = gemini_engine(f"Suggest {meal} for weight 65kg goal. Current glucose: {g_in} {trend_in}.")
        st.info(rec)

with col2:
    # 4. CALORIE TALLY
    st.subheader("🔥 Calorie Tally")
    food_in = st.text_input("Add Food Item")
    if st.button("Calculate via AI"):
        res = gemini_engine(food_in, mode="calories")
        match = re.search(r'\d+', res)
        if match:
            val = int(match.group())
            if val < 5000:
                st.session_state.current_kcal += val
                st.success(f"Added {val} kcal!")
                st.write(f"**Gemini Advice:** {gemini_engine(f'Just ate {food_in} at {g_in} {trend_in}. Advice?')}")
            else: st.error("Unrealistic number.")
        else: st.error("AI Error.")

    manual = st.number_input("Manual Calorie Entry", 0, 2000, 0)
    if st.button("Add Manual"):
        st.session_state.current_kcal += manual
        st.success(f"Added {manual} kcal!")

    st.metric("Total Today", f"{st.session_state.current_kcal} kcal")
    st.progress(min(st.session_state.current_kcal / 2400, 1.0))

# --- CHAT BOX ---
st.divider()
user_q = st.text_input("💬 Chat with Growth Partner:")
if user_q:
    st.write(f"**Gemini:** {gemini_engine(f'Weight {w_in}kg, Glucose {g_in}. Question: {user_q}')}")
