"""
MigrateIQ Sustainability Module

Tracks token usage and estimates energy consumption for the Green Agent Prize.
Compares AI-assisted migration energy cost vs manual developer effort.

Energy estimation methodology:
- LLM inference: ~0.004 kWh per 1K tokens (based on published GPU power consumption
  estimates for A100/H100 inference at ~300W, ~150 tokens/second)
- Developer workstation: ~0.15 kWh per hour (laptop + monitor + peripherals)
- Office overhead (HVAC, lighting): ~0.05 kWh per hour per person
- Source: EPA estimates + published LLM energy research (Luccioni et al. 2023,
  Patterson et al. 2022)

References:
- "Power Hungry Processing" (Luccioni et al., 2023) - energy cost of ML inference
- "Carbon Emissions and Large Neural Network Training" (Patterson et al., 2022)
- EPA GHG Equivalencies Calculator
"""

from dataclasses import dataclass, field


# Energy constants
KWH_PER_1K_TOKENS = 0.004         # Estimated kWh per 1,000 tokens (inference)
KWH_PER_DEV_HOUR = 0.20           # Developer workstation + office overhead
CO2_KG_PER_KWH = 0.385            # US average grid carbon intensity (EPA 2024)
MANUAL_HOURS_PER_FILE = 2.0       # Estimated hours to manually translate one SQL file
MANUAL_REVIEW_HOURS_PER_FILE = 0.5  # Hours for human review of AI translation


@dataclass
class AgentMetrics:
    """Track token usage for a single agent."""
    name: str
    input_tokens: int = 0
    output_tokens: int = 0
    files_processed: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def estimated_kwh(self) -> float:
        return (self.total_tokens / 1000) * KWH_PER_1K_TOKENS


@dataclass
class SustainabilityReport:
    """Aggregate sustainability metrics across all agents."""
    agents: list[AgentMetrics] = field(default_factory=list)
    total_files: int = 0

    @property
    def total_tokens(self) -> int:
        return sum(a.total_tokens for a in self.agents)

    @property
    def total_input_tokens(self) -> int:
        return sum(a.input_tokens for a in self.agents)

    @property
    def total_output_tokens(self) -> int:
        return sum(a.output_tokens for a in self.agents)

    @property
    def ai_energy_kwh(self) -> float:
        """Energy consumed by AI inference."""
        return sum(a.estimated_kwh for a in self.agents)

    @property
    def ai_co2_kg(self) -> float:
        """CO2 emissions from AI inference."""
        return self.ai_energy_kwh * CO2_KG_PER_KWH

    @property
    def manual_energy_kwh(self) -> float:
        """Energy a human developer would consume doing this manually."""
        manual_hours = self.total_files * MANUAL_HOURS_PER_FILE
        return manual_hours * KWH_PER_DEV_HOUR

    @property
    def manual_co2_kg(self) -> float:
        """CO2 from manual developer work."""
        return self.manual_energy_kwh * CO2_KG_PER_KWH

    @property
    def energy_savings_percent(self) -> float:
        """Percentage of energy saved vs manual approach."""
        if self.manual_energy_kwh == 0:
            return 0
        return ((self.manual_energy_kwh - self.ai_energy_kwh) / self.manual_energy_kwh) * 100

    @property
    def hybrid_energy_kwh(self) -> float:
        """AI translation + human review (realistic workflow)."""
        review_hours = self.total_files * MANUAL_REVIEW_HOURS_PER_FILE
        return self.ai_energy_kwh + (review_hours * KWH_PER_DEV_HOUR)

    def format_markdown(self) -> str:
        """Generate a markdown sustainability report for GitLab issue notes."""
        lines = [
            "## :seedling: MigrateIQ Sustainability Report",
            "",
            "### Token Usage",
            "",
            "| Agent | Input Tokens | Output Tokens | Total | Est. Energy |",
            "|-------|-------------|---------------|-------|-------------|",
        ]

        for agent in self.agents:
            lines.append(
                f"| {agent.name} | {agent.input_tokens:,} | {agent.output_tokens:,} "
                f"| {agent.total_tokens:,} | {agent.estimated_kwh:.4f} kWh |"
            )

        lines.append(
            f"| **Total** | **{self.total_input_tokens:,}** | **{self.total_output_tokens:,}** "
            f"| **{self.total_tokens:,}** | **{self.ai_energy_kwh:.4f} kWh** |"
        )

        lines.extend([
            "",
            "### Energy Comparison",
            "",
            "| Approach | Energy (kWh) | CO2 (kg) | Time |",
            "|----------|-------------|----------|------|",
            f"| :robot: AI Migration (MigrateIQ) | {self.ai_energy_kwh:.4f} | {self.ai_co2_kg:.4f} | ~5 min |",
            f"| :robot: + :person: AI + Human Review | {self.hybrid_energy_kwh:.4f} | {self.hybrid_energy_kwh * CO2_KG_PER_KWH:.4f} | ~{self.total_files * MANUAL_REVIEW_HOURS_PER_FILE:.0f} hrs |",
            f"| :person: Fully Manual | {self.manual_energy_kwh:.2f} | {self.manual_co2_kg:.4f} | ~{self.total_files * MANUAL_HOURS_PER_FILE:.0f} hrs |",
            "",
            f"**Energy savings vs fully manual: {self.energy_savings_percent:.1f}%**",
            "",
            "### Methodology",
            "",
            "- LLM inference energy: ~0.004 kWh per 1K tokens (GPU inference estimate)",
            "- Developer workstation: ~0.20 kWh/hr (laptop + monitor + office overhead)",
            "- Carbon intensity: US average grid at 0.385 kg CO2/kWh (EPA 2024)",
            "- Manual estimate: ~2 hrs/file for translation, ~0.5 hrs/file for AI review",
            "",
            "---",
            ":seedling: *MigrateIQ reduces the environmental impact of database migrations*",
            "*by replacing weeks of developer workstation energy with minutes of AI inference.*",
        ])

        return "\n".join(lines)


# Convenience function for the orchestrator
def create_tracker() -> SustainabilityReport:
    """Create a new sustainability tracker."""
    return SustainabilityReport(agents=[
        AgentMetrics(name="Scanner"),
        AgentMetrics(name="Translator"),
        AgentMetrics(name="Validator"),
        AgentMetrics(name="Planner"),
    ])


def get_agent(report: SustainabilityReport, name: str) -> AgentMetrics:
    """Get an agent's metrics by name."""
    for agent in report.agents:
        if agent.name == name:
            return agent
    raise ValueError(f"Agent '{name}' not found")
