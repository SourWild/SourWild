#!/usr/bin/env python3
"""Render private WakaTime stats into the profile README."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


README = Path("README.md")
START = "<!--START_SECTION:waka-->"
END = "<!--END_SECTION:waka-->"
API_URL = "https://api.wakatime.com/api/v1/users/current/stats/last_7_days"


def fetch_stats(api_key: str) -> dict:
    encoded = base64.b64encode(api_key.encode()).decode()
    request = Request(
        API_URL,
        headers={
            "Authorization": f"Basic {encoded}",
            "Accept": "application/json",
            "User-Agent": "SourWild-profile-readme",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)["data"]
    except HTTPError as error:
        raise SystemExit(f"WakaTime API returned HTTP {error.code}") from error


def row(item: dict) -> str:
    name = str(item.get("name", "Unknown"))[:24]
    duration = str(item.get("text") or item.get("digital") or "0 secs")[:18]
    percent = float(item.get("percent", 0))
    filled = max(0, min(25, round(percent / 4)))
    bar = "█" * filled + "░" * (25 - filled)
    return f"{name:<24} {duration:<18} {bar} {percent:05.2f} %"


def group(title: str, items: list[dict]) -> list[str]:
    lines = [title]
    if not items:
        lines.append("No activity recorded yet")
    else:
        lines.extend(row(item) for item in items[:5])
    return lines


def render(stats: dict) -> str:
    lines = ["```text", f"🕑︎ Time Zone: {stats.get('timezone', 'Asia/Shanghai')}", ""]
    lines += group("💬 Programming Languages:", stats.get("languages", []))
    lines += [""]
    lines += group("🔥 Editors:", stats.get("editors", []))
    lines += [""]
    lines += group("💻 Operating System:", stats.get("operating_systems", []))
    lines += ["```"]
    return "\n".join(lines)


def update_readme(section: str) -> None:
    current = README.read_text()
    if START not in current or END not in current:
        raise SystemExit("WakaTime section markers are missing from README.md")
    before, remainder = current.split(START, 1)
    _, after = remainder.split(END, 1)
    updated = f"{before}{START}\n{section}\n{END}{after}"
    README.write_text(updated)


def main() -> None:
    api_key = os.environ.get("WAKATIME_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("WAKATIME_API_KEY is not configured")
    update_readme(render(fetch_stats(api_key)))


if __name__ == "__main__":
    main()
