from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from services.database import db
import asyncio
import os

async def get_service_keyboard():
    """Получает клавиатуру с услугами из базы данных"""
    services = await db.get_all_services()
    buttons = []
    for service in services:
        # Форматирование: название, цена и время
        price_text = f" {service[4]}₽" if service[4] and service[4] > 0 else ""
        duration_text = f" ({service[3]} мин)" if service[3] else ""
        button_text = f"{service[1]}{price_text}{duration_text}"
        
        buttons.append([InlineKeyboardButton(
            text=button_text,
            callback_data=f"service_{service[1]}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def send_services_with_photos(bot, chat_id, message_text="🌟 Выберите услугу, которая вас интересует:"):
    """Отправляет услуги с фотографиями"""
    services = await db.get_all_services()
    
    if not services:
        await bot.send_message(chat_id, "❌ К сожалению, услуги временно недоступны.")
        return
    
    # Отправляем первую услугу с фотографией
    first_service = services[0]
    keyboard = await get_service_keyboard()
    
    # Проверяем, есть ли фотография у первой услуги
    if first_service[5] and os.path.exists(first_service[5]):  # photo_path
        try:
            photo = FSInputFile(first_service[5])
            await bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=message_text,
                reply_markup=keyboard
            )
        except Exception as e:
            # Если не удалось отправить фото, отправляем обычное сообщение
            await bot.send_message(chat_id, message_text, reply_markup=keyboard)
    else:
        # Если нет фотографии, отправляем обычное сообщение
        await bot.send_message(chat_id, message_text, reply_markup=keyboard)

def get_date_keyboard(service, dates):
    if not dates:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📅 Нет доступных дат", callback_data="none")],
            [InlineKeyboardButton(text="🔙 Назад к услугам", callback_data="back_to_service")]
        ])
    
    buttons = []
    for date in dates:
        # Форматирование даты с днем недели
        try:
            from datetime import datetime
            date_obj = datetime.strptime(date, '%d.%m.%Y')
            day_name = date_obj.strftime('%A')
            day_names = {
                'Monday': 'Пн', 'Tuesday': 'Вт', 'Wednesday': 'Ср', 
                'Thursday': 'Чт', 'Friday': 'Пт', 'Saturday': 'Сб', 'Sunday': 'Вс'
            }
            day_text = day_names.get(day_name, '')
            button_text = f"📅 {date} ({day_text})"
        except:
            button_text = f"📅 {date}"
        
        buttons.append([InlineKeyboardButton(text=button_text, callback_data=f"date_{date}_{service}")])
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад к услугам", callback_data="back_to_service")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_time_keyboard(date, service, times):
    if not times:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏰ Нет доступного времени", callback_data="none")],
            [InlineKeyboardButton(text="🔙 Назад к датам", callback_data=f"back_to_date_{service}")]
        ])
    
    buttons = []
    for time in times:
        # Форматирование времени
        button_text = f"⏰ {time}"
        buttons.append([InlineKeyboardButton(text=button_text, callback_data=f"time_{time}_{date}_{service}")])
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад к датам", callback_data=f"back_to_date_{service}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_allergies_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⚠️ Да, есть аллергии", callback_data="allergy_yes"),
                InlineKeyboardButton(text="✅ Нет аллергий", callback_data="allergy_no")
            ],
            [InlineKeyboardButton(text="🔙 Назад к ФИО", callback_data="back_to_fio")]
        ]
    )

def get_confirmation_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить запись", callback_data="confirm_booking")],
            [InlineKeyboardButton(text="❌ Отменить запись", callback_data="cancel_booking")],
            [InlineKeyboardButton(text="🔙 Назад к телефону", callback_data="back_to_phone")]
        ]
    )

def get_admin_appointment_keyboard(appointments):
    buttons = []
    for appt in appointments:
        buttons.append([
            InlineKeyboardButton(
                text=f"👤 {appt[2]} {appt[3]} ({appt[4]})",
                callback_data=f"edit_{appt[0]}"
            ),
            InlineKeyboardButton(text="❌", callback_data=f"delete_{appt[0]}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def get_admin_services_keyboard():
    """Клавиатура для управления услугами"""
    services = await db.get_all_services_admin()
    buttons = []
    for service in services:
        status = "✅" if service[5] else "❌"  # is_active
        price_text = f" {service[4]}₽" if service[4] and service[4] > 0 else " (бесплатно)"
        duration_text = f" • {service[3]} мин" if service[3] else ""
        button_text = f"{status} {service[1]}{price_text}{duration_text}"
        
        buttons.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"edit_service_{service[0]}"
            ),
            InlineKeyboardButton(text="🗑️", callback_data=f"delete_service_{service[0]}")
        ])
    buttons.append([InlineKeyboardButton(text="➕ Добавить новую услугу", callback_data="add_service")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад в админ-панель", callback_data="back_to_admin")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_service_edit_keyboard(service_id):
    """Клавиатура для редактирования услуги"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить название", callback_data=f"edit_name_{service_id}")],
        [InlineKeyboardButton(text="📝 Изменить описание", callback_data=f"edit_desc_{service_id}")],
        [InlineKeyboardButton(text="⏱️ Изменить длительность", callback_data=f"edit_duration_{service_id}")],
        [InlineKeyboardButton(text="💰 Изменить цену", callback_data=f"edit_price_{service_id}")],
        [InlineKeyboardButton(text="📸 Изменить фото", callback_data=f"edit_photo_{service_id}")],
        [InlineKeyboardButton(text="🔄 Активировать/Деактивировать", callback_data=f"toggle_active_{service_id}")],
        [InlineKeyboardButton(text="🔙 Назад к услугам", callback_data="back_to_services")]
    ])

def get_admin_main_keyboard():
    """Главная клавиатура админ-панели"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Управление записями", callback_data="manage_appointments")],
        [InlineKeyboardButton(text="🔧 Управление услугами", callback_data="manage_services")],
        [InlineKeyboardButton(text="➕ Добавить слот", callback_data="add_slot")]
    ])


