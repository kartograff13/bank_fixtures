from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from src.views import (
    events_page_data,
    get_exchange_rates,
    get_fallback_exchange_rates,
    get_fallback_rate,
    get_fallback_stock_price,
    get_fallback_stock_prices,
    get_stock_prices,
    main_page_data,
)


def test_get_fallback_exchange_rates() -> None:
    """Тест функции заглушки курсов валют"""
    currencies = ["USD", "EUR", "GBP", "RUB"]
    result = get_fallback_exchange_rates(currencies)

    assert len(result) == 3
    assert result[0]["currency"] == "USD"
    assert result[0]["rate"] == 80.0
    assert result[1]["currency"] == "EUR"
    assert result[1]["rate"] == 90.0


def test_get_fallback_rate() -> None:
    """Тест функции заглушки для отдельной валюты"""
    assert get_fallback_rate("USD") == 80.0
    assert get_fallback_rate("EUR") == 90.0
    assert get_fallback_rate("UNKNOWN") == 1.0


def test_get_fallback_stock_prices() -> None:
    """Тест функции заглушки цен акций"""
    stocks = ["AAPL", "AMZN", "UNKNOWN"]
    result = get_fallback_stock_prices(stocks)

    assert len(result) == 3
    assert result[0]["stock"] == "AAPL"
    assert result[0]["price"] == 150.0
    assert result[2]["price"] == 100.0


def test_get_fallback_stock_price() -> None:
    """Тест функции заглушки для отдельной акции"""
    assert get_fallback_stock_price("AAPL") == 150.0
    assert get_fallback_stock_price("UNKNOWN") == 100.0


def test_get_exchange_rates_without_api_key() -> None:
    """Тест получения курсов валют без API ключа"""
    with patch("src.views.get_api_key") as mock_api_key:
        mock_api_key.return_value = None
        currencies = ["USD", "EUR"]
        result = get_exchange_rates(currencies)

        assert len(result) == 2
        assert result[0]["currency"] == "USD"
        assert result[0]["rate"] == 80.0


def test_get_exchange_rates_with_api_success() -> None:
    """Тест успешного получения курсов валют через API"""
    with patch("src.views.get_api_key") as mock_api_key, patch("src.views.requests.get") as mock_get:
        mock_api_key.return_value = "test_api_key"
        mock_response = MagicMock()
        mock_response.json.return_value = {"rate": "75.5"}
        mock_get.return_value = mock_response

        currencies = ["USD"]
        result = get_exchange_rates(currencies)

        assert result[0]["currency"] == "USD"
        assert result[0]["rate"] == 75.5


def test_get_exchange_rates_with_api_failure() -> None:
    """Тест получения курсов валют при ошибке API"""
    with patch("src.views.get_api_key") as mock_api_key, patch("src.views.requests.get") as mock_get:
        mock_api_key.return_value = "test_api_key"
        mock_get.side_effect = requests.RequestException("API error")

        currencies = ["USD"]
        result = get_exchange_rates(currencies)

        assert result[0]["currency"] == "USD"
        assert result[0]["rate"] == 80.0


def test_get_exchange_rates_missing_rate_in_response() -> None:
    """Тест получения курсов валют, когда в ответе API нет ключа 'rate'"""
    with patch("src.views.get_api_key") as mock_api_key, patch("src.views.requests.get") as mock_get:
        mock_api_key.return_value = "test_api_key"
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "Invalid currency"}
        mock_get.return_value = mock_response

        currencies = ["USD"]
        result = get_exchange_rates(currencies)

        assert result[0]["currency"] == "USD"
        assert result[0]["rate"] == 80.0


def test_get_stock_prices_without_api_key() -> None:
    """Тест получения цен акций без API ключа"""
    with patch("src.views.get_api_key") as mock_api_key:
        mock_api_key.return_value = None
        stocks = ["AAPL", "AMZN"]
        result = get_stock_prices(stocks)

        assert len(result) == 2
        assert result[0]["stock"] == "AAPL"
        assert result[0]["price"] == 150.0


def test_get_stock_prices_with_api_success() -> None:
    """Тест успешного получения цен акций через API"""
    with patch("src.views.get_api_key") as mock_api_key, patch("src.views.requests.get") as mock_get:
        mock_api_key.return_value = "test_api_key"
        mock_response = MagicMock()
        mock_response.json.return_value = {"AAPL": {"price": "155.0"}, "AMZN": {"price": "135.0"}}
        mock_get.return_value = mock_response

        stocks = ["AAPL", "AMZN"]
        result = get_stock_prices(stocks)

        assert result[0]["stock"] == "AAPL"
        assert result[0]["price"] == 155.0
        assert result[1]["stock"] == "AMZN"
        assert result[1]["price"] == 135.0


def test_get_stock_prices_missing_price_in_response() -> None:
    """Тест получения цен акций, когда в ответе API нет цены для акции"""
    with patch("src.views.get_api_key") as mock_api_key, patch("src.views.requests.get") as mock_get, patch(
        "src.views.logger"
    ) as mock_logger:
        mock_api_key.return_value = "test_api_key"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "AAPL": {"price": "155.0"},
            "AMZN": {"error": "Stock not found"},
        }
        mock_get.return_value = mock_response

        stocks = ["AAPL", "AMZN"]
        result = get_stock_prices(stocks)
        aapl_stock = next(item for item in result if item["stock"] == "AAPL")
        assert aapl_stock["price"] == 155.0

        amzn_stock = next(item for item in result if item["stock"] == "AMZN")
        assert amzn_stock["price"] == 130.0

        mock_logger.warning.assert_called()


def test_get_stock_prices_stock_not_in_response() -> None:
    """Тест получения цен акций, когда акции нет в ответе API"""
    with patch("src.views.get_api_key") as mock_api_key, patch("src.views.requests.get") as mock_get, patch(
        "src.views.logger"
    ) as mock_logger:
        mock_api_key.return_value = "test_api_key"
        mock_response = MagicMock()
        mock_response.json.return_value = {"AAPL": {"price": "155.0"}}
        mock_get.return_value = mock_response

        stocks = ["AAPL", "AMZN"]
        result = get_stock_prices(stocks)

        aapl_stock = next(item for item in result if item["stock"] == "AAPL")
        assert aapl_stock["price"] == 155.0

        amzn_stock = next(item for item in result if item["stock"] == "AMZN")
        assert amzn_stock["price"] == 130.0

        mock_logger.warning.assert_called()


def test_stock_prices_api_failure() -> None:
    """Тест получения цен акций при ошибке API"""
    with patch("src.views.get_api_key") as mock_api_key, patch("src.views.requests.get") as mock_get:
        mock_api_key.return_value = "test_api_key"
        mock_get.side_effect = requests.RequestException("API error")

        stocks = ["AAPL"]
        result = get_stock_prices(stocks)

        assert result[0]["stock"] == "AAPL"
        assert result[0]["price"] == 150.0


def create_test_transactions() -> pd.DataFrame:
    """Создание тестового DataFrame с транзакциями"""
    data = {
        "Дата операции": [
            datetime(2023, 12, 1),
            datetime(2023, 12, 2),
            datetime(2023, 12, 3),
            datetime(2023, 12, 4),
        ],
        "Номер карты": ["1234567890123456", "1234567890123456", "9876543210987654", "9876543210987654"],
        "Сумма операции": [-1000.0, -500.0, -2000.0, 3000.0],
        "Категория": ["Супермаркеты", "Рестораны", "Переводы", "Зарплата"],
        "Описание": ["Покупка в магазине", "Ужин в ресторане", "Перевод другу", "Зарплата"],
    }
    return pd.DataFrame(data)


def create_test_transactions_many_categories() -> pd.DataFrame:
    """Создание тестового DataFrame с большим количеством категорий"""
    data = {
        "Дата операции": [datetime(2023, 12, i) for i in range(1, 11)],
        "Сумма операции": [-100.0] * 10,
        "Категория": [
            "Категория1",
            "Категория2",
            "Категория3",
            "Категория4",
            "Категория5",
            "Категория6",
            "Категория7",
            "Категория8",
            "Категория9",
            "Категория10",
        ],
    }
    return pd.DataFrame(data)


def test_main_page_data() -> None:
    """Тест главной функции для страницы 'Главная'"""
    test_transactions = create_test_transactions()
    date_time = "2023-12-15 12:00:00"

    with patch("src.views.load_user_settings") as mock_settings, patch(
        "src.views.get_exchange_rates"
    ) as mock_rates, patch("src.views.get_stock_prices") as mock_stocks, patch(
        "src.views.get_date_range"
    ) as mock_date_range, patch(
        "src.views.filter_transactions_by_date"
    ) as mock_filter:
        mock_date_range.return_value = ("2023-12-01", "2023-12-31")
        mock_filter.return_value = test_transactions

        mock_settings.return_value = {"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "AMZN"]}
        mock_rates.return_value = [{"currency": "USD", "rate": 75.0}]
        mock_stocks.return_value = [{"stock": "AAPL", "price": 150.0}]

        result = main_page_data(test_transactions, date_time)

        assert "greeting" in result
        assert "cards" in result
        assert "top_transactions" in result
        assert "currency_rates" in result
        assert "stock_prices" in result
        assert len(result["cards"]) == 2

        card_3456 = next((card for card in result["cards"] if card["last_digits"] == "3456"), None)

        assert card_3456 is not None
        assert card_3456["total_spent"] == 1500.0
        assert len(result["top_transactions"]) == 4


def test_main_page_data_empty_transactions() -> None:
    """Тест главной функции с пустыми транзакциями"""
    empty_transactions = pd.DataFrame()
    date_time = "2023-12-15 12:00:00"

    with patch("src.views.load_user_settings") as mock_settings, patch(
        "src.views.get_exchange_rates"
    ) as mock_rates, patch("src.views.get_stock_prices") as mock_stocks, patch(
        "src.views.get_date_range"
    ) as mock_date_range, patch(
        "src.views.filter_transactions_by_date"
    ) as mock_filter:
        mock_date_range.return_value = ("2023-12-01", "2023-12-31")
        mock_filter.return_value = empty_transactions

        mock_settings.return_value = {"user_currencies": ["USD"], "user_stocks": ["AAPL"]}
        mock_rates.return_value = [{"currency": "USD", "rate": 75.0}]
        mock_stocks.return_value = [{"stock": "AAPL", "price": 150.0}]

        result = main_page_data(empty_transactions, date_time)

        assert result["cards"] == []
        assert result["top_transactions"] == []


def test_events_page_data() -> None:
    """Тест функции генерации данных для страницы событий"""
    test_transactions = create_test_transactions()
    date_time = "2023-12-15 12:00:00"

    with patch("src.views.load_user_settings") as mock_settings, patch(
        "src.views.get_exchange_rates"
    ) as mock_rates, patch("src.views.get_stock_prices") as mock_stocks, patch(
        "src.views.get_date_range"
    ) as mock_date_range, patch(
        "src.views.filter_transactions_by_date"
    ) as mock_filter:
        mock_date_range.return_value = ("2023-12-01", "2023-12-31")
        mock_filter.return_value = test_transactions

        mock_settings.return_value = {"user_currencies": ["USD"], "user_stocks": ["AAPL"]}
        mock_rates.return_value = [{"currency": "USD", "rate": 75.0}]
        mock_stocks.return_value = [{"stock": "AAPL", "price": 150.0}]

        result = events_page_data(test_transactions, date_time, "M")

        assert "expenses" in result
        assert "income" in result
        assert "exchange_rates" in result
        assert "stock_prices" in result

        assert result["expenses"]["total"] == 3500
        assert "Супермаркеты" in result["expenses"]["main_categories"]
        assert "Переводы" in result["expenses"]["cash_transfers"]

        assert result["income"]["total"] == 3000
        assert "Зарплата" in result["income"]["main_categories"]


def test_events_page_data_more_than_7_categories() -> None:
    """Тест функции events_page_data с более чем 7 категориями (проверка 'Остальное')"""
    test_transactions = create_test_transactions_many_categories()
    date_time = "2023-12-15 12:00:00"

    with patch("src.views.load_user_settings") as mock_settings, patch(
        "src.views.get_exchange_rates"
    ) as mock_rates, patch("src.views.get_stock_prices") as mock_stocks, patch(
        "src.views.get_date_range"
    ) as mock_date_range, patch(
        "src.views.filter_transactions_by_date"
    ) as mock_filter:
        mock_date_range.return_value = ("2023-12-01", "2023-12-31")
        mock_filter.return_value = test_transactions

        mock_settings.return_value = {"user_currencies": ["USD"], "user_stocks": ["AAPL"]}
        mock_rates.return_value = [{"currency": "USD", "rate": 75.0}]
        mock_stocks.return_value = [{"stock": "AAPL", "price": 150.0}]

        result = events_page_data(test_transactions, date_time, "M")

        assert "Остальное" in result["expenses"]["main_categories"]
        assert result["expenses"]["main_categories"]["Остальное"] == 300.0
        assert len(result["expenses"]["main_categories"]) == 8
        assert result["expenses"]["total"] == 1000.0


def test_events_page_data_exactly_7_categories() -> None:
    """Тест функции events_page_data с ровно 7 категориями (без 'Остальное')"""
    data = {
        "Дата операции": [datetime(2023, 12, i) for i in range(1, 8)],
        "Сумма операции": [-100.0] * 7,
        "Категория": [f"Категория{i}" for i in range(1, 8)],
    }
    test_transactions = pd.DataFrame(data)

    date_time = "2023-12-15 12:00:00"

    with patch("src.views.load_user_settings") as mock_settings, patch(
        "src.views.get_exchange_rates"
    ) as mock_rates, patch("src.views.get_stock_prices") as mock_stocks, patch(
        "src.views.get_date_range"
    ) as mock_date_range, patch(
        "src.views.filter_transactions_by_date"
    ) as mock_filter:
        mock_date_range.return_value = ("2023-12-01", "2023-12-31")
        mock_filter.return_value = test_transactions

        mock_settings.return_value = {"user_currencies": ["USD"], "user_stocks": ["AAPL"]}
        mock_rates.return_value = [{"currency": "USD", "rate": 75.0}]
        mock_stocks.return_value = [{"stock": "AAPL", "price": 150.0}]

        result = events_page_data(test_transactions, date_time, "M")

        assert "Остальное" not in result["expenses"]["main_categories"]
        assert len(result["expenses"]["main_categories"]) == 7


def test_events_page_data_different_period() -> None:
    """Тест функции events_page_data с разными периодами"""
    test_transactions = create_test_transactions()
    date_time = "2023-12-15 12:00:00"

    with patch("src.views.load_user_settings") as mock_settings, patch(
        "src.views.get_exchange_rates"
    ) as mock_rates, patch("src.views.get_stock_prices") as mock_stocks, patch(
        "src.views.get_date_range"
    ) as mock_date_range, patch(
        "src.views.filter_transactions_by_date"
    ) as mock_filter:
        mock_date_range.return_value = ("2023-12-01", "2023-12-31")
        mock_filter.return_value = test_transactions

        mock_settings.return_value = {"user_currencies": ["USD"], "user_stocks": ["AAPL"]}
        mock_rates.return_value = [{"currency": "USD", "rate": 75.0}]
        mock_stocks.return_value = [{"stock": "AAPL", "price": 150.0}]

        for period in ["D", "W", "M", "Q", "Y"]:
            result = events_page_data(test_transactions, date_time, period)
            assert "expenses" in result
            assert "income" in result


def test_rub_currency_in_exchange_rates() -> None:
    """Тест обработки RUB валюты в курсах обмена"""
    with patch("src.views.get_api_key") as mock_api_key:
        mock_api_key.return_value = "test_key"

        currencies = ["RUB", "USD"]
        result = get_exchange_rates(currencies)
        rub_currency = [item for item in result if item["currency"] == "RUB"][0]
        assert rub_currency["rate"] == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
