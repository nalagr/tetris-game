# Tetris Game & Bot

An asynchronous Tetris game server and heuristic bot player built with Python, `aiohttp`, and `asyncio`. 

Supports real-time browser play over WebSockets, live spectator streaming, side-by-side **Player vs Computer** battle mode, and a multi-difficulty heuristic bot.

---

## Features

### 1. Interactive Terminal Launcher
When launching from the terminal (`play` or `python play.py`), an interactive menu lets you choose:
1. **Play by yourself** (Solo Play with keyboard controls)
2. **Watch a bot play** (Live spectator stream of autoplay bot)
3. **Play against a bot** (Split-screen player vs bot battle)

### 2. Difficulty Levels
- **Easy**: Beginner level. Slower reactions (160–240ms delay), 15% random blunder rate, ignores bumpiness and blockades, shallow hole penalty.
- **Medium**: Intermediate level. Human-paced moves (60–100ms delay), balanced heuristic penalizing column height, holes, and bumpiness (0-ply greedy).
- **Hard**: Master level. Pierre Dellacherie / genetic weights with full 1-ply lookahead over upcoming piece (`next`), bumpiness minimization, blockade tracking, emergency height dampening, and rapid execution.

### 3. Player vs Computer Mode (`/vs`)
- Side-by-side split-screen arena in the browser.
- Select bot difficulty on the fly (`Easy`, `Medium`, `Hard`).
- Real-time opponent streaming via `/snoop`.
- Live score, lines cleared, next piece preview, and automated winner/loser detection.

### 4. Board & Engine (`tetris.py`)
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
├── play.py           # Interactive & CLI launcher (Solo, Bot Watch, Versus)
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

### Interactive Menu (Recommended)
Run without arguments to bring up the terminal selection menu:

```bash
# Windows
play

# Direct python
python play.py
```

```
============================================
             TETRIS LAUNCHER            
============================================
  1) Play by yourself (Solo)
  2) Watch a bot play (Spectator)
  3) Play against a bot (Versus)
============================================
Enter choice [1/2/3] (default 1):
```

### Direct CLI Shortcuts
You can also launch directly into any mode without the interactive prompt:

```bash
# 1. Play by yourself
python play.py solo
# or: python play.py --solo

# 2. Watch a bot play
python play.py watch
# or: python play.py watch --difficulty hard

# 3. Play against a bot
python play.py vs
# or: python play.py vs --difficulty medium
```

### Controls (Solo & Versus)
- `Left` / `Right`: Move piece
- `Up` / `X`: Rotate clockwise
- `Z`: Rotate counter-clockwise
- `Down`: Soft drop
- `Space`: Hard drop
