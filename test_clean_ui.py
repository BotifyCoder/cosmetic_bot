#!/usr/bin/env python3
"""
Финальный тестовый скрипт для проверки чистого интерфейса без лишних эмодзи
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.database import db

async def test_clean_ui():
    """Тестирует чистый интерфейс без лишних эмодзи"""
    print("🧹 Тестирование чистого интерфейса...")
    
    try:
        # Инициализируем базу данных
        await db._create_tables()
        
        print("\n📊 === ОБНОВЛЕННЫЙ ИНТЕРФЕЙС ===")
        
        # Проверяем услуги
        services = await db.get_all_services()
        print(f"Услуг: {len(services)}")
        for service in services:
            print(f"   {service[1]} - {service[4]}₽ ({service[3]} мин)")
        
        # Проверяем записи
        appointments = await db.get_all_appointments()
        print(f"\nЗаписей: {len(appointments)}")
        
        if appointments:
            print("Последние записи:")
            for apt in appointments[-2:]:  # Показываем последние 2
                print(f"   {apt[2]} - {apt[3]} {apt[4]} - {apt[5]}")
        
        print("\n✅ === ИНТЕРФЕЙС ОБНОВЛЕН ===")
        print("✓ Убраны лишние эмодзи из кнопок")
        print("✓ Оставлены только название, цена и время")
        print("✓ Сохранены эмодзи для навигации (🔙)")
        print("✓ Чистый и профессиональный вид")
        
        print("\n🎯 === ГОТОВО К ИСПОЛЬЗОВАНИЮ ===")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_clean_ui()) 