# Skill: Null Pointer Guard

**skill_id:** `null_pointer_guard_001`  
**name:** null_pointer_guard  
**category:** repair  
**version:** 1.0  

## Description

Adds defensive checks to prevent null/None/undefined reference errors in code.

## Primitive Tags

- null_check
- defensive_programming
- optional_handling
- safe_navigation
- guard_clause
- early_return

## Prompt Strategy

```
For null pointer prevention:

1. IDENTIFY RISKY ACCESS PATTERNS
   - Chained property access: a.b.c
   - Function return values (may be null)
   - Dictionary/map lookups
   - Array element access
   - User input/external data

2. ADD GUARD CLAUSES
   - Check for null before access
   - Return early if null
   - Provide default values

3. USE SAFE ACCESS PATTERNS
   - Optional chaining: a?.b?.c
   - Nullish coalescing: a ?? default
   - Try/except for risky access
   - get() method for dictionaries

4. CONSIDER TYPE SYSTEM
   - Use Optional/Nullable types
   - Enforce null checks at compile time
   - Document which values can be null
```

## Solution Summary

### Python Patterns

```python
# ❌ WRONG: Assumes value exists
def get_user_name(user):
    return user.profile.name


# ✅ CORRECT: Guard clause
def get_user_name(user):
    if user is None:
        return None
    if user.profile is None:
        return None
    return user.profile.name


# ✅ BETTER: Using Optional type hints
from typing import Optional

def get_user_name(user: Optional[User]) -> Optional[str]:
    if user is None or user.profile is None:
        return None
    return user.profile.name


# ✅ BEST: Using safe navigation pattern
def get_user_name(user: Optional[User]) -> Optional[str]:
    return getattr(getattr(user, 'profile', None), 'name', None)


# ❌ WRONG: Dictionary access may fail
def get_config_value(config, key):
    return config[key]  # KeyError if missing


# ✅ CORRECT: Safe dictionary access
def get_config_value(config, key, default=None):
    return config.get(key, default)


# ❌ WRONG: List access may fail
def get_first_item(items):
    return items[0]  # IndexError if empty


# ✅ CORRECT: Safe list access
def get_first_item(items, default=None):
    return items[0] if items else default
```

### TypeScript Patterns

```typescript
// ❌ WRONG: Assumes value exists
function getUserName(user: User): string {
    return user.profile.name;
}

// ✅ CORRECT: Optional chaining
function getUserName(user: User | null): string | null {
    return user?.profile?.name ?? null;
}

// ✅ BETTER: With nullish coalescing
function getUserName(user: User | null): string {
    return user?.profile?.name ?? 'Anonymous';
}
```

## Tests Passed

- [x] Handles null/None input
- [x] Handles nested null properties
- [x] Handles missing dictionary keys
- [x] Handles empty arrays
- [x] Provides sensible defaults
- [x] Uses type hints correctly

## Failure Modes

- **Excessive guards**: Performance impact
  - Mitigation: Guard only at boundaries
- **Hidden bugs**: Swallowing real errors
  - Mitigation: Log when null encountered
- **Default masking**: Wrong defaults hide issues
  - Mitigation: Use None/null as default, handle explicitly

## Related Skills

- `input_validator_001` - Validate inputs
- `error_handler_001` - Error handling patterns
- `type_safety_001` - Type system usage

## Timestamp

2026-03-08
