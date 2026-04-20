import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()

client = QdrantClient(
    url=os.getenv("QDRANT_HOST"),
    api_key=os.getenv("QDRANT_API_KEY")
)

collections = client.get_collections().collections

for collection in collections:
    print(f"\n📊 Collection: {collection.name}")
    info = client.get_collection(collection.name)
    print(f"   Points: {info.points_count}")
    
    if info.payload_schema:
        print("   Indexed fields:")
        for field, schema in info.payload_schema.items():
            print(f"     ✅ {field}: {schema.data_type}")
    else:
        print("   ⚠️  No payload indexes found")
