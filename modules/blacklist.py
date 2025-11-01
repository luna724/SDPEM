import os
import re
import json
from typing import Literal, Optional
from logger import println, critical, debug
from pathlib import Path
from modules.utils.prompt import Prompt, PromptPiece

# Import is_lora_trigger lazily to avoid circular imports
_is_lora_trigger = None

def _get_is_lora_trigger():
    global _is_lora_trigger
    if _is_lora_trigger is None:
        from modules.utils.lora_util import is_lora_trigger
        _is_lora_trigger = is_lora_trigger
    return _is_lora_trigger


class BlacklistFilterRule:
    """
    Represents a single blacklist filter rule that determines when a blacklisted tag should NOT be filtered.
    
    Rule types:
    1. "has" - Don't filter the target if specified tags are present in the prompt
    2. "not_has" - Don't filter the target if specified tags are NOT present in the prompt
    """
    
    @staticmethod
    def defaults() -> dict:
        return {
            "name": "_DEFAULT",
            "description": "",
            "enabled": True,
            "version": 1.0,
            "data": {
                "version": 1.0,
                "target": "",  # The blacklisted tag this rule applies to
                "rule_type": "not_has",  # "has" or "not_has"
                "conditions": [],  # List of tags/patterns to check
                "is_pattern": False,  # Whether conditions should be treated as regex patterns
                "flags": ["IGNORECASE"],  # Regex flags if is_pattern is True
            }
        }
    
    LATEST = 1.0
    
    def __init__(self, opt: dict):
        self.opt = opt
        
        self.name = opt["name"]
        self.description = opt.get("description", "")
        self.enabled = opt.get("enabled", True)
        self.version = opt["version"]
        
        self.data = opt["data"]
        self.d_ver = self.data.get("version", 1.0)
        
        self.target = self.data["target"]
        self.rule_type: Literal["has", "not_has"] = self.data.get("rule_type", "not_has")
        self.conditions = self.data.get("conditions", [])
        self.is_pattern = self.data.get("is_pattern", False)
        self.flags = self.data.get("flags", ["IGNORECASE"])
        
        self.compiled_target: Optional[re.Pattern] = None
        self.compiled_conditions: list[re.Pattern] = []
        self.initialized = False
    
    async def prepare_rule(self):
        """Compile regex patterns for target and conditions"""
        # Compile target pattern
        flag = 0
        for f in self.flags:
            if hasattr(re, f):
                flag |= getattr(re, f)
        
        # Compile the target pattern (what to match in blacklist)
        target_pattern = self.target if self.is_pattern else re.escape(self.target)
        self.compiled_target = re.compile(rf"^\s*{target_pattern}\s*$", flag)
        debug(f"[BlacklistFilterRule] Compiled target pattern: {self.compiled_target.pattern}")
        
        # Compile condition patterns
        for condition in self.conditions:
            cond_pattern = condition if self.is_pattern else re.escape(condition)
            compiled = re.compile(rf"^\s*{cond_pattern}\s*$", flag)
            self.compiled_conditions.append(compiled)
            debug(f"[BlacklistFilterRule] Compiled condition pattern: {compiled.pattern}")
        
        self.initialized = True
    
    def matches_target(self, tag: str) -> bool:
        """Check if a tag matches this rule's target"""
        if not self.initialized or not self.compiled_target:
            return False
        return bool(self.compiled_target.search(tag))
    
    def should_keep(self, prompt: Prompt) -> bool:
        """
        Determine if the target should be kept based on the rule.
        
        Returns True if the tag should NOT be filtered (should be kept).
        """
        if not self.enabled or not self.initialized:
            return False
        
        # Track which specific conditions are matched in the prompt
        matched_conditions = set()
        for piece in prompt:
            target_text = piece.text
            for idx, cond_pattern in enumerate(self.compiled_conditions):
                if cond_pattern.search(target_text):
                    matched_conditions.add(idx)
        
        if self.rule_type == "has":
            # Keep the target if ALL conditions are present
            return len(matched_conditions) == len(self.conditions) and len(self.conditions) > 0
        elif self.rule_type == "not_has":
            # Keep the target if NONE of the conditions are present
            return len(matched_conditions) == 0 and len(self.conditions) > 0
        
        return False


class BlacklistFilterRuleManager:
    """
    Manages blacklist filter rules, similar to PromptPlaceholderManager.
    """
    
    def __init__(self):
        self.rules = {}
        self.config_path = Path("./config/blacklist_filter_rules.json")
        self.config_default = Path("./defaults/DEF/!blacklist_filter_rules.json")
        self.scripts: list[BlacklistFilterRule] = []
        self.initialized = False
        
        try:
            self.load()
        except Exception:
            critical("[BlacklistFilterRuleManager] Failed to load blacklist filter rules.")
            raise
    
    async def init(self):
        """Initialize and prepare all rules"""
        self.scripts = await self.runners()
        self.initialized = True
    
    async def reload(self):
        """Reload all rules"""
        return await self.init()
    
    def load(self):
        """Load rules from configuration file"""
        if not self.config_path.exists():
            if self.config_default.exists():
                self.rules = json.loads(
                    self.config_default.open("r", encoding="utf-8").read()
                )
            else:
                self.rules = {}
            self.save()
        else:
            self.rules = json.loads(self.config_path.open("r", encoding="utf-8").read())
    
    def save(self):
        """Save rules to configuration file"""
        os.makedirs(self.config_path.parent, exist_ok=True)
        self.config_path.open("w", encoding="utf-8").write(
            json.dumps(self.rules, ensure_ascii=False, indent=2)
        )
    
    def get(self, name: str) -> Optional[dict]:
        """Get a rule by name"""
        return self.rules.get(name, None)
    
    def push(self, name: str, data: dict) -> bool:
        """Add a new rule"""
        if name in self.rules:
            println(f"[BlacklistFilterRuleManager] Rule with name '{name}' already exists.")
            return False
        self.rules[name] = data
        self.save()
        debug(f"[BlacklistFilterRuleManager] Added new rule {name}: {data}")
        return True
    
    def update(self, name: str, data: dict):
        """Update an existing rule"""
        self.rules[name] = data
        self.save()
        debug(f"[BlacklistFilterRuleManager] Updated rule {name}: {data}")
    
    def delete(self, name: str):
        """Delete a rule"""
        if name in self.rules:
            bp = self.rules.pop(name)
            println(f"[BlacklistFilterRuleManager] Deleted rule (backup: {bp})")
            self.save()
            debug(f"[BlacklistFilterRuleManager] Deleted rule {name}")
    
    async def runner(self, name: str) -> BlacklistFilterRule:
        """Create and prepare a single rule"""
        data = self.get(name)
        if not data:
            raise ValueError(f"Rule '{name}' not found")
        rule = BlacklistFilterRule(data)
        await rule.prepare_rule()
        return rule
    
    async def runners(self) -> list[BlacklistFilterRule]:
        """Create and prepare all rules"""
        return [await self.runner(name) for name in self.rules.keys()]
    
    async def apply_filter_rules(self, prompt: Prompt, blacklist_patterns: list[re.Pattern]) -> dict[int, bool]:
        """
        Apply filter rules to determine which pieces should be kept.
        
        Returns a keep_map dictionary mapping piece IDs to whether they should be kept.
        """
        if not self.initialized:
            await self.init()
        
        keep_map: dict[int, bool] = {}
        is_lora_trigger = _get_is_lora_trigger()
        
        for piece in list(prompt):
            # Skip LoRA trigger tags - they should always be kept
            if is_lora_trigger(piece):
                keep_map[id(piece)] = True
                continue
            
            disweighted = piece.text
            matched_blacklist = False
            
            # Check if this piece matches any blacklist pattern
            for pattern in blacklist_patterns:
                if pattern.search(disweighted):
                    matched_blacklist = True
                    break
            
            if not matched_blacklist:
                # Not in blacklist, keep it
                keep_map[id(piece)] = True
                continue
            
            # Check if any filter rule applies to this blacklisted tag
            should_keep = False
            for rule in self.scripts:
                if rule.matches_target(disweighted):
                    if rule.should_keep(prompt):
                        debug(f"[BlacklistFilterRule] Rule '{rule.name}' keeps tag: {piece.value}")
                        should_keep = True
                        break
            
            keep_map[id(piece)] = should_keep
        
        return keep_map
    
    def all_names(self) -> list[str]:
        """Get all rule names"""
        return list(self.rules.keys())


# Global instance
blacklist_filter_rules = BlacklistFilterRuleManager()