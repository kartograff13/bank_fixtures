import json
import os
import tempfile
from datetime import datetime
from unittest.mock import patch

import numpy as np
import pandas as pd

from src.utils import (
    convert_dataframe_to_dict_list,
    filter_transactions_by_date,
    get_api_key,
    get_date_range,
    get_greeting_by_time,
    load_transactions,
    load_user_settings,
    prepare_transactions_data,
)


def test_load_transactions_success() -> None:
    """Тест успешной загрузки транзакций из Excel файла"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_data = pd.DataFrame(
            {
                "Дата операции": ["01.01.2023 12:00:00", "02.01.2023 15:30:00"],
                "Сумма операции": [1000, 2000],
                "Статус": ["OK", "OK"],
            }
        )
        file_path = os.path.join(tmp_dir, "test_operations.xlsx")
        test_data.to_excel(file_path, index=False)
        result = load_transactions(file_path)
        assert len(result) == 2
        assert "Дата операции" in result.columns
        assert pd.api.types.is_datetime64_any_dtype(result["Дата операции"])


def test_load_transactions_with_payment_date() -> None:
    """Тест загрузки транзакций с колонкой 'Дата платежа'"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_data = pd.DataFrame(
            {
                "Дата операции": ["01.01.2023 12:00:00", "02.01.2023 15:30:00"],
                "Дата платежа": ["03.01.2023 10:00:00", "04.01.2023 11:00:00"],
                "Сумма операции": [1000, 2000],
                "Статус": ["OK", "OK"],
            }
        )
        file_path = os.path.join(tmp_dir, "test_operations.xlsx")
        test_data.to_excel(file_path, index=False)
        result = load_transactions(file_path)

        assert len(result) == 2
        assert "Дата платежа" in result.columns
        assert pd.api.types.is_datetime64_any_dtype(result["Дата платежа"])


def test_load_transactions_file_not_found() -> None:
    """Тест загрузки транзакций с несуществующим файлом"""
    result = load_transactions("nonexistent_file.xlsx")
    assert result.empty


def test_load_transactions_invalid_data() -> None:
    """Тест загрузки транзакций с некорректными данными"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = os.path.join(tmp_dir, "invalid.xlsx")
        pd.DataFrame().to_excel(file_path, index=False)

        result = load_transactions(file_path)
        assert result.empty


def test_load_user_settings_success() -> None:
    """Тест успешной загрузки пользовательских настроек"""
    test_settings = {
        "user_currencies": ["USD", "EUR"],
        "user_stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"],
    }

    with patch("builtins.open"), patch("json.load", return_value=test_settings):
        result = load_user_settings()
        assert result == test_settings


def test_load_user_settings_invalid_json() -> None:
    """Тест загрузки настроек с некорректным JSON"""
    with patch("builtins.open"), patch("json.load", side_effect=json.JSONDecodeError("Ошибка", "док", 0)):
        result = load_user_settings()
        expected_default = {
            "user_currencies": ["USD", "EUR"],
            "user_stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"],
        }
        assert result == expected_default


def test_load_user_settings_missing_currencies() -> None:
    """Тест загрузки настроек с отсутствующими валютами"""
    incomplete_settings = {"user_stocks": ["AAPL", "AMZN"]}

    with patch("builtins.open"), patch("json.load", return_value=incomplete_settings):
        result = load_user_settings()
        assert result["user_currencies"] == ["USD", "EUR"]
        assert result["user_stocks"] == ["AAPL", "AMZN"]


def test_load_user_settings_missing_stocks() -> None:
    """Тест загрузки настроек с отсутствующими акциями"""
    incomplete_settings = {"user_currencies": ["USD", "EUR"]}

    with patch("builtins.open"), patch("json.load", return_value=incomplete_settings):
        result = load_user_settings()
        assert result["user_currencies"] == ["USD", "EUR"]
        assert result["user_stocks"] == ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]


def test_load_user_settings_invalid_currencies_type() -> None:
    """Тест загрузки настроек с некорректным типом валют"""
    invalid_settings = {
        "user_currencies": "USD",
        "user_stocks": ["AAPL", "AMZN"],
    }

    with patch("builtins.open"), patch("json.load", return_value=invalid_settings):
        result = load_user_settings()
        assert result["user_currencies"] == ["USD", "EUR"]
        assert result["user_stocks"] == ["AAPL", "AMZN"]


def test_load_user_settings_invalid_stocks_type() -> None:
    """Тест загрузки настроек с некорректным типом акций"""
    invalid_settings = {
        "user_currencies": ["USD", "EUR"],
        "user_stocks": "AAPL",
    }

    with patch("builtins.open"), patch("json.load", return_value=invalid_settings):
        result = load_user_settings()
        assert result["user_currencies"] == ["USD", "EUR"]
        assert result["user_stocks"] == ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]


def test_load_user_settings_default() -> None:
    """Тест загрузки настроек по умолчанию при отсутствии файла"""
    with patch("builtins.open", side_effect=FileNotFoundError()):
        result = load_user_settings()
        expected_default = {
            "user_currencies": ["USD", "EUR"],
            "user_stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"],
        }
        assert result == expected_default


def test_get_date_range() -> None:
    """Тест получения диапазона дат для разных периодов"""
    date_str = "2023-06-15 12:00:00"

    start, end = get_date_range(date_str, "M")
    expected_start = datetime(2023, 6, 1, 12, 0, 0)
    expected_end = datetime(2023, 6, 15, 12, 0, 0)
    assert start == expected_start
    assert end == expected_end

    start, end = get_date_range(date_str, "W")
    expected_start = datetime(2023, 6, 12, 12, 0, 0)
    expected_end = datetime(2023, 6, 18, 12, 0, 0)
    assert start == expected_start
    assert end == expected_end

    start, end = get_date_range(date_str, "Y")
    expected_start = datetime(2023, 1, 1, 12, 0, 0)
    expected_end = datetime(2023, 6, 15, 12, 0, 0)
    assert start == expected_start
    assert end == expected_end

    start, end = get_date_range(date_str, "ALL")
    expected_start = datetime(1900, 1, 1)
    expected_end = datetime(2023, 6, 15, 12, 0, 0)
    assert start == expected_start
    assert end == expected_end


def test_filter_transactions_by_date() -> None:
    """Тест фильтрации транзакций по дате"""
    df = pd.DataFrame(
        {
            "Дата операции": pd.date_range("2023-01-01", periods=5, freq="D"),
            "Сумма операции": [100 * i for i in range(1, 6)],
        }
    )

    start_date = datetime(2023, 1, 2)
    end_date = datetime(2023, 1, 4)
    result = filter_transactions_by_date(df, start_date, end_date)
    assert len(result) == 3
    assert all(result["Дата операции"] >= start_date)
    assert all(result["Дата операции"] <= end_date)


def test_filter_transactions_no_date_column() -> None:
    """Тест фильтрации транзакций без колонки с датой"""
    df = pd.DataFrame(
        {
            "Сумма операции": [100, 200, 300],
            "Описание": ["A", "B", "C"],
        }
    )

    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 1, 31)
    result = filter_transactions_by_date(df, start_date, end_date)
    assert len(result) == 3
    pd.testing.assert_frame_equal(result, df)


def test_get_greeting_by_time() -> None:
    """Тест получения приветствия по времени суток"""
    assert get_greeting_by_time(5) == "Доброе утро"
    assert get_greeting_by_time(11) == "Доброе утро"
    assert get_greeting_by_time(12) == "Добрый день"
    assert get_greeting_by_time(16) == "Добрый день"
    assert get_greeting_by_time(17) == "Добрый вечер"
    assert get_greeting_by_time(22) == "Добрый вечер"
    assert get_greeting_by_time(23) == "Доброй ночи"
    assert get_greeting_by_time(4) == "Доброй ночи"


def test_convert_dataframe_to_dict_list() -> None:
    """Тест конвертации DataFrame в список словарей"""
    df = pd.DataFrame({"col1": [1, 2, None], "col2": ["A", "B", "C"]})

    result = convert_dataframe_to_dict_list(df)

    expected = [
        {"col1": 1, "col2": "A"},
        {"col1": 2, "col2": "B"},
        {"col1": None, "col2": "C"},
    ]

    assert len(result) == len(expected)
    for i, (res_dict, exp_dict) in enumerate(zip(result, expected)):
        for key in exp_dict:
            if exp_dict[key] is None and res_dict[key] is None:
                continue
            elif pd.isna(exp_dict[key]) and pd.isna(res_dict[key]):
                continue
            else:
                assert res_dict[key] == exp_dict[key], f"Несоответствие в элементе {i}, ключ {key}"


def test_convert_dataframe_to_dict_list_with_nan() -> None:
    """Тест конвертации DataFrame с NaN значениями"""
    df = pd.DataFrame(
        {
            "numeric_col": [1.0, np.nan, 3.0],
            "str_col": ["A", "B", None],
        }
    )

    result = convert_dataframe_to_dict_list(df)

    assert result[0]["numeric_col"] == 1.0
    assert pd.isna(result[1]["numeric_col"])
    assert result[2]["numeric_col"] == 3.0
    assert result[0]["str_col"] == "A"
    assert result[1]["str_col"] == "B"
    assert result[2]["str_col"] is None


def test_prepare_transactions_data() -> None:
    """Тест подготовки данных для анализа"""
    df = pd.DataFrame(
        {
            "Дата операции": pd.date_range("2023-01-01", periods=10, freq="D"),
            "Сумма операции": range(10),
        }
    )

    result = prepare_transactions_data(df, "2023-01-05 00:00:00", "M")
    assert len(result) == 5
    assert all(result["Дата операции"].dt.month == 1)
    assert all(result["Дата операции"].dt.day <= 5)


def test_get_api_key() -> None:
    """Тест получения API ключа из переменных окружения"""
    original_key = os.getenv("API_KEY")

    try:
        if "API_KEY" in os.environ:
            del os.environ["API_KEY"]
        assert get_api_key() == ""

        os.environ["API_KEY"] = "test_key_123"
        assert get_api_key() == "test_key_123"

    finally:
        if original_key is not None:
            os.environ["API_KEY"] = original_key
        elif "API_KEY" in os.environ:
            del os.environ["API_KEY"]


def test_get_api_key_with_mock() -> None:
    """Альтернативный тест получения API ключа с использованием мока"""
    with patch.dict(os.environ, {}, clear=True):
        assert get_api_key() == ""

    with patch.dict(os.environ, {"API_KEY": "mocked_key"}):
        assert get_api_key() == "mocked_key"


def test_load_transactions_with_invalid_status() -> None:
    """Тест загрузки транзакций с некорректным статусом"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_data = pd.DataFrame(
            {
                "Дата операции": ["01.01.2023 12:00:00"],
                "Сумма операции": [1000],
                "Статус": ["FAILED"],
            }
        )
        file_path = os.path.join(tmp_dir, "test_operations.xlsx")
        test_data.to_excel(file_path, index=False)

        result = load_transactions(file_path)
        assert len(result) == 0


def test_get_date_range_invalid_period() -> None:
    """Тест получения диапазона дат с некорректным периодом"""
    date_str = "2023-06-15 12:00:00"
    start, end = get_date_range(date_str, "INVALID")
    expected_start = datetime(2023, 6, 1, 12, 0, 0)
    expected_end = datetime(2023, 6, 15, 12, 0, 0)
    assert start == expected_start
    assert end == expected_end
