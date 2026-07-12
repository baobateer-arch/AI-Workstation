#!/bin/sh
# AI Workstation Dashboard 更新脚本
# 用于 Kindle KUAL Extension

# 配置
SERVER_URL="http://192.168.31.138:8765/dashboard.png"
TARGET_PATH="/mnt/us/dashboard_kindle.png"
LOG_FILE="/mnt/us/extensions/AIWorkstation/update.log"

# 日志函数
log() {
    echo "[$(date '+%H:%M:%S')] $1"
    echo "[$(date '+%H:%M:%S')] $1" >> "$LOG_FILE"
}

# 开始
log "=== AI Workstation Update ==="
log "Server: $SERVER_URL"
log "Target: $TARGET_PATH"

# 检查网络连接
log "Checking network..."
if ! ping -c 1 -W 3 192.168.31.138 > /dev/null 2>&1; then
    log "ERROR: Cannot reach server"
    exit 1
fi
log "Network OK"

# 下载图片
log "Downloading..."
if wget -q -O "$TARGET_PATH" "$SERVER_URL"; then
    # 验证文件
    if [ -f "$TARGET_PATH" ]; then
        FILE_SIZE=$(ls -l "$TARGET_PATH" | awk '{print $5}')
        log "Download complete"
        log "File size: $FILE_SIZE bytes"
        
        # 刷新 Kindle 显示
        lipc-set-prop com.lab126.winmgr appDrawUpdate 1 2>/dev/null
        
        log "=== Update Complete ==="
        exit 0
    else
        log "ERROR: File not found after download"
        exit 1
    fi
else
    log "ERROR: Download failed"
    exit 1
fi
