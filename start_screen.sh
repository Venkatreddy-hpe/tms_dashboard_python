#!/bin/bash
# TMS Dashboard - Start in Screen Session

SESSION_NAME="tms_dashboard"

# Check if session already exists
if screen -list | grep -q "$SESSION_NAME"; then
    echo "❌ Session '$SESSION_NAME' already exists!"
    echo ""
    echo "To view it, run:"
    echo "  screen -r $SESSION_NAME"
    echo ""
    echo "To kill existing session first:"
    echo "  screen -X -S $SESSION_NAME quit"
    exit 1
fi

echo "🚀 Starting TMS Dashboard in screen session..."
echo ""

# Start screen session in detached mode
screen -dmS "$SESSION_NAME" bash -c "cd /home/pdanekula/tms_dashboard_python && python3 app.py"

# Wait a moment for server to start
sleep 2

# Check if it's running
if screen -list | grep -q "$SESSION_NAME"; then
    echo "✅ TMS Dashboard started successfully!"
    echo ""
    echo "📋 Session Name: $SESSION_NAME"
    echo "🌐 Access URL: http://10.9.91.22:8080"
    echo ""
    echo "📚 Useful Commands:"
    echo "  • View/attach to session:  screen -r $SESSION_NAME"
    echo "  • Detach from session:     Press Ctrl+A then D"
    echo "  • Stop the server:         screen -X -S $SESSION_NAME quit"
    echo "  • List all sessions:       screen -ls"
    echo ""
else
    echo "❌ Failed to start session"
    exit 1
fi
