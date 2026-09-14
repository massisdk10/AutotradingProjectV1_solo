#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Station X trade mapper (log-only) - Robust version

Input:
- logs/copier/stationx_parsed_100.txt

Output:
- logs/copier/stationx_trade_map_100.txt

Rules:
- DETAILS messages define trade masters (master_id)
- Replies attach by reply_to_msg_id == master_id
- NOW attaches by:
    - same symbol (BTCUSD / XAUUSD / NAS100)
    - closest BEFORE DETAILS
    - max window: 2 minutes
- Deduplicate:
    - messages by message_id
    - replies within a trade by reply message_id
"""

from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import sys

PARSED_PATH = Path("logs/copier/stationx_parsed_100.txt")
OUT_PATH = Path("logs/copier/stationx_trade_map_100.txt")

NOW_WINDOW = timedelta(minutes=2)


@dataclass
class ParsedLine:
    date_utc: datetime
    message_id: int
    reply_to: Optional[int]
    msg_type: str
    symbol: Optional[str]
    raw: Optional[str]
    text: str


@dataclass
class TradeGroup:
    symbol: str
    master_id: int
    master_time: datetime
    now_id: Optional[int] = None
    now_time: Optional[datetime] = None
    replies: List[ParsedLine] = field(default_factory=list)
    status: str = "INIT"


# -----------------------------
# Helpers
# -----------------------------
def parse_datetime(s: str) -> datetime:
    # stationx_parsed_100 uses ISO like 2025-12-19T16:00:28+00:00
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def read_parsed_file(path: Path) -> List[ParsedLine]:
    """
    Robust parser of stationx_parsed_100.txt:
    We parse header lines starting with "#", then read the next "text:" line.
    Header format example:
      #006 2025-12-19T16:00:28+00:00  id=13540  reply_to=None  type=DETAILS  symbol=XAUUSD  raw=XAUUSD
      text: ....
    """
    if not path.exists():
        raise FileNotFoundError(f"Parsed file not found: {path}")

    lines = path.read_text(encoding="utf-8").splitlines()

    parsed_by_id: Dict[int, ParsedLine] = {}

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if not line.startswith("#"):
            i += 1
            continue

        parts = line.split()
        # minimal structure: #NNN DATE id=.. reply_to=.. type=.. symbol=.. raw=..
        if len(parts) < 6:
            i += 1
            continue

        # parts[0] is "#006"
        date_s = parts[1]

        kv: Dict[str, str] = {}
        for tok in parts[2:]:
            if "=" in tok:
                k, v = tok.split("=", 1)
                kv[k] = v

        # required keys
        if "id" not in kv or "reply_to" not in kv or "type" not in kv or "symbol" not in kv:
            i += 1
            continue

        try:
            mid = int(kv["id"])
        except ValueError:
            i += 1
            continue

        reply_to_s = kv["reply_to"]
        msg_type = kv["type"]
        symbol = kv["symbol"]
        raw = kv.get("raw", None)

        # find the next "text:" line
        j = i + 1
        while j < len(lines) and not lines[j].startswith("text:"):
            j += 1
        if j >= len(lines):
            i += 1
            continue

        text = lines[j].split("text:", 1)[1].lstrip()

        obj = ParsedLine(
            date_utc=parse_datetime(date_s),
            message_id=mid,
            reply_to=None if reply_to_s == "None" else int(reply_to_s),
            msg_type=msg_type,
            symbol=None if symbol == "-" else symbol,
            raw=None if (raw is None or raw == "-") else raw,
            text=text,
        )

        # Deduplicate by Telegram message_id (safe)
        parsed_by_id[obj.message_id] = obj

        # continue after text line
        i = j + 1

    # Most recent first
    out = list(parsed_by_id.values())
    out.sort(key=lambda x: x.date_utc, reverse=True)
    return out


def build_trade_groups(msgs: List[ParsedLine]) -> List[TradeGroup]:
    # Split categories
    details = [m for m in msgs if m.msg_type == "DETAILS"]
    nows = [m for m in msgs if m.msg_type == "NOW"]
    replies = [m for m in msgs if m.reply_to is not None]

    trades: List[TradeGroup] = []

    for d in details:
        tg = TradeGroup(
            symbol=d.symbol or "UNKNOWN",
            master_id=d.message_id,
            master_time=d.date_utc,
        )

        # Attach replies by reply_to == master_id, dedup by reply message_id
        seen_reply_ids = set()
        for r in replies:
            if r.reply_to == d.message_id and r.message_id not in seen_reply_ids:
                tg.replies.append(r)
                seen_reply_ids.add(r.message_id)

        # Find best NOW: same symbol, closest BEFORE, within window
        candidates = [n for n in nows if n.symbol == tg.symbol and n.date_utc <= tg.master_time]
        candidates.sort(key=lambda x: (tg.master_time - x.date_utc))

        if candidates:
            best = candidates[0]
            if (tg.master_time - best.date_utc) <= NOW_WINDOW:
                tg.now_id = best.message_id
                tg.now_time = best.date_utc

        tg.status = "OK" if tg.now_id is not None else "NOW_MISSING"
        trades.append(tg)

    # Sort trades newest -> oldest
    trades.sort(key=lambda t: t.master_time, reverse=True)
    return trades


def write_report(trades: List[TradeGroup], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)

    lines: List[str] = []
    lines.append("===== STATIONX TRADE MAP (LATEST 100) =====")
    lines.append(f"count_trades: {len(trades)}")
    lines.append("")

    for i, tg in enumerate(trades, start=1):
        lines.append(f"TRADE #{i}")
        lines.append(f"  symbol: {tg.symbol}")
        lines.append(f"  master_id: {tg.master_id}")
        lines.append(f"  master_time: {tg.master_time.isoformat()}")
        lines.append(f"  now_id: {tg.now_id}")
        lines.append(f"  now_time: {tg.now_time.isoformat() if tg.now_time else None}")
        lines.append(f"  status: {tg.status}")

        if tg.replies:
            lines.append("  replies:")
            for r in tg.replies:
                lines.append(f"    - {r.msg_type} (id={r.message_id} time={r.date_utc.isoformat()})")
        else:
            lines.append("  replies: none")

        lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    try:
        msgs = read_parsed_file(PARSED_PATH)
        trades = build_trade_groups(msgs)
        write_report(trades, OUT_PATH)
    except Exception as e:
        print(f"[FATAL] {e}", file=sys.stderr)
        return 2

    print(f"[OK] Wrote: {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

