import PIL.Image

import shared
from modules.image_param import ImageParamUtil
from modules.ui_util import browse_directory
from modules.util import Util
from webui import UiTabs

import os
import gradio as gr

class ParamDeleter(Util):
    def __init__(self):
        self.processor = ImageParamUtil()

    def set_as(self, image, param = None) -> PIL.Image.Image:
        self.processor.replace_param(image, param)
        return image

    def ui(self, fp, out_fp, param: str):
        if not os.path.exists(fp):
            raise gr.Error("Input Directory cannot found.")
        if out_fp == "":
            out_fp = fp
        os.makedirs(out_fp, exist_ok=True)

        images = [
            x
            for x in os.listdir(fp)
            if os.path.splitext(x)[1].lower() in [".png", ".jpg", ".jpeg"]
        ]
        for i in images:
            print(f"processing {i}..")
            img = PIL.Image.open(os.path.join(fp, i))
            img = self.set_as(img, param)
            img.save(
                os.path.join(out_fp, i+".png"), format="PNG"
            )

        gr.Info("All processes done.")

class Template(UiTabs):
    def __init__(self, path):
        super().__init__(path)
        self.child_path = os.path.join(UiTabs.PATH, "share_util_child")

    def title(self):
        return "Param-Deleter"

    def index(self):
        return 0

    def ui(self, outlet):
        module = ParamDeleter()
        with gr.Blocks():
            with gr.Row():
                batch_dir = gr.Textbox(label="Batch Directory", scale=9)
                batch_browse = gr.Button(shared.refresh_button, scale=1)
                batch_browse.click(
                    browse_directory, outputs=batch_dir
                )
            with gr.Row():
                batch_out = gr.Textbox(label="Output Directory", scale=9)
                out_browse = gr.Button(shared.refresh_button, scale=1)
                out_browse.click(
                    browse_directory, outputs=batch_out
                )

            param = gr.Textbox(label="Param Converting to", value="None")
            infer = gr.Button("Convert", variant="primary")
            infer.click(
                module.ui, [batch_dir, batch_out, param]
            )