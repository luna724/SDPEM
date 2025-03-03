from typing import Literal

from discord import Interaction, Embed

from modules.prompt_alias import PromptAlias


async def process_command(interaction: Interaction, mode: Literal["add", "remove", "get", "list"], alias: str, prompt: str = "", memo: str = ""):
    cls = PromptAlias()
    if prompt is None: prompt = ""
    if memo is None: memo = ""

    if mode == "add":
        response = cls.add(alias, prompt, memo)
        await interaction.response.send_message(f"Added alias: {alias} -> {prompt} ({memo})", embed=Embed(description=response))

    elif mode == "remove":
        response = cls.remove(alias)
        await interaction.response.send_message(f"Removed alias: {alias}", embed=Embed(description=response))

    elif mode == "get":
        data = cls.get()
        if data is None or alias in data.keys():
            await interaction.response.send_message(f"Alias not found: {alias}", ephemeral=True)
            return

        await interaction.response.send_message(f"Alias: {alias} -> {data[alias]['prompt']} ({data['memo']})")

    elif mode == "list":
        data = cls.get()
        await interaction.response.send_message("Full json", embed=Embed(description=data))
    return