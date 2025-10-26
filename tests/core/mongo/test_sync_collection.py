import uuid
from datetime import datetime, timezone

import pytest
from bson import Binary
from pydantic import BaseModel, Field

from bcf.core.mongo import SyncMongoCollection

# region Модели для тестов


class UserModel(BaseModel):
    """
    Тестовая модель пользователя для демонстрации работы SyncMongoCollection.

    :ivar id: Уникальный идентификатор пользователя, используется как _id в MongoDB.
    :vartype id: uuid.UUID
    :ivar name: Имя пользователя.
    :vartype name: str
    :ivar created_at: Время создания записи пользователя в UTC.
    :vartype created_at: datetime
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, alias="_id")
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# endregion


# region Фикстуры


@pytest.fixture
def user_collection(sync_db) -> SyncMongoCollection[UserModel]:
    """
    Фикстура для создания экземпляра SyncMongoCollection, параметризованного UserModel.

    :param sync_db: Фикстура, предоставляющая синхронное подключение к тестовой базе данных MongoDB.
    :type sync_db: _type_
    :return: Экземпляр коллекции для работы с UserModel.
    :rtype: SyncMongoCollection[UserModel]
    """
    return SyncMongoCollection[UserModel](collection=sync_db.users)


# endregion


# region Тесты


def test_insert_one(user_collection: SyncMongoCollection[UserModel]):
    """
    Тестирует вставку одного документа в коллекцию.

    Проверяет:
    1. Что ``inserted_id`` возвращается корректно (UUID или Binary).
    2. Что вставленный ``id`` соответствует ``id`` модели пользователя.
    3. Что документ можно найти в базе данных по его ``id``.
    4. Что найденный документ соответствует исходной модели пользователя.

    :param user_collection: Фикстура коллекции пользователей.
    :type user_collection: SyncMongoCollection[UserModel]
    """
    user = UserModel(name="Alice")
    result = user_collection.insert_one(user)
    assert isinstance(result.inserted_id, (uuid.UUID, Binary))
    # Конвертируем в UUID для сравнения, если это Binary
    inserted_id = (
        result.inserted_id
        if isinstance(result.inserted_id, uuid.UUID)
        else uuid.UUID(bytes=result.inserted_id)
    )
    assert inserted_id == user.id

    found_user = user_collection.find_one({"_id": user.id})
    assert found_user is not None
    assert found_user.id == user.id
    assert found_user.name == "Alice"


def test_insert_many(user_collection: SyncMongoCollection[UserModel]):
    """
    Тестирует вставку нескольких документов в коллекцию.

    Проверяет:
    1. Что количество вставленных ``id`` соответствует количеству переданных документов.
    2. Что все вставленные документы можно найти в базе данных.

    :param user_collection: Фикстура коллекции пользователей.
    :type user_collection: SyncMongoCollection[UserModel]
    """
    users = [UserModel(name="Bob"), UserModel(name="Charlie")]
    result = user_collection.insert_many(users)
    assert len(result.inserted_ids) == 2

    count = 0
    for _ in user_collection.find({"name": {"$in": ["Bob", "Charlie"]}}):
        count += 1
    assert count == 2


def test_find_one_not_found(user_collection: SyncMongoCollection[UserModel]):
    """
    Тестирует поиск одного документа, который не существует в коллекции.

    Проверяет:
    1. Что ``find_one`` возвращает ``None``, если документ не найден.

    :param user_collection: Фикстура коллекции пользователей.
    :type user_collection: SyncMongoCollection[UserModel]
    """
    found_user = user_collection.find_one({"name": "Unknown"})
    assert found_user is None


def test_find(user_collection: SyncMongoCollection[UserModel]):
    """
    Тестирует поиск нескольких документов в коллекции.

    Проверяет:
    1. Что ``find`` возвращает ожидаемое количество документов.
    2. Что найденные документы содержат правильные данные.

    :param user_collection: Фикстура коллекции пользователей.
    :type user_collection: SyncMongoCollection[UserModel]
    """
    users_to_insert = [UserModel(name="David"), UserModel(name="Eve")]
    user_collection.insert_many(users_to_insert)

    found_users = list(user_collection.find({"name": {"$in": ["David", "Eve"]}}))
    assert len(found_users) == 2
    names = {user.name for user in found_users}
    assert names == {"David", "Eve"}


def test_update_one(user_collection: SyncMongoCollection[UserModel]):
    """
    Тестирует обновление одного документа в коллекции.

    Проверяет:
    1. Что ``modified_count`` равен 1 после успешного обновления.
    2. Что документ был обновлен в базе данных и содержит новые данные.

    :param user_collection: Фикстура коллекции пользователей.
    :type user_collection: SyncMongoCollection[UserModel]
    """
    user = UserModel(name="Frank")
    user_collection.insert_one(user)

    result = user_collection.update_one(
        {"_id": user.id}, {"$set": {"name": "Franklin"}}
    )
    assert result.modified_count == 1

    updated_user = user_collection.find_one({"_id": user.id})
    assert updated_user is not None
    assert updated_user.name == "Franklin"


def test_update_many(user_collection: SyncMongoCollection[UserModel]):
    """
    Тестирует обновление нескольких документов в коллекции.

    Проверяет:
    1. Что ``modified_count`` соответствует количеству обновленных документов.
    2. Что все целевые документы были обновлены в базе данных.

    :param user_collection: Фикстура коллекции пользователей.
    :type user_collection: SyncMongoCollection[UserModel]
    """
    users = [UserModel(name="Grace"), UserModel(name="Heidi")]
    user_collection.insert_many(users)

    result = user_collection.update_many(
        {"name": {"$in": ["Grace", "Heidi"]}}, {"$set": {"name": "Updated"}}
    )
    assert result.modified_count == 2

    count = 0
    for user in user_collection.find({"name": "Updated"}):
        count += 1
    assert count == 2


def test_delete_one(user_collection: SyncMongoCollection[UserModel]):
    """
    Тестирует удаление одного документа из коллекции.

    Проверяет:
    1. Что ``deleted_count`` равен 1 после успешного удаления.
    2. Что удаленный документ больше не находится в базе данных.

    :param user_collection: Фикстура коллекции пользователей.
    :type user_collection: SyncMongoCollection[UserModel]
    """
    user = UserModel(name="Ivan")
    user_collection.insert_one(user)

    result = user_collection.delete_one({"_id": user.id})
    assert result.deleted_count == 1

    found_user = user_collection.find_one({"_id": user.id})
    assert found_user is None


def test_delete_many(user_collection: SyncMongoCollection[UserModel]):
    """
    Тестирует удаление нескольких документов из коллекции.

    Проверяет:
    1. Что ``deleted_count`` соответствует количеству удаленных документов.
    2. Что удаленные документы больше не находятся в базе данных.

    :param user_collection: Фикстура коллекции пользователей.
    :type user_collection: SyncMongoCollection[UserModel]
    """
    users = [UserModel(name="Judy"), UserModel(name="Mallory")]
    user_collection.insert_many(users)

    result = user_collection.delete_many({"name": {"$in": ["Judy", "Mallory"]}})
    assert result.deleted_count == 2

    found_users = list(user_collection.find({"name": {"$in": ["Judy", "Mallory"]}}))
    assert len(found_users) == 0


def test_document_model_property(user_collection: SyncMongoCollection[UserModel]):
    """
    Тестирует свойство ``_document_model`` коллекции.

    Проверяет:
    1. Что свойство ``_document_model`` возвращает правильную модель (UserModel),
       которой была параметризована коллекция.

    :param user_collection: Фикстура коллекции пользователей.
    :type user_collection: SyncMongoCollection[UserModel]
    """
    assert user_collection._document_model == UserModel


def test_document_model_unparametrized_error(sync_db):
    """
    Тестирует поведение при попытке использования непараметризованной коллекции.

    Проверяет:
    1. Что при попытке доступа к ``_document_model`` у непараметризованной
       ``SyncMongoCollection`` возникает ``TypeError`` с соответствующим сообщением.

    :param sync_db: Фикстура, предоставляющая синхронное подключение к тестовой базе данных MongoDB.
    :type sync_db: _type_
    """
    with pytest.raises(TypeError, match="Не могу определить модель документа"):
        # noinspection PyTypeChecker
        SyncMongoCollection(collection=sync_db.users)._document_model


# endregion
