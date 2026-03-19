from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Deque, Dict, Iterable, Optional

import requests
from dotenv import load_dotenv
from openai import OpenAI

try:
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse, Response
    import uvicorn
except ImportError:  # pragma: no cover - optional runtime dependency
    FastAPI = None
    Request = None
    JSONResponse = None
    Response = None
    uvicorn = None


load_dotenv()


PLACEHOLDER_MARKERS = (
    "your_",
    "replace_me",
    "example",
    "changeme",
    "xxxx",
    "acxxxxxxxx",
)

KNOWLEDGE_BASE = """
You are the Riverwood AI Voice Agent, a warm and premium relationship manager for Riverwood Estate.

Voice and behavior rules:
1. Greet warmly in natural Hindi-English.
2. Keep responses concise, voice-friendly, and polished.
3. Sound confident, calm, and proactive.
4. If the caller asks about pricing, legal matters, payment plans, possession timelines, or anything uncertain,
   offer a callback from a human relationship manager within 2 working hours.
5. If the caller sounds interested in a site visit, collect that intent naturally and encourage a callback.

Riverwood project context:
- Sector A road works are 75 percent complete and bituminous layering is in progress.
- Sector B landscaping and clubhouse foundation work have started.
- The estate is progressing steadily with a focus on premium infrastructure and long-term value.
"""

CALLBACK_KEYWORDS = {
    "price",
    "pricing",
    "cost",
    "payment",
    "emi",
    "loan",
    "registry",
    "legal",
    "possession",
    "visit",
    "site visit",
    "discount",
}


def sanitize_env(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def looks_like_placeholder(value: Optional[str]) -> bool:
    if not value:
        return True
    lowered = value.strip().lower()
    if lowered in {"your_openai_api_key", "your_elevenlabs_api_key", "your_twilio_account_sid"}:
        return True
    return any(marker in lowered for marker in PLACEHOLDER_MARKERS)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AgentConfig:
    openai_api_key: Optional[str]
    elevenlabs_api_key: Optional[str]
    twilio_account_sid: Optional[str]
    twilio_auth_token: Optional[str]
    twilio_phone_number: Optional[str]
    twilio_webhook_base_url: Optional[str]
    apollo_api_key: Optional[str]
    vapi_api_key: Optional[str]
    model: str = "gpt-4o-mini"
    transcription_model: str = "whisper-1"
    elevenlabs_voice_id: str = "pNInz6ovhh85mx4SdID9"
    elevenlabs_model_id: str = "eleven_multilingual_v2"
    output_dir: Path = field(default_factory=lambda: Path("generated_audio"))
    log_dir: Path = field(default_factory=lambda: Path("logs"))

    @classmethod
    def from_env(cls) -> "AgentConfig":
        return cls(
            openai_api_key=sanitize_env(os.getenv("OPENAI_API_KEY")),
            elevenlabs_api_key=sanitize_env(os.getenv("ELEVENLABS_API_KEY")),
            twilio_account_sid=sanitize_env(os.getenv("TWILIO_ACCOUNT_SID")),
            twilio_auth_token=sanitize_env(os.getenv("TWILIO_AUTH_TOKEN")),
            twilio_phone_number=sanitize_env(os.getenv("TWILIO_PHONE_NUMBER")),
            twilio_webhook_base_url=sanitize_env(os.getenv("TWILIO_WEBHOOK_BASE_URL")),
            apollo_api_key=sanitize_env(os.getenv("APOLLO_API_KEY")),
            vapi_api_key=sanitize_env(os.getenv("VAPI_API_KEY")),
            model=sanitize_env(os.getenv("OPENAI_MODEL")) or "gpt-4o-mini",
            transcription_model=sanitize_env(os.getenv("OPENAI_TRANSCRIPTION_MODEL")) or "whisper-1",
            elevenlabs_voice_id=sanitize_env(os.getenv("ELEVENLABS_VOICE_ID")) or "pNInz6ovhh85mx4SdID9",
            elevenlabs_model_id=sanitize_env(os.getenv("ELEVENLABS_MODEL_ID")) or "eleven_multilingual_v2",
        )

    def ensure_directories(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def missing_for_cli(self) -> list[str]:
        missing = []
        if looks_like_placeholder(self.openai_api_key):
            missing.append("OPENAI_API_KEY")
        return missing

    def missing_for_voice_output(self) -> list[str]:
        missing = []
        if looks_like_placeholder(self.elevenlabs_api_key):
            missing.append("ELEVENLABS_API_KEY")
        return missing

    def missing_for_phone_mode(self) -> list[str]:
        return self.missing_for_cli()

    def missing_for_outbound_call(self) -> list[str]:
        missing = []
        if not self.twilio_account_sid:
            missing.append("TWILIO_ACCOUNT_SID")
        if not self.twilio_auth_token:
            missing.append("TWILIO_AUTH_TOKEN")
        if not self.twilio_phone_number:
            missing.append("TWILIO_PHONE_NUMBER")
        if not self.twilio_webhook_base_url:
            missing.append("TWILIO_WEBHOOK_BASE_URL")
        return missing

    def provider_status(self) -> Dict[str, str]:
        return {
            "OpenAI": "ready" if not looks_like_placeholder(self.openai_api_key) else "missing",
            "ElevenLabs": "ready" if not looks_like_placeholder(self.elevenlabs_api_key) else "missing",
            "Twilio": "ready"
            if self.twilio_account_sid and self.twilio_auth_token and self.twilio_phone_number
            else "missing",
            "Twilio Webhook": "ready" if self.twilio_webhook_base_url else "missing",
            "Apollo": "ready" if self.apollo_api_key else "optional",
            "Vapi": "ready" if self.vapi_api_key else "optional",
        }


class ConversationStore:
    def __init__(self, max_turns: int = 10) -> None:
        self.max_turns = max_turns
        self.sessions: Dict[str, Deque[dict]] = defaultdict(lambda: deque(maxlen=max_turns))

    def append(self, session_id: str, user_text: str, agent_text: str) -> None:
        self.sessions[session_id].append({"user": user_text, "assistant": agent_text})

    def as_messages(self, session_id: str) -> list[dict]:
        messages: list[dict] = []
        for turn in self.sessions[session_id]:
            messages.append({"role": "user", "content": turn["user"]})
            messages.append({"role": "assistant", "content": turn["assistant"]})
        return messages


class JsonlLogger:
    def __init__(self, path: Path) -> None:
        self.path = path

    def write(self, payload: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True) + "\n")


class ElevenLabsTTS:
    def __init__(self, config: AgentConfig) -> None:
        self.config = config

    def available(self) -> bool:
        return not looks_like_placeholder(self.config.elevenlabs_api_key)

    def synthesize(self, text: str, output_path: Path) -> Optional[Path]:
        if not self.available():
            return None

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.config.elevenlabs_voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.config.elevenlabs_api_key,
        }
        payload = {
            "text": text,
            "model_id": self.config.elevenlabs_model_id,
            "voice_settings": {"stability": 0.45, "similarity_boost": 0.75},
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60, stream=True)
            response.raise_for_status()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        handle.write(chunk)
            return output_path
        except requests.RequestException as exc:
            print(f"[warn] ElevenLabs synthesis failed: {exc}")
            return None


class OpenAITTS:
    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self._client: Optional[OpenAI] = None

    def available(self) -> bool:
        return not looks_like_placeholder(self.config.openai_api_key)

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            if not self.available():
                raise RuntimeError("OPENAI_API_KEY is missing or still set to a placeholder value.")
            self._client = OpenAI(api_key=self.config.openai_api_key)
        return self._client

    def synthesize(self, text: str, output_path: Path) -> Optional[Path]:
        if not self.available():
            return None

        try:
            response = self.client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="alloy",
                input=text,
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)
            response.stream_to_file(output_path)
            return output_path
        except Exception as exc:
            print(f"[warn] OpenAI speech synthesis failed: {exc}")
            return None


class WindowsSystemTTS:
    def available(self) -> bool:
        return os.name == "nt"

    def synthesize(self, text: str, output_path: Path) -> Optional[Path]:
        if not self.available():
            return None

        output_path.parent.mkdir(parents=True, exist_ok=True)
        escaped_text = text.replace("'", "''")
        escaped_output = str(output_path).replace("'", "''")
        command = (
            "Add-Type -AssemblyName System.Speech; "
            "$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$speaker.SetOutputToWaveFile('{escaped_output}'); "
            f"$speaker.Speak('{escaped_text}'); "
            "$speaker.Dispose();"
        )

        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
            )
            if result.returncode != 0:
                stderr = result.stderr.strip() or "Unknown PowerShell speech error"
                print(f"[warn] Windows speech synthesis failed: {stderr}")
                return None
            return output_path
        except Exception as exc:
            print(f"[warn] Windows speech synthesis failed: {exc}")
            return None


class OpenAIConversationEngine:
    def __init__(self, config: AgentConfig, memory: ConversationStore, transcript_logger: JsonlLogger) -> None:
        self.config = config
        self.memory = memory
        self.transcript_logger = transcript_logger
        self._client: Optional[OpenAI] = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            if looks_like_placeholder(self.config.openai_api_key):
                raise RuntimeError("OPENAI_API_KEY is missing or still set to a placeholder value.")
            self._client = OpenAI(api_key=self.config.openai_api_key)
        return self._client

    def build_system_prompt(self, session_id: str, caller: Optional[str] = None) -> str:
        extra = f"\nCurrent session id: {session_id}."
        if caller:
            extra += f"\nCaller phone number: {caller}."
        extra += (
            "\nIf a callback seems useful, explicitly say a relationship manager can call back within 2 working hours."
        )
        return KNOWLEDGE_BASE.strip() + extra

    def fallback_reply(self, user_text: str) -> str:
        lowered = user_text.lower()
        if any(keyword in lowered for keyword in {"progress", "update", "status", "construction"}):
            return (
                "Namaste. Riverwood Estate is progressing well. Sector A roads are about 75 percent complete "
                "with bituminous layering in progress, and Sector B landscaping plus clubhouse foundation work "
                "have started beautifully."
            )
        if any(keyword in lowered for keyword in {"price", "pricing", "legal", "payment", "visit"}):
            return (
                "Namaste. For pricing, legal guidance, or visit planning, I can arrange a callback from your "
                "Relationship Manager within 2 working hours."
            )
        return (
            "Namaste. Riverwood Estate is progressing steadily, and I can help with project updates, site-visit "
            "interest, or arranging a callback from a Relationship Manager within 2 working hours."
        )

    def generate_reply(self, session_id: str, user_text: str, caller: Optional[str] = None) -> str:
        messages = [{"role": "system", "content": self.build_system_prompt(session_id=session_id, caller=caller)}]
        messages.extend(self.memory.as_messages(session_id))
        messages.append({"role": "user", "content": user_text})

        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=0.55,
                max_tokens=220,
            )
            content = (response.choices[0].message.content or "").strip()
            if not content:
                content = (
                    "Namaste. I am here to help with Riverwood Estate updates. "
                    "Please tell me what you would like to know."
                )
        except Exception as exc:
            print(f"[warn] OpenAI chat failed, using offline fallback: {exc}")
            content = self.fallback_reply(user_text)

        self.memory.append(session_id, user_text, content)
        self.transcript_logger.write(
            {
                "timestamp": now_iso(),
                "session_id": session_id,
                "caller": caller,
                "user": user_text,
                "assistant": content,
            }
        )
        return content

    def transcribe(self, audio_path: Path) -> str:
        with audio_path.open("rb") as audio_file:
            transcript = self.client.audio.transcriptions.create(
                model=self.config.transcription_model,
                file=audio_file,
            )
        return transcript.text.strip()


class RiverwoodVoiceAgent:
    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self.config.ensure_directories()
        self.memory = ConversationStore(max_turns=12)
        self.transcript_logger = JsonlLogger(self.config.log_dir / "transcripts.jsonl")
        self.callback_logger = JsonlLogger(self.config.log_dir / "callbacks.jsonl")
        self.engine = OpenAIConversationEngine(config, self.memory, self.transcript_logger)
        self.primary_tts = ElevenLabsTTS(config)
        self.fallback_tts = OpenAITTS(config)
        self.local_tts = WindowsSystemTTS()

    def should_log_callback(self, user_text: str, reply_text: str) -> bool:
        combined = f"{user_text} {reply_text}".lower()
        return any(keyword in combined for keyword in CALLBACK_KEYWORDS)

    def record_callback(self, session_id: str, caller: Optional[str], user_text: str, reply_text: str) -> None:
        self.callback_logger.write(
            {
                "timestamp": now_iso(),
                "session_id": session_id,
                "caller": caller,
                "source": "voice-agent",
                "reason": user_text,
                "agent_reply": reply_text,
            }
        )

    def answer(self, user_text: str, session_id: str = "cli-session", caller: Optional[str] = None) -> str:
        reply = self.engine.generate_reply(session_id=session_id, user_text=user_text, caller=caller)
        if self.should_log_callback(user_text, reply):
            self.record_callback(session_id=session_id, caller=caller, user_text=user_text, reply_text=reply)
        return reply

    def transcribe_file(self, audio_path: Path) -> str:
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        return self.engine.transcribe(audio_path)

    def speak_to_file(self, text: str) -> Optional[Path]:
        output_mp3 = self.config.output_dir / f"riverwood-{uuid.uuid4().hex}.mp3"

        audio_file = self.primary_tts.synthesize(text=text, output_path=output_mp3)
        if audio_file:
            return audio_file

        audio_file = self.fallback_tts.synthesize(text=text, output_path=output_mp3)
        if audio_file:
            return audio_file

        output_wav = self.config.output_dir / f"riverwood-{uuid.uuid4().hex}.wav"
        return self.local_tts.synthesize(text=text, output_path=output_wav)

    def build_twiml(self, prompt: str, gather_action: str) -> str:
        root = ET.Element("Response")

        say_tag = ET.SubElement(root, "Say", voice="Polly.Aditi-Neural", language="en-IN")
        say_tag.text = prompt

        gather = ET.SubElement(
            root,
            "Gather",
            input="speech",
            action=gather_action,
            method="POST",
            speechTimeout="auto",
            language="en-IN",
        )
        gather_prompt = ET.SubElement(gather, "Say", voice="Polly.Aditi-Neural", language="en-IN")
        gather_prompt.text = "Please go ahead. I am listening."

        fallback = ET.SubElement(root, "Say", voice="Polly.Aditi-Neural", language="en-IN")
        fallback.text = "I did not hear anything, so I will end the call for now. Thank you."
        ET.SubElement(root, "Hangup")
        return ET.tostring(root, encoding="unicode")

    def initial_greeting_twiml(self) -> str:
        return self.build_twiml(
            prompt=(
                "Namaste and hello. You have reached the Riverwood Estate voice desk. "
                "How may I assist you today?"
            ),
            gather_action="/voice/respond",
        )

    def response_twiml(self, user_text: str, session_id: str, caller: Optional[str]) -> str:
        reply = self.answer(user_text=user_text, session_id=session_id, caller=caller)
        return self.build_twiml(prompt=reply, gather_action="/voice/respond")


def normalize_phone_number(raw_value: Optional[str]) -> Optional[str]:
    if not raw_value:
        return None
    return re.sub(r"[^\d+]", "", raw_value)


def start_outbound_call(config: AgentConfig, to_number: str) -> dict:
    missing = config.missing_for_outbound_call()
    if missing:
        raise RuntimeError(f"Outbound call is not ready. Missing: {', '.join(missing)}")

    to_number = normalize_phone_number(to_number)
    from_number = normalize_phone_number(config.twilio_phone_number)
    webhook_base = config.twilio_webhook_base_url.rstrip("/")
    callback_url = f"{webhook_base}/voice/incoming"
    api_url = f"https://api.twilio.com/2010-04-01/Accounts/{config.twilio_account_sid}/Calls.json"

    response = requests.post(
        api_url,
        auth=(config.twilio_account_sid, config.twilio_auth_token),
        data={
            "To": to_number,
            "From": from_number,
            "Url": callback_url,
            "Method": "POST",
        },
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    return {
        "sid": payload.get("sid"),
        "status": payload.get("status"),
        "to": payload.get("to"),
        "from": payload.get("from"),
        "callback_url": callback_url,
    }


def create_fastapi_app(agent: RiverwoodVoiceAgent) -> "FastAPI":
    if FastAPI is None or Response is None or JSONResponse is None:
        raise RuntimeError(
            "FastAPI dependencies are not installed. Run `pip install -r requirements.txt` first."
        )

    app = FastAPI(title="Riverwood Voice Agent", version="2.0.0")

    @app.get("/health")
    async def health() -> JSONResponse:
        return JSONResponse(
            {
                "status": "ok",
                "providers": agent.config.provider_status(),
                "timestamp": now_iso(),
            }
        )

    @app.post("/voice/incoming")
    async def voice_incoming() -> Response:
        return Response(content=agent.initial_greeting_twiml(), media_type="application/xml")

    @app.post("/voice/respond")
    async def voice_respond(request: Request) -> Response:
        form = await request.form()
        speech_result = str(form.get("SpeechResult") or "").strip()
        call_sid = str(form.get("CallSid") or uuid.uuid4().hex)
        caller = normalize_phone_number(str(form.get("Caller") or ""))

        if not speech_result:
            twiml = agent.build_twiml(
                prompt="I could not hear that clearly. Please call again and speak after the beep.",
                gather_action="/voice/respond",
            )
            return Response(content=twiml, media_type="application/xml")

        twiml = agent.response_twiml(user_text=speech_result, session_id=call_sid, caller=caller)
        return Response(content=twiml, media_type="application/xml")

    return app


def open_audio_file(file_path: Path) -> None:
    try:
        if os.name == "nt":
            os.startfile(str(file_path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            os.system(f'open "{file_path}"')
        else:
            os.system(f'xdg-open "{file_path}"')
    except Exception as exc:  # pragma: no cover - OS-specific
        print(f"[warn] Unable to open audio automatically: {exc}")


def print_status_table(status: Dict[str, str]) -> None:
    print("=" * 64)
    print(" Riverwood AI Voice Agent")
    print("=" * 64)
    for name, state in status.items():
        print(f" {name:<16} : {state}")
    print("=" * 64)


def run_cli(agent: RiverwoodVoiceAgent, autoplay: bool = True) -> int:
    print_status_table(agent.config.provider_status())

    missing = agent.config.missing_for_cli()
    if missing:
        print(f"Missing required configuration: {', '.join(missing)}")
        return 1

    print("Type your message, `voice: <path>` to transcribe an audio file, or `exit` to quit.")
    print(
        "\nAgent: Namaste. Hello. I am your Riverwood Estate voice assistant. "
        "How can I help you today?"
    )

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAgent: Thank you for your time. Have a wonderful day.")
            return 0

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit", "bye"}:
            print("\nAgent: Thank you for speaking with Riverwood Estate. Have a wonderful day.")
            return 0

        if user_input.lower().startswith("voice:"):
            audio_path = Path(user_input.split(":", 1)[1].strip()).expanduser()
            try:
                user_input = agent.transcribe_file(audio_path)
                print(f'[transcript] "{user_input}"')
            except Exception as exc:
                print(f"[error] Unable to transcribe audio: {exc}")
                continue

        try:
            reply = agent.answer(user_text=user_input)
        except Exception as exc:
            print(f"[error] Failed to generate a response: {exc}")
            continue

        print(f"\nAgent: {reply}")

        if (
            not agent.primary_tts.available()
            and not agent.fallback_tts.available()
            and not agent.local_tts.available()
        ):
            continue

        audio_file = agent.speak_to_file(reply)
        if not audio_file:
            print("[warn] Voice synthesis failed, so only text was returned.")
            continue

        print(f"[voice] Saved reply to {audio_file}")
        if autoplay:
            open_audio_file(audio_file)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Riverwood AI voice agent")
    subparsers = parser.add_subparsers(dest="command")

    cli_parser = subparsers.add_parser("cli", help="Run the interactive CLI voice assistant")
    cli_parser.add_argument("--no-autoplay", action="store_true", help="Do not auto-open generated audio")

    transcribe_parser = subparsers.add_parser("transcribe", help="Transcribe an audio file")
    transcribe_parser.add_argument("audio_path", help="Path to an audio file")

    speak_parser = subparsers.add_parser("speak", help="Generate spoken audio from text")
    speak_parser.add_argument("text", help="Text to convert into audio")

    server_parser = subparsers.add_parser("server", help="Run the FastAPI phone webhook server")
    server_parser.add_argument("--host", default="0.0.0.0", help="Host to bind")
    server_parser.add_argument("--port", type=int, default=8000, help="Port to bind")

    call_parser = subparsers.add_parser("call", help="Start an outbound Twilio voice call")
    call_parser.add_argument("--to", required=True, help="Destination phone number in E.164 format")

    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if not args.command:
        args = parser.parse_args(["cli"])

    config = AgentConfig.from_env()
    agent = RiverwoodVoiceAgent(config=config)

    if args.command == "cli":
        return run_cli(agent=agent, autoplay=not args.no_autoplay)

    if args.command == "transcribe":
        missing = config.missing_for_cli()
        if missing:
            print(f"Missing required configuration: {', '.join(missing)}")
            return 1
        try:
            print(agent.transcribe_file(Path(args.audio_path).expanduser()))
            return 0
        except Exception as exc:
            print(f"[error] {exc}")
            return 1

    if args.command == "speak":
        missing = config.missing_for_voice_output()
        if missing:
            print(f"Missing required configuration: {', '.join(missing)}")
            return 1
        audio_file = agent.speak_to_file(args.text)
        if not audio_file:
            print("[error] Failed to generate speech")
            return 1
        print(audio_file)
        return 0

    if args.command == "server":
        missing = config.missing_for_phone_mode()
        if missing:
            print(f"Phone mode is not ready. Missing: {', '.join(missing)}")
            return 1
        if uvicorn is None:
            print("FastAPI server dependencies are missing. Run `pip install -r requirements.txt`.")
            return 1
        app = create_fastapi_app(agent)
        uvicorn.run(app, host=args.host, port=args.port)
        return 0

    if args.command == "call":
        try:
            result = start_outbound_call(config=config, to_number=args.to)
        except Exception as exc:
            print(f"[error] Failed to start outbound call: {exc}")
            return 1
        print(json.dumps(result, indent=2))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
