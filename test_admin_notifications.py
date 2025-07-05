#!/usr/bin/env python3
"""
Тестовый скрипт для проверки уведомлений админу
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.database import db
from config import ADMIN_ID

async def test_admin_notifications():
    """Тестирует систему уведомлений админу"""
    print("🔔 Тестирование уведомлений админу...")
    
    try:
        # Инициализируем базу данных
        await db._create_tables()
        
        # Получаем все записи
        appointments = await db.get_all_appointments()
        print(f"📋 Всего записей в базе: {len(appointments)}")
        
        if appointments:
            print("\n📊 Последние записи:")
            for i, apt in enumerate(appointments[-3:], 1):  # Показываем последние 3
                print(f"\n{i}. Запись ID: {apt[0]}")
                print(f"   👤 Клиент: {apt[5]}")
                print(f"   📱 Телефон: {apt[7]}")
                print(f"   ⚠️ Аллергии: {apt[6]}")
                print(f"   💆‍♀️ Услуга: {apt[2]}")
                print(f"   📅 Дата: {apt[3]}")
                print(f"   ⏰ Время: {apt[4]}")
                print(f"   🆔 ID пользователя: {apt[1]}")
        
        print(f"\n👑 ID администратора: {ADMIN_ID}")
        print("✅ Система уведомлений готова к работе!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_admin_notifications()) 