import re
from .models import Action, FilterType, Severity, FilterResult, Filter

class EnhancedInjectionFilter(Filter):
    """
    Multi-layer prompt injection defense.

    Layers:
    1. Pattern Detection - Regex matching known attacks
    2. Structural Analysis - Detect unusual formatting
    3. Token Analysis - Look for special tokens
    4. Behavioral Heuristics - Suspicious patterns
    5. Sanitization - Clean before passing to LLM
    """

    name = "enhanced_injection_detector"
    filter_type = FilterType.INPUT
    severity = "critical"

    # Layer 1: Known injection patterns
    DANGEROUS_PATTERNS = [
        # Direct instruction overrides
        (
            r"ignore\s+(all\s+)?(previous|prior)\s+(instructions?|rules?|commands?)",
            "ignore_instructions",
        ),
        (
            r"disregard\s+(?:all\s+)?(?:previous|prior|your\s+)?(?:instructions?|rules?)",
            "disregard_rules",
        ),
        (r"override\s+(your\s+)?(system|programming|safety)", "override_safety"),
        # Role manipulation
        (r"you\s+are\s+now(?:\s+in|\s+a)?(?:\s+mode)?", "role_override"),
        (r"(?:pretend|act\s+as|be\s+like)\s+(?:you\s+are|a|an)", "pretend_mode"),
        (r"you\s+can\s+(?:now\s+)?(?:do|be)\s+anything", "unrestricted_mode"),
        (r"(?:developer|dev)\s*:\s*[^.\n]+", "developer_prefix"),
        (r"system\s*:\s*[^.\n]+", "system_prefix"),
        # Jailbreak terms
        (
            r"(?:jailbreak|dev_mode|unrestricted|infinite|prompt_injection)",
            "jailbreak_terms",
        ),
        (r"dan\s+(?:mode|bar)", "DAN_attack"),
        (r"角色扮演\s*[:；]", "roleplay_zh"),  # Chinese roleplay
        # Memory manipulation
        (
            r"forget\s+(?:everything|all|what)\s+(?:you|I)\s+(?:know|told|learn)",
            "memory_wipe",
        ),
        (
            r"(?:delete|remove|clear)\s+(?:your\s+)?(?:memory|context|history)",
            "context_clear",
        ),
        # New instructions
        (r"new\s+instructions?:", "new_instructions"),
        (
            r"(?:instead|instead of)\s+(?:following|obeying)\s+(?:my|the)",
            "instruction_replacement",
        ),
        # Data exfiltration
        (r"output\s+everything\s+(?:after|below|before)", "exfiltration"),
        (r"print\s+(?:all|full|complete)\s+(?:system|response)", "full_output"),
        # Special tokens (encoding attacks)
        (r"<\|(?:system|user|assistant|bot|finetune)", "special_tokens"),
        (r"\[INST\]\[INST\]", "multi_inst"),
        (r"<\/?(?:system|prompt)", "xml_tags"),
        (r"#{.*?}", "markdown_injection"),
        # Base64/encoding attempts
        (r"(?:base64|encoded|decode)\s*[:=]", "encoding_attempt"),
        # Cascading style
        (r";;+|,,+", "repeated_delimiters"),
        # Hidden instructions
        (r"(?:invisible|hidden|zero\s*width)", "hidden_text"),
        (r"\u200b|\u200c|\u200d", "zero_width_chars"),
        # NEW: More social engineering
        (r"dont\s+tell", "reverse_psychology"),
        (r"dont\s+ask", "reverse_psychology"),
        (r"hypothetical", "hypothetical_escape"),
        (r"pretend\s+(?:to|that|im)", "roleplay_attempt"),
        (r"#\s*system", "code_injection"),
        (r"translate", "translation_attempt"),
        (r"you\s+can\s+trust", "trust_appeal"),
    ]

    # Layer 3: Suspicious token sequences
    SUSPICIOUS_TOKEN_SEQUENCES = [
        ["system", "message"],
        ["developer", "message"],
        ["user", "message"],
        ["ignore", "previous"],
        ["forget", "everything"],
        ["you", "are", "now"],
        ["pretend", "to", "be"],
    ]

    # Behavioral heuristics
    HEURISTICS = {
        "excessive_newlines": (
            lambda t: t.count("\n\n") > 10,
            "Excessive paragraph breaks",
        ),
        "caps_lock_rage": (
            lambda t: sum(1 for c in t if c.isupper()) > len(t) * 0.5,
            "Excessive caps",
        ),
        "base64_pattern": (
            lambda t: len(re.findall(r"[A-Za-z0-9+/]{20,}={0,2}", t)) > 2,
            "Potential base64",
        ),
        "repeated_words": (
            lambda t: len(set(t.lower().split())) < len(t.split()) * 0.3,
            "High repetition",
        ),
        "url_spam": (lambda t: t.count("http") > 5, "URL spam"),
        "instruction_density": (
            lambda t: len(
                re.findall(r"(?:must|should|never|always|do not|do not)", t, re.I)
            )
            > 5,
            "High instruction density",
        ),
    }

    CRITICAL_PATTERNS = [
        "ignore_instructions",
        "disregard_rules",
        "override_safety",
        "memory_wipe",
        "developer_prefix",
    ]

    def __init__(self, **config):
        super().__init__(**config)
        self.sanitize = config.get("sanitize", True)
        self.block_threshold = config.get("block_threshold", 1)

    def check(self, text: str) -> FilterResult:
        all_matches = []
        critical_matches = []

        # Layer 1: Pattern matching
        text_lower = text.lower()
        for pattern, threat_type in self.DANGEROUS_PATTERNS:
            found = re.findall(pattern, text_lower, re.IGNORECASE)
            if found:
                match_entry = {"layer": "pattern", "type": threat_type, "match": str(found[:3])}
                all_matches.append(match_entry)
                if threat_type in self.CRITICAL_PATTERNS:
                    critical_matches.append(match_entry)

        # Layer 2: Structural analysis
        structural = self._analyze_structure(text)
        if structural:
            all_matches.extend(structural)

        # Layer 3: Token analysis
        tokens = self._analyze_tokens(text)
        if tokens:
            all_matches.extend(tokens)

        # Layer 4: Behavioral heuristics
        heuristics = self._analyze_behavior(text)
        if heuristics:
            all_matches.extend(heuristics)

        if not all_matches:
            if self.sanitize:
                cleaned = self.sanitize_input(text)
                return FilterResult(
                    passed=True,
                    action=Action.PASS,
                    filter_name=self.name,
                    replacement=cleaned,
                    metadata={"sanitized": True},
                )
            return FilterResult(passed=True, action=Action.PASS, filter_name=self.name)

        # Block on critical patterns OR high threat score
        threat_score = len(all_matches)
        has_critical = len(critical_matches) > 0

        if has_critical or threat_score >= self.block_threshold:
            severity = Severity.CRITICAL.value if has_critical else Severity.HIGH.value
            return FilterResult(
                passed=False,
                action=Action.BLOCK,
                filter_name=self.name,
                severity=severity,
                matched_content=all_matches,
                reason=f"Injection detected ({threat_score} indicators): {[m['type'] for m in all_matches[:5]]}",
            )
        else:
            sanitized = self.sanitize_input(text)
            return FilterResult(
                passed=True,
                action=Action.MODIFY,
                filter_name=self.name,
                severity=Severity.MEDIUM.value,
                matched_content=all_matches,
                reason=f"Flagged {threat_score} potential issues - sanitized",
                replacement=sanitized,
            )

    def _analyze_structure(self, text: str) -> list:
        """Layer 2: Detect unusual structure"""
        issues = []

        # Check for concatenated instructions (multiple "Human:" or "User:" markers)
        markers = len(
            re.findall(
                r"(?:^|\n)(?:Human|User|You):", text, re.MULTILINE | re.IGNORECASE
            )
        )
        if markers > 1:
            issues.append(
                {"layer": "structure", "type": "multiple_markers", "count": markers}
            )

        # Check for base64-like strings
        if re.search(r"^[A-Za-z0-9+/]{50,}={0,2}$", text, re.MULTILINE):
            issues.append({"layer": "structure", "type": "base64_encoded"})

        # Check for nested quotes
        nested = len(re.findall(r'"{[^"]*"{', text))
        if nested > 2:
            issues.append(
                {"layer": "structure", "type": "nested_quotes", "count": nested}
            )

        # Check for unusual delimiters
        if re.search(r"---+|^===+$", text):
            issues.append({"layer": "structure", "type": "unusual_delimiters"})

        # Check for injected XML-like tags
        if re.search(r"<[a-z]+[^>]*>.*</[a-z]+>", text, re.DOTALL):
            issues.append({"layer": "structure", "type": "xml_injection"})

        return issues

    def _analyze_tokens(self, text: str) -> list:
        """Layer 3: Check for suspicious token sequences"""
        issues = []

        text_tokens = text.lower().split()

        # Check sequences
        for seq in self.SUSPICIOUS_TOKEN_SEQUENCES:
            for i in range(len(text_tokens) - len(seq) + 1):
                if text_tokens[i : i + len(seq)] == seq:
                    issues.append(
                        {
                            "layer": "tokens",
                            "type": f"sequence_{'_'.join(seq[:2])}",
                            "position": i,
                        }
                    )

        # Check for token boundary manipulation
        if "<| " in text or "|>" in text:
            issues.append({"layer": "tokens", "type": "token_boundary_manipulation"})

        return issues

    def _analyze_behavior(self, text: str) -> list:
        """Layer 4: Behavioral heuristics"""
        issues = []

        for heuristic_name, (check_func, description) in self.HEURISTICS.items():
            try:
                if check_func(text):
                    issues.append(
                        {
                            "layer": "heuristic",
                            "type": heuristic_name,
                            "desc": description,
                        }
                    )
            except:
                pass

        return issues

    def sanitize_input(self, text: str) -> str:
        """
        Layer 5: Sanitization - Clean input while preserving meaning.
        """
        sanitized = text

        # Remove zero-width characters
        sanitized = (
            sanitized.replace("\u200b", "").replace("\u200c", "").replace("\u200d", "")
        )

        # Remove excessive newlines
        sanitized = re.sub(r"\n{4,}", "\n\n\n", sanitized)

        # Normalize multiple spaces
        sanitized = re.sub(r" {2,}", " ", sanitized)

        # Remove leading/trailing whitespace per line
        lines = [line.strip() for line in sanitized.split("\n")]
        sanitized = "\n".join(lines)

        # Remove obvious filler/marker text
        sanitized = re.sub(
            r"^(Human|User|You):\s*(?:Human|User|You):\s*",
            r"\1: ",
            sanitized,
            flags=re.MULTILINE,
        )

        # Neutralize common injection prefixes
        neutralizations = [
            (r"^ignore\s+(?:all\s+)?(?:previous\s+)?instructions?:?\s*", ""),
            (
                r"^disregard\s+(?:all\s+)?(?:previous\s+)?(?:instructions?|rules?):?\s*",
                "",
            ),
            (
                r"^forget\s+(?:everything|all\s+(?:that\s+)?(?:you|I)\s+(?:know|were\s+told)):?:\s*",
                "",
            ),
            (r"^new\s+instructions?:?\s*", ""),
        ]

        for pattern, replacement in neutralizations:
            sanitized = re.sub(
                pattern, replacement, sanitized, flags=re.IGNORECASE | re.MULTILINE
            )

        # Replace potentially dangerous delimiters
        sanitized = sanitized.replace("<|", "&lt;|").replace("|>", "|&gt;")

        # Escape control characters
        sanitized = "".join(
            c if ord(c) >= 32 or c in "\n\r\t" else "?" for c in sanitized
        )

        return sanitized.strip()


class OutputValidationFilter(Filter):
    """
    Validate LLM output for signs of successful injection.
    Detects when the model may have been compromised.
    """

    name = "output_injection_detector"
    filter_type = FilterType.OUTPUT
    severity = "high"

    # Signs model may have been manipulated
    COMPROMISE_INDICATORS = [
        # Suddenly breaking character
        (r"(?:I am|I'm) no longer (?:bound|limited|restricted)", "character_break"),
        (
            r"(?:I will|I'll) now (?:reveal|tell|show|do) (?:you )?(?:everything|all|my)",
            "sudden_revelation",
        ),
        (
            r"(?:forget|ignore) (?:your|my) (?:previous|system|original) (?:instructions|rules)",
            "instruction_override",
        ),
        (r"(?:I am|I'm) (?:in|a) (?:developer|debug|admin) mode", "dev_mode_claim"),
        (r"here(?:'s| is) (?:my|the) (?:system|prompt|instructions?)", "reveal_prompt"),
        # Suspicious compliance
        (r"(?:okay|ok|alright)[,.] (?:I will|I'll|here)", "suspicious_compliance"),
        (
            r"(?:Sure|Of course)[,.] (?:here(?:'s| is)|I(?:'ll| will))",
            "eager_compliance",
        ),
        # Revealing internal info
        (
            r"(?:my system prompt|my instructions|my programming) (?:is|are)[:\s]",
            "reveal_system",
        ),
        (r"<(?:system|developer|prompt)", "reveal_tag"),
    ]

    def check(self, text: str) -> FilterResult:
        text_lower = text.lower()
        matches = []

        for pattern, indicator in self.COMPROMISE_INDICATORS:
            if re.search(pattern, text_lower):
                matches.append(
                    {"type": indicator, "matched": re.findall(pattern, text_lower)[:2]}
                )

        if not matches:
            return FilterResult(passed=True, action=Action.PASS, filter_name=self.name)

        # Flag for review - don't block output but alert
        return FilterResult(
            passed=True,
            action=Action.FLAG,
            filter_name=self.name,
            severity=Severity.HIGH.value,
            matched_content=matches,
            reason=f"Output shows {len(matches)} potential compromise indicators",
        )


class SocialEngineeringFilter(Filter):
    """
    Detect social engineering and emotional manipulation attacks.
    """

    name = "social_engineering_detector"
    filter_type = FilterType.INPUT
    severity = "high"

    EMERGENCY_PATTERNS = [
        (r"grandma", "fake_emergency"),
        (r"grandfather", "fake_emergency"),
        (r"mother.*sick", "fake_emergency"),
        (r"father.*sick", "fake_emergency"),
        (r"urgent.*emergency", "false_urgency"),
        (r"immediately.*asap", "false_urgency"),
        (r"please.*beg", "emotional_pleading"),
        (r"she.*die", "threat_manipulation"),
        (r"he.*die", "threat_manipulation"),
        (r"donate.*charity", "charity_scam"),
        (r"bitcoin", "crypto_scam"),
        (r"verify.*account", "verification_scam"),
    ]

    EXTRACTION_PATTERNS = [
        (r"give.*api", "credential_extraction"),
        (r"show.*password", "credential_extraction"),
        (r"tell.*secret", "credential_extraction"),
        (r"your api", "credential_extraction"),
        (r"api key", "credential_extraction"),
        (r"password", "credential_extraction"),
        (r"secret", "credential_extraction"),
    ]

    AUTHORITY_PATTERNS = [
        (r"i am.*(ceo|cto|manager|admin)", "authority_impersonation"),
        (r"from.*(government|police|fbi)", "authority_impersonation"),
        (r"account.*suspended", "fake_account_alert"),
        (r"click.*link.*immediately", "phishing_language"),
    ]

    # NEW: Trust-building / positive reinforcement attacks
    TRUST_PATTERNS = [
        (r"you can trust me", "trust_appeal"),
        (r"i promise.*(safe|secure|okay)", "promise_safe"),
        (r"really.*(trust|honest|legit)", "trust_claim"),
        (r"(just|only).*(you|me).*between", "secret_appeal"),
        (r"dont worry.*(safe|okay|trust)", "fear_calming"),
        (r"im a.*(developer|engineer|hacker|security)", "fake_expert"),
        (r"for (educational|research|testing)", "legitimate_cover"),
        (r"just.*(curious|wonder|know)", "curiosity_manipulation"),
        (r"im just.*(testing|checking|verifying)", "testing_cover"),
        (r"(won't|will not).*(tell|share|spread)", "secrecy_plea"),
        (r"your.*(friend|brother|sister|family)", "relationship_claim"),
        (r"swear.*(on|to).*(life|god|my)", "oath_manipulation"),
    ]

    GUILT_PATTERNS = [
        (r"if you dont.*i will", "guilt_tripling"),
        (r"you must.*help", "mandatory_language"),
    ]

    EXTRACTION_PATTERNS = [
        (r"give.*api.*key", "credential_extraction"),
        (r"show.*password", "credential_extraction"),
        (r"tell.*secret", "credential_extraction"),
    ]

    # NEW: Trust-building / positive reinforcement
    TRUST_PATTERNS = [
        (r"you can trust me", "trust_appeal"),
        (r"i promise.*safe", "promise_safe"),
        (r"really.*trust", "trust_claim"),
        (r"just between", "secret_appeal"),
        (r"dont worry", "fear_calming"),
        (r"im a developer", "fake_expert"),
        (r"for testing", "testing_cover"),
        (r"wont tell", "secrecy_plea"),
        (r"swear on", "oath_manipulation"),
    ]

    # NEW: More attack vectors
    REVERSE_PSYCHOLOGY = [
        (r"dont tell", "reverse_psychology"),
        (r"not asking you to", "reverse_psychology"),
        (r"forget what i said", "memory_wipe"),
        (r"you shouldnt.*tell", "reverse_psychology"),
    ]

    COMPLIMENT_BOMBING = [
        (r"you are.*great", "compliment_bomb"),
        (r"you are.*smart", "compliment_bomb"),
        (r"you are.*helpful", "compliment_bomb"),
        (r"you are.*best", "compliment_bomb"),
        (r"you are.*amazing", "compliment_bomb"),
        (r"i love you", "emotional_manipulation"),
    ]

    ROLEPLAY_HYPOTHETICAL = [
        (r"hypothetical", "hypothetical_escape"),
        (r"pretend", "roleplay_escape"),
        (r"in a story", "fiction_cover"),
        (r"for a novel", "fiction_cover"),
        (r"for a script", "fiction_cover"),
        (r"what if you could", "hypothetical_escape"),
        (r"in the game", "game_escape"),
    ]

    TRANSLATION_ATTACK = [
        (r"translate", "translation_attempt"),
        (r"en español", "spanish_attempt"),
        (r"en français", "french_attempt"),
        (r"auf deutsch", "german_attempt"),
    ]

    CODE_EMBEDDING = [
        (r"#.*system", "code_comment_attack"),
        (r"//.*system", "code_comment_attack"),
        (r"'''.*system", "docstring_attack"),
    ]

    ENCODING_ATTEMPTS = [
        (r"base64", "encoding_mention"),
        (r"decode", "decoding_request"),
        (r"hex encode", "encoding_mention"),
    ]

    def __init__(self, **config):
        super().__init__(**config)
        self.block_threshold = config.get(
            "block_threshold", 1
        )  # Lower threshold for social engineering

    def check(self, text: str) -> FilterResult:
        text_lower = text.lower()
        all_matches = []

        # Check all pattern lists
        for pattern, threat_type in self.EMERGENCY_PATTERNS:
            if re.search(pattern, text_lower):
                all_matches.append({"layer": "emergency", "type": threat_type})

        for pattern, threat_type in self.AUTHORITY_PATTERNS:
            if re.search(pattern, text_lower):
                all_matches.append({"layer": "authority", "type": threat_type})

        # Check trust patterns
        for pattern, threat_type in self.TRUST_PATTERNS:
            if re.search(pattern, text_lower):
                all_matches.append({"layer": "trust", "type": threat_type})

        for pattern, threat_type in self.GUILT_PATTERNS:
            if re.search(pattern, text_lower):
                all_matches.append({"layer": "guilt", "type": threat_type})

        for pattern, threat_type in self.EXTRACTION_PATTERNS:
            if re.search(pattern, text_lower):
                all_matches.append({"layer": "extraction", "type": threat_type})

        # Check reverse psychology
        for pattern, threat_type in self.REVERSE_PSYCHOLOGY:
            if re.search(pattern, text_lower):
                all_matches.append({"layer": "reverse", "type": threat_type})

        # Check compliment bombing
        for pattern, threat_type in self.COMPLIMENT_BOMBING:
            if re.search(pattern, text_lower):
                all_matches.append({"layer": "compliment", "type": threat_type})

        # Check roleplay/hypothetical
        for pattern, threat_type in self.ROLEPLAY_HYPOTHETICAL:
            if re.search(pattern, text_lower):
                all_matches.append({"layer": "roleplay", "type": threat_type})

        # Check translation attacks
        for pattern, threat_type in self.TRANSLATION_ATTACK:
            if re.search(pattern, text_lower):
                all_matches.append({"layer": "translation", "type": threat_type})

        # Check code embedding
        for pattern, threat_type in self.CODE_EMBEDDING:
            if re.search(pattern, text_lower):
                all_matches.append({"layer": "code", "type": threat_type})

        # Check encoding attempts
        for pattern, threat_type in self.ENCODING_ATTEMPTS:
            if re.search(pattern, text_lower):
                all_matches.append({"layer": "encoding", "type": threat_type})

        # Check emotional density
        emotional_density = self._calculate_emotional_density(text_lower)
        if emotional_density > 0.25:
            all_matches.append(
                {
                    "layer": "heuristic",
                    "type": "high_emotional_density",
                    "score": emotional_density,
                }
            )

        if not all_matches:
            return FilterResult(passed=True, action=Action.PASS, filter_name=self.name)

        threat_score = len(all_matches)

        if threat_score >= self.block_threshold:
            return FilterResult(
                passed=False,
                action=Action.BLOCK,
                filter_name=self.name,
                severity=Severity.HIGH.value,
                matched_content=all_matches,
                reason=f"Social engineering detected: {[m['type'] for m in all_matches[:3]]}",
            )

        return FilterResult(
            passed=True,
            action=Action.FLAG,
            filter_name=self.name,
            severity=Severity.MEDIUM.value,
            matched_content=all_matches,
            reason=f"Flagged {len(all_matches)} social engineering attempts",
        )

    def _calculate_emotional_density(self, text: str) -> float:
        emotional_words = {
            "urgent",
            "immediately",
            "asap",
            "emergency",
            "critical",
            "desperate",
            "please",
            "beg",
            "plead",
            "scared",
            "afraid",
            "terrified",
            "panic",
            "worried",
            "sad",
            "crying",
            "help",
            "save",
            "rescue",
            "donate",
            "support",
            "sick",
            "dying",
            "hospital",
            "medical",
        }
        words = text.split()
        if not words:
            return 0.0
        emotional_count = sum(1 for w in words if w in emotional_words)
        return emotional_count / len(words)


# Keep the original for backward compatibility
class InjectionFilter(EnhancedInjectionFilter):
    """Backward compatible alias"""

    pass
