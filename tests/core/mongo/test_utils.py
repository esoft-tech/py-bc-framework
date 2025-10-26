# tests/core/mongo/test_utils.py

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

import bson
from pydantic import AnyHttpUrl, BaseModel, Field
from pydantic_core import Url

from bcf.core.mongo.utils import recursive_convert_from, recursive_convert_to

# --- Тестовые данные и классы ---


class MyEnum(Enum):
    """Тестовый Enum."""

    A = "a"
    B = "b"


class MyModel(BaseModel):
    """Тестовая Pydantic модель."""

    field_one: str = Field(..., alias="fieldOne")
    field_two: int


# --- Тесты для recursive_convert_to ---


def test_recursive_convert_to_simple_types():
    """Тест: простые типы не должны изменяться."""
    assert recursive_convert_to(123) == 123
    assert recursive_convert_to("hello") == "hello"
    assert recursive_convert_to(None) is None
    assert recursive_convert_to(True) is True


def test_recursive_convert_to_dict():
    """Тест: рекурсивная конвертация словаря."""
    my_uuid = uuid4()
    my_dt = datetime(2023, 1, 1, 12, 0, 0)
    original = {"a": 1, "b": my_uuid, "c": my_dt, "d": {"nested_uuid": my_uuid}}
    expected = {
        "a": 1,
        "b": bson.Binary.from_uuid(my_uuid),
        "c": my_dt.replace(tzinfo=timezone.utc),
        "d": {"nested_uuid": bson.Binary.from_uuid(my_uuid)},
    }
    assert recursive_convert_to(original) == expected


def test_recursive_convert_to_list():
    """Тест: рекурсивная конвертация списка."""
    my_uuid = uuid4()
    original = [1, "text", my_uuid]
    expected = [1, "text", bson.Binary.from_uuid(my_uuid)]
    assert recursive_convert_to(original) == expected


def test_recursive_convert_to_tuple_and_set():
    """Тест: рекурсивная конвертация кортежа и множества."""
    my_uuid = uuid4()
    original_tuple = (1, "text", my_uuid)
    original_set = {1, "text", my_uuid}

    expected = [1, "text", bson.Binary.from_uuid(my_uuid)]

    # Результат будет списком
    assert recursive_convert_to(original_tuple) == expected
    # Порядок в set не гарантирован, поэтому сравниваем как множества
    assert set(recursive_convert_to(original_set)) == set(expected)


def test_recursive_convert_to_pydantic_model():
    """Тест: конвертация Pydantic модели."""
    model = MyModel(fieldOne="value1", field_two=123)
    expected = {"fieldOne": "value1", "field_two": 123}
    assert recursive_convert_to(model) == expected


def test_recursive_convert_to_uuid():
    """Тест: конвертация UUID."""
    my_uuid = uuid4()
    assert recursive_convert_to(my_uuid) == bson.Binary.from_uuid(my_uuid)


def test_recursive_convert_to_enum():
    """Тест: конвертация Enum."""
    assert recursive_convert_to(MyEnum.A) == "a"
    assert recursive_convert_to(MyEnum.B) == "b"


def test_recursive_convert_to_datetime_naive():
    """Тест: конвертация datetime без таймзоны."""
    naive_dt = datetime(2023, 1, 1, 10, 30, 0)
    aware_dt = naive_dt.replace(tzinfo=timezone.utc)
    assert recursive_convert_to(naive_dt) == aware_dt


def test_recursive_convert_to_datetime_aware():
    """Тест: datetime с таймзоной не должен изменяться."""
    aware_dt = datetime(2023, 1, 1, 10, 30, 0, tzinfo=timezone.utc)
    assert recursive_convert_to(aware_dt) == aware_dt


def test_recursive_convert_to_url():
    """Тест: конвертация pydantic_core.Url и pydantic.AnyHttpUrl."""
    url = Url("https://example.com/path?query=1")
    http_url = AnyHttpUrl("https://example.com/path?query=1")
    expected = "https://example.com/path?query=1"
    assert recursive_convert_to(url) == expected
    assert recursive_convert_to(http_url) == expected


def test_recursive_convert_to_complex_nested_structure():
    """Тест: сложная вложенная структура."""
    my_uuid = uuid4()
    model = MyModel(fieldOne="nested", field_two=456)
    original = {
        "level1": [
            1,
            {"uuid": my_uuid, "enum": MyEnum.B},
            (model, datetime(2023, 1, 1)),
        ]
    }
    expected = {
        "level1": [
            1,
            {"uuid": bson.Binary.from_uuid(my_uuid), "enum": "b"},
            [
                {"fieldOne": "nested", "field_two": 456},
                datetime(2023, 1, 1, tzinfo=timezone.utc),
            ],
        ]
    }
    assert recursive_convert_to(original) == expected


# --- Тесты для recursive_convert_from ---


def test_recursive_convert_from_simple_types():
    """Тест: простые типы не должны изменяться."""
    assert recursive_convert_from(123) == 123
    assert recursive_convert_from("hello") == "hello"
    assert recursive_convert_from(None) is None


def test_recursive_convert_from_dict():
    """Тест: рекурсивная конвертация словаря."""
    naive_dt = datetime(2023, 1, 1, 12, 0, 0)
    original = {"a": 1, "b": naive_dt, "c": {"nested_dt": naive_dt}}
    expected = {
        "a": 1,
        "b": naive_dt.replace(tzinfo=timezone.utc),
        "c": {"nested_dt": naive_dt.replace(tzinfo=timezone.utc)},
    }
    assert recursive_convert_from(original) == expected


def test_recursive_convert_from_list():
    """Тест: рекурсивная конвертация списка."""
    naive_dt = datetime(2023, 1, 1, 12, 0, 0)
    original = [1, "text", naive_dt]
    expected = [1, "text", naive_dt.replace(tzinfo=timezone.utc)]
    assert recursive_convert_from(original) == expected


def test_recursive_convert_from_datetime_naive():
    """Тест: конвертация datetime без таймзоны."""
    naive_dt = datetime(2023, 1, 1, 10, 30, 0)
    aware_dt = naive_dt.replace(tzinfo=timezone.utc)
    assert recursive_convert_from(naive_dt) == aware_dt


def test_recursive_convert_from_datetime_aware():
    """Тест: datetime с таймзоной не должен изменяться."""
    aware_dt = datetime(2023, 1, 1, 10, 30, 0, tzinfo=timezone.utc)
    assert recursive_convert_from(aware_dt) == aware_dt
