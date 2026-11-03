import argparse
import asyncio
import sys
import webbrowser
import aiohttp
from aiohttp import web

import bot
import tetris


def prompt_menu():
    """Interactive terminal menu to choose game mode and difficulty."""
    print("\n" + "=" * 44)
    print("             TETRIS LAUNCHER            ")
    print("=" * 44)
    print("  1) Play by yourself (Solo)")
    print("  2) Watch a bot play (Spectator)")
    print("  3) Play against a bot (Versus)")
    print("=" * 44)

    try:
        choice = input("Enter choice [1/2/3] (default 1): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nExiting.")
        sys.exit(0)

    if choice == "2":
        mode = "watch"
    elif choice == "3":
        mode = "vs"
    else:
        mode = "solo"

    difficulty = "medium"
    if mode in ("watch", "vs"):
        print("\nSelect bot difficulty:")
        print("  1) Easy")
        print("  2) Medium (Default)")
        print("  3) Hard")
        try:
            diff_choice = input("Enter choice [1/2/3] (default 2): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            sys.exit(0)

        if diff_choice == "1":
            difficulty = "easy"
        elif diff_choice == "3":
            difficulty = "hard"
        else:
            difficulty = "medium"

    return mode, difficulty


async def main():
    parser = argparse.ArgumentParser(
        description="Tetris Launcher: Solo, Bot Watch, or Player vs Bot",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "mode_pos",
        nargs="?",
        choices=["solo", "watch", "vs"],
        help="Optional game mode: 'solo', 'watch', or 'vs'",
    )
    parser.add_argument(
        "--solo",
        "--manual",
        dest="solo",
        action="store_true",
        help="Option 1: Play by yourself in the browser",
    )
    parser.add_argument(
        "--watch",
        "--autoplay",
        dest="watch",
        action="store_true",
        help="Option 2: Watch a bot play automatically",
    )
    parser.add_argument(
        "--vs",
        action="store_true",
        help="Option 3: Play against a bot in split-screen arena",
    )
    parser.add_argument(
        "--difficulty",
        choices=["easy", "medium", "hard"],
        default=None,
        help="Bot difficulty: 'easy', 'medium', or 'hard' (default: medium)",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
    parser.add_argument("-p", "--port", type=int, default=10340, help="Port to bind to (default: 10340)")
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not automatically launch browser",
    )
    args = parser.parse_args()

    # Determine mode: from CLI flags, positional argument, or interactive prompt
    mode = None
    if args.solo:
        mode = "solo"
    elif args.watch:
        mode = "watch"
    elif args.vs:
        mode = "vs"
    elif args.mode_pos:
        mode = args.mode_pos

    difficulty = args.difficulty

    # If no mode specified, prompt menu (handles interactive terminals and piped input)
    if mode is None:
        try:
            mode, prompt_diff = prompt_menu()
            if difficulty is None:
                difficulty = prompt_diff
        except Exception:
            mode = "solo"

    if difficulty is None:
        difficulty = "medium"

    # 1. Start game server
    app = web.Application()
    tetris.setup_app(app)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, args.host, args.port)
    await site.start()
    base_url = f"http://{args.host}:{args.port}"
    print(f"\n[Server] Tetris server running at {base_url}", flush=True)

    # 2. Determine target page & launch browser
    if mode == "solo":
        target_page = base_url
        mode_desc = "Solo Play (Play by yourself)"
    elif mode == "vs":
        target_page = f"{base_url}/vs?difficulty={difficulty}"
        mode_desc = f"Player vs Bot [Difficulty: {difficulty.upper()}]"
    else:  # watch
        target_page = f"{base_url}/watch"
        mode_desc = f"Watch Bot Play [Difficulty: {difficulty.upper()}]"

    if not args.no_browser:
        print(f"[Browser] Launching {target_page}", flush=True)
        webbrowser.open(target_page)

    print(f"[Mode] {mode_desc}", flush=True)
    print("[Info] Press Ctrl+C in terminal to stop.", flush=True)

    # 3. Handle game runtime
    if mode == "watch":
        async with aiohttp.ClientSession() as client:
            ws_target = f"ws://{args.host}:{args.port}/ws"
            bot_task = asyncio.create_task(bot.play_games(client, ws_target, difficulty=difficulty, loop=True))
            try:
                await bot_task
            except asyncio.CancelledError:
                pass
            finally:
                bot_task.cancel()
                await runner.cleanup()
    else:
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            pass
        finally:
            await runner.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Exit] Stopped Tetris.")
        sys.exit(0)
