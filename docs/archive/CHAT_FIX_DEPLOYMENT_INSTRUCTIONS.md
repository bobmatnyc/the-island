# Chat Interface Fix - Deployment Instructions

**Quick Summary**: Historical documentation archived for reference purposes.

**Category**: Archive
**Status**: Historical
**Last Updated**: 2025-11-24

**Key Points**:
- `curl http://localhost:8081/api/chat/welcome` returns frontend HTML
- Other endpoints (`/api/entities`, `/api/flights`) work correctly

---

## Summary

The chat interface has been fixed to use proper conversational AI endpoints instead of search endpoints. All code changes are complete, but **the backend server must be restarted** to register the chat routes.

## Problem Identification

**Symptom**: Chat endpoint returns HTML instead of JSON
- `curl http://localhost:8081/api/chat/welcome` returns frontend HTML
- Other endpoints (`/api/entities`, `/api/flights`) work correctly

**Root Cause**: The currently running backend server was started before `chat_enhanced.py` route handler existed or was properly configured. The chat routes are not registered in the running server instance.

**Verification**: Import test confirms routes load correctly when server starts fresh:
```bash
$ python3 -c "import sys; sys.path.insert(0, 'server'); from routes.chat_enhanced import router"
INFO:app:Enhanced Chat routes registered at /api/chat
✅ Import successful
```

## Deployment Steps

### 1. Stop the Current Backend Server

```bash
# Find the backend process
ps aux | grep "python.*app.py" | grep -v grep

# Kill the process (replace PID with actual process ID)
kill <PID>

# Or use pkill
pkill -f "python.*app.py"
```

### 2. Restart Backend Server

```bash
cd /Users/masa/Projects/epstein

# Start backend on port 8081
python3 server/app.py 8081
```

**Expected Startup Logs** (should include):
```
INFO:app:Flights routes registered at /api/flights
INFO:app:Enhanced Chat routes registered at /api/chat  ← MUST SEE THIS
INFO:app:News routes registered at /api/news
INFO:app:Stats routes registered at /api/v2/stats
```

### 3. Verify Chat Endpoint Works

```bash
# Test welcome endpoint
curl http://localhost:8081/api/chat/welcome

# Expected: JSON response with welcome message
# Bad: HTML response (means routes not registered)
```

**Expected Response**:
```json
{
  "message": "👋 Welcome to the Epstein Archive!\n\nI'm your AI assistant...",
  "suggestions": [
    "What can I do here?",
    "Tell me about Jeffrey Epstein",
    "Show me flight records",
    "Find court documents"
  ],
  "capabilities": { ... }
}
```

### 4. Test Chat Conversation

```bash
# Send test message
curl -X POST http://localhost:8081/api/chat/enhanced \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "conversation_history": []}'
```

**Expected Response**:
```json
{
  "response": "Hello! I'm your AI assistant for the Epstein Archive...",
  "suggestions": [ ... ],
  "navigation": { ... },
  "context": { ... },
  "model": "openai/gpt-4o"
}
```

### 5. Verify Frontend Integration

```bash
# If frontend is not running, start it:
cd frontend
npm run dev
```

**Manual Test**:
1. Navigate to: `http://localhost:5173/chat`
2. Type: "Hello"
3. **Expected**: Conversational AI response
4. **Bad**: "Sorry, I encountered an error while searching"

## Environment Configuration

### Required for Chat to Work

**Backend** (`.env.local` in project root):
```bash
# OpenRouter API Key (required for AI responses)
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=openai/gpt-4o  # Optional, defaults to gpt-4o
```

**Without API Key**: Chat endpoint falls back to contextual responses (no LLM).

### Frontend Configuration

**Vite** (`.env` in `/frontend/`):
```bash
VITE_API_BASE_URL=http://localhost:8081
```

## Troubleshooting

### Problem: Chat endpoint returns HTML

**Symptom**:
```bash
$ curl http://localhost:8081/api/chat/welcome
<!doctype html>
<html lang="en">
...
```

**Solution**: Backend routes not registered. Restart backend server.

### Problem: "ModuleNotFoundError: No module named 'app'"

**Symptom**:
```
File "/server/routes/chat_enhanced.py", line 44, in get_auth_dependency
    from app import get_current_user
ModuleNotFoundError: No module named 'app'
```

**Solution**: Backend must be run from project root with correct Python path:
```bash
# CORRECT
python3 server/app.py 8081

# WRONG
cd server && python3 app.py 8081  # Changes working directory
```

### Problem: "Sorry, I encountered an error while searching"

**Symptom**: Frontend still shows search error for "Hello"

**Possible Causes**:
1. **Backend not restarted** → Chat routes not registered
2. **API base URL wrong** → Frontend calling wrong server
3. **OpenRouter API error** → Should fall back gracefully, not show search error

**Solutions**:
```bash
# 1. Check backend routes are registered
curl http://localhost:8081/api/chat/welcome

# 2. Check frontend API URL
grep VITE_API_BASE_URL frontend/.env
# Should be: http://localhost:8081

# 3. Check browser console for actual error
# Open DevTools → Console → Network tab
```

### Problem: Chat works but returns "fallback" model

**Symptom**:
```json
{
  "response": "The Epstein Archive contains...",
  "model": "fallback"
}
```

**Cause**: OpenRouter API key not set or invalid

**Solution**:
```bash
# Check .env.local has OPENROUTER_API_KEY
grep OPENROUTER_API_KEY .env.local

# If missing, add it:
echo "OPENROUTER_API_KEY=your_key_here" >> .env.local

# Restart backend to load new env vars
pkill -f "python.*app.py"
python3 server/app.py 8081
```

## File Changes Made

### Modified Files

1. **`/frontend/src/lib/api.ts`** (+45 lines)
   - Added chat TypeScript interfaces
   - Added `sendChatMessage()` method

2. **`/frontend/src/pages/Chat.tsx`** (~0 net lines)
   - Changed `handleSearch()` to use chat endpoint
   - Updated UI text (search → chat)

### Unchanged Files (Already Correct)

- **`/server/routes/chat_enhanced.py`** - Backend chat logic (already working)
- **`/server/app.py`** - Router registration (already correct)

## Success Criteria Checklist

After deployment, verify:

- [ ] Backend starts without errors
- [ ] Startup logs show: `Enhanced Chat routes registered at /api/chat`
- [ ] `curl http://localhost:8081/api/chat/welcome` returns JSON (not HTML)
- [ ] POST to `/api/chat/enhanced` returns conversational response
- [ ] Frontend chat page loads without errors
- [ ] User sends "Hello" → Gets conversational response (not search error)
- [ ] Conversation history maintained across messages
- [ ] Error messages are chat-appropriate (not search-related)

## Quick Verification Script

```bash
#!/bin/bash
# Run from project root

echo "1. Checking backend routes..."
curl -s http://localhost:8081/api/chat/welcome | grep -q "Welcome" && \
  echo "✅ Chat routes registered" || \
  echo "❌ Chat routes NOT registered - restart backend"

echo ""
echo "2. Testing chat endpoint..."
curl -s -X POST http://localhost:8081/api/chat/enhanced \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "conversation_history": []}' | \
  python3 -c "import sys, json; d=json.load(sys.stdin); print('✅ Chat works:', d.get('response')[:50]+'...')" || \
  echo "❌ Chat endpoint failed"

echo ""
echo "3. Checking frontend config..."
grep -q "VITE_API_BASE_URL=http://localhost:8081" frontend/.env && \
  echo "✅ Frontend API URL correct" || \
  echo "⚠️  Check frontend/.env VITE_API_BASE_URL"
```

## Next Steps After Deployment

Once the backend is restarted and chat endpoint works:

1. **Test Frontend**
   - Navigate to `/chat` page
   - Try various queries (greeting, entity questions, capability questions)
   - Verify error messages make sense

2. **Monitor Logs**
   - Watch backend console for errors
   - Check browser DevTools console
   - Verify API calls go to `/api/chat/enhanced` (not `/api/rag/search`)

3. **Performance Check**
   - First message should respond in 2-5 seconds (LLM call)
   - Subsequent messages should be faster (conversation context cached)
   - Fallback responses should be instant (<100ms)

## Rollback Plan

If chat endpoint causes issues:

```bash
# Disable chat routes by commenting out in server/app.py
# Lines 3040-3042:
# if chat_enhanced_available:
#     app.include_router(chat_enhanced_router)
#     logger.info("Enhanced Chat routes registered at /api/chat")

# Restart backend
python3 server/app.py 8081
```

Frontend will show error message, but won't crash. Users can still use other features.

---

**Implementation Date**: 2025-11-20
**Engineer**: Claude Code (Sonnet 4.5)
**Status**: Code changes complete, awaiting backend restart
