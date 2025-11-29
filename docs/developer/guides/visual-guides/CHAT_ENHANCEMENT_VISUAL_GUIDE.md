# Chat Enhancement Visual Testing Guide

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- [ ] Sparkles icon visible in header
- [ ] Subtitle shows "Enhanced with RAG & Knowledge Graph"
- [ ] Four badges visible (Vector Search, Entity Detection, Knowledge Graph, RAG)
- [ ] Three example queries shown
- [ ] Example queries are clickable (cursor changes to pointer)

---

## Visual Verification Checklist

Use this guide to visually verify all new features are working correctly.

---

## 1. Welcome Screen (Empty State)

**How to Test:**
1. Open chat sidebar (click floating button)
2. Verify empty state appears

**Expected Visual:**
```
┌──────────────────────────────────────────┐
│  ✨ AI Assistant                         │
│  Enhanced with RAG & Knowledge Graph     │
├──────────────────────────────────────────┤
│                                          │
│         ✨ (Sparkles Icon)               │
│                                          │
│      Ask Me Anything                     │
│                                          │
│  I can help you search and understand    │
│  the Epstein archive using:              │
│                                          │
│  [Vector Search] [Entity Detection]      │
│  [Knowledge Graph] [RAG]                 │
│                                          │
│  Try asking:                             │
│  • "Ghislaine Maxwell's activities"      │
│  • "Prince Andrew connections"           │
│  • "Flight logs to islands"              │
│                                          │
└──────────────────────────────────────────┘
```

**Visual Checks:**
- [ ] Sparkles icon visible in header
- [ ] Subtitle shows "Enhanced with RAG & Knowledge Graph"
- [ ] Four badges visible (Vector Search, Entity Detection, Knowledge Graph, RAG)
- [ ] Three example queries shown
- [ ] Example queries are clickable (cursor changes to pointer)

---

## 2. Entity Detection (Query: "Prince Andrew")

**How to Test:**
1. Type "Prince Andrew"
2. Press Enter
3. Wait for response

**Expected Visual:**

### User Message
```
┌──────────────────────────────┐
│ Prince Andrew          [You] │
│ 2:30 PM                      │
└──────────────────────────────┘
```

### Assistant Response
```
┌────────────────────────────────────────────┐
│ I found information about **Prince Andrew**│
│                                            │
│ 📄 **156 documents** mention Prince Andrew │
│ (342 total mentions)                       │
│                                            │
│ 🔗 **Connected to:** Jeffrey Epstein,     │
│ Ghislaine Maxwell, Virginia Giuffre       │
│                                            │
│ 🔍 Found 89 semantically relevant         │
│ documents (search took 45ms)               │
│                                            │
│ 2:30 PM                                    │
├────────────────────────────────────────────┤
│ 👥 Entities: [Prince Andrew]              │
├────────────────────────────────────────────┤
│ 🔗 Knowledge Graph Connections             │
│ ┌────────────────────────────────┐         │
│ │ Jeffrey Epstein    [23 flights]│         │
│ │ Ghislaine Maxwell  [18 flights]│         │
│ │ Virginia Giuffre   [12 flights]│         │
│ └────────────────────────────────┘         │
├────────────────────────────────────────────┤
│ 📄 Entity Documents (156)                  │
│ ┌────────────────────────────────┐         │
│ │ giuffre_deposition.pdf         │         │
│ │ [47 mentions]                  │         │
│ └────────────────────────────────┘         │
├────────────────────────────────────────────┤
│ [Search Result Cards...]                   │
├────────────────────────────────────────────┤
│ ✨ You might also ask:                     │
│ [Tell me about Jeffrey Epstein]            │
│ [How are Prince Andrew and Ghislaine       │
│  Maxwell connected?]                       │
│ [Show me documents about Prince Andrew]    │
└────────────────────────────────────────────┘
```

**Visual Checks:**
- [ ] Entity badge appears below message (secondary color, clickable)
- [ ] "Knowledge Graph Connections" card visible
- [ ] Connections show entity name + badge with weight
- [ ] Entity documents section visible
- [ ] Document shows filename + mention count badge
- [ ] Smart suggestions appear at bottom (3 buttons)
- [ ] Suggestions use outline variant, left-aligned text

---

## 3. Search Results with Similarity Scores

**Expected for Each Result Card:**

```
┌────────────────────────────────────────────┐
│ [94.2% match] doc_id_123                   │  ← Green badge (>70%)
│ 📄 flight_logs_2001.pdf                    │
├────────────────────────────────────────────┤
│ ╔════════════════════════════════════════╗ │
│ ║ "Prince Andrew flew on Epstein's       ║ │  ← Muted background
│ ║ private jet on March 19, 2001..."      ║ │
│ ╚════════════════════════════════════════╝ │
├────────────────────────────────────────────┤
│ Source: Flight Logs • 2001-03-19           │
├────────────────────────────────────────────┤
│ [Jeffrey Epstein] [Prince Andrew]          │  ← Entity badges (clickable)
├────────────────────────────────────────────┤
│ [Find Similar Documents]                   │  ← Full-width button
└────────────────────────────────────────────┘
```

**Visual Checks:**

**Similarity Badges:**
- [ ] Green badge: >70% match (bg-green-100, text-green-800)
- [ ] Yellow badge: 50-70% match (bg-yellow-100, text-yellow-800)
- [ ] Blue badge: <50% match (bg-blue-100, text-blue-800)
- [ ] Percentage shown with 1 decimal place

**Text Excerpt:**
- [ ] Muted background (bg-muted/50)
- [ ] Rounded corners
- [ ] Max 3 lines (line-clamp-3)
- [ ] Small text (text-xs)

**Entity Mentions:**
- [ ] Secondary badges
- [ ] Cursor changes to pointer on hover
- [ ] Hover effect (hover:bg-secondary/80)

**Find Similar Button:**
- [ ] Outline variant
- [ ] Small size
- [ ] Full width (w-full)
- [ ] Extra small text (text-xs)

---

## 4. Knowledge Graph Connections Card

**Expected Visual:**

```
┌────────────────────────────────────────┐
│ 🔗 Knowledge Graph Connections         │
├────────────────────────────────────────┤
│ ┌────────────────────────────────────┐ │
│ │ Jeffrey Epstein      [23 flights]  │ │  ← Hover effect
│ │ Ghislaine Maxwell    [18 flights]  │ │
│ │ Virginia Giuffre     [12 flights]  │ │
│ │ Bill Clinton         [8 flights]   │ │
│ │ Donald Trump         [5 flights]   │ │
│ └────────────────────────────────────┘ │
└────────────────────────────────────────┘
```

**Visual Checks:**
- [ ] Link2 icon next to title
- [ ] Each connection is a row
- [ ] Entity name on left (font-medium)
- [ ] Badge on right showing weight + relationship
- [ ] Hover effect: background changes (hover:bg-muted/50)
- [ ] Cursor changes to pointer
- [ ] Max 5 connections shown

---

## 5. Smart Suggestions

**Expected Visual:**

```
┌────────────────────────────────────────┐
│ ✨ You might also ask:                 │
├────────────────────────────────────────┤
│ [Tell me about Jeffrey Epstein]        │
│ [How are Prince Andrew and Ghislaine   │
│  Maxwell connected?]                   │
│ [Show me documents about Prince Andrew]│
└────────────────────────────────────────┘
```

**Visual Checks:**
- [ ] Sparkles icon next to header
- [ ] Max 3 suggestions
- [ ] Outline button variant
- [ ] Small size
- [ ] Left-aligned text (justify-start)
- [ ] Auto height (h-auto)
- [ ] Vertical padding (py-2)
- [ ] Extra small text (text-xs)
- [ ] Buttons stack vertically (flex-col gap-1)

---

## 6. Similar Documents Response

**How to Test:**
1. Run any search
2. Click "Find Similar Documents" on a result
3. Verify new message appears

**Expected Visual:**

```
┌────────────────────────────────────────┐
│ Found 5 documents similar to           │
│ doc_id_123                             │
│ 2:31 PM                                │
├────────────────────────────────────────┤
│ Similar Documents:                     │
├────────────────────────────────────────┤
│ ┌────────────────────────────────────┐ │
│ │ [89.3% similar]                    │ │
│ │ "Another document discussing..."   │ │
│ └────────────────────────────────────┘ │
│ ┌────────────────────────────────────┐ │
│ │ [76.1% similar]                    │ │
│ │ "Related content about..."         │ │
│ └────────────────────────────────────┘ │
└────────────────────────────────────────┘
```

**Visual Checks:**
- [ ] "Similar Documents:" label shown
- [ ] Each similar doc is a card
- [ ] Similarity badge color-coded
- [ ] Excerpt line-clamped to 2 lines
- [ ] Small cards (text-sm)

---

## 7. Entity Documents Section

**Expected Visual:**

```
┌────────────────────────────────────────┐
│ 📄 Entity Documents (156)              │
├────────────────────────────────────────┤
│ ┌────────────────────────────────────┐ │
│ │ giuffre_deposition.pdf             │ │
│ │                    [47 mentions]   │ │
│ └────────────────────────────────────┘ │
│ ┌────────────────────────────────────┐ │
│ │ flight_logs_2001.pdf               │ │
│ │                    [23 mentions]   │ │
│ └────────────────────────────────────┘ │
│ ┌────────────────────────────────────┐ │
│ │ black_book.pdf                     │ │
│ │                    [12 mentions]   │ │
│ └────────────────────────────────────┘ │
└────────────────────────────────────────┘
```

**Visual Checks:**
- [ ] FileText icon next to label
- [ ] Label shows count: "Entity Documents (N)"
- [ ] Max 3 documents shown
- [ ] Filename truncates if too long
- [ ] Mention count in secondary badge
- [ ] Cards have hover effect (hover:shadow-md)

---

## 8. Header Enhancements

**Expected Visual:**

```
┌────────────────────────────────────────┐
│ [<] ✨ AI Assistant            [+] [X] │
│     Enhanced with RAG &                │
│     Knowledge Graph                    │
└────────────────────────────────────────┘
```

**Visual Checks:**
- [ ] Sparkles icon next to "AI Assistant"
- [ ] Subtitle line below title (text-xs, muted)
- [ ] History button on left (ChevronLeft/Right icon)
- [ ] New chat button (Plus icon)
- [ ] Close button (X icon)
- [ ] All buttons same size (size="icon")
- [ ] Ghost variant

---

## 9. Loading State

**Expected Visual:**

```
┌────────────────────────────────────────┐
│ ┌────────────────────────────────────┐ │
│ │ ⟳ Searching knowledge graph...    │ │
│ └────────────────────────────────────┘ │
└────────────────────────────────────────┘
```

**Visual Checks:**
- [ ] Muted background bubble
- [ ] Spinner icon (Loader2) animates
- [ ] Text: "Searching knowledge graph..."
- [ ] Small text size (text-sm)
- [ ] Muted text color

---

## 10. Clickable Elements

**All Clickable Elements Should:**
- [ ] Change cursor to pointer on hover
- [ ] Have hover effect (color/background change)
- [ ] Be keyboard accessible (tab navigation)

**Specific Click Behaviors:**

**Entity Badges:**
- Click → Input auto-fills: "Tell me about {entity}"
- Hover → Background darkens slightly

**Suggestions:**
- Click → Input auto-fills with suggestion text
- Hover → Background changes

**Connections:**
- Click → Input auto-fills: "Tell me about {entity}"
- Hover → Background changes (hover:bg-muted/50)

**Find Similar Button:**
- Click → Fetches similar docs, adds new message
- Disabled state while loading

---

## 11. Mobile Responsive (< 768px width)

**Expected Behavior:**
- [ ] Sidebar takes full screen width (w-full)
- [ ] History panel still works
- [ ] All features functional
- [ ] Touch-friendly tap targets
- [ ] Proper scrolling behavior

**To Test:**
1. Resize browser to mobile width
2. Open chat sidebar
3. Verify all features work
4. Test all clickable elements

---

## 12. Color Coding Reference

**Similarity Scores:**
- 🟢 Green (>70%): High relevance
- 🟡 Yellow (50-70%): Medium relevance
- 🔵 Blue (<50%): Low relevance

**Entity Badges:**
- Secondary variant (gray/muted)
- Clickable with hover effect

**Connection Badges:**
- Outline variant
- Shows weight + relationship type

**Mention Count Badges:**
- Secondary variant
- Shows number of mentions

---

## 13. Accessibility

**Screen Reader Checks:**
- [ ] All buttons have aria-label
- [ ] Time elements have datetime attribute
- [ ] Icons have semantic meaning
- [ ] Proper heading hierarchy

**Keyboard Navigation:**
- [ ] Tab through all interactive elements
- [ ] Enter to submit form
- [ ] Focus visible on all elements

---

## 14. Error States

**Knowledge Index Load Failure:**
- [ ] Error logged to console
- [ ] Chat still works (no entity detection)
- [ ] No error shown to user

**Search Failure:**
- [ ] Error message shown in chat
- [ ] "Sorry, I encountered an error..." message
- [ ] Loading state cleared

**Entity Not Found:**
- [ ] Falls back to semantic search
- [ ] No error shown to user
- [ ] Results still displayed

---

## Testing Checklist Summary

### Essential Tests
- [ ] Welcome screen renders correctly
- [ ] Entity detection works ("Prince Andrew")
- [ ] Similarity scores color-coded correctly
- [ ] Knowledge graph connections appear
- [ ] Smart suggestions appear and work
- [ ] Entity badges clickable
- [ ] Find similar documents works
- [ ] Session history works
- [ ] Mobile responsive

### Visual Quality
- [ ] All icons render
- [ ] Colors match design system
- [ ] Hover effects work
- [ ] Loading states clear
- [ ] Text truncation works
- [ ] Cards have proper spacing

### Interactions
- [ ] All buttons functional
- [ ] All badges clickable
- [ ] Suggestions auto-fill input
- [ ] Entity clicks work
- [ ] Find similar works
- [ ] History panel toggles

### Performance
- [ ] Initial load fast (<1s)
- [ ] Queries respond quickly (<200ms)
- [ ] No lag when typing
- [ ] Smooth scrolling
- [ ] No console errors

---

## Quick Test Script

**5-Minute Smoke Test:**

1. Open chat → Verify welcome screen ✅
2. Query "Prince Andrew" → Verify entity detection ✅
3. Check similarity colors → Green/Yellow/Blue ✅
4. Verify connections card appears ✅
5. Click entity badge → Input auto-fills ✅
6. Click suggestion → Input auto-fills ✅
7. Click "Find Similar" → New results appear ✅
8. Open history → Session saved ✅
9. Resize to mobile → Everything works ✅
10. Check console → No errors ✅

**Pass Criteria:**
All 10 checks must pass for production deployment.

---

**Created:** November 19, 2025
**Purpose:** Visual testing and QA
**Status:** Ready for testing
