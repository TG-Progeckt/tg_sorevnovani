from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class Player:
    chat_id: int
    username: str
    first_name: str
    promo_code: str = ""
    activation_date: str = ""

@dataclass
class Team:
    team_id: str
    name: str
    player1: str
    player2: Optional[str]
    mmr: int
    captain_chat_id: int
    player2_chat_id: Optional[int]
    status: str
    registration_date: str

@dataclass
class SoloProfile:
    chat_id: int
    name: str
    username: str
    mmr: int
    created_at: str

@dataclass
class TournamentMatch:
    match_id: str
    team1: str
    team2: str
    winner: Optional[str]
    round: int