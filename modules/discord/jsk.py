import importlib
import discord
import os
from discord import app_commands
from discord.ext import commands

from jsonutil import JsonUtilities
import shared
from modules.discord.commands.register_slash import register_slash_commands


class Jishaku:
    def __init__(self):
        f = self.token_file()

        self.token: str|None = None
        self.bot: commands.Bot = None
        self.addons: list = []

        self.guild: discord.Object | None  = None
        if f["guild"] is not None: self.guild = discord.Object(f["guild"])
        self.prefix = f["prefix"]

    @staticmethod
    def token_file() -> dict:
        token_file = JsonUtilities(os.path.join(os.getcwd(), "bot_token.json"))
        return token_file.read()

    def obtain_token(self) -> str|None:
        data = self.token_file()
        token_data: str = data["token"]

        token = ""
        if not token_data.startswith("PATH?="):
            token = token_data

        else:
            path = token_data.replace("PATH?=", "").strip()
            token = os.environ.get(path)
            if token is None:
                token = ""

        # tokenを処理
        token = token.strip()
        if token.count(".") != 2:
            print("[WARN]: jsk bot tokens invalidate. please re-check token")
            return None

        else:
            print("[INFO]: jsk bot tokens validate!")
            self.token = token
            return token

    def start_jsk(self):
        print("[Jishaku]: Starting jsk bot...")
        token = self.obtain_token() or self.token
        if token is None:
            print("[Jishaku]: Bot token invalidate.")
            return

        print(f"[Jishaku]: Bot token obtained: {token[:10]}...")

        intents = discord.Intents.default()
        intents.message_content = True # メッセージの内容にアクセス可能にする
        self.bot = commands.Bot(command_prefix=self.prefix, intents=intents)

        self.register_commands()
        print("[Jishaku]: bot starting..")
        self.bot.run(token)

    def register_commands(self):
        self.register_external_commands()
        register_slash_commands(self.bot, self.guild)
        bot = self.bot

        @bot.event
        async def setup_hook():
            await bot.load_extension("jishaku")

        @bot.event
        async def on_ready():
            await self.bot.tree.sync(guild=self.guild)
            print(f'[Jishaku]: Logged in as {bot.user} (ID: {bot.user.id})')

        @bot.event
        async def on_message(message: discord.Message):
            if message.author == bot.user:
                return
            print(f"[Jishaku]: received message: {message.content}")
            await self.external_on_message(message)

            if "<@1314671674242633738>" in message.content:
                await message.channel.send(f"owo, {message.author}\ni'm running on [SD-PEM Client](https://github.com/luna724/SDPEM).")

            await bot.process_commands(message)

            if "pem.jsk" in message.content:
                print("[Jishaku]: called pem.jsk")
                await message.channel.send("SD-PEM Client β5.0-{commit_hash}")

        self.bot = bot
        return

    def register_external_commands(self):
        addon_class = []
        files = [
            file for file in os.listdir(
                os.path.join(os.getcwd(), "addons/jsks")
            )
            if (file.endswith(".py") and not os.path.isdir(file)) #or (os.path.isdir(file) and os.path.exists(os.path.join(os.getcwd(), "addons/jsks", file, "addon.py")))
        ]
        for f in files:
            f = f[:-3]
            module = importlib.import_module(f"addons.jsks.{f}")
            attrs = module.__dict__
            TabClass = [
                x for x in attrs.values()
                if isinstance(x, type) and issubclass(x, JishakuAddon) and not x == JishakuAddon
            ]

            if len(TabClass) > 0:
                addon_class.append(TabClass[0]())

        self.addons = addon_class
        for addon in self.addons:
            addon(self.bot) # __call__4

    async def external_on_message(self, message):
        for addon in self.addons:
            await addon.on_message(message)

class JishakuAddon:
    """ extend this """
    def __call__(self, bot: commands.Bot):
        """Override this"""
        pass

    @staticmethod
    async def on_message(message: discord.Message):
        """Override this"""
        pass

runned: bool = False
def start_jsk():
    global runned
    if runned:
        print("[Jishaku]: Jishaku already called.")
        return

    print("[Jishaku]: Initializing...")
    runned = True
    shared.jsk = Jishaku()

    # この関数を非同期で動かしたい
    shared.jsk.start_jsk()