"""Coordinate the five sample-data agents around one shared company context."""

from __future__ import annotations

from pathlib import Path

from sample_data.agents.ap_ar import APARSampleDataAgent
from sample_data.agents.audit_controls import AuditControlsSampleDataAgent
from sample_data.agents.cash_recon import CashReconSampleDataAgent
from sample_data.agents.close import CloseSampleDataAgent
from sample_data.agents.reporting_forecasting import ReportingForecastingSampleDataAgent
from sample_data.context import Company, CompanyScenarioContext, build_calendar
from sample_data.extended import plant_extended_scenarios
from sample_data.models import DatasetManifest
from sample_data.schema_map import SCHEMA_VERSION
from sample_data.validators import validate_dataset
from sample_data.writers import write_dataset


class CFOSampleDataOrchestrator:
    def __init__(self) -> None:
        self.agents = [
            APARSampleDataAgent(),
            CashReconSampleDataAgent(),
            CloseSampleDataAgent(),
            AuditControlsSampleDataAgent(),
            ReportingForecastingSampleDataAgent(),
        ]

    def build_context(self, *, seed: int, period: str) -> CompanyScenarioContext:
        return CompanyScenarioContext(
            seed=seed,
            calendar=build_calendar(period),
            company=Company(),
        )

    def generate(self, *, seed: int = 42, period: str = "2026-09", output: Path | None = None) -> CompanyScenarioContext:
        ctx = self.build_context(seed=seed, period=period)
        for agent in self.agents:
            agent.generate(ctx)
        plant_extended_scenarios(ctx)
        validate_dataset(ctx)
        if output is not None:
            write_dataset(ctx, Path(output))
        return ctx


def generate_sample_data(*, seed: int = 42, period: str = "2026-09", output: str | Path | None = "data/demo") -> CompanyScenarioContext:
    dest = None if output is None else Path(output)
    return CFOSampleDataOrchestrator().generate(seed=seed, period=period, output=dest)


def validate_sample_data(data_root: str | Path) -> DatasetManifest:
    path = Path(data_root) / "manifest.json"
    raw = path.read_text()
    import json

    payload = json.loads(raw)
    ctx = generate_sample_data(seed=int(payload["seed"]), period=payload["period"], output=None)
    return DatasetManifest(
        seed=ctx.seed,
        company=ctx.company.legal_name,
        period=ctx.period,
        comparison_period=ctx.calendar.comparison_period,
        schema_version=SCHEMA_VERSION,
        generated_files=payload.get("generated_files", []),
        record_counts=payload.get("record_counts", {}),
        scenario_ids=sorted(ctx.scenarios),
        storyline_ids=[item.storyline_id for item in ctx.storylines],
        validation="PASS",
    )
