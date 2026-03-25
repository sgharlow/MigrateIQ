# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# MigrateIQ -- Database Migration Intelligence for GitLab

A multi-agent flow on GitLab Duo that automates SQL dialect translation, risk analysis, and migration planning directly inside GitLab. Assign an agent to an issue, get a full migration plan.

**Hackathon:** GitLab AI Hackathon 2026 (deadline Mar 25, prize pool $65K)
**Powered by:** Claude (Anthropic) via GitLab Duo Agent Platform

## Tech Stack

- GitLab Duo Agent Platform (Custom Flow)
- TypeScript (application layer, mssql + tedious)
- Python (orchestrator fallback, sustainability tracking)
- SQL (MSSQL T-SQL source files for demo)

## Project Structure

```
MigrateIQ/
├── .gitlab/duo/flows/migrateiq.yml   # Multi-agent flow (4 agents, 638 lines)
├── database/                          # Demo SQL files (WideWorldImporters)
│   ├── tables/                        # 4 table definitions
│   ├── stored-procedures/             # 6 stored procedures
│   ├── functions/                     # 2 functions
│   ├── views/                         # 1 view
│   └── user-defined-types/            # 2 types
├── src/                               # TypeScript application code
│   ├── config/database.config.ts
│   ├── queries/                       # Inline T-SQL queries
│   └── utils/sql-helpers.ts
├── migrateiq/
│   ├── orchestrator.py                # External Agent fallback
│   └── sustainability.py              # Token tracking + energy estimation
├── docs/                              # Architecture, demo script, sample outputs
├── AGENTS.md                          # GitLab Duo context
└── package.json                       # Node.js manifest
```

## Agent Pipeline (4 agents, 13 GitLab Duo tools)

1. **Scanner** -- Find and classify SQL files in the repo
2. **Translator** -- Convert SQL dialect (MSSQL to PostgreSQL)
3. **Validator** -- Flag risks and behavioral differences
4. **Planner** -- Create sub-issues, merge request, and roadmap

## Development

```bash
npm install
npm run build    # TypeScript compilation
npm run start    # Run application
```

## Testing

4 test files in the project. Demo repo uses WideWorldImporters (MIT).

## Supported Migrations

| Source | Target | Status |
|--------|--------|--------|
| MSSQL (T-SQL) | PostgreSQL 15+ | Full support |
| MySQL | PostgreSQL | Planned |
| Oracle PL/SQL | PostgreSQL | Planned |
