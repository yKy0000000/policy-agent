# Multi-turn rewrite review

This file is for human comparison only; no LLM-generated quality score is included.

## multi_001

### History

- **User:** How does GitHub handle requests to remove private information from a repository?
- **Assistant:** GitHub's Private Information Removal Policy describes how it reviews reports and may disable qualifying content.

### Queries

- **Latest question:** What happens to the forks?
- **LLM rewrite:** What happens to forks when GitHub removes private information from a repository under its Private Information Removal Policy?
- **Oracle reference:** What happens to forks when a parent repository is disabled under GitHub's Private Information Removal Policy?

### Retrieval ranks

- **latest_only:** 2
- **raw_concat:** 8
- **llm_rewrite:** 1
- **oracle:** 1

---

## multi_002

### History

- **User:** What can GitHub do if it decides that my content or account violates a policy?
- **Assistant:** Depending on the circumstances, GitHub may restrict content or disable access to an account or service.

### Queries

- **Latest question:** Can I challenge that decision?
- **LLM rewrite:** Can a GitHub user challenge a decision to restrict content or disable access to an account or service for a policy violation?
- **Oracle reference:** Can a user appeal GitHub's decision to restrict content or disable an account for an alleged policy violation?

### Retrieval ranks

- **latest_only:** 1
- **raw_concat:** 4
- **llm_rewrite:** 1
- **oracle:** 1

---

## multi_003

### History

- **User:** What personal data does GitHub collect from users?
- **Assistant:** The Privacy Statement separates data provided directly, collected automatically, and received from third parties.

### Queries

- **Latest question:** What does it gather automatically?
- **LLM rewrite:** What personal data does GitHub automatically collect from users?
- **Oracle reference:** What personal data does GitHub collect automatically from a user's device or use of the services?

### Retrieval ranks

- **latest_only:** 1
- **raw_concat:** 2
- **llm_rewrite:** 2
- **oracle:** 2

---

## multi_004

### History

- **User:** Does GitHub prohibit repositories that support malware or exploit campaigns?
- **Assistant:** GitHub prohibits using the platform in direct support of unlawful attacks that cause technical harm.

### Queries

- **Latest question:** What if it is for security research?
- **LLM rewrite:** Does GitHub's prohibition on using the platform in direct support of unlawful attacks that cause technical harm apply to security research?
- **Oracle reference:** Does GitHub allow dual-use vulnerability, malware, or exploit content when it is posted for security research?

### Retrieval ranks

- **latest_only:** 4
- **raw_concat:** 1
- **llm_rewrite:** 1
- **oracle:** 1

---
