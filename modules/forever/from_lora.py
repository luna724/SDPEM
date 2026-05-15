import traceback
from typing import *
import gradio as gr
import random

from modules.prompt_setting import setting
from modules.prompt_processor import PromptProcessor
from modules.forever.common2 import ForeverGenerationTemplate
from utils import *

# ForeverGeneration instanceは tab/.. によって保持され生涯有効
class ForeverGenerationFromLoRA(ForeverGenerationTemplate):
    def on_reset(self):
        self.lora_names: list[str]
        
        # Random LoRA selection
        self.lora_list: list[str] = []
        self.enable_random_lora: bool = False
        self.rnd_lora_select_count: int = 0
        self.default_prompt_request_param = setting.request_param().copy()

    async def get_payload(self) -> dict:
        p = await self._get_payload()
        
        # Select LoRA for this generation
        def select_lora() -> list[str]:
            current_lora = self.lora_list
            if self.enable_random_lora and len(self.lora_list) >= self.rnd_lora_select_count:
                current_lora = random.sample(self.lora_list, k=self.rnd_lora_select_count)
                self.stdout(f"[Random LoRA] Selected: {current_lora}")
            return current_lora
        
        
        current_request_param = self.default_prompt_request_param.copy()
        prompt_generated = False
        
        try:
            for t in range(10):
                current_request_param["lora_name"] = select_lora()
                try:
                    prompt = await PromptProcessor.gather_from_lora_rnd_prompt(
                        proc_kw=self.processor_prompt_param,
                        max_tries=self.prompt_generation_max_tries,
                        **current_request_param,
                    )
                    if len(prompt) == 0:
                        raise ValueError("No prompt could be generated.")
                    
                except Exception as e:
                    self.stdout(f"[Random LoRA] Not enough tags could be gathered with the current LoRA selection. Retrying... ({t+1}) ({e})")
                    traceback.print_exc();
                    continue 
                
                prompt_generated = True
                break
            if not prompt_generated:
                raise ValueError("Failed to generate prompt after 10 attempts.")
            
        except ValueError as e:
            raise gr.Error(
                f"Failed to generate prompt. Please check your Prompt Settings. ({e})"
            )
        except RuntimeError:
            raise gr.Error(
                "Failed to generate prompt after multiple attempts. Please adjust your Prompt Settings."
            )

        # rpp = self.regional_prompter_param_default.copy()        
        # try:
        #     rpp["Regional Prompter"]["args"][3] = random.choice(self.rp_matrix_mode)
        #     rpp["Regional Prompter"]["args"][6] = random.choice(self.divine_ratio)
        #     rpp["Regional Prompter"]["args"][11] = self.rp_calculation
        #     println(f"[Regional Prompter] Matrix Mode: {rpp['Regional Prompter']['args'][3]}, Divine Ratio: {rpp['Regional Prompter']['args'][6]}, Calculation: {rpp['Regional Prompter']['args'][11]}")
            
        # except (IndexError, KeyError):
        #     warn(
        #         "IndexError or KeyError occurred while updating Regional Prompter parameters."
        #     )
        # finally:
        #     p["alwayson_scripts"].update(rpp)    
        p["prompt"] = ", ".join(prompt)
        
        return p
    
    async def on_update_prompt_settings(
        self, lora, add_lora_name, add_trigger_word, add_trig_to, lora_weight, lora_weight_prio,
        enable_random_lora, rnd_lora_select_count, 
        _new_param: dict, _new_kp: dict,
        **kw
    ):
        if enable_random_lora:
            self.rnd_lora_select_count = min(max(1, rnd_lora_select_count), len(lora))
            if len(lora) < self.rnd_lora_select_count:
                raise gr.Error(f"Not enough LoRAs selected for random selection ({len(lora)} < {self.rnd_lora_select_count})")
        self.enable_random_lora = enable_random_lora
        
        new_param = _new_param | {
            "lora_name": lora,
            "lora_weight": lora_weight,
            "lora_weight_prio": lora_weight_prio,
            "add_lora_name": add_lora_name,
            "add_trigger_word": add_trigger_word,
            "add_trig_to": add_trig_to,
        } | setting.request_param(pop_for_processor=True)
        new_kp = _new_kp
        self.lora_list = lora
        
        validate = await PromptProcessor.test_from_lora_rnd_prompt_available(test_prompt=False, kw_p=new_kp, kw=new_param)
        # if validate is True:
        #     self.default_prompt_request_param = new_param
        #     gr.Info("Prompt settings updated successfully.")
        #     self.stdout("Prompt settings updated successfully.")
        # else:
        #     raise gr.Error("Failed to update prompt settings. Please check your settings.")

        self.processor_prompt_param = new_kp
        self.default_prompt_request_param = new_param 
        return validate is True
        
    # def start(...):
        # self.regional_prompter_param_default = (
        #     {
        #         "Regional Prompter": {
        #             "args": [
        #                 active_rp, False, rp_mode, None, #matrix mode
        #                 "TODO:Mask", "TODO:Prompt", None, # Divine
        #                 rp_base_ratio, rp_base, False, False,
        #                 None, # rp_calc
        #                 False, 0, 0, overlay_ratio, None, # mask
        #                 lora_stop_step, 0, False
        #             ]
        #         }
        #     }
        #     if active_rp
        #     else {}
        # )
        
        