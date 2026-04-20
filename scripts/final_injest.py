"""
MASTER RESET & RE-INGESTION SCRIPT (FIXED - Includes Mantra Names!)
Clears both Qdrant Cloud and ChromaDB, then re-ingests ALL data

FIXED: format_shloka() now includes quick_version field with mantra names
"""

import asyncio
import logging
import sys
import json
import shutil
from pathlib import Path
from dotenv import load_dotenv
import os

# ------------------------------------------------------------------
# Setup
# ------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
load_dotenv()

from rag.vector_store import VectorStoreManager
from rag.content_manager import ContentManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------
DATA_DIR = BASE_DIR / "data"
JSON_DIR = DATA_DIR / "json_content"
SPIRITUAL_DIR = DATA_DIR / "spiritual"
VECTOR_DB_DIR = DATA_DIR / "vector_db"
RAG_CONTENT_DIR = DATA_DIR / "rag_content"

# ------------------------------------------------------------------
# Special JSON Configuration
# ------------------------------------------------------------------
SPECIAL_JSON_MAPPINGS = {
    "shlokas.json": ("cultural", "shlokas"),
    "festivals.json": ("cultural", "festivals"),
    "crowdPatterns.json": ("general", "patterns"),
    "wellness.json": ("cultural", "routines"),
    "emergencyInfo.json": ("general", "emergencies"),
    "ecoTips.json": ("general", "tips"),
    "cuisines.json": ("general", "cuisines"),
    "treks.json": ("trekking", "treks")
}

# ------------------------------------------------------------------
# Formatters for Special JSONs - FIXED VERSION
# ------------------------------------------------------------------
# ------------------------------------------------------------------
# Formatters for Special JSONs - ENHANCED VERSION
# ------------------------------------------------------------------
def format_shloka(item):
    """FIXED: Now includes quick_version with mantra name"""
    return f"""
{item.get('quick_version', 'Vedic Shloka')}
Shloka ID: {item.get('id', 'unknown')}
Category: {item.get('category', 'general')}
Sanskrit: {item.get('sanskrit', '')}
Transliteration: {item.get('transliteration', '')}
Meaning (English): {item.get('meaning_english', '')}
Meaning (Hindi): {item.get('meaning_hindi', '')}
Context: {item.get('use_context', '')}
Common Mistake to Avoid: {item.get('avoid_common_mistake', '')}
""".strip()

def format_festival(item):
    return f"""
Festival: {item.get('name', 'unknown')}
ID: {item.get('id', 'unknown')}
Region: {item.get('region', 'unknown')}
Type: {item.get('type', 'religious')}
Month: {item.get('month', 'varies')}
Duration: {item.get('duration_days', 1)} days
Description: {item.get('description', '')}
Significance: {item.get('significance', '')}
Main Rituals: {', '.join(item.get('main_rituals', []))}
Best Places: {', '.join(item.get('best_places_to_experience', []))}
""".strip()

def format_crowd_pattern(item):
    return f"""
Location: {item.get('name', 'unknown')}
Place ID: {item.get('place_id', 'unknown')}
State: {item.get('state', '')}
Peak Months: {', '.join(item.get('peak_months', []))}
Off Season: {', '.join(item.get('off_season_months', []))}
Weekend Spike: {item.get('weekend_spike', 'unknown')}
Crowd Summary: {item.get('crowd_level_summary', '')}
Avoid: {item.get('avoid_common_mistake', '')}
""".strip()

def format_wellness(item):
    return f"""
Practice: {item.get('name', 'unknown')}
Type: {item.get('routine_type', 'unknown')}
Target: {item.get('target_mood', '')}
Duration: {item.get('duration_minutes', 0)} minutes
Difficulty: {item.get('difficulty', 'beginner')}
Steps: {'; '.join(item.get('steps', [])[:3])}...
Safety: {item.get('safety_notes', '')}
""".strip()

def format_emergency(item):
    """ENHANCED: Includes quick_version and avoid_common_mistake"""
    # Convert category to human-readable
    category = item.get('category', 'unknown').replace('_', ' ').title()
    
    # Format steps properly
    steps = item.get('immediate_steps', [])
    if isinstance(steps, list) and len(steps) > 0:
        # Check if it's a single long string or multiple steps
        if len(steps) == 1 and len(steps[0]) > 200:
            steps_formatted = steps[0]
        else:
            steps_formatted = '\n'.join([f"  • {step}" for step in steps[:5]])
    else:
        steps_formatted = 'Not specified'
    
    # Format contacts
    contacts = ', '.join(item.get('who_to_contact', []))
    
    return f"""
{item.get('quick_version', category)}

Emergency Type: {category}
Region: {item.get('region_specific', 'All India')}
Emergency ID: {item.get('id', 'unknown')}

Description:
{item.get('description', 'No description available')}

IMMEDIATE STEPS TO TAKE:
{steps_formatted}

WHO TO CONTACT:
{contacts}

PREVENTION TIPS:
{item.get('prevention_tips', 'No prevention tips available')}

COMMON MISTAKE TO AVOID:
{item.get('avoid_common_mistake', 'Not specified')}
""".strip()

def format_eco_tip(item):
    return f"""
Eco Tip: {item.get('context', 'unknown')}
Category: {item.get('category', 'general')}
Tip: {item.get('tip', '')}
Impact: {item.get('impact', '')}
Explanation: {item.get('explanation', '')}
""".strip()

def format_cuisine(item):
    return f"""
Dish: {item.get('dish_name', 'unknown')}
State: {item.get('state', 'unknown')}
Type: {item.get('veg_or_nonveg', '')}
Description: {item.get('description', '')}
When to Try: {item.get('when_to_try', '')}
Places: {item.get('recommended_places_generic', '')}
""".strip()

def format_trek(item):
    return f"""
Trek: {item.get('name', 'unknown')}
Location: {item.get('location', 'unknown')}
Difficulty: {item.get('difficulty', 'moderate')}
Duration: {item.get('duration_days', 0)} days
Max Altitude: {item.get('max_altitude_m', 0)}m
Best Season: {item.get('best_season', '')}
Description: {item.get('description', '')}
""".strip()


SPECIAL_JSON_FORMATTERS = {
    "shlokas.json": format_shloka,
    "festivals.json": format_festival,
    "crowdPatterns.json": format_crowd_pattern,
    "wellness.json": format_wellness,
    "emergencyInfo.json": format_emergency,
    "ecoTips.json": format_eco_tip,
    "cuisines.json": format_cuisine,
    "treks.json": format_trek
}

# ------------------------------------------------------------------
# Clearing Functions
# ------------------------------------------------------------------
def clear_local_chromadb():
    """Clear local ChromaDB"""
    logger.info("🗑️  STEP 1: Clearing LOCAL ChromaDB...")
    if VECTOR_DB_DIR.exists():
        shutil.rmtree(VECTOR_DB_DIR)
        logger.info("✅ Local ChromaDB cleared")
    else:
        logger.info("⚠️  Local ChromaDB already empty")

def clear_qdrant_cloud(vector_store):
    """Clear all Qdrant Cloud collections"""
    logger.info("\n🗑️  STEP 2: Clearing QDRANT CLOUD...")
    
    if not vector_store._cloud_available():
        logger.warning("⚠️  Qdrant Cloud not available - skipping")
        return False
    
    try:
        collections = ['general', 'cultural', 'trekking', 'government']
        for coll in collections:
            try:
                full_name = f"india_{coll}"
                # Delete collection from Qdrant
                if vector_store.qdrant_client:
                    vector_store.qdrant_client.delete_collection(full_name)
                    logger.info(f"   ✅ Cleared Qdrant: {full_name}")
            except Exception as e:
                logger.warning(f"   ⚠️  Could not clear {coll}: {e}")
        
        logger.info("✅ Qdrant Cloud cleared")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to clear Qdrant: {e}")
        return False

def clear_managed_content():
    """Clear managed content registry"""
    logger.info("\n🗑️  STEP 3: Clearing managed content registry...")
    if RAG_CONTENT_DIR.exists():
        shutil.rmtree(RAG_CONTENT_DIR)
        logger.info("✅ Managed content registry cleared")
    else:
        logger.info("⚠️  Registry already empty")

# ------------------------------------------------------------------
# Ingestion Functions
# ------------------------------------------------------------------
async def ingest_special_jsons(vector_store):
    """Ingest special JSON files (shlokas, festivals, etc.)"""
    logger.info("\n📂 PART 1: Ingesting SPECIAL JSON files...")
    logger.info("   (shlokas, festivals, crowds, wellness, emergency, eco, cuisine, treks)")
    
    success_count = 0
    total_items = 0
    
    for filename, (collection, key) in SPECIAL_JSON_MAPPINGS.items():
        filepath = JSON_DIR / filename
        
        if not filepath.exists():
            logger.warning(f"   ⚠️  Missing: {filename}")
            continue
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            items = data.get(key, [])
            if not items:
                logger.warning(f"   ⚠️  No items in {filename} under key '{key}'")
                continue
            
            formatter = SPECIAL_JSON_FORMATTERS.get(filename)
            if not formatter:
                logger.warning(f"   ⚠️  No formatter for {filename}")
                continue
            
            documents = [formatter(item) for item in items]
            metadatas = [
                {
                    "source_file": filename,
                    "entity_id": item.get('id', f"{filename}_{i}"),
                    "content_type": key,
                    "source_type": "json"
                }
                for i, item in enumerate(items)
            ]
            
            vector_store.add_documents(
                documents=documents,
                metadatas=metadatas,
                collection_name=collection
            )
            
            logger.info(f"   ✅ {filename}: {len(items)} items → {collection}")
            success_count += 1
            total_items += len(items)
            
        except Exception as e:
            logger.error(f"   ❌ {filename}: {e}")
    
    logger.info(f"\n📊 Special JSONs: {success_count} files, {total_items} items")
    return success_count, total_items

async def ingest_standard_jsons(content_manager):
    """Ingest standard JSON files (Buddhist, Hindu, Christian, Jain, Sikh, Islam sites)"""
    logger.info("\n📂 PART 2: Ingesting STANDARD JSON files...")
    logger.info("   (Buddhist, Hindu, Christian, Jain, Sikh, Islam sites)")
    
    if not JSON_DIR.exists():
        logger.warning("   ⚠️ JSON directory not found")
        return 0, 0
    
    # ✅ FIX: Get list of special JSON files to exclude
    special_json_files = set(SPECIAL_JSON_MAPPINGS.keys())
    
    # ✅ FIX: Filter out special JSONs before processing
    all_json_files = list(JSON_DIR.glob('*.json'))
    standard_json_files = [
        f for f in all_json_files 
        if f.name not in special_json_files
    ]
    
    logger.info(f"   Found {len(all_json_files)} total JSON files")
    logger.info(f"   Processing {len(standard_json_files)} standard site files")
    logger.info(f"   Skipping {len(special_json_files)} special files (already processed)")
    
    # ✅ Create a temporary directory with only standard JSONs
    temp_dir = JSON_DIR.parent / "temp_standard_jsons"
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Copy only standard JSONs to temp directory
        for json_file in standard_json_files:
            shutil.copy2(json_file, temp_dir / json_file.name)
        
        # Process only standard JSONs
        results = await content_manager.batch_ingest_all_json(
            json_directory=temp_dir,
            managed=True
        )
        
        if results['processed_files']:
            logger.info(f"\n ✅ Processed {len(results['processed_files'])} files")
            logger.info(f" 📊 Entities: {results['total_entities']}")
            logger.info(f" 📊 Chunks: {results['total_chunks']}")
            return len(results['processed_files']), results['total_entities']
        
        return 0, 0
        
    finally:
        # Cleanup temp directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


async def ingest_pdfs(content_manager):
    """Ingest PDF files (religious texts, yoga, government docs)"""
    logger.info("\n📂 PART 3: Ingesting PDF files...")
    logger.info("   (Religious texts, yoga guides, government documents)")
    
    if not SPIRITUAL_DIR.exists():
        logger.warning("   ⚠️  PDF directory not found")
        return 0, 0
    
    results = await content_manager.batch_process_directory(
        directory_path=SPIRITUAL_DIR,
        content_type="cultural"
    )
    
    if results['processed_files']:
        logger.info(f"\n   ✅ Processed {len(results['processed_files'])} files")
        logger.info(f"   📊 Chunks: {results['total_chunks']}")
        return len(results['processed_files']), results['total_chunks']
    
    return 0, 0

# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
async def main():
    logger.info("="*70)
    logger.info("🔄 MASTER RESET & RE-INGESTION (FIXED VERSION)")
    logger.info("="*70)
    logger.info("This will:")
    logger.info("  1. Clear Qdrant Cloud collections")
    logger.info("  2. Clear local ChromaDB")
    logger.info("  3. Clear managed content registry")
    logger.info("  4. Re-ingest ALL data to BOTH systems")
    logger.info("  ✨ FIX: Shlokas now include mantra names!")
    logger.info("="*70)
    
    # Confirmation
    response = input("\n⚠️  This will DELETE all existing data. Continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        logger.info("❌ Operation cancelled")
        return
    
    # Phase 1: CLEAR EVERYTHING
    logger.info("\n" + "="*70)
    logger.info("PHASE 1: CLEARING ALL DATA")
    logger.info("="*70)
    
    # ✅ FIX: Clear ChromaDB FIRST (before any connection is made)
    clear_local_chromadb()
    clear_managed_content()
    
    # Now initialize vector store ONLY for Qdrant clearing
    qdrant_host = os.getenv("QDRANT_HOST")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    qdrant_dim = int(os.getenv("QDRANT_DIM", 384))
    
    temp_vector_store = VectorStoreManager(
        persist_directory=str(VECTOR_DB_DIR),
        embedding_model_name="all-MiniLM-L6-v2",
        qdrant_host=qdrant_host,
        qdrant_api_key=qdrant_api_key,
        qdrant_dim=qdrant_dim
    )
    
    clear_qdrant_cloud(temp_vector_store)
    
    # Close temporary connection
    del temp_vector_store
    
    # Phase 2: RE-INITIALIZE
    logger.info("\n" + "="*70)
    logger.info("PHASE 2: RE-INITIALIZING VECTOR STORES")
    logger.info("="*70)
    
    vector_store = VectorStoreManager(
        persist_directory=str(VECTOR_DB_DIR),
        embedding_model_name="all-MiniLM-L6-v2",
        qdrant_host=qdrant_host,
        qdrant_api_key=qdrant_api_key,
        qdrant_dim=qdrant_dim
    )
    
    if vector_store._cloud_available():
        logger.info("✅ Qdrant Cloud connected")
    else:
        logger.warning("⚠️  Qdrant Cloud not available - will use ChromaDB only")
    
    logger.info("✅ Local ChromaDB initialized")
    content_manager = ContentManager(vector_store)
    
    # Phase 3: RE-INGEST
    logger.info("\n" + "="*70)
    logger.info("PHASE 3: RE-INGESTING ALL DATA")
    logger.info("="*70)
    
    total_files = 0
    total_items = 0
    
    # Part 1: Special JSONs (shlokas, festivals, etc.)
    special_files, special_items = await ingest_special_jsons(vector_store)
    total_files += special_files
    total_items += special_items
    
    # Part 2: Standard JSONs (sites)
    standard_files, standard_items = await ingest_standard_jsons(content_manager)
    total_files += standard_files
    total_items += standard_items
    
    # Part 3: PDFs
    pdf_files, pdf_chunks = await ingest_pdfs(content_manager)
    total_files += pdf_files
    total_items += pdf_chunks
    
    # Final Summary
    logger.info("\n" + "="*70)
    logger.info("✨ MASTER RESET & RE-INGESTION COMPLETE")
    logger.info("="*70)
    logger.info(f"✅ Total files processed: {total_files}")
    logger.info(f"📦 Total items ingested: {total_items}")
    logger.info(f"🌐 Qdrant Cloud: {'✅ Active' if vector_store._cloud_available() else '❌ Not available'}")
    logger.info(f"💾 Local ChromaDB: ✅ Active")
    
    # Get statistics
    stats = content_manager.get_content_statistics()
    logger.info("\n📊 FINAL DATABASE STATE:")
    collections = stats.get("collections", {})
    for name, c in collections.items():
        count = c.get('document_count', 0)
        if count > 0:
            logger.info(f"   • {name:25s}: {count:5d} documents")
    
    logger.info("="*70)
    logger.info("\n🎉 SUCCESS! Now test these queries:")
    logger.info("   • 'tell me about gayatri mantra'  ← FIXED!")
    logger.info("   • 'bhagavad gita karma yoga verse'")
    logger.info("   • 'when is kumbh mela?'")
    logger.info("   • 'best time visit golden temple'")
    logger.info("="*70)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}", exc_info=True)
