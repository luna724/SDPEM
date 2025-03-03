from discord import Interaction

from modules.api.txt2img import txt2img_api
from modules.util import EmptyInstance


async def process_command(interaction: Interaction, prompt: str):
    api = txt2img_api(15)

    prompt = "score_9, score_8_up, score_7_up, best quality, masterpiece, BREAK\n"+prompt
    await interaction.response.send_message("Generating...")
    await api.bot_generate(prompt, interaction)
    return