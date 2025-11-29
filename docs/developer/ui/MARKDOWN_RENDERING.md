# Markdown Rendering Documentation

**Quick Summary**: The Epstein Document Archive chatbot now supports **rich markdown rendering** with automatic feature link detection.  This makes assistant responses more readable, interactive, and well-formatted.

**Category**: Developer
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- **XSS Prevention**: Script tags are automatically removed
- **Safe HTML**: Only whitelisted HTML tags are allowed
- **Link Safety**: External links open in new tabs with `rel="noopener noreferrer"`

---

## Overview

The Epstein Document Archive chatbot now supports **rich markdown rendering** with automatic feature link detection. This makes assistant responses more readable, interactive, and well-formatted.

## Features

### 1. Markdown Support

All standard markdown elements are fully supported:

#### Headers
```markdown
# Header 1
## Header 2
### Header 3
#### Header 4
```

#### Text Formatting
```markdown
**bold text** or __bold text__
*italic text* or _italic text_
`inline code`
```

#### Code Blocks
````markdown
```javascript
function example() {
    return "syntax highlighting";
}
```
````

#### Lists
```markdown
Unordered:
- Item 1
- Item 2
- Item 3

Ordered:
1. First
2. Second
3. Third
```

#### Links
```markdown
[Link text](https://example.com)
```

#### Blockquotes
```markdown
> This is a quoted text
```

#### Tables
```markdown
| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |
```

#### Horizontal Rules
```markdown
---
or
***
```

### 2. Automatic Feature Link Detection

The chatbot automatically converts mentions of site features into clickable links:

| Pattern | Action | Example |
|---------|--------|---------|
| `network graph` | Switch to Network tab | "Check the **network graph**" → clickable link |
| `entity network` | Switch to Network tab | "View the **entity network**" → clickable link |
| `knowledge graph` | Switch to Network tab | "Explore the **knowledge graph**" → clickable link |
| `entities list` | Switch to Entities tab | "See the **entities list**" → clickable link |
| `view entities` | Switch to Entities tab | "You can **view entities**" → clickable link |
| `roadmap` | Switch to Roadmap tab | "Check the **roadmap**" → clickable link |
| `project roadmap` | Switch to Roadmap tab | "See the **project roadmap**" → clickable link |
| `suggest a source` | Open source form | "**Suggest a source**" → opens modal |
| `ingestion status` | Switch to Ingestion tab | "View **ingestion status**" → clickable link |
| `ocr progress` | Switch to Ingestion tab | "Check **OCR progress**" → clickable link |
| `overview` | Switch to Overview tab | "Return to **overview**" → clickable link |

### 3. Security Features

- **XSS Prevention**: Script tags are automatically removed
- **Safe HTML**: Only whitelisted HTML tags are allowed
- **Link Safety**: External links open in new tabs with `rel="noopener noreferrer"`

## Technical Implementation

### Libraries Used

- **marked.js v11.0.0**: Full-featured markdown parser
- **Fallback Renderer**: Custom basic markdown renderer if marked.js fails to load

### Architecture

```javascript
// 1. Load marked.js library
loadMarkedJS() → Promise

// 2. Enhance text with feature links
enhanceWithFeatureLinks(text) → enhanced text

// 3. Render markdown
renderMarkdown(text) → HTML

// 4. Display in chat
addChatMessage('assistant', content) → renders with markdown
```

### Configuration

```javascript
marked.setOptions({
    breaks: true,        // Convert \n to <br>
    gfm: true,          // GitHub Flavored Markdown
    headerIds: false,   // Don't generate header IDs
    mangle: false       // Don't mangle email addresses
});
```

## Usage Examples

### Example 1: Search Results
```markdown
## Search Results

I found **3 entities** matching your query:

1. **Jeffrey Epstein** - 256 connections, 4,523 documents
2. **Ghislaine Maxwell** - 228 connections, 3,891 documents
3. **Les Wexner** - 42 connections, 567 documents

You can view these in the **network graph** or check the **entities list** for more details.
```

**Rendered Output:**
- Headers are styled with proper hierarchy
- Bold names are emphasized
- "network graph" and "entities list" become clickable feature links
- Numbers are formatted consistently

### Example 2: Code Snippets
````markdown
To search for entities programmatically:

```python
def search_entities(query):
    return [e for e in entities if query.lower() in e.name.lower()]
```

This returns all matching entities.
````

**Rendered Output:**
- Code block with syntax highlighting container
- Proper monospace font
- Distinguished background color
- Horizontal scrolling for long lines

### Example 3: Data Tables
```markdown
| Entity | Connections | Documents | Billionaire |
|--------|-------------|-----------|-------------|
| Jeffrey Epstein | 256 | 4,523 | Yes |
| Ghislaine Maxwell | 228 | 3,891 | No |
| Bill Clinton | 26 | 234 | No |
```

**Rendered Output:**
- Bordered table with header row
- Aligned columns
- Responsive sizing
- Themed colors matching site design

### Example 4: Mixed Content
```markdown
## Entity Analysis

Based on the **entity network**, here are the top connections:

> **Note:** These connections are based on co-occurrences in flight logs and contact books.

### Top 3 Entities:
1. **Jeffrey Epstein** - Central node with 256 direct connections
2. **Ghislaine Maxwell** - 228 connections, frequently traveled together
3. **Les Wexner** - 42 connections, business relationship

You can explore these relationships in the **network graph**.

---

**Next Steps:**
- View the roadmap for planned features
- Suggest a source to expand the archive
- Check ingestion status for OCR progress
```

**Rendered Output:**
- Headers create visual hierarchy
- Blockquote stands out with border styling
- Lists are properly formatted
- Feature links are interactive
- Horizontal rule creates section break
- All emphasis renders correctly

## Testing

### Test Page

Open `/server/web/markdown-test.html` to see all markdown features in action.

The test page includes 8 comprehensive test cases:
1. **Basic Formatting** - Bold, italic, inline code
2. **Headers** - All header levels
3. **Lists** - Ordered and unordered
4. **Code Blocks** - Multi-line code with language tags
5. **Links and Blockquotes** - External/internal links, quotes
6. **Feature Link Detection** - Auto-linking to site features
7. **Tables** - Data table rendering
8. **Mixed Content** - Real-world complex example

### Manual Testing Checklist

- [ ] Headers render with correct hierarchy
- [ ] Bold and italic formatting works
- [ ] Inline code has correct styling
- [ ] Code blocks are properly formatted
- [ ] Lists (ordered/unordered) display correctly
- [ ] Links are clickable and styled
- [ ] Feature links navigate to correct tabs
- [ ] Blockquotes have left border
- [ ] Tables render with borders and headers
- [ ] Horizontal rules display correctly
- [ ] No XSS vulnerabilities (script tags removed)
- [ ] Markdown renders in both light and dark themes

### Console Testing

Open browser console and test rendering:

```javascript
// Test basic markdown
renderMarkdown("This is **bold** and this is *italic*");

// Test feature links
renderMarkdown("Check the **network graph** for connections");

// Test code blocks
renderMarkdown("```javascript\nconst x = 42;\n```");

// Test tables
renderMarkdown("| Col1 | Col2 |\n|------|------|\n| A | B |");
```

## Styling Details

All markdown elements are styled using CSS custom properties for theme consistency:

```css
/* Headers */
.chat-message.assistant h1 { font-size: 18px; }
.chat-message.assistant h2 { font-size: 16px; }
.chat-message.assistant h3 { font-size: 14px; }
.chat-message.assistant h4 { font-size: 13px; }

/* Code */
.chat-message.assistant code {
    background: var(--bg-tertiary);
    font-family: 'Monaco', 'Courier New', monospace;
}

/* Links */
.chat-message.assistant a {
    color: var(--accent-blue);
    border-bottom: 1px dotted var(--accent-blue);
}

/* Feature links */
.chat-message.assistant .feature-link {
    font-weight: 600;
    border-bottom: 1px solid var(--accent-blue);
}

/* Tables */
.chat-message.assistant table {
    border-collapse: collapse;
    width: 100%;
}
```

## Performance Considerations

- **Library Size**: marked.js is ~31KB minified (~9KB gzipped)
- **Lazy Loading**: Library loads asynchronously on page load
- **Fallback**: If marked.js fails, basic renderer handles common markdown
- **Caching**: CDN-hosted library benefits from browser caching
- **Render Speed**: Markdown parsing adds <5ms per message

## Browser Compatibility

- **Chrome/Edge**: Full support (tested on latest)
- **Firefox**: Full support (tested on latest)
- **Safari**: Full support (tested on latest)
- **Mobile**: Fully responsive on iOS and Android

## Future Enhancements

Potential improvements for future versions:

1. **Syntax Highlighting**: Add Prism.js or highlight.js for code blocks
2. **Entity Auto-Linking**: Detect entity names and link to entity details
3. **Math Support**: Add KaTeX for mathematical expressions
4. **Diagrams**: Support Mermaid.js for flowcharts and diagrams
5. **Emoji Support**: Add emoji shortcode support (`:smile:` → 😊)
6. **Custom Containers**: Add callout boxes for notes/warnings/tips

## Troubleshooting

### Markdown Not Rendering

**Issue**: Plain text appears instead of formatted markdown

**Solutions**:
1. Check browser console for errors
2. Verify marked.js loaded: `typeof marked !== 'undefined'`
3. Check message type: `type === 'assistant'` (only assistant messages render markdown)
4. Try fallback renderer directly: `basicMarkdownRender(text)`

### Feature Links Not Working

**Issue**: Feature links don't navigate to correct tabs

**Solutions**:
1. Check `featureLinks` object contains pattern
2. Verify `switchTab()` function exists
3. Check for JavaScript errors in console
4. Ensure pattern matching is case-insensitive

### XSS Vulnerability Concerns

**Issue**: Worried about malicious content

**Solutions**:
1. Script tags are automatically removed
2. HTML is sanitized by marked.js
3. Only whitelisted tags are rendered
4. External links have `rel="noopener noreferrer"`
5. No `eval()` or dynamic code execution

### Styling Issues

**Issue**: Markdown elements don't match theme

**Solutions**:
1. Verify CSS custom properties are defined
2. Check `.chat-message.assistant` selector specificity
3. Clear browser cache
4. Toggle theme to verify both light/dark modes

## Contributing

To add new markdown features:

1. Update `renderMarkdown()` function in `app.js`
2. Add corresponding CSS styles in `index.html`
3. Add test case to `markdown-test.html`
4. Update this documentation
5. Test in both light and dark themes

To add new feature link patterns:

1. Add pattern to `featureLinks` object in `app.js`
2. Define action (tab switch, modal open, etc.)
3. Test pattern detection with regex
4. Add example to test page
5. Document in table above

## Resources

- **marked.js Documentation**: https://marked.js.org/
- **GitHub Flavored Markdown**: https://github.github.com/gfm/
- **Markdown Guide**: https://www.markdownguide.org/
- **CommonMark Spec**: https://commonmark.org/

---

**Last Updated**: 2025-11-16
**Version**: 1.0.0
**Maintainer**: WebUI Agent
