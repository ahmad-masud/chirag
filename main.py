import discord
import os
from dotenv import load_dotenv
from ai_handler import generate_chirag_response
from keep_alive import keep_alive

# Load environment variables for local testing
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in successfully as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if client.user.mentioned_in(message):
        prompt = message.content.replace(f'<@{client.user.id}>', '').strip()
        
        async with message.channel.typing():
            reply = generate_chirag_response(prompt)
            await message.channel.send(reply[:2000])

# Start the web server
keep_alive()

# Start the bot
client.run(os.getenv("DISCORD_TOKEN"))