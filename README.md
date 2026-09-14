# AutoTrader

A personal automated trading project built with Python, MetaTrader 5, and Telegram integration.

The goal of this project is to explore how a modular software system can receive trading signals from Telegram, process and validate them, and prepare them for execution through MetaTrader 5.

> This project was developed for educational and personal learning purposes.

## Overview

AutoTrader is a Python-based project designed to automate parts of a trading workflow.

The system is structured around several components responsible for:

- Reading trading signals from Telegram
- Parsing incoming messages
- Extracting relevant trading information
- Mapping parsed signals into structured trade instructions
- Preparing trades for execution
- Logging system activity
- Separating sensitive configuration from the source code

The project focuses on modularity, maintainability, and safe handling of credentials.

## Technologies Used

- **Python**
- **MetaTrader 5**
- **Telegram / Telethon**
- **Git**
- **GitHub**
- Environment variables for credential management

## Main Features

### Telegram Integration

The project connects to Telegram using Telethon and retrieves messages from configured sources.

Telegram credentials and session information are stored outside the public repository using environment variables.

### Signal Parsing

Incoming Telegram trading messages can be processed to extract relevant information such as:

- Trading instrument
- Buy or sell direction
- Entry information
- Stop-loss
- Take-profit targets

### Trade Mapping

Parsed signals are converted into structured trade information that can be used by other components of the system.

This separates Telegram message processing from trading execution logic.

### Execution Layer

The project contains an execution component designed to handle trade instructions separately from the signal-processing system.

This modular approach makes it easier to test components independently and improve the system over time.

### Logging

Logging functionality is used to track system behavior and help with debugging and monitoring.

Runtime logs are excluded from the public repository.

### Security

Sensitive information is intentionally excluded from GitHub.

The project uses environment variables for information such as:

- Telegram API ID
- Telegram API hash
- Telegram session information
- Other private configuration values

Files containing credentials, sessions, logs, and local configuration are excluded through `.gitignore`.

## Project Structure

```text
AutotradingProjectV1_solo/
│
├── docs/
│   ├── broker/
│   ├── integrity_check.md
│   ├── parsed_message_schema.md
│   ├── security_plan.md
│   └── structure_notes.md
│
├── src/
│   ├── copier/
│   │   ├── stationx_parser_from_snapshot.py
│   │   ├── stationx_trade_mapper_from_parsed.py
│   │   ├── tg_check_source_channel.py
│   │   ├── tg_listener_readonly.py
│   │   ├── tg_listener_stationx_logonly.py
│   │   ├── tg_scan_chats.py
│   │   ├── tg_stationx_listener_live.py
│   │   └── tg_stationx_snapshot_last.py
│   │
│   └── executor/
│       └── executor_logonly.py
│
├── tg_copier/
├── scan_chats_id.py
├── .gitignore
└── README.md
