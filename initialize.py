import os

import chromedriver_autoinstaller

import shared
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
        shared.a1111_webui_path = path
        return True

def auto_install_chromedriver_for_selenium():
    os.makedirs(os.path.join(os.getcwd(), "bin"), exist_ok=True)
    return chromedriver_autoinstaller.install(path=os.path.join(
        os.getcwd(), "bin"
    ))

def load_default_model():
    bcfg = BuilderConfig()
    bcfg.required = False
    json = JsonUtilities("./default_model.json", bcfg)
    if not json.loadable:
        return None

    data = json.read()
    if data is None:
        return None

    return data

def file_cleaner():
    if os.path.exists("cc.en.300.bin.gz"):
        os.remove("cc.en.300.bin.gz")
    if os.path.exists("GoogleNews-vectors-negative300.bin.gz"):
        os.remove("GoogleNews-vectors-negative300.bin.gz")