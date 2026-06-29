#!/usr/bin/env python3
"""
Bootstrap secrets from Infisical into civicconnect.env.

Prerequisites:
  pip install infisical-python
  Log in: infisical login
  Create a .infisical.json token for the project or set INFISICAL_TOKEN env var.

Usage:
  python setup_env.py [--env production|staging|development]
"""
import os, sys, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", default="development", help="Infisical environment slug")
    parser.add_argument("--project-id", required=True, help="Infisical project ID")
    args = parser.parse_args()

    try:
        from infisical import InfisicalClient
    except ImportError:
        sys.exit("Run: pip install infisical-python")

    client = InfisicalClient(
        token=os.environ.get("INFISICAL_TOKEN"),
        site_url=os.environ.get("INFISICAL_SITE_URL", "https://app.infisical.com"),
    )

    required = [
        "LOOP_TELEGRAM_TOKEN",
        "TELNYX_API_KEY",
        "TELNYX_PUBLIC_KEY",
        "OPENROUTER_API_KEY",
    ]

    lines = []
    for key in required:
        secret = client.get_secret(
            secret_name=key,
            project_id=args.project_id,
            environment=args.env,
        )
        lines.append(f'{key}="{secret.secret_value}"')
        print(f"  {key} ✓")

    out = "loop.env"
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nWritten to {out}")

if __name__ == "__main__":
    main()
