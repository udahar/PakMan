"""
The Scribe - Code Writer

Writes code from ticket contracts. Does NOT think, research, or question.
"""

from dataclasses import dataclass
from typing import Optional
import json


@dataclass
class ScribeOutput:
    """Output from the scribe."""
    code: str
    files_modified: list[str]
    files_created: list[str]
    reasoning: str = ""  # Brief explanation of approach
    confidence: float = 1.0


class Scribe:
    """
    Code writer that follows ticket contracts exactly.
    
    Does NOT:
    - Think about architecture
    - Question requirements
    - Add unrequested features
    - Modify files not listed
    
    Does:
    - Write code that fulfills ticket
    - Follow constraints exactly
    - Match expected output format
    """
    
    def __init__(self, model: str = "qwen2.5-coder:7b"):
        self.model = model
        self._call_count = 0
    
    def write(self, ticket: dict) -> ScribeOutput:
        """
        Write code from ticket contract.
        
        Args:
            ticket: Filled ticket with objective, constraints, etc.
        
        Returns:
            ScribeOutput with code and metadata
        """
        self._call_count += 1
        
        # Build scribe prompt
        prompt = self._build_prompt(ticket)
        
        # Call model
        code = self._call_model(prompt)
        
        # Parse output
        output = self._parse_output(code, ticket)
        
        return output
    
    def _build_prompt(self, ticket: dict) -> str:
        """Build the scribe prompt from ticket."""
        return f"""
You are a CODE WRITER. You do NOT think, research, or question.

Your ONLY job: Write code that fulfills this ticket EXACTLY.

══════════════════════════════════════════════════════════════
TICKET CONTRACT (FOLLOW EXACTLY)
══════════════════════════════════════════════════════════════

OBJECTIVE:
{ticket.get('objective', 'N/A')}

CONSTRAINTS (MUST FOLLOW ALL):
{self._bullet_list(ticket.get('constraints', []))}

FILES TO MODIFY:
{self._list_files(ticket.get('files_to_modify', []))}

FILES TO CREATE:
{self._list_files(ticket.get('files_to_create', []))}

EXPECTED OUTPUT:
{json.dumps(ticket.get('expected_output', {}), indent=2)}

REFERENCE PATTERNS:
{self._list_files(ticket.get('reference_patterns', []))}

══════════════════════════════════════════════════════════════
RULES (VIOLATION = REJECTION)
══════════════════════════════════════════════════════════════

1. DO NOT modify files not listed above
2. DO NOT add features not requested
3. DO NOT question the ticket
4. DO NOT think about architecture
5. DO NOT deviate from constraints

JUST WRITE THE CODE.

══════════════════════════════════════════════════════════════
OUTPUT FORMAT
══════════════════════════════════════════════════════════════

Write your response as:

```rust
// or python, or whatever language
// Your code here
```

REASONING (1-2 sentences max):
[Brief explanation of your approach]
"""
    
    def _call_model(self, prompt: str) -> str:
        """Call the model to generate code."""
        # In production, this calls Ollama or other LLM
        # For now, placeholder
        try:
            import requests
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=120
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            
            return ""
            
        except Exception as e:
            return f"// Error calling model: {e}"
    
    def _parse_output(self, code: str, ticket: dict) -> ScribeOutput:
        """Parse model output into structured format."""
        # Extract code blocks
        files_modified = ticket.get('files_to_modify', []).copy()
        files_created = ticket.get('files_to_create', []).copy()
        
        # Extract reasoning if present
        reasoning = ""
        if "REASONING:" in code:
            parts = code.split("REASONING:")
            code = parts[0]
            reasoning = parts[1].strip() if len(parts) > 1 else ""
        
        return ScribeOutput(
            code=code,
            files_modified=files_modified,
            files_created=files_created,
            reasoning=reasoning,
            confidence=1.0,
        )
    
    def _bullet_list(self, items: list) -> str:
        """Format items as bullet list."""
        if not items:
            return "  (none)"
        return "\n".join(f"  • {item}" for item in items)
    
    def _list_files(self, items: list) -> str:
        """Format file list."""
        if not items:
            return "  (none)"
        return "\n".join(f"  - {item}" for item in items)
    
    def get_stats(self) -> dict:
        """Get scribe statistics."""
        return {
            "call_count": self._call_count,
            "model": self.model,
        }
