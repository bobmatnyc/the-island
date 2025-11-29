# Epstein Archive Server - Quick Reference

**Quick Summary**: Quick reference guide for rapid lookup of key information.

**Category**: Quick Reference
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- 🚀 Startup
- 🌐 Access Points
- 📊 RAG Endpoints
- 📝 Logs

---

## 🚀 Startup

```bash
# Start everything (recommended)
./start_all.sh

# Or start individually
./start_server.sh 8081
./start_ngrok.sh
```

## 🌐 Access Points

| Service | URL | Notes |
|---------|-----|-------|
| Local Server | http://localhost:8081/ | Development access |
| Public Server | https://the-island.ngrok.app/ | Public access via ngrok |
| Ngrok Dashboard | http://localhost:4040 | Tunnel monitoring |

## 📊 RAG Endpoints

```bash
# Search documents
curl "http://localhost:8081/api/rag/search?query=YOUR_QUERY&limit=10"

# Get statistics
curl "http://localhost:8081/api/rag/stats"

# Search by entity
curl "http://localhost:8081/api/rag/entity/ENTITY_NAME"

# Find similar documents
curl "http://localhost:8081/api/rag/similar/DOCUMENT_ID"
```

## 📝 Logs

```bash
# Server logs (real-time)
tail -f /tmp/epstein_8081_venv.log

# Ngrok logs (real-time)
tail -f /tmp/ngrok_the-island.log

# Check for errors
grep -i error /tmp/epstein_8081_venv.log
```

## 🛑 Stop Services

```bash
# Stop server
lsof -ti:8081 | xargs kill

# Stop ngrok
pkill -f "ngrok start"

# Stop all
lsof -ti:8081 | xargs kill && pkill -f "ngrok start"
```

## 🔍 Health Checks

```bash
# Server responding?
curl -I http://localhost:8081/

# RAG working?
curl -s "http://localhost:8081/api/rag/stats" | python3 -m json.tool

# Ngrok active?
curl -I https://the-island.ngrok.app/

# Check processes
ps aux | grep -E "[a]pp.py|[n]grok"
```

## 🐛 Troubleshooting

### Server won't start
```bash
# Check port usage
lsof -i:8081

# Kill processes on port
lsof -ti:8081 | xargs kill -9

# Verify venv
ls -la /Users/masa/Projects/epstein/.venv/bin/python3
```

### RAG not working
```bash
# Check ChromaDB
.venv/bin/pip list | grep chroma

# Check for RAG errors
grep -i "rag\|chroma" /tmp/epstein_8081_venv.log
```

### Ngrok issues
```bash
# Verify config
ngrok config check

# Check if running
ps aux | grep ngrok

# Check tunnel status
curl -s http://localhost:4040/api/tunnels | python3 -m json.tool
```

## 📦 Dependencies

**Install all dependencies:**
```bash
cd /Users/masa/Projects/epstein
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -r server/requirements.txt
```

**Key packages:**
- ChromaDB 0.4.22
- FastAPI 0.104.1
- SentenceTransformers
- sse-starlette 1.8.2

## ⚙️ Configuration Files

| File | Purpose |
|------|---------|
| `start_all.sh` | Start server + ngrok |
| `start_server.sh` | Start server only |
| `start_ngrok.sh` | Start ngrok only |
| `server/app.py` | Main application |
| `server/routes/rag.py` | RAG endpoints |
| `~/.config/ngrok/ngrok.yml` | Ngrok config |

## 📈 System Stats

**Current Status:**
- ✅ 33,329 documents indexed
- ✅ 284 network nodes
- ✅ 1,624 network edges
- ✅ RAG search operational
- ✅ Public access enabled

## 🔐 Security Notes

- Server runs on localhost:8081
- Ngrok provides HTTPS encryption
- Domain: the-island.ngrok.app (static)
- No authentication on endpoints (consider adding)

## 💡 Pro Tips

1. **Always use startup scripts** - They handle cleanup and verification
2. **Monitor logs** - Use `tail -f` to watch for issues in real-time
3. **Check stats** - `/api/rag/stats` shows system health
4. **Restart cleanly** - Kill old processes before starting new ones
5. **Test after restart** - Use health check commands to verify

---

**Last Updated**: 2025-11-18
**Status**: ✅ All systems operational
