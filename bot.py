import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand, BotCommandScopeChat
from config import BOT_TOKEN, ADMIN_ID
from handlers import user_handlers, admin_handlers
from services.scheduler import start_scheduler
from services.database import db
from services.rate_limiter import cleanup_task

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def setup_bot_commands(bot: Bot):
    """Настройка команд бота"""
    # Общие команды для всех пользователей
    await bot.set_my_commands([
        BotCommand(command="start", description="🚀 Запустить бота"),
        BotCommand(command="help", description="❓ Помощь"),
    ])
    
    # Команды только для админа
    await bot.set_my_commands([
        BotCommand(command="start", description="🚀 Запустить бота"),
        BotCommand(command="help", description="❓ Помощь"),
        BotCommand(command="admin", description="🔧 Панель администратора"),
    ], scope=BotCommandScopeChat(chat_id=ADMIN_ID))
    
    print("✅ Команды бота настроены")

async def main():
    await db._create_tables()  # Асинхронная инициализация таблиц
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не найден в переменных окружения")
    
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    
    # Очищаем webhook при запуске, чтобы избежать обработки накопившихся команд
    await bot.delete_webhook(drop_pending_updates=True)
    print("🧹 Webhook очищен, накопившиеся обновления удалены")
    
    # Настраиваем команды бота
    await setup_bot_commands(bot)
    
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(user_handlers.router)
    dp.include_router(admin_handlers.router)
    start_scheduler(bot)
    
    # Запускаем задачу очистки в фоне
    asyncio.create_task(cleanup_task())
    
    print("Бот запущен с защитой от спама...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
