#!/usr/bin/env python3
"""Search available Telnyx phone numbers.

Usage:
  export TELNYX_API_KEY=your_key
  python telnyx_search_numbers.py [country_code]   # default: BE
"""
import os, sys, requests

def main():
    key = os.environ.get("TELNYX_API_KEY", "")
    if not key:
        sys.exit("Set TELNYX_API_KEY env var first.")

    country = sys.argv[1] if len(sys.argv) > 1 else "BE"
    r = requests.get(
        "https://api.telnyx.com/v2/available_phone_numbers",
        params={"filter[country_code]": country, "filter[features][]": "voice"},
        headers={"Authorization": f"Bearer {key}"},
    )
    r.raise_for_status()
    numbers = r.json().get("data", [])
    if not numbers:
        print(f"No numbers available for {country}.")
        return
    print(f"\n{len(numbers)} numbers found for {country}:\n")
    for n in numbers[:10]:
        cost = n.get("monthly_cost", {})
        print(f"  {n['phone_number']}  {cost.get('amount','?')} {cost.get('currency','?')}/mo")

if __name__ == "__main__":
    main()
