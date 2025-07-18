# Настройка косметического бота

## Шаг 1: Получение токена бота

1. Откройте Telegram и найдите @BotFather
2. Отправьте команду `/newbot`
3. Следуйте инструкциям:
   - Введите имя бота (например: "Косметический салон")
   - Введите username бота (например: "cosmetic_salon_bot")
4. Скопируйте полученный токен

## Шаг 2: Получение вашего Telegram ID

1. Найдите бота @userinfobot в Telegram
2. Отправьте ему любое сообщение
3. Скопируйте ваш ID (число)

## Шаг 3: Создание файла .env

Создайте файл `.env` в корневой папке проекта со следующим содержимым:

```
BOT_TOKEN=ваш_токен_бота_здесь
ADMIN_ID=ваш_telegram_id_здесь
```

Пример:
```
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_ID=987654321
```

## Шаг 4: Установка зависимостей

```bash
pip install -r requirements.txt
```

## Шаг 5: Тестирование

Запустите тестовый скрипт:

```bash
python test_bot.py
```

## Шаг 6: Запуск бота

```bash
python bot.py
```

## Возможные проблемы

### Ошибка "BOT_TOKEN не найден"
- Проверьте, что файл `.env` создан в корневой папке
- Убедитесь, что токен скопирован правильно

### Ошибка "ADMIN_ID должен быть числом"
- Убедитесь, что ваш Telegram ID - это число
- Проверьте, что в файле `.env` нет лишних символов

### Ошибки с базой данных
- Убедитесь, что у вас есть права на запись в папку
- Проверьте, что SQLite установлен

## Команды бота

- `/start` - начать процесс записи
- `/admin` - открыть админ-панель (только для администратора) 