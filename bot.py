import os
import json
import discord
from discord.ext import commands
from google import genai

# Render bezpiecznie przekaże te klucze ze swoich ustawień
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Inicjalizacja AI z dostępem do wyszukiwarki Google
client = genai.Client(api_key=GEMINI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

SETTINGS_FILE = "settings.json"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

server_settings = load_settings()

@bot.event
async def on_ready():
    print(f"NovaBot ({bot.user}) zalogował się i jest gotowy!")

@bot.command(name="setup")
@commands.has_permissions(administrator=True)
async def setup_channel(ctx):
    guild_id = str(ctx.guild.id)
    channel_id = ctx.channel.id
    
    server_settings[guild_id] = channel_id
    save_settings(server_settings)
    
    await ctx.send(f"✅ Pomyślnie ustawiono ten kanał ({ctx.channel.mention}) jako dedykowany kanał dla **NovaBota**!")

@setup_channel.error
async def setup_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Tylko administratorzy mogą używać tej komendy!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    await bot.process_commands(message)

    if not message.guild:
        return

    guild_id = str(message.guild.id)
    ai_channel_id = server_settings.get(guild_id)

    is_in_ai_channel = (ai_channel_id is not None and message.channel.id == ai_channel_id)
    is_mentioned = bot.user.mentioned_in(message)

    if message.content.startswith("!"):
        return

    if is_in_ai_channel or is_mentioned:
        async with message.channel.typing():
            try:
                user_prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()
                if not user_prompt:
                    return

                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=user_prompt,
                    config={
                        "tools": [{"google_search": {}}]
                    }
                )

                answer = response.text
                if len(answer) > 2000:
                    answer = answer[:1997] + "..."

                await message.reply(answer)
            except Exception as e:
                await message.reply(f"Wystąpił błąd podczas generowania odpowiedzi: {e}")

bot.run(DISCORD_TOKEN)