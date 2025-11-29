# Epstein Document Archive - Access Information

**Quick Summary**: **Public URL**: https://c61d9c1c764c. ngrok.

**Category**: Deployment
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- Username: `epstein`
- Password: `archive2025`
- **Overview Dashboard**: Statistics and top entities
- **Ingestion Progress**: Real-time OCR status with auto-refresh (every 5 seconds)
- **Network Graph**: Interactive D3.js visualization of entity connections

---

## 🌐 Public Access (ngrok)

**Public URL**: https://c61d9c1c764c.ngrok.app

**Credentials**:
- Username: `epstein`
- Password: `archive2025`

## 🏠 Local Access

**Local URL**: http://localhost:8081

**Credentials**: Same as above

## 📊 Available Features

### Web Interface
- **Overview Dashboard**: Statistics and top entities
- **Ingestion Progress**: Real-time OCR status with auto-refresh (every 5 seconds)
- **Network Graph**: Interactive D3.js visualization of entity connections
- **Entity Details**: Comprehensive profiles with connections and documents
- **Documents**: Document search and classification
- **🤖 AI Chat Assistant**: Qwen 2.5 Coder chatbot for archive questions (bottom right corner)
  - Ask about entities, connections, documents
  - Get statistics and archive information
  - ⚠️ Note: Responses may be slow (30-60 seconds) - running on local LLM
- **📤 Source Suggestions**: Submit URLs for new document sources
  - Security validated before acceptance
  - Stored for manual review

### API Endpoints

All endpoints require HTTP Basic Authentication with the credentials above.

**Core APIs**:
- `GET /` - Web interface (redirects to /static/index.html)
- `GET /api/stats` - Overall statistics
- `GET /api/ingestion/status` - Live ingestion progress
- `GET /api/entities` - List entities (with filtering/sorting)
- `GET /api/entities/{name}` - Entity details
- `GET /api/network` - Network graph data
- `GET /api/search?q={query}` - Search entities and documents
- `GET /api/timeline` - Timeline events

**AI Chat APIs** (NEW):
- `POST /api/chat` - Chat with Qwen assistant about the archive
- `POST /api/suggest-source` - Submit a source URL suggestion
- `GET /api/suggestions` - View submitted source suggestions

### API Documentation
- **Interactive Docs**: http://localhost:8081/docs (Swagger UI)
- **ReDoc**: http://localhost:8081/redoc

## 🔐 Security

- HTTP Basic Authentication required for all endpoints
- Credentials stored in `server/.credentials` file
- Password-protected via browser authentication dialog
- ngrok tunnel provides HTTPS encryption

## 🎯 Current Archive Status

As of now:
- **Entities**: 1,702 (71 duplicates merged)
- **Network Nodes**: 387
- **Network Connections**: 2,221 edges
- **Documents**: 6 classified
- **OCR Progress**: Check ingestion dashboard for real-time status

## 🛠️ Starting/Stopping Services

### Start FastAPI Server
```bash
cd /Users/masa/Projects/Epstein
source .venv/bin/activate
cd server
python3 app.py 8081
```

### Start ngrok Tunnel
```bash
ngrok http 8081
```

### Stop Services
```bash
# Kill FastAPI server
pkill -f "python3 app.py 8081"

# Kill ngrok
pkill -f "ngrok http"
```

## 📝 Modifying Credentials

Edit `server/.credentials`:
```
username1:password1
username2:password2
```

Then restart the FastAPI server.

## 🔍 Monitoring

- **Server Logs**: Check the terminal where FastAPI is running
- **Ingestion Progress**: Navigate to "Ingestion Progress" tab in web interface
- **OCR Status**: Real-time updates every 5 seconds
- **ngrok Dashboard**: http://localhost:4040

## 📚 Documentation

- Full project structure: See `README.md` in project root
- API endpoints: Visit `/docs` on the running server
- Network visualization: D3.js force-directed graph with zoom/pan
- Entity search: Real-time filtering in sidebar

---

**Generated**: 2025-11-17 02:46 EDT
**Server**: FastAPI with uvicorn
**Tunnel**: ngrok
**Authentication**: HTTP Basic Auth
