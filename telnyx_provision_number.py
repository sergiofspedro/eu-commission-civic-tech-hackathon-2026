#!/usr/bin/env python3
"""
Phase A: Search for available Telnyx phone numbers and print with monthly cost.
Phase B: Purchase + create TeXML app + assign to number.

Usage:
  export TELNYX_API_KEY=your_key
  export PUBLIC_DOMAIN=your-domain.com
  python telnyx_provision_number.py search [BE|PT|NL]
  python telnyx_provision_number.py provision <phone_number>
"""
import os, sys, requests

BASE = "https://api.telnyx.com/v2"


def headers():
    key = os.environ.get("TELNYX_API_KEY", "")
    if not key:
        sys.exit("Set TELNYX_API_KEY env var first.")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def search(country="BE"):
    """List available numbers for a country with voice capability."""
    r = requests.get(
        f"{BASE}/available_phone_numbers",
        params={"filter[country_code]": country, "filter[features][]": "voice"},
        headers=headers(),
    )
    r.raise_for_status()
    numbers = r.json().get("data", [])
    if not numbers:
        print(f"No numbers found for {country}.")
        return
    print(f"\nAvailable numbers ({country}) — top {min(5, len(numbers))}:\n")
    for n in numbers[:5]:
        cost = n.get("monthly_cost", {})
        print(f"  {n['phone_number']}  {cost.get('amount','?')} {cost.get('currency','?')}/mo")
    print("\nTo provision: python telnyx_provision_number.py provision <number>")


def provision(phone_number: str):
    domain = os.environ.get("PUBLIC_DOMAIN", "your-domain.com")
    webhook_url = f"https://{domain}/voice/incoming"

    # 1. Order number
    r = requests.post(
        f"{BASE}/number_orders",
        json={"phone_numbers": [{"phone_number": phone_number}]},
        headers=headers(),
    )
    r.raise_for_status()
    print(f"Ordered: {phone_number}")

    # 2. Create TeXML application
    r = requests.post(
        f"{BASE}/texml_applications",
        json={
            "application_name": "LOOP",
            "webhook_url": webhook_url,
            "webhook_api_version": "API v2",
        },
        headers=headers(),
    )
    r.raise_for_status()
    app_id = r.json()["data"]["id"]
    print(f"TeXML app: {app_id} → {webhook_url}")

    # 3. Look up phone number resource ID
    r = requests.get(
        f"{BASE}/phone_numbers",
        params={"filter[phone_number]": phone_number},
        headers=headers(),
    )
    r.raise_for_status()
    items = r.json().get("data", [])
    if not items:
        sys.exit(f"Number {phone_number} not found in account after ordering.")
    number_id = items[0]["id"]

    # 4. Assign number to TeXML app
    r = requests.patch(
        f"{BASE}/phone_numbers/{number_id}",
        json={"connection_id": app_id},
        headers=headers(),
    )
    r.raise_for_status()
    print(f"Assigned {phone_number} → TeXML app {app_id}")
    print(f"\nDone. Dial {phone_number} to test.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "search":
        country = sys.argv[2] if len(sys.argv) > 2 else "BE"
        search(country)
    elif cmd == "provision":
        if len(sys.argv) < 3:
            sys.exit("Provide phone number: python telnyx_provision_number.py provision +32...")
        provision(sys.argv[2])
    else:
        print(__doc__)
