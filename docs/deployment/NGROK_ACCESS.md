# Epstein Document Archive - Public Access via Ngrok

**Quick Summary**: **Last Updated**: 2025-11-17 00:18 EST...

**Category**: Deployment
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- Username: `epstein`
- Password: `@rchiv*!2025`
- Username: `masa`
- Password: `@rchiv*!2025`
- **Main Site**: https://d470886dc7af.ngrok.app

---

**Last Updated**: 2025-11-17 00:18 EST

## Public Access URL

**HTTPS URL**: https://d470886dc7af.ngrok.app

### Authentication Credentials

**Option 1**:
- Username: `epstein`
- Password: `@rchiv*!2025`

**Option 2**:
- Username: `masa`
- Password: `@rchiv*!2025`

## Quick Access Links

- **Main Site**: https://d470886dc7af.ngrok.app
- **Ngrok Dashboard**: http://localhost:4040 (local only)
- **API Stats**: https://d470886dc7af.ngrok.app/api/stats

## Tunnel Management

### Check Status
```bash
/Users/masa/Projects/Epstein/scripts/ngrok_manager.sh status
```

### Stop Tunnel
```bash
/Users/masa/Projects/Epstein/scripts/ngrok_manager.sh stop
```

### Restart Tunnel
```bash
/Users/masa/Projects/Epstein/scripts/ngrok_manager.sh restart
```

### Start Tunnel
```bash
/Users/masa/Projects/Epstein/scripts/ngrok_manager.sh start
```

## Features Available

1. **Entity Search** - Search 1,702 entities from contact books and flight logs
2. **Document Explorer** - Browse 6 documents (will expand to 67,144 after OCR)
3. **Network Visualization** - Interactive graph of 387 entities and 2,221 connections
4. **Entity Details** - View entity profiles, connections, and document mentions
5. **Timeline View** - Chronological event timeline (coming soon)
6. **Dark/Light Theme** - Toggle theme in top-right corner

## Current Data Stats

- **Total Entities**: 1,702
- **Documents Indexed**: 6 (OCR in progress for 67,144)
- **Network Nodes**: 387
- **Network Connections**: 2,221
- **OCR Progress**: 45% complete (15,100 / 33,572 files)

## Technical Details

### Server Backend
- **Local Port**: 8081
- **Framework**: FastAPI (Python)
- **Process ID**: Run `lsof -ti:8081` to check

### Ngrok Tunnel
- **Public Port**: 443 (HTTPS)
- **Local Port**: 8081
- **Protocol**: HTTPS only
- **Logs**: `/Users/masa/Projects/Epstein/logs/ngrok.log`

### Security
- HTTP Basic Authentication enabled
- All traffic encrypted via HTTPS (ngrok)
- No sensitive data in public URLs
- Credentials required for all endpoints

## Important Notes

1. **URL Persistence**: The ngrok URL (https://d470886dc7af.ngrok.app) will change if the tunnel is restarted. Use the manager script to get the current URL.

2. **Free Tier Limits**: Ngrok free tier has:
   - Random subdomain (changes on restart)
   - 40 connections/minute limit
   - Session timeout after inactivity

3. **Uptime**: The tunnel will stay active as long as:
   - The ngrok process is running
   - The backend server (port 8081) is running
   - Your computer doesn't sleep/restart

4. **Sharing**: You can share the public URL with anyone. They will need the authentication credentials to access the site.

## Troubleshooting

### URL Not Working
```bash
# Check if ngrok is running
/Users/masa/Projects/Epstein/scripts/ngrok_manager.sh status

# Restart if needed
/Users/masa/Projects/Epstein/scripts/ngrok_manager.sh restart
```

### Server Not Responding
```bash
# Check if backend server is running
lsof -ti:8081

# If no output, restart the server:
cd /Users/masa/Projects/epstein/server/web
python3 app.py
```

### Authentication Issues
- Ensure you're using the exact credentials (case-sensitive)
- Password includes special characters: `@rchiv*!2025`
- Try both username options: `epstein` or `masa`

### Check Ngrok Logs
```bash
tail -f /Users/masa/Projects/Epstein/logs/ngrok.log
```

## Ngrok Web Interface (Local Only)

Access http://localhost:4040 for:
- Request/response inspection
- Traffic statistics
- Replay requests
- Connection details

---

**Pro Tip**: Bookmark the public URL and save these credentials in your password manager for easy access.
