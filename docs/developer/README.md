# Developer Documentation

**Last Updated**: November 17, 2025

This directory contains technical documentation for developers working on the Epstein Document Archive project.

---

## 📋 QUICK START

### Essential Developer Reading
1. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick command reference
2. **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Testing procedures and guidelines
3. **[CHATBOT_INTEGRATION.md](CHATBOT_INTEGRATION.md)** - Chatbot integration guide

---

## 📚 DOCUMENTATION INDEX

### System Architecture
- **[CHATBOT_INTEGRATION.md](CHATBOT_INTEGRATION.md)** - Chatbot integration guide and examples

### Development Guides
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick command reference for common tasks
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Testing procedures, guidelines, and best practices
- **[BUG_FIXES.md](BUG_FIXES.md)** - Bug tracking, fixes, and known issues
- **[BUG_FIX_SUMMARY.md](BUG_FIX_SUMMARY.md)** - Summary of major bug fixes
- **[API_FIXES_SUMMARY.md](API_FIXES_SUMMARY.md)** - API-related bug fixes and improvements

### UI/Frontend Documentation
- **[BEFORE_AFTER.md](BEFORE_AFTER.md)** - Before/after comparisons of UI changes and improvements

---

## 🛠️ DEVELOPMENT WORKFLOW

### Setting Up Development Environment
```bash
# Clone repository
git clone <repository-url>
cd Epstein

# Install Python dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Install web dependencies
cd server/web
npm install
```

### Running the Development Server
```bash
# Start backend server
cd server
uvicorn api:app --reload --port 8000

# Start frontend development server
cd server/web
npm run dev
```

### Running Tests
```bash
# Run Python tests
pytest

# Run frontend tests
cd server/web
npm test
```

See **[TESTING_GUIDE.md](TESTING_GUIDE.md)** for comprehensive testing documentation.

---

## 🏗️ ARCHITECTURE OVERVIEW

### System Components
- **Backend API**: FastAPI server (`server/api.py`)
- **Frontend**: React + TypeScript (`server/web/`)
- **Knowledge Graph**: KuzuDB graph database
- **Search**: Semantic search with embeddings
- **Chatbot**: LLM-powered conversational interface

### Key Technologies
- **Python**: FastAPI, KuzuDB, sentence-transformers
- **Frontend**: React, TypeScript, Vite, TailwindCSS
- **Database**: KuzuDB (graph database), SQLite (metadata)
- **AI/ML**: OpenAI API, sentence-transformers

See **[CHATBOT_KNOWLEDGE_SYSTEM.md](CHATBOT_KNOWLEDGE_SYSTEM.md)** for detailed architecture.

---

## 🐛 DEBUGGING & TROUBLESHOOTING

### Common Issues
See **[BUG_FIXES.md](BUG_FIXES.md)** for a comprehensive list of known issues and fixes.

### Debugging Tools
- **Browser DevTools**: Network tab, Console, React DevTools
- **Python Debugger**: `pdb` or VSCode debugger
- **API Testing**: Postman, curl, or `/docs` endpoint

### Logging
- **Backend logs**: Check console output from uvicorn
- **Frontend logs**: Check browser console
- **Database logs**: KuzuDB query logs

---

## 📖 API DOCUMENTATION

### REST API Endpoints
Access interactive API documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints
- `GET /api/entities` - List all entities
- `GET /api/entities/{id}` - Get entity details
- `GET /api/relationships` - Get relationships
- `POST /api/search` - Semantic search
- `POST /api/chat` - Chatbot endpoint

---

## 🧪 TESTING

### Test Coverage
- **Unit Tests**: Test individual functions and components
- **Integration Tests**: Test API endpoints and database operations
- **E2E Tests**: Test complete user workflows

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py

# Run with coverage
pytest --cov=server --cov-report=html
```

See **[TESTING_GUIDE.md](TESTING_GUIDE.md)** for detailed testing documentation.

---

## 🎨 UI DEVELOPMENT

### Frontend Structure
```
server/web/
├── src/
│   ├── components/     # React components
│   ├── pages/          # Page components
│   ├── hooks/          # Custom React hooks
│   ├── utils/          # Utility functions
│   └── types/          # TypeScript types
├── public/             # Static assets
└── package.json        # Dependencies
```

### Key Components
- **Network Visualization**: Force-directed graph (D3.js/vis.js)
- **Document Viewer**: Markdown rendering with syntax highlighting
- **Search Interface**: Semantic search with autocomplete
- **Chatbot Interface**: Conversational UI with streaming responses

See **[EDGE_TOOLTIPS_IMPLEMENTATION.md](EDGE_TOOLTIPS_IMPLEMENTATION.md)** and **[NETWORK_FEATURES.md](NETWORK_FEATURES.md)** for UI implementation details.

---

## 📝 CODING STANDARDS

### Python Code Style
- **PEP 8**: Follow Python style guide
- **Type Hints**: Use type annotations
- **Docstrings**: Document all public functions
- **Formatting**: Use `black` for code formatting

### TypeScript Code Style
- **ESLint**: Follow ESLint rules
- **Prettier**: Use Prettier for formatting
- **Type Safety**: Avoid `any`, use proper types
- **Components**: Functional components with hooks

### Git Workflow
```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: add your feature"

# Push and create PR
git push origin feature/your-feature-name
```

---

## 🔧 COMMON TASKS

### Adding a New Entity Type
1. Update KuzuDB schema
2. Update API endpoints
3. Update frontend types
4. Add tests

### Adding a New API Endpoint
1. Define endpoint in `server/api.py`
2. Add tests in `tests/test_api.py`
3. Update API documentation
4. Update frontend API client

### Updating the Knowledge Graph
1. Modify ingestion scripts
2. Run database migrations
3. Rebuild indexes
4. Update queries

See **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** for quick command reference.

---

## 📚 ADDITIONAL RESOURCES

### Related Documentation
- **[../README.md](../README.md)** - Main documentation index
- **[../data/README.md](../data/README.md)** - Data documentation
- **[../deployment/README.md](../deployment/README.md)** - Deployment documentation
- **[../../CLAUDE.md](../../CLAUDE.md)** - Project resumption guide

### External Resources
- **FastAPI**: https://fastapi.tiangolo.com/
- **React**: https://react.dev/
- **KuzuDB**: https://kuzudb.com/
- **TypeScript**: https://www.typescriptlang.org/

---

## 🤝 CONTRIBUTING

### Before You Start
1. Read this documentation
2. Review existing code and patterns
3. Check open issues and PRs
4. Set up development environment

### Contribution Guidelines
1. Write tests for new features
2. Follow coding standards
3. Update documentation
4. Create clear PR descriptions
5. Respond to review feedback

---

*For questions or issues, check [BUG_FIXES.md](BUG_FIXES.md) or create a new issue.*
