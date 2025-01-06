import gradio as gr
import os

import shared
from modules.ui_util import browse_file
from webui import UiTabs

class Generator(UiTabs):
    def __init__(self, path):
        super().__init__(path)

        self.child_path = os.path.join(UiTabs.PATH, "generator_child/image_resizer_child")

    def title(self):
        return "Background Detailer"

    def index(self):
        return 0

    def ui(self, outlet):
        with gr.Blocks():
            gr.Markdown(
                """
                ## Background Detailer
                - Detail background by using ADetailer and ControlNet
                
                - Requires a ADetailer and ControlNet to run. (install to SD-WebUI extension)
                """
            )

            with gr.Row():
                base_image = gr.Image(
                    type="pil", label="Base Image", sources=["upload"], format="png", show_download_button=False)

                resized_image = gr.Image(
                    type="pil", label="Resized Image", interactive=False, format="png", show_download_button=True)

            with gr.Row():
                with gr.Column():
                    adetailer_threshold = gr.Slider(
                        minimum=0.0, maximum=1.0, step=0.01, value=0.32, label="[ADetailer] Detection Model confidence threshold")

                    # 選択されたディレクトリに応じて表示項目を変更するコード
                    internal_adetailer_models = ["internal/person_yolov8n-seg.pt", "internal/person_yolov8s-seg.pt", "internal/yolov8x-worldv2.pt"]
                    def update_model_list() -> str | dict:
                        target_file = browse_file()
                        if "Please select file." == target_file:
                            return "Please select file."

                        # ファイルが選択されたらその親ディレクトリに含まれるファイルと同じ拡張子をすべてリストに追加
                        target_dir = os.path.dirname(target_file)
                        target_ext = os.path.splitext(target_file)[1].lower()
                        target_files = [
                            os.path.join(target_dir, f)
                            for f in os.listdir(target_dir)
                            if os.path.splitext(f)[1].lower() == target_ext
                            if f != os.path.basename(target_file)
                        ] + internal_adetailer_models
                        return gr.update(
                            value=target_file,
                            choices=target_files
                        )

                    def adetailer_person_check(model_name) -> bool | None:
                        # モデル名に"person"が含まれているかどうかを返す
                        if model_name is None: return None
                        return "person" in model_name

                    with gr.Row():
                        adetailer_model = gr.Dropdown(
                            scale=9, interactive=True, allow_custom_value=True,
                            label="[ADetailer] Detection Model", choices=internal_adetailer_models, value="internal/person_yolov8n-seg.pt")
                        adetailer_model_custom = gr.Button(
                            shared.browse_directory, size="lg"
                        )
                    adetailer_invert_mask = gr.Checkbox(
                        label="Invert mask (for Person-model)", value=False)

                    adetailer_model_custom.click(
                        update_model_list,
                        outputs=adetailer_model
                    )
                    adetailer_model.change(
                        adetailer_person_check,
                        [adetailer_model],
                        outputs=adetailer_invert_mask
                    )

                    adetailer_mask_only = gr.Button(
                        "Run Mask", size="lg", variant="primary"
                    )

                adetailer_mask_image = gr.Image(
                    type="pil", label="Output Mask", interactive=False, format="png", show_download_button=True)