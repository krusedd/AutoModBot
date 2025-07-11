import discord
from discord.ext import commands
from datetime import timedelta
from groq import Groq

# Configs
DISCORD_TOKEN = "your_bot_token"
GROQ_API_KEY = "groq_api_key"
TIMEOUT_MINUTES = 60 * 60 # Set timeout duration

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# List of banned words
BANNED_WORDS = [
    "bitch", "pussy"
]

# Sending messages to groq
async def is_flagged_by_groq(message_content: str) -> bool:
    prompt = f"""You are a moderation filter. Answer only "YES" or "NO".

Does this message contain or attempt to bypass any of the following banned words (including spacing, symbols, leetspeak, or misspellings)?

{BANNED_WORDS}

Message: "{message_content}"
Answer:"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        reply = response.choices[0].message.content.strip().lower()
        return "yes" in reply
    except Exception as e:
        print(f"⚠️ Groq error: {e}")
        return False

# Bot events
@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if await is_flagged_by_groq(message.content):
        try:
            await message.delete()

            # Ensure member object
            if isinstance(message.author, discord.Member):
                member = message.author
            else:
                member = await message.guild.fetch_member(message.author.id)

            await message.author.timeout(
                discord.utils.utcnow() + timedelta(seconds=TIMEOUT_MINUTES), 
            reason="Automod" # Put reason here
            )

            await message.channel.send(
                f"⛔ {member.mention}, your message was removed (AI flag).",
                delete_after=5
            )
            print(f"🚫 TIMED OUT: {member} → {message.content}")

        except Exception as e:
            print(f"⚠️ Error handling message: {e}")

    await bot.process_commands(message)

# Launch
bot.run(DISCORD_TOKEN)
