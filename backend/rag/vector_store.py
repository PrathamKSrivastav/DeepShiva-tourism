import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import uuid

# Qdrant imports
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, Filter, FieldCondition, MatchValue

logger = logging.getLogger(__name__)

class VectorStoreManager:
    """Manages vector store operations with ChromaDB and optional Qdrant Cloud"""

    def __init__(
        self,
        persist_directory: str = "data/vector_db",
        embedding_model_name: str = "all-MiniLM-L6-v2",
        qdrant_host: str = None,
        qdrant_api_key: str = None,
        qdrant_dim: int = 384  # default embedding size
    ):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client (fallback)
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize Qdrant client (optional)
        self.qdrant_client = None
        self.qdrant_dim = qdrant_dim
        
        if qdrant_host and qdrant_api_key:
            try:
                self.qdrant_client = QdrantClient(
                    url=qdrant_host, 
                    api_key=qdrant_api_key,
                    prefer_grpc=False
                )
                logger.info("Connected to Qdrant Cloud")
            except Exception as e:
                logger.warning(f"Could not connect to Qdrant Cloud: {e}")
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {embedding_model_name}")
        self.embedding_model = SentenceTransformer(embedding_model_name)
        
        # Initialize collections
        self.collections = self._initialize_collections()
        logger.info(f"VectorStoreManager initialized with {len(self.collections)} collections")

    # --------------------------------------------------
    # Cloud availability
    # --------------------------------------------------
    def _cloud_available(self) -> bool:
        if not self.qdrant_client:
            return False
        try:
            self.qdrant_client.get_collections()
            return True
        except Exception:
            return False

    # --------------------------------------------------
    # Collections (with optional Qdrant)
    # --------------------------------------------------
    def _get_or_create_collection(self, name: str):
        full_name = f"india_{name}"
        
        # Try Qdrant first
        if self._cloud_available():
            try:
                existing = [c.name for c in self.qdrant_client.get_collections().collections]
                if full_name not in existing:
                    self.qdrant_client.recreate_collection(
                        collection_name=full_name,
                        vectors_config=VectorParams(size=self.qdrant_dim, distance=Distance.COSINE)
                    )
                    
                    # === ADD THIS TO FIX 400 ERROR ===
                    try:
                        self.qdrant_client.create_payload_index(
                            collection_name=full_name,
                            field_name="entity_id",
                            field_schema="keyword"
                        )
                        logger.info(f"Created index for entity_id in {full_name}")
                    except Exception as e:
                        logger.warning(f"Index creation failed (might exist): {e}")
                    # =================================
                    
                return full_name
            except Exception as e:
                logger.warning(f"Qdrant error for {full_name}: {e}")
        
        # Fallback to local Chroma
        try:
            return self.client.get_collection(name=full_name)
        except Exception:
            return self.client.create_collection(name=full_name)


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
            
            # Document-based collections
            'general': {'description': 'General purpose documents', 'type': 'document'},
            'trekking': {'description': 'Trekking and adventure content', 'type': 'document'},
            'cultural': {'description': 'Cultural and heritage content', 'type': 'document'},
            'government': {'description': 'Official and regulatory content', 'type': 'document'},
        }
        
        collections = {}
        for name, config in collection_configs.items():
            try:
                collections[name] = self._get_or_create_collection(name)
                logger.info(f"✓ Initialized collection: india_{name}")
            except Exception as e:
                logger.error(f"✗ Error creating collection india_{name}: {str(e)}")
        
        return collections

    def _map_entity_type_to_collection(self, entity_type: str) -> str:
        """
        Maps detected entity types to actual collection names.
        """
        # Mapping from singular/detected types to collection names
        entity_to_collection = {
            'cuisine': 'cuisines',
            'wellness': 'wellness',
            'festival': 'festivals',
            'homestay': 'homestays',
            'trek': 'treks',
            'shloka': 'shlokas',
            'spiritual_site': 'spiritual_sites',
            'emergency_info': 'emergency_info',
            'eco_tip': 'eco_tips',
            'persona': 'personas',
            'crowd_pattern': 'crowd_patterns',
            # Add plurals as well for direct mapping
            'cuisines': 'cuisines',
            'festivals': 'festivals',
            'homestays': 'homestays',
            'treks': 'treks',
            'shlokas': 'shlokas',
            'spiritual_sites': 'spiritual_sites',
            'wellness': 'wellness',
            'emergency_info': 'emergency_info',
            'eco_tips': 'eco_tips',
            'personas': 'personas',
            'crowd_patterns': 'crowd_patterns',
        }
        
        mapped = entity_to_collection.get(entity_type)
        if not mapped:
            logger.warning(f"Unknown entity type '{entity_type}', defaulting to 'general'")
            return 'general'
        return mapped

    # --------------------------------------------------
    # Add documents (tries Qdrant first, then fallback)
    # --------------------------------------------------
    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        collection_name: str = "general",
        ids: Optional[List[str]] = None
    ) -> List[str]:
        if not documents:
            logger.warning("No documents to add")
            return []
            
        ids = ids or [str(uuid.uuid4()) for _ in documents]
        embeddings = self.embedding_model.encode(documents).tolist()
        
        # Clean metadata
        cleaned_metadatas = []
        for metadata in metadatas:
            cleaned = {}
            for k, v in metadata.items():
                if isinstance(v, list):
                    cleaned[k] = ', '.join(str(i) for i in v) if v else ''
                elif v is None:
                    cleaned[k] = ''
                elif isinstance(v, (str, int, float, bool)):
                    cleaned[k] = v
                else:
                    cleaned[k] = str(v)
            cleaned_metadatas.append(cleaned)
            
        # Try Qdrant first
        if self._cloud_available():
            try:
                points = [{"id": id_, "vector": emb, "payload": {"text": doc, **meta} } 
                         for id_, emb, doc, meta in zip(ids, embeddings, documents, cleaned_metadatas)]
                
                self.qdrant_client.upsert(collection_name=f"india_{collection_name}", points=points)
                logger.info(f"Added {len(documents)} documents to Qdrant: {collection_name}")
                return ids
            except Exception as e:
                logger.warning(f"Qdrant upload failed, using Chroma: {e}")
        
        # Fallback to Chroma
        collection = self.collections.get(collection_name)
        if isinstance(collection, str):
            # If it's a string (Qdrant name), get the actual Chroma collection
            collection = self.client.get_collection(name=collection)
            
        collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=cleaned_metadatas,
            ids=ids
        )
        logger.info(f"Added {len(documents)} documents to Chroma: {collection_name}")
        return ids

    def add_json_documents(
        self,
        documents,
        metadatas,
        collection_name=None,
        **kwargs,
    ):
        """
        Compatibility layer for ContentManager JSON ingestion.
        """
        # Map entity type to actual collection name
        if collection_name:
            collection_name = self._map_entity_type_to_collection(collection_name)
        else:
            collection_name = 'general'
            
        logger.info(
            "📥 Ingesting %d JSON documents into collection: %s",
            len(documents),
            collection_name
        )
        
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
        Tries Qdrant first, falls back to Chroma if unavailable.
        """
        # ============ LOGGING ============
        if self.qdrant_client:
            logger.info(f"🟢 USING QDRANT for query: '{query_text[:50]}...' in collection: {collection_name}")
        else:
            logger.warning(f"🔴 USING CHROMADB (Qdrant unavailable) for query: '{query_text[:50]}...' in collection: {collection_name}")
        
        query_embedding = self.embedding_model.encode([query_text]).tolist()

        # --- Try Qdrant first ---
        if self._cloud_available():
            try:
                response = self.qdrant_client.search(
                    collection_name=f"india_{collection_name}",
                    query_vector=query_embedding[0],
                    limit=n_results,
                    with_payload=True,
                    score_threshold=None
                )
                
                return {
                    "documents": [[hit.payload.get("text", "") for hit in response]],
                    "metadatas": [[hit.payload for hit in response]],
                    "distances": [[hit.score for hit in response]]
                }
            except Exception as e:
                logger.warning(f"Qdrant query failed, using Chroma fallback: {e}")

        # --- Fallback to Chroma ---
        # FIX: Explicitly retrieve the collection object if we only have the name
        collection = self.collections.get(collection_name)
        
        if isinstance(collection, str):
            try:
                collection = self.client.get_collection(name=collection)
            except Exception as e:
                logger.error(f"Could not retrieve Chroma collection object for '{collection_name}': {e}")
                return {"documents": [], "metadatas": [], "distances": []}

        if not collection:
            logger.error(f"Collection not found: {collection_name}")
            return {"documents": [], "metadatas": [], "distances": []}

        try:
            return collection.query(
                query_embeddings=query_embedding,
                n_results=n_results,
                where=where,
                where_document=where_document
            )
        except Exception as e:
            logger.error(f"Error querying Chroma {collection_name}: {str(e)}")
            return {"documents": [], "metadatas": [], "distances": []}

    def query_multiple_collections(
        self,
        query_text: str,
        collection_names: List[str],
        n_results_per_collection: int = 3,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query multiple collections and combine results.
        Tries Qdrant first for each collection; falls back to Chroma if unavailable.
        """
        all_results = []
        query_embedding = self.embedding_model.encode([query_text]).tolist()

        for collection_name in collection_names:
            # --- Try Qdrant first ---
            collection_results = None
            if self._cloud_available():
                try:
                    response = self.qdrant_client.search(
                        collection_name=f"india_{collection_name}",
                        query_vector=query_embedding[0],
                        limit=n_results_per_collection,
                        with_payload=True,
                        score_threshold=None
                    )
                    
                    collection_results = {
                        "documents": [[hit.payload.get("text", "") for hit in response]],
                        "metadatas": [[hit.payload for hit in response]],
                        "distances": [[hit.score for hit in response]]
                    }
                except Exception as e:
                    logger.warning(f"Qdrant query failed for {collection_name}, using Chroma fallback: {e}")
            
            # --- Fallback to Chroma ---
            if collection_results is None:
                collection = self.collections.get(collection_name)
                # FIX: Ensure we have the object
                if isinstance(collection, str):
                    try:
                        collection = self.client.get_collection(name=collection)
                    except Exception:
                        collection = None
                        
                if not collection:
                    logger.error(f"Collection not found: {collection_name}")
                    continue
                
                try:
                    collection_results = collection.query(
                        query_embeddings=query_embedding,
                        n_results=n_results_per_collection,
                        where=where
                    )
                except Exception as e:
                    logger.error(f"Error querying Chroma {collection_name}: {str(e)}")
                    continue
            
            # --- Format results ---
            if collection_results.get("documents") and collection_results["documents"][0]:
                for i in range(len(collection_results["documents"][0])):
                    all_results.append({
                        "content": collection_results["documents"][0][i],
                        "metadata": collection_results["metadatas"][0][i],
                        "distance": collection_results["distances"][0][i],
                        "collection": collection_name
                    })

        return all_results

    def get_by_entity_id(
        self,
        entity_id: str,
        collection_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch entity by ID from collection (Qdrant first, fallback to Chroma)
        """
        try:
            # ---------- Qdrant FIRST (correct way: scroll + filter) ----------
            if self._cloud_available():
                try:
                    hits, _ = self.qdrant_client.scroll(
                        collection_name=f"india_{collection_name}",
                        scroll_filter=Filter(
                            must=[
                                FieldCondition(
                                    key="entity_id",
                                    match=MatchValue(value=entity_id)
                                )
                            ]
                        ),
                        limit=1,
                        with_payload=True
                    )
                    
                    if hits:
                        hit = hits[0]
                        return {
                            "content": hit.payload.get("text", ""),
                            "metadata": hit.payload,
                            "id": hit.id
                        }
                except Exception as e:
                    logger.warning(
                        f"Qdrant fetch failed for {collection_name} entity {entity_id}: {e}"
                    )
            
            # ---------- FALLBACK TO CHROMA ----------
            collection = self.collections.get(collection_name)
            if isinstance(collection, str):
                collection = self.client.get_collection(name=collection)

            if not collection:
                return None

            results = collection.get(where={"entity_id": entity_id}, limit=1)
            if results and results.get("documents"):
                return {
                    "content": results["documents"][0],
                    "metadata": results["metadatas"][0],
                    "id": results["ids"][0]
                }
            return None
            
        except Exception as e:
            logger.error(f"Error fetching entity {entity_id}: {str(e)}")
            return None

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics for a collection (supports both Qdrant and Chroma)"""
        try:
            collection = self.collections.get(collection_name)
            
            if not collection:
                return {"error": "Collection not found"}

            # If Qdrant is available, get stats from Qdrant
            if self._cloud_available():
                try:
                    info = self.qdrant_client.get_collection(collection_name=f"india_{collection_name}")
                    return {
                        "collection_name": collection_name,
                        "document_count": info.points_count,
                        "full_name": f"india_{collection_name}"
                    }
                except Exception as e:
                    logger.warning(f"Qdrant stats failed for {collection_name}, trying Chroma: {e}")

            # Fallback to Chroma or if collection is a Chroma object
            if isinstance(collection, str):
                try:
                    collection = self.client.get_collection(name=collection)
                except:
                    return {"document_count": 0}

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
        """Delete a collection (Chroma only, Qdrant can be added optionally)"""
        try:
            full_name = f"india_{collection_name}"
            
            # Chroma delete
            try:
                self.client.delete_collection(name=full_name)
            except:
                pass
            
            # Remove from internal map
            if collection_name in self.collections:
                del self.collections[collection_name]
                
            # Optional: Qdrant delete
            if self._cloud_available():
                try:
                    self.qdrant_client.delete_collection(collection_name=full_name)
                except Exception as e:
                    logger.warning(f"Qdrant delete failed for {full_name}: {e}")
            
            logger.info(f"Deleted collection: {full_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection {collection_name}: {str(e)}")
            return False

    def reset_collection(self, collection_name: str) -> bool:
        """Reset (delete and recreate) a collection"""
        if not self.delete_collection(collection_name):
            return False
            
        # Recreate Chroma collection
        full_name = f"india_{collection_name}"
        self.collections[collection_name] = self.client.create_collection(name=full_name)
        
        # Recreate Qdrant collection
        if self._cloud_available():
            try:
                self.qdrant_client.recreate_collection(
                    collection_name=full_name,
                    vectors_config=VectorParams(size=self.qdrant_dim, distance=Distance.COSINE)
                )
            except Exception as e:
                logger.warning(f"Qdrant recreate failed for {full_name}: {e}")
        
        logger.info(f"Reset collection: {full_name}")
        return True

    def qdrant_health(self) -> dict:
        if not self._cloud_available():
            return {"status": "down"}
        try:
            collections = self.qdrant_client.get_collections().collections
            details = {}
            for c in collections:
                info = self.qdrant_client.get_collection(c.name)
                details[c.name] = {
                    "vectors": info.points_count,
                    "status": info.status
                }
            return {
                "status": "up",
                "collections": details
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
