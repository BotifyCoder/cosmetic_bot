import aiosqlite
from datetime import datetime
import logging


class Database:
    def __init__(self, db_path='database.sqlite'):
        self.db_path = db_path

    async def _create_tables(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    service TEXT,
                    date TEXT,
                    time TEXT,
                    fio TEXT,
                    allergies TEXT,
                    phone TEXT,
                    created_at TEXT
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS available_slots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    time TEXT,
                    service TEXT,
                    is_booked BOOLEAN DEFAULT 0,
                    UNIQUE(date, time, service)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS services (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    duration INTEGER DEFAULT 60,
                    price REAL,
                    photo_path TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TEXT
                )
            """)
            
            # Создаем индексы для ускорения запросов
            await db.execute("CREATE INDEX IF NOT EXISTS idx_slots_service_date ON available_slots(service, date)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_slots_date_service ON available_slots(date, service)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(date)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_appointments_time ON appointments(time)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_services_active ON services(is_active)")
            
            # Добавляем базовые услуги, если их нет
            await self._add_default_services()
            
            await db.commit()

    async def get_available_dates(self, service):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT DISTINCT date FROM available_slots WHERE service=? AND is_booked=0 ORDER BY date", (service,)) as cursor:
                return [row[0] async for row in cursor]

    async def get_available_times(self, date, service):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT time FROM available_slots WHERE date=? AND service=? AND is_booked=0 ORDER BY time", (date, service)) as cursor:
                return [row[0] async for row in cursor]

    async def mark_slot_as_booked(self, date, time, service):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE available_slots
                SET is_booked = 1
                WHERE date = ? AND time = ? AND service = ?
            """, (date, time, service))
            await db.commit()

    async def mark_slot_as_available(self, date, time, service):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE available_slots
                SET is_booked = 0
                WHERE date = ? AND time = ? AND service = ?
            """, (date, time, service))
            await db.commit()

    async def add_slot(self, date, time, service):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR IGNORE INTO available_slots (date, time, service) 
                VALUES (?, ?, ?)
            """, (date, time, service))
            await db.commit()

    async def delete_slot(self, slot_id):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM available_slots WHERE id=?", (slot_id,))
            await db.commit()

    async def get_all_slots(self):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM available_slots") as cursor:
                return [row async for row in cursor]

    async def add_appointment(self, user_id, service, date, time, fio, allergies, phone):
        async with aiosqlite.connect(self.db_path) as db:
            # Проверяем, нет ли уже записи у этого пользователя на это время
            async with db.execute("""
                SELECT id FROM appointments 
                WHERE user_id = ? AND date = ? AND time = ?
            """, (user_id, date, time)) as cursor:
                existing = await cursor.fetchone()
                if existing:
                    raise ValueError("У вас уже есть запись на это время")
            
            # Проверяем, свободен ли слот
            async with db.execute("""
                SELECT is_booked FROM available_slots 
                WHERE date = ? AND time = ? AND service = ?
            """, (date, time, service)) as cursor:
                slot = await cursor.fetchone()
                if not slot:
                    raise ValueError("Выбранный слот недоступен")
                if slot[0]:
                    raise ValueError("Этот слот уже занят")
            
            await db.execute("""
                INSERT INTO appointments 
                (user_id, service, date, time, fio, allergies, phone, created_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, service, date, time, fio, allergies, phone, datetime.now().isoformat()))
            await db.commit()

    async def get_all_appointments(self):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM appointments") as cursor:
                return [row async for row in cursor]

    async def delete_appointment(self, appointment_id):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM appointments WHERE id=?", (appointment_id,))
            await db.commit()

    async def get_appointments_by_date(self, date):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM appointments WHERE date=?", (date,)) as cursor:
                return [row async for row in cursor]

    async def get_appointments_by_time(self, time):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM appointments WHERE time=?", (time,)) as cursor:
                return [row async for row in cursor]

    async def _add_default_services(self):
        """Добавляет базовые услуги при первом запуске"""
        default_services = [
            ("Маникюр", "Классический маникюр", 60, 1500.0),
            ("Педикюр", "Классический педикюр", 90, 2000.0),
            ("Массаж лица", "Омолаживающий массаж лица", 45, 2500.0),
            ("Чистка лица", "Глубокая чистка лица", 60, 3000.0),
            ("Макияж", "Вечерний макияж", 90, 3500.0)
        ]
        
        async with aiosqlite.connect(self.db_path) as db:
            for name, description, duration, price in default_services:
                try:
                    await db.execute("""
                        INSERT OR IGNORE INTO services (name, description, duration, price, created_at)
                        VALUES (?, ?, ?, ?, datetime('now'))
                    """, (name, description, duration, price))
                except Exception as e:
                    print(f"Ошибка добавления услуги {name}: {e}")
            await db.commit()

    async def get_all_services(self):
        """Получает все активные услуги"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT * FROM services 
                WHERE is_active = 1 
                ORDER BY name
            """) as cursor:
                return [row async for row in cursor]

    async def get_all_services_admin(self):
        """Получает все услуги для админ-панели (включая неактивные)"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT * FROM services 
                ORDER BY name
            """) as cursor:
                return [row async for row in cursor]

    async def add_service(self, name, description="", duration=60, price=0.0, photo_path=None):
        """Добавляет новую услугу"""
        from services.validation import sanitize_input
        name = sanitize_input(name, 50)
        description = sanitize_input(description, 200)
        if not name or len(name) < 2:
            logging.warning(f"Попытка добавить услугу с некорректным именем: '{name}'")
            return False
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("SELECT id FROM services WHERE name = ?", (name,))
                if await cursor.fetchone():
                    logging.warning(f"Попытка добавить дублирующую услугу: '{name}'")
                    return False
                await db.execute("""
                    INSERT INTO services (name, description, duration, price, photo_path, created_at)
                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                """, (name, description, duration, price, photo_path))
                await db.commit()
                return True
        except Exception as e:
            logging.error(f"Ошибка добавления услуги: {e}")
            return False

    async def update_service(self, service_id, name=None, description=None, duration=None, price=None, photo_path=None, is_active=None):
        """Обновляет услугу"""
        from services.validation import sanitize_input
        try:
            async with aiosqlite.connect(self.db_path) as db:
                updates = []
                params = []
                if name is not None:
                    name = sanitize_input(name, 50)
                    if not name or len(name) < 2:
                        logging.warning(f"Попытка обновить услугу с некорректным именем: '{name}'")
                        return False
                    updates.append("name = ?")
                    params.append(name)
                if description is not None:
                    description = sanitize_input(description, 200)
                    updates.append("description = ?")
                    params.append(description)
                if duration is not None:
                    updates.append("duration = ?")
                    params.append(duration)
                if price is not None:
                    updates.append("price = ?")
                    params.append(price)
                if photo_path is not None:
                    updates.append("photo_path = ?")
                    params.append(photo_path)
                if is_active is not None:
                    updates.append("is_active = ?")
                    params.append(is_active)
                if not updates:
                    return False
                params.append(service_id)
                query = f"UPDATE services SET {', '.join(updates)} WHERE id = ?"
                await db.execute(query, params)
                await db.commit()
                return True
        except Exception as e:
            logging.error(f"Ошибка обновления услуги: {e}")
            return False

    async def delete_service(self, service_id):
        """Удаляет услугу (помечает как неактивную)"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("UPDATE services SET is_active = 0 WHERE id = ?", (service_id,))
                await db.commit()
                return True
        except Exception as e:
            print(f"Ошибка удаления услуги: {e}")
            return False

    async def get_service_by_id(self, service_id):
        """Получает услугу по ID"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM services WHERE id = ?", (service_id,)) as cursor:
                row = await cursor.fetchone()
                return row if row else None

db = Database()
