import typing

import pytest
import pytest_asyncio
from pymongo import MongoClient
from pymongo.asynchronous.mongo_client import AsyncMongoClient
from testcontainers.mongodb import MongoDbContainer

# --- Фикстуры для Testcontainers ---


@pytest.fixture(scope="session")
def mongo_container():
    """
    Фикстура, которая запускает контейнер MongoDB для сессии тестов.
    """
    with MongoDbContainer("mongo:7") as mongo:
        yield mongo


@pytest.fixture(scope="session")
def mongo_uri(mongo_container: MongoDbContainer) -> str:
    """
    Возвращает URI для подключения к контейнеру MongoDB.
    """
    return mongo_container.get_connection_url()


# --- Синхронные фикстуры ---


@pytest.fixture
def sync_mongo_client(mongo_uri: str) -> typing.Generator[MongoClient, None, None]:
    """
    Создает синхронный клиент MongoClient для тестов.
    """
    client = MongoClient(mongo_uri)
    yield client
    client.close()


@pytest.fixture
def sync_db(sync_mongo_client: MongoClient):
    """
    Предоставляет тестовую базу данных и очищает ее после каждого теста.
    """
    db = sync_mongo_client.get_database("test_db")
    yield db
    for collection_name in db.list_collection_names():
        db.drop_collection(collection_name)


# --- Асинхронные фикстуры ---


@pytest_asyncio.fixture
async def async_mongo_client(
    mongo_uri: str,
) -> typing.AsyncGenerator[AsyncMongoClient, None]:
    """
    Создает асинхронный клиент AsyncMongoClient для тестов.
    """
    client = AsyncMongoClient(mongo_uri)
    yield client
    client.close()


@pytest_asyncio.fixture
async def async_db(
    async_mongo_client: AsyncMongoClient,
) -> typing.AsyncGenerator[typing.Any, None]:
    """
    Предоставляет асинхронную тестовую базу данных и очищает ее после каждого теста.
    """
    db = async_mongo_client.get_database("test_db")
    yield db
    for collection_name in await db.list_collection_names():
        await db.drop_collection(collection_name)
