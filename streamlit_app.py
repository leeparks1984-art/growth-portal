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
        {"Timestamp": "2026-01-12 08:30", "Weight": 55.0, "Kcal": 3217, "Glucose": 10.2, "Trend": "→"}
    ])
if 'current_kcal' not in st.session_state:
    st.session_state.current_kcal = 0

# --- GEMINI "GROWTH BRAIN" ---
def gemini_engine(prompt, mode="chat"):
    if not API_KEY: return "Enter API Key"
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Hard-coding your preferences into every AI request
        system_instruction = (
            "You are a Clinical Growth Assistant for a user aiming for 65kg. "
            "Constraints: User HAS Pancreatic Insufficiency (needs Creon) and Diabetes. "
            "IMPORTANT: User HATES Tuna and Coleslaw. NEVER suggest them. "
        )
        
        if mode == "calories":
            full_prompt = f"Provide ONLY the numeric integer calorie count for: {prompt}. No text."
        else:
            full_prompt = system_instruction + prompt
            
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"AI Error: {str(e)}"

# --- SIDEBAR: LOGGING ---
st.sidebar.header("📝 Real-Time Entry")
w_in = st.sidebar.number_input("Weight (kg)", 40.0, 80.0, 55.2, 0.1)
g_in = st.sidebar.number_input("Glucose (mmol/L)", 2.0, 25.0, 13.6, 0.1)

# FIXED: Added Trend Arrow selection
trend_in = st.sidebar.selectbox("Trend Arrow", ["→ (Stable)", "↑ (Rising)", "↗ (Slow Rise)", "↓ (Falling)", "↘ (Slow Fall)"])

if st.sidebar.button("💾 SAVE DATA NOW"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_row = pd.DataFrame([{"Timestamp": now, "Weight": w_in, "Kcal": st.session_state.current_kcal, "Glucose": g_in, "Trend": trend_in}])
    st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True)
    st.sidebar.success(f"Saved at {now}!")

# --- MAIN DASHBOARD ---
st.title("🚀 My 65kg Growth Portal")
df = st.session_state.history
df['Timestamp'] = pd.to_datetime(df['Timestamp'])

col1, col2 = st.columns([2, 1])

with col1:
    # Graphs
    st.subheader("Growth & Glucose Trends")
    fig_g = go.Figure()
    fig_g.add_hrect(y0=3.9, y1=10.0, fillcolor="green", opacity=0.15, line_width=0, annotation_text="Target")
    fig_g.add_trace(go.Scatter(x=df['Timestamp'], y=df['Glucose'], mode='lines+markers', name='Glucose'))
    fig_g.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig_g, use_container_width=True)

    # NEW: MEAL SUGGESTION BUTTONS
    st.write("### 🍽️ Meal Planner (AI Suggestion)")
    m_col1, m_col2, m_col3 = st.columns(3)
    
    meal_type = None
    if m_col1.button("🍳 Breakfast"): meal_type = "Breakfast"
    if m_col2.button("🥪 Lunch"): meal_type = "Lunch"
    if m_col3.button("🍲 Dinner"): meal_type = "Dinner"
    
    if meal_type:
        context = f"Current Glucose: {g_in} ({trend_in}). Kcal today: {st.session_state.current_kcal}. Goal: 65kg."
        plan = gemini_engine(f"{context} Suggest a high-calorie {meal_type} that fits these sugars. Remember no tuna/coleslaw.")
        st.info(f"**Gemini's {meal_type} Recommendation:**\n\n{plan}")

with col2:
    st.subheader("Calorie Tally")
    food_in = st.text_input("Food Item (for AI calc)")
    if st.button("Add via AI"):
        res = gemini_engine(food_in, mode="calories")
        match = re.search(r'\d+', res)
        if match:
            val = int(match.group())
            if val < 5000:
                st.session_state.current_kcal += val
                st.success(f"Added {val} kcal!")
                # Immediate AI Feedback on the food
                feedback = gemini_engine(f"User just ate {food_in}. Glucose is {g_in} {trend_in}. Is this an ideal time/choice?")
                st.write(f"**Gemini Feedback:** {feedback}")

    # FIXED: Added Manual Calorie Entry
    st.divider()
    manual_kcal = st.number_input("Manual Calorie Entry", 0, 2000, 0)
    if st.button("Add Manual Kcal"):
        st.session_state.current_kcal += manual_kcal
        st.success(f"Added {manual_kcal} kcal!")

    st.metric("Today's Total", f"{st.session_state.current_kcal} kcal")
    st.progress(min(st.session_state.current_kcal / 2400, 1.0))

# --- CHAT BOX ---
st.divider()
user_q = st.text_input("💬 Chat with Growth Partner:")
if user_q:
    context = f"User is {w_in}kg. Glucose {g_in} {trend_in}. Total kcal: {st.session_state.current_kcal}."
    answer = gemini_engine(context + " Question: " + user_q)
    st.write(f"**Gemini:** {answer}")
