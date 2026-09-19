from accrual.store import list_expected_vendors


def _by_name(period: str = "2026-09") -> dict:
    return {item.vendor: item for item in list_expected_vendors(period)}


def test_expected_vendors_cover_demo_situations():
    vendors = _by_name()
    names = set(vendors)
    assert names == {
        "Aether Compute",
        "Amazon Web Services",
        "CleanSpace Facilities",
        "Harbor Electric",
        "Helios Hardware",
        "Lindholm & Ruiz LLP",
        "NewForge Consulting",
        "Orbit Analytics",
        "Pulse Recruiting",
    }


def test_received_invoices_are_flagged():
    vendors = _by_name()
    assert vendors["Amazon Web Services"].invoice_already_received is True
    assert vendors["Orbit Analytics"].invoice_already_received is True
    assert vendors["Aether Compute"].invoice_already_received is False
    assert vendors["Helios Hardware"].invoice_already_received is False


def test_demo_vendor_filter_keeps_requested_order():
    from accrual.store import list_expected_vendors
    from accrual.workflow import DEMO_VENDORS

    expected = list_expected_vendors("2026-09")
    by_name = {item.vendor.lower(): item for item in expected}
    ordered = [by_name[name.lower()].vendor for name in DEMO_VENDORS if name.lower() in by_name]
    assert ordered == DEMO_VENDORS


def test_ap_only_vendors_are_not_pulled_in():
    vendors = _by_name()
    assert "Acme Supplies" not in vendors
    assert "Office Depot" not in vendors
    assert "Salesforce" not in vendors
