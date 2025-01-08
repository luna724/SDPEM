import gradio as gr
import os

from modules.character_template import CharacterTemplate
from modules.simple_template import SimpleTemplate
from webui import UiTabs

class Define(UiTabs):
    def __init__(self, path):
        super().__init__(path)

        self.child_path = os.path.join(UiTabs.PATH, "define_child")

    def title(self):
        return "Character-Template"

    def index(self):
        return 3

    def ui(self, outlet):
        module = CharacterTemplate()
        def validate_lora(lora):
            status = module.check_lora_trigger(lora)
            if status:
                gr.Info("LoRA Triggers correctly!")
            else:
                raise gr.Error("LoRA Triggers incorrectly!")

        with gr.Blocks():
            chara_version = gr.Dropdown(label="Template ver.", choices=["v3 Legacy", "v6"], value="v6")
            display_name = gr.Textbox(label="Display Name", placeholder="REQUIRED")

            with gr.Row():
                lora_trig = gr.Textbox(label="LoRA Trigger (placeholder of $LORA)", placeholder="may <lora:name:w> style", scale=8)
                check_lora = gr.Button("Validate", size="lg")
                check_lora.click(
                    validate_lora, lora_trig
                )
            with gr.Row():
                name = gr.Textbox(label="placeholder of $NAME")
                prompt = gr.Textbox(label="placeholder of $PROMPT")
            overwrite = gr.Checkbox(label="overwrite prv key")

            save = gr.Button("Save", variant="primary")
            save.click(
                module.new_chara_v3,
                inputs=[
                    chara_version, display_name, lora_trig, name, prompt, overwrite
                ]
            )