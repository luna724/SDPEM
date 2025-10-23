import os, json, shared, requests
import shutil
from utils import *
from huggingface_hub import hf_hub_download


class ModelInstaller:
    def __init__(self, base_path: str, schema: dict):
        self.base_path = base_path
        self.schema = schema

    def parse(self, item: dict) -> dict:
        """初期値を定義"""
        return self.schema.copy() | item

    def download(self, item: dict) -> bool:
        i = self.parse(item)
        model_path = os.path.join(self.base_path, i["fn"])
        typ = i.get("type")
        if typ == "hf.co":
            try:
                if os.path.exists(model_path):
                    return True

                fp = hf_hub_download(
                    repo_id=i["url"].split(":")[0],
                    filename=i["url"].split(":")[1],
                    cache_dir=self.base_path,
                    local_dir=self.base_path,
                    local_dir_use_symlinks=False,
                )
                shutil.copy(fp, model_path)
                shutil.rmtree(fp, ignore_errors=True)
                println(f"Downloaded {i['fn']} to {model_path}")

                depend = i.get("depend", [])
                if depend is not None and len(depend) > 0:
                    println(f"Installing dependencies for {i['fn']}..")
                    for dep in depend:
                        result = self.download(dep)
                        if not result:
                            critical(
                                f"Failed to install dependency {dep['fn']} for {i['fn']}"
                            )
                            raise Exception(
                                f"Failed to install dependency {dep['fn']} for {i['fn']}"
                            )
                        else:
                            self.register("_dependencies", dep)
                        continue
                return True
            except Exception as e:
                critical(f"Failed to download {i['fn']} from {i['url']}: {e}")
                return False
        return False

    def register(self, model_index: str, item: dict) -> None:
        """モデルをshared.modelsに登録する"""
        i = self.parse(item)
        model_path = os.path.join(self.base_path, i["fn"])
        if not model_index in shared.models:
            shared.models[model_index] = []
        shared.models[model_index].append(
            {
                "fn": i["fn"],
                "path": model_path,
                "display_name": i.get("name", i["fn"]),
                "sig": i.get("signature", "?"),
            }
        )
        println(f"Registered model {i['name']} at {model_path}")

def init_character_models():
    data_url = "https://files.catbox.moe/6holoy.json"
    data_dir = "./models/characters.json"
    println("Downloading waidb characters..")
    if os.path.exists(data_dir):
        return
    rsp = requests.get(data_url, timeout=180, headers={ 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    if rsp.status_code == 200:
        data = rsp.json()
        data["proj"] = [
            {
                "kv": k["kv"],
                "title": k["title"],
            }
            for k in data["proj"]
        ]
        
        with open(data_dir, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        println(f"Downloaded waidb characters")
    else:
        critical(f"Failed to download waidb characters: {rsp.status_code}")
        # rsp.raise_for_status()


def init_models():
    model_index_path = os.path.join(os.getcwd(), "models/index.json")
    if not os.path.exists(model_index_path):
        print(
            f"Model index file not found at {model_index_path}. Please ensure the file exists."
        )
        return

    os.makedirs(os.path.join(os.getcwd(), "models/prompts"), exist_ok=True)
    with open(model_index_path, "r") as f:
        model_index = json.load(f)

    indexes = model_index["index"]
    values = model_index["values"]

    for index in indexes:
        for value in values:
            if value["name"] != index:
                continue
            schema = value.get("schema", {})
            installer = ModelInstaller(
                os.path.join(os.getcwd(), "models", index), schema
            )
            for item in value.get("items", []):
                ok = installer.download(item)
                if ok:
                    installer.register(index, item)

    # print_critical(shared.models)
    init_character_models()
