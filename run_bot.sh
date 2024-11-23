#!/bin/bash

# Set working directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Export environment variables from .env file
set -a
source .env
set +a

# Run the bot with start command
python3 manage.py start
