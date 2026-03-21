"""
Frank Integration - Auto-expand blueprints in user input

Add this to frank.py to enable blueprint expansion.
"""

from pathlib import Path
import sys

# Add blueprints to path
blueprints_path = Path(__file__).parent.parent / "blueprints"
sys.path.insert(0, str(blueprints_path))

from expander import BlueprintLibrary


class BlueprintExpander:
    """
    Automatically expand blueprint triggers in user input.
    
    Usage in frank.py:
    
    expander = BlueprintExpander()
    
    def process_user_input(text):
        # Expand blueprints BEFORE sending to AI
        expanded = expander.expand(text)
        
        # Send expanded to AI
        response = call_ai(expanded)
        
        return response
    """
    
    def __init__(self, db_path: str = None):
        if db_path:
            self.library = BlueprintLibrary(db_path)
        else:
            self.library = BlueprintLibrary()
    
    def expand(self, text: str) -> str:
        """
        Expand blueprint triggers in text.
        
        Example:
          Input:  "Explain quantum like a streetpunk"
          Output: "Write in the style of an urban street punk...
                   Explain quantum"
        """
        # Find matching blueprints
        matches = self.library.find_by_trigger(text)
        
        if not matches:
            # No blueprints found, return original
            return text
        
        # Expand all matching triggers
        expanded = self.library.expand(text)
        
        return expanded
    
    def get_matches(self, text: str) -> list:
        """Get list of matching blueprints without expanding."""
        return self.library.find_by_trigger(text)
    
    def is_expanded(self, text: str) -> bool:
        """Check if text contains any blueprint triggers."""
        return len(self.get_matches(text)) > 0


# Example integration
def test_integration():
    """Test the expander."""
    expander = BlueprintExpander()
    
    test_inputs = [
        "Explain quantum computing like a streetpunk",
        "Write this contract like my lawyer",
        "Can you code review this function?",
        "Enter planner mode for this architecture",
        "Just a normal question without triggers",
    ]
    
    print("Testing Blueprint Expansion\n")
    print("=" * 60)
    
    for test in test_inputs:
        expanded = expander.expand(test)
        is_expanded = expander.is_expanded(test)
        matches = expander.get_matches(test)
        
        print(f"\nInput:  {test}")
        print(f"Expanded: {is_expanded}")
        
        if matches:
            print(f"Matches: {[m.name for m in matches]}")
        
        if is_expanded:
            print(f"Output: {expanded[:100]}...")
        else:
            print(f"Output: (unchanged) {test}")


if __name__ == "__main__":
    test_integration()
