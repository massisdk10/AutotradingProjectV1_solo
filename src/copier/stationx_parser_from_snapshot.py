#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Station X snapshot parser (log-only)
- Reads logs/copier/stationx_snapshot.log (text blocks)
- Extracts messages (date_utc, message_id, reply_to_msg_id, text)
- Classifies message types (NOW/DETAILS/TP hits/SL BE/CLOSE/SL explicit/NOISE)
- Normalizes symbols (BTCUSD / XAUUSD / NAS100)
- Writes logs/copier/stationx_parsed_100.txt (latest 100 messages = most recent)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Tuple
import re
import sys
import json
from datetime import datetime, timezone



SNAPSHOT_PATH = Path("logs/copier/stationx_snapshot.log")
OUT_PATH = Path("logs/copier/stationx_parsed_100.txt")
OUT_V1_PATH = Path("logs/copier/stationx_parsed_v1_100.jsonl")


@dataclass
class ParsedMsg:
    date_utc: str
    message_id: int
    reply_to_msg_id: Optional[int]
    text: str
    msg_type: str
    symbol: Optional[str]
    symbol_raw: Optional[str]


# -----------------------------
# Symbol normalization
# -----------------------------
SYMBOL_MAP = {
    # BTCUSD
    "BTC": "BTCUSD",
    "BITCOIN": "BTCUSD",
    "BTCUSD": "BTCUSD",
    # XAUUSD
    "XAU": "XAUUSD",
    "XAUUSD": "XAUUSD",
    "OR": "XAUUSD",
    "GOLD": "XAUUSD",
    # NAS100
    "NAS": "NAS100",
    "NAS100": "NAS100",
    "NASDAQ": "NAS100",
}

# Find raw symbols in text (word boundaries, uppercase compare)
SYMBOL_REGEX = re.compile(r"\b(BTCUSD|BTC|BITCOIN|XAUUSD|XAU|OR|GOLD|NAS100|NAS|NASDAQ)\b", re.IGNORECASE)


def normalize_symbol(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Returns (symbol_canonical, symbol_raw) if found.
    If multiple matches exist, pick the first occurrence in text.
    """
    m = SYMBOL_REGEX.search(text)
    if not m:
        return None, None
    raw = m.group(1)
    raw_up = raw.upper()
    # Normalize OR/GOLD/etc.
    canonical = SYMBOL_MAP.get(raw_up)
    return canonical, raw


# -----------------------------
# Classification
# -----------------------------
def classify(text: str) -> str:
    t = text.strip()
    t_up = t.upper()

    # DETAILS: most reliable signature
    if ("TP1" in t_up) and ("TP2" in t_up) and ("TP3" in t_up) and ("SL" in t_up):
        return "DETAILS"

    # NOW
    if ("NOW" in t_up) and (("ACHAT" in t_up) or ("VENTE" in t_up)):
        # Ex: "ACHAT BITCOIN NOW !", "VENTE XAUUSD NOW !"
        return "NOW"

    # TP hits
    if ("TP1" in t_up) and ("TOUCH" in t_up):
        return "TP1_HIT"
    if ("TP2" in t_up) and ("TOUCH" in t_up):
        return "TP2_HIT"
    if ("TP3" in t_up) and ("TOUCH" in t_up):
        return "TP3_HIT"

    # SL BE
    if ("SL" in t_up) and ("BE" in t_up):
        return "SL_BE"

    # CLOSE NOW (accept accents/no accents)
    if (("CLOTUREZ" in t_up) or ("CLÔTUREZ" in t_up)) and ("NOW" in t_up) and (("PRIX D'ENTR" in t_up) or ("PRIX D’ENTR" in t_up)):
        return "CLOSE_NOW"

    # SL explicit (e.g., "SL -350 pips")
    if t_up.startswith("SL") and ("PIPS" in t_up):
        return "SL_EXPLICIT"

    # Recap / bilan message are NOT actionable
    if ("BILAN" in t_up): 
        return "NOISE"

    # Unknown action vs noise
    actionish = any(k in t_up for k in ["TP", "SL", "BE", "CLOTUREZ", "CLÔTUREZ", "NOW"])
    if actionish:
        return "UNKNOWN_ACTION"

    return "NOISE"


# -----------------------------
# Snapshot parsing
# -----------------------------
def parse_snapshot(path: Path) -> List[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Snapshot not found: {path}")

    lines = path.read_text(encoding="utf-8").splitlines()
    msgs: List[List[str]] = []
    cur: List[str] = []

    for ln in lines:
        if ln.strip() == "[MSG]":
            if cur:
                msgs.append(cur)
            cur = ["[MSG]"]
        else:
            if cur:
                cur.append(ln)

    if cur:
        msgs.append(cur)

    # Drop any trailing garbage block that doesn't look like a message
    cleaned: List[List[str]] = []
    for block in msgs:
        # needs at least date_utc and message_id lines
        joined = "\n".join(block)
        if "date_utc:" in joined and "message_id:" in joined and "text:" in joined:
            cleaned.append(block)

    parsed: List[dict] = []
    for block in cleaned:
        d = extract_fields(block)
        parsed.append(d)

    return parsed


def extract_fields(block_lines: List[str]) -> dict:
    # Expected keys
    date_utc = None
    message_id = None
    reply_to = None
    text_val = None

    for ln in block_lines:
        s = ln.strip()
        if s.startswith("date_utc:"):
            date_utc = s.split("date_utc:", 1)[1].strip()
        elif s.startswith("message_id:"):
            message_id = int(s.split("message_id:", 1)[1].strip())
        elif s.startswith("reply_to_msg_id:"):
            raw = s.split("reply_to_msg_id:", 1)[1].strip()
            if raw == "None":
                reply_to = None
            else:
                try:
                    reply_to = int(raw)
                except ValueError:
                    reply_to = None
        elif s.startswith("text:"):
            # Snapshot contains "\n" literal sequences already, keep as-is
            text_val = s.split("text:", 1)[1].lstrip()

    if date_utc is None or message_id is None or text_val is None:
        raise ValueError(f"Bad message block (missing required field):\n{block_lines}")

    return {
        "date_utc": date_utc,
        "message_id": message_id,
        "reply_to_msg_id": reply_to,
        "text": text_val,
    }

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def norm_text_minimal(s: str) -> str:
    # Non-destructive: trim + collapse whitespace
    return re.sub(r"\s+", " ", s.strip())


def map_classification(msg_type: str) -> str:
    if msg_type in {"DETAILS", "NOW"}:
        return "ALERT"
    if msg_type in {"TP1_HIT", "TP2_HIT", "TP3_HIT", "SL_BE", "SL_EXPLICIT"}:
        return "UPDATE"
    if msg_type in {"CLOSE_NOW"}:
        return "CLOSE"
    if msg_type in {"UNKNOWN_ACTION"}:
        return "UNKNOWN"
    if msg_type in {"NOISE"}:
        return "NOISE"
    return "UNKNOWN"


def build_intent_flags(text: str) -> dict:
    t = text.upper()
    return {
        "has_entry": ("NOW" in t) and (("ACHAT" in t) or ("VENTE" in t)),
        "has_sl": "SL" in t,
        "has_tp": "TP" in t,
        "is_be": ("SL" in t) and ("BE" in t),
        "is_partial": ("TP1" in t) or ("TP2" in t) or ("TP3" in t),
    }


def to_v1(pm: ParsedMsg, ingest_time_utc: str) -> dict:
    assets = []
    if pm.symbol:
        assets = [pm.symbol]

    v1 = {
        "source": "telegram",
        "source_channel": None,

        "message_id": pm.message_id,
        "grouped_id": None,
        "reply_to_id": pm.reply_to_msg_id,

        "date_utc": pm.date_utc,
        "ingest_time_utc": ingest_time_utc,

        "text_raw": pm.text,
        "text_norm": norm_text_minimal(pm.text),
        "assets": assets,

        "classification": map_classification(pm.msg_type),
        "intent_flags": build_intent_flags(pm.text),

        "trade_ref": {
            "trade_id": None,
            "confidence": 0.0,
            "reason": "snapshot_parse_only"
        },

        "parse_meta": {
            "parser_version": "v1",
            "errors": [],
            "warnings": []
        }
    }
    return v1


def write_v1_jsonl(v1_msgs: List[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(m, ensure_ascii=False) for m in v1_msgs]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(msgs: List[ParsedMsg], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Stats
    counts = {}
    for m in msgs:
        counts[m.msg_type] = counts.get(m.msg_type, 0) + 1

    lines: List[str] = []
    lines.append("===== STATIONX PARSED (LATEST 100) =====")
    lines.append(f"input: {SNAPSHOT_PATH}")
    lines.append(f"count: {len(msgs)}")
    lines.append("types:")
    for k in sorted(counts.keys()):
        lines.append(f"  {k}: {counts[k]}")
    lines.append("")

    for i, m in enumerate(msgs, start=1):
        lines.append(f"#{i:03d} {m.date_utc}  id={m.message_id}  reply_to={m.reply_to_msg_id}  type={m.msg_type}  symbol={m.symbol or '-'}  raw={m.symbol_raw or '-'}")
        # Keep text readable (snapshot uses literal \n, keep it)
        lines.append(f"text: {m.text}")
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    try:
        raw = parse_snapshot(SNAPSHOT_PATH)
    except Exception as e:
        print(f"[FATAL] parse_snapshot failed: {e}", file=sys.stderr)
        return 2

    # Snapshot is newest -> oldest, so latest 100 = first 100 blocks
    raw_100 = raw[:100]

    parsed: List[ParsedMsg] = []
    unknown_actions: List[ParsedMsg] = []

    for r in raw_100:
        t = r["text"]
        msg_type = classify(t)
        symbol, symbol_raw = normalize_symbol(t)

        pm = ParsedMsg(
            date_utc=r["date_utc"],
            message_id=r["message_id"],
            reply_to_msg_id=r["reply_to_msg_id"],
            text=t,
            msg_type=msg_type,
            symbol=symbol,
            symbol_raw=symbol_raw,
        )
        parsed.append(pm)

        if msg_type == "UNKNOWN_ACTION":
            unknown_actions.append(pm)

    # Fail-stop: if we have unknown action-like messages in the latest window, we want to know.
    # For Phase 2 (log-only), we still write the report, but we return a non-zero code to force attention.
   

    ingest_time = utc_now_iso()
    v1_msgs = [to_v1(pm, ingest_time) for pm in parsed]
    write_v1_jsonl(v1_msgs, OUT_V1_PATH)

    write_report(parsed, OUT_PATH)

    if unknown_actions:
        print(f"[WARN] UNKNOWN_ACTION messages in latest 100: {len(unknown_actions)}", file=sys.stderr)
        print(f"       See: {OUT_PATH}", file=sys.stderr)
        print(f"       See: {OUT_V1_PATH}", file=sys.stderr)
        return 1

    print(f"[OK] Wrote: {OUT_PATH}")
    print(f"[OK] Wrote: {OUT_V1_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

