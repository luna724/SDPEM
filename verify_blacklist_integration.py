"""
Manual verification script for blacklist filter rules
Run this to manually verify the integration works as expected
"""
import asyncio
import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_minimal_deps():
    """Mock minimal dependencies needed for testing"""
    class MockLogger:
        @staticmethod
        def setup_logger(name, level):
            pass
        @staticmethod
        def debug(msg):
            print(f"[DEBUG] {msg}")
        @staticmethod
        def println(msg):
            print(msg)
        @staticmethod
        def critical(msg):
            print(f"[CRITICAL] {msg}")
        @staticmethod
        def warn(msg):
            print(f"[WARN] {msg}")
    
    sys.modules['logger'] = MockLogger()

setup_minimal_deps()

from modules.utils.prompt import Prompt
from modules.blacklist import blacklist_filter_rules
import json


async def verify_integration():
    """Verify the blacklist filter rules integration"""
    
    print("\n" + "="*70)
    print("BLACKLIST FILTER RULES - INTEGRATION VERIFICATION")
    print("="*70 + "\n")
    
    # Test 1: Verify config loading
    print("Test 1: Verify configuration loading")
    print("-" * 70)
    
    # Create a test rule
    test_rule = {
        "name": "verification_rule",
        "description": "Test rule for verification",
        "enabled": True,
        "version": 1.0,
        "data": {
            "version": 1.0,
            "target": "test_tag",
            "rule_type": "not_has",
            "conditions": ["condition_tag"],
            "is_pattern": False,
            "flags": ["IGNORECASE"],
        }
    }
    
    # Add the rule
    if "verification_rule" in blacklist_filter_rules.rules:
        print("✓ Rule already exists in configuration")
    else:
        blacklist_filter_rules.push("verification_rule", test_rule)
        print("✓ Rule successfully added to configuration")
    
    # Reload rules
    await blacklist_filter_rules.reload()
    print(f"✓ Rules reloaded. Total rules: {len(blacklist_filter_rules.scripts)}")
    
    # Test 2: Verify rule behavior
    print("\nTest 2: Verify rule behavior")
    print("-" * 70)
    
    # Find the verification rule
    verification_rule = None
    for rule in blacklist_filter_rules.scripts:
        if rule.name == "verification_rule":
            verification_rule = rule
            break
    
    if verification_rule:
        print("✓ Verification rule found in loaded scripts")
        
        # Test with condition absent
        prompt1 = Prompt("test_tag, other_tag")
        should_keep1 = verification_rule.should_keep(prompt1)
        print(f"  - Prompt without condition: should_keep = {should_keep1} (expected: True)")
        assert should_keep1, "Expected rule to keep tag when condition is absent"
        
        # Test with condition present
        prompt2 = Prompt("test_tag, condition_tag, other_tag")
        should_keep2 = verification_rule.should_keep(prompt2)
        print(f"  - Prompt with condition: should_keep = {should_keep2} (expected: False)")
        assert not should_keep2, "Expected rule to filter tag when condition is present"
        
        print("✓ Rule behavior verified successfully")
    else:
        print("✗ Verification rule not found in loaded scripts")
        return False
    
    # Test 3: Check configuration file
    print("\nTest 3: Verify configuration file")
    print("-" * 70)
    
    config_path = blacklist_filter_rules.config_path
    if config_path.exists():
        print(f"✓ Configuration file exists: {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"✓ Configuration loaded. Keys: {list(config.keys())}")
    else:
        print(f"✗ Configuration file not found: {config_path}")
        return False
    
    # Clean up test rule
    if "verification_rule" in blacklist_filter_rules.rules:
        blacklist_filter_rules.delete("verification_rule")
        print("✓ Test rule cleaned up")
    
    print("\n" + "="*70)
    print("ALL VERIFICATION TESTS PASSED!")
    print("="*70 + "\n")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(verify_integration())
    sys.exit(0 if success else 1)
