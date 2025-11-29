# Home Page API - Quick Start Guide

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- 🚀 What's Ready
- 📡 API Endpoints
- 1. Get About Content
- 2. Get Recent Updates
- ⚡ Quick Test

---

## 🚀 What's Ready

Backend API for the Epstein Archive home page is **100% complete** and ready for frontend integration.

---

## 📡 API Endpoints

### 1. Get About Content
```bash
GET /api/about
```

**Response**:
```json
{
  "content": "# The Epstein Archive\n\n...",
  "updated_at": "2025-11-19T23:44:36.597662",
  "file_size": 11426
}
```

### 2. Get Recent Updates
```bash
GET /api/updates?limit=10
```

**Response**:
```json
{
  "commits": [
    {
      "hash": "d93f75062",
      "author": "Bob Matsuoka",
      "time": "7 hours ago",
      "message": "docs: add migration quick start summary"
    }
  ],
  "total": 10
}
```

---

## ⚡ Quick Test

```bash
# Test endpoints without server
python3 test_endpoints.py

# Start server
source .venv/bin/activate
uvicorn server.app:app --host 0.0.0.0 --port 8081 --reload

# Test with curl
curl http://localhost:8081/api/about | jq '.file_size'
curl http://localhost:8081/api/updates?limit=5 | jq '.total'
```

---

## 🎨 Frontend Integration (React)

### Install Dependencies
```bash
cd frontend
npm install react-markdown remark-gfm
```

### Sample Component
```typescript
import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';

export function HomePage() {
  const [about, setAbout] = useState(null);
  const [updates, setUpdates] = useState([]);

  useEffect(() => {
    fetch('/api/about').then(r => r.json()).then(setAbout);
    fetch('/api/updates?limit=10')
      .then(r => r.json())
      .then(data => setUpdates(data.commits));
  }, []);

  return (
    <div className="container mx-auto p-8">
      <section className="prose max-w-none">
        {about && <ReactMarkdown>{about.content}</ReactMarkdown>}
      </section>

      <aside className="mt-8">
        <h2 className="text-2xl font-bold mb-4">Recent Updates</h2>
        <div className="space-y-4">
          {updates.map(commit => (
            <div key={commit.hash} className="border-l-4 border-blue-500 pl-4">
              <code className="text-sm text-gray-500">{commit.hash}</code>
              <p className="font-medium">{commit.message}</p>
              <span className="text-sm text-gray-600">{commit.time}</span>
            </div>
          ))}
        </div>
      </aside>
    </div>
  );
}
```

---

## 📊 Current Statistics

- **Total Entities**: 1,639
- **Biographical Coverage**: 86% (1,409 entities with Wikipedia data)
- **Documents**: 305+ (House Oversight Committee)
- **Data Quality**: B+ (87/100)

---

## 📁 Files

- **ABOUT.md**: `/Users/masa/Projects/epstein/ABOUT.md`
- **API Code**: `server/app.py` (lines 718-844)
- **Test Script**: `test_endpoints.py`
- **Full Docs**: `HOME_PAGE_API_IMPLEMENTATION.md`

---

## ✅ Success Criteria

- [x] ABOUT.md with comprehensive content
- [x] `/api/about` endpoint working
- [x] `/api/updates` endpoint working
- [x] Error handling implemented
- [x] Tests passing (2/2)
- [x] Documentation complete
- [x] Ready for frontend

---

## 🎯 Next Steps

1. **Frontend**: Create `HomePage.tsx` component
2. **Styling**: Use ShadCN UI cards for updates
3. **Markdown**: Render ABOUT.md with react-markdown
4. **Polish**: Add loading states and animations

---

**Status**: ✅ COMPLETE
**Ready for**: Frontend integration
**Test Results**: 2/2 passing (100%)
