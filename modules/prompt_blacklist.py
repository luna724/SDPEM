"""
```json
{
  "name($以外入る)": {
    "name": "name($以外入る)",
    "description": "comment",
    "enabled": bool,
    "version": 2.0,
    "data": {
      "target": {"tags": [str], "pattern": [str], "flags": ["IGNORECASE"], patternDefault: "{TAG}"},
      "rule_type": Literal["has", "not_has", "never" "allowlist", 
      "conditions" Optional{"tags": [str], pattern: [str], flags: [IGNORECASE], patternDefault: "{TAG}", atLeast: int=1, refill_placeholder: bool=False},
    }
  },
  "$neverRule": {
    enabled: bool,
    tags: [str], pattern[str], patternDefault: "{TAG}", flags: [IGNORECASE], 
}
```
"""

class PromptBlacklist:
    def __init__(self, opt: dict):
        pass