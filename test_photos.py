#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы с фотографиями услуг
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.database import db

async def test_photos():
    """Тестирует работу с фотографиями услуг"""
    print("📸 Тестирование работы с фотографиями услуг...")
    
    try:
        # Инициализируем базу данных
        await db._create_tables()
        
        # Получаем все услуги
        services = await db.get_all_services()
        print(f"📋 Всего услуг: {len(services)}")
        
        for service in services:
            print(f"\n💆‍♀️ Услуга: {service[1]}")
            print(f"   ID: {service[0]}")
            print(f"   Описание: {service[2]}")
            print(f"   Длительность: {service[3]} мин")
            print(f"   Цена: {service[4]}₽")
            print(f"   Фото: {service[5] if len(service) > 5 else 'Нет'}")
            
            # Проверяем существование файла
            if len(service) > 5 and service[5]:
                if os.path.exists(service[5]):
                    print(f"   ✅ Файл существует: {service[5]}")
                    file_size = os.path.getsize(service[5])
                    print(f"   📁 Размер файла: {file_size} байт")
                else:
                    print(f"   ❌ Файл не найден: {service[5]}")
            else:
                print("   📷 Фотография не установлена")
        
        print("\n✅ Тестирование завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_photos()) 