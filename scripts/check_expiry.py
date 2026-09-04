#!/usr/bin/env python3
"""Compute switch-off status for a fleet of prototype repos.

Stdlib-only by design (this runs inside a GitHub Actions job with no
guaranteed package installs beyond Python itself).

Usage as a library (used by fleet-check.yml):

    from check_expiry import build_report

    entries = [
        {"repo": "publicdigital/foo", "switch_off_date": "2026-10-01", ...},
        ...
    ]
    print(build_report(entries))

Usage from the command line for a quick manual check:

    echo '[{"repo": "publicdigital/foo", "switch_off_date": "2026-10-01"}]' \
        | python3 scripts/check_expiry.py
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime
from typing import Iterable, Optional, TypedDict

DUE_SOON_THRESHOLD_DAYS = 14


class PrototypeEntry(TypedDict, total=False):
    repo: str
    client: str
    project: str
    owner_github: str
    created_date: str
    switch_off_date: str
    error: str


def parse_date(value: str) -> date:
    return datetime.strptime(value.strip(), "%Y-%m-%d").date()


def categorize(days_remaining: int) -> str:
    if days_remaining < 0:
        return "OVERDUE"
    if days_remaining <= DUE_SOON_THRESHOLD_DAYS:
        return "due soon"
    return "OK"


def status_for_entry(entry: PrototypeEntry, today: Optional[date] = None) -> dict:
    today = today or date.today()
    repo = entry.get("repo", "<unknown repo>")

    if entry.get("error"):
        return {
            "repo": repo,
            "status": "ERROR",
            "days_remaining": None,
            "switch_off_date": entry.get("switch_off_date", ""),
            "owner_github": entry.get("owner_github", ""),
            "detail": entry["error"],
        }

    switch_off_raw = entry.get("switch_off_date", "")
    try:
        switch_off = parse_date(switch_off_raw)
    except (ValueError, AttributeError):
        return {
            "repo": repo,
            "status": "ERROR",
            "days_remaining": None,
            "switch_off_date": switch_off_raw,
            "owner_github": entry.get("owner_github", ""),
            "detail": f"could not parse switch_off_date {switch_off_raw!r}",
        }

    days_remaining = (switch_off - today).days
    return {
        "repo": repo,
        "status": categorize(days_remaining),
        "days_remaining": days_remaining,
        "switch_off_date": switch_off_raw,
        "owner_github": entry.get("owner_github", ""),
        "detail": "",
    }


_STATUS_ORDER = {"OVERDUE": 0, "ERROR": 1, "due soon": 2, "OK": 3}


def build_report(entries: Iterable[PrototypeEntry], today: Optional[date] = None) -> str:
    rows = [status_for_entry(entry, today=today) for entry in entries]
    rows.sort(key=lambda r: (_STATUS_ORDER.get(r["status"], 99), r["repo"]))

    today = today or date.today()
    lines = [
        f"_Fleet check run: {today.isoformat()}_",
        "",
        "| Status | Repo | Owner | Switch-off date | Days remaining |",
        "|---|---|---|---|---|",
    ]
    if not rows:
        lines.append("| — | _no prototype repos found_ | | | |")
    for row in rows:
        days = "" if row["days_remaining"] is None else str(row["days_remaining"])
        detail = f" ({row['detail']})" if row["detail"] else ""
        lines.append(
            f"| {row['status']}{detail} | {row['repo']} | {row['owner_github']} "
            f"| {row['switch_off_date']} | {days} |"
        )

    overdue = sum(1 for r in rows if r["status"] == "OVERDUE")
    due_soon = sum(1 for r in rows if r["status"] == "due soon")
    errors = sum(1 for r in rows if r["status"] == "ERROR")
    ok = sum(1 for r in rows if r["status"] == "OK")
    lines += [
        "",
        f"**Summary:** {overdue} overdue, {due_soon} due soon, {ok} OK, {errors} errors "
        f"— {len(rows)} prototypes total.",
        "",
        "This is a reporting-only audit. Nothing is deleted or disabled automatically "
        "— an admin should follow up on OVERDUE prototypes directly with their owner.",
    ]
    return "\n".join(lines)


def main() -> int:
    raw = sys.stdin.read()
    try:
        entries = json.loads(raw) if raw.strip() else []
    except json.JSONDecodeError as exc:
        print(f"Failed to parse input JSON: {exc}", file=sys.stderr)
        return 1

    print(build_report(entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
