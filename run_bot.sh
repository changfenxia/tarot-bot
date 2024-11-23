#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Export environment variables from .env file
set -a
source .env
set +a

# Run the bot
python manage.py
