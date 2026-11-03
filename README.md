# Tetris Game & Bot

An asynchronous Tetris game server and heuristic bot player built with Python, `aiohttp`, and `asyncio`. 

Supports real-time browser play over WebSockets, live spectator streaming, side-by-side **Player vs Computer** battle mode, and a multi-difficulty heuristic bot.

---

## Features

### 1. Difficulty Levels
- **Easy**: Beginner level. Slower reactions (160–240ms delay), 15% random blunder rate, ignores bumpiness and blockades, shallow hole penalty.
- **Medium**: Intermediate level. Human-paced moves (60–100ms delay), balanced heuristic penalizing column height, holes, and bumpiness (0-ply greedy).
- **Hard**: Master level. Pierre Dellacherie / genetic weights with full 1-ply lookahead over the upcoming piece (`next`), bumpiness minimization, blockade tracking, emergency height dampening, and rapid execution.

### 2. Player vs Computer Mode (`/vs`)
- Side-by-side split-screen arena in the browser.
- Select bot difficulty on the fly (`Easy`, `Medium`, `Hard`).
- Real-time opponent streaming via `/snoop`.
- Live score, lines cleared, next piece preview, and automated winner/loser detection.

### 3. Board & Engine (`tetris.py`)
- **Bitmask Board Representation**: 20 rows $\times$ 10 columns stored as 20 integers (3 bits per cell).
- **Collision & Movement**: Fast bitwise operations for boundary checks and collisions (`valid_board`). Includes wall kicks during piece rotation and automatic gravity via `asyncio`.
- **Row Clearing**: Scans rows after piece placement, removes completed lines, shifts board down, and pads top rows.

---

## Project Structure

```
tetris-game/
├── tetris.py         # Game server, WebSocket routes (/ws, /snoop), and bot manager
├── bot.py            # Heuristic bot solver (Easy, Medium, Hard)
├── tilestub.py       # Tetromino generator
├── play.py           # Unified launcher (Solo, Bot Autoplay, Versus)
├── play.bat          # Windows batch shortcut for single-command run
├── vs.html           # Player vs Computer split-screen arena
├── index.html        # Playable solo browser UI
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

### ⚔️ Play Against the Computer (Versus Mode)
Launch the split-screen battle arena directly in your browser:

```bash
# Windows shortcut
play.bat --vs

# or using python
python play.py --vs --difficulty medium
```
You can switch difficulties (`Easy`, `Medium`, `Hard`) and rematch directly in the UI.

### 🎮 Solo Play Mode
Play single-player with arrow keys:

```bash
python play.py --manual
```

Controls:
- `Left` / `Right`: Move piece
- `Up` / `X`: Rotate clockwise
- `Z`: Rotate counter-clockwise
- `Down`: Soft drop
- `Space`: Hard drop

### 👁️ Bot Autoplay / Spectator Mode
Watch the bot play automatically:

```bash
# Default hard difficulty
python play.py

# Or specify difficulty
python play.py --difficulty easy
```
