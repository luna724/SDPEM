"""
Final validation test - Tests the exact scenario from the issue
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock dependencies
class MockLogger:
    @staticmethod
    def setup_logger(name, level): pass
    @staticmethod
    def debug(msg): pass
    @staticmethod
    def println(msg): print(msg)
    @staticmethod
    def critical(msg): print(f"[CRITICAL] {msg}")
    @staticmethod
    def warn(msg): print(f"[WARN] {msg}")

sys.modules['logger'] = MockLogger()

# Mock is_lora_trigger before importing blacklist
def mock_is_lora_trigger(tag):
    """Mock function that always returns False (no LoRA triggers in our tests)"""
    return False

# Patch the lazy loader
import modules.blacklist as blacklist_module
original_get_is_lora_trigger = blacklist_module._get_is_lora_trigger

def patched_get_is_lora_trigger():
    return mock_is_lora_trigger

blacklist_module._get_is_lora_trigger = patched_get_is_lora_trigger

from modules.utils.prompt import Prompt
from modules.blacklist import blacklist_filter_rules
import re


async def test_issue_example():
    """
    Test the exact example from the issue:
    
    Filter target: blindfold
    Rule: not_has "looking at viewer"
    
    Input 1: blindfold, looking at viewer, open eyes
    Expected Output 1: looking at viewer, open eyes
    
    Input 2: blindfold, open eyes, open mouth
    Expected Output 2: blindfold, open eyes, open mouth
    """
    
    print("\n" + "="*70)
    print("FINAL VALIDATION - Issue Example Test")
    print("="*70)
    
    # Setup rule
    rule_data = {
        "name": "issue_example_rule",
        "description": "Example from the issue",
        "enabled": True,
        "version": 1.0,
        "data": {
            "version": 1.0,
            "target": "blindfold",
            "rule_type": "not_has",
            "conditions": ["looking at viewer"],
            "is_pattern": False,
            "flags": ["IGNORECASE"],
        }
    }
    
    # Add rule
    if "issue_example_rule" not in blacklist_filter_rules.rules:
        blacklist_filter_rules.push("issue_example_rule", rule_data)
    else:
        blacklist_filter_rules.update("issue_example_rule", rule_data)
    
    await blacklist_filter_rules.reload()
    
    # Setup blacklist pattern
    blacklist_patterns = [
        re.compile(r"^\s*blindfold\s*$", re.IGNORECASE)
    ]
    
    print("\nSetup:")
    print("  - Blacklist: blindfold")
    print("  - Rule: Keep 'blindfold' if 'looking at viewer' is NOT present")
    
    # Test Case 1
    print("\n" + "-"*70)
    print("Test Case 1:")
    input1 = "blindfold, looking at viewer, open eyes"
    prompt1 = Prompt(input1)
    keep_map1 = await blacklist_filter_rules.apply_filter_rules(prompt1, blacklist_patterns)
    
    # Apply the keep_map to get the result
    result1 = [str(piece) for piece in prompt1 if keep_map1.get(id(piece), True)]
    
    print(f"  Input:    {input1}")
    print(f"  Output:   {', '.join(result1)}")
    print(f"  Expected: looking at viewer, open eyes")
    
    assert "blindfold" not in result1, "blindfold should be filtered"
    assert "looking at viewer" in result1, "looking at viewer should be kept"
    assert "open eyes" in result1, "open eyes should be kept"
    print("  ✅ PASS")
    
    # Test Case 2
    print("\n" + "-"*70)
    print("Test Case 2:")
    input2 = "blindfold, open eyes, open mouth"
    prompt2 = Prompt(input2)
    keep_map2 = await blacklist_filter_rules.apply_filter_rules(prompt2, blacklist_patterns)
    
    # Apply the keep_map to get the result
    result2 = [str(piece) for piece in prompt2 if keep_map2.get(id(piece), True)]
    
    print(f"  Input:    {input2}")
    print(f"  Output:   {', '.join(result2)}")
    print(f"  Expected: blindfold, open eyes, open mouth")
    
    assert "blindfold" in result2, "blindfold should be kept (rule applies)"
    assert "open eyes" in result2, "open eyes should be kept"
    assert "open mouth" in result2, "open mouth should be kept"
    print("  ✅ PASS")
    
    # Cleanup
    blacklist_filter_rules.delete("issue_example_rule")
    
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED - Issue requirements verified!")
    print("="*70 + "\n")
    
    return True


async def test_additional_scenarios():
    """Test additional edge cases"""
    print("\n" + "="*70)
    print("ADDITIONAL SCENARIO TESTS")
    print("="*70)
    
    # Setup rule
    rule_data = {
        "name": "test_rule",
        "description": "Test rule",
        "enabled": True,
        "version": 1.0,
        "data": {
            "version": 1.0,
            "target": "weapon",
            "rule_type": "not_has",
            "conditions": ["sword"],
            "is_pattern": False,
            "flags": ["IGNORECASE"],
        }
    }
    
    blacklist_filter_rules.push("test_rule", rule_data)
    await blacklist_filter_rules.reload()
    
    blacklist_patterns = [re.compile(r"^\s*weapon\s*$", re.IGNORECASE)]
    
    # Scenario 1: Tag not in blacklist
    print("\nScenario 1: Tag not in blacklist")
    prompt = Prompt("gun, sword, battle")
    keep_map = await blacklist_filter_rules.apply_filter_rules(prompt, blacklist_patterns)
    result = [str(p) for p in prompt if keep_map.get(id(p), True)]
    
    print(f"  Input:  gun, sword, battle")
    print(f"  Output: {', '.join(result)}")
    assert all(tag in result for tag in ["gun", "sword", "battle"]), "All non-blacklisted tags kept"
    print("  ✅ PASS")
    
    # Scenario 2: Empty prompt
    print("\nScenario 2: Single tag that matches rule")
    prompt = Prompt("weapon, gun")
    keep_map = await blacklist_filter_rules.apply_filter_rules(prompt, blacklist_patterns)
    result = [str(p) for p in prompt if keep_map.get(id(p), True)]
    
    print(f"  Input:  weapon, gun")
    print(f"  Output: {', '.join(result)}")
    assert "weapon" in result, "weapon should be kept (no sword)"
    print("  ✅ PASS")
    
    # Cleanup
    blacklist_filter_rules.delete("test_rule")
    
    print("\n✅ Additional scenarios passed!\n")


async def main():
    try:
        await test_issue_example()
        await test_additional_scenarios()
        print("\n🎉 ALL VALIDATION TESTS PASSED! 🎉\n")
        return 0
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
