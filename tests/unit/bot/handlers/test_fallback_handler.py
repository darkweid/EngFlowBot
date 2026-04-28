from bot.handlers.fallback_handler import send_fallback_message
from bot.lexicon import MessageTexts
from tests.helpers import FakeMessage


async def test_send_fallback_message_replies_with_error_text():
    message = FakeMessage(full_name="Alice Tester")

    await send_fallback_message(message)

    message.reply.assert_awaited_once_with(f"Hey, Alice\n{MessageTexts.ERROR}")
