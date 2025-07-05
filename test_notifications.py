#!/usr/bin/env python3
"""
Тестовый скрипт для проверки системы уведомлений
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.database import db
from datetime import datetime, timedelta

async def test_notifications():
    """Тестирует систему уведомлений"""
    print("🧪 Тестирование системы уведомлений...")
    
    try:
        # Получаем все записи
        appointments = await db.get_all_appointments()
        print(f"📋 Всего записей в базе: {len(appointments)}")
        
        if not appointments:
            print("❌ Нет записей для тестирования")
            return
        
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        one_hour_later = now + timedelta(hours=1)
        
        print(f"🕐 Текущее время: {now.strftime('%d.%m.%Y %H:%M')}")
        print(f"📅 Завтра: {tomorrow.strftime('%d.%m.%Y')}")
        print(f"⏰ Через час: {one_hour_later.strftime('%H:%M')}")
        
        # Проверяем записи на завтра
        tomorrow_appointments = await db.get_appointments_by_date(tomorrow.strftime("%d.%m.%Y"))
        print(f"📅 Записей на завтра: {len(tomorrow_appointments)}")
        
        for apt in tomorrow_appointments:
            print(f"  - {apt[2]} в {apt[4]} (пользователь {apt[1]})")
        
        # Проверяем записи через час
        hour_appointments = await db.get_appointments_by_time(one_hour_later.strftime("%H:%M"))
        print(f"⏰ Записей через час: {len(hour_appointments)}")
        
        for apt in hour_appointments:
            print(f"  - {apt[2]} в {apt[4]} (пользователь {apt[1]})")
        
        print("\n✅ Тестирование завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_notifications()) 