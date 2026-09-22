"""Office host for cash: identifier ticks, Harness Handles, trusted cash.

Kernel JSON under runs/cash_recon/handles is not a Harness Handle.
This host writes harness/bots/<id>/handles/. Finance types stay out of Harness src.
"""

from __future__ import annotations

import json
from pathlib import Path

from atomic_json import write_json_atomic
from cash_recon.concur import review_rec
from cash_recon.handles import persist_rec_queue, verifier_handle
from cash_recon.identifiers import (
    choose_candidate_for_line,
    load_apply_identifier_packets,
    load_pay_identifier_packets,
)
from cash_recon.models import (
    CashReconciliationReport,
    PipeIdentifier,
    ReconciliationMatch,
    TrustedCash,
)
from cash_recon.workflow import run_cash_reconciliation
from harness_handles import default_computer_root, relative_to_computer, write_peer_handle

CASH_SLUG = "cash"
CTL_CASH_SLUG = "ctl-cash"
CLOSE_SLUG = "close"
PLANTED_UNEXPLAINED_BANK_ID = "TXN-2026-09-015"


def collect_pipe_identifiers(
    *,
    identifiers: list[PipeIdentifier] | None = None,
    apply_packets_dir: Path | None = None,
    pay_packets_dir: Path | None = None,
) -> list[PipeIdentifier]:
    rows = list(identifiers or [])
    rows.extend(load_apply_identifier_packets(apply_packets_dir))
    rows.extend(load_pay_identifier_packets(pay_packets_dir))
    return rows


def _status_for_candidate(candidate) -> str:
    if candidate.match_type in {
        "UNEXPLAINED_DIFFERENCE",
        "UNMATCHED_BANK",
        "UNMATCHED_LEDGER",
        "POSSIBLE_DUPLICATE_BANK_TXN",
        "POSSIBLE_DUPLICATE_REFUND",
        "POSSIBLE_DUPLICATE_LEDGER_ENTRY",
    }:
        return "HUMAN_REVIEW"
    if candidate.match_type == "FEE_NETTED":
        return "EXPLAINED_EXCEPTION"
    if candidate.match_type == "TIMING_DIFFERENCE":
        return "OUTSTANDING_TIMING_ITEM"
    if candidate.difference_minor == 0:
        return "MATCHED"
    return "HUMAN_REVIEW"


def _overlay_candidate(current: ReconciliationMatch, candidate) -> ReconciliationMatch:
    """Copy the Kernel candidate onto the existing match. Do not invent amounts."""
    if current.candidate_id == candidate.candidate_id:
        return current
    status = _status_for_candidate(candidate)
    return current.model_copy(
        update={
            "match_type": candidate.match_type,
            "bank_transaction_ids": list(candidate.bank_transaction_ids),
            "ledger_entry_ids": list(candidate.ledger_entry_ids),
            "bank_amount": candidate.bank_amount,
            "ledger_amount": candidate.ledger_amount,
            "difference": candidate.difference,
            "bank_amount_minor": candidate.bank_amount_minor,
            "ledger_amount_minor": candidate.ledger_amount_minor,
            "difference_minor": candidate.difference_minor,
            "confidence": candidate.confidence,
            "status": status,
            "human_review": status == "HUMAN_REVIEW",
            "reviewer_status": "HUMAN_REVIEW" if status == "HUMAN_REVIEW" else current.reviewer_status,
            "candidate_id": candidate.candidate_id,
            "evidence": list(candidate.evidence),
            "proposed_adjusting_entries": list(candidate.proposed_adjusting_entries),
            "provider": candidate.provider,
            "provider_payout_id": candidate.provider_payout_id,
            "provider_status": candidate.provider_status,
        }
    )


def tick_universe(
    report: CashReconciliationReport,
    identifiers: list[PipeIdentifier],
    *,
    require_identifier: bool = False,
) -> list[ReconciliationMatch]:
    """Re-select from Kernel candidates using apply/pay identifiers. Do not re-guess."""
    by_final = {
        trace.final.candidate_id: trace.final
        for trace in report.traces
        if trace.final.candidate_id
    }
    universe = []
    for trace in report.traces:
        universe.extend(trace.candidates or [])
    if not universe:
        universe = _matches_as_candidates(report.matches)
    cand_by_id = {item.candidate_id: item for item in universe}
    bank_ids: list[str] = []
    for match in report.matches:
        for bank_id in match.bank_transaction_ids:
            if bank_id not in bank_ids:
                bank_ids.append(bank_id)
    adjusted: list[ReconciliationMatch] = []
    used: set[str] = set()
    for bank_id in bank_ids:
        tick = choose_candidate_for_line(
            bank_id,
            universe,
            identifiers,
            require_identifier=require_identifier,
        )
        current = next(
            (item for item in report.matches if bank_id in item.bank_transaction_ids),
            None,
        )
        if current is None:
            continue
        if tick.fail_closed:
            findings = list(current.control_findings)
            if "missing_pipe_identifier" not in findings and not tick.identifier_present:
                findings.append("missing_pipe_identifier")
            if "identifier_conflict" not in findings and tick.identifier_present:
                findings.append("identifier_conflict")
            adjusted.append(
                current.model_copy(
                    update={
                        "status": "HUMAN_REVIEW",
                        "human_review": True,
                        "reviewer_status": "HUMAN_REVIEW",
                        "control_findings": findings,
                        "explanation": tick.reason,
                    }
                )
            )
            used.add(bank_id)
            continue
        selected_id = tick.selected_candidate_id
        if selected_id and selected_id in by_final:
            adjusted.append(by_final[selected_id])
            used.add(bank_id)
            continue
        if selected_id and selected_id in cand_by_id:
            adjusted.append(_overlay_candidate(current, cand_by_id[selected_id]))
            used.add(bank_id)
            continue
        adjusted.append(current)
        used.add(bank_id)
    for match in report.matches:
        if any(item in used for item in match.bank_transaction_ids):
            continue
        adjusted.append(match)
    return adjusted


def _matches_as_candidates(matches: list[ReconciliationMatch]):
    from cash_recon.models import MatchCandidate

    rows: list[MatchCandidate] = []
    for match in matches:
        if not match.candidate_id:
            continue
        rows.append(
            MatchCandidate(
                candidate_id=match.candidate_id,
                match_type=match.match_type,
                bank_transaction_ids=list(match.bank_transaction_ids),
                ledger_entry_ids=list(match.ledger_entry_ids),
                bank_amount=match.bank_amount,
                ledger_amount=match.ledger_amount,
                difference=match.difference,
                bank_amount_minor=match.bank_amount_minor,
                ledger_amount_minor=match.ledger_amount_minor,
                difference_minor=match.difference_minor,
                confidence=match.confidence,
                evidence=list(match.evidence),
            )
        )
    return rows


def write_trusted_cash_packet(
    computer_root: Path,
    report: CashReconciliationReport,
    *,
    concurrences: list,
) -> TrustedCash:
    unexplained = [
        item
        for item in report.matches
        if item.match_type == "UNEXPLAINED_DIFFERENCE" or item.bank_transaction_ids == [PLANTED_UNEXPLAINED_BANK_ID]
    ]
    unexplained_minor = sum(abs(item.difference_minor) for item in unexplained)
    refused = [item for item in concurrences if getattr(item, "decision", "") == "REFUSE"]
    kernel_allow = (
        report.period_status == "RECONCILED"
        and report.arithmetic_tied
        and unexplained_minor == 0
        and not refused
    )
    ctl_ok = bool(concurrences) and all(
        getattr(item, "decision", "") == "CONCUR" for item in concurrences
    )
    trusted = bool(kernel_allow and ctl_ok)
    reasons: list[str] = []
    if unexplained_minor:
        reasons.append(f"unexplained_difference_minor:{unexplained_minor}")
    if report.period_status != "RECONCILED":
        reasons.append(f"period_status:{report.period_status}")
    if not report.arithmetic_tied:
        reasons.append("arithmetic_not_tied")
    if refused:
        reasons.append("ctl-cash REFUSE")
    if not ctl_ok:
        reasons.append("ctl-cash has not concurred")
    dest_dir = computer_root / "workspace" / "cash" / "trusted"
    dest_dir.mkdir(parents=True, exist_ok=True)
    packet_path = dest_dir / f"{report.period}.json"
    payload = {
        "object": "trusted_cash",
        "period": report.period,
        "trusted": trusted,
        "period_status": report.period_status,
        "arithmetic_tied": report.arithmetic_tied,
        "unexplained_difference": report.unexplained_difference,
        "unexplained_difference_minor": unexplained_minor,
        "kernel_allow": kernel_allow,
        "ctl_cash": "CONCUR" if ctl_ok and not refused else "BLOCKED",
        "queue_owner": CTL_CASH_SLUG,
        "human_queue": False,
        "reasons": reasons,
        "close_may_read": True,
        "forecast_may_start": trusted,
    }
    write_json_atomic(packet_path, payload)
    close_handle = False
    if trusted:
        rel = relative_to_computer(computer_root, packet_path)
        write_peer_handle(
            computer_root,
            from_slug=CASH_SLUG,
            to_slug=CLOSE_SLUG,
            profile="coordinate",
            paths=[rel],
            prompt=(
                f"profile: coordinate\n"
                f"Trusted cash for {report.period} at {rel}. "
                "ctl-cash concurred. Kernel period_status is RECONCILED. "
                "Peer Handle is not approval. Do not start a forecast from unreconciled GL."
            ),
            extra={"trusted": True, "period": report.period, "kernelAllow": True},
        )
        close_handle = True
    return TrustedCash(
        period=report.period,
        trusted=trusted,
        period_status=report.period_status,
        unexplained_difference_minor=unexplained_minor,
        arithmetic_tied=report.arithmetic_tied,
        ctl_cash="CONCUR" if ctl_ok and not refused else "BLOCKED",
        kernel_allow=kernel_allow,
        close_handle=close_handle,
        reasons=reasons,
        packet_path=str(packet_path),
    )


def persist_harness_rec_queue(
    computer_root: Path,
    *,
    period: str,
    case_id: str,
    matches: list[ReconciliationMatch],
) -> list[Path]:
    """Kernel packets plus Harness Handles cash → ctl-cash / review-rec."""
    kernel_paths = persist_rec_queue(period=period, case_id=case_id, matches=matches)
    written = list(kernel_paths)
    dest_dir = computer_root / "workspace" / "cash" / "rec"
    dest_dir.mkdir(parents=True, exist_ok=True)
    for match in matches:
        if not (
            match.human_review
            or match.status == "HUMAN_REVIEW"
            or match.match_type == "UNEXPLAINED_DIFFERENCE"
        ):
            continue
        handle_path, packet_path = verifier_handle(match, period=period, case_id=case_id)
        computer_packet = dest_dir / f"{match.reconciliation_id}.json"
        write_json_atomic(computer_packet, json.loads(packet_path.read_text()))
        rel = relative_to_computer(computer_root, computer_packet)
        dest, _payload = write_peer_handle(
            computer_root,
            from_slug=CASH_SLUG,
            to_slug=CTL_CASH_SLUG,
            profile="review-rec",
            paths=[rel],
            prompt=(
                f"profile: review-rec\n"
                f"Concur or refuse bank-rec {match.reconciliation_id}. "
                f"Kernel status is {match.status} ({match.match_type}). "
                "Do not force MATCHED. Do not ask a human. Packet path is the evidence."
            ),
            extra={
                "kernelStatus": match.status,
                "humanQueue": False,
                "queueOwner": CTL_CASH_SLUG,
            },
        )
        written.extend([handle_path, dest, computer_packet])
    return written


def run_cash_office(
    period: str = "2026-09",
    *,
    computer_root: Path | None = None,
    identifiers: list[PipeIdentifier] | None = None,
    require_identifier: bool = True,
    seed_demo: bool = False,
    reset: bool = True,
) -> dict:
    """Kernel rec + identifier trust + Harness Handle to ctl-cash. Trusted cash if allowed."""
    computer = Path(computer_root) if computer_root is not None else default_computer_root()
    apply_dir = computer / "workspace" / "apply" / "packets"
    pay_dir = computer / "workspace" / "cash" / "expected-outflows"
    idents = collect_pipe_identifiers(
        identifiers=identifiers,
        apply_packets_dir=apply_dir,
        pay_packets_dir=pay_dir,
    )
    report = run_cash_reconciliation(
        period, seed_demo=seed_demo, use_agent=False, reset=reset
    )
    matches = tick_universe(report, idents, require_identifier=require_identifier)
    report = report.model_copy(update={"matches": matches})
    persist_harness_rec_queue(
        computer, period=period, case_id=period, matches=matches
    )
    concurrences = [review_rec(item) for item in matches]
    trusted = write_trusted_cash_packet(computer, report, concurrences=concurrences)
    return {
        "report": report,
        "identifiers": idents,
        "require_identifier": require_identifier,
        "concurrences": concurrences,
        "trusted_cash": trusted,
        "computer_root": str(computer),
    }
