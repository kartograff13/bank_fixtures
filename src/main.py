import json

import pandas as pd

from src.reports import spending_by_category, spending_by_weekday, spending_by_workday
from src.services import (investment_bank, profitable_cashback_categories, search_person_transfers,
                          search_phone_numbers, simple_search)
from src.utils import convert_dataframe_to_dict_list, load_transactions, load_user_settings, prepare_transactions_data
from src.views import events_page_data, main_page_data


def main() -> None:
    """Главная функция для демонстрации работы всех модулей с ограниченными данными"""

    print("=" * 50)
    print("БАНКОВСКИЙ АНАЛИЗАТОР - ДЕМОНСТРАЦИЯ РАБОТЫ")
    print("=" * 50)
    print("\n1. ЗАГРУЗКА ДАННЫХ...")

    transactions_df = load_transactions()
    if transactions_df.empty:
        print("Не удалось загрузить данные транзакций")
        return

    if len(transactions_df) > 20:
        transactions_df = transactions_df.head(20)
        print(f"Загружено первых 20 транзакций из {len(load_transactions())} доступных")
    else:
        print(f"Загружено {len(transactions_df)} транзакций")

    settings = load_user_settings()
    print(f"Загружены настройки: {settings}")

    transactions_list = convert_dataframe_to_dict_list(transactions_df)
    target_date = "2021-12-31 14:30:00"
    january_transactions = prepare_transactions_data(transactions_df, target_date, "M")
    january_transactions_list = convert_dataframe_to_dict_list(january_transactions)

    print(f"Подготовлены данные за период: {target_date}")
    print("\n" + "=" * 50)
    print("2. МОДУЛЬ VIEWS (ВИЗУАЛИЗАЦИЯ)")
    print("=" * 50)
    print("\nГЛАВНАЯ СТРАНИЦА:")

    main_data = main_page_data(transactions_df, target_date)
    print(f"   Приветствие: {main_data['greeting']}")
    print(f"   Карты: {len(main_data['cards'])}")

    for card in main_data["cards"]:
        print(
            f"     Карта ***{card['last_digits']}: {card['total_spent']} руб. потрачено, кешбэк: {card['cashback']} руб."
        )
    print(f"   Топ транзакций: {len(main_data['top_transactions'])}")
    print(f"   Курсы валют: {len(main_data['currency_rates'])}")
    print(f"   Цены акций: {len(main_data['stock_prices'])}")
    print("\nСТРАНИЦА СОБЫТИЙ:")

    events_data = events_page_data(transactions_df, target_date, "M")
    print(f"   Общие расходы: {events_data['expenses']['total']} руб.")
    print(f"   Общие поступления: {events_data['income']['total']} руб.")
    print(f"   Основные категории расходов: {len(events_data['expenses']['main_categories'])}")
    print("\n" + "=" * 50)
    print("3. МОДУЛЬ SERVICES (СЕРВИСЫ АНАЛИЗА)")
    print("=" * 50)
    print("\nАНАЛИЗ КЕШБЭКА:")

    cashback_categories = profitable_cashback_categories(january_transactions_list, 2021, 12)
    if cashback_categories:
        for category, cashback in list(cashback_categories.items())[:3]:
            print(f"   {category}: {cashback:.2f} руб. кешбэка")
    else:
        print("   Нет данных по кешбэку")

    print("\nИНВЕСТКОПИЛКА:")

    investment = investment_bank("2021-12", january_transactions_list, 50)
    print(f"   Сумма для инвесткопилки за декабрь 2021: {investment:.2f} руб.")
    print("\nПОИСК ТРАНЗАКЦИЙ:")

    search_results = simple_search(transactions_list, "магазин")
    print(f"   Найдено по запросу 'магазин': {len(search_results)} транзакций")

    phone_transactions = search_phone_numbers(transactions_list)
    print(f"   Транзакций с телефонными номерами: {len(phone_transactions)}")

    person_transfers = search_person_transfers(transactions_list)
    print(f"   Переводов физическим лицам: {len(person_transfers)}")
    print("\n" + "=" * 50)
    print("4. МОДУЛЬ REPORTS (ОТЧЕТЫ)")
    print("=" * 50)
    print("\nОТЧЕТЫ ПО КАТЕГОРИЯМ:")

    category_report = spending_by_category(transactions_df, "Супермаркеты", "2021-12-31")
    if not category_report.empty:
        print("   Траты по категории 'Супермаркеты' за 3 месяца:")
        for _, row in category_report.iterrows():
            amount_value = row["Сумма операции"]
            if pd.notna(amount_value):
                amount = abs(float(amount_value.item()))
            else:
                amount = 0.0
            month_value = row["Месяц"]
            month_str = str(month_value) if pd.notna(month_value) else "Нет данных"
            print(f"     {month_str}: {amount:.2f} руб.")
    else:
        print("   Нет данных по категории 'Супермаркеты'")

    print("\nОТЧЕТ ПО ДНЯМ НЕДЕЛИ:")

    weekday_report = spending_by_weekday(transactions_df, "2021-12-31")
    if not weekday_report.empty:
        print("   Средние траты по дням недели:")
        for _, row in weekday_report.iterrows():
            amount_value = row["Сумма"]
            if pd.notna(amount_value):
                amount = float(amount_value.item())
            else:
                amount = 0.0
            day_value = row["День недели"]
            day_str = str(day_value) if pd.notna(day_value) else "Нет данных"
            print(f"     {day_str}: {amount:.2f} руб.")
    else:
        print("   Нет данных для анализа по дням недели")

    print("\nОТЧЕТ ПО ТИПАМ ДНЕЙ:")

    workday_report = spending_by_workday(transactions_df, "2021-12-31")
    if not workday_report.empty:
        print("   Средние траты по типам дней:")
        for _, row in workday_report.iterrows():
            amount_value = row["Сумма"]
            if pd.notna(amount_value):
                amount = float(amount_value.item())
            else:
                amount = 0.0
            day_type_value = row["День типа"]
            day_type_str = str(day_type_value) if pd.notna(day_type_value) else "Нет данных"
            print(f"     {day_type_str}: {amount:.2f} руб.")
    else:
        print("   Нет данных для анализа по типам дней")

    print("\n" + "=" * 50)
    print("5. СОХРАНЕНИЕ РЕЗУЛЬТАТОВ")
    print("=" * 50)

    try:
        with open("demo_main_page.json", "w", encoding="utf-8") as f:
            json.dump(main_data, f, ensure_ascii=False, indent=2)
        print("Данные главной страницы сохранены в demo_main_page.json")

        with open("demo_events_page.json", "w", encoding="utf-8") as f:
            json.dump(events_data, f, ensure_ascii=False, indent=2)
        print("Данные страницы событий сохранены в demo_events_page.json")

        with open("demo_services.json", "w", encoding="utf-8") as f:
            services_data = {
                "cashback_categories": cashback_categories,
                "investment": investment,
                "search_results_count": len(search_results),
                "phone_transactions_count": len(phone_transactions),
                "person_transfers_count": len(person_transfers),
            }
            json.dump(services_data, f, ensure_ascii=False, indent=2)
        print("Данные сервисов сохранены в demo_services.json")

    except Exception as e:
        print(f"Ошибка сохранения демо-данных: {e}")

    print("\n" + "=" * 50)
    print("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА!")
    print("=" * 50)
    print("\nСозданные файлы:")
    print("- report_spending_by_category.json")
    print("- report_spending_by_weekday.json")
    print("- report_spending_by_workday.json")
    print("- demo_main_page.json")
    print("- demo_events_page.json")
    print("- demo_services.json")


if __name__ == "__main__":
    main()
