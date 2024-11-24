import gradio as gr
import os

import shared
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
        def update_target_lora(): return gr.update(choices=viewer.all_lora("fn")+generator.try_sd_webui_lora_models(True))
        with gr.Row():
            target_lora = gr.Dropdown(
                choices=viewer.all_lora("fn")+generator.try_sd_webui_lora_models(True), multiselect=True, label="Target LoRA",
                scale=9
            )
            target_lora_refresh = gr.Button(shared.refresh_button)
            target_lora_refresh.click(update_target_lora, outputs=target_lora)

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

        header = gr.Textbox(label="Header prompt", placeholder="this prompts always add and not affect max tags limit", max_lines=3)

        with gr.Row():
            output = gr.Textbox(
                label="Output prompt", show_copy_button=True, lines=5
            )
            with gr.Column():
                # TODO: use_lora関係の実装
                use_lora = gr.Checkbox(label="use LoRA from Database (using trigger words)", interactive=False)
                lora_weight = gr.Slider(label="LoRA Weight", minimum=-1, maximum=1, step=0.01, value=0.75, interactive=False)
                lbw_toggle = gr.Checkbox(label="Add Randomly LBW trigger (eg. lbw=OUTALL)", value=True, interactive=False)

                max_tags = gr.Slider(label="Max tags", minimum=1, maximum=999, step=1, value=75)
                tags_base_chance = gr.Slider(label="base chance (high to more randomize)", minimum=0.01, maximum=10, step=0.01, value=1)

        infer = gr.Button(
            "Infer", variant="primary"
        )

        def infer_run(
            target_lora, meta_mode, blacklists, blacklist_multiply,
                weight_multiply, target_weight_min, target_weight_max,
                use_lora, lora_weight, lbw_toggle, max_tags, tags_base_chance,
                add_lora_to_last, adding_lora_weight, disallow_duplicate, header
        ) -> str:
            return generator.gen_from_lora(
                target_lora, meta_mode, blacklists, blacklist_multiply,
                weight_multiply, target_weight_min, target_weight_max,
                use_lora, lora_weight, lbw_toggle, max_tags, tags_base_chance,
                add_lora_to_last, adding_lora_weight, disallow_duplicate, header
            )

        infer.click(
            infer_run,
            inputs=[
                target_lora, meta_mode, blacklists, blacklist_multiply,
                weight_multiply, target_weight_min, target_weight_max,
                use_lora, lora_weight, lbw_toggle, max_tags, tags_base_chance,
                add_lora_to_last, adding_lora_weight, disallow_duplicate, header
            ],
            outputs=[output]
        )

        with gr.Accordion("API Image-Generation", open=False):
            gr.Markdown("`API Image-Generation` requires launch SD-WebUI with argument `--api`! <br/>"
                        "[Wiki](https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/API)")

            gr.Markdown("[WARNING]: this features currently beta, some features cannot usable (eg. result-preview, refiner, model selection, etc..)<br/>")
            ui_port = gr.Number(label="SD-WebUI Port (127.0.0.1:7860 -> 7860)", value=7860)
            with gr.Row():
                ad_model = gr.Dropdown(
                    label="ADetailer detector",
                    choices=["face_yolov8n.pt", "face_yolov8s.pt", "hand_yolov8n.pt"],
                    value="face_yolov8n.pt"
                )
                _ = gr.Textbox(label="Prompt", interactive=False, visible=False)
                negative = gr.Textbox(label="Negative", value="", lines=4) # TODO: 値の保持機能
            with gr.Row():
                ad_prompt = gr.Textbox(label="ADetailer Prompt", lines=2)
                ad_negative = gr.Textbox(label="ADetailer Negative", lines=2)
            with gr.Row():
                sampling_method = gr.Dropdown(
                    choices=["DPM++ 2M", "DPM++ SDE", "DPM++ 2M SDE", "Euler a", "Euler"],
                    value="Euler a", label="Sampling Method (Schedule type are Automatic)"
                )
                steps = gr.Slider(1, 150, step=1, label="Steps", value=30)
                cfg_scale = gr.Slider(1, 30, step=0.5, label="CFG Scale", value=7)
            with gr.Row():
                with gr.Column():
                    width = gr.Slider(512, 2048, step=1, label="Width", value=1024)
                    height = gr.Slider(512, 2048, step=1, label="Height", value=1360)
                with gr.Column():
                    bcount = gr.Slider(1, 100, step=1, label="Batch Count", value=1)
                    bsize = gr.Slider(1, 8, step=1, label="Batch Size", value=8)
            seed = gr.Number(label="Seed (-1 to randomize)", value=-1)

            with gr.Accordion("Hires.fix", open=True):
                with gr.Row():
                    hires_step = gr.Slider(0, 150, step=1, label="Hires Step (0 to disable Hires.fix)", value=0)
                    denoising = gr.Slider(0, 1, step=0.01, label="Denoising Strength", value=0.2)
                with gr.Row():
                    hires_sampler = gr.Dropdown(
                        choices=["Latent", "Lanczos", "DAT x4", "DAT_x4", "ESRGAN_4x", "R-ESRGAN 4x+", "R-ESRGAN 4x+ Anime6B", "ScuNET", "ScuNET PSNR", "SwinIR 4x"],
                        value="R-ESRGAN 4x+ Anime6B", label="Hires Upscaler"
                    )
                    upscale_by = gr.Slider(1, 8, step=0.05, label="Upscale by")

            with gr.Row():
                restore_face = gr.Checkbox(label="Restore face", value=False)
                tiling = gr.Checkbox(label="Tiling", value=False)
                clip_skip = gr.Slider(1, 12, step=1, label="Clip skip", value=2)

            start_infini_generation = gr.Button("Start Generate Forever", variant="primary")
            stop_infini_generation = gr.Button("Stop Generate Forever")
            status = gr.Textbox(label="Generating Info", interactive=False, max_lines=12, lines=12)


        start_infini_generation.click(
            fn=generator.generate_forever,
            inputs=[
                target_lora, meta_mode, blacklists, blacklist_multiply,
                weight_multiply, target_weight_min, target_weight_max,
                use_lora, lora_weight, lbw_toggle, max_tags, tags_base_chance,
                add_lora_to_last, adding_lora_weight, disallow_duplicate, header,
                ## above ^ gen_from_lora options ^ above
                ## below v txt2img options v below
                negative, ad_prompt, ad_negative, sampling_method, steps,
                cfg_scale, width, height, bcount, bsize, seed, hires_step,
                denoising, hires_sampler, upscale_by, restore_face, tiling, clip_skip,
                ad_model, ui_port
            ]
        )

        def stop_forever_generation():
            generator.forever_generation = False
            return "Forever Generation stopped. (its still working while last-image generation)"
        stop_infini_generation.click(
            fn=stop_forever_generation
        )