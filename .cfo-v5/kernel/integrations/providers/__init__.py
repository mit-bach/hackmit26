from integrations.providers import adyen, coupa, gmail, netsuite, outlook, stripe, xero

PROVIDERS = {
    "stripe": stripe,
    "adyen": adyen,
    "gmail": gmail,
    "outlook": outlook,
    "xero": xero,
    "coupa": coupa,
    "netsuite": netsuite,
}

INVOICE_PROVIDERS = ("gmail", "outlook", "xero", "coupa", "netsuite")
CASH_PROVIDERS = ("stripe", "adyen")
WEBHOOK_PROVIDERS = ("stripe", "adyen", "gmail", "outlook", "xero")
SYNC_PROVIDERS = ("coupa", "netsuite", "stripe")


def get_provider(name: str):
    try:
        return PROVIDERS[name]
    except KeyError as exc:
        raise KeyError(f"Unknown provider: {name}") from exc
