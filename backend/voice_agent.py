import os
import requests
from config.api_keys import ELEVENLABS_API_KEY

def text_to_speech(text: str, output_path: str = "response.mp3"):
    """Converts text to speech using ElevenLabs."""
    
    CHUNK_SIZE = 1024
    url = "https://api.elevenlabs.io/v1/text-to-speech/pNInz6ovhh85mx4SdID9" # Rachel Voice

    headers = {
      "Accept": "audio/mpeg",
      "Content-Type": "application/json",
      "xi-api-key": ELEVENLABS_API_KEY
    }

    data = {
      "text": text,
      "model_id": "eleven_monolingual_v1",
      "voice_settings": {
        "stability": 0.5,
        "similarity_boost": 0.5
      }
    }

    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
        return output_path
    else:
        print(f"Error in TTS: {response.text}")
        return None

def speech_to_text(audio_path: str):
    """Placeholder for Whisper STT integration."""
    # In a real scenario, we'd use openai.Audio.transcribe
    return "Demo user input from voice."
