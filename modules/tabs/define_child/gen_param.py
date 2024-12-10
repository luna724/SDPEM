import shutil

import gradio as gr
import os

from jsonutil import JsonUtilities
from modules.lora_viewer import LoRADatabaseViewer
from modules.simple_template import SimpleTemplate
from modules.ui_util import ItemRegister
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

        register = ItemRegister(setter=setter)
        default_fp = os.path.join(
            os.getcwd(), "configs/default/generator-ai_generation.json"
        )
        if not os.path.exists(default_fp):
            shutil.copy(
                os.path.join(
                    os.getcwd(), "configs/default/default/generator-ai_generation.json"
                ),
                default_fp,
            )
        default_file = JsonUtilities(default_fp)
        default = default_file.make_dynamic_data()

        with gr.Blocks():
            @register.register("negative")
            def func_negative():
                return gr.Textbox(
                    label="Negative prompt",
                    lines=3, placeholder="Negative prompt default",
                    value=default.negative
                )
            negative = func_negative()

            @register.register("sampling_method", "schedule_type")
            def func_col_1():
                return (
                    gr.Dropdown(
                        label="Sampling Method (if multiselect, randomly select one)", value=default.sampling_method,
                        choices=["DPM++ 2M", "DPM++ SDE", "DPM++ 2M SDE", "Euler a", "Euler"],
                        multiselect=True, scale=4
                    ),
                    gr.Dropdown(
                        label="Schedule type", value=default.schedule_type,
                        choices=["Automatic", "Uniform", "Karras", "Exponential", "Polyexponential",
                                 "SGM Uniform", "KL Optimal", "Align Your Steps", "Simple", "Normal",
                                 "DDIM", "Beta"],
                        multiselect=True, scale=4
                    )
                )

            @register.register("sampling_steps_min", "sampling_steps_max")
            def func_col_1_col():
                return (
                    gr.Slider(
                        1, 150, value=default.sampling_step_min, step=1,
                        label="Sampling steps (MIN)",
                    ),
                    gr.Slider(
                        1, 150, value=default.sampling_step_max, step=1,
                        label="Sampling steps (MAX)",
                    )
                )

            with gr.Row():
                sampling_method, schedule_type = func_col_1()
                with gr.Column(scale=4):
                    sampling_steps_min, sampling_steps_max = func_col_1_col()
                validate_step = gr.Button("check", scale=1)
                def fun_validate_step(min, max):
                    if min > max: return max, min

                validate_step.click(
                    fun_validate_step, [sampling_steps_min, sampling_steps_max], [sampling_steps_min, sampling_steps_max]
                )

            with gr.Accordion("Hires.fix", open=True):
                @register.register("hr_upscaler")
                def fun_hr_col1():
                    return (
                        gr.Dropdown(
                            label="Upscaler", value=default.hr_upscaler,
                            multiselect=True, scale=10,
                            choices=[
                                "Latent", "Latent (antialiased)", "Latent (bicubic)", "Latent (bicubic antialiased)", "Latent (nearest)",
                                "Latent (nearest-exact)", "None", "Lanczos", "Nearest", "DAT x2", "DAT x3", "DAT x4",
                                "DAT_x4", "ESRGAN_4x", "LDSR", "R-ESRGAN 4x+", "R-ESRGAN 4x+ Anime6B", "ScuNET", "ScuNET PSNR",
                                "SwiniR4x"
                            ]
                        )
                    )

                @register.register("hr_step_min", "hr_step_max")
                def fun_hr_steps():
                    return (
                        gr.Slider(
                            0, 150, step=1, value=default.hr_steps,
                            label="Hires steps MIN", scale=10
                        ),
                        gr.Slider(
                            0, 150, step=1, value=default.hr_steps,
                            label="Hires steps MAX", scale=10
                        )
                    )

                @register.register("denoising_strength_min", "denoising_strength_max")
                def fun_hr_denoising_strength():
                    return (
                        gr.Slider(
                            0, 1, step=0.01, value=default.denoising_strength_min,
                            label="Denoising Strength MIN", scale=10
                        ),
                        gr.Slider(
                            0, 1, step=0.01, value=default.denoising_strength_max,
                            label="Denoising Strength MAX", scale=10
                        )
                    )

                @register.register("hr_upscale")
                def fun_hr_upscale():
                    return gr.Slider(

                    )

                with gr.Row():
                    hr_upscaler = fun_hr_col1()
                    with gr.Column(scale=10):
                        hr_step_min, hr_step_max = fun_hr_steps()
                    with gr.Column(scale=10):
                        denoising_strength_min, denoising_strength_max = fun_hr_denoising_strength()

                with gr.Row():
                    hr_upscale = fun_hr_upscale()
