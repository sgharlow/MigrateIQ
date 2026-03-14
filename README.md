# MigrateIQ — Database Migration Intelligence for GitLab

> **Assign an agent. Get a migration plan.** MigrateIQ is a multi-agent flow on GitLab Duo that automates SQL dialect translation, risk analysis, and migration planning — directly inside GitLab.

## The Problem

Database migrations between SQL dialects cost organizations **$50K–$200K** in consulting fees and take **weeks of manual work**. Teams must audit hundreds of files, translate dialect-specific syntax, identify data loss risks, and create a structured migration plan — all while keeping the project running.

## The Solution

MigrateIQ brings database migration intelligence into GitLab. Create an issue, assign the MigrateIQ agent, and a pipeline of four specialized AI agents automatically:

1. **Scans** your codebase for all SQL and application files
2. **Translates** every file from the source dialect to the target
3. **Validates** each translation for risks and behavioral differences
4. **Plans** the migration with sub-issues, a merge request, and a roadmap

## How It Works

```
  Issue: "Migrate from MSSQL to PostgreSQL"
  [Assign MigrateIQ]
          │
          ▼
  ┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────┐
  │ SCANNER  │───▶│  TRANSLATOR  │───▶│  VALIDATOR   │───▶│ PLANNER  │
  │          │    │              │    │              │    │          │
  │ Find all │    │ Convert SQL  │    │ Flag risks   │    │ Create   │
  │ SQL files│    │ dialect      │    │ & warnings   │    │ plan     │
  │          │    │              │    │              │    │          │
  │ 4 tools  │    │ 3 tools      │    │ 3 tools      │    │ 8 tools  │
  └──────────┘    └──────────────┘    └──────────────┘    └──────────┘
          │                │                                    │
          ▼                ▼                                    ▼
    Issue Note:      Migration Branch          Sub-Issues + MR + Roadmap
    "Found 19        with translated
     files..."       PostgreSQL code
```

## Quick Start

### 1. Create a migration issue

Create a new issue in this project with a title describing your migration:

> **Migrate database from Microsoft SQL Server to PostgreSQL**

### 2. Assign MigrateIQ

Assign the `@migrateiq` service account to the issue. This triggers the multi-agent flow.

### 3. Watch the agents work

The four agents execute in sequence, posting progress updates as issue comments:
- Scanner reports the files it found and their classifications
- Translator posts progress as it converts each file
- Validator posts a structured risk report with severity levels
- Planner creates sub-issues, a merge request, and a migration roadmap

### 4. Review the output

- **Migration branch** with all translated files (`migrateiq/mssql-to-postgresql`)
- **6 sub-issues** organized by migration phase
- **Merge request** with review checklist based on validation findings
- **Migration roadmap** with estimated effort and recommended execution order

## Supported Migrations

| Source | Target | Status |
|--------|--------|--------|
| Microsoft SQL Server (T-SQL) | PostgreSQL 15+ | Full support |
| MySQL | PostgreSQL | Planned |
| Oracle PL/SQL | PostgreSQL | Planned |

## Translation Coverage

MigrateIQ handles 50+ MSSQL-to-PostgreSQL translation patterns including:

| Category | Examples |
|----------|---------|
| **Data types** | `IDENTITY` → `GENERATED ALWAYS AS IDENTITY`, `NVARCHAR` → `VARCHAR`, `MONEY` → `NUMERIC(19,4)`, `geography` → PostGIS |
| **Query syntax** | `TOP` → `LIMIT`, `ISNULL` → `COALESCE`, `IIF` → `CASE WHEN`, `CROSS APPLY` → `CROSS JOIN LATERAL` |
| **Procedures** | `CREATE PROCEDURE` → `CREATE OR REPLACE PROCEDURE`, `TRY/CATCH` → `EXCEPTION`, `EXEC` → `CALL` |
| **JSON** | `FOR JSON AUTO` → `json_agg`, `JSON_MODIFY` → `jsonb_set`, `OPENJSON` → `jsonb_array_elements` |
| **Security** | `EXECUTE AS OWNER` → `SECURITY DEFINER`, `SECURITY POLICY` → `CREATE POLICY` (native RLS) |
| **Search** | `FREETEXTTABLE` → `tsvector/tsquery` with GIN index |
| **Temporal** | `SYSTEM_VERSIONING` → trigger-based temporal approach |
| **Advanced** | Native compilation, memory-optimized types, `DECOMPRESS`, sequences, extended properties |

## Risk Detection

The Validator agent categorizes every finding by severity:

| Level | What It Catches |
|-------|----------------|
| :red_circle: **Critical** | Features with no PG equivalent (native compilation, CLR, linked servers), data precision loss, complex MERGE clauses |
| :warning: **Warning** | Behavioral differences (RLS semantics, trigger timing, isolation levels), performance implications (cursor-heavy code) |
| :white_check_mark: **Info** | Clean translations (TOP→LIMIT, ISNULL→COALESCE, bracket removal) |

## Demo Repository

This repository contains a curated subset of Microsoft's [WideWorldImporters](https://github.com/microsoft/sql-server-samples) sample database (MIT License) — a realistic application showcasing 17+ MSSQL-specific features:

- **15 SQL files**: Tables with temporal versioning, natively compiled stored procedures, Row-Level Security, full-text search, geography types, JSON operations, memory-optimized TVPs
- **4 TypeScript files**: Application code using the `mssql` npm package with inline T-SQL queries

## Architecture

**Built on:** GitLab Duo Agent Platform (Custom Flow)
**Powered by:** Claude (Anthropic) — auto-qualified for the GitLab & Anthropic sponsor track
**Flow definition:** `.gitlab/duo/flows/migrateiq.yml`

| Component | Role | GitLab Duo Tools |
|-----------|------|-----------------|
| **Scanner** | Find and classify SQL files | `list_repository_tree`, `gitlab_blob_search`, `get_repository_file`, `create_issue_note` |
| **Translator** | Convert dialect, create commits | `get_repository_file`, `create_commit`, `create_issue_note` |
| **Validator** | Flag risks and behavioral diffs | `get_repository_file`, `get_commit_diff`, `create_issue_note` |
| **Planner** | Create issues, MR, and roadmap | `create_issue`, `update_issue`, `create_merge_request`, `create_merge_request_note`, `create_issue_note`, `create_plan`, `add_new_task`, `set_task_status` |

**13 unique GitLab Duo tools** used across the 4-agent pipeline.

## For Judges: Testing MigrateIQ

1. Navigate to the [Issues](../../issues) tab
2. Create a new issue with title: `Migrate database from MSSQL to PostgreSQL`
3. Assign the `@migrateiq` service account
4. Watch the agent comments appear on the issue
5. Review the created sub-issues, migration branch, and merge request

A pre-created sample issue is available: [Sample Migration Issue](#) *(link added after deployment)*

## Project Structure

```
.gitlab/duo/
  flows/migrateiq.yml       # Multi-agent flow definition (4 agents, 657 lines)
  agent-config.yml           # Flow execution environment
  chat-rules.md              # Project context for Duo chat
database/
  tables/                    # 4 table definitions (temporal, geography, JSON)
  stored-procedures/         # 6 procedures (native compilation, RLS, TVPs)
  functions/                 # 2 functions (scalar UDF, inline TVF)
  views/                     # 1 view (DECOMPRESS)
  user-defined-types/        # 2 types (memory-optimized TVPs)
src/
  config/database.config.ts  # MSSQL connection pool
  queries/                   # 2 query files with inline T-SQL
  utils/sql-helpers.ts       # Temporal queries, full-text search, proc execution
AGENTS.md                    # Project structure for GitLab Duo context
LICENSE                      # MIT
```

## License

MIT — see [LICENSE](LICENSE)

SQL files in `database/` are derived from Microsoft's WideWorldImporters sample database, also MIT licensed.

---

:robot: Built for the [GitLab AI Hackathon 2026](https://gitlab.devpost.com) — *You Orchestrate. AI Accelerates.*
