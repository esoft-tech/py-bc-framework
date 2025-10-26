import typing
from functools import cached_property
from typing import get_args

from pydantic import BaseModel
from pymongo.client_session import ClientSession
from pymongo.collection import Collection as OriginalCollection
from pymongo.operations import _IndexKeyHint
from pymongo.results import (
    DeleteResult,
    InsertManyResult,
    InsertOneResult,
    UpdateResult,
)
from pymongo.typings import _CollationIn, _Pipeline

from . import utils

DocumentT = typing.TypeVar("DocumentT", bound=BaseModel)


class SyncMongoCollection(typing.Generic[DocumentT]):
    """
    Синхронная обертка над стандартной коллекцией MongoDB.

    Эта обертка предоставляет удобные методы для работы с коллекцией,
    автоматически преобразуя данные между Pydantic-моделями и форматом BSON,
    используя утилиты из `utils.py`.
    """

    def __init__(
        self,
        *,
        collection: OriginalCollection,
    ) -> None:
        """
        Инициализирует обертку для коллекции.

        :param collection: Экземпляр оригинальной синхронной коллекции PyMongo.
        """
        self._collection: OriginalCollection = collection

    @cached_property
    def _document_model(self) -> type[DocumentT]:
        """
        Лениво извлекает тип модели документа из generic-аннотации.
        """
        # Используем getattr для безопасного доступа, хотя к моменту вызова он уже должен быть
        orig_class = getattr(self, "__orig_class__", None)
        if orig_class is None:
            raise TypeError(
                "Не могу определить модель документа. "
                "Убедись, что класс параметризован: SyncMongoCollection[MyModel](...)"
            )

        type_args = get_args(orig_class)
        if not type_args:
            # Эта ветка маловероятна, если orig_class найден, но для надёжности оставим
            raise TypeError("Не удалось извлечь тип модели из generic-аннотации.")

        return type_args[0]

    @property
    def c(self) -> OriginalCollection:
        """
        Возвращает оригинальный экземпляр коллекции PyMongo.
        """
        return self._collection

    def insert_one(
        self,
        document: DocumentT,
        bypass_document_validation: bool | None = None,
        session: ClientSession | None = None,
        comment: typing.Any | None = None,
    ) -> InsertOneResult:
        """
        Вставляет один документ в коллекцию.

        Данные из Pydantic-модели рекурсивно конвертируются в формат,
        пригодный для сохранения в MongoDB.

        :param document: Экземпляр Pydantic-модели для вставки.
        :param bypass_document_validation: Если True, отключает валидацию документа на сервере.
        :param session: Сессия клиента.
        :param comment: Комментарий, который будет прикреплен к команде.
        :return: Результат операции вставки.
        """
        return self.c.insert_one(
            utils.recursive_convert_to(document),
            bypass_document_validation=bypass_document_validation,
            session=session,
            comment=comment,
        )

    def insert_many(
        self,
        documents: list[DocumentT],
        ordered: bool = True,
        bypass_document_validation: bool | None = None,
        session: ClientSession | None = None,
        comment: typing.Any | None = None,
    ) -> InsertManyResult:
        """
        Вставляет несколько документов в коллекцию.

        Данные из каждой Pydantic-модели в списке рекурсивно конвертируются.

        :param documents: Список экземпляров Pydantic-моделей для вставки.
        :param ordered: Если True, вставка будет упорядоченной.
        :param bypass_document_validation: Если True, отключает валидацию документа на сервере.
        :param session: Сессия клиента.
        :param comment: Комментарий, который будет прикреплен к команде.
        :return: Результат операции вставки.
        """
        return self.c.insert_many(
            [utils.recursive_convert_to(doc) for doc in documents],
            ordered=ordered,
            bypass_document_validation=bypass_document_validation,
            session=session,
            comment=comment,
        )

    def find_one(
        self, filter: dict[str, typing.Any], *args: typing.Any, **kwargs: typing.Any
    ) -> DocumentT | None:
        """
        Находит один документ, соответствующий фильтру.

        Фильтр предварительно конвертируется для корректного запроса к MongoDB.
        Найденный документ конвертируется из формата BSON в экземпляр Pydantic-модели.

        :param filter: Словарь с условиями фильтрации.
        :return: Экземпляр Pydantic-модели или None, если документ не найден.
        """
        raw_result = self.c.find_one(
            utils.recursive_convert_to(filter), *args, **kwargs
        )
        if raw_result is None:
            return None
        return self._document_model.model_validate(
            utils.recursive_convert_from(raw_result)
        )

    def find(
        self, filter: dict[str, typing.Any], *args: typing.Any, **kwargs: typing.Any
    ) -> typing.Generator[DocumentT, None, None]:
        """
        Находит все документы, соответствующие фильтру, и возвращает генератор.

        Фильтр конвертируется для запроса. Каждый найденный документ
        преобразуется в экземпляр Pydantic-модели.

        :param filter: Словарь с условиями фильтрации.
        :return: Генератор, возвращающий экземпляры Pydantic-моделей.
        """
        cursor = self.c.find(utils.recursive_convert_to(filter), *args, **kwargs)
        for raw_doc in cursor:
            yield self._document_model.model_validate(
                utils.recursive_convert_from(raw_doc)
            )

    def update_one(
        self,
        filter: dict[str, typing.Any],
        update: dict[str, typing.Any] | _Pipeline,
        upsert: bool = False,
        bypass_document_validation: bool | None = None,
        collation: _CollationIn | None = None,
        array_filters: list[dict[str, typing.Any]] | None = None,
        hint: _IndexKeyHint | None = None,
        session: ClientSession | None = None,
        let: typing.Mapping[str, typing.Any] | None = None,
        sort: typing.Mapping[str, typing.Any] | None = None,
        comment: typing.Any | None = None,
    ) -> UpdateResult:
        """
        Обновляет один документ, соответствующий фильтру.

        Фильтр и данные для обновления рекурсивно конвертируются.

        :param filter: Словарь с условиями фильтрации.
        :param update: Словарь с операциями обновления (например, `$set`).
        :param upsert: Если True, выполняет вставку, если документ не найден.
        :param bypass_document_validation: Если True, отключает валидацию документа на сервере.
        :param collation: Настройки сопоставления.
        :param array_filters: Список фильтров для обновления элементов массива.
        :param hint: Подсказка по индексу.
        :param session: Сессия клиента.
        :param let: Переменные для использования в выражении обновления.
        :param sort: Порядок сортировки для выбора документа для обновления.
        :param comment: Комментарий.
        :return: Результат операции обновления.
        """
        return self.c.update_one(
            utils.recursive_convert_to(filter),
            utils.recursive_convert_to(update),
            upsert=upsert,
            bypass_document_validation=bypass_document_validation,
            collation=collation,
            array_filters=array_filters,
            hint=hint,
            session=session,
            let=let,
            sort=sort,
            comment=comment,
        )

    def update_many(
        self,
        filter: dict[str, typing.Any],
        update: dict[str, typing.Any] | _Pipeline,
        upsert: bool = False,
        array_filters: list[dict[str, typing.Any]] | None = None,
        bypass_document_validation: bool | None = None,
        collation: _CollationIn | None = None,
        hint: _IndexKeyHint | None = None,
        session: ClientSession | None = None,
        let: typing.Mapping[str, typing.Any] | None = None,
        comment: typing.Any | None = None,
    ) -> UpdateResult:
        """
        Обновляет несколько документов, соответствующих фильтру.

        Фильтр и данные для обновления рекурсивно конвертируются.

        :param filter: Словарь с условиями фильтрации.
        :param update: Словарь с операциями обновления (например, `$set`).
        :param upsert: Если True, выполняет вставку, если документ не найден.
        :param array_filters: Список фильтров для обновления элементов массива.
        :param bypass_document_validation: Если True, отключает валидацию документа на сервере.
        :param collation: Настройки сопоставления.
        :param hint: Подсказка по индексу.
        :param session: Сессия клиента.
        :param let: Переменные для использования в выражении обновления.
        :param comment: Комментарий.
        :return: Результат операции обновления.
        """
        return self.c.update_many(
            utils.recursive_convert_to(filter),
            utils.recursive_convert_to(update),
            upsert=upsert,
            array_filters=array_filters,
            bypass_document_validation=bypass_document_validation,
            collation=collation,
            hint=hint,
            session=session,
            let=let,
            comment=comment,
        )

    def delete_one(
        self,
        filter: dict[str, typing.Any],
        collation: _CollationIn | None = None,
        hint: _IndexKeyHint | None = None,
        session: ClientSession | None = None,
        let: typing.Mapping[str, typing.Any] | None = None,
        comment: typing.Any | None = None,
    ) -> DeleteResult:
        """
        Удаляет один документ, соответствующий фильтру.

        :param filter: Словарь с условиями фильтрации.
        :param collation: Настройки сопоставления.
        :param hint: Подсказка по индексу.
        :param session: Сессия клиента.
        :param let: Переменные для использования в выражении.
        :param comment: Комментарий.
        :return: Результат операции удаления.
        """
        return self.c.delete_one(
            utils.recursive_convert_to(filter),
            collation=collation,
            hint=hint,
            session=session,
            let=let,
            comment=comment,
        )

    def delete_many(
        self,
        filter: dict[str, typing.Any],
        collation: _CollationIn | None = None,
        hint: _IndexKeyHint | None = None,
        session: ClientSession | None = None,
        let: typing.Mapping[str, typing.Any] | None = None,
        comment: typing.Any | None = None,
    ) -> DeleteResult:
        """
        Удаляет несколько документов, соответствующих фильтру.

        :param filter: Словарь с условиями фильтрации.
        :param collation: Настройки сопоставления.
        :param hint: Подсказка по индексу.
        :param session: Сессия клиента.
        :param let: Переменные для использования в выражении.
        :param comment: Комментарий.
        :return: Результат операции удаления.
        """
        return self.c.delete_many(
            utils.recursive_convert_to(filter),
            collation=collation,
            hint=hint,
            session=session,
            let=let,
            comment=comment,
        )
