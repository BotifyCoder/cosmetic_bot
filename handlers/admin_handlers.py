from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from states import AdminStates
from keyboards.inline_keyboards import get_admin_appointment_keyboard, get_admin_services_keyboard, get_service_edit_keyboard, get_admin_main_keyboard
from services.database import db
from services.rate_limiter import rate_limiter
from config import ADMIN_ID
from datetime import datetime

logger = logging.getLogger(__name__)

router = Router()


@router.message(F.text == "/admin")
async def admin(message: Message, state: FSMContext):
    if message.from_user is None or message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "🔧 Панель администратора\n\n"
        "Выберите нужный раздел:",
        reply_markup=get_admin_main_keyboard()
    )


@router.callback_query(F.data == "add_slot")
async def add_slot(callback: CallbackQuery, state: FSMContext):
    if callback.message is None:
        return
    await callback.message.answer("Введите дату, время и тип услуги (через запятую):\n\nПример: 15.06.2025,14:00,Массаж")
    await state.set_state(AdminStates.ADD_SLOT)


@router.message(AdminStates.ADD_SLOT)
async def process_add_slot(message: Message, state: FSMContext):
    if message.text is None:
        await message.answer("Пожалуйста, введите текст.")
        return
        
    try:
        date, time, service = message.text.split(",")
        date = date.strip()
        time = time.strip()
        service = service.strip()
        
        # Получаем список всех услуг для проверки
        from services.database import db
        all_services = await db.get_all_services()
        service_names = [s[1].lower() for s in all_services]
        
        # Ищем подходящую услугу (частичное совпадение)
        matched_service = None
        for s in all_services:
            if service.lower() in s[1].lower() or s[1].lower() in service.lower():
                matched_service = s[1]
                break
        
        if not matched_service:
            available_services = ", ".join([s[1] for s in all_services])
            await message.answer(f"Услуга '{service}' не найдена. Доступные услуги: {available_services}")
            return
        
        await db.add_slot(date, time, matched_service)
        
        # Отправляем уведомление админу о добавлении слота
        try:
            if message.bot:
                slot_notification = (
                    f"➕ <b>Новый слот добавлен!</b>\n\n"
                    f"💆‍♀️ <b>Услуга:</b> {matched_service}\n"
                    f"📅 <b>Дата:</b> {date}\n"
                    f"⏰ <b>Время:</b> {time}\n"
                    f"👤 <b>Добавил:</b> Администратор"
                )
                
                await message.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=slot_notification,
                    parse_mode="HTML"
                )
                logging.info(f"Отправлено уведомление админу о добавлении слота {date} {time} - {matched_service}")
        except Exception as e:
            logging.error(f"Ошибка отправки уведомления админу о слоте: {e}")
        
        await message.answer(f"✅ Слот добавлен: {date} {time} - {matched_service}")
        await state.clear()
    except Exception as e:
        logging.error(f"Ошибка добавления слота: {e}")
        await message.answer("Неверный формат. Используйте: дата,время,название_услуги")

@router.callback_query(F.data == "admin_exit")
async def admin_exit(callback: CallbackQuery, state: FSMContext):
    if callback.message is None:
        return
    
    await callback.message.answer("Выход из админ-панели. Используйте /admin для повторного входа.")
    await state.clear()




@router.callback_query(F.data == "delete_slot")
async def delete_slot(callback: CallbackQuery, state: FSMContext):
    if callback.message is None or callback.from_user is None or callback.from_user.id != ADMIN_ID:
        logging.warning(f"Попытка доступа к delete_slot: {getattr(callback.from_user, 'id', None)}")
        if callback.message:
            await callback.message.answer("Нет доступа.")
        return
        
    slots = await db.get_all_slots()
    if not slots:
        await callback.message.answer("Нет доступных слотов")
        return

    buttons = []
    for slot in slots:
        buttons.append([
            InlineKeyboardButton(
                text=f"{slot[1]} {slot[2]} ({slot[3]})",
                callback_data=f"delete_{slot[0]}"
            )
        ])

    await callback.message.answer("Выберите слот для удаления:",
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await state.set_state(AdminStates.DELETE_SLOT)


@router.callback_query(F.data.startswith("delete_"), AdminStates.DELETE_SLOT)
async def confirm_delete(callback: CallbackQuery, state: FSMContext):
    if callback.data is None or callback.message is None:
        return
        
    slot_id = int(callback.data.split("_")[1])
    
    # Получаем информацию о слоте перед удалением
    slots = await db.get_all_slots()
    slot_to_delete = next((slot for slot in slots if slot[0] == slot_id), None)
    
    await db.delete_slot(slot_id)
    
    # Отправляем уведомление админу об удалении слота
    if slot_to_delete and callback.message and callback.message.bot:
        try:
            slot_notification = (
                f"➖ <b>Слот удален!</b>\n\n"
                f"💆‍♀️ <b>Услуга:</b> {slot_to_delete[3]}\n"
                f"📅 <b>Дата:</b> {slot_to_delete[1]}\n"
                f"⏰ <b>Время:</b> {slot_to_delete[2]}\n"
                f"👤 <b>Удалил:</b> Администратор"
            )
            
            await callback.message.bot.send_message(
                chat_id=ADMIN_ID,
                text=slot_notification,
                parse_mode="HTML"
            )
            logging.info(f"Отправлено уведомление админу об удалении слота {slot_to_delete[1]} {slot_to_delete[2]} - {slot_to_delete[3]}")
        except Exception as e:
            logging.error(f"Ошибка отправки уведомления админу об удалении слота: {e}")
    
    await callback.message.answer("Слот удален!")
    await state.clear()


@router.callback_query(F.data == "view_appointments")
async def view_appointments(callback: CallbackQuery, state: FSMContext):
    if callback.message is None:
        return
        
    appointments = await db.get_all_appointments()

    if not appointments:
        await callback.message.answer("Нет записей")
        return

    for appt in appointments:
        # Убедитесь, что индексы соответствуют структуре БД
        message_text = (
            f"👤 ФИО: {appt[5] if appt[5] else 'Не указано'}\n"
            f"📱 Телефон: {appt[7] if appt[7] else 'Не указан'}\n"
            f"⚠️ Аллергии: {appt[6] if appt[6] in ['Да', 'Нет'] else 'Не указано'}\n"
            f"💆‍♂️ Услуга: {appt[2]}\n"
            f"📅 Дата: {appt[3]}\n"
            f"⏰ Время: {appt[4]}\n"
        )

        action_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_appt_{appt[0]}")],
                [InlineKeyboardButton(text="🔄 Перенести", callback_data=f"move_appt_{appt[0]}")]
            ]
        )

        await callback.message.answer(message_text, reply_markup=action_keyboard)

    await callback.message.answer("Все записи отправлены выше.")


@router.callback_query(F.data.startswith("delete_appt_"))
async def handle_delete_appt(callback: CallbackQuery):
    if callback.message is None or callback.from_user is None or callback.from_user.id != ADMIN_ID or callback.data is None:
        logging.warning(f"Попытка доступа к delete_appt: {getattr(callback.from_user, 'id', None)}")
        if callback.message:
            await callback.message.answer("Нет доступа.")
        return
    appt_id = int(callback.data.replace("delete_appt_", ""))
    appointments = await db.get_all_appointments()
    appt = next((a for a in appointments if a[0] == appt_id), None)
    if not appt:
        logging.warning(f"Попытка удалить несуществующую запись: {appt_id}")
        await callback.message.answer("Запись не найдена.")
        return
    await db.delete_appointment(appt_id)
    await callback.message.answer("✅ Запись удалена")

@router.callback_query(F.data.startswith("move_appt_"))
async def move_appointment_start(callback: CallbackQuery, state: FSMContext):
    if callback.message is None or callback.from_user is None or callback.from_user.id != ADMIN_ID or callback.data is None:
        logging.warning(f"Попытка доступа к move_appt: {getattr(callback.from_user, 'id', None)}")
        if callback.message:
            await callback.message.answer("Нет доступа.")
        return
    appt_id = int(callback.data.replace("move_appt_", ""))
    appointments = await db.get_all_appointments()
    appt = next((a for a in appointments if a[0] == appt_id), None)
    if not appt:
        logging.warning(f"Попытка перенести несуществующую запись: {appt_id}")
        await callback.message.answer("Запись не найдена.")
        return
    await state.update_data(move_appt_id=appt_id)
    await callback.message.answer("Введите новую дату и время для переноса (пример: 16.06.2025,15:00):")
    await state.set_state(AdminStates.MOVE_APPOINTMENT)

@router.message(AdminStates.MOVE_APPOINTMENT)
async def move_appointment_process(message: Message, state: FSMContext):
    if message.text is None or message.from_user is None or message.from_user.id != ADMIN_ID:
        logging.warning(f"Попытка переноса записи неадмином: {getattr(message.from_user, 'id', None)}")
        if message.from_user:
            await message.answer("Нет доступа.")
        return
        
    try:
        date, time = message.text.split(",")
        data = await state.get_data()
        appt_id = data["move_appt_id"]
        # Получаем старую запись
        appointments = await db.get_all_appointments()
        appt = next((a for a in appointments if a[0] == appt_id), None)
        if not appt:
            await message.answer("Запись не найдена.")
            await state.clear()
            return
        # Проверяем, есть ли свободный слот
        slots = await db.get_all_slots()
        slot_exists = any(s[1] == date.strip() and s[2] == time.strip() and s[3] == appt[2] and not s[4] for s in slots)
        if not slot_exists:
            await message.answer("Нет свободного окна для этой услуги на выбранные дату и время.")
            return
        # Обновляем запись (удаляем старую, создаём новую)
        await db.delete_appointment(appt_id)
        await db.add_appointment(
            user_id=appt[1],
            service=appt[2],
            date=date.strip(),
            time=time.strip(),
            fio=appt[5],
            allergies=appt[6],
            phone=appt[7]
        )
        await message.answer("Запись успешно перенесена!")
        await state.clear()
    except Exception as e:
        await message.answer(f"Ошибка переноса: {e}\nФормат: дата,время (например: 16.06.2025,15:00)")

# Обработчики для управления услугами
@router.callback_query(F.data == "manage_services")
async def manage_services(callback: CallbackQuery, state: FSMContext):
    if callback.message is None:
        return
    
    await callback.message.answer(
        "Управление услугами:",
        reply_markup=await get_admin_services_keyboard()
    )

@router.callback_query(F.data == "add_service")
async def add_service_start(callback: CallbackQuery, state: FSMContext):
    if callback.message is None or callback.from_user is None or callback.from_user.id != ADMIN_ID:
        logging.warning(f"Попытка доступа к админке: {getattr(callback.from_user, 'id', None)}")
        if callback.message:
            await callback.message.answer("Нет доступа.")
        return
    
    await callback.message.answer(
        "Введите данные услуги в формате:\n"
        "название, описание, длительность(мин), цена\n\n"
        "Пример: Маникюр, Классический маникюр, 60, 1500"
    )
    await state.set_state(AdminStates.ADD_SERVICE)

@router.message(AdminStates.ADD_SERVICE)
async def add_service_process(message: Message, state: FSMContext):
    if message.text is None or message.from_user is None or message.from_user.id != ADMIN_ID:
        logging.warning(f"Попытка добавить услугу неадмином: {getattr(message.from_user, 'id', None)}")
        if message.from_user:
            await message.answer("Нет доступа.")
        return
    
    try:
        parts = message.text.split(",")
        if len(parts) >= 4:
            name = parts[0].strip()
            description = parts[1].strip()
            duration = int(parts[2].strip())
            price = float(parts[3].strip())
            
            if rate_limiter.is_rate_limited(message.from_user.id):
                await message.answer("Слишком много действий. Попробуйте позже.")
                return

            success = await db.add_service(name, description, duration, price)
            if success:
                await message.answer("✅ Услуга добавлена!")
            else:
                await message.answer("❌ Ошибка при добавлении услуги.")
        else:
            await message.answer("Неверный формат. Используйте: название, описание, длительность, цена")
    except ValueError:
        await message.answer("❌ Ошибка в данных. Проверьте формат чисел.")
    except Exception as e:
        logger.error(f"Ошибка добавления услуги: {e}")
        await message.answer("❌ Произошла ошибка при добавлении услуги.")
    
    await state.clear()

@router.callback_query(F.data.startswith("edit_service_"))
async def edit_service_start(callback: CallbackQuery, state: FSMContext):
    if callback.message is None or callback.from_user is None or callback.from_user.id != ADMIN_ID or callback.data is None:
        logging.warning(f"Попытка доступа к edit_service: {getattr(callback.from_user, 'id', None)}")
        if callback.message:
            await callback.message.answer("Нет доступа.")
        return
    
    service_id = int(callback.data.replace("edit_service_", ""))
    service = await db.get_service_by_id(service_id)
    
    if not service:
        logging.warning(f"Попытка редактировать несуществующую услугу: {service_id}")
        await callback.message.answer("❌ Услуга не найдена.")
        return
    
    status = "✅ Активна" if service[5] else "❌ Неактивна"
    message_text = (
        f"🔧 Редактирование услуги:\n\n"
        f"📝 Название: {service[1]}\n"
        f"📄 Описание: {service[2]}\n"
        f"⏱️ Длительность: {service[3]} мин\n"
        f"💰 Цена: {service[4]}₽\n"
        f"📊 Статус: {status}"
    )
    
    await callback.message.answer(
        message_text,
        reply_markup=get_service_edit_keyboard(service_id)
    )

@router.callback_query(F.data.startswith("delete_service_"))
async def delete_service_confirm(callback: CallbackQuery, state: FSMContext):
    if callback.message is None or callback.from_user is None or callback.from_user.id != ADMIN_ID or callback.data is None:
        logging.warning(f"Попытка доступа к delete_service: {getattr(callback.from_user, 'id', None)}")
        if callback.message:
            await callback.message.answer("Нет доступа.")
        return
    
    service_id = int(callback.data.replace("delete_service_", ""))
    service = await db.get_service_by_id(service_id)
    
    if not service:
        logging.warning(f"Попытка удалить несуществующую услугу: {service_id}")
        await callback.message.answer("❌ Услуга не найдена.")
        return
    
    success = await db.delete_service(service_id)
    if success:
        await callback.message.answer(f"✅ Услуга '{service[1]}' удалена (деактивирована).")
    else:
        await callback.message.answer("❌ Ошибка при удалении услуги.")

@router.callback_query(F.data.startswith("edit_name_"))
async def edit_service_name_start(callback: CallbackQuery, state: FSMContext):
    if callback.message is None or callback.from_user is None or callback.from_user.id != ADMIN_ID or callback.data is None:
        logging.warning(f"Попытка доступа к edit_name: {getattr(callback.from_user, 'id', None)}")
        if callback.message:
            await callback.message.answer("Нет доступа.")
        return
    
    service_id = int(callback.data.replace("edit_name_", ""))
    service = await db.get_service_by_id(service_id)
    
    if not service:
        logging.warning(f"Попытка изменить имя несуществующей услуги: {service_id}")
        await callback.message.answer("❌ Услуга не найдена.")
        return
    
    await state.update_data(edit_service_id=service_id, edit_field="name")
    await callback.message.answer("Введите новое название услуги:")
    await state.set_state(AdminStates.EDIT_SERVICE)

@router.callback_query(F.data.startswith("edit_desc_"))
async def edit_service_desc_start(callback: CallbackQuery, state: FSMContext):
    if callback.message is None or callback.from_user is None or callback.from_user.id != ADMIN_ID or callback.data is None:
        logging.warning(f"Попытка доступа к edit_desc: {getattr(callback.from_user, 'id', None)}")
        if callback.message:
            await callback.message.answer("Нет доступа.")
        return
    
    service_id = int(callback.data.replace("edit_desc_", ""))
    service = await db.get_service_by_id(service_id)
    
    if not service:
        logging.warning(f"Попытка изменить описание несуществующей услуги: {service_id}")
        await callback.message.answer("❌ Услуга не найдена.")
        return
    
    await state.update_data(edit_service_id=service_id, edit_field="description")
    await callback.message.answer("Введите новое описание услуги:")
    await state.set_state(AdminStates.EDIT_SERVICE)

@router.callback_query(F.data.startswith("edit_duration_"))
async def edit_service_duration_start(callback: CallbackQuery, state: FSMContext):
    if callback.message is None or callback.from_user is None or callback.from_user.id != ADMIN_ID or callback.data is None:
        logging.warning(f"Попытка доступа к edit_duration: {getattr(callback.from_user, 'id', None)}")
        if callback.message:
            await callback.message.answer("Нет доступа.")
        return
    
    service_id = int(callback.data.replace("edit_duration_", ""))
    service = await db.get_service_by_id(service_id)
    
    if not service:
        logging.warning(f"Попытка изменить длительность несуществующей услуги: {service_id}")
        await callback.message.answer("❌ Услуга не найдена.")
        return
    
    await state.update_data(edit_service_id=service_id, edit_field="duration")
    await callback.message.answer("Введите новую длительность услуги (в минутах):")
    await state.set_state(AdminStates.EDIT_SERVICE)

@router.callback_query(F.data.startswith("edit_price_"))
async def edit_service_price_start(callback: CallbackQuery, state: FSMContext):
    if callback.message is None or callback.from_user is None or callback.from_user.id != ADMIN_ID or callback.data is None:
        logging.warning(f"Попытка доступа к edit_price: {getattr(callback.from_user, 'id', None)}")
        if callback.message:
            await callback.message.answer("Нет доступа.")
        return
    
    service_id = int(callback.data.replace("edit_price_", ""))
    service = await db.get_service_by_id(service_id)
    
    if not service:
        logging.warning(f"Попытка изменить цену несуществующей услуги: {service_id}")
        await callback.message.answer("❌ Услуга не найдена.")
        return
    
    await state.update_data(edit_service_id=service_id, edit_field="price")
    await callback.message.answer("Введите новую цену услуги:")

@router.callback_query(F.data.startswith("toggle_active_"))
async def toggle_service_active(callback: CallbackQuery, state: FSMContext):
    if callback.message is None or callback.from_user is None or callback.from_user.id != ADMIN_ID or callback.data is None:
        logging.warning(f"Попытка доступа к toggle_active: {getattr(callback.from_user, 'id', None)}")
        if callback.message:
            await callback.message.answer("Нет доступа.")
        return
    
    service_id = int(callback.data.replace("toggle_active_", ""))
    service = await db.get_service_by_id(service_id)
    
    if not service:
        logging.warning(f"Попытка изменить статус несуществующей услуги: {service_id}")
        await callback.message.answer("❌ Услуга не найдена.")
        return
    
    new_status = not service[5]  # Инвертируем текущий статус
    success = await db.update_service(service_id, is_active=new_status)
    
    if success:
        status_text = "активирована" if new_status else "деактивирована"
        await callback.message.answer(f"✅ Услуга '{service[1]}' {status_text}.")
    else:
        await callback.message.answer("❌ Ошибка при изменении статуса услуги.")

@router.callback_query(F.data.startswith("edit_photo_"))
async def edit_service_photo_start(callback: CallbackQuery, state: FSMContext):
    if callback.message is None or callback.from_user is None or callback.from_user.id != ADMIN_ID or callback.data is None:
        logging.warning(f"Попытка доступа к edit_photo: {getattr(callback.from_user, 'id', None)}")
        if callback.message:
            await callback.message.answer("Нет доступа.")
        return
    
    try:
        service_id = int(callback.data.replace("edit_photo_", ""))
        service = await db.get_service_by_id(service_id)
        
        if not service:
            await callback.message.answer("❌ Услуга не найдена.")
            return
        
        await state.update_data(editing_service_id=service_id)
        await callback.message.answer(
            f"📸 Отправьте новую фотографию для услуги '{service[1]}'\n\n"
            "Поддерживаемые форматы: JPG, PNG, GIF\n"
            "Максимальный размер: 10 МБ\n\n"
            "Или отправьте 'удалить' чтобы убрать фотографию."
        )
        await state.set_state(AdminStates.EDIT_PHOTO)
        
    except Exception as e:
        logger.error(f"Ошибка при начале редактирования фото: {e}")
        await callback.message.answer("❌ Произошла ошибка.")

@router.message(AdminStates.EDIT_PHOTO, F.photo)
async def edit_service_photo_process(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer("❌ Пожалуйста, отправьте фотографию.")
        return
    
    try:
        data = await state.get_data()
        service_id = data.get('editing_service_id')
        
        if not service_id:
            await message.answer("❌ Ошибка: не найден ID услуги.")
            await state.clear()
            return
        
        service = await db.get_service_by_id(service_id)
        if not service:
            await message.answer("❌ Услуга не найдена.")
            await state.clear()
            return
        
        # Получаем файл фотографии
        photo = message.photo[-1]  # Берем самое большое разрешение
        if not message.bot:
            await message.answer("❌ Ошибка: бот недоступен.")
            await state.clear()
            return
            
        file = await message.bot.get_file(photo.file_id)
        
        if not file or not file.file_path:
            await message.answer("❌ Ошибка при получении файла.")
            await state.clear()
            return
        
        # Создаем имя файла
        file_extension = file.file_path.split('.')[-1] if '.' in file.file_path else 'jpg'
        filename = f"images/service_{service_id}.{file_extension}"
        
        # Скачиваем файл
        await message.bot.download_file(file.file_path, filename)
        
        # Обновляем путь к фотографии в базе данных
        success = await db.update_service(service_id, photo_path=filename)
        
        if success:
            await message.answer(
                f"✅ Фотография для услуги '{service[1]}' успешно обновлена!\n\n"
                f"📁 Файл сохранен: {filename}"
            )
        else:
            await message.answer("❌ Ошибка при сохранении фотографии в базе данных.")
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка при обработке фотографии: {e}")
        await message.answer("❌ Произошла ошибка при обработке фотографии.")
        await state.clear()

@router.message(AdminStates.EDIT_PHOTO, F.text)
async def edit_service_photo_text(message: Message, state: FSMContext):
    if message.text and message.text.lower() == 'удалить':
        try:
            data = await state.get_data()
            service_id = data.get('editing_service_id')
            
            if not service_id:
                await message.answer("❌ Ошибка: не найден ID услуги.")
                await state.clear()
                return
            
            service = await db.get_service_by_id(service_id)
            if not service:
                await message.answer("❌ Услуга не найдена.")
                await state.clear()
                return
            
            # Удаляем старую фотографию, если она существует
            if service[5] and os.path.exists(service[5]):  # photo_path
                try:
                    os.remove(service[5])
                except Exception as e:
                    logger.error(f"Ошибка при удалении файла {service[5]}: {e}")
            
            # Обновляем базу данных
            success = await db.update_service(service_id, photo_path=None)
            
            if success:
                await message.answer(f"✅ Фотография для услуги '{service[1]}' удалена.")
            else:
                await message.answer("❌ Ошибка при удалении фотографии из базы данных.")
            
            await state.clear()
            
        except Exception as e:
            logger.error(f"Ошибка при удалении фотографии: {e}")
            await message.answer("❌ Произошла ошибка при удалении фотографии.")
            await state.clear()
    else:
        await message.answer("❌ Пожалуйста, отправьте фотографию или напишите 'удалить' для удаления текущей фотографии.")

@router.message(AdminStates.EDIT_SERVICE)
async def edit_service_process(message: Message, state: FSMContext):
    if message.text is None:
        await message.answer("Пожалуйста, введите текст.")
        return
    
    try:
        data = await state.get_data()
        service_id = data.get("edit_service_id")
        edit_field = data.get("edit_field")
        
        if not service_id or not edit_field:
            await message.answer("❌ Ошибка: данные не найдены.")
            await state.clear()
            return
        
        # Подготавливаем параметры для обновления
        update_params = {}
        
        if edit_field == "name":
            update_params["name"] = message.text.strip()
        elif edit_field == "description":
            update_params["description"] = message.text.strip()
        elif edit_field == "duration":
            update_params["duration"] = int(message.text.strip())
        elif edit_field == "price":
            update_params["price"] = float(message.text.strip())
        
        success = await db.update_service(service_id, **update_params)
        
        if success:
            await message.answer("✅ Услуга обновлена!")
        else:
            await message.answer("❌ Ошибка при обновлении услуги.")
            
    except ValueError:
        await message.answer("❌ Ошибка в данных. Проверьте формат.")
    except Exception as e:
        logger.error(f"Ошибка обновления услуги: {e}")
        await message.answer("❌ Произошла ошибка при обновлении услуги.")
    
    await state.clear()

# Обработчики навигации
@router.callback_query(F.data == "back_to_admin")
async def back_to_admin(callback: CallbackQuery, state: FSMContext):
    if callback.message is None:
        return
    
    await callback.message.answer(
        "Панель администратора:",
        reply_markup=get_admin_main_keyboard()
    )

@router.callback_query(F.data == "back_to_services")
async def back_to_services(callback: CallbackQuery, state: FSMContext):
    if callback.message is None:
        return
    
    await callback.message.answer(
        "Управление услугами:",
        reply_markup=await get_admin_services_keyboard()
    )

@router.callback_query(F.data == "manage_appointments")
async def manage_appointments(callback: CallbackQuery, state: FSMContext):
    if callback.message is None:
        return
    
    await callback.message.answer(
        "Управление записями:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="➕ Добавить слот", callback_data="add_slot")],
                [InlineKeyboardButton(text="➖ Удалить слот", callback_data="delete_slot")],
                [InlineKeyboardButton(text="📋 Просмотр записей", callback_data="view_appointments")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_admin")]
            ]
        )
    )
