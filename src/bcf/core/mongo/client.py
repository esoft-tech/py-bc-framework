from typing import ClassVar

from pymongo import AsyncMongoClient as OriginalAsyncMongoClient
from pymongo import MongoClient as OriginalMongoClient

from .config import MongoConfig


class MongoClient:
    _a_mongo_clients: ClassVar[dict[int, OriginalAsyncMongoClient]] = {}
    _mongo_clients: ClassVar[dict[int, OriginalMongoClient]] = {}

    def __init__(self, *, config: MongoConfig) -> None:
        self._config = config

    @property
    def _a_mongo_client(self) -> OriginalAsyncMongoClient:
        key = hash(self._config)
        if key not in self._a_mongo_clients:
            self._a_mongo_clients[key] = OriginalAsyncMongoClient(self._config.url)

        return self._a_mongo_clients[key]

    @property
    def _mongo_client(self) -> OriginalMongoClient:
        key = hash(self._config)
        if key not in self._a_mongo_clients:
            self._mongo_clients[key] = OriginalMongoClient(self._config.url)

        return self._mongo_clients[key]

    