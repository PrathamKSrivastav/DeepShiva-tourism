"""
CLEAN RAG INGESTION — idempotent full rebuild of Qdrant + local Chroma.

Unlike ingest_all_data.py, this script wipes Qdrant Cloud collections
before re-ingesting, so running it twice gives the same final state
(no duplicate points).

Run from backend/ folder:
    python scripts/clean_ingest.py

Requires backend/.env with QDRANT_HOST, QDRANT_API_KEY, QDRANT_DIM.
"""
import asyncio
import logging
import os
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv

# Resolve backend root
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

load_dotenv()

from qdrant_client import QdrantClient

from rag.content_manager import ContentManager
from rag.vector_store import VectorStoreManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = BASE_DIR / "data"
JSON_DIR = DATA_DIR / "json_content"
SPIRITUAL_DIR = DATA_DIR / "spiritual"
VECTOR_DB_DIR = DATA_DIR / "vector_db"
RAG_CONTENT_DIR = DATA_DIR / "rag_content"

# Collections the app uses. india_spiritual intentionally omitted —
# no persona references it (see rag/retriever.py persona_strategies).
TARGET_COLLECTIONS = ["cultural", "trekking", "government", "general"]


def wipe_qdrant() -> None:
    """Delete india_* collections via a bare QdrantClient so we don't
    hold any Chroma file handles during the subsequent local rmtree."""
    host = os.getenv("QDRANT_HOST")
    api_key = os.getenv("QDRANT_API_KEY")
    if not (host and api_key):
        logger.warning("QDRANT_HOST/QDRANT_API_KEY missing — skipping cloud wipe")
        return
    client = QdrantClient(url=host, api_key=api_key, prefer_grpc=False)
    try:
        existing = {c.name for c in client.get_collections().collections}
    except Exception as e:
        logger.warning(f"Qdrant unreachable — skipping cloud wipe ({e})")
        return
    for short in TARGET_COLLECTIONS:
        full = f"india_{short}"
        if full in existing:
            logger.info(f"Deleting Qdrant collection: {full}")
            client.delete_collection(collection_name=full)
    client.close()


def wipe_local() -> None:
    for path in (VECTOR_DB_DIR, RAG_CONTENT_DIR):
        if path.exists():
            logger.info(f"Deleting local dir: {path}")
            shutil.rmtree(path)


async def main() -> None:
    logger.info("=" * 60)
    logger.info("CLEAN INGEST — this will WIPE Qdrant Cloud collections")
    logger.info(f"  Qdrant host: {os.getenv('QDRANT_HOST')}")
    logger.info(f"  Collections to wipe: {['india_' + c for c in TARGET_COLLECTIONS]}")
    logger.info("=" * 60)
    if input("Type 'wipe' to continue, anything else to abort: ").strip() != "wipe":
        logger.info("Aborted.")
        return

    # 1. Wipe Qdrant + local FS. wipe_qdrant uses a bare QdrantClient
    #    (not VectorStoreManager) so no Chroma SQLite handles are open
    #    when wipe_local does shutil.rmtree — avoids Windows file-lock
    #    errors on chroma.sqlite3.
    wipe_qdrant()
    wipe_local()

    # 2. Rebuild a fresh VectorStoreManager so it recreates Qdrant
    #    collections + a clean local Chroma on disk.
    vs = VectorStoreManager(
        persist_directory=str(VECTOR_DB_DIR),
        embedding_model_name="all-MiniLM-L6-v2",
        qdrant_host=os.getenv("QDRANT_HOST"),
        qdrant_api_key=os.getenv("QDRANT_API_KEY"),
        qdrant_dim=int(os.getenv("QDRANT_DIM", 384)),
    )
    cm = ContentManager(vs)

    # 3. Ingest JSON
    if JSON_DIR.exists():
        logger.info("Ingesting JSON files")
        res = await cm.batch_ingest_all_json(json_directory=JSON_DIR, managed=True)
        logger.info(f"  {len(res.get('processed_files', []))} files, "
                    f"{res.get('total_entities', 0)} entities, "
                    f"{res.get('total_chunks', 0)} chunks")
    else:
        logger.warning(f"JSON dir missing: {JSON_DIR}")

    # 4. Ingest PDFs — religion PDFs go into 'cultural' (see
    #    existing ingest_all_data.py for the rationale).
    if SPIRITUAL_DIR.exists():
        logger.info("Ingesting PDF/text files from data/spiritual")
        res = await cm.batch_process_directory(
            directory_path=SPIRITUAL_DIR,
            content_type="cultural",
        )
        logger.info(f"  {len(res.get('processed_files', []))} files, "
                    f"{res.get('total_chunks', 0)} chunks")
    else:
        logger.warning(f"Spiritual dir missing: {SPIRITUAL_DIR}")

    # 5. Final counts from Qdrant
    logger.info("=" * 60)
    logger.info("FINAL QDRANT STATE")
    logger.info("=" * 60)
    if vs._cloud_available():
        for short in TARGET_COLLECTIONS:
            full = f"india_{short}"
            try:
                info = vs.qdrant_client.get_collection(collection_name=full)
                logger.info(f"  {full}: {info.points_count} points")
            except Exception as e:
                logger.info(f"  {full}: (not present — {str(e)[:60]})")
    else:
        logger.warning("Qdrant unreachable at end — counts unavailable")


if __name__ == "__main__":
    asyncio.run(main())
