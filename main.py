import warnings
import logging
import traceback

warnings.filterwarnings("ignore", message="pkg_resources is deprecated")

from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters

from config import BOT_TOKEN, WAITING_FOR_SOLO_MMR, WAITING_FOR_MMR
from managers.data_manager import DataManager
from managers.tournament_manager import TournamentManager
from bot.handlers import MainHandlers
from bot.callback_handlers import CallbackHandlers
from bot.conversation import create_conversation_handler
from bot.admin_handlers import AdminHandlers

# --- Настройка логирования ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def error_handler(update, context):
    """Обработчик ошибок"""
    try:
        # Логируем ошибку
        logger.error(f"Ошибка при обработке update {update}: {context.error}")

        # Логируем traceback для отладки
        logger.error(f"Traceback: {traceback.format_exc()}")

        # Очищаем user_data при ошибке
        if update and update.effective_user:
            if hasattr(context, 'user_data') and context.user_data:
                context.user_data.clear()

        # Отправляем сообщение пользователю
        if update and update.effective_chat:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Произошла ошибка. Попробуйте начать заново с команды /start"
                )
            except Exception as e:
                logger.error(f"Не удалось отправить сообщение об ошибке: {e}")

    except Exception as e:
        logger.error(f"Ошибка в error_handler: {e}")


def main():
    """Основная функция запуска бота"""
    try:
        # Инициализация менеджеров
        data_manager = DataManager()
        tournament_manager = TournamentManager(data_manager)

        # Инициализация обработчиков
        main_handlers = MainHandlers(tournament_manager)
        callback_handlers = CallbackHandlers(tournament_manager, main_handlers)
        admin_handlers = AdminHandlers(tournament_manager)

        # Создаем Application
        application = Application.builder().token(BOT_TOKEN).build()

        # Добавляем обработчик ошибок
        application.add_error_handler(error_handler)

        # Обработчик диалога регистрации
        conv_handler = create_conversation_handler(main_handlers)
        application.add_handler(conv_handler)

        # Основные обработчики
        application.add_handler(CommandHandler("start", main_handlers.start))
        application.add_handler(CommandHandler("status", main_handlers.show_tournament_status))
        application.add_handler(CommandHandler("help", main_handlers.show_help))
        application.add_handler(CommandHandler("admin", admin_handlers.admin_panel))
        application.add_handler(CommandHandler("cancel", main_handlers.cancel))

        # Обработчики callback queries - ГЛАВНОЕ МЕНЮ
        application.add_handler(CallbackQueryHandler(
            callback_handlers.handle_main_menu_callbacks,
            pattern="^create_team|find_team|my_profile|tournament_status|fan_zone|help|back_to_main$"
        ))

        # Обработчики callback queries - ПРОФИЛЬ
        application.add_handler(CallbackQueryHandler(
            callback_handlers.handle_profile_actions,
            pattern="^create_profile|update_profile|delete_profile|back_to_profile$"
        ))

        # Обработчики callback queries - РЕГИСТРАЦИЯ
        application.add_handler(CallbackQueryHandler(
            callback_handlers.handle_registration_callbacks,
            pattern="^with_partner|i_am_captain|find_existing_team|back_to_registration|back_to_captain_confirm$"
        ))

        # Обработчики callback queries - ПРОСМОТР КОМАНД
        application.add_handler(CallbackQueryHandler(
            callback_handlers.handle_team_browsing,
            pattern="^next_team|find_team$"
        ))

        # Обработчики промокодов
        application.add_handler(CallbackQueryHandler(
            main_handlers.handle_promo_confirmation,
            pattern="^confirm_promo|cancel_promo$"
        ))

        application.add_handler(CallbackQueryHandler(
            main_handlers.handle_cancel_callback,
            pattern="^cancel$"
        ))

        # Админ обработчики
        application.add_handler(CallbackQueryHandler(admin_handlers.handle_admin_actions, pattern="^admin_"))
        application.add_handler(CallbackQueryHandler(admin_handlers.handle_winner_selection, pattern="^winner_"))

        # Запуск бота
        logger.info("Бот запускается...")
        print("🎮 True Gamers Tournament Bot запущен!")
        print("📊 Логичная структура навигации активирована")
        print("⚙️ Админ-панель активирована")
        print("🤖 Для остановки нажмите Ctrl+C")

        application.run_polling()

    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        print(f"❌ Критическая ошибка: {e}")


if __name__ == '__main__':
    main()