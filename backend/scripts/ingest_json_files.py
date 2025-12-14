# scripts/ingest_json_files.py

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from rag.vector_store import VectorStoreManager
from rag.content_manager import ContentManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main ingestion function"""
    logger.info("=" * 70)
    logger.info("JSON RAG INGESTION SCRIPT - INTEGRATED VERSION")
    logger.info("=" * 70)
    
    # Initialize components
    logger.info("Initializing vector store and content manager...")
    vector_store = VectorStoreManager(persist_directory="data/vector_db")
    content_manager = ContentManager(vector_store)
    
    # Path to your JSON files - UPDATE THIS PATH
    json_dir = Path("data/json_content")  # ← CHANGE THIS to your folder
    
    # Alternative: Use command line argument
    if len(sys.argv) > 1:
        json_dir = Path(sys.argv[1])
    
    if not json_dir.exists():
        logger.error(f"❌ JSON directory not found: {json_dir}")
        logger.info("Creating directory...")
        json_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Created directory. Please add your JSON files to: {json_dir}")
        return
    
    # Check what files exist
    json_files = list(json_dir.glob('*.json'))
    logger.info(f"\n📂 Found {len(json_files)} JSON files:")
    for f in json_files:
        logger.info(f"   • {f.name} ({f.stat().st_size / 1024:.1f} KB)")
    
    if not json_files:
        logger.error("❌ No JSON files found. Exiting.")
        return
    
    # Ask for confirmation
    logger.info(f"\n⚠️  About to process {len(json_files)} files")
    response = input("Continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        logger.info("Cancelled by user.")
        return
    
    # Batch ingest
    logger.info("\n" + "=" * 70)
    logger.info("🚀 Starting batch ingestion...")
    logger.info("=" * 70 + "\n")
    
    results = await content_manager.batch_ingest_all_json(
        json_directory=json_dir,
        managed=True  # Copy files to managed location
    )
    
    # Report results
    logger.info("\n" + "=" * 70)
    logger.info("✅ INGESTION COMPLETE")
    logger.info("=" * 70)
    logger.info(f"✅ Processed files: {len(results['processed_files'])}")
    logger.info(f"❌ Failed files: {len(results['failed_files'])}")
    logger.info(f"📦 Total entities: {results['total_entities']}")
    logger.info(f"🔢 Total chunks: {results['total_chunks']}")
    logger.info(f"⏱️  Processing time: {results['processing_time']}")
    
    if results['processed_files']:
        logger.info("\n📁 Successfully processed:")
        for file_info in results['processed_files']:
            logger.info(
                f"   ✓ {file_info['file']:25s} → "
                f"{file_info['entities']:3d} entities → "
                f"{file_info['chunks']:3d} chunks  "
                f"({file_info['type']})"
            )
    
    if results['failed_files']:
        logger.warning("\n⚠️  Failed files:")
        for fail_info in results['failed_files']:
            logger.warning(f"   ✗ {fail_info['file']}: {fail_info['error']}")
    
    # Get comprehensive stats
    logger.info("\n" + "=" * 70)
    logger.info("📊 SYSTEM STATISTICS")
    logger.info("=" * 70)
    
    stats = content_manager.get_content_statistics()
    
    logger.info(f"Total content in system:")
    logger.info(f"  • PDF files: {stats['total_files']}")
    logger.info(f"  • Web pages: {stats['total_urls']}")
    logger.info(f"  • JSON files: {stats['total_json_files']}")
    logger.info(f"  • Total documents: {stats['total_documents']}")
    
    if stats.get('json_entities_by_type'):
        logger.info("\nJSON entities by type:")
        for entity_type, type_stats in stats['json_entities_by_type'].items():
            logger.info(
                f"  • {entity_type:20s}: "
                f"{type_stats['files']} files, "
                f"{type_stats['entities']} entities, "
                f"{type_stats['chunks']} chunks"
            )
    
    # Vector store stats
    vector_stats = stats.get('collections', {})
    if vector_stats:
        logger.info("\nVector store collections:")
        for col_name, col_stats in vector_stats.items():
            doc_count = col_stats.get('document_count', 0)
            if doc_count > 0:
                logger.info(f"  • {col_name:25s}: {doc_count:4d} documents")
    
    logger.info("\n" + "=" * 70)
    logger.info("✨ Your RAG system is ready!")
    logger.info("=" * 70)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Interrupted by user")
    except Exception as e:
        logger.error(f"\n\n❌ Fatal error: {str(e)}", exc_info=True)
