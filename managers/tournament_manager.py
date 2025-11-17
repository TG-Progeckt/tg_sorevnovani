import random
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List

from managers.data_manager import DataManager
from config import PROMOCODES_FILE

logger = logging.getLogger(__name__)


class TournamentManager:
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager

    def check_promo_code(self, code: str) -> str:
        """Проверка валидности промокода"""
        promo_codes = self.data_manager.load_promo_codes(PROMOCODES_FILE)
        code_clean = code.upper().strip()

        if code_clean not in promo_codes:
            return "not_found"
        elif promo_codes[code_clean]:
            return "used"
        else:
            return "valid"

    def use_promo_code(self, code: str) -> bool:
        """Использование промокода"""
        promo_codes = self.data_manager.load_promo_codes(PROMOCODES_FILE)
        code_clean = code.upper().strip()

        if code_clean in promo_codes and not promo_codes[code_clean]:
            used_codes = self.data_manager.load_data('used_promo_codes')
            if not used_codes:
                used_codes = {}
            used_codes[code_clean] = True
            self.data_manager.save_data(used_codes, 'used_promo_codes')
            return True
        return False

    def get_team_count(self) -> int:
        """Получение количества зарегистрированных команд"""
        teams = self.data_manager.load_data('teams')
        return len(teams)

    def save_team(self, team_data: Dict[str, Any]) -> Optional[str]:
        """Сохранение команды"""
        teams = self.data_manager.load_data('teams')
        team_id = str(len(teams) + 1)
        teams[team_id] = team_data
        if self.data_manager.save_data(teams, 'teams'):
            return team_id
        return None

    def get_all_teams(self) -> Dict[str, Any]:
        """Получение всех команд"""
        return self.data_manager.load_data('teams')

    def add_solo_profile(self, chat_id: int, profile_data: Dict[str, Any]) -> bool:
        """Добавление анкеты соло-игрока"""
        solo_profiles = self.data_manager.load_data('solo_profiles')
        if not solo_profiles:
            solo_profiles = {}

        solo_profiles[str(chat_id)] = profile_data
        return self.data_manager.save_data(solo_profiles, 'solo_profiles')

    def get_solo_profile(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Получение анкеты соло-игрока"""
        solo_profiles = self.data_manager.load_data('solo_profiles')
        return solo_profiles.get(str(chat_id))

    def get_all_solo_profiles(self) -> Dict[str, Any]:
        """Получение всех анкет соло-игроков"""
        return self.data_manager.load_data('solo_profiles')

    def remove_solo_profile(self, chat_id: int) -> bool:
        """Удаление анкеты соло-игрока"""
        solo_profiles = self.data_manager.load_data('solo_profiles')
        if str(chat_id) in solo_profiles:
            del solo_profiles[str(chat_id)]
            return self.data_manager.save_data(solo_profiles, 'solo_profiles')
        return False

    def get_user_teams(self, chat_id: int) -> List[Dict[str, Any]]:
        """Получение всех команд пользователя"""
        teams = self.get_all_teams()
        user_teams = []

        for team_id, team_data in teams.items():
            if (team_data.get('captain_chat_id') == chat_id or
                    team_data.get('player2_chat_id') == chat_id):
                user_teams.append({
                    'team_id': team_id,
                    **team_data
                })

        return user_teams

    def get_incomplete_teams(self) -> List[Dict[str, Any]]:
        """Получение команд с одним игроком"""
        teams = self.get_all_teams()
        incomplete_teams = []

        for team_id, team_data in teams.items():
            if team_data.get('player2_chat_id') is None:
                incomplete_teams.append({
                    'team_id': team_id,
                    **team_data
                })

        return incomplete_teams

    def select_tournament_teams(self) -> List[str]:
        """Выбор команд для турнира"""
        teams = self.get_all_teams()
        if not teams:
            return []

        if len(teams) <= 5:
            selected_ids = list(teams.keys())
        else:
            team_list = list(teams.items())
            random.shuffle(team_list)
            selected_ids = [team_id for team_id, _ in team_list[:5]]

        selected_teams = {team_id: teams[team_id] for team_id in selected_ids}
        self.data_manager.save_data(selected_teams, 'selected_teams')
        return selected_ids

    def get_tournament_teams(self) -> Dict[str, Any]:
        """Получение команд, отобранных для турнира"""
        return self.data_manager.load_data('selected_teams')

    def generate_bracket(self) -> Optional[Dict[str, Any]]:
        """Генерация турнирной сетки"""
        teams = self.get_tournament_teams()
        if len(teams) < 2:
            return None

        team_list = list(teams.items())
        random.shuffle(team_list)

        bracket = {}
        matches = []

        for i in range(0, len(team_list), 2):
            if i + 1 < len(team_list):
                match_id = len(matches) + 1
                match = {
                    'match_id': match_id,
                    'team1': team_list[i][0],
                    'team2': team_list[i + 1][0],
                    'winner': None,
                    'round': 1
                }
                matches.append(match)
                bracket[str(match_id)] = match

        self.data_manager.save_data(bracket, 'bracket')
        return bracket

    def get_bracket(self) -> Dict[str, Any]:
        """Получение турнирной сетки"""
        return self.data_manager.load_data('bracket')

    def set_tournament_winner(self, winner_team_id: str) -> Dict[str, Any]:
        """Установка победителя турнира"""
        winner_data = {
            'team_id': winner_team_id,
            'date': datetime.now().isoformat()[:19],
            'fans_rewarded': False
        }
        self.data_manager.save_data(winner_data, 'winner')
        return winner_data

    def get_activated_players(self) -> Dict[str, Any]:
        """Получение списка игроков, активировавших промокоды"""
        activated_players = self.data_manager.load_data('activated_players')
        return activated_players if activated_players else {}

    def add_activated_player(self, chat_id: int, player_data: Dict[str, Any]) -> bool:
        """Добавление игрока в список активировавших промокоды"""
        activated_players = self.get_activated_players()
        activated_players[str(chat_id)] = player_data
        return self.data_manager.save_data(activated_players, 'activated_players')

    def is_player_activated(self, chat_id: int) -> bool:
        """Проверка, активировал ли игрок промокод"""
        activated_players = self.get_activated_players()
        return str(chat_id) in activated_players

    def is_player_in_team(self, chat_id: int) -> bool:
        """Проверка, состоит ли игрок уже в команде"""
        teams = self.get_all_teams()
        for team_data in teams.values():
            if (team_data.get('captain_chat_id') == chat_id or
                    team_data.get('player2_chat_id') == chat_id):
                return True
        return False

    def cleanup_old_invitations(self):
        """Очистка старых приглашений (старше 24 часов)"""
        pending_invites = self.data_manager.load_data('pending_invites')
        if not pending_invites:
            return

        now = datetime.now()
        updated = False

        for invite_id, invite_data in list(pending_invites.items()):
            timestamp = datetime.fromisoformat(invite_data['timestamp'])
            if now - timestamp > timedelta(hours=24):
                del pending_invites[invite_id]
                updated = True

        if updated:
            self.data_manager.save_data(pending_invites, 'pending_invites')