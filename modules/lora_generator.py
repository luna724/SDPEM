import base64
import io
import json
import os
import random
import re
import time
from datetime import datetime
from typing import *

import PIL.Image
import gradio as gr
from safetensors.torch import safe_open

import shared
from modules import deepbooru
from modules.api.txt2img import txt2img_api
from modules.lora_metadata_util import LoRAMetadataReader
from modules.lora_viewer import LoRADatabaseViewer
from modules.tag_compare import TagCompareUtilities
from modules.yield_util import new_yield


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
                metadata = reader.metadata
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

    """Generate Forever"""
    def generate_forever(
            self,
            target_lora, meta_mode, blacklists, blacklist_multiply,
            weight_multiply, target_weight_min, target_weight_max,
            use_lora, lora_weight, lbw_toggle, max_tags, tags_base_chance,
            add_lora_to_last, adding_lora_weight, disallow_duplicate, header,
            lower, threshold, separate_blacklist, bcf_blacklist, booru_threshold,
            bcf_dont_discard, bcf_invert, bcf_filtered_path, bcf_enable,
            ## above ^ gen_from_lora options ^ above
            ## below v txt2img options v below
            negative, ad_prompt, ad_negative, sampling_method, step_min, step_max,
            cfg_scale, width, height, bcount, bsize, seed, hires_step,
            denoising, hires_sampler, upscale_by, restore_face, tiling, clip_skip,
            ad_model, ui_port
    ) -> str:
        gr.Info("Generation Forever started!")
        # デフォルトペイロードを定義
        txt2img = txt2img_api(int(ui_port),
            **{
                "negative_prompt": negative,
                "seed": int(seed),
                "scheduler": "Automatic",
                "batch_size": int(bsize),
                "n_iter": int(bcount),
                "cfg_scale": int(cfg_scale),
                "width": int(width),
                "height": int(height),
                "restore_faces": restore_face,
                "tiling": tiling,
                "denoising_strength": denoising,
                "enable_hr": hires_step != 0,
                "hr_scale": upscale_by,
                "hr_upscaler": hires_sampler,
                "override_settings": {
                    "CLIP_stop_at_last_layers": int(clip_skip),
                },
                "alwayson_scripts": {
                    "ADetailer": {
                        "args": [
                            True,
                            False,
                            {
                                "ad_model": ad_model,
                                "ad_prompt": ad_prompt,
                                "ad_negative_prompt": ad_negative,
                                "ad_denoising_strength": denoising
                            }
                        ]
                    }
                }
            }
        )

        if separate_blacklist:
            booru_blacklists = [x.lower() for x in bcf_blacklist.split(",") if x.strip() != ""]
            booru_regex_patterns = [re.compile(bl[7:], re.IGNORECASE) for bl in booru_blacklists if
                                    bl.startswith("$regex=")]
            booru_includes_patterns = [bl[10:].lower() for bl in booru_blacklists if bl.startswith("$includes=")]
            booru_type_patterns = [bl[6:].lower() for bl in booru_blacklists if bl.startswith("$type=")]
        else:
            booru_blacklists = [x.lower() for x in blacklists.split(",") if x.strip() != ""]
            booru_regex_patterns = [re.compile(bl[7:], re.IGNORECASE) for bl in blacklists if bl.startswith("$regex=")]
            booru_includes_patterns = [bl[10:].lower() for bl in blacklists if bl.startswith("$includes=")]
            booru_type_patterns = [bl[6:].lower() for bl in blacklists if bl.startswith("$type=")]

        # BCF出力パスがないのに Don't Discard がオンなら、デフォルトフォルダを使用
        if bcf_enable and bcf_dont_discard and bcf_filtered_path == "":
            bcf_filtered_path = os.path.join(shared.a1111_webui_path, "outputs/txt2img-images/bcf-filtered")
        os.makedirs(bcf_filtered_path, exist_ok=True)

        if step_min > step_max:
            raise gr.Error("step MIN > step MAX is not allowed.")
        if len(sampling_method) == 0:
            raise gr.Error("Please select sampling method (at least one)")

        # ユーザーが止めるまで
        sent_text = new_yield("[Forever-Generation]: ", max_line=200)
        yield sent_text("Starting..")
        self.forever_generation = True
        while self.forever_generation:
            try:
                prompt = self.gen_from_lora(
                    target_lora, meta_mode, blacklists, blacklist_multiply,
                    weight_multiply, target_weight_min, target_weight_max,
                    use_lora, lora_weight, lbw_toggle, max_tags, tags_base_chance,
                    add_lora_to_last, adding_lora_weight, disallow_duplicate, header,
                    lower, threshold
                )
            except gr.Error as e:
                self.forever_generation = False
                gr.Warning("Current randomization options are incorrect. Forever Generations stopped.")
                return str(e)

            yield sent_text("Prompt successfully Created.")
            steps = random.randrange(step_min, step_max+1, 1)
            sampler = random.choice(sampling_method)
            print(f"[INFO]: Processing for prompt ({prompt})")
            yield sent_text("Started generation with option\n"+f"Prompt: {prompt}\nSteps: {steps} | Sampler: {sampler}")
            response = txt2img.generate(**{"prompt": prompt, "steps": steps, "sampler_name": sampler})
            yield sent_text("Generation finished. validating images..")
            print("[INFO]: Generation finished.")

            formatted_date = datetime.now().strftime("%Y-%m-%d")
            output_dir = os.path.join(
                shared.a1111_webui_path, f"outputs/txt2img-images/{formatted_date}"
            )
            os.makedirs(output_dir, exist_ok=True)
            infotxt = response.get("info")
            param = json.loads(infotxt)
            default_seed = param["seed"]
            for (index, image) in enumerate(response.get("images")):
                fc = len([x for x in os.listdir(output_dir) if os.path.splitext(x)[1].lower() == ".png"])
                current_seed = default_seed + index
                fn = f"{fc + 1:05d}-{current_seed}.png"
                save_path = os.path.join(
                    output_dir, fn
                )

                discard_flag = False

                if bcf_enable:
                    yield sent_text("Starting Deepbooru checking..")
                    pil_image = PIL.Image.open(
                        io.BytesIO(base64.b64decode(image))
                    )
                    booru_outputs = deepbooru.default.interrogate(
                        pil_image, booru_threshold
                    )
                    booru_keys = list(booru_outputs.keys())
                    yield sent_text(f"Deepbooru outputs: {', '.join(booru_keys)}")
                    for booru_key in booru_keys:
                        # ブラックリストに設定されていたら
                        if (booru_key.lower() in booru_blacklists or
                                any(pattern.search(booru_key) for pattern in booru_regex_patterns) or
                                any(include in booru_key.lower() for include in booru_includes_patterns) or
                                self.tag_compare_util.check_typo_multiply(booru_key.lower(), booru_type_patterns, threshold)):
                            yield sent_text(f"Image Blacklisted by. {booru_key}")
                            if not bcf_invert:
                                # 反転オフ
                                # 設定されている + 破棄設定
                                if not bcf_dont_discard:
                                    discard_flag = True
                                    break
                                    # 保存せず無視
                                else:
                                    # 特定ディレクトリに保存
                                    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
                                    for char in invalid_chars:
                                        booru_key = booru_key.replace(char, '_')
                                    save_path = os.path.join(
                                        bcf_filtered_path, fn + f" - {booru_key}.png"
                                    )
                                    break
                            else:
                                # 反転オン
                                # 設定されている場合はパス、設定されていないなら消す
                                break
                        elif bcf_invert:
                            yield sent_text(f"Image Whitelisted (not matched & Inverted)")
                            # ブラックリストに設定されていないが、反転がオンなら
                            if not bcf_dont_discard:
                                discard_flag = True
                                break
                                # 保存せず無視
                            else:
                                invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
                                for char in invalid_chars:
                                    booru_key = booru_key.replace(char, '_')
                                save_path = os.path.join(
                                    bcf_filtered_path, fn + f" - {booru_key}.png"
                                ) # ディレクトリ変更
                                break
                        continue
                    yield sent_text(f"Deepbooru checking finished.\nStatus: discard_flag: {discard_flag} | save_path: {save_path}")
                    if discard_flag:
                        continue # 破棄ならパス
                # BCFがオフ、または破棄しない設定ならディレクトリ変更後、股は普通のフォルダでセーブを実行
                with open(save_path, "wb") as file:
                    file.write(base64.b64decode(image))
                yield sent_text(f"saving image to {save_path}")
            print(f"[INFO]: Processed for prompt ({prompt})")
            if not self.forever_generation:
                break
            yield sent_text("refreshing session...")
            time.sleep(1)
        gr.Info("Forever Generation Stopped!")
        print("[INFO]: Generation Forever ended.")
        yield "Generation Forever Stopped."