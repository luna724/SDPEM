import sys
from typing import *
import gradio as gr
import importlib

from initialize import *
import shared


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
        print(f"Child path: {self.child_path} ({files})")

        for file in files:
            module_name = file[:-3]
            module_path = os.path.relpath(
                self.child_path, UiTabs.PATH
            ).replace("/", ".").replace("\\", ".").strip(".")
            print(f"Loading {module_path}'s child tab ({module_name})..")
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
        pass

    # def has_child(self):
    #   return [rootID, child_rel_import_path, importlib's Path]

    def __call__(self):
        child_dir = self.filepath[:-3]  # .py を取り除く子ディレクトリの検出
        children = []
        tabs = []

        if os.path.isdir(child_dir):
            for file in [file for file in os.listdir(child_dir) if file.endswith(".py")]:
                module_name = file[:-3]

                parent = os.path.relpath(
                    UiTabs.PATH, UiTabs.PATH
                ).replace(
                    "/", "."
                ).strip(".")
                print("parent: ", parent)

                children.append(
                    importlib.import_module(
                        f"modules.tabs.{parent}.{module_name}"
                    )  # インポートしていたものを children に追加
                )

        children = sorted(children, key=lambda x: x.index())

        for child in children:
            # 辞書として変数の値を取得
            # このクラスのサブクラスを発見したら最初のものを追加
            attrs = child.__dict__
            tab = [x for x in attrs.values() if issubclass(x, UiTabs)]
            if len(tab) != 0:
                tabs.append(tab[0])

        def outlet():
            with gr.Tabs():
                for tab in tabs:
                    tab: UiTabs  # for IDE
                    with gr.Tab(tab.title()[0]):
                        tab()

        return self.ui(outlet)

def make_ui() -> gr.Blocks:
    def get_ui() -> List[UiTabs]:
        tabs = []
        files = [file for file in os.listdir(UiTabs.PATH) if file.endswith(".py")]

        for file in files:
            module_name = file[:-3]
            print(f"Loading tab ({module_name})..")
            module = importlib.import_module(f"modules.tabs.{module_name}")

            attrs = module.__dict__
            UiTabs_ref = sys.modules["webui"].UiTabs
            for x in attrs.values():
                print(f"Checking: {x}, type: {type(x)}")
                if isinstance(x, type):
                    print(f"Is subclass of UiTabs: {issubclass(x, UiTabs_ref)}")
            TabClass = [
                x for x in attrs.values()
                if isinstance(x, type) and issubclass(x, UiTabs_ref) and not x == UiTabs_ref
            ]
            print(f"UiTabs reference in webui: {UiTabs}")
            print(f"UiTabs reference in module: {sys.modules['webui'].UiTabs}")
            print(f"Is same reference: {UiTabs is sys.modules['webui'].UiTabs}")

            if len(TabClass) > 0:
                tabs.append((file, TabClass[0]))
                print(f"tab module found in ({module_name})")

        tabs = sorted([TabClass(file) for file, TabClass in tabs], key=lambda x: x.index())
        return tabs

    block = gr.Blocks(title="luna724 / SD-PEM Client", analytics_enabled=False)

    with block:
        with gr.Tabs():
            tabs = get_ui()
            for tab in tabs:
                with gr.Tab(tab.title()):
                    tab()

    return block

def launch():
    shared.sd_webui_exists = search_sd_webui_at1()
    shared.driver_path = auto_install_chromedriver_for_selenium()
    os.environ["PATH"] += os.pathsep + shared.driver_path

    ui = make_ui()
    ui.queue(64)
    ui.launch(inbrowser=True)
    return

if __name__ == "__main__":
    launch()