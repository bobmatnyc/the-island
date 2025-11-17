#!/bin/bash
# ngrok Quick Reference

cat << 'EOF'
╔═══════════════════════════════════════════════════════════════════╗
║                   ngrok Tunnel Quick Reference                    ║
╚═══════════════════════════════════════════════════════════════════╝

📊 DASHBOARD
  ./scripts/ngrok_dashboard.sh          Full status dashboard

🎛️  TUNNEL CONTROL
  ./scripts/ngrok_persistent.sh status   Check tunnel status
  ./scripts/ngrok_persistent.sh restart  Restart tunnel
  ./scripts/ngrok_persistent.sh stop     Stop tunnel
  ./scripts/ngrok_persistent.sh start    Start tunnel

🔧 SERVICE MANAGEMENT
  launchctl list | grep epstein          Check service
  launchctl stop com.epstein.ngrok      Stop monitoring
  launchctl start com.epstein.ngrok     Start monitoring

📝 LOGS
  tail -f /tmp/ngrok_persistent.log      Monitor activity
  grep ERROR /tmp/ngrok_persistent.log   Check errors

🌐 ACCESS
  Public URL:  https://the-island.ngrok.app
  Web UI:      http://localhost:4040
  API:         http://localhost:4040/api/tunnels

🧪 TESTING
  ./scripts/test_tunnel_failover.sh      Test auto-restart

📚 DOCUMENTATION
  cat NGROK_SETUP.md                     Full setup guide

EOF
