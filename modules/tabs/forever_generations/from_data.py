import gradio as gr
from pathlib import Path
from typing import Callable

from modules.sd_param import get_sampler, get_scheduler
from modules.utils.browse import select_file
from modules.utils.ui.register import RegisterComponent
from modules.utils.ui.templates import TabContent
from webui import UiTabs


class DataToPrompt(UiTabs):
	def title(self) -> str:
		return "from Data"

	def index(self) -> int:
		return 2

	async def ui(self, outlet: Callable[[str, gr.components.Component], None]) -> None:
		config = RegisterComponent(
			Path("./defaults/forever_generation.from_data.json"),
			"forever_generations/from_data",
		)
		r = config.register
		default = config.get()

		def d(key, fallback):
			val = getattr(default, key, None)
			return fallback if val is None else val

		with gr.Blocks():
			with gr.Row():
				datapath = r(
					"datapath",
					gr.Textbox(
						label="Data filepath",
						value=d("datapath", "data/eg.json"),
						scale=6,
					),
				)
				browse_btn = gr.Button("Browse", variant="secondary")
				browse_btn.click(fn=select_file, outputs=datapath, show_progress=False)

			with gr.Accordion(label="Prompt Settings", open=False):
				header = r(
					"header",
					gr.Textbox(
						label="Prompt Header",
						placeholder="Enter the prompt header",
						lines=2,
						max_lines=4,
						value=d("header", ""),
					),
				)
				footer = r(
					"footer",
					gr.Textbox(
						label="Prompt Footer",
						placeholder="Enter the prompt footer",
						lines=2,
						max_lines=4,
						value=d("footer", ""),
					),
				)
				negative = r(
					"negative",
					gr.Textbox(
						label="Negative Prompt",
						placeholder="Enter negative prompt",
						lines=2,
						max_lines=4,
						value=d("negative", ""),
					),
				)

			await TabContent.render_tmpl("sd_params", r, default)

			with gr.Row():
				generate = gr.Button("Start generation", variant="primary")
				status = gr.Markdown(value="Waiting for generator binding")
				generate.click(
					fn=lambda: "Bind to generation handler",
					outputs=status,
					show_progress=False,
				)
