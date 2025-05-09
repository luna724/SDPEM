import gradio as gr
import os

import shared
from modules.character_template import CharacterTemplate
from modules.simple_template import SimpleTemplate
from modules.simple_template_api_gen import SimpleTemplateAPIGenerator
from webui import UiTabs

class SimpleTemplateGenerateUI(UiTabs):
    def __init__(self, path):
        super().__init__(path)

        self.child_path = os.path.join(UiTabs.PATH, "generator_child")

    def title(self):
        return "Simple-Template"

    def index(self):
        return 1

    def ui(self, outlet):
        module = SimpleTemplate()
        api_module = SimpleTemplateAPIGenerator()
        chara = CharacterTemplate()
        with gr.Blocks():
            with gr.Row():
                with gr.Column(scale=6):
                    with gr.Row():
                        template = gr.Dropdown(
                            label="target Template", choices=module.list_templates(),
                            scale=8
                        )
                        def template_refresh_click():
                            templates = module.list_templates()
                            if not isinstance(templates, list) or len(templates) < 1:
                                print(f"[ERROR]: error in loading templates ({templates})")
                                raise gr.Error("Templates not found or Any errors occurred!")
                            return gr.update(choices=templates, value=None)
                        template_refresh = gr.Button(shared.refresh_button, scale=2)
                        template_refresh.click(template_refresh_click, outputs=template)

                    with gr.Row():
                        header = gr.Textbox(label="Header", max_lines=3)
                        lower = gr.Textbox(label="Lower", max_lines=3)

                    with gr.Row():
                        prompt = gr.Textbox(label="Output prompt", max_lines=100, lines=4, scale=6)
                        negative = gr.Textbox(label="Output Negative prompt", max_lines=100, lines=4, scale=4)

                    generate = gr.Button("Generate", variant="primary")

                with gr.Column(scale=4):
                    with gr.Row():
                        lora_1 = gr.Dropdown(
                            label="target Character", choices=chara.list_characters(),
                            scale=8
                        )
                        def lora_refresh_click(): return gr.update(choices=chara.list_characters())
                        lora_refresh = gr.Button(shared.refresh_button, scale=2)
                        lora_refresh.click(lora_refresh_click, outputs=lora_1)
                    gr.Markdown("[Preview]")
                    with gr.Row():
                        lora_trigger_1 = gr.Textbox(label="Character LoRA trigger", interactive=False)
                        chara_name_1 = gr.Textbox(label="Character name", interactive=False)
                    with gr.Row():
                        chara_prompt_1 = gr.Textbox(label="Character Prompt", interactive=False)
                        chara_def_1 = gr.Textbox(label="Character Default", interactive=False)

                    with gr.Group(
                        visible=False
                    ) as character_2_enable:
                        gr.Markdown("Character 2 (for Regional Prompter)")
                        with gr.Row():
                            lora_2 = gr.Dropdown(
                                label="target Character", choices=chara.list_characters(),
                                scale=8
                            )

                            def lora_refresh_click(): return gr.update(choices=chara.list_characters())

                            lora_refresh = gr.Button(shared.refresh_button, scale=2)
                            lora_refresh.click(lora_refresh_click, outputs=lora_1)
                        gr.Markdown("[Preview]")
                        with gr.Row():
                            lora_trigger_2 = gr.Textbox(label="Sec. Character LoRA trigger", interactive=False)
                            chara_name_2 = gr.Textbox(label="Sec. Character name", interactive=False)
                        with gr.Row():
                            chara_prompt_2 = gr.Textbox(label="Sec. Character Prompt", interactive=False)
                            chara_def_2 = gr.Textbox(label="Sec. Character Default", interactive=False)

                    with gr.Row():
                        lora_weight_1 = gr.Textbox(label="LoRA Weight", max_lines=1, placeholder="insert into <lora:example:{here}>", value="0.75:lbw=ALL")
                        lora_weight_2 = gr.Textbox(label="Sec. LoRA Weight", max_lines=1, placeholder="insert into <lora:example:{here}>", value="0.75:lbw=ALL", visible=False)

            with gr.Accordion("XY Plot", open=False):
                with gr.Row():
                    x_axis = gr.Dropdown(
                        choices=["Character"], value="Character", interactive=False,
                        scale=4
                    )
                    x_values = gr.Dropdown(
                        choices=chara.list_characters(),
                        label="X choices", scale=5
                    )
                    x_value_refresh = gr.Button(shared.refresh_button, scale=1)
                    x_value_refresh.click(lora_refresh_click, outputs=x_values)
                with gr.Row():
                    y_axis = gr.Dropdown(
                        choices=["Weights"], value="Weights", interactive=False,
                        scale=4
                    )
                    y_values = gr.Textbox(
                        placeholder="separate with ,",
                        scale=6
                    )

                enable_xy_plot = gr.Checkbox(label="Enable XY Plot", value=False)
                with gr.Row():
                    step = gr.Slider(0, 150, step=1, label="Steps", value=30)
                    sampler = gr.Dropdown(
                        choices=["DPM++ 2M", "DPM++ SDE", "DPM++ 2M SDE", "Euler a", "Euler"], multiselect=True,
                        value="Euler a",
                        label="Sampling Method (Schedule type are Automatic)",
                    )
                    cfg_scale = gr.Slider(
                        1, 30, step=0.5, label="CFG Scale", value=7
                    )
                with gr.Row():
                    hires_enable = gr.Checkbox(value=False, label="Hires.fix enable")
                    clip_skip = gr.Slider(1, 12, step=1, value=2, label="Clip skip")
                    seed = gr.Number(label="Seed", value=-1)

                infer = gr.Button("Generate image with template", variant="primary")
                infer.click(
                    api_module.api_generate,
                    inputs=[

                    ]
                )

                def preview_lora(lora):
                    try:
                        return chara.load_character_data(lora)
                    except IndexError:
                        raise gr.Error("Character data not found")

                lora_1.change(
                    preview_lora, lora_1, [lora_trigger_1, chara_name_1, chara_prompt_1, chara_def_1]
                )
                lora_2.change(
                    preview_lora, lora_2, [lora_trigger_2, chara_name_2, chara_prompt_2, chara_def_2]
                )

                generate.click(
                    module.generate,
                    [
                        template, header, lower,
                        lora_1, lora_2, lora_weight_1, lora_weight_2
                    ],
                    outputs=[prompt, negative]
                )