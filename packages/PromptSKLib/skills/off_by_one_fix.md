# Skill: Off-by-One Loop Fix

**skill_id:** `off_by_one_fix_001`  
**name:** off_by_one_loop_fix  
**category:** repair  
**version:** 1.0  

## Description

Identifies and fixes off-by-one errors in loops, array indexing, and boundary conditions.

## Primitive Tags

- loop_bounds
- array_indexing
- boundary_condition
- fence_post_error
- iteration_fix
- index_validation

## Prompt Strategy

```
For off-by-one errors:

1. IDENTIFY SYMPTOMS
   - Loop runs one too many/few times
   - Index out of bounds error
   - Last/first element not processed
   - Array access at invalid index

2. CHECK COMMON PATTERNS
   - Loop condition: < vs <=
   - Starting index: 0 vs 1
   - Ending index: length vs length-1
   - Slice boundaries: [start:end] semantics

3. APPLY FIXES
   - For inclusive end: use <= or length-1
   - For exclusive end: use < or length
   - Zero-based arrays: start at 0, end at length-1
   - Python slices: [0:n] includes 0, excludes n

4. VERIFY FIX
   - Test with empty array
   - Test with single element
   - Test with two elements
   - Test boundary conditions
```

## Solution Summary

### Common Patterns and Fixes

```python
# ❌ WRONG: Runs n+1 times (0, 1, 2, ..., n)
for i in range(0, n + 1):  # or i <= n
    process(arr[i])  # Index out of bounds!

# ✅ CORRECT: Runs n times (0, 1, 2, ..., n-1)
for i in range(0, n):  # or i < n
    process(arr[i])


# ❌ WRONG: Misses last element
for i in range(0, len(arr) - 1):
    process(arr[i])  # Never processes arr[len-1]

# ✅ CORRECT: Processes all elements
for i in range(0, len(arr)):
    process(arr[i])


# ❌ WRONG: Starts at wrong index
for i in range(1, len(arr)):  # Skips arr[0]
    process(arr[i])

# ✅ CORRECT: Zero-based indexing
for i in range(0, len(arr)):
    process(arr[i])


# ❌ WRONG: Slice misses last element
result = arr[0:len(arr) - 1]  # Excludes last element

# ✅ CORRECT: Slice includes up to (but not including) end
result = arr[0:len(arr)]  # or just arr[:]


# ❌ WRONG: Two-pointer meeting condition
left, right = 0, len(arr) - 1
while left < right:  # May miss middle element
    # ...

# ✅ CORRECT: Depends on use case
while left <= right:  # Process until pointers cross
    # ...
```

## Tests Passed

- [x] Identifies < vs <= errors
- [x] Fixes starting index errors
- [x] Fixes ending index errors
- [x] Handles slice boundary errors
- [x] Handles two-pointer errors
- [x] Works with empty arrays
- [x] Works with single-element arrays

## Failure Modes

- **Over-correction**: Fix creates opposite error
  - Mitigation: Test with known inputs
- **Wrong pattern**: Misdiagnosed root cause
  - Mitigation: Trace through with debugger

## Related Skills

- `boundary_checker_001` - Validate boundaries
- `loop_invariant_001` - Verify loop correctness
- `array_bounds_checker_001` - Safe array access

## Timestamp

2026-03-08
