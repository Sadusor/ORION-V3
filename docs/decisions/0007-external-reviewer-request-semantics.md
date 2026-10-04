# Decision 0007 — External reviewer request semantics

Date: 2026-10-04
Status: OWNER CLARIFICATION

When the owner says phrases such as "ask DeepSeek", "ask Claude", or similar in this ChatGPT conversation, interpret that as:

- prepare a high-quality prompt for the owner to paste into that external model manually;
- do not invoke that provider through ORION unless the owner explicitly asks ORION/the system to run that provider.

For ORION-internal model benchmarks or automated reviewer runs, prefer stronger benchmark/reviewer models when available (for example GPT-OSS-class large models) rather than small models, subject to the owner's cost and availability constraints.

This clarification exists to keep manual external brainstorming distinct from ORION's automated reviewer infrastructure.
