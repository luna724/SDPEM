import json
import os
import random
import re
from typing import *

import gradio as gr

import shared
from modules.lora_metadata_util import LoRAMetadataReader
from modules.lora_viewer import LoRADatabaseViewer
from modules.tag_compare import TagCompareUtilities


class LoRAGeneratingUtil(LoRADatabaseViewer):
    def __init__(self):
        super().__init__()
        self.forever_generation = False
        self.tag_compare_util = TagCompareUtilities()

    @staticmethod
    def try_sd_webui_lora_models(only_sft:bool=False) -> list:
        if shared.sd_webui_exists:
            if only_sft:
                return [x for x in os.listdir(
                    os.path.join(shared.a1111_webui_path, "models/Lora")
                )
                        if os.path.splitext(x)[1].lower() == ".safetensors"
                ]
            return os.listdir(os.path.join(shared.a1111_webui_path, "models/Lora"))
        return []

    """
    LoRA safetensors を読み込み、メタデータから tag_frequency のタグ、重みをtagsに梱包して返す
    """
    def get_tag_frequency(self, lora_fn:str, mode:Literal["ss_tag_frequency", "tag_frequency"], only_database_loras: bool = False) -> List[Tuple[str, int]]:
        lora_fns = set()
        if not only_database_loras:
            for f in self.try_sd_webui_lora_models():
                lora_fns.add(os.path.abspath(os.path.join(shared.a1111_webui_path, "models/Lora", f)))
        for f in self.all_lora("fn"):
            lora_fns.add(os.path.abspath(os.path.join(shared.a1111_webui_path, "models/Lora", f)))
        # ^ LoRAリストを作成 (すべては a1111_webui_path にあると想定)

        tags = list()
        for fn in lora_fns:
            if os.path.splitext(os.path.basename(fn))[1].lower() != ".safetensors": continue
            # 拡張子が safetensors なら処理
            if fn != os.path.abspath(os.path.join(shared.a1111_webui_path, "models/Lora", lora_fn)): continue

            if os.path.exists(fn):
                reader = LoRAMetadataReader(fn)
                metadata = reader.metadata or {}
                tags_data = metadata.get(mode, {})
                if isinstance(tags_data, str):
                    try:
                        tags_data = json.loads(tags_data)
                    except json.JSONDecodeError as e:
                        print(f"[ERROR] Failed to parse JSON for {mode} in {fn}: {e}")
                        continue
                #print(tags_data, "\ntype: ", type(tags_data))
                for (k, v) in tags_data.items():
                    if isinstance(v, dict):
                        for (tag, u) in v.items():
                            tags.append((tag, u))
                    elif isinstance(v, int):
                        tags.append((k, v))
        return tags

    def gen_from_lora(self,
                      target_lora:List[str], meta_mode:List[str],
                      blacklists:str, blacklist_multiply:float,
                      weight_multiply:float, target_weight_min:float, target_weight_max:float,
                      use_lora:bool, lora_weight:float, lbw_toggle:bool, max_tags:float, tags_base_chance:float,
                      add_lora_to_last:bool, add_lora_weight:str, disallow_duplicate:bool,
                      header:str, lower:str, threshold: float,
                      ) -> str:
        if len(target_lora) < 1:
            raise gr.Error("No LoRA Selected")
        if len(meta_mode) < 1:
            raise gr.Error("Metadata cannot found")

        ## TODO:
        if use_lora: gr.Warning("use LoRA aren't Supported on v1.0!")

        # 変数の処理
        blacklists = [x.lower() for x in blacklists.split(",") if x.strip() != ""]
        regex_patterns = [re.compile(bl[7:], re.IGNORECASE) for bl in blacklists if bl.startswith("$regex=")]
        includes_patterns = [bl[10:].lower() for bl in blacklists if bl.startswith("$includes=")]
        type_patterns = [bl[6:].lower() for bl in blacklists if bl.startswith("$type=")]

        target_weight_min = int(target_weight_min)
        target_weight_max = int(target_weight_max)
        max_tags = int(max_tags)

        lora_triggers = []
        prompts = []
        # タグリストの取得
        tags:List[Tuple[str, int]] = list()
        for lora in target_lora:
            # LoRAの取得
            path = os.path.abspath(os.path.join(shared.a1111_webui_path, "models/Lora", lora))
            if os.path.exists(path):
                reader = LoRAMetadataReader(path)
                trigger = reader.get_output_name()
                if not trigger is None:
                    lora_triggers.append(f"<lora:{trigger}:{add_lora_weight}>")
            for meta in meta_mode:
                for tag in self.get_tag_frequency(lora, meta):
                    tags.append(tag)

        # 重み再調整
        resized_tags = list()
        for (tag, weight) in tags:
            if tag.lower() in blacklists or \
                any(pattern.search(tag) for pattern in regex_patterns) or \
                any(include in tag.lower() for include in includes_patterns) or \
                self.tag_compare_util.check_typo_multiply(tag.lower(), type_patterns, threshold):
                    weight *= blacklist_multiply

            if target_weight_min <= weight <= target_weight_max:
                weight *= weight_multiply
            weight /= (100*tags_base_chance)

            #print(f"Adjusted weight for tag '{tag}': {weight}")
            if weight > 0:
                resized_tags.append((tag, weight))
        def get_weight(t): return t[1]
        resized_tags = sorted(resized_tags, key=get_weight)

        # プロンプト構築
        if len(resized_tags) < 1 or (disallow_duplicate and len(resized_tags) < max_tags):
            raise gr.Error("tags not found")
        while len(prompts) < max_tags:
            for (tag, weight) in resized_tags:
                if len(prompts) >= max_tags:
                    break
                if random.random() < weight and (not disallow_duplicate or not tag in prompts):
                    if random.random() < 0.05: # 5% でプロンプトに重みづけ
                        tag = f"({tag}:{random.randrange(1, 160, 1)/100})" #崩壊しない範囲
                    prompts.append(tag)

        if not add_lora_to_last:
            lora_triggers = []
        prompts = [h.strip() for h in header.split(",") if h.strip() != ""] + prompts + lora_triggers + [l.strip() for l in lower.split(",") if l.strip() != ""]
        return ", ".join(prompts)