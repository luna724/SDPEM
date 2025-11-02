import json
import os
import os.path as op
import gradio as gr
import re 
from logger import warn, println

class BooruOptions:
    def resolve_directory(self):
        if self.booru_save_each_rate:
            os.makedirs(self.general_save_dir, exist_ok=True)
            os.makedirs(self.sensitive_save_dir, exist_ok=True)
            os.makedirs(self.explicit_save_dir, exist_ok=True)
            if not self.booru_merge_sensitive:
                os.makedirs(self.questionable_save_dir, exist_ok=True)
        if self.booru_save_blacklisted:
            os.makedirs(self.booru_blacklist_save_dir, exist_ok=True)
    
    def __init__(
        self,
        booru_threshold,
        booru_character_threshold,
        booru_allow_rating,
        booru_ignore_questionable,
        booru_save_each_rate,
        booru_merge_sensitive,
        general_save_dir,
        sensitive_save_dir,
        questionable_save_dir,
        explicit_save_dir,
        booru_save_blacklisted,
        booru_blacklist_save_dir,
        booru_blacklist
    ):
        self.booru_threshold = booru_threshold
        self.booru_character_threshold = booru_character_threshold
        self.booru_allow_rating = booru_allow_rating
        self.booru_ignore_questionable = booru_ignore_questionable
        self.booru_save_each_rate = booru_save_each_rate
        self.booru_merge_sensitive = booru_merge_sensitive
        self.general_save_dir = general_save_dir
        self.sensitive_save_dir = sensitive_save_dir
        self.questionable_save_dir = questionable_save_dir
        self.explicit_save_dir = explicit_save_dir
        self.booru_save_blacklisted = booru_save_blacklisted
        self.booru_blacklist_save_dir = booru_blacklist_save_dir
        self.booru_blacklist: list[re.Pattern] = booru_blacklist
        
        self.resolve_directory()
        
    def put(self, key, value):
        if key in self.__dict__:
            setattr(self, key, value)
        else: raise KeyError(f"BooruOptions has no attribute '{key}'")

class BooruFilterSettingManager:
    def __init__(self, name: str):
        ## cache ##
        self.blacklist_formatted: list[re.Pattern] = []
        self.blacklist_last_hash: str = None
        
        self.name = name
        self.setting = {}
        self.config_path = "./config/bf_settings"
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
            "filter_enable", "model", "threshold", "character_threshold", "allow_rating", "ignore_questionable", "save_each_rate", "merge_sensitive", "general_save_dir", "sensitive_save_dir", "questionable_save_dir", "explicit_save_dir", "blacklist", "pattern_blacklist", "save_blacklisted", "blacklist_save_dir"
        ]
        
        if len(options) != len(opts):
            raise ValueError(f"Expected {len(options)} options, but got {len(opts)} (Input: {opts})")

        self.setting.update({options[i]: v for i,v in enumerate(opts)})
        warn(f"[BooruFilter] Updated settings: {self.setting}")
        gr.Info(f"Booru Filter settings updated")
        
        self.save()
    
    def save(self):
        with open(op.join(self.config_path, self.name+".json"), "w", encoding="utf-8") as f:
            json.dump(self.setting, f, indent=2, ensure_ascii=False)
    
    def get(self, key, default=None):
        return self.setting.get(key, default)
    
    def calculate_blacklist_hash(self) -> str:
        blacklist = self.get("blacklist", "")
        black_patterns = self.get("pattern_blacklist", "")
        combined = blacklist + black_patterns
        return str(hash(str(combined)))
    
    def obtain_blacklist(self, no_patterns = False) -> list[re.Pattern]:
        if self.blacklist_last_hash == self.calculate_blacklist_hash():
            return self.blacklist_formatted
        
        l = [
                re.compile(rf"^\s*{re.escape(tag.strip())}\s*$", re.IGNORECASE)
                for tag in self.get("blacklist", "").split(",")
                if tag.strip() != ""
            ] + [
                re.compile(pattern, re.IGNORECASE)
                for pattern in self.get("pattern_blacklist", "").splitlines()
                if pattern.strip() != ""
        ]
        self.blacklist_last_hash = self.calculate_blacklist_hash()
        self.blacklist_formatted = l
        println(f"[Booru blacklist registered]: {len(self.blacklist_formatted)} patterns.")
        return l
    
    def into_options(self) -> BooruOptions:
        return BooruOptions(
            booru_threshold=self.get("threshold"),
            booru_character_threshold=self.get("character_threshold"),
            booru_allow_rating=self.get("allow_rating"),
            booru_ignore_questionable=self.get("ignore_questionable"),
            booru_save_each_rate=self.get("save_each_rate"),
            booru_merge_sensitive=self.get("merge_sensitive"),
            general_save_dir=self.get("general_save_dir"),
            sensitive_save_dir=self.get("sensitive_save_dir"),
            questionable_save_dir=self.get("questionable_save_dir"),
            explicit_save_dir=self.get("explicit_save_dir"),
            booru_save_blacklisted=self.get("save_blacklisted"),
            booru_blacklist_save_dir=self.get("blacklist_save_dir"),
            booru_blacklist=self.obtain_blacklist()
        )

booru_filter: BooruFilterSettingManager = BooruFilterSettingManager.from_dict("main")