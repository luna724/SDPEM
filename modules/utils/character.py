# https://github.com/lanner0403/WAI-NSFW-illustrious-character-select-EN
import json
import os

from modules.utils.prompt import Prompt
from modules.utils.lora_util import is_lora_trigger

from logger import println, debug
try:
    from logger import debug as _logger_debug, critical as _logger_critical  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    _logger_debug = None
    _logger_critical = None

import logging

_fallback_logger = logging.getLogger("WAICharacters")
if not _fallback_logger.handlers:
    _fallback_logger.addHandler(logging.NullHandler())


def log_debug(message: str) -> None:
    if _logger_debug is not None:
        try:
            _logger_debug(message)
            return
        except AttributeError:
            pass
    _fallback_logger.debug(message)


def log_critical(message: str) -> None:
    if _logger_critical is not None:
        try:
            _logger_critical(message)
            return
        except AttributeError:
            pass
    _fallback_logger.critical(message)


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
            println(f"[WAICharacters] Loaded {len(self.characters)} characters")
        else:
            log_critical(f"Character data file not found at {self.path}")
            self.warn = True
    
    async def remove_character(self, prompt: Prompt) -> Prompt:
        # print("Removing character prompts...")
        if self.warn:
            log_critical("Character data not loaded. Cannot remove characters.")
            return prompt
        
        for p in list(prompt):
            if is_lora_trigger(p):
                log_debug(f"[WAICharacters] Skipping LoRA trigger tag: {p.value}")
                continue
            tag = (p.text or "").strip().lower()
            # log_debug(f"[WAICharacters] Checking tag: {p.value} -> {tag}")
            if tag and tag in self.characters:
                log_debug(f"[WAICharacters] Removed character tag: {p.value}")
                prompt.remove(p)
        return prompt
    

waic = WAICharacters()
