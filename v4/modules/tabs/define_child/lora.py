from v4.webui import UiTabs, os, gr
from typing import *
from v4.lunapy_module_importer import Importer

class Template(UiTabs):
  def __init__(self, path):
    super().__init__(path)
    self.child_path = os.path.join(UiTabs.PATH, "define_child", "lora_versions")
  
  def title(self):
    return "LoRA"

  def index(self):
    return 1
  
  def ui(self, outlet):
    def selected_ver(ver):
      invisible = gr.update(visible=False)
      visible = gr.update(visible=True)
      
      if ver == "v5":
        return visible
    
    def get_ver_tabs(tabs:List[UiTabs], rtn_version:Literal["v5"]="v5") -> UiTabs:
      version_list = {
        "v5": 1
      }
      trigger_index = version_list[rtn_version]
      for tab in tabs:
        if tab in tabs:
          if tab.index() == trigger_index:
            return tab
    
    child_tabs = self.get_ui()
    
    tmpl_common = Importer("modules.generate.common")
    get_lora_template = tmpl_common.obtain_lora_list
    module = Importer("modules.manage.lora.save")
    
    with gr.Blocks():
      with gr.Row():
        version = gr.Dropdown(label="version", scale=3, choices=module.get_avv(), value=module.get_recommend_version())
      
      with gr.Column(visible=True) as v5_root:
        with gr.Tabs():
          with gr.Tab("v5"): # version によって変更するタブ  template/save.py 参照
            get_ver_tabs(child_tabs, "v5")()
      
      version.change(
        selected_ver, version, [v5_root]
      )
      