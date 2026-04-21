import streamlit as st
import pandas as pd
import sqlite3
import time
from datetime import datetime
from emotion_engine import get_response_and_emotion

# --- 1. DATABASE MANAGEMENT ---
DB_NAME = 'student_wellness_v2026.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Stores the full dialogue for memory persistence
    c.execute('''CREATE TABLE IF NOT EXISTS mood_logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  timestamp TEXT, username TEXT, role TEXT, 
                  content TEXT, emotion TEXT)''')
    conn.commit()
    conn.close()

def save_to_db(user, role, content, emo):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO mood_logs (timestamp, username, role, content, emotion) VALUES (?,?,?,?,?)",
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user, role, content, emo))
    conn.commit()
    conn.close()

def load_full_history(user):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT role, content FROM mood_logs WHERE username = ? ORDER BY timestamp ASC", (user,))
    rows = c.fetchall()
    conn.close()
    return [{"role": row[0], "content": row[1]} for row in rows]

def clear_db_history(user):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM mood_logs WHERE username = ?", (user,))
    conn.commit()
    conn.close()

# --- 2. STREAMLIT INTERFACE ---
st.set_page_config(page_title="Student Wellness AI", page_icon="🌱", layout="wide")
init_db()

if "user_name" not in st.session_state:
    st.session_state.user_name = "Student"

# Initialize memory from SQLite
if "messages" not in st.session_state:
    st.session_state.messages = load_full_history(st.session_state.user_name)

# --- 3. SIDEBAR DASHBOARD ---
with st.sidebar:
    st.title("📊 My Wellbeing")
    name = st.text_input("Username:", value=st.session_state.user_name).strip()
    
    if name != st.session_state.user_name:
        st.session_state.user_name = name
        st.session_state.messages = load_full_history(name)
        st.rerun()

    st.markdown("---")
    if st.button("🗑️ Clear History"):
        clear_db_history(st.session_state.user_name)
        st.session_state.messages = []
        st.success("History Reset!")
        time.sleep(1)
        st.rerun()

# --- 4. CHAT WINDOW ---
st.title(f"🌱 Hello, {st.session_state.user_name}!")
chat_col, stats_col = st.columns([3, 1])

with chat_col:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

if prompt := st.chat_input("Tell your mentor how you are feeling..."):
    # Save User Interaction
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_to_db(st.session_state.user_name, "user", prompt, "N/A")
    with chat_col:
        with st.chat_message("user"): st.markdown(prompt)

    # Trigger AI Brain
    with st.spinner("Analyzing Vibe..."):
        emotion, score, ai_response = get_response_and_emotion(prompt)
    
    # Save AI Mentor Response
    mood_label = emotion.upper()
    full_txt = f"**[Vibe: {mood_label}]**\n\n{ai_response}"
    st.session_state.messages.append({"role": "assistant", "content": full_txt})
    save_to_db(st.session_state.user_name, "assistant", full_txt, emotion)
    
    with chat_col:
        with st.chat_message("assistant"): st.markdown(full_txt)
    
    with stats_col:
        st.metric("Detected Emotion", mood_label)
    
    st.rerun()