import re
from datetime import datetime
from functools import reduce
from typing import Any

import pandas as pd


def profitable_cashback_categories(data: list[dict[str, Any]], year: int, month: int) -> dict[str, float]:
    """Функция анализа выгодности категорий повышенного кешбэка"""

    def filter_by_date(transaction: dict[str, Any]) -> bool:
        if "Дата операции" not in transaction or transaction["Дата операции"] is None:
            return False
        trans_date = transaction["Дата операции"]

        if isinstance(trans_date, (datetime, pd.Timestamp)):
            return trans_date.year == year and trans_date.month == month
        elif isinstance(trans_date, str):
            for fmt in ["%Y-%m-%d %H:%M:%S", "%d.%m.%Y %H:%M:%S", "%Y-%m-%d"]:
                try:
                    parsed_date = datetime.strptime(trans_date, fmt)
                    return parsed_date.year == year and parsed_date.month == month
                except ValueError:
                    continue
            return False
        return False

    monthly_transactions = list(filter(filter_by_date, data))

    def calculate_cashback(acc: dict[str, float], transaction: dict[str, Any]) -> dict[str, float]:
        amount_raw = transaction.get("Сумма операции", 0)
        if amount_raw is None:
            return acc

        try:
            if isinstance(amount_raw, str):
                amount_str = amount_raw.replace(",", ".").replace(" ", "")
                amount = float(amount_str)
            else:
                amount = float(amount_raw)
        except (ValueError, TypeError):
            return acc

        if amount >= 0:
            return acc

        category = str(transaction.get("Категория", "Другое"))
        cashback = abs(amount) * 0.01
        acc[category] = acc.get(category, 0.0) + cashback
        return acc

    return reduce(calculate_cashback, monthly_transactions, {})


def investment_bank(month: str, transactions: list[dict[str, Any]], limit: int) -> float:
    """Функция для расчета суммы для инвесткопилки через округление"""
    try:
        year, month_num = map(int, month.split("-"))
    except ValueError:
        return 0.0

    def filter_by_month(transaction: dict[str, Any]) -> bool:
        if "Дата операции" not in transaction or transaction["Дата операции"] is None:
            return False
        trans_date = transaction["Дата операции"]

        if isinstance(trans_date, (datetime, pd.Timestamp)):
            return trans_date.year == year and trans_date.month == month_num
        elif isinstance(trans_date, str):
            for fmt in ["%Y-%m-%d %H:%M:%S", "%d.%m.%Y %H:%M:%S", "%Y-%m-%d"]:
                try:
                    parsed_date = datetime.strptime(trans_date, fmt)
                    return parsed_date.year == year and parsed_date.month == month_num
                except ValueError:
                    continue
            return False
        return False

    monthly_transactions = list(filter(filter_by_month, transactions))

    def calculate_rounding(acc: float, transaction: dict[str, Any]) -> float:
        amount_raw = transaction.get("Сумма операции", 0)
        if amount_raw is None:
            return acc

        try:
            if isinstance(amount_raw, str):
                amount_str = amount_raw.replace(",", ".").replace(" ", "")
                amount = float(amount_str)
            else:
                amount = float(amount_raw)
        except (ValueError, TypeError):
            return acc

        if amount >= 0:
            return acc

        amount_abs = abs(amount)
        rounded_amount = ((amount_abs + limit - 1) // limit) * limit
        difference = rounded_amount - amount_abs
        return acc + max(difference, 0)

    return reduce(calculate_rounding, monthly_transactions, 0.0)


def simple_search(transactions: list[dict[str, Any]], search_query: str) -> list[dict[str, Any]]:
    """Функция простого поиска по описанию и категории"""

    def matches_query(transaction: dict[str, Any]) -> bool:
        description = str(transaction.get("Описание", "")).lower()
        category = str(transaction.get("Категория", "")).lower()
        query = search_query.lower()
        return query in description or query in category

    return list(filter(matches_query, transactions))


def search_phone_numbers(transactions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Функция поиска транзакций с телефонными номерами"""
    phone_pattern = r"(\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}"

    def has_phone_number(transaction: dict[str, Any]) -> bool:
        description = str(transaction.get("Описание", ""))
        return bool(re.search(phone_pattern, description))

    return list(filter(has_phone_number, transactions))


def search_person_transfers(transactions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Функция поиска переводов физическим лицам"""
    name_pattern = r"[А-Я][а-я]+\s[А-Я]\."

    def is_person_transfer(transaction: dict[str, Any]) -> bool:
        category = str(transaction.get("Категория", ""))
        description = str(transaction.get("Описание", ""))
        return category == "Переводы" and bool(re.search(name_pattern, description))

    return list(filter(is_person_transfer, transactions))
