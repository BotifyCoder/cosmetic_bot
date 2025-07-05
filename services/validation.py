import re
from datetime import datetime, timedelta
from typing import Optional, Tuple

class ValidationError(Exception):
    """Исключение для ошибок валидации"""
    pass

def sanitize_input(text: str, max_length: int = 1000) -> str:
    if not text:
        return ""
    # Убираем невидимые символы и emoji
    text = ''.join(c for c in text if c.isprintable() and ord(c) < 10000)
    # Убираем html-теги
    text = re.sub(r'<.*?>', '', text)
    # Убираем лишние пробелы
    text = ' '.join(text.split())
    # Ограничиваем длину
    if len(text) > max_length:
        text = text[:max_length]
    # Убираем потенциально опасные символы
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    return text.strip()

def validate_fio(fio: str) -> str:
    fio = sanitize_input(fio, 100)
    if not fio or len(fio.strip()) < 2:
        raise ValidationError("ФИО должно содержать минимум 2 символа")
    if len(fio) > 100:
        raise ValidationError("ФИО слишком длинное (максимум 100 символов)")
    if not re.match(r'^[а-яёА-ЯЁa-zA-Z\s\-\.]+$', fio):
        raise ValidationError("ФИО может содержать только буквы, пробелы, дефисы и точки")
    return fio.strip()

def validate_phone(phone: str) -> str:
    phone = sanitize_input(phone, 20)
    if not phone:
        raise ValidationError("Номер телефона обязателен")
    clean_phone = re.sub(r'[\s\-\(\)\+]', '', phone)
    if clean_phone.startswith('8'):
        clean_phone = '7' + clean_phone[1:]
    if not clean_phone.startswith('7') or len(clean_phone) != 11:
        raise ValidationError("Неверный формат номера телефона. Используйте: +7 (999) 123-45-67")
    if not clean_phone.isdigit():
        raise ValidationError("Номер телефона должен содержать только цифры")
    return f"+7 ({clean_phone[1:4]}) {clean_phone[4:7]}-{clean_phone[7:9]}-{clean_phone[9:11]}"

def validate_date(date_str: str) -> str:
    date_str = sanitize_input(date_str, 20)
    try:
        if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', date_str):
            raise ValidationError("Неверный формат даты. Используйте: DD.MM.YYYY")
        date_obj = datetime.strptime(date_str, '%d.%m.%Y')
        if date_obj.date() < datetime.now().date():
            raise ValidationError("Нельзя записаться на прошедшую дату")
        if date_obj.date() > (datetime.now() + timedelta(days=365)).date():
            raise ValidationError("Нельзя записаться более чем на год вперед")
        return date_str
    except ValueError:
        raise ValidationError("Неверная дата")

def validate_time(time_str: str) -> str:
    time_str = sanitize_input(time_str, 10)
    try:
        if not re.match(r'^\d{2}:\d{2}$', time_str):
            raise ValidationError("Неверный формат времени. Используйте: HH:MM")
        hour, minute = map(int, time_str.split(':'))
        if hour < 8 or hour > 20:
            raise ValidationError("Время работы: с 8:00 до 20:00")
        if minute not in [0, 15, 30, 45]:
            raise ValidationError("Запись возможна каждые 15 минут (00, 15, 30, 45)")
        return time_str
    except ValueError:
        raise ValidationError("Неверное время")

async def validate_service(service: str) -> str:
    """Валидация услуги"""
    from services.database import db
    
    # Получаем все активные услуги из базы данных
    services = await db.get_all_services()
    allowed_services = {s[1].lower() for s in services}  # s[1] - это название услуги
    
    service_lower = service.lower().strip()
    
    if service_lower not in allowed_services:
        raise ValidationError("Неверная услуга")
    
    # Возвращаем оригинальное название (с правильным регистром)
    for s in services:
        if s[1].lower() == service_lower:
            return s[1]
    
    return service_lower

def validate_callback_data(data: str, expected_prefix: str) -> Tuple[str, ...]:
    if not data or not data.startswith(expected_prefix):
        raise ValidationError("Неверные данные")
    parts = data.split('_')
    if len(parts) < 2:
        raise ValidationError("Неверный формат данных")
    return tuple(parts[1:]) 