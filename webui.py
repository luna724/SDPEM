import importlib
import logging
import sys
import traceback
from typing import *
import os
import gradio as gr
import asyncio
import inspect
import abc

from utils import println, critical


class UiTabs:
    PATH = os.path.join(os.getcwd(), "modules/tabs")

    def __init__(self, path: str) -> None:
        self.filepath = path
        self.rootpath = UiTabs.PATH
        self.child_path = None
        pass

    @abc.abstractmethod
    def title(self) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def index(self) -> int:
        """return ui's index"""
        raise NotImplementedError()
    
    def _id(self) -> str:
        return self.title().replace(" ", "_")+"_tab"
    def _class(self) -> str | list[str]:
        return None

    def get_ui(self) -> list:
        tabs = []
        files = [file for file in os.listdir(self.child_path) if file.endswith(".py")]
        # print(f"Child path: {self.child_path} ({files})")

        for file in files:
            module_name = file[:-3]
            module_path = (
                os.path.relpath(self.child_path, UiTabs.PATH)
                .replace("/", ".")
                .replace("\\", ".")
                .strip(".")
            )
            # print(f"Loading {module_path}'s child tab ({module_name})..")
            module = importlib.import_module(
                f"modules.tabs.{module_path}.{module_name}"
            )

            attrs = module.__dict__
            TabClass = [
                x
                for x in attrs.values()
                if type(x) == type and issubclass(x, UiTabs) and not x == UiTabs
            ]
            if len(TabClass) > 0:
                tabs.append((file, TabClass[0]))

        tabs = sorted(
            [TabClass(file) for file, TabClass in tabs], key=lambda x: x.index()
        )
        return tabs

    async def ui(self, outlet: Callable[[str, gr.components.Component], None]) -> None:
        """make ui data
        don't return"""
        with gr.Blocks():

            with gr.Tabs():
                tabs = self.get_ui()
                for tab in tabs:
                    with gr.Tab(tab.title(), elem_id=tab._id(), elem_classes=tab._class()):
                        tab_ui_elements = {}

                        # タブ内のUIを生成し、そのエレメントを辞書に格納
                        def capture_ui(component_name, component):
                            # print(f"Captured UI: {component_name}, {component}")
                            tab_ui_elements[component_name] = component

                        # 実際のUI生成 (async/sync両対応)
                        ui_method = tab.ui
                        if inspect.iscoroutinefunction(ui_method):
                            await ui_method(
                                lambda component_name, component: capture_ui(
                                    component_name, component
                                )
                            )
                        else:
                            ui_method(
                                lambda component_name, component: capture_ui(
                                    component_name, component
                                )
                            )

                        # タブ全体のエレメントを保存
                        # tab_ui_elements
        # shared.ui_obj[self.title()] = tab_elements

    # def has_child(self):
    #   return [rootID, child_rel_import_path, importlib's Path]


async def make_ui() -> tuple[gr.Blocks, dict]:
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
                x
                for x in attrs.values()
                if isinstance(x, type)
                and issubclass(x, UiTabs_ref)
                and not x == UiTabs_ref
            ]
            # print(f"UiTabs reference in webui: {UiTabs}")
            # print(f"UiTabs reference in module: {sys.modules['webui'].UiTabs}")
            # print(f"Is same reference: {UiTabs is sys.modules['webui'].UiTabs}")

            if len(TabClass) > 0:
                tabs.append((file, TabClass[0]))
                # print(f"tab module found in ({module_name})")

        tabs = sorted(
            [TabClass(file) for file, TabClass in tabs], key=lambda x: x.index()
        )
        return tabs

    with open("style.css", "r", encoding="utf-8") as css_f:
        css = css_f.read()

    block = gr.Blocks(title="luna724 / SD-PEM Client", analytics_enabled=False, css=css)
    # tab_elements = {}
    with block:
        with gr.Tabs():
            tabs = get_ui()
            for tab in tabs:
                with gr.Tab(tab.title()):
                    # 各タブの要素を保存するための辞書
                    tab_ui_elements = {}
                    def capture_ui(component_name, component):
                        pass

                    # 実際のUI生成 (async/sync両対応)
                    ui_method = tab.ui
                    if inspect.iscoroutinefunction(ui_method):
                        await ui_method(
                            lambda component_name, component: capture_ui(
                                component_name, component
                            )
                        )
                    else:
                        ui_method(
                            lambda component_name, component: capture_ui(
                                component_name, component
                            )
                        )

                    # タブ全体のエレメントを保存
                    # tab_elements[tab.title()] = tab_ui_elements

    return block, {}


def register_apps() -> None:
    modules_root_dir = os.path.join(os.getcwd(), "modules/api")
    for root, _, files in os.walk(modules_root_dir):
        for filename in files:
            if filename.endswith(".py") and filename != "__init__.py":
                full_path = os.path.join(root, filename)
                # モジュール名を生成 (例: modules.api.subdir.filename)
                relative_path = os.path.relpath(full_path, os.path.join(os.getcwd()))
                module_name = relative_path.replace(os.sep, ".")[:-3]

                try:
                    importlib.import_module(module_name)
                    println(f"Successfully imported module: {module_name}")
                except ImportError as e:
                    critical(f"Failed to import module {module_name}: {e}")
                    traceback.print_exc()


import uvicorn
import asyncio

async def launch(args=None) -> None:
    import shared
    import logger
    os.makedirs("./config", exist_ok=True)
    
    level = logging.INFO
    if args.debug is True: level = logging.DEBUG
    logger.setup_logger("SDPEM", level)
    
    go_web = False
    # argsが渡された場合は引数を使用
    if args:
        shared.ui_port = args.ui_port
        shared.pem_api_port = args.api_port
        go_web = args.go_web

    shared.pem_api += str(shared.pem_api_port)
    from init_model import init_models
    
    
    init_models()
    register_apps()
    t = asyncio.create_task(
        asyncio.to_thread(
            uvicorn.run,
            app=shared.app,
            host="127.0.0.1",
            port=shared.pem_api_port,
            log_level="info",
            timeout_keep_alive=120,
        )
    )
    
    try:
        ui, _ = await make_ui()
        ui.queue(64)
        ui.launch(
            server_name="0.0.0.0",
            server_port=shared.ui_port,
            inbrowser=go_web
        )
    except:
        traceback.print_exc()
        
    finally:
        t.cancel()
    return


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SD-PEM Web UI")
    parser.add_argument("--ui_port", type=int, default=7866, help="Port for UI server (default: 7866)")
    parser.add_argument("--api_port", type=int, default=7865, help="Port for API server (default: 7865)")
    parser.add_argument("--go_web", action="store_true", help="Enable opening the web UI in a browser")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    asyncio.run(launch(args))
