from argparse import Namespace

sd_webui_exists: bool = False
driver_path: str = ""
a1111_webui_path: str = ""
refresh_button = "🔄"
circular_button = "🔁"
select_all_button = "📦"
ui_obj: dict = {}
model_file: dict = {}

args: Namespace = None

## BETA Opts
# 1. Deepbooru don't keep models in memory
deepbooru_dont_keep_models_in_ram = True