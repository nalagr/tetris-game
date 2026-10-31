import asyncio

import tilestub
from aiohttp import WSMsgType, web

TETROMINOS = { # this is from the index.html file
    1: {0: [(0,0),(1,0),(0,-1),(1,-1)]},
    2: {0: [(0,0),(0,-1),(0,-2),(0,-3)],
        1: [(-1,0),(0,0),(1,0),(2,0)]},
    3: {0: [(-1,-1),(0,-1),(1,-1),(0,0)],
        1: [(-1,-1),(0,-1),(0,-2),(0,0)],
        2: [(-1,0),(0,0),(1,0),(0,-1)],
        3: [(0,0),(0,-1),(0,-2),(1,-1)]},
    4: {0: [(0,-2),(0,-1),(0,0),(1,0)],
        1: [(0,0),(0,-1),(1,-1),(2,-1)],
        2: [(-1,-2),(0,-2),(0,-1),(0,0)],
        3: [(-1,0),(0,0),(1,0),(1,-1)]},
    5: {0: [(-1,0),(0,0),(0,-1),(0,-2)],
        1: [(0,-1),(0,0),(1,0),(2,0)],
        2: [(0,0),(0,-1),(0,-2),(1,-2)],
        3: [(-1,-1),(0,-1),(1,-1),(1,0)]},
    6: {0: [(0,-2),(0,-1),(1,-1),(1,0)],
        1: [(-1,0),(0,0),(0,-1),(1,-1)]},
    7: {0: [(1,-2),(1,-1),(0,-1),(0,0)],
        1: [(-1,-1),(0,-1),(0,0),(1,0)]},
}

# this is so we know where eacch tetromino spawns in the board. this is a map, so we know the y cal
spawn_map = {}
for s in TETROMINOS:
    location = TETROMINOS[s][0]
    minimum = min(dy for _, dy in location)
    spawn_map[s] = -minimum

class tetris_game:
    def __init__(self, ws: web.WebSocketResponse): # constucuer
        self.ws = ws
        self.board = [0]*20 # this is how we are storing the board, docs say not to use a list tho
        self.live = None # this is the current tetromino that is moving downn
        self.next = None # this is the the thigng that is next
        self.gravity = None # this is the function that will move the tetromino down AUTOMATICALLY, diff from the down function

    async def game_start(self):
        t1 = tilestub.new_tile()
        t2 = tilestub.new_tile() # it sayafter to call this twice to get two tgetrominos
        self.live = (t1, 0, 4, spawn_map[t1]) # here we are spawin the first one according to the docs
        self.next = t2 # we set the next one to the second one create
        await self.send() # in stead of sending it multiple times, jsut call the function i created bc we have to send it after every move
        self.gravity = asyncio.create_task(self.auto_down()) # this makes the grav task that it sayafter to do in the docs.

    async def auto_down(self): # this is the function that will move the tetromino down. code take  from the ocs
        while True:
            await asyncio.sleep(0.5) # ut sayafter to add a delay
            await self.down()

    async def left(self):
        shape, orient, x, y = self.live
        if self.valid_board(shape, orient, x-1, y):
            self.live = (shape, orient, x-1, y)
            await self.send_live()

    async def right(self):
        shape, orient, x, y = self.live
        if self.valid_board(shape, orient, x+1, y):
            self.live = (shape, orient, x+1, y)
            await self.send_live()

    async def down(self):
        shape, orient, x, y = self.live
        if self.valid_board(shape, orient, x, y + 1):
            self.live = (shape, orient, x, y + 1)
            await self.send_live()
        else:
            await self.place()

    async def drop(self): # this is for droping the piece to the lowest possible postiion on the bboard. brute force from the docs
        shape, orient, x, y = self.live
        d = self.drop_dist(shape, orient, x, y)
        self.live = (shape, orient, x, y + d)
        await self.place()

    async def rotate_cw(self):
        await self.rotate(1)

    async def rotate_ccw(self):
        await self.rotate(-1)

    async def rotate(self, change):
        shape, orient, x, y = self.live
        orientation = (orient + change) % len(TETROMINOS[shape])
        possiblelocations = TETROMINOS[shape][orientation]

        # posititions after the rotatoon has been compelteted
        xafter = [x + dx for dx, _ in possiblelocations]
        yafter = [y + dy for _, dy in possiblelocations]

        # we want to know what is the minimum amount that we need to move the tetromino after we roate so we can keep it in the valid indicies
        xshift = 0
        if min(xafter) < 0:
            xshift = -min(xafter)
        elif max(xafter) > 9:
            xshift = 9 - max(xafter)

        # figure out how much to shift to stay for they
        yshift = 0
        if min(yafter) < 0:
            yshift = -min(yafter)
        elif max(yafter) > 19:
            yshift = 19 - max(yafter)

        if self.valid_board(shape, orientation, x + xshift, y + yshift): # shouldnt have to check but the test fails for some reason whe i dont
            self.live = (shape, orientation, x + xshift, y + yshift)
            await self.send_live()

    async def place(self): # puts the tetromino on the board
        shape, orient, x, y = self.live
        for dx, dy in TETROMINOS[shape][orient]:
            xpos, ypos = x+dx, y+dy
            if 0 <= xpos < 10 and 0 <= ypos < 20:
                shift = 3*(9 - xpos)
                self.board[ypos] &= ~(0b111 << shift)
                self.board[ypos] |= (shape << shift)

        # this is where we are checking if tehere are anewy fill rows in the board, ie our list
        rows_after = []
        for row_int in self.board:
            # i make the each row into the ten cells
            cells = [(row_int >> (3*(9-i))) & 0b111 for i in range(10)]
            # this means that there is an empty cell in the row so we dont remove it
            if any(c == 0 for c in cells):
                rows_after.append(row_int) # python list append to add to the end
        # then if we deleted a row we add one to the top, ie, extend our list back to the og 20
        while len(rows_after) < 20:
            rows_after.insert(0, 0)
        self.board = rows_after

        # then after we delete rows or not, we then can start the nexgt part of the game
        current = self.next
        self.next = tilestub.new_tile()
        self.live = (current, 0, 4, spawn_map[current])
        # same thing as the start gaem fucntion

        # so in tetris if the new one spwans at it min and it is not on the board, then the game auto ends
        if not self.valid_board(current, 0, 4, spawn_map[current]):
            await new_send(self.ws, {
                "board": self.board,
                "live":  [*self.live, self.drop_dist(*self.live)], # learned this for tuples, passes the first four arguents, unpacks the tuple from docs
                "next":  self.next,
                "event": "gameover" # they said to ignore this for this mp but i tried without this it doesnt wwork
            })
        else:
            await self.send() # again this just makes it easier to send a response of the current game

    def valid_board(self, shape, orient, x, y): # this is the function that checks if we are on the baord or not
        for dx, dy in TETROMINOS[shape][orient]:
            xpos, ypos = x+dx, y+dy
            if xpos< 0 or xpos >=10 or ypos<0 or ypos >= 20: # make sure we havent stepps off the board
                return False
            shift = 3*(9 - xpos)
            if ((self.board[ypos] >> shift) & 0b111) != 0: # masking to make sure that cell is not already filled
                return False
        return True

    def drop_dist(self, shape, orient, x, y): # this is basically simply chekcing how far down is a valid palcemaent, brute force mehtod from the docs
        d = 0
        while self.valid_board(shape, orient, x, y+ d +1):
            d += 1
        return d

    async def send(self): # this is the function we call over and over again to send after moves or anewythig selse
        shape, orient, x, y = self.live
        howfar = self.drop_dist(shape, orient, x, y)
        await new_send(self.ws, {
            "board":self.board,
            "live": [shape, orient, x, y, howfar],
            "next": self.next
        })

    async def send_live(self): # this is so wen the move or roate is calle d we will sen the new live
        shape, orient, x, y = self.live
        howfar = self.drop_dist(shape, orient, x, y)
        await new_send(self.ws,{
            "live":[shape, orient, x, y, howfar]
        })

routes = web.RouteTableDef()

playws = {} # used to track open websockets to support graceful shutdown on Ctrl+C
watchws = {}
watchers = {}

async def new_send(player, msg):
    await player.send_json(msg)

    for w in watchers.get(id(player), ()):
        await w.send_json(msg)

@routes.get('/ws')
async def websocket_handler(request : web.Request) -> web.WebSocketResponse:
    """The main event loop: accepts connections, manages games, cleans up"""
    ws = web.WebSocketResponse() # this is going to create the websocket response
    await ws.prepare(request) # this performs the upgrade from http to websocket
    playws[id(ws)] = ws

    # FIX ME: initialize a game for this websocket

    new_game = tetris_game(ws)
    await new_game.game_start()

    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            # FIX ME: process user event from msg.data
            if (msg.data == 'left'):
                await new_game.left()
            elif (msg.data == 'right'):
                await new_game.right()
            elif (msg.data == 'cw'):
                await new_game.rotate_cw()
            elif (msg.data == 'ccw'):
                await new_game.rotate_ccw()
            elif (msg.data == 'down'):
                await new_game.down()
            elif (msg.data == 'drop'):
                await new_game.drop()
        elif msg.type == WSMsgType.ERROR:
            print(f'WebSocket received exception {ws.exception()}')

    del playws[id(ws)]
    watchers.pop(id(ws), None)
    return ws

@routes.get('/')
async def index(req : web.Request) -> web.FileResponse:
    """A simple method for sharing the index.html with players"""
    return web.FileResponse(path="index.html")

@routes.get('/watch')
async def watch(req : web.Request) -> web.FileResponse:
    return web.FileResponse(path="watch.html")

@routes.get('/snoop')
async def snoop(req : web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse()
    await ws.prepare(req)

    watchws[id(ws)] = ws # this is a new websocket and we are adding it to the watchws dict
    game = None

    async for msg in ws:

        if msg.data == '?': # docs say to send the key alive and a list of all the games
            await ws.send_json({'alive': list(playws.keys()) })

        else:
            current = int(msg.data)

            if game in watchers:
                watchers[game].discard(ws)

            if current in playws:
                watchers.setdefault(current, set()).add(ws)
                game = current

    del watchws[id(ws)]
    if game in watchers:
        watchers[game].discard(ws)

    return ws

async def shutdown_ws(app: web.Application) -> None:
    """Ctrl+C won't work right unless we close anewy open websockets,
    so this function does that."""
    for ws in list(playws.values()):
        await ws.close()
    for ws in list(watchws.values()):
        await ws.close()

def setup_app(app: web.Application) -> None:
    """Registers routes and anewy setup and shutdown handlers needed
    The default provided with the MP is probablt sufficient"""
    app.on_shutdown.append(shutdown_ws)
    app.add_routes(routes)

# To facilitate testing, do not change anewything below this line
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default="0.0.0.0")
    parser.add_argument('-p','--port', type=int, default=10340)
    args = parser.parse_args()

    app = web.Application()
    setup_app(app)
    web.run_app(app, host=args.host, port=args.port) # this function never returns


#human player
#http://sp25-cs340-090.cs.illinois.edu:10340/
#place to connect bot
#http://sp25-cs340-090.cs.illinois.edu:41801/ #websocket to paste - ws://sp25-cs340-090.cs.illinois.edu:10340/ws
#to watch
#http://sp25-cs340-090.cs.illinois.edu:10340/watch