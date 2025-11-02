import os
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
    
    def on_reset(self):
        self.use_images = []
        self.use_tags = {}
        self.tc_weight_multiplier = 1.0
    
    async def test_new_setting(self, new_param, new_kp):
        return await super().test_new_setting(new_param, new_kp)
    
    async def on_update_prompt_settings(
        self, use_images, use_folder, tag_count_weight, 
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
        
        try:
            prompt = await PromptProcessor.from_frequency_like(
                fq=self.use_tags,
                max_tries=self.prompt_generation_max_tries,
                proc_kw=self.processor_prompt_param,
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
        async for i in super().start(**self.resize_locals(locals())): yield i