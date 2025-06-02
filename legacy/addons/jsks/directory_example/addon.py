from modules.discord.jsk import JishakuAddon

from discord.ext import commands
from discord import Message

from modules.static_generator import StaticGenerator


class StaticTemplateList(JishakuAddon):
    def __call__(self, bot: commands.Bot):
        @bot.command("static_template_list2")
        async def __static_template_lists(ctx: commands.Context):
            static_templates = StaticGenerator()
            lists = list(static_templates.load().keys())

            await ctx.send(
                f"Current Static templates list2: \n```{', '.join(lists)}```"[:4000]
            )

    @staticmethod  # Staticmethod are optional
    async def on_message(message: Message):
        """
        if message.author == bot.use: return
        aren't needed
        """
        if "owo" in message.content:
            await message.channel.send(f"owo")
