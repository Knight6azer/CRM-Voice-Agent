from fastapi import FastAPI, Request
from pydantic import BaseModel
from backend.llm import generate_llm_response
from backend.voice_agent import text_to_speech
import os

app = FastAPI(title="Riverwood AI Voice Agent")

class CallPayload(BaseModel):
    user_input: str
    session_id: str = "default"

@app.get("/")
async def root():
    return {"status": "Riverwood AI Server Online"}

@app.post("/chat")
async def chat(payload: CallPayload):
    """Main endpoint for handling voice-to-text input and returning AI text/audio."""
    
    # 1. Generate AI Response
    response_text = generate_llm_response(payload.user_input)
    
    # 2. Convert to Speech (Optional playback for demo)
    audio_file = text_to_speech(response_text)
    
    return {
        "response": response_text,
        "audio_url": audio_file,
        "session_id": payload.session_id
    }

@app.post("/twilio/voice")
async def twilio_voice(request: Request):
    """Endpoint for Twilio to fetch TwiML for the call."""
    from twilio.twiml.voice_response import VoiceResponse
    
    vr = VoiceResponse()
    vr.say("Namaste! Hello! This is the Riverwood AI Assistant. How can I help you today?", voice='alice')
    # Twilio would then stream audio to a websocket or record and send to /chat
    return str(vr)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
