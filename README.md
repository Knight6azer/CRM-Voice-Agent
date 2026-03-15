# 🏡 Riverwood AI CRM Voice Agent

![Status](https://img.shields.io/badge/Status-Enhanced-brightgreen)
![Tech](https://img.shields.io/badge/Tech-FastAPI%20%7C%20Streamlit%20%7C%20OpenAI-blue)
![License](https://img.shields.io/badge/License-MIT-orange)

An industry-standard, scalable AI-powered voice assistant designed for the prestigious **Riverwood Estate**. This agent provides personalized construction updates, handles bilingual (Hindi/English) conversations with a premium persona, and is architected to scale to thousands of concurrent calls.

## ✨ Key Features
- **Premium AI Persona**: Sophisticated relationship manager personality using GPT-4o-mini.
- **Bilingual Conversations**: Seamlessly switches between Hindi and English greetings and updates.
- **High-Fidelity Voice**: Natural-sounding TTS via ElevenLabs.
- **Advanced STT**: High-accuracy speech-to-text integration via OpenAI Whisper.
- **Interactive Dashboard**: Modern, vibrant Streamlit UI with real-time analytics and live demo.
- **Scalable Architecture**: Designed for deployment with Kubernetes, Redis, and Twilio.

## 🛠 Tech Stack
- **AI Core**: OpenAI GPT-4o-mini & Whisper (STT)
- **Memory**: LangChain `ConversationBufferMemory`
- **Voice Synthesis**: ElevenLabs (Rachel Voice)
- **Backend**: FastAPI (Python 3.9+)
- **Frontend**: Streamlit (Vibrant UI with Custom CSS & Plotly)
- **Telephony**: Twilio Voice API

## 📂 Project Structure
```text
├── backend/          # Core AI logic, STT/TTS integration, and FastAPI server
├── frontend/         # Vibrant Streamlit dashboard for monitoring and simulation
├── config/           # Centralized API key and configuration management
├── tests/            # Automated test suite (in progress)
└── requirements.txt  # Production dependencies
```

## 🚀 Quick Start

1.  **Clone & Install**:
    ```bash
    git clone <repo-url>
    cd Riverwood-AI-CRM-VA
    pip install -r requirements.txt
    ```

2.  **Environment Setup**:
    Create a `.env` file from the example:
    ```bash
    cp .env.example .env
    # Add your OpenAI, ElevenLabs, and Twilio keys
    ```

3.  **Run Backend (API)**:
    ```bash
    python -m backend.main
    ```

4.  **Run Dashboard (UI)**:
    ```bash
    streamlit run frontend/streamlit_app.py
    ```

## 📈 Scalability Roadmap
To handle high-volume morning campaigns (1000+ calls):
1.  **Load Balancing**: Use Nginx or AWS ALB to distribute traffic.
2.  **Async Task Queue**: Implement Redis with Celery to dispatch calls and handle retries.
3.  **Horizontal Scaling**: Deploy FastAPI workers as pods in a Kubernetes cluster.
4.  **Concurrency**: Twilio's API handles the telephony layer's high concurrency limits.

---
*Built with ❤️ for Riverwood Estate.*
