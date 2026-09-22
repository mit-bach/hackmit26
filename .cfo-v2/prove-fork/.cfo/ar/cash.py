"""Deterministic cash-application candidates, validation, and posting."""

from __future__ import annotations

import re
from itertools import combinations

from accrual.estimation import money
from ar.models import ARPrecedent
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
INVOICE_TOKEN_RE = re.compile(r"\b(?:AR-INV-\d+|INV-AR-\d+|INV[- ][A-Z0-9]+(?:-[A-Z0-9]+)*)\b", re.I)
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


def _token_set(value: str) -> set[str]:
    return {item for item in re.findall(r"[a-z0-9]+", (value or "").lower()) if len(item) > 2}


def _precedent_support(invoice: CustomerInvoice, payment: CustomerPayment, rows: list[ARPrecedent]) -> float:
    haystack = " ".join(
        part
        for part in [
            payment.remittance_text,
            payment.invoice_reference,
            payment.bank_reference,
            " ".join(str(value) for value in (payment.metadata or {}).values()),
            invoice.description,
            invoice.reference or "",
            invoice.invoice_id,
        ]
        if part
    )
    tokens = _token_set(haystack)
    score = 0.0
    for item in rows:
        facts = item.facts or {}
        prior_ids = [str(value) for value in facts.get("invoice_ids") or []]
        prior_desc = str(facts.get("description") or "")
        overlap = _token_set(prior_desc) & _token_set(invoice.description + " " + (invoice.reference or ""))
        if invoice.invoice_id in prior_ids:
            score += 2.0
        if overlap:
            score += min(1.5, 0.5 * len(overlap))
        if facts.get("source") == "stripe" and payment.source == "stripe":
            score += 0.25
    invoice_day = (invoice.invoice_date or "")[:10]
    due_day = (invoice.due_date or "")[:10]
    payment_day = (payment.payment_date or "")[:10]
    if payment_day and invoice_day and payment_day >= invoice_day and (not due_day or payment_day <= due_day):
        score += 0.1
    invoice_tokens = _token_set(f"{invoice.description} {invoice.reference or ''} {invoice.invoice_id}")
    remittance_tokens = _token_set(f"{payment.remittance_text} {payment.invoice_reference or ''}")
    shared = invoice_tokens & remittance_tokens
    if shared:
        score += min(2.0, 0.75 * len(shared))
    return score


def extract_invoice_ids(
    payment: CustomerPayment,
    invoices: list[CustomerInvoice] | None = None,
) -> list[str]:
    found: list[str] = []
    meta = payment.metadata or {}
    blobs = [
        payment.invoice_reference or "",
        payment.remittance_text or "",
        payment.bank_reference or "",
        str(meta.get("invoice_id") or ""),
        str(meta.get("order_id") or ""),
    ]
    for raw in blobs:
        for match in list(INVOICE_RE.findall(raw)) + list(INVOICE_TOKEN_RE.findall(raw)):
            key = re.sub(r"\s+", "-", match.upper())
            if key not in found:
                found.append(key)
    universe = invoices if invoices is not None else all_invoices()
    haystack = " ".join(blobs).upper()
    for invoice in universe:
        token = invoice.invoice_id.upper()
        if token and token in haystack and invoice.invoice_id not in found and token not in found:
            found.append(invoice.invoice_id)
    return found


def remittance_identity_conflicts(
    payment: CustomerPayment,
    customer,
    named_invoices: list[CustomerInvoice],
    customers: list[Customer],
) -> list[str]:
    conflicts: list[str] = []
    remittance = payment.remittance_text or ""
    if payment.customer_id and payment.payer_name:
        tagged = get_customer(payment.customer_id)
        aliases = [tagged.customer_name, *(tagged.aliases if tagged else [])] if tagged else []
        if tagged and not any(names_similar(payment.payer_name, name) for name in aliases if name):
            conflicts.append(
                f"Payer {payment.payer_name!r} does not match tagged customer {tagged.customer_name}"
            )
    if customer:
        for invoice in named_invoices:
            if invoice.customer_id and invoice.customer_id != customer.customer_id:
                conflicts.append(
                    f"{invoice.invoice_id} belongs to {invoice.customer_id}, not {customer.customer_id}"
                )
        for other in customers:
            if other.customer_id == customer.customer_id:
                continue
            names = [other.customer_name, *other.aliases]
            if any(name and name.lower() in remittance.lower() for name in names):
                conflicts.append(
                    f"Remittance names {other.customer_name} but payment is identified as {customer.customer_name}"
                )
    return conflicts


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
    named_ids = extract_invoice_ids(payment, universe)
    named = [get_invoice(item) or next((row for row in universe if row.invoice_id == item), None) for item in named_ids]
    named_found = [item for item in named if item is not None]
    missing_ids = [item for item, row in zip(named_ids, named) if row is None]
    identity_conflicts = remittance_identity_conflicts(payment, customer, named_found, customers)
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

    from memory.policy import memory_enabled

    used_precedents = precedents(customer.customer_id) if customer and memory_enabled() else []
    facts: list[str] = [
        f"Payment {payment.payment_id} {money(payment.amount)} {payment.currency} from {payment.payer_name}",
        f"Remittance: {payment.remittance_text or '(none)'}",
    ]
    facts.extend(customer_evidence)
    if named_ids:
        facts.append("Remittance invoice references: " + ", ".join(named_ids))
    if missing_ids:
        facts.append("Invalid remittance invoice references: " + ", ".join(missing_ids))
    if identity_conflicts:
        facts.extend(identity_conflicts)
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

    if len(exact) > 1:
        ranked = sorted(
            ((_precedent_support(invoice, payment, used_precedents), invoice) for invoice in exact),
            key=lambda item: (-item[0], item[1].invoice_id),
        )
        best_score, best_invoice = ranked[0]
        runner_up = ranked[1][0] if len(ranked) > 1 else 0.0
        if best_score >= 0.75 and best_score > runner_up:
            match_type = "precedent_context" if used_precedents else "contextual_description"
            candidates.append(
                _candidate(
                    f"C{index}",
                    [best_invoice],
                    payment,
                    match_type,
                    [
                        f"{best_invoice.invoice_id} uniquely matches remittance/precedent context "
                        f"(score {best_score:.2f})"
                    ],
                    score=0.9,
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

    # Deduplicate equivalent application sets, keeping the most specific match type.
    rank = {
        "explicit_invoice": 0,
        "explicit_multi": 0,
        "precedent_context": 1,
        "contextual_description": 1,
        "exact_amount": 2,
        "combination": 2,
        "partial_single_open": 3,
        "global_exact_amount": 4,
    }
    unique: list[CashMatchCandidate] = []
    seen_sets: dict[tuple[tuple[str, float], ...], CashMatchCandidate] = {}
    for item in candidates:
        key = tuple(sorted((row.invoice_id, row.amount) for row in item.applications))
        existing = seen_sets.get(key)
        if existing is None or rank.get(item.match_type, 9) < rank.get(existing.match_type, 9):
            seen_sets[key] = item
    unique = list(seen_sets.values())

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
        missing_invoice_ids=missing_ids,
        identity_conflicts=identity_conflicts,
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

    if facts.identity_conflicts:
        return CashApplicationProposal(
            payment_id=payment.payment_id,
            decision="HUMAN_REVIEW",
            reason="Customer identity on the remittance conflicts with the bank sender or tagged customer.",
            confidence=0.35,
            evidence_used=used + facts.identity_conflicts,
            ambiguities=list(facts.identity_conflicts),
            review_question="Which customer actually sent this payment?",
        )

    if facts.missing_invoice_ids:
        return CashApplicationProposal(
            payment_id=payment.payment_id,
            decision="HUMAN_REVIEW",
            reason="Remittance cites invoice "
            + ", ".join(facts.missing_invoice_ids)
            + " which does not exist; invalid reference.",
            confidence=0.4,
            evidence_used=used,
            ambiguities=[f"Invalid references: {', '.join(facts.missing_invoice_ids)}"],
            review_question="Which live invoice should this invalid reference apply to?",
        )

    explicit = [item for item in candidates if item.match_type in {"explicit_invoice", "explicit_multi"}]
    contextual = [item for item in candidates if item.match_type in {"precedent_context", "contextual_description"}]
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

    if len(contextual) == 1 and not explicit:
        chosen = contextual[0]
        return CashApplicationProposal(
            payment_id=payment.payment_id,
            decision="AUTO_APPLY",
            applications=chosen.applications,
            confidence=0.88,
            reason=(
                "Prior Stripe remittance pattern and current description uniquely support "
                + ", ".join(row.invoice_id for row in chosen.applications)
                + ". Current-period facts were not overwritten."
            ),
            evidence_used=used + chosen.evidence,
            precedent_used=facts.precedents,
            precedent_affected=bool(facts.precedents) or chosen.match_type == "precedent_context",
        )

    if len(explicit) == 1 and not (exact or combos) or (len(explicit) == 1 and explicit[0].match_type == "explicit_invoice"):
        chosen = explicit[0]
        # An explicit invoice plus a competing exact/combo on a different set is still strong if the memo names one invoice.
        if chosen.match_type == "explicit_invoice":
            named_outstanding = money(sum(row.amount for row in chosen.applications))
            if money(payment.amount) - named_outstanding > 0.001:
                return CashApplicationProposal(
                    payment_id=payment.payment_id,
                    decision="HUMAN_REVIEW",
                    applications=chosen.applications,
                    confidence=0.7,
                    reason=(
                        f"Payment {money(payment.amount)} exceeds named invoice outstanding "
                        f"{named_outstanding}; overpayment residual "
                        f"{money(payment.amount - named_outstanding)} must not disappear."
                    ),
                    evidence_used=used + chosen.evidence,
                    ambiguities=[f"Overpayment residual {money(payment.amount - named_outstanding)}"],
                    review_question="How should the overpayment residual be treated?",
                    precedent_used=facts.precedents,
                )
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


def strict_deterministic_cash_decision(facts: CashApplicationFacts) -> CashApplicationProposal:
    """Baseline that uses only explicit Stripe invoice metadata.

    Description overlap, unique-amount guesses, and remittance precedent are
    withheld so agentic judgment can be measured against this mode.
    """
    payment = facts.payment
    used = list(facts.facts)
    if payment.application_status in {"APPLIED", "PARTIALLY_APPLIED"}:
        return CashApplicationProposal(
            payment_id=payment.payment_id,
            decision="UNAPPLIED",
            reason="Payment was already posted; refusing to apply it again.",
            confidence=1.0,
            evidence_used=used,
        )
    explicit = [item for item in facts.candidates if item.match_type in {"explicit_invoice", "explicit_multi"}]
    if len(explicit) == 1 and explicit[0].match_type == "explicit_invoice":
        chosen = explicit[0]
        named_outstanding = money(sum(item.amount for item in chosen.applications))
        if money(payment.amount) - named_outstanding > 0.001:
            return CashApplicationProposal(
                payment_id=payment.payment_id,
                decision="HUMAN_REVIEW",
                applications=chosen.applications,
                confidence=0.7,
                reason=(
                    f"Payment {money(payment.amount)} exceeds named invoice outstanding "
                    f"{named_outstanding}; residual must not disappear."
                ),
                evidence_used=used + chosen.evidence,
                ambiguities=[f"Overpayment residual {money(payment.amount - named_outstanding)}"],
                review_question="How should the overpayment residual be treated?",
            )
        return CashApplicationProposal(
            payment_id=payment.payment_id,
            decision="AUTO_APPLY",
            applications=chosen.applications,
            confidence=0.96,
            reason="Invoice is explicitly named and the amount fits the outstanding balance.",
            evidence_used=used + chosen.evidence,
        )
    if not facts.identified_customer_id and not explicit:
        return CashApplicationProposal(
            payment_id=payment.payment_id,
            decision="UNAPPLIED",
            reason="No explicit invoice ID and payer is not uniquely identified.",
            confidence=0.35,
            evidence_used=used,
        )
    return CashApplicationProposal(
        payment_id=payment.payment_id,
        decision="HUMAN_REVIEW" if facts.candidates else "UNAPPLIED",
        confidence=0.35,
        reason="Strict baseline does not use description context or remittance precedent.",
        evidence_used=used,
        ambiguities=[item.match_type for item in facts.candidates],
        review_question="Which invoice should receive this payment?",
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
