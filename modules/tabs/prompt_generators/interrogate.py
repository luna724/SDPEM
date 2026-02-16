from webui import UiTabs
import gradio as gr
from utils import *
import shared

from modules.tagger.predictor import OnnxRuntimeTagger as WDTaggerPredictor, sharedRuntime


class Interrogate(UiTabs):
    def title(self) -> str:
        return "Interrogate"

    def index(self) -> int:
        return 2

    def ui(self, outlet):
        with gr.Tabs():
            with gr.Tab("WD-Tagger"):

                async def predict_wd(img, model: str, thres, c_thres):
                    # display nameからモデルパスを取得
                    model_path = next(
                        (
                            x["path"]
                            for x in shared.models["wd-tagger"]
                            if x["display_name"] == model
                        ),
                        None,
                    )
                    if sharedRuntime is None or sharedRuntime.model_path != model_path:
                        sharedRuntime = WDTaggerPredictor(model_path=model_path, find_path=False)
                    println("Loading WD-Tagger model into CUDA..")
                    await sharedRuntime.load_model_cuda()
                    println("WD-Tagger model loaded successfully.")
                    general, character, rating = await sharedRuntime.predict(
                        img, threshold=thres, character_threshold=c_thres
                    )
                    await sharedRuntime.unload_model()
                    output_string = ", ".join(
                        [
                            x[0]
                            for x in sorted(
                                general.items(), key=lambda x: x[1], reverse=True
                            )
                        ]
                    )
                    return output_string, general, character, rating

                with gr.Blocks():
                  with gr.Row():
                    with gr.Column():
                        img = gr.Image(
                            type="pil",
                            image_mode="RGBA",
                            label="Input image",
                            sources="upload",
                        )

                        model = gr.Dropdown(
                            choices=[
                                x["display_name"]
                                for x in shared.models["wd-tagger"]
                            ],
                            value=shared.models["wd-tagger"][0]["display_name"],
                            label="Predictor Model",
                        )
                        with gr.Row():
                            threshold = gr.Slider(
                                minimum=0.0,
                                maximum=1.0,
                                value=0.5,
                                label="Threshold",
                                step=0.01,
                            )
                            character_threshold = gr.Slider(
                                minimum=0.0,
                                maximum=1.0,
                                value=0.5,
                                label="Character Threshold",
                                step=0.01,
                            )
                        infer = gr.Button(
                            "Predict",
                            variant="primary",
                            elem_id="wdtagger_infer_button",
                        )
                    with gr.Column():
                        output_string = gr.Textbox(
                            label="Output String",
                            placeholder="",
                            lines=5,
                            max_lines=10,
                        )
                        output_rating = gr.Label(
                            label="Rating",
                        )
                        output_character = gr.Label(
                            label="Output Character tags",
                        )
                        output_tags = gr.Label(
                            label="Output Tags",
                        )

                  infer.click(
                      fn=predict_wd,
                      inputs=[img, model, threshold, character_threshold],
                      outputs=[
                          output_string,
                          output_tags,
                          output_character,
                          output_rating,
                      ],
                  )
