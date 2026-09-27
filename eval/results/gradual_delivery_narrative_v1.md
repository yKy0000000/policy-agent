# Gradual Delivery Narrative (v1) — ~90 seconds

I was asked to improve a GitHub policy Q&A agent. Rather than adding more RAG features, I first measured where the system actually broke. Candidate retrieval was already near-saturated — about 98% of the required facts were already reaching the candidate pool — so the real bottleneck was evidence *allocation*, not search. That reframed the whole project around choosing the right context, not fetching more of it.

My first hypothesis was query-aware routing: classify a question as simple or broad and give broad ones more context. I built it, evaluated it blindly against a frozen human rubric, and it lost. A simpler evidence-side selector matched its answer quality with fewer regressions and about 11% fewer tokens, so the router was strictly dominated. I killed it instead of tuning it back into relevance.

My second hypothesis was requirement decomposition: some multi-part questions get collapsed into a single search, hiding one requirement. I built a minimal offline probe and found a real case where the needed evidence was completely absent for the normal query yet surfaced at rank two once the requirement was searched on its own. It worked — but only in one of fifty cases. So I documented it as a proven mechanism and deliberately did not put it in the default path.

A third idea, hierarchical retrieval for split evidence, had no failure mode to fix, so it was never built.

The final system is simpler than what I started with: one clean retrieval pipeline, a fixed top-five context, and the router removed. The lesson is the point: add complexity only when a measured failure mode justifies it.
