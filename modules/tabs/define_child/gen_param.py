import inspect
import shutil

import gradio as gr
import os

import shared
from jsonutil import JsonUtilities
from shared import gen_param
from modules.ui_util import ItemRegister
from modules.generation_param import GenerationParameterDefault
from webui import UiTabs

class Define(UiTabs):
    def __init__(self, path):
        super().__init__(path)

        self.child_path = os.path.join(UiTabs.PATH, "define_child")

    def title(self):
        return "Generation Param"

    def index(self):
        return 40

    def ui(self, outlet):
        def setter(d, k, i):
            return ItemRegister.dynamic_setter(d, k, i, "Generation", self.title())

        regist = ItemRegister(setter=setter).register
        default_fp = os.path.join(
            os.getcwd(), "configs/default/gen_param.json"
        )
        if not os.path.exists(default_fp):
            shutil.copy(
                os.path.join(
                    os.getcwd(), "configs/default/default/gen_param.json"
                ),
                default_fp,
            )
        default_file = JsonUtilities(default_fp)
        default = default_file.make_dynamic_data()
        items: list[gr.components.Component] = []
        def register(*args):
            items.append(args[0])
            return gen_param.register(*args)

        with gr.Blocks():
            @regist("negative_prompt")
            def fun_negative_prompt():
                return gr.Textbox(
                    label="Negative Prompt",
                    value=default.negative_prompt,
                    lines=4, max_lines=999
                )
            negative_prompt = register(fun_negative_prompt())
            with gr.Column():
                with gr.Row():
                    @regist("sampling_method")
                    def fun_sampling_method():
                        return gr.Dropdown(
                            choices=['DPM++ 2M', 'DPM++ SDE', 'DPM++ 2M SDE', 'DPM++ 2M SDE Heun', 'DPM++ 2S a', 'DPM++ 3M SDE', 'Euler a', 'Euler', 'LMS', 'Heun', 'DPM2', 'DPM2 a', 'DPM fast', 'DPM adaptive', 'Restart', 'DDIM', 'DDIM CFG++', 'PLMS', 'UniPC', 'LCM'],
                            value=default.sampling_method,
                            label="Sampling methods",
                            multiselect=True
                        )
                    sampling_method = register(fun_sampling_method())

                    @regist("schedule_type")
                    def fun_schedule_type():
                        return gr.Dropdown(
                            choices=['Automatic', 'Uniform', 'Karras', 'Exponential', 'Polyexponential', 'SGM Uniform', 'KL Optimal', 'Align Your Steps', 'Simple', 'Normal', 'DDIM', 'Beta'],
                            value=default.schedule_type,
                            label="Schedule type",
                            multiselect=True
                        )
                    schedule_type = register(fun_schedule_type())

                with gr.Row():
                    @regist("sampling_steps_min")
                    def fun_sampling_steps_min():
                        return gr.Slider(
                            label="Sampling steps (min)",
                            value=default.sampling_steps_min,
                            minimum=1, maximum=150, step=1
                        )
                    sampling_steps_min = register(fun_sampling_steps_min())

                    @regist("sampling_steps_max")
                    def fun_sampling_steps_max():
                        return gr.Slider(
                            label="Sampling steps (max)",
                            value=default.sampling_steps_max,
                            minimum=1, maximum=150, step=1
                        )
                    sampling_steps_max = register(fun_sampling_steps_max())

                    # ステップ数が min > max の場合に再処理する
                    def fun_resize_steps(step_min, step_max):
                        if step_min > step_max: return step_max, step_min
                        else: return step_min, step_max
                    resize_steps = gr.Button(shared.check_mark, size="lg")
                    resize_steps.click(
                        fun_resize_steps, [sampling_steps_min, sampling_steps_max], [sampling_steps_min, sampling_steps_max]
                    )


                with gr.Row():
                    @regist("refiner_checkpoint")
                    def fun_refiner_checkpoint():
                        return gr.Dropdown(
                            label="Refiner checkpoint",
                            multiselect=True,
                            value=default.refiner_checkpoint,
                            choices=[], # TODO: Checkpointsの取得 (http://127.0.0.1:7860/sdapi/v1/sd-models)
                            scale=4
                        )
                    refiner_checkpoint = register(fun_refiner_checkpoint())

                    @regist("refiner_switch_at")
                    def fun_refiner_switch_at():
                        return gr.Slider(
                            label="Refiner switch at",
                            value=default.refiner_switch_at,
                            minimum=0, maximum=1, step=0.01,
                            scale=4
                        )
                    refiner_switch_at = register(fun_refiner_switch_at())

                    @regist("refiner_only_compatibility")
                    def fun_refiner_only_compatibility():
                        return gr.Checkbox(
                            label="Refiner Compatibility (DISABLE Refiner when incompatibility with checkpoint version)",
                            value=default.refiner_only_compatibility
                        )
                    refiner_only_compatibility = register(fun_refiner_only_compatibility())

                with gr.Row():
                    # max が 0 なら hires.fix が無効として非オープン
                    with gr.Accordion(open=(default.hires_steps_max != 0), label="Hires. fix"):
                        with gr.Row():
                            @regist("hires_upscaler")
                            def fun_hires_upscaler():
                                return gr.Dropdown(
                                    choices=['None', 'Lanczos', 'Nearest', 'DAT x2', 'DAT x3', 'DAT x4', 'DAT_x4', 'ESRGAN_4x', 'LDSR', 'R-ESRGAN 4x+', 'R-ESRGAN 4x+ Anime6B', 'ScuNET', 'ScuNET PSNR', 'SwinIR 4x'],
                                    value=default.hires_upscaler,
                                    label="Upscaler",
                                    multiselect=True
                                )
                            hires_upscaler = register(fun_hires_upscaler())

                            @regist("hires_sampler")
                            def fun_hires_sampler():
                                return gr.Dropdown(
                                    choices=['DPM++ 2M', 'DPM++ SDE', 'DPM++ 2M SDE', 'DPM++ 2M SDE Heun', 'DPM++ 2S a', 'DPM++ 3M SDE', 'Euler a', 'Euler', 'LMS', 'Heun', 'DPM2', 'DPM2 a', 'DPM fast', 'DPM adaptive', 'Restart', 'DDIM', 'DDIM CFG++', 'PLMS', 'UniPC', 'LCM'],
                                    value=default.hires_sampler,
                                    label="Custom Sampler (blank to disable)",
                                    multiselect=True
                                )
                            hires_sampler = register(fun_hires_sampler())

                            @regist("denoising_strength")
                            def fun_denoising_strength():
                                return gr.Slider(
                                    label="Denoising Strength",
                                    value=default.denoising_strength,
                                    minimum=0.0, maximum=1.0, step=0.01
                                )
                            denoising_strength = register(fun_denoising_strength())

                        with gr.Row():
                            with gr.Column():
                                @regist("hires_steps_min")
                                def fun_hires_steps_min():
                                    return gr.Slider(
                                        label="Hires. steps (min)",
                                        value=default.hires_steps_min,
                                        minimum=0, maximum=150, step=1
                                    )
                                hires_steps_min = register(fun_hires_steps_min())

                                @regist("hires_steps_max")
                                def fun_hires_steps_max():
                                    return gr.Slider(
                                        label="Hires. steps (max)",
                                        value=default.hires_steps_max,
                                        minimum=0, maximum=150, step=1
                                    )
                                hires_steps_max = register(fun_hires_steps_max())

                            with gr.Column():
                                @regist("hires_use_scaled")
                                def fun_hires_use_scaled():
                                    return gr.Checkbox(
                                        label="Use scaled by.",
                                        value=default.hires_use_scaled
                                    )
                                hires_use_scaled = register(fun_hires_use_scaled())

                                @regist("hires_scale")
                                def fun_hires_scale():
                                    return gr.Slider(
                                        label="Hires. upscale by.",
                                        value=default.hires_scale,
                                        minimum=1.0, maximum=8.0, step=0.05
                                    )
                                hires_scale = register(fun_hires_scale())

                            with gr.Column():
                                @regist("hires_width")
                                def fun_hires_width():
                                    return gr.Slider(
                                        label="Resize width to",
                                        value=default.hires_width,
                                        minimum=0, maximum=8192, step=1
                                    )
                                hires_width = register(fun_hires_width())

                                @regist("hires_height")
                                def fun_hires_height():
                                    return gr.Slider(
                                        label="Resize height to",
                                        value=default.hires_height,
                                        minimum=0, maximum=8192, step=1
                                    )
                                hires_height = register(fun_hires_height())

                with gr.Row():
                    with gr.Column(scale=13):
                        @regist("width")
                        def fun_width():
                            return gr.Slider(
                                label="Width",
                                value=default.width,
                                minimum=0, maximum=2048, step=1
                            )
                        width = register(fun_width())

                        @regist("height")
                        def fun_height():
                            return gr.Slider(
                                label="Height",
                                value=default.height,
                                minimum=0, maximum=2048, step=1
                            )
                        height = register(fun_height())

                    def fun_reverse_wh(w, h):
                        return h, w
                    reverse_wh = gr.Button(shared.reverse_button, variant="secondary")
                    reverse_wh.click(
                        fun_reverse_wh, [width, height], [width, height]
                    )

                    with gr.Column(scale=6):
                        @regist("batch_count")
                        def fun_batch_count():
                            return gr.Slider(
                                label="Batch count",
                                value=default.batch_count,
                                minimum=1, maximum=100, step=1
                            )
                        batch_count = register(fun_batch_count())

                        @regist("batch_size")
                        def fun_batch_size():
                            return gr.Slider(
                                label="Batch size",
                                value=default.batch_size,
                                minimum=1, maximum=8, step=1
                            )
                        batch_size = register(fun_batch_size())

                @regist("cfg_scale")
                def fun_cfg_scale():
                    return gr.Slider(
                        label="CFG Scale",
                        value=default.cfg_scale,
                        minimum=1, maximum=30.0, step=0.5
                    )
                cfg_scale = register(fun_cfg_scale())

                with gr.Row():
                    @regist("seed")
                    def fun_seed():
                        return gr.Number(
                            label="Seed",
                            value=default.seed,
                            scale=70
                        )
                    seed = register(fun_seed())

                    def fun_randomize_seed():
                        return -1
                    randomize_seed = gr.Button("🎲️", variant="secondary", scale=10)
                    randomize_seed.click(
                        fun_randomize_seed, outputs=seed
                    )

                    extra_seeds = gr.Checkbox(
                        scale=20, interactive=False, label="Extra seeds"
                    )

                with gr.Row():
                    @regist("restore_face")
                    def fun_restore_face():
                        return gr.Checkbox(
                            label="Restore face",
                            value=default.restore_face
                        )
                    restore_face = register(fun_restore_face())

                    @regist("tiling")
                    def fun_tiling():
                        return gr.Checkbox(
                            label="Tiling",
                            value=default.tiling
                        )
                    tiling = register(fun_tiling())

                    @regist("clip_skip")
                    def fun_clip_skip():
                        return gr.Slider(
                            label="Clip skip",
                            value=default.clip_skip,
                            minimum=1, maximum=12, step=1
                        )
                    clip_skip = register(fun_clip_skip())

                with gr.Row():
                    @regist("do_not_save_samples")
                    def fun_do_not_save_samples():
                        return gr.Checkbox(
                            label="Do not save samples",
                            value=default.do_not_save_samples
                        )
                    do_not_save_samples = register(fun_do_not_save_samples())

                    @regist("do_not_save_grid")
                    def fun_do_not_save_grid():
                        return gr.Checkbox(
                            label="Do not save grid",
                            value=default.do_not_save_grid
                        )
                    do_not_save_grid = register(fun_do_not_save_grid())

                    @regist("save_interrupted")
                    def fun_save_interrupted():
                        return gr.Checkbox(
                            label="Save interrupted image",
                            value=default.save_interrupted
                        )
                    save_interrupted = register(fun_save_interrupted())

            with gr.Row():
                with gr.Accordion("ADetailer", open=(default.adetailer_model != "None")):
                    with gr.Column():
                        @regist("adetailer_prompt")
                        def fun_adetailer_prompt():
                            return gr.Textbox(
                                label="ADetailer Prompt",
                                value=default.adetailer_prompt,
                                lines=3, max_lines=999, placeholder="Blank to copy main prompt"
                            )
                        adetailer_prompt = register(fun_adetailer_prompt())

                        @regist("adetailer_negative")
                        def fun_adetailer_negative():
                            return gr.Textbox(
                                label="ADetailer Negative",
                                value=default.adetailer_negative,
                                lines=3, max_lines=999, placeholder="Blank to copy main negative"
                            )
                        adetailer_negative = register(fun_adetailer_negative())

                        with gr.Row():
                            @regist("adetailer_model_1st")
                            def fun_adetailer_model_1st():
                                return gr.Dropdown(
                                    label="ADetailer Model 1st",
                                    choices=['face_yolov8n.pt', 'face_yolov8s.pt', 'hand_yolov8n.pt', 'person_yolov8n-seg.pt', 'person_yolov8s-seg.pt', 'yolov8x-worldv2.pt', 'mediapipe_face_full', 'mediapipe_face_short', 'mediapipe_face_mesh', 'mediapipe_face_mesh_eyes_only'],
                                    value=default.adetailer_model
                                )
                            adetailer_model_1st = register(fun_adetailer_model_1st())

                            @regist("adetailer_model_2nd")
                            def fun_adetailer_model_2nd():
                                return gr.Dropdown(
                                    label="ADetailer Model 2nd",
                                    choices=['face_yolov8n.pt', 'face_yolov8s.pt', 'hand_yolov8n.pt', 'person_yolov8n-seg.pt', 'person_yolov8s-seg.pt', 'yolov8x-worldv2.pt', 'mediapipe_face_full', 'mediapipe_face_short', 'mediapipe_face_mesh', 'mediapipe_face_mesh_eyes_only'],
                                    value=default.adetailer_model
                                )
                            adetailer_model_2nd = register(fun_adetailer_model_2nd())


                @regist("override_settings")
                def fun_override_settings():
                    return gr.Textbox(
                        label="Override settings",
                        value=default.override_settings,
                        lines=3, max_lines=999, placeholder="additional override_settings,\nvalues may be json loadable.\nDO NOT EDIT THIS IF YOU DON'T KNOW WHAT YOU'RE DOING."
                    )
                override_settings = register(fun_override_settings())

            def save_values(
                    negative_prompt, sampling_method, schedule_type, sampling_steps_min, sampling_steps_max,
                    refiner_checkpoint, refiner_switch_at, refiner_only_compatibility,
                    hires_upscaler, hires_sampler, denoising_strength,
                    hires_steps_min, hires_steps_max, hires_use_scaled, hires_scale, hires_width, hires_height,
                    width, height, batch_count, batch_size, cfg_scale, seed, restore_face, tiling, clip_skip,
                    do_not_save_samples, do_not_save_grid, save_interrupted,
                    adetailer_prompt, adetailer_negative, adetailer_model_1st, adetailer_model_2nd,
                    override_settings
            ):
                frame = inspect.currentframe()
                args, _, _, values = inspect.getargvalues(frame)
                data = {arg: values[arg] for arg in args}
                default_file.save(data)
                gr.Info("Successfully saved!")
                return


            save = gr.Button("update values", variant="primary")
            save.click(
                save_values, items
            )