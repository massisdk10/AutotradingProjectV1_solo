# Telegram Copier — Phase 2 (LOG-ONLY)

Purpose:
- Read messages from a source Telegram channel (later, in 2.1.2)
- Strictly classify messages:
  - TRADING_IMPORTANT → will be copied to private channel
  - NON_TRADING → ignored (not copied)
- Maintain strict 1-trade = 1-thread mapping (no mixing)
- Recreate messages as manual copy/paste (no forward, no attribution)
- Full audit logs

Rules:
- LOG-ONLY: no MT5, no trading
- No Telegram connection in 2.1.1
- No secrets stored in this repository


