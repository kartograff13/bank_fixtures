import json
import os
from datetime import datetime, timedelta
from typing import Any, Tuple

import pandas as pd
from dotenv import load_dotenv

load_dotenv()


def load_transactions(file_path: str = "data/operations.xlsx") -> pd.DataFrame:
    """Функция загружает транзакции из Excel файла"""
    try:
        df = pd.read_excel(file_path)

        if "Дата операции" in df.columns:
            df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S", errors="coerce")
        if "Дата платежа" in df.columns:
            df["Дата платежа"] = pd.to_datetime(df["Дата платежа"], format="%d.%m.%Y %H:%M:%S", errors="coerce")

        numeric_columns = [
            "Сумма операции",
            "Сумма платежа",
            "Кэшбэк",
            "Бонусы (включая кэшбэк)",
            "Округление на инвесткопилку",
            "Сумма операции с округлением",
        ]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        if "Статус" in df.columns:
            df = df[df["Статус"] == "OK"]

        return df
    except Exception as e:
        print(f"Ошибка загрузки данных: {e}")
        return pd.DataFrame()


def load_user_settings() -> dict[str, list[str]]:
    """Функция загружает пользовательские настройки из JSON файла"""
    default_settings: dict[str, list[str]] = {
        "user_currencies": ["USD", "EUR"],
        "user_stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"],
    }

    try:
        with open("user_settings.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return default_settings

        result: dict[str, list[str]] = {}

        if "user_currencies" in data and isinstance(data["user_currencies"], list):
            result["user_currencies"] = [str(item) for item in data["user_currencies"]]
        else:
            result["user_currencies"] = default_settings["user_currencies"]

        if "user_stocks" in data and isinstance(data["user_stocks"], list):
            result["user_stocks"] = [str(item) for item in data["user_stocks"]]
        else:
            result["user_stocks"] = default_settings["user_stocks"]

        return result

    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return default_settings


def get_date_range(date_str: str, period: str = "M") -> Tuple[datetime, datetime]:
    """Функция для получения диапазона дат для анализа"""
    date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

    if period == "W":
        start_date = date - timedelta(days=date.weekday())
        end_date = start_date + timedelta(days=6)
    elif period == "M":
        start_date = date.replace(day=1)
        end_date = date
    elif period == "Y":
        start_date = date.replace(month=1, day=1)
        end_date = date
    elif period == "ALL":
        start_date = datetime(1900, 1, 1)
        end_date = date
    else:
        start_date = date.replace(day=1)
        end_date = date

    return start_date, end_date


def filter_transactions_by_date(transactions: pd.DataFrame, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Функция фильтрует транзакций по дате"""
    if "Дата операции" not in transactions.columns:
        return transactions

    mask = (transactions["Дата операции"] >= start_date) & (transactions["Дата операции"] <= end_date)
    return transactions[mask]


def get_greeting_by_time(hour: int) -> str:
    """Функция для получения приветствия в зависимости от времени суток"""
    if 5 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 17:
        return "Добрый день"
    elif 17 <= hour < 23:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def convert_dataframe_to_dict_list(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Функция конвертации DataFrame в список словарей для сервисов"""
    df_clean = df.where(pd.notnull(df), None)

    records = df_clean.to_dict("records")

    result: list[dict[str, Any]] = []
    for record in records:
        string_key_record: dict[str, Any] = {}
        for key, value in record.items():
            string_key_record[str(key)] = value
        result.append(string_key_record)

    return result


def prepare_transactions_data(transactions: pd.DataFrame, date_str: str, period: str = "M") -> pd.DataFrame:
    """Функция подготовки данных для анализа: фильтрация по дате и базовая обработка"""
    start_date, end_date = get_date_range(date_str, period)
    filtered_data = filter_transactions_by_date(transactions, start_date, end_date)
    return filtered_data


def get_api_key() -> str:
    """Функция для получения API ключа из переменных окружения .env"""
    return os.getenv("API_KEY", "")
