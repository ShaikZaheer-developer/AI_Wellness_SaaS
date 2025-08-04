import streamlit as st
import random
import pandas as pd
from datetime import datetime
from textblob import TextBlob
from gtts import gTTS
import matplotlib.pyplot as plt
import firebase_admin
from firebase_admin import credentials, firestore
from io import BytesIO
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.audio import MIMEAudio
from email.mime.text import MIMEText

# ---------------------------
# 1. Firebase Init
#if not firebase_admin._apps:
    #cred = credentials.Certificate("firebase_key.json")  # Your Firebase Admin SDK Key
    #firebase_admin.initialize_app(cred)
#db = firestore.client()

# ---------------------------
# 2. Email Config (replace with your Gmail + App Password)
SMTP_EMAIL = ""
SMTP_PASSWORD = ""  # 16-char App Password from Google

# ---------------------------
# 3. AI Responses
responses = {
    "positive": ["Keep shining! 🌟", "Life loves your vibe 😎", "Today is your day to win! 🔥"],
    "negative": ["Tough times don't last 💪", "Every storm runs out of rain ☔", "Your comeback is coming 🌈"],
    "neutral": ["Stay curious 🚀", "Neutral minds create ideas 🌈", "A calm mind is power 💡"]
}

# ---------------------------
# 4. Helper Functions

def detect_emotion_ai(user_input):
    polarity = TextBlob(user_input).sentiment.polarity
    if polarity > 0.2: return "positive"
    elif polarity < -0.2: return "negative"
    else: return "neutral"

def log_mood(user_email, emotion, text):
    db.collection("moods").add({
        "email": user_email,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "emotion": emotion,
        "text": text
    })

def fetch_user_moods(user_email):
    docs = db.collection("moods").where("email", "==", user_email).stream()
    data = [{"Time": d.to_dict()["time"], "Emotion": d.to_dict()["emotion"], "Text": d.to_dict()["text"]} for d in docs]
    return pd.DataFrame(data)

def plot_mood_chart(df):
    if df.empty:
        st.warning("No mood data yet!")
        return
    mood_counts = df["Emotion"].value_counts()
    fig, ax = plt.subplots()
    mood_counts.plot(kind='bar', color=['green','red','gray'], ax=ax)
    plt.title("Your Mood Tracker")
    plt.xlabel("Emotions")
    plt.ylabel("Frequency")
    st.pyplot(fig)

def generate_audio_in_memory(text):
    """Generate TTS audio directly in memory"""
    tts = gTTS(text)
    audio_buffer = BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    return audio_buffer

def send_motivational_email(to_email, text_message):
    """Send email with motivational audio attachment + debug logs"""
    try:
        # Generate audio in memory
        tts = gTTS(text_message)
        audio_buffer = BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        audio_data = audio_buffer.read()

        # Compose email
        msg = MIMEMultipart()
        msg['From'] = SMTP_EMAIL
        msg['To'] = to_email
        msg['Subject'] = "Your Daily AI Motivation 💡"
        msg.attach(MIMEText(f"Hello!\n\nYour AI Motivation:\n\n{text_message}", 'plain'))

        # Attach audio as mp3
        audio_part = MIMEAudio(audio_data, _subtype="mp3")
        audio_part.add_header('Content-Disposition', 'attachment', filename="motivation.mp3")
        msg.attach(audio_part)

        print("🔹 Connecting to Gmail SMTP...")
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            print("🔹 Logging in to Gmail...")
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            print("✅ Logged in successfully!")
            server.send_message(msg)
            print(f"✅ Email sent to {to_email}")

        return True

    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False

# ---------------------------
# 5. Streamlit App

st.set_page_config(page_title="AI Wellness SaaS", page_icon="💡", layout="centered")
st.title("💡 AI Wellness SaaS")
st.write("Login with your email to track your mood & get AI voice + email motivation!")

user_email = st.text_input("Enter your email to log in:")

if user_email:
    st.success(f"Welcome, {user_email}!")

    user_input = st.text_input("How are you feeling today?")

    if st.button("Motivate Me"):
        if user_input.strip():
            # Detect emotion
            emotion = detect_emotion_ai(user_input)
            response = random.choice(responses[emotion])
            st.success(f"**AI:** {response}")

            # Log mood to Firebase
            log_mood(user_email, emotion, user_input)

            # Generate and play voice motivation
            audio_buffer = generate_audio_in_memory(response)
            st.audio(audio_buffer, format="audio/mp3")

            # Option to send email
            if st.button("Send Me Email"):
                success = send_motivational_email(user_email, response)
                if success:
                    st.success(f"✅ Motivational email sent to {user_email}")
                else:
                    st.error("❌ Failed to send email. Check console logs for details.")

    if st.button("Show Mood Chart"):
        df = fetch_user_moods(user_email)
        plot_mood_chart(df)
