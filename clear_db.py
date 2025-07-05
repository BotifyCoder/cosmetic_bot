#!/usr/bin/env python3
"""
Скрипт для очистки базы данных от старых записей
"""

import asyncio
import os
from services.database import db

async def clear_database():
    """Очистка базы данных"""
    print("Очистка базы данных...")
    
    # Получаем все записи
    appointments = await db.get_all_appointments()
    print(f"Найдено записей: {len(appointments)}")
    
    # Удаляем все записи
    for appt in appointments:
        await db.delete_appointment(appt[0])
    
    print("✅ Все записи удалены")
    
    # Получаем все слоты
    slots = await db.get_all_slots()
    print(f"Найдено слотов: {len(slots)}")
    
    # Удаляем все слоты
    for slot in slots:
        await db.delete_slot(slot[0])
    
    print("✅ Все слоты удалены")
    print("\n🎉 База данных очищена!")

async def main():
    """Основная функция"""
    try:
        await clear_database()
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 