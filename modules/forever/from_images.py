import os
import re
from typing import Pattern

import gradio as gr
from PIL import Image

from modules.forever.common import ForeverGenerationTemplate
from modules.prompt_processor import PromptProcessor
from modules.utils.pnginfo import read_pnginfo
from modules.utils.prompt import separate_prompt

from logger import println, debug

class ForeverGenerationFromImages(ForeverGenerationTemplate):
    def __init__(self):
        super().__init__()
        self.instance_name = "from_images"
        self.special_blacklist: list[Pattern[str]] = []

    def on_reset(self):
        self.use_images = []
        self.use_tags = {}
        self.tc_weight_multiplier = 1.0
    
    async def test_new_setting(self, new_param, new_kp):
        return await super().test_new_setting(new_param, new_kp)
    
    def _compile_special_blacklist(self, blacklist: str | None) -> list[Pattern[str]]:
        if not blacklist:
            return []

        patterns: list[Pattern[str]] = []
        for raw_line in blacklist.splitlines():
            parts = [segment.strip() for segment in raw_line.split(",")]
            for entry in parts:
                if not entry:
                    continue
                try:
                    compiled = re.compile(entry, re.IGNORECASE)
                except re.error as exc:
                    self.stdout(
                        f"[Instance Blacklist] Ignored invalid pattern '{entry}': {exc}"
                    )
                    continue
                patterns.append(compiled)

        if patterns:
            self.stdout(
                f"[Instance Blacklist] Loaded {len(patterns)} temporary pattern(s)."
            )
        return patterns

    async def prepare_param(
        self,
        negative: str,
        batch_size: int,
        batch_count: int,
        adetailer: bool,
        enable_hand_tap: bool,
        disable_lora_in_adetailer: bool,
        enable_freeu: bool,
        freeu_preset: str,
        enable_neveroom_unet: bool,
        enable_neveroom_vae: bool,
        enable_sag: bool,
        sag_strength: float,
        instance_blacklist: str | None = None,
        **kwargs,
    ):
        self.special_blacklist = self._compile_special_blacklist(instance_blacklist)
        await super().prepare_param(
            negative=negative,
            batch_size=batch_size,
            batch_count=batch_count,
            adetailer=adetailer,
            enable_hand_tap=enable_hand_tap,
            disable_lora_in_adetailer=disable_lora_in_adetailer,
            enable_freeu=enable_freeu,
            freeu_preset=freeu_preset,
            enable_neveroom_unet=enable_neveroom_unet,
            enable_neveroom_vae=enable_neveroom_vae,
            enable_sag=enable_sag,
            sag_strength=sag_strength,
            **kwargs,
        )

    async def on_update_prompt_settings(
        self, use_images, use_folder, tag_count_weight,
        instance_blacklist: str | None = None,
        **kw
    ):
        if use_images is None: use_images = []
        if use_folder is None: use_folder = []

        imagefiles = set()
        for i in use_images:
            if os.path.exists(i) and os.path.isfile(i) and i.lower().endswith((".png",".jpg",".jpeg")):
                imagefiles.add(i)

        for i in use_folder:
            if os.path.exists(i) and os.path.isdir(i):
                for f in os.listdir(i):
                    fp = os.path.join(i, f)
                    if os.path.isfile(fp) and f.lower().endswith((".png",".jpg",".jpeg")):
                        imagefiles.add(fp)
        if len(imagefiles) == 0:
            raise gr.Error("No valid image files found in the provided paths.")
        self.stdout(f"Found {len(imagefiles)} image files.")
        
        self.use_images = list(imagefiles)
        self.tc_weight_multiplier = tag_count_weight

        proceed = 0
        tags = {}
        for fp in self.use_images:
            if not os.path.exists(fp):
                debug(f"File not found: {fp}")
                continue
            
            try:
                img = Image.open(fp)
                img.verify()
                prompt, _ = await read_pnginfo(img, False, True, False)
                img.close()
                
                for t in separate_prompt(prompt):
                    if t in tags:
                        tags[t] += 1
                    else:
                        tags[t] = 1
                proceed += 1
            except Exception as e:
                debug(f"Failed to process image {fp}: {e}")
                continue
        
        self.use_tags = {k:0.1*(v*self.tc_weight_multiplier) for k,v in tags.items()}
    
    async def get_payload(self):
        p = await super()._get_payload()
        
        proc_kw = dict(self.processor_prompt_param)
        if self.special_blacklist:
            proc_kw["special_blacklist"] = self.special_blacklist

        try:
            prompt = await PromptProcessor.from_frequency_like(
                fq=self.use_tags,
                max_tries=self.prompt_generation_max_tries,
                proc_kw=proc_kw,
                finalize=True,
                **self.default_prompt_request_param,
            )
        except ValueError as e:
            raise gr.Error(
                f"Failed to generate prompt. Please check your Prompt Settings. ({e})"
            )
        except RuntimeError:
            raise gr.Error(
                "Failed to generate prompt after multiple attempts. Please adjust your Prompt Settings."
            )
        p["prompt"] = ", ".join(prompt)
        return p

    async def start(
        self,
        header,
        footer,
        tags,
        random_rate,
        add_lora_name,
        s_method,
        scheduler,
        steps_min,
        steps_max,
        cfg_min,
        cfg_max,
        batch_count,
        batch_size,
        size,
        adetailer,
        enable_hand_tap,
        disable_lora_in_adetailer,
        enable_freeu,
        freeu_preset,
        negative,
        enable_sag,
        sag_strength,
        use_images,
        use_folder,
        tag_count_weight,
        remove_character,
        save_tmp_images,
        prompt_generation_max_tries,
        prompt_weight_chance,
        prompt_weight_min,
        prompt_weight_max,
        instance_blacklist,
        output_dir,
        output_format,
        output_name,
        save_metadata,
        save_infotext,
        booru_filter_enable,
        booru_model,
        enable_neveroom_unet,
        enable_neveroom_vae,
        enable_auto_stop,
        stop_mode,
        stop_minutes,
        stop_after_img,
        stop_after_datetime,
    ):
        async for i in super().start(**self.resize_locals(locals())):
            yield i
