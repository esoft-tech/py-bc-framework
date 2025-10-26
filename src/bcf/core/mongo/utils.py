import typing
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID

import bson
from pydantic import AnyHttpUrl, BaseModel
from pydantic_core import Url


def recursive_convert_to(value: typing.Any) -> typing.Any:
    """Рекурсивно конвертирует значения для сохранения в MongoDB.

    Эта функция предназначена для подготовки данных перед их записью в MongoDB.
    Она рекурсивно обходит переданное значение (словари, списки, кортежи, множества)
    и конвертирует специфические типы данных в формат, который MongoDB может корректно хранить.

    Конвертации включают:

    *   :class:`pydantic.BaseModel` в словарь (используя ``model_dump(by_alias=True)``).
    *   :class:`uuid.UUID` в :class:`bson.Binary` (UUID subtype 4).
    *   :class:`enum.Enum` в его значение (``value``).
    *   :class:`datetime.datetime` без временной зоны в UTC (добавляет ``timezone.utc``).
    *   :class:`pydantic_core.Url` и :class:`pydantic.AnyHttpUrl` в строковое представление.

    :param value: Входное значение любого типа, которое нужно конвертировать.
    :type value: typing.Any
    :return: Сконвертированное значение, готовое для записи в MongoDB.
    :rtype: typing.Any
    """
    if isinstance(value, dict):
        return {k: recursive_convert_to(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [recursive_convert_to(v) for v in value]
    if isinstance(value, BaseModel):
        return recursive_convert_to(value.model_dump(by_alias=True))
    if isinstance(value, UUID):
        return bson.Binary.from_uuid(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime) and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    if isinstance(value, Url):
        return str(value)
    if isinstance(value, AnyHttpUrl):
        return str(value)

    return value


def recursive_convert_from(value: typing.Any) -> typing.Any:
    """Рекурсивно конвертирует значения, полученные из MongoDB.

    Эта функция предназначена для обработки данных, извлеченных из MongoDB,
    и их приведения к ожидаемому формату. Она рекурсивно обходит переданное
    значение (словари, списки, кортежи, множества).

    Конвертации включают:

    *   :class:`datetime.datetime` без временной зоны в UTC (добавляет ``timezone.utc``).
        Это обеспечивает единообразие при работе с датами, хранящимися в MongoDB.

    :param value: Входное значение любого типа, полученное из MongoDB.
    :type value: typing.Any
    :return: Сконвертированное значение, готовое для использования в приложении.
    :rtype: typing.Any
    """
    if isinstance(value, dict):
        return {k: recursive_convert_from(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [recursive_convert_from(i) for i in value]
    if isinstance(value, datetime) and value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value
