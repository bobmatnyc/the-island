#!/bin/bash
# ngrok Tunnel Dashboard - Quick status overview

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NGROK_SCRIPT="$SCRIPT_DIR/ngrok_persistent.sh"
NGROK_URL="the-island.ngrok.app"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║        Epstein Archive - ngrok Tunnel Dashboard                ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 1. Service Status
echo -e "${BLUE}🔧 Service Status${NC}"
SERVICE_PID=$(launchctl list | grep com.epstein.ngrok | awk '{print $1}')
if [ -n "$SERVICE_PID" ] && [ "$SERVICE_PID" != "-" ]; then
    echo -e "   ${GREEN}✓${NC} launchd service: ${GREEN}Running${NC} (PID: $SERVICE_PID)"
else
    echo -e "   ${RED}✗${NC} launchd service: ${RED}Not Running${NC}"
fi

# 2. Tunnel Status
echo -e "\n${BLUE}🌐 Tunnel Status${NC}"
TUNNEL_STATUS=$("$NGROK_SCRIPT" status 2>&1)
if echo "$TUNNEL_STATUS" | grep -q "Tunnel Status: UP"; then
    echo -e "   ${GREEN}✓${NC} Tunnel: ${GREEN}UP${NC}"

    # Parse tunnel info
    PUBLIC_URL=$(echo "$TUNNEL_STATUS" | grep "Public URL:" | awk '{print $3}')
    LOCAL_PORT=$(echo "$TUNNEL_STATUS" | grep "Local Port:" | awk '{print $3}')
    CONNECTIONS=$(echo "$TUNNEL_STATUS" | grep "Connections:" | awk '{print $2}')
    HTTP_REQUESTS=$(echo "$TUNNEL_STATUS" | grep "HTTP Requests:" | awk '{print $3}')
    TUNNEL_PID=$(echo "$TUNNEL_STATUS" | grep "PID:" | awk '{print $2}')

    echo -e "   ${CYAN}→${NC} Public URL: ${GREEN}$PUBLIC_URL${NC}"
    echo -e "   ${CYAN}→${NC} Local Port: $LOCAL_PORT"
    echo -e "   ${CYAN}→${NC} Connections: $CONNECTIONS"
    echo -e "   ${CYAN}→${NC} HTTP Requests: $HTTP_REQUESTS"
    echo -e "   ${CYAN}→${NC} Process PID: $TUNNEL_PID"
else
    echo -e "   ${RED}✗${NC} Tunnel: ${RED}DOWN${NC}"
fi

# 3. Process Health
echo -e "\n${BLUE}💓 Process Health${NC}"
NGROK_PROC=$(ps aux | grep "ngrok.*$NGROK_URL" | grep -v grep)
if [ -n "$NGROK_PROC" ]; then
    CPU=$(echo "$NGROK_PROC" | awk '{print $3}')
    MEM=$(echo "$NGROK_PROC" | awk '{print $4}')
    UPTIME=$(ps -p $(echo "$NGROK_PROC" | awk '{print $2}') -o etime= | xargs)
    echo -e "   ${GREEN}✓${NC} ngrok process: ${GREEN}Healthy${NC}"
    echo -e "   ${CYAN}→${NC} CPU: ${CPU}%"
    echo -e "   ${CYAN}→${NC} Memory: ${MEM}%"
    echo -e "   ${CYAN}→${NC} Uptime: $UPTIME"
else
    echo -e "   ${RED}✗${NC} ngrok process: ${RED}Not Found${NC}"
fi

# 4. Backend Service Check
echo -e "\n${BLUE}🔌 Backend Service (Port 8081)${NC}"
BACKEND_PROC=$(lsof -i :8081 -sTCP:LISTEN 2>/dev/null)
if [ -n "$BACKEND_PROC" ]; then
    BACKEND_CMD=$(echo "$BACKEND_PROC" | tail -1 | awk '{print $1}')
    echo -e "   ${GREEN}✓${NC} Backend: ${GREEN}Running${NC} ($BACKEND_CMD)"
else
    echo -e "   ${YELLOW}⚠${NC} Backend: ${YELLOW}No service listening${NC}"
    echo -e "   ${CYAN}→${NC} Tunnel is active but no backend service on port 8081"
fi

# 5. Recent Logs
echo -e "\n${BLUE}📋 Recent Activity (Last 10 minutes)${NC}"
if [ -f /tmp/ngrok_persistent.log ]; then
    RECENT_LOGS=$(tail -20 /tmp/ngrok_persistent.log | grep -E "$(date -v-10M '+%Y-%m-%d %H:')" || echo "No recent activity")
    if [ "$RECENT_LOGS" != "No recent activity" ]; then
        echo "$RECENT_LOGS" | sed 's/^/   /' | tail -5
    else
        echo -e "   ${CYAN}→${NC} No activity in last 10 minutes"
    fi

    # Check for errors
    ERROR_COUNT=$(grep -c "ERROR" /tmp/ngrok_persistent.log 2>/dev/null || echo "0")
    WARNING_COUNT=$(grep -c "WARNING" /tmp/ngrok_persistent.log 2>/dev/null || echo "0")

    if [ "$ERROR_COUNT" -gt 0 ] || [ "$WARNING_COUNT" -gt 0 ]; then
        echo -e "\n   ${YELLOW}⚠${NC} Log Summary: ${RED}$ERROR_COUNT errors${NC}, ${YELLOW}$WARNING_COUNT warnings${NC}"
    fi
else
    echo -e "   ${YELLOW}⚠${NC} No log file found"
fi

# 6. API Health
echo -e "\n${BLUE}🔍 ngrok API${NC}"
API_CHECK=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null)
if [ -n "$API_CHECK" ]; then
    TUNNEL_COUNT=$(echo "$API_CHECK" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data['tunnels']))" 2>/dev/null || echo "0")
    echo -e "   ${GREEN}✓${NC} API: ${GREEN}Responsive${NC}"
    echo -e "   ${CYAN}→${NC} Active tunnels: $TUNNEL_COUNT"
else
    echo -e "   ${RED}✗${NC} API: ${RED}Not Responsive${NC}"
fi

# 7. Quick Actions
echo -e "\n${BLUE}⚡ Quick Actions${NC}"
echo -e "   ${CYAN}→${NC} Restart tunnel: $NGROK_SCRIPT restart"
echo -e "   ${CYAN}→${NC} Stop service:   launchctl stop com.epstein.ngrok"
echo -e "   ${CYAN}→${NC} Start service:  launchctl start com.epstein.ngrok"
echo -e "   ${CYAN}→${NC} View logs:      tail -f /tmp/ngrok_persistent.log"
echo -e "   ${CYAN}→${NC} Web UI:         http://localhost:4040"

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
