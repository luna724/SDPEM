import os, re
from typing import Literal, Optional
from logger import println, critical, debug
from pathlib import Path
import json 
from modules.utils.prompt import Prompt, PromptPiece

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
        self.initialized = False
        
        # TODO: PromptPlaceholder script mode!?
        self._func_pairs = { # 呼び出されてほしくないものは登録しない
            "get_default_if": (self.default_if, False),
            "get_default": (self.defaults, False),
            # "remove_rule": (self.remove_rule, True),
            "prepare_rule": (self.apply_pattern, True),
            "trigger": (self.trig, True),
        }
        
        self.rprTo = self.data["key"]
        self.matchTo = self.data["matchTo"]
        self.if_opt = self.default_if() | self.data.get("if", {})
        
        self.pattern_template = self.if_opt["patternTemplate"]
        self.at_least = self.if_opt["atLeast"]
        self.escape = self.if_opt["escape"]
        self.flags = self.if_opt["flags"]
        
        # v1.1
        self.refill_after = self.if_opt.get("refill_after_blacklist", False) #+
        self.d_ver = self.data.get("version", 1.0) #-
        
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
        self.initialized = True

    def _mark_refill_snapshot(self, piece: PromptPiece) -> None:
        entries: list[dict[str, str]] = piece.ensure_meta("placeholder_refill", [])
        label = f"placeholder:{self.name}:{id(piece)}:{len(entries)}"
        piece.snapshot(label)
        entries.append({
            "placeholder": self.name,
            "label": label,
            "key": self.rprTo,
        })
        piece.set_meta("placeholder_refill", entries)

    async def trig(self, piece: PromptPiece, trigger_word: str) -> PromptPiece:
        if self.if_opt["replace"] and trigger_word in piece.value:
            debug(f"[PromptPlaceholder] Replacing '{trigger_word}' with '{self.rprTo}'")
            piece.set(piece.value.replace(trigger_word, self.rprTo, 1), source=self.name)
        return piece
    
    async def process_prompt(self, prompt: Prompt) -> Prompt:
        matched = 0
        for piece in prompt:
            target_text = piece.text
            # debug(f"[PromptPlaceholder] Checking '{piece.value}' ({target_text})")
            for pattern in self.should_process:
                match = pattern.search(target_text)
                if not match:
                    continue
                debug(f"[PromptPlaceholder] Matched pattern: {pattern.pattern}")
                matched += 1
                if matched >= self.at_least:
                    if self.refill_after:
                        self._mark_refill_snapshot(piece)
                    await self.trig(piece, match.group(1))
                    matched = 0
                    break

        return prompt

class PromptPlaceholderManager:
    def __init__(self):
        self.placeholders = {}
        self.config_path = Path("./config/prompt_placeholder.json")
        self.config_default = Path("./defaults/DEF/!prompt_placeholder.json")
        self.scripts: list[PromptPlaceholder] = []
        self.initialized = False

        try:
            self.load()
        except:
            critical("[PromptPlaceholderManager] Failed to load prompt placeholders.")
            raise

    async def init(self):
        self.scripts = await self.runners()
        self.initialized = True
    async def reload(self): return await self.init()

    def load(self):
        if not self.config_path.exists(): 
            self.placeholders = json.loads(
                self.config_default.open("r", encoding="utf-8").read()
            )
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
    
    async def runner(self, n: str) -> PromptPlaceholder:
        data = self.get(n)
        if not data:
            raise ValueError(f"Placeholder '{n}' not found")
        d = PromptPlaceholder(data)
        await d.apply_pattern()
        return d

    async def runners(self) -> list[PromptPlaceholder]:
        return [await self.runner(p) for p in self.placeholders.keys()]

    def _coerce_prompt(self, prompt) -> tuple[Prompt, str]:
        if isinstance(prompt, Prompt):
            return prompt, "prompt"
        if isinstance(prompt, str):
            return Prompt(prompt), "string"
        if isinstance(prompt, (list, tuple)):
            return Prompt(list(prompt)), "list"
        raise TypeError("prompt must be str, list, tuple, or Prompt instance")

    async def process_prompt(self, prompt) -> Prompt | list[str] | str:
        if not self.initialized:
            await self.init()
        prompt_obj, mode = self._coerce_prompt(prompt)
        for p in self.scripts:
            if not p.initialized:
                await p.apply_pattern() # TODO: cache?
            prompt_obj = await p.process_prompt(prompt_obj)

        if mode == "prompt":
            return prompt_obj
        if mode == "string":
            return prompt_obj.combine()
        return prompt_obj.as_list()
    
    def all_names(self) -> list[str]:
        return list(self.placeholders.keys())

placeholder = PromptPlaceholderManager()