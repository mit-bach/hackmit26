from __future__ import annotations

from memory.eval import format_eval_summary, persist_eval, run_memory_evaluation


def test_memory_on_vs_off_eval_uses_real_differences(tmp_path):
    payload = run_memory_evaluation()
    metrics = payload["metrics"]
    off = metrics["memory_off"]
    on = metrics["memory_on"]
    assert metrics["cases"] >= 8
    assert off["correct"] >= 1
    assert on["correct"] >= off["correct"]
    reusable_off = metrics["reusable_precedent_cases"]["memory_off"]
    reusable_on = metrics["reusable_precedent_cases"]["memory_on"]
    assert reusable_on["investigation_steps"] <= reusable_off["investigation_steps"]
    assert on["precedent_used"] > off["precedent_used"]
    assert off["precedent_used"] == 0
    cases = {row["case_id"]: row for row in payload["cases"]}
    standard = cases["stripe_sep_standard"]
    assert standard["memory_off"]["correct"] is True
    assert standard["memory_on"]["correct"] is True
    assert standard["memory_on"]["precedent_used"] is True
    assert standard["memory_off"]["precedent_used"] is False
    assert standard["memory_on"]["retrieved"]
    contradict = cases["stripe_sep_contradictory"]
    assert contradict["memory_on"]["correct"] is True
    assert contradict["memory_on"]["precedent_used"] is False
    path = persist_eval(payload, tmp_path / "eval.json")
    assert path.exists()
    summary = format_eval_summary(payload)
    assert "Cross-period memory evaluation" in summary
    assert "Memory OFF:" in summary
    assert "Memory ON:" in summary
