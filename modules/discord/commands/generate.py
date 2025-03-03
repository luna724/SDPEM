import asyncio
import discord
import time

from io import BytesIO
from discord import Interaction

from modules.api.txt2img import txt2img_api
from modules.generation_param import get_generation_param
from modules.image_progress import ImageProgressAPI
from modules.prompt_alias import PromptAlias

class txt2img_api_for_bot(txt2img_api):
    async def bot_generate(self, prompt: str, interaction: discord.Interaction, **override_payload):
        start = time.time()
        param = get_generation_param()
        payload = {
                      "prompt": prompt,
                      "negative_prompt": param.negative_prompt,
                      "seed": int(param.seed),
                      "scheduler": "Automatic",
                      "batch_size": int(param.batch_size),
                      "n_iter": 1,
                      "cfg_scale": param.cfg_scale,
                      "width": int(param.width),
                      "height": int(param.height),
                      "restore_faces": param.restore_face,
                      "tiling": param.tiling,
                      "denoising_strength": param.denoising_strength,
                      "enable_hr": False,
                      "override_settings": {
                          "CLIP_stop_at_last_layers": int(param.clip_skip),
                      },
                      "alwayson_scripts": {
                          "ADetailer": {
                              "args": [
                                  True,
                                  False,
                                  {
                                      "ad_model": param.adetailer_model_1st,
                                      "ad_prompt": param.adetailer_prompt,
                                      "ad_negative_prompt": param.adetailer_negative,
                                      "ad_denoising_strength": param.denoising_strength
                                  }
                              ]
                          }
                      }
                  } | override_payload

        future = self.executor.submit(self._txt2img_api, payload)
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

            for _ in range(25):
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
                await interaction.followup.send(
                    content="Generation Started!",
                    embed=discord.Embed(
                        title="Parameter & API are Ready!",
                        description=f'**Prompt**: `{prompt}`\n'
                    ),
                    **img
                )

            else:
                await interaction.followup.send(
                    content=f"Phase {pharase}: Processing in {pharase * 25} seconds...",
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


async def process_command(interaction: Interaction, prompt: str, **payload):
    api = txt2img_api_for_bot(15)

    # TODO: Promptのヘッダーを指定できるように

    prompt = PromptAlias().process_command(prompt)
    prompt = "score_9, score_8_up, score_7_up, best quality, masterpiece, BREAK\n"+prompt
    await interaction.response.send_message("preparing API, please wait..")
    await api.bot_generate(prompt, interaction, **payload)
    return