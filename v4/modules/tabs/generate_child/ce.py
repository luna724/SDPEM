from v4.webui import UiTabs, os, gr
from v4.lunapy_module_importer import Importer

class CE(UiTabs):
  def __init__(self, path):
    super().__init__(path)
    
    self.child_path = os.path.join(UiTabs.PATH, "generate_child")
  
  def title(self):
    return "Character Exchanger"
  
  def index(self):
    return 1
  
  def ui(self, outlet):
    generate_common = Importer("modules.generate.common")
    character_exchanger = Importer("modules.ce_all")
    
    with gr.Blocks() as iface:
      gr.Markdown("version: CE-v3b5")
      
      with gr.Row():
        mode = gr.Dropdown(choices=["lora, name", "prompt", "extend"], label="mode", value=["lora, name", "prompt", "extend"], multiselect=True)
      
      with gr.Row():
        template = gr.Dropdown(label="template", choices=generate_common.obtain_lora_list.manual())
        refresh = gr.Button("refresh")
        refresh.click(generate_common.obtain_lora_list.update, outputs=template)
      
      with gr.Row():
        target = gr.Textbox(label="input", lines=4, scale=10)
        outs = gr.Textbox(label="output", interactive=False, show_copy_button=True, lines=4, scale=9)
      
      with gr.Blocks():
        with gr.Row():
          template_mode = gr.Checkbox(label="for template")
        
      status = gr.Textbox(label="status", interactive=False)
      run = gr.Button("run", variant="primary")
      run.click(
        character_exchanger.call,
        [mode, target, template, template_mode],
        [outs, status]
      )