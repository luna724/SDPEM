import inspect
import shutil

import gradio as gr
import os

import shared
from jsonutil import JsonUtilities
from modules.ui_util import checkbox_default, isInOrNull
from modules.lora_generator import LoRAGeneratingUtil
from modules.lora_viewer import LoRADatabaseViewer
from modules.ui_util import ItemRegister
from modules.util import Util
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
        def setter(d, k, i):
            return ItemRegister.dynamic_setter(d, k, i, "Generation", self.title())

        viewer = LoRADatabaseViewer()
        generator = LoRAGeneratingUtil()
        register = ItemRegister(setter=setter)
        default_fp = os.path.join(os.getcwd(), "configs/default/generator-from_lora.json")
        if not os.path.exists(default_fp):
            shutil.copy(
                os.path.join(os.getcwd(), "configs/default/default/generator-from_lora.json"),
                default_fp
            )
        default_file = JsonUtilities(default_fp)
        default = default_file.make_dynamic_data()

        gr.Markdown("Generate from LoRA Safetensors weight <br/>"
                    "(using metadata in 'ss_tag_frequency', 'tag_frequency' if exists)")
        def select_all_target_lora(): return viewer.all_lora("fn")+generator.try_sd_webui_lora_models(True)
        def update_target_lora(): return gr.update(choices=select_all_target_lora())
        with gr.Row():
            @register.register("target_lora")
            def func_target_lora():
                init_value = viewer.all_lora("fn")+generator.try_sd_webui_lora_models(True)
                return gr.Dropdown(
                choices=init_value, multiselect=True, label="Target LoRA",
                scale=26, elem_id="generate-from_lora-target_lora",
                value=Util.resize_is_in(init_value, default.target_lora)
            )
            target_lora = func_target_lora()
            target_lora_refresh = gr.Button(shared.refresh_button, scale=3, elem_classes="refresh-btn")
            target_lora_select_all = gr.Button(shared.select_all_button, size="sm", scale=1, elem_classes="select-all-btn")
            target_lora_select_all.click(select_all_target_lora, outputs=target_lora)
            target_lora_refresh.click(update_target_lora, outputs=target_lora)

        @register.register("meta_mode", "blacklists", "blacklist_multiply")
        def func_meta_and_blacklist():
            available_meta = ["ss_tag_frequency", "tag_frequency"]
            return (
                gr.Dropdown(
                    choices=available_meta,
                    multiselect=True, label="Metadata allow",
                    elem_id="generate-from_lora-metadata_mode",
                    value=Util.resize_is_in(available_meta, default.meta_mode)
                ),
                gr.Textbox(
                    label="tag blacklist",lines=4, placeholder="separate with comma (,)\nYou can use $regex={regex_pattern} $includes={text}\neg. $regex=^white == blacklisted starts white\neg. $includes=thighhighs == blacklisted includes thighhighs (instead. $regex=thighhighs). $type=fruits == blacklisted fruits related fruits",
                    elem_id="generate-from_lora-tag_blacklist", value=default.blacklists
                ),
                gr.Slider(
                    label="blacklisted tags weight multiply", maximum=10, minimum=0, step=0.01,
                    elem_id="generate-from_lora-blacklist_multiply", value=default.blacklist_multiply
            ))

        @register.register("threshold")
        def func_threshold():
            return (
                gr.Slider(0, 1, step=0.05, value=0.75, label="Blacklist Threshold")
            )
        
        meta_mode, blacklists, blacklist_multiply = func_meta_and_blacklist()
        threshold = func_threshold()

        with gr.Row():
            gr.HTML("tag_chance = ({tag_strength}*{weight_multiply})/(100*{base_change})")
            @register.register("weight_multiply")
            def func_weight_multiply():
                return gr.Slider(
                    label="Weight Multiply", maximum=10, minimum=0, step=0.01, elem_id="generate-from_lora-weight_multiply",
                    value=default.weight_multiply
                )
            weight_multiply = func_weight_multiply()
            with gr.Column():
                @register.register("target_weight_min", "target_weight_max")
                def func_target_weights():
                    return (
                        gr.Slider(
                            label="Multiply Target strength MIN",
                            maximum=100, minimum=1, step=1, elem_id="generate-from_lora-multiply_strength_min",
                            value=default.target_weight_min
                        ),
                        gr.Slider(
                            label="Multiply Target strength MAX",
                            maximum=100, minimum=1, step=1, elem_id="generate-from_lora-multiply_strength_max",
                            value=default.target_weight_max
                    ))
                target_weight_min, target_weight_max = func_target_weights()
        with gr.Row():
            @register.register("add_lora_to_last", "adding_lora_weight", "disallow_duplicate")
            def func_row001():
                return (
                    gr.Checkbox(label="add selected LoRA trigger to last", elem_id="generate-from_lora-selected_lora_to_last", value=checkbox_default(default.add_lora_to_last)),
                    gr.Textbox(label="selected LoRA weight", value=default.adding_lora_weight, max_lines=1, placeholder="<lora:example:{this}>", elem_id="generate-from_lora-selected_lora_weight"),
                    gr.Checkbox(label="Disallow tag Duplication", value=checkbox_default(default.disallow_duplicate), elem_id="generate-from_lora-disallow_tag_dupe")
                )
            add_lora_to_last, adding_lora_weight, disallow_duplicate = func_row001()
        @register.register("header", "lower")
        def func_head_and_low():
            return (
                gr.Textbox(label="Header prompt", placeholder="this prompts always add and not affect max tags limit", max_lines=3, elem_id="generate-from_lora-header_prompt", value=default.header),
                gr.Textbox(label="Lower prompt", placeholder="this prompts always add and not affect max tags limit", max_lines=3, elem_id="generate-from_lora-lower_prompt", value=default.lower)
            )
        header, lower = func_head_and_low()

        

        with gr.Row():
            output = gr.Textbox(
                label="Output prompt", show_copy_button=True, lines=5
            )
            with gr.Column():
                # TODO: use_lora関係の実装
                @register.register("use_lora", "lora_weight", "lbw_toggle")
                def func_use_lora_related():
                    return (
                        gr.Checkbox(label="use LoRA from Database (using trigger words)", interactive=False, elem_id="generate-from_lora-use_lora_from_db", value=checkbox_default(default.use_lora)),
                        gr.Slider(label="LoRA Weight", minimum=-1, maximum=1, step=0.01, value=default.lora_weight, interactive=False, elem_id="generate-from_lora-lora_weight"),
                        gr.Checkbox(label="Add Randomly LBW trigger (eg. lbw=OUTALL)", value=checkbox_default(default.lbw_toggle), interactive=False, elem_id="generate-from_lora-add_random_lbw")
                    )
                use_lora, lora_weight, lbw_toggle = func_use_lora_related()

                @register.register("max_tags", "tags_base_chance")
                def func_use_tags_related():
                    return (
                        gr.Slider(label="Max tags", minimum=1, maximum=999, step=1, value=default.max_tags, elem_id="generate-from_lora-max_tags"),
                        gr.Slider(label="base chance (high to more randomize)", minimum=0.01, maximum=10, step=0.01, value=default.tags_base_chance, elem_id="generate-from_lora-base_chance")
                    )
                max_tags, tags_base_chance = func_use_tags_related()


        infer = gr.Button(
            "Infer", variant="primary"
        )

        def infer_run(
            target_lora, meta_mode, blacklists, blacklist_multiply,
                weight_multiply, target_weight_min, target_weight_max,
                use_lora, lora_weight, lbw_toggle, max_tags, tags_base_chance,
                add_lora_to_last, adding_lora_weight, disallow_duplicate, header,
                lower, threshold
        ) -> str:
            return generator.gen_from_lora(
                target_lora, meta_mode, blacklists, blacklist_multiply,
                weight_multiply, target_weight_min, target_weight_max,
                use_lora, lora_weight, lbw_toggle, max_tags, tags_base_chance,
                add_lora_to_last, adding_lora_weight, disallow_duplicate, header,
                lower, threshold
            )

        infer.click(
            infer_run,
            inputs=[
                target_lora, meta_mode, blacklists, blacklist_multiply,
                weight_multiply, target_weight_min, target_weight_max,
                use_lora, lora_weight, lbw_toggle, max_tags, tags_base_chance,
                add_lora_to_last, adding_lora_weight, disallow_duplicate, header,
                lower, threshold
            ],
            outputs=[output]
        )

        with gr.Accordion("API Image-Generation", open=False):
            gr.Markdown("`API Image-Generation` requires launch SD-WebUI with argument `--api`! <br/>"
                        "[Wiki](https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/API)")

            gr.Markdown("[WARNING]: this features currently beta, some features cannot usable (eg. result-preview, refiner, model selection, etc..)<br/>")
            def func_ui_port():
                return gr.Number(label="SD-WebUI Port (127.0.0.1:7860 -> 7860)", value=int(default.ui_port), elem_id="generate-from_lora-ui_port")
            ui_port = func_ui_port()

            with gr.Row():
                def func_adm_neg():
                    adetailer_models = ["face_yolov8n.pt", "face_yolov8s.pt", "hand_yolov8n.pt", "None"]
                    return (
                        gr.Dropdown(
                            label="ADetailer detector",
                            choices=adetailer_models,
                            value=default.ad_model,
                            elem_id="generate-from_lora-adetailer_model", allow_custom_value=True
                        ),
                        gr.Textbox(label="Negative", value=default.negative, lines=4, elem_id="generate-from_lora-negative")
                    )
                ad_model, negative = func_adm_neg()

            with gr.Row():
                def func_adetailer():
                    return (
                        gr.Textbox(
                            label="ADetailer Prompt", lines=2, elem_id="generate-from_lora-adetailer_prompt",
                            value=default.ad_prompt
                        ),
                        gr.Textbox(
                            label="ADetailer Negative", lines=2, elem_id="generate-from_lora-adetailer_negative",
                            value=default.ad_negative
                        )
                    )
                ad_prompt, ad_negative = func_adetailer()
            with gr.Row():
                def func_sampler_step_cfg():
                    sampling_methods = ["DPM++ 2M", "DPM++ SDE", "DPM++ 2M SDE", "Euler a", "Euler"]
                    return gr.Dropdown(
                            choices=sampling_methods, multiselect=True,
                            value=Util.resize_is_in(sampling_methods, default.sampling_method), label="Sampling Method (Schedule type are Automatic)", elem_id="generate-from_lora-sampling_method")
                def func_steps():
                    return (
                        gr.Slider(
                            1, 150, step=1, label="Steps MIN", value=default.step_min,
                            elem_id="generate-from_lora-steps"),
                        gr.Slider(
                            1, 150, step=1, label="Steps MAX", value=default.step_max,
                            )
                    )
                def func_cfg_scale():
                    return gr.Slider(1, 30, step=0.5, label="CFG Scale", value=default.cfg_scale, elem_id="generate-from_lora-cfg_scale")

                sampling_method = func_sampler_step_cfg()
                with gr.Column():
                    step_min, step_max = func_steps()
                cfg_scale = func_cfg_scale()

            with gr.Row():
                with gr.Column():
                    with gr.Row():
                        with gr.Column(scale=8):
                            def func_resolution():
                                return (
                                    gr.Slider(512, 2048, step=1, label="Width", value=default.width, elem_id="generate-from_lora-width"),
                                    gr.Slider(512, 2048, step=1, label="Height", value=default.height, elem_id="generate-from_lora-height")
                                )
                            width, height = func_resolution()
                        def invert_wh(w, h): return h, w
                        invert_w_h = gr.Button(shared.circular_button, scale=2)
                        invert_w_h.click(
                            invert_wh, [width, height], [width, height]
                        )
                with gr.Column():
                    def func_batch():
                        return (
                                gr.Slider(1, 100, step=1, label="Batch Count", value=default.bcount, elem_id="generate-from_lora-batch_count"),
                                gr.Slider(1, 8, step=1, label="Batch Size", value=default.bsize, elem_id="generate-from_lora-batch_size")
                            )
                    bcount, bsize = func_batch()
            def func_seed():
                return gr.Number(label="Seed (-1 to randomize)", value=int(default.seed), elem_id="generate-from_lora-seed")
            seed = func_seed()

            with gr.Accordion("Hires.fix", open=True):
                with gr.Row():
                    def func_hires_001():
                        return (
                            gr.Slider(
                                0, 150, step=1, label="Hires Step (0 to disable Hires.fix)",
                                elem_id="generate-from_lora-hires_step", value=default.hires_step
                            ),
                            gr.Slider(
                                0, 1, step=0.01, label="Denoising Strength",
                                elem_id="generate-from_lora-denoising", value=default.denoising
                            )
                        )
                    hires_step, denoising = func_hires_001()
                with gr.Row():
                    def func_hires_002():
                        hires_upscaler_list = ["Latent", "Lanczos", "DAT x4", "DAT_x4", "ESRGAN_4x", "R-ESRGAN 4x+", "R-ESRGAN 4x+ Anime6B", "ScuNET", "ScuNET PSNR", "SwinIR 4x"]
                        return (
                            gr.Dropdown(
                                choices=hires_upscaler_list, value=default.hires_upscaler,
                                label="Hires Upscaler", elem_id="generate-from_lora-hires_upscaler",
                                allow_custom_value=True
                            ),
                            gr.Slider(
                                1, 8, step=0.05, label="Upscale by", elem_id="generate-from_lora-upscale_by",
                                value=default.upscale_by
                            )
                        )
                    hires_upscaler, upscale_by = func_hires_002()
            with gr.Row():
                def func_sd_others():
                    return (
                        gr.Checkbox(label="Restore face", value=checkbox_default(default.restore_face), elem_id="generate-from_lora-restore_face"),
                        gr.Checkbox(label="Tiling", value=checkbox_default(default.tiling), elem_id="generate-from_lora-tiling"),
                        gr.Slider(1, 12, step=1, label="Clip skip", value=default.clip_skip, elem_id="generate-from_lora-clip_skip")
                    )
                restore_face, tiling, clip_skip = func_sd_others()

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
                lower, threshold,
                ## above ^ gen_from_lora options ^ above
                ## below v txt2img options v below
                negative, ad_prompt, ad_negative, sampling_method, step_min, step_max,
                cfg_scale, width, height, bcount, bsize, seed, hires_step,
                denoising, hires_upscaler, upscale_by, restore_face, tiling, clip_skip,
                ad_model, ui_port
            ], outputs=status
        )

        def stop_forever_generation():
            generator.forever_generation = False
            return "Forever Generation stopped. (its still working while last-image generation)"
        stop_infini_generation.click(
            fn=stop_forever_generation
        )

        def save_default(
                target_lora, meta_mode, blacklists, blacklist_multiply,
                weight_multiply, target_weight_min, target_weight_max,
                use_lora, lora_weight, lbw_toggle, max_tags, tags_base_chance,
                add_lora_to_last, adding_lora_weight, disallow_duplicate, header,
                lower, threshold,
                negative, ad_prompt, ad_negative, sampling_method, step_min, step_max,
                cfg_scale, width, height, bcount, bsize, seed, hires_step,
                denoising, hires_upscaler, upscale_by, restore_face, tiling, clip_skip,
                ad_model, ui_port
        ):
            frame = inspect.currentframe()
            args, _, _, values = inspect.getargvalues(frame)
            data = {arg: values[arg] for arg in args}
            default_file.save(data)
            gr.Info("Successfully saved!")

        save_as_default = gr.Button(
            "Save current value as default"
        )
        save_as_default.click(
            save_default, [
                target_lora, meta_mode, blacklists, blacklist_multiply,
                weight_multiply, target_weight_min, target_weight_max,
                use_lora, lora_weight, lbw_toggle, max_tags, tags_base_chance,
                add_lora_to_last, adding_lora_weight, disallow_duplicate, header,
                lower, threshold,
                negative, ad_prompt, ad_negative, sampling_method, step_min, step_max,
                cfg_scale, width, height, bcount, bsize, seed, hires_step,
                denoising, hires_upscaler, upscale_by, restore_face, tiling, clip_skip,
                ad_model, ui_port
            ]
        )