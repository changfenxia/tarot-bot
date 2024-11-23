#!/usr/bin/env python3
import os
import sys
import signal
import subprocess
import time
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BOT_DIR = Path(__file__).resolve().parent
PID_FILE = BOT_DIR / "bot.pid"
LOCK_FILE = BOT_DIR / "bot.lock"
VENV_PYTHON = BOT_DIR / "venv" / "bin" / "python"

def cleanup_files():
    """Remove PID and lock files if they exist."""
    for file in [PID_FILE, LOCK_FILE]:
        try:
            if file.exists():
                file.unlink()
                logger.info(f"Removed {file}")
        except Exception as e:
            logger.error(f"Error removing {file}: {e}")

def start_bot():
    cleanup_files()  # Clean up any stale files before starting
    
    try:
        process = subprocess.Popen(
            [str(VENV_PYTHON), "app/bot.py"],
            cwd=str(BOT_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a bit to see if the process starts successfully
        time.sleep(2)
        if process.poll() is not None:
            # Process has already terminated
            stdout, stderr = process.communicate()
            logger.error(f"Bot failed to start. Exit code: {process.returncode}")
            logger.error(f"stdout: {stdout.decode()}")
            logger.error(f"stderr: {stderr.decode()}")
            return
        
        PID_FILE.write_text(str(process.pid))
        logger.info(f"Bot started with PID {process.pid}")
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        cleanup_files()

def stop_bot():
    if not PID_FILE.exists():
        logger.info("Bot not running or PID file not found")
        cleanup_files()
        return
    
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, signal.SIGTERM)
        
        # Wait for process to terminate
        max_wait = 10
        while max_wait > 0:
            try:
                os.kill(pid, 0)  # Check if process exists
                time.sleep(1)
                max_wait -= 1
            except ProcessLookupError:
                break
        
        if max_wait == 0:
            logger.warning("Bot didn't stop gracefully, forcing termination")
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        
        logger.info(f"Bot stopped (PID {pid})")
        
    except ProcessLookupError:
        logger.warning("Bot process not found")
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
    finally:
        cleanup_files()

def restart_bot():
    logger.info("Restarting bot...")
    stop_bot()
    time.sleep(2)  # Wait for resources to be properly released
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
