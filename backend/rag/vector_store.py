import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import uuid

logger = logging.getLogger(__name__)

class VectorStoreManager:
    """Manages vector store operations with ChromaDB"""
    
    def __init__(
        self, 
        persist_directory: str = "data/vector_db",
        embedding_model_name: str = "all-MiniLM-L6-v2"
    ):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {embedding_model_name}")
        self.embedding_model = SentenceTransformer(embedding_model_name)
        
        # Initialize collections
        self.collections = self._initialize_collections()
        
        logger.info(f"VectorStoreManager initialized with {len(self.collections)} collections")
    
    # In vector_store.py, update _initialize_collections method:

    def _initialize_collections(self) -> Dict[str, Any]:
        """Initialize all content-type collections"""
        collection_configs = {
            # JSON-based collections
            'spiritual_sites': {'description': 'JSON entities from spiritualSites.json', 'type': 'entity'},
            'festivals': {'description': 'JSON entities from festivals.json', 'type': 'entity'},
            'crowd_patterns': {'description': 'JSON entities from crowdPatterns.json', 'type': 'entity'},
            'homestays': {'description': 'JSON entities from homestays.json', 'type': 'entity'},
            'treks': {'description': 'JSON entities from treks.json', 'type': 'entity'},
            'cuisines': {'description': 'JSON entities from cuisines.json', 'type': 'entity'},
            'wellness': {'description': 'JSON entities from wellness.json', 'type': 'entity'},
            'eco_tips': {'description': 'JSON entities from ecoTips.json', 'type': 'entity'},
            'emergency_info': {'description': 'JSON entities from emergencyInfo.json', 'type': 'entity'},
            'shlokas': {'description': 'JSON entities from shlokas.json', 'type': 'entity'},
            'personas': {'description': 'JSON entities from personas.json', 'type': 'entity'},
            
            # Document-based collections (existing)
            'general': {'description': 'General purpose documents', 'type': 'document'},
            'trekking': {'description': 'Trekking and adventure content', 'type': 'document'},
            'cultural': {'description': 'Cultural and heritage content', 'type': 'document'},
            'government': {'description': 'Official and regulatory content', 'type': 'document'},
        }
        
        collections = {}
        for name, config in collection_configs.items():
            full_name = f"india_{name}"
            try:
                collections[name] = self.client.get_or_create_collection(
                    name=full_name,
                    metadata=config
                )
                logger.info(f"✓ Initialized collection: {full_name}")
            except Exception as e:
                logger.error(f"✗ Error creating collection {full_name}: {str(e)}")
        
        return collections

    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        collection_name: str = "general",
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add documents to specified collection
        
        Args:
            documents: List of document texts
            metadatas: List of metadata dicts
            collection_name: Target collection (without 'india_' prefix)
            ids: Optional list of document IDs
        
        Returns:
            List of document IDs
        """
        if not documents:
            logger.warning("No documents to add")
            return []
        
        try:
            # Get collection
            collection = self.collections.get(collection_name)
            if not collection:
                logger.error(f"Collection not found: {collection_name}")
                return []
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(documents).tolist()
            
            # Generate IDs if not provided
            if ids is None:
                ids = [str(uuid.uuid4()) for _ in documents]
            
            # Clean metadata (ChromaDB restrictions)
            cleaned_metadatas = []
            for metadata in metadatas:
                cleaned = {}
                for key, value in metadata.items():
                    # Convert lists to comma-separated strings
                    if isinstance(value, list):
                        cleaned[key] = ', '.join(str(v) for v in value) if value else ''
                    # Convert None to empty string
                    elif value is None:
                        cleaned[key] = ''
                    # Keep strings, numbers, bools
                    elif isinstance(value, (str, int, float, bool)):
                        cleaned[key] = value
                    # Convert everything else to string
                    else:
                        cleaned[key] = str(value)
                cleaned_metadatas.append(cleaned)
            
            # Add to collection
            collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=cleaned_metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(documents)} documents to {collection_name}")
            return ids
            
        except Exception as e:
            logger.error(f"Error adding documents to {collection_name}: {str(e)}")
            return []
    
    def add_json_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        entity_type: str
    ) -> List[str]:
        """
        Add JSON-processed documents to appropriate collection
        
        Args:
            documents: List of document texts
            metadatas: List of metadata dicts
            entity_type: Entity type (spiritual_site, festival, etc.)
        
        Returns:
            List of document IDs
        """
        # Map entity_type to collection name
        collection_map = {
            'spiritual_site': 'spiritual_sites',
            'festival': 'festivals',
            'crowd_pattern': 'crowd_patterns',
            'homestay': 'homestays',
            'persona': 'personas',
            'trek': 'treks',
            'cuisine': 'cuisines',
            'wellness': 'wellness',
            'eco_tip': 'eco_tips',
            'emergency_info': 'emergency_info',
            'shloka': 'shlokas',
            'generic': 'general'
        }
        
        collection_name = collection_map.get(entity_type, 'general')
        
        return self.add_documents(
            documents=documents,
            metadatas=metadatas,
            collection_name=collection_name
        )
   

    
    def query(
        self,
        query_text: str,
        collection_name: str = "general",
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query collection with semantic search
        
        Args:
            query_text: Query string
            collection_name: Collection to search
            n_results: Number of results
            where: Metadata filters
            where_document: Document content filters
        
        Returns:
            Query results dict
        """
        try:
            collection = self.collections.get(collection_name)
            if not collection:
                logger.error(f"Collection not found: {collection_name}")
                return {"documents": [], "metadatas": [], "distances": []}
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query_text]).tolist()
            
            # Query collection
            results = collection.query(
                query_embeddings=query_embedding,
                n_results=n_results,
                where=where,
                where_document=where_document
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error querying {collection_name}: {str(e)}")
            return {"documents": [], "metadatas": [], "distances": []}
    
    def query_multiple_collections(
        self,
        query_text: str,
        collection_names: List[str],
        n_results_per_collection: int = 3,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query multiple collections and combine results
        
        Args:
            query_text: Query string
            collection_names: List of collections to search
            n_results_per_collection: Results per collection
            where: Metadata filters
        
        Returns:
            Combined and sorted results
        """
        all_results = []
        
        for collection_name in collection_names:
            results = self.query(
                query_text=query_text,
                collection_name=collection_name,
                n_results=n_results_per_collection,
                where=where
            )
            
            # Format results
            if results.get('documents') and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    all_results.append({
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i],
                        'collection': collection_name
                    })
        
        # Sort by distance (lower is better)
        all_results.sort(key=lambda x: x['distance'])
        
        return all_results
    
    def get_by_entity_id(
        self,
        entity_id: str,
        collection_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch entity by ID from collection
        
        Args:
            entity_id: Entity ID to fetch
            collection_name: Collection to search
        
        Returns:
            Entity data or None
        """
        try:
            collection = self.collections.get(collection_name)
            if not collection:
                return None
            
            results = collection.get(
                where={"entity_id": entity_id},
                limit=1
            )
            
            if results and results['documents']:
                return {
                    'content': results['documents'][0],
                    'metadata': results['metadatas'][0],
                    'id': results['ids'][0]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching entity {entity_id}: {str(e)}")
            return None
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics for a collection"""
        try:
            collection = self.collections.get(collection_name)
            if not collection:
                return {"error": "Collection not found"}
            
            count = collection.count()
            
            return {
                "collection_name": collection_name,
                "document_count": count,
                "full_name": f"india_{collection_name}"
            }
            
        except Exception as e:
            logger.error(f"Error getting stats for {collection_name}: {str(e)}")
            return {"error": str(e)}
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all collections"""
        stats = {}
        total_docs = 0
        
        for collection_name in self.collections.keys():
            collection_stats = self.get_collection_stats(collection_name)
            stats[collection_name] = collection_stats
            if 'document_count' in collection_stats:
                total_docs += collection_stats['document_count']
        
        return {
            "collections": stats,
            "total_documents": total_docs,
            "total_collections": len(self.collections)
        }
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection"""
        try:
            full_name = f"india_{collection_name}"
            self.client.delete_collection(name=full_name)
            if collection_name in self.collections:
                del self.collections[collection_name]
            logger.info(f"Deleted collection: {full_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection {collection_name}: {str(e)}")
            return False
    
    def reset_collection(self, collection_name: str) -> bool:
        """Reset (delete and recreate) a collection"""
        try:
            self.delete_collection(collection_name)
            # Recreate
            full_name = f"india_{collection_name}"
            self.collections[collection_name] = self.client.create_collection(
                name=full_name
            )
            logger.info(f"Reset collection: {full_name}")
            return True
        except Exception as e:
            logger.error(f"Error resetting collection {collection_name}: {str(e)}")
            return False
