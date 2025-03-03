import os
import discord

from io import BytesIO
from PIL import Image
from discord import Interaction
from typing import *

from modules.image_progress import ImageProgressAPI
import shared

async def process_command(interaction: Interaction, mode: Literal["ram", "last_file"], format: Literal["JPEG", "PNG"]):
    if mode == "ram":
        image = ImageProgressAPI.last_generated_image

        if image is None:
            await interaction.response.send_message("No images found.", ephemeral=True)
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

    else:
        await interaction.response.send_message("Invalid mode.", ephemeral=True)
        return

    # JPEGに対応させる
    image_buffer = BytesIO()
    img = Image.open(image)
    img.save(image_buffer, format=format)
    image_buffer.seek(0)

    if image_buffer.getbuffer().nbytes > 10 * 1024 * 1024:
        await interaction.response.send_message("Image is too large to send. did you try JPEG mode? (> 10MB)",
                                                ephemeral=True)
        return

    image = discord.File(image_buffer, filename=f"last_image.{format.lower()}")
    await interaction.response.send_message(file=image)
    return img