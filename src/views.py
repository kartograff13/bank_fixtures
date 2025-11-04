import logging
from datetime import datetime
from typing import Any

import pandas as pd
import requests

from src.utils import (
    filter_transactions_by_date,
    get_api_key,
    get_date_range,
    get_greeting_by_time,
    load_user_settings,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_fallback_exchange_rates(currencies: list[str]) -> list[dict[str, Any]]:
    """Функция заглушки курсов валют для тестирования"""
    fallback_rates = {"USD": 80.0, "EUR": 90.0, "GBP": 100.0}
    return [{"currency": curr, "rate": fallback_rates.get(curr, 1.0)} for curr in currencies if curr != "RUB"]


def get_fallback_rate(currency: str) -> float:
    """Функция заглушки для отдельной валюты"""
    rates = {"USD": 80.0, "EUR": 90.0, "GBP": 100.0}
    return rates.get(currency, 1.0)


def get_fallback_stock_prices(stocks: list[str]) -> list[dict[str, Any]]:
    """Функция заглушки цен акций для тестирования"""
    fallback_prices = {"AAPL": 150.0, "AMZN": 130.0, "GOOGL": 140.0, "MSFT": 300.0, "TSLA": 200.0}
    return [{"stock": stock, "price": fallback_prices.get(stock, 100.0)} for stock in stocks]


def get_fallback_stock_price(stock: str) -> float:
    """Функция заглушки для отдельной акции"""
    prices = {"AAPL": 150.0, "AMZN": 130.0, "GOOGL": 140.0, "MSFT": 300.0, "TSLA": 200.0}
    return prices.get(stock, 100.0)


def get_exchange_rates(currencies: list[str]) -> list[dict[str, Any]]:
    """Функция получения реальных курсов валют через Twelve Data API с заглушками"""
    api_key = get_api_key()
    if not api_key:
        logger.warning("API ключ не найден. Используем тестовые данные.")
        return get_fallback_exchange_rates(currencies)

    rates_list = []
    for currency in currencies:
        if currency == "RUB":
            rates_list.append({"currency": currency, "rate": 1.0})
            continue

        try:
            url = f"https://api.twelvedata.com/exchange_rate?symbol={currency}/RUB&apikey={api_key}"
            response = requests.get(url, timeout=10)
            data = response.json()

            if "rate" in data:
                rate_value = float(data["rate"])
                rates_list.append({"currency": currency, "rate": rate_value})
            else:
                logger.warning(f"Ошибка получения курса {currency}: {data}")
                rates_list.append({"currency": currency, "rate": get_fallback_rate(currency)})
                continue

        except (requests.RequestException, ValueError, KeyError) as e:
            logger.error(f"Ошибка при запросе курса {currency}: {e}")
            rates_list.append({"currency": currency, "rate": get_fallback_rate(currency)})
            continue

    return rates_list


def get_stock_prices(stocks: list[str]) -> list[dict[str, Any]]:
    """Функция получения реальных цен акций через Twelve Data API с заглушками"""
    api_key = get_api_key()
    if not api_key:
        logger.warning("API ключ не найден. Используем тестовые данные.")
        return get_fallback_stock_prices(stocks)

    prices_list = []
    try:
        symbols = ",".join(stocks)
        url = f"https://api.twelvedata.com/price?symbol={symbols}&apikey={api_key}"
        response = requests.get(url, timeout=10)
        data = response.json()

        for stock in stocks:
            if stock in data and "price" in data[stock]:
                price_value = float(data[stock]["price"])
                prices_list.append({"stock": stock, "price": price_value})
            else:
                logger.warning(f"Ошибка получения цены {stock}: {data.get(stock, 'Нет данных')}")
                prices_list.append({"stock": stock, "price": get_fallback_stock_price(stock)})
                continue

    except (requests.RequestException, ValueError, KeyError) as e:
        logger.error(f"Ошибка при запросе цен акций: {e}")
        return get_fallback_stock_prices(stocks)

    return prices_list


def main_page_data(transactions: pd.DataFrame, date_time: str) -> dict[str, Any]:
    """
    Главная функция для страницы 'Главная'

    Принимает:
    - transactions: DataFrame с транзакциями
    - date_time: строка в формате 'YYYY-MM-DD HH:MM:SS'

    Возвращает JSON-ответ со структурой:
    {
        "greeting": "Добрый день",
        "cards": [
            {
                "last_digits": "5814",
                "total_spent": 1262.00,
                "cashback": 12.62
            }
        ],
        "top_transactions": [
            {
                "date": "21.12.2021",
                "amount": 1198.23,
                "category": "Переводы",
                "description": "Перевод Кредитная карта. ТП 10.2 RUR"
            }
        ],
        "currency_rates": [
            {
                "currency": "USD",
                "rate": 73.21
            }
        ],
        "stock_prices": [
            {
                "stock": "AAPL",
                "price": 150.12
            }
        ]
    }
    """
    logger.info(f"Обработка запроса для главной страницы с датой: {date_time}")
    dt = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")
    greeting = get_greeting_by_time(dt.hour)
    logger.info(f"Сгенерировано приветствие: {greeting}")
    settings = load_user_settings()
    logger.info(f"Загружены настройки: {settings}")
    start_date, end_date = get_date_range(date_time, "M")
    filtered_transactions = filter_transactions_by_date(transactions, start_date, end_date)
    logger.info(f"Отфильтровано {len(filtered_transactions)} транзакций за период с {start_date} по {end_date}")
    cards_data: list[dict[str, Any]] = []
    if "Номер карты" in filtered_transactions.columns:
        for card in filtered_transactions["Номер карты"].unique():
            if pd.isna(card):
                continue

            card_transactions = filtered_transactions[filtered_transactions["Номер карты"] == card]
            expenses = card_transactions[card_transactions["Сумма операции"] < 0]
            total_spent = float(expenses["Сумма операции"].abs().sum())
            cashback = total_spent * 0.01

            cards_data.append(
                {
                    "last_digits": str(card)[-4:],
                    "total_spent": round(total_spent, 2),
                    "cashback": round(cashback, 2),
                }
            )

    logger.info(f"Проанализировано {len(cards_data)} карт")
    top_transactions_data: list[dict[str, Any]] = []
    if not filtered_transactions.empty:
        top_transactions = filtered_transactions.copy()
        top_transactions["abs_amount"] = top_transactions["Сумма операции"].abs()
        top_transactions = top_transactions.nlargest(5, "abs_amount")
        transactions_dict = top_transactions.to_dict("records")
        for transaction in transactions_dict:
            date_obj = transaction["Дата операции"]
            date_str = date_obj.strftime("%d.%m.%Y") if not pd.isna(date_obj) else "Нет даты"
            amount_value = transaction["Сумма операции"]
            amount_float = float(amount_value) if not pd.isna(amount_value) else 0.0
            top_transactions_data.append(
                {
                    "date": date_str,
                    "amount": amount_float,
                    "category": str(transaction.get("Категория", "Не указана")),
                    "description": str(transaction.get("Описание", "Нет описания")),
                }
            )

    logger.info(f"Найдено {len(top_transactions_data)} топ-транзакций")
    currency_rates = get_exchange_rates(settings["user_currencies"])
    logger.info(f"Получены курсы для {len(currency_rates)} валют")
    stock_prices = get_stock_prices(settings["user_stocks"])
    logger.info(f"Получены цены для {len(stock_prices)} акций")

    result = {
        "greeting": greeting,
        "cards": cards_data,
        "top_transactions": top_transactions_data,
        "currency_rates": currency_rates,
        "stock_prices": stock_prices,
    }

    logger.info("Успешно сформирован ответ для главной страницы")
    return result


def events_page_data(transactions: pd.DataFrame, date_time: str, period: str = "M") -> dict[str, Any]:
    """Функция генерации данных для страницы событий с учетом реальной структуры данных"""
    settings = load_user_settings()

    start_date, end_date = get_date_range(date_time, period)
    filtered_transactions = filter_transactions_by_date(transactions, start_date, end_date)
    expenses_data = filtered_transactions[filtered_transactions["Сумма операции"] < 0].copy()
    expenses_data["Абсолютная сумма"] = expenses_data["Сумма операции"].abs()
    total_expenses_value = float(expenses_data["Абсолютная сумма"].sum())
    category_expenses = expenses_data.groupby("Категория")["Абсолютная сумма"].sum().sort_values(ascending=False)
    top_categories = category_expenses.head(7)
    other_categories = category_expenses.iloc[7:].sum() if len(category_expenses) > 7 else 0
    main_categories = {str(cat): round(float(amount), 2) for cat, amount in top_categories.items()}
    if other_categories > 0:
        main_categories["Остальное"] = round(float(other_categories), 2)

    cash_transfers = expenses_data[expenses_data["Категория"].isin(["Наличные", "Переводы"])]
    cash_transfers_by_cat = cash_transfers.groupby("Категория")["Абсолютная сумма"].sum().sort_values(ascending=False)
    cash_transfers_data = {str(cat): round(float(amount), 2) for cat, amount in cash_transfers_by_cat.items()}
    income_data = filtered_transactions[filtered_transactions["Сумма операции"] > 0].copy()
    total_income_value = float(income_data["Сумма операции"].sum())
    income_by_category = income_data.groupby("Категория")["Сумма операции"].sum().sort_values(ascending=False)
    main_income = {str(cat): round(float(amount), 2) for cat, amount in income_by_category.items()}
    exchange_rates = get_exchange_rates(settings["user_currencies"])
    stock_prices = get_stock_prices(settings["user_stocks"])

    return {
        "expenses": {
            "total": round(total_expenses_value),
            "main_categories": main_categories,
            "cash_transfers": cash_transfers_data,
        },
        "income": {
            "total": round(total_income_value),
            "main_categories": main_income,
        },
        "exchange_rates": exchange_rates,
        "stock_prices": stock_prices,
    }
