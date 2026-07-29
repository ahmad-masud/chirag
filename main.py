import discord
import os
import random
import time
from dotenv import load_dotenv
from ai_handler import generate_chirag_response
from keep_alive import keep_alive

# Load environment variables for local testing
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# --- Chat Algorithm Configuration ---
REPLY_PROBABILITY = 0.15  # 15% chance to reply to a normal message
COOLDOWN_SECONDS = 15     # Minimum seconds between random responses in a channel
channel_cooldowns = {}    # Dictionary to track the last time the bot spoke per channel

@client.event
async def on_ready():
    print(f'Logged in successfully as {client.user}')

@client.event
async def on_message(message):
    # 1. Ignore messages from the bot itself
    if message.author == client.user:
        return

    # Clean mention from the prompt
    prompt = message.content.replace(f'<@{client.user.id}>', '').strip()
    if not prompt:
        return

    # 2. Check Triggers
    is_mentioned = client.user.mentioned_in(message)
    contains_name = "chirag" in message.content.lower()
    
    # 3. Check Cooldown
    current_time = time.time()
    last_reply_time = channel_cooldowns.get(message.channel.id, 0)
    time_since_last_reply = current_time - last_reply_time
    on_cooldown = time_since_last_reply < COOLDOWN_SECONDS

    # 4. Decision Algorithm
    should_respond = False
    
    if is_mentioned or contains_name:
        # Rule: Always respond if directly addressed or named, regardless of cooldown
        should_respond = True  
    elif not on_cooldown:
        # Rule: If the chat is quiet (not on cooldown), roll a 15% chance to chime in
        if random.random() < REPLY_PROBABILITY:
            should_respond = True

    # 5. Execute Response
    if should_respond:
        # Update the cooldown timer for this channel
        channel_cooldowns[message.channel.id] = time.time()
        
        async with message.channel.typing():
            reply = generate_chirag_response(prompt)
            await message.channel.send(reply[:2000])

# Start the web server
keep_alive()

# Start the bot
client.run(os.getenv("DISCORD_TOKEN"))