from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from services.database import db
from datetime import datetime, timedelta
import logging


def start_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler()

    async def send_reminders():
        try:
            now = datetime.now()
            tomorrow = now + timedelta(days=1)
            
            # Напоминания за день
            tomorrow_appointments = await db.get_appointments_by_date(tomorrow.strftime("%d.%m.%Y"))
            for appt in tomorrow_appointments:
                try:
                    reminder_text = (
                        f"🔔 <b>Напоминание о записи!</b>\n\n"
                        f"📅 Завтра у вас запись:\n"
                        f"💆‍♀️ <b>{appt[2]}</b>\n"
                        f"📅 Дата: {appt[3]}\n"
                        f"⏰ Время: {appt[4]}\n"
                        f"👤 {appt[5]}\n\n"
                        f"⚠️ <b>Важно:</b>\n"
                        f"• Приходите за 10 минут до назначенного времени\n"
                        f"• Возьмите с собой документы\n"
                        f"• При аллергиях предупредите мастера\n\n"
                        f"📞 Если нужно отменить запись, обратитесь к администратору"
                    )
                    
                    await bot.send_message(
                        appt[1],
                        reminder_text,
                        parse_mode="HTML"
                    )
                    logging.info(f"Отправлено напоминание за день пользователю {appt[1]}")
                except Exception as e:
                    logging.error(f"Ошибка отправки напоминания за день пользователю {appt[1]}: {e}")
            
            # Напоминания за час
            one_hour_later = now + timedelta(hours=1)
            hour_appointments = await db.get_appointments_by_time(one_hour_later.strftime("%H:%M"))
            for appt in hour_appointments:
                try:
                    reminder_text = (
                        f"⏰ <b>Скоро ваша запись!</b>\n\n"
                        f"💆‍♀️ <b>{appt[2]}</b>\n"
                        f"📅 {appt[3]} в {appt[4]}\n"
                        f"👤 {appt[5]}\n\n"
                        f"🚀 <b>Готовьтесь к приему!</b>\n"
                        f"• У вас есть 1 час до записи\n"
                        f"• Не забудьте документы\n"
                        f"• Приходите за 10 минут до времени\n\n"
                        f"🎯 Ждем вас!"
                    )
                    
                    await bot.send_message(
                        appt[1],
                        reminder_text,
                        parse_mode="HTML"
                    )
                    logging.info(f"Отправлено напоминание за час пользователю {appt[1]}")
                except Exception as e:
                    logging.error(f"Ошибка отправки напоминания за час пользователю {appt[1]}: {e}")
                    
        except Exception as e:
            logging.error(f"Ошибка в send_reminders: {e}")

    # Запускаем проверку каждые 30 минут
    scheduler.add_job(send_reminders, "interval", minutes=30)
    scheduler.start()
    logging.info("Планировщик уведомлений запущен")
