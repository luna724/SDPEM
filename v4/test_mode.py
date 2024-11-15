import gradio as gr
from typing import Literal

from test_script import ce, g_template, mt_s_lora
from lunapy_module_importer import Importer

def main(mode:Literal["ce", "g_template", "mt_s_template", "mt_s_lora"]):
  if mode == "ce": #Archived (tests/ce.py)
    iface = ce.get()
  elif mode == "g_template": #Archived (tests/g_template.py)
    iface = g_template.get()
  elif mode == "mt_s_lora":
    iface = mt_s_lora.get()
  elif mode == "mt_s_template":
    tmpl_common = Importer("modules.generate.common")
    get_template = tmpl_common.obtain_template_list
    get_lora_template = tmpl_common.obtain_lora_list
    
    module = Importer("modules.manage.templates.save")
    AVV = module.available_versions
    
    with gr.Blocks() as iface:
      ## TODO: get versions (e.g. v3/modules/ui/mt_child/define_child/prompt.py)
      
      ## From below, insert to "/prompts/v4.py"
      with gr.Blocks():
        display_name = gr.Textbox(label="displayName")
        
        with gr.Row():
          prompt = gr.Textbox(label="Prompt", lines=4, placeholder="All buildins keywords at template_info.md")
          negative = gr.Textbox(label="Negative prompt", lines=4, placeholder="if blank, insteads database's value\nif need blank Negative, set to \".\"")
        
        with gr.Row():
          with gr.Column():
            with gr.Group(visible=True) as example:
              gr.Markdown("Example releases soon.. (planning: v4.0-pre2 or later)")
          
          with gr.Column():
            adetailer_status = gr.Checkbox(label="Activate ADetailer", value=False)
            with gr.Group(visible=False) as adetailer:
              adetailer_name = gr.Textbox("ADetailer", visible=False)
              gr.Markdown("ADetailer releases soon.. (planning: v4.0-pre1)")
              with gr.Tab("1st"):
                adetailer_model = gr.Dropdown(
                  allow_custom_value=True,
                  label="ADetailer Model", choices=["face_yolov8n.pt", "face_yolov8s.pt"],
                  value="face_yolov8n.pt"
                )
                adetailer_prompt = gr.Textbox(label="ADetailer prompt", lines=3)
                adetailer_negative = gr.Textbox(label="ADetailer negative", lines=3)
            adetailer_status.change(module.bool2visible, [adetailer_status, adetailer_name], [adetailer, adetailer_status])
            
            

        gr.Markdown("More soon..")
      overwrite = gr.Checkbox(label="Overwrite", value=False)
      save = gr.Button("Save", variant="primary")
      save.click(
        module.save_primary, 
        inputs = [
          display_name, prompt, negative, 
          adetailer_status, adetailer_model, adetailer_prompt, adetailer_negative,
          overwrite
        ]
      )
      

                
  iface.queue(64).launch(server_port=9999)