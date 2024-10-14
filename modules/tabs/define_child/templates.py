from webui import UiTabs, os, gr
from typing import *
from lunapy_module_importer import Importer

class Template(UiTabs):
  def __init__(self, path):
    super().__init__(path)
    self.child_path = os.path.join(UiTabs.PATH, "define_child", "template_versions")
  
  def title(self):
    return "Template"

  def index(self):
    return 0
  
  def ui(self, outlet):
    def selected_ver(ver):
      module.selected_version_changer(ver)
      invisible = gr.update(visible=False)
      visible = gr.update(visible=True)
      
      if ver == "v4.0":
        return visible
    
    def get_ver_tabs(tabs:List[UiTabs], rtn_version:Literal["v4pre1"]="v4pre1") -> UiTabs:
      version_list = {
        "v4pre1": 41
      }
      trigger_index = version_list[rtn_version]
      for tab in tabs:
        if tab in tabs:
          if tab.index() == trigger_index:
            return tab
    
    child_tabs = self.get_ui()
    
    module = Importer("modules.manage.templates.save")
    AVV = module.available_versions
    
    with gr.Blocks() as iface:
      ver = gr.Markdown("CURRENTLY Alpha: v4.0-pre1")
      
      selected_version = gr.Dropdown(AVV, value=AVV[0], label="Selected version")
      ## TODO: get versions (e.g. v3/modules/ui/mt_child/define_child/prompt.py)
      
      with gr.Column(visible=True) as v4pre1:
        with gr.Tabs():
          with gr.Tab("v4pre1"):
            get_ver_tabs(child_tabs, "v4pre1")()
      
      selected_version.change(
        selected_ver,
        selected_version,
        [v4pre1]
      )
