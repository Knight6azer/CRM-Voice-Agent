import unittest
from pathlib import Path
from uuid import uuid4

from cli_agent import AgentConfig, RiverwoodVoiceAgent, looks_like_placeholder


class VoiceAgentTests(unittest.TestCase):
    def make_config(self) -> AgentConfig:
        temp_root = Path("tests_runtime") / uuid4().hex
        return AgentConfig(
            openai_api_key="test-openai-key",
            elevenlabs_api_key=None,
            twilio_account_sid="AC123456789",
            twilio_auth_token="test-auth-token",
            twilio_phone_number="+15551234567",
            twilio_webhook_base_url="https://example.ngrok-free.app",
            apollo_api_key=None,
            vapi_api_key=None,
            output_dir=temp_root / "audio",
            log_dir=temp_root / "logs",
        )

    def test_placeholder_detection(self) -> None:
        self.assertTrue(looks_like_placeholder("your_openai_api_key"))
        self.assertFalse(looks_like_placeholder("test-openai-key"))

    def test_phone_mode_only_requires_openai(self) -> None:
        config = self.make_config()
        self.assertEqual(config.missing_for_phone_mode(), [])

    def test_outbound_call_requirements_are_present(self) -> None:
        config = self.make_config()
        self.assertEqual(config.missing_for_outbound_call(), [])

    def test_initial_twiml_contains_gather(self) -> None:
        agent = RiverwoodVoiceAgent(self.make_config())
        twiml = agent.initial_greeting_twiml()
        self.assertIn("<Gather", twiml)
        self.assertIn("/voice/respond", twiml)

    def test_callback_detection(self) -> None:
        agent = RiverwoodVoiceAgent(self.make_config())
        self.assertTrue(agent.should_log_callback("What is the price for this plot?", "We can arrange a callback."))
        self.assertFalse(agent.should_log_callback("Thank you", "You are welcome."))


if __name__ == "__main__":
    unittest.main()
