import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from config import *
from managers.tournament_manager import TournamentManager
from bot.keyboards import *
from utils.helpers import get_welcome_message

logger = logging.getLogger(__name__)


class MainHandlers:
    def __init__(self, tournament_manager: TournamentManager):
        self.tournament_manager = tournament_manager

    def _clear_user_data(self, context: ContextTypes.DEFAULT_TYPE):
        """Очистка временных данных пользователя"""
        keys_to_clear = ['pending_promo', 'promo_code', 'registration_type',
                         'is_captain', 'team_name', 'team_mmr',
                         'browsing_teams', 'current_team_index', 'profile_action']
        for key in keys_to_clear:
            if key in context.user_data:
                del context.user_data[key]

    async def _safe_edit_message(self, query, text, reply_markup=None, parse_mode='HTML'):
        """Безопасное редактирование сообщения с обработкой ошибок"""
        try:
            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            return True
        except Exception as e:
            if "Message is not modified" in str(e):
                return True
            else:
                logger.warning(f"Не удалось отредактировать сообщение: {e}")
                try:
                    await query.message.reply_text(
                        text=text,
                        reply_markup=reply_markup,
                        parse_mode=parse_mode
                    )
                    return True
                except Exception as e2:
                    logger.error(f"Не удалось отправить новое сообщение: {e2}")
                    return False

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user

        # Очищаем старые приглашения и временные данные
        self.tournament_manager.cleanup_old_invitations()
        self._clear_user_data(context)

        # Проверяем активацию промокода
        if self.tournament_manager.is_player_activated(user.id):
            await self.show_main_menu(update, context)
            return ConversationHandler.END
        else:
            welcome_text = get_welcome_message(user.first_name)
            await update.message.reply_text(welcome_text, parse_mode='HTML')
            return WAITING_FOR_PROMO

    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать главное меню"""
        user = update.effective_user
        reply_markup = get_main_menu_keyboard()

        text = f"👋 <b>Привет, {user.first_name}!</b>\n\nВыбери действие:"

        if update.callback_query:
            await self._safe_edit_message(update.callback_query, text, reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')

        return ConversationHandler.END

    async def handle_promo_code(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода промокода"""
        promo_code = update.message.text.upper().strip()
        status = self.tournament_manager.check_promo_code(promo_code)

        if status == "not_found":
            await update.message.reply_text(
                "❌ <b>Промокод не найден</b>\n\n"
                "Проверь правильность ввода или обратись к администратору.\n"
                "Введи промокод еще раз:",
                parse_mode='HTML',
                reply_markup=get_back_keyboard("cancel")
            )
            return WAITING_FOR_PROMO
        elif status == "used":
            await update.message.reply_text(
                "⚠️ <b>Промокод уже использован</b>\n\n"
                "Один промокод = одна регистрация.\n"
                "Введи другой промокод:",
                parse_mode='HTML',
                reply_markup=get_back_keyboard("cancel")
            )
            return WAITING_FOR_PROMO
        elif status == "valid":
            context.user_data['pending_promo'] = promo_code

            reply_markup = get_confirmation_keyboard("confirm_promo", "cancel_promo")

            await update.message.reply_text(
                f"🔍 <b>Проверь промокод:</b>\n\n"
                f"<code>{promo_code}</code>\n\n"
                f"Все верно?",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            return CONFIRM_PROMO

    async def handle_promo_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка подтверждения промокода"""
        query = update.callback_query
        await query.answer()

        if query.data == "confirm_promo":
            promo_code = context.user_data.get('pending_promo')
            if not promo_code:
                await self._safe_edit_message(query, "❌ Промокод не найден. Попробуй снова.")
                return WAITING_FOR_PROMO

            if self.tournament_manager.use_promo_code(promo_code):
                context.user_data['promo_code'] = promo_code
                del context.user_data['pending_promo']

                user = update.effective_user
                player_data = {
                    'username': user.username or '',
                    'first_name': user.first_name,
                    'promo_code': promo_code,
                    'activation_date': datetime.now().isoformat()[:19]
                }
                self.tournament_manager.add_activated_player(user.id, player_data)

                await self._safe_edit_message(
                    query,
                    f"✅ <b>Промокод {promo_code} успешно активирован!</b>\n\n"
                    f"Теперь ты можешь участвовать в турнире! 🎮"
                )

                return await self.show_main_menu(update, context)
            else:
                await self._safe_edit_message(query, "❌ Ошибка активации промокода. Попробуй снова.")
                return WAITING_FOR_PROMO
        else:
            if 'pending_promo' in context.user_data:
                del context.user_data['pending_promo']
            await self._safe_edit_message(
                query,
                "🔄 <b>Введи промокод заново:</b>",
                reply_markup=get_back_keyboard("cancel")
            )
            return WAITING_FOR_PROMO

    async def start_team_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало создания команды"""
        query = update.callback_query
        await query.answer()

        keys_to_clear = ['registration_type', 'is_captain', 'team_name', 'team_mmr']
        for key in keys_to_clear:
            if key in context.user_data:
                del context.user_data[key]

        reply_markup = get_registration_keyboard()

        text = (
            "🎯 <b>Создание команды</b>\n\n"
            "Для создания команды тебе понадобится напарник.\n"
            "Если у тебя есть напарник - нажми кнопку ниже.\n\n"
            "Если ты ищешь напарника - создай анкету в разделе «👤 Моя анкета»"
        )

        await self._safe_edit_message(query, text, reply_markup)
        return REGISTER_OPTION

    async def handle_registration_option(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора типа регистрации"""
        query = update.callback_query
        await query.answer()

        if query.data == "with_partner":
            context.user_data['registration_type'] = 'with_partner'

            reply_markup = get_captain_confirmation_keyboard()

            await self._safe_edit_message(
                query,
                "👑 <b>Ты капитан команды?</b>\n\n"
                "Капитан создает команду и приглашает напарника.\n"
                "Если у тебя уже есть команда - найди её в списке.",
                reply_markup
            )
            return WAITING_FOR_CAPTAIN_CONFIRM

        elif query.data == "back_to_main":
            return await self.show_main_menu(update, context)

        elif query.data == "back_to_registration":
            return await self.start_team_creation(update, context)

        return REGISTER_OPTION

    async def handle_captain_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка подтверждения капитана"""
        query = update.callback_query
        await query.answer()

        if query.data == "i_am_captain":
            context.user_data['is_captain'] = True

            await self._safe_edit_message(
                query,
                "👑 <b>Отлично! Ты капитан команды!</b>\n\n"
                "Придумай название для своей команды:\n"
                "<i>Например: «Кибервоины» или «Титан»</i>",
                reply_markup=get_back_keyboard("back_to_captain_confirm")
            )
            return WAITING_FOR_TEAM_NAME

        elif query.data == "find_existing_team":
            return await self.browse_incomplete_teams(update, context)

        elif query.data in ["back_to_registration", "back_to_captain_confirm"]:
            return await self.start_team_creation(update, context)

        return WAITING_FOR_CAPTAIN_CONFIRM

    async def handle_team_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка названия команды"""
        logger.info(f"Обработка названия команды: {update.message.text}")
        """Обработка названия команды"""
        team_name = update.message.text.strip()

        if len(team_name) < 2 or len(team_name) > 30:
            await update.message.reply_text(
                "❌ Название команды должно быть от 2 до 30 символов.\n"
                "Придумай другое название:",
                reply_markup=get_back_keyboard("back_to_captain_confirm")
            )
            return WAITING_FOR_TEAM_NAME

        context.user_data[team_name] = team_name

        # Сохраняем команду сразу после ввода названия (без второго игрока)
        user = update.effective_user
        team_data = {
            'name': team_name,
            'player1': user.first_name,
            'player2': None,
            'mmr': 0,  # Временное значение
            'captain_chat_id': user.id,
            'player2_chat_id': None,
            'status': 'waiting_partner',
            'registration_date': datetime.now().isoformat()[:19]
        }

        team_id = self.tournament_manager.save_team(team_data)

        if team_id:
            context.user_data['temp_team_id'] = team_id
            await update.message.reply_text(
                "📊 <b>Теперь укажи средний MMR команды:</b>\n\n"
                "<i>Сложи MMR обоих игроков и раздели на 2\n"
                "Например: если у тебя 15000, а у напарника 17000,\n"
                "то средний MMR = (15000 + 17000) / 2 = 16000</i>",
                parse_mode='HTML',
                reply_markup=get_back_keyboard("back_to_team_name")
            )
            return WAITING_FOR_MMR
        else:
            await update.message.reply_text(
                "❌ Ошибка при создании команды. Попробуй еще раз.",
                reply_markup=get_back_keyboard("back_to_captain_confirm")
            )
            return WAITING_FOR_TEAM_NAME

    async def handle_team_mmr(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка MMR команды (только для создания команды)"""
        try:
            mmr = int(update.message.text)
            if mmr < 0 or mmr > 50000:
                await update.message.reply_text("⚠️ Введите реальное значение MMR (0-50000):")
                return WAITING_FOR_MMR
        except ValueError:
            await update.message.reply_text("❌ Введите число для MMR:")
            return WAITING_FOR_MMR

        context.user_data['team_mmr'] = mmr

        # Сохраняем команду только после ввода MMR
        user = update.effective_user
        team_data = {
            'name': context.user_data["team_name"],
            'player1': user.first_name,
            'player2': None,
            'mmr': mmr,
            'captain_chat_id': user.id,
            'player2_chat_id': None,
            'status': 'waiting_partner',
            'registration_date': datetime.now().isoformat()[:19]
        }

        team_id = self.tournament_manager.save_team(team_data)

        # Очищаем временные данные
        keys_to_clear = ['team_name', 'team_mmr', 'is_captain', 'registration_type']
        for key in keys_to_clear:
            if key in context.user_data:
                del context.user_data[key]

        if team_id:
            await update.message.reply_text(
                f"✅ <b>Команда «{team_data['name']}» создана!</b>\n\n"
                f"👤 <b>Капитан:</b> {user.first_name}\n"
                f"📊 <b>MMR:</b> {mmr}\n"
                f"🔍 <b>Статус:</b> В поиске напарника\n\n"
                f"Теперь ты можешь найти напарника через меню «🔍 Найти команду»!",
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text("❌ Ошибка при сохранении команды.")

        return await self.show_main_menu(update, context)

    async def handle_solo_mmr(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка MMR для соло-игрока (только для создания анкеты)"""
        # Проверяем, что это действительно создание анкеты, а не команды
        if 'profile_action' not in context.user_data:
            # Если нет флага создания анкеты, игнорируем сообщение
            return ConversationHandler.END

        try:
            mmr = int(update.message.text)
            if mmr < 0 or mmr > 50000:
                await update.message.reply_text("⚠️ Введите реальное значение MMR (0-50000):")
                return WAITING_FOR_SOLO_MMR
        except ValueError:
            await update.message.reply_text("❌ Введите число для MMR:")
            return WAITING_FOR_SOLO_MMR

        user = update.effective_user
        logger.info(f"Создание анкеты для пользователя {user.id} с MMR {mmr}")

        profile_action = context.user_data.get('profile_action', 'create')

        # Создаем анкету соло-игрока
        profile_data = {
            'name': user.first_name,
            'username': user.username or '',
            'mmr': mmr,
            'created_at': datetime.now().isoformat()[:19],
            'chat_id': user.id
        }

        # Используем правильный метод для сохранения анкеты
        success = self.tournament_manager.add_solo_profile(user.id, profile_data)
        logger.info(f"Результат сохранения анкеты: {success}")

        # Очищаем временные данные
        keys_to_clear = ['registration_type', 'profile_action']
        for key in keys_to_clear:
            if key in context.user_data:
                del context.user_data[key]

        if success:
            if profile_action == 'create':
                message = (
                    f"✅ <b>Анкета создана!</b>\n\n"
                    f"👤 <b>Игрок:</b> {user.first_name}\n"
                    f"📊 <b>MMR:</b> {mmr}\n\n"
                    f"Теперь другие игроки могут найти тебя и предложить создать команду!"
                )
            else:
                message = (
                    f"✅ <b>Анкета обновлена!</b>\n\n"
                    f"👤 <b>Игрок:</b> {user.first_name}\n"
                    f"📊 <b>MMR:</b> {mmr}\n\n"
                    f"Твоя анкета теперь отображает актуальные данные!"
                )

            # Отправляем сообщение с кнопкой возврата в меню
            reply_markup = get_back_keyboard()
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await update.message.reply_text("❌ Ошибка при сохранении анкеты.")

        return ConversationHandler.END

    async def show_tournament_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать статус турнира"""
        teams_count = self.tournament_manager.get_team_count()
        tournament_teams = len(self.tournament_manager.get_tournament_teams())
        activated_players = len(self.tournament_manager.get_activated_players())
        solo_profiles = len(self.tournament_manager.get_all_solo_profiles())
        incomplete_teams = len(self.tournament_manager.get_incomplete_teams())

        status_text = f"""
📊 <b>Статус турнира</b>

👥 Зарегистрировано команд: <b>{teams_count}/10</b>
🔍 Команд ищут игрока: <b>{incomplete_teams}</b>
📝 Активных анкет: <b>{solo_profiles}</b>
🏆 Отобрано для турнира: <b>{tournament_teams}/5</b>
🔑 Активировано промокодов: <b>{activated_players}</b>

{'✅ Регистрация открыта' if teams_count < 10 else '❌ Регистрация закрыта'}
{'🎯 Отбор завершен' if tournament_teams > 0 else '⏳ Ожидаем отбора'}
📅 <b>Дата турнира:</b> {TOURNAMENT_DATE}
        """

        reply_markup = get_back_keyboard()

        if update.callback_query:
            await self._safe_edit_message(update.callback_query, status_text, reply_markup)
        else:
            await update.message.reply_text(status_text, reply_markup=reply_markup, parse_mode='HTML')

        return ConversationHandler.END

    async def show_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать справку"""
        help_text = """
🤖 <b>Команды бота:</b>

/start - Главное меню
/status - Статус турнира
/help - Эта справка

<b>Основные функции:</b>
• 👥 Создать команду - регистрация новой команды
• 🔍 Найти команду - поиск команд, которым нужен игрок
• 👤 Моя анкета - управление своей анкетой для поиска
• 📊 Статус турнира - текущая статистика
• 🏆 Фан-зона - поддержать команду (после отбора)

<b>Для администраторов:</b>
/admin - Панель управления
        """
        reply_markup = get_back_keyboard()

        if update.callback_query:
            await self._safe_edit_message(update.callback_query, help_text, reply_markup)
        else:
            await update.message.reply_text(help_text, reply_markup=reply_markup, parse_mode='HTML')

        return ConversationHandler.END

    async def browse_incomplete_teams(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Просмотр команд с одним игроком"""
        query = update.callback_query
        if query:
            await query.answer()

        incomplete_teams = self.tournament_manager.get_incomplete_teams()

        if not incomplete_teams:
            reply_markup = get_back_keyboard()
            message = (
                "😔 <b>Сейчас нет команд, которые ищут игроков.</b>\n\n"
                "Попробуй позже или создай свою команду!"
            )

            if query:
                await self._safe_edit_message(query, message, reply_markup)
            else:
                await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')
            return ConversationHandler.END

        context.user_data['browsing_teams'] = incomplete_teams
        context.user_data['current_team_index'] = 0

        await self.show_current_team(update, context)
        return ConversationHandler.END

    async def show_current_team(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать текущую команду при просмотре"""
        query = update.callback_query
        if query:
            await query.answer()

        browsing_teams = context.user_data.get('browsing_teams', [])
        current_index = context.user_data.get('current_team_index', 0)

        if current_index >= len(browsing_teams):
            await self.browse_incomplete_teams(update, context)
            return ConversationHandler.END

        team = browsing_teams[current_index]

        team_info = f"""
🏆 <b>{team['name']}</b>

👤 <b>Капитан:</b> {team['player1']}
📊 <b>MMR команды:</b> {team.get('mmr', 'Не указан')}
🔍 <b>Статус:</b> Ищет напарника

📊 <b>Команда {current_index + 1} из {len(browsing_teams)}</b>
        """

        keyboard = [
            [InlineKeyboardButton("✅ Вступить в команду", callback_data=f"join_team_{team['team_id']}")],
            [InlineKeyboardButton("➡️ Следующая команда", callback_data="next_team")],
            [InlineKeyboardButton("🔄 Обновить список", callback_data="find_team")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if query:
            await self._safe_edit_message(query, team_info, reply_markup)
        else:
            await update.message.reply_text(team_info, reply_markup=reply_markup, parse_mode='HTML')

        return ConversationHandler.END

    async def show_my_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать профиль пользователя"""
        query = update.callback_query
        await query.answer()

        user = update.effective_user
        user_profile = self.tournament_manager.get_solo_profile(user.id)
        user_teams = self.tournament_manager.get_user_teams(user.id)

        text = f"👤 <b>Твой профиль</b>\n\n"

        if user_profile:
            text += f"📊 <b>MMR:</b> {user_profile['mmr']}\n"
            text += f"📅 <b>Анкета создана:</b> {user_profile.get('created_at', 'N/A')}\n"
            text += "✅ <b>Статус анкеты:</b> Активна\n\n"
        else:
            text += "❌ <b>Анкета не создана</b>\n\n"

        if user_teams:
            text += f"🏆 <b>Твои команды:</b> {len(user_teams)}\n"
            for team in user_teams:
                status = "✅ Полная" if team.get('player2_chat_id') else "🔍 Ищет игрока"
                text += f"• {team['name']} - {status}\n"
        else:
            text += "😔 <b>У тебя пока нет команд</b>\n"

        keyboard = []
        if user_profile:
            keyboard.append([InlineKeyboardButton("🔄 Обновить MMR", callback_data="update_profile")])
            keyboard.append([InlineKeyboardButton("❌ Удалить анкету", callback_data="delete_profile")])
        else:
            keyboard.append([InlineKeyboardButton("📝 Создать анкету", callback_data="create_profile")])

        keyboard.append([InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await self._safe_edit_message(query, text, reply_markup)
        return ConversationHandler.END

    async def start_create_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало создания анкеты"""
        query = update.callback_query
        await query.answer()

        context.user_data['profile_action'] = 'create'

        await self._safe_edit_message(
            query,
            "🎲 <b>Создание анкеты для поиска напарника</b>\n\n"
            "Укажи свой <b>текущий MMR</b> в CS2:\n"
            "<i>Например: 15000</i>",
            reply_markup=get_back_keyboard("back_to_profile")
        )
        return WAITING_FOR_SOLO_MMR

    async def start_update_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало обновления анкеты"""
        query = update.callback_query
        await query.answer()

        context.user_data['profile_action'] = 'update'

        await self._safe_edit_message(
            query,
            "🔄 <b>Обновление MMR в анкете</b>\n\n"
            "Укажи свой <b>текущий MMR</b> в CS2:\n"
            "<i>Например: 15000</i>",
            reply_markup=get_back_keyboard("back_to_profile")
        )
        return WAITING_FOR_SOLO_MMR

    async def handle_delete_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка удаления анкеты"""
        query = update.callback_query
        await query.answer()

        user = update.effective_user

        if self.tournament_manager.remove_solo_profile(user.id):
            await self._safe_edit_message(
                query,
                "✅ <b>Анкета успешно удалена!</b>\n\n"
                "Твоя анкета больше не будет отображаться в поиске.",
                reply_markup=get_back_keyboard("back_to_main")
            )
        else:
            await self._safe_edit_message(
                query,
                "❌ <b>Не удалось удалить анкету</b>\n\n"
                "Возможно, анкета уже была удалена.",
                reply_markup=get_back_keyboard("back_to_profile")
            )

        return ConversationHandler.END

    async def show_fan_zone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Фан-зона"""
        query = update.callback_query
        await query.answer()

        teams = self.tournament_manager.get_tournament_teams()
        if not teams:
            await self._safe_edit_message(
                query,
                f"📋 <b>Список команд для турнира еще не сформирован.</b>\n\n"
                f"Ждем отбора {TOURNAMENT_DATE}! 🔄",
                reply_markup=get_back_keyboard()
            )
            return ConversationHandler.END

        keyboard = []
        for team_id, team_data in teams.items():
            button_text = f"{team_data['name']} ({team_data['player1']} & {team_data['player2']})"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"fan_{team_id}")])

        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await self._safe_edit_message(
            query,
            "🏆 <b>Фан Зона</b> 🏆\n\n"
            "Выбери команду для поддержки:\n"
            "Если твои фавориты победят - получишь 500₽ на баланс! 💰",
            reply_markup
        )

        return ConversationHandler.END

    async def back_to_main_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик возврата в главное меню"""
        query = update.callback_query
        await query.answer()

        self._clear_user_data(context)
        return await self.show_main_menu(update, context)

    async def back_to_profile_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик возврата к профилю"""
        query = update.callback_query
        await query.answer()

        return await self.show_my_profile(update, context)

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена текущего действия"""
        self._clear_user_data(context)

        if update.message:
            await update.message.reply_text('❌ Действие отменено.')
        elif update.callback_query:
            query = update.callback_query
            await query.answer()
            await self._safe_edit_message(query, '❌ Действие отменено.')

        return await self.show_main_menu(update, context)

    async def handle_cancel_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик отмены через callback"""
        query = update.callback_query
        await query.answer()

        return await self.cancel(update, context)