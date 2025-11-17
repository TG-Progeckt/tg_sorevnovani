import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import ADMIN_CHAT_ID, TOURNAMENT_DATE, ADMIN_ACTIONS, WAITING_WINNER_SELECTION
from bot.keyboards import get_admin_keyboard, get_back_keyboard

logger = logging.getLogger(__name__)

class AdminHandlers:
    def __init__(self, tournament_manager):
        self.tournament_manager = tournament_manager

    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Админ-панель"""
        if update.effective_user.id != ADMIN_CHAT_ID:
            await update.message.reply_text("❌ У вас нет прав для этой команды.")
            return ConversationHandler.END

        teams_count = self.tournament_manager.get_team_count()
        tournament_teams = len(self.tournament_manager.get_tournament_teams())
        bracket = self.tournament_manager.get_bracket()
        solo_profiles = len(self.tournament_manager.get_all_solo_profiles())
        activated_players = len(self.tournament_manager.get_activated_players())

        keyboard = get_admin_keyboard()

        status_text = f"""
⚙️ <b>Админ-панель</b>

👥 Команд зарегистрировано: <b>{teams_count}</b>
🎲 Активных анкет: <b>{solo_profiles}</b>
🏆 Отобрано для турнира: <b>{tournament_teams}</b>
🔑 Активировано промокодов: <b>{activated_players}</b>
📋 Сетка сгенерирована: <b>{'✅' if bracket else '❌'}</b>

Выбери действие:
        """

        await update.message.reply_text(status_text, reply_markup=keyboard, parse_mode='HTML')
        return ADMIN_ACTIONS

    async def handle_admin_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка действий админа"""
        query = update.callback_query
        await query.answer()

        if query.data == "admin_select_teams":
            selected_ids = self.tournament_manager.select_tournament_teams()
            teams = self.tournament_manager.get_tournament_teams()

            if not teams:
                await query.edit_message_text("❌ Нет зарегистрированных команд.")
                return ADMIN_ACTIONS

            notified = 0
            for team_id, team_data in teams.items():
                try:
                    captain_id = team_data['captain_chat_id']
                    await context.bot.send_message(
                        captain_id,
                        f"🎊 <b>Поздравляем!</b> 🎊\n\n"
                        f"Твоя команда <b>«{team_data['name']}»</b> прошла отбор на офлайн-турнир!\n\n"
                        f"📅 <b>Дата:</b> {TOURNAMENT_DATE}\n"
                        f"🏠 <b>Место:</b> Клуб True Gamers\n"
                        f"⏰ <b>Время:</b> 15:00\n\n"
                        f"Готовься к битве! ⚔️",
                        parse_mode='HTML'
                    )
                    notified += 1
                except Exception as e:
                    logger.error(f"Не удалось уведомить капитана: {e}")

            team_list = "\n".join([f"🏆 {data['name']} ({data['player1']} & {data['player2']})" for data in teams.values()])

            await query.edit_message_text(
                f"✅ <b>Отбор завершен!</b>\n\n"
                f"Уведомлено: {notified}/{len(teams)} капитанов\n\n"
                f"<b>Выбранные команды:</b>\n{team_list}",
                parse_mode='HTML'
            )

        elif query.data == "admin_generate_bracket":
            bracket = self.tournament_manager.generate_bracket()

            if not bracket:
                await query.edit_message_text("❌ Недостаточно команд для генерации сетки (нужно минимум 2).")
                return ADMIN_ACTIONS

            bracket_text = "🎯 <b>Турнирная сетка сгенерирована:</b>\n\n"
            for match_id, match in bracket.items():
                teams_data = self.tournament_manager.get_tournament_teams()
                team1 = teams_data[match['team1']]
                team2 = teams_data[match['team2']]
                bracket_text += f"⚔️ <b>Матч {match_id}:</b>\n"
                bracket_text += f"   {team1['name']} vs {team2['name']}\n"
                bracket_text += f"   MMR: {team1['mmr']} vs {team2['mmr']}\n\n"

            await query.edit_message_text(bracket_text, parse_mode='HTML')

        elif query.data == "admin_select_winner":
            teams = self.tournament_manager.get_tournament_teams()
            if not teams:
                await query.edit_message_text("❌ Нет команд для выбора победителя.")
                return ADMIN_ACTIONS

            keyboard = []
            for team_id, team_data in teams.items():
                button_text = f"{team_data['name']} ({team_data['player1']} & {team_data['player2']})"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"winner_{team_id}")])

            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_back")])
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                "🏆 <b>Выбери команду-победителя:</b>",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            return WAITING_WINNER_SELECTION

        elif query.data == "admin_stats":
            teams_count = self.tournament_manager.get_team_count()
            tournament_teams = len(self.tournament_manager.get_tournament_teams())
            solo_profiles = len(self.tournament_manager.get_all_solo_profiles())
            activated_players = len(self.tournament_manager.get_activated_players())
            pending_invites = len(self.tournament_manager.data_manager.load_data('pending_invites') or {})

            stats_text = f"""
📊 <b>Статистика турнира</b>

👥 Всего команд: <b>{teams_count}</b>
📝 Активных анкет: <b>{solo_profiles}</b>
🏆 В турнире: <b>{tournament_teams}</b>
🔑 Активировано промокодов: <b>{activated_players}</b>
📨 Ожидающих приглашений: <b>{pending_invites}</b>

<b>Команды в турнире:</b>
            """

            teams = self.tournament_manager.get_tournament_teams()
            for team_id, team_data in teams.items():
                stats_text += f"\n🏆 {team_data['name']}"

            await query.edit_message_text(stats_text, parse_mode='HTML')

        elif query.data == "admin_cleanup":
            self.tournament_manager.cleanup_old_invitations()
            await query.edit_message_text("✅ Старые приглашения очищены!")

        elif query.data == "admin_back":
            return await self.admin_panel(update, context)

        return ADMIN_ACTIONS

    async def handle_winner_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора победителя"""
        query = update.callback_query
        await query.answer()

        if query.data.startswith("winner_"):
            winner_team_id = query.data[7:]
            teams = self.tournament_manager.get_tournament_teams()
            winner_team = teams.get(winner_team_id)

            if winner_team:
                self.tournament_manager.set_tournament_winner(winner_team_id)

                # Оповещаем победителей
                try:
                    await context.bot.send_message(
                        winner_team['captain_chat_id'],
                        f"🎉 <b>ПОЗДРАВЛЯЕМ!</b> 🎉\n\n"
                        f"Ваша команда <b>«{winner_team['name']}»</b> победила в турнире!\n\n"
                        f"🏆 <b>Главный приз:</b> 10,000₽ на баланс\n"
                        f"👥 <b>Состав:</b> {winner_team['player1']} & {winner_team['player2']}\n\n"
                        f"Заберите призы у администратора!",
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.error(f"Не удалось уведомить победителей: {e}")

                await query.edit_message_text(
                    f"🎊 <b>Победитель объявлен!</b> 🎊\n\n"
                    f"🏆 <b>Команда:</b> {winner_team['name']}\n"
                    f"👥 <b>Состав:</b> {winner_team['player1']} & {winner_team['player2']}\n"
                    f"📊 <b>MMR:</b> {winner_team['mmr']}",
                    parse_mode='HTML'
                )

        return await self.admin_panel(update, context)