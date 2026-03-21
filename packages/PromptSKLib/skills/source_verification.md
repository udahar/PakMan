# Skill: Source Verification

**skill_id:** `source_verification_001`  
**name:** source_verification  
**category:** inquiry  
**version:** 1.0  

## Description

Cross-references information across multiple sources to verify accuracy and identify potential misinformation.

## Primitive Tags

- cross_reference
- verify_claims
- check_consistency
- flag_contradictions
- assess_credibility

## Prompt Strategy

```
For verifying information:

1. COLLECT SOURCES
   - Gather all available sources on topic
   - Note source type (internal DB, web, documentation)
   
2. EXTRACT CLAIMS
   - Identify key factual claims from each source
   - Create claim comparison table
   
3. CROSS-REFERENCE
   - Check if claims agree across sources
   - Note timestamps (prefer recent sources)
   - Assess source credibility
   
4. REPORT VERIFICATION
   - Verified claims (multiple sources agree)
   - Disputed claims (sources contradict)
   - Unverified claims (single source only)
   - Confidence assessment
```

## Solution Summary

```python
async def verify_sources(sources: list) -> dict:
    claims = extract_claims_from_sources(sources)
    
    verification = {
        "verified": [],      # 3+ sources agree
        "likely_true": [],   # 2 sources agree
        "disputed": [],      # Sources contradict
        "unverified": [],    # Single source claim
        "confidence": {}     # Per-claim confidence
    }
    
    for claim in claims:
        supporting = count_supporting_sources(claim, sources)
        contradicting = count_contradicting_sources(claim, sources)
        
        if supporting >= 3:
            verification["verified"].append(claim)
        elif supporting >= 2 and contradicting == 0:
            verification["likely_true"].append(claim)
        elif contradicting > 0:
            verification["disputed"].append({
                "claim": claim,
                "supporting": supporting,
                "contradicting": contradicting
            })
        else:
            verification["unverified"].append(claim)
    
    return verification
```

## Tests Passed

- [x] Identifies consensus across sources
- [x] Flags contradictory information
- [x] Reports confidence levels

## Failure Modes

- **Echo chamber**: Multiple sources repeat same error
  - Mitigation: Check source independence
- **Outdated consensus**: Old information widely repeated
  - Mitigation: Weight recent sources higher

## Timestamp

2026-03-08
