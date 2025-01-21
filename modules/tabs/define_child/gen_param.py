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
        items = []
        def register(*args):
            items.append(args[0])
            return gen_param.register(*args)

        with gr.Blocks():
            with gr.Row():
                with gr.Column():
                    with gr.Row():
                        @regist("sampling_method")
                        def fun_sampling_method():
                            return gr.Dropdown(
                                choices=[],
                                value=default.sampling_method,
                                label="Sampling methods",
                                multiselect=True
                            )
                        sampling_method = register(fun_sampling_method())

                        @regist("schedule_type")
                        def fun_schedule_type():
                            return gr.Dropdown(
                                choices=[],
                                value=default.schedule_type,
                                label="Schedule type",
                                multiselect=True
                            )
                        schedule_type = register(fun_schedule_type())

                        with gr.Row():
                            with gr.Column(scale=9):
                                @regist("sampling_steps_min")
                                def fun_sampling_steps_min():
                                    return gr.Slider(
                                        label="Sampling steps (min)",
                                        value=default.sampling_steps,
                                        minimum=1, maximum=150, step=1
                                    )
                                sampling_steps_min = register(fun_sampling_steps_min())

                                @regist("sampling_steps_max")
                                def fun_sampling_steps_max():
                                    return gr.Slider(
                                        label="Sampling steps (max)",
                                        value=default.sampling_steps,
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
                        # max が 0 なら hires.fix が無効として非オープン
                        with gr.Accordion(open=(default.hires_steps_max != 0), label="Hires. fix"):
                            with gr.Row():
                                @regist("hires_upscaler")
                                def fun_hires_upscaler():
                                    return gr.Dropdown(
                                        choices=[],
                                        value=default.hires_upscaler,
                                        label="Upscaler",
                                        multiselect=True
                                    )
                                hires_upscaler = register(fun_hires_upscaler())

                                @regist("hires_sampler")
                                def fun_hires_sampler():
                                    return gr.Dropdown(
                                        choices=[],
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

