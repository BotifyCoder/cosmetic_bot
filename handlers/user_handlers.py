from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import sys
import os
import logging
import aiosqlite
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from states import AppointmentStates
from keyboards.inline_keyboards import get_service_keyboard, send_services_with_photos, get_date_keyboard, get_time_keyboard, \
    get_confirmation_keyboard, get_allergies_keyboard
from services.database import db
from services.validation import (
    validate_fio, validate_phone, validate_date, validate_time, 
    validate_service, sanitize_input, validate_callback_data, ValidationError
)
from services.rate_limiter import rate_limiter
from aiogram.utils.formatting import Bold, Text

logger = logging.getLogger(__name__)

router = Router()

@router.message(F.text == "/start")
async def start(message: Message, state: FSMContext):
    if not message.from_user:
        return
    
    user_id = message.from_user.id
    
    # Проверяем защиту от спама
    if rate_limiter.is_rate_limited(user_id):
        await message.answer("Слишком много запросов. Попробуйте позже.")
        return
    
    # Проверяем, не заблокирован ли пользователь
    if rate_limiter.is_user_blocked(user_id):
        await message.answer("Вы заблокированы за нарушение правил. Попробуйте позже.")
        return
    
    try:
        await state.clear()
        rate_limiter.set_user_state(user_id, "SELECT_SERVICE")
        await send_services_with_photos(
            message.bot, 
            message.chat.id, 
            "Добро пожаловать в салон красоты!\n\nВыберите услугу, которая вас интересует:"
        )
        await state.set_state(AppointmentStates.SELECT_SERVICE)
    except Exception as e:
        logger.error(f"Ошибка в start: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

@router.message(F.text == "/help")
async def help_command(message: Message):
    if not message.from_user:
        return
    
    help_text = """
🌟 <b>Как записаться на услугу?</b>

📋 <b>Пошаговая инструкция:</b>

1️⃣ <b>Выберите услугу</b>
   • Нажмите /start или выберите услугу из списка
   • Увидите цены и длительность процедур

2️⃣ <b>Выберите дату</b>
   • Выберите удобную дату из доступных
   • Даты показываются с днями недели

3️⃣ <b>Выберите время</b>
   • Выберите удобное время из свободных слотов
   • Время работы: 8:00 - 20:00

4️⃣ <b>Заполните данные</b>
   • Введите ваше полное имя (ФИО)
   • Укажите наличие аллергий
   • Введите номер телефона

5️⃣ <b>Подтвердите запись</b>
   • Проверьте все данные
   • Нажмите "Подтвердить запись"

📱 <b>Доступные команды:</b>
/start - Начать запись на услугу
/help - Показать эту справку
/my_bookings - Посмотреть ваши записи
/cancel_booking - Отменить запись

⚠️ <b>Важно:</b>
• Максимум 3 активные записи на пользователя
• Отмена записи возможна не менее чем за 2 часа до приема
• Приходите за 10 минут до назначенного времени
• Используйте /cancel_booking для отмены записи

📞 <b>Поддержка:</b>
Если возникли вопросы, обратитесь к администратору.
    """
    
    await message.answer(help_text, parse_mode="HTML")

@router.message(F.text == "/my_bookings")
async def my_bookings(message: Message):
    if not message.from_user:
        return
    
    user_id = message.from_user.id
    
    try:
        appointments = await db.get_all_appointments()
        user_appointments = [apt for apt in appointments if apt[1] == user_id]
        
        if not user_appointments:
            await message.answer("У вас пока нет активных записей.\n\nНажмите /start чтобы записаться на услугу!")
            return
        
        bookings_text = "<b>Ваши записи:</b>\n\n"
        
        for i, apt in enumerate(user_appointments, 1):
            bookings_text += f"{i}. <b>{apt[2]}</b>\n"
            bookings_text += f"   Дата: {apt[3]} в {apt[4]}\n"
            bookings_text += f"   Клиент: {apt[5]}\n"
            bookings_text += f"   Телефон: {apt[7]}\n"
            bookings_text += f"   Аллергии: {apt[6]}\n\n"
        
        await message.answer(bookings_text, parse_mode="HTML")
        
    except Exception as e:
        logging.error(f"Ошибка при получении записей: {e}")
        await message.answer("Произошла ошибка при получении записей.")

@router.message(F.text == "/cancel_booking")
async def cancel_booking_start(message: Message, state: FSMContext):
    if not message.from_user:
        return
    
    user_id = message.from_user.id
    
    try:
        appointments = await db.get_all_appointments()
        user_appointments = [apt for apt in appointments if apt[1] == user_id]
        
        if not user_appointments:
            await message.answer("У вас нет активных записей для отмены.")
            return
        
        # Проверяем, есть ли записи в ближайшие 2 часа
        now = datetime.now()
        cancellable_appointments = []
        
        for apt in user_appointments:
            try:
                apt_datetime = datetime.strptime(f"{apt[3]} {apt[4]}", "%d.%m.%Y %H:%M")
                if apt_datetime > now + timedelta(hours=2):
                    cancellable_appointments.append(apt)
            except:
                continue
        
        if not cancellable_appointments:
            await message.answer("Отмена записи возможна не менее чем за 2 часа до приема.")
            return
        
        # Создаем клавиатуру для отмены
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        buttons = []
        for apt in cancellable_appointments:
            button_text = f"{apt[2]} - {apt[3]} {apt[4]}"
            buttons.append([InlineKeyboardButton(
                text=button_text,
                callback_data=f"cancel_apt_{apt[0]}"
            )])
        
        buttons.append([InlineKeyboardButton(text="🔙 Отмена", callback_data="cancel_cancel")])
        
        await message.answer(
            "<b>Выберите запись для отмены:</b>\n\n"
            "Отмена возможна не менее чем за 2 часа до приема",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logging.error(f"Ошибка при отмене записи: {e}")
        await message.answer("Произошла ошибка при отмене записи.")

@router.callback_query(F.data.startswith("cancel_apt_"))
async def cancel_booking_confirm(callback: CallbackQuery, state: FSMContext):
    if callback.message is None or callback.data is None:
        return
    
    try:
        apt_id = int(callback.data.replace("cancel_apt_", ""))
        
        # Получаем запись
        appointments = await db.get_all_appointments()
        appointment = next((apt for apt in appointments if apt[0] == apt_id), None)
        
        if not appointment:
            await callback.message.answer("❌ Запись не найдена.")
            return
        
        # Проверяем права пользователя
        if appointment[1] != callback.from_user.id:
            await callback.message.answer("❌ Вы не можете отменить чужую запись.")
            return
        
        # Проверяем время (не менее 2 часов)
        now = datetime.now()
        apt_datetime = datetime.strptime(f"{appointment[3]} {appointment[4]}", "%d.%m.%Y %H:%M")
        
        if apt_datetime <= now + timedelta(hours=2):
            await callback.message.answer("⚠️ Отмена записи возможна не менее чем за 2 часа до приема.")
            return
        
        # Отменяем запись
        await db.delete_appointment(apt_id)
        
        # Освобождаем слот
        await db.mark_slot_as_available(appointment[3], appointment[4], appointment[2])
        
        # Отправляем уведомление админу об отмене
        try:
            from config import ADMIN_ID
            if callback.message and callback.message.bot:
                cancel_notification = (
                    f"❌ <b>Запись отменена клиентом!</b>\n\n"
                    f"👤 <b>Клиент:</b> {appointment[5]}\n"
                    f"📱 <b>Телефон:</b> {appointment[7]}\n"
                    f"💆‍♀️ <b>Услуга:</b> {appointment[2]}\n"
                    f"📅 <b>Дата:</b> {appointment[3]}\n"
                    f"⏰ <b>Время:</b> {appointment[4]}\n"
                    f"🆔 <b>ID пользователя:</b> {appointment[1]}\n\n"
                    f"✅ Слот освобожден для других клиентов"
                )
                
                await callback.message.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=cancel_notification,
                    parse_mode="HTML"
                )
                logging.info(f"Отправлено уведомление админу об отмене записи пользователем {appointment[1]}")
        except Exception as e:
            logging.error(f"Ошибка отправки уведомления админу об отмене: {e}")
        
        await callback.message.answer(
            f"<b>Запись отменена!</b>\n\n"
            f"{appointment[2]}\n"
            f"{appointment[3]} в {appointment[4]}\n\n"
            f"Слот освобожден для других клиентов.",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logging.error(f"Ошибка при подтверждении отмены: {e}")
        await callback.message.answer("Произошла ошибка при отмене записи.")

@router.callback_query(F.data == "cancel_cancel")
async def cancel_cancel_booking(callback: CallbackQuery, state: FSMContext):
    if callback.message is None:
        return
    
    await callback.message.answer("Отмена записи прервана.")

@router.callback_query(F.data.startswith("service_"))
async def select_service(callback: CallbackQuery, state: FSMContext):
    if callback.data is None or callback.message is None or not callback.from_user:
        return
    user_id = callback.from_user.id
    # Проверяем защиту от спама
    if rate_limiter.is_rate_limited(user_id):
        await callback.message.answer("Слишком много запросов. Попробуйте позже.")
        return
    try:
        service_parts = validate_callback_data(callback.data, "service_")
        if not service_parts:
            await callback.message.answer("Неверные данные. Попробуйте еще раз.")
            return
        service = await validate_service(service_parts[0])
        # Проверяем, что услуга реально есть в базе
        from services.database import db
        all_services = await db.get_all_services()
        if not any(s[1] == service for s in all_services):
            logging.warning(f"Пользователь {user_id} выбрал несуществующую услугу: {service}")
            await state.clear()
            await callback.message.answer("Услуга не найдена. Начните сначала.")
            return
        await state.update_data(service=service)
        rate_limiter.set_user_state(user_id, "ENTER_DATE")
        dates = await db.get_available_dates(service)
        await callback.message.answer(
            f"📅 Выберите удобную дату для услуги «{service}»:",
            reply_markup=get_date_keyboard(service, dates)
        )
        await state.set_state(AppointmentStates.ENTER_DATE)
    except ValidationError as e:
        await callback.message.answer(f"Ошибка валидации: {e}")
    except Exception as e:
        logging.error(f"Ошибка в select_service: {e}")
        await callback.message.answer("Произошла ошибка. Попробуйте позже.")

@router.callback_query(F.data.startswith("date_"), AppointmentStates.ENTER_DATE)
async def select_date(callback: CallbackQuery, state: FSMContext):
    if callback.data is None or callback.message is None:
        return
        
    try:
        parts = callback.data.split("_")
        if len(parts) >= 3:
            date = parts[1]
            service = parts[2]
            await state.update_data(date=date, service=service)
            times = await db.get_available_times(date, service)
            await callback.message.answer(
                f"⏰ Выберите удобное время на {date}:",
                reply_markup=get_time_keyboard(date, service, times)
            )
            await state.set_state(AppointmentStates.ENTER_TIME)
        else:
            await callback.message.answer("Ошибка обработки данных. Попробуйте еще раз.")
    except Exception as e:
        await callback.message.answer(f"Произошла ошибка: {e}. Попробуйте еще раз.")

@router.callback_query(F.data.startswith("time_"), AppointmentStates.ENTER_TIME)
async def select_time(callback: CallbackQuery, state: FSMContext):
    if callback.data is None or callback.message is None:
        return
        
    try:
        parts = callback.data.split("_")
        if len(parts) >= 4:
            time = parts[1]
            date = parts[2]
            service = parts[3]
            await state.update_data(time=time, date=date, service=service)
            await callback.message.answer(
                "👤 Пожалуйста, введите ваше полное имя (ФИО):"
            )
            await state.set_state(AppointmentStates.ENTER_FIO)
        else:
            await callback.message.answer("Ошибка обработки данных. Попробуйте еще раз.")
    except Exception as e:
        await callback.message.answer(f"Произошла ошибка: {e}. Попробуйте еще раз.")

@router.message(AppointmentStates.ENTER_FIO)
async def process_fio(message: Message, state: FSMContext):
    if message.text is None or not message.from_user:
        return
    
    user_id = message.from_user.id
    
    # Проверяем защиту от спама
    if rate_limiter.is_rate_limited(user_id):
        await message.answer("Слишком много запросов. Попробуйте позже.")
        return
    
    try:
        # Валидируем ФИО
        fio = validate_fio(sanitize_input(message.text))
        await state.update_data(fio=fio)
        rate_limiter.set_user_state(user_id, "ALLERGIES")
        await message.answer(
            "⚠️ Есть ли у вас аллергии на косметические средства?",
            reply_markup=get_allergies_keyboard()
        )
        await state.set_state(AppointmentStates.ALLERGIES)
    except ValidationError as e:
        await message.answer(f"Ошибка валидации: {e}")
    except Exception as e:
        logger.error(f"Ошибка в process_fio: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

@router.callback_query(F.data.startswith("allergy_"), AppointmentStates.ALLERGIES)
async def process_allergies(callback: CallbackQuery, state: FSMContext):
    if callback.data is None or callback.message is None:
        return
        
    allergies = "Да" if callback.data == "allergy_yes" else "Нет"
    await state.update_data(allergies=allergies)
    await callback.message.answer(
        "📱 Пожалуйста, введите ваш номер телефона для связи:"
    )
    await state.set_state(AppointmentStates.PHONE)

@router.message(AppointmentStates.PHONE)
async def process_phone(message: Message, state: FSMContext):
    if message.text is None or not message.from_user:
        return
    
    user_id = message.from_user.id
    
    # Проверяем защиту от спама
    if rate_limiter.is_rate_limited(user_id):
        await message.answer("Слишком много запросов. Попробуйте позже.")
        return
    
    try:
        # Валидируем телефон
        phone = validate_phone(sanitize_input(message.text))
        await state.update_data(phone=phone)
        rate_limiter.set_user_state(user_id, "CONFIRM")
        await message.answer(
            "📋 Проверьте данные и подтвердите запись:",
            reply_markup=get_confirmation_keyboard()
        )
        await state.set_state(AppointmentStates.CONFIRM)
    except ValidationError as e:
        await message.answer(f"Ошибка валидации: {e}")
    except Exception as e:
        logger.error(f"Ошибка в process_phone: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

@router.callback_query(F.data == "confirm_booking", AppointmentStates.CONFIRM)
async def confirm_booking(callback: CallbackQuery, state: FSMContext):
    if callback.message is None or not callback.from_user:
        return
    
    user_id = callback.from_user.id
    
    # Проверяем защиту от спама
    if rate_limiter.is_rate_limited(user_id):
        await callback.message.answer("Слишком много запросов. Попробуйте позже.")
        return
    
    try:
        data = await state.get_data()
        
        # Проверяем, что все необходимые данные есть
        required_fields = ["service", "date", "time", "fio", "allergies", "phone"]
        for field in required_fields:
            if field not in data or not data[field]:
                await callback.message.answer("Неполные данные. Начните запись заново.")
                await state.clear()
                rate_limiter.clear_user_state(user_id)
                return
        
        # Валидируем данные перед сохранением
        service = await validate_service(data["service"])
        date = validate_date(data["date"])
        time = validate_time(data["time"])
        fio = validate_fio(data["fio"])
        phone = validate_phone(data["phone"])
        
        # Проверяем лимит записей
        user_appointments = await db.get_all_appointments()
        user_count = sum(1 for appt in user_appointments if appt[1] == user_id)
        if user_count >= 3:
            logging.warning(f"Пользователь {user_id} превысил лимит записей")
            await callback.message.answer("У вас уже 3 активные записи. Нельзя больше.")
            return

        # Создаем запись
        await db.add_appointment(
            user_id=user_id,
            service=service,
            date=date,
            time=time,
            fio=fio,
            allergies=data["allergies"],
            phone=phone
        )
        
        # Помечаем слот как занятый
        await db.mark_slot_as_booked(date, time, service)
        
        # Отправляем уведомление админу
        try:
            from config import ADMIN_ID
            if callback.message and callback.message.bot:
                admin_notification = (
                    f"🆕 <b>Новая запись!</b>\n\n"
                    f"👤 <b>Клиент:</b> {fio}\n"
                    f"📱 <b>Телефон:</b> {phone}\n"
                    f"⚠️ <b>Аллергии:</b> {data['allergies']}\n"
                    f"💆‍♀️ <b>Услуга:</b> {service}\n"
                    f"📅 <b>Дата:</b> {date}\n"
                    f"⏰ <b>Время:</b> {time}\n"
                    f"🆔 <b>ID пользователя:</b> {user_id}\n\n"
                    f"📊 <b>Всего записей у клиента:</b> {user_count + 1}"
                )
                
                await callback.message.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=admin_notification,
                    parse_mode="HTML"
                )
                logging.info(f"Отправлено уведомление админу о новой записи от пользователя {user_id}")
        except Exception as e:
            logging.error(f"Ошибка отправки уведомления админу: {e}")
        
        await callback.message.answer(
            "Отлично! Ваша запись подтверждена!\n\n"
            f"Дата: {date}\n"
            f"Время: {time}\n"
            f"Услуга: {service}\n\n"
            "Ждем вас в назначенное время!"
        )
        await state.clear()
        rate_limiter.clear_user_state(user_id)
        
    except ValidationError as e:
        await callback.message.answer(f"Ошибка валидации: {e}")
    except ValueError as e:
        await callback.message.answer(f"Ошибка записи: {e}")
    except Exception as e:
        logger.error(f"Ошибка в confirm_booking: {e}")
        await callback.message.answer("Произошла ошибка. Попробуйте позже.")

@router.callback_query(F.data == "cancel_booking", AppointmentStates.CONFIRM)
async def cancel_booking(callback: CallbackQuery, state: FSMContext):
    if callback.message is None:
        return
        
    await callback.message.answer("Запись отменена.")
    await state.clear()

# Обработчики кнопок "Назад"
@router.callback_query(F.data == "back_to_service")
async def back_to_service(callback: CallbackQuery, state: FSMContext):
    if callback.message is None:
        return
    user_state = await state.get_state()
    if user_state != AppointmentStates.ENTER_DATE.state:
        logging.warning(f"Пользователь {callback.from_user.id if callback.from_user else 'None'} попытался вернуться к услугам не из даты")
        await state.clear()
        await callback.message.answer("Сброс состояния. Начните сначала.")
        return
    await callback.message.answer(
        "Выберите услугу, которая вас интересует:",
        reply_markup=await get_service_keyboard()
    )
    await state.set_state(AppointmentStates.SELECT_SERVICE)

@router.callback_query(F.data.startswith("back_to_date_"))
async def back_to_date(callback: CallbackQuery, state: FSMContext):
    if callback.message is None or callback.data is None:
        return
    
    service = callback.data.replace("back_to_date_", "")
    await state.update_data(service=service)
    dates = await db.get_available_dates(service)
    await callback.message.answer("Выберите дату:", reply_markup=get_date_keyboard(service, dates))
    await state.set_state(AppointmentStates.ENTER_DATE)

@router.callback_query(F.data == "back_to_fio")
async def back_to_fio(callback: CallbackQuery, state: FSMContext):
    if callback.message is None:
        return
    
    await callback.message.answer("Введите ваше ФИО:")
    await state.set_state(AppointmentStates.ENTER_FIO)

@router.callback_query(F.data == "back_to_phone")
async def back_to_phone(callback: CallbackQuery, state: FSMContext):
    if callback.message is None:
        return
    
    await callback.message.answer("Введите ваш номер телефона:")
    await state.set_state(AppointmentStates.PHONE)

