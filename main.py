import discord
import os
import time
import asyncio
from dotenv import load_dotenv
from ai_handler import (
    generate_chirag_response, 
    get_ai_stats, 
    add_custom_context, 
    get_custom_context_list
)
from keep_alive import keep_alive

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# --- Bot Metrics & Configuration ---
BOT_START_TIME = time.time()
TOTAL_RESPONSES_SENT = 0

COOLDOWN_SECONDS = 10     
HISTORY_LIMIT = 10        
channel_cooldowns = {}    

IS_SHUTUP_MODE = False    # Tracks if the bot is in silent mode

BOT_PREFIXES = ('!', '>', '?', '.', '$', '-', '/', ';', '~')

def get_uptime():
    """Calculates formatted uptime string."""
    seconds = int(time.time() - BOT_START_TIME)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"

@client.event
async def on_ready():
    print(f'Logged in successfully as {client.user}')

@client.event
async def on_message(message):
    global TOTAL_RESPONSES_SENT, IS_SHUTUP_MODE

    if message.author.bot:
        return

    clean_content = message.content.strip()
    if clean_content.startswith(BOT_PREFIXES):
        return

    prompt = message.content.replace(f'<@{client.user.id}>', '').strip()
    if not prompt:
        return

    is_mentioned = client.user.mentioned_in(message)
    contains_name = "chirag" in message.content.lower()

    # Process command requests if Chirag was mentioned or named
    if is_mentioned or contains_name:
        clean_prompt_lower = prompt.lower()

        # --- COMMAND: help ---
        if clean_prompt_lower == "help":
            embed = discord.Embed(
                title="📚 Chirag Gupta — Command Manual",
                description="I am highly intelligent. Here is how you may instruct me:",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=client.user.display_avatar.url)
            
            embed.add_field(name="`@Chirag help`", value="Displays this manual.", inline=False)
            embed.add_field(name="`@Chirag stats`", value="Shows AI usage, ping, and uptime.", inline=False)
            embed.add_field(name="`@Chirag shutup`", value="Forces me to only speak when directly addressed.", inline=False)
            embed.add_field(name="`@Chirag startup`", value="Allows me to chime into conversations freely again.", inline=False)
            embed.add_field(name="`@Chirag add_context <text>`", value="Memorize a fact for this session.", inline=False)
            embed.add_field(name="`@Chirag context`", value="Read all facts I currently have memorized.", inline=False)
            
            await message.channel.send(embed=embed)
            return

        # --- COMMAND: shutup ---
        elif clean_prompt_lower in ["shutup", "shut up"]:
            IS_SHUTUP_MODE = True
            await message.channel.send("Very well. I shall remain silent unless spoken to directly. Good day to you.")
            return
            
        # --- COMMAND: startup ---
        elif clean_prompt_lower == "startup":
            IS_SHUTUP_MODE = False
            await message.channel.send("Excellent. I shall resume gracing this chat with my intellect.")
            return

        # --- COMMAND: add_context <text> ---
        elif clean_prompt_lower.startswith("add_context"):
            idx = clean_prompt_lower.find("add_context")
            context_text = prompt[idx + len("add_context"):].strip()

            if context_text:
                add_custom_context(context_text)
                await message.channel.send(
                    f"Very well. I have recorded that in my memory: \"{context_text}\""
                )
            else:
                await message.channel.send(
                    "Please provide the context you would like me to remember."
                )
            return

        # --- COMMAND: context ---
        elif clean_prompt_lower == "context":
            context_list = get_custom_context_list()

            embed = discord.Embed(
                title="📝 Chirag Gupta — Active Context & Server Memory",
                color=discord.Color.purple()
            )
            embed.set_thumbnail(url=client.user.display_avatar.url)

            if not context_list:
                embed.description = "No custom context has been added during this session."
            else:
                formatted_notes = "\n".join(
                    [f"**{i+1}.** {item}" for i, item in enumerate(context_list)]
                )
                embed.description = formatted_notes

            embed.set_footer(text="Memory persists in RAM until the bot restarts.")
            await message.channel.send(embed=embed)
            return

        # --- COMMAND: stats ---
        elif clean_prompt_lower == "stats":
            ai_stats = get_ai_stats()
            latency_ms = round(client.latency * 1000)

            embed = discord.Embed(
                title="📊 Chirag Gupta — System & AI Stats",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=client.user.display_avatar.url)
            
            embed.add_field(name="⏱️ Uptime", value=get_uptime(), inline=True)
            embed.add_field(name="📡 Latency", value=f"{latency_ms} ms", inline=True)
            embed.add_field(name="💬 Responses Sent", value=str(TOTAL_RESPONSES_SENT), inline=True)
            
            embed.add_field(
                name="🤖 Active Provider", 
                value=f"**{ai_stats['active_provider']}**", 
                inline=True
            )
            embed.add_field(
                name="🧠 Active Model", 
                value=f"`{ai_stats['active_model']}`", 
                inline=True
            )
            embed.add_field(
                name="⚙️ Cooldown / Context", 
                value=f"{COOLDOWN_SECONDS}s / {HISTORY_LIMIT} msgs", 
                inline=True
            )

            counts = ai_stats['request_counts']
            usage_text = (
                f"• **Gemini:** {counts['gemini']} requests\n"
                f"• **Groq:** {counts['groq']} requests\n"
                f"• **OpenRouter:** {counts['openrouter']} requests"
            )
            embed.add_field(name="📈 API Usage Breakdown", value=usage_text, inline=False)
            embed.set_footer(text="Westmore Middle School • Honor Student & Class Icon")

            await message.channel.send(embed=embed)
            return

    # --- REGULAR CHAT LOGIC ---
    current_time = time.time()
    last_reply_time = channel_cooldowns.get(message.channel.id, 0)
    time_since_last_reply = current_time - last_reply_time
    on_cooldown = time_since_last_reply < COOLDOWN_SECONDS

    should_respond = False
    
    if is_mentioned or contains_name:
        # Rule 1: Always respond if pinged or named, regardless of shutup mode
        should_respond = True  
    elif not IS_SHUTUP_MODE and not on_cooldown:
        # Rule 2: Only chime in autonomously if NOT in shutup mode, and cooldown is met
        should_respond = True

    if should_respond:
        try:
            messages = [msg async for msg in message.channel.history(limit=HISTORY_LIMIT)]
            messages.reverse()
            
            conversation = ""
            for msg in messages:
                if msg.author.bot or msg.content.strip().startswith(BOT_PREFIXES):
                    continue

                speaker = "Chirag" if msg.author == client.user else msg.author.display_name
                clean_text = msg.content.replace(f'<@{client.user.id}>', 'Chirag')
                
                if clean_text.strip():
                    conversation += f"[{speaker}]: {clean_text}\n"

            reply = generate_chirag_response(conversation)
            
            channel_cooldowns[message.channel.id] = time.time()
            TOTAL_RESPONSES_SENT += 1
            
            async with message.channel.typing():
                await asyncio.sleep(1.5)
                await message.channel.send(reply[:2000])

        except Exception as e:
            print(f"An error occurred: {e}")
            
            if is_mentioned:
                async with message.channel.typing():
                    await asyncio.sleep(1)
                    await message.channel.send("This is highly unacceptable. I am experiencing technical difficulties.")

keep_alive()
client.run(os.getenv("DISCORD_TOKEN"))