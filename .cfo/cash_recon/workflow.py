"""Month-level cash reconciliation. Python assigns; agents may only choose among candidates."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from cash_recon.demo import load_demo_dataset, seed_provider_payouts
from cash_recon.engine import PRIORITY, generate_all_candidates, propose_matches
from cash_recon.eval import evaluate_report
from cash_recon.mathutil import dollars, money_text
from cash_recon.models import (
    BankTransaction,
    CashReconciliationReport,
    FeeEvidence,
    InvestigationNote,
    LedgerEntry,
    MatchCandidate,
    MatchTrace,
    PeriodBalances,
    PreparerSelection,
    ReconciliationMatch,
    ReviewerVerdict,
    ValidationResult,
)
from cash_recon.normalize import prepare_bank, prepare_ledger
from cash_recon.store import (
    clear_period,
    get_report,
    remember_match,
    remember_report,
    remember_trace,
    save_report,
    save_trace,
)
from cash_recon.tools import bind_case
from cash_recon.validate import (
    compute_tie_out,
    control_finding_for,
    expected_disposition,
    period_status,
    validate_candidate,
)
from skills.loader import usage_from_agent

NEEDS_INVESTIGATION = {
    "FEE_NETTED",
    "TIMING_DIFFERENCE",
    "POSSIBLE_DUPLICATE_BANK_TXN",
    "POSSIBLE_DUPLICATE_REFUND",
    "POSSIBLE_DUPLICATE_LEDGER_ENTRY",
    "UNEXPLAINED_DIFFERENCE",
    "UNMATCHED_BANK",
    "UNMATCHED_LEDGER",
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def match_key_for(period: str, candidate: MatchCandidate) -> str:
    payload = "|".join(
        [
            period,
            candidate.match_type,
            ",".join(candidate.bank_transaction_ids),
            ",".join(candidate.ledger_entry_ids),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def related_candidates(candidate: MatchCandidate, universe: list[MatchCandidate]) -> list[MatchCandidate]:
    bank_ids = set(candidate.bank_transaction_ids)
    ledger_ids = set(candidate.ledger_entry_ids)
    related = []
    for item in universe:
        if bank_ids & set(item.bank_transaction_ids) or ledger_ids & set(item.ledger_entry_ids):
            related.append(item)
    return related


def explain(candidate: MatchCandidate) -> str:
    bank_ids = ", ".join(candidate.bank_transaction_ids) or "(none)"
    ledger_ids = ", ".join(candidate.ledger_entry_ids) or "(none)"
    if candidate.match_type == "EXACT_MATCH":
        return f"Bank {bank_ids} equals ledger {ledger_ids} at {money_text(candidate.bank_amount)}."
    if candidate.match_type == "GROUPED_MATCH":
        return (
            f"Ledger entries {ledger_ids} sum exactly to bank {bank_ids} "
            f"({money_text(candidate.bank_amount)})."
        )
    if candidate.match_type == "FEE_NETTED":
        if candidate.provider:
            return (
                f"{candidate.provider.title()} payout {candidate.provider_payout_id} "
                f"arrived net of processor fees and chargebacks. Bank {bank_ids} is "
                f"ledger {ledger_ids} ({money_text(candidate.ledger_amount)}) less "
                f"{money_text(abs(candidate.difference))}."
            )
        return (
            f"Wire {bank_ids} is ledger principal {ledger_ids} "
            f"({money_text(candidate.ledger_amount)}) plus bank fee "
            f"{money_text(abs(candidate.difference))}."
        )
    if candidate.match_type == "PROVIDER_PAYOUT":
        return (
            f"{(candidate.provider or 'processor').title()} payout "
            f"{candidate.provider_payout_id} matched to bank {bank_ids} "
            f"({candidate.provider_status})."
        )
    if candidate.match_type == "TIMING_DIFFERENCE":
        return (
            f"Timing difference: ledger {ledger_ids} vs bank {bank_ids}. "
            "Outstanding until the adjacent period clears."
        )
    if candidate.match_type == "UNEXPLAINED_DIFFERENCE":
        return f"Unexplained difference: {money_text(abs(candidate.difference))}"
    if candidate.match_type == "POSSIBLE_DUPLICATE_REFUND":
        return f"Possible duplicate refund {bank_ids}; one counterpart was already matched."
    if candidate.match_type == "POSSIBLE_DUPLICATE_BANK_TXN":
        return f"Possible duplicate bank transaction {bank_ids}."
    if candidate.match_type == "POSSIBLE_DUPLICATE_LEDGER_ENTRY":
        return f"Possible duplicate GL posting {ledger_ids}; one counterpart was already matched."
    if candidate.match_type == "UNMATCHED_BANK":
        return f"Unmatched bank activity {bank_ids} {money_text(candidate.bank_amount)}."
    return f"Unmatched ledger activity {ledger_ids} {money_text(candidate.ledger_amount)}."


def deterministic_prepare(candidate: MatchCandidate) -> PreparerSelection:
    disposition = expected_disposition(candidate.match_type, provider_status=candidate.provider_status)
    return PreparerSelection(
        case_id=candidate.candidate_id,
        selected_candidate_id=candidate.candidate_id,
        disposition=disposition,  # type: ignore[arg-type]
        confidence=candidate.confidence,
        reasons=[explain(candidate)],
        evidence_used=list(candidate.evidence),
        review_question="Requires human review" if disposition == "HUMAN_REVIEW" else None,
    )


def deterministic_investigate(candidate: MatchCandidate) -> InvestigationNote:
    disposition = expected_disposition(candidate.match_type, provider_status=candidate.provider_status)
    unsupported = list(candidate.ambiguities)
    findings = [explain(candidate)]
    if candidate.match_type == "UNEXPLAINED_DIFFERENCE":
        findings.append(
            "Checked fee, rounding, FX, partial payment, duplicate/missing entry, and timing. "
            "No evidence supports an explanation."
        )
        unsupported = unsupported or [
            "fee",
            "rounding",
            "foreign_exchange",
            "partial_payment",
            "duplicate_or_missing",
            "timing_difference",
        ]
    if candidate.match_type in {"POSSIBLE_DUPLICATE_REFUND", "POSSIBLE_DUPLICATE_BANK_TXN", "POSSIBLE_DUPLICATE_LEDGER_ENTRY"}:
        findings.append("Duplicate suspicion based on amount, counterparty/reference, and timing. Not auto-cleared.")
    return InvestigationNote(
        case_id=candidate.candidate_id,
        issues_investigated=[candidate.match_type],
        findings=findings,
        supported_explanations=[] if disposition == "HUMAN_REVIEW" and candidate.match_type != "FEE_NETTED" else [candidate.match_type],
        unsupported_hypotheses=unsupported,
        recommendation=disposition,  # type: ignore[arg-type]
        confidence=candidate.confidence,
        human_review=disposition == "HUMAN_REVIEW",
        evidence_used=list(candidate.evidence),
    )


def deterministic_review(
    candidate: MatchCandidate,
    preparer: PreparerSelection,
    validation: ValidationResult,
    investigation: InvestigationNote | None,
) -> ReviewerVerdict:
    disposition = expected_disposition(candidate.match_type, provider_status=candidate.provider_status)
    reasons = list(validation.reasons)
    human = validation.human_review_required or disposition == "HUMAN_REVIEW" or not validation.passed
    if not validation.passed:
        disposition = "HUMAN_REVIEW"
        reasons.append("validator_rejected_arithmetic")
    if investigation and investigation.human_review:
        human = True
        disposition = "HUMAN_REVIEW"
    reviewer_status = "HUMAN_REVIEW" if human else "CONFIRMED"
    return ReviewerVerdict(
        case_id=candidate.candidate_id,
        reviewer_status=reviewer_status,  # type: ignore[arg-type]
        disposition=disposition,  # type: ignore[arg-type]
        agree_with_preparer=preparer.disposition == disposition,
        confidence=1.0 if validation.passed else 0.2,
        reasons=reasons or ["Python validation passed"],
        arithmetic_ok=validation.passed,
        human_review=human,
    )


def _agent_prepare(candidate: MatchCandidate) -> PreparerSelection:
    from agent import run_agent
    from cash_recon.agent import preparer_agent

    try:
        return run_agent(
            preparer_agent,
            (
                f"Prepare cash reconciliation case {candidate.candidate_id}.\n"
                "Python already computed candidates. Select one candidate_id or HUMAN_REVIEW.\n"
                f"Proposed candidate:\n{candidate.model_dump_json(indent=2)}"
            ),
        )
    except Exception:
        return deterministic_prepare(candidate)


def _agent_investigate(candidate: MatchCandidate, memory_block: str = "") -> InvestigationNote:
    from agent import run_agent
    from cash_recon.agent import investigator_agent

    extra = f"\n\n{memory_block}" if memory_block else ""
    try:
        return run_agent(
            investigator_agent,
            (
                f"Investigate cash exception {candidate.candidate_id}.\n"
                "Do not invent an explanation. Copy Python amounts.\n"
                f"{candidate.model_dump_json(indent=2)}"
                f"{extra}"
            ),
        )
    except Exception:
        return deterministic_investigate(candidate)


def _agent_review(candidate: MatchCandidate, preparer: PreparerSelection, validation: ValidationResult) -> ReviewerVerdict:
    from agent import run_agent
    from cash_recon.agent import reviewer_agent

    try:
        return run_agent(
            reviewer_agent,
            (
                f"Review cash reconciliation {candidate.candidate_id}.\n"
                f"Preparer:\n{preparer.model_dump_json(indent=2)}\n"
                f"Validator:\n{validation.model_dump_json(indent=2)}\n"
                f"Candidate:\n{candidate.model_dump_json(indent=2)}"
            ),
        )
    except Exception:
        return deterministic_review(candidate, preparer, validation, None)


def _apply_agent_choice(
    proposed: MatchCandidate,
    preparer: PreparerSelection,
    related: list[MatchCandidate],
) -> MatchCandidate:
    if not preparer.selected_candidate_id:
        return proposed
    chosen = next((item for item in related if item.candidate_id == preparer.selected_candidate_id), None)
    return chosen or proposed


def finalize_match(
    *,
    period: str,
    index: int,
    candidate: MatchCandidate,
    related: list[MatchCandidate],
    bank: dict[str, BankTransaction],
    ledger: dict[str, LedgerEntry],
    preparer: PreparerSelection,
    investigation: InvestigationNote | None,
    validation: ValidationResult,
    reviewer: ReviewerVerdict,
    used_agent: bool,
    replay: bool,
    memory_lookup=None,
) -> tuple[ReconciliationMatch, MatchTrace]:
    disposition = reviewer.disposition
    if not validation.passed:
        disposition = "HUMAN_REVIEW"
    finding = control_finding_for(candidate.match_type)
    findings = [finding] if finding else []
    human = disposition == "HUMAN_REVIEW" or reviewer.human_review or validation.human_review_required
    if human:
        disposition = "HUMAN_REVIEW"
    match = ReconciliationMatch(
        reconciliation_id=f"REC-{index:03d}",
        period=period,
        match_key=match_key_for(period, candidate),
        bank_transaction_ids=list(candidate.bank_transaction_ids),
        ledger_entry_ids=list(candidate.ledger_entry_ids),
        match_type=candidate.match_type,
        bank_amount=candidate.bank_amount,
        ledger_amount=candidate.ledger_amount,
        difference=candidate.difference,
        bank_amount_minor=candidate.bank_amount_minor,
        ledger_amount_minor=candidate.ledger_amount_minor,
        difference_minor=candidate.difference_minor,
        confidence=candidate.confidence if validation.passed else 0.0,
        status=disposition,  # type: ignore[arg-type]
        explanation=explain(candidate),
        evidence=list(candidate.evidence),
        control_findings=findings,
        proposed_adjusting_entries=list(candidate.proposed_adjusting_entries),
        reviewer_status=reviewer.reviewer_status,
        human_review=human,
        candidate_id=candidate.candidate_id,
        provider=candidate.provider,
        provider_payout_id=candidate.provider_payout_id,
        provider_status=candidate.provider_status,
        calculations={
            "bank_amount_minor": candidate.bank_amount_minor,
            "ledger_amount_minor": candidate.ledger_amount_minor,
            "difference_minor": candidate.difference_minor,
            "group_sum_equals_bank": candidate.bank_amount_minor == candidate.ledger_amount_minor
            if candidate.match_type == "GROUPED_MATCH"
            else None,
        },
    )
    stored, is_new = remember_match(match)
    if not is_new:
        match = stored
        replay = True
    agents = []
    if used_agent:
        from cash_recon.agent import investigator_agent, preparer_agent, reviewer_agent

        agents = [
            usage_from_agent(preparer_agent),
            usage_from_agent(investigator_agent),
            usage_from_agent(reviewer_agent),
        ]
    trace = MatchTrace(
        reconciliation_id=match.reconciliation_id,
        period=period,
        match_type=match.match_type,
        status=match.status,
        bank_transactions=[bank[item] for item in match.bank_transaction_ids if item in bank],
        ledger_entries=[ledger[item] for item in match.ledger_entry_ids if item in ledger],
        candidates=related,
        calculations=match.calculations,
        preparer=preparer,
        investigation=investigation,
        validation=validation,
        reviewer=reviewer,
        final=match,
        proposed_journal_entries=list(match.proposed_adjusting_entries),
        human_review=match.human_review,
        evidence=list(match.evidence),
        control_findings=list(match.control_findings),
        agents=agents,
        used_agent=used_agent,
        replay=replay or not is_new,
        memory_lookup=memory_lookup,
    )
    stored_trace, trace_new = remember_trace(trace)
    if not trace_new:
        return match, stored_trace
    return match, trace


def run_cash_reconciliation(
    period: str,
    *,
    seed_demo: bool = False,
    use_agent: bool = False,
    reset: bool = False,
    seed_providers: bool = True,
    balances: PeriodBalances | None = None,
    bank: list[BankTransaction] | None = None,
    ledger: list[LedgerEntry] | None = None,
    fees: list[FeeEvidence] | None = None,
) -> CashReconciliationReport:
    if reset:
        clear_period(period)
    existing = get_report(period)
    if existing is not None and existing.matches and not reset:
        existing.replay = True
        return existing

    if seed_demo or balances is None:
        demo_balances, demo_bank, demo_ledger, demo_fees = load_demo_dataset()
        balances = balances or demo_balances
        bank = bank if bank is not None else demo_bank
        ledger = ledger if ledger is not None else demo_ledger
        fees = fees if fees is not None else demo_fees
    if balances is None or bank is None or ledger is None:
        raise ValueError("Cash reconciliation requires balances, bank activity, and ledger entries.")
    fees = fees or []
    if seed_providers:
        seed_provider_payouts()

    bank = prepare_bank(bank)
    ledger = prepare_ledger(ledger)
    bank_map = {item.transaction_id: item for item in bank}
    ledger_map = {item.entry_id: item for item in ledger}
    period_bank = [item for item in bank if item.period == period]
    period_ledger = [item for item in ledger if item.period == period]

    universe = generate_all_candidates(bank, ledger, fees, period)
    proposed = propose_matches(bank, ledger, fees, period)
    bind_case(bank=bank, ledger=ledger, fees=fees, candidates=universe)

    matches: list[ReconciliationMatch] = []
    traces: list[MatchTrace] = []
    agent_traces = []
    for index, candidate in enumerate(proposed, start=1):
        related = related_candidates(candidate, universe) or [candidate]
        if use_agent:
            preparer = _agent_prepare(candidate)
            candidate = _apply_agent_choice(candidate, preparer, related)
        else:
            preparer = deterministic_prepare(candidate)
        validation = validate_candidate(candidate, bank_map, ledger_map)
        investigation = None
        memory_lookup = None
        if candidate.match_type in NEEDS_INVESTIGATION or not validation.passed or validation.human_review_required:
            from memory.hooks import apply_cash_investigation, lookup_for_cash

            memory_lookup = lookup_for_cash(candidate, period)
            from memory.format import format_precedents

            investigation = (
                _agent_investigate(candidate, memory_block=format_precedents(memory_lookup))
                if use_agent
                else deterministic_investigate(candidate)
            )
            investigation, memory_lookup = apply_cash_investigation(candidate, investigation, memory_lookup)
        if use_agent:
            reviewer = _agent_review(candidate, preparer, validation)
            reviewer = deterministic_review(candidate, preparer, validation, investigation).model_copy(
                update={
                    "reasons": list(dict.fromkeys(reviewer.reasons + ["python_validator_authoritative"])),
                    "arithmetic_ok": validation.passed,
                    "disposition": "HUMAN_REVIEW"
                    if not validation.passed or validation.human_review_required
                    else expected_disposition(candidate.match_type, provider_status=candidate.provider_status),
                    "human_review": (not validation.passed) or validation.human_review_required,
                    "reviewer_status": "HUMAN_REVIEW"
                    if (not validation.passed) or validation.human_review_required
                    else "CONFIRMED",
                }
            )
        else:
            reviewer = deterministic_review(candidate, preparer, validation, investigation)
        match, trace = finalize_match(
            period=period,
            index=index,
            candidate=candidate,
            related=related,
            bank=bank_map,
            ledger=ledger_map,
            preparer=preparer,
            investigation=investigation,
            validation=validation,
            reviewer=reviewer,
            used_agent=use_agent,
            replay=False,
            memory_lookup=memory_lookup,
        )
        from memory.hooks import write_cash_memory

        if memory_lookup is not None and match.provider == "stripe" and match.status in {
            "MATCHED",
            "EXPLAINED_EXCEPTION",
        }:
            memory_lookup.decision = "reconcile payout net of fees and chargebacks"
        written = write_cash_memory(match, trace)
        written_id = written[0].decision_id if written is not None else None
        if memory_lookup is not None or written_id:
            trace = trace.model_copy(update={"memory_lookup": memory_lookup, "written_memory_id": written_id})
        matches.append(match)
        traces.append(trace)
        agent_traces.extend(trace.agents)

    run_id = _run_id()
    for trace in traces:
        if not trace.replay:
            save_trace(trace, run_id=run_id)

    tie = compute_tie_out(
        balances,
        period_bank,
        period_ledger,
        matches,
        period=period,
        bank=bank_map,
        ledger=ledger_map,
    )
    status = period_status(tie, matches)
    if not tie.tied:
        status = "FAILED_TIE"
        matches = [
            item.model_copy(update={"status": "HUMAN_REVIEW", "human_review": True, "reviewer_status": "HUMAN_REVIEW"})
            if item.status == "MATCHED"
            else item
            for item in matches
        ]
        status = "FAILED_TIE"

    reconciled_minor = sum(
        abs(item.bank_amount_minor)
        for item in matches
        if item.status in {"MATCHED", "EXPLAINED_EXCEPTION"} and item.bank_transaction_ids
    )
    timing_minor = sum(abs(item.ledger_amount_minor or item.bank_amount_minor) for item in matches if item.status == "OUTSTANDING_TIMING_ITEM")
    unexplained_minor = sum(abs(item.difference_minor) for item in matches if item.match_type == "UNEXPLAINED_DIFFERENCE")
    controls = []
    for item in matches:
        controls.extend(item.control_findings)

    report = CashReconciliationReport(
        period=period,
        run_id=run_id,
        started_at=_now(),
        opening_bank=balances.opening_bank,
        opening_ledger=balances.opening_ledger,
        bank_ending=tie.bank_ending,
        ledger_ending=tie.ledger_ending,
        reconciled_amount=dollars(reconciled_minor),
        outstanding_timing=dollars(timing_minor),
        unexplained_difference=dollars(unexplained_minor),
        human_review_count=sum(1 for item in matches if item.human_review),
        period_status=status,  # type: ignore[arg-type]
        arithmetic_tied=tie.tied,
        tie_out=tie,
        matches=matches,
        traces=traces,
        control_findings=list(dict.fromkeys(controls)),
        agents=agent_traces,
        used_agent=use_agent,
        replay=False,
    )
    report.metrics = evaluate_report(report, period_bank=period_bank)
    stored, is_new = remember_report(report)
    if not is_new:
        stored.replay = True
        return stored
    return save_report(report)
