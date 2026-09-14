# ParsedMessage Schema (v1)

## Objectif
Structure unique produite par:
- Snapshot parser (historique)
- Live listener (temps réel)

## Structure (dict / JSON)

parsed_message = {
  "source": "telegram",
  "source_channel": "<string|optional>",

  "message_id": <int>,
  "grouped_id": <int|None>,          # si Telegram donne un grouped_id (albums, etc.)
  "reply_to_id": <int|None>,         # si c’est une réponse à un message

  "date_utc": "<ISO-8601 string>",   # ex: 2025-12-21T01:37:12Z
  "ingest_time_utc": "<ISO-8601>",   # quand notre bot l’a capté

  "text_raw": "<string>",            # texte brut original
  "text_norm": "<string>",           # normalisation minimale (espaces, symboles)
  "assets": ["XAUUSD"|"BTCUSD"|"NAS100"|"..."],

  "classification": "<ALERT|UPDATE|CLOSE|NOISE|UNKNOWN>",
  "intent_flags": {
    "has_entry": <bool>,
    "has_sl": <bool>,
    "has_tp": <bool>,
    "is_be": <bool>,
    "is_partial": <bool>
  },

  "trade_ref": {
    "trade_id": <int|None>,          # trade interne, si rattaché
    "confidence": <float>,           # 0.0–1.0
    "reason": "<string>"             # pourquoi rattaché / ou pourquoi None
  },

  "parse_meta": {
    "parser_version": "v1",
    "errors": ["<string>", "..."],   # vide si OK
    "warnings": ["<string>", "..."]  # vide si OK
  }
}

## Règles
- Tous les champs existent toujours (même si None).
- date_utc est toujours en UTC (suffixe Z).
- text_raw ne doit jamais être modifié.
- text_norm = normalisation NON-destructive (espaces, trim, etc.).
- assets doit utiliser la normalisation:
  - BTC/BITCOIN/BTCUSD -> BTCUSD
  - XAU/XAUUSD/OR/GOLD -> XAUUSD
  - NAS/NAS100 -> NAS100


## Ordre des messages (garantie)
- Les sorties "latest 100" sont triées du plus récent au plus ancien.
- Donc:
  - index #001 = message le plus récent
  - index #100 = message le plus ancien (dans la fenêtre)
- Cette garantie doit rester identique en snapshot et en live.


## Statut
- Schéma ParsedMessage v1 GELÉ.
- Toute modification future implique une nouvelle version (v2+).


## LIVE listener (log-only) — sortie v1
- Fichier: logs/copier/stationx_live_v1.log
- Format: JSONL (1 message = 1 ligne JSON)
- Schéma: ParsedMessage v1 (identique snapshot)
- ingest_time_utc: rempli à la capture (UTC, suffixe Z)
- Ordre: ordre d'arrivée des événements (pas de tri). Pour l’historique, utiliser date_utc.
- Mode mock: possible via flag `--mock` (pour tests uniquement)

