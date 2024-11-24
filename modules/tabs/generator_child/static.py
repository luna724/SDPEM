import gradio as gr
import os

import pyperclip

import shared
from modules.static_generator import StaticGenerator
from webui import UiTabs

class Define(UiTabs):
    def __init__(self, path):
        super().__init__(path)

        self.child_path = os.path.join(UiTabs.PATH, "define_child")

    def title(self):
        return "Static"

    def index(self):
        return 2

    def ui(self, outlet):
        module = StaticGenerator()
        def show_available_templates(onInit: bool = False):
            if onInit: return list(module.load().keys())
            else: return gr.Dropdown.update(choices=list(module.load().keys()))

        def copy_image_path(template):
            _, _, _, _, directory = module.generate(template)
            pyperclip.copy(directory)
            gr.Info("Successfully copied!")

        with gr.Blocks():
            with gr.Row():
                template = gr.Dropdown(
                    label="Templates", choices=show_available_templates(True),
                    scale=6
                )
                template_refresh = gr.Button(shared.refresh_button, scale=1)
                template_refresh.click(
                    show_available_templates, outputs=template
                )
                copy_image_pth = gr.Button("Copy Param-image path", scale=3, variant="primary")
                copy_image_pth.click(
                    copy_image_path, template
                )
            with gr.Row():
                with gr.Column():
                    prompt = gr.Textbox(
                        label="Prompt (N/A)", lines=4, show_copy_button=True, interactive=False
                    )
                    negative = gr.Textbox(
                        label="Negative (N/A)", lines=4, show_copy_button=True, interactive=False
                    )
                    with gr.Row():
                        # ADetailer
                        ad_prompt = gr.Textbox(label="ADetailer Prompt", lines=2, show_copy_button=True, interactive=False)
                        ad_negative = gr.Textbox(label="ADetailer Negative", lines=2, show_copy_button=True, interactive=False)
                with gr.Column():
                    # Image
                    image = gr.Image(
                        label="Sample Image", height=0, width=0, image_mode="RGBA",
                        type="pil", interactive=False, show_share_button=True,
                        elem_id="define-static-sample_image"
                    )
            author = gr.Textbox(
                label="Template Author", interactive=False, visible=False
            )

            def visualize_template(template):
                """CSS不使用時の一時関数 ## TODO: applicate #define-static-sample_image style in CSS
                クラスを適用してもっと柔軟な表示法を求める"""
                def div_img(size:int) -> int:
                    if size > 1000:
                        return size // 2
                    return size

                prompt, negative, author, image, _ = module.generate(template)
                prompt_count = len([
                    x for x in prompt.split(",") if x != ""
                ])
                negative_count = len([
                    x for x in negative.split(",") if x != ""
                ])
                prompt_obj = gr.Textbox.update(
                    label=f"Prompt ({prompt_count})", value=prompt
                )
                negative_obj = gr.Textbox.update(
                    label=f"Negative ({negative_count})", value=negative
                )
                image_obj = gr.Image.update(
                    height=div_img(image.size[1]), width=div_img(image.size[0]), value=image
                )
                author_obj = gr.Textbox.update(
                    value=author, visible = author != ""
                )
                return prompt_obj, negative_obj, "UNSUPPORTED", "UNSUPPORTED", image_obj, author_obj

            template.input(
                visualize_template, template,
                outputs=[
                    prompt, negative, ad_prompt, ad_negative, image, author
                ]
            )