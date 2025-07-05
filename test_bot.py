#!/usr/bin/env python3
"""
Скрипт для тестирования основных функций бота
"""

import asyncio
import os
from services.database import db

async def test_database():
    """Тестирование функций базы данных"""
    print("Тестирование базы данных...")
    
    # Создание таблиц
    await db._create_tables()
    print("✅ Таблицы созданы")
    
    # Добавление тестовых слотов
    await db.add_slot("15.06.2025", "10:00", "массаж")
    await db.add_slot("15.06.2025", "11:00", "массаж")
    await db.add_slot("16.06.2025", "14:00", "пилинг")
    print("✅ Тестовые слоты добавлены")
    
    # Получение доступных дат
    dates = await db.get_available_dates("массаж")
    print(f"✅ Доступные даты для массажа: {dates}")
    
    # Получение доступного времени
    times = await db.get_available_times("15.06.2025", "массаж")
    print(f"✅ Доступное время на 15.06.2025: {times}")
    
    # Добавление тестовой записи
    await db.add_appointment(
        user_id=123456789,
        service="массаж",
        date="15.06.2025",
        time="10:00",
        fio="Иванов Иван Иванович",
        allergies="Нет",
        phone="+7 (999) 123-45-67"
    )
    print("✅ Тестовая запись добавлена")
    
    # Получение всех записей
    appointments = await db.get_all_appointments()
    print(f"✅ Всего записей: {len(appointments)}")
    
    # Получение всех слотов
    slots = await db.get_all_slots()
    print(f"✅ Всего слотов: {len(slots)}")
    
    print("\n🎉 Все тесты пройдены успешно!")

async def main():
    """Основная функция"""
    try:
        await test_database()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        # Закрываем соединения с БД
        pass

if __name__ == "__main__":
    asyncio.run(main()) 