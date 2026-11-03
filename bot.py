import asyncio
import random

import aiohttp
from aiohttp import WSMsgType, web

import tetris

TETROMINOS = tetris.TETROMINOS
spawn_map = tetris.spawn_map

PROFILES = {
    'easy': {
        'name': 'Easy',
        'weights': {
            'height': -0.10,
            'clears': 8.0,
            'holes': -4.0,
            'bumpiness': -0.10,
            'blockades': -0.05,
        },
        'lookahead': False,
        'randomness': 25.0,
        'blunder_rate': 0.15,
        'delays': {
            'initial': 0.20,
            'step': (0.16, 0.24),
            'shift_pause': 0.15,
            'drop_pause': 0.20,
        },
    },
    'medium': {
        'name': 'Medium',
        'weights': {
            'height': -0.40,
            'clears': 20.0,
            'holes': -18.0,
            'bumpiness': -0.80,
            'blockades': -0.30,
        },
        'lookahead': False,
        'randomness': 3.0,
        'blunder_rate': 0.0,
        'delays': {
            'initial': 0.08,
            'step': (0.06, 0.10),
            'shift_pause': 0.06,
            'drop_pause': 0.08,
        },
    },
    'hard': {
        'name': 'Hard',
        'weights': {
            'height': -0.51,
            'clears': 30.0,
            'holes': -36.0,
            'bumpiness': -1.84,
            'blockades': -0.56,
        },
        'lookahead': True,
        'randomness': 0.0,
        'blunder_rate': 0.0,
        'delays': {
            'initial': 0.02,
            'step': (0.015, 0.03),
            'shift_pause': 0.02,
            'drop_pause': 0.02,
        },
    },
}

def valid_board(board, shape, orient, x, y):
    for dx, dy in TETROMINOS[shape][orient]:
        xpos, ypos = x + dx, y + dy
        if xpos < 0 or xpos >= 10 or ypos < 0 or ypos >= 20:
            return False
        shift = 3 * (9 - xpos)
        if ((board[ypos] >> shift) & 0b111) != 0:
            return False
    return True

def drop_dist(board, shape, orient, x, y):
    d = 0
    while valid_board(board, shape, orient, x, y + d + 1):
        d += 1
    return d

def count_cleared(board, shape, orient, x, y):
    newb, cleared = if_placed(board, shape, orient, x, y)
    return cleared

def if_placed(board, shape, orient, x, y):
    """Places piece into board copy and properly simulates clearing completed rows."""
    newb = board.copy()
    for dx, dy in TETROMINOS[shape][orient]:
        px, py = x + dx, y + dy
        if 0 <= px < 10 and 0 <= py < 20:
            shift = 3 * (9 - px)
            newb[py] &= ~(0b111 << shift)
            newb[py] |= (shape << shift)

    rows_after = []
    for row in newb:
        cells = [(row >> (3 * (9 - i))) & 0b111 for i in range(10)]
        if any(c == 0 for c in cells):
            rows_after.append(row)

    cleared = 20 - len(rows_after)
    while len(rows_after) < 20:
        rows_after.insert(0, 0)

    return rows_after, cleared

def get_heights(board):
    heights = [0] * 10
    for col in range(10):
        shift = 3 * (9 - col)
        for row in range(20):
            if ((board[row] >> shift) & 0b111) != 0:
                heights[col] = 20 - row
                break
    return heights

def get_holes_and_blockades(board):
    holes = 0
    blockades = 0
    for col in range(10):
        shift = 3 * (9 - col)
        seen = False
        blocks = 0
        for row in range(20):
            filled = ((board[row] >> shift) & 0b111) != 0
            if filled:
                seen = True
                blocks += 1
            elif seen:
                holes += 1
                blockades += blocks
    return holes, blockades

def count_holes(board):
    holes, _ = get_holes_and_blockades(board)
    return holes

def evaluate_board(board, clears, difficulty='hard'):
    profile = PROFILES.get(difficulty, PROFILES['hard'])
    w = profile['weights']

    heights = get_heights(board)
    agg_height = sum(heights)
    max_height = max(heights)
    bumpiness = sum(abs(heights[i] - heights[i + 1]) for i in range(9))
    holes, blockades = get_holes_and_blockades(board)

    score = (
        w['height'] * agg_height
        + w['clears'] * clears
        + w['holes'] * holes
        + w['bumpiness'] * bumpiness
        + w['blockades'] * blockades
    )

    if difficulty == 'hard' and max_height > 14:
        score -= (max_height - 14) * 25.0

    if profile.get('randomness', 0) > 0:
        score += random.uniform(-profile['randomness'], profile['randomness'])

    return score

def choose_best_move(board, live_shape, orient, x0, next_shape=None, difficulty='hard'):
    profile = PROFILES.get(difficulty, PROFILES['hard'])

    # Blunder simulation for easy difficulty
    if profile.get('blunder_rate', 0) > 0 and random.random() < profile['blunder_rate']:
        valid_moves = []
        for o in range(len(TETROMINOS[live_shape])):
            for x in range(10):
                y = spawn_map[live_shape]
                if valid_board(board, live_shape, o, x, y):
                    valid_moves.append((o, x))
        if valid_moves:
            return random.choice(valid_moves)

    best_score = -float('inf')
    best_move = None

    for o in range(len(TETROMINOS[live_shape])):
        for x in range(10):
            y = spawn_map[live_shape]
            if not valid_board(board, live_shape, o, x, y):
                continue
            d = drop_dist(board, live_shape, o, x, y)
            nb, clears = if_placed(board, live_shape, o, x, y + d)
            eval1 = evaluate_board(nb, clears, difficulty)

            total_eval = eval1
            if profile.get('lookahead', False) and next_shape:
                best_next = -float('inf')
                for o2 in range(len(TETROMINOS[next_shape])):
                    for x2 in range(10):
                        y2 = spawn_map[next_shape]
                        if not valid_board(nb, next_shape, o2, x2, y2):
                            continue
                        d2 = drop_dist(nb, next_shape, o2, x2, y2)
                        nb2, c2 = if_placed(nb, next_shape, o2, x2, y2 + d2)
                        ev2 = evaluate_board(nb2, c2, difficulty)
                        if ev2 > best_next:
                            best_next = ev2
                if best_next != -float('inf'):
                    total_eval += 0.75 * best_next

            if total_eval > best_score:
                best_score = total_eval
                best_move = (o, x)

    return best_move

async def play_games(client, url, difficulty='hard', loop=True):
    """Main game connection and play logic supporting difficulty levels and loop flag."""
    current_task = asyncio.current_task()
    alltasks.add(current_task)
    current_task.add_done_callback(taskdone)
    try:
        while True:
            await asyncio.sleep(0.5 if not loop else 2.5)
            try:
                ws = await client.ws_connect(url)
            except Exception as e:
                print('Game server at', url, 'did not let the bot play:', e)
                return

            wsoftask[current_task] = ws
            print(f'Starting game [Difficulty: {difficulty}]')
            profile = PROFILES.get(difficulty, PROFILES['hard'])
            delays = profile['delays']

            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    data = msg.json()

                    if 'event' in data:
                        print('EVENT:', data['event'])
                        await ws.close()
                        if not loop:
                            return
                        break
                    elif 'next' in data:
                        board = data['board']
                        live_shape, orient, x0, y0, _ = data['live']
                        next_shape = data.get('next')

                        move = choose_best_move(board, live_shape, orient, x0, next_shape, difficulty)
                        if not move:
                            target_o, target_x = orient, x0
                        else:
                            target_o, target_x = move

                        # Rotation
                        await asyncio.sleep(delays['initial'])
                        while orient != target_o:
                            await ws.send_str('cw')
                            orient = (orient + 1) % len(TETROMINOS[live_shape])
                            await asyncio.sleep(random.uniform(*delays['step']))

                        # Horizontal positioning
                        await asyncio.sleep(delays['shift_pause'])
                        while x0 < target_x:
                            await ws.send_str('right')
                            x0 += 1
                            await asyncio.sleep(random.uniform(*delays['step']))
                        while x0 > target_x:
                            await ws.send_str('left')
                            x0 -= 1
                            await asyncio.sleep(random.uniform(*delays['step']))

                        # Drop
                        await asyncio.sleep(delays['drop_pause'])
                        await ws.send_str('drop')

                elif msg.type == WSMsgType.ERROR:
                    print(f'connection to {url} received {ws.exception()}')
                    break

            if not loop:
                break

    except asyncio.CancelledError:
        pass
    except BaseException as ex:
        print("Game terminated with exception:\n   ", type(ex), '\n   ', ex)

# Written by course staff. Do not edit.
routes = web.RouteTableDef()
alltasks = set() # track tasks we might need to cancel if the server stops
wsoftask = {}    # when a task opens a ws, that is added here

def taskdone(task):
    """Written by course staff. Do not edit.
    Helper method to clean up ws and tasks"""
    alltasks.discard(task)
    if task in wsoftask:
        asyncio.create_task(wsoftask[task].close())
        del wsoftask[task]

@routes.get('/')
async def get_html(request):
    """Written by course staff. Do not edit.
    Returns the HTML user interface"""
    return web.FileResponse("botui.html")

@routes.post('/server')
async def play_on_server(request):
    """Written by course staff. Do not edit.
    Connects the bot to a server"""
    url = await request.text()
    alltasks.add(asyncio.create_task(play_games(request.app['client'], url)))
    return web.Response(status=200, text="OK")

@routes.get('/stopall')
async def get_html(request):
    """Written by course staff. Do not edit.
    Returns the HTML user interface"""
    for task in tuple(alltasks):
        try: task.cancel()
        except: pass
    return web.Response(status=200, text="OK")


async def shutdown_ws(app):
    """Cleanup"""
    for task in tuple(alltasks):
        try: task.cancel()
        except: pass

async def startup_client(app):
    """A shared client for better DNS caching"""
    app['client'] = aiohttp.ClientSession()

async def shutdown_client(app):
    """Cleanup"""
    await app['client'].close()


def setup_app(app):
    """Register all the setup and cleanup callbacks"""
    app.on_startup.append(startup_client)
    app.on_shutdown.append(shutdown_ws)
    app.on_shutdown.append(shutdown_client)
    app.add_routes(routes)

if __name__ == '__main__':
    app = web.Application()
    setup_app(app)
    web.run_app(app, host='0.0.0.0', port=41801)
