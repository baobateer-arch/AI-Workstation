#!/bin/sh
# AI Workstation Stop Auto Refresh Script

PID_FILE="/mnt/us/extensions/AIWorkstation/refresh.pid"
LOG_FILE="/mnt/us/extensions/AIWorkstation/refresh.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
    echo "$1"
}

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        rm -f "$PID_FILE"
        log "Auto refresh stopped (PID: $PID)"
        echo "Stopped"
    else
        rm -f "$PID_FILE"
        log "Process not running, cleaned PID file"
        echo "Not running"
    fi
else
    log "No PID file found"
    echo "Not running"
fi
