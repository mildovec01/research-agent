import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import threading
import io
from config import (
    DISCORD_BOT_TOKEN,
    DISCORD_GUILD_ID,
    DISCORD_CHANNEL_ROBOTIKA,
    DISCORD_CHANNEL_MARKET,
    DISCORD_CHANNEL_PROJEKTY,
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


@bot.tree.command(
    name="project",
    description="Vygeneruje kompletní projekt: součástky, ceny, OpenSCAD model, kód",
    guild=discord.Object(id=DISCORD_GUILD_ID),
)
@app_commands.describe(description="Popis projektu (např. 'sledovač čáry' nebo 'robotická ruka 3DOF')")
async def slash_project(interaction: discord.Interaction, description: str):
    await interaction.response.defer(thinking=True)
    await interaction.followup.send(f"⚙️ Navrhuji projekt: **{description}**\nTohle může trvat 1-2 minuty...")

    loop = asyncio.get_event_loop()

    from agents.project import run as project_run
    from agents.review import run as review_run

    project_data = await loop.run_in_executor(None, lambda: project_run(description))
    await interaction.followup.send("🔍 Review agent kontroluje návrh...")
    final_data = await loop.run_in_executor(None, lambda: review_run(project_data))

    channel = bot.get_channel(DISCORD_CHANNEL_PROJEKTY)
    if channel:
        await send_project_to_discord(channel, final_data)

    await interaction.followup.send(f"✅ Projekt odeslán do <#{DISCORD_CHANNEL_PROJEKTY}>!")


async def send_project_to_discord(channel, data: dict):
    score = data.get("confidence_score", 0)
    score_emoji = "🟢" if score >= 7 else "🟡" if score >= 4 else "🔴"

    main_embed = discord.Embed(
        title=f"🤖 {data.get('project_name', 'Nový projekt')}",
        description=data.get("description", ""),
        color=0x1D9E75,
    )

    mc = data.get("microcontroller", {})
    main_embed.add_field(
        name="🧠 Mikrokontrolér",
        value=f"**{mc.get('name', '?')}**\n{mc.get('reason', '')}",
        inline=False,
    )

    components = data.get("components", [])
    comp_lines = []
    for c in components:
        comp_lines.append(
            f"• **{c.get('name')}** ×{c.get('quantity', 1)} — "
            f"{c.get('unit_price_czk', '?')} Kč/ks = **{c.get('total_price_czk', '?')} Kč**"
        )
    if comp_lines:
        main_embed.add_field(
            name="🛒 Součástky",
            value="\n".join(comp_lines[:10]),
            inline=False,
        )

    main_embed.add_field(
        name="💰 Celková cena",
        value=f"**{data.get('total_price_czk', '?')} Kč**",
        inline=True,
    )
    main_embed.add_field(
        name="Review score",
        value=f"{score_emoji} {score}/10",
        inline=True,
    )

    warnings = data.get("warnings", [])
    if warnings:
        main_embed.add_field(
            name="⚠️ Upozornění",
            value="\n".join(f"• {w}" for w in warnings),
            inline=False,
        )

    review_notes = data.get("review_notes", [])
    if review_notes:
        main_embed.add_field(
            name="📝 Review notes",
            value="\n".join(f"• {n}" for n in review_notes[:5]),
            inline=False,
        )

    await channel.send(embed=main_embed)

    openscad = data.get("openscad_code", "")
    if openscad:
        scad_file = discord.File(
            fp=io.BytesIO(openscad.encode("utf-8")),
            filename=f"{data.get('project_name', 'project').replace(' ', '_')}.scad",
        )
        await channel.send("📐 **OpenSCAD model:**", file=scad_file)

    code = data.get("main_code", "")
    lang = data.get("code_language", "arduino")
    ext = {"arduino": "ino", "python": "py", "ros2": "py"}.get(lang, "txt")
    if code:
        code_file = discord.File(
            fp=io.BytesIO(code.encode("utf-8")),
            filename=f"{data.get('project_name', 'project').replace(' ', '_')}.{ext}",
        )
        await channel.send(f"💻 **Kód ({lang}):**", file=code_file)

    steps = data.get("assembly_steps", [])
    if steps:
        steps_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
        steps_embed = discord.Embed(
            title="🔧 Postup sestavení",
            description=steps_text,
            color=0x7F77DD,
        )
        await channel.send(embed=steps_embed)


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
    _bot_ready.wait(timeout=15)
    future = asyncio.run_coroutine_threadsafe(
        send_embeds(embeds, channel_id),
        bot.loop
    )
    try:
        future.result(timeout=15)
        print("[Discord] Embedy odeslány ✓")
    except Exception as e:
        print(f"[Discord] Chyba při odesílání: {e}")


def run_bot():
    bot.run(DISCORD_BOT_TOKEN)


def start_bot_thread():
    thread = threading.Thread(target=run_bot, daemon=True)
    thread.start()
    print("[Discord] Bot thread spuštěn")
    return thread
