import asyncio
import os
import re
import time
from modules.forever_generation import ForeverGeneration
from typing import *
from PIL import Image, PngImagePlugin
from modules.adetailer import ADetailerAPI, ADetailerResult
from modules.generate import GenerationProgress, GenerationResult, Txt2imgAPI
import gradio as gr
import random
from modules.utils.timer import TimerInstance
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

        self.sampling_methods: list[str]
        self.schedulers: list[str]
        self.auto_cast_scheduler = False
        self.steps: tuple[int, int]
        self.cfg_scales: tuple[float, float]
        self.sizes: list[tuple[int, int]]
        self.lora_names: list[str]
        self.disable_lora_in_adetailer: bool

        self.n_of_img = 2140000000
        self.image_skipped = False
        self.skipped_by = "User"

    async def get_payload(self) -> dict:
        p = self.param.copy()
        prompt_rq = await shared.session.post(
            url=f"{shared.pem_api}/v1/generator/lora/lora2prompt",
            json=self.default_prompt_request_param,
        )
        if prompt_rq.status_code != 200:
            if prompt_rq.status_code == 422:
                print_critical(
                    "API Error: ", prompt_rq.json()[0].get("message", "Unknown error")
                )
            raise gr.Error(f"Failed to call API ({prompt_rq.status_code})")
        prompt = prompt_rq.json()[0].get("prompt", "")
        if prompt == "":
            raise gr.Error(
                "Failed to generate prompt. Please check your Prompt Settings."
            )

        sampler = random.choice(self.sampling_methods)
        scheduler = random.choice(self.schedulers)
        # TODO: Implement auto-casting for scheduler
        step = random.randint(self.steps[0], self.steps[1])
        cfg_scale = (
            random.randrange(self.cfg_scales[0] * 10, self.cfg_scales[1] * 10, 5) / 10
        )
        size = random.choice(self.sizes)
        w = size[0]
        h = size[1]

        p.update(
            {
                "prompt": prompt,
                "sampler_name": sampler,
                "scheduler": scheduler,
                "steps": step,
                "cfg_scale": cfg_scale,
                "width": w,
                "height": h,
            }
        )

        p.update(self.freeu_param)
        return p

    # @override
    async def start(
        self,
        lora: list[str],
        blacklist: str,
        pattern_blacklist: str,
        blacklist_multiplier: float,
        use_relative_freq: bool,
        w_multiplier: float,
        w_min: int,
        w_max: int,
        disallow_duplicate: bool,
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
        output_dir, output_format, output_name,
        save_metadata, save_infotext
    ) -> AsyncGenerator[tuple[str, Image.Image], None]:
        self.default_prompt_request_param = {
            "lora_name": lora,
            "blacklist": blacklist.split(",") if blacklist else [],
            "black_patterns": (
                pattern_blacklist.splitlines() if pattern_blacklist else []
            ),
            "blacklisted_weight": blacklist_multiplier,
            "use_relative_freq": use_relative_freq,
            "weight_multiplier": w_multiplier,
            "weight_multiplier_target": [w_min, w_max],
            "disallow_duplicate": disallow_duplicate,
            "header": header,
            "footer": footer,
            "max_tags": max_tags,
            "base_chance": base_chance,
            "lora_weight": lora_weight,
            "add_lora_name": add_lora_name,
        }
        # テスト呼び出し + 必要ならLoRA名取得
        response = await shared.session.post(
            url=f"{shared.pem_api}/v1/generator/lora/lora2prompt",
            json=self.default_prompt_request_param,
        )
        if response.status_code != 200 or response.json()[0].get("prompt", "") == "":
            raise gr.Error(
                f"Failed to call API or generate prompt. check your Prompt Settings ({response.status_code})"
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

        timer = None
        if enable_stop:
            timer = TimerInstance(name="Forever Generation/LoRA Timer")
            if stop_mode == "After Minutes":
                timer.end_at(time.time() + stop_min * 60)
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

        eta = ""
        progress = ""
        progress_bar_html = ""
        num_of_loop = 1
        num_of_iter = 0
        num_of_image = 0
        prv_generation_c = None
        async for i in self.start_generation():
            # 停止チェック
            if timer and timer.is_done():
                self.stdout(
                    f"Stopping generation due to timer expiration. (image: {num_of_iter}) (loop: {num_of_loop} | iter: {num_of_iter})"
                )
                self.skipped_by = "[User Setting] Timer Expiration"
                self.skipped()
                break

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
                yield (eta, progress, progress_bar_html, image, self.stdout())
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
                        printwarn(
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
                                )
                else:
                    images = await p.convert_images()

                if self.image_skipped:
                    self.skipped()
                    continue

                # TODO: Implement Image Filter (Before Save)
                for index, image_obj in enumerate(images, start=0):
                  image_obj.save(f"./tmp/img/generated_{num_of_iter}_{index}-{num_of_loop}.png")
                  
                
                  DATE = time.strftime("%Y-%m-%d")
                  fp = output_dir.format(DATE=DATE)
                  os.makedirs(fp, exist_ok=True)                  
                  img_files = sorted([f
                    for f in os.listdir(fp)
                    if re.match(r"^\d{5}-\d+.png$", f) is not None
                  ], key=lambda x: int(x.split("-")[0]))
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
                    info = PngImagePlugin.PngInfo()
                    info.add_text("parameters", txtinfo)
                    image_obj.save(
                      fn, format=output_format, pnginfo=info
                    )
                  else:
                    image_obj.save(fn, format=output_format)
                  self.stdout(f"[{index}/{len(images)}] Image saved as {fn}")

                yield (eta, progress, progress_bar_html, image_obj, self.stdout())
            elif not ok and status == "error":
                raise gr.Error("Generation failed due to an error.")
        yield (
            "N/A",
            "N/A",
            LegacyImageProgressAPI.progress_bar_html(0, -1),
            None,
            self.stdout("Generation Stopped."),
        )
  
    async def stop_generation(self):
      self.n_of_img = 2140000000
      self.image_skipped = False
      self.skipped_by = "User"
      gr.Warning("Generation will be stop after this iteration.")
      await super().stop_generation()