#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

"""
Station X Telegram LIVE listener (LOG-ONLY — DISABLED)

PURPOSE
- Future live listener for Station X Telegram channel
- Must produce ParsedMessage v1 objects IDENTICAL to snapshot parser
- NO execution
- NO repost
- NO forward
- LOG-ONLY

STATUS
- Skeleton only
- Live connection intentionally disabled
"""

# -----------------------------------------------------------------------------
# CONTRACT — ParsedMessage v1 (FROZEN)
#
# This live listener MUST emit ParsedMessage objects that are:
# - Structurally IDENTICAL to the snapshot parser output
# - Fully compliant with docs/parsed_message_schema.md (v1)
#
# No field may be added, removed, or modified without:
# - Creating a new schema version (v2+)
# - Updating BOTH snapshot and live pipelines
#
# This guarantee is CRITICAL for:
# - Trade/thread mapping
# - Deterministic execution
# - Fail-safe behavior
# -----------------------------------------------------------------------------


from pathlib import Path
from typing import Dict

import sys
from pathlib import Path as _Path

import argparse

import json

# Ensure project root is on sys.path so imports work when running as a script
PROJECT_ROOT = _Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.copier.stationx_parser_from_snapshot import (
    utc_now_iso,
    norm_text_minimal,
    build_intent_flags,
    normalize_symbol,
    classify,
    map_classification,
)


# Output (same contract as snapshot parser)
OUT_V1_PATH = Path("logs/copier/stationx_live_v1.log")


def emit_parsed_message_v1(msg: Dict) -> None:
    """
    Receives a ParsedMessage v1 dict and writes it to log.
    (Live listener will call this once implemented)
    """
    OUT_V1_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_V1_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(msg, ensure_ascii=False) + "\n")


def _mock_live_event(raw_text: str, message_id: int) -> None:
    """
    MOCK ONLY — simulates a Telegram live message.
    This function defines the LIVE processing pipeline
    without any Telegram dependency.
    """
    # NOTE:
    # In real live mode:
    # - raw_text comes from Telegram
    # - message_id comes from Telegram
    # - date_utc comes from Telegram metadata

    # PLACEHOLDER — will be replaced by real parser
    parsed_v1 = {
        "source": "telegram",
        "source_channel": None,

        "message_id": message_id,
        "grouped_id": None,
        "reply_to_id": None,

        "date_utc": "LIVE_TODO",
        "ingest_time_utc": utc_now_iso(),

        "text_raw": raw_text,
        "text_norm": norm_text_minimal(raw_text),
        
        "assets": ([normalize_symbol(raw_text)[0]] if normalize_symbol(raw_text)[0] else []),
        "classification": map_classification(classify(raw_text)),

        "intent_flags": build_intent_flags(raw_text),

        "trade_ref": {
            "trade_id": None,
            "confidence": 0.0,
            "reason": "live_mock_only"
        },

        "parse_meta": {
            "parser_version": "v1",
            "errors": [],
            "warnings": ["MOCK_PIPELINE"]
        }
    }

    emit_parsed_message_v1(parsed_v1)


def main() -> int:
    """
    Live listener intentionally DISABLED.
    This file only defines the contract and structure.
    """
    parser = argparse.ArgumentParser(description="StationX LIVE listener (DISABLED, log-only)")
    parser.add_argument("--mock", action="store_true", help="Emit one mock ParsedMessage v1 event")
    args = parser.parse_args()

    print("[INFO] tg_stationx_listener_live.py loaded (DISABLED — skeleton only)")

    if args.mock:
        _mock_live_event(
            raw_text="ACHAT XAUUSD NOW !",
            message_id=999999
        )
        print("[INFO] MOCK live event emitted")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

