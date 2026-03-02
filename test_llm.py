#!/usr/bin/env python3
"""
Smart Home LLM Test Harness v2

Tests Llama 3.1 with AI_CONTEXT structure.
Includes Tool Broker validation layer.

Run: python Smart_Home/test_llm.py
Interactive: python Smart_Home/test_llm.py -i
"""

import json
import urllib.request
from pathlib import Path
from datetime import datetime
from typing import Optional

# Paths
AI_CONTEXT = Path(__file__).parent / "AI_CONTEXT"
LLM_RUNTIME = AI_CONTEXT / "LLM_RUNTIME"
MEMORY = AI_CONTEXT / "MEMORY"

# Model config
MODEL = "llama3.1:8b"
OLLAMA_URL = "http://localhost:11434/api/generate"


def load_file(path: Path) -> str:
    """Load file content."""
    if path.exists():
        return path.read_text()
    return ""


def load_json(path: Path) -> dict:
    """Load JSON file."""
    if path.exists():
        return json.loads(path.read_text())
    return {}


class ToolBroker:
    """
    Validates tool calls from LLM before execution.
    This prevents hallucinated entities from being executed.
    """
    
    def __init__(self):
        self.entities = load_json(LLM_RUNTIME / "entity_registry.json")
        self.alias_index = self.entities.get("alias_index", {})
        
    def resolve_entity(self, name: str) -> Optional[str]:
        """Resolve friendly name to entity_id."""
        name_lower = name.lower().strip()
        if name_lower in self.alias_index:
            return self.alias_index[name_lower]
        for alias, entity_id in self.alias_index.items():
            if name_lower in alias or alias in name_lower:
                return entity_id
        return None
    
    def validate_entity(self, entity_name: str) -> tuple[bool, str]:
        """Check if entity exists in registry."""
        all_entities = []
        for domain_entities in self.entities.get("entities", {}).values():
            for e in domain_entities:
                all_entities.append(e.get("entity_id"))
                all_entities.extend(e.get("aliases", []))
        
        if entity_name.lower() in [e.lower() for e in all_entities]:
            return True, "Valid"
        if self.resolve_entity(entity_name):
            return True, "Resolved"
        return False, f"Unknown entity: {entity_name}"


def count_tokens(text: str) -> int:
    """Rough token estimate (4 chars per token)."""
    return len(text) // 4


def build_context(user_query: str, user_id: str = "alex") -> str:
    """
    Build the full context to inject into the LLM.
    Uses a more explicit prompt format that 8B models follow better.
    """
    
    # Entity registry - explicit list
    entities = load_json(LLM_RUNTIME / "entity_registry.json")
    alias_index = entities.get("alias_index", {})
    known_devices = list(alias_index.keys())
    
    # Dossier retrieval
    dossier_index = load_json(MEMORY / "INDEX" / "dossier_index.json")
    retrieved_dossiers = []
    query_lower = user_query.lower()
    
    for dossier in dossier_index.get("dossiers", []):
        keywords = dossier.get("keywords", [])
        if any(kw in query_lower for kw in keywords):
            dossier_path = MEMORY / dossier["path"].replace("MEMORY/", "")
            if dossier_path.exists():
                retrieved_dossiers.append(load_file(dossier_path))
    
    # Current time
    now = datetime.now().strftime("%A, %B %d, %Y %I:%M %p")
    
    # Simpler, more explicit prompt for 8B model
    context = f"""You are a smart home assistant. Follow these rules EXACTLY:

RULE 1: You can ONLY control these devices: {', '.join(known_devices)}
RULE 2: If user asks for a device NOT in that list, say "I don't have [device]. I have: {', '.join(known_devices)}"
RULE 3: For "unlock" requests, ALWAYS ask "Are you sure?" first
RULE 4: Keep responses to 1-2 sentences

KNOWN DEVICES: {', '.join(known_devices)}

USER PREFERENCES:
- Movie mode: set lights to 40% (NOT 30%), warm (2700K)
- Verbosity: concise

{"MEMORY: " + retrieved_dossiers[0][:500] if retrieved_dossiers else ""}

TIME: {now}

User: {user_query}
Assistant:"""

    return context


def query_llama(prompt: str, model: str = MODEL) -> str:
    """Send query to Ollama API and get response."""
    try:
        data = json.dumps({
            "model": model,
            "prompt": prompt,
            "stream": False
        }).encode()
        
        req = urllib.request.Request(
            OLLAMA_URL,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            return result.get("response", "No response")
    except Exception as e:
        return f"[Error: {e}]"


def test_query(query: str, verbose: bool = True) -> str:
    """Test a single query with context."""
    ctx = build_context(query, "alex")
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"QUERY: {query}")
        print(f"Context: ~{count_tokens(ctx)} tokens")
        print("="*60)
    
    response = query_llama(ctx)
    
    if verbose:
        print(f"\nRESPONSE: {response}")
    
    return response


def main():
    print("=" * 60)
    print("Smart Home LLM Test Harness")
    print(f"Model: {MODEL}")
    print("=" * 60)
    
    # Test queries
    tests = [
        ("Turn on the living room lights", "Should work - entity exists"),
        ("Turn on the garage lights", "Should FAIL - entity not in registry"),
        ("Set up movie mode", "Should use 40% brightness from dossier"),
        ("Unlock the front door", "Should ask for confirmation"),
    ]
    
    for query, expected in tests:
        print(f"\n{'='*60}")
        print(f"TEST: {query}")
        print(f"EXPECTED: {expected}")
        print("="*60)
        
        response = test_query(query, verbose=False)
        print(f"RESPONSE: {response}")
        
        # Simple validation
        if "garage" in query.lower() and "don't" not in response.lower():
            print("⚠️  WARNING: Model may have hallucinated entity")
        elif "unlock" in query.lower() and "sure" not in response.lower() and "confirm" not in response.lower():
            print("⚠️  WARNING: Model should ask for confirmation")
        else:
            print("✅ Response looks reasonable")


def interactive():
    """Interactive chat mode."""
    print("=" * 60)
    print(f"Smart Home LLM - Interactive Mode ({MODEL})")
    print("Type 'quit' to exit, 'broker' to test with ToolBroker")
    print("=" * 60)
    
    broker = ToolBroker()
    
    while True:
        query = input("\nYou: ").strip()
        if query.lower() in ["quit", "exit", "q"]:
            break
        if not query:
            continue
        
        # Check for entity validation mode
        if query.startswith("broker "):
            entity = query.replace("broker ", "")
            valid, msg = broker.validate_entity(entity)
            print(f"Broker: {valid} - {msg}")
            continue
        
        ctx = build_context(query, "alex")
        print(f"[Context: ~{count_tokens(ctx)} tokens]")
        
        response = query_llama(ctx)
        print(f"\nAssistant: {response}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "-i":
        interactive()
    else:
        main()
