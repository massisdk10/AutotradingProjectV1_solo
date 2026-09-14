#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

"""
Executor (LOG-ONLY — DISABLED)

PURPOSE
- Consume ParsedMessage v1 (JSONL)
- Decide what action WOULD be taken
- NEVER execute trades
- Write intent-only logs

STATUS
- Log-only
- No MT5 connection
- Safe by design
"""

import json
import sys
from pathlib import Path
from typing import Dict, Iterable


# Input sources (snapshot or live)
INPUT_SNAPSHOT_V1 = Path("logs/copier/stationx_parsed_v1_100.jsonl")
INPUT_LIVE_V1 = Path("logs/copier/stationx_live_v1.log")

# Output (executor decisions)
OUT_EXECUTOR_LOG = Path("logs/executor/executor_decisions.log")


# -----------------------------------------------------------------------------
# CONTRACT — ParsedMessage v1 (FROZEN)
#
# This executor consumes ONLY ParsedMessage v1 objects.
# Any missing or incompatible field MUST trigger a fail-stop.
# -----------------------------------------------------------------------------

REQUIRED_FIELDS = {
    "source",
    "message_id",
    "date_utc",
    "ingest_time_utc",
    "text_raw",
    "text_norm",
    "assets",
    "classification",
    "intent_flags",
    "trade_ref",
    "parse_meta",
}


def read_jsonl(path: Path) -> Iterable[Dict]:
    """Yield JSON objects line by line. Skips invalid JSON lines safely."""
    if not path.exists():
        return

    with path.open("r", encoding="utf-8") as f:
        for ln_no, ln in enumerate(f, start=1):
            ln = ln.strip()
            if not ln:
                continue
            try:
                yield json.loads(ln)
            except json.JSONDecodeError:
                # Skip legacy non-JSON lines (e.g., old Python dict str)
                print(f"[WARN] Skipping non-JSON line in {path} at line {ln_no}", file=sys.stderr)
                continue


def validate_v1(msg: Dict) -> None:
    """Fail-stop if ParsedMessage v1 is invalid."""
    missing = REQUIRED_FIELDS - msg.keys()
    if missing:
        raise ValueError(f"Invalid v1 message, missing fields: {missing}")


def decide_action(msg: Dict) -> Dict:
    """
    Decide what WOULD be done for this message.
    NO EXECUTION.
    """
    action = {
        "message_id": msg["message_id"],
        "classification": msg["classification"],
        "assets": msg["assets"],
        "decision": "IGNORE",
        "reason": "",
    }

    if msg["classification"] == "ALERT" and msg["intent_flags"].get("has_entry"):
        action["decision"] = "OPEN_TRADE"
        action["reason"] = "entry signal detected"

    elif msg["classification"] == "UPDATE":
        action["decision"] = "UPDATE_TRADE"
        action["reason"] = "trade update"

    elif msg["classification"] == "CLOSE":
        action["decision"] = "CLOSE_TRADE"
        action["reason"] = "close instruction"

    return action


def emit_decision(action: Dict) -> None:
    """Write executor decision to log (JSONL)."""
    OUT_EXECUTOR_LOG.parent.mkdir(parents=True, exist_ok=True)
    with OUT_EXECUTOR_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(action, ensure_ascii=False) + "\n")


def run_source(path: Path) -> None:
    """Process one input source."""
    for msg in read_jsonl(path):
        validate_v1(msg)
        decision = decide_action(msg)
        emit_decision(decision)


def main() -> int:
    """
    Executor is DISABLED by default.
    Reads inputs and logs decisions only.
    """
    print("[INFO] executor_logonly loaded (DISABLED)")

    # Snapshot source
    run_source(INPUT_SNAPSHOT_V1)

    # Live source
    run_source(INPUT_LIVE_V1)

    print("[INFO] executor_logonly finished (log-only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

