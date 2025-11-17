import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from config import *
from managers.tournament_manager import TournamentManager
from bot.keyboards import *

logger = logging.getLogger(__name__)

class CallbackHandlers:
    def __init__(self, tournament_manager: TournamentManager, main_handlers):
        self.tournament_manager = tournament_manager
        self.main_handlers = main_handlers

    async def handle_main_menu_callbacks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка callback'ов главного меню"""
        query = update.callback_query
        await query.answer()

        if query.data == "create_team":
            return await self.main_handlers.start_team_creation(update, context)
        elif query.data == "find_team":
            return await self.main_handlers.browse_incomplete_teams(update, context)
        elif query.data == "my_profile":
            return await self.main_handlers.show_my_profile(update, context)
        elif query.data == "tournament_status":
            return await self.main_handlers.show_tournament_status(update, context)
        elif query.data == "fan_zone":
            return await self.main_handlers.show_fan_zone(update, context)
        elif query.data == "help":
            return await self.main_handlers.show_help(update, context)
        elif query.data == "back_to_main":
            return await self.main_handlers.back_to_main_handler(update, context)

        return ConversationHandler.END

    async def handle_profile_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка действий с профилем"""
        query = update.callback_query
        await query.answer()

        if query.data == "create_profile":
            return await self.main_handlers.start_create_profile(update, context)
        elif query.data == "update_profile":
            return await self.main_handlers.start_update_profile(update, context)
        elif query.data == "delete_profile":
            return await self.main_handlers.handle_delete_profile(update, context)
        elif query.data == "back_to_profile":
            return await self.main_handlers.back_to_profile_handler(update, context)

        return ConversationHandler.END

    async def handle_registration_callbacks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка callback'ов регистрации"""
        query = update.callback_query
        await query.answer()

        if query.data == "with_partner":
            return await self.main_handlers.handle_registration_option(update, context)
        elif query.data == "i_am_captain":
            return await self.main_handlers.handle_captain_confirmation(update, context)
        elif query.data == "find_existing_team":
            return await self.main_handlers.handle_captain_confirmation(update, context)
        elif query.data == "back_to_registration":
            return await self.main_handlers.handle_registration_option(update, context)
        elif query.data == "back_to_captain_confirm":
            return await self.main_handlers.handle_captain_confirmation(update, context)

        return ConversationHandler.END

    async def handle_team_browsing(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка просмотра команд"""
        query = update.callback_query
        await query.answer()

        if query.data == "next_team":
            return await self.main_handlers.show_current_team(update, context)
        elif query.data == "find_team":
            return await self.main_handlers.browse_incomplete_teams(update, context)

        return ConversationHandler.END