from typing import Literal

import gradio as gr
import os

from modules.lora_installer import LoRAModelInstaller
from webui import UiTabs


class Lora(UiTabs):
    def __init__(self, path):
        super().__init__(path)
        self.child_path = os.path.join(UiTabs.PATH, "installer_child")


    def title(self):
        return "LoRA"

    def index(self):
        return -1

    def ui(self, outlet):
        gr.Markdown("[DISCLAIMER: CivitAI API Scraping aren't allowed!](https://civitai.com/robots.txt)")
        url_input = gr.Textbox(
            label="CivitAI URLs (separate with comma)",
            placeholder="https://civitai.com/models/137826/background-only-blursharpdetailup",
        )

        urls = gr.Dropdown(
            label="CivitAI URLs"
        )

        with gr.Group():
            url = gr.Textbox(label="URL", interactive=False)

            with gr.Row():
                url_type = gr.Dropdown(label="Type", choices=["Concept"], value="Concept", interactive=False)
                fn = gr.Textbox(label="Filename", placeholder="leave empty to use urls")
                isapi = gr.Checkbox(label="Is API URL", value=False)

            with gr.Group(visible=False) as if_character:
                with gr.Column():
                    ch_auto_save = gr.Checkbox(label="Auto Save", visible=False, value=False)
                    with gr.Group(visible=False) as character_auto_save:
                        with gr.Row():
                            name = gr.Textbox(label="Name", placeholder="$NAME field")
                            prompt = gr.Textbox(label="Prompt", placeholder="$PROMPT field")
                        with gr.Row():
                            extend = gr.Textbox(label="Extend", placeholder="$EXTEND field")
                send_lora_definition_tab = gr.Button(
                    "Download models&Save this&Send data to Define/LoRA"
                )
            insert_data = gr.Button("Send Model to Downloader")

        instance_state = gr.Textbox(label="Downloader Log", lines=2, max_lines=12, placeholder="Idling..")
        create_instance = gr.Button("Launch New Downloader", visible=True)
        terminate_instance = gr.Button("Terminate Downloader", visible=False)
        run_instance = gr.Button("Run Downloader", visible=False)

        # change
        prv_urls = []
        def url_input_resizer(url_input, urls_value) -> tuple:
            if url_input.count(",") > 0:
                url = url_input.split(",")[0]
                if url.startswith("civitai"):
                    url = "https://"+url
                if not url.startswith("https://"): raise gr.Error("your input aren't url")
                if not "civitai.com" in url: raise gr.Error("this URL aren't CivitAI!")
                prv_urls.append(url)
            else: return url_input, prv_urls, None, None, None

            urls = list(dict.fromkeys(prv_urls))
            url_input = ",".join(url_input.split(",")[1:]).strip(",")
            return url_input, gr.Dropdown.update(choices=urls,value=urls_value)

        url_input.input(
            url_input_resizer, [url_input, urls],
            [url_input, urls]
        )

        def urls_change(urls):
            return urls

        urls.input(
            urls_change, urls, url
        )

        def url_change(url) -> tuple:
            fn = None
            isapi = False

            if url.startswith("https://civitai.com/api"):
                isapi = True

            if not isapi and fn is None:
                if i.instance is not None:
                    if url in i.instance.data.keys():
                        fn = i.instance.data[url][0]
                        return fn, isapi
                fn = url.strip("/").split("/")[-1]
            return fn, isapi

        url.change(url_change, url, [fn, isapi])

        # 実行
        class i: instance:LoRAModelInstaller|None = None
        def create_instance_run():
            i.instance = LoRAModelInstaller()
            return (
                gr.update(visible=False), gr.update(visible=True), gr.update(visible=True)
            )

        def terminate_instance_run():
            i.instance = None
            return (
                gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)
            )

        def run_instance_run():
            if i.instance is None: raise gr.Error("Instances Not Found!")
            gr.Warning("Process started!\n if you saw error, maybe fake(see console)")
            i.instance.run()
            gr.Info("Process Done!")

        create_instance.click(
            create_instance_run, outputs=[create_instance, terminate_instance, run_instance]
        )
        terminate_instance.click(
            terminate_instance_run, outputs=[create_instance, terminate_instance, run_instance]
        )
        run_instance.click(
            run_instance_run, outputs=instance_state
        )

        def insert_data_run(url, type:Literal["Concept"], fn, isapi):
            if i.instance is None:
                gr.Warning("Instances not Intialized!")
                return
            i.instance.push(url, fn, isapi)
            gr.Info("Success")

        insert_data.click(
            insert_data_run,
            [url, url_type, fn, isapi]
        )