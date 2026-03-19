# 🏡 Riverwood AI CRM CLI Voice Agent

![Status](https://img.shields.io/badge/Status-Simplified-brightgreen)
![Tech](https://img.shields.io/badge/Tech-OpenAI%20%7C%20ElevenLabs-blue)
![License](https://img.shields.io/badge/License-MIT-orange)

A streamlined, single-file AI voice assistant for **Riverwood Estate**. This agent handles property updates and bilingual conversations via a simple CLI interface.

## ✨ Key Features
- **Consolidated Core**: All logic (LLM, STT, TTS) is in a single, well-organized file.
- **Premium AI Persona**: Sophisticated relationship manager personality using GPT-4o-mini.
- **Bilingual Support**: Hindi/English greetings and updates.
- **Voice Integration**: ElevenLabs for high-fidelity speech and OpenAI Whisper for transcription.
- **CLI Interface**: Interactive terminal-based chat with command support.

## 📂 Project Structure
```text
├── cli_agent.py      # The main application (Logic + Interface)
├── requirements.txt  # Project dependencies
├── .env              # Your API Keys (Not tracked by Git)
└── .env.example      # Template for environment variables
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
    cat .env.example > .env
    # Add your OPENAI_API_KEY and ELEVENLABS_API_KEY
    ```

3.  **Run the Agent**:
    ```bash
    python cli_agent.py
    ```

## 🛠 Usage
- **Chat**: Simply type your message in the terminal.
- **Voice Input**: Use `voice: <path_to_audio_file>` to process a recording.
- **Exit**: Type `exit` or `quit`.

---
*Built with ❤️ for Riverwood Estate.*
