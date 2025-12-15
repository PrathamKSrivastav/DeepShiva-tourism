import json

class OfflineCursor:
    def __init__(self, path, query):
        self.files = list(path.glob("*.json"))
        self.query = query
        self._limit = None

    def limit(self, n):
        self._limit = n
        return self

    async def to_list(self, length=None):
        results = []
        for f in self.files:
            data = json.loads(f.read_text())
            if all(data.get(k) == v for k, v in self.query.items()):
                results.append(data)
            if self._limit and len(results) >= self._limit:
                break
        return results
