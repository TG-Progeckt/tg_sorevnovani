from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from config import *
from bot.handlers import MainHandlers

def create_conversation_handler(main_handlers: MainHandlers):
    """Создание ConversationHandler с зависимостями"""
    return ConversationHandler(
        entry_points=[CommandHandler("start", main_handlers.start)],
        states={
            WAITING_FOR_PROMO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, main_handlers.handle_promo_code),
                CallbackQueryHandler(main_handlers.handle_cancel_callback, pattern="^cancel$")
            ],
            CONFIRM_PROMO: [CallbackQueryHandler(main_handlers.handle_promo_confirmation)],
            REGISTER_OPTION: [CallbackQueryHandler(main_handlers.handle_registration_option)],
            WAITING_FOR_CAPTAIN_CONFIRM: [
                CallbackQueryHandler(main_handlers.handle_captain_confirmation,
                                     pattern="^i_am_captain|^find_existing_team|^back_to_"),
            ],
            WAITING_FOR_TEAM_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, main_handlers.handle_team_name),
                CallbackQueryHandler(main_handlers.handle_captain_confirmation, pattern="^back_to_")
            ],
            WAITING_FOR_MMR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, main_handlers.handle_team_mmr),
                CallbackQueryHandler(main_handlers.handle_captain_confirmation, pattern="^back_to_")
            ],
            WAITING_FOR_SOLO_MMR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, main_handlers.handle_solo_mmr),
                CallbackQueryHandler(main_handlers.back_to_profile_handler, pattern="^back_to_profile$")
            ],
        },
        fallbacks=[CommandHandler('cancel', main_handlers.cancel)],
    )