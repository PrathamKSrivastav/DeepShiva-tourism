"""
UNIFIED RAG INGESTION SCRIPT
Ingests ALL data sources: JSON, PDF, TXT, MD

RUN from backend folder:
python scripts/ingest_all_data.py

Supported file types:
- .json (structured entities)
- .pdf (documents)
- .txt (text files)
- .md (markdown)
"""
import asyncio
import logging
import sys
from pathlib import Path
import shutil

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
# Data structure
# ------------------------------------------------------------------
DATA_DIR = BASE_DIR / "data"
JSON_DIR = DATA_DIR / "json_content"
SPIRITUAL_DIR = DATA_DIR / "spiritual"
VECTOR_DB_DIR = DATA_DIR / "vector_db"
RAG_CONTENT_DIR = DATA_DIR / "rag_content"

# ------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------
def get_file_stats(directory: Path):
    """Get statistics of files in directory"""
    if not directory.exists():
        return {}
    
    stats = {}
    for ext in ['.json', '.pdf', '.txt', '.md']:
        files = list(directory.rglob(f'*{ext}'))
        if files:
            total_size = sum(f.stat().st_size for f in files)
            stats[ext] = {
                'count': len(files),
                'size_mb': total_size / (1024 * 1024),
                'files': [f.name for f in files]
            }
    return stats

def clear_vector_db():
    """Clear entire vector database"""
    if VECTOR_DB_DIR.exists():
        logger.info(f"🗑️  Clearing vector database: {VECTOR_DB_DIR}")
        shutil.rmtree(VECTOR_DB_DIR)
        logger.info("✅ Vector database cleared")
        return True
    return False

def clear_rag_content():
    """Clear managed content (keeps source files)"""
    if RAG_CONTENT_DIR.exists():
        logger.info(f"🗑️  Clearing managed content: {RAG_CONTENT_DIR}")
        shutil.rmtree(RAG_CONTENT_DIR)
        logger.info("✅ Managed content cleared")
        return True
    return False

# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
async def main():
    logger.info("=" * 70)
    logger.info("UNIFIED RAG INGESTION - ALL DATA SOURCES")
    logger.info("=" * 70)

    # ------------------------------------------------------------------
    # Discover data sources
    # ------------------------------------------------------------------
    logger.info("\n📂 Scanning data directories...\n")
    
    all_stats = {}
    
    # JSON files
    if JSON_DIR.exists():
        json_stats = get_file_stats(JSON_DIR)
        if json_stats:
            all_stats['json_content'] = json_stats
            logger.info(f"📁 {JSON_DIR.name}/")
            for ext, data in json_stats.items():
                logger.info(f"   {ext}: {data['count']} files ({data['size_mb']:.1f} MB)")
                for fname in data['files']:
                    logger.info(f"      • {fname}")
    
    # PDFs
    if SPIRITUAL_DIR.exists():
        pdf_stats = get_file_stats(SPIRITUAL_DIR)
        if pdf_stats:
            all_stats['spiritual'] = pdf_stats
            logger.info(f"\n📁 {SPIRITUAL_DIR.name}/")
            for ext, data in pdf_stats.items():
                logger.info(f"   {ext}: {data['count']} files ({data['size_mb']:.1f} MB)")
                for fname in data['files']:
                    logger.info(f"      • {fname}")
    
    # Check if any data found
    if not all_stats:
        logger.warning("\n⚠️  No data files found!")
        logger.info(f"💡 Expected locations:")
        logger.info(f"   • JSON files: {JSON_DIR}")
        logger.info(f"   • PDF files: {SPIRITUAL_DIR}")
        return

    # Count totals
    total_files = sum(
        data['count'] 
        for dir_stats in all_stats.values() 
        for data in dir_stats.values()
    )
    total_size = sum(
        data['size_mb'] 
        for dir_stats in all_stats.values() 
        for data in dir_stats.values()
    )

    logger.info(f"\n📊 TOTAL: {total_files} files ({total_size:.1f} MB)")

    # ------------------------------------------------------------------
    # Clear old data options
    # ------------------------------------------------------------------
    logger.info("\n" + "=" * 70)
    logger.info("CLEAR OLD DATA?")
    logger.info("=" * 70)
    logger.info("1. 🗑️  Clear EVERYTHING (vector DB + managed content)")
    logger.info("2. 🗑️  Clear vector DB only (fresh start, keep registry)")
    logger.info("3. ➕ Keep existing data (ADD new data)")
    logger.info("=" * 70)
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    if choice == "1":
        clear_vector_db()
        clear_rag_content()
        logger.info("✅ Complete reset - starting fresh")
    elif choice == "2":
        clear_vector_db()
        logger.info("✅ Vector DB cleared - will rebuild from scratch")
    else:
        logger.info("➕ Will ADD to existing data")

    # ------------------------------------------------------------------
    # Confirmation
    # ------------------------------------------------------------------
    logger.info("\n" + "=" * 70)
    logger.info(f"⚠️  READY TO INGEST {total_files} FILES")
    logger.info("=" * 70)
    response = input("Continue ingestion? (yes/no): ").strip().lower()
    if response not in {"yes", "y"}:
        logger.info("❌ Ingestion cancelled")
        return

    # ------------------------------------------------------------------
    # Initialize RAG system
    # ------------------------------------------------------------------
    logger.info("\n🚀 Initializing RAG system...")
    
    vector_store = VectorStoreManager(
        persist_directory=str(VECTOR_DB_DIR)
    )
    content_manager = ContentManager(vector_store)
    
    logger.info("✅ RAG system initialized\n")

    # ------------------------------------------------------------------
    # Ingest JSON files
    # ------------------------------------------------------------------
    if 'json_content' in all_stats and JSON_DIR.exists():
        logger.info("=" * 70)
        logger.info("📥 INGESTING JSON FILES")
        logger.info("=" * 70)
        
        json_results = await content_manager.batch_ingest_all_json(
            json_directory=JSON_DIR,
            managed=True
        )
        
        if json_results['processed_files']:
            logger.info(f"\n✅ Processed {len(json_results['processed_files'])} JSON files")
            logger.info(f"📊 Total entities: {json_results['total_entities']}")
            logger.info(f"📊 Total chunks: {json_results['total_chunks']}")
            
            logger.info("\n📁 JSON Files Summary:")
            for f in json_results['processed_files']:
                logger.info(
                    f"  ✓ {f['file']:25s} | "
                    f"{f['entities']:3d} entities | "
                    f"{f['chunks']:3d} chunks | "
                    f"{f['type']}"
                )
        
        if json_results['failed_files']:
            logger.warning(f"\n⚠️ Failed {len(json_results['failed_files'])} files:")
            for f in json_results['failed_files']:
                logger.warning(f"  ✗ {f['file']} → {f['error']}")

    # ------------------------------------------------------------------
    # Ingest PDFs and other documents
    # ------------------------------------------------------------------
    if 'spiritual' in all_stats and SPIRITUAL_DIR.exists():
        logger.info("\n" + "=" * 70)
        logger.info("📥 INGESTING PDF/TEXT FILES")
        logger.info("=" * 70)
        
        pdf_results = await content_manager.batch_process_directory(
            directory_path=SPIRITUAL_DIR,
            content_type="cultural"  # Religion PDFs go to cultural collection
        )
        
        if pdf_results['processed_files']:
            logger.info(f"\n✅ Processed {len(pdf_results['processed_files'])} files")
            logger.info(f"📊 Total chunks: {pdf_results['total_chunks']}")
            
            logger.info("\n📁 PDF/Text Files Summary:")
            for f in pdf_results['processed_files']:
                filename = Path(f['file']).name
                logger.info(
                    f"  ✓ {filename:30s} | "
                    f"{f['chunks']:3d} chunks | "
                    f"{f['collection']}"
                )
        
        if pdf_results['failed_files']:
            logger.warning(f"\n⚠️ Failed {len(pdf_results['failed_files'])} files:")
            for f in pdf_results['failed_files']:
                logger.warning(f"  ✗ {Path(f['file']).name} → {f['error']}")

    # ------------------------------------------------------------------
    # Final statistics
    # ------------------------------------------------------------------
    logger.info("\n" + "=" * 70)
    logger.info("✅ INGESTION COMPLETE")
    logger.info("=" * 70)
    
    stats = content_manager.get_content_statistics()
    
    logger.info(f"\n📊 FINAL SYSTEM STATE")
    logger.info(f"Total files       : {stats['total_files']}")
    logger.info(f"Total JSON files  : {stats['total_json_files']}")
    logger.info(f"Total URLs        : {stats['total_urls']}")
    logger.info(f"Total documents   : {stats['total_documents']}")
    
    # Collection statistics
    collections = stats.get("collections", {})
    if collections:
        logger.info("\n🧠 Vector DB Collections:")
        for name, c in collections.items():
            count = c.get('document_count', 0)
            if count > 0:
                logger.info(f"  • {name:25s} : {count:5d} documents")
    
    # JSON entities by type
    json_entities = stats.get("json_entities_by_type", {})
    if json_entities:
        logger.info("\n📋 JSON Entities by Type:")
        for entity_type, data in json_entities.items():
            logger.info(
                f"  • {entity_type:20s} : "
                f"{data['entities']:3d} entities | "
                f"{data['chunks']:4d} chunks"
            )
    
    # Content type distribution
    content_dist = stats.get("content_types_distribution", {})
    if content_dist:
        logger.info("\n📚 Content Types Distribution:")
        for content_type, chunk_count in content_dist.items():
            logger.info(f"  • {content_type:20s} : {chunk_count:5d} chunks")
    
    logger.info("\n✨ RAG system ready for queries!")
    logger.info("=" * 70)


# ------------------------------------------------------------------
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⚠️ Interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}", exc_info=True)
