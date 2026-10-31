import asyncio
import random  # this is to make it seem more human bc the ramdomness

import aiohttp
from aiohttp import WSMsgType, web

import tetris

TETROMINOS = tetris.TETROMINOS
spawn_map = tetris.spawn_map
# these are both things in tetris.py already just copy and pasted ehre

def valid_board(board, shape, orient, x, y): # this is the function that checks if we are on the baord or not
        for dx, dy in TETROMINOS[shape][orient]:
            xpos, ypos = x+dx, y+dy
            if xpos< 0 or xpos >=10 or ypos<0 or ypos >= 20: # make sure we havent stepps off the board
                return False
            shift = 3*(9 - xpos)
            if ((board[ypos] >> shift) & 0b111) != 0: # masking to make sure that cell is not already filled
                return False
        return True

def drop_dist(board, shape, orient, x, y): # this is basically simply chekcing how far down is a valid palcemaent, brute force mehtod from the docs
        d = 0
        while valid_board(board, shape, orient, x, y+ d +1):
            d += 1
        return d

# these two fucns are also from tetris.py

def count_cleared(board, shape, orient, x, y): # this is a function that counts if we will clear a row if the bot places the block in this so
    copyBoard = board.copy() # make a copy of the board to prevent messing with the acutal game

    for dx, dy in TETROMINOS[shape][orient]:
        px, py = x+dx, y+dy
        shift = 3*(9-px) # getting the cell
        copyBoard[py] &= ~(0b111 << shift)
        copyBoard[py] |= (shape << shift)

    clearedLine = 0

    for row in copyBoard:
        full = True

        for i in range(10):
            cell = (row >> (3 * (9 - i))) & 0b111
            if cell == 0:
                full = False
                break

        if full:
            clearedLine += 1

    return clearedLine

def if_placed(board, shape, orient, x, y): # checking what would happen if we placed the block
    newb = board.copy()
    for dx, dy in TETROMINOS[shape][orient]:
        px, py = x+dx, y+dy
        shift = 3*(9-px)
        newb[py] &= ~(0b111 << shift)
        newb[py] |= (shape << shift)
    return newb

def count_holes(nb):
    holes = 0
    for col in range(10):
        seen = False
        for row in range(20):
            filled = ((nb[row] >> (3*(9-col))) & 0b111) != 0
            if filled:
                seen = True
            elif seen:
                holes += 1
    return holes

async def play_games(client, url):
    """Main game connection and play logic."""
    alltasks.add(asyncio.current_task())
    asyncio.current_task().add_done_callback(taskdone)
    try:
        while True:
            await asyncio.sleep(2.5) # pause between games; feel free to change this
            try: ws = await client.ws_connect(url)
            except:
                print('Game server at', url, 'did not let the bot play')
                return
            wsoftask[asyncio.current_task()] = ws
            print('Starting a new game')
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    data = msg.json() # parse message from server

                    # replace code starting here
                    if 'event' in data: # game over
                        print('EVENT:', data['event'])
                        await ws.close() # MUST keep this to avoid infinite wait on ended game
                    elif 'next' in data: # 'next' is given when a new tetromino appears
                        board = data['board']
                        live_shape, orient, x0, y0, _ = data['live']

                        best_score = -1
                        best_move  = None

                        # trying diff orientations and x positions
                        for o in range(len(TETROMINOS[live_shape])):
                            for x in range(10):
                                y = spawn_map[live_shape]
                                if not valid_board(board, live_shape, o, x, y):
                                    continue
                                d = drop_dist(board, live_shape, o, x, y)

                                # scoring part
                                first = sum((y + dy + d) for dx, dy in TETROMINOS[live_shape][o]) * 3
                                clears = count_cleared(board, live_shape, o, x, y)
                                move_penalty = 1 if (o==orient and x==x0) else 0
                                if   clears == 1: biasforClear = 30
                                elif clears == 2: biasforClear = 80
                                elif clears == 3: biasforClear = 150
                                elif clears == 4: biasforClear = 300
                                else: biasforClear = 0
                                hole_penalty = count_holes(if_placed(board, live_shape, o, x, y))
                                newboard = if_placed(board, live_shape, o, x, y)
                                next = data['next']
                                best_next_drop = 0
                                for o2 in range(len(TETROMINOS[next])):
                                    for x2 in range(10):
                                        y2 = spawn_map[next]
                                        if not valid_board(newboard, next, o2, x2, y2):
                                            continue
                                        d2 = drop_dist(newboard, next, o2, x2, y2)
                                        best_next_drop = max(best_next_drop, d2)
                                bonus = 5 * best_next_drop
                                score = first + biasforClear - hole_penalty - move_penalty + bonus
                                if score > best_score:
                                    best_score = score
                                    best_move  = (o, x)

                        target_o, target_x = best_move

                        # roation testing.
                        await asyncio.sleep(0.7)
                        while orient != target_o:
                            await ws.send_str('cw')
                            orient = (orient + 1) % len(TETROMINOS[live_shape])
                            await asyncio.sleep(random.uniform(0.14, 0.18))

                        # left and right movign
                        await asyncio.sleep(0.2)
                        while x0 < target_x:
                            await ws.send_str('right')
                            x0 += 1
                            await asyncio.sleep(random.uniform(0.14, 0.18))
                        while x0 > target_x:
                            await ws.send_str('left')
                            x0 -= 1
                            await asyncio.sleep(random.uniform(0.14, 0.18))

                        # drop when we have found the
                        await asyncio.sleep(0.14)
                        await ws.send_str('drop')
                    # replace code above here

                elif msg.type == WSMsgType.ERROR:
                    print(f'connection to {url} received {ws.exception()}')

    except BaseException as ex:
        print("Game terminated with exception:\n   ", type(ex),'\n   ', ex)


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
    web.run_app(app, host='0.0.0.0', port=41801) # this function never returns