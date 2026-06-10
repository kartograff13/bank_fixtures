import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from src.reports import report_decorator, spending_by_category, spending_by_weekday, spending_by_workday


@pytest.fixture
def sample_transactions() -> pd.DataFrame:
    """Фикстура с тестовыми транзакциями"""
    data = {
        "Дата операции": [
            datetime.now() - timedelta(days=10),
            datetime.now() - timedelta(days=20),
            datetime.now() - timedelta(days=40),
            datetime.now() - timedelta(days=70),
            datetime.now() - timedelta(days=100),
        ],
        "Категория": ["Еда", "Еда", "Развлечения", "Еда", "Еда"],
        "Сумма операции": [-500, -300, -1000, -200, -100],
        "Статус": ["OK"] * 5,
    }
    return pd.DataFrame(data)


def test_spending_by_category(sample_transactions: pd.DataFrame) -> None:
    """Тест функции трат по категории"""
    result = spending_by_category(sample_transactions, "Еда")

    assert not result.empty
    assert "Месяц" in result.columns
    assert "Сумма операции" in result.columns
    assert len(result) == 2
    assert result["Сумма операции"].sum() == 1000


def test_spending_by_category_empty(sample_transactions: pd.DataFrame) -> None:
    """Тест функции трат по категории с несуществующей категорией"""
    result = spending_by_category(sample_transactions, "Несуществующая")

    assert result.empty


def test_spending_by_weekday(sample_transactions: pd.DataFrame) -> None:
    """Тест функции трат по дням недели"""
    result = spending_by_weekday(sample_transactions)

    assert not result.empty
    assert "День недели" in result.columns
    assert "Сумма" in result.columns
    assert len(result) <= 7


def test_spending_by_workday(sample_transactions: pd.DataFrame) -> None:
    """Тест функции трат по типам дней"""
    result = spending_by_workday(sample_transactions)

    assert not result.empty
    assert "День типа" in result.columns
    assert "Сумма" in result.columns
    assert set(result["День типа"].tolist()) == {"Рабочий", "Выходной"}


def test_report_decorator_creates_file(tmp_path: Path) -> None:
    """Тест создания файла декоратором"""
    test_file = tmp_path / "test_report.json"

    @report_decorator(filename=str(test_file))
    def test_func() -> pd.DataFrame:
        return pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})

    test_func()

    assert test_file.exists()
    with open(test_file, "r") as f:
        data = json.load(f)

    assert len(data) == 2
    assert all("_timestamp" in record for record in data)
    assert all("_report_type" in record for record in data)


def test_report_decorator_avoid_duplicates(tmp_path: Path) -> None:
    """Тест избегания дубликатов в декораторе"""
    test_file = tmp_path / "test_report.json"

    @report_decorator(filename=str(test_file), avoid_duplicates=True)
    def test_func() -> pd.DataFrame:
        return pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})

    test_func()
    test_func()

    with open(test_file, "r") as f:
        data = json.load(f)

    assert len(data) == 2


def test_report_decorator_with_empty_dataframe(tmp_path: Path) -> None:
    """Тест декоратора с пустым DataFrame"""
    test_file = tmp_path / "test_report.json"

    @report_decorator(filename=str(test_file))
    def test_func() -> pd.DataFrame:
        return pd.DataFrame()

    test_func()

    assert not test_file.exists()


def test_report_decorator_with_non_dataframe(tmp_path: Path) -> None:
    """Тест декоратора с не-DataFrame результатом"""
    test_file = tmp_path / "test_report.json"

    @report_decorator(filename=str(test_file))
    def test_func() -> dict:
        return {"key": "value"}

    test_func()

    assert test_file.exists()
    with open(test_file, "r") as f:
        data = json.load(f)

    assert len(data) == 1
    assert data[0]["data"] == {"key": "value"}


def test_spending_functions_with_specific_date(sample_transactions: pd.DataFrame) -> None:
    """Тест функций с указанием конкретной даты"""
    test_date = "2023-01-01"
    result1 = spending_by_category(sample_transactions, "Еда", test_date)
    result2 = spending_by_weekday(sample_transactions, test_date)
    result3 = spending_by_workday(sample_transactions, test_date)

    assert isinstance(result1, pd.DataFrame)
    assert isinstance(result2, pd.DataFrame)
    assert isinstance(result3, pd.DataFrame)


def test_report_decorator_handles_json_decode_error(tmp_path: Path) -> None:
    """Тест обработки ошибки JSONDecodeError при чтении существующего файла"""
    test_file = tmp_path / "test_report.json"

    # Создаем битый JSON файл
    with open(test_file, "w") as f:
        f.write("{ invalid json }")

    @report_decorator(filename=str(test_file))
    def test_func() -> pd.DataFrame:
        return pd.DataFrame({"col1": [5, 6], "col2": [7, 8]})

    result = test_func()

    assert not result.empty
    assert test_file.exists()

    with open(test_file, "r") as f:
        data = json.load(f)

    assert len(data) == 2
    assert data[0]["col1"] == 5


def test_report_decorator_handles_general_exception_when_reading(tmp_path: Path) -> None:
    """Тест обработки общего исключения при чтении существующего файла"""
    test_file = tmp_path / "test_report.json"

    with patch("builtins.open", side_effect=Exception("Test read error")):

        @report_decorator(filename=str(test_file))
        def test_func() -> pd.DataFrame:
            return pd.DataFrame({"col1": [9, 10], "col2": [11, 12]})

        result = test_func()

        assert not result.empty


def test_report_decorator_handles_general_exception_when_writing(tmp_path: Path) -> None:
    """Тест обработки общего исключения при записи файла"""
    test_file = tmp_path / "test_report.json"

    with patch("builtins.open", side_effect=Exception("Test write error")):

        @report_decorator(filename=str(test_file))
        def test_func() -> pd.DataFrame:
            return pd.DataFrame({"col1": [13, 14], "col2": [15, 16]})

        result = test_func()

        assert not result.empty


def test_report_decorator_handles_non_list_json_content(tmp_path: Path) -> None:
    """Тест обработки случая, когда JSON файл существует, но содержит не список"""
    test_file = tmp_path / "test_report.json"

    with open(test_file, "w") as f:
        json.dump({"not": "a list"}, f)

    @report_decorator(filename=str(test_file))
    def test_func() -> pd.DataFrame:
        return pd.DataFrame({"col1": [17, 18], "col2": [19, 20]})

    result = test_func()

    assert not result.empty
    assert test_file.exists()

    with open(test_file, "r") as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert len(data) == 2


def test_report_decorator_with_non_dataframe_handles_json_error(tmp_path: Path) -> None:
    """Тест обработки ошибки JSON для не-DataFrame результатов"""
    test_file = tmp_path / "test_report.json"

    with open(test_file, "w") as f:
        f.write("{ invalid json }")

    @report_decorator(filename=str(test_file))
    def test_func() -> dict:
        return {"new_key": "new_value"}

    result = test_func()

    assert result == {"new_key": "new_value"}
    assert test_file.exists()

    with open(test_file, "r") as f:
        data = json.load(f)

    assert len(data) == 1
    assert data[0]["data"] == {"new_key": "new_value"}
