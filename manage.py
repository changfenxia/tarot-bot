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
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot_manager.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

BOT_DIR = Path(__file__).resolve().parent
PID_FILE = BOT_DIR / "bot.pid"
LOCK_FILE = BOT_DIR / "bot.lock"
VENV_PYTHON = BOT_DIR / "venv" / "bin" / "python"

# Global process variable
bot_process = None

def signal_handler(signum, frame):
    """Handle termination signals"""
    logger.info(f"Received signal {signum}")
    if bot_process:
        logger.info("Gracefully shutting down bot...")
        bot_process.terminate()
        try:
            # Wait up to 10 seconds for the process to terminate
            bot_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            logger.warning("Bot didn't terminate gracefully, forcing...")
            bot_process.kill()
    cleanup_files()
    sys.exit(0)

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
    global bot_process
    cleanup_files()  # Clean up any stale files before starting
    
    try:
        # Set up signal handlers
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        # Start the bot process
        bot_process = subprocess.Popen(
            [str(VENV_PYTHON), "-u", "app/bot.py"],  # -u for unbuffered output
            cwd=str(BOT_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1  # Line buffered
        )
        
        # Write PID file
        with open(PID_FILE, 'w') as f:
            f.write(str(bot_process.pid))
        
        logger.info(f"Started bot process with PID {bot_process.pid}")
        
        # Monitor the process and its output
        while True:
            # Check if process is still running
            if bot_process.poll() is not None:
                logger.error(f"Bot process terminated unexpectedly with code {bot_process.returncode}")
                break
                
            # Read and log output
            stdout_line = bot_process.stdout.readline()
            if stdout_line:
                logger.info(f"Bot: {stdout_line.strip()}")
            
            stderr_line = bot_process.stderr.readline()
            if stderr_line:
                logger.error(f"Bot error: {stderr_line.strip()}")
            
            # Small sleep to prevent CPU hogging
            time.sleep(0.1)
            
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        if bot_process:
            bot_process.terminate()
    finally:
        cleanup_files()

def stop_bot():
    """Stop the bot process"""
    try:
        if PID_FILE.exists():
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            try:
                os.kill(pid, signal.SIGTERM)
                logger.info(f"Sent SIGTERM to process {pid}")
                # Wait for process to terminate
                for _ in range(30):  # Wait up to 3 seconds
                    try:
                        os.kill(pid, 0)  # Check if process exists
                        time.sleep(0.1)
                    except OSError:
                        break
                else:
                    # Process didn't terminate, send SIGKILL
                    os.kill(pid, signal.SIGKILL)
                    logger.info(f"Sent SIGKILL to process {pid}")
            except ProcessLookupError:
                logger.info(f"Process {pid} not found")
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
    finally:
        cleanup_files()

def restart_bot():
    """Restart the bot"""
    stop_bot()
    time.sleep(2)  # Wait for cleanup
    start_bot()

def main():
    if len(sys.argv) < 2:
        print("Usage: python manage.py [start|stop|restart]")
        sys.exit(1)

    command = sys.argv[1].lower()
    if command == "start":
        start_bot()
    elif command == "stop":
        stop_bot()
    elif command == "restart":
        restart_bot()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == '__main__':
    main()
