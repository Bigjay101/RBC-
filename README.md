# RBC Bot Match — Setup & Usage

## Prerequisites

### 1. Install Stockfish
```bash
sudo apt install stockfish        # Ubuntu/Debian
```

Verify the path after installing:
```bash
which stockfish
# typically /usr/games/stockfish or /usr/bin/stockfish
```

### 2. Install Python dependencies
```bash
pip install reconchess
```

Or if using the provided virtual environment:
```bash
source .venv/bin/activate
```

---

## Running a Game

### 1. Set the Stockfish environment variable

In your terminal, export the path to the Stockfish executable:
```bash
export STOCKFISH_PATH=/usr/games/stockfish
```

> **Note:** This only lasts for the current terminal session. You can add it to your `~/.bashrc` or `~/.zshrc` to make it permanent.

### 2. Run the match

```bash
rc-bot-match <white_bot.py> <black_bot.py>
```

For example, to run RandomBot (white) vs TroutBot (black):
```bash
rc-bot-match random_agent.py agent.py
```

> **Important:** Use explicit file paths (e.g. `./random_agent.py`) or avoid naming bots after Python standard library modules (e.g. don't name a file `random.py`), as this causes import conflicts.

---

## Notes

- After the game, a replay file is automatically saved in the current directory as a `.json` file (e.g. `RandomBot-TroutBot-black-2026_05_12-16_16_47.json`).
- `Stockfish Engine died` messages during a game are a known quirk and can be ignored — the bot recovers and the game continues.
- All `rc-bot-match` commands must be run in the same terminal session where `STOCKFISH_PATH` was exported.