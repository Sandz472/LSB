# LSB Phase Status

> Only a human edits this file. Claude Code may not cross a locked phase
> (CLAUDE.md rule 9; Blueprint Part 15.9).

| Phase | Scope | Status |
|---|---|---|
| Phase 0 | Setup, governing files, scaffold (Sessions 0) | **ACTIVE** |
| Phase 1 | Data, config/schema, state machine, replay harness (Sessions 1–4, Gate G1) | LOCKED until Session 0 acceptance passes |
| Phase 2 | The Engine — modules M1–M14 offline (Sessions 5–17, Gate G2) | LOCKED |
| Phase 3 | Walk-forward validation, GO/NO-GO verdict (Sessions 18–19, Gate G3) | LOCKED |
| Phase 4 | Live infrastructure — broker adapter, alerting, deploy (Sessions 20–22, Gate G4) | **LOCKED — human unlock only, after a G3 GO** |
| Phase 5–8 | Forward test, Bayesian advisor, hypothesis engine, research layer (Sessions 23–29, Gates G5–G6) | **LOCKED — human unlock only** |

## Environment decisions

- **Dev database:** native PostgreSQL 16 on Windows — *no Docker locally*
  (low-spec workstation; deviation from Blueprint Step 0 item 6, dev
  environment only). Installation is due at **Session 2**, the first
  session that touches the database. The VPS/container architecture for
  Phase 4 (Blueprint Part 15.7) is unaffected and waits for the gate.
- **CI:** local script `scripts/ci.ps1` (no GitHub remote yet);
  `.github/workflows/ci.yml` is in place and activates when a remote is
  added.
