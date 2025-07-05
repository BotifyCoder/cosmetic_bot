#!/usr/bin/env python3
"""
Тестовый скрипт для проверки обновленных клавиатур без эмодзи
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from keyboards.inline_keyboards import get_service_keyboard, get_date_keyboard, get_time_keyboard, get_allergies_keyboard, get_confirmation_keyboard

async def test_keyboards():
    """Тестирует обновленные клавиатуры"""
    print("🎯 Тестирование клавиатур без эмодзи...")
    
    try:
        # Инициализируем базу данных
        from services.database import db
        await db._create_tables()
        
        print("\n📋 === КЛАВИАТУРА УСЛУГ ===")
        service_keyboard = await get_service_keyboard()
        for row in service_keyboard.inline_keyboard:
            for button in row:
                print(f"   {button.text}")
        
        print("\n📅 === КЛАВИАТУРА ДАТ ===")
        # Тестовые даты
        test_dates = ["15.07.2025", "16.07.2025", "17.07.2025"]
        date_keyboard = get_date_keyboard("Массаж лица", test_dates)
        for row in date_keyboard.inline_keyboard:
            for button in row:
                print(f"   {button.text}")
        
        print("\n⏰ === КЛАВИАТУРА ВРЕМЕНИ ===")
        # Тестовое время
        test_times = ["10:00", "14:00", "18:00"]
        time_keyboard = get_time_keyboard("15.07.2025", "Массаж лица", test_times)
        for row in time_keyboard.inline_keyboard:
            for button in row:
                print(f"   {button.text}")
        
        print("\n⚠️ === КЛАВИАТУРА АЛЛЕРГИЙ ===")
        allergies_keyboard = get_allergies_keyboard()
        for row in allergies_keyboard.inline_keyboard:
            for button in row:
                print(f"   {button.text}")
        
        print("\n✅ === КЛАВИАТУРА ПОДТВЕРЖДЕНИЯ ===")
        confirmation_keyboard = get_confirmation_keyboard()
        for row in confirmation_keyboard.inline_keyboard:
            for button in row:
                print(f"   {button.text}")
        
        print("\n✅ Клавиатуры обновлены и готовы к использованию!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_keyboards()) 