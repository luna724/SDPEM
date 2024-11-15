import os

from jsonutil import JsonUtilities, BuilderConfig

"""
まず存在するかどうかを探す
"""
def search_sd_webui_at1() -> bool:
    builderConfig = BuilderConfig()
    builderConfig.required=False
    json = JsonUtilities("./a1111_webui_pth.json", builderConfig)
    if not json.loadable:
        return False

    data = json.read()
    if data is None:
        return False

    path = data["path"]
    if os.path.exists(path) and os.path.isdir(path):
        return True