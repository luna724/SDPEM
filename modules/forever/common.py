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
from modules.forever_generation import ForeverGeneration, ForeverGenerationResponse
from modules.prompt_setting import setting
from modules.booru_filter import BooruOptions, booru_filter
from modules.utils.lora_util import is_lora_trigger

import shared
from logger import println, debug, warn, error, critical

class VariableStorage:
    __slots__ = ("_storage",)

    def __init__(self, initial: Optional[Dict[str, Any]] = None):
        object.__setattr__(self, "_storage", {})
        if initial:
            self._storage.update(initial)

    def __getattr__(self, name: str) -> Any:
        return self._storage.get(name)

    def __setattr__(self, name: str, value: Any) -> None:
        self._storage[name] = value

    def get(self, name: str, default: Any = None) -> Any:
        return self._storage.get(name, default)

    def clear(self) -> None:
        self._storage.clear()

class ForeverGenerationTemplate(ForeverGeneration):
    @staticmethod
    def resize_locals(l: dict) -> dict:
        l.pop("self", None)
        return l
    
    @staticmethod
    def resize_eta(eta: float) -> str:
        if eta is None or eta <= 0:
            return "N/A"

        total_seconds = int(eta)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        parts: list[str] = []
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        if seconds or not parts:
            parts.append(f"{seconds}s")

        return " ".join(parts)
    
    @staticmethod
    def resize_steps(s: int, total_s: int) -> str:
        if total_s == 0: return "N/A"
        percentage = "{:.1f}".format(s / total_s * 100)
        return f"({s}/{total_s} (steps)) ({percentage}%)"
    
    @classmethod
    def resize_progress_bar(cls, progress: float, eta: float) -> str:
        eta_text = cls.resize_eta(eta)
        clamped_progress = max(0.0, min(progress, 100.0))
        return (
            "<div style='display:flex;align-items:center;gap:0.5rem;font-size:0.85rem;'>"
            "<div style=\"flex:1;height:10px;background:rgba(59,130,246,0.18);"
            "border-radius:9999px;overflow:hidden;\">"
            f"<div style=\"width:{clamped_progress:.2f}%;height:100%;"
            "background:linear-gradient(90deg,#3b82f6,#2563eb);"
            "transition:width 0.2s ease-out;\"></div>"
            "</div>"
            f"<span style='white-space:nowrap;color:#1f2937;'>ETA: {eta_text} ({clamped_progress:.2f}%)</span>"
            "</div>"
        )
    
    def stdout(self, txt: str | None = None, silent: bool = False) -> str:
        if txt is None:
            return self.output
        if not silent:
            println(f"[Forever/{self.instance_name}]: {txt}")
        self.output += txt + "\n"
        return self.output
    
    def clear_stdout(self):
        self.output = ""

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
    
    def yielding(
        self,
        eta=None, progress=None, pg_html=None, image=None, stdout=None, skip_override=None,
        *args, **kw
    ):
        if eta is not None: self.history.eta = eta
        if progress is not None: self.history.progress = progress
        if pg_html is not None: self.history.pg_html = pg_html
        
        if image is not None and isinstance(image, Image.Image):
            image = gr.Image(value=image, width=image.width, height=image.height, interactive=False)
        
        return (
            (eta or self.history.eta) + " | " + (progress or self.history.progress), 
            pg_html or self.history.pg_html, 
            image if image is not None else gr.update(interactive=False), # Required or None
            stdout or self.stdout(),
            skip_override if skip_override is not None else self.image_skipped, 
            not self.is_generating
        )
    
    def stdnow(self, txt: str = None, silent: bool = False):
        output = self.stdout(txt, silent=silent) if txt is not None else self.stdout()
        return self.yielding(stdout=output)
    
    def reset(self):
        self.payload = {}
        self.param = {}
        self.default_prompt_request_param = {}
        self.processor_prompt_param = {}
        self.adetailer_param = {}
        self.freeu_param = {}
        self.neveroom_param = {}
        self.sag_param = {}

        self.sampling_methods: list[str]
        self.schedulers: list[str]
        self.auto_cast_scheduler = False
        self.steps: tuple[int, int]
        self.adetailer_steps: int = 120
        self.cfg_scales: tuple[float, float]
        self.sizes: list[tuple[int, int]]
        self.disable_lora_in_adetailer: bool

        ### timer ###
        self.enable_auto_stop: bool = False
        self.timer: TimerInstance = None
        self.stop_after_n_of_img = 2140000000
        self.timer_method: str = None
        self.num_of_loop: int = 1
        self.num_of_iter: int = 0
        self.num_of_image: int = 0
        self.prv_generation_c: int = -1
        
        ### stop ###
        self.image_skipped = False
        self.skipped_by = "User"
        self.TIMER_STATE: StateManager = None #TODO
        
        self.killable = False
        self.killMethod = "stop_generation_by_state_manager"
        
        ### booru filter ###
        self.rating_indexes = []
        self.booru_filter_enabled: bool = False
        self.booru_model: OnnxRuntimeTagger = None
        
        # TODO: add variables
        self.early_booru_filter: bool = True # ADetailer前にフィルタする
        self.image_skipped_adetailer = False
        
        # other
        self.save_image_to_tmp = False
        self.prompt_generation_max_tries = 500000
        self.generation_error_count = 0
        self.generation_error_count_limit = 5
        
        self.history = VariableStorage({
            "eta": "N/A",
            "progress": "",
            "pg_html": "",
        })
        self.on_reset()

    def __init__(self, payload: dict | None = None) -> None:
        super().__init__({})
        self.instance_name = "Template"
        
        self.output = ""
        self.reset()

    # abstract
    async def get_payload(self) -> dict:
        """
        sdapiに渡すpayloadを返す
        _get_payload()を呼び出すことでプロンプト以外をデフォルトで設定することが可能
        
        """
        p = await self._get_payload()
        p["prompt"] = "example"
        
        return p 
    
    # abstract
    async def test_new_setting(self, new_param: dict, new_kp: dict) -> tuple[dict, dict, bool]:
        """
        update_prompt_settings() で使われる新しい設定のテスト
        return: 修正された new_param, new_kp, is_valid
        """
        return new_param, new_kp, True
        
    async def _get_payload(self) -> dict:
        p = self.param.copy()
        sampler = random.choice(self.sampling_methods)
        scheduler = random.choice(self.schedulers)
        step = random.randint(self.steps[0], self.steps[1]) if self.steps[0] < self.steps[1] else self.steps[0]
        cfg_scale = (
            random.randrange(self.cfg_scales[0] * 10, self.cfg_scales[1] * 10, 5) / 10
        ) if self.cfg_scales[0] < self.cfg_scales[1] else self.cfg_scales[0]
        size = random.choice(self.sizes)
        w = size[0]
        h = size[1]
        
        p.update(
            {
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
    
    # protected
    async def start(self, **kw) -> AsyncGenerator[tuple[str, Image.Image], None]:
        """
        画像生成を開始する
        進捗(ETA, Progress, ProgressBarHTML)と生成画像を非同期でyieldする
        画像がスキップされた場合、画像はNoneになる
        """
        # example usage
        # await self._start(self, **self.resize_locals(kw)) # ？
        
        # await self.auto_chain(**self.resize_locals(locals())) # 適当に全部つなげるやつ
        # 初期化
        self.reset()
        self.clear_stdout()
        
        await self.auto_chain(**self.resize_locals(kw))
        async for item in self.run_loop(**self.resize_locals(kw)):
            yield item
        return
    
    async def auto_chain(self, **kw):
        """
        start(): 0 ~ 
        
        """
        self.reset()
        self.clear_stdout()
        
        await self.prepare_param(**kw)
        await self.prepare_timer(**kw)
        await self.update_prompt_settings(**kw)
        await self.prepare_caption_model(**kw)
    
    async def prepare_param(
        self,
        negative: str,
        batch_size: int, batch_count: int,
        adetailer: bool, enable_hand_tap: bool, disable_lora_in_adetailer: bool,
        enable_freeu: bool, freeu_preset: str,
        enable_neveroom_unet: bool, enable_neveroom_vae: bool,
        enable_sag: bool, sag_strength: float,
        **kwargs
    ):
        """start():1"""
        self.stdout("Preparing parameters...")
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
            [1.3, 1.4, 0.9, 0.2] if freeu_preset == "SDXL" else [1.5, 1.6, 0.9, 0.2]
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
                            "unet_enabled": enable_neveroom_unet,
                            "vae_enabled": enable_neveroom_vae
                        },
                    ],
                }
            }
            if (enable_neveroom_unet or enable_neveroom_vae)
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
        self.stdout("done.")
        return

    async def prepare_timer(
        self, 
        enable_auto_stop: bool,
        stop_mode: Literal["After Minutes", "At Datetime", "After Images"],
        stop_minutes: int, stop_after_img: int, stop_after_datetime: str,
        **kwargs
    ):
        self.stdout("Preparing timer...")

        timer = None
        if enable_auto_stop:
            timer = TimerInstance(name="Forever Generation/LoRA Timer")
            if stop_mode == "After Minutes":
                timer.set_end_at(time.time() + stop_minutes * 60)
            elif stop_mode == "At Datetime":
                try:
                    timer.end_at_dt(timer.dtparse(stop_after_datetime))
                except ValueError as e:
                    raise gr.Error(f"Invalid datetime format: {e}")
            elif stop_mode == "After Images":
                self.stop_after_n_of_img = stop_after_img
                timer = False
            if timer is None:
                raise gr.Error("Timer is not set. Please enable stop mode.")
        
        self.timer = timer
        self.enable_auto_stop = enable_auto_stop
        self.stdout("done.")
        return timer

    async def update_prompt_settings(
        self,
        s_method: list[str], scheduler: list[str],
        steps_min: int, steps_max: int,
        cfg_min: float, cfg_max: float,
        size: str,
        disable_lora_in_adetailer: bool,
        save_tmp_images: bool,
        prompt_generation_max_tries: int,
        header: str, footer: str,
        tags: int, random_rate: float,
        prompt_weight_chance, prompt_weight_min, prompt_weight_max,
        remove_character,
        booru_filter_enable: bool,
        **kwargs
    ): 
        """
        一時停止せずにself内の引数を変えるためのやつ
        """
        await self.on_update_prompt_settings(**self.resize_locals(locals()|kwargs))
        
        self.disable_lora_in_adetailer = disable_lora_in_adetailer
        self.sampling_methods = s_method
        self.schedulers = scheduler
        self.steps = (steps_min, steps_max)
        self.cfg_scales = (cfg_min, cfg_max)
        s = []
        for si in size.split(","):
            w, h = si.split(":")
            s.append((int(w), int(h)))
        self.sizes = s

        self.save_image_to_tmp = save_tmp_images
        self.prompt_generation_max_tries = min(5000000, max(1, prompt_generation_max_tries)) # 1 ~ 5,000,000
        
        new_param = {
            "header": header,
            "footer": footer,
            "tags": tags,
            "random_rate": random_rate,
            "prompt_weight_chance": prompt_weight_chance,
            "prompt_weight_min": prompt_weight_min,
            "prompt_weight_max": prompt_weight_max,
        } | setting.request_param(pop_for_processor=True)
        new_kp = {
            "remove_character": remove_character,
        }
        new_param, new_kp, is_valid = await self.test_new_setting(new_param, new_kp)
        
        if is_valid is True:
            self.default_prompt_request_param = new_param
            gr.Info("Prompt settings updated successfully.")
            self.stdout("Prompt settings updated successfully.")
        else:
            raise gr.Error("Failed to update prompt settings. Please check your settings.")

        self.processor_prompt_param = new_kp
        self.default_prompt_request_param = new_param
        self.booru_filter_enabled = booru_filter_enable
        
    
    
    async def prepare_caption_model(
        self,
        booru_filter_enable: bool, booru_model: str,
        **kwargs
    ):
        caption: OnnxRuntimeTagger = None
        if booru_filter_enable:
            caption = OnnxRuntimeTagger(model_path=booru_model, find_path=True)
            self.stdout(f"[Booru] Caption model loaded. ({booru_model})")
            
        self.booru_filter_enabled = booru_filter_enable
        self.booru_model = caption
    
    ###########################
    ##### Event Listeners #####
    # override
    async def on_loop_start(self, i: ForeverGenerationResponse, **kw):
        """ループ開始時毎回呼ばれる"""
        return 
    
    # override
    async def on_iter_start(self, i: ForeverGenerationResponse, **kw):
        """画像生成完了後のループ開始時に１度呼ばれる、生成完了ごとに毎回呼ばれる"""
        return
    
    # override
    async def on_in_progress(
        self, i: ForeverGenerationResponse,
        p: GenerationProgress, **kw
    ):
        """画像生成中に進捗が更新されるたびに呼ばれる
        pに行った変更は保持されてeta, prg, pb_htmlに反映される"""
        return
    
    # override
    async def on_generation_complete_now(
        self, i: ForeverGenerationResponse,
        p: GenerationResult, **kw
    ):
        """画像生成が完了した瞬間に呼ばれる"""
        return
    
    # override
    async def on_image_skipped(
        self, i: ForeverGenerationResponse,
        type: Literal["in_progress", "after_generation_complete", "in_adetailer", "after_all_complete"],
        image: Optional[Image.Image | list[Image.Image]] = None,
    ):
        """画像がスキップされ、実際に消去されるタイミングで呼ばれる
        画像は渡されないかもしれない"""
        return

    async def on_save_temp_image(
        self, images: list[Image.Image], reason: str
    ) -> bool | None:
        """
        skipされた画像などを保存する際に呼ばれる
        return: 保存するかどうか
        """
        return True
    
    async def on_booru_early_filter(
        self, i: ForeverGenerationResponse, p: GenerationResult,
        **kwargs
    ) -> tuple[bool, list[Image.Image]]:
        """
        ADetailer処理前に画像をフィルタする
        返り値: (through, to_proc)
        
        through: Trueの場合 to_proc をそのまま帰す
        to_proc: フィルタ後に処理する画像リスト
        """
        return False, None
    
    async def on_prepare_adetailer(
        self, p: GenerationResult, 
        adp: dict,
        **kw
    ) -> dict:
        """
        Adetailer param用意完了時に呼ばれる
        再処理したい場合はdictを返す
        """
        return adp
    
    async def on_before_save_images(
        self, image: list[Image.Image],
        p: GenerationResult, **kw
    ) -> bool:
        """
        画像保存前に呼ばれる
        return: 画像保存を続行しないかどうか
        """
        return False
    
    def on_reset(self):
        """
        reset()実行時に呼ばれる
        """
        return
    
    async def on_update_prompt_settings(
        self, **kw
    ): return
    ###########################
    ###########################
    
    async def check_stop_conditions(self) -> bool:
        # after n of img
        if self.num_of_image >= self.stop_after_n_of_img:
            self.stdout(
                f"Stopping generation due to image limit ({self.stop_after_n_of_img} images reached). (loop: {self.num_of_loop} | iter: {self.num_of_iter})"
            )
            self.skipped_by = "[User Setting] image Limit"
            self.skipped()
            return True
        
        # timer
        if self.num_of_iter != self.prv_generation_c:
            # 生成開始時にのみ止める
            if self.timer and self.timer.is_done():
                self.stdout(
                    f"Stopping generation due to timer expiration. (image: {self.num_of_iter}) (loop: {self.num_of_loop} | iter: {self.num_of_iter})"
                )
                self.skipped_by = "[User Setting] Timer Expiration"
                self.skipped()
                return True
            
        return False

    async def save_tmp_image(
        self, images: list[Image.Image], 
        reason: Literal["after_generation_complete_skipped", "after_generation_complete_skipped"],
    ):
        if not self.save_image_to_tmp:
            return
        if not await self.on_save_temp_image(images, reason) is True:
            return
        
        for index, image_obj in enumerate(images, start=0):
            image_obj.save(
                f"./tmp/img/generated_skipped_{self.num_of_iter}_{index}-{self.num_of_loop}-{sha256(image_obj.tobytes())}.png"
            )
        return
    
    async def booru_filter(
        self, i: ForeverGenerationResponse, p: GenerationResult,
        images: list[Image.Image], is_early: bool = True,
        **kwargs
    ) -> list[Image.Image]:
        if not self.booru_filter_enabled:
            return images
        if not self.early_booru_filter and is_early:
            return images
        if not booru_filter.get("save_each_rate", False) and not is_early and self.early_booru_filter:
            return images
        if not is_early:
            p._booru_image_bridge = images
        
        through, to_proc = await self.on_booru_early_filter(i, p, **kwargs)
        if through: return to_proc
        to_proc = []
        
        await self.booru_model.load_model_cuda()
        self.stdout("Processing image with Booru Filter..")
        to_proc = await self.caption_filter(
            self.booru_model, p,
            before_adetailer=True
        )
        await self.booru_model.unload_model()
        self.stdout("Booru Filter processing done.")
        return to_proc
    
    async def prepare_adetailer(
        self, p: GenerationResult
    ) -> dict:
        adp = self.adetailer_param
        try:
            ad_prompt = p.prompt
            if self.disable_lora_in_adetailer:
                ad_prompt = ", ".join(
                    [
                        p
                        for p in ad_prompt.split(",")
                        if not is_lora_trigger(p.strip())
                    ]
                )
            adp["ADetailer"]["args"][2]["ad_prompt"] = ad_prompt
            adp["ADetailer"]["args"][3]["ad_prompt"] = ad_prompt
            adp.update(self.freeu_param)
            adp.update(self.neveroom_param)
            adp.update(self.sag_param)
            
        except (IndexError, KeyError):
            self.stdout(
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
                "steps": self.adetailer_steps,
                "alwayson_scripts": adp,
            }
        
        return await self.on_prepare_adetailer(p, ad_param)

    async def run_loop(
        self, 
        adetailer: bool, 
        output_dir,
        output_format,
        output_name,
        save_metadata,
        save_infotext,
        **kw
    ): # -> eta, progress(text), progress_bar(html), preview image, stdout, image_skipped, is_stopping
        eta: str = ""
        progress: str = ""
        progress_bar_html: str = ""
        
        async for i in self.start_generation():
            i: ForeverGenerationResponse
            if await self.check_stop_conditions(): break
            
            self.num_of_loop += 1
            await self.on_loop_start(i)
            
            if self.num_of_iter != self.prv_generation_c:
                await self.on_iter_start(i)
                yield self.stdnow(
                    f"Starting generation ({self.num_of_iter + 1} / inf) with Prompt: {i.payload.get('prompt', 'N/A')}",
                    silent=True,
                )
                self.prv_generation_c = self.num_of_iter

            ok = i.ok
            status = i.status
            if status == i.IN_PROGRESS:
                p: GenerationProgress = i.get_progress()
                await self.on_in_progress(i, p)
                
                eta = self.resize_eta(p.eta)
                progress = self.resize_steps(p.step, p.total_steps)
                progress_bar_html = self.resize_progress_bar(p.progress, p.eta)
                image = await p.convert_image()
                
                yield self.yielding(eta, progress, progress_bar_html, image)
            
            elif status == i.ERROR:
                err_msg = i.get_error_message()
                yield self.stdnow(f"Generation error: {err_msg} ({self.generation_error_count})")
                gr.Warning(f"Generation error: {err_msg}")
                if self.generation_error_count > self.generation_error_count_limit:
                    yield self.stdnow("Too many generation errors. Stopping generation.")
                    self.skipped_by = "Too many generation errors"
                    self.skipped()
                    break
                self.generation_error_count += 1
            
            elif ok and status == i.COMPLETED:
                p: GenerationResult = i.get_result()
                await self.on_generation_complete_now(i, p)
                
                self.num_of_iter += 1
                eta = "N/A"
                progress = "100%"
                progress_bar_html = self.resize_progress_bar(100, -1)
                image = await p.convert_images_into_gr()
                
                if self.image_skipped:
                    self.skipped()
                    await self.on_image_skipped(i, type="after_generation_complete", image=await p.convert_images())
                    await self.save_tmp_image(await p.convert_images(), reason="after_generation_complete_skipped")
                    continue
                
                self.num_of_image += len(p.images)
                to_proc = await self.booru_filter(i, p, await p.convert_images(), is_early=True, **kw)
                
                if adetailer:
                    ad_param = await self.prepare_adetailer(p)
                    yield self.yielding(
                        eta, progress, progress_bar_html, image,
                        self.stdout(f"Generation completed. Processing ADetailer.. ({len(to_proc)})"),
                        self.image_skipped,
                    )
                    ad_api = ADetailerAPI(ad_param)
                    images = []
                    for index, proc in enumerate(to_proc, start=1):
                        if self.image_skipped:
                            yield self.stdnow("AD-Image skipped by skip event.")
                            await self.on_image_skipped(i, type="in_adetailer")
                            continue
                        
                        yield self.stdnow(
                            f"[{index}/{len(to_proc)}] Processing image with ADetailer.."
                        )
                        async for processing in ad_api.generate_with_progress(
                            init_images=[proc]
                        ):
                            if processing[0] is False:
                                pr: GenerationProgress = processing[2]
                                eta_ = self.resize_eta(pr.eta)
                                progress_ = self.resize_steps(
                                    pr.step, pr.total_steps
                                )
                                progress_bar_html_ = self.resize_progress_bar(
                                        pr.progress, pr.eta
                                    )
                                yield self.yielding(
                                    eta_,
                                    progress_,
                                    progress_bar_html_,
                                    await pr.convert_image_into_gr(),
                                    self.stdout(),
                                )
                                await asyncio.sleep(1.5)  # Prevent OSError
                            elif processing[0] is True:
                                result: ADetailerResult = processing[1]
                                
                                if self.image_skipped_adetailer:
                                    yield self.stdnow(f"AD-Image skipped by skip event. ({index}/{len(to_proc)})")
                                    
                                else:
                                    images += await result.convert_images()
                                    yield self.yielding(
                                        image=await result.convert_images_into_gr(),
                                        stdout=self.stdout(
                                            f"[{index}/{len(to_proc)}] ADetailer completed."
                                        ),
                                        skip_override=self.image_skipped_adetailer
                                    )
                            
                else:
                    yield self.yielding(
                        eta, progress, progress_bar_html, image,
                        self.stdout(f"Generation completed. ({len(to_proc)})"),
                        self.image_skipped,
                    )
                    images = to_proc # fallback: ADetailer無効時
                
                images = await self.booru_filter(i, p, images, is_early=False, **kw)
                
                # 最終skipチェック
                if self.image_skipped:
                    self.skipped()
                    await self.on_image_skipped(i, type="after_all_complete", image=images)
                    await self.save_tmp_image(images, reason="after_generation_complete_skipped")
                    continue
                
                skip_save = await self.on_before_save_images(images, p, output_dir=output_dir, output_format=output_format, output_name=output_name, save_metadata=save_metadata, save_infotext=save_infotext, **kw)
                if not skip_save:
                    for index, image_obj in enumerate(images):
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
                        yield self.yielding(
                            eta="100%", progress="100%", progress_bar_html=self.resize_progress_bar(100, -1),
                            stdout=self.stdout(f"[{index+1}/{len(images)}] Image saved as {fn}"),
                            image=image_obj
                            )
                yield self.yielding(
                    eta="N/A", progress="N/A", progress_bar_html=self.resize_progress_bar(0, -1), image=gr.Image(value=None, interactive=False),
                )
                
        self.skipped()
        yield self.yielding(
            eta="N/A", progress="N/A", progress_bar_html=self.resize_progress_bar(0, -1), image=gr.Image(value=None, interactive=False),
            stdout=self.stdout("Generation Stopped."),
        )

    async def stop_generation(self):
        self.stop_after_n_of_img = 2140000000
        self.image_skipped = False
        self.skipped_by = "User"
        gr.Warning("Generation will be stop after this iteration.")
        await super().stop_generation()
    async def stop_generation_by_state_manager(self, sm: StateManager) -> str: # TODO
        await self.stop_generation()
    
    
    async def caption_filter( # TODO: rewrite
        self,
        caption: OnnxRuntimeTagger,
        p: GenerationResult,
        before_adetailer: bool = True,
    ) -> list[str] | list[Image.Image]:  # base64 encoded images
        """
        booruでなんやかんやして画像をフィルタリングする
        okな画像はそのままで返す

        before_adetailer の場合は list[b64img] を返し、
        after_adetailer の場合は list[Image.Image] を返す
        """
        opt = booru_filter.into_options()
        def save_blacklisted_image(
            i: Image.Image,
            rate: str,
        ):
            if not opt.booru_separate_save:
                return
            self.stdout(f"[Caption]: Saving blacklisted image with rate: {rate}")
            os.makedirs(opt.booru_blacklist_save_dir, exist_ok=True)
            fn = f"[{rate}] {p.seed} - " + sha256(i.tobytes()) + ".png"
            fp = os.path.join(opt.booru_blacklist_save_dir, fn)
            info = PngImagePlugin.PngInfo()
            info.add_text("parameters", p.infotext)
            i.save(fp, format="PNG", pnginfo=info)
            self.stdout(f"[Caption]: Blacklisted image saved as {fp}")
            return

        def save_separated_rate(
            i: Image.Image,
            rate: str,
        ):
            if not opt.booru_save_each_rate:
                return
            self.stdout(f"[Caption]: Saving image with rate: {rate}")
            DATE = time.strftime("%Y-%m-%d")
            if rate == "general" or (rate == "sensitive" and opt.booru_merge_sensitive):
                fp = opt.general_save_dir.format(DATE=DATE)
            elif rate == "sensitive":
                fp = opt.sensitive_save_dir.format(DATE=DATE)
            elif rate == "questionable":
                fp = opt.questionable_save_dir.format(DATE=DATE)
            elif rate == "explicit":
                fp = opt.explicit_save_dir.format(DATE=DATE)
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

        if before_adetailer and opt.booru_separate_save:
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
                threshold=opt.booru_threshold,
                character_threshold=opt.booru_character_threshold,
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

            if opt.booru_ignore_questionable and rate == "questionable":
                d = rating.copy()
                d.pop("questionable", None)
                rate = max(d, key=d.get, default="general")
                self.stdout(f"Ignoring questionable rating. (questionable -> {rate})")
            if not rate in opt.booru_allow_rating and not opt.booru_save_each_rate:
                save_blacklisted_image(img, rate)
                continue

            # blacklist check
            b = self.booru_blacklist

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

            if opt.booru_save_each_rate and not before_adetailer:
                save_separated_rate(image, rate)
            else:
                allow_image.append(img)
        return allow_image