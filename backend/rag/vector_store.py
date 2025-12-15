import logging
import os
import socket
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# Disable Chroma telemetry globally
os.environ["ANONYMIZED_TELEMETRY"] = "False"

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """
    Hybrid Chroma manager:
    - Remote Chroma (primary)
    - Local Persistent Chroma (fallback)
    """

    def __init__(
        self,
        persist_directory: str = "data/vector_db",
        embedding_model_name: str = "all-MiniLM-L6-v2",
        chroma_host: str = "localhost",
        chroma_port: int = 8001,
    ):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self._cloud_timeout = 0.3

        self._local_client = None
        self._remote_client = None
        self._collections: Dict[str, Any] = {}

        logger.info("Loading embedding model: %s", embedding_model_name)
        self.embedding_model = SentenceTransformer(embedding_model_name)

    # --------------------------------------------------
    # Clients (lazy)
    # --------------------------------------------------
    def _get_local_client(self):
        if self._local_client is None:
            self._local_client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                ),
            )
        return self._local_client

    def _get_remote_client(self):
        if self._remote_client is None:
            self._remote_client = chromadb.HttpClient(
                host=self.chroma_host,
                port=self.chroma_port,
            )
        return self._remote_client

    # --------------------------------------------------
    # Cloud availability
    # --------------------------------------------------
    def _cloud_available(self) -> bool:
        try:
            with socket.create_connection(
                (self.chroma_host, self.chroma_port),
                timeout=self._cloud_timeout,
            ):
                return True
        except OSError:
            return False

    # --------------------------------------------------
    # Client selector
    # --------------------------------------------------
    def _active_client(self):
        if self._cloud_available():
            try:
                return self._get_remote_client()
            except Exception as e:
                logger.warning(
                    "Remote Chroma unavailable (%s). Falling back to local.",
                    str(e),
                )
        return self._get_local_client()

    # --------------------------------------------------
    # Collections
    # --------------------------------------------------
    def _get_or_create_collection(self, short_name: str, metadata: Dict[str, Any]):
        full_name = f"india_{short_name}"
        client = self._active_client()

        try:
            return client.get_collection(full_name)
        except Exception:
            return client.create_collection(
                name=full_name,
                metadata=metadata,
            )

    def initialize_collections(self):
        if self._collections:
            return self._collections

        configs = {
            "spiritual_sites": {"type": "entity"},
            "festivals": {"type": "entity"},
            "crowd_patterns": {"type": "entity"},
            "homestays": {"type": "entity"},
            "treks": {"type": "entity"},
            "cuisines": {"type": "entity"},
            "wellness": {"type": "entity"},
            "eco_tips": {"type": "entity"},
            "emergency_info": {"type": "entity"},
            "shlokas": {"type": "entity"},
            "personas": {"type": "entity"},
            "general": {"type": "document"},
            "trekking": {"type": "document"},
            "cultural": {"type": "document"},
            "government": {"type": "document"},
        }

        for name, meta in configs.items():
            self._collections[name] = self._get_or_create_collection(name, meta)
            logger.info("✓ Initialized collection: india_%s", name)

        return self._collections

    # --------------------------------------------------
    # CRUD
    # --------------------------------------------------
    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        collection_name: str = "general",
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        self.initialize_collections()
        collection = self._collections.get(collection_name)
        if not collection:
            return []

        embeddings = self.embedding_model.encode(documents).tolist()
        ids = ids or [str(uuid.uuid4()) for _ in documents]

        cleaned_metadatas = []
        for m in metadatas:
            cleaned_metadatas.append(
                {k: "" if v is None else str(v) for k, v in m.items()}
            )

        collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=cleaned_metadatas,
            ids=ids,
        )
        return ids

    def query(
        self,
        query_text: str,
        collection_name: str = "general",
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        self.initialize_collections()
        collection = self._collections.get(collection_name)
        if not collection:
            return {}

        embedding = self.embedding_model.encode([query_text]).tolist()
        return collection.query(
            query_embeddings=embedding,
            n_results=n_results,
            where=where,
        )

    # --------------------------------------------------
    # Admin
    # --------------------------------------------------
    def delete_collection(self, collection_name: str) -> bool:
        full_name = f"india_{collection_name}"
        client = self._active_client()

        try:
            client.delete_collection(full_name)
            self._collections.pop(collection_name, None)
            return True
        except Exception as e:
            logger.error("Delete failed: %s", e)
            return False

    def reset_collection(self, collection_name: str) -> bool:
        if not self.delete_collection(collection_name):
            return False

        self._collections[collection_name] = self._get_or_create_collection(
            collection_name, {}
        )
        return True
