# LSB — Governing Instructions

> Authoritative governance for the LSB project. These rules are taken verbatim
> from `docs/BUILD_PLAYBOOK.md` §3. They govern every Claude Code run in this
> repository.

1. `docs/LSB_System_Requirements_v2.0` is IMMUTABLE. Implement §8.1 literally per
   `docs/GATE_SPECIFICATION.md`. Any deviation is a written proposal in
   `docs/decisions/`, never silent code.
2. Before reading source, query the graph: `graphify query` / `graphify affected`.
3. Every module is built independently with unit tests against hand-verified
   reference values BEFORE integration.
4. Determinism is law: same candles + config -> byte-identical decisions. No
   wall-clock, randomness, dict-order, or float-order in a decision path.
5. Risk code gets adversarial tests. Build the FULL §8.1 gate set: do not drop
   the EMA-Interaction gate; do not promote the sweep score to a gate; implement
   the §6.1.1/.2 Invalidation rule; sweep target = block HIGH (§7.2); flat
   tolerance baseline = 0.15% (§6.1.1); crypto sessions = 24/7 (§3.3).
6. `pytest -q` and the golden-fixture replay must be green before any task is done.
7. After each task: `graphify update .` ; commit including `graphify-out/`.
8. Never touch broker/live paths before Phase B is unlocked in `PHASE_STATUS.md`.
