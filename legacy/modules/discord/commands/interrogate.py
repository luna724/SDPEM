import discord
from discord import Interaction
from typing import Literal

async def process_command(
        interaction: Interaction,
        image: discord.Attachment,
        model: Literal["clip"] = "clip",
):
    await interaction.response.send_message(
        "not implemented yet",
    )
    return