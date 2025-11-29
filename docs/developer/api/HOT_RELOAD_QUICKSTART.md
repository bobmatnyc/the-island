# Hot-Reload Quick Start Guide

**Quick Summary**: Quick reference guide for rapid lookup of key information.

**Category**: Quick Reference
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- **Toast notification** appears in bottom-right corner
- **Browser console** logs: `[Hot-Reload] entity_network updated...`
- **Network graph** automatically reloads (if you're on that tab)
- No manual refresh needed!

---

## What is Hot-Reload?

The Epstein Archive site now **automatically updates** when data files change - no manual page refresh needed!

When you modify data files (entity network, timeline, etc.), the frontend:
1. Receives instant notification via Server-Sent Events (SSE)
2. Shows toast notification: "entity network updated - reloading..."
3. Automatically fetches and displays updated data
4. All without requiring manual page refresh!

## Quick Test

### 1. Start the Server

```bash
cd /Users/masa/Projects/Epstein/server
python3 app.py 8000
```

### 2. Open Browser

Visit: `http://localhost:8000`

Look for the **"Live"** indicator in the bottom-left corner (green dot = connected).

### 3. Trigger an Update

In another terminal:

```bash
cd /Users/masa/Projects/Epstein/server
python3 test_hot_reload.py entity_network
```

### 4. Watch the Magic! ✨

You should see:
- **Toast notification** appears in bottom-right corner
- **Browser console** logs: `[Hot-Reload] entity_network updated...`
- **Network graph** automatically reloads (if you're on that tab)
- No manual refresh needed!

## Testing Different Data Types

```bash
# Test entity network updates
python3 test_hot_reload.py entity_network

# Test timeline updates
python3 test_hot_reload.py timeline

# Test entities list updates
python3 test_hot_reload.py entities

# Test any other watched file
python3 test_hot_reload.py cases
python3 test_hot_reload.py victims
python3 test_hot_reload.py entity_mappings
```

## Real-World Usage

### During Data Processing

When you run data processing scripts:

```bash
# Rebuild entity network
python3 scripts/analysis/rebuild_flight_network.py

# → Browser automatically updates when entity_network.json changes
```

```bash
# Build timeline
python3 scripts/timeline/build_timeline.py

# → Browser automatically updates when timeline_events.json changes
```

### During Development

While developing, any modification to watched files triggers auto-reload:

```bash
# Manual edit to data file
vim data/metadata/entity_network.json
# Save (:wq)

# → Browser detects change and reloads!
```

## Configuration

### Enable/Disable

Edit `.env.local`:

```bash
# Enable hot-reload (default)
ENABLE_HOT_RELOAD=true

# Disable hot-reload
ENABLE_HOT_RELOAD=false
```

Restart server after changing.

### Watched Files

These files automatically trigger updates:

| File | Event Type | What Reloads |
|------|-----------|--------------|
| `entity_network.json` | `entity_network_updated` | Network graph |
| `timeline_events.json` | `timeline_updated` | Timeline view |
| `master_document_index.json` | `entities_updated` | Entities list |
| `unified_document_index.json` | `documents_updated` | Document stats |
| `cases_index.json` | `cases_updated` | Cases data |
| `victims_index.json` | `victims_updated` | Victims data |
| `entity_name_mappings.json` | `entity_mappings_updated` | Entity names |
| `entity_filter_list.json` | `entity_filter_updated` | Entity filters |

## Troubleshooting

### "Live" indicator not showing?

1. Check browser console for errors
2. Verify you're logged in (session token valid)
3. Check server logs for SSE connection
4. Ensure `ENABLE_HOT_RELOAD=true` in `.env.local`

### File changes not detected?

1. Check file is in `data/metadata/` directory
2. Verify file is in the watched list above
3. Look for errors in server logs
4. Test with: `python3 test_hot_reload.py entity_network`

### Toast notifications not appearing?

1. Check browser console for JavaScript errors
2. Try different browser (Chrome, Firefox, Safari all supported)
3. Disable browser extensions that might block UI

## Browser Support

### Full SSE Support
✅ Chrome 6+
✅ Firefox 6+
✅ Safari 5+
✅ Edge 79+
✅ Opera 11+

### Fallback Mode
⚠️ IE 11 (uses polling every 30 seconds)

## Technical Details

For detailed documentation, see: `HOT_RELOAD_README.md`

## Need Help?

1. Check server logs: `tail -f logs/app.log`
2. Check browser console (F12 → Console)
3. Run test script: `python3 test_hot_reload.py entity_network`
4. See full docs: `HOT_RELOAD_README.md`

---

**Enjoy seamless real-time updates! 🚀**
