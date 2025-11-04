import datetime
from decimal import Decimal

import pytest

from src.services import (
    investment_bank,
    profitable_cashback_categories,
    search_person_transfers,
    search_phone_numbers,
    simple_search,
)


@pytest.fixture
def sample_transactions() -> list[dict]:
    return [
        {
            "Дата операции": "2023-10-05 12:00:00",
            "Сумма операции": "-1500.00",
            "Категория": "Супермаркеты",
            "Описание": "Покупка в Магните",
        },
        {
            "Дата операции": "2023-10-10 15:30:00",
            "Сумма операции": "-200.50",
            "Категория": "АЗС",
            "Описание": "Заправка ВР",
        },
        {
            "Дата операции": "2023-11-01 09:15:00",
            "Сумма операции": "-3000",
            "Категория": "Рестораны",
            "Описание": "Ужин в Старбакс",
        },
        {
            "Дата операции": datetime.datetime(2023, 10, 15, 14, 0, 0),
            "Сумма операции": Decimal("-500.75"),
            "Категория": "Такси",
            "Описание": "Поездка в аэропорт",
        },
        {
            "Дата операции": "01.10.2023 08:45:00",
            "Сумма операции": "-100.00",
            "Категория": "Супермаркеты",
            "Описание": "Пятерочка",
        },
        {
            "Дата операции": None,
            "Сумма операции": "-50.00",
            "Категория": "Прочее",
            "Описание": "Перевод",
        },
        {
            "Дата операции": "2023-10-20",
            "Сумма операции": "150.00",
            "Категория": "Возврат",
            "Описание": "Возврат средств",
        },
        {
            "Дата операции": "2023-10-25 19:20:00",
            "Сумма операции": "-1200.00",
            "Категория": "Переводы",
            "Описание": "Перевод Иванов И.И.",
        },
        {
            "Дата операции": "2023-10-18 12:00:00",
            "Сумма операции": "-500.00",
            "Категория": "Переводы",
            "Описание": "Пополнение телефона +7 912 345-67-89",
        },
    ]


@pytest.fixture
def edge_case_transactions() -> list[dict]:
    """Транзакции с крайними случаями для покрытия всех веток кода"""
    return [
        {
            "Дата операции": "2023/10/05 12:00:00",
            "Сумма операции": "-100.00",
            "Категория": "Тест",
            "Описание": "Тестовая транзакция",
        },
        {
            "Дата операции": "",
            "Сумма операции": "-200.00",
            "Категория": "Тест",
            "Описание": "Тестовая транзакция 2",
        },
        {
            "Дата операции": "2023-10-05 12:00:00",
            "Сумма операции": "не число",
            "Категория": "Тест",
            "Описание": "Тестовая транзакция 3",
        },
        {
            "Дата операции": "2023-10-05 12:00:00",
            "Сумма операции": None,
            "Категория": "Тест",
            "Описание": "Тестовая транзакция 4",
        },
        {
            "Дата операции": "2023-10-05 12:00:00",
            "Сумма операции": "",
            "Категория": "Тест",
            "Описание": "Тестовая транзакция 5",
        },
    ]


def test_profitable_cashback_categories(sample_transactions: list[dict]) -> None:
    result = profitable_cashback_categories(sample_transactions, 2023, 10)

    expected = {
        "Супермаркеты": 16.0,
        "АЗС": 2.005,
        "Такси": 5.0075,
        "Переводы": 17.0,
    }

    assert result == pytest.approx(expected, rel=1e-3)


def test_profitable_cashback_empty() -> None:
    result = profitable_cashback_categories([], 2023, 10)
    assert result == {}


def test_profitable_cashback_edge_cases(edge_case_transactions: list[dict]) -> None:
    """Тестирование крайних случаев для покрытия всех веток profitable_cashback_categories"""
    result = profitable_cashback_categories(edge_case_transactions, 2023, 10)
    assert result == {}


def test_profitable_cashback_invalid_dates() -> None:
    """Тестирование транзакций с невалидными датами"""
    transactions = [
        {
            "Дата операции": "invalid-date-format",
            "Сумма операции": "-100.00",
            "Категория": "Тест",
            "Описание": "Тест",
        },
        {
            "Дата операции": "2023-13-45 25:61:61",
            "Сумма операции": "-200.00",
            "Категория": "Тест",
            "Описание": "Тест",
        },
    ]
    result = profitable_cashback_categories(transactions, 2023, 10)
    assert result == {}


def test_investment_bank(sample_transactions: list[dict]) -> None:
    result = investment_bank("2023-10", sample_transactions, 100)
    expected = 0.0
    assert result == pytest.approx(expected, 0.01)


def test_investment_bank_different_limit(sample_transactions: list[dict]) -> None:
    result = investment_bank("2023-10", sample_transactions, 500)
    expected = 999.5
    assert result == pytest.approx(expected, 0.01)


def test_investment_bank_no_transactions() -> None:
    result = investment_bank("2023-12", [], 100)
    assert result == 0.0


def test_investment_bank_invalid_month_format() -> None:
    """Тестирование неверного формата месяца для покрытия строк 60-61"""
    result = investment_bank("2023/10", [], 100)
    assert result == 0.0


def test_investment_bank_empty_month() -> None:
    """Тестирование пустой строки месяца"""
    result = investment_bank("", [], 100)
    assert result == 0.0


def test_investment_bank_edge_cases(edge_case_transactions: list[dict]) -> None:
    """Тестирование крайних случаев для покрытия всех веток investment_bank"""
    result = investment_bank("2023-10", edge_case_transactions, 100)
    assert result == 0.0


def test_investment_bank_invalid_amounts() -> None:
    """Тестирование транзакций с невалидными суммами"""
    transactions = [
        {
            "Дата операции": "2023-10-05 12:00:00",
            "Сумма операции": "abc123",
            "Категория": "Тест",
            "Описание": "Тест",
        },
        {
            "Дата операции": "2023-10-05 12:00:00",
            "Сумма операции": "123,456.78.90",
            "Категория": "Тест",
            "Описание": "Тест",
        },
    ]
    result = investment_bank("2023-10", transactions, 100)
    assert result == 0.0


def test_simple_search(sample_transactions: list[dict]) -> None:
    result = simple_search(sample_transactions, "Магнит")
    assert len(result) == 1
    assert result[0]["Описание"] == "Покупка в Магните"


def test_simple_search_category(sample_transactions: list[dict]) -> None:
    result = simple_search(sample_transactions, "Супермаркеты")
    assert len(result) == 2
    assert all("Супермаркеты" in t["Категория"] for t in result)


def test_simple_search_case_insensitive(sample_transactions: list[dict]) -> None:
    result = simple_search(sample_transactions, "СТАРБАКС")
    assert len(result) == 1
    assert result[0]["Описание"] == "Ужин в Старбакс"


def test_simple_search_no_results(sample_transactions: list[dict]) -> None:
    result = simple_search(sample_transactions, "Несуществующий запрос")
    assert len(result) == 0


def test_simple_search_empty_query(sample_transactions: list[dict]) -> None:
    result = simple_search(sample_transactions, "")
    assert len(result) == len(sample_transactions)


def test_search_phone_numbers(sample_transactions: list[dict]) -> None:
    result = search_phone_numbers(sample_transactions)
    assert len(result) == 1
    assert "+7 912 345-67-89" in result[0]["Описание"]


def test_search_phone_numbers_no_matches(sample_transactions: list[dict]) -> None:
    no_phone_transactions = [
        {**t, "Описание": "Простой перевод"} for t in sample_transactions if "телефона" not in t.get("Описание", "")
    ]
    result = search_phone_numbers(no_phone_transactions)
    assert len(result) == 0


def test_search_phone_numbers_different_formats() -> None:
    """Тестирование разных форматов телефонных номеров"""
    transactions = [
        {
            "Дата операции": "2023-10-05 12:00:00",
            "Сумма операции": "-100.00",
            "Категория": "Тест",
            "Описание": "Пополнение +79123456789",
        },
        {
            "Дата операции": "2023-10-05 12:00:00",
            "Сумма операции": "-200.00",
            "Категория": "Тест",
            "Описание": "Пополнение 8(912)345-67-89",
        },
        {
            "Дата операции": "2023-10-05 12:00:00",
            "Сумма операции": "-300.00",
            "Категория": "Тест",
            "Описание": "Пополнение 8-912-345-67-89",
        },
    ]
    result = search_phone_numbers(transactions)
    assert len(result) == 3


def test_search_person_transfers(sample_transactions: list[dict]) -> None:
    result = search_person_transfers(sample_transactions)
    assert len(result) == 1
    assert "Иванов И.И." in result[0]["Описание"]
    assert result[0]["Категория"] == "Переводы"


def test_search_person_transfers_no_matches(sample_transactions: list[dict]) -> None:
    modified_transactions = [
        {**t, "Категория": "Прочее"} if "Иванов" in t.get("Описание", "") else t for t in sample_transactions
    ]
    result = search_person_transfers(modified_transactions)
    assert len(result) == 0


def test_search_person_transfers_no_name_pattern(sample_transactions: list[dict]) -> None:
    modified_transactions = [
        {**t, "Описание": "Простой перевод"} if "Иванов" in t.get("Описание", "") else t for t in sample_transactions
    ]
    result = search_person_transfers(modified_transactions)
    assert len(result) == 0


def test_search_person_transfers_different_name_formats() -> None:
    """Тестирование разных форматов ФИО"""
    transactions = [
        {
            "Дата операции": "2023-10-05 12:00:00",
            "Сумма операции": "-100.00",
            "Категория": "Переводы",
            "Описание": "Перевод Петров А.В.",
        },
        {
            "Дата операции": "2023-10-05 12:00:00",
            "Сумма операции": "-200.00",
            "Категория": "Переводы",
            "Описание": "Перевод Сидорова М.К.",
        },
        {
            "Дата операции": "2023-10-05 12:00:00",
            "Сумма операции": "-300.00",
            "Категория": "Переводы",
            "Описание": "Перевод Иванов Иван",
        },
    ]
    result = search_person_transfers(transactions)
    assert len(result) == 2
