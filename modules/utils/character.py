# https://github.com/lanner0403/WAI-NSFW-illustrious-character-select-EN
import json
import os

from modules.utils.prompt import Prompt
from modules.utils.lora_util import is_lora_trigger

from logger import println, debug, critical

class WAICharacters:
    def __init__(self):
        self.data = []
        self.characters: set[str] = set()
        self.path = "./models/characters.json"
        self.warn = False
        
        self.load()
        
    def load(self):
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
                # Normalize character tokens to lower-case, trimmed entries
                characters: set[str] = set()
                for c in self.data.get("proj", []):
                    for t in c.get("title", "").split(","):
                        norm = t.strip().lower()
                        if norm:
                            characters.add(norm)
                self.characters = characters
            println(f"[WAICharacters] Loaded {len(self.characters)} character identifies")
        else:
            critical(f"Character data file not found at {self.path}")
            self.warn = True
    
    async def remove_character(self, prompt: Prompt) -> Prompt:
        # print("Removing character prompts...")
        if self.warn:
            critical("Character data not loaded. Cannot remove characters.")
            return prompt
        
        for p in list(prompt):
            if is_lora_trigger(p):
                debug(f"[WAICharacters] Skipping LoRA trigger tag: {p.value}")
                continue
            tag = (p.text or "").strip().lower()
            # debug(f"[WAICharacters] Checking tag: {p.value} -> {tag}")
            if tag and tag in self.characters:
                debug(f"[WAICharacters] Removed character tag: {p.value}")
                prompt.remove(p)
        return prompt
    

waic = WAICharacters()
