import functools
import json
import os
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

import pandas as pd


def report_decorator(filename: Optional[str] = None, avoid_duplicates: bool = True) -> Callable:
    """Декоратор для записи результатов отчетов в файл с возможностью добавления"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)

            if isinstance(result, pd.DataFrame) and result.empty:
                print(f"Результат функции {func.__name__} пустой, пропускаем сохранение")
                return result

            if filename is None:
                output_filename = f"report_{func.__name__}.json"
            else:
                output_filename = filename

            try:
                if isinstance(result, pd.DataFrame):
                    new_records = result.to_dict("records")
                    timestamp = datetime.now().isoformat()
                    for record in new_records:
                        record["_timestamp"] = timestamp
                        record["_report_type"] = func.__name__
                        if avoid_duplicates:
                            record_content = {}
                            for k, v in record.items():
                                key_str = str(k)
                                if not key_str.startswith("_"):
                                    record_content[key_str] = v
                            record_hash = hash(frozenset(record_content.items()))
                            record["_hash"] = record_hash

                    existing_data = []
                    if os.path.exists(output_filename):
                        try:
                            with open(output_filename, "r", encoding="utf-8") as f:
                                existing_data = json.load(f)
                                if not isinstance(existing_data, list):
                                    existing_data = []
                        except (json.JSONDecodeError, Exception) as e:
                            print(f"Ошибка чтения существующего файла: {e}")
                            existing_data = []
                    if avoid_duplicates and existing_data:
                        existing_hashes = {r.get("_hash") for r in existing_data if "_hash" in r}
                        new_records = [r for r in new_records if r.get("_hash") not in existing_hashes]
                    if new_records:
                        combined_data = existing_data + new_records
                        with open(output_filename, "w", encoding="utf-8") as f:
                            json.dump(combined_data, f, ensure_ascii=False, indent=2)
                        action = "Дополнен" if existing_data else "Создан"
                        print(
                            f"{action} отчет: {output_filename} (+{len(new_records)} записей, "
                            f"всего: {len(combined_data)})"
                        )
                    else:
                        print(f"Отчет {output_filename} уже содержит эти данные, дополнение не требуется")
                else:
                    existing_data = []
                    if os.path.exists(output_filename):
                        try:
                            with open(output_filename, "r", encoding="utf-8") as f:
                                existing_data = json.load(f)
                        except (json.JSONDecodeError, Exception):
                            existing_data = []
                    timestamp = datetime.now().isoformat()
                    new_record = {"_timestamp": timestamp, "_report_type": func.__name__, "data": result}
                    combined_data = existing_data + [new_record]
                    with open(output_filename, "w", encoding="utf-8") as f:
                        json.dump(combined_data, f, ensure_ascii=False, indent=2)

                    action = "Дополнен" if existing_data else "Создан"
                    print(f"{action} отчет: {output_filename}")
            except Exception as e:
                print(f"Ошибка сохранения отчета {func.__name__}: {e}")
            return result

        return wrapper

    return decorator


@report_decorator(avoid_duplicates=True)
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    """Траты по категории за последние 3 месяца"""
    if date is None:
        end_date = datetime.now()
    else:
        end_date = datetime.strptime(date, "%Y-%m-%d")

    start_date = end_date - timedelta(days=90)
    filtered_data = transactions[
        (transactions["Дата операции"] >= start_date)
        & (transactions["Дата операции"] <= end_date)
        & (transactions["Категория"] == category)
    ].copy()

    if filtered_data.empty:
        return pd.DataFrame()

    filtered_data["Месяц"] = filtered_data["Дата операции"].dt.to_period("M")
    monthly_spending = filtered_data.groupby("Месяц")["Сумма операции"].sum().abs().reset_index()
    monthly_spending["Месяц"] = monthly_spending["Месяц"].astype(str)

    return monthly_spending


@report_decorator(avoid_duplicates=True)
def spending_by_weekday(transactions: pd.DataFrame, date: Optional[str] = None) -> pd.DataFrame:
    """Средние траты по дням недели за последние 3 месяца"""
    if date is None:
        end_date = datetime.now()
    else:
        end_date = datetime.strptime(date, "%Y-%m-%d")

    start_date = end_date - timedelta(days=90)
    filtered_data = transactions[
        (transactions["Дата операции"] >= start_date) & (transactions["Дата операции"] <= end_date)
    ].copy()

    if filtered_data.empty:
        return pd.DataFrame()

    filtered_data.loc[:, "День недели"] = filtered_data["Дата операции"].dt.day_name()
    filtered_data.loc[:, "Сумма"] = filtered_data["Сумма операции"].abs()

    weekday_mapping = {
        "Monday": "Понедельник",
        "Tuesday": "Вторник",
        "Wednesday": "Среда",
        "Thursday": "Четверг",
        "Friday": "Пятница",
        "Saturday": "Суббота",
        "Sunday": "Воскресенье",
    }

    filtered_data.loc[:, "День недели"] = filtered_data["День недели"].map(weekday_mapping)
    avg_spending = filtered_data.groupby("День недели")["Сумма"].mean().reset_index()

    return avg_spending


@report_decorator(avoid_duplicates=True)
def spending_by_workday(transactions: pd.DataFrame, date: Optional[str] = None) -> pd.DataFrame:
    """Средние траты в рабочие/выходные дни за последние 3 месяца"""
    if date is None:
        end_date = datetime.now()
    else:
        end_date = datetime.strptime(date, "%Y-%m-%d")

    start_date = end_date - timedelta(days=90)
    filtered_data = transactions[
        (transactions["Дата операции"] >= start_date) & (transactions["Дата операции"] <= end_date)
    ].copy()
    if filtered_data.empty:
        return pd.DataFrame()

    filtered_data.loc[:, "День типа"] = filtered_data["Дата операции"].dt.weekday.apply(
        lambda x: "Выходной" if x >= 5 else "Рабочий"
    )
    filtered_data.loc[:, "Сумма"] = filtered_data["Сумма операции"].abs()
    avg_spending = filtered_data.groupby("День типа")["Сумма"].mean().reset_index()

    return avg_spending
