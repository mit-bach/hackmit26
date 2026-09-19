"""Deterministic cash-application candidates, validation, and posting."""

from __future__ import annotations

import re
from itertools import combinations

from accrual.estimation import money
from ar.aging import derive_status
from ar.models import (
    CashApplicationFacts,
    CashApplicationProposal,
    CashMatchCandidate,
    Customer,
    CustomerInvoice,
    CustomerPayment,
    MatchApplication,
    ValidationResult,
)
from ar.store import (
    all_customers,
    all_invoices,
    get_customer,
    get_invoice,
    open_invoices,
    precedents,
)

INVOICE_RE = re.compile(r"INV-AR-\d+", re.I)
MATERIAL_AMOUNT = 10000.0
AUTO_APPLY_CONFIDENCE = 0.9


def normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def _levenshtein(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)
    previous = list(range(len(right) + 1))
    for i, lch in enumerate(left, start=1):
        current = [i]
        for j, rch in enumerate(right, start=1):
            insert = current[j - 1] + 1
            delete = previous[j] + 1
            replace = previous[j - 1] + (lch != rch)
            current.append(min(insert, delete, replace))
        previous = current
    return previous[-1]


def names_similar(left: str, right: str) -> bool:
    a, b = normalize_name(left), normalize_name(right)
    if not a or not b:
        return False
    if a == b or a in b or b in a:
        return True
    longest = max(len(a), len(b))
    return _levenshtein(a, b) <= (2 if longest <= 16 else 3)


def identify_customer(payment: CustomerPayment, customers: list[Customer] | None = None) -> tuple[Customer | None, float, list[str]]:
    customers = customers if customers is not None else all_customers()
    evidence: list[str] = []
    if payment.customer_id:
        match = get_customer(payment.customer_id) or next(
            (item for item in customers if item.customer_id == payment.customer_id), None
        )
        if match:
            evidence.append(f"Payment already tagged {match.customer_id}")
            return match, 0.99, evidence
    scored: list[tuple[float, Customer, str]] = []
    for customer in customers:
        names = [customer.customer_name, *customer.aliases]
        for name in names:
            if names_similar(payment.payer_name, name):
                exact = normalize_name(payment.payer_name) == normalize_name(name)
                score = 0.95 if exact else 0.8
                label = f"Payer {payment.payer_name!r} matches {name!r}"
                scored.append((score, customer, label))
                break
    if not scored:
        return None, 0.0, ["Payer could not be identified"]
    scored.sort(key=lambda item: (-item[0], item[1].customer_id))
    best = scored[0]
    if len({item[1].customer_id for item in scored if item[0] == best[0]}) > 1:
        return None, 0.4, ["Multiple customers match the payer name"]
    return best[1], best[0], [best[2]]


def extract_invoice_ids(payment: CustomerPayment) -> list[str]:
    found: list[str] = []
    for raw in (payment.invoice_reference or "", payment.remittance_text or "", payment.bank_reference or ""):
        for match in INVOICE_RE.findall(raw):
            key = match.upper()
            if key not in found:
                found.append(key)
    return found


def _candidate(
    candidate_id: str,
    invoices: list[CustomerInvoice],
    payment: CustomerPayment,
    match_type: str,
    evidence: list[str],
    *,
    amounts: list[float] | None = None,
    score: float,
    ambiguities: list[str] | None = None,
) -> CashMatchCandidate:
    if amounts is None:
        amounts = [money(item.outstanding_amount) for item in invoices]
    applications = [
        MatchApplication(invoice_id=invoice.invoice_id, amount=money(amount))
        for invoice, amount in zip(invoices, amounts)
    ]
    applied = money(sum(item.amount for item in applications))
    return CashMatchCandidate(
        candidate_id=candidate_id,
        applications=applications,
        total_applied=applied,
        unapplied_amount=money(payment.amount - applied),
        match_type=match_type,
        score=score,
        evidence=evidence,
        ambiguities=ambiguities or [],
    )


def generate_cash_candidates(
    payment: CustomerPayment,
    *,
    invoices: list[CustomerInvoice] | None = None,
    customers: list[Customer] | None = None,
) -> CashApplicationFacts:
    customers = customers if customers is not None else all_customers()
    universe = invoices if invoices is not None else all_invoices()
    customer, customer_confidence, customer_evidence = identify_customer(payment, customers)
    named_ids = extract_invoice_ids(payment)
    named = [get_invoice(item) or next((row for row in universe if row.invoice_id == item), None) for item in named_ids]
    named_found = [item for item in named if item is not None]
    stale = [item.invoice_id for item in named_found if money(item.outstanding_amount) <= 0]
    open_named = [item for item in named_found if money(item.outstanding_amount) > 0]
    customer_open = [
        item
        for item in (invoices if invoices is not None else open_invoices(customer.customer_id if customer else ""))
        if money(item.outstanding_amount) > 0
        and (customer is None or item.customer_id == customer.customer_id)
    ]
    if invoices is not None and customer is not None:
        customer_open = [
            item
            for item in invoices
            if item.customer_id == customer.customer_id and money(item.outstanding_amount) > 0
        ]
    elif invoices is not None and customer is None:
        customer_open = [item for item in invoices if money(item.outstanding_amount) > 0]

    used_precedents = precedents(customer.customer_id) if customer else []
    facts: list[str] = [
        f"Payment {payment.payment_id} {money(payment.amount)} {payment.currency} from {payment.payer_name}",
        f"Remittance: {payment.remittance_text or '(none)'}",
    ]
    facts.extend(customer_evidence)
    if named_ids:
        facts.append("Remittance invoice references: " + ", ".join(named_ids))
    if stale:
        facts.append("Stale / already-paid references: " + ", ".join(stale))
    for item in used_precedents:
        facts.append(f"Precedent {item.precedent_id}: {item.summary}")

    candidates: list[CashMatchCandidate] = []
    index = 1

    if open_named:
        amounts = [min(money(payment.amount), money(item.outstanding_amount)) for item in open_named]
        if len(open_named) == 1:
            match_type = "explicit_invoice"
            score = 0.99
            evidence = [f"Remittance names {open_named[0].invoice_id}"]
        else:
            match_type = "explicit_multi"
            score = 0.97
            evidence = [f"Remittance names {', '.join(item.invoice_id for item in open_named)}"]
        total = money(sum(amounts))
        if total > money(payment.amount):
            # Scale is not allowed; only take invoices that fit oldest-first within the payment.
            running = 0.0
            fitted: list[CustomerInvoice] = []
            fitted_amounts: list[float] = []
            for invoice in sorted(open_named, key=lambda item: item.due_date):
                take = min(money(invoice.outstanding_amount), money(payment.amount - running))
                if take <= 0:
                    continue
                fitted.append(invoice)
                fitted_amounts.append(take)
                running = money(running + take)
            open_named, amounts = fitted, fitted_amounts
        candidates.append(
            _candidate(f"C{index}", open_named, payment, match_type, evidence, amounts=amounts, score=score)
        )
        index += 1

    pool = customer_open if customer else []
    exact = [item for item in pool if money(item.outstanding_amount) == money(payment.amount)]
    for invoice in exact:
        candidates.append(
            _candidate(
                f"C{index}",
                [invoice],
                payment,
                "exact_amount",
                [f"{invoice.invoice_id} outstanding equals payment {money(payment.amount)}"],
                score=0.86,
            )
        )
        index += 1

    combo_limit = min(4, len(pool))
    seen_combo: set[tuple[str, ...]] = set()
    for size in range(2, combo_limit + 1):
        for combo in combinations(sorted(pool, key=lambda item: item.invoice_id), size):
            key = tuple(item.invoice_id for item in combo)
            if key in seen_combo:
                continue
            total = money(sum(item.outstanding_amount for item in combo))
            if total != money(payment.amount):
                continue
            seen_combo.add(key)
            candidates.append(
                _candidate(
                    f"C{index}",
                    list(combo),
                    payment,
                    "combination",
                    [f"{'+'.join(key)} sum to {total}"],
                    score=0.84,
                )
            )
            index += 1

    if customer and len(pool) == 1 and money(payment.amount) < money(pool[0].outstanding_amount) and not open_named:
        candidates.append(
            _candidate(
                f"C{index}",
                pool,
                payment,
                "partial_single_open",
                [f"Only one open invoice; apply partial {money(payment.amount)} to {pool[0].invoice_id}"],
                amounts=[money(payment.amount)],
                score=0.72,
            )
        )
        index += 1

    unique_global = [
        item
        for item in (invoices if invoices is not None else open_invoices())
        if money(item.outstanding_amount) == money(payment.amount)
    ]
    if customer is None and len(unique_global) == 1:
        candidates.append(
            _candidate(
                f"C{index}",
                unique_global,
                payment,
                "global_exact_amount",
                [f"Unidentified payer but only one open invoice equals {money(payment.amount)}"],
                score=0.55,
                ambiguities=["Customer is not identified"],
            )
        )

    # Deduplicate equivalent application sets.
    unique: list[CashMatchCandidate] = []
    seen_sets: set[tuple[tuple[str, float], ...]] = set()
    for item in candidates:
        key = tuple(sorted((row.invoice_id, row.amount) for row in item.applications))
        if key in seen_sets:
            continue
        seen_sets.add(key)
        unique.append(item)

    exact_like = [item for item in unique if item.match_type in {"exact_amount", "combination", "explicit_invoice"}]
    if len(exact_like) > 1 or len(unique) > 1:
        for item in unique:
            others = [other.candidate_id for other in unique if other.candidate_id != item.candidate_id]
            if others:
                item.ambiguities.append("Competing explanations: " + ", ".join(others))

    return CashApplicationFacts(
        payment=payment,
        identified_customer_id=customer.customer_id if customer else None,
        identified_customer_name=customer.customer_name if customer else None,
        customer_confidence=customer_confidence,
        open_invoices=pool if customer else [],
        candidates=unique,
        remittance_invoice_ids=named_ids,
        stale_invoice_ids=stale,
        precedents=[item.precedent_id for item in used_precedents],
        facts=facts,
    )


def validate_proposal(
    payment: CustomerPayment,
    proposal: CashApplicationProposal,
    invoices: list[CustomerInvoice] | None = None,
) -> ValidationResult:
    errors: list[str] = []
    invoice_map = {item.invoice_id: item for item in (invoices if invoices is not None else all_invoices())}
    applied = 0.0
    per_invoice: dict[str, float] = {}
    if proposal.decision == "AUTO_APPLY" and not proposal.applications:
        errors.append("AUTO_APPLY requires at least one invoice application.")
    for row in proposal.applications:
        if row.amount <= 0:
            errors.append(f"Negative or zero application on {row.invoice_id}.")
        invoice = invoice_map.get(row.invoice_id)
        if invoice is None:
            errors.append(f"Unknown invoice {row.invoice_id}.")
            continue
        if invoice.currency != payment.currency:
            errors.append(f"Currency mismatch on {row.invoice_id}: {invoice.currency} vs {payment.currency}.")
        if money(invoice.outstanding_amount) <= 0 or derive_status(invoice, payment.payment_date) == "PAID":
            errors.append(f"Paid invoice {row.invoice_id} cannot receive more payment.")
        if money(row.amount) - money(invoice.outstanding_amount) > 0.001:
            errors.append(
                f"Application {row.amount} exceeds outstanding {invoice.outstanding_amount} on {row.invoice_id}."
            )
        per_invoice[row.invoice_id] = money(per_invoice.get(row.invoice_id, 0) + row.amount)
        applied = money(applied + row.amount)
    if money(applied) - money(payment.amount) > 0.001:
        errors.append(f"Total applied {applied} exceeds payment {payment.amount}.")
    remainder = money(payment.amount - applied)
    if proposal.decision == "AUTO_APPLY" and remainder < 0:
        errors.append("Application does not balance.")
    if proposal.decision == "UNAPPLIED" and proposal.applications:
        errors.append("UNAPPLIED cannot include invoice applications.")
    return ValidationResult(passed=not errors, errors=errors)


def policy_cash_decision(facts: CashApplicationFacts) -> CashApplicationProposal:
    payment = facts.payment
    candidates = facts.candidates
    used = list(facts.facts)
    if payment.application_status in {"APPLIED", "PARTIALLY_APPLIED"}:
        return CashApplicationProposal(
            payment_id=payment.payment_id,
            decision="UNAPPLIED",
            reason="Payment was already posted; refusing to apply it again.",
            confidence=1.0,
            evidence_used=used,
        )

    explicit = [item for item in candidates if item.match_type in {"explicit_invoice", "explicit_multi"}]
    exact = [item for item in candidates if item.match_type == "exact_amount"]
    combos = [item for item in candidates if item.match_type == "combination"]

    if not facts.identified_customer_id and not explicit:
        return CashApplicationProposal(
            payment_id=payment.payment_id,
            decision="UNAPPLIED" if not candidates else "HUMAN_REVIEW",
            reason="Customer cannot be identified from the payer name or remittance.",
            confidence=0.4,
            evidence_used=used,
            ambiguities=["Unidentified payer"],
            review_question="Who sent this payment?",
        )

    if facts.stale_invoice_ids and not explicit:
        return CashApplicationProposal(
            payment_id=payment.payment_id,
            decision="HUMAN_REVIEW",
            reason="Remittance cites a paid or stale invoice and no live match is unique.",
            confidence=0.45,
            evidence_used=used,
            ambiguities=[f"Stale references: {', '.join(facts.stale_invoice_ids)}"],
            review_question="Which open invoice should this stale reference apply to?",
            precedent_used=facts.precedents,
            precedent_affected=False,
        )

    if len(explicit) == 1 and not (exact or combos) or (len(explicit) == 1 and explicit[0].match_type == "explicit_invoice"):
        chosen = explicit[0]
        # An explicit invoice plus a competing exact/combo on a different set is still strong if the memo names one invoice.
        if chosen.match_type == "explicit_invoice":
            return CashApplicationProposal(
                payment_id=payment.payment_id,
                decision="AUTO_APPLY",
                applications=chosen.applications,
                confidence=0.96,
                reason="Invoice is explicitly named and the amount is valid against the outstanding balance.",
                evidence_used=used + chosen.evidence,
                precedent_used=facts.precedents,
                precedent_affected=False,
            )
        if chosen.match_type == "explicit_multi":
            return CashApplicationProposal(
                payment_id=payment.payment_id,
                decision="AUTO_APPLY",
                applications=chosen.applications,
                confidence=0.94,
                reason="Remittance names multiple open invoices whose outstanding balances fit the payment.",
                evidence_used=used + chosen.evidence,
                precedent_used=facts.precedents,
                precedent_affected=False,
            )

    unique_strong = []
    seen: set[tuple[tuple[str, float], ...]] = set()
    for item in exact + combos:
        key = tuple(sorted((row.invoice_id, row.amount) for row in item.applications))
        if key in seen:
            continue
        seen.add(key)
        unique_strong.append(item)

    if len(unique_strong) > 1:
        return CashApplicationProposal(
            payment_id=payment.payment_id,
            decision="HUMAN_REVIEW",
            confidence=0.52,
            reason="Multiple equally plausible exact matches explain this payment.",
            evidence_used=used + [item.candidate_id + ": " + item.match_type for item in unique_strong],
            ambiguities=[
                f"{item.candidate_id} {item.match_type}: "
                + ", ".join(f"{row.invoice_id} ${row.amount:,.2f}" for row in item.applications)
                for item in unique_strong
            ],
            review_question="Which candidate set should receive this payment?",
            precedent_used=facts.precedents,
            precedent_affected=False,
        )

    if len(unique_strong) == 1:
        chosen = unique_strong[0]
        return CashApplicationProposal(
            payment_id=payment.payment_id,
            decision="AUTO_APPLY",
            applications=chosen.applications,
            confidence=0.91 if chosen.match_type == "exact_amount" else 0.88,
            reason=(
                "One customer has a unique invoice whose outstanding amount matches the payment."
                if chosen.match_type == "exact_amount"
                else "One combination of open invoices uniquely matches the payment amount."
            ),
            evidence_used=used + chosen.evidence,
            precedent_used=facts.precedents,
            precedent_affected=bool(facts.precedents and chosen.match_type == "combination"),
        )

    if facts.stale_invoice_ids:
        return CashApplicationProposal(
            payment_id=payment.payment_id,
            decision="HUMAN_REVIEW",
            reason="Remittance cites a paid invoice and no unique live match remains.",
            confidence=0.42,
            evidence_used=used,
            ambiguities=[f"Stale references: {', '.join(facts.stale_invoice_ids)}"],
            review_question="Apply this payment to a different open invoice?",
            precedent_used=facts.precedents,
        )

    if not candidates:
        return CashApplicationProposal(
            payment_id=payment.payment_id,
            decision="UNAPPLIED",
            reason="No plausible invoice match was found; cash stays unapplied.",
            confidence=0.7,
            evidence_used=used,
        )

    only = candidates[0]
    if only.match_type == "partial_single_open":
        return CashApplicationProposal(
            payment_id=payment.payment_id,
            decision="AUTO_APPLY",
            applications=only.applications,
            confidence=0.8,
            reason="Customer has a single open invoice; apply the payment as a partial.",
            evidence_used=used + only.evidence,
            precedent_used=facts.precedents,
        )

    return CashApplicationProposal(
        payment_id=payment.payment_id,
        decision="HUMAN_REVIEW",
        confidence=0.48,
        reason="Evidence is not unique enough to auto-apply.",
        evidence_used=used,
        ambiguities=[item.match_type for item in candidates],
        review_question="Which invoices should receive this payment?",
        precedent_used=facts.precedents,
    )


def needs_reviewer(proposal: CashApplicationProposal, facts: CashApplicationFacts) -> bool:
    if proposal.decision != "AUTO_APPLY":
        return False
    applied = money(sum(item.amount for item in proposal.applications))
    competing = len(facts.candidates) > 1
    material = applied >= MATERIAL_AMOUNT
    return competing and material and proposal.confidence < 0.95


def reviewer_policy(proposal: CashApplicationProposal, facts: CashApplicationFacts):
    from ar.models import CashReviewDecision

    competing = len(facts.candidates) > 1
    applied = money(sum(item.amount for item in proposal.applications))
    if competing and proposal.decision == "AUTO_APPLY":
        return CashReviewDecision(
            payment_id=proposal.payment_id,
            recommendation="HUMAN_REVIEW",
            agree_with_preparer=False,
            confidence=0.7,
            reasons=["Another candidate is equally plausible; do not auto-apply."],
            contradictions=[],
            equally_plausible=True,
            material=applied >= MATERIAL_AMOUNT,
        )
    return CashReviewDecision(
        payment_id=proposal.payment_id,
        recommendation=proposal.decision,
        agree_with_preparer=True,
        confidence=min(proposal.confidence + 0.02, 1.0),
        reasons=["Evidence is sufficient and no equally plausible alternative remains."],
        equally_plausible=False,
        material=applied >= MATERIAL_AMOUNT,
    )
