#!/bin/sh
# AI Workstation Auto Refresh Script
# 后台自动刷新 Dashboard 图片

# 配置文件路径
CONFIG_FILE="/mnt/us/extensions/AIWorkstation/config.ini"

# 读取配置函数
read_config() {
    local section=$1
    local key=$2
    local default=$3
    
    # 简单的 ini 解析
    if [ -f "$CONFIG_FILE" ]; then
        value=$(awk -F '=' "/\[$section\]/{found=1} found && /^$key/{print \$2; exit}" "$CONFIG_FILE" | tr -d ' ')
        if [ -n "$value" ]; then
            echo "$value"
            return
        fi
    fi
    echo "$default"
}

# 读取配置
SERVER_URL=$(read_config "server" "url" "http://192.168.31.138:8765/dashboard.png")
INTERVAL=$(read_config "refresh" "interval" "60")
RETRY_INTERVAL=$(read_config "refresh" "retry_interval" "30")
FBINK_MODE=$(read_config "pixel" "mode" "1")
TARGET_PATH=$(read_config "paths" "target" "/mnt/us/dashboard_kindle.png")
TEMP_PATH=$(read_config "paths" "temp" "/tmp/dashboard.png")
LOG_FILE=$(read_config "paths" "log" "/mnt/us/extensions/AIWorkstation/refresh.log")
PID_FILE=$(read_config "paths" "pid" "/mnt/us/extensions/AIWorkstation/refresh.pid")

# 日志函数
log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$msg" >> "$LOG_FILE"
    echo "$1"
}

# 检查是否已运行
check_running() {
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if kill -0 "$OLD_PID" 2>/dev/null; then
            log "Auto refresh already running (PID: $OLD_PID)"
            exit 1
        fi
    fi
}

# 写入 PID
write_pid() {
    echo $$ > "$PID_FILE"
    log "Started with PID: $$"
}

# 清理 PID
cleanup() {
    rm -f "$PID_FILE"
    log "Stopped"
    exit 0
}

# 刷新显示
refresh_display() {
    local file=$1
    if command -v fbink >/dev/null 2>&1; then
        fbink -m -b -"${FBINK_MODE}" "$file"
    elif command -v eips >/dev/null 2>&1; then
        eips -g "$file"
    fi
}

# 检查网络
check_network() {
    # 从 URL 提取 IP
    SERVER_IP=$(echo "$SERVER_URL" | sed -n 's|http://\([^:/]*\).*|\1|p')
    ping -c 1 -W 3 "$SERVER_IP" > /dev/null 2>&1
    return $?
}

# 下载图片
download_image() {
    wget -q -O "$TEMP_PATH" "$SERVER_URL" 2>/dev/null
    if [ $? -eq 0 ] && [ -f "$TEMP_PATH" ]; then
        mv "$TEMP_PATH" "$TARGET_PATH"
        return 0
    fi
    return 1
}

# 主循环
main_loop() {
    log "=== Auto Refresh Started ==="
    log "URL: $SERVER_URL"
    log "Interval: ${INTERVAL}s"
    
    trap cleanup INT TERM
    
    while true; do
        log "Checking..."
        
        if check_network; then
            if download_image; then
                log "Download OK"
                refresh_display "$TARGET_PATH"
                log "Display refreshed"
                sleep "$INTERVAL"
            else
                log "Download failed, retry in ${RETRY_INTERVAL}s"
                sleep "$RETRY_INTERVAL"
            fi
        else
            log "Network unavailable, retry in ${RETRY_INTERVAL}s"
            sleep "$RETRY_INTERVAL"
        fi
    done
}

# 检查是否已运行
check_running

# 写入 PID
write_pid

# 启动主循环
main_loop
