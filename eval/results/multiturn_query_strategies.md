# Multi-turn query strategy evaluation

All query strategies use the same frozen lexical Top20 + semantic Top20 candidate union and Cross-Encoder reranker.

## Configuration

- Provider: `openai-compatible-chat-completions`
- Base URL: `https://api.deepseek.com`
- Model: `deepseek-v4-flash`
- History window: 2 turns
- Prompt version: `contextual-query-rewrite-v1`

## Metrics

- latest_only: Hit@1=0.5000, Hit@3=0.7500, Hit@5=1.0000, MRR=0.6875
- raw_concat: Hit@1=0.2500, Hit@3=0.5000, Hit@5=0.7500, MRR=0.4688
- llm_rewrite: Hit@1=0.7500, Hit@3=1.0000, Hit@5=1.0000, MRR=0.8750
- oracle: Hit@1=0.7500, Hit@3=1.0000, Hit@5=1.0000, MRR=0.8750

## Rewrite API/cache usage

- API calls: 4
- Cache hits: 0
- Cache misses: 4
- Errors: 0

## Per-case ranks

### multi_001

- Latest: What happens to the forks?
- LLM rewrite: What happens to forks when GitHub removes private information from a repository under its Private Information Removal Policy?
- Oracle: What happens to forks when a parent repository is disabled under GitHub's Private Information Removal Policy?
- Ranks: latest_only=2, raw_concat=8, llm_rewrite=1, oracle=1

### multi_002

- Latest: Can I challenge that decision?
- LLM rewrite: Can a GitHub user challenge a decision to restrict content or disable access to an account or service for a policy violation?
- Oracle: Can a user appeal GitHub's decision to restrict content or disable an account for an alleged policy violation?
- Ranks: latest_only=1, raw_concat=4, llm_rewrite=1, oracle=1

### multi_003

- Latest: What does it gather automatically?
- LLM rewrite: What personal data does GitHub automatically collect from users?
- Oracle: What personal data does GitHub collect automatically from a user's device or use of the services?
- Ranks: latest_only=1, raw_concat=2, llm_rewrite=2, oracle=2

### multi_004

- Latest: What if it is for security research?
- LLM rewrite: Does GitHub's prohibition on using the platform in direct support of unlawful attacks that cause technical harm apply to security research?
- Oracle: Does GitHub allow dual-use vulnerability, malware, or exploit content when it is posted for security research?
- Ranks: latest_only=4, raw_concat=1, llm_rewrite=1, oracle=1
