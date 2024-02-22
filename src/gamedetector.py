import re
from typing import Optional

import pyautogui


class GameDetector:
    __KNOWN_GAMES = {
        '7 Days To Die': '^7 days to die$',
        'Age of Empires II Definitive Edition': '^age of empires ii: definitive edition$',
        'Apex Legends': '^apex legends$',
        'Battlefield 1': '^battlefield™ 1$',
        'Battlefield 1942': r'^bf1942 \(ver: \w+, \d+ \w+\.? \d+(?: [:0-9]+)?\)$',
        'Battlefield 2': r'^bf2 \(v1.[\.\-0-9]+, pid: [0-9]+\)$',
        'Battlefield 2042': '^battlefield™ 2042$',
        'Battlefield 2142': r'^bf2142 \(v1.[\.\-0-9]+, pid: [0-9]+\)$',
        'Battlefield 3': '^battlefield 3™$',
        'Battlefield 4': '^battlefield 4$',
        'Battlefield Bad Company 2': '^battlefield: bad company 2$',
        'Battlefield V': '^battlefield™ v$',
        'Battlefield Vietnam': '^battlefield vietnam$',
        'Call of Duty': '^call of duty (?:single|multi)player$',
        'Call of Duty 2': '^call of duty 2 (?:single|multi)player$',
        'Call of Duty 4': '^call of duty 4$',
        'Call of Duty Modern Warfare': '^call of duty®: modern warfare®$',
        'Call of Duty Modern Warfare II': '^call of duty® hq$',
        'Call of Duty United Offensive': '^cod:united offensive (?:single|multi)player$',
        'Call of Duty World at War': '^call of duty®$',
        'Counter-Strike': '^counter-strike$',
        'Counter-Strike Condition Zero': '^condition zero$',
        'Counter-Strike Global Offensive': '^counter-strike: global offensive(?: - direct3d 9)?$',
        'Counter-Strike Source': '^counter-strike source$',
        'Day of Defeat': '^day of defeat$',
        'Day of Defeat Source': '^day of defeat source$',
        'DCS World': '^digital combat simulator$',
        'Destiny 2': '^destiny 2$',
        'Dota 2': '^dota 2$',
        'Fortnite': '^fortnite$',
        'Half-Life': '^half-life$',
        'Half-Life 2': '^half-life 2 - direct3d 9$',
        'Half-Life 2 Deathmatch': '^half-life 2 dm$',
        'Half-Life 2 Lost Coast': '^half-life 2: lost coast - direct3d 9$',
        'Half-Life Source': '^half-life - direct3d 9$',
        'Heroes of the Storm': '^heroes of the storm$',
        'Hyperscape': '^hyperscape$',
        'League of Legends': r'^league of legends \(tm\) client$',
        'Left 4 Dead': '^left 4 dead$',
        'Left 4 Dead 2': '^left 4 dead 2 - direct3d 9$',
        'Metro Redux': '^metro redux$',
        'Overwatch': '^overwatch$',
        'ParaWorld': r'^paraworld   .*pwclient wip \(base [0-9]+\)$',
        'Portal': '^portal$',
        'Portal 2': '^portal 2$',
        'PUBG Battlegrounds': '^pubg: battlegrounds$',
        'Quake II': '^quake (?:2|ii rtx)$',
        'Rainbox Six Siege': '^rainbow six$',
        'Rocket League': r'^rocket league \(\d\d-.*\)$',
        'StarCraft II': '^starcraft ii$',
        'Star Wars Battlefront 2': '^star wars battlefront ii$',
        'Star Wars Squadrons': '^star wars™: squadrons$',
        'Stronghold Crusader': '^crusader$',
        'Team Fortress': '^team fortress$',
        'Team Fortress 2': '^team fortress 2$',
        'The Sims 3': '^the sims 3$',
        'The Sims 4': '^the sims™ 4$',
        'Trackmania': '^trackmania$',
        'Unreal': '^unreal$',
        'Unreal II': '^unreal2$',
        'Unreal Tournament': '^unreal tournament$',
        'Unreal Tournament 2003': '^unreal tournament 2003$',
        'Unreal Tournament 2004': '^unreal tournament 2004$',
        'Unreal Tournament 3': '^unreal tournament 3$',
        'Valorant': '^valorant$',
        'Warhammer Vermintide 2': '^warhammer: vermintide 2$',
        'War Thunder': '^war thunder(?: - in battle)?$',
        'World of Tanks': '^wot client$',
        'World of Warcraft': '^world of warcraft$'
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
