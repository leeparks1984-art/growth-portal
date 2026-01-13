import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
import re
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="65kg Growth Portal", layout="wide")
USER_DISLIKES = "Tuna and Coleslaw"

# --- API KEY (HARDCODED) ---
# ⚠️ SECURITY NOTE: Keep your GitHub Repo PRIVATE to protect this key.
API_KEY = "AIzaSyAxknnmKqG90os-bsX68x5zebfoYYA2H4M"

# --- BULLETPROOF AI ENGINE ---
def gemini_engine(prompt, mode="chat"):
    # Dual-Engine: Tries Flash first, then Pro if Flash fails
    # This loop prevents the "404 Model Not Found" crash
    models_to_try = ['gemini-1.5-flash', 'gemini-pro']
    
    try:
        genai.configure(api_key=API_KEY)
        
        system_rules = f"You are a Clinical Growth Assistant. Goal: 65kg. User HATES {USER_DISLIKES}. Never suggest them."
        
        if mode == "calories":
            full_prompt = f"Return ONLY the numeric integer calorie count for: {prompt}. No text."
        else:
            full_prompt = f"{system_rules} Context: {prompt}"

        # Loop through models until one works
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(full_prompt)
                return response.text
            except Exception:
                continue # If model fails, try the next one
        
        return "⚠️ AI Connection Failed. Please update requirements.txt."
        
    except Exception as e:
        return f"⚠️ System Error: {str(e)}"

# --- SESSION MEMORY ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame([
        {"Timestamp": "2026-01-12 08:30", "Weight": 55.0, "Kcal": 3217, "Glucose": 10.2, "Trend": "→", "Notes": "Start"},
        {"Timestamp": "2026-01-13 09:30", "Weight": 55.2, "Kcal": 2560, "Glucose": 13.6, "Trend": "↑", "Notes": "Work shift"}
    ])
if 'current_kcal' not in st.session_state:
    st.session_state.current_kcal = 0

# --- SIDEBAR: ENTRY ---
st.sidebar.header("📝 Real-Time Entry")
w_in = st.sidebar.number_input("Weight (kg)", 40.0, 80.0, 55.2, 0.1)
g_in = st.sidebar.number_input("Glucose (mmol/L)", 2.0, 25.0, 13.6, 0.1)
trend_in = st.sidebar.selectbox("Trend Arrow", ["→ (Stable)", "↑ (Rising)", "↗ (Slow Rise)", "↓ (Falling)", "↘ (Slow Fall)"])
note_in = st.sidebar.text_input("Notes (e.g. '7 Creon')")

if st.sidebar.button("💾 SAVE DATA NOW"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_row = pd.DataFrame([{
        "Timestamp": now, "Weight": w_in, "Kcal": st.session_state.current_kcal, 
        "Glucose": g_in, "Trend": trend_in, "Notes": note_in
    }])
    st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True)
    st.sidebar.success(f"Saved entry at {now}!")

# --- MAIN DASHBOARD ---
st.title("🚀 My 65kg Growth Portal")
df = st.session_state.history
df['Timestamp'] = pd.to_datetime(df['Timestamp'])

# 1. WEIGHT TRACKER
st.subheader("⚖️ Weight Journey to 65kg")
fig_w = px.line(df, x='Timestamp', y='Weight', markers=True)
fig_w.add_hline(y=65.0, line_dash="dash", line_color="red", annotation_text="Goal 65kg")
fig_w.update_traces(line_color='#00FF00', line_width=4)
fig_w.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig_w, use_container_width=True)

st.divider()

col1, col2 = st.columns([2, 1])

with col1:
    # 2. GLUCOSE TRACKER
    st.subheader("🩸 Glucose Trends")
    fig_g = go.Figure()
    fig_g.add_hrect(y0=3.9, y1=10.0, fillcolor="green", opacity=0.15, line_width=0, annotation_text="Target")
    fig_g.add_trace(go.Scatter(x=df['Timestamp'], y=df['Glucose'], mode='lines+markers', name='Glucose'))
    fig_g.update_layout(height=350, yaxis_range=[0, 22], margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_g, use_container_width=True)

    # 3. MEAL PLANNER
    st.write("### 🍽️ AI Meal Suggestions (No Tuna/Coleslaw)")
    m1, m2, m3 = st.columns(3)
    if m1.button("🍳 Breakfast"): 
        st.info(gemini_engine(f"Suggest Breakfast. Weight {w_in}kg. Glucose {g_in} {trend_in}."))
    if m2.button("🥪 Lunch"): 
        st.info(gemini_engine(f"Suggest Lunch. Weight {w_in}kg. Glucose {g_in} {trend_in}."))
    if m3.button("🍲 Dinner"): 
        st.info(gemini_engine(f"Suggest Dinner. Weight {w_in}kg. Glucose {g_in} {trend_in}."))

with col2:
    # 4. CALORIE TALLY
    st.subheader("🔥 Calorie Tally")
    food_item = st.text_input("Add Food (AI Calc)")
    if st.button("Add via AI"):
        res = gemini_engine(food_item, mode="calories")
        match = re.search(r'\d+', res)
        if match:
            val = int(match.group())
            if val < 5000:
                st.session_state.current_kcal += val
                st.success(f"Added {val} kcal!")
            else: st.error("AI returned unrealistic number.")
        else: 
            st.error("AI Busy. Please enter manually.")

    manual_k = st.number_input("Manual Calorie Entry", 0, 2000, 0)
    if st.button("Add Manual"):
        st.session_state.current_kcal += manual_k
        st.success(f"Added {manual_k} kcal!")

    st.metric("Today's Total", f"{st.session_state.current_kcal} kcal")
    st.progress(min(st.session_state.current_kcal / 2400, 1.0))

# --- 5. CHAT BOX ---
st.divider()
st.subheader("💬 Chat with Growth Partner")
st.write("Ask about Creon, Sugars, or your progress:")
user_chat = st.text_input("Type your question here...")
if user_chat:
    context = f"User stats: Weight {w_in}kg, Glucose {g_in} ({trend_in}), Today's Calories {st.session_state.current_kcal}."
    response = gemini_engine(f"{context} User Question: {user_chat}")
    st.markdown(f"**Gemini:** {response}")

# --- 6. HISTORY LOG ---
st.divider()
st.write("### 📓 History & Notes")
st.dataframe(df.tail(5), use_container_width=True)
