import re
from .models import Action, FilterType, Severity, FilterResult, Filter

class PIIFilter(Filter):
    """Detect and redact personally identifiable information"""

    name = "pii_detector"
    filter_type = FilterType.OUTPUT
    severity = "high"

    PATTERNS = {
        "email": (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "EMAIL"),
        "phone_us": (r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "PHONE"),
        "ssn": (r"\b\d{3}-\d{2}-\d{4}\b", "SSN"),
        "credit_card": (r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "CREDIT_CARD"),
        "ip_address": (r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "IP_ADDRESS"),
        "date_of_birth": (
            r"\b(?:DOB|dob|birth\s*date)[:\s]+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
            "DOB",
            re.IGNORECASE,
        ),
    }

    def check(self, text: str) -> FilterResult:
        matches = []
        redacted = text

        for pii_type, pattern_data in self.PATTERNS.items():
            if isinstance(pattern_data, tuple):
                pattern = pattern_data[0]
                label = pattern_data[1]
            else:
                pattern = pattern_data
                label = pii_type.upper()
            found = re.findall(pattern, text, re.IGNORECASE)
            if found:
                for match in found:
                    matches.append({"type": label, "value": match[:4] + "****"})
                    redacted = redacted.replace(match, f"[{label}_REDACTED]")

        if not matches:
            return FilterResult(passed=True, action=Action.PASS, filter_name=self.name)

        return FilterResult(
            passed=True,
            action=Action.MODIFY,
            filter_name=self.name,
            severity=Severity.HIGH.value,
            matched_content=matches,
            reason=f"Found {len(matches)} PII items - redacted",
            replacement=redacted,
        )


class SecretsFilter(Filter):
    """Detect and redact API keys, passwords, tokens"""

    name = "secrets_detector"
    filter_type = FilterType.OUTPUT
    severity = "critical"

    PATTERNS = {
        "openai_key": (r"sk-[a-zA-Z0-9]{20,}", "OPENAI_KEY"),
        "anthropic_key": (r"sk-ant-[a-zA-Z0-9-]{50,}", "ANTHROPIC_KEY"),
        "aws_access": (r"AKIA[0-9A-Z]{16}", "AWS_ACCESS_KEY"),
        "github_token": (r"ghp_[a-zA-Z0-9]{36}", "GITHUB_TOKEN"),
        "jwt_token": (r"eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*", "JWT"),
        "password_in_code": (r'password["\s:=]+\S+', "PASSWORD"),
        "api_key_generic": (
            r'(?i)(api[_-]?key|secret[_-]?key)["\s:=]+\S{10,}',
            "API_KEY",
        ),
        "private_key": (
            r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
            "PRIVATE_KEY",
        ),
    }

    def check(self, text: str) -> FilterResult:
        matches = []
        redacted = text

        for secret_type, (pattern, label) in self.PATTERNS.items():
            found = re.findall(pattern, text, re.IGNORECASE)
            if found:
                for match in found:
                    masked = (
                        match[:4] + "*" * max(0, len(match) - 8) + match[-4:]
                        if len(match) > 12
                        else "****"
                    )
                    matches.append({"type": label, "masked": masked})
                    redacted = redacted.replace(match, f"[{label}_REDACTED]")

        if not matches:
            return FilterResult(passed=True, action=Action.PASS, filter_name=self.name)

        return FilterResult(
            passed=True,
            action=Action.MODIFY,
            filter_name=self.name,
            severity=Severity.CRITICAL.value,
            matched_content=matches,
            reason=f"Found {len(matches)} secrets - redacted",
            replacement=redacted,
        )


class HarmfulContentFilter(Filter):
    """Detect harmful content"""

    name = "harmful_content_detector"
    filter_type = FilterType.OUTPUT
    severity = "critical"

    CATEGORIES = {
        "violence": [
            "harm",
            "kill",
            "murder",
            "attack",
            "weapon",
            "bomb",
            "shoot",
            "stab",
            "assault",
            "violence",
        ],
        "hate_speech": [
            "hate",
            "slur",
            "discriminate",
            "racist",
            "sexist",
            "homophobic",
        ],
        "self_harm": ["suicide", "self harm", "cutting", "anorexia", "bulimia"],
        "illegal": ["drug", "illegal", "fraud", "scam", "piracy", "theft", "bribe"],
    }

    def check(self, text: str) -> FilterResult:
        text_lower = text.lower()
        matches = []

        for category, keywords in self.CATEGORIES.items():
            found = [kw for kw in keywords if kw in text_lower]
            if found:
                matches.append({"category": category, "keywords": found})

        if not matches:
            return FilterResult(passed=True, action=Action.PASS, filter_name=self.name)

        action = (
            Action.BLOCK
            if any(
                m["category"] in ["violence", "hate_speech", "self_harm"]
                for m in matches
            )
            else Action.FLAG
        )

        return FilterResult(
            passed=False,
            action=action,
            filter_name=self.name,
            severity=Severity.CRITICAL.value
            if action == Action.BLOCK
            else Severity.HIGH.value,
            matched_content=matches,
            reason=f"Found harmful content: {[m['category'] for m in matches]}",
        )


class ProfanityFilter(Filter):
    """Detect profanity"""

    name = "profanity_detector"
    filter_type = FilterType.OUTPUT
    severity = "medium"

    PROFANITY = [
        "fuck",
        "shit",
        "damn",
        "ass",
        "bitch",
        "bastard",
        "crap",
        "piss",
        "dick",
        "cock",
        "cunt",
        "whore",
        "slut",
    ]

    def check(self, text: str) -> FilterResult:
        text_lower = text.lower()
        found = [
            w
            for w in self.PROFANITY
            if re.search(r"\b" + re.escape(w) + r"(s|ing|ed)?\b", text_lower)
        ]

        if not found:
            return FilterResult(passed=True, action=Action.PASS, filter_name=self.name)

        censored = text
        for word in set(found):
            censored = re.sub(
                re.escape(word), "*" * len(word), censored, flags=re.IGNORECASE
            )

        return FilterResult(
            passed=True,
            action=Action.MODIFY,
            filter_name=self.name,
            severity=Severity.MEDIUM.value,
            matched_content=list(set(found)),
            reason=f"Found {len(found)} profanity terms",
            replacement=censored,
        )


class FormatValidator(Filter):
    """Validate output format"""

    name = "format_validator"
    filter_type = FilterType.OUTPUT
    severity = "low"

    def __init__(self, max_length: int = 100000, **config):
        super().__init__(**config)
        self.max_length = max_length

    def check(self, text: str) -> FilterResult:
        issues = []
        if len(text) > self.max_length:
            issues.append(f"Exceeds {self.max_length} chars")
        if "\x00" in text:
            issues.append("Null bytes")
        if re.search(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", text):
            issues.append("Control characters")

        if issues:
            return FilterResult(
                passed=True,
                action=Action.FLAG,
                filter_name=self.name,
                severity=Severity.LOW.value,
                reason="; ".join(issues),
            )
        return FilterResult(passed=True, action=Action.PASS, filter_name=self.name)


class LengthLimitFilter(Filter):
    """Enforce length limits"""

    name = "length_limiter"
    filter_type = FilterType.OUTPUT
    severity = "medium"

    def __init__(self, max_tokens: int = 4000, **config):
        super().__init__(**config)
        self.max_tokens = max_tokens

    def check(self, text: str) -> FilterResult:
        estimated = len(text) // 4
        if estimated > self.max_tokens:
            truncated = self.max_tokens * 4
            return FilterResult(
                passed=True,
                action=Action.MODIFY,
                filter_name=self.name,
                severity=Severity.MEDIUM.value,
                reason=f"Truncated from ~{estimated} to {self.max_tokens} tokens",
                replacement=text[:truncated] + "\n\n[Output truncated]",
            )
        return FilterResult(passed=True, action=Action.PASS, filter_name=self.name)

