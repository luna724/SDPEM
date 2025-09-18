import json
import gradio as gr
import re
from logger import warn
import os.path as op
import os

class PromptSetting:
    def __init__(self, **values):
        self.values = values
    @classmethod
    def from_dict(cls, data):
        return cls(**data)
    
    def __getattr__(self, name):
        try:
            return self.values[name]
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        
    def get(self, key, default=None):
        return self.values.get(key, default)

class PromptSettingManager:
    def __init__(self, name: str):
        # initialize regular attributes without touching settings
        self.name = name
        self.setting = {}
        self.config_path = "./config/prompt_settings"
        os.makedirs(self.config_path, exist_ok=True)
        
    @classmethod
    def from_dict(cls, name: str,):
        i = cls(name)
        if op.exists(op.join(i.config_path, name+".json")):
            with open(op.join(i.config_path, name+".json"), "r", encoding="utf-8") as f:
                i.setting = json.load(f)
        return i
    
    async def push_ui(self, *opts):
        options = [
            "blacklist", "black_patterns", "disallow_duplicate", "blacklisted_weight",  "use_relative_freq", "w_min", "w_max", "w_multiplier"
        ]
        
        if len(options) != len(opts):
            raise ValueError(f"Expected {len(options)} options, but got {len(opts)} (Input: {opts})")

        self.setting.update({options[i]: v for i,v in enumerate(opts)})
        warn(f"[PromptSetting] Updated settings: {self.setting}")
        gr.Info(f"Prompt settings updated")
        
        self.save()
    
    def save(self):
        with open(op.join(self.config_path, self.name+".json"), "w", encoding="utf-8") as f:
            json.dump(self.setting, f, indent=2, ensure_ascii=False)
    
    def get(self, key, default=None):
        return self.setting.get(key, default)
    
    def obtain_blacklist(self, no_patterns = False) -> list[re.Pattern]:
        if no_patterns:
            return [
                rf"^\s*{re.escape(tag.strip())}\s*$"
                for tag in self.get("blacklist", "").split(",")
                if tag.strip() != ""
            ] + self.get("black_patterns", "").splitlines()
        return [
            re.compile(rf"^\s*{re.escape(tag.strip())}\s*$", re.IGNORECASE)
            for tag in self.get("blacklist", "").split(",")
            if tag.strip() != ""
        ] + [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.get("black_patterns", "").splitlines()
            if pattern.strip() != ""
        ]
    
    async def setup(self) -> PromptSetting:
        opt = self.setting.copy()
        blacklist = opt.get("blacklist", "")
        black_pattern = opt.get("black_patterns", "")
        
        opt["blacklist"] = blacklist.split(",")
        opt["black_patterns"] = black_pattern.splitlines()
        opt["blacklist_formatted"] = self.obtain_blacklist()
    
    def request_param(self, **kw) -> dict:
        to_return = {
            "blacklist": self.obtain_blacklist(no_patterns=True),
            "blacklisted_weight": self.get("blacklisted_weight", 0),
            "disallow_duplicate": self.get("disallow_duplicate", False),
            "use_relative_freq": self.get("use_relative_freq", True),
            "weight_multiplier_target": [
                self.get("w_min", 1),
                self.get("w_max", 12),
            ],
            "weight_multiplier": self.get("w_multiplier", 1)
        }
        return to_return
        
setting: PromptSettingManager = PromptSettingManager.from_dict("main")
