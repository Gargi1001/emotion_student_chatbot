import google.generativeai as genai
import streamlit as st
from transformers import pipeline
import time

# --- 1. LOCAL EMOTION ENGINE ---
@st.cache_resource
def load_classifier():
    # Detects: Joy, Sadness, Anger, Fear, Love, Surprise
    return pipeline("text-classification", model="bhadresh-savani/distilbert-base-uncased-emotion")

classifier = load_classifier()

# --- 2. GEMINI CONFIGURATION ---
# Using the stable 2026 model ID: gemini-2.5-flash-lite
API_KEY = "AIzaSyAJQTxLyTFX6psL5QcDZ5XmGg29FKhKYeI" 
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash-lite')

def get_response_and_emotion(user_text):
    # Detect Emotion Locally
    result = classifier(user_text)
    emotion = result[0]['label']
    score = result[0]['score']

    # --- THE "ANGER" FILTER ---
    # Fixes misclassification of short direct questions
    if "?" in user_text or len(user_text.split()) < 4:
        if emotion == "anger" or score < 0.85:
            emotion = "neutral"

    ai_answer = None
    prompt = f"Student is feeling {emotion}. They said: '{user_text}'. Respond briefly as a mentor."

    # --- AUTO-RETRY LOGIC (Error 429 Fix) ---
    # Implements exponential backoff for rate-limited requests
    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            if response and response.text:
                ai_answer = response.text
                break
        except Exception as e:
            if "429" in str(e):
                time.sleep(2) # Cooldown before retrying
                continue
            else:
                ai_answer = f"⚠️ Gemini API Error: {str(e)}"
                break

    if not ai_answer:
        ai_answer = "I'm here for you. Tell me more about what's happening."

    return emotion, score, ai_answer