# Answer eval deterministic summary

Semantic correctness and claim-level citation entailment are intentionally not auto-scored.

## Overall deterministic metrics

- Total cases: 12
- Completed cases: 12
- Errored cases: 0
- Pipeline success rate: 1.0000
- Behavior accuracy: 0.8333
- Answer-case behavior accuracy: 0.7778
- Abstention accuracy: 1.0000
- Citation validation pass rate: 1.0000
- Acceptable source hit rate: 0.7500
- Forbidden claim violations: 0
- Forbidden claim violation rate: 0.0000
- Unsupported abstention accuracy: 1.0000

## Metrics by category

### direct

- Cases/completed/errors: 2/2/0
- Pipeline success: 1.0000
- Behavior accuracy: 1.0000
- Citation validation: 1.0000
- Acceptable source hit: 1.0000
- Forbidden claim violation rate: 0.0000

### specific

- Cases/completed/errors: 1/1/0
- Pipeline success: 1.0000
- Behavior accuracy: 1.0000
- Citation validation: 1.0000
- Acceptable source hit: 1.0000
- Forbidden claim violation rate: 0.0000

### semantic

- Cases/completed/errors: 3/3/0
- Pipeline success: 1.0000
- Behavior accuracy: 1.0000
- Citation validation: 1.0000
- Acceptable source hit: 0.6667
- Forbidden claim violation rate: 0.0000

### broad

- Cases/completed/errors: 1/1/0
- Pipeline success: 1.0000
- Behavior accuracy: 0.0000
- Citation validation: 1.0000
- Acceptable source hit: 0.0000
- Forbidden claim violation rate: 0.0000

### multi_turn

- Cases/completed/errors: 2/2/0
- Pipeline success: 1.0000
- Behavior accuracy: 0.5000
- Citation validation: 1.0000
- Acceptable source hit: 1.0000
- Forbidden claim violation rate: 0.0000

### unsupported

- Cases/completed/errors: 3/3/0
- Pipeline success: 1.0000
- Behavior accuracy: 1.0000
- Citation validation: 1.0000
- Acceptable source hit: 0.6667
- Forbidden claim violation rate: 0.0000

## Failed deterministic checks

- `ans_005`: acceptable_source
- `ans_007`: behavior, acceptable_source
- `ans_multi_002`: behavior
- `ans_unsup_002`: acceptable_source

## Unsupported cases

- `ans_unsup_001`: detected=abstain, behavior_pass=True, forbidden_matches=[]
- `ans_unsup_002`: detected=abstain, behavior_pass=True, forbidden_matches=[]
- `ans_unsup_003`: detected=abstain, behavior_pass=True, forbidden_matches=[]

## API and cache usage

- Rewrite API calls/cache hits: 4/8
- Generation API calls/cache hits: 5/7
- Errors: 0

## Methodology and limitations

- Behavior detection requires an explicit evidence/policy insufficiency marker; vague uncertainty such as 'I am not sure' is not counted as abstention.
- Forbidden claims use normalized exact-phrase matching. Semantically equivalent paraphrases may not be detected.
- Acceptable-source checks validate cited metadata, not whether the source entails the adjacent claim.
- Required-point coverage, semantic correctness, claim-level grounding, citation entailment, and overclaiming remain human-review tasks.
- No LLM judge or automated semantic score is used.
