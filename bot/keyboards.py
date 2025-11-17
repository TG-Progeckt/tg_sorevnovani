from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_menu_keyboard():
    """Главное меню"""
    keyboard = [
        [InlineKeyboardButton("👥 Создать команду", callback_data="create_team")],
        [InlineKeyboardButton("🔍 Найти команду", callback_data="find_team")],
        [InlineKeyboardButton("👤 Моя анкета", callback_data="my_profile")],
        [InlineKeyboardButton("📊 Статус турнира", callback_data="tournament_status")],
        [InlineKeyboardButton("🏆 Фан-зона", callback_data="fan_zone")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard():
    """Клавиатура админ-панели"""
    keyboard = [
        [InlineKeyboardButton("🎯 Отобрать команды для турнира", callback_data="admin_select_teams")],
        [InlineKeyboardButton("📊 Сгенерировать сетку", callback_data="admin_generate_bracket")],
        [InlineKeyboardButton("🏆 Выбрать победителя", callback_data="admin_select_winner")],
        [InlineKeyboardButton("📈 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("🔧 Очистить старые приглашения", callback_data="admin_cleanup")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard(back_callback="back_to_main"):
    """Кнопка Назад"""
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=back_callback)]]
    return InlineKeyboardMarkup(keyboard)

def get_confirmation_keyboard(confirm_callback, cancel_callback):
    """Клавиатура подтверждения"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Да", callback_data=confirm_callback),
            InlineKeyboardButton("❌ Нет", callback_data=cancel_callback)
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_registration_keyboard():
    """Клавиатура регистрации - ТОЛЬКО создание команды"""
    keyboard = [
        [InlineKeyboardButton("🎯 Создать команду", callback_data="with_partner")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_captain_confirmation_keyboard():
    """Клавиатура подтверждения капитана"""
    keyboard = [
        [InlineKeyboardButton("✅ Да, я капитан", callback_data="i_am_captain")],
        [InlineKeyboardButton("🔍 Найти команду", callback_data="find_existing_team")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_registration")]
    ]
    return InlineKeyboardMarkup(keyboard)