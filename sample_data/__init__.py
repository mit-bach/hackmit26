"""Deterministic synthetic sample-data generation for the Office of the CFO.

Five specialized agents populate one shared ``CompanyScenarioContext``.
Python owns IDs, dates, amounts, and arithmetic. Agents may only choose
among approved scenario templates and narrative metadata.
"""

from sample_data.orchestrator import generate_sample_data, validate_sample_data

__all__ = ["generate_sample_data", "validate_sample_data"]
