# Tetris Game & Bot

An asynchronous Tetris game server and heuristic bot player built with Python, `aiohttp`, and `asyncio`. 

Supports real-time browser play over WebSockets, live spectator streaming, and an automated bot that evaluates board placements and simulates human input timing.

---

## How It Works

### 1. Board & Engine (`tetris.py`)
- **Bitmask Board Representation**: The 20-row $\times$ 10-column board is stored as a list of 20 integers. Each column occupies 3 bits (`0b111`), encoding the tetromino color/shape ID (1–7).
- **Collision & Movement**: Fast bitwise operations handle boundary checks and collisions (`valid_board`). Includes wall kicks during piece rotation and automatic gravity via `asyncio`.
- **Row Clearing**: Scans rows after piece placement, removes completed lines, shifts board down, and pads top rows.

### 2. Spectator & WebSockets
- `/ws`: WebSocket endpoint for active gameplay. Accepts actions (`left`, `right`, `cw`, `ccw`, `down`, `drop`) and broadcasts state updates (`board`, `live`, `next`).
- `/snoop`: Multiplexed WebSocket stream that allows spectator clients (`/watch`) to observe any running game ID without interrupting the player.

### 3. Heuristic Bot (`bot.py`)
For every spawned piece, the bot tests all possible rotations and column drop positions:
- **Depth score**: Prefers placements lower on the board to keep the stack low.
- **Line clear bonus**: Weighted rewards for clears (+30 for single, +80 double, +150 triple, +300 tetris).
- **Hole penalty**: Heavily penalizes placing blocks over empty cells.
- **Lookahead**: 1-ply lookahead evaluating the best possible drop depth for the upcoming piece.
- **Human simulation**: Adds small randomized delays (140ms–180ms) between rotations and shifts to avoid instantaneous execution.

---

## Project Structure

```
tetris-game/
├── tetris.py         # Authoritative game server & WebSocket routes
├── bot.py            # Heuristic bot solver & client logic
├── tilestub.py       # Tetromino generator
├── play.py           # Unified launcher (starts server + bot + browser)
├── play.bat          # Windows batch shortcut for single-command run
├── index.html        # Playable browser UI
├── watch.html        # Live spectator UI
└── botui.html        # Standalone bot controller interface
```

---

## Setup

Requires Python 3.10+.

```bash
git clone https://github.com/nalagr/tetris-game.git
cd tetris-game

# using uv
uv venv
uv pip install aiohttp

# or standard venv
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

pip install aiohttp
```

---

## Usage

### One-Command Auto Play
Starts the server, connects the bot, and automatically opens the live spectator board in your browser:

```bash
# Windows cmd/powershell
play

# or directly with python
python play.py
```

### Manual Play Mode
To play the game yourself in the browser with arrow keys:

```bash
python play.py --manual
```

Controls:
- `Left` / `Right`: Move piece
- `Up` / `X`: Rotate clockwise
- `Z`: Rotate counter-clockwise
- `Down`: Soft drop
- `Space`: Hard drop

### Running Components Individually
You can also run the server and bot as separate services:

```bash
# Terminal 1: Game server
python tetris.py --host 127.0.0.1 -p 10340

# Terminal 2: Bot controller (port 41801)
python bot.py

# Terminal 3: Trigger bot connection
curl -X POST -d "ws://127.0.0.1:10340/ws" http://127.0.0.1:41801/server
```
