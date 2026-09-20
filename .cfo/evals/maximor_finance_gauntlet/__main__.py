from evals.maximor_finance_gauntlet.runner import run_gauntlet, write_gauntlet


def main() -> int:
    payload = run_gauntlet(include_existing=True)
    path = write_gauntlet(payload)
    card = payload["scorecard"]
    print(
        f"Maximor Finance Gauntlet {payload['run_id']}: "
        f"{card['scenarios_passed']}/{card['total_scenarios']} passed"
    )
    for family, row in (card.get("by_family") or {}).items():
        print(f"  {family}: {row['passed']}/{row['total']} ({row['rate']:.0%})")
    print(f"Wrote {path}")
    return 0 if card["scenarios_failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
