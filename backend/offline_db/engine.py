from offline_db.database import OfflineDatabase

class OfflineMongoClient:
    def __init__(self, base_path):
        self.base_path = base_path
        self._dbs = {}

    def get_database(self, name):
        if name not in self._dbs:
            self._dbs[name] = OfflineDatabase(self.base_path, name)
        return self._dbs[name]
