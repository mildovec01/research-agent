import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import threading
from config import (
    DISCORD_BOT_TOKEN,
    DISCORD_GUILD_ID,
    DISCORD_CHANNEL_ROBOTIKA,
    DISCORD_CHANNEL_MARKET,
)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
_bot_ready = threading.Event()


@bot.event
async def on_ready():
    print(f"[Discord] Bot přihlášen jako {bot.user}")
    try:
        guild = discord.Object(id=DISCORD_GUILD_ID)
        synced = await bot.tree.sync(guild=guild)
        print(f"[Discord] Synchronizovány {len(synced)} slash příkazy")
    except Exception as e:
        print(f"[Discord] Chyba při sync příkazů: {e}")
    _bot_ready.set()


@bot.tree.command(
    name="research",
    description="Spustí research agenta pro zadané téma",
    guild=discord.Object(id=DISCORD_GUILD_ID),
)
@app_commands.describe(topic="Téma pro výzkum (např. 'Boston Dynamics')")
async def slash_research(interaction: discord.Interaction, topic: str):
    await interaction.response.defer(thinking=True)
    await interaction.followup.send(f"🔍 Spouštím research pro: **{topic}**...")

    loop = asyncio.get_event_loop()
    from agents.orchestrator import run as orchestrator_run
    result = await loop.run_in_executor(None, lambda: orchestrator_run(topics=[topic]))

    embeds = result.get("discord", [])
    discord_embeds = [discord.Embed.from_dict(e) for e in embeds]

    channel = bot.get_channel(DISCORD_CHANNEL_ROBOTIKA)
    if channel:
        await channel.send(embeds=discord_embeds[:4])
    await interaction.followup.send("✅ Report odeslán!")


async def send_embeds(embeds: list[dict], channel_id: int):
    await _bot_ready_async()
    channel = bot.get_channel(channel_id)
    if not channel:
        print(f"[Discord] Kanál {channel_id} nenalezen")
        return
    discord_embeds = [discord.Embed.from_dict(e) for e in embeds[:4]]
    await channel.send(embeds=discord_embeds)
    print(f"[Discord] Embedy odeslány do kanálu {channel_id}")


async def _bot_ready_async():
    while not _bot_ready.is_set():
        await asyncio.sleep(0.5)


def send_report(embeds: list[dict], channel_id: int | None = None):
    if channel_id is None:
        channel_id = DISCORD_CHANNEL_ROBOTIKA
    loop = asyncio.get_event_loop()
    loop.create_task(send_embeds(embeds, channel_id))


def run_bot():
    bot.run(DISCORD_BOT_TOKEN)


def start_bot_thread():
    thread = threading.Thread(target=run_bot, daemon=True)
    thread.start()
    print("[Discord] Bot thread spuštěn")
    return thread
