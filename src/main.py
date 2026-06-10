import json
import os
import sys
from typing import Optional

from src.reports import spending_by_category, spending_by_weekday, spending_by_workday
from src.services import (
    investment_bank,
    profitable_cashback_categories,
    search_person_transfers,
    search_phone_numbers,
    simple_search,
)
from src.utils import convert_dataframe_to_dict_list, load_transactions
from src.views import events_page_data, main_page_data


def find_data_file() -> Optional[str]:
    """Функция для поиска файла с данными в разных возможных расположениях"""
    possible_paths = [
        "data/operations.xlsx",
        "../data/operations.xlsx",
        "./data/operations.xlsx",
        "operations.xlsx",
    ]

    for path in possible_paths:
        if os.path.exists(path):
            print(f"Найден файл данных: {path}")
            return path

    print("\n✗ Файл operations.xlsx не найден. Поиск в директориях:")
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".xlsx"):
                print(f"  Найден: {os.path.join(root, file)}")

    print("\nРекомендации:")
    print("1. Поместите файл operations.xlsx в папку data/ в корне проекта")
    print("2. Или укажите правильный путь к файлу в функции load_transactions()")
    print("3. Убедитесь, что файл существует и доступен для чтения")

    return None


def main() -> None:
    """Главная функция для демонстрации работы проекта"""
    print("=" * 60)
    print("ДЕМОНСТРАЦИЯ РАБОТЫ ПРОЕКТА АНАЛИЗА БАНКОВСКИХ ОПЕРАЦИЙ")
    print("=" * 60)

    print("\n1. ЗАГРУЗКА ДАННЫХ")
    print("-" * 40)

    data_file_path = find_data_file()

    if not data_file_path:
        print("\nОШИБКА: Файл с данными не найден.")
        print("Программа не может продолжить работу без файла operations.xlsx")
        sys.exit(1)

    transactions_df = load_transactions(data_file_path)
    print(f"Загружено транзакций: {len(transactions_df)}")

    if transactions_df.empty:
        print("ОШИБКА: Не удалось загрузить транзакции или файл пуст")
        sys.exit(1)

    transactions_list = convert_dataframe_to_dict_list(transactions_df)
    print(f"Сконвертировано записей для сервисов: {len(transactions_list)}")

    print("\nПервые 5 транзакций:")
    print("-" * 80)
    for i, transaction in enumerate(transactions_list[:5]):
        date_str = transaction.get("Дата операции", "Нет даты")
        description = transaction.get("Описание", "Нет описания")
        amount = transaction.get("Сумма операции", 0)
        category = transaction.get("Категория", "Не указана")

        print(f"{i + 1}. Дата: {date_str}")
        print(f"   Описание: {description}")
        print(f"   Сумма: {amount} руб.")
        print(f"   Категория: {category}")
        print(f"   Карта: {transaction.get('Номер карты', 'Не указана')}")
        print("-" * 80)

    print("\n2. ОТЧЕТЫ")
    print("-" * 40)

    report_date = "2021-12-31"

    print(f"\nОтчет по тратам в категории 'Супермаркеты' на {report_date}:")
    supermarket_report = spending_by_category(transactions_df, "Супермаркеты", report_date)
    if not supermarket_report.empty:
        print(supermarket_report.to_string(index=False))
    else:
        print("Нет данных за указанный период")

    print(f"\nСредние траты по дням недели на {report_date}:")
    weekday_report = spending_by_weekday(transactions_df, report_date)
    if not weekday_report.empty:
        print(weekday_report.to_string(index=False))
    else:
        print("Нет данных для отчета по дням недели")

    print(f"\nСредние траты по типам дней на {report_date}:")
    workday_report = spending_by_workday(transactions_df, report_date)
    if not workday_report.empty:
        print(workday_report.to_string(index=False))
    else:
        print("Нет данных для отчета по типам дней")

    print("\n3. СЕРВИСЫ")
    print("-" * 40)

    analysis_year = 2021
    analysis_month = 12

    cashback_analysis = profitable_cashback_categories(transactions_list, analysis_year, analysis_month)
    print(f"\nАнализ кешбэка за {analysis_month}/{analysis_year}:")
    if cashback_analysis:
        for category, cashback in list(cashback_analysis.items())[:5]:
            print(f"  {category}: {cashback:.2f} руб.")
    else:
        print("  Нет данных для анализа кешбэка")

    investment_month = "2021-12"
    investment_amount = investment_bank(investment_month, transactions_list, 10)
    print(f"\nСумма для инвесткопилки ({investment_month}): {investment_amount:.2f} руб.")

    search_results = simple_search(transactions_list, "Магнит")
    print(f"\nПоиск по 'Магнит': найдено {len(search_results)} транзакций")
    for i, transaction in enumerate(search_results[:3]):
        print(
            f"  {i + 1}. {transaction.get('Дата операции')} - "
            f"{transaction.get('Сумма операции')} руб. - "
            f"{transaction.get('Описание')}"
        )

    phone_transactions = search_phone_numbers(transactions_list)
    print(f"\nТранзакции с телефонными номерами: {len(phone_transactions)}")
    for i, transaction in enumerate(phone_transactions[:2]):
        print(f"  {i + 1}. {transaction.get('Дата операции')} - {transaction.get('Описание')}")

    person_transfers = search_person_transfers(transactions_list)
    print(f"Переводы физическим лицам: {len(person_transfers)}")
    for i, transaction in enumerate(person_transfers[:2]):
        print(
            f"  {i + 1}. {transaction.get('Дата операции')} - "
            f"{transaction.get('Описание')} - "
            f"{transaction.get('Сумма операции')} руб."
        )

    print("\n4. ПРЕДСТАВЛЕНИЯ (VIEWS)")
    print("-" * 40)

    analysis_datetime = "2021-12-31 23:59:59"
    main_data = main_page_data(transactions_df, analysis_datetime)

    print(f"\nГлавная страница - {main_data['greeting']}:")
    print(f"Карты: {len(main_data['cards'])}")
    for card in main_data["cards"][:3]:
        print(
            f"  Карта *{card['last_digits']}: потрачено {card['total_spent']} руб., " f"кешбэк {card['cashback']} руб."
        )

    print(f"Топ транзакций: {len(main_data['top_transactions'])}")
    for i, transaction in enumerate(main_data["top_transactions"][:3]):
        print(f"  {i + 1}. {transaction['date']} - {transaction['amount']} руб. - {transaction['category']}")

    print(f"Курсы валют: {len(main_data['currency_rates'])}")
    for rate in main_data["currency_rates"][:3]:
        print(f"  {rate['currency']}: {rate['rate']} руб.")

    print(f"Цены акций: {len(main_data['stock_prices'])}")
    for stock in main_data["stock_prices"][:3]:
        print(f"  {stock['stock']}: {stock['price']} $")

    events_data = events_page_data(transactions_df, analysis_datetime, "M")
    print("\nСтраница событий:")
    print(f"Общие расходы: {events_data['expenses']['total']} руб.")
    print("Основные категории расходов:")
    for category, amount in list(events_data["expenses"]["main_categories"].items())[:5]:
        print(f"  {category}: {amount} руб.")

    print(f"Общие доходы: {events_data['income']['total']} руб.")
    if events_data["income"]["main_categories"]:
        print("Основные категории доходов:")
        for category, amount in list(events_data["income"]["main_categories"].items())[:3]:
            print(f"  {category}: {amount} руб.")
    else:
        print("Нет данных по доходам")

    print("\n5. СОХРАНЕНИЕ РЕЗУЛЬТАТОВ")
    print("-" * 40)

    with open("main_page_example.json", "w", encoding="utf-8") as f:
        json.dump(main_data, f, ensure_ascii=False, indent=2, default=str)
    print("Пример главной страницы сохранен в main_page_example.json")

    with open("events_page_example.json", "w", encoding="utf-8") as f:
        json.dump(events_data, f, ensure_ascii=False, indent=2, default=str)
    print("Пример страницы событий сохранен в events_page_example.json")

    if "supermarket_report" in locals() and not supermarket_report.empty:
        supermarket_report.to_json("supermarket_report_example.json", orient="records", force_ascii=False, indent=2)
        print("Пример отчета по супермаркетам сохранен в supermarket_report_example.json")

    print("\n" + "=" * 60)
    print("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА!")
    print("=" * 60)


if __name__ == "__main__":
    main()
