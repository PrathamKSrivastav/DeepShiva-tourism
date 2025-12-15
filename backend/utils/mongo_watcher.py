import asyncio
import logging
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

logger = logging.getLogger(__name__)


class MongoWatcher:
    """
    Pure availability watcher.
    Does NOT import database state.
    """

    def __init__(self, uri: str, db_name: str, check_interval: int = 5):
        self.uri = uri
        self.db_name = db_name
        self.check_interval = check_interval
        self._online = False

    async def wait_until_available(self):
        """
        Blocks until MongoDB becomes reachable.
        """
        while True:
            try:
                client = MongoClient(
                    self.uri,
                    serverSelectionTimeoutMS=2000
                )
                client.admin.command("ping")
                self._online = True
                logger.info("🟢 MongoDB became available")
                return
            except ServerSelectionTimeoutError:
                self._online = False
                await asyncio.sleep(self.check_interval)

    def is_online(self) -> bool:
        return self._online
