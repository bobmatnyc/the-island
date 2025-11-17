# ngrok Persistent Tunnel Setup

**Domain**: https://the-island.ngrok.app
**Local Port**: 8081
**Auto-restart**: Enabled via launchd
**Health Monitoring**: Every 5 minutes

## Overview

This setup provides a persistent, self-healing ngrok tunnel that:
- Starts automatically on system boot
- Monitors tunnel health every 5 minutes
- Auto-restarts on failure
- Logs all activity
- Provides a dashboard for quick status checks

## Components

### 1. Management Script
**Location**: `/Users/masa/Projects/Epstein/scripts/ngrok_persistent.sh`

**Commands**:
```bash
# Start tunnel
./scripts/ngrok_persistent.sh start

# Stop tunnel
./scripts/ngrok_persistent.sh stop

# Restart tunnel
./scripts/ngrok_persistent.sh restart

# Check status
./scripts/ngrok_persistent.sh status

# Run monitoring loop (used by launchd)
./scripts/ngrok_persistent.sh monitor
```

### 2. Dashboard
**Location**: `/Users/masa/Projects/Epstein/scripts/ngrok_dashboard.sh`

**Usage**:
```bash
./scripts/ngrok_dashboard.sh
```

Shows:
- Service status (launchd)
- Tunnel status (up/down)
- Process health (CPU, memory, uptime)
- Backend service status (port 8081)
- Recent activity logs
- ngrok API health
- Quick action commands

### 3. launchd Service
**Location**: `~/Library/LaunchAgents/com.epstein.ngrok.plist`

**Service Management**:
```bash
# Load service (auto-start enabled)
launchctl load ~/Library/LaunchAgents/com.epstein.ngrok.plist

# Unload service
launchctl unload ~/Library/LaunchAgents/com.epstein.ngrok.plist

# Start service manually
launchctl start com.epstein.ngrok

# Stop service manually
launchctl stop com.epstein.ngrok

# Check service status
launchctl list | grep com.epstein.ngrok
```

### 4. Test Script
**Location**: `/Users/masa/Projects/Epstein/scripts/test_tunnel_failover.sh`

Simulates tunnel failure and verifies restart functionality.

## Health Checks

The monitoring script performs 3 checks every 5 minutes:

1. **Process Check**: Is ngrok running?
2. **API Check**: Is ngrok API responsive?
3. **Tunnel Check**: Is the tunnel URL listed?

If any check fails, the tunnel is automatically restarted.

## Logs

### Activity Log
**Location**: `/tmp/ngrok_persistent.log`

View real-time:
```bash
tail -f /tmp/ngrok_persistent.log
```

### Error Log
**Location**: `/tmp/ngrok_persistent_error.log`

Check for errors:
```bash
cat /tmp/ngrok_persistent_error.log
```

## Configuration

### Change Monitoring Interval
Edit `/Users/masa/Projects/Epstein/scripts/ngrok_persistent.sh`:
```bash
HEALTH_CHECK_INTERVAL=300  # Change to desired seconds
```

Then reload service:
```bash
launchctl unload ~/Library/LaunchAgents/com.epstein.ngrok.plist
launchctl load ~/Library/LaunchAgents/com.epstein.ngrok.plist
```

### Change Domain or Port
Edit `/Users/masa/Projects/Epstein/scripts/ngrok_persistent.sh`:
```bash
NGROK_URL="your-domain.ngrok.app"
LOCAL_PORT="8081"
```

## Troubleshooting

### Tunnel Won't Start
```bash
# Check ngrok auth
ngrok config check

# Verify account has custom domain access
ngrok config list

# Check if port is in use
lsof -i :8081
```

### Service Not Auto-Starting
```bash
# Verify plist syntax
plutil -lint ~/Library/LaunchAgents/com.epstein.ngrok.plist

# Check launchd logs
log show --predicate 'subsystem == "com.apple.launchd"' --last 1h | grep epstein
```

### Tunnel Keeps Restarting
```bash
# Check for errors in log
grep ERROR /tmp/ngrok_persistent.log

# Verify ngrok account status
ngrok diagnose
```

## Current Status

As of setup (2025-11-17):

- **Service**: Running (PID: 26382)
- **Tunnel**: UP
- **Public URL**: https://the-island.ngrok.app
- **Backend**: Python service on port 8081
- **Uptime**: 52 minutes
- **Connections**: 54
- **HTTP Requests**: 89

## ngrok Web Interface

Access the ngrok inspection interface:
```
http://localhost:4040
```

Features:
- Request inspection
- Replay requests
- Tunnel metrics
- Connection details

## API Access

Query tunnel status programmatically:
```bash
# Get all tunnels
curl http://localhost:4040/api/tunnels | jq

# Get specific tunnel
curl http://localhost:4040/api/tunnels/command_line | jq
```

## Security Notes

1. **Domain Access**: Requires ngrok paid account with custom domain feature
2. **Auth Token**: Stored in `~/.ngrok2/ngrok.yml`
3. **HTTPS**: All traffic to the-island.ngrok.app is encrypted
4. **Backend**: Ensure backend service has proper authentication

## Maintenance

### Monthly Tasks
- Review logs for unusual activity
- Check tunnel uptime statistics
- Verify launchd service is running
- Update ngrok if new version available

### Update ngrok
```bash
# Homebrew
brew upgrade ngrok

# Or download latest from ngrok.com
```

After updating:
```bash
./scripts/ngrok_persistent.sh restart
```

## Uninstallation

To completely remove the persistent tunnel:

```bash
# Stop and unload service
launchctl stop com.epstein.ngrok
launchctl unload ~/Library/LaunchAgents/com.epstein.ngrok.plist

# Remove service file
rm ~/Library/LaunchAgents/com.epstein.ngrok.plist

# Stop tunnel
./scripts/ngrok_persistent.sh stop

# Remove scripts (optional)
rm /Users/masa/Projects/Epstein/scripts/ngrok_persistent.sh
rm /Users/masa/Projects/Epstein/scripts/ngrok_dashboard.sh
rm /Users/masa/Projects/Epstein/scripts/test_tunnel_failover.sh

# Remove logs
rm /tmp/ngrok_persistent.log
rm /tmp/ngrok_persistent_error.log
rm /tmp/ngrok.pid
```

## Support

For ngrok issues:
- Documentation: https://ngrok.com/docs
- Status: https://status.ngrok.com
- Support: support@ngrok.com

For script issues:
- Check logs: `/tmp/ngrok_persistent.log`
- Run dashboard: `./scripts/ngrok_dashboard.sh`
- Test failover: `./scripts/test_tunnel_failover.sh`
