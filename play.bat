@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" play.py %*
) else (
    uv run --with aiohttp python play.py %*
)
