import json
import os
import shutil
def bc():
  #key preset -> freeu_preset
  #key enable_stop -> enable_auto_stop
  #key stop_after_minutes -> stop_minutes
  # key stop_after_images -> stop_after_img
  #key base_chance -> random_rate
  #key max_tags -> tags
  mv_key=['tags', 'random_rate', 'add_lora_name', 'add_trigger_word', 'add_trig_to', 'lora_weight', 'lora_weight_prio', 'header', 'footer', 'negative', 'prompt_weight_chance', 'prompt_weight_min', 'prompt_weight_max', 'remove_character', 'blacklist', 's_method', 'scheduler', 'steps_min', 'steps_max', 'cfg_min', 'cfg_max', 'batch_count', 'batch_size', 'size', 'adetailer', 'enable_hand_tap', 'disable_lora_in_adetailer', 'enable_freeu', 'freeu_preset', 'enable_sag', 'sag_strength', 'enable_auto_stop', 'stop_mode', 'stop_minutes', 'stop_after_img', 'stop_after_datetime', 'save_tmp_images', 'prompt_generation_max_tries', 'booru_filter_enable', 'booru_use_shared', 'booru_model', 'enable_neveroom_unet', 'enable_neveroom_vae', 'merge_adetailer_test', 'output_dir', 'output_format', 'output_name', 'save_metadata', 'save_infotext']
  mv_from="from_lora" # or from_images
  
  #rc-instance_name 
  # forever_generation/from_lora -> legacy_forever/from_lora
  # forever_generation/from_images -> legacy_forever/from_images
  if os.path.exists("config/presets/forever_generation.from_lora"):
    shutil.copytree("config/presets/forever_generation.from_lora", "config/presets/legacy_forever.from_lora", dirs_exist_ok=True)
  if os.path.exists("config/presets/forever_generation.from_images"):
    shutil.copytree("config/presets/forever_generation.from_images", "config/presets/legacy_forever.from_images", dirs_exist_ok=True)
  
  if os.path.exists(f"config/presets/forever_generation.{mv_from}/default.json"):
    with open(f"config/presets/forever_generation.{mv_from}/default.json", "r", encoding="utf-8") as f:
      data = json.load(f)
    com = {}
    for k,x in data.items():
      if k in mv_key:
        com[k] = x
      if k in ["preset", "enable_stop", "stop_after_minutes", "stop_after_images", "base_chance", "max_tags"]:
        if k == "preset":
          com["freeu_preset"] = x
        elif k == "enable_stop":
          com["enable_auto_stop"] = x
        elif k == "stop_after_minutes":
          com["stop_minutes"] = x
        elif k == "stop_after_images":
          com["stop_after_img"] = x
        elif k == "base_chance":
          com["random_rate"] = x
        elif k == "max_tags":
          com["tags"] = x
    with open(f"config/presets/forever_generation.common/default.json", "w", encoding="utf-8") as f:
      json.dump(com, f, indent=2)
    return True# True
  return False

def bc_3():
  # legacy_forever/from_lora -> forever_generation/from_lora
  # legacy_forever/from_images -> forever_generation/from_images
  # forever_generation/common -> 分散
  
  if os.path.exists("config/presets/legacy_forever.from_lora"):
    shutil.copytree("config/presets/legacy_forever.from_lora", "config/presets/forever_generation.from_lora", dirs_exist_ok=True)
    shutil.rmtree("config/presets/legacy_forever.from_lora", ignore_errors=True)
  if os.path.exists("config/presets/legacy_forever.from_images"):
    shutil.copytree("config/presets/legacy_forever.from_images", "config/presets/forever_generation.from_images", dirs_exist_ok=True)
    shutil.rmtree("config/presets/legacy_forever.from_images", ignore_errors=True)
  if os.path.exists("config/presets/forever_generation.common"):
    for f in os.listdir("config/presets/forever_generation.common"):
      if not f.endswith(".json"):
        continue
      src = os.path.join("config/presets/forever_generation.common", f)
      with open(src, "r", encoding="utf-8") as f:
        data = json.load(f)
      for r in ["from_lora", "from_images", "from_data"]:
        dst_dir = os.path.join(f"config/presets/forever_generation.{r}")
        os.makedirs(dst_dir, exist_ok=True)
        dst = os.path.join(dst_dir, f)
        if os.path.exists(dst):
          with open(dst, "r", encoding="utf-8") as f:
            dst_data = json.load(f)
        else: dst_data = {}
        dst_data.update(data)
        with open(dst, "w", encoding="utf-8") as f:
          json.dump(dst_data, f, separators=(',', ':'))
        
      # shutil.copy(src, dst)
    # shutil.rmtree("config/presets/forever_generation.common", ignore_errors=True)
    return True