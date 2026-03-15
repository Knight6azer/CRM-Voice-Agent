import streamlit as st
import requests
import json
import os
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Riverwood AI Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Look
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f8fafc;
    }
    
    .main-header {
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    
    .stat-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 1rem;
        padding: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: transform 0.3s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-5px);
        border-color: #3b82f6;
    }
    
    .chat-bubble {
        padding: 1rem;
        border-radius: 1rem;
        margin-bottom: 1rem;
    }
    
    .assistant-bubble {
        background: rgba(59, 130, 246, 0.1);
        border-left: 4px solid #3b82f6;
    }
    
    .user-bubble {
        background: rgba(139, 92, 246, 0.1);
        border-right: 4px solid #8b5cf6;
        text-align: right;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">Riverwood AI CRM</h1>', unsafe_allow_html=True)
st.markdown("#### The Future of Real Estate Customer Engagement")

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/isometric/512/real-estate.png", width=100)
    st.header("Campaign Control")
    st.info("🎯 **Current Focus:** Sector A Road Development Update")
    
    concurrency = st.slider("Worker Concurrency", 1, 1000, 50)
    
    if st.button("🚀 Launch Morning Campaign", use_container_width=True):
        st.balloons()
        st.success(f"Dispatched 1000 calls across {concurrency} workers!")

# Main Layout
col1, col2 = st.columns([1.5, 1])

with col1:
    st.subheader("🤖 Live Demo Interaction")
    
    with st.container():
        user_text = st.text_input("Simulate Customer Speech:", placeholder="e.g., Namaste! How is the work going at Sector A?")
        
        if st.button("Synthesize & Reply", type="primary"):
            with st.status("AI Agent processing...", expanded=True) as status:
                try:
                    st.write("Generating strategic response...")
                    response = requests.post("http://localhost:8000/chat", json={"user_input": user_text})
                    data = response.json()
                    
                    st.write("Converting to high-fidelity voice...")
                    status.update(label="Response specialized!", state="complete", expanded=False)
                    
                    st.markdown(f"""
                    <div class="chat-bubble assistant-bubble">
                        <strong>Riverwood Assistant:</strong><br>{data["response"]}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if data["audio_url"] and os.path.exists(data["audio_url"]):
                        st.audio(data["audio_url"])
                except Exception as e:
                    st.error(f"Backend offline or API issue: {e}")

with col2:
    st.subheader("📊 Performance Analytics")
    
    # Mock data for chart
    df = pd.DataFrame({
        'Hour': ['08:00', '09:00', '10:00', '11:00'],
        'Success': [120, 250, 480, 550],
        'Retries': [10, 25, 15, 30]
    })
    fig = px.line(df, x='Hour', y=['Success', 'Retries'], 
                 template='plotly_dark',
                 color_discrete_sequence=['#3b82f6', '#ef4444'])
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Calls Made", "1.2k", "+12%")
    with c2:
        st.metric("Site Visits", "42", "+5%")

# Recent Logs Table
st.subheader("📝 Activity Stream")
logs_df = pd.DataFrame([
    {"Time": "09:40 AM", "Customer": "Amit Shah", "Status": "✅ Completed", "Summary": "Interested in Sunday visit"},
    {"Time": "09:35 AM", "Customer": "Priya Rai", "Status": "⏳ No Answer", "Summary": "Scheduled for 2PM retry"},
    {"Time": "09:30 AM", "Customer": "Rajesh K.", "Status": "✅ Completed", "Summary": "Asked about club house ETA"},
])
st.table(logs_df)
