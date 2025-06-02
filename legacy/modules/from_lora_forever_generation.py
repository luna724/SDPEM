import gradio as gr
import os
import re
import random
import io
import PIL.Image
import base64
import hashlib
import json
import time

from typing import *
from datetime import datetime

import shared
from modules.models import deepbooru
from modules.api.txt2img import txt2img_api
from modules.generation_param import get_generation_param
from modules.image_progress import ImageProgressAPI
from modules.lora_generator import LoRAGeneratingUtil
from modules.text_generate import ImageGeneration
from modules.yield_util import new_yield

# from LoRA / Generate Forever のコード
# めっちゃ中心部みたいなもんだから保守的に書けよ？

class FromLoRAForeverGeneration(ImageGeneration, LoRAGeneratingUtil):
    def __init__(self):
        ImageGeneration.__init__(self)
        LoRAGeneratingUtil.__init__(self)
        self.forever_generation = False
        self.sent_text = None

    @staticmethod
    def filter_prompt(p: str, replace: str):
        return [
            x[len(replace):].lower()
            for x in p.split(",") if x.strip() != ""
            if x.startswith(replace)
        ]


    def generate_forever(
            self,
            target_lora,
            meta_mode,
            blacklists,
            blacklist_multiply,
            weight_multiply,
            target_weight_min,
            target_weight_max,
            use_lora,
            lora_weight,
            lbw_toggle,
            max_tags,
            tags_base_chance,
            add_lora_to_last,
            adding_lora_weight,
            disallow_duplicate,
            header,
            lower,
            threshold,
            separate_blacklist,
            bcf_blacklist,
            booru_threshold,
            bcf_dont_discard,
            bcf_invert,
            bcf_filtered_path,
            bcf_enable,
            ## above ^ gen_from_lora options ^ above
            ## below v txt2img options v below
            refresh_rate, dont_discard_interrupted_image
    ) -> Any:
        param = get_generation_param()
        gr.Info("Generation Forever started!")
        self.override_payload( # 実行のたびに初期化
            **{
                "negative_prompt": param.negative_prompt,
                "seed": int(param.seed),
                "scheduler": "Automatic",
                "batch_size": int(param.batch_size),
                "n_iter": 1,
                "cfg_scale": param.cfg_scale,
                "width": int(param.width),
                "height": int(param.height),
                "restore_faces": param.restore_face,
                "tiling": param.tiling,
                "denoising_strength": param.denoising_strength,
                "enable_hr": False,
                "override_settings": {
                    "CLIP_stop_at_last_layers": int(param.clip_skip),
                },
                "alwayson_scripts": {
                    "ADetailer": {
                        "args": [
                            True,
                            False,
                            {
                                "ad_model": param.adetailer_model_1st,
                                "ad_prompt": param.adetailer_prompt,
                                "ad_negative_prompt": param.adetailer_negative,
                                "ad_denoising_strength": param.denoising_strength,
                                "ad_use_steps": True,
                                "ad_steps": 28,
                            }
                        ]
                    }
                }
            }
        )

        # デフォルトペイロードを定義
        txt2img = txt2img_api(refresh_rate, **self.default_payload)

        if separate_blacklist:
            booru_blacklists = [x.lower() for x in bcf_blacklist.split(",") if x.strip() != ""]
            booru_regex_patterns = [re.compile(bl[7:], re.IGNORECASE) for bl in booru_blacklists if bl.startswith("$regex=")]
            booru_includes_patterns = self.filter_prompt(bcf_blacklist, "$includes=")
            booru_type_patterns = self.filter_prompt(bcf_blacklist, "$type=")

        else:
            booru_blacklists = [x.lower() for x in blacklists.split(",") if x.strip() != ""]
            booru_regex_patterns = [re.compile(bl[7:], re.IGNORECASE) for bl in blacklists if bl.startswith("$regex=")]
            booru_includes_patterns = self.filter_prompt(blacklists, "$includes=")
            booru_type_patterns = self.filter_prompt(blacklists, "$type=")

        # BCF出力パスがないのに Don't Discard がオンなら、デフォルトフォルダを使用
        if bcf_enable and bcf_dont_discard and bcf_filtered_path == "":
            bcf_filtered_path = os.path.join(shared.a1111_webui_path, "outputs/txt2img-images/bcf-filtered")
        os.makedirs(bcf_filtered_path, exist_ok=True)

        if param.sampling_steps_min > param.sampling_steps_max:
            raise gr.Error("step MIN > step MAX is not allowed.")
        if len(param.sampling_method) == 0:
            raise gr.Error("Please select sampling method (at least one)")

        # ユーザーが止めるまで
        self.sent_text = new_yield("[Forever-Generation]: ", max_line=200)
        empty = ("N/A", "N/A", None, ImageProgressAPI.progress_bar_html(0, -1), False)
        final_value = empty
        yield self.sent_text("Starting.."), *empty

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

            yield self.sent_text("Prompt successfully Created."), *empty
            steps = random.randrange(param.sampling_steps_min, param.sampling_steps_max + 1, 1)
            sampler = random.choice(param.sampling_method)
            print(f"[INFO]: Processing for prompt ({prompt})")
            yield self.sent_text(
                "Started generation with option\n" + f"Prompt: {prompt}\nSteps: {steps} | Sampler: {sampler}"), ImageProgressAPI.status_text(
                0, steps), "N/A", None, ImageProgressAPI.progress_bar_html(0, -1), False
            response, final_value = yield from txt2img.generate(self, **{"prompt": prompt, "steps": steps,
                                                                         "sampler_name": sampler}) # type: ignore
            interrupted = final_value[4]
            if interrupted:
                if not dont_discard_interrupted_image:
                    yield self.sent_text("Detected Interrupt, skip saving.."), *final_value
                    continue

            yield self.sent_text("Generation finished. validating images.."), *final_value
            print("[INFO]: Generation finished.")

            try:
                formatted_date = datetime.now().strftime("%Y-%m-%d")
                output_dir = os.path.join(
                    shared.a1111_webui_path, f"outputs/txt2img-images/{formatted_date}"
                )
                os.makedirs(output_dir, exist_ok=True)
                infotxt = response.get("info")
                out_param = json.loads(infotxt)
                default_seed = out_param["seed"]
                for (index, image) in enumerate(response.get("images")):
                    fc = len([x for x in os.listdir(output_dir) if os.path.splitext(x)[1].lower() == ".png"])
                    current_seed = default_seed + index
                    fn = f"{fc + 1:05d}-{current_seed}.png"
                    save_path = os.path.join(
                        output_dir, fn
                    )

                    discard_flag = False

                    if bcf_enable:
                        yield self.sent_text("Starting Deepbooru checking.."), *final_value
                        pil_image = PIL.Image.open(
                            io.BytesIO(base64.b64decode(image))
                        )
                        booru_outputs = deepbooru.default.interrogate(
                            pil_image, booru_threshold
                        )
                        booru_keys = list(booru_outputs.keys())
                        yield self.sent_text(f"Deepbooru outputs: {', '.join(booru_keys)}"), *final_value
                        for booru_key in booru_keys:
                            # ブラックリストに設定されていたら
                            if (booru_key.lower() in booru_blacklists or
                                    any(pattern.search(booru_key) for pattern in booru_regex_patterns) or
                                    any(include in booru_key.lower() for include in booru_includes_patterns) or
                                    self.tag_compare_util.check_typo_multiply(booru_key.lower(), booru_type_patterns,
                                                                              threshold)):
                                yield self.sent_text(f"Image Blacklisted by. {booru_key}"), *final_value
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
                                yield self.sent_text(f"Image Whitelisted (not matched & Inverted)"), *final_value
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
                                    )  # ディレクトリ変更
                                    break
                            continue
                        yield self.sent_text(
                            f"Deepbooru checking finished.\nStatus: discard_flag: {discard_flag} | save_path: {save_path}"), *final_value
                        if discard_flag:
                            continue  # 破棄ならパス
                    # BCFがオフ、または破棄しない設定ならディレクトリ変更後、股は普通のフォルダでセーブを実行
                    with open(save_path, "wb") as file:
                        file.write(base64.b64decode(image))
                    yield self.sent_text(f"saving image to {save_path}"), *final_value

            except Exception as e:
                # 後処理に失敗したら一時フォルダに保存する
                yield self.sent_text("Error occurred in saving image!"), *final_value
                for (index, image) in enumerate(response.get("images")):
                    pil_image = PIL.Image.open(
                        io.BytesIO(base64.b64decode(image))
                    )
                    image_hash = hashlib.sha256(pil_image.tobytes()).hexdigest()
                    pil_image.save(
                        os.path.join(os.getcwd(), "temp", f"{image_hash}.png")
                    )
                self.forever_generation = False  ## TODO: 強制停止のオンオフ
                gr.Warning("Forever Generation Stopped!")
                raise e

            print(f"[INFO]: Processed for prompt ({prompt})")
            if not self.forever_generation:
                break
            yield self.sent_text("refreshing session..."), *final_value
            time.sleep(1)
        gr.Info("Forever Generation Stopped!")
        print("[INFO]: Generation Forever ended.")
        yield "Generation Forever Stopped.", *final_value