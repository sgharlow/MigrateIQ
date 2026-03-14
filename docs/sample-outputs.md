# MigrateIQ Sample Agent Outputs

> These are the expected issue note formats from each agent. Use as test
> fixtures to validate output formatting on the GitLab Duo platform.

---

## Scanner Agent Output

```markdown
## :mag: MigrateIQ Scanner Report

**Source dialect detected:** Microsoft SQL Server (T-SQL)
**Target dialect requested:** PostgreSQL 15+

### Files Found: 19 total

| # | File | Category | Key MSSQL Features |
|---|------|----------|--------------------|
| 1 | `database/tables/People.sql` | DDL | Temporal tables, sequences, JSON computed columns, persisted computed, extended properties |
| 2 | `database/tables/Cities.sql` | DDL | Geography spatial type, temporal tables, sequences |
| 3 | `database/tables/StockItems.sql` | DDL | JSON query computed columns, temporal tables, full-text search column |
| 4 | `database/tables/Customers.sql` | DDL | Geography, temporal tables, covering indexes with INCLUDE, self-referential FK |
| 5 | `database/stored-procedures/RecordColdRoomTemperatures.sql` | STORED_PROC | :red_circle: Native compilation, ATOMIC block, In-Memory OLTP, memory-optimized TVP |
| 6 | `database/stored-procedures/InvoiceCustomerOrders.sql` | STORED_PROC | JSON_MODIFY (nested), CTE-based UPDATE FROM, TVP, multi-table transaction, sequences |
| 7 | `database/stored-procedures/InsertCustomerOrders.sql` | STORED_PROC | Table-valued parameters, table variables, SEQUENCE in INSERT...SELECT, TRY/CATCH |
| 8 | `database/stored-procedures/SearchForStockItemsByTags.sql` | STORED_PROC | FOR JSON AUTO with ROOT, TOP, EXECUTE AS OWNER |
| 9 | `database/stored-procedures/Configuration_ApplyRowLevelSecurity.sql` | STORED_PROC | :warning: Row-Level Security, SECURITY POLICY, SESSION_CONTEXT, dynamic SQL |
| 10 | `database/stored-procedures/Configuration_ApplyFullTextIndexing.sql` | STORED_PROC | FULLTEXT CATALOG, FREETEXTTABLE, FOR JSON AUTO, dynamic DDL generation |
| 11 | `database/functions/CalculateCustomerPrice.sql` | FUNCTION | Scalar UDF, EXECUTE AS OWNER, complex business logic |
| 12 | `database/functions/DetermineCustomerAccess.sql` | FUNCTION | Inline table-valued function, IS_ROLEMEMBER, SESSION_CONTEXT, RLS predicate |
| 13 | `database/views/VehicleTemperatures.sql` | VIEW | :warning: DECOMPRESS() function, conditional decompression |
| 14 | `database/user-defined-types/OrderList.sql` | UDT | :red_circle: Memory-optimized table type (MEMORY_OPTIMIZED = ON) |
| 15 | `database/user-defined-types/SensorDataList.sql` | UDT | :red_circle: Memory-optimized TVP with IDENTITY column in type |
| 16 | `src/config/database.config.ts` | CONFIG | mssql npm package, connection pool configuration |
| 17 | `src/queries/customers.ts` | APP_CODE | TOP, ISNULL, CONVERT with style, CROSS APPLY, geography methods, IIF |
| 18 | `src/queries/stock-items.ts` | APP_CODE | JSON_QUERY, JSON_VALUE, OPENJSON, FOR JSON AUTO |
| 19 | `src/utils/sql-helpers.ts` | APP_CODE | EXEC stored proc, FOR SYSTEM_TIME ALL, FREETEXTTABLE |

### Summary by Category
| Category | Count |
|----------|-------|
| DDL (Tables) | 4 |
| Stored Procedures | 6 |
| Functions | 2 |
| Views | 1 |
| User-Defined Types | 2 |
| Application Code | 3 |
| Configuration | 1 |
| **Total** | **19** |

---
:robot: MigrateIQ Scanner — Database Migration Intelligence for GitLab
```

---

## Translator Agent Progress Notes

```markdown
## :arrows_counterclockwise: MigrateIQ Translator — Batch 1/4

**Translating DDL files to PostgreSQL...**

:white_check_mark: `database/tables/People.sql`
- `IDENTITY(1,1)` → `GENERATED ALWAYS AS IDENTITY`
- `NVARCHAR(MAX)` → `TEXT`, `VARBINARY(MAX)` → `BYTEA`
- `SYSTEM_VERSIONING` → temporal table note (trigger-based approach)
- `json_query()` computed column → documented as manual implementation
- `sp_addextendedproperty` → `COMMENT ON` (14 columns documented)

:white_check_mark: `database/tables/Cities.sql`
- `[sys].[geography]` → `geography` (PostGIS extension required)
- `NEXT VALUE FOR [Sequences].[CityID]` → `nextval('sequences.city_id')`
- Temporal versioning documented

:white_check_mark: `database/tables/StockItems.sql`
- `json_query()` computed column → documented as NOTE
- `concat()` persisted column → `GENERATED ALWAYS AS ... STORED`
- 4 FK indexes translated

:white_check_mark: `database/tables/Customers.sql`
- PostGIS extension for `delivery_location`
- Self-referential FK preserved
- 7 FK indexes + 1 covering index with INCLUDE

**Committed to branch:** `migrateiq/mssql-to-postgresql` (SHA: abc1234)
```

---

## Validator Agent Output

```markdown
## :shield: MigrateIQ Validation Report

### Summary
| Metric | Count |
|--------|-------|
| Files validated | 19 |
| :white_check_mark: Clean translations | 12 |
| :warning: Warnings | 5 |
| :red_circle: Critical issues | 2 |

---

### :red_circle: Critical Issues

**1. `database/stored-procedures/RecordColdRoomTemperatures.sql` — Native Compilation Removed**

The original uses `WITH NATIVE_COMPILATION` and `BEGIN ATOMIC` for In-Memory OLTP (Hekaton) performance. PostgreSQL has no equivalent execution model. The translated version uses standard PL/pgSQL which is functionally correct but may have significant performance differences under high-throughput sensor data ingestion scenarios.

**Recommendation:** Benchmark the translated procedure under expected load. Consider using PL/pgSQL `IMMUTABLE` or `STABLE` volatility hints. For extreme throughput, consider a C extension or batch INSERT approach.

**2. `database/views/VehicleTemperatures.sql` — DECOMPRESS() Has No Direct Equivalent**

The original uses MSSQL's built-in `DECOMPRESS()` function to decompress `VARBINARY` data inline. PostgreSQL has no built-in `DECOMPRESS()`. The translation uses `convert_from(data, 'UTF8')` which only works if data is UTF-8 text, not actually compressed.

**Recommendation:** Create a custom PostgreSQL function using `pg_lz_decompress` or handle decompression in the application layer. If the data was compressed with MSSQL's `COMPRESS()`, you'll need a compatible decompression implementation.

---

### :warning: Warnings

**3. `database/stored-procedures/Configuration_ApplyRowLevelSecurity.sql` — RLS Implementation Differs**

MSSQL uses `CREATE SECURITY POLICY` with filter and block predicates via an inline TVF. PostgreSQL uses `CREATE POLICY` with `USING` and `WITH CHECK` clauses. While both achieve row-level security, the mechanics differ:
- MSSQL: centralized SECURITY POLICY object managing multiple predicates
- PostgreSQL: per-table policies with `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`

`SESSION_CONTEXT(N'SalesTerritory')` is translated to `current_setting('app.SalesTerritory')` — the `app.*` GUC namespace must be configured in `postgresql.conf` or set per-session.

**Recommendation:** Verify row filtering behavior matches original. Test with multiple user roles. Ensure `app.SalesTerritory` is set in application connection initialization.

**4. `database/stored-procedures/Configuration_ApplyFullTextIndexing.sql` — Full-Text Search Engine Differs**

MSSQL's `FREETEXTTABLE` uses a different ranking algorithm than PostgreSQL's `ts_rank`. Search result ordering may differ. The `FULLTEXT CATALOG` concept has no PostgreSQL equivalent — PostgreSQL uses GIN indexes directly.

**Recommendation:** Compare search result rankings between MSSQL and PostgreSQL for representative queries. Tune `ts_rank` weights if needed.

**5. `database/tables/People.sql, Cities.sql, StockItems.sql, Customers.sql` — Temporal Tables**

MSSQL's native system-versioned temporal tables (`SYSTEM_VERSIONING = ON`) have no direct PostgreSQL equivalent. The translation preserves `valid_from`/`valid_to` columns and documents a trigger-based approach, but the automatic history tracking is not implemented.

**Recommendation:** Install the `temporal_tables` PostgreSQL extension, or implement triggers that copy rows to `*_history` tables on UPDATE/DELETE.

**6. `database/user-defined-types/OrderList.sql, SensorDataList.sql` — Memory-Optimized Types**

`WITH (MEMORY_OPTIMIZED = ON)` is removed. PostgreSQL composite types do not support memory optimization. The `IDENTITY` column in `SensorDataList` is also removed (not supported in PG composite types).

**Recommendation:** If performance is critical for TVP-heavy workloads, consider using temporary tables instead of composite type arrays.

**7. `src/queries/customers.ts` — Geography Methods**

`geography.STAsText()`, `.Lat`, `.Long` are translated to PostGIS `ST_AsText()`, `ST_Y()`, `ST_X()`. These require the PostGIS extension (`CREATE EXTENSION IF NOT EXISTS postgis`).

**Recommendation:** Ensure PostGIS is installed on the target PostgreSQL instance.

---

### :white_check_mark: Clean Translations (12 files)

| File | Key Translations |
|------|-----------------|
| `InsertCustomerOrders.sql` | TVP → composite array, TRY/CATCH → EXCEPTION, NEXT VALUE FOR → nextval() |
| `InvoiceCustomerOrders.sql` | JSON_MODIFY → jsonb_set, CONVERT style → TO_CHAR, table vars → temp tables |
| `SearchForStockItemsByTags.sql` | FOR JSON AUTO → json_build_object + json_agg, TOP → LIMIT |
| `CalculateCustomerPrice.sql` | Scalar UDF → LANGUAGE plpgsql, EXECUTE AS → SECURITY DEFINER |
| `DetermineCustomerAccess.sql` | Inline TVF → LANGUAGE sql, IS_ROLEMEMBER → pg_has_role |
| `database.config.ts` | mssql → pg driver, ConnectionPool → Pool, close → end |
| `customers.ts` | TOP → LIMIT, ISNULL → COALESCE, CROSS APPLY → CROSS JOIN LATERAL |
| `stock-items.ts` | JSON_QUERY → jsonb #>, OPENJSON → jsonb_array_elements_text |
| `sql-helpers.ts` | EXEC → CALL, FOR SYSTEM_TIME → union query, FREETEXTTABLE → tsvector |
| `Cities.sql` | geography → PostGIS, IDENTITY → GENERATED, temporal documented |
| `StockItems.sql` | JSON computed → documented, concat PERSISTED → STORED |
| `Customers.sql` | geography, temporal, covering index preserved |

---
:robot: MigrateIQ Validator — Database Migration Intelligence for GitLab
```

---

## Planner Agent Output (Migration Roadmap)

```markdown
## :world_map: MigrateIQ Migration Roadmap

### Migration Summary
| Metric | Value |
|--------|-------|
| Files translated | 19 |
| :white_check_mark: Clean translations | 12 |
| :warning: Warnings | 5 |
| :red_circle: Critical issues | 2 |
| Estimated total effort | 18 hours |

### Prerequisites
- [ ] Install PostGIS extension: `CREATE EXTENSION IF NOT EXISTS postgis;`
- [ ] Install pg_trgm extension: `CREATE EXTENSION IF NOT EXISTS pg_trgm;`
- [ ] Configure `app.*` GUC namespace for Row-Level Security session variables
- [ ] Create sequences matching `sequences.*` schema

### Recommended Execution Order

| Order | Phase | Scope | Est. Hours | Dependencies | Issue |
|-------|-------|-------|-----------|-------------|-------|
| 1st | Phase 1 | **Schema Migration** — 4 table DDL files | 3 hrs | None | #101 |
| 2nd | Phase 3 | **Views & UDTs** — 1 view, 2 type definitions | 1 hr | Phase 1 | #103 |
| 3rd | Phase 2 | **Procedures & Functions** — 6 procs, 2 functions | 6 hrs | Phase 1 | #102 |
| 4th | Phase 4 | **Application Code** — 4 TypeScript files | 3 hrs | Phase 1 | #104 |
| 5th | Phase 5 | **Manual Review** — 2 critical + 5 warnings | 3 hrs | Phases 1-4 | #105 |
| 6th | Phase 6 | **Testing & Validation** — Verify correctness | 2 hrs | All phases | #106 |

> Note: Execution order differs from phase numbering. Views/UDTs (Phase 3) should be
> applied before procedures (Phase 2) because procedures may reference views and types.

### Merge Request
See !42 for all translated files. Review checklist attached based on validation findings.

### Sub-Issues Created
- #101 — [MigrateIQ] Phase 1: Schema Migration (DDL)
- #102 — [MigrateIQ] Phase 2: Stored Procedures & Functions
- #103 — [MigrateIQ] Phase 3: Views & User-Defined Types
- #104 — [MigrateIQ] Phase 4: Application Code Updates
- #105 — [MigrateIQ] Phase 5: Manual Review Required
- #106 — [MigrateIQ] Phase 6: Testing & Validation

---
:robot: Generated by MigrateIQ — Database Migration Intelligence for GitLab
```

---

## Sustainability Report (Green Agent Prize)

```markdown
## :seedling: MigrateIQ Sustainability Report

### Token Usage

| Agent | Input Tokens | Output Tokens | Total | Est. Energy |
|-------|-------------|---------------|-------|-------------|
| Scanner | 8,200 | 2,400 | 10,600 | 0.0424 kWh |
| Translator | 45,000 | 38,000 | 83,000 | 0.3320 kWh |
| Validator | 52,000 | 6,500 | 58,500 | 0.2340 kWh |
| Planner | 12,000 | 4,800 | 16,800 | 0.0672 kWh |
| **Total** | **117,200** | **51,700** | **168,900** | **0.6756 kWh** |

### Energy Comparison

| Approach | Energy (kWh) | CO2 (kg) | Time |
|----------|-------------|----------|------|
| :robot: AI Migration (MigrateIQ) | 0.6756 | 0.2601 | ~5 min |
| :robot: + :person: AI + Human Review | 2.5756 | 0.9916 | ~10 hrs |
| :person: Fully Manual | 7.60 | 2.9260 | ~38 hrs |

**Energy savings vs fully manual: 91.1%**

### Methodology

- LLM inference energy: ~0.004 kWh per 1K tokens (GPU inference estimate)
- Developer workstation: ~0.20 kWh/hr (laptop + monitor + office overhead)
- Carbon intensity: US average grid at 0.385 kg CO2/kWh (EPA 2024)
- Manual estimate: ~2 hrs/file for translation, ~0.5 hrs/file for AI review

---
:seedling: *MigrateIQ reduces the environmental impact of database migrations by replacing weeks of developer workstation energy with minutes of AI inference.*
```
