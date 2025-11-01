"""
Test for blacklist filter rules feature
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logger
import logging
logger.setup_logger("TEST", logging.DEBUG)

from modules.blacklist import blacklist_filter_rules, BlacklistFilterRule
from modules.prompt_processor import PromptProcessor
from modules.prompt_setting import setting
from modules.utils.prompt import Prompt


async def test_example_from_issue():
    """
    Test the example from the issue:
    
    Filter target: blindfold | Rule: [1]-2 looking at viewer
    Input: blindfold, looking at viewer, open eyes -> looking at viewer, open eyes 
           ([1]-2 looking at viewerが含まれているため)
    Input: blindfold, open eyes, open mouth -> blindfold, open eyes, open mouth 
           (looking at viewerが含まれていないためフィルタせず残す)
    """
    print("\n=== Test: Example from Issue ===")
    
    # Setup: Add blindfold to blacklist
    original_blacklist = setting.get("blacklist", "")
    if "blindfold" not in original_blacklist:
        new_blacklist = original_blacklist + ",blindfold" if original_blacklist else "blindfold"
        setting.setting["blacklist"] = new_blacklist
        setting.save()
    
    # Create a filter rule for blindfold
    rule_data = {
        "name": "blindfold_rule",
        "description": "Don't filter blindfold if 'looking at viewer' is NOT present",
        "enabled": True,
        "version": 1.0,
        "data": {
            "version": 1.0,
            "target": "blindfold",
            "rule_type": "not_has",  # Don't filter if conditions are NOT present
            "conditions": ["looking at viewer"],
            "is_pattern": False,
            "flags": ["IGNORECASE"],
        }
    }
    
    # Add the rule
    if "blindfold_rule" not in blacklist_filter_rules.rules:
        blacklist_filter_rules.push("blindfold_rule", rule_data)
    else:
        blacklist_filter_rules.update("blindfold_rule", rule_data)
    
    # Reload rules
    await blacklist_filter_rules.reload()
    
    # Test case 1: blindfold with "looking at viewer" should filter blindfold
    test1 = "blindfold, looking at viewer, open eyes"
    processor1 = PromptProcessor(test1)
    result1 = await processor1.process()
    print(f"Input 1: {test1}")
    print(f"Output 1: {', '.join(result1)}")
    assert "blindfold" not in result1, "Expected blindfold to be filtered"
    assert "looking at viewer" in result1, "Expected 'looking at viewer' to be kept"
    assert "open eyes" in result1, "Expected 'open eyes' to be kept"
    print("✓ Test case 1 passed")
    
    # Test case 2: blindfold without "looking at viewer" should keep blindfold
    test2 = "blindfold, open eyes, open mouth"
    processor2 = PromptProcessor(test2)
    result2 = await processor2.process()
    print(f"\nInput 2: {test2}")
    print(f"Output 2: {', '.join(result2)}")
    assert "blindfold" in result2, "Expected blindfold to be kept (rule applies)"
    assert "open eyes" in result2, "Expected 'open eyes' to be kept"
    assert "open mouth" in result2, "Expected 'open mouth' to be kept"
    print("✓ Test case 2 passed")
    
    print("\n=== All tests passed! ===\n")


async def test_has_rule_type():
    """
    Test the "has" rule type - filter only when conditions ARE present
    """
    print("\n=== Test: 'has' Rule Type ===")
    
    # Setup: Add "red eyes" to blacklist
    original_blacklist = setting.get("blacklist", "")
    if "red eyes" not in original_blacklist:
        new_blacklist = original_blacklist + ",red eyes" if original_blacklist else "red eyes"
        setting.setting["blacklist"] = new_blacklist
        setting.save()
    
    # Create a filter rule: keep "red eyes" only if "vampire" is present
    rule_data = {
        "name": "red_eyes_vampire_rule",
        "description": "Keep red eyes only if vampire is present",
        "enabled": True,
        "version": 1.0,
        "data": {
            "version": 1.0,
            "target": "red eyes",
            "rule_type": "has",  # Keep if conditions ARE present
            "conditions": ["vampire"],
            "is_pattern": False,
            "flags": ["IGNORECASE"],
        }
    }
    
    # Add the rule
    if "red_eyes_vampire_rule" not in blacklist_filter_rules.rules:
        blacklist_filter_rules.push("red_eyes_vampire_rule", rule_data)
    else:
        blacklist_filter_rules.update("red_eyes_vampire_rule", rule_data)
    
    # Reload rules
    await blacklist_filter_rules.reload()
    
    # Test case 1: red eyes with vampire should keep red eyes
    test1 = "red eyes, vampire, pale skin"
    processor1 = PromptProcessor(test1)
    result1 = await processor1.process()
    print(f"Input 1: {test1}")
    print(f"Output 1: {', '.join(result1)}")
    assert "red eyes" in result1, "Expected 'red eyes' to be kept (vampire present)"
    assert "vampire" in result1, "Expected 'vampire' to be kept"
    print("✓ Test case 1 passed")
    
    # Test case 2: red eyes without vampire should filter red eyes
    test2 = "red eyes, angry, clenched teeth"
    processor2 = PromptProcessor(test2)
    result2 = await processor2.process()
    print(f"\nInput 2: {test2}")
    print(f"Output 2: {', '.join(result2)}")
    assert "red eyes" not in result2, "Expected 'red eyes' to be filtered (no vampire)"
    assert "angry" in result2, "Expected 'angry' to be kept"
    print("✓ Test case 2 passed")
    
    print("\n=== All tests passed! ===\n")


async def test_multiple_conditions():
    """
    Test rules with multiple conditions
    """
    print("\n=== Test: Multiple Conditions ===")
    
    # Setup: Add "weapon" to blacklist
    original_blacklist = setting.get("blacklist", "")
    if "weapon" not in original_blacklist:
        new_blacklist = original_blacklist + ",weapon" if original_blacklist else "weapon"
        setting.setting["blacklist"] = new_blacklist
        setting.save()
    
    # Create a filter rule: keep "weapon" only if both "sword" and "knight" are NOT present
    rule_data = {
        "name": "weapon_rule",
        "description": "Keep weapon only if sword and knight are both NOT present",
        "enabled": True,
        "version": 1.0,
        "data": {
            "version": 1.0,
            "target": "weapon",
            "rule_type": "not_has",
            "conditions": ["sword", "knight"],
            "is_pattern": False,
            "flags": ["IGNORECASE"],
        }
    }
    
    # Add the rule
    if "weapon_rule" not in blacklist_filter_rules.rules:
        blacklist_filter_rules.push("weapon_rule", rule_data)
    else:
        blacklist_filter_rules.update("weapon_rule", rule_data)
    
    # Reload rules
    await blacklist_filter_rules.reload()
    
    # Test case 1: weapon without sword or knight should keep weapon
    test1 = "weapon, gun, modern"
    processor1 = PromptProcessor(test1)
    result1 = await processor1.process()
    print(f"Input 1: {test1}")
    print(f"Output 1: {', '.join(result1)}")
    assert "weapon" in result1, "Expected 'weapon' to be kept"
    print("✓ Test case 1 passed")
    
    # Test case 2: weapon with sword should filter weapon
    test2 = "weapon, sword, battle"
    processor2 = PromptProcessor(test2)
    result2 = await processor2.process()
    print(f"\nInput 2: {test2}")
    print(f"Output 2: {', '.join(result2)}")
    assert "weapon" not in result2, "Expected 'weapon' to be filtered (sword present)"
    assert "sword" in result2, "Expected 'sword' to be kept"
    print("✓ Test case 2 passed")
    
    # Test case 3: weapon with knight should filter weapon
    test3 = "weapon, knight, armor"
    processor3 = PromptProcessor(test3)
    result3 = await processor3.process()
    print(f"\nInput 3: {test3}")
    print(f"Output 3: {', '.join(result3)}")
    assert "weapon" not in result3, "Expected 'weapon' to be filtered (knight present)"
    assert "knight" in result3, "Expected 'knight' to be kept"
    print("✓ Test case 3 passed")
    
    print("\n=== All tests passed! ===\n")


async def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("BLACKLIST FILTER RULES TEST SUITE")
    print("="*60)
    
    try:
        await test_example_from_issue()
        await test_has_rule_type()
        await test_multiple_conditions()
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED SUCCESSFULLY!")
        print("="*60 + "\n")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
