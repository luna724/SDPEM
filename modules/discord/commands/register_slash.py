import datetime
import time

import discord
from discord import Interaction
from discord.ext import commands

from modules.discord.commands.show_status import get_gpu_info, get_cpu_info, get_ram_info


def register_slash_commands(bot: commands.Bot, guild: discord.Object | None):
    """register ALL slash commands"""
    @bot.tree.command(
        name="status",
        description="show current machine status",
        guild=guild
    )
    async def show_status(interaction: Interaction):
        await interaction.response.send_message("Gathering state..")
        start = time.time()

        gpu_info = get_gpu_info()
        cpu_info = get_cpu_info()
        ram_info = get_ram_info()

        response = f"""
- **{cpu_info["name"]}**
  - Usage: {int(cpu_info["usage"])}%
  - Clock: {cpu_info["clock_speed"]/1024:.2f} GHz"""
        if cpu_info["temperature"] is not None:
            response += """ / Temp: {cpu_info["temperature"]}°C"""

        response += """\n- **GPU(s)**\n"""
        for gpu in gpu_info:
            vram_percentage = f'{((gpu["vram_used"] / gpu["vram_total"]) * 100):.2f}'
            response += f"""  - {gpu["name"].decode("utf-8")} (ID: {gpu["id"]})\n"""
            response += f'  - VRAM: {gpu["vram_used"]/1024:.1f} / {gpu["vram_total"]/1024:.1f} (GB) ({vram_percentage}%)\n'
            response += f'  - Temperature: {gpu["temperature"]}°C\n'
        ram_percentage = f'{((ram_info["used"] / ram_info["total"]) * 100):.2f}'
        response += f"""- **RAM Usage** : {ram_info["used"]/1024:.1f} / {ram_info["total"]/1024:.1f} (GB) ({ram_percentage}%)"""
        await interaction.edit_original_response(content=f"taken: {int((time.time() - start) * 1000)}ms", embed=discord.Embed(title="Machine Status", description=response, color=0xFF0000, timestamp=datetime.datetime.now()))


    @bot.tree.command(
        name="txt2img",
        description="run txt2img with prompt & PEM's Default",
        guild=guild
    )
    async def txt2img(interaction: interaction)