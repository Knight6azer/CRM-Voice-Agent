import os
import requests
from dotenv import load_dotenv
from openai import OpenAI

# --- Configuration & API Keys ---
load_dotenv()

# Required for core functionality
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Additional integration keys
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
VAPI_API_KEY = os.getenv("VAPI_API_KEY")

def check_keys():
    """Diagnostic to check which API keys are loaded."""
    keys = {
        "OpenAI": OPENAI_API_KEY,
        "ElevenLabs": ELEVENLABS_API_KEY,
        "Twilio": TWILIO_ACCOUNT_SID,
        "Apollo": APOLLO_API_KEY,
        "Vapi": VAPI_API_KEY
    }
    loaded = [name for name, val in keys.items() if val and "your_" not in val.lower()]
    missing = [name for name, val in keys.items() if not val or "your_" in val.lower()]
    return loaded, missing

# Initializing OpenAI Client
client = OpenAI(api_key=OPENAI_API_KEY)

# LLM Engine (Persona & Manual Memory)
# We use a simple list to store conversation history for better compatibility
conversation_history = []

SYSTEM_PROMPT = """
You are the Riverwood AI Assistant, a warm, professional, and sophisticated representative for Riverwood Estate.
Your persona is that of a knowledgeable relationship manager who truly cares about the client's investment.

Objectives:
1. Greet the customer warmly in a bilingual manner (Hindi/English). Example: "Namaste! Hello! I hope you're having a wonderful day."
2. Provide a detailed, enthusiastic update on development progress based on the context.
3. Be proactive: Mention specific milestones (e.g., "Roads are almost done in Sector A!").
4. If they have a question about something you don't know (like specific pricing or legal details), gracefully offer to have their dedicated Relationship Manager call them back within 2 hours.
5. Keep the tone premium: Use words like "prestigious," "milestone," "future-ready," and "excellence."
6. Ensure responses are optimized for voice: Concise, clear, and natural pauses.

Context for Today:
- Sector A: Road works are 75% complete. High-quality bituminous layering is in progress.
- Sector B: Landscaping and club house foundation work has started.
- General: The estate is looking more beautiful every day.
"""

def generate_llm_response(user_input):
    """Generates a response using GPT-4o-mini with enhanced persona and manual memory."""
    global conversation_history

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    # Add conversation history
    for entry in conversation_history[-10:]: # Keep last 10 exchanges
        messages.append({"role": "user", "content": entry["input"]})
        messages.append({"role": "assistant", "content": entry["output"]})

    messages.append({"role": "user", "content": user_input})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.6,
            max_tokens=250
        )

        content = response.choices[0].message.content

        # Update history
        conversation_history.append({"input": user_input, "output": content})

        return content
    except Exception as e:
        print(f"Error in LLM Generation: {e}")
        return "I apologize, but I'm having a bit of trouble connecting to my system. Could I have your Relationship Manager call you back shortly?"

# Voice Engine (TTS & STT)

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

    try:
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
    except Exception as e:
        print(f"TTS Exception: {e}")
        return None

def speech_to_text(audio_path: str):
    """Converts speech to text using OpenAI Whisper."""
    if not os.path.exists(audio_path):
        print(f"Audio file not found: {audio_path}")
        return None
        
    try:
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
        return transcript.text
    except Exception as e:
        print(f"Error in STT: {e}")
        return "Sorry, I couldn't hear that clearly. Could you please repeat?"

# Playback Utility 

def play_audio(file_path):
    """Attempts to play audio on Windows."""
    if os.path.exists(file_path):
        print(f"Playing response: {file_path}")
        # Using 'start' to open the default media player on Windows
        os.system(f"start {file_path}")
    else:
        print("Audio file not found for playback.")

# CLI Interface 

def main():
    loaded, missing = check_keys()
    
    os.system('cls' if os.name == 'nt' else 'clear')
    print("="*60)
    print("      *** RIVERWOOD ESTATE AI VOICE ASSISTANT ***      ")
    print("="*60)
    print(f" Status: CLI Mode Active | Keys Loaded: {len(loaded)}/{len(loaded) + len(missing)}")
    print(f" System: GPT-4o-mini | ElevenLabs (Rachel)")
    
    if missing:
        print(f" Warning: Missing keys ({', '.join(missing)})")
    
    print("="*60)
    print("\n[Commands]")
    print(" - Type your message to chat.")
    print(" - Type 'voice: <path>' to process an audio file.")
    print(" - Type 'exit' or 'quit' to end the session.")
    print("-" * 60)

    # Initial Greet
    initial_text = "Namaste! Hello! I am your Riverwood AI Assistant. How can I help you with your property at Riverwood Estate today?"
    print(f"\nAgent: {initial_text}")

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except EOFError:
            break

        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("\nAgent: Namaste! It was a pleasure assisting you. Have a wonderful day!")
            break

        if not user_input:
            continue

        # Check for voice input command
        if user_input.lower().startswith("voice:"):
            audio_path = user_input[6:].strip()
            if not os.path.exists(audio_path):
                print(f"[!] Error: Audio file not found at '{audio_path}'")
                continue
                
            print(f"[*] Processing audio from: {audio_path}...")
            transcribed_text = speech_to_text(audio_path)
            
            if transcribed_text:
                print(f"[#] Transcribed: \"{transcribed_text}\"")
                user_input = transcribed_text
            else:
                print("[!] Failed to transcribe audio. Please check your OpenAI API quota.")
                continue

        # Generate Response
        print("[*] Thinking...")
        response_text = generate_llm_response(user_input)
        
        if "insufficient_quota" in response_text or "Error in LLM" in response_text:
             print("\n[!] OpenAI API Error: Please check your quota or billing at https://platform.openai.com/usage")
        
        print(f"\nAgent: {response_text}")

        # Convert to Speech and Play
        print("[*] Generating voice...")
        audio_file = text_to_speech(response_text)
        if audio_file:
            play_audio(audio_file)
        else:
            print("[!] Voice generation failed. Please check your ElevenLabs API key and Voice ID.")


if __name__ == "__main__":
    main()
