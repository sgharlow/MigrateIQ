"""
Tests for MigrateIQ Sustainability Module.

Covers AgentMetrics, SustainabilityReport, create_tracker, get_agent,
format_markdown, and math verification with known inputs.
"""

import pytest

from migrateiq.sustainability import (
    CO2_KG_PER_KWH,
    KWH_PER_1K_TOKENS,
    KWH_PER_DEV_HOUR,
    MANUAL_HOURS_PER_FILE,
    MANUAL_REVIEW_HOURS_PER_FILE,
    AgentMetrics,
    SustainabilityReport,
    create_tracker,
    get_agent,
)


# ---------------------------------------------------------------------------
# 1. AgentMetrics
# ---------------------------------------------------------------------------


class TestAgentMetrics:
    """Tests for AgentMetrics dataclass."""

    def test_creation_with_defaults(self):
        agent = AgentMetrics(name="TestAgent")
        assert agent.name == "TestAgent"
        assert agent.input_tokens == 0
        assert agent.output_tokens == 0
        assert agent.files_processed == 0

    def test_creation_with_values(self):
        agent = AgentMetrics(
            name="Scanner",
            input_tokens=5000,
            output_tokens=3000,
            files_processed=10,
        )
        assert agent.name == "Scanner"
        assert agent.input_tokens == 5000
        assert agent.output_tokens == 3000
        assert agent.files_processed == 10

    def test_total_tokens_property(self):
        agent = AgentMetrics(name="A", input_tokens=4000, output_tokens=6000)
        assert agent.total_tokens == 10000

    def test_total_tokens_zero_by_default(self):
        agent = AgentMetrics(name="A")
        assert agent.total_tokens == 0

    def test_estimated_kwh_calculation(self):
        # 10,000 tokens => (10000 / 1000) * 0.004 = 0.04 kWh
        agent = AgentMetrics(name="A", input_tokens=5000, output_tokens=5000)
        assert agent.estimated_kwh == pytest.approx(0.04)

    def test_estimated_kwh_zero_tokens(self):
        agent = AgentMetrics(name="A")
        assert agent.estimated_kwh == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# 2. SustainabilityReport — properties
# ---------------------------------------------------------------------------


class TestSustainabilityReportProperties:
    """Tests for SustainabilityReport computed properties."""

    @pytest.fixture()
    def two_agent_report(self) -> SustainabilityReport:
        """Report with two agents and 10 files for reusable test data."""
        return SustainabilityReport(
            agents=[
                AgentMetrics(name="A", input_tokens=3000, output_tokens=2000),
                AgentMetrics(name="B", input_tokens=7000, output_tokens=8000),
            ],
            total_files=10,
        )

    def test_total_tokens(self, two_agent_report: SustainabilityReport):
        # A: 5000, B: 15000 => 20000
        assert two_agent_report.total_tokens == 20000

    def test_total_input_tokens(self, two_agent_report: SustainabilityReport):
        assert two_agent_report.total_input_tokens == 10000

    def test_total_output_tokens(self, two_agent_report: SustainabilityReport):
        assert two_agent_report.total_output_tokens == 10000

    def test_ai_energy_kwh(self, two_agent_report: SustainabilityReport):
        # 20000 tokens => (20000/1000)*0.004 = 0.08 kWh
        assert two_agent_report.ai_energy_kwh == pytest.approx(0.08)

    def test_ai_co2_kg(self, two_agent_report: SustainabilityReport):
        # 0.08 kWh * 0.385 = 0.0308 kg
        expected = 0.08 * CO2_KG_PER_KWH
        assert two_agent_report.ai_co2_kg == pytest.approx(expected)

    def test_manual_energy_kwh(self, two_agent_report: SustainabilityReport):
        # 10 files * 2.0 hrs/file * 0.20 kWh/hr = 4.0 kWh
        assert two_agent_report.manual_energy_kwh == pytest.approx(4.0)

    def test_manual_co2_kg(self, two_agent_report: SustainabilityReport):
        # 4.0 kWh * 0.385 = 1.54 kg
        expected = 4.0 * CO2_KG_PER_KWH
        assert two_agent_report.manual_co2_kg == pytest.approx(expected)

    def test_energy_savings_percent(self, two_agent_report: SustainabilityReport):
        # (4.0 - 0.08) / 4.0 * 100 = 98.0%
        expected = ((4.0 - 0.08) / 4.0) * 100
        assert two_agent_report.energy_savings_percent == pytest.approx(expected)

    def test_hybrid_energy_kwh(self, two_agent_report: SustainabilityReport):
        # AI energy + review: 0.08 + (10 * 0.5 * 0.20) = 0.08 + 1.0 = 1.08
        expected = 0.08 + (10 * MANUAL_REVIEW_HOURS_PER_FILE * KWH_PER_DEV_HOUR)
        assert two_agent_report.hybrid_energy_kwh == pytest.approx(expected)


# ---------------------------------------------------------------------------
# 3. SustainabilityReport — edge cases
# ---------------------------------------------------------------------------


class TestSustainabilityReportEdgeCases:
    """Edge cases: zero tokens, zero files, single agent, empty agents list."""

    def test_zero_tokens_zero_files(self):
        report = SustainabilityReport(
            agents=[AgentMetrics(name="A")],
            total_files=0,
        )
        assert report.total_tokens == 0
        assert report.ai_energy_kwh == pytest.approx(0.0)
        assert report.manual_energy_kwh == pytest.approx(0.0)
        assert report.energy_savings_percent == pytest.approx(0.0)
        assert report.hybrid_energy_kwh == pytest.approx(0.0)

    def test_energy_savings_zero_files_no_division_error(self):
        """When manual_energy_kwh is 0, savings should be 0 (not ZeroDivisionError)."""
        report = SustainabilityReport(agents=[], total_files=0)
        assert report.energy_savings_percent == pytest.approx(0.0)

    def test_single_agent(self):
        agent = AgentMetrics(name="Solo", input_tokens=1000, output_tokens=1000)
        report = SustainabilityReport(agents=[agent], total_files=5)
        assert report.total_tokens == 2000
        assert report.ai_energy_kwh == pytest.approx((2000 / 1000) * KWH_PER_1K_TOKENS)
        assert report.manual_energy_kwh == pytest.approx(5 * MANUAL_HOURS_PER_FILE * KWH_PER_DEV_HOUR)

    def test_empty_agents_list(self):
        report = SustainabilityReport(agents=[], total_files=5)
        assert report.total_tokens == 0
        assert report.ai_energy_kwh == pytest.approx(0.0)
        # Manual energy still applies (files exist, dev would still work)
        assert report.manual_energy_kwh == pytest.approx(5 * MANUAL_HOURS_PER_FILE * KWH_PER_DEV_HOUR)


# ---------------------------------------------------------------------------
# 4. format_markdown
# ---------------------------------------------------------------------------


class TestFormatMarkdown:
    """Tests for SustainabilityReport.format_markdown()."""

    @pytest.fixture()
    def markdown_output(self) -> str:
        report = SustainabilityReport(
            agents=[
                AgentMetrics(name="Scanner", input_tokens=1000, output_tokens=500),
                AgentMetrics(name="Translator", input_tokens=2000, output_tokens=3000),
            ],
            total_files=5,
        )
        return report.format_markdown()

    def test_returns_string(self, markdown_output: str):
        assert isinstance(markdown_output, str)

    def test_contains_token_usage_section(self, markdown_output: str):
        assert "### Token Usage" in markdown_output

    def test_contains_energy_comparison_section(self, markdown_output: str):
        assert "### Energy Comparison" in markdown_output

    def test_contains_methodology_section(self, markdown_output: str):
        assert "### Methodology" in markdown_output

    def test_contains_agent_names(self, markdown_output: str):
        assert "Scanner" in markdown_output
        assert "Translator" in markdown_output

    def test_contains_total_row(self, markdown_output: str):
        assert "**Total**" in markdown_output

    def test_contains_savings_line(self, markdown_output: str):
        assert "Energy savings vs fully manual:" in markdown_output


# ---------------------------------------------------------------------------
# 5. create_tracker
# ---------------------------------------------------------------------------


class TestCreateTracker:
    """Tests for the create_tracker() convenience function."""

    def test_returns_sustainability_report(self):
        tracker = create_tracker()
        assert isinstance(tracker, SustainabilityReport)

    def test_has_four_agents(self):
        tracker = create_tracker()
        assert len(tracker.agents) == 4

    def test_agent_names(self):
        tracker = create_tracker()
        names = [a.name for a in tracker.agents]
        assert names == ["Scanner", "Translator", "Validator", "Planner"]

    def test_agents_start_at_zero(self):
        tracker = create_tracker()
        for agent in tracker.agents:
            assert agent.input_tokens == 0
            assert agent.output_tokens == 0
            assert agent.files_processed == 0


# ---------------------------------------------------------------------------
# 6. get_agent
# ---------------------------------------------------------------------------


class TestGetAgent:
    """Tests for the get_agent() lookup function."""

    def test_find_existing_agent(self):
        tracker = create_tracker()
        scanner = get_agent(tracker, "Scanner")
        assert scanner.name == "Scanner"

    def test_find_each_agent(self):
        tracker = create_tracker()
        for name in ("Scanner", "Translator", "Validator", "Planner"):
            agent = get_agent(tracker, name)
            assert agent.name == name

    def test_raises_value_error_for_unknown(self):
        tracker = create_tracker()
        with pytest.raises(ValueError, match="Agent 'Unknown' not found"):
            get_agent(tracker, "Unknown")


# ---------------------------------------------------------------------------
# 7. Math verification with known inputs
# ---------------------------------------------------------------------------


class TestMathVerification:
    """Verify specific numeric calculations against hand-computed values."""

    def test_10k_tokens_energy(self):
        """10,000 tokens should consume exactly 0.04 kWh."""
        agent = AgentMetrics(name="X", input_tokens=10000, output_tokens=0)
        assert agent.estimated_kwh == pytest.approx(0.04)

    def test_10_files_manual_energy(self):
        """10 files * 2.0 hrs * 0.20 kWh/hr = 4.0 kWh manual energy."""
        report = SustainabilityReport(agents=[], total_files=10)
        assert report.manual_energy_kwh == pytest.approx(4.0)

    def test_10_files_manual_co2(self):
        """4.0 kWh * 0.385 kg/kWh = 1.54 kg CO2."""
        report = SustainabilityReport(agents=[], total_files=10)
        assert report.manual_co2_kg == pytest.approx(1.54)

    def test_hybrid_energy_with_known_values(self):
        """AI (0.04 kWh) + review (10 files * 0.5 hrs * 0.20) = 0.04 + 1.0 = 1.04."""
        agent = AgentMetrics(name="X", input_tokens=5000, output_tokens=5000)
        report = SustainabilityReport(agents=[agent], total_files=10)
        assert report.hybrid_energy_kwh == pytest.approx(1.04)

    def test_constants_match_expected_values(self):
        """Guard against accidental constant changes."""
        assert KWH_PER_1K_TOKENS == 0.004
        assert KWH_PER_DEV_HOUR == 0.20
        assert CO2_KG_PER_KWH == 0.385
        assert MANUAL_HOURS_PER_FILE == 2.0
        assert MANUAL_REVIEW_HOURS_PER_FILE == 0.5
