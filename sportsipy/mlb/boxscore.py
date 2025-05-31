from datetime import datetime, timedelta
import re
import pandas as pd
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
from ..base import (AbstractParser, int_property_decorator, float_property_decorator,
                    _parse_field, _fetch_html, _clean_stat, _parse_team_abbreviation,
                    _parse_inning_scores, _parse_game_info)
from .player import AbstractPlayer
from .constants import (BOXSCORE_SCHEME, BOXSCORE_URL, BOXSCORES_URL, AWAY, HOME,
                       DAY, NIGHT, BOXSCORE_ELEMENT_INDEX)

class BoxscorePlayer(AbstractPlayer):
    """Player-specific stats for a single MLB game.

    Extends AbstractPlayer to capture MLB-specific stats for a player in a game,
    such as innings pitched, strikes, and win probability. Should be instantiated
    via the Boxscore class.

    Parameters
    ----------
    player_id : str
        Player's ID (e.g., 'altuvjo01' for Jose Altuve), typically in the format
        'LLLLLFFNN' where 'LLLLL' is the first five letters of the last name,
        'FF' is the first two letters of the first name, and 'NN' is a numeric suffix.
    player_name : str
        Player's full name (e.g., 'Jose Altuve').
    player_data : str
        HTML data containing the player's game stats.

    Attributes
    ----------
    player_id : str
        The player's unique ID.
    name : str
        The player's full name.
    """
    def __init__(self, player_id: str, player_name: str, player_data: str):
        self._index: int = 0
        self._average_leverage_index: List[Optional[str]] = []
        self._base_out_runs_added: List[Optional[str]] = []
        self._earned_runs_against: List[Optional[str]] = []
        self._innings_pitched: List[Optional[str]] = []
        self._pitches_thrown: List[Optional[str]] = []
        self._strikes: List[Optional[str]] = []
        self._home_runs_thrown: List[Optional[str]] = []
        self._strikes_thrown: List[Optional[str]] = []
        self._strikes_contact: List[Optional[str]] = []
        self._strikes_swinging: List[Optional[str]] = []
        self._strikes_looking: List[Optional[str]] = []
        self._grounded_balls: List[Optional[str]] = []
        self._fly_balls: List[Optional[str]] = []
        self._line_drives: List[Optional[str]] = []
        self._unknown_bat_types: List[Optional[str]] = []
        self._game_score: List[Optional[str]] = []
        self._inherited_runners: List[Optional[str]] = []
        self._inherited_score: List[Optional[str]] = []
        self._win_probability_added_pitcher: List[Optional[str]] = []
        self._average_leverage_index_pitcher: List[Optional[str]] = []
        self._base_out_runs_saved: List[Optional[str]] = []
        self._win_probability_added: List[Optional[str]] = []
        self._win_probability_for_offensive_player: List[Optional[str]] = []
        self._win_probability_subtracted: List[Optional[str]] = []
        AbstractPlayer.__init__(self, player_id, player_name, player_data)

    @property
    def dataframe(self) -> Optional[pd.DataFrame]:
        """Return a pandas DataFrame of player stats for the game.

        Returns
        -------
        pd.DataFrame
            DataFrame containing all relevant player stats, indexed by player_id.
        """
        fields = {
            'assists': self.assists,
            'at_bats': self.at_bats,
            'average_leverage_index': self.average_leverage_index,
            'average_leverage_index_pitcher': self.average_leverage_index_pitcher,
            'bases_on_balls': self.bases_on_balls,
            'bases_on_balls_given': self.bases_on_balls_given,
            'base_out_runs_added': self.base_out_runs_added,
            'base_out_runs_saved': self.base_out_runs_saved,
            'batters_faced': self.batters_faced,
            'batting_average': self.batting_average,
            'earned_runs_allowed': self.earned_runs_allowed,
            'earned_runs_against': self.earned_runs_against,
            'fly_balls': self.fly_balls,
            'game_score': self.game_score,
            'grounded_balls': self.grounded_balls,
            'hits': self.hits,
            'hits_allowed': self.hits_allowed,
            'home_runs_thrown': self.home_runs_thrown,
            'inherited_runners': self.inherited_runners,
            'inherited_score': self.inherited_score,
            'innings_pitched': self.innings_pitched,
            'line_drives': self.line_drives,
            'name': self.name,
            'on_base_percentage': self.on_base_percentage,
            'on_base_plus_slugging_percentage': self.on_base_plus_slugging_percentage,
            'pitches_thrown': self.pitches_thrown,
            'plate_appearances': self.plate_appearances,
            'putouts': self.putouts,
            'runs': self.runs,
            'runs_allowed': self.runs_allowed,
            'runs_batted_in': self.runs_batted_in,
            'slugging_percentage': self.slugging_percentage,
            'strikes': self.strikes,
            'strikes_contact': self.strikes_contact,
            'strikes_looking': self.strikes_looking,
            'strikes_swinging': self.strikes_swinging,
            'strikes_thrown': self.strikes_thrown,
            'strikeouts': self.strikeouts,
            'times_struck_out': self.times_struck_out,
            'unknown_bat_types': self.unknown_bat_types,
            'win_probability_added': self.win_probability_added,
            'win_probability_added_pitcher': self.win_probability_added_pitcher,
            'win_probability_for_offensive_player': self.win_probability_for_offensive_player,
            'win_probability_subtracted': self.win_probability_subtracted
        }
        return pd.DataFrame([fields], index=[self.player_id])

    @float_property_decorator
    def average_leverage_index(self) -> Optional[float]:
        """Return the player's average leverage index.

        Returns
        -------
        float or None
            Pressure faced (1.0 is average, <0 is lighter).
        """
        return self._average_leverage_index

    @float_property_decorator
    def base_out_runs_added(self) -> Optional[float]:
        """Return the base out runs added.

        Returns
        -------
        float or None
            Number of base out runs added.
        """
        return self._base_out_runs_added

    @float_property_decorator
    def earned_runs_against(self) -> Optional[float]:
        """Return the earned runs against.

        Returns
        -------
        float or None
            Earned runs against (9 * earned_runs / innings_pitched).
        """
        return self._earned_runs_against

    @float_property_decorator
    def innings_pitched(self) -> Optional[float]:
        """Return the innings pitched.

        Returns
        -------
        float or None
            Innings pitched (.0 for full, .1 for 1/3, .2 for 2/3).
        """
        return self._innings_pitched

    @int_property_decorator
    def pitches_thrown(self) -> Optional[int]:
        """Return the number of pitches thrown.

        Returns
        -------
        int or None
            Total pitches thrown.
        """
        return self._pitches_thrown

    @int_property_decorator
    def strikes(self) -> Optional[int]:
        """Return the number of strikes called against the player.

        Returns
        -------
        int or None
            Total strikes called.
        """
        return self._strikes

    @int_property_decorator
    def home_runs_thrown(self) -> Optional[int]:
        """Return the number of home runs thrown.

        Returns
        -------
        int or None
            Total home runs allowed.
        """
        return self._home_runs_thrown

    @int_property_decorator
    def strikes_thrown(self) -> Optional[int]:
        """Return the number of strikes thrown.

        Returns
        -------
        int or None
            Total strikes thrown.
        """
        return self._strikes_thrown

    @int_property_decorator
    def strikes_contact(self) -> Optional[int]:
        """Return the number of contact strikes thrown.

        Returns
        -------
        int or None
            Strikes with batter contact.
        """
        return self._strikes_contact

    @int_property_decorator
    def strikes_swinging(self) -> Optional[int]:
        """Return the number of swinging strikes thrown.

        Returns
        -------
        int or None
            Strikes with batter swinging.
        """
        return self._strikes_swinging

    @int_property_decorator
    def strikes_looking(self) -> Optional[int]:
        """Return the number of looking strikes thrown.

        Returns
        -------
        int or None
            Strikes with batter looking.
        """
        return self._strikes_looking

    @int_property_decorator
    def grounded_balls(self) -> Optional[int]:
        """Return the number of grounded balls allowed.

        Returns
        -------
        int or None
            Total grounded balls.
        """
        return self._grounded_balls

    @int_property_decorator
    def fly_balls(self) -> Optional[int]:
        """Return the number of fly balls allowed.

        Returns
        -------
        int or None
            Total fly balls.
        """
        return self._fly_balls

    @int_property_decorator
    def line_drives(self) -> Optional[int]:
        """Return the number of line drives allowed.

        Returns
        -------
        int or None
            Total line drives.
        """
        return self._line_drives

    @int_property_decorator
    def unknown_bat_types(self) -> Optional[int]:
        """Return the number of unknown bat types.

        Returns
        -------
        int or None
            Total unknown bat types.
        """
        return self._unknown_bat_types

    @int_property_decorator
    def game_score(self) -> Optional[int]:
        """Return the pitcher's game score.

        Returns
        -------
        int or None
            Score based on runs, strikes, etc.
        """
        return self._game_score

    @int_property_decorator
    def inherited_runners(self) -> Optional[int]:
        """Return the number of inherited runners.

        Returns
        -------
        int or None
            Runners inherited by a relief pitcher.
        """
        return self._inherited_runners

    @int_property_decorator
    def inherited_score(self) -> Optional[int]:
        """Return the number of inherited runners who scored.

        Returns
        -------
        int or None
            Inherited runners who scored.
        """
        return self._inherited_score

    @float_property_decorator
    def win_probability_added_pitcher(self) -> Optional[float]:
        """Return the pitcher's win probability added.

        Returns
        -------
        float or None
            Positive influence on game outcome.
        """
        return self._win_probability_added_pitcher

    @float_property_decorator
    def average_leverage_index_pitcher(self) -> Optional[float]:
        """Return the pitcher's average leverage index.

        Returns
        -------
        float or None
            Pressure faced (1.0 is average, <0 is lighter).
        """
        return self._average_leverage_index_pitcher

    @float_property_decorator
    def base_out_runs_saved(self) -> Optional[float]:
        """Return the base out runs saved.

        Returns
        -------
        float or None
            Runs saved based on base runners (0.0 is average).
        """
        return self._base_out_runs_saved

    @float_property_decorator
    def win_probability_added(self) -> Optional[float]:
        """Return the offensive win probability added.

        Returns
        -------
        float or None
            Positive offensive influence on game outcome.
        """
        return self._win_probability_added

    @float_property_decorator
    def win_probability_for_offensive_player(self) -> Optional[float]:
        """Return the offensive player's win probability.

        Returns
        -------
        float or None
            Overall offensive influence (0.0 to 1.0).
        """
        return self._win_probability_for_offensive_player

    @float_property_decorator
    def win_probability_subtracted(self) -> Optional[float]:
        """Return the offensive win probability subtracted.

        Returns
        -------
        float or None
            Negative offensive influence on game outcome.
        """
        return self._win_probability_subtracted

class Boxscore:
    """Detailed statistics for an MLB game.

    Captures game-level data such as date, time, teams, scores, and advanced
    metrics like win probability and innings pitched. Also manages player stats
    via BoxscorePlayer instances.

    Parameters
    ----------
    uri : str
        The relative link to the boxscore page (e.g., 'BOS/BOS201806070').

    Attributes
    ----------
    uri : str
        The boxscore URI.
    date : str
        The game date.
    winner : str
        The winning team (HOME or AWAY).
    away_players : List[BoxscorePlayer]
        List of away team player instances.
    home_players : List[BoxscorePlayer]
        List of home team player instances.
    """
    def __init__(self, uri: str):
        self._uri: str = uri
        self._date: Optional[str] = None
        self._time: Optional[str] = None
        self._attendance: Optional[str] = None
        self._venue: Optional[str] = None
        self._time_of_day: Optional[str] = None
        self._duration: Optional[str] = None
        self._away_name: Optional[BeautifulSoup] = None
        self._home_name: Optional[BeautifulSoup] = None
        self._summary: Optional[Dict[str, List[Optional[int]]]] = None
        self._winner: Optional[str] = None
        self._winning_name: Optional[str] = None
        self._winning_abbr: Optional[str] = None
        self._losing_name: Optional[str] = None
        self._losing_abbr: Optional[str] = None
        self._away_at_bats: Optional[str] = None
        self._away_runs: Optional[str] = None
        self._away_hits: Optional[str] = None
        self._away_rbi: Optional[str] = None
        self._away_earned_runs: Optional[str] = None
        self._away_bases_on_balls: Optional[str] = None
        self._away_strikeouts: Optional[str] = None
        self._away_plate_appearances: Optional[str] = None
        self._away_batting_average: Optional[str] = None
        self._away_on_base_percentage: Optional[str] = None
        self._away_slugging_percentage: Optional[str] = None
        self._away_on_base_plus: Optional[str] = None
        self._away_pitches: Optional[str] = None
        self._away_strikes: Optional[str] = None
        self._away_win_probability_for_offensive_player: Optional[str] = None
        self._away_average_leverage_index: Optional[str] = None
        self._away_win_probability_added: Optional[str] = None
        self._away_win_probability_subtracted: Optional[str] = None
        self._away_base_out_runs_added: Optional[str] = None
        self._away_putouts: Optional[str] = None
        self._away_assists: Optional[str] = None
        self._away_innings_pitched: Optional[str] = None
        self._away_home_runs: Optional[str] = None
        self._away_strikes_by_contact: Optional[str] = None
        self._away_strikes_swinging: Optional[str] = None
        self._away_strikes_looking: Optional[str] = None
        self._away_grounded_balls: Optional[str] = None
        self._away_fly_balls: Optional[str] = None
        self._away_line_drives: Optional[str] = None
        self._away_unknown_bat_type: Optional[str] = None
        self._away_game_score: Optional[str] = None
        self._away_inherited_runners: Optional[str] = None
        self._away_inherited_score: Optional[str] = None
        self._away_win_probability_by_pitcher: Optional[str] = None
        self._away_base_out_runs_saved: Optional[str] = None
        self._home_at_bats: Optional[str] = None
        self._home_runs: Optional[str] = None
        self._home_hits: Optional[str] = None
        self._home_rbi: Optional[str] = None
        self._home_earned_runs: Optional[str] = None
        self._home_bases_on_balls: Optional[str] = None
        self._home_strikeouts: Optional[str] = None
        self._home_plate_appearances: Optional[str] = None
        self._home_batting_average: Optional[str] = None
        self._home_on_base_percentage: Optional[str] = None
        self._home_slugging_percentage: Optional[str] = None
        self._home_on_base_plus: Optional[str] = None
        self._home_pitches: Optional[str] = None
        self._home_strikes: Optional[str] = None
        self._home_win_probability_for_offensive_player: Optional[str] = None
        self._home_average_leverage_index: Optional[str] = None
        self._home_win_probability_added: Optional[str] = None
        self._home_win_probability_subtracted: Optional[str] = None
        self._home_base_out_runs_added: Optional[str] = None
        self._home_putouts: Optional[str] = None
        self._home_assists: Optional[str] = None
        self._home_innings_pitched: Optional[str] = None
        self._home_home_runs: Optional[str] = None
        self._home_strikes_by_contact: Optional[str] = None
        self._home_strikes_swinging: Optional[str] = None
        self._home_strikes_looking: Optional[str] = None
        self._home_grounded_balls: Optional[str] = None
        self._home_fly_balls: Optional[str] = None
        self._home_line_drives: Optional[str] = None
        self._home_unknown_bat_type: Optional[str] = None
        self._home_game_score: Optional[str] = None
        self._home_inherited_runners: Optional[str] = None
        self._home_inherited_score: Optional[str] = None
        self._home_win_probability_by_pitcher: Optional[str] = None
        self._home_base_out_runs_saved: Optional[str] = None
        self._away_players: List[BoxscorePlayer] = []
        self._home_players: List[BoxscorePlayer] = []
        self._parse_game_data()

    def __str__(self) -> str:
        """Return the string representation of the boxscore."""
        away = self._away_name.get_text(strip=True) if self._away_name else 'Unknown'
        home = self._home_name.get_text(strip=True) if self._home_name else 'Unknown'
        return f'Boxscore for {away} at {home} ({self.date})'

    def __repr__(self) -> str:
        """Return the string representation of the boxscore."""
        return self.__str__()

    def _fetch_boxscore(self) -> Optional[BeautifulSoup]:
        """Fetch the boxscore HTML.

        Returns
        -------
        BeautifulSoup or None
            Parsed HTML or None if fetching fails.
        """
        url = BOXSCORE_URL % self._uri
        return _fetch_html(url)

    def _parse_summary(self, soup: BeautifulSoup) -> Dict[str, List[Optional[int]]]:
        """Parse inning-by-inning scores.

        Parameters
        ----------
        soup : BeautifulSoup
            Parsed boxscore HTML.

        Returns
        -------
        Dict[str, List[Optional[int]]]
            Dictionary with 'away' and 'home' keys, each containing a list of scores.
        """
        summary = {'away': [], 'home': []}
        table = soup.select_one(BOXSCORE_SCHEME['summary'])
        if not table:
            return summary
        rows = table.find_all('tr')
        for i, row in enumerate(rows):
            if i == 0:
                continue  # Skip header
            scores = _parse_inning_scores(row)
            summary['away' if i == 1 else 'home'] = scores
        return summary

    def _parse_name(self, field: str, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """Parse a team's name tag.

        Parameters
        ----------
        field : str
            The field to parse ('away_name' or 'home_name').
        soup : BeautifulSoup
            Parsed boxscore HTML.

        Returns
        -------
        BeautifulSoup or None
            The team's name tag.
        """
        selector = BOXSCORE_SCHEME.get(field)
        if not selector:
            return None
        tag = soup.select_one(selector)
        return tag

    def _find_boxscore_tables(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        """Find boxscore tables.

        Parameters
        ----------
        soup : BeautifulSoup
            Parsed boxscore HTML.

        Returns
        -------
        List[BeautifulSoup]
            List of boxscore table elements.
        """
        tables = []
        for table in soup.find_all('table'):
            table_id = table.get('id', '')
            if 'pitching' in table_id or 'batting' in table_id:
                tables.append(table)
        return tables

    def _find_player_id(self, row: BeautifulSoup) -> Optional[str]:
        """Find a player's ID.

        Parameters
        ----------
        row : BeautifulSoup
            Table row for a player.

        Returns
        -------
        str or None
            Player's ID (e.g., 'altuvjo01').
        """
        th = row.find('th')
        return th.get('data-append-csv') if th else None

    def _find_player_name(self, row: BeautifulSoup) -> Optional[str]:
        """Find a player's name.

        Parameters
        ----------
        row : BeautifulSoup
            Table row for a player.

        Returns
        -------
        str or None
            Player's full name.
        """
        a = row.find('a')
        return a.get_text(strip=True) if a else None

    def _extract_player_stats(self, table: BeautifulSoup, player_dict: Dict, team: str) -> Dict:
        """Extract player stats from a table.

        Parameters
        ----------
        table : BeautifulSoup
            Boxscore table.
        player_dict : Dict
            Dictionary of player data.
        team : str
            Team identifier (HOME or AWAY).

        Returns
        -------
        Dict
            Updated player dictionary.
        """
        tbody = table.find('tbody')
        if not tbody:
            return player_dict
        for row in tbody.find_all('tr'):
            player_id = self._find_player_id(row)
            if not player_id:
                continue
            name = self._find_player_name(row)
            row_html = str(row).strip()
            if player_id in player_dict:
                player_dict[player_id]['data'] += row_html
            else:
                player_dict[player_id] = {'name': name, 'data': row_html, 'team': team}
        return player_dict

    def _instantiate_players(self, player_dict: Dict) -> Tuple[List[BoxscorePlayer], List[BoxscorePlayer]]:
        """Create player instances.

        Parameters
        ----------
        player_dict : Dict
            Dictionary of player data.

        Returns
        -------
        Tuple[List[BoxscorePlayer], List[BoxscorePlayer]]
            Lists of away and home player instances.
        """
        away_players = []
        home_players = []
        for player_id, details in player_dict.items():
            player = BoxscorePlayer(player_id, details['name'], details['data'])
            if details['team'] == HOME:
                home_players.append(player)
            else:
                away_players.append(player)
        return away_players, home_players

    def _find_players(self, soup: BeautifulSoup) -> Tuple[List[BoxscorePlayer], List[BoxscorePlayer]]:
        """Find all players in the boxscore.

        Parameters
        ----------
        soup : BeautifulSoup
            Parsed boxscore HTML.

        Returns
        -------
        Tuple[List[BoxscorePlayer], List[BoxscorePlayer]]
            Lists of away and home player instances.
        """
        player_dict = {}
        tables = self._find_boxscore_tables(soup)
        for i, table in enumerate(tables):
            team = HOME if i % 2 == 1 else AWAY
            player_dict = self._extract_player_stats(table, player_dict, team)
        return self._instantiate_players(player_dict)

    def _parse_game_data(self) -> None:
        """Parse all game data."""
        soup = self._fetch_boxscore()
        if not soup:
            return
        game_info = _parse_game_info(soup, BOXSCORE_SCHEME['game_info'])
        self._date = game_info['date']
        self._time = game_info['time']
        self._attendance = game_info['attendance']
        self._venue = game_info['venue']
        self._duration = game_info['duration']
        self._time_of_day = game_info['time_of_day']
        self._summary = self._parse_summary(soup)
        self._away_name = self._parse_name('away_name', soup)
        self._home_name = self._parse_name('home_name', soup)
        for field in self.__dict__:
            if field in ('_uri', '_date', '_time', '_attendance', '_venue', '_duration',
                         '_time_of_day', '_summary', '_away_name', '_home_name',
                         '_away_players', '_home_players', '_winner', '_winning_name',
                         '_winning_abbr', '_losing_name', '_losing_abbr'):
                continue
            short_field = field.lstrip('_')
            index = BOXSCORE_ELEMENT_INDEX.get(short_field, 0)
            value = _clean_stat(_parse_field(BOXSCORE_SCHEME, soup, short_field, index))
            setattr(self, field, value)
        self._away_players, self._home_players = self._find_players(soup)

    @property
    def dataframe(self) -> Optional[pd.DataFrame]:
        """Return a pandas DataFrame of game stats.

        Returns
        -------
        pd.DataFrame or None
            DataFrame of game stats, indexed by URI.
        """
        if self._away_runs is None and self._home_runs is None:
            return None
        fields = {
            'date': self.date,
            'time': self.time,
            'venue': self.venue,
            'attendance': self.attendance,
            'duration': self.duration,
            'time_of_day': self.time_of_day,
            'winner': self.winner,
            'winning_name': self.winning_name,
            'winning_abbr': self.winning_abbr,
            'losing_name': self.losing_name,
            'losing_abbr': self.losing_abbr,
            'away_at_bats': self.away_at_bats,
            'away_runs': self.away_runs,
            'away_hits': self.away_hits,
            'away_rbi': self.away_rbi,
            'away_earned_runs': self.away_earned_runs,
            'away_bases_on_balls': self.away_bases_on_balls,
            'away_strikeouts': self.away_strikeouts,
            'away_plate_appearances': self.away_plate_appearances,
            'away_batting_average': self.away_batting_average,
            'away_on_base_percentage': self.away_on_base_percentage,
            'away_slugging_percentage': self.away_slugging_percentage,
            'away_on_base_plus': self.away_on_base_plus,
            'away_pitches': self.away_pitches,
            'away_strikes': self.away_strikes,
            'away_win_probability_for_offensive_player': self.away_win_probability_for_offensive_player,
            'away_average_leverage_index': self.away_average_leverage_index,
            'away_win_probability_added': self.away_win_probability_added,
            'away_win_probability_subtracted': self.away_win_probability_subtracted,
            'away_base_out_runs_added': self.away_base_out_runs_added,
            'away_putouts': self.away_putouts,
            'away_assists': self.away_assists,
            'away_innings_pitched': self.away_innings_pitched,
            'away_home_runs': self.away_home_runs,
            'away_strikes_by_contact': self.away_strikes_by_contact,
            'away_strikes_swinging': self.away_strikes_swinging,
            'away_strikes_looking': self.away_strikes_looking,
            'away_grounded_balls': self.away_grounded_balls,
            'away_fly_balls': self.away_fly_balls,
            'away_line_drives': self.away_line_drives,
            'away_unknown_bat_type': self.away_unknown_bat_type,
            'away_game_score': self.away_game_score,
            'away_inherited_runners': self.away_inherited_runners,
            'away_inherited_score': self.away_inherited_score,
            'away_win_probability_by_pitcher': self.away_win_probability_by_pitcher,
            'away_base_out_runs_saved': self.away_base_out_runs_saved,
            'home_at_bats': self.home_at_bats,
            'home_runs': self.home_runs,
            'home_hits': self.home_hits,
            'home_rbi': self.home_rbi,
            'home_earned_runs': self.home_earned_runs,
            'home_bases_on_balls': self.home_bases_on_balls,
            'home_strikeouts': self.home_strikeouts,
            'home_plate_appearances': self.home_plate_appearances,
            'home_batting_average': self.home_batting_average,
            'home_on_base_percentage': self.home_on_base_percentage,
            'home_slugging_percentage': self.home_slugging_percentage,
            'home_on_base_plus': self.home_on_base_plus,
            'home_pitches': self.home_pitches,
            'home_strikes': self.home_strikes,
            'home_win_probability_for_offensive_player': self.home_win_probability_for_offensive_player,
            'home_average_leverage_index': self.home_average_leverage_index,
            'home_win_probability_added': self.home_win_probability_added,
            'home_win_probability_subtracted': self.home_win_probability_subtracted,
            'home_base_out_runs_added': self.home_base_out_runs_added,
            'home_putouts': self.home_putouts,
            'home_assists': self.home_assists,
            'home_innings_pitched': self.home_innings_pitched,
            'home_home_runs': self.home_home_runs,
            'home_strikes_by_contact': self.home_strikes_by_contact,
            'home_strikes_swinging': self.home_strikes_swinging,
            'home_strikes_looking': self.home_strikes_looking,
            'home_grounded_balls': self.home_grounded_balls,
            'home_fly_balls': self.home_fly_balls,
            'home_line_drives': self.home_line_drives,
            'home_unknown_bat_type': self.home_unknown_bat_type,
            'home_game_score': self.home_game_score,
            'home_inherited_runners': self.home_inherited_runners,
            'home_inherited_score': self.home_inherited_score,
            'home_win_probability_by_pitcher': self.home_win_probability_by_pitcher,
            'home_base_out_runs_saved': self.home_base_out_runs_saved
        }
        return pd.DataFrame([fields], index=[self._uri])

    @property
    def away_players(self) -> List[BoxscorePlayer]:
        """Return the away team players."""
        return self._away_players

    @property
    def home_players(self) -> List[BoxscorePlayer]:
        """Return the home team players."""
        return self._home_players

    @property
    def date(self) -> Optional[str]:
        """Return the game date."""
        return self._date

    @property
    def time(self) -> Optional[str]:
        """Return the game start time."""
        return self._time

    @property
    def venue(self) -> Optional[str]:
        """Return the game venue."""
        return self._venue

    @int_property_decorator
    def attendance(self) -> Optional[int]:
        """Return the game attendance."""
        return self._attendance

    @property
    def duration(self) -> Optional[str]:
        """Return the game duration."""
        return self._duration

    @property
    def time_of_day(self) -> Optional[str]:
        """Return whether the game was played during the day or night."""
        if self._time_of_day and 'night' in self._time_of_day.lower():
            return NIGHT
        return DAY

    @property
    def summary(self) -> Optional[Dict[str, List[Optional[int]]]]:
        """Return the inning-by-inning scores."""
        return self._summary

    @property
    def winner(self) -> Optional[str]:
        """Return the winning team (HOME or AWAY)."""
        if self.home_runs is not None and self.away_runs is not None:
            return HOME if self.home_runs > self.away_runs else AWAY
        return None

    @property
    def winning_name(self) -> Optional[str]:
        """Return the winning team's name."""
        if self.winner == HOME and self._home_name:
            return self._home_name.get_text(strip=True)
        elif self.winner == AWAY and self._away_name:
            return self._away_name.get_text(strip=True)
        return None

    @property
    def winning_abbr(self) -> Optional[str]:
        """Return the winning team's abbreviation."""
        if self.winner == HOME and self._home_name:
            return _parse_team_abbreviation(self._home_name)
        elif self.winner == AWAY and self._away_name:
            return _parse_team_abbreviation(self._away_name)
        return None

    @property
    def losing_name(self) -> Optional[str]:
        """Return the losing team's name."""
        if self.winner == HOME and self._away_name:
            return self._away_name.get_text(strip=True)
        elif self.winner == AWAY and self._home_name:
            return self._home_name.get_text(strip=True)
        return None

    @property
    def losing_abbr(self) -> Optional[str]:
        """Return the losing team's abbreviation."""
        if self.winner == HOME and self._away_name:
            return _parse_team_abbreviation(self._away_name)
        elif self.winner == AWAY and self._home_name:
            return _parse_team_abbreviation(self._home_name)
        return None

    @int_property_decorator
    def away_at_bats(self) -> Optional[int]:
        """Return the away team's at-bats."""
        return self._away_at_bats

    @int_property_decorator
    def away_runs(self) -> Optional[int]:
        """Return the away team's runs."""
        return self._away_runs

    @int_property_decorator
    def away_hits(self) -> Optional[int]:
        """Return the away team's hits."""
        return self._away_hits

    @int_property_decorator
    def away_rbi(self) -> Optional[int]:
        """Return the away team's runs batted in."""
        return self._away_rbi

    @float_property_decorator
    def away_earned_runs(self) -> Optional[float]:
        """Return the away team's earned runs."""
        return self._away_earned_runs

    @int_property_decorator
    def away_bases_on_balls(self) -> Optional[int]:
        """Return the away team's bases on balls."""
        return self._away_bases_on_balls

    @int_property_decorator
    def away_strikeouts(self) -> Optional[int]:
        """Return the away team's strikeouts."""
        return self._away_strikeouts

    @int_property_decorator
    def away_plate_appearances(self) -> Optional[int]:
        """Return the away team's plate appearances."""
        return self._away_plate_appearances

    @float_property_decorator
    def away_batting_average(self) -> Optional[float]:
        """Return the away team's batting average."""
        return self._away_batting_average

    @float_property_decorator
    def away_on_base_percentage(self) -> Optional[float]:
        """Return the away team's on-base percentage."""
        return self._away_on_base_percentage

    @float_property_decorator
    def away_slugging_percentage(self) -> Optional[float]:
        """Return the away team's slugging percentage."""
        return self._away_slugging_percentage

    @float_property_decorator
    def away_on_base_plus(self) -> Optional[float]:
        """Return the away team's on-base plus slugging."""
        return self._away_on_base_plus

    @int_property_decorator
    def away_pitches(self) -> Optional[int]:
        """Return the away team's pitches faced."""
        return self._away_pitches

    @int_property_decorator
    def away_strikes(self) -> Optional[int]:
        """Return the away team's strikes called."""
        return self._away_strikes

    @float_property_decorator
    def away_win_probability_for_offensive_player(self) -> Optional[float]:
        """Return the away team's offensive win probability."""
        return self._away_win_probability_for_offensive_player

    @float_property_decorator
    def away_average_leverage_index(self) -> Optional[float]:
        """Return the away team's average leverage index."""
        return self._away_average_leverage_index

    @float_property_decorator
    def away_win_probability_added(self) -> Optional[float]:
        """Return the away team's win probability added."""
        return self._away_win_probability_added

    @float_property_decorator
    def away_win_probability_subtracted(self) -> Optional[float]:
        """Return the away team's win probability subtracted."""
        return self._away_win_probability_subtracted

    @float_property_decorator
    def away_base_out_runs_added(self) -> Optional[float]:
        """Return the away team's base out runs added."""
        return self._away_base_out_runs_added

    @int_property_decorator
    def away_putouts(self) -> Optional[int]:
        """Return the away team's putouts."""
        return self._away_putouts

    @int_property_decorator
    def away_assists(self) -> Optional[int]:
        """Return the away team's assists."""
        return self._away_assists

    @float_property_decorator
    def away_innings_pitched(self) -> Optional[float]:
        """Return the away team's innings pitched."""
        return self._away_innings_pitched

    @int_property_decorator
    def away_home_runs(self) -> Optional[int]:
        """Return the away team's home runs allowed."""
        return self._away_home_runs

    @int_property_decorator
    def away_strikes_by_contact(self) -> Optional[int]:
        """Return the away team's contact strikes."""
        return self._away_strikes_by_contact

    @int_property_decorator
    def away_strikes_swinging(self) -> Optional[int]:
        """Return the away team's swinging strikes."""
        return self._away_strikes_swinging

    @int_property_decorator
    def away_strikes_looking(self) -> Optional[int]:
        """Return the away team's looking strikes."""
        return self._away_strikes_looking

    @int_property_decorator
    def away_grounded_balls(self) -> Optional[int]:
        """Return the away team's grounded balls."""
        return self._away_grounded_balls

    @int_property_decorator
    def away_fly_balls(self) -> Optional[int]:
        """Return the away team's fly balls."""
        return self._away_fly_balls

    @int_property_decorator
    def away_line_drives(self) -> Optional[int]:
        """Return the away team's line drives."""
        return self._away_line_drives

    @int_property_decorator
    def away_unknown_bat_type(self) -> Optional[int]:
        """Return the away team's unknown bat types."""
        return self._away_unknown_bat_type

    @int_property_decorator
    def away_game_score(self) -> Optional[int]:
        """Return the away team's game score."""
        return self._away_game_score

    @int_property_decorator
    def away_inherited_runners(self) -> Optional[int]:
        """Return the away team's inherited runners."""
        return self._away_inherited_runners

    @int_property_decorator
    def away_inherited_score(self) -> Optional[int]:
        """Return the away team's inherited score."""
        return self._away_inherited_score

    @float_property_decorator
    def away_win_probability_by_pitcher(self) -> Optional[float]:
        """Return the away team's pitcher win probability."""
        return self._away_win_probability_by_pitcher

    @float_property_decorator
    def away_base_out_runs_saved(self) -> Optional[float]:
        """Return the away team's base out runs saved."""
        return self._away_base_out_runs_saved

    @int_property_decorator
    def home_at_bats(self) -> Optional[int]:
        """Return the home team's at-bats."""
        return self._home_at_bats

    @int_property_decorator
    def home_runs(self) -> Optional[int]:
        """Return the home team's runs."""
        return self._home_runs

    @int_property_decorator
    def home_hits(self) -> Optional[int]:
        """Return the home team's hits."""
        return self._home_hits

    @int_property_decorator
    def home_rbi(self) -> Optional[int]:
        """Return the home team's runs batted in."""
        return self._home_rbi

    @float_property_decorator
    def home_earned_runs(self) -> Optional[float]:
        """Return the home team's earned runs."""
        return self._home_earned_runs

    @int_property_decorator
    def home_bases_on_balls(self) -> Optional[int]:
        """Return the home team's bases on balls."""
        return self._home_bases_on_balls

    @int_property_decorator
    def home_strikeouts(self) -> Optional[int]:
        """Return the home team's strikeouts."""
        return self._home_strikeouts

    @int_property_decorator
    def home_plate_appearances(self) -> Optional[int]:
        """Return the home team's plate appearances."""
        return self._home_plate_appearances

    @float_property_decorator
    def home_batting_average(self) -> Optional[float]:
        """Return the home team's batting average."""
        return self._home_batting_average

    @float_property_decorator
    def home_on_base_percentage(self) -> Optional[float]:
        """Return the home team's on-base percentage."""
        return self._home_on_base_percentage

    @float_property_decorator
    def home_slugging_percentage(self) -> Optional[float]:
        """Return the home team's slugging percentage."""
        return self._home_slugging_percentage

    @float_property_decorator
    def home_on_base_plus(self) -> Optional[float]:
        """Return the home team's on-base plus slugging."""
        return self._home_on_base_plus

    @int_property_decorator
    def home_pitches(self) -> Optional[int]:
        """Return the home team's pitches faced."""
        return self._home_pitches

    @int_property_decorator
    def home_strikes(self) -> Optional[int]:
        """Return the home team's strikes called."""
        return self._home_strikes

    @float_property_decorator
    def home_win_probability_for_offensive_player(self) -> Optional[float]:
        """Return the home team's offensive win probability."""
        return self._home_win_probability_for_offensive_player

    @float_property_decorator
    def home_average_leverage_index(self) -> Optional[float]:
        """Return the home team's average leverage index."""
        return self._home_average_leverage_index

    @float_property_decorator
    def home_win_probability_added(self) -> Optional[float]:
        """Return the home team's win probability added."""
        return self._home_win_probability_added

    @float_property_decorator
    def home_win_probability_subtracted(self) -> Optional[float]:
        """Return the home team's win probability subtracted."""
        return self._home_win_probability_subtracted

    @float_property_decorator
    def home_base_out_runs_added(self) -> Optional[float]:
        """Return the home team's base out runs added."""
        return self._home_base_out_runs_added

    @int_property_decorator
    def home_putouts(self) -> Optional[int]:
        """Return the home team's putouts."""
        return self._home_putouts

    @int_property_decorator
    def home_assists(self) -> Optional[int]:
        """Return the home team's assists."""
        return self._home_assists

    @float_property_decorator
    def home_innings_pitched(self) -> Optional[float]:
        """Return the home team's innings pitched."""
        return self._home_innings_pitched

    @int_property_decorator
    def home_home_runs(self) -> Optional[int]:
        """Return the home team's home runs allowed."""
        return self._home_home_runs

    @int_property_decorator
    def home_strikes_by_contact(self) -> Optional[int]:
        """Return the home team's contact strikes."""
        return self._home_strikes_by_contact

    @int_property_decorator
    def home_strikes_swinging(self) -> Optional[int]:
        """Return the home team's swinging strikes."""
        return self._home_strikes_swinging

    @int_property_decorator
    def home_strikes_looking(self) -> Optional[int]:
        """Return the home team's looking strikes."""
        return self._home_strikes_looking

    @int_property_decorator
    def home_grounded_balls(self) -> Optional[int]:
        """Return the home team's grounded balls."""
        return self._home_grounded_balls

    @int_property_decorator
    def home_fly_balls(self) -> Optional[int]:
        """Return the home team's fly balls."""
        return self._home_fly_balls

    @int_property_decorator
    def home_line_drives(self) -> Optional[int]:
        """Return the home team's line drives."""
        return self._home_line_drives

    @int_property_decorator
    def home_unknown_bat_type(self) -> Optional[int]:
        """Return the home team's unknown bat types."""
        return self._home_unknown_bat_type

    @int_property_decorator
    def home_game_score(self) -> Optional[int]:
        """Return the home team's game score."""
        return self._home_game_score

    @int_property_decorator
    def home_inherited_runners(self) -> Optional[int]:
        """Return the home team's inherited runners."""
        return self._home_inherited_runners

    @int_property_decorator
    def home_inherited_score(self) -> Optional[int]:
        """Return the home team's inherited score."""
        return self._home_inherited_score

    @float_property_decorator
    def home_win_probability_by_pitcher(self) -> Optional[float]:
        """Return the home team's pitcher win probability."""
        return self._home_win_probability_by_pitcher

    @float_property_decorator
    def home_base_out_runs_saved(self) -> Optional[float]:
        """Return the home team's base out runs saved."""
        return self._home_base_out_runs_saved

class Boxscores:
    """Search for MLB games on a specific day or date range.

    Retrieves a dictionary of games played on the specified date(s), including
    team names, abbreviations, scores, and boxscore URIs.

    Parameters
    ----------
    date : datetime
        The start date to search for games.
    end_date : datetime, optional
        The end date for the search range. Defaults to the start date.

    Attributes
    ----------
    games : Dict[str, List[Dict]]
        Dictionary of games by date, where each game includes team and score details.
    """
    def __init__(self, date: datetime, end_date: Optional[datetime] = None):
        self._boxscores: Dict[str, List[Dict]] = {}
        self._find_games(date, end_date)

    def __str__(self) -> str:
        """Return the string representation of the boxscores."""
        return f"MLB games for {', '.join(self._boxscores.keys())}"

    def __repr__(self) -> str:
        """Return the string representation of the boxscores."""
        return self.__str__()

    @property
    def games(self) -> Dict[str, List[Dict]]:
        """Return the games dictionary.

        Returns
        -------
        Dict[str, List[Dict]]
            Games by date, with each game containing team names, abbreviations,
            scores, and boxscore URI.
        """
        return self._boxscores

    def _create_url(self, date: datetime) -> str:
        """Create the boxscores URL for a date.

        Parameters
        ----------
        date : datetime
            The date for the boxscores.

        Returns
        -------
        str
            The formatted URL.
        """
        return BOXSCORES_URL % (date.year, date.month, date.day)

    def _get_boxscore_uri(self, link: BeautifulSoup) -> Optional[str]:
        """Extract the boxscore URI from a link.

        Parameters
        ----------
        link : BeautifulSoup
            The link tag containing the boxscore URI.

        Returns
        -------
        str or None
            The boxscore URI.
        """
        if not link or not link.get('href'):
            return None
        href = link['href']
        match = re.search(r'/boxes/(.+)\.shtml', href)
        return match.group(1) if match else None

    def _get_score(self, td: BeautifulSoup) -> Optional[int]:
        """Extract a team's score from a table cell.

        Parameters
        ----------
        td : BeautifulSoup
            The table cell containing the score.

        Returns
        -------
        int or None
            The score.
        """
        text = td.get_text(strip=True)
        try:
            return int(text)
        except ValueError:
            return None

    def _get_team_details(self, game: BeautifulSoup) -> Tuple:
        """Extract team details from a game row.

        Parameters
        ----------
        game : BeautifulSoup
            The game row HTML.

        Returns
        -------
        Tuple
            (away_name, away_abbr, away_score, home_name, home_abbr, home_score)
        """
        links = game.find_all('td', class_=lambda x: not x)
        scores = game.find_all('td', class_='right')
        away_link = links[0].find('a') if links else None
        home_link = links[-1].find('a') if len(links) > 1 else None
        away_score = self._get_score(scores[0]) if len(scores) > 1 else None
        home_score = self._get_score(scores[1]) if len(scores) > 1 else None
        away_name = away_link.get_text(strip=True) if away_link else None
        away_abbr = _parse_team_abbreviation(away_link) if away_link else None
        home_name = home_link.get_text(strip=True) if home_link else None
        home_abbr = _parse_team_abbreviation(home_link) if home_link else None
        return away_name, away_abbr, away_score, home_name, home_abbr, home_score

    def _get_team_results(self, row: BeautifulSoup) -> Optional[Tuple[str, str]]:
        """Extract winning or losing team details.

        Parameters
        ----------
        row : BeautifulSoup
            The winner or loser row.

        Returns
        -------
        Tuple[str, str] or None
            (name, abbreviation) of the team.
        """
        link = row.find('td').find('a')
        if not link:
            return None
        name = link.get_text(strip=True)
        abbr = _parse_team_abbreviation(link)
        return name, abbr

    def _extract_game_info(self, games: List[BeautifulSoup]) -> List[Dict]:
        """Extract game information.

        Parameters
        ----------
        games : List[BeautifulSoup]
            List of game rows.

        Returns
        -------
        List[Dict]
            List of game details.
        """
        all_boxscores = []
        for game in games:
            details = self._get_team_details(game)
            away_name, away_abbr, away_score, home_name, home_abbr, home_score = details
            link = game.find('td', class_='right gamelink')
            boxscore_uri = self._get_boxscore_uri(link.find('a') if link else None)
            winner_row = game.find('tr', class_='winner')
            loser_row = game.find('tr', class_='loser')
            losers = game.find_all('tr', class_='loser')
            winner = self._get_team_results(winner_row) if winner_row else None
            loser = self._get_team_results(loser_row) if loser_row else None
            if (len(losers) != 2 and loser and not winner) or \
               (len(losers) != 2 and winner and not loser):
                continue
            winning_name, winning_abbr = winner if winner else (None, None)
            losing_name, losing_abbr = loser if loser else (None, None)
            game_info = {
                'boxscore': boxscore_uri,
                'away_name': away_name,
                'away_abbr': away_abbr,
                'away_score': away_score,
                'home_name': home_name,
                'home_abbr': home_abbr,
                'home_score': home_score,
                'winning_name': winning_name,
                'winning_abbr': winning_abbr,
                'losing_name': losing_name,
                'losing_abbr': losing_abbr
            }
            all_boxscores.append(game_info)
        return all_boxscores

    def _find_games(self, date: datetime, end_date: Optional[datetime]) -> None:
        """Find games for the specified date range.

        Parameters
        ----------
        date : datetime
            Start date.
        end_date : datetime, optional
            End date.
        """
        end_date = date if not end_date or date > end_date else end_date
        current_date = date
        while current_date <= end_date:
            url = self._create_url(current_date)
            soup = _fetch_html(url)
            if not soup:
                continue
            games = soup.find_all('table', class_='teams')
            boxscores = self._extract_game_info(games)
            timestamp = f'{current_date.month}-{current_date.day}-{current_date.year}'
            self._boxscores[timestamp] = boxscores
            current_date += timedelta(days=1)