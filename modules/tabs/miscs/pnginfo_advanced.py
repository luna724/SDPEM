from webui import UiTabs
import gradio as gr
import os
import shared
from typing import Callable
from utils import *

import json
from PIL import Image
from modules.utils.ui.register import RegisterComponent, Path
from modules.prompt_setting import setting
from modules.utils.ui.globals import get_components
from modules.tagger.predictor import OnnxRuntimeTagger

class PngInfo(UiTabs):
    def title(self) -> str:
        return "PNGInfo+"
    def _id(self) -> str:
        return "pnginfo_advanced_tab"
    def index(self) -> int:
        return 2
    def ui(self, outlet: Callable[[str, gr.components.Component], None]) -> None:
        async def read_pnginfo(
            img: Image.Image, 
            do_booru, booru_model, thres: float,
            apt: str = "", bapt: str = ""
        ): 
            if img is None: return gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
            if not hasattr(img, "info"):
                raise gr.Error("Image has no metadata")
            info = img.info
            prompt = info.get("parameters", "").split("\nNegative prompt: ")[0].strip()
            blacklist = setting.obtain_blacklist()
            
            filtered = []
            p = []
            for tag in prompt.split(","):
                tag = tag.strip()
                if not any(b.search(tag) for b in blacklist):
                    p.append(tag)
                else:
                    filtered.append(tag)
            filtered_out = ", ".join(p)
            filtered_tags = ", ".join(filtered)
            apts = set(apt.split(", "))
            b_apts = set(bapt.split(", "))
            apts.update(set(p))
            
            booru_out = None
            rate = "?"
            if do_booru:
                try:
                    i = OnnxRuntimeTagger(booru_model, find_path=True)
                    await i.load_model_cuda()
                    bt, _, rate = await i.predict(
                        img, threshold=thres, character_threshold=0.9
                    )
                    bts = [
                            x[0]
                            for x in sorted(
                                bt.items(), key=lambda x: x[1], reverse=True
                            )
                        ]
                    booru_out = ", ".join(bts)
                    rate = " > ".join(
                        [
                            x[0]
                            for x in sorted(
                                rate.items(), key=lambda x: x[1], reverse=True
                            )
                        ][:1]
                    )
                    b_apts.update(set(bts))
                except:
                    import traceback; traceback.print_exc();
                    gr.Warning("Failed to run booru tagger")


            return prompt, filtered_out, filtered_tags, booru_out, rate, ", ".join(apts), ", ".join(b_apts)

        pnginfo_advanced = RegisterComponent(
            Path("./defaults/miscs.pnginfo_advanced.json"),
            "miscs/pnginfo_advanced"
        )
        r = pnginfo_advanced.register
        default = pnginfo_advanced.get()
        
        with gr.Row():
            in_image = r(
                "in_image",
                gr.Image(
                    type="pil",
                    image_mode="RGBA",
                    label="Input PNG image",
                    sources="upload", show_download_button=False,
                    interactive=True
                )
            )
        
            out_info = gr.Textbox(
                    label="Prompt",
                    placeholder="The embed prompt will appear here",
                    lines=8,
                    max_lines=400,
                    interactive=False, show_copy_button=True
                )
        
        filtered_out = gr.Textbox(
            label="Filtered Prompt", interactive=False, lines=2, max_lines=400, show_copy_button=True 
        )
        filtered_tags = gr.Textbox(
            label="Filtered Tags", interactive=False, lines=1, max_lines=400, show_copy_button=True 
        )
        with gr.Row():
            booru_out = gr.Textbox(
                label="Booru output", interactive=False, lines=2, max_lines=400, show_copy_button=True,
                scale=9
            )
            booru_rate = gr.Textbox(
                label="Booru rating", interactive=False, lines=1, max_lines=100, scale=1
            )
        
        with gr.Accordion("booru Settings", open=True):
            do_booru = r(
                "do_booru",
                gr.Checkbox(label="Do Booru tagger", value=default.do_booru), order=1
            )
            
            with gr.Row():
                booru_model = r(
                    "booru_model",
                    gr.Dropdown(
                        choices=[x["display_name"] for x in shared.models["wd-tagger"]],
                        value=default.booru_model,
                        label="Booru tagger model",
                    ), order=2
                )
                booru_threshold = r(
                    "booru_threshold",
                    gr.Slider(
                        0.0,
                        1.0,
                        step=0.01,
                        value=default.booru_threshold,
                        label="Booru tagger threshold",
                    ), order=3
                )
        
        with gr.Accordion("Appeared Tags", open=True):
            with gr.Row():
                appeared_tags = gr.Textbox(
                    label="Appeared Tags", interactive=False, lines=5, max_lines=400
                )
                booru_appeared_tags = gr.Textbox(
                    label="Booru Appeared Tags", interactive=False, lines=5, max_lines=400
                )
            clear_appeared = gr.Button("Clear Appeared Tags")
            def clear(): return "", ""
            clear_appeared.click(
                fn=clear,
                outputs=[appeared_tags, booru_appeared_tags]
            )
        
        with gr.Accordion("Memo", open=False):
            with gr.Row():
                to_blacklist = r(
                    "to_blacklist",
                    gr.Textbox(
                        label="To Blacklist (memo)",
                        lines=5,
                        max_lines=400, interactive=True,
                        show_copy_button=True
                    ),
                )
                to_booru_blacklist = r(
                    "to_booru_blacklist",
                    gr.Textbox(
                        label="To Booru Blacklist(separate by comma)",
                        lines=5,
                        max_lines=400, interactive=True,
                        show_copy_button=True
                    ),
                )
        
        in_image.change(
            fn=read_pnginfo,
            inputs=[in_image, do_booru, booru_model, booru_threshold],
            outputs=[out_info, filtered_out, filtered_tags, booru_out, booru_rate, appeared_tags, booru_appeared_tags],
        )
        async def save(*values):
            pnginfo_advanced.save(values, dont_saves=["in_image"])
        save_inputs = [c for k, c in pnginfo_advanced.components.items() if k != "in_image"]
        in_image.change(
            fn=save,
            inputs=save_inputs,
        )