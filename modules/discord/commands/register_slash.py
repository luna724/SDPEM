import datetime
import time
from io import BytesIO
from typing import Literal

import discord
from discord import Interaction
from discord.ext import commands

from modules.api.txt2img import txt2img_api
from modules.discord.commands.show_status import get_gpu_info, get_cpu_info, get_ram_info
from modules.image_progress import ImageProgressAPI


def register_slash_commands(bot: commands.Bot, guild: discord.Object | None):
    """register ALL slash commands"""
    @bot.tree.command(
        name="status",
        description="show current machine status",
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
        name="current_image",
        description="show current_generation or last generated image",
    )
    async def current_image(interaction: Interaction):
        progress, eta, states, img, _ = ImageProgressAPI.get_progress()
        image = {}
        if img is not None:
            image_buffer = BytesIO()
            img.save(image_buffer, format="PNG")

            if image_buffer.getbuffer().nbytes > 9.5 * 1024 * 1024:
                # Discordの許容量を超えているならJPEG保存
                image_buffer = BytesIO()
                img.save(image_buffer, format="JPEG")
                image_buffer.seek(0)
                image = {"file": discord.File(image_buffer, filename="current_image.jpg")}

            else:
                image_buffer.seek(0)
                image = {"file": discord.File(image_buffer, filename="current_image.png")}


        # await interaction.response.send_message(f"test: \n```Progress: {progress}\nETA: {eta}\nStates: {states}```", **image)
        note = ""
        step = states.get("sampling_step", 0)
        if eta == 0 or step <= 0:
            note += "- Preview image are Unavailable. (__/last_image__ to show)\n"
            image = {}
        if states.get("interrupted", False):
            note += "- Generation was interrupted.\n"
        if states.get("skipped", False):
            note += "- Generation was Skipped.\n"

        embed = discord.Embed(
            title="Current Image",
            description=f'{note}\n'+
                        f'**Steps**: {ImageProgressAPI.status_text(step, states.get("sampling_steps", -1)) if eta != 0 else "NaN"}\n' +
                        f'**ETA**: {ImageProgressAPI.resize_eta(eta) if eta != 0 else "NaN"}\n\n' +
                        f'Generation {f"will Ends on: <t:{int(time.time() + eta)}:F>" if eta != 0 else "was **Ended**."}',
            color=discord.Color.greyple()
        )
        await interaction.response.send_message(embed=embed, **image)


    import modules.discord.commands.last_image
    @bot.tree.command(
        name="last_image",
        description="show last generated image",
    )
    async def last_image(interaction: Interaction, mode: Literal["last_file", "ram"] = "last_file", format: Literal["JPEG", "PNG"] = "PNG"):
        await modules.discord.commands.last_image.process_command(interaction, mode, format)


    @bot.tree.command(
        name="interrupt",
        description="interrupt current generation",
    )
    async def interrupt(interaction: Interaction, force: bool = False):
        txt2img_api().interrupt()
        if force:
            txt2img_api().interrupt()
            txt2img_api().skip()

        await interaction.response.send_message("Interrupting... (__/current_image__ to check status)", ephemeral=True)
        return

    import modules.discord.commands.generate
    @bot.tree.command(
        name="generate",
        description="Generate image from prompt",
    )
    async def generate(
            interaction: Interaction, *, prompt: str,
            batch_size: int = None,
            width: int = None,
            height: int = None,
            denoising_strength: float = None
    ):
        payload = {}
        if batch_size is not None: payload["batch_size"] = batch_size
        if width is not None: payload["width"] = width
        if height is not None: payload["height"] = height
        if denoising_strength is not None: payload["denoising_strength"] = denoising_strength

        await modules.discord.commands.generate.process_command(interaction, prompt=prompt, **payload)


    import modules.discord.commands.alias
    @bot.tree.command(
        name="alias",
        description="Manage prompt aliases",
    )
    async def alias(
            interaction: Interaction,
            mode: Literal["add", "remove", "get", "list"] = "add", _alias: str = None, prompt: str = None, memo: str = None
    ):
        await modules.discord.commands.alias.process_command(interaction, mode=mode, alias=_alias, prompt=prompt, memo=memo)


    import modules.discord.commands.interrogate
    @bot.tree.command(
        name="interrogate",
        description="Interrogate image",
    )
    async def interrogate(
            interaction: Interaction,
            image: discord.Attachment,
            model: Literal["clip"] = "clip",
    ):
        await modules.discord.commands.interrogate.process_command(interaction, image, model)


    import modules.discord.commands.adetailer
    @bot.tree.command(
        name="adetailer",
        description="ADetailer inference",
    )
    async def adetailer(
            interaction: Interaction,
            image: discord.Attachment,
            model: Literal[
            "face_yolov8n.pt",
            "face_yolov8s.pt",
            "hand_yolov8n.pt",
            "person_yolov8n-seg.pt",
            "person_yolov8s-seg.pt",
            "yolov8x-worldv2.pt",
            "mediapipe_face_full",
            "mediapipe_face_short",
            "mediapipe_face_mesh",
            "mediapipe_face_mesh_eyes_only"
    ] = "face_yolov8n.pt",
            steps: int = 24,
    ):
        await modules.discord.commands.adetailer.process_command(interaction, image, model, steps)
        return