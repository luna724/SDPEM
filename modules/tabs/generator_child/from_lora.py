import gradio as gr
import os

from modules.lora_generator import LoRAGeneratingUtil
from modules.lora_viewer import LoRADatabaseViewer
from webui import UiTabs

class Generator(UiTabs):
    def __init__(self, path):
        super().__init__(path)

        self.child_path = os.path.join(UiTabs.PATH, "generator_child")

    def title(self):
        return "from LoRA"

    def index(self):
        return 0

    def ui(self, outlet):
        viewer = LoRADatabaseViewer()
        generator = LoRAGeneratingUtil()

        gr.Markdown("Generate from LoRA Safetensors weight <br/>"
                    "(using metadata in 'ss_tag_frequency', 'tag_frequency' if exists)")
        target_lora = gr.Dropdown(
            choices=viewer.all_lora("fn")+generator.try_sd_webui_lora_models(True), multiselect=True, label="Target LoRA",
        )
        meta_mode = gr.Dropdown(
            choices=["ss_tag_frequency", "tag_frequency"],
            multiselect=True, value=["ss_tag_frequency", "tag_frequency"], label="Metadata allow"
        )
        blacklists = gr.Textbox(
            label="tag blacklist", value="", lines=4, placeholder="separate with comma (,)\nYou can use $regex={regex_pattern} $includes={text}\neg. $regex=^white == blacklisted starts white\neg. $includes=thighhighs == blacklisted includes thighhighs (instead. $regex=thighhighs)"
        )
        blacklist_multiply = gr.Slider(
            label="blacklisted tags weight multiply", maximum=10, minimum=0, step=0.01, value=0
        )

        with gr.Row():
            gr.HTML("tag_chance = ({tag_strength}*{weight_multiply})/(100*{base_change})")
            weight_multiply = gr.Slider(
                label="Weight Multiply", maximum=10, minimum=0, step=0.01, value=1.75
            )
            with gr.Column():
                target_weight_min = gr.Slider(
                    label="Multiply Target strength MIN",
                    maximum=100, minimum=1, step=1, value=1
                )
                target_weight_max = gr.Slider(
                    label="Multiply Target strength MAX",
                    maximum=100, minimum=1, step=1, value=12
                )
        with gr.Row():
            add_lora_to_last = gr.Checkbox(label="add selected LoRA trigger to last")
            adding_lora_weight = gr.Textbox(label="selected LoRA weight", value="0.75:lbw=OUTALL:stop=14", max_lines=1, placeholder="<lora:example:{this}>")
            disallow_duplicate = gr.Checkbox(label="Disallow tag Duplication", value=True)

        with gr.Row():
            output = gr.Textbox(
                label="Output prompt", show_copy_button=True, lines=5
            )
            with gr.Column():
                # TODO: use_lora関係の実装
                use_lora = gr.Checkbox(label="use LoRA from Database (using trigger words)", interactive=False)
                lora_weight = gr.Slider(label="LoRA Weight", minimum=-1, maximum=1, step=0.01, value=0.75, interactive=False)
                lbw_toggle = gr.Checkbox(label="Add Randomly LBW trigger (eg. lbw=OUTALL)", value=True, interactive=False)

                max_tags = gr.Slider(label="Max tags", minimum=1, maximum=255, step=1, value=75)
                tags_base_chance = gr.Slider(label="base chance (high to more randomize)", minimum=0.01, maximum=1000, step=0.01, value=1)

        infer = gr.Button(
            "Infer", variant="primary"
        )
        def infer_run(
            target_lora, meta_mode, blacklists, blacklist_multiply,
                weight_multiply, target_weight_min, target_weight_max,
                use_lora, lora_weight, lbw_toggle, max_tags, tags_base_chance,
                add_lora_to_last, adding_lora_weight, disallow_duplicate
        ) -> str:
            return generator.gen_from_lora(
                target_lora, meta_mode, blacklists, blacklist_multiply,
                weight_multiply, target_weight_min, target_weight_max,
                use_lora, lora_weight, lbw_toggle, max_tags, tags_base_chance,
                add_lora_to_last, adding_lora_weight, disallow_duplicate
            )

        infer.click(
            infer_run,
            inputs=[
                target_lora, meta_mode, blacklists, blacklist_multiply,
                weight_multiply, target_weight_min, target_weight_max,
                use_lora, lora_weight, lbw_toggle, max_tags, tags_base_chance,
                add_lora_to_last, adding_lora_weight, disallow_duplicate
            ],
            outputs=[output]
        )