import os, re
from typing import Literal, Optional
from logger import println, critical, debug
from pathlib import Path
import json 
from modules.utils.prompt import disweight

def _example():
    # pattern
    pattern_example = { # matchTo に atLeast個マッチしたらプロンプトは key に置き換えられる
        "name": "Example Pattern",
        "description": "An example pattern placeholder",
        "version": 1.0,
        "mode": "pattern",
        "data": {
            "version": 1.0,
            "key": "$EXAMPLE",
            "matchTo": ["example", "sample"],
            "if": { # if の中ではデフォルト値が使用される
                "atLeast": 1,
                "patternTemplate": "^\s*{MATCH}\s*$",
                "escape": False, # re.escape(MATCH)
                "flags": ["IGNORECASE"], # getattr(re, flag)
                "replace": True, # replace False means do nothing
            }
        }
    }
    
    # replaceRule
    replace_rule_example = {
        "name": "Example Replace Rule",
        "description": "An example replace rule placeholder",
        "version": 1.0,
        "mode": "replaceRule",
        "data": {
            "version": 1.0,
            "key": "$REPLACE_EXAMPLE",
            "rules": [
                {
                    "mode": "simple",
                    "matches": ["^some$", "^words$"],
                    "replaceInto": "new words",
                    "is_remove": False,
                },
                {
                    "mode": "if_has",
                    "matches": [
                        {
                            "conditions": "Regex",
                            "built_pattern": "^{MATCH}$",
                            "pattern": [],
                            "flags": ["IGNORECASE"],
                            "escape": False,
                        },
                    ],
                    "atLeast": 1,
                    "replaceInto": "new words",
                    "allow_dupe": False,
                    "is_remove": False,
                },
                {
                    "mode": "script",
                    "__": "configでALLOW_EXTERNAL_SCRIPTがTrueの場合のみ有効",
                    "use": "script", # or "script_file"
                    "script": "def do(text: str) -> str:\n    return text*4 if len(text) < 5 else text",
                    "script_file": "./userconf/scripts/sample.py",
                },
            ]
        }
    }

class PromptReplaceRule: # TODO
    @staticmethod
    def defaults() -> dict:
        return {
            "name": "_DEFAULT",
            "description": "",
            "version": 1.0,
            "mode": "replaceRule",
            "data": {
                "version": 1.0,
                "key": "",
                "rules": [],
            }
        }

class PromptPlaceholder: # pattern mode
    @staticmethod
    def default_if() -> dict:
        return {
            "atLeast": 1, # matchTo がいくつマッチすればそれを置き換えるか
            "patternTemplate": r"^\s*{MATCH}\s*$",
            "escape": False, # re.escape(MATCH)
            "flags": ["IGNORECASE"], # getattr(re, flag)
            "replace": True, # replace False means do nothing
        }
    
    @staticmethod
    def defaults() -> dict:
        return {
            "name": "_DEFAULT",
            "description": "",
            "version": 1.0,
            "data": {
                "version": 1.0,
                "key": "",
                "matchTo": [],
                "if": {},
            }
        }
    
    LATEST = 1.0
    def __init__(self, opt: dict):
        self.opt = opt
        
        self.name = opt["name"]
        self.description = opt.get("description", "")
        self.version = opt["version"]
        
        self.data = opt["data"]
        self.should_process: list[re.Pattern] = []
        
        # TODO: PromptPlaceholder script mode!?
        self._func_pairs = { # 呼び出されてほしくないものは登録しない
            "get_default_if": (self.default_if, False),
            "get_default": (self.defaults, False),
            # "remove_rule": (self.remove_rule, True),
            "prepare_rule": (self.apply_pattern, True),
            "trigger": (self.trig, True),
        }
        
        self.d_ver = self.data["version"]
        self.rprTo = self.data["key"]
        self.matchTo = self.data["matchTo"]
        self.if_opt = self.default_if() | self.data.get("if", {})
        
        self.pattern_template = self.if_opt["patternTemplate"]
        self.at_least = self.if_opt["atLeast"]
        self.escape = self.if_opt["escape"]
        self.flags = self.if_opt["flags"]
        
    async def apply_pattern(self):
        flag = 0
        for f in self.flags:
            if hasattr(re, f):
                flag |= getattr(re, f)
                debug(f"[PromptPlaceholder] Applied flag {f}")
        
        for m in self.matchTo:
            m = re.escape(m) if self.escape else m
            pattern = self.pattern_template.format(MATCH=f"({m})")
            debug(f"[PromptPlaceholder] Applied pattern: {pattern}")
            
            self.should_process.append(
                re.compile(
                    pattern,
                    flags=flag
                )
            )

    async def trig(self, piece: str, trigger_word: str, ) -> str:
        if self.if_opt["replace"]:
            debug(f"[PromptPlaceholder] Replacing '{trigger_word}' with '{self.rprTo}'")
            piece = piece.replace(trigger_word, self.rprTo, 1)
        return piece
    
    async def process_prompt(self, prompt: list[str]) -> list[str]:
        processed = []
        matched = 0
        for piece in prompt:
            disweigted = disweight(piece)[0]
            debug(f"[PromptPlaceholder] Checking '{piece}' ({disweigted})")
            for pattern in self.should_process:
                match = pattern.search(disweigted)
                if match:
                    debug(f"[PromptPlaceholder] Matched pattern: {pattern.pattern}")
                    matched += 1
                if matched >= self.at_least:
                    piece = await self.trig(
                        piece, 
                        match.group(1)
                    )
                    matched = 0
                    break
            processed.append(piece)

        return processed

class PromptPlaceholderManager:
    def __init__(self):
        self.placeholders = {}
        self.config_path = Path("./config/prompt_placeholder.json")
        self.config_default = Path("./defaults/DEF/!prompt_placeholder.json")

        try:
            self.load()
        except:
            critical("[PromptPlaceholderManager] Failed to load prompt placeholders.")
            raise

    def init(self):
        self.placeholders = json.loads(
            self.config_default.open("r", encoding="utf-8").read()
        )

    def load(self):
        if not self.config_path.exists(): 
            self.init()
            self.save()
        self.placeholders = json.loads(self.config_path.open("r", encoding="utf-8").read())
        
    def save(self):
        self.config_path.open("w", encoding="utf-8").write(json.dumps(self.placeholders, ensure_ascii=False,indent=2))
    
    def get(self, name: str) -> Optional[dict]:
        return self.placeholders.get(name, None)
    
    def push(self, name, data: dict) -> bool:
        if name in self.placeholders:
            println(f"[PromptPlaceholderManager] Placeholder with name '{name}' already exists.")
            return False
        self.placeholders[name] = data
        self.save()
        debug(f"[PromptPlaceholderManager] Added new placeholder {name}: {data}")
        return True
    
    def update(self, n: str, data: dict):
        self.placeholders[n] = data
        self.save()
        debug(f"[PromptPlaceholderManager] Updated placeholder {n}: {data}")
        
    def delete(self, n: str):
        if n in self.placeholders:
            bp = self.placeholders.pop(n)
            println(f"[PromptPlaceholderManager] Deleted placeholder (backup: {bp})")
            self.save()
            debug(f"[PromptPlaceholderManager] Deleted placeholder index {n}")
        return
    
    def runner(self, n: str) -> PromptPlaceholder:
        return PromptPlaceholder(self.get(n))
    
    def runners(self) -> list[PromptPlaceholder]:
        return [PromptPlaceholder(p) for p in self.placeholders.values()]

    async def process_prompt(self, prompt: list[str]) -> list[str]:
        for p in self.runners():
            await p.apply_pattern() # TODO: cache?
            prompt = await p.process_prompt(prompt)
        return prompt
    
    def all_names(self) -> list[str]:
        return list(self.placeholders.keys())

placeholder = PromptPlaceholderManager()