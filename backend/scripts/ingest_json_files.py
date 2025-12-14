"""
RUN from the backend folder only

python scripts/ingest_json_files.py
as the content manager takes the working directory and that might result in creating more new data folders
"""
import asyncio
import logging
import sys
from pathlib import Path

# ------------------------------------------------------------------
# Resolve backend root safely
# ------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from rag.vector_store import VectorStoreManager
from rag.content_manager import ContentManager

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Fixed data layout (EXISTING folders only)
# ------------------------------------------------------------------
DATA_DIR = BASE_DIR / "data"
JSON_SOURCE_DIR = DATA_DIR / "json_content"
VECTOR_DB_DIR = DATA_DIR / "vector_db"
RAG_CONTENT_DIR = DATA_DIR / "rag_content"

# ------------------------------------------------------------------
# Validation helpers
# ------------------------------------------------------------------
def validate_directory(path: Path, name: str):
    if not path.exists() or not path.is_dir():
        raise RuntimeError(
            f"❌ Required {name} directory not found: {path}"
        )

# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
async def main():
    logger.info("=" * 70)
    logger.info("JSON RAG INGESTION (EXISTING DATA MODE)")
    logger.info("=" * 70)

    # ------------------------------------------------------------------
    # Validate existing structure
    # ------------------------------------------------------------------
    validate_directory(DATA_DIR, "data")
    validate_directory(JSON_SOURCE_DIR, "json_content")
    validate_directory(VECTOR_DB_DIR, "vector_db")
    validate_directory(RAG_CONTENT_DIR, "rag_content")

    logger.info("✅ Existing data structure validated")

    # ------------------------------------------------------------------
    # Initialize components (reuse existing DB)
    # ------------------------------------------------------------------
    vector_store = VectorStoreManager(
        persist_directory=str(VECTOR_DB_DIR)
    )
    content_manager = ContentManager(vector_store)

    # ------------------------------------------------------------------
    # Discover JSON files
    # ------------------------------------------------------------------
    json_files = list(JSON_SOURCE_DIR.glob("*.json"))

    logger.info(f"\n📂 JSON source directory: {JSON_SOURCE_DIR}")
    logger.info(f"📄 Found {len(json_files)} JSON files")

    if not json_files:
        logger.warning("⚠️  No JSON files found. Nothing to ingest.")
        return

    for f in json_files:
        logger.info(f"   • {f.name} ({f.stat().st_size / 1024:.1f} KB)")

    # ------------------------------------------------------------------
    # Confirmation
    # ------------------------------------------------------------------
    logger.info("\n⚠️  This will ADD data to the existing vector DB")
    response = input("Continue ingestion? (yes/no): ").strip().lower()
    if response not in {"yes", "y"}:
        logger.info("❌ Ingestion cancelled")
        return

    # ------------------------------------------------------------------
    # Ingest (NO structure creation)
    # ------------------------------------------------------------------
    logger.info("\n🚀 Starting ingestion...\n")

    results = await content_manager.batch_ingest_all_json(
        json_directory=JSON_SOURCE_DIR,
        managed=True  # Uses existing rag_content/json_files
    )

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------
    logger.info("\n" + "=" * 70)
    logger.info("✅ INGESTION COMPLETE")
    logger.info("=" * 70)

    logger.info(f"Processed files : {len(results['processed_files'])}")
    logger.info(f"Failed files    : {len(results['failed_files'])}")
    logger.info(f"Total entities  : {results['total_entities']}")
    logger.info(f"Total chunks    : {results['total_chunks']}")
    logger.info(f"Time taken      : {results['processing_time']}")

    if results["processed_files"]:
        logger.info("\n📁 Successfully ingested:")
        for f in results["processed_files"]:
            logger.info(
                f"  ✓ {f['file']:20s} | "
                f"{f['entities']:3d} entities | "
                f"{f['chunks']:3d} chunks"
            )

    if results["failed_files"]:
        logger.warning("\n⚠️ Failed files:")
        for f in results["failed_files"]:
            logger.warning(f"  ✗ {f['file']} → {f['error']}")

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------
    stats = content_manager.get_content_statistics()

    logger.info("\n📊 CURRENT SYSTEM STATE")
    logger.info(f"JSON files      : {stats['total_json_files']}")
    logger.info(f"Total documents : {stats['total_documents']}")

    collections = stats.get("collections", {})
    if collections:
        logger.info("\n🧠 Vector DB collections:")
        for name, c in collections.items():
            if c.get("document_count", 0) > 0:
                logger.info(f"  • {name:25s} : {c['document_count']} docs")

    logger.info("\n✨ Existing RAG system successfully updated")
    logger.info("=" * 70)


# ------------------------------------------------------------------
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⚠️ Interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}", exc_info=True)
