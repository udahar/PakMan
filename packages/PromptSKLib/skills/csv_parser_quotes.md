# Skill: CSV Parser with Quote Handling

**skill_id:** `csv_parser_quotes_001`  
**name:** csv_parser_with_quotes  
**category:** engineering  
**version:** 1.0  

## Description

Parses CSV files correctly handling quoted fields, embedded commas, newlines within quotes, and escaped quotes.

## Primitive Tags

- csv_parsing
- quoted_fields
- embedded_commas
- escaped_quotes
- multiline_fields
- rfc4180

## Prompt Strategy

```
For robust CSV parsing:

1. UNDERSTAND CSV COMPLEXITIES
   - Fields may be quoted with double quotes
   - Quoted fields can contain commas (not delimiters)
   - Quoted fields can contain newlines
   - Double quotes inside quoted fields are escaped as ""
   - Leading/trailing whitespace in unquoted fields

2. USE STANDARD LIBRARY
   - Python: csv module with proper dialect
   - Node.js: csv-parse or papaparse
   - Never write naive split(',') parser

3. CONFIGURE PARSER
   - delimiter: Usually comma
   - quotechar: Usually double quote
   - escapechar or doublequote for escaping
   - skipinitialspace for whitespace

4. HANDLE EDGE CASES
   - Empty fields
   - Fields with only whitespace
   - Mixed quoted and unquoted fields
   - Inconsistent quoting
```

## Solution Summary

```python
import csv
from io import StringIO
from typing import List, Dict, Optional

def parse_csv(
    csv_content: str,
    has_header: bool = True,
    delimiter: str = ',',
    quotechar: str = '"',
    skipinitialspace: bool = True
) -> List[Dict[str, str]]:
    """
    Parse CSV with proper quote handling.
    
    Args:
        csv_content: Raw CSV string
        has_header: Whether first row is header
        delimiter: Field delimiter
        quotechar: Quote character for fields
        skipinitialspace: Skip space after delimiter
    
    Returns:
        List of dictionaries (one per row)
    """
    reader = csv.reader(
        StringIO(csv_content),
        delimiter=delimiter,
        quotechar=quotechar,
        skipinitialspace=skipinitialspace,
        doublequote=True  # Handle "" as escaped quote
    )
    
    rows = list(reader)
    
    if not rows:
        return []
    
    if has_header:
        headers = rows[0]
        data_rows = rows[1:]
        
        return [
            dict(zip(headers, row))
            for row in data_rows
        ]
    else:
        # Generate column names
        num_cols = max(len(row) for row in rows)
        headers = [f"col_{i}" for i in range(num_cols)]
        
        return [
            dict(zip(headers, row))
            for row in rows
        ]


def parse_csv_file(file_path: str, **kwargs) -> List[Dict[str, str]]:
    """Parse CSV file with proper quote handling."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return parse_csv(f.read(), **kwargs)
```

## Tests Passed

- [x] Parses simple CSV without quotes
- [x] Handles quoted fields with embedded commas
- [x] Handles quoted fields with newlines
- [x] Handles escaped quotes ("")
- [x] Handles empty fields
- [x] Handles header row
- [x] Handles rows without headers
- [x] Handles UTF-8 encoding

## Benchmark Score

Pending evaluation

## Failure Modes

- **Malformed CSV**: Unclosed quotes
  - Mitigation: Use strict mode or provide helpful error
- **Large files**: Memory exhaustion
  - Mitigation: Use streaming/iterator approach
- **Inconsistent columns**: Different row lengths
  - Mitigation: Validate and handle missing values

## Created From Task

Initial skill library creation

## Related Skills

- `json_parser_001` - JSON parsing with edge cases
- `data_validator_001` - Validate parsed data
- `streaming_parser_001` - Handle large files

## Timestamp

2026-03-08
