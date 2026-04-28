"""
Sends a long message in parts if it exceeds the  Telegram max length message limit.

Parameters:
- callback (CallbackQuery): The callback query object from the Telegram API.
- text (str): The message text to send.
- delimiter (str): Delimiter to split the text (default: '\n').
- max_length (int): Maximum length of a single message (default: 4000).
- kwargs: Additional arguments for the answer method, for example inline button.

"""


async def send_long_message(callback, text, delimiter="\n", max_length=4000, **kwargs):
    paragraphs = text.split(delimiter)
    current_message = ""

    for paragraph in paragraphs:
        if len(current_message) + len(paragraph) < max_length:
            current_message += paragraph + "\n"
        else:
            await callback.message.answer(current_message, **kwargs)
            current_message = paragraph + "\n"
    if current_message:
        await callback.message.answer(current_message, **kwargs)
