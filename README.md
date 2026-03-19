# Riverwood AI CRM Voice Agent

Riverwood now ships as a more complete voice-agent app instead of a one-off CLI demo. The project supports:

- Interactive CLI chat with text or audio input
- OpenAI transcription and conversation handling
- ElevenLabs voice generation for spoken replies
- FastAPI webhook endpoints for Twilio phone calls
- Conversation and callback logging for lightweight CRM follow-up

## Project Structure

```text
|-- cli_agent.py
|-- requirements.txt
|-- .env.example
|-- generated_audio/
`-- logs/
```

## Environment Setup

Copy `.env.example` to `.env` and fill in real credentials.

Important:
- `TWILIO_PHONE_NUMBER` should be in E.164 format, for example `+15551234567`
- `TWILIO_WEBHOOK_BASE_URL` must be a public HTTPS URL that Twilio can reach, such as an ngrok or deployed server URL
- If `ELEVENLABS_API_KEY` is missing, the app still works, but phone mode falls back to Twilio `<Say>`

## Install

```bash
pip install -r requirements.txt
```

## Run the CLI Agent

```bash
python cli_agent.py cli
```

Useful CLI commands:
- Type any message to chat
- Type `voice: path/to/file.wav` to transcribe an audio file and answer it
- Type `exit` to leave

## Transcribe a File

```bash
python cli_agent.py transcribe sample.wav
```

## Generate Speech

```bash
python cli_agent.py speak "Namaste, your Riverwood update is ready."
```

## Run the Phone Webhook Server

```bash
python cli_agent.py server --host 0.0.0.0 --port 8000
```

Configure your Twilio voice webhook to point to:

```text
https://your-domain.com/voice/incoming
```

Available endpoints:
- `GET /health`
- `POST /voice/incoming`
- `POST /voice/respond`

## Start an Outbound Phone Call

Run the server on a public URL first, then start the outbound call:

```bash
python cli_agent.py call --to +15551234567
```

Twilio will place the call from `TWILIO_PHONE_NUMBER` and hand the conversation to the voice-agent webhook at `TWILIO_WEBHOOK_BASE_URL/voice/incoming`.

## Run the Test Suite

```bash
python -m unittest discover -s tests
```

## CRM Logs

The app writes lightweight JSONL logs to:
- `logs/transcripts.jsonl`
- `logs/callbacks.jsonl`

These help capture call context and potential sales follow-up without needing a full CRM backend.
