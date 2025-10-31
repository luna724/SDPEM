# Test Files for Blacklist Filter Rules

This directory contains several test files for validating the blacklist filter rule feature.

## Test Files

### 1. test_blacklist_minimal.py
**Purpose:** Unit tests with no external dependencies  
**Runtime:** ~1 second  
**Coverage:**
- Basic rule logic (has/not_has)
- Pattern matching with regex
- Case-insensitive matching
- Multiple condition handling
- Target matching accuracy

**Run:**
```bash
python test_blacklist_minimal.py
```

### 2. test_blacklist_filter.py
**Purpose:** Full integration tests with PromptProcessor  
**Runtime:** ~5 seconds  
**Requirements:** All project dependencies installed  
**Coverage:**
- Complete integration with prompt processing
- Blacklist configuration interaction
- Real-world usage scenarios
- Examples from the issue

**Run:**
```bash
python test_blacklist_filter.py
```

### 3. verify_blacklist_integration.py
**Purpose:** Manual verification of system integration  
**Runtime:** ~1 second  
**Coverage:**
- Configuration file loading/saving
- Rule initialization
- Manager functionality
- Cleanup operations

**Run:**
```bash
python verify_blacklist_integration.py
```

### 4. final_validation.py
**Purpose:** Validation of exact issue requirements  
**Runtime:** ~1 second  
**Coverage:**
- Exact examples from the issue
- Edge case scenarios
- Complete end-to-end workflow

**Run:**
```bash
python final_validation.py
```

## Quick Test

To quickly verify everything works:

```bash
# Run the minimal test (fastest, no dependencies)
python test_blacklist_minimal.py

# Run the final validation (verifies issue requirements)
python final_validation.py
```

## Expected Output

All tests should output:
```
✅ ALL TESTS PASSED!
```

If any test fails, it will output:
```
❌ Test failed with error: [error message]
```

## Test Structure

Each test follows this pattern:
1. **Setup**: Create test rules and configurations
2. **Execute**: Run the blacklist filtering
3. **Verify**: Assert expected outputs
4. **Cleanup**: Remove test data

## Debugging

If tests fail:
1. Check the error message for the specific assertion that failed
2. Look for `[DEBUG]` messages in the output
3. Verify configuration files exist in `config/` directory
4. Ensure the `modules/blacklist.py` module is accessible

## Adding New Tests

When adding new tests:
1. Follow the existing test structure
2. Use descriptive test names
3. Include cleanup code
4. Add assertions with clear error messages
5. Document what the test validates
