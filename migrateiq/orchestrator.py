"""
MigrateIQ External Agent Orchestrator

Fallback implementation that runs the 4-agent pipeline via Claude API
in a GitLab CI/CD pipeline. Used if Custom Flow YAML doesn't work
on the GitLab Duo platform.

Usage:
    python migrateiq/orchestrator.py

Environment variables (set by GitLab CI or .gitlab/duo/flows config):
    AI_FLOW_INPUT          - The issue description / migration request
    AI_FLOW_CONTEXT        - JSON with issue details
    AI_FLOW_GITLAB_TOKEN   - GitLab API token
    AI_FLOW_AI_GATEWAY_TOKEN - Anthropic API key (via GitLab AI Gateway)
    ANTHROPIC_BASE_URL     - Anthropic API endpoint
    ANTHROPIC_API_KEY      - Anthropic API key
    CI_PROJECT_ID          - GitLab project ID
    CI_SERVER_URL          - GitLab server URL
"""

import json
import os
import sys
import urllib.request
import urllib.error

from migrateiq.sustainability import create_tracker, get_agent

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GITLAB_URL = os.environ.get("CI_SERVER_URL", "https://gitlab.com")
PROJECT_ID = os.environ.get("CI_PROJECT_ID", "")
GITLAB_TOKEN = os.environ.get("AI_FLOW_GITLAB_TOKEN", os.environ.get("GITLAB_TOKEN", ""))
ANTHROPIC_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
ANTHROPIC_KEY = os.environ.get("AI_FLOW_AI_GATEWAY_TOKEN", os.environ.get("ANTHROPIC_API_KEY", ""))
MIGRATION_REQUEST = os.environ.get("AI_FLOW_INPUT", "Migrate database from MSSQL to PostgreSQL")
ISSUE_IID = os.environ.get("CI_ISSUE_IID", "")

MODEL = "claude-sonnet-4-5-20250514"
MAX_TOKENS = 8192

# ---------------------------------------------------------------------------
# GitLab API helpers
# ---------------------------------------------------------------------------

def gitlab_api(method: str, endpoint: str, data: dict | None = None) -> dict:
    """Make a GitLab API request."""
    url = f"{GITLAB_URL}/api/v4/projects/{PROJECT_ID}/{endpoint}"
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN, "Content-Type": "application/json"}
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"GitLab API error: {e.code} {e.read().decode()}", file=sys.stderr)
        return {}


def post_issue_note(issue_iid: str, body: str) -> dict:
    """Post a comment on a GitLab issue."""
    return gitlab_api("POST", f"issues/{issue_iid}/notes", {"body": body})


def list_repository_tree(path: str = "", ref: str = "main") -> list:
    """List files in the repository."""
    result = gitlab_api("GET", f"repository/tree?path={path}&ref={ref}&per_page=100&recursive=true")
    return result if isinstance(result, list) else []


def get_file_content(file_path: str, ref: str = "main") -> str:
    """Get a file's content from the repository."""
    import base64
    encoded_path = urllib.parse.quote(file_path, safe="")
    result = gitlab_api("GET", f"repository/files/{encoded_path}?ref={ref}")
    if result and "content" in result:
        return base64.b64decode(result["content"]).decode("utf-8", errors="replace")
    return ""


def create_branch(branch_name: str, ref: str = "main") -> dict:
    """Create a new branch."""
    return gitlab_api("POST", "repository/branches", {"branch": branch_name, "ref": ref})


def create_commit(branch: str, message: str, actions: list) -> dict:
    """Create a commit with file changes."""
    return gitlab_api("POST", "repository/commits", {
        "branch": branch,
        "commit_message": message,
        "actions": actions,
    })


def create_issue(title: str, description: str, labels: str = "") -> dict:
    """Create a new issue."""
    data = {"title": title, "description": description}
    if labels:
        data["labels"] = labels
    return gitlab_api("POST", "issues", data)


def create_merge_request(source: str, target: str, title: str, description: str) -> dict:
    """Create a merge request."""
    return gitlab_api("POST", "merge_requests", {
        "source_branch": source,
        "target_branch": target,
        "title": title,
        "description": description,
    })

# ---------------------------------------------------------------------------
# Claude API helper
# ---------------------------------------------------------------------------

def call_claude(system_prompt: str, user_message: str) -> str:
    """Call Claude API and return the response text."""
    url = f"{ANTHROPIC_URL}/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_KEY,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    data = json.dumps({
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_message}],
    }).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.loads(resp.read().decode())
            return result.get("content", [{}])[0].get("text", "")
    except urllib.error.HTTPError as e:
        print(f"Claude API error: {e.code} {e.read().decode()}", file=sys.stderr)
        return ""


def extract_json(text: str) -> dict:
    """Extract JSON from Claude's response (may be wrapped in markdown)."""
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try extracting from ```json ... ``` block
    if "```json" in text:
        start = text.index("```json") + 7
        end = text.index("```", start)
        try:
            return json.loads(text[start:end].strip())
        except json.JSONDecodeError:
            pass
    # Try finding first { ... last }
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1:
        try:
            return json.loads(text[first_brace:last_brace + 1])
        except json.JSONDecodeError:
            pass
    return {}

# ---------------------------------------------------------------------------
# Agent prompts (abbreviated — full prompts are in migrateiq.yml)
# ---------------------------------------------------------------------------

SCANNER_SYSTEM = """You are the Scanner agent in MigrateIQ. Given a list of files
in a repository, identify all SQL-related files and classify them.

Respond with JSON: {"source_dialect": "mssql", "target_dialect": "postgresql",
"files": [{"path": "...", "category": "DDL|STORED_PROC|FUNCTION|VIEW|UDT|APP_CODE|CONFIG",
"description": "...", "dialect_features": ["..."]}],
"summary": {"total": N, "by_category": {...}}}"""

TRANSLATOR_SYSTEM = """You are the Translator agent in MigrateIQ. Translate the given
MSSQL SQL file to PostgreSQL 15+. Apply all standard translation rules:
TOP→LIMIT, ISNULL→COALESCE, IDENTITY→GENERATED ALWAYS AS IDENTITY,
NVARCHAR→VARCHAR, DATETIME2→TIMESTAMP, MONEY→NUMERIC(19,4), BIT→BOOLEAN,
CREATE PROCEDURE→CREATE OR REPLACE PROCEDURE, TRY/CATCH→EXCEPTION,
CROSS APPLY→CROSS JOIN LATERAL, FOR JSON AUTO→json_agg, MERGE→native PG15 MERGE,
[brackets]→"quotes" or unquoted, dbo.→remove, SET NOCOUNT ON→remove, GO→remove,
EXECUTE AS OWNER→SECURITY DEFINER, sp_addextendedproperty→COMMENT ON,
@@IDENTITY→RETURNING, SCOPE_IDENTITY()→RETURNING, RAISERROR→RAISE EXCEPTION,
NEXT VALUE FOR→nextval(), geography→PostGIS geography, JSON_MODIFY→jsonb_set,
OPENJSON→jsonb_array_elements, SESSION_CONTEXT→current_setting, IS_ROLEMEMBER→pg_has_role,
FREETEXTTABLE→tsvector/tsquery, WITH NATIVE_COMPILATION→remove (standard PL/pgSQL),
CREATE TYPE AS TABLE→CREATE TYPE AS composite, MEMORY_OPTIMIZED→remove.

Return ONLY the translated SQL/code. No explanations."""

VALIDATOR_SYSTEM = """You are the Validator agent in MigrateIQ. Review the original
MSSQL file and its PostgreSQL translation. Identify risks:
CRITICAL: features with no PG equivalent, data precision loss, native compilation removed
WARNING: behavioral differences (RLS, triggers, isolation), performance implications
INFO: clean translations

Respond with JSON: {"file": "...", "risks": [{"severity": "CRITICAL|WARNING|INFO",
"issue": "...", "recommendation": "..."}]}"""

# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def run_scanner(file_list: list[str]) -> dict:
    """Run the Scanner agent."""
    print("=== SCANNER AGENT ===")
    files_text = "\n".join(file_list)
    user_msg = f"Migration request: {MIGRATION_REQUEST}\n\nRepository files:\n{files_text}"
    response = call_claude(SCANNER_SYSTEM, user_msg)
    result = extract_json(response)
    print(f"Scanner found {result.get('summary', {}).get('total', 0)} files")
    return result


def run_translator(scan_results: dict) -> dict:
    """Run the Translator agent on each file."""
    print("\n=== TRANSLATOR AGENT ===")
    translations = []
    branch_name = "migrateiq/mssql-to-postgresql"
    commit_actions = []

    for file_info in scan_results.get("files", []):
        path = file_info["path"]
        print(f"  Translating: {path}")
        original = get_file_content(path)
        if not original:
            print(f"  Skipped (empty/unreadable): {path}")
            continue

        user_msg = f"Translate this file from MSSQL to PostgreSQL 15+.\n\nFile: {path}\n\n```sql\n{original}\n```"
        translated = call_claude(TRANSLATOR_SYSTEM, user_msg)

        # Strip markdown code fences if present
        if translated.startswith("```"):
            lines = translated.split("\n")
            translated = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

        commit_actions.append({
            "action": "update",
            "file_path": path,
            "content": translated,
        })
        translations.append({
            "original_path": path,
            "category": file_info.get("category", "UNKNOWN"),
            "complexity": "high" if len(original) > 100 else "low",
        })

    # Create branch and commit
    if commit_actions:
        create_branch(branch_name)
        create_commit(branch_name, "MigrateIQ: Translate MSSQL to PostgreSQL", commit_actions)
        print(f"  Committed {len(commit_actions)} files to {branch_name}")

    return {
        "branch": branch_name,
        "translations": translations,
        "summary": {"translated": len(translations), "skipped": 0, "total": len(translations)},
    }


def run_validator(scan_results: dict, translation_results: dict) -> dict:
    """Run the Validator agent on each translated file."""
    print("\n=== VALIDATOR AGENT ===")
    all_risks = {"critical": [], "warning": [], "info": []}

    for file_info in scan_results.get("files", []):
        path = file_info["path"]
        original = get_file_content(path, ref="main")
        translated = get_file_content(path, ref=translation_results.get("branch", "main"))
        if not original or not translated:
            continue

        print(f"  Validating: {path}")
        user_msg = f"Validate this translation.\n\nOriginal MSSQL:\n```sql\n{original}\n```\n\nTranslated PostgreSQL:\n```sql\n{translated}\n```"
        response = call_claude(VALIDATOR_SYSTEM, user_msg)
        result = extract_json(response)

        for risk in result.get("risks", []):
            severity = risk.get("severity", "INFO").lower()
            risk["file"] = path
            if severity == "critical":
                all_risks["critical"].append(risk)
            elif severity == "warning":
                all_risks["warning"].append(risk)
            else:
                all_risks["info"].append(risk)

    total = len(all_risks["critical"]) + len(all_risks["warning"]) + len(all_risks["info"])
    print(f"  Found: {len(all_risks['critical'])} critical, {len(all_risks['warning'])} warnings, {len(all_risks['info'])} info")

    return {
        "branch": translation_results.get("branch", ""),
        "translations": translation_results.get("translations", []),
        "validation": all_risks,
        "summary": {
            "clean": len(all_risks["info"]),
            "warnings": len(all_risks["warning"]),
            "critical": len(all_risks["critical"]),
            "total": total,
        },
    }


def run_planner(validation_results: dict) -> None:
    """Run the Planner agent to create issues, MR, and roadmap."""
    print("\n=== PLANNER AGENT ===")
    branch = validation_results.get("branch", "migrateiq/mssql-to-postgresql")
    summary = validation_results.get("summary", {})
    validation = validation_results.get("validation", {})

    # Create sub-issues for each phase
    phases = [
        ("Phase 1: Schema Migration (DDL)", "DDL", "phase-1"),
        ("Phase 2: Stored Procedures & Functions", "STORED_PROC,FUNCTION", "phase-2"),
        ("Phase 3: Views & User-Defined Types", "VIEW,UDT", "phase-3"),
        ("Phase 4: Application Code Updates", "APP_CODE,CONFIG", "phase-4"),
        ("Phase 5: Manual Review Required", "CRITICAL,WARNING", "phase-5"),
        ("Phase 6: Testing & Validation", "ALL", "phase-6"),
    ]

    issue_ids = []
    for title, categories, label in phases:
        full_title = f"[MigrateIQ] {title}"
        body = f"## {title}\n\nCreated by MigrateIQ migration flow.\n\nCategories: {categories}\n"

        if label == "phase-5":
            body += "\n### Critical Issues\n"
            for risk in validation.get("critical", []):
                body += f"- :red_circle: **{risk.get('file', '')}**: {risk.get('issue', '')}\n"
            body += "\n### Warnings\n"
            for risk in validation.get("warning", []):
                body += f"- :warning: **{risk.get('file', '')}**: {risk.get('issue', '')}\n"

        result = create_issue(full_title, body, f"migrateiq,migration,{label}")
        iid = result.get("iid", "?")
        issue_ids.append(iid)
        print(f"  Created issue #{iid}: {full_title}")

    # Create merge request
    mr_desc = f"""## MigrateIQ: MSSQL to PostgreSQL Migration

### Summary
- Files translated: {summary.get('clean', 0) + summary.get('warnings', 0) + summary.get('critical', 0)}
- Clean translations: {summary.get('clean', 0)}
- Warnings: {summary.get('warnings', 0)}
- Critical issues: {summary.get('critical', 0)}

### Phase Issues
{chr(10).join(f'- #{iid}' for iid in issue_ids)}

---
:robot: Generated by MigrateIQ
"""
    mr = create_merge_request(branch, "main", "MigrateIQ: MSSQL to PostgreSQL Migration", mr_desc)
    mr_iid = mr.get("iid", "?")
    print(f"  Created MR !{mr_iid}")

    # Post roadmap on parent issue
    if ISSUE_IID:
        roadmap = f"""## :world_map: MigrateIQ Migration Roadmap

### Summary
| Metric | Value |
|--------|-------|
| Files translated | {summary.get('clean', 0) + summary.get('warnings', 0) + summary.get('critical', 0)} |
| :white_check_mark: Clean | {summary.get('clean', 0)} |
| :warning: Warnings | {summary.get('warnings', 0)} |
| :red_circle: Critical | {summary.get('critical', 0)} |

### Execution Order
1. Phase 1: Schema (#{issue_ids[0]})
2. Phase 3: Views & UDTs (#{issue_ids[2]})
3. Phase 2: Procedures & Functions (#{issue_ids[1]})
4. Phase 4: Application Code (#{issue_ids[3]})
5. Phase 5: Manual Review (#{issue_ids[4]})
6. Phase 6: Testing (#{issue_ids[5]})

### Merge Request
See !{mr_iid} for all translated files.

---
:robot: Generated by MigrateIQ — Database Migration Intelligence for GitLab
"""
        post_issue_note(ISSUE_IID, roadmap)
        print(f"  Posted roadmap on issue #{ISSUE_IID}")

    print("\n=== MIGRATION PLAN COMPLETE ===")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("MigrateIQ External Agent Orchestrator")
    print(f"Project: {PROJECT_ID}")
    print(f"Request: {MIGRATION_REQUEST}")
    print()

    # Initialize sustainability tracker
    tracker = create_tracker()

    # Step 1: Get file list
    tree = list_repository_tree()
    file_paths = [f["path"] for f in tree if f.get("type") == "blob"]
    print(f"Repository has {len(file_paths)} files\n")

    # Step 2: Scanner
    scan_results = run_scanner(file_paths)
    tracker.total_files = scan_results.get("summary", {}).get("total", 0)

    if ISSUE_IID:
        note = f"## :mag: MigrateIQ Scanner\n\nFound **{scan_results.get('summary', {}).get('total', 0)}** SQL-related files.\n"
        post_issue_note(ISSUE_IID, note)

    # Step 3: Translator
    translation_results = run_translator(scan_results)

    if ISSUE_IID:
        note = f"## :arrows_counterclockwise: MigrateIQ Translator\n\nTranslated **{translation_results.get('summary', {}).get('translated', 0)}** files to PostgreSQL.\nBranch: `{translation_results.get('branch', '')}`\n"
        post_issue_note(ISSUE_IID, note)

    # Step 4: Validator
    validation_results = run_validator(scan_results, translation_results)

    if ISSUE_IID:
        s = validation_results.get("summary", {})
        note = f"## :shield: MigrateIQ Validator\n\n| Level | Count |\n|-------|-------|\n| :white_check_mark: Clean | {s.get('clean', 0)} |\n| :warning: Warning | {s.get('warnings', 0)} |\n| :red_circle: Critical | {s.get('critical', 0)} |\n"
        post_issue_note(ISSUE_IID, note)

    # Step 5: Planner
    run_planner(validation_results)

    # Step 6: Sustainability report
    if ISSUE_IID:
        post_issue_note(ISSUE_IID, tracker.format_markdown())


if __name__ == "__main__":
    main()
