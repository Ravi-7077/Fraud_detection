#!/usr/bin/env bash

# Create virtual environment if it does not exist
if [ ! -d ".venv" ]; then
  python -m venv .venv
fi

# Activate virtual environment (Windows PowerShell)
# For CMD use .venv\Scripts\activate.bat
# For PowerShell use:
. .venv/Scripts/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

echo "Environment setup complete."
