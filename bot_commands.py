import discord

from ai_handler import (
    get_ai_stats,
    get_custom_context_list,
)
from memory_store import add_context, clear_context, remove_context


BOT_PREFIXES = ('!', '>', '?', '.', '$', '-', '/', ';', '~')


def is_bot_command(content: str) -> bool:
    return content.strip().startswith(BOT_PREFIXES)


def build_help_embed(bot_user: discord.ClientUser) -> discord.Embed:
    embed = discord.Embed(
        title="📚 Chirag Gupta — Command Manual",
        description="I am highly intelligent. Here is how you may instruct me:",
        color=discord.Color.green(),
    )
    embed.set_thumbnail(url=bot_user.display_avatar.url)

    embed.add_field(name="`@Chirag help`", value="Displays this manual.", inline=False)
    embed.add_field(name="`@Chirag stats`", value="Shows AI usage, ping, and uptime.", inline=False)
    embed.add_field(name="`@Chirag shutup`", value="Forces me to only speak when explicitly @pinged.", inline=False)
    embed.add_field(name="`@Chirag startup`", value="Allows me to chime into conversations freely again.", inline=False)
    embed.add_field(name="`@Chirag add_context <text>`", value="Memorize a fact for this server.", inline=False)
    embed.add_field(name="`@Chirag remove_context <number>`", value="Delete a specific memory by its number.", inline=False)
    embed.add_field(name="`@Chirag clear_context`", value="Wipe all memorized facts completely for this server.", inline=False)
    embed.add_field(name="`@Chirag context`", value="Read all facts I currently have memorized for this server.", inline=False)
    return embed


def build_context_embed(bot_user: discord.ClientUser, context_list: list[str]) -> discord.Embed:
    embed = discord.Embed(
        title="📝 Chirag Gupta — Active Context (This Server)",
        color=discord.Color.purple(),
    )
    embed.set_thumbnail(url=bot_user.display_avatar.url)

    if not context_list:
        embed.description = "No custom context has been added for this server during this session."
    else:
        embed.description = "\n".join(f"**{index + 1}.** {item}" for index, item in enumerate(context_list))

    embed.set_footer(text="Memory persists in RAM until the bot restarts.")
    return embed


def build_stats_embed(
    bot_user: discord.ClientUser,
    uptime_text: str,
    latency_ms: int,
    total_responses_sent: int,
    ai_stats: dict,
    shutup_enabled: bool,
) -> discord.Embed:
    embed = discord.Embed(
        title="📊 Chirag Gupta — System & AI Stats",
        color=discord.Color.blue(),
    )
    embed.set_thumbnail(url=bot_user.display_avatar.url)

    embed.add_field(name="⏱️ Uptime", value=uptime_text, inline=True)
    embed.add_field(name="📡 Latency", value=f"{latency_ms} ms", inline=True)
    embed.add_field(name="💬 Responses Sent", value=str(total_responses_sent), inline=True)
    embed.add_field(name="🤖 Active Provider", value=f"**{ai_stats['active_provider']}**", inline=True)
    embed.add_field(name="🧠 Active Model", value=f"`{ai_stats['active_model']}`", inline=True)

    mode_text = "🔴 ON (Silent)" if shutup_enabled else "🟢 OFF (Active)"
    embed.add_field(name="🔇 Shutup Mode", value=mode_text, inline=True)

    counts = ai_stats["request_counts"]
    usage_text = (
        f"• **DeepSeek:** {counts.get('deepseek', 0)} requests\n"
        f"• **Gemini:** {counts.get('gemini', 0)} requests\n"
        f"• **Groq:** {counts.get('groq', 0)} requests\n"
        f"• **OpenRouter:** {counts.get('openrouter', 0)} requests"
    )
    embed.add_field(name="📈 API Usage Breakdown", value=usage_text, inline=False)
    embed.set_footer(text="Westmore Middle School • Honor Student & Class Icon")
    return embed


async def handle_mention_command(
    message: discord.Message,
    prompt: str,
    server_id: int,
    bot_state,
    bot_user: discord.ClientUser,
) -> bool:
    clean_prompt_lower = prompt.lower()

    if clean_prompt_lower == "help":
        await message.channel.send(embed=build_help_embed(bot_user))
        return True

    if clean_prompt_lower.startswith("shutup") or clean_prompt_lower.startswith("shut up"):
        bot_state.shutup_modes[server_id] = True
        await message.channel.send("Very well. I shall remain strictly silent in this server unless explicitly pinged. Good day to you.")
        return True

    if clean_prompt_lower.startswith("startup"):
        bot_state.shutup_modes[server_id] = False
        await message.channel.send("Excellent. I shall resume gracing this server with my intellect autonomously.")
        return True

    if clean_prompt_lower.startswith("add_context"):
        idx = clean_prompt_lower.find("add_context")
        context_text = prompt[idx + len("add_context"):].strip()

        if context_text:
            add_context(server_id, context_text)
            await message.channel.send(f"Very well. I have recorded that in this server's memory: \"{context_text}\"")
        else:
            await message.channel.send("Please provide the context you would like me to remember.")
        return True

    if clean_prompt_lower.startswith("remove_context"):
        try:
            parts = clean_prompt_lower.split("remove_context", 1)[1].strip()
            index = int(parts)

            if remove_context(server_id, index):
                await message.channel.send(f"Done. I have erased item #{index} from this server's memory.")
            else:
                await message.channel.send(f"I cannot do that. Item #{index} does not exist in this server's memory.")
        except ValueError:
            await message.channel.send("Please provide a valid number. For example: `@Chirag remove_context 2`")
        return True

    if clean_prompt_lower.startswith("clear_context"):
        clear_context(server_id)
        await message.channel.send("This server's memory has been completely wiped. A fresh start for my brilliant mind.")
        return True

    if clean_prompt_lower.startswith("context"):
        await message.channel.send(embed=build_context_embed(bot_user, get_custom_context_list(server_id)))
        return True

    if clean_prompt_lower.startswith("stats"):
        ai_stats = get_ai_stats()
        latency_ms = round(message.client.latency * 1000)
        await message.channel.send(
            embed=build_stats_embed(
                bot_user,
                bot_state.get_uptime(),
                latency_ms,
                bot_state.total_responses_sent,
                ai_stats,
                bot_state.shutup_modes.get(server_id, False),
            )
        )
        return True

    return False
