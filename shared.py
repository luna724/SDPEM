from argparse import Namespace
from asyncio import AbstractEventLoop
import asyncio
from typing import Optional

from modules.generation_param import GenerationParameterDefault

sd_webui_exists: bool = False
driver_path: str = ""
a1111_webui_path: str = ""
refresh_button = "🔄"
circular_button = "🔁"
select_all_button = "📦"
browse_directory = "📁"
reverse_button = "⇅"
browse_file = "📄"
check_mark = "✅"
ui_obj: dict = {}
gen_param: GenerationParameterDefault = GenerationParameterDefault()
model_file: dict = {}

loop: AbstractEventLoop = asyncio.new_event_loop()
args: Optional[Namespace] = None
jsk = None # modules.discord.jsk.py:Jishaku

## BETA Opts
# 1. Deepbooru don't keep models in memory
deepbooru_dont_keep_models_in_ram = True
