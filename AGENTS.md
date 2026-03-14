# WideWorldImporters Application

## Overview
This is a TypeScript application backed by Microsoft's WideWorldImporters sample database
running on SQL Server. The codebase contains both raw SQL database objects and application
code with inline MSSQL queries.

## Project Structure
- `database/` — SQL Server database objects from WideWorldImporters
  - `tables/` — Table definitions with temporal versioning, geography, JSON, sequences
  - `stored-procedures/` — T-SQL procedures including natively compiled (In-Memory OLTP)
  - `functions/` — Scalar and inline table-valued functions
  - `views/` — Database views with DECOMPRESS and cross-schema joins
  - `user-defined-types/` — Memory-optimized table-valued parameter types
- `src/` — TypeScript application code using the mssql npm package
  - `config/` — MSSQL connection pool configuration
  - `queries/` — Data access layer with inline T-SQL
  - `utils/` — Helpers for stored proc execution, temporal queries, full-text search

## Database
- SQL Server (WideWorldImporters sample database)
- Schemas: Application, Sales, Warehouse, Website, Integration, DataLoadSimulation
- Key features used: temporal tables, sequences, geography, JSON, Row-Level Security,
  full-text search, natively compiled procedures, memory-optimized table types

## SQL Dialect
All SQL uses **Microsoft SQL Server (T-SQL)** dialect including:
- `[bracketed]` identifiers
- `IDENTITY`, `NEXT VALUE FOR` sequences
- `TOP`, `ISNULL`, `CONVERT` with style codes
- `CROSS APPLY`, `FOR JSON AUTO`
- `TRY/CATCH`, `THROW`, `XACT_STATE()`
- System versioned temporal tables (`FOR SYSTEM_TIME`)
- Natively compiled stored procedures (`WITH NATIVE_COMPILATION`)
