import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from gtts import gTTS
import json
import os
import time

# -------------------------------
# 1️⃣ Initialize Firebase
# -------------------------------
firebase_key = json.loads(st.secrets["FIREBASE_KEY"])
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_key)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# -------------------------------
# 2️⃣ Streamlit App UI
# -------------------------------
st.title("🌟 AI Wellness SaaS - Audio Motivation App")

st.write("Welcome! This app generates motivational audio messages and stores user info in Firebase.")

name = st.text_input("Enter your name")
email = st.text_input("Enter your email")
message = st.text_area("Enter a motivational message to convert to audio")

if st.button("Generate & Send Audio"):
    if name and email and message:
        # -------------------------------
        # 3️⃣ Save user info to Firebase
        # -------------------------------
        user_data = {
            "name": name,
            "email": email,
            "message": message,
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        db.collection("users").add(user_data)

        # -------------------------------
        # 4️⃣ Generate TTS Audio
        # -------------------------------
        audio_filename = f"voice_{int(time.time())}.mp3"
        tts = gTTS(text=message, lang='en')
        tts.save(audio_filename)

        st.audio(audio_filename, format="audio/mp3")
        st.success("Audio generated successfully! 🎵")

        # -------------------------------
        # 5️⃣ Send Email Notification
        # -------------------------------
        try:
            smtp_email = st.secrets["SMTP_EMAIL"]
            smtp_pass = st.secrets["SMTP_PASSWORD"]

            msg = MIMEMultipart()
            msg['From'] = smtp_email
            msg['To'] = email
            msg['Subject'] = "Your Motivational Audio from AI Wellness SaaS"
            body = f"Hi {name},\n\nHere is your motivational message:\n\n{message}\n\nStay Positive! 🌟"
            msg.attach(MIMEText(body, 'plain'))

            # Send via Gmail SMTP
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(smtp_email, smtp_pass)
            server.send_message(msg)
            server.quit()

            st.success("Email sent successfully! 📧")
        except Exception as e:
            st.error(f"Failed to send email: {e}")

        # Clean up local audio file
        os.remove(audio_filename)

    else:
        st.error("⚠️ Please fill all fields before generating audio.")
