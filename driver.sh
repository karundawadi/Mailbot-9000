#!/bin/bash

PROJECT_DIR="/Users/karundawadi/Downloads/Mailbot-9000" # Adjust this path as necessary
VENV_PYTHON="$PROJECT_DIR/mailbot9000/bin/python"
LOGFILE="$PROJECT_DIR/python_run.log"

echo "$(date): Script starting..." >> "$LOGFILE"

cd "$PROJECT_DIR" || exit 1

source ./setup.sh >> "$LOGFILE" 2>&1

cd "$PROJECT_DIR/mailbot" || exit 1

python3 -u e2e.py >> "$LOGFILE" 2>&1 &

echo "$(date): Python script launched in background" >> "$LOGFILE"
