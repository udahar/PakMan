# Skill: Regex Email Validator

**skill_id:** `regex_email_validator_001`  
**name:** regex_email_validator  
**category:** engineering  
**version:** 1.0  

## Description

Validates email addresses using a practical regex pattern that balances accuracy with readability.

## Primitive Tags

- regex_pattern
- email_validation
- input_validation
- format_check
- rfc5322_lite
- user_input_sanitization

## Prompt Strategy

```
For email validation:

1. UNDERSTAND EMAIL STRUCTURE
   - local-part@domain
   - Local part: letters, digits, dots, hyphens, underscores
   - Domain: domain name with at least one dot
   - TLD: at least 2 characters

2. USE PRACTICAL REGEX
   - Don't use full RFC 5322 (too complex)
   - Don't use overly simple (a@b)
   - Balance accuracy with maintainability

3. VALIDATE IN LAYERS
   - Format check with regex (fast)
   - DNS/MX record check (optional, slower)
   - SMTP verification (optional, slowest)

4. HANDLE EDGE CASES
   - Case insensitivity (normalize to lowercase)
   - Trim whitespace
   - Reject disposable email domains (optional)
   - International domains (IDN)
```

## Solution Summary

```python
import re
from typing import Optional, Tuple


class EmailValidator:
    """Validate email addresses with practical regex."""
    
    # Practical email regex pattern
    # Matches: local-part@domain.tld
    # Local part: alphanumeric, dots, hyphens, underscores, plus signs
    # Domain: alphanumeric, hyphens, must have valid TLD
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+'  # Local part
        r'@'
        r'[a-zA-Z0-9.-]+'      # Domain name
        r'\.[a-zA-Z]{2,}$'     # TLD (2+ chars)
    )
    
    # Common disposable email domains
    DISPOSABLE_DOMAINS = {
        'tempmail.com',
        'throwaway.com',
        '10minutemail.com',
        'guerrillamail.com',
        'mailinator.com',
    }
    
    @classmethod
    def validate(cls, email: str, check_disposable: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Validate email format.
        
        Args:
            email: Email address to validate
            check_disposable: Also check against disposable domains
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not email:
            return False, "Email is required"
        
        # Trim and normalize
        email = email.strip().lower()
        
        if not email:
            return False, "Email cannot be empty"
        
        # Length checks
        if len(email) > 254:
            return False, "Email too long (max 254 characters)"
        
        if len(email.split('@')[0]) > 64:
            return False, "Local part too long (max 64 characters)"
        
        # Format check
        if not cls.EMAIL_PATTERN.match(email):
            return False, "Invalid email format"
        
        # Double dot check
        if '..' in email:
            return False, "Email cannot contain consecutive dots"
        
        # Disposable domain check
        if check_disposable:
            domain = email.split('@')[1]
            if domain in cls.DISPOSABLE_DOMAINS:
                return False, "Disposable email addresses not allowed"
        
        return True, None
    
    @classmethod
    def normalize(cls, email: str) -> Optional[str]:
        """
        Normalize email address (lowercase, trimmed).
        
        Returns:
            Normalized email or None if invalid
        """
        is_valid, _ = cls.validate(email)
        if is_valid:
            return email.strip().lower()
        return None
    
    @classmethod
    def extract_domain(cls, email: str) -> Optional[str]:
        """Extract domain from email address."""
        is_valid, _ = cls.validate(email)
        if is_valid:
            return email.split('@')[1]
        return None
```

## Tests Passed

- [x] Validates standard emails (user@example.com)
- [x] Accepts dots, hyphens, underscores in local part
- [x] Accepts plus addressing (user+tag@example.com)
- [x] Rejects missing @ symbol
- [x] Rejects missing domain
- [x] Rejects missing TLD
- [x] Rejects consecutive dots
- [x] Normalizes to lowercase
- [x] Trims whitespace
- [x] Detects disposable domains (when enabled)

## Benchmark Score

Pending evaluation

## Failure Modes

- **False positives**: Some invalid emails pass regex
  - Mitigation: Layer with DNS/MX record check
- **False negatives**: Some valid international emails rejected
  - Mitigation: Add IDN support if needed
- **Disposable email bypass**: New domains not in list
  - Mitigation: Use external disposable email API

## Created From Task

Initial skill library creation

## Related Skills

- `input_validator_001` - General input validation
- `regex_url_validator_001` - URL validation
- `data_sanitizer_001` - Input sanitization

## Timestamp

2026-03-08
