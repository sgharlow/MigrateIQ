"""
Comprehensive tests for migrateiq.orchestrator module.

Tests cover all public functions with mocked external dependencies
(urllib for GitLab/Claude API calls). No real API calls are made.
"""

import base64
import json
import os
import sys
import urllib.error
from io import BytesIO
from unittest.mock import MagicMock, patch, call

import pytest

# We need to set env vars BEFORE importing the module so module-level globals
# pick them up. Use a module-level patch via conftest-style setup.
_ENV_VARS = {
    "CI_SERVER_URL": "https://gitlab.example.com",
    "CI_PROJECT_ID": "42",
    "GITLAB_TOKEN": "test-gitlab-token",
    "ANTHROPIC_API_KEY": "test-anthropic-key",
    "ANTHROPIC_BASE_URL": "https://api.anthropic.test",
    "AI_FLOW_INPUT": "Migrate MSSQL to PostgreSQL",
    "CI_ISSUE_IID": "7",
}


@pytest.fixture(autouse=True)
def _patch_module_globals():
    """Patch the module-level globals that are set from env vars at import time."""
    import migrateiq.orchestrator as orch
    original = {
        "GITLAB_URL": orch.GITLAB_URL,
        "PROJECT_ID": orch.PROJECT_ID,
        "GITLAB_TOKEN": orch.GITLAB_TOKEN,
        "ANTHROPIC_URL": orch.ANTHROPIC_URL,
        "ANTHROPIC_KEY": orch.ANTHROPIC_KEY,
        "MIGRATION_REQUEST": orch.MIGRATION_REQUEST,
        "ISSUE_IID": orch.ISSUE_IID,
        "_tracker": orch._tracker,
    }
    orch.GITLAB_URL = "https://gitlab.example.com"
    orch.PROJECT_ID = "42"
    orch.GITLAB_TOKEN = "test-gitlab-token"
    orch.ANTHROPIC_URL = "https://api.anthropic.test"
    orch.ANTHROPIC_KEY = "test-anthropic-key"
    orch.MIGRATION_REQUEST = "Migrate MSSQL to PostgreSQL"
    orch.ISSUE_IID = "7"
    yield
    # Restore originals
    for k, v in original.items():
        setattr(orch, k, v)


# =========================================================================
# extract_json tests
# =========================================================================

class TestExtractJson:
    """Tests for extract_json — all 4 code paths."""

    def test_direct_json_parse(self):
        """Direct valid JSON string should be parsed successfully."""
        from migrateiq.orchestrator import extract_json
        data = {"files": [{"path": "a.sql"}], "total": 1}
        result = extract_json(json.dumps(data))
        assert result == data

    def test_json_code_block(self):
        """JSON wrapped in ```json ... ``` markdown fences should be extracted."""
        from migrateiq.orchestrator import extract_json
        data = {"source_dialect": "mssql", "files": []}
        text = f"Here is the result:\n```json\n{json.dumps(data)}\n```\nDone."
        result = extract_json(text)
        assert result == data

    def test_brace_extraction(self):
        """JSON embedded in prose (first {{ to last }}) should be extracted."""
        from migrateiq.orchestrator import extract_json
        data = {"severity": "CRITICAL", "issue": "no equivalent"}
        text = f'The analysis shows: {json.dumps(data)} as the result.'
        result = extract_json(text)
        assert result == data

    def test_returns_empty_on_failure(self):
        """Unparseable text should return empty dict."""
        from migrateiq.orchestrator import extract_json
        result = extract_json("This is not JSON at all")
        assert result == {}

    def test_returns_empty_for_empty_string(self):
        """Empty string input should return empty dict."""
        from migrateiq.orchestrator import extract_json
        result = extract_json("")
        assert result == {}

    def test_json_block_with_whitespace(self):
        """JSON code block with extra whitespace should still parse."""
        from migrateiq.orchestrator import extract_json
        data = {"key": "value"}
        text = f"```json\n  \n{json.dumps(data)}\n  \n```"
        result = extract_json(text)
        assert result == data

    def test_nested_json(self):
        """Nested JSON objects should parse correctly."""
        from migrateiq.orchestrator import extract_json
        data = {"summary": {"total": 5, "by_category": {"DDL": 2, "STORED_PROC": 3}}}
        result = extract_json(json.dumps(data))
        assert result == data


# =========================================================================
# gitlab_api tests
# =========================================================================

class TestGitlabApi:
    """Tests for gitlab_api — success and error handling."""

    @patch("migrateiq.orchestrator.urllib.request.urlopen")
    def test_get_request_success(self, mock_urlopen):
        """Successful GET should return parsed JSON response."""
        from migrateiq.orchestrator import gitlab_api
        response_data = {"id": 1, "name": "test-branch"}
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(response_data).encode()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = gitlab_api("GET", "repository/branches")
        assert result == response_data
        # Verify the URL was constructed correctly
        req_obj = mock_urlopen.call_args[0][0]
        assert "https://gitlab.example.com/api/v4/projects/42/repository/branches" == req_obj.full_url
        assert req_obj.get_method() == "GET"

    @patch("migrateiq.orchestrator.urllib.request.urlopen")
    def test_post_request_with_data(self, mock_urlopen):
        """POST with data should send JSON-encoded body."""
        from migrateiq.orchestrator import gitlab_api
        response_data = {"iid": 10}
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(response_data).encode()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = gitlab_api("POST", "issues", {"title": "Test"})
        assert result == response_data
        req_obj = mock_urlopen.call_args[0][0]
        assert req_obj.get_method() == "POST"
        assert json.loads(req_obj.data.decode()) == {"title": "Test"}

    @patch("migrateiq.orchestrator.urllib.request.urlopen")
    def test_http_error_returns_empty_dict(self, mock_urlopen):
        """HTTPError should be caught and return empty dict."""
        from migrateiq.orchestrator import gitlab_api
        error_body = BytesIO(b"Not Found")
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="http://test", code=404, msg="Not Found",
            hdrs={}, fp=error_body,
        )
        result = gitlab_api("GET", "nonexistent")
        assert result == {}

    @patch("migrateiq.orchestrator.urllib.request.urlopen")
    def test_headers_include_private_token(self, mock_urlopen):
        """Request should include PRIVATE-TOKEN header."""
        from migrateiq.orchestrator import gitlab_api
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"{}"
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        gitlab_api("GET", "test")
        req_obj = mock_urlopen.call_args[0][0]
        assert req_obj.get_header("Private-token") == "test-gitlab-token"


# =========================================================================
# Helper function tests (post_issue_note, list_repository_tree, etc.)
# =========================================================================

class TestGitlabHelpers:
    """Tests for thin wrapper functions around gitlab_api."""

    @patch("migrateiq.orchestrator.gitlab_api")
    def test_post_issue_note(self, mock_api):
        """post_issue_note should call gitlab_api with correct endpoint and body."""
        from migrateiq.orchestrator import post_issue_note
        mock_api.return_value = {"id": 1}
        result = post_issue_note("7", "Hello")
        mock_api.assert_called_once_with("POST", "issues/7/notes", {"body": "Hello"})
        assert result == {"id": 1}

    @patch("migrateiq.orchestrator.gitlab_api")
    def test_list_repository_tree_returns_list(self, mock_api):
        """list_repository_tree should return list when API returns list."""
        from migrateiq.orchestrator import list_repository_tree
        tree = [{"path": "a.sql", "type": "blob"}]
        mock_api.return_value = tree
        result = list_repository_tree()
        assert result == tree

    @patch("migrateiq.orchestrator.gitlab_api")
    def test_list_repository_tree_returns_empty_on_dict(self, mock_api):
        """list_repository_tree should return [] when API returns dict (error)."""
        from migrateiq.orchestrator import list_repository_tree
        mock_api.return_value = {}
        result = list_repository_tree()
        assert result == []

    @patch("migrateiq.orchestrator.gitlab_api")
    def test_get_file_content_decodes_base64(self, mock_api):
        """get_file_content should base64-decode the content field."""
        from migrateiq.orchestrator import get_file_content
        raw = "SELECT * FROM dbo.Users"
        mock_api.return_value = {"content": base64.b64encode(raw.encode()).decode()}
        result = get_file_content("db/schema.sql")
        assert result == raw

    @patch("migrateiq.orchestrator.gitlab_api")
    def test_get_file_content_empty_when_no_content(self, mock_api):
        """get_file_content should return '' when content key is missing."""
        from migrateiq.orchestrator import get_file_content
        mock_api.return_value = {}
        result = get_file_content("missing.sql")
        assert result == ""

    @patch("migrateiq.orchestrator.gitlab_api")
    def test_create_branch(self, mock_api):
        """create_branch should POST with branch name and ref."""
        from migrateiq.orchestrator import create_branch
        mock_api.return_value = {"name": "feat"}
        result = create_branch("feat", "main")
        mock_api.assert_called_once_with("POST", "repository/branches", {"branch": "feat", "ref": "main"})
        assert result == {"name": "feat"}

    @patch("migrateiq.orchestrator.gitlab_api")
    def test_create_issue_with_labels(self, mock_api):
        """create_issue should include labels when provided."""
        from migrateiq.orchestrator import create_issue
        mock_api.return_value = {"iid": 5}
        create_issue("Title", "Desc", "bug,high")
        mock_api.assert_called_once_with("POST", "issues", {
            "title": "Title", "description": "Desc", "labels": "bug,high",
        })

    @patch("migrateiq.orchestrator.gitlab_api")
    def test_create_issue_without_labels(self, mock_api):
        """create_issue should omit labels key when empty string."""
        from migrateiq.orchestrator import create_issue
        mock_api.return_value = {"iid": 6}
        create_issue("Title", "Desc")
        mock_api.assert_called_once_with("POST", "issues", {
            "title": "Title", "description": "Desc",
        })


# =========================================================================
# call_claude tests
# =========================================================================

class TestCallClaude:
    """Tests for call_claude — success, token tracking, and error handling."""

    @patch("migrateiq.orchestrator.urllib.request.urlopen")
    def test_success_returns_text(self, mock_urlopen):
        """Successful Claude call should return the text from content."""
        from migrateiq.orchestrator import call_claude
        response = {
            "content": [{"type": "text", "text": "SELECT 1;"}],
            "usage": {"input_tokens": 100, "output_tokens": 50},
        }
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(response).encode()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = call_claude("system", "user")
        assert result == "SELECT 1;"

    @patch("migrateiq.orchestrator.urllib.request.urlopen")
    def test_token_tracking_with_agent_name(self, mock_urlopen):
        """When agent_name is provided and _tracker is set, tokens should be tracked."""
        import migrateiq.orchestrator as orch
        from migrateiq.sustainability import create_tracker, get_agent

        tracker = create_tracker()
        orch._tracker = tracker

        response = {
            "content": [{"type": "text", "text": "result"}],
            "usage": {"input_tokens": 200, "output_tokens": 75},
        }
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(response).encode()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        orch.call_claude("sys", "user", agent_name="Scanner")

        scanner = get_agent(tracker, "Scanner")
        assert scanner.input_tokens == 200
        assert scanner.output_tokens == 75
        assert scanner.files_processed == 1

    @patch("migrateiq.orchestrator.urllib.request.urlopen")
    def test_no_tracking_without_agent_name(self, mock_urlopen):
        """Without agent_name, token tracking should be skipped."""
        import migrateiq.orchestrator as orch
        from migrateiq.sustainability import create_tracker, get_agent

        tracker = create_tracker()
        orch._tracker = tracker

        response = {
            "content": [{"type": "text", "text": "ok"}],
            "usage": {"input_tokens": 100, "output_tokens": 50},
        }
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(response).encode()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        orch.call_claude("sys", "user")

        # No agent should have tokens tracked
        for agent in tracker.agents:
            assert agent.input_tokens == 0
            assert agent.output_tokens == 0

    @patch("migrateiq.orchestrator.urllib.request.urlopen")
    def test_http_error_returns_empty_string(self, mock_urlopen):
        """HTTPError from Claude API should return empty string."""
        from migrateiq.orchestrator import call_claude
        error_body = BytesIO(b"Rate limited")
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="http://test", code=429, msg="Too Many Requests",
            hdrs={}, fp=error_body,
        )
        result = call_claude("sys", "user")
        assert result == ""

    @patch("migrateiq.orchestrator.urllib.request.urlopen")
    def test_request_uses_correct_url_and_headers(self, mock_urlopen):
        """Claude request should use ANTHROPIC_URL and include API key header."""
        from migrateiq.orchestrator import call_claude
        response = {"content": [{"text": "x"}], "usage": {}}
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(response).encode()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        call_claude("sys", "msg")
        req_obj = mock_urlopen.call_args[0][0]
        assert req_obj.full_url == "https://api.anthropic.test/v1/messages"
        assert req_obj.get_header("X-api-key") == "test-anthropic-key"
        assert req_obj.get_header("Anthropic-version") == "2023-06-01"


# =========================================================================
# run_scanner tests
# =========================================================================

class TestRunScanner:
    """Tests for run_scanner — delegates to call_claude + extract_json."""

    @patch("migrateiq.orchestrator.call_claude")
    def test_returns_parsed_scan_results(self, mock_claude):
        """run_scanner should pass file list to Claude and return parsed JSON."""
        from migrateiq.orchestrator import run_scanner
        scan_data = {
            "source_dialect": "mssql",
            "target_dialect": "postgresql",
            "files": [{"path": "schema.sql", "category": "DDL"}],
            "summary": {"total": 1, "by_category": {"DDL": 1}},
        }
        mock_claude.return_value = json.dumps(scan_data)
        result = run_scanner(["schema.sql", "README.md"])

        assert result == scan_data
        # Verify call_claude was called with Scanner agent name
        _, kwargs = mock_claude.call_args
        assert kwargs.get("agent_name") == "Scanner"

    @patch("migrateiq.orchestrator.call_claude")
    def test_handles_empty_response(self, mock_claude):
        """Empty Claude response should yield empty dict from extract_json."""
        from migrateiq.orchestrator import run_scanner
        mock_claude.return_value = ""
        result = run_scanner(["file.sql"])
        assert result == {}


# =========================================================================
# run_translator tests
# =========================================================================

class TestRunTranslator:
    """Tests for run_translator — file translation + branch/commit creation."""

    @patch("migrateiq.orchestrator.create_commit")
    @patch("migrateiq.orchestrator.create_branch")
    @patch("migrateiq.orchestrator.call_claude")
    @patch("migrateiq.orchestrator.get_file_content")
    def test_translates_files_and_creates_commit(
        self, mock_get_file, mock_claude, mock_branch, mock_commit
    ):
        """run_translator should get file content, call Claude, then create branch + commit."""
        from migrateiq.orchestrator import run_translator
        scan_results = {
            "files": [
                {"path": "db/schema.sql", "category": "DDL"},
                {"path": "db/proc.sql", "category": "STORED_PROC"},
            ],
        }
        mock_get_file.side_effect = [
            "CREATE TABLE dbo.Users (Id INT IDENTITY)",
            "CREATE PROCEDURE dbo.GetUser AS SELECT TOP 1 * FROM Users",
        ]
        mock_claude.side_effect = [
            "CREATE TABLE users (id INT GENERATED ALWAYS AS IDENTITY)",
            "CREATE OR REPLACE PROCEDURE get_user() AS $$ SELECT * FROM users LIMIT 1 $$",
        ]
        mock_branch.return_value = {"name": "migrateiq/mssql-to-postgresql"}
        mock_commit.return_value = {"id": "abc123"}

        result = run_translator(scan_results)

        assert result["branch"] == "migrateiq/mssql-to-postgresql"
        assert len(result["translations"]) == 2
        assert result["summary"]["translated"] == 2
        mock_branch.assert_called_once_with("migrateiq/mssql-to-postgresql")
        mock_commit.assert_called_once()
        # Verify commit actions contain the translated content
        commit_args = mock_commit.call_args
        actions = commit_args[0][2] if len(commit_args[0]) > 2 else commit_args[1].get("actions")
        assert len(actions) == 2
        assert actions[0]["action"] == "update"
        assert actions[0]["file_path"] == "db/schema.sql"

    @patch("migrateiq.orchestrator.create_commit")
    @patch("migrateiq.orchestrator.create_branch")
    @patch("migrateiq.orchestrator.call_claude")
    @patch("migrateiq.orchestrator.get_file_content")
    def test_skips_empty_files(
        self, mock_get_file, mock_claude, mock_branch, mock_commit
    ):
        """Files with empty content should be skipped."""
        from migrateiq.orchestrator import run_translator
        scan_results = {"files": [{"path": "empty.sql", "category": "DDL"}]}
        mock_get_file.return_value = ""

        result = run_translator(scan_results)

        assert result["summary"]["translated"] == 0
        mock_claude.assert_not_called()
        mock_branch.assert_not_called()
        mock_commit.assert_not_called()

    @patch("migrateiq.orchestrator.create_commit")
    @patch("migrateiq.orchestrator.create_branch")
    @patch("migrateiq.orchestrator.call_claude")
    @patch("migrateiq.orchestrator.get_file_content")
    def test_strips_markdown_code_fences(
        self, mock_get_file, mock_claude, mock_branch, mock_commit
    ):
        """Translated content wrapped in ``` fences should be stripped."""
        from migrateiq.orchestrator import run_translator
        scan_results = {"files": [{"path": "a.sql", "category": "DDL"}]}
        mock_get_file.return_value = "CREATE TABLE x (id INT)"
        mock_claude.return_value = "```sql\nCREATE TABLE x (id INT)\n```"
        mock_branch.return_value = {}
        mock_commit.return_value = {}

        run_translator(scan_results)

        commit_actions = mock_commit.call_args[0][2]
        # The code fence lines should be stripped
        assert not commit_actions[0]["content"].startswith("```")
        assert "CREATE TABLE x (id INT)" in commit_actions[0]["content"]

    @patch("migrateiq.orchestrator.create_commit")
    @patch("migrateiq.orchestrator.create_branch")
    @patch("migrateiq.orchestrator.call_claude")
    @patch("migrateiq.orchestrator.get_file_content")
    def test_complexity_based_on_content_length(
        self, mock_get_file, mock_claude, mock_branch, mock_commit
    ):
        """Files > 100 chars should be marked high complexity, else low."""
        from migrateiq.orchestrator import run_translator
        short_content = "SELECT 1"  # < 100 chars
        long_content = "X" * 200    # > 100 chars
        scan_results = {
            "files": [
                {"path": "short.sql", "category": "DDL"},
                {"path": "long.sql", "category": "DDL"},
            ],
        }
        mock_get_file.side_effect = [short_content, long_content]
        mock_claude.side_effect = ["translated short", "translated long"]
        mock_branch.return_value = {}
        mock_commit.return_value = {}

        result = run_translator(scan_results)

        assert result["translations"][0]["complexity"] == "low"
        assert result["translations"][1]["complexity"] == "high"


# =========================================================================
# run_validator tests
# =========================================================================

class TestRunValidator:
    """Tests for run_validator — risk categorization by severity."""

    @patch("migrateiq.orchestrator.call_claude")
    @patch("migrateiq.orchestrator.get_file_content")
    def test_categorizes_risks_by_severity(self, mock_get_file, mock_claude):
        """Risks should be sorted into critical, warning, and info buckets."""
        from migrateiq.orchestrator import run_validator
        scan_results = {
            "files": [{"path": "schema.sql"}],
        }
        translation_results = {
            "branch": "migrateiq/mssql-to-postgresql",
            "translations": [{"original_path": "schema.sql"}],
        }
        # Original and translated content
        mock_get_file.side_effect = [
            "CREATE TABLE dbo.Users (Id INT IDENTITY)",   # original (ref=main)
            "CREATE TABLE users (id INT GENERATED ALWAYS AS IDENTITY)",  # translated
        ]
        validation_response = {
            "file": "schema.sql",
            "risks": [
                {"severity": "CRITICAL", "issue": "Data loss risk", "recommendation": "Review"},
                {"severity": "WARNING", "issue": "Behavior difference", "recommendation": "Test"},
                {"severity": "INFO", "issue": "Clean translation", "recommendation": "OK"},
            ],
        }
        mock_claude.return_value = json.dumps(validation_response)

        result = run_validator(scan_results, translation_results)

        assert len(result["validation"]["critical"]) == 1
        assert len(result["validation"]["warning"]) == 1
        assert len(result["validation"]["info"]) == 1
        assert result["summary"]["critical"] == 1
        assert result["summary"]["warnings"] == 1
        assert result["summary"]["clean"] == 1
        assert result["summary"]["total"] == 3

    @patch("migrateiq.orchestrator.call_claude")
    @patch("migrateiq.orchestrator.get_file_content")
    def test_skips_files_with_missing_content(self, mock_get_file, mock_claude):
        """Files where original or translated content is empty should be skipped."""
        from migrateiq.orchestrator import run_validator
        scan_results = {"files": [{"path": "missing.sql"}]}
        translation_results = {"branch": "migrateiq/mssql-to-postgresql"}
        mock_get_file.side_effect = ["original content", ""]  # translated is empty

        result = run_validator(scan_results, translation_results)

        assert result["summary"]["total"] == 0
        mock_claude.assert_not_called()

    @patch("migrateiq.orchestrator.call_claude")
    @patch("migrateiq.orchestrator.get_file_content")
    def test_risk_entries_include_file_path(self, mock_get_file, mock_claude):
        """Each risk entry should have the file path injected."""
        from migrateiq.orchestrator import run_validator
        scan_results = {"files": [{"path": "proc.sql"}]}
        translation_results = {"branch": "test-branch"}
        mock_get_file.side_effect = ["original", "translated"]
        mock_claude.return_value = json.dumps({
            "file": "proc.sql",
            "risks": [{"severity": "WARNING", "issue": "perf"}],
        })

        result = run_validator(scan_results, translation_results)

        assert result["validation"]["warning"][0]["file"] == "proc.sql"

    @patch("migrateiq.orchestrator.call_claude")
    @patch("migrateiq.orchestrator.get_file_content")
    def test_gets_translated_from_correct_branch(self, mock_get_file, mock_claude):
        """Translated file should be fetched from the translation branch, not main."""
        from migrateiq.orchestrator import run_validator
        scan_results = {"files": [{"path": "x.sql"}]}
        translation_results = {"branch": "migrateiq/mssql-to-postgresql"}
        mock_get_file.side_effect = ["orig", "trans"]
        mock_claude.return_value = json.dumps({"risks": []})

        run_validator(scan_results, translation_results)

        # First call: original from main, second call: translated from branch
        calls = mock_get_file.call_args_list
        assert calls[0] == call("x.sql", ref="main")
        assert calls[1] == call("x.sql", ref="migrateiq/mssql-to-postgresql")


# =========================================================================
# run_planner tests
# =========================================================================

class TestRunPlanner:
    """Tests for run_planner — issue creation, MR, and roadmap note."""

    @patch("migrateiq.orchestrator.post_issue_note")
    @patch("migrateiq.orchestrator.create_merge_request")
    @patch("migrateiq.orchestrator.create_issue")
    def test_creates_six_phase_issues(self, mock_issue, mock_mr, mock_note):
        """run_planner should create exactly 6 phase issues."""
        from migrateiq.orchestrator import run_planner
        mock_issue.side_effect = [
            {"iid": i} for i in range(1, 7)
        ]
        mock_mr.return_value = {"iid": 100}
        validation_results = {
            "branch": "migrateiq/mssql-to-postgresql",
            "summary": {"clean": 3, "warnings": 1, "critical": 0, "total": 4},
            "validation": {"critical": [], "warning": [], "info": []},
        }

        run_planner(validation_results)

        assert mock_issue.call_count == 6
        # Verify phase titles
        titles = [c[0][0] for c in mock_issue.call_args_list]
        assert "[MigrateIQ] Phase 1: Schema Migration (DDL)" in titles
        assert "[MigrateIQ] Phase 6: Testing & Validation" in titles

    @patch("migrateiq.orchestrator.post_issue_note")
    @patch("migrateiq.orchestrator.create_merge_request")
    @patch("migrateiq.orchestrator.create_issue")
    def test_creates_merge_request(self, mock_issue, mock_mr, mock_note):
        """run_planner should create a merge request from translation branch to main."""
        from migrateiq.orchestrator import run_planner
        mock_issue.side_effect = [{"iid": i} for i in range(1, 7)]
        mock_mr.return_value = {"iid": 50}
        validation_results = {
            "branch": "migrateiq/mssql-to-postgresql",
            "summary": {"clean": 1, "warnings": 0, "critical": 0, "total": 1},
            "validation": {"critical": [], "warning": [], "info": []},
        }

        run_planner(validation_results)

        mock_mr.assert_called_once()
        mr_args = mock_mr.call_args[0]
        assert mr_args[0] == "migrateiq/mssql-to-postgresql"  # source
        assert mr_args[1] == "main"  # target

    @patch("migrateiq.orchestrator.post_issue_note")
    @patch("migrateiq.orchestrator.create_merge_request")
    @patch("migrateiq.orchestrator.create_issue")
    def test_posts_roadmap_note_when_issue_iid_set(self, mock_issue, mock_mr, mock_note):
        """When ISSUE_IID is set, a roadmap note should be posted."""
        from migrateiq.orchestrator import run_planner
        mock_issue.side_effect = [{"iid": i} for i in range(1, 7)]
        mock_mr.return_value = {"iid": 50}
        validation_results = {
            "branch": "migrateiq/mssql-to-postgresql",
            "summary": {"clean": 2, "warnings": 1, "critical": 0, "total": 3},
            "validation": {"critical": [], "warning": [], "info": []},
        }

        run_planner(validation_results)

        mock_note.assert_called_once()
        note_args = mock_note.call_args[0]
        assert note_args[0] == "7"  # ISSUE_IID
        assert "Migration Roadmap" in note_args[1]
        assert "!50" in note_args[1]  # MR reference

    @patch("migrateiq.orchestrator.post_issue_note")
    @patch("migrateiq.orchestrator.create_merge_request")
    @patch("migrateiq.orchestrator.create_issue")
    def test_no_roadmap_when_issue_iid_empty(self, mock_issue, mock_mr, mock_note):
        """When ISSUE_IID is empty, no roadmap note should be posted."""
        import migrateiq.orchestrator as orch
        orch.ISSUE_IID = ""  # override to empty

        mock_issue.side_effect = [{"iid": i} for i in range(1, 7)]
        mock_mr.return_value = {"iid": 50}
        validation_results = {
            "branch": "migrateiq/mssql-to-postgresql",
            "summary": {"clean": 0, "warnings": 0, "critical": 0, "total": 0},
            "validation": {"critical": [], "warning": [], "info": []},
        }

        orch.run_planner(validation_results)

        mock_note.assert_not_called()

    @patch("migrateiq.orchestrator.post_issue_note")
    @patch("migrateiq.orchestrator.create_merge_request")
    @patch("migrateiq.orchestrator.create_issue")
    def test_phase5_includes_critical_and_warning_risks(self, mock_issue, mock_mr, mock_note):
        """Phase 5 issue body should list critical issues and warnings."""
        from migrateiq.orchestrator import run_planner
        mock_issue.side_effect = [{"iid": i} for i in range(1, 7)]
        mock_mr.return_value = {"iid": 50}
        validation_results = {
            "branch": "migrateiq/mssql-to-postgresql",
            "summary": {"clean": 0, "warnings": 1, "critical": 1, "total": 2},
            "validation": {
                "critical": [{"file": "geo.sql", "issue": "No PostGIS extension"}],
                "warning": [{"file": "proc.sql", "issue": "Different isolation"}],
                "info": [],
            },
        }

        run_planner(validation_results)

        # Phase 5 is the 5th call (index 4)
        phase5_call = mock_issue.call_args_list[4]
        phase5_body = phase5_call[0][1]  # description argument
        assert "geo.sql" in phase5_body
        assert "No PostGIS extension" in phase5_body
        assert "proc.sql" in phase5_body
        assert "Different isolation" in phase5_body

    @patch("migrateiq.orchestrator.post_issue_note")
    @patch("migrateiq.orchestrator.create_merge_request")
    @patch("migrateiq.orchestrator.create_issue")
    def test_issues_have_migrateiq_labels(self, mock_issue, mock_mr, mock_note):
        """Each phase issue should have migrateiq and migration labels."""
        from migrateiq.orchestrator import run_planner
        mock_issue.side_effect = [{"iid": i} for i in range(1, 7)]
        mock_mr.return_value = {"iid": 50}
        validation_results = {
            "branch": "b",
            "summary": {"clean": 0, "warnings": 0, "critical": 0, "total": 0},
            "validation": {"critical": [], "warning": [], "info": []},
        }

        run_planner(validation_results)

        for i, c in enumerate(mock_issue.call_args_list):
            labels = c[0][2]  # labels argument
            assert "migrateiq" in labels
            assert "migration" in labels
            assert f"phase-{i + 1}" in labels
