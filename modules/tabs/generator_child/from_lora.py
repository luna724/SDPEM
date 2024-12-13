import inspect
import shutil

import gradio as gr
import os

import shared
from jsonutil import JsonUtilities
from modules.api.txt2img import txt2img_api
from modules.lora_generator import LoRAGeneratingUtil
from modules.lora_viewer import LoRADatabaseViewer
from modules.ui_util import (
    ItemRegister,
    bool2visible,
    checkbox_default,
    browse_directory,
)
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
        default_fp = os.path.join(
            os.getcwd(), "configs/default/generator-from_lora.json"
        )
        if not os.path.exists(default_fp):
            shutil.copy(
                os.path.join(
                    os.getcwd(), "configs/default/default/generator-from_lora.json"
                ),
                default_fp,
            )
        default_file = JsonUtilities(default_fp)
        default = default_file.make_dynamic_data()

        gr.Markdown(
            "Generate from LoRA Safetensors weight <br/>"
            "(using metadata in 'ss_tag_frequency', 'tag_frequency' if exists)"
        )

        def select_all_target_lora():
            return viewer.all_lora("fn") + generator.try_sd_webui_lora_models(True)

        def update_target_lora():
            return gr.update(choices=select_all_target_lora())

        with gr.Row():

            @register.register("target_lora")
            def func_target_lora():
                init_value = viewer.all_lora("fn") + generator.try_sd_webui_lora_models(
                    True
                )
                return gr.Dropdown(
                    choices=init_value,
                    multiselect=True,
                    label="Target LoRA",
                    scale=26,
                    elem_id="generate-from_lora-target_lora",
                    value=Util.resize_is_in(init_value, default.target_lora),
                )

            target_lora = func_target_lora()
            target_lora_refresh = gr.Button(
                shared.refresh_button, scale=3, elem_classes="refresh-btn"
            )
            target_lora_select_all = gr.Button(
                shared.select_all_button,
                size="sm",
                scale=1,
                elem_classes="select-all-btn",
            )
            target_lora_select_all.click(select_all_target_lora, outputs=target_lora)
            target_lora_refresh.click(update_target_lora, outputs=target_lora)

        @register.register("meta_mode", "blacklists", "blacklist_multiply")
        def func_meta_and_blacklist():
            available_meta = ["ss_tag_frequency", "tag_frequency"]
            return (
                gr.Dropdown(
                    choices=available_meta,
                    multiselect=True,
                    label="Metadata allow",
                    elem_id="generate-from_lora-metadata_mode",
                    value=Util.resize_is_in(available_meta, default.meta_mode),
                ),
                gr.Textbox(
                    label="tag blacklist",
                    lines=4,
                    placeholder="separate with comma (,)\nYou can use $regex={regex_pattern} $includes={text}\neg. $regex=^white == blacklisted starts white\neg. $includes=thighhighs == blacklisted includes thighhighs (instead. $regex=thighhighs). $type=fruits == blacklisted fruits related fruits",
                    elem_id="generate-from_lora-tag_blacklist",
                    value=default.blacklists,
                ),
                gr.Slider(
                    label="blacklisted tags weight multiply",
                    maximum=10,
                    minimum=0,
                    step=0.01,
                    elem_id="generate-from_lora-blacklist_multiply",
                    value=default.blacklist_multiply,
                ),
            )

        @register.register("separate_blacklist")
        def func_separate_blacklist():
            return gr.Checkbox(
                label="Separate blacklist", value=default.separate_blacklist
            )

        separate_blacklist = func_separate_blacklist()

        @register.register("bcf_blacklist")
        def func_bcf_blacklist():
            return gr.Textbox(
                label="tag blacklist (BooruCaptionFilter)",
                lines=4,
                placeholder="separate with comma (,)\nYou can use $regex={regex_pattern} $includes={text}\neg. $regex=^white == blacklisted starts white\neg. $includes=thighhighs == blacklisted includes thighhighs (instead. $regex=thighhighs). etc..",
                value=default.bcf_blacklist, visible=True
            )

        with gr.Group(visible=default.separate_blacklist) as bcf_group:
            bcf_blacklist = func_bcf_blacklist()

        separate_blacklist.input(
            fn=bool2visible, inputs=separate_blacklist, outputs=bcf_group
        )

        @register.register("threshold", "booru_threshold")
        def func_threshold():
            return (
                gr.Slider(
                    0,
                    1,
                    step=0.05,
                    value=default.threshold,
                    label="Blacklist FastText&Word2Vec Threshold",
                ),
                gr.Slider(
                    0,
                    1,
                    step=0.05,
                    value=default.booru_threshold,
                    label="BooruCaptionFilter Booru Threshold",
                ),
            )

        meta_mode, blacklists, blacklist_multiply = func_meta_and_blacklist()
        with gr.Row():
            threshold, booru_threshold = func_threshold()

        @register.register("bcf_dont_discard", "bcf_invert", "bcf_filtered_path")
        def func_bcf_opts():
            return (
                gr.Checkbox(
                    label="[BCF] Don't Discard blacklisted image",
                    value=default.bcf_dont_discard,
                    scale=4,
                ),
                gr.Checkbox(
                    label="[BCF] Invert target image (whitelisted)",
                    value=default.bcf_invert,
                    scale=5,
                ),
                gr.Textbox(
                    label="[BCF] blacklisted image output path",
                    value=default.bcf_filtered_path,
                    scale=6,
                )
            )

        @register.register("bcf_enable")
        def func_bcf_enable():
            return gr.Checkbox(
                label="[BCF] Enable",
                value=default.bcf_enable,
                scale=10
            )

        bcf_enable = func_bcf_enable()
        with gr.Row():
            bcf_dont_discard, bcf_invert, bcf_filtered_path = func_bcf_opts()
            bcf_browse_dir = gr.Button(value=shared.refresh_button, size="lg", scale=2)
            bcf_browse_dir.click(browse_directory, outputs=bcf_filtered_path)

        with gr.Row():
            gr.HTML(
                "tag_chance = ({tag_strength}*{weight_multiply})/(100*{base_change})"
            )

            @register.register("weight_multiply")
            def func_weight_multiply():
                return gr.Slider(
                    label="Weight Multiply",
                    maximum=10,
                    minimum=0,
                    step=0.01,
                    elem_id="generate-from_lora-weight_multiply",
                    value=default.weight_multiply,
                    scale=3,
                )

            weight_multiply = func_weight_multiply()
            with gr.Column(scale=3):

                @register.register("target_weight_min", "target_weight_max")
                def func_target_weights():
                    return (
                        gr.Slider(
                            label="Multiply Target strength MIN",
                            maximum=100,
                            minimum=1,
                            step=1,
                            elem_id="generate-from_lora-multiply_strength_min",
                            value=default.target_weight_min,
                        ),
                        gr.Slider(
                            label="Multiply Target strength MAX",
                            maximum=100,
                            minimum=1,
                            step=1,
                            elem_id="generate-from_lora-multiply_strength_max",
                            value=default.target_weight_max,
                        ),
                    )

                target_weight_min, target_weight_max = func_target_weights()

        with gr.Row():

            @register.register(
                "add_lora_to_last", "adding_lora_weight", "disallow_duplicate"
            )
            def func_row001():
                return (
                    gr.Checkbox(
                        label="add selected LoRA trigger to last",
                        elem_id="generate-from_lora-selected_lora_to_last",
                        value=checkbox_default(default.add_lora_to_last),
                    ),
                    gr.Textbox(
                        label="selected LoRA weight",
                        value=default.adding_lora_weight,
                        max_lines=1,
                        placeholder="<lora:example:{this}>",
                        elem_id="generate-from_lora-selected_lora_weight",
                    ),
                    gr.Checkbox(
                        label="Disallow tag Duplication",
                        value=checkbox_default(default.disallow_duplicate),
                        elem_id="generate-from_lora-disallow_tag_dupe",
                    ),
                )

            add_lora_to_last, adding_lora_weight, disallow_duplicate = func_row001()

        @register.register("header", "lower")
        def func_head_and_low():
            return (
                gr.Textbox(
                    label="Header prompt",
                    placeholder="this prompts always add and not affect max tags limit",
                    max_lines=3,
                    elem_id="generate-from_lora-header_prompt",
                    value=default.header,
                ),
                gr.Textbox(
                    label="Lower prompt",
                    placeholder="this prompts always add and not affect max tags limit",
                    max_lines=3,
                    elem_id="generate-from_lora-lower_prompt",
                    value=default.lower,
                ),
            )

        header, lower = func_head_and_low()

        with gr.Row():
            output = gr.Textbox(label="Output prompt", show_copy_button=True, lines=5)
            with gr.Column():
                # TODO: use_lora関係の実装
                @register.register("use_lora", "lora_weight", "lbw_toggle")
                def func_use_lora_related():
                    return (
                        gr.Checkbox(
                            label="use LoRA from Database (using trigger words)",
                            interactive=False,
                            elem_id="generate-from_lora-use_lora_from_db",
                            value=checkbox_default(default.use_lora),
                        ),
                        gr.Slider(
                            label="LoRA Weight",
                            minimum=-1,
                            maximum=1,
                            step=0.01,
                            value=default.lora_weight,
                            interactive=False,
                            elem_id="generate-from_lora-lora_weight",
                        ),
                        gr.Checkbox(
                            label="Add Randomly LBW trigger (eg. lbw=OUTALL)",
                            value=checkbox_default(default.lbw_toggle),
                            interactive=False,
                            elem_id="generate-from_lora-add_random_lbw",
                        ),
                    )

                use_lora, lora_weight, lbw_toggle = func_use_lora_related()

                @register.register("max_tags", "tags_base_chance")
                def func_use_tags_related():
                    return (
                        gr.Slider(
                            label="Max tags",
                            minimum=1,
                            maximum=999,
                            step=1,
                            value=default.max_tags,
                            elem_id="generate-from_lora-max_tags",
                        ),
                        gr.Slider(
                            label="base chance (high to more randomize)",
                            minimum=0.01,
                            maximum=10,
                            step=0.01,
                            value=default.tags_base_chance,
                            elem_id="generate-from_lora-base_chance",
                        ),
                    )

                max_tags, tags_base_chance = func_use_tags_related()

        infer = gr.Button("Infer", variant="primary")
        base_inference_variables = [
            target_lora,
            meta_mode,
            blacklists,
            blacklist_multiply,
            weight_multiply,
            target_weight_min,
            target_weight_max,
            use_lora,
            lora_weight,
            lbw_toggle,
            max_tags,
            tags_base_chance,
            add_lora_to_last,
            adding_lora_weight,
            disallow_duplicate,
            header,
            lower,
            threshold,

        ]
        
        infer.click(
            generator.gen_from_lora,
            inputs=base_inference_variables,
            outputs=[output],
        )

        with gr.Accordion("API Image-Generation", open=False):
            gr.Markdown(
                "`API Image-Generation` requires launch SD-WebUI with argument `--api`! <br/>"
                "[Wiki](https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/API)"
            )

            gr.Markdown(
                "[WARNING]: this features currently beta, some features cannot usable (eg. result-preview, refiner, model selection, etc..)<br/>"
            )

            with gr.Row():
                @register.register("ad_model", "negative")
                def func_adm_neg():
                    adetailer_models = [
                        "face_yolov8n.pt",
                        "face_yolov8s.pt",
                        "hand_yolov8n.pt",
                        "None",
                    ]
                    return (
                        gr.Dropdown(
                            label="ADetailer detector",
                            choices=adetailer_models,
                            value=default.ad_model,
                            elem_id="generate-from_lora-adetailer_model",
                            allow_custom_value=True,
                        ),
                        gr.Textbox(
                            label="Negative",
                            value=default.negative,
                            lines=4,
                            elem_id="generate-from_lora-negative",
                        ),
                    )

                ad_model, negative = func_adm_neg()

            with gr.Row():
                @register.register("ad_prompt", "ad_negative")
                def func_adetailer():
                    return (
                        gr.Textbox(
                            label="ADetailer Prompt",
                            lines=2,
                            elem_id="generate-from_lora-adetailer_prompt",
                            value=default.ad_prompt,
                        ),
                        gr.Textbox(
                            label="ADetailer Negative",
                            lines=2,
                            elem_id="generate-from_lora-adetailer_negative",
                            value=default.ad_negative,
                        )
                    )

                ad_prompt, ad_negative = func_adetailer()
            with gr.Row():
                @register.register("sampling_method")
                def func_sampler_step_cfg():
                    sampling_methods = [
                        "DPM++ 2M",
                        "DPM++ SDE",
                        "DPM++ 2M SDE",
                        "Euler a",
                        "Euler",
                    ]
                    return gr.Dropdown(
                        choices=sampling_methods,
                        multiselect=True,
                        value=Util.resize_is_in(
                            sampling_methods, default.sampling_method
                        ),
                        label="Sampling Method (Schedule type are Automatic)",
                        elem_id="generate-from_lora-sampling_method",
                    )

                @register.register("step_min", "step_max")
                def func_steps():
                    return (
                        gr.Slider(
                            1,
                            150,
                            step=1,
                            label="Steps MIN",
                            value=default.step_min,
                            elem_id="generate-from_lora-steps",
                        ),
                        gr.Slider(
                            1,
                            150,
                            step=1,
                            label="Steps MAX",
                            value=default.step_max,
                        ),
                    )

                @register.register("cfg_scale")
                def func_cfg_scale():
                    return gr.Slider(
                        1,
                        30,
                        step=0.5,
                        label="CFG Scale",
                        value=default.cfg_scale,
                        elem_id="generate-from_lora-cfg_scale",
                    )

                sampling_method = func_sampler_step_cfg()
                with gr.Column():
                    step_min, step_max = func_steps()
                cfg_scale = func_cfg_scale()

            with gr.Row():
                with gr.Column():
                    with gr.Row():
                        with gr.Column(scale=8):
                            @register.register("width", "height")
                            def func_resolution():
                                return (
                                    gr.Slider(
                                        512,
                                        2048,
                                        step=1,
                                        label="Width",
                                        value=default.width,
                                        elem_id="generate-from_lora-width",
                                    ),
                                    gr.Slider(
                                        512,
                                        2048,
                                        step=1,
                                        label="Height",
                                        value=default.height,
                                        elem_id="generate-from_lora-height",
                                    ),
                                )

                            width, height = func_resolution()

                        def invert_wh(w, h):
                            return h, w

                        invert_w_h = gr.Button(shared.circular_button, scale=2)
                        invert_w_h.click(invert_wh, [width, height], [width, height])
                with gr.Column():
                    @register.register("bcount", "bsize")
                    def func_batch():
                        return (
                            gr.Slider(
                                1,
                                100,
                                step=1,
                                label="Batch Count",
                                value=default.bcount,
                                elem_id="generate-from_lora-batch_count",
                            ),
                            gr.Slider(
                                1,
                                8,
                                step=1,
                                label="Batch Size",
                                value=default.bsize,
                                elem_id="generate-from_lora-batch_size",
                            )
                        )

                    bcount, bsize = func_batch()

            @register.register("seed")
            def func_seed():
                return gr.Number(
                    label="Seed (-1 to randomize)",
                    value=int(default.seed),
                    elem_id="generate-from_lora-seed",
                )

            seed = func_seed()

            with gr.Accordion("Hires.fix", open=True):
                with gr.Row():
                    @register.register("hires_step", "denoising")
                    def func_hires_001():
                        return (
                            gr.Slider(
                                0,
                                150,
                                step=1,
                                label="Hires Step (0 to disable Hires.fix)",
                                elem_id="generate-from_lora-hires_step",
                                value=default.hires_step,
                            ),
                            gr.Slider(
                                0,
                                1,
                                step=0.01,
                                label="Denoising Strength",
                                elem_id="generate-from_lora-denoising",
                                value=default.denoising,
                            )
                        )

                    hires_step, denoising = func_hires_001()
                with gr.Row():
                    @register.register("hires_upscaler", "upscale_by")
                    def func_hires_002():
                        hires_upscaler_list = [
                            "Latent",
                            "Lanczos",
                            "DAT x4",
                            "DAT_x4",
                            "ESRGAN_4x",
                            "R-ESRGAN 4x+",
                            "R-ESRGAN 4x+ Anime6B",
                            "ScuNET",
                            "ScuNET PSNR",
                            "SwinIR 4x",
                        ]
                        return (
                            gr.Dropdown(
                                choices=hires_upscaler_list,
                                value=default.hires_upscaler,
                                label="Hires Upscaler",
                                elem_id="generate-from_lora-hires_upscaler",
                                allow_custom_value=True,
                            ),
                            gr.Slider(
                                1,
                                8,
                                step=0.05,
                                label="Upscale by",
                                elem_id="generate-from_lora-upscale_by",
                                value=default.upscale_by,
                            ),
                        )

                    hires_upscaler, upscale_by = func_hires_002()
            with gr.Row():
                @register.register("restore_face", "tiling", "clip_skip")
                def func_sd_others():
                    return (
                        gr.Checkbox(
                            label="Restore face",
                            value=checkbox_default(default.restore_face),
                            elem_id="generate-from_lora-restore_face",
                        ),
                        gr.Checkbox(
                            label="Tiling",
                            value=checkbox_default(default.tiling),
                            elem_id="generate-from_lora-tiling",
                        ),
                        gr.Slider(
                            1,
                            12,
                            step=1,
                            label="Clip skip",
                            value=default.clip_skip,
                            elem_id="generate-from_lora-clip_skip",
                        ),
                    )
                restore_face, tiling, clip_skip = func_sd_others()
            with gr.Row():
                @register.register("discard_interrupted_image")
                def fun_sd_other2():
                    return gr.Checkbox(
                        label="Don't Discard Interrupted Image",
                        value=checkbox_default(default.discard_interrupted_image),
                        elem_id="generate-from_lora-discard_interrupted_image",
                    )
                dont_discard_interrupted = fun_sd_other2()

            @register.register("refresh_rate")
            def fun_rr():
                return gr.Slider(
                    0.5,
                    10,
                    step=0.1,
                    label="Preview Refresh Rate (seconds) -= Image Refresh rates Depend on SD-WebUI Settings! =-",
                    value=default.refresh_rate,
                )
            refresh_rate = fun_rr()

            start_infini_generation = gr.Button(
                "Start Generate Forever", variant="primary", elem_classes="luna724_green_button"
            )
            stop_infini_generation = gr.Button("Stop Generate Forever", visible=False, variant="primary", elem_classes="luna724_red_button")
            status = gr.Textbox(
                label="Generating Info", interactive=False, max_lines=12, lines=12
            )

            with gr.Row():
                with gr.Column(scale=3):
                    interrupt = gr.Button(
                        "Interrupt", elem_classes="luna724_red_button"
                    )
                    progress_text = gr.Textbox(
                        label="Progress", interactive=False, max_lines=1, lines=1
                    )
                    eta = gr.Textbox(
                        label="ETA", interactive=False, max_lines=1, lines=1
                    )
                    interrupted = gr.Checkbox(interactive=False, label="Interrupted")
                with gr.Column(scale=7):
                    status_bar = gr.HTML(
                        show_label=False, elem_id="generate-from_lora-status_bar"
                    )
                    current_image = gr.Image(
                        type="pil", interactive=False, show_label=False,
                        label="Current Image", elem_classes="img1024"
                    )

        txt2img_variables = [
                negative,
                ad_prompt,
                ad_negative,
                sampling_method,
                step_min,
                step_max,
                cfg_scale,
                width,
                height,
                bcount,
                bsize,
                seed,
                hires_step,
                denoising,
                hires_upscaler,
                upscale_by,
                restore_face,
                tiling,
                clip_skip,
                ad_model,
                refresh_rate,
                dont_discard_interrupted
                ]
        bcfs = [
            separate_blacklist,
            bcf_blacklist,
            booru_threshold,
            bcf_dont_discard,
            bcf_invert,
            bcf_filtered_path,
            bcf_enable
        ]
        start_infini_generation.click(
            fn=generator.generate_forever,
            inputs=base_inference_variables+bcfs+txt2img_variables,
            outputs=[
                status, progress_text, eta, current_image, status_bar, interrupted
            ],
        )

        txt2img_instance = txt2img_api()
        interrupt.click(
            txt2img_instance.interrupt,
        )

        def visible_stop_infini_generation():
            return (
                gr.update(visible=False), gr.update(visible=True)
            )
        start_infini_generation.click(
            fn=visible_stop_infini_generation,
            outputs=[start_infini_generation, stop_infini_generation],
        )

        def stop_forever_generation():
            generator.forever_generation = False
            gr.Warning("Forever Generation stopped. (its still working while last-image generation)")
            return (
                    gr.update(visible=True), gr.update(visible=False)
                )
        stop_infini_generation.click(
            fn=stop_forever_generation,
            outputs=[start_infini_generation, stop_infini_generation],
        )

        def save_default(
            target_lora,
            meta_mode,
            blacklists,
            blacklist_multiply,
            weight_multiply,
            target_weight_min,
            target_weight_max,
            use_lora,
            lora_weight,
            lbw_toggle,
            max_tags,
            tags_base_chance,
            add_lora_to_last,
            adding_lora_weight,
            disallow_duplicate,
            header,
            lower,
            threshold,
            negative,
            ad_prompt,
            ad_negative,
            sampling_method,
            step_min,
            step_max,
            cfg_scale,
            width,
            height,
            bcount,
            bsize,
            seed,
            hires_step,
            denoising,
            hires_upscaler,
            upscale_by,
            restore_face,
            tiling,
            clip_skip,
            ad_model,
            refresh_rate,
                dont_discard_interrupted,
            separate_blacklist, bcf_blacklist, booru_threshold,
            bcf_dont_discard, bcf_invert, bcf_filtered_path, bcf_enable
        ):
            frame = inspect.currentframe()
            args, _, _, values = inspect.getargvalues(frame)
            data = {arg: values[arg] for arg in args}
            default_file.save(data)
            gr.Info("Successfully saved!")

        save_as_default = gr.Button("Save current value as default")
        save_as_default.click(
            save_default,
            base_inference_variables+txt2img_variables+bcfs,
        )
