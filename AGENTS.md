# AGENTS.md

<!-- BEGIN:sampu-canon (synced from sampu-codex/standards/agents-md/sampu-canon.md; edit there, never here) -->
## Sampu canon (digest)

Sampu Dynamics builds from Africa, for the world: AI-native, held to a global bar. The full canon is `SAMPU_DNA.md` at this repo's root; read it before any decision with weight (money, user data, dignity, or an architecture that is expensive to reverse).

- **Faith is the fixed centre.** When a trade-off touches integrity, dignity or user trust, integrity wins.
- **Build for the constraint:** a low-end phone on a slow, expensive, dropping network. Offline-first, low-bandwidth, fails gracefully and says so.
- **Three gates, all required:** Quality (works under real conditions, fast, secure, finished to the edges: error, empty and loading states), Impact (a named person, a measurable dent), Value (compounds; worth more next year).
- **Done means verified:** this repo's typecheck, test and lint commands green and the change exercised in the running app. Compiling is not done; an un-run feature is not done.
- **Keep the domain legible:** names in code match `GLOSSARY.md`; hard decisions become ADRs in `docs/adr/`; update both in the same change as the code.
- **Deep modules, narrow types:** make illegal states unrepresentable; no `any` at boundaries.
- **Test first** for business logic, money, data integrity and bug fixes: the failing test that reproduces the bug comes before the fix.
- **Small commits on a branch**, one logical change each. Pushes to `main` fast-forward only; secrets and keys stay out of git.
- **Sovereignty and dignity:** protect user data as our own most private information; meet users in their language, on their device, without condescension.
- **Tell the truth:** report what works, what failed, and where it is weak, plainly.
<!-- END:sampu-canon -->

> Operating DNA (canonical lives in sampu-codex; synced here, do not hand-edit):
@SAMPU_DNA.md

> Founder & product delivery capability (canonical lives in sampu-codex; synced here, do not hand-edit):
@founder-product-delivery-capability.md

> Design doctrine (canonical lives in sampu-codex; synced here, do not hand-edit):
@design-doctrine.md


## Coding workflow — the Sampu spine

All work in this repo follows the Sampu coding workflow (canon: `standards/coding-workflow.md` in [sampu-codex](https://github.com/Sandz472/sampu-codex); adopted 2026-07-29). The loop: grill → spec → tickets → `groom-ticket` at pickup (six-field mini-knowledge-graph gate, never bulk-labeled) → one fresh session per ticket with `Implement issue #N` as the entire prompt → finish line per this file's Engineering Standards → founder merges and verifies the issue closed → write back what was learned. Work larger than one agent session goes through `wayfinder`; hard bugs through `diagnosing-bugs`; business logic, money, and data integrity through TDD. Tickets point at code and canon — they never copy them.
