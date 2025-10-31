"""
Minimal test for blacklist filter rules without full dependency chain
"""
import asyncio
import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock modules to avoid dependency issues
class MockLogger:
    @staticmethod
    def debug(msg): print(f"[DEBUG] {msg}")
    @staticmethod
    def println(msg): print(msg)
    @staticmethod
    def critical(msg): print(f"[CRITICAL] {msg}")

sys.modules['logger'] = MockLogger()

from modules.utils.prompt import Prompt
from modules.blacklist import BlacklistFilterRule


async def test_basic_rule_logic():
    """Test basic rule logic without full integration"""
    print("\n=== Test: Basic Rule Logic ===")
    
    # Test 1: "not_has" rule type
    rule_data = {
        "name": "test_rule",
        "description": "Test rule",
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
    
    rule = BlacklistFilterRule(rule_data)
    await rule.prepare_rule()
    
    # Test target matching
    assert rule.matches_target("blindfold"), "Should match 'blindfold'"
    assert rule.matches_target(" blindfold "), "Should match ' blindfold '"
    assert not rule.matches_target("blindfold2"), "Should not match 'blindfold2'"
    print("✓ Target matching works correctly")
    
    # Test should_keep with "not_has" - should keep when condition is NOT present
    prompt1 = Prompt("blindfold, open eyes, open mouth")
    assert rule.should_keep(prompt1), "Should keep blindfold when 'looking at viewer' is NOT present"
    print("✓ Rule correctly keeps tag when condition is absent")
    
    # Test should_keep with "not_has" - should NOT keep when condition IS present
    prompt2 = Prompt("blindfold, looking at viewer, open eyes")
    assert not rule.should_keep(prompt2), "Should NOT keep blindfold when 'looking at viewer' IS present"
    print("✓ Rule correctly filters tag when condition is present")
    
    print("\n=== Test: 'has' Rule Type ===")
    
    # Test 2: "has" rule type
    rule_data2 = {
        "name": "test_rule2",
        "description": "Test has rule",
        "enabled": True,
        "version": 1.0,
        "data": {
            "version": 1.0,
            "target": "red eyes",
            "rule_type": "has",
            "conditions": ["vampire"],
            "is_pattern": False,
            "flags": ["IGNORECASE"],
        }
    }
    
    rule2 = BlacklistFilterRule(rule_data2)
    await rule2.prepare_rule()
    
    # Test should_keep with "has" - should keep when condition IS present
    prompt3 = Prompt("red eyes, vampire, pale skin")
    assert rule2.should_keep(prompt3), "Should keep 'red eyes' when 'vampire' IS present"
    print("✓ 'has' rule correctly keeps tag when condition is present")
    
    # Test should_keep with "has" - should NOT keep when condition is NOT present
    prompt4 = Prompt("red eyes, angry, clenched teeth")
    assert not rule2.should_keep(prompt4), "Should NOT keep 'red eyes' when 'vampire' is NOT present"
    print("✓ 'has' rule correctly filters tag when condition is absent")
    
    print("\n=== Test: Multiple Conditions ===")
    
    # Test 3: Multiple conditions with "not_has"
    rule_data3 = {
        "name": "test_rule3",
        "description": "Test multiple conditions",
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
    
    rule3 = BlacklistFilterRule(rule_data3)
    await rule3.prepare_rule()
    
    # Should keep when NONE of the conditions are present
    prompt5 = Prompt("weapon, gun, modern")
    assert rule3.should_keep(prompt5), "Should keep when none of the conditions are present"
    print("✓ Multiple conditions: keeps when none are present")
    
    # Should NOT keep when ANY condition is present
    prompt6 = Prompt("weapon, sword, battle")
    assert not rule3.should_keep(prompt6), "Should NOT keep when 'sword' is present"
    print("✓ Multiple conditions: filters when any condition is present")
    
    prompt7 = Prompt("weapon, knight, armor")
    assert not rule3.should_keep(prompt7), "Should NOT keep when 'knight' is present"
    print("✓ Multiple conditions: filters when any condition is present (2)")
    
    print("\n=== All Basic Tests Passed! ===\n")


async def test_pattern_matching():
    """Test pattern-based matching"""
    print("\n=== Test: Pattern Matching ===")
    
    rule_data = {
        "name": "pattern_rule",
        "description": "Test pattern matching",
        "enabled": True,
        "version": 1.0,
        "data": {
            "version": 1.0,
            "target": ".*blind.*",
            "rule_type": "not_has",
            "conditions": ["viewer"],
            "is_pattern": True,
            "flags": ["IGNORECASE"],
        }
    }
    
    rule = BlacklistFilterRule(rule_data)
    await rule.prepare_rule()
    
    # Test pattern matching for target
    assert rule.matches_target("blindfold"), "Should match 'blindfold' with pattern"
    assert rule.matches_target("blind"), "Should match 'blind' with pattern"
    assert rule.matches_target("blinded"), "Should match 'blinded' with pattern"
    assert not rule.matches_target("fold"), "Should not match 'fold'"
    print("✓ Pattern matching works correctly")
    
    print("\n=== Pattern Matching Tests Passed! ===\n")


async def test_case_insensitivity():
    """Test case insensitive matching"""
    print("\n=== Test: Case Insensitivity ===")
    
    rule_data = {
        "name": "case_rule",
        "description": "Test case insensitivity",
        "enabled": True,
        "version": 1.0,
        "data": {
            "version": 1.0,
            "target": "BlindFold",
            "rule_type": "not_has",
            "conditions": ["Looking At Viewer"],
            "is_pattern": False,
            "flags": ["IGNORECASE"],
        }
    }
    
    rule = BlacklistFilterRule(rule_data)
    await rule.prepare_rule()
    
    # Test case insensitive target matching
    assert rule.matches_target("blindfold"), "Should match lowercase"
    assert rule.matches_target("BLINDFOLD"), "Should match uppercase"
    assert rule.matches_target("BlindFold"), "Should match mixed case"
    print("✓ Case insensitive target matching works")
    
    # Test case insensitive condition matching
    prompt1 = Prompt("blindfold, LOOKING AT VIEWER, open eyes")
    assert not rule.should_keep(prompt1), "Should recognize uppercase condition"
    
    prompt2 = Prompt("blindfold, looking at viewer, open eyes")
    assert not rule.should_keep(prompt2), "Should recognize lowercase condition"
    
    prompt3 = Prompt("blindfold, Looking At Viewer, open eyes")
    assert not rule.should_keep(prompt3), "Should recognize mixed case condition"
    print("✓ Case insensitive condition matching works")
    
    print("\n=== Case Insensitivity Tests Passed! ===\n")


async def test_has_with_multiple_conditions():
    """Test 'has' rule with multiple conditions - all must be present"""
    print("\n=== Test: 'has' with Multiple Conditions ===")
    
    rule_data = {
        "name": "multi_has_rule",
        "description": "Keep only if both vampire AND gothic are present",
        "enabled": True,
        "version": 1.0,
        "data": {
            "version": 1.0,
            "target": "red eyes",
            "rule_type": "has",
            "conditions": ["vampire", "gothic"],
            "is_pattern": False,
            "flags": ["IGNORECASE"],
        }
    }
    
    rule = BlacklistFilterRule(rule_data)
    await rule.prepare_rule()
    
    # Test: Both conditions present - should keep
    prompt1 = Prompt("red eyes, vampire, gothic, pale skin")
    assert rule.should_keep(prompt1), "Should keep when both conditions are present"
    print("✓ Keeps target when ALL conditions are present")
    
    # Test: Only one condition present - should NOT keep
    prompt2 = Prompt("red eyes, vampire, modern")
    assert not rule.should_keep(prompt2), "Should NOT keep when only vampire is present"
    print("✓ Filters target when only one condition is present")
    
    prompt3 = Prompt("red eyes, gothic, night")
    assert not rule.should_keep(prompt3), "Should NOT keep when only gothic is present"
    print("✓ Filters target when only other condition is present")
    
    # Test: Neither condition present - should NOT keep
    prompt4 = Prompt("red eyes, angry, modern")
    assert not rule.should_keep(prompt4), "Should NOT keep when neither condition is present"
    print("✓ Filters target when no conditions are present")
    
    print("\n=== Multiple Conditions 'has' Tests Passed! ===\n")


async def run_all_tests():
    """Run all minimal tests"""
    print("\n" + "="*60)
    print("BLACKLIST FILTER RULES - MINIMAL TEST SUITE")
    print("="*60)
    
    try:
        await test_basic_rule_logic()
        await test_pattern_matching()
        await test_case_insensitivity()
        await test_has_with_multiple_conditions()
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED SUCCESSFULLY!")
        print("="*60 + "\n")
        return 0
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
