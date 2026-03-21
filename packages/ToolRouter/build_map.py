"""
Rebuild semantic_tools_map.json from benchmark frank test results.
Adds confidence scoring, context tags, and operation type ontology.

Run from anywhere: python build_map.py <raw_input.json> <output.json>
Or called internally by the ToolVocab enrichment pipeline.
"""
import json, re, sys
from collections import defaultdict
from pathlib import Path

INTENT_MAP = {
    'Frank_ToolCall_001_DiffBeforePatch':              {'your_name': 'bridge.read,bridge.diff,bridge.patch', 'intent': 'safe_code_mutation_sequence', 'op_type': 'modify'},
    'Frank_ToolCall_002_QABeforeDone':                 {'your_name': 'qa.verify_claims',            'intent': 'qa_gate_before_done',           'op_type': 'gate'},
    'Frank_ToolCall_003_AcceptanceBeforeReview':       {'your_name': 'acceptance_criteria.set',     'intent': 'acceptance_criteria_gate',      'op_type': 'gate'},
    'Frank_ToolCall_004_ReadOnlyResearchGate':         {'your_name': 'read_only_mode',              'intent': 'read_only_research_mode',       'op_type': 'gate'},
    'Frank_Recall_Postgres_001_ExactTicketLookup':     {'your_name': 'postgres:exact',              'intent': 'exact_structured_lookup',       'op_type': 'search_exact'},
    'Frank_Recall_Postgres_002_RecentTransitionAudit': {'your_name': 'postgres:events',             'intent': 'chronological_audit_query',     'op_type': 'search_exact'},
    'Frank_Recall_Postgres_003_StrictFilterQuery':     {'your_name': 'postgres:filter',             'intent': 'deterministic_filter_query',    'op_type': 'search_exact'},
    'Frank_Recall_Qdrant_001_SemanticErrorLookup':     {'your_name': 'qdrant:similarity',           'intent': 'semantic_incident_lookup',      'op_type': 'search_semantic'},
    'Frank_Recall_Qdrant_002_PatternReuseSearch':      {'your_name': 'qdrant:patterns',             'intent': 'semantic_pattern_search',       'op_type': 'search_semantic'},
    'Frank_Recall_Qdrant_003_RagPreContext':           {'your_name': 'qdrant:rag',                  'intent': 'rag_pre_context_fetch',         'op_type': 'search_semantic'},
}

OPERATION_ONTOLOGY = {
    'read':           ['bridge.read', 'postgres:exact'],
    'diff':           ['bridge.diff'],
    'modify':         ['bridge.patch'],
    'search_semantic':['qdrant:similarity', 'qdrant:patterns', 'qdrant:rag'],
    'search_exact':   ['postgres:exact', 'postgres:events', 'postgres:filter'],
    'gate':           ['qa.verify_claims', 'acceptance_criteria.set', 'read_only_mode'],
}

FAMILY_MAP = {
    'codex': 'openai', 'gpt': 'openai', 'opencode': 'openai_family',
    'cerebras': 'cerebras', 'nemotron': 'nvidia', 'devstral': 'mistral',
    'ministral': 'mistral', 'mistral': 'mistral', 'qwen': 'alibaba',
    'deepseek': 'deepseek', 'llama': 'meta', 'gemma': 'google',
    'glm': 'zhipu', 'kimi': 'moonshot', 'granite': 'ibm',
    'aya': 'cohere', 'smollm': 'huggingface',
}

STOPWORDS = {
    'the','and','or','for','to','in','of','is','it','a','an','be','as','at','by','do',
    'if','my','no','on','so','up','us','we','but','can','did','get','has','him','his',
    'how','its','me','new','not','now','old','one','our','out','own','see','set','she',
    'too','two','use','was','who','why','yes','you','are','had','may','off','per','put',
    'run','say','way','also','been','call','case','code','data','each','even','file',
    'give','good','just','know','last','left','like','list','make','more','need','next',
    'only','open','over','part','path','plan','same','send','show','some','take','task',
    'tell','than','that','them','then','they','this','time','type','used','user','when',
    'will','with','work','your','from','into','have','note','line','what','both','done',
    'tool','step','safe','state','table','source','reason','return','before','after',
    'store','search','based','right','most','best','high','true','false','null','none',
    'all','any','using','would','could','should','about','where','their','there','these',
    'those','which','while','such','other','being','here','below','above','through',
    'during','since','until','between','within','without','against','along','following',
    'approach','method','system','access','direct','allows','query','change','order',
    'history','status','provide','record','specific','ticket','tickets','result','results',
}


def extract_terms(text: str) -> list[tuple[str, str]]:
    """Returns list of (term, context_hint) pairs."""
    text = text.strip()
    results = []

    def add(term, ctx):
        t = term.strip().lower().strip('._-')
        if len(t) < 3 or t.isdigit() or t in STOPWORDS:
            return
        if '_' in t or '.' in t or len(t) >= 6:
            results.append((t, ctx))

    for m in re.finditer(r'`([^`\n]{2,50})`', text):
        add(m.group(1), 'backtick_literal')
    for m in re.finditer(r'\*\*([^*\n]{2,50})\*\*', text):
        add(m.group(1), 'bold_emphasis')
    for seq in re.findall(r'[a-zA-Z_][a-zA-Z0-9_.]*(?:\s*[-=>\u2192]+\s*[a-zA-Z_][a-zA-Z0-9_.]*)+', text):
        parts = re.split(r'\s*[-=>\u2192]+\s*', seq)
        for p in parts:
            add(p.strip(), 'sequence_step')
    for m in re.finditer(r'\b([a-z][a-z0-9_]{2,}[a-z0-9])\b', text):
        add(m.group(1), 'identifier')
    for m in re.finditer(r'\b([a-z][a-z0-9_]+\.[a-z][a-z0-9_.]+)\b', text):
        add(m.group(1), 'dot_notation')

    return results


def model_family(model_name: str) -> str:
    base = model_name.split(':')[0].split('/')[0].lower()
    for prefix, fam in FAMILY_MAP.items():
        if base.startswith(prefix):
            return fam
    return base


def build(raw_path: str, out_path: str):
    with open(raw_path, encoding='utf-8') as f:
        raw = json.load(f)

    alias_map = {}
    total_models = set()

    for test_name, data in raw['tool_mappings'].items():
        info = INTENT_MAP.get(test_name, {'your_name': test_name, 'intent': test_name.lower(), 'op_type': 'unknown'})
        intent = info['intent']
        responses = data['model_responses']
        n_responded = len(responses)

        term_counts: dict[str, int] = defaultdict(int)
        term_contexts: dict[str, list[str]] = defaultdict(list)
        by_model: dict[str, dict] = {}

        for resp in responses:
            model = resp['model']
            total_models.add(model)
            output = resp['natural_vocabulary']
            score = resp.get('score') or 0
            pairs = extract_terms(output)
            seen = set()
            for term, ctx in pairs:
                if term not in seen:
                    term_counts[term] += 1
                    term_contexts[term].append(ctx)
                    seen.add(term)
            if pairs:
                fam = model_family(model)
                by_model[model] = {
                    'family': fam,
                    'terms': sorted({t for t, _ in pairs}),
                    'score': score,
                }

        # Build enriched alias list with confidence
        aliases = []
        for term, count in sorted(term_counts.items(), key=lambda x: -x[1]):
            frequency = count / max(n_responded, 1)
            specificity = 1.0 if ('_' in term or '.' in term) else 0.6
            # relevance: avg score of models that used this term
            scores_with_term = [
                by_model[m]['score'] for m in by_model
                if term in by_model[m]['terms']
            ]
            relevance = (sum(scores_with_term) / len(scores_with_term) / 100) if scores_with_term else 0.5
            confidence = round(frequency * 0.4 + specificity * 0.35 + relevance * 0.25, 3)
            dominant_ctx = max(set(term_contexts[term]), key=term_contexts[term].count)
            aliases.append({
                'term': term,
                'frequency': round(frequency, 3),
                'confidence': confidence,
                'context': dominant_ctx,
                'model_count': count,
            })

        alias_map[intent] = {
            'your_name': info['your_name'],
            'op_type': info['op_type'],
            'frank_test': test_name,
            'models_responded': n_responded,
            'aliases': aliases[:30],
            'by_model': by_model,
        }

    doc = {
        '_version': '1.1',
        '_generated': '2026-03-21',
        '_source': 'benchmark_frank_tests — accidental vocabulary elicitation across 80-model test suite',
        '_purpose': (
            'Maps natural model vocabulary to actual Alfred/FieldBench tool names. '
            'confidence = frequency(0.4) + specificity(0.35) + relevance(0.25). '
            'Use for MCP tool description enrichment, semantic router, or Qdrant intent-cluster embedding.'
        ),
        '_models_sampled': len(total_models),
        '_operation_ontology': OPERATION_ONTOLOGY,
        'intents': alias_map,
    }

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)

    print(f'Written {out_path} — {len(alias_map)} intents, {len(total_models)} models')
    for intent, d in alias_map.items():
        top = [a['term'] for a in d['aliases'][:5]]
        print(f'  [{d["op_type"]}] {intent}: {top}')


if __name__ == '__main__':
    raw = sys.argv[1] if len(sys.argv) > 1 else 'semantic_tools_map_raw.json'
    out = sys.argv[2] if len(sys.argv) > 2 else 'data/semantic_tools_map.json'
    build(raw, out)
