# Global ChatSidebar - Visual Testing Guide

## Quick Start
1. Start the dev server: `npm run dev`
2. Navigate to ANY page (Dashboard, Entities, Timeline, etc.)
3. Look for floating chat button in bottom-right corner
4. Click to open the global AI Assistant sidebar

## Visual Testing Steps

### Step 1: Initial State (Empty History)
**What to Check:**
- [ ] Sidebar visible on left (300px wide)
- [ ] "Search History" header with "New" button
- [ ] Message: "No search history yet"
- [ ] Main content takes remaining space
- [ ] Search input at bottom

**Expected Appearance:**
```
┌────────────────┬──────────────────────────────┐
│ Search History │ Document Search              │
│     [+ New]    │                              │
│                │ [Empty state with icon]      │
│ No search      │ "Start a Search"             │
│ history yet    │                              │
│                │                              │
│                │ [Search input at bottom]     │
└────────────────┴──────────────────────────────┘
```

### Step 2: First Search
**Actions:**
1. Type a query (e.g., "Ghislaine Maxwell")
2. Click search button

**What to Check:**
- [ ] Session appears in sidebar
- [ ] Session title matches your query (truncated to 40 chars)
- [ ] Timestamp shows "Just now"
- [ ] Session is highlighted (active state)
- [ ] MessageSquare icon visible
- [ ] Search results appear in main area

**Expected Appearance:**
```
┌────────────────┬──────────────────────────────┐
│ Search History │ Document Search              │
│     [+ New]    │                              │
│ ┌────────────┐ │                              │
│ │ 💬 Ghislaine│ │ [User query bubble]          │
│ │   Maxwell   │ │ [Search results cards]       │
│ │   Just now  │ │                              │
│ └────────────┘ │                              │
│                │ [Search input at bottom]     │
└────────────────┴──────────────────────────────┘
```

### Step 3: Session Hover State
**Actions:**
1. Hover over the session in sidebar

**What to Check:**
- [ ] Background changes to semi-transparent accent
- [ ] Trash icon (🗑️) appears on right
- [ ] Cursor changes to pointer
- [ ] Smooth transition

**Visual Feedback:**
- Hover: Lighter background
- Active: Darker accent background
- Delete button: Fades in smoothly

### Step 4: Multiple Sessions
**Actions:**
1. Click "New" button
2. Perform another search
3. Repeat 2-3 times

**What to Check:**
- [ ] Each session shows in list
- [ ] Most recent at top
- [ ] Each has unique title and timestamp
- [ ] Active session stays highlighted
- [ ] List is scrollable if many sessions
- [ ] Timestamps update ("2 mins ago", etc.)

**Expected Appearance:**
```
┌────────────────┬──────────────────────────────┐
│ Search History │ Document Search              │
│     [+ New]    │                              │
│ ┌────────────┐ │                              │
│ │ 💬 Prince   │ │ [Current conversation]       │
│ │   Andrew... │ │                              │
│ │   2 mins ago│ │                              │
│ └────────────┘ │                              │
│ ┌────────────┐ │                              │
│ │ 💬 Ghislaine│ │                              │
│ │   Maxwell   │ │                              │
│ │   5 mins ago│ │                              │
│ └────────────┘ │                              │
└────────────────┴──────────────────────────────┘
```

### Step 5: Load Previous Session
**Actions:**
1. Click on an older session

**What to Check:**
- [ ] Previous conversation loads
- [ ] All messages restored
- [ ] Search results preserved
- [ ] Clicked session becomes active (highlighted)
- [ ] Previous active session unhighlights
- [ ] Smooth transition

### Step 6: Delete Session
**Actions:**
1. Hover over a session
2. Click trash icon
3. Confirm it's deleted

**What to Check:**
- [ ] Session removed from list
- [ ] Remaining sessions shift up
- [ ] If deleted current session, messages clear
- [ ] No error in console
- [ ] Change persists on page reload

### Step 7: Page Reload Persistence
**Actions:**
1. Refresh the page (F5 or Cmd+R)

**What to Check:**
- [ ] All sessions still in sidebar
- [ ] Timestamps still accurate
- [ ] Can load any session
- [ ] Messages and results intact

### Step 8: Mobile View (Resize to <768px)
**Actions:**
1. Resize browser to mobile width
2. Or use Chrome DevTools device mode

**What to Check:**
- [ ] Sidebar hidden by default
- [ ] Menu button (☰) visible in top-left
- [ ] Click menu button → sidebar slides in
- [ ] Click X button → sidebar slides out
- [ ] Smooth 200ms animation
- [ ] Sidebar overlays content (not pushing it)
- [ ] Can still use all sidebar features

**Mobile Layout:**
```
Closed:
┌─────────────────────────────┐
│ [☰]                         │
│ Document Search             │
│                             │
│ [Search results]            │
│                             │
│ [Search input]              │
└─────────────────────────────┘

Open:
┌──────────┬──────────────────┐
│ Search   │[X]               │
│ History  │ Document Search  │
│          │                  │
│ [List]   │ [Hidden]         │
│          │                  │
└──────────┴──────────────────┘
```

## Edge Cases to Test

### Long Query Titles
**Test:**
1. Enter a very long query (>40 characters)
2. Check session title

**Expected:**
- Title truncated at 40 chars with "..."
- Full query still searchable in messages

### Rapid Searching
**Test:**
1. Perform multiple searches quickly
2. Check session creation

**Expected:**
- Each search updates current session
- No duplicate sessions created
- Timestamps update correctly

### localStorage Limits
**Test:**
1. Create >50 sessions
2. Check session count

**Expected:**
- Only 50 most recent kept
- Oldest sessions removed automatically
- No errors or crashes

### Empty Query
**Test:**
1. Try submitting empty search
2. Check button state

**Expected:**
- Submit button disabled when empty
- No session created
- No errors

## Accessibility Testing

### Keyboard Navigation
**Test:**
1. Tab through sidebar
2. Use Enter to activate

**Check:**
- [ ] Can tab to "New" button
- [ ] Can tab to each session
- [ ] Enter/Space activates buttons
- [ ] Can tab to delete buttons
- [ ] Focus indicators visible

### Screen Reader
**Test:**
1. Use screen reader (VoiceOver/NVDA)

**Check:**
- [ ] Sidebar announced as "Search history"
- [ ] Sessions read with title and time
- [ ] Buttons have clear labels
- [ ] Icons hidden from screen reader

## Performance Testing

### Session Loading
**Test:**
1. Create 50 sessions
2. Reload page
3. Check load time

**Expected:**
- Page loads in <1 second
- No visible lag
- Smooth rendering

### Scroll Performance
**Test:**
1. Create many sessions
2. Scroll sidebar quickly

**Expected:**
- Smooth 60fps scrolling
- No jank or stutter
- Delete buttons appear smoothly

## Browser Compatibility

**Test in:**
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

**Check:**
- localStorage works
- Styles render correctly
- Animations smooth
- No console errors

## Common Issues & Solutions

### Issue: Sidebar not showing
**Solution:** Check browser width - sidebar auto-hides on mobile

### Issue: Sessions not persisting
**Solution:**
- Check browser allows localStorage
- Check private/incognito mode settings
- Clear localStorage and retry

### Issue: Delete button not appearing
**Solution:**
- Ensure mouse hovering directly over session
- Check CSS for `group` and `group-hover` classes

### Issue: Timestamps wrong
**Solution:**
- Check system time is correct
- Refresh page to recalculate relative times

### Issue: Mobile toggle not working
**Solution:**
- Check screen width <768px
- Look for console errors
- Verify button visibility

## Visual Regression Checklist

After any CSS changes, verify:
- [ ] Sidebar width correct (300px)
- [ ] Border present and styled
- [ ] Active state uses accent color
- [ ] Hover states work
- [ ] Icons properly sized and aligned
- [ ] Text truncation working
- [ ] Timestamps right-aligned
- [ ] Delete button positioned correctly
- [ ] Mobile overlay z-index correct

## Success Criteria

All features working when:
- ✅ Can create unlimited sessions (capped at 50)
- ✅ Can load any previous session
- ✅ Can delete any session
- ✅ Sessions persist after reload
- ✅ Mobile responsive works perfectly
- ✅ No TypeScript errors
- ✅ No console errors or warnings
- ✅ Smooth animations and transitions
- ✅ Accessible to keyboard and screen readers
- ✅ Works across all major browsers

---

**Last Updated**: 2025-11-19
**Test Status**: Ready for QA
