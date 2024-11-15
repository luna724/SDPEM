from v4.webui import UiTabs, os, gr
from v4.lunapy_module_importer import Importer

class Template(UiTabs):
  def __init__(self, path):
    super().__init__(path)
    self.child_path = os.path.join(UiTabs.PATH, "generate_child")
  
  def title(self):
    return "Templates"

  def index(self):
    return 0
  
  def ui(self, outlet):
    version = "version: v4.1.2R"
    
    class var:
      refresh = "\U0001f504"
      cfn:dict = {
        "interactive": False,
        "show_copy_button": True,
        "max_lines": 1
      }
    
    config = Importer("modules.config.get").get_spec_value("user_variable")["ui"]["system"]["generate"]
    tmpl_common = Importer("modules.generate.common")
    get_template = tmpl_common.obtain_template_list
    get_lora_template = tmpl_common.obtain_lora_list
    
    with gr.Blocks() as iface:
      gr.Markdown(version)
      
      # Initialize
      module = Importer("modules.generate.template")
      generate = Importer("modules.generate.generate")
      with gr.Row():
        template = gr.Dropdown(label="Template", choices=get_template.webui(), scale=4)
        template_refresh = gr.Button(var.refresh, scale=1)
        template_refresh.click(
          fn=get_template.update,
          outputs=template
        )
        
        lora = gr.Dropdown(label="LoRA Template", choices=get_lora_template.manual(), scale=4)
        lora_refresh = gr.Button(var.refresh, scale=1)
        lora_refresh.click(
          fn=get_lora_template.update, outputs=lora
        )
      
      with gr.Accordion("LoRA Variables", open=True, visible=False) as lora_var:
        with gr.Row():
          lora_var_check_1 = gr.Checkbox(label="", interactive=False, value=False)
          lora_var_check_2 = gr.Checkbox(label="", interactive=False, value=False)
        with gr.Row():
          lora_var_check_1_info = gr.Textbox(label="", **var.cfn)
          lora_var_check_2_info = gr.Textbox(label="", **var.cfn)
          
      with gr.Blocks():
        with gr.Row():
          with gr.Column():
            # Code for user variable
            with gr.Row():
              lwcfg = config["lora_weight_range"]
              lora_weight = gr.Slider(lwcfg[0], lwcfg[1], 0.75, step=lwcfg[2], label="LoRA Weight")
              extend_lora_enable = gr.Checkbox(label="Enable Extend prompt", value=False)
            with gr.Row():
              enable_adetailer_lora = gr.Checkbox(label="Enable ADetailer LoRA", value=True)
              enable_negative_lora = gr.Checkbox(label="Enable negative LoRA", value=True)
            with gr.Row():
              realtime_infer = gr.Checkbox(label="Realtime Infer (get Prompt/Negative from right tab)", value=False)
              use_prompt_nsfw_mode = gr.Checkbox(label="Use prompt NSFW Mode (if prompt supported)", value=False)
            
            with gr.Accordion("some variables", open=False):
              with gr.Row():
                face = gr.Textbox(label="$FACE")
                face2 = gr.Textbox(label="$FACE (secondary)")
              with gr.Row():
                location = gr.Textbox(label="$LOCATION")
                location2 = gr.Textbox(label="$LOCATION (secondary)")
              with gr.Row():
                accessory = gr.Textbox(label="$ACCESSORY")
                other = gr.Textbox(label="$OTHER")
              with gr.Row():
                header = gr.Textbox(label="Header")
                lower = gr.Textbox(label="Lower")
              variables_obtain_from_right = gr.Button("Get from example data")
              variables_obtain_from_right.click(
                module.variables_from_example,
                outputs=[
                  face, face2, location, location2, accessory, other,
                  header, lower
                ]
              )
              
            infer = gr.Button("Generate", variant="primary")
            sd_paste = gr.Button("copy Paster")
            
            with gr.Row():
              prompt = gr.Textbox(label="output Prompt", lines=5, interactive=False, show_copy_button=True)
              negative = gr.Textbox(label="output Negative", lines=5, interactive=False, show_copy_button=True)
            with gr.Row():
              ad_prompt = gr.Textbox(label="output ADetailer prompt", lines=3, interactive=False, show_copy_button=True)
              ad_negative = gr.Textbox(label="output ADetailer negative prompt", lines=3, interactive=False, show_copy_button=True)
            
          with gr.Column():
            # Code for NOT Interactive interface
            # Selected LoRA
            with gr.Row():
              lora_id_1 = gr.Textbox(label="LoRA ID", **var.cfn)
              lora_nm_1 = gr.Textbox(label="LoRA Name", **var.cfn)
            with gr.Row():
              lora_pm_1 = gr.Textbox(label="LoRA Prompt", **var.cfn)
              lora_ex_1 = gr.Textbox(label="LoRA Extend", **var.cfn)
            
            # Selected Template
            with gr.Row():
              method = gr.Textbox(label="Method ver.", **var.cfn)
              tmpl_key = gr.Textbox(label="Key", **var.cfn)
            with gr.Column():
              gr.Markdown("theses(Prompt/Negative) values are updatable from Left tab's value")
              tmpl_prompts_info = gr.HTML(every=module.get_prompts_info)
            with gr.Row():
              tmpl_prompt = gr.Textbox(label="Prompt", lines=5, interactive=True)
              tmpl_negative = gr.Textbox(label="Negative", lines=5, interactive=True)
            update_tmpl_prompt_negative = gr.Button("Update with this values (Prompt/Negative)", size="sm")
            update_tmpl_prompt_negative.click(
              module.update_prompt_only,
              [tmpl_prompt, tmpl_negative]
            )
            use_prompt_nsfw_mode.change(
              module.use_prompt_nsfw_mode,
              use_prompt_nsfw_mode, [tmpl_prompt, tmpl_negative]
            )
            
            
            load_viewer = gr.Button("Load viewers", variant="primary")
            
            tmpl_adetailer = gr.Checkbox(label="ADetailer Status", visible=False, **var.cfn)
            with gr.Accordion("ADetailer Status", visible=True) as tmpl_adetailer_visible:
              with gr.Row():
                tmpl_ad_prompt = gr.Textbox(label="Prompt 1st", lines=3, interactive=False)
                tmpl_ad_negative = gr.Textbox(label="Negative 1st", lines=3, interactive=False)
            tmpl_adetailer.change(
              module.lib.bool2visible, tmpl_adetailer, tmpl_adetailer_visible
            )
            
            tmpl_hires = gr.Checkbox(label="Hires.fix Status", visible=False, **var.cfn)
            with gr.Accordion("Hires.fix Status", visible=True) as tmpl_hires_visible:
              with gr.Row():
                tmpl_hi_upscaler = gr.Textbox(label="Hires UpScaler", **var.cfn)
                tmpl_hi_step = gr.Slider(0, 150, label="Hires Step", **var.cfn)
              with gr.Row():
                tmpl_hi_denoise = gr.Slider(0, 1, label="DeNoising Strength", **var.cfn)
                tmpl_hi_upscale = gr.Slider(1, 4, label="Upscale (×)", **var.cfn)
            tmpl_hires.change(
              module.lib.bool2visible, tmpl_hires, tmpl_hires_visible
            )
            
            tmpl_cn = gr.Checkbox(label="ControlNet[1st] Status", visible=False, **var.cfn)
            with gr.Accordion("ControlNet[1st] Status", visible=True) as tmpl_cn_visible:
              with gr.Row():
                tmpl_cn_mode = gr.Textbox(label="Control Mode", **var.cfn)
                tmpl_cn_weight = gr.Slider(-1, 2, label="Control Weights", **var.cfn)
              
              with gr.Accordion("Image"):
                cnimageelem = gr.Textbox(visible=False, value="cn_image", **var.cfn)
                tmpl_cn_image = gr.Image(height=768, width=768, image_mode="RGBA", type="pil", label="ControlNet Image", elem_classes=["image-center"], **var.cfn)
                tmpl_cn_load_image = gr.Button("Load", variant="primary")
                tmpl_cn_load_image.click(
                  module.load_image_ui, [cnimageelem], tmpl_cn_image
                ) ## Load CN Image Function
            tmpl_cn.change(
              module.lib.bool2visible, tmpl_cn, tmpl_cn_visible
            )
            
            # tmpl_rp = gr.Checkbox(label="Regional Prompter Status")
            # with gr.Group(visible=False) as tmpl_rp_visible:
            #   tmpl_rp_mode = gr.Textbox(label="Generation Mode", **var.cfn)
            #   with gr.Row():
            #     tmpl_rp_base = gr.Checkbox(label="Use base prompt", **var.cfn)
            #     tmpl_rp_common = gr.Checkbox(label="Use common prompt", **var.cfn)
            #     tmpl_rp_ncommon = gr.Checkbox(label="Use common negative prompt", **var.cfn)
            #   tmpl_rp_ratio = gr.Textbox(label="Base Ratio", **var.cfn)
              
            #   with gr.Row():
            #     tmpl_rp_stop = gr.Slider(0, 150, label="LoRA stop step", **var.cfn)
            #     tmpl_rp_hires = gr.Slider(0, 150, label="LoRA Hires stop step", **var.cfn)
              
            #   with gr.Row():
            #     with gr.Column():
            #       tmpl_rp_split = gr.Textbox(label="Main Matrix mode", **var.cfn)
            #       tmpl_rp_division = gr.Textbox(label="Division Ratio", **var.cfn)
            #     with gr.Column():
            #       tmpl_rp_w = gr.Slider(1, 2048, label="Width", **var.cfn)
            #       tmpl_rp_h = gr.Slider(1, 2048, label="Height", **var.cfn)
              
            #   with gr.Row():
            #     tmpl_rp_template = gr.Textbox(label="Template", **var.cfn)
              
            #   with gr.Accordion(label="Sample"):
            #     tmpl_rp_image = gr.Image(height=768, width=768, image_mode="RGBA", type="pil", label="COntrolNet Image", elem_classes=["image-center"], **var.cfn)
            #     tmpl_rp_load_image = gr.Button("Load", variant="primary")
            #     tmpl_rp_load_image.click(
            #       None, [template], tmpl_rp_image
            #     ) ## Load RP Sample Image Function
            
            tmpl_ex = gr.Checkbox(label="Example values", visible=False, **var.cfn)
            with gr.Accordion("Example values", visible=True) as tmpl_ex_visible:
              tmpl_ex_lora = gr.Textbox(label="LoRA Template (When saved)", **var.cfn)
              
              with gr.Row():
                tmpl_ex_weight = gr.Slider(-2.0, 2.0, label="LoRA Weight", **var.cfn)
                tmpl_ex_extend = gr.Checkbox(label="Apply Extend Prompt", **var.cfn)
              with gr.Row():
                tmpl_ex_header = gr.Textbox(label="Header", **var.cfn)
                tmpl_ex_lower = gr.Textbox(label="Lower", **var.cfn)
              with gr.Row():
                tmpl_ex_face = gr.Textbox(label="1st Face", **var.cfn)
                tmpl_ex_face_2 = gr.Textbox(label="2nd Face", **var.cfn)
              with gr.Row():
                tmpl_ex_location = gr.Textbox(label="1st Location", **var.cfn)
                tmpl_ex_location_2 = gr.Textbox(label="2nd Location", **var.cfn)
              with gr.Row():
                tmpl_ex_accessory = gr.Textbox(label="Accessory", **var.cfn)
                tmpl_ex_other = gr.Textbox(label="Other", **var.cfn)
              
              with gr.Blocks():
                with gr.Row():
                  tmpl_ex_w = gr.Slider(1, 2048, label="Width", **var.cfn)
                  tmpl_ex_h = gr.Slider(1, 2048, label="Height", **var.cfn)
                with gr.Row():
                  clip_skip = gr.Slider(1, 15, label="Clip Skip", **var.cfn)
              
              with gr.Accordion("Image"):
                eximageelem = gr.Textbox(visible=False, value="ex_image", **var.cfn)
                tmpl_ex_image = gr.Image(height=768, width=768, image_mode="RGBA", type="pil", label="Image", elem_classes=["image-center"], **var.cfn)
                tmpl_ex_load_image = gr.Button("Load", variant="primary")
                tmpl_ex_load_image.click(
                  module.load_image_ui, [eximageelem], tmpl_ex_image
                ) ## Load Sample Image Function
            tmpl_ex.change(
              module.lib.bool2visible, tmpl_ex, tmpl_ex_visible
            )
            
            tmpl_bi = gr.Checkbox(label="Builtins Opts", value=True, visible=False, **var.cfn)
            with gr.Accordion("Builtins Opts", visible=True) as tmpl_bi_visible:
              with gr.Row():
                tmpl_bi_model = gr.Textbox(label="Checkpoints", **var.cfn)
                tmpl_bi_vae = gr.Textbox(label="VAE", value="Auto", **var.cfn)
              with gr.Row():
                tmpl_bi_refiner = gr.Textbox(label="Refiner Checkpoints", **var.cfn)
                tmpl_bi_refiner_swap_to = gr.Slider(0, 1, step=0.05, label="Refiner rate", **var.cfn)
              with gr.Row():
                tmpl_bi_sampler = gr.Textbox(label="Sampler", **var.cfn)
                tmpl_bi_method = gr.Textbox(label="Sampler Method", **var.cfn)
            tmpl_bi.change(
              module.lib.bool2visible, tmpl_bi, tmpl_bi_visible
            )
            
            ## Update database
            lora.change(
              module.change_lora, lora, [lora_var, # 
                lora_var_check_1, lora_var_check_1_info, #
                lora_var_check_2, lora_var_check_2_info, # LoRA Variables
                lora_id_1, lora_nm_1, lora_pm_1, lora_ex_1 # LoRA Example Viewer
                ]
            )
            template.change(
              module.change_template, template,
              [
                method, tmpl_key, tmpl_prompt, tmpl_negative,
                
              ]
            )
            
            load_viewer.click(
              module.load_viewers,
              inputs=[template], outputs=[
                tmpl_adetailer_visible, tmpl_ad_prompt, tmpl_ad_negative,
                tmpl_hires_visible, tmpl_hi_upscaler, tmpl_hi_step,
                tmpl_hi_denoise, tmpl_hi_upscale, tmpl_cn_visible,
                tmpl_cn_mode, tmpl_cn_weight, tmpl_ex_visible, tmpl_ex_lora,
                tmpl_ex_weight, tmpl_ex_extend, tmpl_ex_header, tmpl_ex_lower,
                tmpl_ex_face, tmpl_ex_face_2, tmpl_ex_location,
                tmpl_ex_location_2, tmpl_ex_accessory, tmpl_ex_other,
                tmpl_ex_w, tmpl_ex_h, clip_skip, tmpl_bi_visible, tmpl_bi_model,
                tmpl_bi_vae, tmpl_bi_sampler, tmpl_bi_method, tmpl_bi_refiner,
                tmpl_bi_refiner_swap_to
              ]
            )
            
            
            ## Inference
            infer.click(
              generate.generate,
              [
                template, lora, 
                lora_weight, extend_lora_enable, enable_adetailer_lora,
                enable_negative_lora, realtime_infer, tmpl_prompt, tmpl_negative,
                use_prompt_nsfw_mode, lora_var_check_1, lora_var_check_2,
                face, face2, location, location2, accessory, other,
                header, lower
              ],
              [prompt, negative, ad_prompt, ad_negative]
            )
            
            sd_paste.click(
              generate.generate_paster,
              [
                template, lora, 
                lora_weight, extend_lora_enable, enable_adetailer_lora,
                enable_negative_lora, realtime_infer, tmpl_prompt, tmpl_negative,
                use_prompt_nsfw_mode, lora_var_check_1, lora_var_check_2,
                face, face2, location, location2, accessory, other,
                header, lower
              ],
              prompt
            )