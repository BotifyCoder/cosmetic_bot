from aiogram.fsm.state import State, StatesGroup

class AppointmentStates(StatesGroup):
    SELECT_SERVICE = State()
    ENTER_DATE = State()
    ENTER_TIME = State()
    ENTER_FIO = State()
    ALLERGIES = State()
    PHONE = State()  # Состояние для ввода телефона
    CONFIRM = State()

class AdminStates(StatesGroup):
    SELECT_APPOINTMENT = State()
    EDIT_DATE = State()
    EDIT_TIME = State()
    ADD_SLOT = State()
    DELETE_SLOT = State()
    MOVE_APPOINTMENT = State()  # Новое состояние для переноса записи
    ADD_SERVICE = State()  # Состояние для добавления услуги
    EDIT_SERVICE = State()  # Состояние для редактирования услуги
    EDIT_PHOTO = State()  # Состояние для редактирования фотографии услуги
