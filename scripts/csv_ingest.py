"""
CSV Ingestion Script for India Tourism Chatbot
FIXED: Batched uploads + proper ChromaDB fallback
Date: December 18, 2025
"""

import asyncio
import logging
import sys
import json
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
import os

# Setup paths (EXACT same as final_injest.py)
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
load_dotenv()

from rag.vector_store import VectorStoreManager
from rag.content_manager import ContentManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================
# Paths
# ============================================================
DATA_DIR = BASE_DIR / "data"
JSON_DIR = DATA_DIR / "json_content"
SPIRITUAL_DIR = DATA_DIR / "spiritual"
VECTOR_DB_DIR = DATA_DIR / "vectordb"
RAG_CONTENT_DIR = DATA_DIR / "rag_content"


# ============================================================
# CSV Formatting Functions
# ============================================================
def format_geeta_verse(row):
    """Format Bhagavad Gita verse"""
    return f"""Bhagavad Gita Chapter {row['chapter']} Verse {row['verse']}

Sanskrit (Original): {row['sanskrit']}

Transliteration: {row['transliteration']}

English Translation: {row['english']}

Hindi Translation: {row['hindi']}

Context: This is verse {row['verse']} from Chapter {row['chapter']} of the Bhagavad Gita, one of the most sacred Hindu scriptures. The Bhagavad Gita is a 700-verse dialogue between Lord Krishna and Arjuna on the battlefield of Kurukshetra, covering profound teachings on dharma (duty), yoga (spiritual practice), karma (action), bhakti (devotion), and moksha (liberation). This scripture is revered across India and is considered essential spiritual knowledge for understanding Hindu philosophy and Indian culture.""".strip()


def format_trek_peak(row):
    """Format trekking peak"""
    state = row['State'].split('(')[0].strip()
    height_m = row['Height in Meters']
    height_ft = int(height_m * 3.28084)

    return f"""Trekking Peak: {row['Name of the Peaks']}

Location: {state}, India
Elevation: {height_m} meters ({height_ft} feet)
Activity Type: {row['Purpose']}

Description: {row['Name of the Peaks']} is a prominent peak located in {state}, India, standing at an impressive elevation of {height_m} meters ({height_ft} feet) above sea level. This peak is officially designated for {row['Purpose'].lower()} activities and attracts adventure enthusiasts from around the world.

{state} is renowned for its spectacular Himalayan terrain, offering some of India's most challenging and rewarding high-altitude trekking and mountaineering experiences. The region provides stunning panoramic views, diverse alpine ecosystems, and the opportunity to experience the raw beauty of the Indian Himalayas.

Adventure Activities: {row['Purpose']}, high-altitude trekking, alpine climbing, glacier navigation
Best Season: Typically May-June and September-October (weather permitting)
Difficulty Level: High altitude - requires proper acclimatization and mountaineering experience
Region: {state} Himalayas""".strip()


# ============================================================
# Helper: Add documents in batches
# ============================================================
def add_documents_batched(vector_store, documents, metadatas, collection_name, batch_size=100):
    """
    Add documents in batches to avoid timeouts
    Handles both Qdrant and ChromaDB properly
    """
    total_docs = len(documents)
    logger.info(f"Adding {total_docs} documents in batches of {batch_size}...")

    for i in range(0, total_docs, batch_size):
        batch_docs = documents[i:i+batch_size]
        batch_metas = metadatas[i:i+batch_size]

        try:
            # Try to add this batch
            vector_store.add_documents(
                documents=batch_docs,
                metadatas=batch_metas,
                collection_name=collection_name
            )
            logger.info(f"  ✅ Batch {i//batch_size + 1}/{(total_docs-1)//batch_size + 1}: Added {len(batch_docs)} docs")

        except Exception as e:
            logger.error(f"  ❌ Batch {i//batch_size + 1} failed: {e}")

            # Try ChromaDB fallback for this batch
            try:
                logger.info(f"  🔄 Retrying batch with ChromaDB...")
                collection = vector_store.collections.get(collection_name)

                if collection:
                    # Generate embeddings
                    embeddings = vector_store.embedding_model.encode(batch_docs).tolist()

                    # Generate IDs
                    import uuid
                    ids = [str(uuid.uuid4()) for _ in batch_docs]

                    # Clean metadata
                    cleaned_metas = []
                    for meta in batch_metas:
                        cleaned = {}
                        for k, v in meta.items():
                            if isinstance(v, (str, int, float, bool)):
                                cleaned[k] = v
                            elif v is None:
                                cleaned[k] = ''
                            else:
                                cleaned[k] = str(v)
                        cleaned_metas.append(cleaned)

                    # Add to ChromaDB
                    collection.add(
                        embeddings=embeddings,
                        documents=batch_docs,
                        metadatas=cleaned_metas,
                        ids=ids
                    )
                    logger.info(f"  ✅ ChromaDB fallback succeeded for batch {i//batch_size + 1}")
                else:
                    logger.error(f"  ❌ Collection '{collection_name}' not found in ChromaDB")

            except Exception as e2:
                logger.error(f"  ❌ ChromaDB fallback also failed: {e2}")
                raise


# ============================================================
# CSV Ingestion Functions
# ============================================================
async def ingest_geeta_csv(vector_store):
    """Ingest Bhagavad Gita CSV with batching"""
    logger.info("PART 1: Ingesting Bhagavad Gita CSV...")

    csv_path = SPIRITUAL_DIR / "geeta_dataset.csv"

    if not csv_path.exists():
        logger.warning(f"❌ Missing {csv_path.name}")
        logger.info(f"   Expected location: {csv_path}")
        return 0, 0

    try:
        # Read CSV
        df = pd.read_csv(csv_path)
        logger.info(f"✅ Found {len(df)} verses in {csv_path.name}")

        # Format all verses
        documents = []
        metadatas = []

        for idx, row in df.iterrows():
            content = format_geeta_verse(row)
            documents.append(content)

            metadata = {
                'source_file': csv_path.name,
                'entity_id': f"BG_{row['chapter']}_{row['verse']}",
                'content_type': 'spiritual_text',
                'source_type': 'csv',
                'chapter': int(row['chapter']),
                'verse': int(row['verse']),
                'reference': f"BG {row['chapter']}.{row['verse']}",
                'scripture': 'Bhagavad Gita',
                'category': 'hinduism'
            }
            metadatas.append(metadata)

        # Add to vector store in batches
        add_documents_batched(vector_store, documents, metadatas, "cultural", batch_size=100)

        logger.info(f"🎉 {csv_path.name}: {len(documents)} verses → cultural collection")
        return 1, len(documents)

    except Exception as e:
        logger.error(f"❌ {csv_path.name}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 0, 0


async def ingest_treks_csv(vector_store):
    """Ingest Trekking Peaks CSV with batching"""
    logger.info("PART 2: Ingesting Trekking Peaks CSV...")

    csv_path = SPIRITUAL_DIR / "New-Treks-List-2022.csv"

    if not csv_path.exists():
        logger.warning(f"❌ Missing {csv_path.name}")
        logger.info(f"   Expected location: {csv_path}")
        logger.info(f"   Please place the CSV file in: {SPIRITUAL_DIR}")
        return 0, 0

    try:
        # Read CSV
        df = pd.read_csv(csv_path)
        logger.info(f"✅ Found {len(df)} peaks in {csv_path.name}")

        # Format all peaks
        documents = []
        metadatas = []

        for idx, row in df.iterrows():
            content = format_trek_peak(row)
            documents.append(content)

            state = row['State'].split('(')[0].strip()
            metadata = {
                'source_file': csv_path.name,
                'entity_id': f"PEAK_{idx}_{row['Name of the Peaks'].replace(' ', '_')}",
                'content_type': 'trekking_peak',
                'source_type': 'csv',
                'peak_name': row['Name of the Peaks'],
                'state': state,
                'height_meters': int(row['Height in Meters']),
                'purpose': row['Purpose'],
                'region': state.lower().replace(' ', '_')
            }
            metadatas.append(metadata)

        # Add to vector store in batches
        add_documents_batched(vector_store, documents, metadatas, "trekking", batch_size=100)

        logger.info(f"🎉 {csv_path.name}: {len(documents)} peaks → trekking collection")
        return 1, len(documents)

    except Exception as e:
        logger.error(f"❌ {csv_path.name}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 0, 0


# ============================================================
# Main Function
# ============================================================
async def main():
    logger.info("=" * 70)
    logger.info("CSV INGESTION SCRIPT - BATCHED VERSION")
    logger.info("=" * 70)
    logger.info("This will:")
    logger.info("  1. Ingest Bhagavad Gita verses (701 verses)")
    logger.info("  2. Ingest Trekking Peaks (123 peaks)")
    logger.info("  3. Add to existing Qdrant/ChromaDB collections")
    logger.info("  4. Upload in batches of 100 to avoid timeouts")
    logger.info("=" * 70)

    # Confirmation
    response = input("Continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        logger.info("Operation cancelled")
        return

    # Initialize vector store
    logger.info("=" * 70)
    logger.info("INITIALIZING VECTOR STORES")
    logger.info("=" * 70)

    qdrant_host = os.getenv("QDRANT_HOST")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    qdrant_dim = int(os.getenv("QDRANT_DIM", "384"))

    vector_store = VectorStoreManager(
        persist_directory=str(VECTOR_DB_DIR),
        embedding_model_name="all-MiniLM-L6-v2",
        qdrant_host=qdrant_host,
        qdrant_api_key=qdrant_api_key,
        qdrant_dim=qdrant_dim
    )

    # Check connectivity
    if vector_store._cloud_available():
        logger.info("✅ Qdrant Cloud connected")
    else:
        logger.warning("⚠️ Qdrant Cloud not available - will use ChromaDB only")

    logger.info("✅ Local ChromaDB initialized")

    # Initialize content manager
    content_manager = ContentManager(vector_store)

    # Ingest CSVs
    logger.info("=" * 70)
    logger.info("INGESTING CSV DATA")
    logger.info("=" * 70)

    total_files = 0
    total_items = 0

    # Part 1: Bhagavad Gita
    geeta_files, geeta_items = await ingest_geeta_csv(vector_store)
    total_files += geeta_files
    total_items += geeta_items

    # Part 2: Trekking Peaks
    treks_files, treks_items = await ingest_treks_csv(vector_store)
    total_files += treks_files
    total_items += treks_items

    # Final summary
    logger.info("=" * 70)
    logger.info("CSV INGESTION COMPLETE")
    logger.info("=" * 70)
    logger.info(f"✅ Total files processed: {total_files}")
    logger.info(f"✅ Total items ingested: {total_items}")
    logger.info(f"✅ Qdrant Cloud: {'Active' if vector_store._cloud_available() else 'Not available'}")
    logger.info(f"✅ Local ChromaDB: Active")

    # Get statistics
    try:
        stats = content_manager.get_content_statistics()
        logger.info("\n" + "=" * 70)
        logger.info("FINAL DATABASE STATE")
        logger.info("=" * 70)
        collections = stats.get('collections', {})
        for name, c in collections.items():
            count = c.get('document_count', 0)
            if count > 0:
                logger.info(f"  {name:25s} {count:5d} documents")
    except Exception as e:
        logger.warning(f"Could not fetch statistics: {e}")

    logger.info("=" * 70)
    logger.info("✅ SUCCESS! Now test these queries:")
    logger.info("  • 'What does Krishna say about karma in Bhagavad Gita?'")
    logger.info("  • 'Bhagavad Gita Chapter 2 Verse 47'")
    logger.info("  • 'Show me trekking peaks in Uttarakhand'")
    logger.info("  • 'Which are the highest peaks for mountaineering?'")
    logger.info("=" * 70)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)