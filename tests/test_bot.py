import asyncio
import os
import tempfile
import unittest
from unittest.mock import Mock, patch


os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")
os.environ.setdefault("DEEPSEEK_API_KEY", "test-deepseek-key")
os.environ.setdefault("GROQ_API_KEY", "test-groq-key")
os.environ.setdefault("OPENROUTER_API_KEY", "test-openrouter-key")
os.environ["CHIRAG_MEMORY_FILE"] = os.path.join(tempfile.mkdtemp(prefix="chirag-memory-"), "memory.json")


import ai_handler
from bot_commands import (
    build_context_embed,
    build_stats_embed,
    handle_mention_command,
    is_bot_command,
)
from bot_state import BotState
from conversation import build_recent_conversation
from memory_store import clear_context


class StubAvatar:
    url = "https://example.invalid/avatar.png"


class StubUser:
    display_avatar = StubAvatar()


class StubChannel:
    def __init__(self):
        self.sent = []

    async def send(self, content=None, embed=None):
        self.sent.append({"content": content, "embed": embed})


class StubClient:
    latency = 0.123


class StubMessage:
    def __init__(self, channel=None, client=None):
        self.channel = channel or StubChannel()
        self.client = client or StubClient()


class BotStateTests(unittest.TestCase):
    def test_get_uptime_formats_hours_minutes_seconds(self):
        state = BotState(started_at=0)

        with patch("bot_state.time.time", return_value=3661):
            self.assertEqual(state.get_uptime(), "1h 1m 1s")


class BotCommandTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        clear_context(123)

    def test_is_bot_command_detects_prefixes(self):
        self.assertTrue(is_bot_command("!help"))
        self.assertTrue(is_bot_command("   /stats"))
        self.assertFalse(is_bot_command("chirag help"))

    def test_build_context_embed_renders_notes(self):
        embed = build_context_embed(StubUser(), ["likes chess", "hates homework"])

        self.assertEqual(embed.title, "📝 Chirag Gupta — Active Context (This Server)")
        self.assertEqual(embed.description, "**1.** likes chess\n**2.** hates homework")

    def test_build_stats_embed_includes_usage_counts(self):
        embed = build_stats_embed(
            StubUser(),
            "1h 2m 3s",
            42,
            9,
            {
                "active_provider": "DeepSeek",
                "active_model": "deepseek-v4-flash",
                "request_counts": {"deepseek": 3, "gemini": 2, "groq": 1, "openrouter": 4},
            },
            True,
        )

        fields = {field.name: field.value for field in embed.fields}
        self.assertEqual(fields["⏱️ Uptime"], "1h 2m 3s")
        self.assertEqual(fields["🔇 Shutup Mode"], "🔴 ON (Silent)")
        self.assertIn("DeepSeek", fields["📈 API Usage Breakdown"])

    async def test_handle_mention_command_adds_context(self):
        channel = StubChannel()
        message = StubMessage(channel=channel)
        state = BotState()

        handled = await handle_mention_command(message, "add_context remembers chess", 123, state, StubUser())

        self.assertTrue(handled)
        self.assertEqual(ai_handler.get_custom_context_list(123), ["remembers chess"])
        self.assertIn("recorded", channel.sent[0]["content"])

    async def test_handle_mention_command_toggles_shutup(self):
        channel = StubChannel()
        message = StubMessage(channel=channel)
        state = BotState()

        handled = await handle_mention_command(message, "shutup", 123, state, StubUser())

        self.assertTrue(handled)
        self.assertTrue(state.shutup_modes[123])
        self.assertIn("strictly silent", channel.sent[0]["content"])


class AiHandlerTests(unittest.TestCase):
    def setUp(self):
        self.old_active_provider = ai_handler.ACTIVE_PROVIDER
        self.old_request_counts = ai_handler.REQUEST_COUNTS.copy()

    def tearDown(self):
        ai_handler.ACTIVE_PROVIDER = self.old_active_provider
        ai_handler.REQUEST_COUNTS.clear()
        ai_handler.REQUEST_COUNTS.update(self.old_request_counts)

    def test_get_full_persona_includes_server_context(self):
        clear_context(7)
        ai_handler.add_custom_context(7, "likes chess")

        persona = ai_handler.get_full_persona(7)

        self.assertIn("likes chess", persona)
        self.assertIn("CRITICAL SERVER FACTS & CONTEXT TO REMEMBER", persona)

    def test_build_recent_conversation_limits_and_focuses_last_message(self):
        bot_user = type("BotUser", (), {"id": 999})()
        messages = []

        for index in range(20):
            author = type("Author", (), {"bot": False, "display_name": f"User{index}"})()
            message = type("Message", (), {"author": author, "content": f"message {index}"})()
            messages.append(message)

        transcript = build_recent_conversation(messages, bot_user)

        self.assertIn("[User0]: message 0", transcript)
        self.assertIn("[User19]: message 19", transcript)
        self.assertIn("Answer the last message directly", transcript)

    def test_generate_chirag_response_rotates_until_success(self):
        ai_handler.ACTIVE_PROVIDER = "deepseek"

        mock_generate = Mock(side_effect=[RuntimeError("deepseek down"), RuntimeError("openrouter down"), "final reply"])

        with patch.object(ai_handler, "_generate_for_provider", mock_generate):
            reply = ai_handler.generate_chirag_response(99, "hello there")

        self.assertEqual(reply, "final reply")
        self.assertEqual(ai_handler.ACTIVE_PROVIDER, "gemini")
        self.assertEqual(ai_handler.REQUEST_COUNTS["gemini"], self.old_request_counts["gemini"] + 1)
        self.assertEqual(
            [call.args[0] for call in mock_generate.call_args_list],
            ["deepseek", "openrouter", "gemini"],
        )


if __name__ == "__main__":
    unittest.main()