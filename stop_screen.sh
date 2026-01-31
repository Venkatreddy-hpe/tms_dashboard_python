#!/bin/bash
# TMS Dashboard - Stop Screen Session

SESSION_NAME="tms_dashboard"

# Check if session exists
if ! screen -list | grep -q "$SESSION_NAME"; then
    echo "❌ No session named '$SESSION_NAME' found!"
    echo ""
    echo "Active screen sessions:"
    screen -ls
    exit 1
fi

echo "🛑 Stopping TMS Dashboard..."

# Kill the session
screen -X -S "$SESSION_NAME" quit

# Wait a moment
sleep 1

# Verify it's stopped
if ! screen -list | grep -q "$SESSION_NAME"; then
    echo "✅ TMS Dashboard stopped successfully!"
else
    echo "❌ Failed to stop session"
    exit 1
fi
