from typing import *
import gradio as gr

import os
import sys
import importlib

class UiTabs:
  PATH = os.path.join(os.getcwd(), "modules/tabs")
  
  def __init__(self, path):
    self.filepath = path
    self.rootpath = UiTabs.PATH
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

    for file in files:
      module_name = file[:-3]
      module_path = os.path.relpath(
        self.child_path, UiTabs.PATH 
      ).replace("/", ".").replace("\\", ".").strip(".")
      module = importlib.import_module(f"modules.tabs.{module_path}.{module_name}")
      
      attrs = module.__dict__
      TabClass = [
        x for x in attrs.values() if type(x) == type and issubclass(x, UiTabs) and not x == UiTabs
      ]
      if len(TabClass) > 0:
        tabs.append((file, TabClass[0]))
      
    tabs = sorted([TabClass(file) for file, TabClass in tabs], key= lambda x: x.index())
    return tabs
  
  def ui(self, outlet: Callable):
    """ make ui data 
    don't return """
    pass
  
  # def has_child(self):
  #   return [rootID, child_rel_import_path, importlib's Path]
  
  def __call__(self):
    child_dir = self.filepath[:-3]  #.py を取り除く子ディレクトリの検出
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
          ) # インポートしていたものを children に追加
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
          tab:UiTabs # for IDE
          with gr.Tab(tab.variable()[0]): 
            tab() 
    
    return self.ui(outlet)

class launch:
  def __init__(self, env_type:Literal["pem", "pdb"], **kwargs):
    self.is_api= env_type == "pdb"
    if self.is_api:
      raise RuntimeError("class webui.py:launch was called from SDPDB.\nthis class is ONLY supported SDPEM. please remove them.")
    
  @staticmethod
  def launch_ui(ui:gr.Blocks):
    # sys.path に addons を追加
    addons = os.listdir(
      os.path.join(os.getcwd(), "addons")
    )
    for addon in addons:
      if os.path.isdir(addon):
        sys.path.append(addon)
    
    from modules.addon import _addon as addon_util
    addon_util().load_addons()
    
    ui.queue(64)
    ui.launch(inbrowser=True)
    return
  
  @staticmethod
  def build_ui() -> gr.Blocks:
    def get_ui() -> List[UiTabs]:
      tabs = []
      files = [file for file in os.listdir(UiTabs.PATH) if file.endswith(".py")]
      
      for file in files:
        module_name = file[:-3]
        module = importlib.import_module(f"modules.tabs.{module_name}")
        
        attrs = module.__dict__
        TabClass = [
          x for x in attrs.values()
          if type(x) == type and issubclass(x, UiTabs) and not x == UiTabs
        ]
        if len(TabClass) > 0:
          tabs.append((file, TabClass[0]))
      
      tabs = sorted([TabClass(file) for file, TabClass in tabs], key=lambda x: x.index())
      return tabs
    
    block = gr.Blocks(title="lunapy / SD-PEM Client")
    
    with block:
      with gr.Tabs():
        tabs = get_ui()
        for tab in tabs:
          with gr.Tab(tab.title()):
            tab()
    
    return block
  
  def __call__(self):
    ui = self.build_ui()
    raise TimeoutError(self.launch_ui(ui))

# Define Importer
if "__main__" == "pem_launcher.py":
  import lunapy_module_importer
  lunapy_module_importer.Importer = lunapy_module_importer.moduleImporter("pem")