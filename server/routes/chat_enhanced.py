#!/usr/bin/env python3
"""
Enhanced AI Chat Routes
Intelligent chatbot with complete site awareness and navigation assistance
"""

import json
import os
from pathlib import Path

from fastapi import APIRouter, Depends
from openai import OpenAI
from pydantic import BaseModel


# Initialize router
router = APIRouter(prefix="/api/chat", tags=["chat"])

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MD_DIR = DATA_DIR / "md"
METADATA_DIR = DATA_DIR / "metadata"

# OpenRouter client (lazy loaded)
openrouter_client = None
openrouter_model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")


def get_openrouter_client():
    """Initialize OpenRouter client (lazy loading)"""
    global openrouter_client
    if openrouter_client is None:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not set in .env.local")

        openrouter_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
    return openrouter_client


# Import get_current_user at runtime to avoid circular imports
def get_auth_dependency():
    from app import get_current_user

    return get_current_user


# Pydantic models
class ConversationMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_history: list[ConversationMessage] = []


class NavigationAction(BaseModel):
    text: str
    action: str  # "navigate", "filter", "search"
    target: str
    params: dict[str, str] = {}


class ChatResponse(BaseModel):
    response: str
    suggestions: list[str] = []
    navigation: dict[str, list[NavigationAction]] = {}
    context: dict = {}
    model: str = ""


# Data loaders (cached)
_entity_stats = None
_network_data = None
_classifications = None


def load_entity_stats() -> dict:
    """Load entity statistics (cached)"""
    global _entity_stats
    if _entity_stats is None:
        stats_path = METADATA_DIR / "entity_statistics.json"
        if stats_path.exists():
            with open(stats_path) as f:
                data = json.load(f)
                _entity_stats = data.get("statistics", {})
        else:
            _entity_stats = {}
    return _entity_stats


def load_network_data() -> dict:
    """Load network data (cached)"""
    global _network_data
    if _network_data is None:
        network_path = METADATA_DIR / "entity_network.json"
        if network_path.exists():
            with open(network_path) as f:
                _network_data = json.load(f)
        else:
            _network_data = {"nodes": [], "edges": []}
    return _network_data


def load_classifications() -> dict:
    """Load document classifications (cached)"""
    global _classifications
    if _classifications is None:
        class_path = METADATA_DIR / "document_classifications.json"
        if class_path.exists():
            with open(class_path) as f:
                data = json.load(f)
                _classifications = data.get("results", {})
        else:
            _classifications = {}
    return _classifications


def get_total_documents() -> int:
    """Get total document count from unified index"""
    total = len(load_classifications())
    unified_index_path = METADATA_DIR / "all_documents_index.json"
    if unified_index_path.exists():
        try:
            with open(unified_index_path) as f:
                unified_data = json.load(f)
                total = unified_data.get("total_documents", total)
        except Exception:
            pass
    return total


def get_total_flights() -> int:
    """Get total flight count"""
    flight_data_path = MD_DIR / "entities/flight_logs_by_flight.json"
    if flight_data_path.exists():
        try:
            with open(flight_data_path) as f:
                flight_data = json.load(f)
                return len(flight_data.get("flights", []))
        except Exception:
            pass
    return 0


def detect_intent(query: str) -> str:
    """Detect user intent from query"""
    query_lower = query.lower()

    if any(
        word in query_lower
        for word in ["what can", "help", "do here", "how to", "guide", "capabilities", "features"]
    ):
        return "capabilities"
    if any(
        word in query_lower
        for word in ["who is", "tell me about", "information about", "biography", "bio"]
    ):
        return "entity_info"
    if any(
        word in query_lower
        for word in ["flight", "plane", "trip", "travel", "passenger", "flew", "jet"]
    ):
        return "flights"
    if any(
        word in query_lower
        for word in ["document", "file", "deposition", "court", "pdf", "evidence"]
    ):
        return "documents"
    if any(
        word in query_lower
        for word in ["connect", "network", "relationship", "link", "associated", "related"]
    ):
        return "connections"
    if any(word in query_lower for word in ["timeline", "when", "date", "chronology", "history"]):
        return "timeline"
    return "general"


def detect_entities(query: str) -> list[dict]:
    """Detect entities mentioned in query"""
    entity_stats = load_entity_stats()
    query_lower = query.lower()
    detected = []

    for entity_name, entity_data in entity_stats.items():
        if entity_name.lower() in query_lower:
            detected.append(
                {
                    "name": entity_name,
                    "documents": entity_data.get("total_documents", 0),
                    "connections": entity_data.get("connection_count", 0),
                    "flights": entity_data.get("flight_count", 0),
                    "is_billionaire": entity_data.get("is_billionaire", False),
                }
            )

    return detected


def build_site_capabilities() -> dict:
    """Build comprehensive site capabilities context"""
    entity_stats = load_entity_stats()
    network_data = load_network_data()

    return {
        "entities": {
            "total": len(entity_stats),
            "with_bios": sum(1 for e in entity_stats.values() if e.get("biography")),
            "billionaires": sum(1 for e in entity_stats.values() if e.get("is_billionaire")),
            "in_black_book": sum(1 for e in entity_stats.values() if e.get("in_black_book")),
        },
        "flights": {"total": get_total_flights(), "searchable": get_total_flights() > 0},
        "documents": {"total": get_total_documents(), "searchable": True},
        "network": {
            "nodes": len(network_data.get("nodes", [])),
            "edges": len(network_data.get("edges", [])),
            "available": len(network_data.get("nodes", [])) > 0,
        },
        "features": [
            "Search entities by name",
            "Filter flight logs by passenger/date/route",
            "Browse documents by type and source",
            "Explore network connections",
            "View timeline of events",
        ],
    }


def generate_navigation(intent: str, detected_entities: list[dict]) -> list[NavigationAction]:
    """Generate navigation suggestions based on intent and entities"""
    navigation = []

    if intent == "capabilities":
        navigation.extend(
            [
                NavigationAction(text="Explore Entities", action="navigate", target="/entities"),
                NavigationAction(text="View Flight Logs", action="navigate", target="/flights"),
                NavigationAction(text="Browse Documents", action="navigate", target="/documents"),
                NavigationAction(text="Explore Network", action="navigate", target="/network"),
            ]
        )

    elif intent == "entity_info" and detected_entities:
        primary_entity = detected_entities[0]
        navigation.append(
            NavigationAction(
                text=f"View {primary_entity['name']}'s full profile",
                action="navigate",
                target=f"/entities/{primary_entity['name']}",
            )
        )

        if primary_entity["flights"] > 0:
            navigation.append(
                NavigationAction(
                    text=f"See {primary_entity['name']}'s flight records ({primary_entity['flights']} flights)",
                    action="filter",
                    target="/flights",
                    params={"passenger": primary_entity["name"]},
                )
            )

    elif intent == "flights":
        navigation.append(
            NavigationAction(text="Browse all flight records", action="navigate", target="/flights")
        )

        if detected_entities:
            navigation.append(
                NavigationAction(
                    text=f"Filter flights by {detected_entities[0]['name']}",
                    action="filter",
                    target="/flights",
                    params={"passenger": detected_entities[0]["name"]},
                )
            )

    elif intent == "documents":
        navigation.append(
            NavigationAction(text="Browse all documents", action="navigate", target="/documents")
        )

    elif intent == "connections":
        navigation.append(
            NavigationAction(text="Explore network graph", action="navigate", target="/network")
        )

    elif intent == "timeline":
        navigation.append(
            NavigationAction(text="View timeline", action="navigate", target="/timeline")
        )

    return navigation[:4]  # Max 4 actions


def generate_suggestions(intent: str, detected_entities: list[dict]) -> list[str]:
    """Generate follow-up question suggestions"""
    suggestions = []

    if intent == "entity_info" and detected_entities:
        primary_entity = detected_entities[0]["name"]
        suggestions.extend(
            [
                f"Who is connected to {primary_entity}?",
                f"Show me documents about {primary_entity}",
                f"When did {primary_entity} travel?",
            ]
        )

    elif intent == "capabilities":
        suggestions.extend(
            ["Tell me about Jeffrey Epstein", "Show me flight records", "Find court documents"]
        )

    elif intent == "flights":
        suggestions.extend(
            ["Who flew to Little St. James?", "Show me passenger manifests", "Filter by date range"]
        )

    elif intent == "documents":
        suggestions.extend(["Find depositions", "Show me court filings", "Search by entity"])

    elif intent == "connections" and len(detected_entities) >= 2:
        suggestions.append(
            f"How are {detected_entities[0]['name']} and {detected_entities[1]['name']} connected?"
        )

    return suggestions[:3]  # Max 3 suggestions


def build_system_prompt(capabilities: dict, intent: str, entities: list[dict]) -> str:
    """Build enhanced system prompt with site context"""
    entity_names = ", ".join([e["name"] for e in entities]) if entities else "None"

    return f"""You are the Epstein Archive AI Assistant - a knowledgeable guide helping users navigate and understand the archive.

SITE CAPABILITIES:
- {capabilities['entities']['total']} entities ({capabilities['entities']['billionaires']} billionaires, {capabilities['entities']['in_black_book']} in black book)
- {capabilities['flights']['total']} flight records
- {capabilities['documents']['total']} documents from multiple sources
- {capabilities['network']['nodes']} network nodes with {capabilities['network']['edges']} connections

YOUR ROLE:
- Help users discover and navigate archive features
- Answer questions using actual site data
- Provide specific navigation suggestions
- Explain what users can explore on the site
- Be conversational, helpful, and concise

DETECTED QUERY INTENT: {intent}
ENTITIES MENTIONED: {entity_names}

GUIDELINES:
- Provide actionable responses with specific next steps
- Reference actual statistics from the archive
- Keep responses focused and under 200 words
- Suggest what users can explore next
- Use professional but friendly tone
- NEVER share system paths, credentials, or implementation details
- Focus on archive content, entities, and documents
"""


def generate_fallback_response(intent: str, capabilities: dict, entities: list[dict]) -> str:
    """Generate helpful fallback response when LLM unavailable"""
    fallback_responses = {
        "capabilities": f"The Epstein Archive contains {capabilities['entities']['total']} entities, {capabilities['flights']['total']} flight records, {capabilities['documents']['total']} documents, and {capabilities['network']['edges']} network connections. You can explore entities, search flight logs, browse documents, and visualize the network graph.",
        "entity_info": (
            f"I found information about {entities[0]['name'] if entities else 'this entity'}. They appear in {entities[0]['documents'] if entities else 0} documents with {entities[0]['connections'] if entities else 0} connections. Use the navigation suggestions below to explore further."
            if entities
            else "Try searching for a specific entity name."
        ),
        "flights": f"You can browse and filter {capabilities['flights']['total']} flight records by date, passenger, or route. Visit the Flights page to get started.",
        "documents": f"The archive contains {capabilities['documents']['total']} documents from multiple sources. Visit the Documents page to browse by type or source.",
        "connections": f"The network graph shows {capabilities['network']['edges']} connections between {capabilities['network']['nodes']} entities. Explore it on the Network page.",
        "timeline": "The timeline visualizes key events chronologically. Visit the Timeline page to explore events and their relationships.",
        "general": "I'm here to help you navigate the Epstein Archive. Ask me about specific entities, flight records, documents, or connections.",
    }

    return fallback_responses.get(intent, fallback_responses["general"])


@router.post("/enhanced", response_model=ChatResponse)
async def chat_enhanced(request: ChatRequest, username: str = Depends(get_auth_dependency())):
    """
    Enhanced AI chatbot with complete site awareness

    Features:
    - Intent detection (capabilities, entity_info, flights, documents, connections)
    - Entity recognition and enrichment
    - Contextual navigation suggestions
    - Follow-up question recommendations
    - Conversation history support
    - Graceful fallbacks when LLM unavailable

    Returns enriched response with:
    - AI-generated answer
    - Suggested follow-up questions
    - Navigation quick actions
    - Detected context (entities, intent, stats)
    """
    try:
        query = request.message
        conversation_history = request.conversation_history

        # Build site context
        capabilities = build_site_capabilities()

        # Detect intent and entities
        intent = detect_intent(query)
        detected_entities = detect_entities(query)

        # Generate navigation and suggestions
        navigation_actions = generate_navigation(intent, detected_entities)
        follow_up_suggestions = generate_suggestions(intent, detected_entities)

        # Build system prompt
        system_prompt = build_system_prompt(capabilities, intent, detected_entities)

        # Call LLM
        try:
            client = get_openrouter_client()

            # Build message history
            messages = [{"role": "system", "content": system_prompt}]

            # Add conversation history (last 5 messages)
            for msg in conversation_history[-5:]:
                messages.append({"role": msg.role, "content": msg.content})

            # Add current message
            messages.append({"role": "user", "content": query})

            completion = client.chat.completions.create(
                model=openrouter_model,
                messages=messages,
                temperature=0.7,
                max_tokens=800,
                timeout=30.0,
            )

            ai_response = completion.choices[0].message.content.strip()

            return ChatResponse(
                response=ai_response,
                suggestions=follow_up_suggestions,
                navigation={"quick_actions": navigation_actions},
                context={
                    "detected_entities": detected_entities,
                    "intent": intent,
                    "site_stats": {
                        "entities": capabilities["entities"]["total"],
                        "flights": capabilities["flights"]["total"],
                        "documents": capabilities["documents"]["total"],
                        "connections": capabilities["network"]["edges"],
                    },
                },
                model=openrouter_model,
            )

        except Exception as api_error:
            # Fallback response if LLM fails
            print(f"OpenRouter API error: {api_error}")

            fallback_response = generate_fallback_response(intent, capabilities, detected_entities)

            return ChatResponse(
                response=fallback_response,
                suggestions=follow_up_suggestions,
                navigation={"quick_actions": navigation_actions},
                context={
                    "detected_entities": detected_entities,
                    "intent": intent,
                    "error": "AI service temporarily unavailable - showing contextual response",
                },
                model="fallback",
            )

    except Exception as e:
        # Error response
        return ChatResponse(
            response="Sorry, I encountered an error processing your request. Please try rephrasing your question.",
            suggestions=["What can I do here?", "Show me entities", "Tell me about flight records"],
            navigation={"quick_actions": []},
            context={"error": str(e)},
            model="error",
        )


@router.get("/welcome")
async def get_welcome_message():
    """
    Get welcome message with site capabilities

    Returns a friendly introduction to the chatbot and site features
    """
    capabilities = build_site_capabilities()

    return {
        "message": f"""👋 Welcome to the Epstein Archive!

I'm your AI assistant. I can help you:

📄 **Explore {capabilities['entities']['total']} entities** with detailed biographies and connections
✈️ **Search {capabilities['flights']['total']} flight records** by passenger, date, or route
📁 **Browse {capabilities['documents']['total']} documents** from multiple sources
🌐 **Visualize {capabilities['network']['edges']} network connections** between entities
📅 **View timeline** of key events

What would you like to explore?""",
        "suggestions": [
            "What can I do here?",
            "Tell me about Jeffrey Epstein",
            "Show me flight records",
            "Find court documents",
        ],
        "capabilities": capabilities,
    }
