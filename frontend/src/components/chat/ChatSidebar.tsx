import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, FileText, MessageSquare, Plus, Trash2, X, ChevronLeft, ChevronRight, Users, Link2, Sparkles } from 'lucide-react';
import {
  api,
  type SearchResult,
  type EntityConnection,
  type EntityDocumentResult,
  type SimilarDocument
} from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  results?: SearchResult[];
  entityResults?: EntityDocumentResult[];
  connections?: EntityConnection[];
  similarDocs?: SimilarDocument[];
  detectedEntities?: string[];
  suggestions?: string[];
  timestamp: Date;
}

interface ChatSession {
  id: string;
  title: string;
  timestamp: Date;
  messages: Message[];
}

const STORAGE_KEY = 'chat-sessions';
const SIDEBAR_STATE_KEY = 'chat-sidebar-open';
const MAX_SESSIONS = 50;

export function ChatSidebar() {
  const [isOpen, setIsOpen] = useState(() => {
    const stored = localStorage.getItem(SIDEBAR_STATE_KEY);
    return stored ? JSON.parse(stored) : false;
  });
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [entityList, setEntityList] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Load knowledge index on mount
  useEffect(() => {
    const loadKnowledge = async () => {
      try {
        const knowledge = await api.getChatbotKnowledge();

        // Extract entity names from knowledge index
        if (knowledge.entities) {
          const entities = Object.keys(knowledge.entities);
          setEntityList(entities);
        }
      } catch (error) {
        console.error('Failed to load knowledge index:', error);
      }
    };

    loadKnowledge();
  }, []);

  // Load sessions from localStorage on mount
  useEffect(() => {
    const loadSessions = () => {
      try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
          const parsed = JSON.parse(stored);
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

  // Persist sidebar open state
  useEffect(() => {
    localStorage.setItem(SIDEBAR_STATE_KEY, JSON.stringify(isOpen));
  }, [isOpen]);

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
      updatedSessions = [...sessions];
      updatedSessions[sessionIndex] = updatedSession;
    } else {
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
      setHistoryOpen(false);
    }
  };

  const deleteSession = (sessionId: string) => {
    const updatedSessions = sessions.filter((s) => s.id !== sessionId);
    setSessions(updatedSessions);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedSessions));

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
    setHistoryOpen(false);
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

  /**
   * Detect entities mentioned in user query
   */
  const detectEntities = (query: string): string[] => {
    if (!entityList.length) return [];

    const queryLower = query.toLowerCase();
    const detected: string[] = [];

    for (const entity of entityList) {
      const entityLower = entity.toLowerCase();
      if (queryLower.includes(entityLower)) {
        detected.push(entity);
      }
    }

    return detected;
  };

  /**
   * Generate smart follow-up suggestions based on results
   */
  const generateSuggestions = (
    detectedEntities: string[],
    connections?: EntityConnection[]
  ): string[] => {
    const suggestions: string[] = [];

    // Suggest exploring connections
    if (connections && connections.length > 0) {
      const topConnection = connections[0];
      suggestions.push(`Tell me about ${topConnection.entity}`);
      if (connections.length > 1) {
        suggestions.push(`How are ${detectedEntities[0]} and ${connections[1].entity} connected?`);
      }
    }

    // Suggest related queries
    if (detectedEntities.length > 0) {
      suggestions.push(`Show me documents about ${detectedEntities[0]}`);
      if (detectedEntities.length > 1) {
        suggestions.push(`Find connections between ${detectedEntities[0]} and ${detectedEntities[1]}`);
      }
    }

    return suggestions.slice(0, 3);
  };

  /**
   * Enhanced search handler with entity detection and knowledge graph integration
   */
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
      // Step 1: Detect entities in query
      const detectedEntities = detectEntities(queryText);

      let assistantMessage: Message;
      let contentParts: string[] = [];

      if (detectedEntities.length > 0) {
        // Entity-focused search
        const primaryEntity = detectedEntities[0];

        // Fetch entity documents and connections in parallel
        const [entityDocs, connections, semanticResults] = await Promise.all([
          api.getEntityDocuments(primaryEntity, 10).catch(() => null),
          api.getEntityConnections(primaryEntity, 10).catch(() => null),
          api.ragSearch(queryText, 10, primaryEntity).catch(() => null)
        ]);

        // Build response message
        contentParts.push(`I found information about **${detectedEntities.join(', ')}**`);

        if (entityDocs) {
          contentParts.push(`\n\n📄 **${entityDocs.total_documents} documents** mention ${primaryEntity} (${entityDocs.total_mentions} total mentions)`);
        }

        if (connections && connections.connections.length > 0) {
          const topConnections = connections.connections.slice(0, 3).map(c => c.entity).join(', ');
          contentParts.push(`\n\n🔗 **Connected to:** ${topConnections}`);
        }

        if (semanticResults && semanticResults.total_results > 0) {
          contentParts.push(`\n\n🔍 Found ${semanticResults.total_results} semantically relevant documents (search took ${semanticResults.search_time_ms.toFixed(0)}ms)`);
        }

        // Generate suggestions
        const suggestions = generateSuggestions(detectedEntities, connections?.connections);

        assistantMessage = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: contentParts.join(''),
          results: semanticResults?.results || [],
          entityResults: entityDocs?.documents || [],
          connections: connections?.connections || [],
          detectedEntities,
          suggestions,
          timestamp: new Date(),
        };
      } else {
        // General semantic search
        const response = await api.ragSearch(queryText, 10);

        assistantMessage = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: `🔍 Found ${response.total_results} relevant documents for "${response.query}" (search took ${response.search_time_ms.toFixed(0)}ms)`,
          results: response.results,
          timestamp: new Date(),
        };
      }

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Search failed:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: 'Sorry, I encountered an error while searching. Please try again.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle clicking on a suggestion
   */
  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion);
  };

  /**
   * Handle clicking on an entity badge
   */
  const handleEntityClick = (entity: string) => {
    setInput(`Tell me about ${entity}`);
  };

  /**
   * Find similar documents to a result
   */
  const handleFindSimilar = async (docId: string) => {
    setLoading(true);
    try {
      const response = await api.getSimilarDocuments(docId, 5);

      const similarMessage: Message = {
        id: Date.now().toString(),
        type: 'assistant',
        content: `Found ${response.total_found} documents similar to ${response.document_id}`,
        similarDocs: response.similar_documents,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, similarMessage]);
    } catch (error) {
      console.error('Failed to find similar documents:', error);
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

  // Floating button when collapsed
  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed right-4 bottom-4 z-50 w-14 h-14 rounded-full bg-primary text-primary-foreground shadow-lg hover:shadow-xl transition-all hover:scale-110"
        aria-label="Open AI Assistant"
      >
        <MessageSquare className="w-6 h-6 mx-auto" />
      </button>
    );
  }

  // Expanded sidebar
  return (
    <aside
      className="fixed right-0 top-14 h-[calc(100vh-3.5rem)] w-full md:w-[480px] bg-background border-l shadow-xl z-40 transform transition-transform flex flex-col"
      data-testid="chat-sidebar"
    >
      {/* Header */}
      <header className="flex items-center justify-between p-4 border-b bg-background sticky top-0 z-10">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setHistoryOpen(!historyOpen)}
            aria-label={historyOpen ? 'Close history' : 'Open history'}
          >
            {historyOpen ? <ChevronRight className="h-5 w-5" /> : <ChevronLeft className="h-5 w-5" />}
          </Button>
          <div>
            <h2 className="font-semibold text-lg flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              AI Assistant
            </h2>
            <p className="text-xs text-muted-foreground">Enhanced with RAG & Knowledge Graph</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={createNewSession}
            aria-label="Start new chat"
          >
            <Plus className="h-5 w-5" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsOpen(false)}
            aria-label="Close assistant"
          >
            <X className="h-5 w-5" />
          </Button>
        </div>
      </header>

      <div className="flex flex-1 min-h-0">
        {/* History Panel */}
        {historyOpen && (
          <div className="w-[250px] border-r overflow-y-auto bg-muted/50">
            <div className="p-2 space-y-1">
              {sessions.length === 0 ? (
                <div className="p-4 text-center text-sm text-muted-foreground">
                  No chat history yet
                </div>
              ) : (
                sessions.map((session) => (
                  <div
                    key={session.id}
                    className={`group relative rounded-md transition-colors ${
                      currentSessionId === session.id
                        ? 'bg-accent text-accent-foreground'
                        : 'hover:bg-accent/50'
                    }`}
                  >
                    <button
                      onClick={() => loadSession(session.id)}
                      className="w-full text-left p-3 pr-10"
                      aria-label={`Load session: ${session.title}`}
                    >
                      <div className="flex items-start gap-2">
                        <MessageSquare className="h-4 w-4 flex-shrink-0 mt-0.5" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">
                            {session.title}
                          </p>
                          <p className="text-xs text-muted-foreground">
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
                      aria-label={`Delete session: ${session.title}`}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Messages Container */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center max-w-md px-4">
                  <Sparkles className="h-16 w-16 text-primary mx-auto mb-4" />
                  <h3 className="text-lg font-semibold mb-2">Ask Me Anything</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    I can help you search and understand the Epstein archive using:
                  </p>
                  <div className="text-xs text-muted-foreground space-y-2 mb-4">
                    <div className="flex items-center gap-2 justify-center">
                      <Badge variant="outline" className="text-xs">Vector Search</Badge>
                      <Badge variant="outline" className="text-xs">Entity Detection</Badge>
                    </div>
                    <div className="flex items-center gap-2 justify-center">
                      <Badge variant="outline" className="text-xs">Knowledge Graph</Badge>
                      <Badge variant="outline" className="text-xs">RAG</Badge>
                    </div>
                  </div>
                  <div className="text-xs text-muted-foreground space-y-1">
                    <p className="font-medium">Try asking:</p>
                    <p className="cursor-pointer hover:text-primary" onClick={() => setInput("Ghislaine Maxwell's activities")}>
                      "Ghislaine Maxwell's activities"
                    </p>
                    <p className="cursor-pointer hover:text-primary" onClick={() => setInput("Prince Andrew connections")}>
                      "Prince Andrew connections"
                    </p>
                    <p className="cursor-pointer hover:text-primary" onClick={() => setInput("Flight logs to islands")}>
                      "Flight logs to islands"
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className={`max-w-[90%] ${message.type === 'user' ? 'ml-auto' : 'mr-auto'}`}>
                      {/* Message Bubble */}
                      <div
                        className={`rounded-lg p-3 ${
                          message.type === 'user'
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-muted'
                        }`}
                      >
                        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                        <time
                          className={`text-xs mt-1.5 block ${
                            message.type === 'user'
                              ? 'text-primary-foreground/70'
                              : 'text-muted-foreground'
                          }`}
                          dateTime={message.timestamp.toISOString()}
                        >
                          {formatTimestamp(message.timestamp)}
                        </time>
                      </div>

                      {/* Detected Entities */}
                      {message.detectedEntities && message.detectedEntities.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          <span className="text-xs text-muted-foreground flex items-center gap-1">
                            <Users className="h-3 w-3" />
                            Entities:
                          </span>
                          {message.detectedEntities.map((entity, idx) => (
                            <Badge
                              key={idx}
                              variant="secondary"
                              className="text-xs cursor-pointer hover:bg-secondary/80"
                              onClick={() => handleEntityClick(entity)}
                            >
                              {entity}
                            </Badge>
                          ))}
                        </div>
                      )}

                      {/* Entity Connections */}
                      {message.connections && message.connections.length > 0 && (
                        <Card className="mt-3 text-sm">
                          <CardHeader className="pb-2 px-3 pt-3">
                            <CardTitle className="text-sm flex items-center gap-2">
                              <Link2 className="h-3.5 w-3.5" />
                              Knowledge Graph Connections
                            </CardTitle>
                          </CardHeader>
                          <CardContent className="px-3 pb-3">
                            <div className="space-y-1">
                              {message.connections.slice(0, 5).map((conn, idx) => (
                                <div
                                  key={idx}
                                  className="flex items-center justify-between text-xs hover:bg-muted/50 p-1 rounded cursor-pointer"
                                  onClick={() => handleEntityClick(conn.entity)}
                                >
                                  <span className="font-medium">{conn.entity}</span>
                                  <Badge variant="outline" className="text-xs">
                                    {conn.weight} {conn.relationship}
                                  </Badge>
                                </div>
                              ))}
                            </div>
                          </CardContent>
                        </Card>
                      )}

                      {/* Entity Documents */}
                      {message.entityResults && message.entityResults.length > 0 && (
                        <div className="mt-3 space-y-2">
                          <div className="text-xs text-muted-foreground flex items-center gap-1">
                            <FileText className="h-3 w-3" />
                            Entity Documents ({message.entityResults.length})
                          </div>
                          {message.entityResults.slice(0, 3).map((doc, idx) => (
                            <Card key={idx} className="text-sm hover:shadow-md transition-shadow">
                              <CardContent className="p-3">
                                <div className="flex items-center justify-between">
                                  <span className="text-xs font-medium truncate flex-1">{doc.filename}</span>
                                  <Badge variant="secondary" className="text-xs ml-2">
                                    {doc.mentions} mentions
                                  </Badge>
                                </div>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      )}

                      {/* Search Results */}
                      {message.results && message.results.length > 0 && (
                        <div className="mt-3 space-y-2">
                          {message.results.map((result, idx) => (
                            <Card
                              key={idx}
                              className="hover:shadow-md transition-shadow text-sm"
                            >
                              <CardHeader className="pb-2 px-3 pt-3">
                                <div className="space-y-1.5">
                                  <div className="flex items-center gap-2 flex-wrap">
                                    <Badge
                                      variant="outline"
                                      className={`text-xs ${getSimilarityColor(result.similarity)}`}
                                    >
                                      {(result.similarity * 100).toFixed(1)}% match
                                    </Badge>
                                    <span className="text-xs text-muted-foreground">
                                      {result.metadata.doc_id}
                                    </span>
                                  </div>
                                  <CardTitle className="text-sm leading-tight flex items-center gap-2">
                                    <FileText className="h-3.5 w-3.5 flex-shrink-0" />
                                    <span className="truncate">{result.metadata.filename}</span>
                                  </CardTitle>
                                </div>
                              </CardHeader>
                              <CardContent className="space-y-2 px-3 pb-3">
                                {/* Text Excerpt */}
                                <div className="bg-muted/50 rounded-md p-2">
                                  <p className="text-xs leading-relaxed line-clamp-3">
                                    {result.text_excerpt}
                                  </p>
                                </div>

                                {/* Metadata */}
                                <div className="text-xs text-muted-foreground">
                                  <span className="font-medium">Source:</span> {result.metadata.source}
                                  {result.metadata.date_extracted && (
                                    <> • {result.metadata.date_extracted}</>
                                  )}
                                </div>

                                {/* Entity Mentions */}
                                {result.metadata.entity_mentions && (
                                  <div className="flex flex-wrap gap-1">
                                    {result.metadata.entity_mentions.split(',').slice(0, 3).map((entity, i) => (
                                      <Badge
                                        key={i}
                                        variant="secondary"
                                        className="text-xs py-0 h-5 cursor-pointer hover:bg-secondary/80"
                                        onClick={() => handleEntityClick(entity.trim())}
                                      >
                                        {entity.trim()}
                                      </Badge>
                                    ))}
                                  </div>
                                )}

                                {/* Find Similar Button */}
                                <Button
                                  variant="outline"
                                  size="sm"
                                  className="w-full text-xs"
                                  onClick={() => handleFindSimilar(result.id)}
                                >
                                  Find Similar Documents
                                </Button>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      )}

                      {/* Similar Documents */}
                      {message.similarDocs && message.similarDocs.length > 0 && (
                        <div className="mt-3 space-y-2">
                          <div className="text-xs text-muted-foreground">Similar Documents:</div>
                          {message.similarDocs.map((doc, idx) => (
                            <Card key={idx} className="text-sm">
                              <CardContent className="p-3">
                                <div className="flex items-center gap-2 mb-2">
                                  <Badge
                                    variant="outline"
                                    className={`text-xs ${getSimilarityColor(doc.similarity_score)}`}
                                  >
                                    {(doc.similarity_score * 100).toFixed(1)}% similar
                                  </Badge>
                                </div>
                                <p className="text-xs line-clamp-2">{doc.preview}</p>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      )}

                      {/* Smart Suggestions */}
                      {message.suggestions && message.suggestions.length > 0 && (
                        <div className="mt-3">
                          <div className="text-xs text-muted-foreground mb-2 flex items-center gap-1">
                            <Sparkles className="h-3 w-3" />
                            You might also ask:
                          </div>
                          <div className="flex flex-col gap-1">
                            {message.suggestions.map((suggestion, idx) => (
                              <Button
                                key={idx}
                                variant="outline"
                                size="sm"
                                className="text-xs justify-start h-auto py-2"
                                onClick={() => handleSuggestionClick(suggestion)}
                              >
                                {suggestion}
                              </Button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}

            {/* Loading Indicator */}
            {loading && (
              <div className="flex items-center justify-start">
                <div className="bg-muted rounded-lg p-3 flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">Searching knowledge graph...</span>
                </div>
              </div>
            )}
          </div>

          {/* Input Form */}
          <form
            onSubmit={handleSearch}
            className="p-4 border-t bg-background"
          >
            <div className="flex gap-2">
              <Input
                type="text"
                placeholder="Ask me anything about the Epstein archive..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={loading}
                className="flex-1"
                aria-label="Chat message"
              />
              <Button
                type="submit"
                disabled={loading || !input.trim()}
                aria-label={loading ? 'Sending...' : 'Send message'}
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </aside>
  );
}
