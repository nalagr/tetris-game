import argparse
import asyncio
import sys
import webbrowser
import aiohttp
from aiohttp import web

import bot
import tetris


async def main():
    parser = argparse.ArgumentParser(description="Single-command Tetris launcher")
    parser.add_argument(
        "--manual",
        action="store_true",
        help="Open playable manual interface instead of bot spectator",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("-p", "--port", type=int, default=10340, help="Port to bind to")
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not automatically launch browser",
    )
    args = parser.parse_args()

    # 1. Start game server
    app = web.Application()
    tetris.setup_app(app)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, args.host, args.port)
    await site.start()
    base_url = f"http://{args.host}:{args.port}"
    print(f"[Server] Tetris server running at {base_url}")

    # 2. Open browser
    if not args.no_browser:
        target_page = base_url if args.manual else f"{base_url}/watch"
        print(f"[Browser] Launching {target_page}")
        webbrowser.open(target_page)

    # 3. Handle manual vs bot
    if args.manual:
        print("[Mode] Manual mode. Play in your browser with arrow keys!")
        print("Press Ctrl+C to stop.")
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            pass
        finally:
            await runner.cleanup()
    else:
        print("[Mode] Bot autoplay mode. Bot is connecting...")
        print("Press Ctrl+C to stop.")
        async with aiohttp.ClientSession() as client:
            ws_target = f"ws://{args.host}:{args.port}/ws"
            bot_task = asyncio.create_task(bot.play_games(client, ws_target))
            try:
                await bot_task
            except asyncio.CancelledError:
                pass
            finally:
                bot_task.cancel()
                await runner.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Exit] Stopped Tetris.")
        sys.exit(0)
