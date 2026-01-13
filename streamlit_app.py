import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
import re
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="65kg Growth Portal", layout="wide")

# --- API KEY (Sidebar) ---
API_KEY = st.sidebar.text_input("Gemini API Key", type="password")

# --- DATA INITIALIZATION ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame([
        {"Timestamp": "2026-01-12 08:30", "Weight": 55.0, "Kcal": 3217, "Glucose": 10.2},
        {"Timestamp": "2026-01-13 09:30", "Weight": 55.2, "Kcal": 2560, "Glucose": 13.6}
    ])
if 'current_kcal' not in st.session_state:
    st.session_state.current_kcal = 0

# --- GEMINI ENGINE (Updated to fix 404) ---
def gemini_engine(prompt, mode="chat"):
    if not API_KEY: return "Enter API Key"
    try:
        genai.configure(api_key=API_KEY)
        # Using the standard gemini-1.5-flash model string
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        if mode == "calories":
            full_prompt = f"Provide ONLY the numeric integer calorie count for: {prompt}. No units, no text."
        else:
            full_prompt = prompt
            
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"AI Error: {str(e)}"

# --- SIDEBAR: LOGGING ---
st.sidebar.header("📝 Real-Time Entry")
w_in = st.sidebar.number_input("Weight (kg)", 40.0, 80.0, 55.2, 0.1)
g_in = st.sidebar.number_input("Glucose (mmol/L)", 2.0, 25.0, 13.6, 0.1)

if st.sidebar.button("💾 SAVE DATA NOW"):
    # FIX: This captures the exact current time
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_row = pd.DataFrame([{"Timestamp": now, "Weight": w_in, "Kcal": st.session_state.current_kcal, "Glucose": g_in}])
    st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True)
    st.sidebar.success(f"Saved at {now}!")

# --- MAIN DASHBOARD ---
st.title("🚀 My 65kg Growth Portal")
df = st.session_state.history
df['Timestamp'] = pd.to_datetime(df['Timestamp'])

col1, col2 = st.columns([2, 1])

with col1:
    # --- WEIGHT GRAPH ---
    st.subheader("Weight Progress (Goal: 65kg)")
    fig_w = px.line(df, x='Timestamp', y='Weight', markers=True)
    fig_w.add_hline(y=65.0, line_dash="dash", line_color="red")
    fig_w.update_traces(line_color='#00FF00')
    st.plotly_chart(fig_w, width="stretch")

    # --- GLUCOSE RANGE GRAPH (Libre Style) ---
    st.subheader("Glucose Range (mmol/L)")
    fig_g = go.Figure()
    # Green Zone (3.9 to 10.0 mmol/L)
    fig_g.add_hrect(y0=3.9, y1=10.0, fillcolor="green", opacity=0.15, line_width=0, annotation_text="Target Range")
    fig_g.add_trace(go.Scatter(x=df['Timestamp'], y=df['Glucose'], mode='lines+markers', name='Glucose', line=dict(color='blue')))
    fig_g.update_layout(yaxis_range=[0, 22])
    st.plotly_chart(fig_g, width="stretch")

with col2:
    st.subheader("Food & Calorie Tally")
    food_in = st.text_input("Add food")
    if st.button("Add & Calculate"):
        res = gemini_engine(food_in, mode="calories")
        # FIX: Extract only the FIRST number found to stop the 400,000 kcal bug
        match = re.search(r'\d+', res)
        if match:
            val = int(match.group())
            if val < 5000: # Safety cap
                st.session_state.current_kcal += val
                st.success(f"Added {val} kcal!")
            else:
                st.error("AI returned an unrealistic number.")
        else:
            st.error("AI failed to calculate. Enter manually.")

    st.metric("Today's Total", f"{st.session_state.current_kcal} kcal")
    st.progress(min(st.session_state.current_kcal / 2400, 1.0))

# --- CHAT BOX ---
st.divider()
st.subheader("💬 Growth Partner Chat")
user_q = st.text_input("Ask me about Creon or your 65kg goal:")
if user_q:
    context = f"User is {w_in}kg. Glucose {g_in} mmol/L. Total kcal today: {st.session_state.current_kcal}."
    answer = gemini_engine(context + " Question: " + user_q)
    st.write(f"**Gemini:** {answer}")
