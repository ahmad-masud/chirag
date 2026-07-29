import discord
import os
import time
import asyncio
from dotenv import load_dotenv
from ai_handler import generate_chirag_response
from keep_alive import keep_alive

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# --- Chat Algorithm Configuration ---
COOLDOWN_SECONDS = 10     
HISTORY_LIMIT = 10        
channel_cooldowns = {}    

BOT_PREFIXES = ('!', '>', '?', '.', '$', '-', '/', ';', '~')

@client.event
async def on_ready():
    print(f'Logged in successfully as {client.user}')

@client.event
async def on_message(message):
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
    
    current_time = time.time()
    last_reply_time = channel_cooldowns.get(message.channel.id, 0)
    time_since_last_reply = current_time - last_reply_time
    on_cooldown = time_since_last_reply < COOLDOWN_SECONDS

    should_respond = False
    
    if is_mentioned or contains_name:
        should_respond = True  
    elif not on_cooldown:
        should_respond = True

    if should_respond:
        channel_cooldowns[message.channel.id] = time.time()
        
        try:
            # 1. Fetch history silently
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

            # 2. Get the AI response silently
            reply = generate_chirag_response(conversation)
            
            # 3. If successful, NOW show the typing indicator for realism
            async with message.channel.typing():
                await asyncio.sleep(1.5) # Pause briefly so users see he is "typing"
                await message.channel.send(reply[:2000])

        except Exception as e:
            print(f"An error occurred: {e}")
            
            # If he was mentioned during a crash, show typing and complain
            if is_mentioned:
                async with message.channel.typing():
                    await asyncio.sleep(1)
                    await message.channel.send("This is highly unacceptable. I am experiencing technical difficulties.")
            
            # If he wasn't mentioned, he fails completely invisibly. No ghost typing!

keep_alive()
client.run(os.getenv("DISCORD_TOKEN"))