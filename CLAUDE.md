# LSB — Governing Instructions

1. The specification (docs/LSB_System_Requirements_v2.0) is IMMUTABLE.
   Implement it literally. Any deviation is a written proposal in
   docs/proposals/, never silent code.
2. Before reading source files, query the knowledge graph:
   `graphify query "..."` / `graphify affected "..."`. Re-read raw files
   only when the graph is insufficient.
3. Every module (M1–M14) is built independently with unit tests against
   hand-verified reference values BEFORE integration.
4. Determinism is law: same candles + same config → byte-identical
   decisions. Never introduce wall-clock time, randomness, dict-ordering
   dependence, or float nondeterminism into a decision path.
5. The initial release is entirely rule-based. Intelligence lives only
   behind the Advisor interface and may only reduce risk or veto.
6. Risk code (M8, M11) gets adversarial tests. Forced breaches MUST halt.
7. Run `pytest -q` and the golden-fixture replay before declaring any
   task complete. A task with red tests is not done.
8. After completing a task: `graphify update .` and include graphify-out/
   in the commit.
9. Never touch live-broker code paths before Phase 4 is unlocked in
   docs/PHASE_STATUS.md.
