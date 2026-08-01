import discord
import os
import time
import asyncio
from dotenv import load_dotenv
from ai_handler import (
    generate_chirag_response, 
)
from keep_alive import keep_alive
from bot_commands import handle_mention_command, is_bot_command
from bot_state import BotState
from conversation import build_recent_conversation

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

COOLDOWN_SECONDS = 10     
HISTORY_LIMIT = 20        
bot_state = BotState()

@client.event
async def on_ready():
    print(f'Logged in successfully as {client.user}')

@client.event
async def on_message(message):
    if message.author.bot:
        return

    clean_content = message.content.strip()
    if is_bot_command(clean_content):
        return

    prompt = message.content.replace(f'<@{client.user.id}>', '').strip()
    if not prompt:
        return

    # Use the guild ID for server-specific memory (fallback to author ID for DMs)
    server_id = message.guild.id if message.guild else message.author.id

    is_mentioned = f'<@{client.user.id}>' in message.content or client.user.mentioned_in(message)
    contains_name = "chirag" in message.content.lower()

    if is_mentioned or contains_name:
        handled = await handle_mention_command(message, prompt, server_id, bot_state, client.user)
        if handled:
            return

    # --- REGULAR CHAT LOGIC ---
    current_time = time.time()
    last_reply_time = bot_state.channel_cooldowns.get(message.channel.id, 0)
    time_since_last_reply = current_time - last_reply_time
    on_cooldown = time_since_last_reply < COOLDOWN_SECONDS

    is_shutup = bot_state.shutup_modes.get(server_id, False)
    should_respond = False
    
    if is_shutup:
        if is_mentioned:
            should_respond = True
    else:
        if is_mentioned or contains_name:
            should_respond = True  
        elif not on_cooldown:
            should_respond = True

    if should_respond:
        try:
            messages = [
                msg async for msg in message.channel.history(limit=HISTORY_LIMIT - 1, before=message.created_at)
            ]
            messages.reverse()

            conversation = build_recent_conversation(messages + [message], client.user)

            if not conversation:
                return

            # Pass the server_id so the AI knows which context to load
            reply = generate_chirag_response(server_id, conversation)
            
            bot_state.channel_cooldowns[message.channel.id] = time.time()
            bot_state.total_responses_sent += 1
            
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