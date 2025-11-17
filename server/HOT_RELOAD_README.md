# Hot-Reload System Documentation

## Overview

The Epstein Archive site now features **dynamic hot-reload capability** that automatically updates the frontend when data files change. This eliminates the need for manual page refreshes during development and data updates.

## Architecture

### Backend Components

1. **File Watcher Service** (`services/file_watcher.py`)
   - Monitors `data/metadata/` and `data/md/entities/` directories
   - Detects changes to JSON data files
   - Debounces rapid changes (1 second window)
   - Broadcasts events to connected SSE clients

2. **SSE Endpoint** (`/api/sse/updates`)
   - Server-Sent Events stream for real-time updates
   - Authenticates clients via session tokens
   - Sends keepalive pings every 30 seconds
   - Graceful cleanup on disconnect

3. **Watched Files**
   - `entity_network.json` → `entity_network_updated`
   - `timeline_events.json` → `timeline_updated`
   - `master_document_index.json` → `entities_updated`
   - `unified_document_index.json` → `documents_updated`
   - `cases_index.json` → `cases_updated`
   - `victims_index.json` → `victims_updated`
   - `entity_name_mappings.json` → `entity_mappings_updated`
   - `entity_filter_list.json` → `entity_filter_updated`

### Frontend Components

1. **Hot-Reload Client** (`web/hot-reload.js`)
   - Connects to SSE endpoint on page load
   - Auto-reconnects on disconnect (5 second delay)
   - Fallback to polling for unsupported browsers
   - Toast notifications for update alerts

2. **Event Handlers** (`web/app.js`)
   - Registered handlers for each data type
   - Calls appropriate reload functions
   - Logs updates to console

3. **UI Components**
   - Toast notifications (bottom-right corner)
   - Status indicator (bottom-left corner)
   - CSS animations for smooth transitions

## Usage

### Enable/Disable Hot-Reload

Set environment variable in `.env.local`:

```bash
# Enable hot-reload (default in development)
ENABLE_HOT_RELOAD=true

# Disable hot-reload (recommended for production)
ENABLE_HOT_RELOAD=false
```

### Test Hot-Reload

Use the test script to simulate file updates:

```bash
# Test entity network updates
python3 server/test_hot_reload.py entity_network

# Test timeline updates
python3 server/test_hot_reload.py timeline

# Test any JSON file
python3 server/test_hot_reload.py entity_filter_list.json
```

### Expected Behavior

1. **File Changed**
   - Modification detected by watchdog observer
   - 1 second debounce delay
   - Event broadcast to SSE clients

2. **Frontend Receives Event**
   - Toast notification appears (bottom-right)
   - Console logs: `[App] entity_network updated, reloading...`
   - Data automatically reloaded (no page refresh)

3. **User Experience**
   - Seamless updates during data processing
   - No manual refresh needed
   - Visual feedback via toast notifications

## Event Flow

```
File System Change
        ↓
Watchdog Observer (file_watcher.py)
        ↓
1 second debounce
        ↓
Broadcast to SSE clients
        ↓
Frontend receives event (hot-reload.js)
        ↓
Show toast notification
        ↓
Call reload handler (app.js)
        ↓
Fetch updated data from API
        ↓
Update UI components
```

## Browser Support

### Full SSE Support
- Chrome 6+
- Firefox 6+
- Safari 5+
- Edge 79+
- Opera 11+

### Fallback Polling
- IE 11 (not supported, uses polling)
- Older browsers without EventSource API

## Configuration

### File Watcher Settings

```python
# services/file_watcher.py
class DataFileWatcher:
    debounce_delay = 1.0  # seconds
    EVENT_MAP = {
        "entity_network.json": "entity_network_updated",
        # ... other mappings
    }
```

### SSE Settings

```python
# app.py
@app.get("/api/sse/updates")
async def sse_updates():
    # Keepalive timeout: 30 seconds
    # Max queue size: 100 events
    # Auto-reconnect: 5 seconds
```

### Frontend Settings

```javascript
// web/hot-reload.js
class HotReloadClient {
    reconnectDelay = 5000;      // 5 seconds
    pollingDelay = 30000;       // 30 seconds (fallback)
}
```

## Troubleshooting

### SSE Connection Not Established

**Symptoms:**
- No "Live" indicator in bottom-left
- No console message: `[Hot-Reload] Connected`

**Solutions:**
1. Check authentication (session token valid)
2. Verify `ENABLE_HOT_RELOAD=true` in `.env.local`
3. Check server logs for connection errors
4. Ensure no firewall blocking SSE endpoint

### File Changes Not Detected

**Symptoms:**
- File modified but no toast notification
- No console message about updates

**Solutions:**
1. Verify file is in watched directory (`data/metadata/`)
2. Check file is in EVENT_MAP (file_watcher.py)
3. Look for file watcher errors in server logs
4. Test with: `python3 test_hot_reload.py entity_network`

### Toast Notifications Not Appearing

**Symptoms:**
- Console shows updates but no visual notification

**Solutions:**
1. Check browser console for JavaScript errors
2. Verify CSS is loaded (inspect `.hot-reload-toast`)
3. Check z-index conflicts with other UI elements

### Reconnection Loop

**Symptoms:**
- Constant reconnect attempts in console
- Status indicator flickering

**Solutions:**
1. Check server is running and accessible
2. Verify authentication endpoint working
3. Look for CORS issues in browser console
4. Check server logs for SSE endpoint errors

## Performance Considerations

### Memory Usage
- Each SSE connection: ~10KB overhead
- Queue per client: Max 100 events (~50KB)
- Typical usage: Minimal impact (<1MB per 10 clients)

### Network Usage
- Keepalive pings: ~50 bytes every 30 seconds
- Update events: ~200 bytes per file change
- Typical: <1KB/minute per client

### Server Load
- File watching: Negligible CPU (<0.1%)
- SSE streaming: ~0.5% CPU per 100 clients
- Broadcasting: O(n) where n = connected clients

## Development Tips

### Debugging SSE

```javascript
// Browser console
const status = window.hotReload.getStatus();
console.log('Hot-reload status:', status);
// { connected: true, method: 'SSE', handlers: 8 }
```

### Manual Event Testing

```python
# In Python REPL
from services.file_watcher import DataFileWatcher
watcher = DataFileWatcher()
watcher.broadcast('entity_network_updated', 'entity_network.json')
```

### Adding New Watched Files

1. Add to `EVENT_MAP` in `file_watcher.py`:
   ```python
   EVENT_MAP = {
       "new_file.json": "new_data_updated",
   }
   ```

2. Register handler in `app.js`:
   ```javascript
   hotReload.on('new_data', (data) => {
       console.log('New data updated');
       loadNewData();
   });
   ```

3. Update SSE endpoint docstring in `app.py`

## Production Deployment

### Recommendations

1. **Disable in Production**
   ```bash
   ENABLE_HOT_RELOAD=false
   ```

2. **Or Enable Selectively**
   - Only for admin dashboard
   - Only for development environments
   - With rate limiting per client

3. **Security Considerations**
   - SSE endpoint requires authentication
   - No sensitive data in event payloads
   - Proper CORS configuration

### Monitoring

Track these metrics:
- Number of connected SSE clients
- Event broadcast frequency
- Reconnection rate
- Client-side error rate

## Future Enhancements

Potential improvements:
- [ ] Granular updates (only reload changed entities)
- [ ] Binary diff protocol for large files
- [ ] Compression for event payloads
- [ ] Client-side caching with ETags
- [ ] Selective subscription (choose which events to receive)
- [ ] WebSocket upgrade option

## Dependencies

### Backend
```
watchdog==3.0.0         # File system monitoring
sse-starlette==1.8.2    # SSE support for FastAPI
```

### Frontend
```
Native EventSource API  # Browser-native SSE client
No additional libraries required
```

## License

Part of the Epstein Document Archive project.
See main project README for license information.
