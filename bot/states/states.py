from aiogram.fsm.state import State, StatesGroup

class Registration(StatesGroup):
    # Driver registration
    driver_name = State()
    driver_car_type = State()
    driver_phone = State()
    waiting_payment_amount = State() # To'lov miqdori
    waiting_receipt = State() # Chek rasmi
    # Passenger registration
    passenger_name = State()
    passenger_phone = State()
    waiting_sms_code = State()

class OrderProcess(StatesGroup):
    choosing_from = State()
    entering_from_custom = State() # Yangi
    choosing_to = State()
    entering_to_custom = State() # Yangi
    choosing_time = State()
    entering_time_custom = State() # Yangi
    entering_phone = State() # Har safar raqam so'rash
    waiting_order_sms_code = State() # Buyurtma payti SMS tasdiqlash
    choosing_location = State()
    entering_details = State()
    waiting_voice = State() # Ovozli xabar uchun
    confirming = State()

class AdminState(StatesGroup):
    # waiting_broadcast_msg = State() # Removed
    waiting_driver_query = State()
    waiting_user_query = State() # Yangi qidiruv
    waiting_user_message = State() # Alohida xabar yuborish
    waiting_balance_amount = State()
    waiting_setting_value = State()
    # waiting_broadcast_button = State() # Removed
    editing_driver_id = State()
    editing_passenger_id = State()
    waiting_new_admin_id = State()
    waiting_user_search = State()
    
    # Broadcast advanced
    waiting_broadcast_target = State()
    waiting_broadcast_user_query = State()
    waiting_broadcast_msg = State()
    waiting_broadcast_button = State()
    confirming_broadcast = State()
    
    # Missing states for management
    waiting_amount_refill = State()
    waiting_direct_message = State()
    
    # Promocodes
    waiting_promo_code = State()
    waiting_promo_amount = State()

class UserUpdate(StatesGroup):
    waiting_new_name = State()

class DriverRefill(StatesGroup):
    waiting_amount = State()
    waiting_receipt = State()
