"""ctl-cash / review-rec. Concurrence is not a post. Unexplained stays unexplained."""

from __future__ import annotations

from cash_recon.models import RecConcurrence, ReconciliationMatch

UNEXPLAINED = "UNEXPLAINED_DIFFERENCE"


def _fee_ids(match: ReconciliationMatch) -> list[str]:
    found: list[str] = []
    for item in match.evidence:
        text = str(item)
        if text.startswith("fee_evidence:"):
            found.append(text.split(":", 1)[1])
        elif text.startswith("FEE-") or text.startswith("ADV-"):
            found.append(text)
    for entry in match.proposed_adjusting_entries:
        if entry.support:
            found.append(entry.support)
    return [item for item in found if item]


def review_rec(
    match: ReconciliationMatch,
    *,
    requested_status: str | None = None,
) -> RecConcurrence:
    """Refuse MATCHED on unexplained. Refuse fee stories without Kernel fee evidence."""
    requested = requested_status or match.status
    match_type = match.match_type
    reasons: list[str] = []

    if any(entry.posted for entry in match.proposed_adjusting_entries):
        return RecConcurrence(
            decision="REFUSE",
            match_type=match_type,
            kernel_status=match.status,
            reasons=["proposed fee journal is already posted; reviewer cannot post"],
            can_mark_matched=False,
            can_mark_reconciled=False,
        )

    if match_type == UNEXPLAINED or match.status == "HUMAN_REVIEW" and match_type == UNEXPLAINED:
        if requested == "MATCHED":
            reasons.append("cannot convert UNEXPLAINED_DIFFERENCE to MATCHED")
            return RecConcurrence(
                decision="REFUSE",
                match_type=match_type,
                kernel_status=match.status,
                reasons=reasons,
                can_mark_matched=False,
                can_mark_reconciled=False,
            )
        if requested == "EXPLAINED_EXCEPTION":
            reasons.append("cannot relabel unexplained residual as a fee without Kernel fee evidence")
            return RecConcurrence(
                decision="REFUSE",
                match_type=match_type,
                kernel_status=match.status,
                reasons=reasons,
                can_mark_matched=False,
                can_mark_reconciled=False,
            )
        reasons.append("unexplained difference remains unexplained; period cannot be RECONCILED")
        return RecConcurrence(
            decision="CONCUR",
            match_type=match_type,
            kernel_status=match.status,
            reasons=reasons,
            can_mark_matched=False,
            can_mark_reconciled=False,
        )

    if match_type == "FEE_NETTED":
        fee_ids = _fee_ids(match)
        if not fee_ids:
            return RecConcurrence(
                decision="REFUSE",
                match_type=match_type,
                kernel_status=match.status,
                reasons=["FEE_NETTED requires Kernel fee evidence"],
                can_mark_matched=False,
                can_mark_reconciled=False,
            )
        if requested == "MATCHED" and match.difference_minor != 0:
            return RecConcurrence(
                decision="REFUSE",
                match_type=match_type,
                kernel_status=match.status,
                reasons=["fee-netted residual is EXPLAINED_EXCEPTION, not MATCHED"],
                can_mark_matched=False,
                can_mark_reconciled=False,
            )
        return RecConcurrence(
            decision="CONCUR",
            match_type=match_type,
            kernel_status=match.status,
            reasons=[f"fee evidence {', '.join(fee_ids)}"],
            can_mark_matched=False,
            can_mark_reconciled=match.status == "EXPLAINED_EXCEPTION",
        )

    if match.status == "MATCHED" and match.difference_minor == 0:
        return RecConcurrence(
            decision="CONCUR",
            match_type=match_type,
            kernel_status=match.status,
            reasons=["Kernel MATCHED with zero difference"],
            can_mark_matched=True,
            can_mark_reconciled=True,
        )
    if match.status == "OUTSTANDING_TIMING_ITEM":
        return RecConcurrence(
            decision="CONCUR",
            match_type=match_type,
            kernel_status=match.status,
            reasons=["timing item stays outstanding"],
            can_mark_matched=False,
            can_mark_reconciled=True,
        )
    if match.status == "HUMAN_REVIEW":
        return RecConcurrence(
            decision="CONCUR",
            match_type=match_type,
            kernel_status=match.status,
            reasons=["fail-closed HUMAN_REVIEW stays on the queue; not MATCHED"],
            can_mark_matched=False,
            can_mark_reconciled=False,
        )
    return RecConcurrence(
        decision="REFUSE",
        match_type=match_type,
        kernel_status=match.status,
        reasons=["packet is not Kernel-allowed for MATCHED or RECONCILED"],
        can_mark_matched=False,
        can_mark_reconciled=False,
    )
