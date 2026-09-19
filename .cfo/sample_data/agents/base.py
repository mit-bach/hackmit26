"""Shared agent shell. Scenario selection is deterministic; arithmetic is Python."""

from __future__ import annotations

from abc import ABC, abstractmethod

from agents import Agent

from sample_data.context import CompanyScenarioContext
from sample_data.models import ScenarioPlan
from skills import compose_instructions, skills_for


SAFETY = """
Safety rules for sample-data generation:
- Select only approved scenario templates from the registry.
- Never invent amounts, dates, IDs, or totals.
- Never decide whether debits equal credits.
- Never compute aging, forecast totals, or reconciliation differences.
- Narrative text must not encode hidden answers such as "THIS MATCHES REC-004".
""".strip()


def build_agent(name: str, role: str, output_type=ScenarioPlan) -> Agent:
    return Agent(
        name=name,
        instructions=compose_instructions(role, skills=skills_for(name), safety=SAFETY),
        output_type=output_type,
    )


class SampleDataAgent(ABC):
    name: str
    domain: str

    @abstractmethod
    def plan(self, ctx: CompanyScenarioContext) -> ScenarioPlan:
        """Choose approved templates. Seed-stable. No arithmetic."""

    @abstractmethod
    def apply(self, ctx: CompanyScenarioContext, plan: ScenarioPlan) -> None:
        """Instantiate templates using Python-owned IDs, dates, and amounts."""

    def generate(self, ctx: CompanyScenarioContext) -> ScenarioPlan:
        plan = self.plan(ctx)
        self.apply(ctx, plan)
        return plan

    def sdk_agent(self) -> Agent:
        return build_agent(self.name, f"You are the {self.name}.")
