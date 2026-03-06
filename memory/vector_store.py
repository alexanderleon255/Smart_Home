#!/usr/bin/env python3
"""
Vector Memory Implementation using ChromaDB.

Provides semantic search over historical conversations, entities, and automations.
Part of the 4-tier memory architecture (Tier 4: Vector Memory).
"""

import chromadb
from sentence_transformers import SentenceTransformer
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


class VectorMemory:
    """Semantic search over historical data using ChromaDB."""
    
    def __init__(
        self,
        persist_dir: str = "~/hub_memory/vector_db",
        model_name: str = "all-MiniLM-L6-v2"  # Fast, small model (80MB, 384-dim)
    ):
        """
        Initialize vector memory with ChromaDB persistence.
        
        Args:
            persist_dir: Directory to persist the database
            model_name: Sentence-transformers model for embeddings
        """
        self.persist_dir = Path(persist_dir).expanduser()
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB with persistence (new API – PersistentClient)
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
        )
        
        # Collections
        self.conversations = self.client.get_or_create_collection(
            name="conversations",
            metadata={"description": "Session transcripts and summaries"}
        )
        self.entities = self.client.get_or_create_collection(
            name="entities",
            metadata={"description": "People, places, products mentioned"}
        )
        self.automations = self.client.get_or_create_collection(
            name="automations",
            metadata={"description": "Created automations and their rationale"}
        )
        
        # Embedding model (lazy loaded on first use)
        self._embedder = None
        self.model_name = model_name
    
    @property
    def embedder(self):
        """Lazy load the embedding model."""
        if self._embedder is None:
            self._embedder = SentenceTransformer(self.model_name)
        return self._embedder
        
    def add_conversation(
        self,
        text: str,
        metadata: Dict[str, Any],
        session_id: Optional[str] = None
    ):
        """
        Add conversation chunk or summary to vector store.
        
        Args:
            text: Conversation text to embed
            metadata: Additional context (speaker, timestamp, etc.)
            session_id: Session identifier
        """
        import uuid
        
        if session_id is None:
            session_id = datetime.now().strftime("session_%Y%m%d_%H%M%S")
            
        embedding = self.embedder.encode(text).tolist()
        
        self.conversations.add(
            ids=[f"{session_id}_{str(uuid.uuid4())}"],
            embeddings=[embedding],
            documents=[text],
            metadatas=[{
                **metadata,
                "session_id": session_id,
                "indexed_at": datetime.now().isoformat()
            }]
        )
        
    def add_entity(
        self,
        entity_type: str,
        entity_value: str,
        context: str,
        source_session: str
    ):
        """
        Add entity with context to vector store.
        
        Args:
            entity_type: Type of entity (person, place, product, etc.)
            entity_value: The entity value itself
            context: Surrounding context
            source_session: Source session ID
        """
        import uuid
        
        text = f"{entity_type}: {entity_value}. Context: {context}"
        embedding = self.embedder.encode(text).tolist()
        
        self.entities.add(
            ids=[f"entity_{str(uuid.uuid4())}"],
            embeddings=[embedding],
            documents=[text],
            metadatas=[{
                "type": entity_type,
                "value": entity_value,
                "context": context,
                "source_session": source_session,
                "indexed_at": datetime.now().isoformat()
            }]
        )
    
    def add_automation(
        self,
        name: str,
        description: str,
        rationale: str,
        config: Dict[str, Any]
    ):
        """
        Add automation to vector store.
        
        Args:
            name: Automation name
            description: What it does
            rationale: Why it was created
            config: Configuration details
        """
        import uuid
        
        text = f"{name}: {description}. Rationale: {rationale}"
        embedding = self.embedder.encode(text).tolist()
        
        self.automations.add(
            ids=[f"automation_{str(uuid.uuid4())}"],
            embeddings=[embedding],
            documents=[text],
            metadatas=[{
                "name": name,
                "description": description,
                "rationale": rationale,
                "config": str(config),
                "created_at": datetime.now().isoformat()
            }]
        )
        
    def search(
        self,
        query: str,
        collection: str = "conversations",
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Semantic search across a collection.
        
        Args:
            query: Search query
            collection: Collection name (conversations, entities, automations)
            n_results: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of matching documents with metadata and similarity scores
        """
        collection_obj = getattr(self, collection)
        query_embedding = self.embedder.encode(query).tolist()
        
        results = collection_obj.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                formatted.append({
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "similarity": 1 - results["distances"][0][i]  # Convert distance to similarity
                })
            
        return formatted
        
    def search_all(
        self,
        query: str,
        n_results: int = 5
    ) -> Dict[str, List[Dict]]:
        """
        Search across all collections.
        
        Args:
            query: Search query
            n_results: Number of results per collection
            
        Returns:
            Dictionary with results from each collection
        """
        return {
            "conversations": self.search(query, "conversations", n_results),
            "entities": self.search(query, "entities", n_results),
            "automations": self.search(query, "automations", n_results)
        }
    
    def search_by_session(
        self,
        session_id: str,
        n_results: int = 10
    ) -> List[Dict]:
        """
        Retrieve all entries from a specific session.
        
        Args:
            session_id: Session identifier
            n_results: Maximum results
            
        Returns:
            List of conversation entries from that session
        """
        return self.search(
            query="",
            collection="conversations",
            n_results=n_results,
            filter_metadata={"session_id": session_id}
        )
        
    def get_stats(self) -> Dict[str, int]:
        """
        Get collection sizes.
        
        Returns:
            Dictionary with counts for each collection
        """
        return {
            "conversations": self.conversations.count(),
            "entities": self.entities.count(),
            "automations": self.automations.count()
        }
    
    def clear_collection(self, collection: str):
        """Clear a specific collection (use with caution)."""
        if collection == "conversations":
            self.client.delete_collection("conversations")
            self.conversations = self.client.create_collection("conversations")
        elif collection == "entities":
            self.client.delete_collection("entities")
            self.entities = self.client.create_collection("entities")
        elif collection == "automations":
            self.client.delete_collection("automations")
            self.automations = self.client.create_collection("automations")
