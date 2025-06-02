import asyncio
import subprocess
import sys
import threading
from typing import *
import gradio as gr
import importlib
import torch
import uvicorn
from fastapi import FastAPI

from initialize import *
import shared
from modules.argparser import parse_args
from modules.receive import initialize_server


class UiTabs:
    PATH = os.path.join(os.getcwd(), "modules/tabs")

    def __init__(self, path):
        self.filepath = path
        self.rootpath = UiTabs.PATH
        self.child_path = None
        pass

    def title(self) -> str:
        """ return tab_title"""
        return "Tab_Title"

    def index(self) -> int:
        """ return ui's index """
        return 0

    def get_ui(self) -> list:
        tabs = []
        files = [file for file in os.listdir(self.child_path) if file.endswith(".py")]
        #print(f"Child path: {self.child_path} ({files})")

        for file in files:
            module_name = file[:-3]
            module_path = os.path.relpath(
                self.child_path, UiTabs.PATH
            ).replace("/", ".").replace("\\", ".").strip(".")
            #print(f"Loading {module_path}'s child tab ({module_name})..")
            module = importlib.import_module(f"modules.tabs.{module_path}.{module_name}")

            attrs = module.__dict__
            TabClass = [
                x for x in attrs.values() if type(x) == type and issubclass(x, UiTabs) and not x == UiTabs
            ]
            if len(TabClass) > 0:
                tabs.append((file, TabClass[0]))

        tabs = sorted([TabClass(file) for file, TabClass in tabs], key=lambda x: x.index())
        return tabs

    def ui(self, outlet: Callable):
        """ make ui data
        don't return """
        with gr.Blocks():


            with gr.Tabs():
                tabs = self.get_ui()
                for tab in tabs:
                    with gr.Tab(tab.title()):
                        tab_ui_elements = {}

                        # タブ内のUIを生成し、そのエレメントを辞書に格納
                        def capture_ui(component_name, component):
                            #print(f"Captured UI: {component_name}, {component}")
                            tab_ui_elements[component_name] = component

                        # 実際のUI生成
                        tab.ui(lambda component_name, component: capture_ui(component_name, component))

                        # タブ全体のエレメントを保存
                        # tab_ui_elements
        #shared.ui_obj[self.title()] = tab_elements

    # def has_child(self):
    #   return [rootID, child_rel_import_path, importlib's Path]

def make_ui() -> tuple[gr.Blocks, dict]:
    def get_ui() -> List[UiTabs]:
        tabs = []
        files = [file for file in os.listdir(UiTabs.PATH) if file.endswith(".py")]

        for file in files:
            module_name = file[:-3]
            # print(f"Loading tab ({module_name})..")
            module = importlib.import_module(f"modules.tabs.{module_name}")

            attrs = module.__dict__
            UiTabs_ref = sys.modules["webui"].UiTabs
            for x in attrs.values():
                # print(f"Checking: {x}, type: {type(x)}")
                if isinstance(x, type):
                    # print(f"Is subclass of UiTabs: {issubclass(x, UiTabs_ref)}")
                    pass
            TabClass = [
                x for x in attrs.values()
                if isinstance(x, type) and issubclass(x, UiTabs_ref) and not x == UiTabs_ref
            ]
            # print(f"UiTabs reference in webui: {UiTabs}")
            # print(f"UiTabs reference in module: {sys.modules['webui'].UiTabs}")
            # print(f"Is same reference: {UiTabs is sys.modules['webui'].UiTabs}")

            if len(TabClass) > 0:
                tabs.append((file, TabClass[0]))
                # print(f"tab module found in ({module_name})")

        tabs = sorted([TabClass(file) for file, TabClass in tabs], key=lambda x: x.index())
        return tabs

    with open("style.css", "r", encoding="utf-8") as css_f:
        css = css_f.read()
    with open("luna724.css", "r", encoding="utf-8") as my_css_f:
        my_css = my_css_f.read()
        if shared.args.luna_theme:
            css += "\n"+my_css
    block = gr.Blocks(title="luna724 / SD-PEM Client", analytics_enabled=False, css=css)
    #tab_elements = {}
    with block:
        # IPのデフォルトを取得
        from modules.api.server_ip import server_ip
        with gr.Row():
            sdui_ip = gr.Textbox(label="SD-WebUI(--api) IP", value=server_ip.ip)
            sdui_port = gr.Number(label="SD-WebUI(--api) Port", value=server_ip.port)
            sdui_apply = gr.Button("Apply", variant="primary")
            sdui_apply.click(
                server_ip.new,
                inputs=[sdui_ip, sdui_port]
            )

        with gr.Tabs():
            tabs = get_ui()
            for tab in tabs:
                with gr.Tab(tab.title()):
                    # 各タブの要素を保存するための辞書
                    tab_ui_elements = {}

                    # タブ内のUIを生成し、そのエレメントを辞書に格納
                    def capture_ui(component_name, component):
                        #print(f"Captured UI: {component_name}, {component}")
                        tab_ui_elements[component_name] = component

                    # 実際のUI生成
                    tab.ui(lambda component_name, component: capture_ui(component_name, component))

                    # タブ全体のエレメントを保存
                    # tab_elements[tab.title()] = tab_ui_elements

    return block, {}

def jishaku_launcher():
    def read_output(process):
        """
        サブプロセスの出力をリアルタイムで読み取り、コンソールに表示します。
        """
        try:
            with process.stdout:
                for line in iter(process.stdout.readline, ''):
                    print(f"[JSK-Launcher]: {line}", end='')
        except Exception as e:
            print(f"[JSK-Launcher]: 出力の読み取り中にエラーが発生しました: {e}")

    if os.name == 'nt':
        # Windowsの場合
        venv_python = os.path.join(".venv", "Scripts", "python.exe")
    else:
        # Unix/Linux/Macの場合
        venv_python = os.path.join(".venv", "bin", "python")

        # 実行したいコマンドのリスト
    commands = [venv_python, "-u", "pem_jsk.py"]
    try:
        proc = subprocess.Popen(
            commands,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # 出力読み取り用のスレッドを開始
        threading.Thread(target=read_output, args=(proc,), daemon=True).start()
        threading.Thread(target=read_output, args=(proc.stderr,), daemon=True).start()

        # プロセス終了まで待機し、異常終了の場合はログ出力
        retcode = proc.wait()
        if retcode != 0:
            print(f"[JSK-Launcher]: プロセスが異常終了しました。戻り値: {retcode}")

    except subprocess.CalledProcessError as e:
        print(f"[JSK-Launcher]: Error in pem_jsk.py:\n{e.stderr}")

    except Exception as e:
        print(f"[JSK-Launcher]: Error while launching: {e}")

def launch_server():
    app = shared.app
    uvicorn.run(app, host=shared.args.server_ip, port=7850)


def launch():
    parse_args()  # ArgumentParser
    default_model = load_default_model() # Load Model

    # fastapi server
    initialize_server()
    server = threading.Thread(target=launch_server, daemon=True)
    server.start()

    shared.sd_webui_exists = search_sd_webui_at1()
    shared.driver_path = auto_install_chromedriver_for_selenium()
    if default_model is not None: shared.model_file = default_model
    os.environ["PATH"] += os.pathsep + shared.driver_path

    if not shared.sd_webui_exists:
        raise ValueError("REQUIRED AUTOMATIC1111/stable-diffusion-webui (see README for more information)")

    if not shared.args.ignore_cuda:
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA isn't Available. may features ALWAYS throw critical errors.\n(--ignore_cuda to bypass check. errors keep occurred.)")

    if not shared.args.nojsk:
        # Jishaku
        thread = threading.Thread(target=jishaku_launcher)
        thread.start()

    else:
        print("[Jishaku]: --nojsk accepted. Jishaku was disabled.")

    ui, _ = make_ui()
    file_cleaner()
    ui.queue(64)
    ui.launch(
        inbrowser=True,
        server_name=shared.args.server_ip,
        server_port=shared.args.server_port,
        favicon_path="favicon.png"
    )
    return

if __name__ == "__main__":
    launch()