
import gradio as gr
from gradio_conditional_prompt import conditional_prompt


example = conditional_prompt().example_value()

with gr.Blocks() as demo:
    with gr.Row():
        conditional_prompt()


if __name__ == "__main__":
    demo.launch()
