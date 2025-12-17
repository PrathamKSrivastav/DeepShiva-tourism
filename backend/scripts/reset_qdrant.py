import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()

qdrant_host = os.getenv("QDRANT_HOST")
qdrant_api_key = os.getenv("QDRANT_API_KEY")

if not qdrant_host or not qdrant_api_key:
    print("❌ Qdrant credentials not found in .env")
    exit(1)

client = QdrantClient(
    url=qdrant_host,
    api_key=qdrant_api_key
)

print("🔍 Fetching collections...")
collections = client.get_collections().collections

if not collections:
    print("✅ No collections to delete")
else:
    print(f"\n📋 Found {len(collections)} collections:")
    for c in collections:
        print(f"  • {c.name}")
    
    confirm = input("\n⚠️  Delete ALL collections? (yes/no): ").strip().lower()
    
    if confirm in ['yes', 'y']:
        for c in collections:
            print(f"🗑️  Deleting {c.name}...")
            client.delete_collection(c.name)
        print("\n✅ All Qdrant collections deleted successfully")
    else:
        print("❌ Deletion cancelled")
