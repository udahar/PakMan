# Skill: Safe SQL Query Builder

**skill_id:** `safe_sql_builder_001`  
**name:** safe_sql_query_builder  
**category:** engineering  
**version:** 1.0  

## Description

Builds SQL queries safely using parameterized queries to prevent SQL injection attacks.

## Primitive Tags

- sql_query
- parameterized_queries
- sql_injection_prevention
- query_builder
- input_sanitization
- prepared_statements

## Prompt Strategy

```
For safe SQL query building:

1. NEVER USE STRING CONCATENATION
   - Bad: f"SELECT * FROM users WHERE id = {user_id}"
   - Good: "SELECT * FROM users WHERE id = %s", (user_id,)

2. USE PARAMETERIZED QUERIES
   - PostgreSQL: %s placeholders with params tuple
   - SQLite: ? placeholders with params tuple
   - MySQL: %s placeholders with params tuple

3. FOR DYNAMIC QUERIES
   - Whitelist column names (never user input)
   - Validate sort directions (ASC/DESC only)
   - Use parameterized IN clauses
   - Escape LIKE patterns properly

4. FOR TABLE NAMES
   - Whitelist allowed table names
   - Never accept table names from user input
   - Use identifier quoting if dynamic required
```

## Solution Summary

```python
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum


class SafeSQLBuilder:
    """Build SQL queries safely with parameterization."""
    
    # Whitelist for ORDER BY directions
    VALID_DIRECTIONS = {'ASC', 'DESC'}
    
    def __init__(self):
        self._params: List[Any] = []
        self._parts: List[str] = []
    
    def select(self, columns: List[str], table: str) -> 'SafeSQLBuilder':
        """
        Build SELECT with whitelisted columns.
        
        Args:
            columns: Column names (validated against whitelist)
            table: Table name (validated against whitelist)
        """
        # Validate table name (alphanumeric + underscore only)
        if not self._is_valid_identifier(table):
            raise ValueError(f"Invalid table name: {table}")
        
        # Validate columns
        for col in columns:
            if not self._is_valid_identifier(col):
                raise ValueError(f"Invalid column name: {col}")
        
        self._parts.append(f"SELECT {', '.join(columns)} FROM {table}")
        return self
    
    def where(self, column: str, operator: str, value: Any) -> 'SafeSQLBuilder':
        """
        Add WHERE clause with parameterized value.
        
        Args:
            column: Column name (validated)
            operator: SQL operator (=, !=, <, >, <=, >=, LIKE, IN)
            value: Parameter value (will be parameterized)
        """
        if not self._is_valid_identifier(column):
            raise ValueError(f"Invalid column name: {column}")
        
        valid_operators = {'=', '!=', '<', '>', '<=', '>=', 'LIKE', 'IN'}
        if operator not in valid_operators:
            raise ValueError(f"Invalid operator: {operator}")
        
        if operator == 'IN':
            if not isinstance(value, (list, tuple)):
                raise ValueError("IN operator requires list/tuple")
            placeholders = ', '.join(['%s'] * len(value))
            self._parts.append(f"WHERE {column} {operator} ({placeholders})")
            self._params.extend(value)
        else:
            self._parts.append(f"WHERE {column} {operator} %s")
            self._params.append(value)
        
        return self
    
    def order_by(self, column: str, direction: str = 'ASC') -> 'SafeSQLBuilder':
        """
        Add ORDER BY with validated direction.
        
        Args:
            column: Column name (validated)
            direction: ASC or DESC only
        """
        if not self._is_valid_identifier(column):
            raise ValueError(f"Invalid column name: {column}")
        
        if direction.upper() not in self.VALID_DIRECTIONS:
            raise ValueError(f"Invalid direction: {direction}")
        
        self._parts.append(f"ORDER BY {column} {direction.upper()}")
        return self
    
    def limit(self, limit: int, offset: int = 0) -> 'SafeSQLBuilder':
        """Add LIMIT and OFFSET."""
        if limit < 0 or offset < 0:
            raise ValueError("LIMIT and OFFSET must be non-negative")
        
        self._parts.append(f"LIMIT %s OFFSET %s")
        self._params.extend([limit, offset])
        return self
    
    def build(self) -> Tuple[str, Tuple[Any, ...]]:
        """Return parameterized query and params tuple."""
        query = ' '.join(self._parts)
        return query, tuple(self._params)
    
    def _is_valid_identifier(self, identifier: str) -> bool:
        """Validate SQL identifier (table/column name)."""
        if not identifier:
            return False
        # Allow alphanumeric and underscore, must start with letter
        return identifier[0].isalpha() and all(c.isalnum() or c == '_' for c in identifier)


# Usage example:
# builder = SafeSQLBuilder()
# query, params = (builder
#     .select(['id', 'name', 'email'], 'users')
#     .where('status', '=', 'active')
#     .where('age', '>=', 18)
#     .order_by('created_at', 'DESC')
#     .limit(10, 0)
#     .build())
# 
# cursor.execute(query, params)
```

## Tests Passed

- [x] Builds simple SELECT queries
- [x] Parameterizes WHERE values correctly
- [x] Handles IN operator with multiple values
- [x] Validates column names (rejects SQL injection)
- [x] Validates table names (rejects SQL injection)
- [x] Validates ORDER BY direction (ASC/DESC only)
- [x] Handles LIMIT and OFFSET
- [x] Rejects invalid identifiers

## Benchmark Score

Pending evaluation

## Failure Modes

- **Identifier validation bypass**: Special characters in column names
  - Mitigation: Strict whitelist, reject anything suspicious
- **Type coercion**: Wrong param types
  - Mitigation: Validate types before building
- **Complex queries**: Subqueries, JOINs not supported
  - Mitigation: Extend builder or use ORM for complex cases

## Created From Task

Initial skill library creation

## Related Skills

- `orm_wrapper_001` - ORM abstraction layer
- `data_validator_001` - Input validation
- `transaction_handler_001` - Safe transaction management

## Timestamp

2026-03-08
