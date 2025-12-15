import json
from bson import ObjectId
from pathlib import Path
from offline_db.cursor import OfflineCursor

class OfflineCollection:
    def __init__(self, root, name):
        self.path = root / name
        self.path.mkdir(exist_ok=True)

    async def insert_one(self, doc):
        if "_id" not in doc:
            doc["_id"] = ObjectId()
        file = self.path / f"{doc['_id']}.json"
        file.write_text(json.dumps(doc, default=str))
        return doc["_id"]

    async def find_one(self, query):
        for f in self.path.glob("*.json"):
            data = json.loads(f.read_text())
            if all(data.get(k) == v for k, v in query.items()):
                return data
        return None

    def find(self, query):
        return OfflineCursor(self.path, query)

    async def update_one(self, query, update):
        doc = await self.find_one(query)
        if not doc:
            return
        for k, v in update.get("$set", {}).items():
            doc[k] = v
        file = self.path / f"{doc['_id']}.json"
        file.write_text(json.dumps(doc, default=str))

    async def delete_one(self, query):
        doc = await self.find_one(query)
        if doc:
            (self.path / f"{doc['_id']}.json").unlink(missing_ok=True)
