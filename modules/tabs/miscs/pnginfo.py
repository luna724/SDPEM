from webui import UiTabs
import gradio as gr
import os
import shared
from typing import Callable
from utils import *

import json
from PIL import Image
from modules.prompt_setting import setting
from modules.utils.ui.globals import get_components
from modules.utils.ui.register import RegisterComponent, Path
import modules.utils.ui.js as js

class PngInfo(UiTabs):
    def title(self) -> str:
        return "PNGInfo"
    def index(self) -> int:
        return 3
    def ui(self, outlet: Callable[[str, gr.components.Component], None]) -> None:
        async def read_pnginfo(
            img: Image.Image,
            clear_image: bool, only_prompt: bool, show_raw: bool
        ) -> tuple[str, Image.Image|None]:
            if img is None: raise gr.Error("No image provided")
            if not hasattr(img, "info"):
                raise gr.Error("Image has no metadata")
            
            info = img.info
            if show_raw: i = json.dumps(info, indent=2, ensure_ascii=False)
            else: i = info.get("parameters", "")
            if clear_image: img = None
            if only_prompt: i = i.split("\nNegative prompt: ")[0].strip()
            return i, img
        async def read_pnginfo_onchange(i, *args, **kw):
            if i is not None: return await read_pnginfo(i, *args, **kw)
            return gr.update(), gr.update()
        
        pnginfo = RegisterComponent(
            Path("./defaults/miscs.pnginfo.json"),
            "miscs/pnginfo"
        )
        r = pnginfo.register
        default = pnginfo.get()
        
        with gr.Row():
            in_image = gr.Image(
                type="pil",
                image_mode="RGBA",
                label="Input PNG image",
                source="upload", show_download_button=False
            )
        
            out_info = gr.Textbox(
                label="Info",
                placeholder="The PNG info will appear here",
                lines=8,
                max_lines=400,
                interactive=False, show_copy_button=True
            )
        
        with gr.Row():
            clear_image = r(
                "clear_image",
                gr.Checkbox(label="Clear input image after read", value=default.clear_image), order=1
            )
            only_prompt = r(
                "only_prompt",
                gr.Checkbox(label="Only extract prompt", value=default.only_prompt), order=1
            )
            show_raw = r(
                "show_raw",
                gr.Checkbox(label="Show raw metadata", value=default.show_raw), order=2
            )

        run = gr.Button("Read", variant="primary")
        run.click(
            fn=read_pnginfo,
            inputs=[in_image, clear_image, only_prompt, show_raw],
            outputs=[out_info, in_image]
        )
        in_image.change(
            fn=read_pnginfo_onchange,
            inputs=[in_image, clear_image, only_prompt, show_raw],
            outputs=[out_info, in_image]
        )
        in_image.change(
            fn=pnginfo.insta_save,
            inputs=pnginfo.values(),
        )
        
        def through(v): return v
        adv_out = get_components("miscs/pnginfo_advanced").components.get("in_image")
        if adv_out:
            send_advanced = gr.Button("Send PngInfo+")
            send_advanced.click(
                fn=through,
                inputs=[in_image],
                outputs=[adv_out],
            ).then(
                fn=None,
                _js=js.click("pnginfo_advanced_tab-button")
            )
        else:
            gr.Markdown("`PngInfo+` is not available.")