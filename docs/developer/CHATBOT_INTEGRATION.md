# Chatbot Integration Example

**Quick Summary**: **Purpose**: Show how to integrate the knowledge index into a chatbot interface...

**Category**: Developer
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- Quick Start
- 1. Load Knowledge Index Once
- 2. Answer Questions from Knowledge

---

**Purpose**: Show how to integrate the knowledge index into a chatbot interface

## Quick Start

### 1. Load Knowledge Index Once

```javascript
// chatbot.js
class EpsteinChatbot {
  constructor() {
    this.knowledge = null;
    this.loadKnowledge();
  }

  async loadKnowledge() {
    try {
      const response = await fetch('/api/chatbot/knowledge', {
        headers: {
          'Authorization': 'Basic ' + btoa('username:password')
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to load knowledge: ${response.status}`);
      }

      this.knowledge = await response.json();
      console.log('✅ Knowledge index loaded:', {
        entities: this.knowledge.quick_stats.unique_entities,
        documents: this.knowledge.quick_stats.unique_documents,
        scripts: this.knowledge.files.scripts.length
      });

    } catch (error) {
      console.error('❌ Failed to load chatbot knowledge:', error);
      // Fallback: continue without knowledge index
      this.knowledge = null;
    }
  }

  // ... rest of chatbot implementation
}
```

### 2. Answer Questions from Knowledge

```javascript
// chatbot.js (continued)
class EpsteinChatbot {
  // ... constructor, loadKnowledge ...

  async handleUserMessage(message) {
    const lowerMessage = message.toLowerCase();

    // Quick pattern matching for common questions
    if (lowerMessage.includes('how many documents')) {
      return this.answerDocumentCount();
    }

    if (lowerMessage.includes('how many entities')) {
      return this.answerEntityCount();
    }

    if (lowerMessage.includes('where') && lowerMessage.includes('flight log')) {
      return this.answerFlightLogLocation();
    }

    if (lowerMessage.includes('search') && lowerMessage.includes('clinton')) {
      return this.answerSearchCommand('Clinton');
    }

    // Fallback to AI-powered response
    return this.askAI(message);
  }

  answerDocumentCount() {
    if (!this.knowledge) {
      return "I don't have access to document statistics. Please try refreshing.";
    }

    const stats = this.knowledge.quick_stats;
    return `The archive contains **${stats.unique_documents.toLocaleString()}** unique documents ` +
           `(${stats.total_pdfs.toLocaleString()} total PDFs, ${stats.deduplication_rate} duplicates removed).`;
  }

  answerEntityCount() {
    if (!this.knowledge) {
      return "I don't have access to entity statistics. Please try refreshing.";
    }

    const stats = this.knowledge.quick_stats;
    return `The archive has indexed **${stats.unique_entities.toLocaleString()}** unique entities, ` +
           `with **${stats.network_nodes}** entities in the relationship network ` +
           `(${stats.network_edges.toLocaleString()} documented connections).`;
  }

  answerFlightLogLocation() {
    if (!this.knowledge) {
      return "I don't have access to file locations. Please try refreshing.";
    }

    const location = this.knowledge.data_locations.flight_logs;
    return `Flight logs are located at: \`${location}\`\n\n` +
           `You can also search flight logs using the entity search tool.`;
  }

  answerSearchCommand(entityName) {
    if (!this.knowledge) {
      return "I don't have access to command information. Please try refreshing.";
    }

    const command = this.knowledge.common_commands.search_by_entity.replace('"Clinton"', `"${entityName}"`);
    return `To search for documents mentioning ${entityName}, run:\n\n` +
           `\`\`\`bash\n${command}\n\`\`\``;
  }

  async askAI(message) {
    // Include knowledge context in AI prompt
    const context = this.buildContextFromKnowledge();

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Basic ' + btoa('username:password')
        },
        body: JSON.stringify({
          message: message,
          context: context  // Include knowledge in AI request
        })
      });

      const data = await response.json();
      return data.response;

    } catch (error) {
      console.error('AI request failed:', error);
      return "Sorry, I'm having trouble processing your request.";
    }
  }

  buildContextFromKnowledge() {
    if (!this.knowledge) return null;

    // Provide AI with key statistics for better answers
    return {
      quick_stats: this.knowledge.quick_stats,
      data_locations: this.knowledge.data_locations,
      search_capabilities: this.knowledge.search_capabilities,
      common_commands: this.knowledge.common_commands
    };
  }
}

// Initialize chatbot
const chatbot = new EpsteinChatbot();
```

## Example Conversations

### Conversation 1: Document Statistics

**User**: "How many documents are in the archive?"

**Chatbot** (from knowledge):
```
The archive contains 38,177 unique documents
(67,975 total PDFs, 43.8% duplicates removed).
```

### Conversation 2: Entity Search

**User**: "How do I search for documents mentioning Ghislaine Maxwell?"

**Chatbot** (from knowledge):
```
To search for documents mentioning Ghislaine Maxwell, run:

```bash
python3 scripts/search/entity_search.py --entity "Ghislaine Maxwell"
```
```

### Conversation 3: Network Information

**User**: "Tell me about the entity network"

**Chatbot** (from knowledge):
```
The entity relationship network contains:
- 387 entities (nodes)
- 2,221 documented connections (edges)
- Connections are based on flight co-occurrences

Top connected entities include Ghislaine Maxwell and Jeffrey Epstein.

You can visualize the network at /static/index.html or query it
via the /api/network endpoint.
```

### Conversation 4: File Locations

**User**: "Where can I find the flight logs?"

**Chatbot** (from knowledge):
```
Flight logs are located at: `data/md/entities/flight_logs_by_flight.json`

This file contains 1,167 individual flights with passenger lists.
You can also search flight logs using the entity search tool.
```

## Advanced Integration

### Smart Context Selection

```javascript
class EpsteinChatbot {
  // ... previous code ...

  async askAI(message) {
    // Analyze question to select relevant context
    const relevantContext = this.selectRelevantContext(message);

    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Basic ' + btoa('username:password')
      },
      body: JSON.stringify({
        message: message,
        context: relevantContext
      })
    });

    const data = await response.json();
    return data.response;
  }

  selectRelevantContext(message) {
    if (!this.knowledge) return null;

    const lowerMessage = message.toLowerCase();
    const context = {};

    // Include statistics if question is about counts/numbers
    if (lowerMessage.match(/how many|count|total|number of/)) {
      context.statistics = this.knowledge.quick_stats;
    }

    // Include file locations if question is about finding files
    if (lowerMessage.match(/where|location|find|file/)) {
      context.locations = this.knowledge.data_locations;
    }

    // Include script info if question is about how to do something
    if (lowerMessage.match(/how do i|how to|command|script/)) {
      context.scripts = this.knowledge.available_scripts;
      context.commands = this.knowledge.common_commands;
    }

    // Include search capabilities if question is about searching
    if (lowerMessage.match(/search|query|find/)) {
      context.search = this.knowledge.search_capabilities;
    }

    return Object.keys(context).length > 0 ? context : null;
  }
}
```

### Fallback Handling

```javascript
class EpsteinChatbot {
  // ... previous code ...

  async handleUserMessage(message) {
    // Try instant answers first
    const instantAnswer = this.tryInstantAnswer(message);
    if (instantAnswer) {
      return {
        source: 'knowledge_index',
        response: instantAnswer,
        confidence: 'high'
      };
    }

    // Fallback to AI if no instant answer
    const aiResponse = await this.askAI(message);
    return {
      source: 'ai',
      response: aiResponse,
      confidence: 'medium'
    };
  }

  tryInstantAnswer(message) {
    if (!this.knowledge) return null;

    const patterns = [
      {
        pattern: /how many (documents?|pdfs?)/i,
        answer: () => this.answerDocumentCount()
      },
      {
        pattern: /how many entities/i,
        answer: () => this.answerEntityCount()
      },
      {
        pattern: /where.*flight logs?/i,
        answer: () => this.answerFlightLogLocation()
      },
      {
        pattern: /search.*for\s+(.+)/i,
        answer: (match) => this.answerSearchCommand(match[1])
      }
    ];

    for (const { pattern, answer } of patterns) {
      const match = message.match(pattern);
      if (match) {
        return answer(match);
      }
    }

    return null;
  }
}
```

## React Component Example

```jsx
// ChatbotWidget.jsx
import React, { useState, useEffect } from 'react';

function ChatbotWidget() {
  const [knowledge, setKnowledge] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  // Load knowledge index on mount
  useEffect(() => {
    async function loadKnowledge() {
      try {
        const response = await fetch('/api/chatbot/knowledge', {
          headers: {
            'Authorization': 'Basic ' + btoa('username:password')
          }
        });
        const data = await response.json();
        setKnowledge(data);
        console.log('Knowledge loaded:', data.quick_stats);
      } catch (error) {
        console.error('Failed to load knowledge:', error);
      }
    }

    loadKnowledge();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    // Add user message
    const userMessage = { role: 'user', content: input };
    setMessages([...messages, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // Try instant answer from knowledge
      const instantAnswer = getInstantAnswer(input, knowledge);

      if (instantAnswer) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: instantAnswer,
          source: 'knowledge'
        }]);
      } else {
        // Fallback to AI
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Basic ' + btoa('username:password')
          },
          body: JSON.stringify({ message: input })
        });

        const data = await response.json();
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.response,
          source: 'ai'
        }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error.',
        source: 'error'
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chatbot-widget">
      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <div className="content">{msg.content}</div>
            {msg.source && (
              <div className="source">Source: {msg.source}</div>
            )}
          </div>
        ))}
        {loading && <div className="loading">Thinking...</div>}
      </div>

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about the archive..."
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          Send
        </button>
      </form>

      {knowledge && (
        <div className="knowledge-status">
          ✅ Knowledge loaded: {knowledge.quick_stats.unique_documents.toLocaleString()} docs
        </div>
      )}
    </div>
  );
}

function getInstantAnswer(message, knowledge) {
  if (!knowledge) return null;

  const lower = message.toLowerCase();

  if (lower.includes('how many documents')) {
    return `The archive contains ${knowledge.quick_stats.unique_documents.toLocaleString()} unique documents.`;
  }

  if (lower.includes('how many entities')) {
    return `${knowledge.quick_stats.unique_entities.toLocaleString()} unique entities indexed.`;
  }

  // Add more patterns...

  return null;
}

export default ChatbotWidget;
```

## Performance Optimization

### Cache Knowledge in LocalStorage

```javascript
class EpsteinChatbot {
  async loadKnowledge() {
    // Check localStorage first
    const cached = localStorage.getItem('chatbot_knowledge');
    const cacheTime = localStorage.getItem('chatbot_knowledge_time');

    if (cached && cacheTime) {
      const age = Date.now() - parseInt(cacheTime);
      const maxAge = 1000 * 60 * 60; // 1 hour

      if (age < maxAge) {
        console.log('✅ Using cached knowledge (age:', Math.round(age / 1000), 'seconds)');
        this.knowledge = JSON.parse(cached);
        return;
      }
    }

    // Fetch fresh knowledge
    try {
      const response = await fetch('/api/chatbot/knowledge', {
        headers: {
          'Authorization': 'Basic ' + btoa('username:password')
        }
      });

      this.knowledge = await response.json();

      // Cache in localStorage
      localStorage.setItem('chatbot_knowledge', JSON.stringify(this.knowledge));
      localStorage.setItem('chatbot_knowledge_time', Date.now().toString());

      console.log('✅ Fresh knowledge loaded and cached');
    } catch (error) {
      console.error('❌ Failed to load knowledge:', error);
    }
  }
}
```

## Error Handling

```javascript
class EpsteinChatbot {
  async loadKnowledge() {
    try {
      const response = await fetch('/api/chatbot/knowledge', {
        headers: {
          'Authorization': 'Basic ' + btoa('username:password')
        }
      });

      if (response.status === 404) {
        console.warn('Knowledge index not found. Some features may be limited.');
        this.knowledge = null;
        return;
      }

      if (response.status === 401) {
        console.error('Authentication failed. Please log in.');
        throw new Error('Authentication required');
      }

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      this.knowledge = await response.json();

      // Validate knowledge structure
      if (!this.knowledge.quick_stats || !this.knowledge.data_locations) {
        console.warn('Knowledge index has unexpected structure. Using fallback.');
        this.knowledge = null;
        return;
      }

      console.log('✅ Knowledge loaded successfully');

    } catch (error) {
      console.error('Failed to load chatbot knowledge:', error);
      this.knowledge = null;

      // Show user-friendly error
      this.showError('Some chatbot features are unavailable. Please refresh the page.');
    }
  }

  showError(message) {
    // Display error to user (implementation depends on UI framework)
    console.error('[Chatbot]', message);
  }
}
```

## Testing

### Unit Tests

```javascript
// chatbot.test.js
import { describe, it, expect, beforeEach } from 'vitest';
import { EpsteinChatbot } from './chatbot';

describe('EpsteinChatbot', () => {
  let chatbot;
  let mockKnowledge;

  beforeEach(() => {
    mockKnowledge = {
      quick_stats: {
        unique_documents: 38177,
        unique_entities: 1773,
        network_nodes: 387,
        network_edges: 2221
      },
      data_locations: {
        flight_logs: 'data/md/entities/flight_logs_by_flight.json'
      },
      common_commands: {
        search_by_entity: 'python3 scripts/search/entity_search.py --entity "Clinton"'
      }
    };

    chatbot = new EpsteinChatbot();
    chatbot.knowledge = mockKnowledge;
  });

  it('answers document count questions', () => {
    const answer = chatbot.answerDocumentCount();
    expect(answer).toContain('38,177');
    expect(answer).toContain('unique documents');
  });

  it('answers entity count questions', () => {
    const answer = chatbot.answerEntityCount();
    expect(answer).toContain('1,773');
    expect(answer).toContain('unique entities');
  });

  it('provides flight log location', () => {
    const answer = chatbot.answerFlightLogLocation();
    expect(answer).toContain('data/md/entities/flight_logs_by_flight.json');
  });

  it('handles missing knowledge gracefully', () => {
    chatbot.knowledge = null;
    const answer = chatbot.answerDocumentCount();
    expect(answer).toContain("don't have access");
  });
});
```

## Summary

This integration example shows:

1. ✅ **Load knowledge once** on chatbot initialization
2. ✅ **Answer common questions instantly** from knowledge index
3. ✅ **Fallback to AI** for complex questions
4. ✅ **Cache knowledge** in localStorage for performance
5. ✅ **Handle errors gracefully** when knowledge unavailable
6. ✅ **Select relevant context** to provide AI with focused information

**Benefits**:
- Fast instant answers (no AI latency)
- Reduced AI API costs
- Better user experience
- Graceful degradation when knowledge unavailable
