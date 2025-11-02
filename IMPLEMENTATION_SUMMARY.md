# Blacklist Filter Rules - Implementation Summary

## Overview
This PR implements a conditional blacklist filtering feature as requested in the issue. The feature allows certain tags to be excluded from the blacklist under specific conditions based on the presence or absence of other tags in the prompt.

## Files Changed

### New Files
1. **modules/blacklist.py** (266 lines)
   - BlacklistFilterRule class: Represents individual filter rules
   - BlacklistFilterRuleManager class: Manages all filter rules
   - Similar structure to prompt_placeholder.py for consistency

2. **defaults/DEF/!blacklist_filter_rules.json**
   - Default configuration with example rules
   - Includes examples for both "has" and "not_has" rule types

3. **docs/blacklist_filter_rules.md** (167 lines)
   - Comprehensive Japanese documentation
   - Usage examples, configuration guide, and implementation details

4. **Test Files**
   - test_blacklist_minimal.py (276 lines): Unit tests without dependencies
   - test_blacklist_filter.py (241 lines): Full integration tests
   - verify_blacklist_integration.py (137 lines): Manual verification script

### Modified Files
1. **modules/prompt_processor.py**
   - Added import for blacklist_filter_rules
   - Modified proc_blacklist() to be async and use filter rules
   - Updated process() to await proc_blacklist()

## Key Features

### Rule Types
1. **"not_has"**: Keep target tag if specified conditions are NOT present
2. **"has"**: Keep target tag if specified conditions ARE present

### Support
- Multiple conditions per rule
- Pattern matching with regex
- Case-insensitive matching (configurable)
- LoRA trigger tag preservation

## Example from Issue

### Setup
- Blacklist: `blindfold`
- Rule: Keep `blindfold` if `looking at viewer` is NOT present (not_has)

### Results
- Input: `blindfold, looking at viewer, open eyes`
  - Output: `looking at viewer, open eyes` ✓
  
- Input: `blindfold, open eyes, open mouth`
  - Output: `blindfold, open eyes, open mouth` ✓

## Testing

### Test Results
- ✅ All unit tests passing (test_blacklist_minimal.py)
- ✅ Integration verification passing (verify_blacklist_integration.py)
- ✅ CodeQL security scan: 0 alerts
- ✅ Code review feedback addressed

### Test Coverage
- Basic rule logic (has/not_has)
- Pattern matching
- Case insensitivity
- Multiple condition handling
- Target matching accuracy
- Configuration loading/saving

## Architecture

### Design Decisions
1. **Similar to prompt_placeholder.py**: Maintains consistency with existing codebase
2. **Lazy import**: Avoids circular dependency with lora_util
3. **Set-based matching**: Tracks which specific conditions are matched for accuracy
4. **Async integration**: Seamlessly integrates with existing async processing

### Configuration Flow
```
defaults/DEF/!blacklist_filter_rules.json (default)
    ↓ (auto-copied on first run)
config/blacklist_filter_rules.json (user config)
    ↓ (loaded by)
BlacklistFilterRuleManager
    ↓ (used by)
PromptProcessor.proc_blacklist()
```

## Usage

### Add a Rule Programmatically
```python
from modules.blacklist import blacklist_filter_rules

rule_data = {
    "name": "my_rule",
    "description": "Description",
    "enabled": True,
    "version": 1.0,
    "data": {
        "version": 1.0,
        "target": "target_tag",
        "rule_type": "not_has",
        "conditions": ["condition1", "condition2"],
        "is_pattern": False,
        "flags": ["IGNORECASE"],
    }
}

blacklist_filter_rules.push("my_rule", rule_data)
await blacklist_filter_rules.reload()
```

### Edit Configuration File
Edit `config/blacklist_filter_rules.json` and reload the application.

## Security

- CodeQL scan: 0 alerts
- No external code execution
- Regex patterns are compiled safely
- Configuration file paths are validated

## Performance Considerations

- Rules are compiled once and cached
- Set-based condition matching is O(n×m) where n=prompt pieces, m=conditions
- Lazy initialization avoids startup overhead

## Future Enhancements (Not in Scope)

- UI for rule management (mentioned in issue but not required for this PR)
- Rule priority/ordering when multiple rules match
- More complex condition logic (AND/OR combinations)
- Condition negation within rules

## Compatibility

- No breaking changes to existing functionality
- Existing blacklist behavior preserved when no rules are defined
- LoRA trigger tags always preserved
- Works with existing prompt_processor flow

## Documentation

See `docs/blacklist_filter_rules.md` for:
- Complete feature documentation (Japanese)
- Configuration examples
- Usage patterns
- Implementation details
