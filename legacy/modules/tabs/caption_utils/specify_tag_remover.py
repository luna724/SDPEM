import gradio as gr
import os

import shared
from modules.dataset_util.specify_tag_remover import run_ui
from webui import UiTabs

class Define(UiTabs):
    def __init__(self, path):
        super().__init__(path)

        self.child_path = os.path.join(UiTabs.PATH, "caption_utils")

    def title(self):
        return "Tag Detector"

    def index(self):
        return 2

    def ui(self, outlet):
        gr.Markdown("## Specify Tag Detector")
        with gr.Blocks():
            target_tags = gr.Textbox(
                label="Target tags (?tag to detect missing) ({src};{required} to required required src tag)", lines=2
            )
            target_tag_separator = gr.Textbox(
                label="Target tag Separator (can't use \";\", \"?\")", max_lines=1, value=","
            )

            with gr.Row():
                target_col = gr.Textbox(label="Target Column (wildcard available) (separate comma to multiselect) (not supported unchained-line eg. 1,3)", value="*")
                if_contained = gr.Textbox(label="If contained (separate with comma)", value="1girl,solo")

            with gr.Row():
                contain_mode = gr.Radio(
                    label="Contained mode (NONE to disable)", choices=[
                        "AND", "OR", "PERCENTAGE", ">COUNT", "NONE"
                    ], value="OR"
                )

            with gr.Row():
                def visibility_cm(mode):
                    if mode == "PERCENTAGE":
                        return gr.update(visible=True), gr.update(visible=False)
                    elif mode == ">COUNT":
                        return gr.update(visible=False), gr.update(visible=True)
                    return gr.update(visible=False), gr.update(visible=False)

                cm_percentage = gr.Slider(
                    label="Percentage", minimum=0, maximum=100, value=100, step=1,
                    visible=False
                )
                cm_count = gr.Slider(
                    label="Count", minimum=0, maximum=100, value=1, step=1,
                    visible=False
                )
            contain_mode.input(
                visibility_cm, [contain_mode], [cm_percentage, cm_count]
            )

            warn_mode = gr.Checkbox(label="WARNING Mode (only notice, don't auto-resize caption)", value=True, interactive=False, visible=False)
            output = gr.Textbox(label="Output", lines=4)
            infer = gr.Button("Start", variant="primary")

            default = shared.ui_obj["Caption-Util"]
            infer.click(
                run_ui,
                inputs=[default["target_dir"], default["caption_ext"], default["autoscale_caption"], default["convert_to_space"], default["convert_to_lowercase"], default["png_exist_check"]]+[
                    target_tags, target_tag_separator, target_col,
                    if_contained, contain_mode, cm_percentage, cm_count, warn_mode
                ],
                outputs=output
            )