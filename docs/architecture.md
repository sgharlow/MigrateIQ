# MigrateIQ Architecture

## System Overview

```mermaid
flowchart TB
    subgraph trigger["Trigger"]
        issue["GitLab Issue<br/><i>'Migrate from MSSQL to PostgreSQL'</i>"]
        assign["Assign @migrateiq"]
    end

    subgraph flow["MigrateIQ Flow (GitLab Duo Agent Platform)"]
        direction TB

        subgraph scanner["1. Scanner Agent"]
            s_desc["Find & classify all SQL files"]
            s_tools["Tools: list_repository_tree<br/>gitlab_blob_search<br/>get_repository_file<br/>create_issue_note"]
        end

        subgraph translator["2. Translator Agent"]
            t_desc["Convert MSSQL → PostgreSQL<br/>50+ translation rules"]
            t_tools["Tools: get_repository_file<br/>create_commit<br/>create_issue_note"]
        end

        subgraph validator["3. Validator Agent"]
            v_desc["Risk analysis<br/>CRITICAL · WARNING · INFO"]
            v_tools["Tools: get_repository_file<br/>get_commit_diff<br/>create_issue_note"]
        end

        subgraph planner["4. Planner Agent"]
            p_desc["Migration plan<br/>Issues · MR · Roadmap"]
            p_tools["Tools: create_issue · update_issue<br/>create_merge_request<br/>create_merge_request_note<br/>create_issue_note · create_plan<br/>add_new_task · set_task_status"]
        end

        scanner --> translator --> validator --> planner
    end

    subgraph output["Output"]
        branch["Migration Branch<br/><code>migrateiq/mssql-to-postgresql</code><br/>Translated PostgreSQL files"]
        issues["6 Sub-Issues<br/>Phase 1: Schema<br/>Phase 2: Procedures<br/>Phase 3: Views & Types<br/>Phase 4: App Code<br/>Phase 5: Manual Review<br/>Phase 6: Testing"]
        mr["Merge Request<br/>Review checklist<br/>Validation summary"]
        roadmap["Migration Roadmap<br/>Effort estimates<br/>Dependency graph"]
    end

    issue --> assign --> scanner
    translator --> branch
    planner --> issues
    planner --> mr
    planner --> roadmap

    style trigger fill:#f5f5f5,stroke:#333
    style flow fill:#e8f4fd,stroke:#1f78b4
    style scanner fill:#fff3cd,stroke:#ffc107
    style translator fill:#d4edda,stroke:#28a745
    style validator fill:#f8d7da,stroke:#dc3545
    style planner fill:#d1ecf1,stroke:#17a2b8
    style output fill:#f5f5f5,stroke:#333
```

## Data Flow Between Agents

```mermaid
sequenceDiagram
    participant I as GitLab Issue
    participant S as Scanner
    participant T as Translator
    participant V as Validator
    participant P as Planner

    I->>S: Assignment trigger<br/>(AI_FLOW_INPUT, AI_FLOW_CONTEXT)

    Note over S: Walks repo tree<br/>Searches for SQL patterns<br/>Reads & classifies files

    S->>I: 📝 Issue note: "Found 19 files..."
    S->>T: JSON: {files[], source_dialect, target_dialect}

    Note over T: Reads each original file<br/>Applies 50+ translation rules<br/>Creates commits on branch

    T->>I: 📝 Issue note: "Translating [3/19]..."
    T->>V: JSON: {branch, translations[], commits[]}

    Note over V: Reads translated files<br/>Compares with originals<br/>Categorizes risks

    V->>I: 📝 Issue note: "Validation Report<br/>🔴 2 Critical, ⚠️ 5 Warning"
    V->>P: JSON: {branch, translations[], validation{}}

    Note over P: Creates 6 phase sub-issues<br/>Creates merge request<br/>Posts migration roadmap

    P->>I: 📝 Issue note: "Migration Roadmap"
    P-->>I: Creates 6 sub-issues
    P-->>I: Creates MR with review checklist
```

## Translation Pipeline Detail

```mermaid
flowchart LR
    subgraph input["MSSQL Input"]
        mssql_ddl["Tables<br/>IDENTITY, NVARCHAR,<br/>DATETIME2, MONEY"]
        mssql_proc["Procedures<br/>TRY/CATCH, TVPs,<br/>NATIVE_COMPILATION"]
        mssql_func["Functions<br/>EXECUTE AS,<br/>TABLE return"]
        mssql_json["JSON Ops<br/>FOR JSON AUTO,<br/>JSON_MODIFY"]
        mssql_sec["Security<br/>RLS, SESSION_CONTEXT,<br/>IS_ROLEMEMBER"]
        mssql_app["App Code<br/>mssql npm, TOP,<br/>CROSS APPLY"]
    end

    subgraph rules["Claude Translation (50+ Rules)"]
        translate["Dialect-aware<br/>semantic translation"]
    end

    subgraph output_pg["PostgreSQL Output"]
        pg_ddl["Tables<br/>GENERATED IDENTITY,<br/>VARCHAR, TIMESTAMP,<br/>NUMERIC(19,4)"]
        pg_proc["Procedures<br/>EXCEPTION, composite<br/>types, PL/pgSQL"]
        pg_func["Functions<br/>SECURITY DEFINER,<br/>RETURNS TABLE"]
        pg_json["JSON Ops<br/>json_agg, jsonb_set,<br/>jsonb_array_elements"]
        pg_sec["Security<br/>CREATE POLICY,<br/>current_setting,<br/>pg_has_role"]
        pg_app["App Code<br/>pg npm, LIMIT,<br/>CROSS JOIN LATERAL"]
    end

    mssql_ddl --> translate --> pg_ddl
    mssql_proc --> translate --> pg_proc
    mssql_func --> translate --> pg_func
    mssql_json --> translate --> pg_json
    mssql_sec --> translate --> pg_sec
    mssql_app --> translate --> pg_app

    style input fill:#fff3cd,stroke:#ffc107
    style rules fill:#e8f4fd,stroke:#1f78b4
    style output_pg fill:#d4edda,stroke:#28a745
```

## Tool Usage Map

| Agent | Tool | Purpose |
|-------|------|---------|
| Scanner | `list_repository_tree` | Walk directory structure |
| Scanner | `gitlab_blob_search` | Find SQL patterns in files |
| Scanner | `get_repository_file` | Read file contents for classification |
| Scanner | `create_issue_note` | Post scan results |
| Translator | `get_repository_file` | Read original files |
| Translator | `create_commit` | Commit translated files to migration branch |
| Translator | `create_issue_note` | Post translation progress |
| Validator | `get_repository_file` | Read translated files |
| Validator | `get_commit_diff` | Compare original vs translated |
| Validator | `create_issue_note` | Post risk report |
| Planner | `create_issue` | Create phase sub-issues |
| Planner | `update_issue` | Add labels and metadata |
| Planner | `create_merge_request` | Create MR from migration branch |
| Planner | `create_merge_request_note` | Add review checklist to MR |
| Planner | `create_issue_note` | Post migration roadmap |
| Planner | `create_plan` | Create structured task plan |
| Planner | `add_new_task` | Add tasks to the plan |
| Planner | `set_task_status` | Update task completion |

**13 unique tools** across 4 agents.
