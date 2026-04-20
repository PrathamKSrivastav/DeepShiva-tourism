import logging
import os
import uuid
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from sentence_transformers import SentenceTransformer

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PayloadSchemaType,
    VectorParams,
)

# Silence Pydantic chatter from qdrant-client schema diffs.
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
warnings.filterwarnings("ignore", message=".*validation errors.*")

logger = logging.getLogger(__name__)

# The 4 collections the app uses. Kept as a module constant so callers
# (and clean_ingest.py) can reference a single source of truth.
COLLECTION_NAMES = ("general", "cultural", "trekking", "government")


class VectorStoreManager:
    """Qdrant-backed vector store.

    ChromaDB was removed in favour of a single cloud backend. If Qdrant
    is unreachable, read methods return empty results and write methods
    raise — there is no local fallback.
    """

    def __init__(
        self,
        persist_directory: str = "data/vector_db",  # kept for signature compat, unused
        embedding_model_name: str = "all-MiniLM-L6-v2",
        qdrant_host: str = None,
        qdrant_api_key: str = None,
        qdrant_dim: int = 384,
    ):
        self.persist_directory = Path(persist_directory)
        self.qdrant_dim = qdrant_dim

        self.qdrant_client: Optional[QdrantClient] = None
        if qdrant_host and qdrant_api_key:
            try:
                self.qdrant_client = QdrantClient(
                    url=qdrant_host, api_key=qdrant_api_key, prefer_grpc=False
                )
                logger.info("✅ Connected to Qdrant Cloud")
            except Exception as e:
                logger.error(f"❌ Could not connect to Qdrant Cloud: {e}")

        logger.info(f"Loading embedding model: {embedding_model_name}")
        self.embedding_model = SentenceTransformer(embedding_model_name)

        self.collections: Dict[str, str] = self._initialize_collections()
        logger.info(
            f"VectorStoreManager initialized with {len(self.collections)} collections"
        )

    # ------------------------------------------------------------------
    # Cloud availability
    # ------------------------------------------------------------------
    def _cloud_available(self) -> bool:
        """Availability probe via raw HTTP.

        Using `self.qdrant_client.get_collections()` triggers pydantic
        schema validation on every response. Qdrant Cloud adds new fields
        (e.g. strict_mode_config) ahead of the client's schema, which raises
        ValidationError and makes the client look "down" even though the
        cluster is reachable and search() works. A raw GET /collections
        just needs a 200 — no pydantic parsing, no false negatives.
        """
        if not self.qdrant_client:
            return False
        host = os.getenv("QDRANT_HOST")
        api_key = os.getenv("QDRANT_API_KEY")
        if not (host and api_key):
            return False
        try:
            r = httpx.get(
                f"{host.rstrip('/')}/collections",
                headers={"api-key": api_key},
                timeout=3.0,
            )
            return r.status_code == 200
        except Exception as e:
            logger.warning(f"Qdrant availability probe failed: {e}")
            return False

    # ------------------------------------------------------------------
    # Collection bootstrap
    # ------------------------------------------------------------------
    def _get_or_create_collection(self, name: str) -> str:
        full_name = f"india_{name}"
        if not self._cloud_available():
            logger.warning(
                f"Qdrant unavailable — skipping bootstrap of {full_name}"
            )
            return full_name

        try:
            existing = {c.name for c in self.qdrant_client.get_collections().collections}
            if full_name not in existing:
                self.qdrant_client.recreate_collection(
                    collection_name=full_name,
                    vectors_config=VectorParams(
                        size=self.qdrant_dim, distance=Distance.COSINE
                    ),
                )
                # Payload indexes for filtered lookups.
                for field in ("entity_id", "content_type", "source_type", "location", "region"):
                    try:
                        self.qdrant_client.create_payload_index(
                            collection_name=full_name,
                            field_name=field,
                            field_schema=PayloadSchemaType.KEYWORD,
                        )
                    except Exception as e:
                        logger.warning(
                            f"⚠️ Could not create '{field}' index on {full_name}: {e}"
                        )
                logger.info(f"✅ Created Qdrant collection: {full_name}")
        except Exception as e:
            logger.error(f"❌ Bootstrap error for {full_name}: {e}")

        return full_name

    def _initialize_collections(self) -> Dict[str, str]:
        out = {}
        for name in COLLECTION_NAMES:
            try:
                out[name] = self._get_or_create_collection(name)
                logger.info(f"✓ Initialized collection: india_{name}")
            except Exception as e:
                logger.error(f"✗ Error creating collection india_{name}: {e}")
        return out

    def _map_entity_type_to_collection(self, entity_type: str) -> str:
        mapping = {
            "pilgrimage_site": "cultural",
            "temple": "cultural",
            "mosque": "cultural",
            "church": "cultural",
            "gurudwara": "cultural",
            "monastery": "cultural",
            "festival": "cultural",
            "trek": "trekking",
            "adventure": "trekking",
            "policy": "government",
            "scheme": "government",
            "regulation": "government",
        }
        return mapping.get(entity_type.lower(), "general")

    # ------------------------------------------------------------------
    # Add
    # ------------------------------------------------------------------
    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        collection_name: str = "general",
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        if not documents:
            logger.warning("No documents to add")
            return []
        if not self._cloud_available():
            raise RuntimeError(
                "Qdrant unavailable — cannot add documents (ChromaDB fallback removed)"
            )

        ids = ids or [str(uuid.uuid4()) for _ in documents]
        embeddings = self.embedding_model.encode(documents).tolist()

        cleaned_metadatas = []
        for meta in metadatas:
            out = {}
            for k, v in meta.items():
                if isinstance(v, list):
                    out[k] = ", ".join(str(i) for i in v) if v else ""
                elif v is None:
                    out[k] = ""
                elif isinstance(v, (str, int, float, bool)):
                    out[k] = v
                else:
                    out[k] = str(v)
            cleaned_metadatas.append(out)

        points = [
            {"id": id_, "vector": emb, "payload": {"text": doc, **meta}}
            for id_, emb, doc, meta in zip(ids, embeddings, documents, cleaned_metadatas)
        ]
        self.qdrant_client.upsert(
            collection_name=f"india_{collection_name}", points=points
        )
        logger.info(f"✅ Added {len(documents)} documents to Qdrant: {collection_name}")
        return ids

    def add_json_documents(self, documents, metadatas, collection_name=None, **kwargs):
        """Compatibility wrapper used by ContentManager for JSON ingestion."""
        collection_name = (
            self._map_entity_type_to_collection(collection_name)
            if collection_name
            else "general"
        )
        logger.info(
            "📥 Ingesting %d JSON documents into collection: %s",
            len(documents),
            collection_name,
        )
        return self.add_documents(
            documents=documents, metadatas=metadatas, collection_name=collection_name
        )

    # ------------------------------------------------------------------
    # Single-collection query
    # ------------------------------------------------------------------
    def query(
        self,
        query_text: str,
        collection_name: str = "general",
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        empty = {"documents": [[]], "metadatas": [[]], "distances": [[]]}
        if not self._cloud_available():
            logger.warning(
                f"Qdrant unavailable — returning empty results for '{collection_name}'"
            )
            return empty

        try:
            query_embedding = self.embedding_model.encode([query_text]).tolist()
            logger.info(f"🟢 QDRANT QUERY: '{query_text[:50]}...' in {collection_name}")
            response = self.qdrant_client.search(
                collection_name=f"india_{collection_name}",
                query_vector=query_embedding[0],
                limit=n_results,
                with_payload=True,
                score_threshold=None,
            )
            logger.info(f"✅ QDRANT SUCCESS: Found {len(response)} results")
            return {
                "documents": [[hit.payload.get("text", "") for hit in response]],
                "metadatas": [[hit.payload for hit in response]],
                "distances": [[1 - hit.score for hit in response]],
            }
        except Exception as e:
            logger.warning(f"⚠️ Qdrant query failed for {collection_name}: {e}")
            return empty

    # ------------------------------------------------------------------
    # Multi-collection query
    # ------------------------------------------------------------------
    def query_multiple_collections(
        self,
        query_text: str,
        collection_names: List[str],
        n_results_per_collection: int = 3,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        all_results: List[Dict[str, Any]] = []
        if not self._cloud_available():
            logger.warning("Qdrant unavailable — returning empty multi-collection results")
            return all_results

        query_embedding = self.embedding_model.encode([query_text]).tolist()
        for collection_name in collection_names:
            try:
                response = self.qdrant_client.search(
                    collection_name=f"india_{collection_name}",
                    query_vector=query_embedding[0],
                    limit=n_results_per_collection,
                    with_payload=True,
                    score_threshold=None,
                )
                for hit in response:
                    all_results.append(
                        {
                            "content": hit.payload.get("text", ""),
                            "metadata": hit.payload,
                            "distance": 1 - hit.score,
                            "collection": collection_name,
                        }
                    )
            except Exception as e:
                logger.warning(f"⚠️ Qdrant query failed for {collection_name}: {e}")
        return all_results

    def search_documents(
        self,
        query: str,
        collection_names: Optional[List[str]] = None,
        n_results: int = 5,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Dict-shaped search used by the admin /test-search endpoint.

        Returns: {collection_name: [{content, metadata, distance}, ...]}
        """
        targets = collection_names or list(self.collections.keys())
        out: Dict[str, List[Dict[str, Any]]] = {c: [] for c in targets}
        hits = self.query_multiple_collections(
            query_text=query,
            collection_names=targets,
            n_results_per_collection=n_results,
        )
        for h in hits:
            coll = h.get("collection")
            if coll in out:
                out[coll].append(
                    {
                        "content": h["content"],
                        "metadata": h["metadata"],
                        "distance": h["distance"],
                    }
                )
        return out

    def delete_documents(self, ids: List[str], collection_name: str) -> bool:
        """Delete points by id from a Qdrant collection."""
        if not ids:
            return True
        if not self._cloud_available():
            logger.warning(
                f"Qdrant unavailable — cannot delete {len(ids)} docs from {collection_name}"
            )
            return False
        try:
            self.qdrant_client.delete(
                collection_name=f"india_{collection_name}",
                points_selector=ids,
            )
            logger.info(
                f"✅ Deleted {len(ids)} documents from Qdrant: {collection_name}"
            )
            return True
        except Exception as e:
            logger.error(f"❌ Qdrant delete failed for {collection_name}: {e}")
            return False

    # ------------------------------------------------------------------
    # Entity fetch
    # ------------------------------------------------------------------
    def get_by_entity_id(
        self, entity_id: str, collection_name: str
    ) -> Optional[Dict[str, Any]]:
        if not self._cloud_available():
            return None
        try:
            hits, _ = self.qdrant_client.scroll(
                collection_name=f"india_{collection_name}",
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="entity_id", match=MatchValue(value=entity_id)
                        )
                    ]
                ),
                limit=1,
                with_payload=True,
            )
            if hits:
                hit = hits[0]
                return {
                    "content": hit.payload.get("text", ""),
                    "metadata": hit.payload,
                    "id": hit.id,
                }
        except Exception as e:
            logger.warning(
                f"⚠️ Qdrant fetch failed for {collection_name} entity {entity_id}: {e}"
            )
        return None

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        if collection_name not in self.collections:
            return {"error": "Collection not found"}
        if not self._cloud_available():
            return {
                "collection_name": collection_name,
                "document_count": 0,
                "full_name": f"india_{collection_name}",
                "status": "qdrant-unavailable",
            }
        try:
            info = self.qdrant_client.get_collection(
                collection_name=f"india_{collection_name}"
            )
            return {
                "collection_name": collection_name,
                "document_count": getattr(info, "points_count", 0),
                "full_name": f"india_{collection_name}",
            }
        except Exception as e:
            error_str = str(e).lower()
            if not any(x in error_str for x in ("validation error", "extra inputs", "parsing")):
                logger.warning(
                    f"⚠️ Qdrant stats failed for {collection_name}: {str(e)[:100]}"
                )
            return {"error": str(e)[:120]}

    def get_all_stats(self) -> Dict[str, Any]:
        stats: Dict[str, Any] = {}
        total_docs = 0
        for name in self.collections:
            s = self.get_collection_stats(name)
            stats[name] = s
            if isinstance(s, dict) and "document_count" in s:
                total_docs += s["document_count"]
        return {
            "collections": stats,
            "total_documents": total_docs,
            "total_collections": len(self.collections),
        }

    # ------------------------------------------------------------------
    # Delete / reset
    # ------------------------------------------------------------------
    def delete_collection(self, collection_name: str) -> bool:
        full_name = f"india_{collection_name}"
        if not self._cloud_available():
            logger.warning(
                f"Qdrant unavailable — cannot delete {full_name}"
            )
            return False
        try:
            self.qdrant_client.delete_collection(collection_name=full_name)
            self.collections.pop(collection_name, None)
            logger.info(f"✅ Deleted collection: {full_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Error deleting collection {full_name}: {e}")
            return False

    def reset_collection(self, collection_name: str) -> bool:
        if not self.delete_collection(collection_name):
            return False
        self.collections[collection_name] = self._get_or_create_collection(collection_name)
        logger.info(f"✅ Reset collection: india_{collection_name}")
        return True

    def clear_collection(self, collection_name: str) -> bool:
        """Alias retained for admin-router compatibility."""
        return self.reset_collection(collection_name)

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------
    def qdrant_health(self) -> dict:
        if not self._cloud_available():
            return {"status": "down"}
        try:
            cols = self.qdrant_client.get_collections().collections
            details = {}
            for c in cols:
                try:
                    info = self.qdrant_client.get_collection(c.name)
                    details[c.name] = {
                        "vectors": getattr(info, "points_count", 0),
                        "status": getattr(info, "status", "unknown"),
                    }
                except Exception as e:
                    error_str = str(e).lower()
                    if not any(
                        x in error_str for x in ("validation error", "extra inputs", "parsing")
                    ):
                        logger.warning(
                            f"⚠️ Could not get info for {c.name}: {str(e)[:80]}"
                        )
                    details[c.name] = {"vectors": 0, "status": "error"}
            return {"status": "up", "collections": details}
        except Exception as e:
            return {"status": "error", "error": str(e)[:200]}


# ======================================================================
# Module-level singleton
# ======================================================================
# One VectorStoreManager per process. main.py, routers, and
# utils/groq_service.py all call get_vector_store() instead of
# constructing their own — avoids loading the embedding model
# (~100 MB) three times and guarantees every caller shares the
# same Qdrant credentials.

_vector_store_instance: Optional["VectorStoreManager"] = None


def get_vector_store() -> "VectorStoreManager":
    global _vector_store_instance
    if _vector_store_instance is None:
        import os

        logger.info("🔧 Initializing VectorStoreManager (singleton)")
        _vector_store_instance = VectorStoreManager(
            persist_directory="data/vector_db",
            embedding_model_name="all-MiniLM-L6-v2",
            qdrant_host=os.getenv("QDRANT_HOST"),
            qdrant_api_key=os.getenv("QDRANT_API_KEY"),
            qdrant_dim=int(os.getenv("QDRANT_DIM", 384)),
        )
        if _vector_store_instance._cloud_available():
            logger.info("✅ Qdrant Cloud reachable")
        else:
            logger.error("❌ Qdrant Cloud unreachable — reads will return empty, writes will fail")
    return _vector_store_instance
