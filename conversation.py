from bot_commands import is_bot_command


def build_recent_conversation(messages, bot_user) -> str:
    transcript_lines = []

    for message in messages:
        if message.author.bot or is_bot_command(message.content):
            continue

        speaker = "Chirag" if message.author == bot_user else message.author.display_name
        clean_text = message.content.replace(f"<@{bot_user.id}>", "Chirag").strip()

        if clean_text:
            transcript_lines.append(f"[{speaker}]: {clean_text}")

    if not transcript_lines:
        return ""

    transcript = "\n".join(transcript_lines)
    return (
        f"{transcript}\n\n"
        "Answer the last message directly. Use the earlier lines only as context, not as the thing to answer."
    )