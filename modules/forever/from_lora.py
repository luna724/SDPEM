import asyncio
import base64
from io import BytesIO
from itertools import chain
import json
import os
import re
import time
from typing import *
import gradio as gr
import random
from PIL import Image, PngImagePlugin

from modules.adetailer import ADetailerAPI, ADetailerResult
from modules.generate import GenerationProgress, GenerationResult, Txt2imgAPI
from modules.tagger.predictor import OnnxRuntimeTagger
from modules.utils.pnginfo import make_info
from modules.utils.state import StateManager
from modules.utils.timer import TimerInstance
from modules.utils.util import sha256
from modules.forever_generation import ForeverGeneration
from modules.prompt_setting import setting
from modules.prompt_processor import PromptProcessor
import shared
from utils import *


class LegacyImageProgressAPI:
    @staticmethod
    def resize_eta(eta: float) -> str:
        """ETA を h/m/s の形式に変換する"""
        if eta == -1:
            return "N/A"

        converted = int(eta)
        h = converted // 3600
        converted -= h * 3600
        m = converted // 60
        converted -= m * 60
        s = converted

        eta = f""
        if h > 0:
            eta += f"{h}h "
        if m > 0:
            eta += f"{m}m "
        if s > 0:
            eta += f"{s}s"

        return eta.strip()

    @staticmethod
    def status_text(s: int, total_s: int) -> str:
        """受け取った引数を (s/total_s (steps)) (s/total_s%) に変換する"""
        percentage = "{:.1f}".format(s / total_s * 100)
        return f"({s}/{total_s} (steps)) ({percentage}%)"

    @staticmethod
    def progress_bar_html(progress: int, eta: float) -> str:
        """UIのプログレスバーのHTML"""
        eta = LegacyImageProgressAPI.resize_eta(eta)
        return f"""
        <div style="width: 100%; background-color: #e0e0e0; border-radius: 8px; overflow: hidden;">
            <div style="width: {progress}%; height: 30px; background-color: #76c7c0; transition: width 0.3s;"></div>
        </div>
        <p style="text-align: center;">ETA: {eta} ({progress:.2f}%)</p>
        """


# TODO: @Codex
STATE = None # TODO: ForeverGenerationFromLoRAの現在の状況を保持、外部にストリームするための関数
# /modules/api/v1/bot/forever_from_lora.py で使用される予定
# 仕様自体は複数インスタンス対応してもいいが、どんな強靭なGPU使ってんのって話になるから単一保持の予定 (最新のインスタンスを保持する)

# ForeverGeneration instanceは tab/.. によって保持され生涯有効
class ForeverGenerationFromLoRA(ForeverGeneration):
    def stdout(self, txt: str | None = None, silent: bool = False) -> str:
        if txt is None:
            return self.output
        if not silent:
            println(f"[Forever]: {txt}")
        self.output += txt + "\n"
        return self.output

    async def skip_image(self) -> bool:
        self.stdout("Skipping image..")
        gr.Info("Skipping..")
        await Txt2imgAPI._post_requests(path="/sdapi/v1/interrupt", json={})
        await Txt2imgAPI._post_requests(path="/sdapi/v1/skip", json={})
        self.image_skipped = True
        return True

    def skipped(self):
        self.image_skipped = False
        self.stdout(f"Image skipped by {self.skipped_by}.")
        self.skipped_by = "User"  # reset

    def __init__(self, payload: dict | None = None) -> None:
        super().__init__({})
        self.output = ""
        self.payload = {}
        self.param = {}
        self.default_prompt_request_param = {}
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

        self.n_of_img = 2140000000
        self.image_skipped = False
        self.skipped_by = "User"
        
        self.booru_blacklist: str = ""
        self.booru_pattern_blacklist: str = ""

        self.rating_indexes = []
        
        self.TIMER_STATE: StateManager = None #TODO
        
        self.killable = False
        self.killMethod = "stop_generation_by_state_manager"

    async def get_payload(self) -> dict:
        p = self.param.copy()
        try:
            prompt = await PromptProcessor.gather_from_lora_rnd_prompt(
                **self.default_prompt_request_param
            )
        except ValueError as e:
            raise gr.Error(
                f"Failed to generate prompt. Please check your Prompt Settings. ({e})"
            )
        except RuntimeError:
            raise gr.Error(
                "Failed to generate prompt after multiple attempts. Please adjust your Prompt Settings."
            )

        sampler = random.choice(self.sampling_methods)
        scheduler = random.choice(self.schedulers)
        step = random.randint(self.steps[0], self.steps[1])
        cfg_scale = (
            random.randrange(self.cfg_scales[0] * 10, self.cfg_scales[1] * 10, 5) / 10
        )
        size = random.choice(self.sizes)
        w = size[0]
        h = size[1]

        rpp = self.regional_prompter_param_default.copy()        
        try:
            rpp["Regional Prompter"]["args"][3] = random.choice(self.rp_matrix_mode)
            rpp["Regional Prompter"]["args"][6] = random.choice(self.divine_ratio)
            rpp["Regional Prompter"]["args"][11] = self.rp_calculation
        except (IndexError, KeyError):
            warn(
                "IndexError or KeyError occurred while updating Regional Prompter parameters."
            )
        finally:
            p["alwayson_scripts"].update(rpp)    
        p.update(
            {
                "prompt": ", ".join(prompt),
                "sampler_name": sampler,
                "scheduler": scheduler,
                "steps": step,
                "cfg_scale": cfg_scale,
                "width": w,
                "height": h,
            }
        )

        p["alwayson_scripts"].update(self.freeu_param)
        p["alwayson_scripts"].update(self.neveroom_param)
        p["alwayson_scripts"].update(self.sag_param)
        return p
    
    async def update_prompt_settings(
        self, lora, header, footer,
        tags, random_rate, add_lora_name, lora_weight,
        booru_blacklist, booru_pattern_blacklist,
        prompt_weight_chance, prompt_weight_min, prompt_weight_max
    ):
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
        
        validate = await PromptProcessor.test_from_lora_rnd_prompt_available(test_prompt=False, kw=new_param)
        if validate is True:
            self.default_prompt_request_param = new_param
            gr.Info("Prompt settings updated successfully.")
            self.stdout("Prompt settings updated successfully.")
        else:
            raise gr.Error("Failed to update prompt settings. Please check your settings.")

        self.default_prompt_request_param = new_param
        self.booru_blacklist = booru_blacklist
        self.booru_pattern_blacklist = booru_pattern_blacklist  

    async def start(
        self,
        lora: list[str],
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
        booru_threshold,
        booru_character_threshold,
        booru_allow_rating,
        booru_ignore_questionable,
        booru_save_each_rate,
        booru_merge_sensitive,
        general_save_dir,
        sensitive_save_dir,
        questionable_save_dir,
        explicit_save_dir,
        booru_blacklist,
        booru_pattern_blacklist,
        booru_separate_save,
        booru_blacklist_save_dir,
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
    ) -> AsyncGenerator[tuple[str, Image.Image], None]:
        self.default_prompt_request_param = setting.request_param().copy()
        # テスト呼び出し + 必要ならLoRA名取得
        await self.update_prompt_settings(
            lora, header, footer, max_tags, base_chance, add_lora_name, lora_weight, booru_blacklist, booru_pattern_blacklist, prompt_weight_chance, prompt_weight_min, prompt_weight_max
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

        caption: OnnxRuntimeTagger = None
        if booru_filter_enable:
            # TODO: wd以外
            caption = OnnxRuntimeTagger(model_path=booru_model, find_path=True)

        self.disable_lora_in_adetailer = disable_lora_in_adetailer
        self.lora = lora
        self.sampling_methods = s_method
        self.schedulers = scheduler
        self.steps = (steps_min, steps_max)
        self.cfg_scales = (cfg_min, cfg_max)
        self.booru_blacklist = booru_blacklist
        self.booru_pattern_blacklist = booru_pattern_blacklist
        s = []
        for si in size.split(","):
            w, h = si.split(":")
            s.append((int(w), int(h)))
        self.sizes = s
        
        self.rp_enabled = active_rp
        self.rp_matrix_mode = matrix_split
        self.rp_calculation = rp_calc
        self.divine_ratio = matrix_divide.split(",")
        self.rp_auto_res = matrix_canvas_res_auto
        if self.rp_enabled and not self.rp_auto_res:
            s = []
            for si in matrix_canvas_res.split(","):
                w, h = si.split(":")
                s.append((int(w), int(h)))
        self.rp_canvas_res = s

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
                eta = LegacyImageProgressAPI.resize_eta(p.eta)
                progress = LegacyImageProgressAPI.status_text(p.step, p.total_steps)
                progress_bar_html = LegacyImageProgressAPI.progress_bar_html(
                    p.progress, p.eta
                )
                image = await p.convert_image()
                yield (eta, progress, progress_bar_html, image, self.stdout(), self.image_skipped)
            elif ok and status == "completed":
                p: GenerationResult = i["result"]
                image = (await p.convert_images())[0]
                num_of_iter += 1
                eta = "N/A"
                progress = "100%"
                progress_bar_html = LegacyImageProgressAPI.progress_bar_html(100, -1)
                image_obj = gr.Image.update(
                    height=p.height, width=p.width, value=image, interactive=False
                )

                if self.image_skipped:
                    self.skipped()
                    continue
                num_of_image += len(p.images)

                # caption filter
                if booru_filter_enable:
                    await caption.load_model_cuda()
                    self.stdout("Processing image with Booru Filter..")
                    p.images = await self.caption_filter(
                        caption,
                        p,
                        booru_threshold,
                        booru_character_threshold,
                        booru_allow_rating,
                        booru_ignore_questionable,
                        booru_save_each_rate,
                        booru_merge_sensitive,
                        general_save_dir,
                        sensitive_save_dir,
                        questionable_save_dir,
                        explicit_save_dir,
                        booru_separate_save,
                        booru_blacklist_save_dir,
                        before_adetailer=True,
                    )
                    await caption.unload_model()

                if adetailer:
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
                    yield (
                        eta,
                        progress,
                        progress_bar_html,
                        image,
                        self.stdout("Generation completed. Processing ADetailer.."),
                        self.image_skipped
                    )
                    ad_api = ADetailerAPI(ad_param)
                    images = []
                    for index, img in enumerate(p.images, start=1):
                        if self.image_skipped:
                            self.stdout("AD-Image skipped by skip event.")
                            continue
                        self.stdout(
                            f"[{index}/{len(p.images)}] Processing image with ADetailer.."
                        )
                        async for processing in ad_api.generate_with_progress(
                            init_images=[img]
                        ):
                            if processing[0] is False:
                                pr: GenerationProgress = processing[2]
                                eta_ = LegacyImageProgressAPI.resize_eta(pr.eta)
                                progress_ = LegacyImageProgressAPI.status_text(
                                    pr.step, pr.total_steps
                                )
                                progress_bar_html_ = (
                                    LegacyImageProgressAPI.progress_bar_html(
                                        pr.progress, pr.eta
                                    )
                                )
                                i_ = await pr.convert_image()
                                yield (
                                    eta_,
                                    progress_,
                                    progress_bar_html_,
                                    i_,
                                    self.stdout(),
                                    self.image_skipped
                                )
                                await asyncio.sleep(1.5)  # Prevent OSError
                            elif processing[0] is True:
                                result: ADetailerResult = processing[1]
                                images += await result.convert_images()
                                yield (
                                    eta,
                                    progress,
                                    progress_bar_html,
                                    images[0],
                                    self.stdout(
                                        f"[{index}/{len(p.images)}] ADetailer completed."
                                    ),
                                    self.image_skipped
                                )
                else:
                    images = await p.convert_images()

                if self.image_skipped:
                    self.skipped()
                    continue

                # caption filter after adetailer
                if booru_filter_enable:
                    await caption.load_model_cuda()
                    self.stdout("Processing image with Booru Filter..")
                    p._booru_image_bridge = images
                    images = await self.caption_filter(
                        caption,
                        p,
                        booru_threshold,
                        booru_character_threshold,
                        booru_allow_rating,
                        booru_ignore_questionable,
                        booru_save_each_rate,
                        booru_merge_sensitive,
                        general_save_dir,
                        sensitive_save_dir,
                        questionable_save_dir,
                        explicit_save_dir,
                        booru_separate_save,
                        booru_blacklist_save_dir,
                        before_adetailer=False,
                    )
                    await caption.unload_model()

                for index, image_obj in enumerate(images, start=0):
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

                yield (eta, progress, progress_bar_html, image_obj, self.stdout(), self.image_skipped)

            elif not ok and status == "error":
                raise gr.Error("Generation failed due to an error.")
        yield (
            "N/A",
            "N/A",
            LegacyImageProgressAPI.progress_bar_html(0, -1),
            None,
            self.stdout("Generation Stopped."),
            self.image_skipped
        )

    async def stop_generation(self):
        self.n_of_img = 2140000000
        self.image_skipped = False
        self.skipped_by = "User"
        gr.Warning("Generation will be stop after this iteration.")
        await super().stop_generation()
    async def stop_generation_by_state_manager(self, sm: StateManager) -> str: # TODO
        await self.stop_generation()
    
    
    async def caption_filter(
        self,
        caption: OnnxRuntimeTagger,
        p: GenerationResult,
        booru_threshold,
        booru_character_threshold,
        booru_allow_rating,
        booru_ignore_questionable,
        booru_save_each_rate,
        booru_merge_sensitive,
        general_save_dir,
        sensitive_save_dir,
        questionable_save_dir,
        explicit_save_dir,
        # booru_blacklist,
        # booru_pattern_blacklist,
        booru_separate_save,
        booru_blacklist_save_dir,
        before_adetailer: bool,
    ) -> list[str] | list[Image.Image]:  # base64 encoded images
        """
        booruでなんやかんやして画像をフィルタリングする
        okな画像はそのままで返す

        before_adetailer の場合は list[b64img] を返し、
        after_adetailer の場合は list[Image.Image] を返す
        """
        booru_blacklist = self.booru_blacklist
        booru_pattern_blacklist = self.booru_pattern_blacklist
        
        def save_blacklisted_image(
            i: Image.Image,
            rate: str,
        ):
            if not booru_separate_save:
                return
            self.stdout(f"[Caption]: Saving blacklisted image with rate: {rate}")
            os.makedirs(booru_blacklist_save_dir, exist_ok=True)
            fn = f"[{rate}] {p.seed} - " + sha256(i.tobytes()) + ".png"
            fp = os.path.join(booru_blacklist_save_dir, fn)
            info = PngImagePlugin.PngInfo()
            info.add_text("parameters", p.infotext)
            i.save(fp, format="PNG", pnginfo=info)
            self.stdout(f"[Caption]: Blacklisted image saved as {fp}")
            return

        def save_separated_rate(
            i: Image.Image,
            rate: str,
        ):
            if not booru_save_each_rate:
                return
            self.stdout(f"[Caption]: Saving image with rate: {rate}")
            DATE = time.strftime("%Y-%m-%d")
            if rate == "general" or (rate == "sensitive" and booru_merge_sensitive):
                fp = general_save_dir.format(DATE=DATE)
            elif rate == "sensitive":
                fp = sensitive_save_dir.format(DATE=DATE)
            elif rate == "questionable":
                fp = questionable_save_dir.format(DATE=DATE)
            elif rate == "explicit":
                fp = explicit_save_dir.format(DATE=DATE)
            else:
                critical(f"[Caption]: Unknown rate: {rate}. Skipping save.")
                return
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
            image_name = f"{(image_count + 1):05d}-{seed}.png"
            fn = os.path.join(fp, image_name)
            info = PngImagePlugin.PngInfo()
            info.add_text("parameters", p.infotext)
            i.save(fn, format="PNG", pnginfo=info)
            self.stdout(f"[Caption]: Image saved as {fn}")
            return

        if before_adetailer and booru_separate_save:
            # 完成品を保存するならadetailer後に保存する
            return p.images

        if before_adetailer:
            images = p.images.copy()
        else:
            images = p._booru_image_bridge
        allow_image = []
        for img in images:
            blacklisted = False

            if before_adetailer:
                image = Image.open(BytesIO(base64.b64decode(img)))
            else:
                image = img
            tags, character_tags, rating = await caption.predict(
                image.convert("RGBA"),
                threshold=booru_threshold,
                character_threshold=booru_character_threshold,
            )

            rate: str = max(rating, key=rating.get, default="general")
            general_rate: float = rating.get("general", 0)
            sensitive_rate: float = rating.get("sensitive", 0)
            questionable_rate: float = rating.get("questionable", 0)
            explicit_rate: float = rating.get("explicit", 0)
            txtprompt = ", ".join(
                        [
                            x[0]
                            for x in sorted(
                                tags.items(), key=lambda x: x[1], reverse=True
                            )
                        ]
                    )
            self.stdout(
                f"[Caption]: output: {txtprompt}"
            )
            
            if (
                general_rate == 0
                and sensitive_rate == 0
                and questionable_rate == 0
                and explicit_rate == 0
            ):
                self.stdout("No rating found in the image.")
                questionable_rate = 1

            if booru_ignore_questionable and rate == "questionable":
                d = rating.copy()
                d.pop("questionable", None)
                rate = max(d, key=d.get, default="general")
                self.stdout(f"Ignoring questionable rating. (questionable -> {rate})")
            if not rate in booru_allow_rating and not booru_save_each_rate:
                save_blacklisted_image(img, rate)
                continue

            # blacklist check
            # TODO
            b = [
                re.compile(rf"^\s*{re.escape(tag.strip())}\s*$", re.IGNORECASE)
                for tag in booru_blacklist.split(",")
                if tag.strip() != ""
            ] + [
                re.compile(pattern, re.IGNORECASE)
                for pattern in booru_pattern_blacklist.splitlines()
                if pattern.strip() != ""
            ]
            debug(f"[Booru blacklist registered]: {len(b)} patterns.")

            itms = chain(tags.items(), character_tags.items())
            for tag, _ in itms:
                # debug(f"[Checking tag]: {tag}")
                if any(bl.search(tag) for bl in b):
                    self.stdout(
                        f"[Caption]: Tag '{tag}' is blacklisted. Skipping image."
                    )
                    blacklisted = True
                    save_blacklisted_image(image, rate)
                    break
            if blacklisted:
                continue

            if booru_save_each_rate and not before_adetailer:
                save_separated_rate(image, rate)
            else:
                allow_image.append(img)
        return allow_image