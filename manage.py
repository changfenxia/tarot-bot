#!/usr/bin/env python3
import os
import sys
import signal
import subprocess
from pathlib import Path

BOT_DIR = Path(__file__).resolve().parent
PID_FILE = BOT_DIR / "bot.pid"
VENV_PYTHON = BOT_DIR / "venv" / "bin" / "python"

def start_bot():
    if PID_FILE.exists():
        print("Bot already running or PID file exists")
        return
    
    process = subprocess.Popen(
        [str(VENV_PYTHON), "app/bot.py"],
        cwd=str(BOT_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    PID_FILE.write_text(str(process.pid))
    print(f"Bot started with PID {process.pid}")

def stop_bot():
    if not PID_FILE.exists():
        print("Bot not running or PID file not found")
        return
    
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, signal.SIGTERM)
        PID_FILE.unlink()
        print(f"Bot stopped (PID {pid})")
    except ProcessLookupError:
        print("Bot process not found")
        PID_FILE.unlink()
    except Exception as e:
        print(f"Error stopping bot: {e}")

def restart_bot():
    stop_bot()
    start_bot()

def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ['start', 'stop', 'restart']:
        print("Usage: python manage.py [start|stop|restart]")
        return

    command = sys.argv[1]
    if command == 'start':
        start_bot()
    elif command == 'stop':
        stop_bot()
    elif command == 'restart':
        restart_bot()

if __name__ == '__main__':
    main()
