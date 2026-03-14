# Riverwood AI CRM Voice Agent

## Overview
A scalable AI-powered voice assistant designed for real estate customer relationship management. The agent provides personalized construction updates, handles bilingual conversations (Hindi/English), and scales to thousands of calls.

## Tech Stack
- **AI Reasoning**: OpenAI GPT-4o-mini
- **Memory**: LangChain `ConversationBufferMemory`
- **Voice**: ElevenLabs (Natural TTS)
- **Framework**: FastAPI (Backend) & Streamlit (Demo Dashboard)
- **Calling**: Twilio Voice API

## Directory Structure
- `backend/`: Core AI logic and FastAPI server.
- `frontend/`: Streamlit dashboard for monitoring and demos.
- `config/`: Configuration and API key management.

## Setup Instructions
1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Configure API Keys**:
   Create a `.env` file based on `.env.example` and add your keys for OpenAI, ElevenLabs, and Twilio.
3. **Run the Backend**:
   ```bash
   python -m backend.main
   ```
4. **Run the Dashboard**:
   ```bash
   streamlit run frontend/streamlit_app.py
   ```

## Scalability Answer
To handle 1000 calls every morning:
- **Architecture**: Use a Load Balancer with an API Gateway.
- **Queueing**: Implement a Redis/RabbitMQ queue to dispatch calls.
- **Workers**: Deploy FastAPI workers on Kubernetes for horizontal scaling.
- **Provider**: Twilio handles the telephony concurrency.
