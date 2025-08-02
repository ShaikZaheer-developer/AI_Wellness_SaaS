import streamlit as st
import firebase_admin
from firebase_admin import credentials, storage
from gtts import gTTS
import json
import os
import time

# -----------------------------
# Initialize Firebase
# -----------------------------
firebase_key_dict = json.loads(st.secrets["FIREBASE_KEY"])

if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_key_dict)
    firebase_admin.initialize_app(cred, {
        'storageBucket': f"{firebase_key_dict['project_id']}.appspot.com"
    })

bucket = storage.bucket()

# -----------------------------
# Streamlit UI
# -----------------------------
st.title("🎵 AI Wellness SaaS - Audio Generator")
st.write("Enter any motivational message, and I’ll generate an audio file for you!")

text_input = st.text_area("Enter your message:", "Believe in yourself, and success will follow!")

if st.button("Generate Audio"):
    if text_input.strip():
        with st.spinner("Generating audio..."):
            # Create audio file
            tts = gTTS(text=text_input, lang='en')
            filename = f"voice_{int(time.time())}.mp3"
            local_path = filename
            tts.save(local_path)

            # Upload to Firebase Storage
            blob = bucket.blob(f"audio/{filename}")
            blob.upload_from_filename(local_path)
            blob.make_public()
            audio_url = blob.public_url

            # Play audio & show link
            st.audio(local_path)
            st.success("✅ Audio generated & uploaded!")
            st.markdown(f"[🔗 Download Your Audio Here]({audio_url})")

            # Clean up local file
            os.remove(local_path)
    else:
        st.warning("Please enter a message first!")
