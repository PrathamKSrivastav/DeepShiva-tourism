"""
DEBUG SCRIPT: Check Vector Database Contents
Verifies what's actually stored in Qdrant and ChromaDB
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
load_dotenv()

from rag.vector_store import VectorStoreManager
from sentence_transformers import SentenceTransformer
import numpy as np

# Initialize
VECTOR_DB_DIR = BASE_DIR / "data" / "vector_db"

qdrant_host = os.getenv("QDRANT_HOST")
qdrant_api_key = os.getenv("QDRANT_API_KEY")
qdrant_dim = int(os.getenv("QDRANT_DIM", 384))

print("="*80)
print("🔍 VECTOR DATABASE DEBUG TOOL")
print("="*80)

# Initialize vector store
vector_store = VectorStoreManager(
    persist_directory=str(VECTOR_DB_DIR),
    embedding_model_name="all-MiniLM-L6-v2",
    qdrant_host=qdrant_host,
    qdrant_api_key=qdrant_api_key,
    qdrant_dim=qdrant_dim
)

# Check 1: Collection counts
print("\n📊 COLLECTION DOCUMENT COUNTS:")
print("-" * 80)
collections = ['cultural', 'general', 'trekking', 'government']
for coll in collections:
    try:
        full_name = f"india_{coll}"
        if vector_store.qdrant_client:
            info = vector_store.qdrant_client.get_collection(full_name)
            count = info.points_count
            print(f"✅ {full_name:25s}: {count:6d} documents")
    except Exception as e:
        print(f"❌ {full_name:25s}: Error - {e}")

# Check 2: Search for "Gayatri" specifically
print("\n" + "="*80)
print("🔍 SEARCHING FOR 'GAYATRI MANTRA' IN CULTURAL COLLECTION")
print("="*80)

try:
    # Test 1: Direct keyword search
    print("\n📍 Test 1: Searching with 'gayatri mantra'...")
    results = vector_store.query(
        query_text="gayatri mantra",
        collection_name="cultural",
        n_results=5
    )

    print(f"\n✅ Found {len(results.get('documents', [[]])[0])} results")

    if results.get('documents') and results['documents'][0]:
        for i, (doc, meta, dist) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            print(f"\n--- Result {i+1} ---")
            print(f"Distance: {dist:.4f}")
            print(f"Entity ID: {meta.get('entity_id', 'N/A')}")
            print(f"Source: {meta.get('source_file', 'N/A')}")
            print(f"Content Type: {meta.get('content_type', 'N/A')}")
            print(f"Preview: {doc[:200]}...")
    else:
        print("❌ No results found!")

    # Test 2: Search for "shloka"
    print("\n" + "-"*80)
    print("📍 Test 2: Searching with 'shloka'...")
    results = vector_store.query(
        query_text="shloka vedic mantra",
        collection_name="cultural",
        n_results=5
    )

    print(f"\n✅ Found {len(results.get('documents', [[]])[0])} results")
    if results.get('documents') and results['documents'][0]:
        for i, (doc, meta, dist) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            print(f"\n--- Result {i+1} ---")
            print(f"Distance: {dist:.4f}")
            print(f"Entity ID: {meta.get('entity_id', 'N/A')}")
            print(f"Source: {meta.get('source_file', 'N/A')}")
            print(f"Preview: {doc[:200]}...")

    # Test 3: Get ALL shlokas.json entries
    print("\n" + "="*80)
    print("📍 Test 3: Getting ALL shlokas.json entries from cultural collection...")
    print("="*80)

    # We need to use scroll to get all documents
    if vector_store.qdrant_client:
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        scroll_result = vector_store.qdrant_client.scroll(
            collection_name="india_cultural",
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="source_file",
                        match=MatchValue(value="shlokas.json")
                    )
                ]
            ),
            limit=50
        )

        points = scroll_result[0]
        print(f"\n✅ Found {len(points)} shloka entries")

        for point in points:
            entity_id = point.payload.get('entity_id', 'N/A')
            content_preview = point.payload.get('_node_content', '')[:150]
            print(f"\n🔹 {entity_id}")
            print(f"   {content_preview}...")

            # Check if this is the Gayatri Mantra
            if 'gayatri' in content_preview.lower():
                print("   ⭐ FOUND GAYATRI MANTRA!")
                print(f"   Full content: {point.payload.get('_node_content', '')}")

except Exception as e:
    print(f"\n❌ Error during search: {e}")
    import traceback
    traceback.print_exc()

# Check 3: Test embedding similarity
print("\n" + "="*80)
print("🧪 EMBEDDING SIMILARITY TEST")
print("="*80)

model = SentenceTransformer('all-MiniLM-L6-v2')

test_queries = [
    "tell me about gayatri mantra",
    "gayatri mantra meaning",
    "what is gayatri mantra"
]

shloka_samples = [
    "Shloka ID: shl013 Sanskrit: ॐ भूर्भुवः स्वः तत्सवितुर्वरेण्यं भर्गो देवस्य धीमहि धियो यो नः प्रचोदयात्",
    "Pavamana Mantra: Asato Ma Sadgamaya",
    "Om Namah Shivaya"
]

print("\nQuery embeddings vs Shloka embeddings:")
for query in test_queries:
    query_emb = model.encode(query)
    print(f"\n🔍 Query: '{query}'")

    for shloka in shloka_samples:
        shloka_emb = model.encode(shloka)
        similarity = np.dot(query_emb, shloka_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(shloka_emb))
        print(f"   vs '{shloka[:50]}...': {similarity:.4f}")

print("\n" + "="*80)
print("✅ DEBUG COMPLETE")
print("="*80)