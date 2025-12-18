'''
FULLY CORRECTED SPECIAL JSON INGESTION SCRIPT
Fixed both parameter name (documents) AND JSON key names
'''

import asyncio
import logging
import sys
import json
from pathlib import Path

# Resolve backend root
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from rag.vector_store import VectorStoreManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Paths
DATA_DIR = BASE_DIR / "data" / "json_content"
VECTOR_DB_DIR = BASE_DIR / "data" / "vector_db"

# ✅ CORRECTED FILE MAPPINGS with actual JSON keys
FILE_MAPPINGS = {
    "shlokas.json": ("cultural", "shlokas"),
    "festivals.json": ("cultural", "festivals"),
    "crowdPatterns.json": ("general", "patterns"),  # ← FIXED: was "crowdPatterns"
    "wellness.json": ("cultural", "routines"),  # ← FIXED: was "wellnessPractices"
    "emergencyInfo.json": ("general", "emergencies"),  # ← FIXED: was "emergencyContacts"
    "ecoTips.json": ("general", "tips"),  # ← FIXED: was "ecoTips"
    "cuisines.json": ("general", "cuisines"),  # ← FIXED: was "regionalCuisines"
    "treks.json": ("trekking", "treks")
}


def format_shloka(item):
    return f"""
Shloka ID: {item.get('id', 'unknown')}
Category: {item.get('category', 'general')}
Sanskrit: {item.get('sanskrit', '')}
Transliteration: {item.get('transliteration', '')}
Meaning (English): {item.get('meaning_english', '')}
Meaning (Hindi): {item.get('meaning_hindi', '')}
Context: {item.get('use_context', '')}
Quick Version: {item.get('quick_version', '')}
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
Best Places to Experience: {', '.join(item.get('best_places_to_experience', []))}
Travel Tips: {item.get('travel_tips', '')}
""".strip()


def format_crowd_pattern(item):
    return f"""
Location: {item.get('name', 'unknown')}
Place ID: {item.get('place_id', 'unknown')}
State: {item.get('state', '')}
Peak Months: {', '.join(item.get('peak_months', []))}
Off Season: {', '.join(item.get('off_season_months', []))}
Weekend Spike: {item.get('weekend_spike', 'unknown')}
Festival Spikes: {', '.join(item.get('festival_spikes', []))}
Wait Time Low: {item.get('typical_wait_time_low', 'unknown')}
Wait Time High: {item.get('typical_wait_time_high', 'unknown')}
Crowd Summary: {item.get('crowd_level_summary', '')}
Avoid Mistake: {item.get('avoid_common_mistake', '')}
""".strip()


def format_wellness(item):
    return f"""
Wellness Practice: {item.get('name', 'unknown')}
Type: {item.get('routine_type', 'unknown')}
Category: {item.get('category', '')}
Target Mood: {item.get('target_mood', '')}
Duration: {item.get('duration_minutes', 0)} minutes
Difficulty: {item.get('difficulty', 'beginner')}
Effort Level: {item.get('effort_level', '')}
Steps: {'; '.join(item.get('steps', [])[:3])}... (see full details)
Safety Notes: {item.get('safety_notes', '')}
Avoid Mistake: {item.get('avoid_common_mistake', '')}
""".strip()


def format_emergency_info(item):
    return f"""
Emergency Type: {item.get('category', 'unknown')}
Region: {item.get('region_specific', 'All India')}
Description: {item.get('description', '')}
Immediate Steps: {'; '.join(item.get('immediate_steps', [])[:3])}
Who to Contact: {', '.join(item.get('who_to_contact', []))}
Prevention Tips: {item.get('prevention_tips', '')}
Avoid Mistake: {item.get('avoid_common_mistake', '')}
""".strip()


def format_eco_tip(item):
    return f"""
Eco Tip: {item.get('context', 'unknown')}
Category: {item.get('category', 'general')}
Region: {item.get('region_specific', 'All India')}
Quick Version: {item.get('quick_version', '')}
Full Tip: {item.get('tip', '')}
Impact: {item.get('impact', '')}
Explanation: {item.get('explanation', '')}
Avoid Mistake: {item.get('avoid_common_mistake', '')}
Money Saved: {item.get('estimated_money_saved', 'N/A')}
""".strip()


def format_cuisine(item):
    return f"""
Cuisine/Dish: {item.get('dish_name', 'unknown')}
State: {item.get('state', 'unknown')}
Region: {item.get('region_specific', '')}
Type: {item.get('veg_or_nonveg', '')}
Description: {item.get('description', '')}
When to Try: {item.get('when_to_try', '')}
Recommended Places: {item.get('recommended_places_generic', '')}
Avoid Mistake: {item.get('avoid_common_mistake', '')}
""".strip()


def format_trek(item):
    return f"""
Trek: {item.get('name', 'unknown')}
Location: {item.get('location', 'unknown')}
State: {item.get('state', '')}
Difficulty: {item.get('difficulty', 'moderate')}
Duration: {item.get('duration_days', 0)} days
Distance: {item.get('distance_km', 0)} km
Max Altitude: {item.get('max_altitude_m', 0)} meters
Best Season: {item.get('best_season', '')}
Description: {item.get('description', '')}
Highlights: {', '.join(item.get('highlights', []))}
Permits Required: {item.get('permits_required', 'No')}
Fitness Level: {item.get('fitness_level_required', 'moderate')}
""".strip()


# Format dispatcher
FORMATTERS = {
    "shlokas.json": format_shloka,
    "festivals.json": format_festival,
    "crowdPatterns.json": format_crowd_pattern,
    "wellness.json": format_wellness,
    "emergencyInfo.json": format_emergency_info,
    "ecoTips.json": format_eco_tip,
    "cuisines.json": format_cuisine,
    "treks.json": format_trek
}


def main():
    logger.info("="*70)
    logger.info("📥 FULLY CORRECTED SPECIAL JSON INGESTION")
    logger.info("="*70)

    # Initialize vector store
    vector_store = VectorStoreManager(
        persist_directory=str(VECTOR_DB_DIR),
        embedding_model_name="all-MiniLM-L6-v2"
    )

    # Check which files exist
    files_to_process = []
    for filename, (collection, key) in FILE_MAPPINGS.items():
        filepath = DATA_DIR / filename
        if filepath.exists():
            logger.info(f"✅ Found: {filename} (key: '{key}')")
            files_to_process.append((filepath, filename, collection, key))
        else:
            logger.warning(f"⚠️  Missing: {filename}")

    if not files_to_process:
        logger.error("❌ No special JSON files found!")
        return

    logger.info(f"\n🚀 Processing {len(files_to_process)} special JSON files...\n")

    success_count = 0
    error_count = 0
    errors = []
    total_items = 0

    for filepath, filename, collection, key in files_to_process:
        try:
            # Load JSON
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Extract items using CORRECT key
            items = data.get(key, [])
            if not items:
                logger.warning(f"⚠️  No items found in {filename} under key '{key}'")
                logger.info(f"   Available keys: {list(data.keys())}")
                continue

            # Format items
            formatter = FORMATTERS.get(filename)
            if not formatter:
                logger.error(f"❌ No formatter for {filename}")
                continue

            documents = [formatter(item) for item in items]
            metadatas = [
                {
                    "source_file": filename,
                    "entity_id": item.get('id', f"{filename}_{i}"),
                    "content_type": key,
                    "source_type": "json",
                    **{k: v for k, v in item.items() if isinstance(v, (str, int, float, bool))}
                }
                for i, item in enumerate(items)
            ]

            logger.info(f"📄 Processing {filename}: {len(items)} items → {collection}")

            # Add to vector store
            vector_store.add_documents(
                documents=documents,
                metadatas=metadatas,
                collection_name=collection
            )

            success_count += 1
            total_items += len(items)
            logger.info(f"✅ Successfully added {len(items)} items from {filename}")

        except Exception as e:
            error_count += 1
            errors.append((filename, str(e)))
            logger.error(f"❌ Failed to add {filename}: {e}")

    # Summary
    logger.info("\n" + "="*70)
    logger.info("📊 INGESTION SUMMARY")
    logger.info("="*70)
    logger.info(f"✅ Success: {success_count} files")
    logger.info(f"📦 Total Items: {total_items}")
    logger.info(f"❌ Errors: {error_count}")

    if errors:
        logger.info("\n⚠️  ERRORS:")
        for filename, error in errors:
            logger.error(f"   ✗ {filename:20s} → {error}")

    logger.info("="*70)
    logger.info("✨ SPECIAL JSON INGESTION COMPLETE!")
    logger.info("="*70)

    if success_count > 0:
        logger.info("\n🎉 SUCCESS! Now test queries:")
        logger.info("   • 'tell me about gayatri mantra'")
        logger.info("   • 'when is kumbh mela?'")
        logger.info("   • 'bhagavad gita karma yoga verse'")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}", exc_info=True)