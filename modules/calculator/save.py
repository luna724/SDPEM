import time, uuid
import os
import traceback
import json

from logger import warn
from modules.events.generation_ended import OnGenerationEndedEvent, onGenerationEnded
from modules.utils import zstd, jsonl
from modules.utils.zipper import Booru, Scores
from modules.config import get_config
config = get_config()

def SaveGenLog(event: OnGenerationEndedEvent):
  root = config.db_dir
  genlog = os.path.join(root, "generation_records.jsonl")
  stats_dir = os.path.join(root, "tag_stats")
  os.makedirs(root, exist_ok=True)
  os.makedirs(stats_dir, exist_ok=True)
  
  # create entry
  ## v1
  endtypes = ["interrupt", "booru_interrupt", "complete"]
  rates = ["perfect", "ok", "bad", "worst", "undefined"]
  scripts = ["sdpem/lora", "sdpem/image", "sdpem/mlora", "sdpem/db", "webui", "webui/api", "other", "undefined"]
  
  try:
    entry = {
      "v1": int(time.time()),
      "itx": zstd.zip(event.infotxt),
      "et": endtypes.index(event.end_type),
      "r": rates.index(event.rate),
      "s": scripts.index(event.script),
    }
    
    if event.script.startswith("sdpem/"):
      entry["ps"] = Scores.compact(event.prompt_score)
      entry["pp"] = zstd.zip(json.dumps(event.pem_params, ensure_ascii=False))
      
      if event.booru_out:
        entry["b"] = Booru.compact(event.booru_out)
      
      if event.lost_tags:
        entry["lst"] = Scores.compact(event.lost_tags)
        entry["gst"] = Scores.compact(event.ghost_tags)
      
      if event.luuid:
        entry["u"] = event.luuid
        entry["ts"] = int(event.ts)
      
      if event.result_images:
        entry["img"] = event.result_images
    jsonl.append(entry, genlog) 
  except Exception as e:
    warn(f"[SaveGenLog] Unknown event type: {event.event_name}")
    traceback.print_exc()

onGenerationEnded.add_callback(SaveGenLog)