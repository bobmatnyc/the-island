# User Guide

**Quick Summary**: **Documentation for end users of the Epstein Document Archive**...

**Category**: User
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- **Entities**: Search and browse entity database
- **Documents**: Search and view documents
- **Flights**: Explore flight logs
- **Network**: Visualize entity relationships
- **Questions?** → [FAQ](faq.md)

---

**Documentation for end users of the Epstein Document Archive**

---

## Getting Started

New to the system? Start here:

1. **[Getting Started](getting-started.md)** - 5-minute quick start guide
2. **[Searching Documents](searching.md)** - How to search effectively
3. **[FAQ](faq.md)** - Common questions and answers

---

## User Guides

| Guide | Description |
|-------|-------------|
| [getting-started.md](getting-started.md) | First-time user walkthrough and quick start |
| [searching.md](searching.md) | Advanced search techniques and examples |
| [entities.md](entities.md) | Understanding the entity database |
| [flights.md](flights.md) | Flight logs and passenger analysis |
| [network-analysis.md](network-analysis.md) | Relationship network visualization |
| [faq.md](faq.md) | Frequently asked questions |

---

## Quick Commands

```bash
# Search for entity
python3 scripts/search/entity_search.py --entity "NAME"

# View connections
python3 scripts/search/entity_search.py --connections "NAME"

# Multi-entity search
python3 scripts/search/entity_search.py --multiple "NAME1" "NAME2"

# Search by document type
python3 scripts/search/entity_search.py --type "email"
```

---

## Web Interface

Access at: `http://localhost:8081/`

**Main Sections**:
- **Entities**: Search and browse entity database
- **Documents**: Search and view documents
- **Flights**: Explore flight logs
- **Network**: Visualize entity relationships

---

## Support

- **Questions?** → [FAQ](faq.md)
- **Issues?** → [Troubleshooting](../operations/troubleshooting.md)
- **Feedback?** → [GitHub Issues](https://github.com/yourusername/epstein-document-archive/issues)
