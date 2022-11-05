import re
from typing import Optional

import pyautogui


class GameDetector:
    __KNOWN_GAMES = {
        '7 Days To Die': '^7 days to die$',
        'Age of Empires II Definitive Edition': '^age of empires ii: definitive edition$',
        'Apex Legends': '^apex legends$',
        'Battlefield 1': '^battlefield™ 1$',
        'Battlefield 1942': r'^bf1942 \(ver: \w{3}, \d+ \w{3} \d+ [:0-9]+\)$',
        'Battlefield 2': r'^bf2 \(v1.[\.\-0-9]+, pid: [0-9]+\)$',
        'Battlefield 2042': '^battlefield™ 2042$',
        'Battlefield 2142': r'^bf2142 \(v1.[\.\-0-9]+, pid: [0-9]+\)$',
        'Battlefield 3': '^battlefield 3™$',
        'Battlefield 4': '^battlefield 4$',
        'Battlefield Bad Company 2': '^battlefield: bad company 2$',
        'Battlefield V': '^battlefield™ V$',
        'Battlefield Vietnam': '^battlefield vietnam$',
        'Destiny 2': '^destiny 2$',
        'Dota 2': '^dota 2$',
        'Call of Duty 4': '^call of duty 4$',
        'Call of Duty Modern Warfare': '^call of duty®: modern warfare®$',
        'Counter-Strike Global Offensive': '^counter-strike: global offensive$',
        'Fortnite': '^fortnite$',
        'Hyperscape': '^hyperscape$',
        'Metro Redux': '^metro redux$',
        'ParaWorld': r'^paraworld   .*pwclient wip \(base [0-9]+\)$',
        'Portal': '^portal$',
        'Portal 2': '^portal 2$',
        'Rainbox Six Siege': '^rainbow six$',
        'Rocket League': r'^Rocket League \(\d\d-.*\)$',
        'Star Wars Battlefront 2': '^star wars battlefront ii$',
        'Stronghold Crusader': '^crusader$',
        'Team Fortress 2': '^team fortress 2$',
        'The Sims 3': '^the sims 3$',
        'Trackmania': '^trackmania$',
        'Valorant': '^valorant$',
        'Warhammer Vermintide 2': '^warhammer: vermintide 2$'
    }

    __game_regexes: dict = {}
    __configured_games: list = []

    def __init__(self) -> None:
        # Compile regexes for every known game
        for key, pattern in self.__KNOWN_GAMES.items():
            self.__game_regexes[key] = re.compile(pattern, flags=re.IGNORECASE)

    def get_known_games(self) -> list:
        return list(self.__KNOWN_GAMES.keys())

    def set_configured_games(self, configured_games: list) -> None:
        """
        @param configured_games: List of games that currently have rewards configured
        """
        self.__configured_games = configured_games

    def get_configured_games(self) -> list:
        return self.__configured_games

    def get_active_game(self) -> Optional[str]:
        """
        Determine which game is active (=open in the foreground)
        Some games' window titles contain leading/trailing spaces or u200b/non-printing spaces (Call of Duty).
        So, strip spaces and replace u200b-s with nothing
        """
        active_window_title = str(pyautogui.getActiveWindowTitle()).strip().replace('\u200b', '')
        active_game = next(
            (key for key in self.__KNOWN_GAMES.keys() if key in self.__configured_games and
             self.__game_regexes[key].match(active_window_title)),
            None
        )

        return active_game
