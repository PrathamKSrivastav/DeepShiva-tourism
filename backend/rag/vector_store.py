import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import uuid
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class VectorStoreManager:
    def __init__(self, persist_directory: str = "data/vector_db"):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize Chroma client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Create collections for different content types
        self.collections = {
            "general": self._get_or_create_collection("uttarakhand_general"),
            "spiritual": self._get_or_create_collection("uttarakhand_spiritual"),
            "trekking": self._get_or_create_collection("uttarakhand_trekking"),
            "cultural": self._get_or_create_collection("uttarakhand_cultural"),
            "government": self._get_or_create_collection("uttarakhand_government")
        }
        
        logger.info(f"Vector store initialized with {len(self.collections)} collections")
    
    def _get_or_create_collection(self, name: str):
        """Get existing collection or create new one"""
        try:
            return self.client.get_collection(name=name)
        except Exception:
            return self.client.create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
    
    def add_documents(
        self, 
        documents: List[str], 
        metadatas: List[Dict[str, Any]], 
        collection_name: str = "general"
    ) -> List[str]:
        """Add documents to specified collection"""
        
        if collection_name not in self.collections:
            logger.error(f"Collection {collection_name} not found")
            return []
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(documents).tolist()
        
        # Generate unique IDs
        ids = [str(uuid.uuid4()) for _ in documents]
        
        # Add to collection
        collection = self.collections[collection_name]
        collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"Added {len(documents)} documents to {collection_name} collection")
        return ids
    
    def search_documents(
        self, 
        query: str, 
        collection_names: List[str] = None,
        n_results: int = 5,
        persona_filter: str = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search for relevant documents across collections
        
        Args:
            query: Search query
            collection_names: Collections to search (None = all)
            n_results: Number of results per collection
            persona_filter: Filter by persona relevance
        
        Returns:
            Dict with collection names as keys and results as values
        """
        
        if collection_names is None:
            collection_names = list(self.collections.keys())
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query]).tolist()[0]
        
        results = {}
        
        for collection_name in collection_names:
            if collection_name not in self.collections:
                continue
                
            collection = self.collections[collection_name]
            
            # Build where clause for persona filtering
            where_clause = {}
            if persona_filter:
                persona_relevance = self._get_persona_relevance_score(collection_name, persona_filter)
                if persona_relevance < 0.3:  # Skip collections not relevant to persona
                    continue
            
            try:
                collection_results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results,
                    where=where_clause if where_clause else None
                )
                
                # Format results
                formatted_results = []
                if collection_results['documents'] and collection_results['documents'][0]:
                    for i, doc in enumerate(collection_results['documents'][0]):
                        formatted_results.append({
                            'content': doc,
                            'metadata': collection_results['metadatas'][0][i] if collection_results['metadatas'][0] else {},
                            'distance': collection_results['distances'][0][i] if collection_results['distances'] else 0,
                            'collection': collection_name
                        })
                
                results[collection_name] = formatted_results
                
            except Exception as e:
                logger.error(f"Error searching collection {collection_name}: {str(e)}")
                results[collection_name] = []
        
        return results
    
    def _get_persona_relevance_score(self, collection_name: str, persona: str) -> float:
        """Get relevance score for persona-collection combination"""
        relevance_matrix = {
            "local_guide": {
                "general": 0.9,
                "government": 0.8,
                "trekking": 0.7,
                "cultural": 0.6,
                "spiritual": 0.5
            },
            "spiritual_teacher": {
                "spiritual": 0.9,
                "cultural": 0.8,
                "general": 0.6,
                "government": 0.5,
                "trekking": 0.4
            },
            "trek_companion": {
                "trekking": 0.9,
                "government": 0.7,
                "general": 0.6,
                "cultural": 0.4,
                "spiritual": 0.3
            },
            "cultural_expert": {
                "cultural": 0.9,
                "spiritual": 0.8,
                "general": 0.7,
                "government": 0.6,
                "trekking": 0.4
            }
        }
        
        return relevance_matrix.get(persona, {}).get(collection_name, 0.5)
    
    def get_collection_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all collections"""
        stats = {}
        
        for name, collection in self.collections.items():
            try:
                count = collection.count()
                stats[name] = {
                    "document_count": count,
                    "collection_name": name
                }
            except Exception as e:
                logger.error(f"Error getting stats for {name}: {str(e)}")
                stats[name] = {
                    "document_count": 0,
                    "collection_name": name,
                    "error": str(e)
                }
        
        return stats
    
    def delete_documents(self, ids: List[str], collection_name: str = "general") -> bool:
        """Delete documents by IDs"""
        try:
            if collection_name not in self.collections:
                return False
                
            collection = self.collections[collection_name]
            collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents from {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting documents: {str(e)}")
            return False
    
    def clear_collection(self, collection_name: str) -> bool:
        """Clear all documents from a collection"""
        try:
            if collection_name not in self.collections:
                return False
                
            # Delete and recreate collection
            self.client.delete_collection(name=collection_name)
            self.collections[collection_name] = self._get_or_create_collection(collection_name)
            logger.info(f"Cleared collection {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing collection {collection_name}: {str(e)}")
            return False
