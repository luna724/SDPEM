import os
import datetime
import time
from io import BytesIO
from typing import Literal

import discord
from PIL import Image
from discord import Interaction
from discord.ext import commands

import shared
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


    @bot.tree.command(
        name="last_image",
        description="show last generated image",
    )
    async def last_image(interaction: Interaction, mode: Literal["last_file", "ram"] = "last_file", format: Literal["JPEG", "PNG"] = "PNG"): # TODO: まともな処理にする (#27参照)
        if mode == "ram":
            await interaction.response.send_message("Not implemented yet.", ephemeral=True)
            return

        elif mode == "last_file":
            # outputs/txt2img-images から最後の画像を取得
            outputs_dir = os.path.join(shared.a1111_webui_path, "outputs/txt2img-images")
            output_folders = [
                    os.path.join(outputs_dir, folder)
                    for folder in sorted(os.listdir(outputs_dir))
            ]
            if len(output_folders) == 0:
                await interaction.response.send_message("No images found.", ephemeral=True)
                return

            image = None
            folder_index = -1
            while image is None:
                images = [
                    os.path.join(output_folders[folder_index], file)
                    for file in os.listdir(output_folders[folder_index])
                    if file.lower().endswith(".png")
                ]
                if len(images) == 0:
                    folder_index -= 1

                    # フォルダ数が全部なくなったら終了
                    if len(output_folders) + folder_index <= 0:
                        await interaction.response.send_message("No images found.", ephemeral=True)
                        return

                    continue

                image = images[-1]
                break
            if image is None:
                await interaction.response.send_message("No images found.", ephemeral=True)
                return

            # JPEGに対応させる
            image_buffer = BytesIO()
            img = Image.open(image)
            img.save(image_buffer, format=format)
            image_buffer.seek(0)

            if image_buffer.getbuffer().nbytes > 10 * 1024 * 1024:
                await interaction.response.send_message("Image is too large to send. did you try JPEG mode? (> 10MB)", ephemeral=True)
                return

            image = discord.File(image_buffer, filename=f"last_image.{format.lower()}")
            await interaction.response.send_message(file=image)
            return img


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