"""Discrepancy stress-test dataset and evaluation."""

from discrepancy.evaluate import run_discrepancy_benchmark
from discrepancy.generate import generate_discrepancy_data, generate_holdout_data

__all__ = ["generate_discrepancy_data", "generate_holdout_data", "run_discrepancy_benchmark"]
