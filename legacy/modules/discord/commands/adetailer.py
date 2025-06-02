import asyncio
import base64
import time
from io import BytesIO

import discord
from PIL import Image
from discord import Interaction
from typing import Literal

from modules.api.adetailer import ADetailerAPI
from modules.image_param import ImageParamUtil
from modules.image_progress import ImageProgressAPI


class adetailer_api_for_bot(ADetailerAPI):
    async def bot_generate(
            self, interaction: Interaction, image: Image.Image, model: str,
            steps: int, prompt: str = "", negative: str = "",
    ):
        start = time.time()
        param = ImageParamUtil().parse_param(ImageParamUtil().extract_png_metadata(image).get("parameters", ""))[0]
        img_prompt = param["prompt"]
        img_negative = param["negative"]


        payload = self.default_payload | {
            "alwayson_scripts": {
                "ADetailer": {
                    "args": [
                        True,
                        True,
                        {
                            "ad_model": model,
                            "ad_prompt": prompt if prompt.strip() != "" else "",
                            "ad_negative_prompt": negative if negative.strip() != "" else ""
                        }
                    ]
                }
            },
            "prompt": img_prompt,
            "negative_prompt": img_negative,
            "init_images": [],
            "width": image.width,
            "height": image.height,
            "steps": steps,
            "batch_size": 1
        }

        # 画像をbase64に変換
        buffer = BytesIO()
        image.convert("RGB").save(buffer, format="PNG")
        buffer.seek(0)
        payload["init_images"] = [
            base64.b64encode(buffer.getbuffer()).decode("utf-8"),
        ]

        future = self.executor.submit(self._img2img_api, payload)
        pharase = 0

        while not future.done():
            progress, eta, state, image, _ = self.get_progress()
            if state is None:
                time.sleep(1)
                continue

            note = ""
            current_step = state.get("sampling_step", 0)
            total_step = state.get("sampling_steps", 0)

            if eta == 0 or current_step <= 0:
                note += "- Preview image are Unavailable. (__/last_image__ to show)\n"
                img = {}
            if state.get("interrupted", False):
                note += "- Generation was interrupted.\n"
            if state.get("skipped", False):
                note += "- Generation was Skipped.\n"
            if total_step == 0:
                await asyncio.sleep(1)
                continue

            for _ in range(15):
                await asyncio.sleep(1)
                if future.done():
                    break

            embed = discord.Embed(
                title=f"Generation in Progress! ({pharase})",
                description=f'{note}\n' +
                            f'**Steps**: {ImageProgressAPI.status_text(current_step, total_step) if eta != 0 else "NaN"}\n' +
                            f'**ETA**: {ImageProgressAPI.resize_eta(eta) if eta != 0 else "NaN"}\n\n' +
                            f'Generation {f"will Ends on: <t:{int(time.time() + eta)}:F>" if eta != 0 else "was **Ended**."}',
                color=discord.Color.greyple()
            )

            img = {}
            img_buffer = BytesIO()
            if image:
                image.save(img_buffer, format="JPEG")
                img_buffer.seek(0)
                img = {
                    "file": discord.File(img_buffer, filename=f"current_image_{pharase}.jpg")
                }
            if pharase == 0:
                emb = discord.Embed(
                    title="Parameter & API are Ready!",
                    description=f'**Prompt**: `{img_prompt}`\n'
                )
                emb.set_footer(text="Taken: {:.2f} seconds".format(time.time() - start - 15))
                await interaction.followup.send(
                    content="Generation Started!",
                    embed=emb,
                    **img
                )

            else:
                await interaction.followup.send(
                    content=f"Phase {pharase}: Processing in {pharase * 15} seconds...",
                    embed=embed,
                    **img
                )
            pharase += 1

            #
        img = {}
        img_buffer = BytesIO()
        image = ImageProgressAPI.last_image
        if image:
            image.save(img_buffer, format="JPEG")
            img_buffer.seek(0)
            img = {
                "file": discord.File(img_buffer, filename=f"current_image_{pharase}.jpg")
            }
        await interaction.followup.send(
            content="Generation Finished!",
            embed=discord.Embed(
                description="Elapsed Time: {:.2f} seconds".format(time.time() - start),
            ),
            **img
        )

async def process_command(
        interaction: Interaction,
        image: discord.Attachment,
        model: str,
        steps: int
):
    if not (image.content_type or image.content_type.startswith("image/")):
        await interaction.response.send_message(
            "Please upload an image file",
            ephemeral=True
        )
        return

    buffer = BytesIO()
    img_byte = await image.read()
    buffer.write(img_byte)
    buffer.seek(0)

    image = Image.open(buffer, mode="r")
    api = adetailer_api_for_bot(15)

    # TODO: prompt, negative を指定できるように
    await interaction.response.send_message("preparing API, please wait..")
    await api.bot_generate(interaction, image, model, steps)