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

def init_config():
    config_map = {
        "./config/prompt_placeholder.json": r"""{
  "Colors": {
    "name": "Colors",
    "description": "red,yellowなどの色を@colorに置き換える",
    "version": 1.1,
    "data": {
      "key": "@color",
      "matchTo": [
        "red",
        "yellow",
        "blue",
        "grey",
        "green",
        "purple",
        "pink",
        "orange",
        "white",
        "black",
        "brown",
        "cyan",
        "magenta",
        "teal",
        "lavender",
        "beige",
        "maroon",
        "navy",
        "turquoise",
        "gold",
        "silver",
        "gray",
        "blonde",
        "lime",
        "light blue"
      ],
      "if": {
        "patternTemplate": "\\b{MATCH}\\b",
        "escape": true,
        "flags": [],
        "replace": true,
        "atLeast": 1,
        "refill_after_blacklist": true
      }
    }
  },
  "Eye variations": {
    "name": "Eye variations",
    "description": "e.g. rolling eyes, empty eyes",
    "version": 1.0,
    "data": {
      "version": 1.0,
      "key": "$EYE_VARIATIONS",
      "matchTo": [
        "rolling eyes",
        "empty eyes"
      ],
      "if": {
        "patternTemplate": "^\\s*{MATCH}\\s*$",
        "escape": false,
        "flags": [
          "IGNORECASE"
        ],
        "replace": true,
        "atLeast": 1
      }
    }
  }
}""",
    "./config/prompt_settings/main.json": r"""{
  "blacklist": "boy,penis,lips,abs,fat,1boy,@color hair,@color eyes",
  "black_patterns": "boy\nboys\n^megumin\npublic\neye\ntattoo\nmask\nnails\nnail\ngenshin\narchive\nhonkai\nracco319\nnaruto\nfate\nmargatroid\ntouhou\nkancolle\ninakakko!\nskin\nhakurei\nmahjong\nfriends\nshinozaki\ncoffe-kizoku\nkaburagi\nsample\ntwitter\npixiv\nnushi ma\ncoffee-kizoku\nasterisk\nyoou\nvocaloid\nhanasaku\nhakurei\nspider\nkonosuba\ngranblue fantasy\nhanasakigawa\nfan\nramen\nfrom\nbackground\nholding\ndrinking\ntheme\ncake\ndrink\ndark skin\nasian\ncartoon\nzero\nzero suit\nanother's\nblurry\ncensored\nhetero\numbrella\nbestiality\ncomic\noekaki\ncolored tips\nboy\nman\nmale\nshota\nsaki\ndark\n^\\d+\nteeth\nmultiple\nmulti\npenis\npeeing\nout of frame\nfocus\ngroup\ntail\nsenshi\nwitch\nforehead\npolka dot\nbeads\nneison\nbikini\ngarreg mach monastery\ntop-\ncensor\nmosaic\nimminent\ntan\npregnant\nbun\ngrab\nmiqo\\'te\nlips\nmilitary\nmmf threesome\n\\;\n\\\\\\(fate\\\\\\)$\n\\\\\n\\_",
  "blacklisted_weight": 0,
  "disallow_duplicate": true,
  "use_relative_freq": false,
  "w_min": 1,
  "w_max": 12,
  "w_multiplier": 1.5
}""",
    "./config/bf_settings/main.json": r"""{
  "filter_enable": true,
  "model": "WD1.4 Vit Tagger v3 (large)",
  "threshold": 0.65,
  "character_threshold": 0.45,
  "allow_rating": [
    "general",
    "sensitive",
    "questionable",
    "explicit"
  ],
  "ignore_questionable": true,
  "save_each_rate": false,
  "merge_sensitive": false,
  "general_save_dir": "I:/stable-diffusion-webui-forge\\outputs/txt2img-images/{DATE}-pem/general",
  "sensitive_save_dir": "I:/stable-diffusion-webui-forge\\outputs/txt2img-images/{DATE}-pem/sensitive",
  "questionable_save_dir": "I:/stable-diffusion-webui-forge\\outputs/txt2img-images/{DATE}-pem/questionable",
  "explicit_save_dir": "I:/stable-diffusion-webui-forge\\outputs/txt2img-images/{DATE}-pem/explicit",
  "blacklist": "1boy,no humans,huge breasts,large breasts",
  "pattern_blacklist": "^boy$\n^no human",
  "separate_save": true,
  "blacklist_save_dir": "I:/stable-diffusion-webui-forge/outputs/txt2img-images/pem_blacklisted"
}"""
    }
    for path, content in config_map.items():
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            println(f"Initialized config file at {path}")

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
