"""Letterhead documents for the Maximor demo pack.

Text is the demo's PDF layer (same pattern as Invoice Sandbox sidecars).
Parsers still key off Invoice Number / Amount Due / PO Number labels.
"""

from __future__ import annotations

from typing import Iterable


COMPANY_BILL_TO = (
    "Maximor Demo Corp\n"
    "Accounts Payable\n"
    "245 Main Street, Floor 4\n"
    "Cambridge, MA 02142\n"
    "United States\n"
    "ap@maximor.example\n"
    "EIN 04-3829107"
)

VENDOR_DIRECTORY: dict[str, dict[str, str]] = {
    "Acme Supplies": {
        "legal_name": "Acme Supplies, Inc.",
        "address": "180 Northern Avenue, Suite 400\nBoston, MA 02210",
        "phone": "+1 617-555-0140",
        "email": "billing@acmesupplies.example",
        "tax_id": "04-2218891",
        "bank": "First National Bank  ****4410",
        "terms": "2/10 net 30",
        "remit": "ACH routing 011000390  account ****4410",
    },
    "Acme Supply Co.": {
        "legal_name": "Acme Supplies, Inc. d/b/a Acme Supply Co.",
        "address": "180 Northern Avenue, Suite 400\nBoston, MA 02210",
        "phone": "+1 617-555-0140",
        "email": "billing@acmesupplies.example",
        "tax_id": "04-2218891",
        "bank": "First National Bank  ****4410",
        "terms": "2/10 net 30",
        "remit": "ACH routing 011000390  account ****4410",
    },
    "Acme Supplies LLC": {
        "legal_name": "Acme Supplies LLC",
        "address": "22 Harbor Street\nQuincy, MA 02169",
        "phone": "+1 617-555-0199",
        "email": "ap@acmesuppliesllc.example",
        "tax_id": "04-9982104",
        "bank": "Harbor Trust  ****8802",
        "terms": "net 30",
        "remit": "Wire Harbor Trust routing 011001234  account ****8802",
    },
    "Amazon Web Services": {
        "legal_name": "Amazon Web Services, Inc.",
        "address": "410 Terry Avenue North\nSeattle, WA 98109",
        "phone": "+1 206-266-1000",
        "email": "billing@aws.amazon.example",
        "tax_id": "91-1646860",
        "bank": "Wells Fargo  ****2910",
        "terms": "net 30",
        "remit": "ACH Wells Fargo routing 121000248  account ****2910",
    },
    "Northline Fabrication": {
        "legal_name": "Northline Fabrication Corp.",
        "address": "55 Industrial Way\nSomerville, MA 02143",
        "phone": "+1 617-555-2201",
        "email": "ar@northline.example",
        "tax_id": "04-5510298",
        "bank": "Citizens Bank  ****2010",
        "terms": "net 15",
        "remit": "ACH Citizens routing 011500120  account ****2010",
    },
    "Office Depot": {
        "legal_name": "Office Depot, LLC",
        "address": "6600 North Military Trail\nBoca Raton, FL 33496",
        "phone": "+1 800-463-3768",
        "email": "ap@officedepot.example",
        "tax_id": "59-2663954",
        "bank": "Bank of America  ****1040",
        "terms": "2/10 net 30",
        "remit": "ACH Bank of America routing 011000138  account ****1040",
    },
    "Helios Hardware": {
        "legal_name": "Helios Hardware, Inc.",
        "address": "900 Concord Avenue\nCambridge, MA 02138",
        "phone": "+1 617-555-6200",
        "email": "billing@helioshardware.example",
        "tax_id": "04-7733102",
        "bank": "HSBC  ****7291",
        "terms": "net 10",
        "remit": "USD wire HSBC routing 021001088  account ****7291",
    },
    "Datadog": {
        "legal_name": "Datadog, Inc.",
        "address": "620 8th Avenue, 45th Floor\nNew York, NY 10018",
        "phone": "+1 866-329-4466",
        "email": "billing@datadog.example",
        "tax_id": "27-2825225",
        "bank": "JPMorgan Chase  ****9021",
        "terms": "net 30",
        "remit": "ACH Chase routing 021000021  account ****9021",
    },
    "Slack Technologies": {
        "legal_name": "Slack Technologies, LLC",
        "address": "500 Howard Street\nSan Francisco, CA 94105",
        "phone": "+1 415-579-9123",
        "email": "billing@slack.example",
        "tax_id": "45-3887470",
        "bank": "Silicon Valley Bank  ****1088",
        "terms": "net 30",
        "remit": "ACH SVB routing 121140399  account ****1088",
    },
    "Figma": {
        "legal_name": "Figma, Inc.",
        "address": "760 Market Street, Floor 10\nSan Francisco, CA 94102",
        "phone": "+1 415-890-5400",
        "email": "billing@figma.example",
        "tax_id": "46-5748921",
        "bank": "First Republic  ****0926",
        "terms": "net 30",
        "remit": "ACH First Republic routing 321081669  account ****0926",
    },
    "Google Cloud": {
        "legal_name": "Google LLC",
        "address": "1600 Amphitheatre Parkway\nMountain View, CA 94043",
        "phone": "+1 650-253-0000",
        "email": "billing@cloud.google.example",
        "tax_id": "77-0493581",
        "bank": "Citibank  ****6006",
        "terms": "net 30",
        "remit": "ACH Citi routing 021000089  account ****6006",
    },
    "Northwind Phantom LLC": {
        "legal_name": "Northwind Phantom LLC",
        "address": "1 Liberty Place, Suite 12\nPhiladelphia, PA 19103",
        "phone": "+1 215-555-5000",
        "email": "billing@nwphantom.example",
        "tax_id": "23-9911004",
        "bank": "Metro Community Bank  ****5000",
        "terms": "due on receipt",
        "remit": "Wire Metro Community routing 031000037  account ****5000",
    },
    "Hartford Insurance": {
        "legal_name": "Hartford Fire Insurance Company",
        "address": "One Hartford Plaza\nHartford, CT 06155",
        "phone": "+1 860-547-5000",
        "email": "billing@thehartford.example",
        "tax_id": "06-0383750",
        "bank": "Bank of America  ****2026",
        "terms": "net 15",
        "remit": "ACH Bank of America routing 011900254  account ****2026",
    },
    "Orbit Analytics": {
        "legal_name": "Orbit Analytics, Inc.",
        "address": "44 South Street\nWaltham, MA 02453",
        "phone": "+1 781-555-4410",
        "email": "billing@orbitanalytics.example",
        "tax_id": "04-6622108",
        "bank": "Eastern Bank  ****2025",
        "terms": "net 30",
        "remit": "ACH Eastern routing 011306679  account ****2025",
    },
    "Cambridge Properties": {
        "legal_name": "Cambridge Properties LLC",
        "address": "1 Kendall Square, Building 300\nCambridge, MA 02139",
        "phone": "+1 617-555-3100",
        "email": "rent@cambridgeproperties.example",
        "tax_id": "04-1199820",
        "bank": "Cambridge Trust  ****3000",
        "terms": "net 5",
        "remit": "ACH Cambridge Trust routing 011300135  account ****3000",
    },
    "Dell Technologies": {
        "legal_name": "Dell Marketing L.P.",
        "address": "One Dell Way\nRound Rock, TX 78682",
        "phone": "+1 800-289-3355",
        "email": "billing@dell.example",
        "tax_id": "74-2616805",
        "bank": "Bank of America  ****R760",
        "terms": "net 30",
        "remit": "ACH Bank of America routing 111000012  account ****R760",
    },
    "Harbor Electric": {
        "legal_name": "Harbor Electric Company",
        "address": "800 Massachusetts Avenue\nCambridge, MA 02139",
        "phone": "+1 800-555-0192",
        "email": "billing@harborelectric.example",
        "tax_id": "04-1002201",
        "bank": "State Street  ****HE01",
        "terms": "net 20",
        "remit": "ACH State Street routing 011000028  account ****HE01",
    },
    "Lindholm & Ruiz LLP": {
        "legal_name": "Lindholm & Ruiz LLP",
        "address": "100 Federal Street, 22nd Floor\nBoston, MA 02110",
        "phone": "+1 617-555-8800",
        "email": "billing@lindholmruiz.example",
        "tax_id": "04-4488210",
        "bank": "Bank of New York Mellon  ****LR01",
        "terms": "net 15",
        "remit": "ACH BNY routing 021000018  account ****LR01",
    },
    "GitHub": {
        "legal_name": "GitHub, Inc.",
        "address": "88 Colin P. Kelly Jr. Street\nSan Francisco, CA 94107",
        "phone": "+1 877-437-7443",
        "email": "billing@github.example",
        "tax_id": "94-3394628",
        "bank": "Wells Fargo  ****1002",
        "terms": "net 30",
        "remit": "ACH Wells Fargo routing 121042882  account ****1002",
    },
    "Shadow Vendor LLC": {
        "legal_name": "Shadow Vendor LLC",
        "address": "410 Market Street\nWilmington, DE 19801",
        "phone": "+1 302-555-0190",
        "email": "billing@shadowvendor.example",
        "tax_id": "51-7782104",
        "bank": "Wilmington Trust  ****9990",
        "terms": "net 30",
        "remit": "ACH Wilmington Trust routing 031100209  account ****9990",
    },
    "Freightline Logistics": {
        "legal_name": "Freightline Logistics, Inc.",
        "address": "1200 Port Boulevard\nNewark, NJ 07114",
        "phone": "+1 973-555-4412",
        "email": "billing@freightline.example",
        "tax_id": "22-3301988",
        "bank": "PNC Bank  ****FR01",
        "terms": "net 21",
        "remit": "ACH PNC routing 031207607  account ****FR01",
    },
    "Lenovo": {
        "legal_name": "Lenovo (United States) Inc.",
        "address": "8001 Development Drive\nMorrisville, NC 27560",
        "phone": "+1 855-253-6686",
        "email": "billing@lenovo.example",
        "tax_id": "56-2189993",
        "bank": "Bank of America  ****LV01",
        "terms": "net 30",
        "remit": "ACH Bank of America routing 053000196  account ****LV01",
    },
    "Misc Supplies": {
        "legal_name": "Miscellaneous Industrial Supplies Co.",
        "address": "14 Warehouse Road\nMedford, MA 02155",
        "phone": "+1 781-555-0177",
        "email": "billing@miscsupplies.example",
        "tax_id": "04-2299104",
        "bank": "Santander  ****MSC1",
        "terms": "net 30",
        "remit": "ACH Santander routing 011075150  account ****MSC1",
    },
    "Nimbus Analytics LLC": {
        "legal_name": "Nimbus Analytics LLC",
        "address": "77 Summer Street\nBoston, MA 02110",
        "phone": "+1 617-555-8008",
        "email": "ap@nimbus.example",
        "tax_id": "04-8822109",
        "bank": "Brookline Bank  ****8008",
        "terms": "net 30",
        "remit": "ACH Brookline routing 211370150  account ****8008",
    },
    "Kestrel Industrial Supply LLC": {
        "legal_name": "Kestrel Industrial Supply LLC",
        "address": "18 Ware Street\nCambridge, MA 02138",
        "phone": "+1 617-555-4419",
        "email": "billing@kestrelindustrial.example",
        "tax_id": "87-2144091",
        "bank": "First National Bank  ****4419",
        "terms": "net 30",
        "remit": "ACH routing 011000138  account ****4419",
    },
    "North Line Fab Inc": {
        "legal_name": "North Line Fab Inc",
        "address": "440 D Street\nBoston, MA 02210",
        "phone": "+1 617-555-4402",
        "email": "ar@northlinefab.example",
        "tax_id": "04-7712091",
        "bank": "Citizens Bank  ****4402",
        "terms": "net 30",
        "remit": "ACH Citizens routing 011500120  account ****4402",
    },
    "NLF Industrial Components": {
        "legal_name": "NLF Industrial Components",
        "address": "440 D Street, Suite B\nBoston, MA 02210",
        "phone": "+1 617-555-4403",
        "email": "ar@nlfindustrial.example",
        "tax_id": "04-7712288",
        "bank": "Citizens Bank  ****4403",
        "terms": "net 30",
        "remit": "ACH Citizens routing 011500120  account ****4403",
    },
    "Westbrook Tooling": {
        "legal_name": "Westbrook Tooling LLC",
        "address": "90 Westbrook Street\nWestbrook, ME 04092",
        "phone": "+1 207-555-4092",
        "email": "billing@westbrooktooling.example",
        "tax_id": "04-6621180",
        "bank": "Bangor Savings  ****4092",
        "terms": "net 30",
        "remit": "ACH Bangor routing 011201331  account ****4092",
    },
    "Halyard Facilities LLC": {
        "legal_name": "Halyard Facilities LLC",
        "address": "12 Industrial Park\nReno, NV 89502",
        "phone": "+1 775-555-9022",
        "email": "billing@halyardfacilities.example",
        "tax_id": "88-2204419",
        "bank": "Wells Fargo  ****9022",
        "terms": "net 30",
        "remit": "ACH routing 211370545  account ****9022",
    },
    "Clearing Solutions LLC": {
        "legal_name": "Clearing Solutions LLC",
        "address": "1209 Orange Street\nWilmington, DE 19801",
        "phone": "+1 302-555-1988",
        "email": "billing@clearingsolutions.example",
        "tax_id": "85-2201988",
        "bank": "Wilmington Trust  ****1988",
        "terms": "net 30",
        "remit": "ACH Wilmington Trust routing 031100209  account ****1988",
    },
    "Brightline Studio LLC": {
        "legal_name": "Brightline Studio LLC",
        "address": "14 Fayette Street\nSomerville, MA 02143",
        "phone": "+1 617-555-1144",
        "email": "billing@brightlinestudio.example",
        "tax_id": "27-9081144",
        "bank": "Brookline Bank  ****1144",
        "terms": "net 30",
        "remit": "ACH Brookline routing 211370150  account ****1144",
    },
    "Cambridge Property Services": {
        "legal_name": "Cambridge Property Services",
        "address": "1 Kendall Square\nCambridge, MA 02139",
        "phone": "+1 617-555-2190",
        "email": "billing@cambridgepropertyservices.example",
        "tax_id": "04-5518821",
        "bank": "First National Bank  ****2190",
        "terms": "net 30",
        "remit": "ACH routing 011000390  account ****2190",
    },
    "Cambridge Properties": {
        "legal_name": "Cambridge Properties LLC",
        "address": "1 Kendall Square\nCambridge, MA 02139",
        "phone": "+1 617-555-2109",
        "email": "billing@cambridgeproperties.example",
        "tax_id": "04-4418820",
        "bank": "First National Bank  ****2190",
        "terms": "net 5",
        "remit": "ACH routing 011000390  account ****2190",
    },
    "Harbor Electric Services": {
        "legal_name": "Harbor Electric Services LLC",
        "address": "200 Utility Drive\nSomerville, MA 02143",
        "phone": "+1 617-555-7719",
        "email": "billing@harborelectricservices.example",
        "tax_id": "04-2287719",
        "bank": "Citizens Bank  ****7719",
        "terms": "net 30",
        "remit": "ACH Citizens routing 011500120  account ****7719",
    },
    "Orbit Insights Corp": {
        "legal_name": "Orbit Insights Corp",
        "address": "Workbar Boston, 50 Milk Street\nBoston, MA 02109",
        "phone": "+1 617-555-4410",
        "email": "billing@orbitinsights.example",
        "tax_id": "04-8824410",
        "bank": "Santander  ****4410",
        "terms": "net 30",
        "remit": "ACH Santander routing 011075150  account ****4410",
    },
    "Freightline Expedite": {
        "legal_name": "Freightline Expedite LLC",
        "address": "400 Port Road\nNewark, NJ 07114",
        "phone": "+1 973-555-2290",
        "email": "billing@freightlineexpedite.example",
        "tax_id": "04-6612290",
        "bank": "PNC Bank  ****2290",
        "terms": "net 21",
        "remit": "ACH PNC routing 031207607  account ****2290",
    },
    "Hartford Brokerage Partners": {
        "legal_name": "Hartford Brokerage Partners LLC",
        "address": "1 Hartford Plaza\nHartford, CT 06103",
        "phone": "+1 860-555-1188",
        "email": "billing@hartfordbrokerage.example",
        "tax_id": "06-2291188",
        "bank": "Hartford Bank  ****1188",
        "terms": "net 30",
        "remit": "ACH Hartford routing 011900445  account ****1188",
    },
}


def _profile(vendor: str) -> dict[str, str]:
    if vendor in VENDOR_DIRECTORY:
        return VENDOR_DIRECTORY[vendor]
    return {
        "legal_name": vendor,
        "address": "1 Vendor Row\nBoston, MA 02110",
        "phone": "+1 617-555-0000",
        "email": f"billing@{vendor.lower().replace(' ', '').replace('.', '')[:18]}.example",
        "tax_id": "00-0000000",
        "bank": "First National Bank  ****0000",
        "terms": "net 30",
        "remit": "ACH routing 011000390  account ****0000",
    }


def _money(amount: float | int) -> str:
    return f"{float(amount):,.2f}"


def _lines_block(lines: Iterable[tuple[str, float, float]]) -> tuple[str, float]:
    rows = []
    subtotal = 0.0
    rows.append(f"{'Description':<42}{'Qty':>8}{'Unit':>14}{'Amount':>14}")
    rows.append("-" * 78)
    for description, qty, unit in lines:
        amount = round(qty * unit, 2)
        subtotal = round(subtotal + amount, 2)
        rows.append(f"{description:<42}{qty:>8.2f}{unit:>14,.2f}{amount:>14,.2f}")
    return "\n".join(rows), subtotal


def render_vendor_invoice(
    vendor: str,
    number: str,
    *,
    invoice_date: str,
    due_date: str,
    po: str | None = None,
    lines: list[tuple[str, float, float]] | None = None,
    amount: float | None = None,
    tax: float = 0.0,
    extra: str = "",
    currency: str = "USD",
    bill_to: str = COMPANY_BILL_TO,
) -> str:
    profile = _profile(vendor)
    if lines:
        table, subtotal = _lines_block(lines)
    else:
        due = float(amount or 0)
        table, subtotal = _lines_block([(f"Professional services — {number}", 1.0, due)])
    tax_amount = round(float(tax), 2)
    total = round(subtotal + tax_amount, 2)
    if amount is not None and abs(total - float(amount)) > 0.009:
        raise ValueError(f"{number}: line items {total} != amount {amount}")
    po_block = f"PO Number: {po}\n" if po else "PO Number: (none)\n"
    return (
        f"{profile['legal_name']}\n"
        f"{profile['address']}\n"
        f"Phone {profile['phone']}   {profile['email']}\n"
        f"Tax ID {profile['tax_id']}\n"
        f"\n"
        f"INVOICE\n"
        f"\n"
        f"Invoice Number: {number}\n"
        f"Invoice Date: {invoice_date}\n"
        f"Due Date: {due_date}\n"
        f"{po_block}"
        f"Payment Terms: {profile['terms']}\n"
        f"Currency: {currency}\n"
        f"Vendor: {vendor}\n"
        f"\n"
        f"Bill To:\n{bill_to}\n"
        f"\n"
        f"{table}\n"
        f"\n"
        f"{'Subtotal':<64}{_money(subtotal):>14}\n"
        f"{'Tax':<64}{_money(tax_amount):>14}\n"
        f"{'Amount Due':<64}{_money(total):>14}\n"
        f"\n"
        f"Remit to:\n{profile['remit']}\n"
        f"Bank: {profile['bank']}\n"
        f"Please include invoice {number} on the payment advice.\n"
        f"Late payments may accrue a 1.5% monthly finance charge after the due date.\n"
        f"Questions: {profile['email']}\n"
        f"{extra}"
    )


def render_quote(
    vendor: str,
    quote_number: str,
    *,
    amount: float,
    valid_until: str,
    lines: list[tuple[str, float, float]],
) -> str:
    profile = _profile(vendor)
    table, subtotal = _lines_block(lines)
    return (
        f"{profile['legal_name']}\n"
        f"{profile['address']}\n"
        f"{profile['email']}\n"
        f"\n"
        f"QUOTATION\n"
        f"\n"
        f"Quote Number: {quote_number}\n"
        f"Quoted amount: ${_money(amount)}\n"
        f"Estimate valid until {valid_until}\n"
        f"This promotional invoice-ready catalog is a quote, not a request for payment.\n"
        f"No invoice number is issued until you return a signed purchase order.\n"
        f"\n"
        f"Bill To:\n{COMPANY_BILL_TO}\n"
        f"\n"
        f"{table}\n"
        f"\n"
        f"{'Quoted total':<64}{_money(subtotal):>14}\n"
        f"\n"
        f"This is a quotation. Do not pay against this document.\n"
    )


def render_purchase_order(
    po_id: str,
    vendor: str,
    *,
    authorized_amount: float,
    created_date: str,
    description: str,
    approver: str = "Jordan Hale",
) -> str:
    profile = _profile(vendor)
    return (
        f"MAXIMOR DEMO CORP\n"
        f"Procurement  ·  245 Main Street, Cambridge, MA 02142\n"
        f"\n"
        f"PURCHASE ORDER\n"
        f"\n"
        f"Purchase Order {po_id}\n"
        f"PO Number: {po_id}\n"
        f"Issued: {created_date}\n"
        f"Vendor: {vendor}\n"
        f"Vendor legal name: {profile['legal_name']}\n"
        f"Vendor tax ID: {profile['tax_id']}\n"
        f"Authorized amount: {_money(authorized_amount)}\n"
        f"Currency: USD\n"
        f"Approver: {approver}\n"
        f"Ship to: 245 Main Street, Receiving Dock B, Cambridge, MA 02142\n"
        f"\n"
        f"Description\n"
        f"{description}\n"
        f"\n"
        f"This purchase order is not an invoice. The vendor must bill against {po_id}.\n"
        f"Payment terms follow the vendor master unless this order states otherwise.\n"
    )


def render_goods_receipt(
    receipt_id: str,
    po_id: str,
    vendor: str,
    *,
    received_date: str,
    quantity_ordered: int,
    quantity_received: int,
    amount_received: float,
    packing_list: str,
) -> str:
    return (
        f"MAXIMOR DEMO CORP  ·  Cambridge warehouse\n"
        f"Receiving report\n"
        f"\n"
        f"Goods Receipt {receipt_id}\n"
        f"PO Number: {po_id}\n"
        f"Vendor: {vendor}\n"
        f"Goods received in full on {received_date}\n"
        f"Packing list attached: {packing_list}\n"
        f"Quantity ordered: {quantity_ordered}\n"
        f"Quantity received: {quantity_received}\n"
        f"Amount received: {_money(amount_received)} USD\n"
        f"Received by: Maya Ortiz, Dock B\n"
        f"Condition: undamaged, count agrees with the packing list.\n"
        f"This receiving report is not an invoice.\n"
    )


def render_statement(
    vendor: str,
    *,
    period: str,
    open_items: list[tuple[str, float]],
) -> str:
    profile = _profile(vendor)
    rows = "\n".join(f"  {number:<22} {_money(amount):>12}" for number, amount in open_items)
    total = round(sum(item[1] for item in open_items), 2)
    return (
        f"{profile['legal_name']}\n"
        f"{profile['address']}\n"
        f"\n"
        f"Statement of Account\n"
        f"This is not an invoice.\n"
        f"Account statement for {period}.\n"
        f"Customer: Maximor Demo Corp  (CO-MAXIMOR)\n"
        f"\n"
        f"Open invoices:\n"
        f"{rows}\n"
        f"\n"
        f"Balance brought forward                    {_money(total)}\n"
        f"Please remit against the listed invoice numbers. Do not pay this statement as a bill.\n"
    )


def render_payment_confirmation(vendor: str, invoice_number: str, amount: float) -> str:
    profile = _profile(vendor)
    return (
        f"{profile['legal_name']}\n"
        f"{profile['email']}\n"
        f"\n"
        f"Payment received for {invoice_number}. Thank you for your payment.\n"
        f"Amount applied: {_money(amount)} USD\n"
        f"Method: ACH credit to {profile['bank']}\n"
        f"Payment confirmation — this is not a request for payment.\n"
        f"Please retain this receipt with your cash application file.\n"
    )


def render_credit_memo(vendor: str, credit_number: str, amount: float, invoice_number: str) -> str:
    profile = _profile(vendor)
    return (
        f"{profile['legal_name']}\n"
        f"{profile['address']}\n"
        f"\n"
        f"Credit Memo {credit_number}\n"
        f"Vendor: {vendor}\n"
        f"Credit note for returned goods ${_money(amount)}\n"
        f"Applies to invoice {invoice_number}.\n"
        f"This is not an invoice.\n"
        f"We will apply the credit on the next statement unless you request a refund.\n"
    )


def render_remittance(customer: str, invoice_id: str, amount: float) -> str:
    return (
        f"{customer}\n"
        f"Accounts Payable  ·  remittance desk\n"
        f"\n"
        f"Remittance advice\n"
        f"Please apply this payment to {invoice_id}.\n"
        f"Customer: {customer} Amount: {_money(amount)}\n"
        f"Lockbox remittance dated 2026-09-18.\n"
        f"Wire / ACH reference follows the invoice number above.\n"
        f"Contact ar@{customer.lower().replace(' ', '')[:16]}.example if the application is unclear.\n"
    )


def render_packing_list(po_id: str, vendor: str, items: list[str], ship_date: str) -> str:
    listed = "\n".join(f"  - {item}" for item in items)
    return (
        f"{vendor}\n"
        f"Packing list\n"
        f"Ship date: {ship_date}\n"
        f"PO Number: {po_id}\n"
        f"Ship to: Maximor Demo Corp, Dock B, 245 Main Street, Cambridge, MA 02142\n"
        f"Carrier: Freightline Logistics  PRO {po_id[-3:]}-{ship_date[5:7]}{ship_date[8:]}\n"
        f"\n"
        f"Contents:\n"
        f"{listed}\n"
        f"\n"
        f"This packing list is not an invoice.\n"
    )


PLOT_LINE_ITEMS: dict[str, list[tuple[str, float, float]]] = {
    "INV-001": [
        ("Apex standing desk, maple, 72-inch", 10.0, 890.00),
        ("27-inch 4K monitor, height-adjust arm", 10.0, 355.00),
    ],
    "INV-002": [
        ("EC2 compute — September 2026", 1.0, 6120.00),
        ("S3 storage and requests", 1.0, 1480.00),
        ("Data transfer outbound", 1.0, 720.00),
    ],
    "INV-003": [
        ("Datadog Pro host monitoring", 50.0, 300.00),
    ],
    "INV-004": [
        ("Slack Business+ user licenses", 50.0, 100.00),
    ],
    "INV-005": [
        ("Figma Organization seats", 35.0, 125.00),
    ],
    "INV-006": [
        ("Shadow consulting — September sprint", 1.0, 8750.00),
    ],
    "INV-007": [
        ("Shadow consulting — September sprint", 1.0, 8750.00),
    ],
    "INV-008": [
        ("GitHub Enterprise Cloud seats", 70.0, 300.00),
    ],
    "INV-009": [
        ("Manual new-vendor engagement retainer", 1.0, 50000.00),
    ],
    "INV-010": [
        ("Aeron-class task chair, graphite", 8.0, 410.00),
    ],
    "INV-012": [
        ("GitHub Actions minutes — overage pack", 1.0, 21000.00),
    ],
    "INV-013": [
        ("Toner cartridges, black, case of 10", 6.0, 210.00),
        ("Copy paper, 10-ream cartons", 12.0, 70.00),
    ],
    "INV-014": [
        ("CNC bracket lot NF-201", 1.0, 5000.00),
    ],
    "INV-015": [
        ("CNC housing lot NF-202", 1.0, 7500.00),
    ],
    "INV-016": [
        ("CNC plate lot NF-203", 1.0, 6000.00),
    ],
    "INV-017": [
        ("Lab motion controllers, 24V", 4.0, 2500.00),
    ],
    "INV-018": [
        ("PowerEdge R760 server, 64-core", 2.0, 24000.00),
        ("NVMe 7.68TB mixed-use SSD pair", 4.0, 3000.00),
    ],
    "INV-019": [
        ("Commercial package policy 2026-09 to 2027-08", 1.0, 12000.00),
    ],
    "INV-020": [
        ("Orbit Analytics platform — annual", 1.0, 24000.00),
    ],
    "INV-021": [
        ("Apex standing desk, maple, 72-inch", 10.0, 890.00),
        ("27-inch 4K monitor, height-adjust arm", 10.0, 355.00),
    ],
}


def invoice_document_for(
    invoice_id: str,
    vendor: str,
    vendor_invoice_number: str,
    *,
    amount: float,
    invoice_date: str,
    due_date: str,
    po_id: str | None,
    description: str = "",
) -> str:
    lines = PLOT_LINE_ITEMS.get(invoice_id)
    if lines is None:
        lines = [(description or f"Services billed on {vendor_invoice_number}", 1.0, float(amount))]
    extra = ""
    if invoice_id == "INV-001":
        extra = (
            "\nEarly payment discount 2% if paid by 2026-09-18 (2/10 net 30).\n"
            "Packing list PL-101 / goods receipt GR-101 at Dock B.\n"
        )
    if invoice_id == "INV-017":
        extra = (
            "\nInternational USD wire. Beneficiary Helios Hardware, Inc.\n"
            "Correspondent bank may deduct a wire fee from the settlement amount.\n"
        )
    return render_vendor_invoice(
        vendor,
        vendor_invoice_number,
        invoice_date=invoice_date,
        due_date=due_date,
        po=po_id,
        lines=lines,
        amount=round(float(amount), 2),
        extra=extra,
    )


def render_workpaper(
    title: str,
    period: str,
    *,
    preparer: str,
    reviewer: str,
    status: str,
    body: str,
) -> str:
    return (
        f"MAXIMOR DEMO CORP\n"
        f"Office of the CFO  ·  Month-end workpaper\n"
        f"\n"
        f"{title}\n"
        f"Period: {period}\n"
        f"Entity: CO-MAXIMOR   Currency: USD\n"
        f"Preparer: {preparer}\n"
        f"Reviewer: {reviewer}\n"
        f"Status: {status}\n"
        f"Prepared: 2026-09-03T16:40:00Z\n"
        f"\n"
        f"{body.strip()}\n"
        f"\n"
        f"Tickmarks:  ✓  tied to subledger    △  agreed to bank    ※  identity carried from source document\n"
        f"This workpaper does not authorize a journal. Postings live on the numbered JE identities.\n"
    )
