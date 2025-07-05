import asyncio
from datetime import datetime, timedelta
from typing import Dict, Set, Tuple
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Система защиты от спама"""
    
    def __init__(self):
        self.user_requests: Dict[int, list] = {}  # user_id -> list of timestamps
        self.user_states: Dict[int, str] = {}  # user_id -> current state
        self.blocked_users: Set[int] = set()  # заблокированные пользователи
        
        # Настройки лимитов
        self.max_requests_per_minute = 30
        self.max_requests_per_hour = 200
        self.block_duration = timedelta(hours=1)
        self.state_timeout = timedelta(minutes=10)
    
    def is_rate_limited(self, user_id: int) -> bool:
        """Проверяет, не превышен ли лимит запросов"""
        now = datetime.now()
        
        # Проверяем, не заблокирован ли пользователь
        if user_id in self.blocked_users:
            return True
        
        # Получаем историю запросов пользователя
        if user_id not in self.user_requests:
            self.user_requests[user_id] = []
        
        requests = self.user_requests[user_id]
        
        # Удаляем старые запросы (старше часа)
        requests = [req for req in requests if now - req < timedelta(hours=1)]
        self.user_requests[user_id] = requests
        
        # Проверяем лимит за минуту
        recent_requests = [req for req in requests if now - req < timedelta(minutes=1)]
        if len(recent_requests) >= self.max_requests_per_minute:
            self.blocked_users.add(user_id)
            logger.warning(f"Пользователь {user_id} заблокирован за превышение лимита запросов")
            return True
        
        # Проверяем лимит за час
        if len(requests) >= self.max_requests_per_hour:
            self.blocked_users.add(user_id)
            logger.warning(f"Пользователь {user_id} заблокирован за превышение лимита запросов за час")
            return True
        
        # Добавляем текущий запрос
        requests.append(now)
        return False
    
    def check_state_validity(self, user_id: int, expected_state: str) -> bool:
        """Проверяет валидность состояния пользователя"""
        now = datetime.now()
        
        if user_id not in self.user_states:
            return False
        
        # Проверяем, не истекло ли время состояния
        state_time = self.user_states[user_id]
        if isinstance(state_time, str):
            try:
                state_time = datetime.fromisoformat(state_time)
            except ValueError:
                return False
        
        if now - state_time > self.state_timeout:
            # Очищаем состояние
            del self.user_states[user_id]
            return False
        
        return True
    
    def set_user_state(self, user_id: int, state: str):
        """Устанавливает состояние пользователя"""
        self.user_states[user_id] = datetime.now().isoformat()
    
    def clear_user_state(self, user_id: int):
        """Очищает состояние пользователя"""
        if user_id in self.user_states:
            del self.user_states[user_id]
    
    def is_user_blocked(self, user_id: int) -> bool:
        """Проверяет, заблокирован ли пользователь"""
        return user_id in self.blocked_users
    
    def unblock_user(self, user_id: int):
        """Разблокирует пользователя"""
        if user_id in self.blocked_users:
            self.blocked_users.remove(user_id)
            logger.info(f"Пользователь {user_id} разблокирован")
    
    def cleanup_old_data(self):
        """Очищает старые данные"""
        now = datetime.now()
        
        # Очищаем старые запросы
        for user_id in list(self.user_requests.keys()):
            requests = self.user_requests[user_id]
            requests = [req for req in requests if now - req < timedelta(hours=1)]
            if not requests:
                del self.user_requests[user_id]
            else:
                self.user_requests[user_id] = requests
        
        # Очищаем старые состояния
        for user_id in list(self.user_states.keys()):
            state_time = self.user_states[user_id]
            if isinstance(state_time, str):
                try:
                    state_time = datetime.fromisoformat(state_time)
                    if now - state_time > self.state_timeout:
                        del self.user_states[user_id]
                except ValueError:
                    del self.user_states[user_id]

# Глобальный экземпляр
rate_limiter = RateLimiter()

# Запускаем периодическую очистку
async def cleanup_task():
    """Периодическая очистка старых данных"""
    while True:
        try:
            rate_limiter.cleanup_old_data()
            await asyncio.sleep(300)  # Каждые 5 минут
        except Exception as e:
            logger.error(f"Ошибка в cleanup_task: {e}")
            await asyncio.sleep(60) 