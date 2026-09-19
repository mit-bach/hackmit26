# Accounts Payable Agent

A single OpenAI Agents SDK agent that three-way matches invoices against purchase orders and goods receipts, then returns **APPROVE**, **HOLD**, or **HUMAN_REVIEW**.

Python computes the facts (amount difference, exact vendor match, PO approval, receipt completeness, duplicate vendor invoice number). The model uses those facts to make the AP judgment.

## Setup

Python 3.10+ is required.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Put your real key in `.env`:

```
OPENAI_API_KEY=sk-...
```

Do not commit `.env`.

## Run

```bash
python main.py INV-001
```

The agent prints each tool call, then the decision:

```
Review INV-001

→ get_invoice("INV-001")
→ get_purchase_order("PO-101")
→ get_goods_receipt("PO-101")
→ find_duplicate_invoices("INV-001")

Invoice: INV-001
Decision: APPROVE
Confidence: 0.97
Amount difference: $0.00
Duplicate detected: no
Receipt status: FULL

Reasons:
- Invoice matches approved PO PO-101
- Invoice and PO amounts match
- Full goods receipt exists
- No duplicate invoice detected

Evidence:
- INV-001
- PO-101
- GR-101
```

## Human feedback and memory

A reviewer can correct a judgment. The correction is stored in `data/precedents.json` and later similar invoices can reuse it.

```bash
python main.py INV-017
python main.py INV-017 --correct APPROVE --note "Acme Supply Co. is the same vendor as Acme Supplies"
python main.py INV-017
python main.py --list-memory
```

The first run should be **HUMAN_REVIEW** for the vendor-name mismatch. After the correction, a later run of `INV-017` should **APPROVE** and cite `PRE-001`.

Small amount differences work the same way:

```bash
python main.py INV-011 --correct APPROVE --note "Platform surcharges and tax under 5% are allowed"
python main.py INV-013
```


## First five invoices to test

These IDs match the files in `data/`:

| Invoice | What it is | Likely decision |
|---|---|---|
| `INV-001` | Clean three-way match | APPROVE |
| `INV-011` | Amount mismatch ($10,250 vs $10,000) | HUMAN_REVIEW |
| `INV-017` | Vendor-name mismatch (`Acme Supply Co.` vs `Acme Supplies`) | HUMAN_REVIEW |
| `INV-018` | Duplicate of INV-010 | HOLD |
| `INV-016` | No purchase order | HUMAN_REVIEW |
