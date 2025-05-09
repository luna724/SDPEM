import asyncio
import discord
import time

from io import BytesIO
from discord import Interaction, app_commands, Embed
from discord.ext.commands import Cog

from modules.api.txt2img import txt2img_api
from modules.discord.perm import PermissionManager
from modules.generation_param import get_generation_param
from modules.image_progress import ImageProgressAPI
from modules.image_util import ImageUtil
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

        emb = discord.Embed(
            title="Parameter & API are Ready!",
            description=f'**Prompt**: `{prompt}`\n'
        )
        emb.set_footer(text="Taken: {:.2f} seconds".format(time.time() - start))
        await interaction.followup.send(embed=emb)

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

            image = ImageUtil(image)
            img = {}
            if image:
                img = {
                    "file": image.to_file()
                }

            await interaction.followup.send(
                content=f"Phase {pharase}: Processing in {pharase * 25} seconds...",
                embed=embed,
                **img
            )
            pharase += 1

        #
        img = {}
        image = ImageProgressAPI.get_last_grid()
        if image:
            img = {
                "file": image.to_file()
            }
        await interaction.followup.send(
            content="Generation Finished!",
            embed=discord.Embed(
                description="Elapsed Time: {:.2f} seconds".format(time.time() - start),
            ),
            **img
        )

class Generate(Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.describe(
    )
    @app_commands.command(
        name="generate",
        description="Generate image from prompt",
    )
    @PermissionManager()
    async def generate(
            self,
            interaction: Interaction, *, prompt: str,
            batch_size: int = None,
            width: int = None,
            height: int = None,
            denoising_strength: float = None,
            auto_header: bool = False
    ):
        await interaction.response.defer()
        payload = {
            "do_not_save_samples": True,
            "save_images": True
        }
        if batch_size is not None: payload["batch_size"] = batch_size
        if width is not None: payload["width"] = width
        if height is not None: payload["height"] = height
        if denoising_strength is not None: payload["denoising_strength"] = denoising_strength

        api = txt2img_api_for_bot(15)

        prompt = PromptAlias().process_command(prompt)
        if auto_header:
            prompt = "score_9, score_8_up, score_7_up, best quality, masterpiece, BREAK\n" + prompt
        await interaction.followup.send("preparing API, please wait..")
        await api.bot_generate(prompt, interaction, **payload)
        return

async def setup(bot: discord.ext.commands.Bot):
    await bot.add_cog(Generate(bot))