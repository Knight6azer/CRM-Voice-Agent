import streamlit as st
import requests
import json
import os

st.set_page_config(page_title="Riverwood AI Dashboard", layout="wide")

st.title("🏡 Riverwood AI CRM Voice Agent")
st.markdown("### Scalable AI Voice Assistant for Construction Updates")

# Sidebar for configuration
with st.sidebar:
    st.header("Campaign Settings")
    st.info("Status: Sector A - Road development stage")
    st.slider("Call Concurrency", 1, 1000, 10)
    if st.button("Trigger Morning Campaign (1000 calls)"):
        st.success("Campaign Scheduled! Workers scaling up...")

# Main interaction area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("Live Conversation Demo")
    user_text = st.text_input("Simulate Customer Voice/Text:", "Namaste! What's the update for Sector A?")
    
    if st.button("Send to AI"):
        with st.spinner("AI is thinking and generating voice..."):
            try:
                response = requests.post("http://localhost:8000/chat", json={"user_input": user_text})
                data = response.json()
                
                st.chat_message("assistant").write(data["response"])
                
                if data["audio_url"] and os.path.exists(data["audio_url"]):
                    st.audio(data["audio_url"])
                else:
                    st.warning("Audio generation needs ElevenLabs API Key.")
            except Exception as e:
                st.error(f"Error connecting to backend: {e}")

with col2:
    st.header("Scalability Architecture")
    st.code("""
Load Balancer -> API Gateway
             -> Redis Queue
             -> FastAPI Workers (K8s)
             -> Twilio / ElevenLabs
    """, language="text")
    
    st.metric("Estimated Cost per 1000 calls", "$55.00")
    st.metric("Avg Latency", "1.2s")

# Recent Call Logs
st.header("Recent Call Logs")
logs = [
    {"Time": "09:00 AM", "Customer": "Mr. Sharma", "Status": "Completed", "Outcome": "Visit scheduled for Sunday"},
    {"Time": "09:05 AM", "Customer": "Ms. Gupta", "Status": "No Answer", "Outcome": "Retry scheduled"},
    {"Time": "09:10 AM", "Customer": "Mr. Verma", "Status": "Completed", "Outcome": "Question about possession date"},
]
st.table(logs)
