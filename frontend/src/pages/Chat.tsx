import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, FileText, MessageSquare, Plus, Trash2, Menu, X } from 'lucide-react';
import { api, type SearchResult } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  results?: SearchResult[];
  timestamp: Date;
}

interface ChatSession {
  id: string;
  title: string;
  timestamp: Date;
  messages: Message[];
}

const STORAGE_KEY = 'chat-sessions';
const MAX_SESSIONS = 50;

export function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Load sessions from localStorage on mount
  useEffect(() => {
    const loadSessions = () => {
      try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
          const parsed = JSON.parse(stored);
          // Convert timestamp strings back to Date objects
          const sessionsWithDates = parsed.map((session: ChatSession) => ({
            ...session,
            timestamp: new Date(session.timestamp),
            messages: session.messages.map((msg: Message) => ({
              ...msg,
              timestamp: new Date(msg.timestamp),
            })),
          }));
          setSessions(sessionsWithDates);
        }
      } catch (error) {
        console.error('Failed to load sessions:', error);
      }
    };
    loadSessions();
  }, []);

  // Auto-save current session when messages change
  useEffect(() => {
    if (messages.length > 0 && currentSessionId) {
      saveSession();
    }
  }, [messages]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const saveSession = () => {
    if (messages.length === 0) return;

    const sessionIndex = sessions.findIndex((s) => s.id === currentSessionId);
    const title = messages.find((m) => m.type === 'user')?.content.slice(0, 40) || 'New Chat';

    const updatedSession: ChatSession = {
      id: currentSessionId!,
      title: title.length === 40 ? title + '...' : title,
      timestamp: new Date(),
      messages,
    };

    let updatedSessions: ChatSession[];
    if (sessionIndex >= 0) {
      // Update existing session
      updatedSessions = [...sessions];
      updatedSessions[sessionIndex] = updatedSession;
    } else {
      // Add new session
      updatedSessions = [updatedSession, ...sessions].slice(0, MAX_SESSIONS);
    }

    setSessions(updatedSessions);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedSessions));
  };

  const loadSession = (sessionId: string) => {
    const session = sessions.find((s) => s.id === sessionId);
    if (session) {
      setMessages(session.messages);
      setCurrentSessionId(sessionId);
    }
  };

  const deleteSession = (sessionId: string) => {
    const updatedSessions = sessions.filter((s) => s.id !== sessionId);
    setSessions(updatedSessions);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedSessions));

    // If deleting current session, clear messages
    if (currentSessionId === sessionId) {
      setMessages([]);
      setCurrentSessionId(null);
    }
  };

  const createNewSession = () => {
    const newSessionId = Date.now().toString();
    setMessages([]);
    setCurrentSessionId(newSessionId);
    setInput('');
  };

  const getRelativeTime = (date: Date): string => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    return date.toLocaleDateString();
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    // Create new session if none exists
    if (!currentSessionId) {
      const newSessionId = Date.now().toString();
      setCurrentSessionId(newSessionId);
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const queryText = input;
    setInput('');
    setLoading(true);

    try {
      // Build conversation history for context
      const conversationHistory = messages.map((msg) => ({
        role: (msg.type === 'user' ? 'user' : 'assistant') as 'user' | 'assistant',
        content: msg.content,
      }));

      // Use chat endpoint instead of search
      const response = await api.sendChatMessage(queryText, conversationHistory);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.response,
        results: [], // Chat response doesn't include search results by default
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat failed:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: 'Sorry, I encountered an error processing your message. Please try again.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const getSimilarityColor = (similarity: number): string => {
    if (similarity >= 0.7) return 'bg-green-100 text-green-800 border-green-300';
    if (similarity >= 0.5) return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    return 'bg-blue-100 text-blue-800 border-blue-300';
  };

  const formatTimestamp = (date: Date): string => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="flex h-[calc(100vh-4rem)]" data-testid="chat-page">
      {/* Mobile Menu Button */}
      <Button
        variant="outline"
        size="icon"
        className="md:hidden fixed top-20 left-4 z-50"
        onClick={() => setSidebarOpen(!sidebarOpen)}
        data-testid="sidebar-toggle"
        aria-label={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
      >
        {sidebarOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
      </Button>

      {/* Left Sidebar */}
      <aside
        className={`${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } md:translate-x-0 fixed md:relative w-[300px] h-[calc(100vh-4rem)] bg-muted/50 border-r transition-transform duration-200 ease-in-out z-40`}
        data-testid="chat-sidebar"
        aria-label="Search history"
      >
        {/* Sidebar Header */}
        <div className="p-4 border-b" data-testid="sidebar-header">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold text-sm" data-testid="sidebar-title">Chat History</h2>
            <Button
              size="sm"
              onClick={createNewSession}
              data-testid="new-chat-button"
              aria-label="Start new chat"
              className="h-8"
            >
              <Plus className="h-4 w-4 mr-1" />
              New
            </Button>
          </div>
        </div>

        {/* Sessions List */}
        <div className="overflow-y-auto h-[calc(100%-73px)]" data-testid="sessions-list">
          {sessions.length === 0 ? (
            <div className="p-4 text-center text-sm text-muted-foreground" data-testid="empty-sessions">
              No chat history yet
            </div>
          ) : (
            <div className="p-2 space-y-1">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  className={`group relative rounded-md transition-colors ${
                    currentSessionId === session.id
                      ? 'bg-accent text-accent-foreground'
                      : 'hover:bg-accent/50'
                  }`}
                  data-testid="session-item"
                  data-session-id={session.id}
                >
                  <button
                    onClick={() => loadSession(session.id)}
                    className="w-full text-left p-3 pr-10"
                    data-testid="session-button"
                    aria-label={`Load session: ${session.title}`}
                  >
                    <div className="flex items-start gap-2">
                      <MessageSquare className="h-4 w-4 flex-shrink-0 mt-0.5" aria-hidden="true" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate" data-testid="session-title">
                          {session.title}
                        </p>
                        <p className="text-xs text-muted-foreground" data-testid="session-time">
                          {getRelativeTime(session.timestamp)}
                        </p>
                      </div>
                    </div>
                  </button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute right-1 top-1/2 -translate-y-1/2 h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteSession(session.id);
                    }}
                    data-testid="delete-session-button"
                    aria-label={`Delete session: ${session.title}`}
                  >
                    <Trash2 className="h-4 w-4" aria-hidden="true" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0" data-testid="chat-main">
        {/* Header */}
        <header className="mb-4 px-4 md:px-0" data-testid="chat-header">
          <h1 className="text-3xl font-bold mb-2" data-testid="page-title">AI Assistant</h1>
          <p className="text-muted-foreground" data-testid="page-subtitle">
            Chat with an AI assistant powered by RAG and Knowledge Graph
          </p>
        </header>

        {/* Messages Container */}
        <section
          className="flex-1 overflow-y-auto space-y-4 mb-4 px-4 md:px-0"
          data-testid="messages-container"
          aria-label="Search results and conversation"
        >
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full" data-testid="empty-state">
              <div className="text-center max-w-md">
                <MessageSquare className="h-16 w-16 text-muted-foreground mx-auto mb-4" data-testid="empty-state-icon" />
                <h2 className="text-xl font-semibold mb-2" data-testid="empty-state-title">Start a Conversation</h2>
                <p className="text-muted-foreground mb-4" data-testid="empty-state-description">
                  Ask me anything about the Epstein archive. I can help you explore entities,
                  documents, flight records, and network connections.
                </p>
                <div className="text-sm text-muted-foreground space-y-1" data-testid="example-queries">
                  <p className="font-medium">Try asking:</p>
                  <p data-testid="example-query-1">• "What can you help me with?"</p>
                  <p data-testid="example-query-2">• "Tell me about Ghislaine Maxwell"</p>
                  <p data-testid="example-query-3">• "Who flew on the jets?"</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-4" data-testid="messages-list">
              {messages.map((message) => (
                <article
                  key={message.id}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                  data-testid={`message-${message.type}`}
                  data-message-id={message.id}
                >
                  <div className={`max-w-[80%] ${message.type === 'user' ? 'ml-auto' : 'mr-auto'}`}>
                    {/* Message Bubble */}
                    <div
                      className={`rounded-lg p-4 ${
                        message.type === 'user'
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted'
                      }`}
                      data-testid="message-bubble"
                    >
                      <p className="text-sm whitespace-pre-wrap" data-testid="message-content">{message.content}</p>
                      <time
                        className={`text-xs mt-2 ${
                          message.type === 'user'
                            ? 'text-primary-foreground/70'
                            : 'text-muted-foreground'
                        }`}
                        data-testid="message-timestamp"
                        dateTime={message.timestamp.toISOString()}
                      >
                        {formatTimestamp(message.timestamp)}
                      </time>
                    </div>

                    {/* Search Results */}
                    {message.results && message.results.length > 0 && (
                      <div className="mt-4 space-y-3" data-testid="search-results">
                        {message.results.map((result, idx) => (
                          <Card
                            key={idx}
                            className="hover:shadow-md transition-shadow"
                            data-testid="search-result-card"
                            data-result-index={idx}
                            data-doc-id={result.metadata.doc_id}
                          >
                            <CardHeader className="pb-3">
                              <div className="flex items-start justify-between gap-4">
                                <div className="space-y-1 flex-1">
                                  <div className="flex items-center gap-2 flex-wrap">
                                    <Badge
                                      variant="outline"
                                      className={getSimilarityColor(result.similarity)}
                                      data-testid="similarity-score"
                                      data-similarity={result.similarity}
                                    >
                                      {(result.similarity * 100).toFixed(1)}% match
                                    </Badge>
                                    <span className="text-xs text-muted-foreground" data-testid="doc-id">
                                      {result.metadata.doc_id}
                                    </span>
                                  </div>
                                  <CardTitle className="text-base leading-tight flex items-center gap-2">
                                    <FileText className="h-4 w-4 flex-shrink-0" />
                                    <span data-testid="doc-filename">{result.metadata.filename}</span>
                                  </CardTitle>
                                </div>
                              </div>
                            </CardHeader>
                            <CardContent className="space-y-3">
                              {/* Text Excerpt */}
                              <div className="bg-muted/50 rounded-md p-3" data-testid="text-excerpt">
                                <p className="text-sm leading-relaxed whitespace-pre-wrap">
                                  {result.text_excerpt}
                                </p>
                              </div>

                              {/* Metadata */}
                              <dl className="grid grid-cols-2 gap-2 text-xs" data-testid="metadata">
                                <div>
                                  <dt className="font-medium text-muted-foreground inline">Source:</dt>{' '}
                                  <dd className="inline" data-testid="doc-source">{result.metadata.source}</dd>
                                </div>
                                {result.metadata.date_extracted && (
                                  <div>
                                    <dt className="font-medium text-muted-foreground inline">Date:</dt>{' '}
                                    <dd className="inline" data-testid="doc-date">{result.metadata.date_extracted}</dd>
                                  </div>
                                )}
                                <div>
                                  <dt className="font-medium text-muted-foreground inline">Size:</dt>{' '}
                                  <dd className="inline" data-testid="doc-size">{(result.metadata.file_size / 1024).toFixed(1)} KB</dd>
                                </div>
                              </dl>

                              {/* Entity Mentions */}
                              {result.metadata.entity_mentions && (
                                <div className="space-y-1.5" data-testid="entity-mentions">
                                  <div className="text-xs font-medium text-muted-foreground">
                                    Entities Mentioned:
                                  </div>
                                  <div className="flex flex-wrap gap-1.5" role="list">
                                    {result.metadata.entity_mentions.split(',').map((entity, i) => (
                                      <Badge
                                        key={i}
                                        variant="secondary"
                                        className="text-xs"
                                        data-testid="entity-badge"
                                        data-entity={entity.trim()}
                                        role="listitem"
                                      >
                                        {entity.trim()}
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    )}
                  </div>
                </article>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}

          {/* Loading Indicator */}
          {loading && (
            <div
              className="flex items-center justify-start"
              role="status"
              aria-live="polite"
              data-testid="loading-indicator"
            >
              <div className="bg-muted rounded-lg p-4 flex items-center gap-3">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" aria-hidden="true" />
                <span className="text-sm text-muted-foreground">Thinking...</span>
              </div>
            </div>
          )}
        </section>

        {/* Input Form */}
        <form
          onSubmit={handleSearch}
          className="flex gap-2 px-4 md:px-0"
          data-testid="search-form"
          role="search"
          aria-label="Chat input"
        >
          <Input
            type="text"
            placeholder="Ask me anything about the Epstein archive..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            className="flex-1"
            data-testid="search-input"
            aria-label="Chat message"
            aria-describedby="search-description"
          />
          <span id="search-description" className="sr-only">
            Enter a message to chat with the AI assistant
          </span>
          <Button
            type="submit"
            disabled={loading || !input.trim()}
            data-testid="search-submit"
            aria-label={loading ? "Sending..." : "Send message"}
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            ) : (
              <Send className="h-4 w-4" aria-hidden="true" />
            )}
            <span className="sr-only">{loading ? "Sending..." : "Send"}</span>
          </Button>
        </form>
      </div>
    </div>
  );
}
