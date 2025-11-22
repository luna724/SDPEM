import asyncio
import base64
from io import BytesIO
from itertools import chain
import json
import os
import re
import time
import traceback
from typing import *
import gradio as gr
import random
from PIL import Image, PngImagePlugin

from modules.adetailer import ADetailerAPI, ADetailerResult
from modules.generate import GenerationProgress, GenerationResult, Txt2imgAPI
from modules.tagger.predictor import OnnxRuntimeTagger
from modules.utils.exceptions import notEnoughTag
from modules.utils.pnginfo import make_info
from modules.utils.state import StateManager
from modules.utils.timer import TimerInstance
from modules.utils.util import sha256
from modules.forever_generation import ForeverGeneration
from modules.prompt_setting import setting
from modules.prompt_processor import PromptProcessor
from modules.forever.common import ForeverGenerationTemplate
import shared
from utils import *

# RP無効化 ./common.py に対応

# TODO: @Codex
STATE = None # TODO: ForeverGenerationFromLoRAの現在の状況を保持、外部にストリームするための関数
# /modules/api/v1/bot/forever_from_lora.py で使用される予定
# 仕様自体は複数インスタンス対応してもいいが、どんな強靭なGPU使ってんのって話になるから単一保持の予定 (最新のインスタンスを保持する)

# ForeverGeneration instanceは tab/.. によって保持され生涯有効
class ForeverGenerationFromLoRA(ForeverGenerationTemplate):
    def __init__(self, payload: dict | None = None) -> None:
        super().__init__({})
        self.output = ""
        self.payload = {}
        self.param = {}
        self.default_prompt_request_param = {}
        self.processor_prompt_param = {}
        self.adetailer_param = {}
        self.freeu_param = {}
        self.regional_prompter_param_default = {}
        self.neveroom_param = {}
        self.sag_param = {}

        self.sampling_methods: list[str]
        self.schedulers: list[str]
        self.auto_cast_scheduler = False
        self.steps: tuple[int, int]
        self.cfg_scales: tuple[float, float]
        self.sizes: list[tuple[int, int]]
        self.lora_names: list[str]
        self.disable_lora_in_adetailer: bool
        self.rp_matrix_mode: list[str]
        self.rp_enabled: bool
        self.rp_calculation: list[str]
        self.divine_ratio: list[str]
        self.rp_auto_res: bool
        self.rp_canvas_res: list[tuple[int, int]] = []
        
        self.adetailer: bool
        self.separate_adetailer: bool = True

        self.n_of_img = 2140000000
        self.image_skipped = False
        self.skipped_by = "User"
        
        self.booru_blacklist: str = ""
        self.booru_pattern_blacklist: str = ""

        self.rating_indexes = []
        
        self.TIMER_STATE: StateManager = None #TODO
        
        self.killable = False
        self.killMethod = "stop_generation_by_state_manager"
        
        
        ### var
        self.save_image_to_tmp = False
        self.prompt_generation_max_tries = 500000
        
        # Random LoRA selection
        self.lora_list: list[str] = []
        self.enable_random_lora: bool = False
        self.rnd_lora_select_count: int = 0

    async def get_payload(self) -> dict:
        p = self.param.copy()
        
        # Select LoRA for this generation
        def select_lora() -> list[str]:
            current_lora = self.lora_list
            if self.enable_random_lora and len(self.lora_list) >= self.rnd_lora_select_count:
                current_lora = random.choices(self.lora_list, k=self.rnd_lora_select_count)
                self.stdout(f"[Random LoRA] Selected: {current_lora}")
            return current_lora
        
        
        current_request_param = self.default_prompt_request_param.copy()
        prompt_generated = False
        
        try:
            for t in range(10):
                current_request_param["lora_name"] = select_lora()
                try:
                    prompt = await PromptProcessor.gather_from_lora_rnd_prompt(
                        proc_kw=self.processor_prompt_param,
                        max_tries=self.prompt_generation_max_tries,
                        **current_request_param,
                    )
                    if len(prompt) == 0:
                        raise ValueError("No prompt could be generated.")
                    
                except Exception as e:
                    self.stdout(f"[Random LoRA] Not enough tags could be gathered with the current LoRA selection. Retrying... ({t+1}) ({e})")
                    traceback.print_exc();
                    continue 
                
                prompt_generated = True
                break
            if not prompt_generated:
                raise ValueError("Failed to generate prompt after 10 attempts.")
            
        except ValueError as e:
            raise gr.Error(
                f"Failed to generate prompt. Please check your Prompt Settings. ({e})"
            )
        except RuntimeError:
            raise gr.Error(
                "Failed to generate prompt after multiple attempts. Please adjust your Prompt Settings."
            )

        p = await self._get_payload()

        rpp = self.regional_prompter_param_default.copy()        
        try:
            rpp["Regional Prompter"]["args"][3] = random.choice(self.rp_matrix_mode)
            rpp["Regional Prompter"]["args"][6] = random.choice(self.divine_ratio)
            rpp["Regional Prompter"]["args"][11] = self.rp_calculation
            println(f"[Regional Prompter] Matrix Mode: {rpp['Regional Prompter']['args'][3]}, Divine Ratio: {rpp['Regional Prompter']['args'][6]}, Calculation: {rpp['Regional Prompter']['args'][11]}")
            
        except (IndexError, KeyError):
            warn(
                "IndexError or KeyError occurred while updating Regional Prompter parameters."
            )
        finally:
            p["alwayson_scripts"].update(rpp)    
        p.update(
            {
                "prompt": ", ".join(prompt),
            }
        )
        
        if self.adetailer and not self.separate_adetailer:
            adp = self.adetailer_param.copy()
            try:
                ad_prompt = p.prompt
                if self.disable_lora_in_adetailer:
                    ad_prompt = ", ".join(
                        [
                            p
                            for p in ad_prompt.split(",")
                            if not p.strip() in self.lora_names
                        ]
                    )
                adp["ADetailer"]["args"][2]["ad_prompt"] = ad_prompt
                adp["ADetailer"]["args"][3]["ad_prompt"] = ad_prompt
                # adp.update(self.freeu_param)
            except (IndexError, KeyError):
                warn(
                    "IndexError or KeyError occurred while updating ADetailer parameters."
                )
            finally:
                p["alwayson_scripts"].update(adp)
        
        return p
    
    async def update_prompt_settings(
        self, lora, header, footer,
        tags, random_rate, add_lora_name, lora_weight,
        prompt_weight_chance, prompt_weight_min, prompt_weight_max, remove_character,
        enable_random_lora, rnd_lora_selection, blacklist: str,
    ):
        if enable_random_lora:
            self.rnd_lora_select_count = min(max(1, rnd_lora_selection), len(lora))
            if len(lora) < self.rnd_lora_select_count:
                raise gr.Error(f"Not enough LoRAs selected for random selection ({len(lora)} < {self.rnd_lora_select_count})")
        self.enable_random_lora = enable_random_lora
        
        new_param = {
            "lora_name": lora,
            "header": header,
            "footer": footer,
            "tags": tags,
            "random_rate": random_rate,
            "lora_weight": lora_weight,
            "add_lora_name": add_lora_name,
            "prompt_weight_chance": prompt_weight_chance,
            "prompt_weight_min": prompt_weight_min,
            "prompt_weight_max": prompt_weight_max,
        } | setting.request_param(pop_for_processor=True)
        new_kp = {
            "remove_character": remove_character,
            "special_blacklist": [re.compile(x.strip(), re.IGNORECASE) for x in blacklist.split(",") if x.strip()],
        }
        self.lora_list = lora
        
        validate = await PromptProcessor.test_from_lora_rnd_prompt_available(test_prompt=False, kw_p=new_kp, kw=new_param)
        if validate is True:
            self.default_prompt_request_param = new_param
            gr.Info("Prompt settings updated successfully.")
            self.stdout("Prompt settings updated successfully.")
        else:
            raise gr.Error("Failed to update prompt settings. Please check your settings.")

        self.processor_prompt_param = new_kp
        self.default_prompt_request_param = new_param 

    async def start(
        self,
        lora: list[str],
        enable_random_lora: bool,
        rnd_lora_select_count,
        header: str,
        footer: str,
        max_tags: int,
        base_chance: float,
        add_lora_name: bool,
        lora_weight: float,
        s_method: list[str],
        scheduler: list[str],
        steps_min: int,
        steps_max: int,
        cfg_min: float,
        cfg_max: float,
        batch_count: int,
        batch_size: int,
        size: str,
        adetailer: bool,
        enable_hand_tap: bool,
        disable_lora_in_adetailer: bool,
        enable_freeu: bool,
        preset: str,
        negative: str,
        enable_stop,
        stop_mode,
        stop_min,
        stop_after_img,
        stop_after_datetime,
        neverOOM_unet,
        neverOOM_vae,
        output_dir,
        output_format,
        output_name,
        save_metadata,
        save_infotext,
        booru_filter_enable,
        booru_model,
        active_rp,
        rp_mode,
        rp_calc,
        rp_base,
        rp_base_ratio,
        lora_base,
        add_lora_name_base,
        lora_weight_base,
        header_base,
        footer_base,
        max_tags_base,
        base_chance_base,
        disallow_duplicate_base,
        matrix_split,
        matrix_divide,
        matrix_canvas_res_auto,
        matrix_canvas_res,
        lora_stop_step,
        overlay_ratio,
        prompt_weight_chance,
        prompt_weight_min,
        prompt_weight_max,
        enable_sag,
        sag_strength,
        remove_character,
        save_tmp_images,
        prompt_generation_max_tries,
        blacklist: str,
        
        #
        merge_adetailer_test: bool,
    ) -> AsyncGenerator[tuple[str, Image.Image], None]:
        self.default_prompt_request_param = setting.request_param().copy()
        
        # テスト呼び出し + 必要ならLoRA名取得
        await self.update_prompt_settings(
            lora, header, footer, max_tags, base_chance, add_lora_name, lora_weight, prompt_weight_chance, prompt_weight_min, prompt_weight_max, remove_character, enable_random_lora, rnd_lora_select_count, blacklist
        )
        
        if disable_lora_in_adetailer:
            rp = await shared.session.post(
                url=f"{shared.pem_api}/v1/generator/lora/names",
                json={"lora_name": lora},
            )
            if rp.status_code != 200:
                raise gr.Error(f"Failed to get LoRA names ({rp.status_code})")
            self.lora_names = [
                f"<lora:{x}:{lora_weight}>" for x in rp.json()[0].get("lora_names", [])
            ]

        self.param = {
            "negative_prompt": negative,
            "batch_size": batch_size,
            "n_iter": batch_count,
            "restore_faces": False,
            "tiling": False,
            "save_images": False,
            "alwayson_scripts": {}
        }

        arg_list = [
            True,
            True,
            {
                "ad_model": "face_yolov8n.pt",
                "ad_prompt": None,
                "ad_negative_prompt": negative,
            },
        ]
        if enable_hand_tap:
            arg_list.append(
                {
                    "ad_model": "hand_yolov8n.pt",
                    "ad_prompt": None,
                    "ad_negative_prompt": negative,
                }
            )
        self.adetailer_param = (
            {
                "ADetailer": {
                    "args": arg_list,
                }
            }
            if adetailer
            else {}
        )
        self.adetailer = adetailer
        self.separate_adetailer = not merge_adetailer_test
        

        freeu_preset = (
            [1.3, 1.4, 0.9, 0.2] if preset == "SDXL" else [1.5, 1.6, 0.9, 0.2]
        )
        self.freeu_param = (
            {
                "FreeU Integrated (SD 1.x, SD 2.x, SDXL)": {
                    "args": [True] + freeu_preset + [0, 1]
                }
            }
            if enable_freeu
            else {}
        )
        
        self.neveroom_param = (
            {
                "Never OOM Integrated": {
                    "args": [
                        {
                            "unet_enabled": neverOOM_unet,
                            "vae_enabled": neverOOM_vae
                        },
                    ],
                }
            }
            if (neverOOM_unet or neverOOM_vae)
            else {}
        )
        
        self.sag_param = (
            {
                "SelfAttentionGuidance Integrated (SD 1.x, SD 2.x, SDXL)": {
                    "args": [True, sag_strength, 2, 1.0]
                }
            }
            if enable_sag
            else {}
        )
        
        self.regional_prompter_param_default = (
            {
                "Regional Prompter": {
                    "args": [
                        active_rp, False, rp_mode, None, #matrix mode
                        "TODO:Mask", "TODO:Prompt", None, # Divine
                        rp_base_ratio, rp_base, False, False,
                        None, # rp_calc
                        False, 0, 0, overlay_ratio, None, # mask
                        lora_stop_step, 0, False
                    ]
                }
            }
            if active_rp
            else {}
        )
        

        timer = None
        if enable_stop:
            timer = TimerInstance(name="Forever Generation/LoRA Timer")
            if stop_mode == "After Minutes":
                timer.set_end_at(time.time() + stop_min * 60)
            elif stop_mode == "At Datetime":
                try:
                    timer.end_at_dt(timer.dtparse(stop_after_datetime))
                except ValueError as e:
                    raise gr.Error(f"Invalid datetime format: {e}")
            elif stop_mode == "After Images":
                self.n_of_img = stop_after_img
                timer = False
            if timer is None:
                raise gr.Error("Timer is not set. Please enable stop mode.")

        await self.prepare_caption_model(booru_filter_enable, booru_model)

        self.early_booru_filter = True
        self.booru_filter_enabled = booru_filter_enable
        self.disable_lora_in_adetailer = disable_lora_in_adetailer
        self.lora = lora
        self.sampling_methods = s_method
        self.schedulers = scheduler
        self.steps = (steps_min, steps_max)
        self.cfg_scales = (cfg_min, cfg_max)
        s = []
        for si in size.split(","):
            w, h = si.split(":")
            s.append((int(w), int(h)))
        self.sizes = s
        
        self.rp_enabled = active_rp
        self.rp_matrix_mode = matrix_split
        self.rp_calculation = rp_calc
        self.divine_ratio = matrix_divide.split(";")
        self.rp_auto_res = matrix_canvas_res_auto
        if self.rp_enabled and not self.rp_auto_res:
            s = []
            for si in matrix_canvas_res.split(","):
                w, h = si.split(":")
                s.append((int(w), int(h)))
        self.rp_canvas_res = s
        
        self.clear_stdout()
        self.save_image_to_tmp = save_tmp_images
        self.prompt_generation_max_tries = min(5000000, max(1, prompt_generation_max_tries)) # 1 ~ 5,000,000

        eta = ""
        progress = ""
        progress_bar_html = ""
        num_of_loop = 1
        num_of_iter = 0
        num_of_image = 0
        prv_generation_c = None
        async for i in self.start_generation():
            if num_of_image >= self.n_of_img:
                self.stdout(
                    f"Stopping generation due to image limit ({self.n_of_img} images reached). (loop: {num_of_loop} | iter: {num_of_iter})"
                )
                self.skipped_by = "[User Setting] image Limit"
                self.skipped()
                self.n_of_img = 2140000000
                break

            num_of_loop += 1
            if num_of_iter != prv_generation_c:
                self.stdout(
                    f"Starting generation ({num_of_iter + 1} / inf) with Prompt: {i.get('payload', {}).get('prompt', 'N/A')}",
                    silent=True,
                )
                # 停止チェック
                if timer and timer.is_done():
                    self.stdout(
                        f"Stopping generation due to timer expiration. (image: {num_of_iter}) (loop: {num_of_loop} | iter: {num_of_iter})"
                    )
                    self.skipped_by = "[User Setting] Timer Expiration"
                    self.skipped()
                    break
                prv_generation_c = num_of_iter

            ok = i.get("ok", False)
            status = i.get("success", "")
            if not ok and status == "in_progress":
                p: GenerationProgress = i["progress"]
                eta = ForeverGenerationTemplate.resize_eta(p.eta)
                progress = ForeverGenerationTemplate.resize_steps(p.step, p.total_steps)
                progress_bar_html = ForeverGenerationTemplate.resize_progress_bar(
                    p.progress, p.eta
                )
                image = await p.convert_image()
                yield self.yielding(eta, progress, progress_bar_html, image)
            elif ok and status == "completed":
                p: GenerationResult = i["result"]
                image = (await p.convert_images())[0]
                num_of_iter += 1
                eta = "N/A"
                progress = "100%"
                progress_bar_html = self.resize_progress_bar(100, -1)
                yield self.yielding(eta, progress, progress_bar_html, image=await p.convert_images_into_gr())

                if self.image_skipped:
                    self.skipped()
                    continue
                num_of_image += len(p.images)

                # caption filter
                p.images = await self.booru_filter(i, p, await p.convert_images(), True, )

                if self.adetailer and self.separate_adetailer:
                    adp = self.adetailer_param
                    try:
                        ad_prompt = p.prompt
                        if self.disable_lora_in_adetailer:
                            ad_prompt = ", ".join(
                                [
                                    p
                                    for p in ad_prompt.split(",")
                                    if not p.strip() in self.lora_names
                                ]
                            )
                        adp["ADetailer"]["args"][2]["ad_prompt"] = ad_prompt
                        adp["ADetailer"]["args"][3]["ad_prompt"] = ad_prompt
                        adp.update(self.freeu_param)
                    except (IndexError, KeyError):
                        warn(
                            "IndexError or KeyError occurred while updating ADetailer parameters."
                        )
                    finally:
                        ad_param = {
                            "prompt": p.prompt,
                            "negative_prompt": p.negative,
                            "width": p.width,
                            "height": p.height,
                            "seed": p.seed,
                            "sampler_name": p.sampler,
                            "cfg_scale": p.cfg_scale,
                            "scheduler": "Automatic",
                            "batch_size": 1,
                            "steps": 120,
                            "alwayson_scripts": adp,
                        }
                    yield self.yielding(
                        eta,
                        progress,
                        progress_bar_html,
                        image,
                        self.stdout("Generation completed. Processing ADetailer.."),
                    )
                    ad_api = ADetailerAPI(ad_param)
                    images = []
                    for index, img in enumerate(p.images, start=1):
                        if self.image_skipped:
                            self.stdout("AD-Image skipped by skip event.")
                            continue
                        yield self.stdnow(
                            f"[{index}/{len(p.images)}] Processing image with ADetailer.."
                        )
                        async for processing in ad_api.generate_with_progress(
                            init_images=[img]
                        ):
                            if processing[0] is False:
                                pr: GenerationProgress = processing[2]
                                eta_ = self.resize_eta(pr.eta)
                                progress_ = self.resize_steps(
                                    pr.step, pr.total_steps
                                )
                                progress_bar_html_ = (
                                    self.resize_progress_bar(
                                        pr.progress, pr.eta
                                    )
                                )
                                yield self.yielding(
                                    eta_,
                                    progress_,
                                    progress_bar_html_,
                                    await pr.convert_image_into_gr(),
                                )
                                await asyncio.sleep(1.5)  # Prevent OSError
                            elif processing[0] is True:
                                result: ADetailerResult = processing[1]
                                images += await result.convert_images()
                                yield self.yielding(
                                    eta,
                                    progress,
                                    progress_bar_html,
                                    await result.convert_images_into_gr(),
                                    self.stdout(
                                        f"[{index}/{len(p.images)}] ADetailer completed."
                                    ),
                                )
                else:
                    images = await p.convert_images()

                if self.image_skipped:
                    self.skipped()
                    continue

                # caption filter after adetailer
                images = await self.booru_filter(i, p, images, False)

                for index, image_obj in enumerate(images, start=0):
                    if self.save_image_to_tmp:
                        image_obj.save(
                            f"./tmp/img/generated_{num_of_iter}_{index}-{num_of_loop}-{sha256(image_obj.tobytes())}.png"
                        )

                    DATE = time.strftime("%Y-%m-%d")
                    fp = output_dir.format(DATE=DATE)
                    os.makedirs(fp, exist_ok=True)
                    img_files = sorted(
                        [
                            f
                            for f in os.listdir(fp)
                            if re.match(r"^\d{5}-\d+.png$", f) is not None
                        ],
                        key=lambda x: int(x.split("-")[0]),
                    )
                    image_count = int(img_files[-1].split("-")[0]) if img_files else 0
                    seed = p.seed if p.seed is not None else 0
                    ext = output_format.lower() if output_format != "JPEG" else "jpg"
                    image_name = output_name.format(
                        seed=seed + index,
                        date=DATE,
                        image_count=f"{(image_count + 1):05d}",
                        ext=ext,
                    )
                    fn = os.path.join(fp, image_name)
                    txtinfo = p.infotext
                    if save_infotext:
                        with open(fn + ".txt", "w", encoding="utf-8") as f:
                            f.write(txtinfo)

                    if save_metadata:
                        info = make_info(
                            {
                                "parameters": txtinfo,
                                "pem_payload": json.dumps(i["payload"]),
                            }
                        )
                        image_obj.save(fn, format=output_format, pnginfo=info)
                    else:
                        image_obj.save(fn, format=output_format)
                    self.stdout(f"[{index+1}/{len(images)}] Image saved as {fn}")

                yield self.yielding(eta, progress, progress_bar_html, image_obj)

            elif not ok and status == "error":
                raise gr.Error("Generation failed due to an error.")
        yield self.yielding(
            "N/A",
            "N/A",
            self.resize_progress_bar(0, -1),
            None,
            self.stdout("Generation Stopped."),
            False,
        )