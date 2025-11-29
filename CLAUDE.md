# Project Memory Configuration

This project uses KuzuMemory for intelligent context management.

## Project Information
- **Path**: /Users/masa/Projects/epstein
- **Language**: Python
- **Framework**: FastAPI

## Memory Integration

KuzuMemory is configured to enhance all AI interactions with project-specific context.

### Available Commands:
- `kuzu-memory enhance <prompt>` - Enhance prompts with project context
- `kuzu-memory learn <content>` - Store learning from conversations (async)
- `kuzu-memory recall <query>` - Query project memories
- `kuzu-memory stats` - View memory statistics

### MCP Tools Available:
When interacting with Claude Desktop, the following MCP tools are available:
- **kuzu_enhance**: Enhance prompts with project memories
- **kuzu_learn**: Store new learnings asynchronously
- **kuzu_recall**: Query specific memories
- **kuzu_stats**: Get memory system statistics

## Project Context

Comprehensive searchable archive of publicly available Epstein documents

## Linear Project Tracking

**⚠️ IMPORTANT**: This project uses Linear for issue tracking.

- **Primary Project**: [Epstein Island](https://linear.app/1m-hyperdev/project/epstein-island-13ddc89e7271/issues)
- **Project ID**: `13ddc89e7271`
- **Team**: 1M Hyperdev

### Linear Workflow Rules

1. **Work Only on Epstein Island Project Issues**: Unless explicitly directed otherwise, all work should be on issues within the Epstein Island project
2. **State Management**:
   - **Done**: Work completed successfully (NOT "Canceled" or "Closed")
   - **In Progress**: Work currently being worked on
   - **Canceled/Closed**: Should be used ONLY for work that won't be done
3. **Status Updates**: Update Linear issue status as work progresses

## Key Technologies
- Python
- FastAPI

## Development Guidelines
- Use kuzu-memory enhance for all AI interactions
- Store important decisions with kuzu-memory learn
- Query context with kuzu-memory recall when needed
- Keep memories project-specific and relevant

## Memory Guidelines

- Store project decisions and conventions
- Record technical specifications and API details
- Capture user preferences and patterns
- Document error solutions and workarounds

## Deployment

**⚠️ CRITICAL**: This project uses a persistent ngrok tunnel (`the-island.ngrok.app`) that is **port-specific**.

### Key Deployment Information

- **Ngrok URL**: `https://the-island.ngrok.app` forwards to `localhost:8081`
- **Port Configuration**: Backend port (8081) must match ngrok configuration
- **Port Changes**: Require updates to multiple files: `ecosystem.config.js`, `scripts/ngrok_persistent.sh`, `frontend/vite.config.ts`

### Quick Reference

```bash
# Verify port consistency
grep "8081" ecosystem.config.js scripts/ngrok_persistent.sh frontend/vite.config.ts

# Test deployment
curl http://localhost:8081/health           # Local backend
curl https://the-island.ngrok.app/health    # Ngrok tunnel
```

**📖 Complete Guide**: See [docs/DEPLOY.md](docs/DEPLOY.md) for:
- Why the-island.ngrok.app breaks when ports change
- Port change procedure
- Deployment verification steps
- Troubleshooting common issues

**📖 Additional Resources**:
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - Full deployment guide for all environments
- [docs/deployment/NGROK_CONFIGURATION_SUMMARY.md](docs/deployment/NGROK_CONFIGURATION_SUMMARY.md) - Complete ngrok setup

## Project Organization Rules

**Critical**: This project follows strict file organization rules to maintain a clean structure.

### File Structure Requirements

See [docs/reference/PROJECT_ORGANIZATION.md](docs/reference/PROJECT_ORGANIZATION.md) for comprehensive organization standards.

#### Documentation Files
- **Location**: ALL `.md` files must be in `docs/` directory (except core docs listed below)
- **Core docs in root** (only these):
  - `README.md` - Main project readme
  - `CLAUDE.md` - This file (AI assistant instructions)
  - `CHANGELOG.md` - Version history
  - `CONTRIBUTING.md` - Contribution guidelines
  - `SECURITY.md` - Security policy

- **Subdirectories**:
  - `docs/implementation-summaries/` - Feature implementation summaries
  - `docs/qa-reports/` - QA and testing reports
  - `docs/linear-tickets/` - Linear ticket updates and resolutions
  - `docs/archive/` - Historical documentation
  - `docs/reference/` - Reference documentation

#### Test Files
- **Location**: ALL test files must be in `tests/` directory
- **Subdirectories**:
  - `tests/qa/` - QA-specific tests
  - `tests/verification/` - Verification scripts
  - `tests/api/` - API tests
  - `tests/browser/` - Browser/HTML tests
  - `tests/unit/` - Unit tests
  - `tests/integration/` - Integration tests

#### Scripts
- **Location**: ALL scripts must be in `scripts/` directory
- **Subdirectories**:
  - `scripts/analysis/` - Data analysis scripts
  - `scripts/ingestion/` - Data ingestion scripts
  - `scripts/rag/` - RAG-related scripts
  - `scripts/verification/` - Test/verification scripts
  - `scripts/operations/` - Operational scripts (start, restart, etc.)
  - `scripts/cli/` - CLI utilities

#### Root Directory
- Keep minimal - **NO** new `.md`, `.sh`, `.py`, `.html`, `.txt`, or `.log` files in root
- Only configuration files and core documentation allowed:
  - Configuration: `.gitignore`, `pyproject.toml`, `Makefile`, `.env.example`, etc.
  - Core docs: `README.md`, `CLAUDE.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`

### Going Forward

When creating new files:
1. **Documentation**: Create in appropriate `docs/` subdirectory
2. **Tests**: Create in appropriate `tests/` subdirectory
3. **Scripts**: Create in appropriate `scripts/` subdirectory
4. **Never** create files directly in project root (unless configuration files)

### Migration

A complete file reorganization was performed on 2025-11-24. All files have been moved to their proper locations per these rules.

---

*Generated by KuzuMemory Claude Hooks Installer*
