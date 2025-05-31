import pandas as pd
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
from ..base import AbstractParser, int_property_decorator, float_property_decorator, sub_index_property_decorator, _parse_field, _fetch_html, _parse_player_id
from .constants import BOXSCORE_SCHEME, BOXSCORE_URL, BOXSCORES_URL, HOME, AWAY, BOXSCORE_ELEMENT_INDEX, BOXSCORE_ELEMENT_SUB_INDEX
from .player import AbstractPlayer

class BoxscorePlayer(AbstractPlayer):
    """Player stats for an NCAAF game.

    Parses individual player stats for a single game, such as passing yards, kickoff returns, or punting stats. Inherits from AbstractPlayer for shared stats like passing or rushing.

    Parameters
    ----------
    player_id : str
        Player's ID (e.g., 'david-blough-1').
    player_name : str
        Player's full name (e.g., 'David Blough').
    player_data : str
        HTML data string containing the player's stats.

    Attributes
    ----------
    player_id : str
        Player's unique ID.
    name : str
        Player's full name.
    """
    def __init__(self, player_id: str, player_name: str, player_data: str):
        super().__init__(player_id, player_name, player_data)
        self._index: int = 0
        self._pass_yards_per_attempt: Optional[List[str]] = None
        self._kickoff_returns: Optional[List[str]] = None
        self._kickoff_return_yards: Optional[List[str]] = None
        self._average_kickoff_return_yards: Optional[List[str]] = None
        self._punt_returns: Optional[List[str]] = None
        self._punt_return_yards: Optional[List[str]] = None
        self._average_punt_return_yards: Optional[List[str]] = None
        self._extra_points_attempted: Optional[List[str]] = None
        self._extra_point_percentage: Optional[List[str]] = None
        self._field_goals_attempted: Optional[List[str]] = None
        self._field_goal_percentage: Optional[List[str]] = None
        self._points_kicking: Optional[List[str]] = None
        self._punts: Optional[List[str]] = None
        self._punting_yards: Optional[List[str]] = None
        self._punting_yards_per_attempt: Optional[List[str]] = None

    @property
    def dataframe(self) -> pd.DataFrame:
        """Return a pandas DataFrame of player stats.

        Returns
        -------
        pd.DataFrame
            DataFrame indexed by player_id.
        """
        fields = {
            'completed_passes': self.completed_passes,
            'pass_attempts': self.pass_attempts,
            'passing_completion': self.passing_completion,
            'passing_yards': self.passing_yards,
            'pass_yards_per_attempt': self.pass_yards_per_attempt,
            'adjusted_yards_per_attempt': self.adjusted_yards_per_attempt,
            'passing_touchdowns': self.passing_touchdowns,
            'interceptions_thrown': self.interceptions_thrown,
            'quarterback_rating': self.quarterback_rating,
            'rush_attempts': self.rush_attempts,
            'rush_yards': self.rush_yards,
            'rush_yards_per_attempt': self.rush_yards_per_attempt,
            'rush_touchdowns': self.rush_touchdowns,
            'receptions': self.receptions,
            'receiving_yards': self.receiving_yards,
            'receiving_yards_per_reception': self.receiving_yards_per_reception,
            'receiving_touchdowns': self.receiving_touchdowns,
            'plays_from_scrimmage': self.plays_from_scrimmage,
            'yards_from_scrimmage': self.yards_from_scrimmage,
            'yards_from_scrimmage_per_play': self.yards_from_scrimmage_per_play,
            'rushing_and_receiving_touchdowns': self.rushing_and_receiving_touchdowns,
            'solo_tackles': self.solo_tackles,
            'assists_on_tackles': self.assists_on_tackles,
            'total_tackles': self.total_tackles,
            'tackles_for_loss': self.tackles_for_loss,
            'sacks': self.sacks,
            'interceptions': self.interceptions,
            'yards_returned_from_interceptions': self.yards_returned_from_interceptions,
            'yards_returned_per_interception': self.yards_returned_per_interception,
            'interceptions_returned_for_touchdown': self.interceptions_returned_for_touchdown,
            'passes_defended': self.passes_defended,
            'fumbles_recovered': self.fumbles_recovered,
            'yards_recovered_from_fumble': self.yards_recovered_from_fumble,
            'fumbles_recovered_for_touchdown': self.fumbles_recovered_for_touchdown,
            'fumbles_forced': self.fumbles_forced,
            'kickoff_returns': self.kickoff_returns,
            'kickoff_return_yards': self.kickoff_return_yards,
            'average_kickoff_return_yards': self.average_kickoff_return_yards,
            'kickoff_return_touchdowns': self.kickoff_return_touchdowns,
            'punt_returns': self.punt_returns,
            'punt_return_yards': self.punt_return_yards,
            'average_punt_return_yards': self.average_punt_return_yards,
            'punt_return_touchdowns': self.punt_return_touchdowns,
            'extra_points_made': self.extra_points_made,
            'extra_points_attempted': self.extra_points_attempted,
            'extra_point_percentage': self.extra_point_percentage,
            'field_goals_made': self.field_goals_made,
            'field_goals_attempted': self.field_goals_attempted,
            'field_goal_percentage': self.field_goal_percentage,
            'points_kicking': self.points_kicking,
            'punts': self.punts,
            'punting_yards': self.punting_yards,
            'punting_yards_per_punt': self.punting_yards_per_attempt
        }
        return pd.DataFrame([fields], index=[self._player_id])

    @float_property_decorator
    def pass_yards_per_attempt(self) -> Optional[float]:
        """Return the average yards per pass attempt."""
        return self._pass_yards_per_attempt

    @int_property_decorator
    def kickoff_returns(self) -> Optional[int]:
        """Return the number of kickoff returns."""
        return self._kickoff_returns

    @int_property_decorator
    def kickoff_return_yards(self) -> Optional[int]:
        """Return the total kickoff return yards."""
        return self._kickoff_return_yards

    @float_property_decorator
    def average_kickoff_return_yards(self) -> Optional[float]:
        """Return the average yards per kickoff return."""
        return self._average_kickoff_return_yards

    @int_property_decorator
    def punt_returns(self) -> Optional[int]:
        """Return the number of punt returns."""
        return self._punt_returns

    @int_property_decorator
    def punt_return_yards(self) -> Optional[int]:
        """Return the total punt return yards."""
        return self._punt_return_yards

    @float_property_decorator
    def average_punt_return_yards(self) -> Optional[float]:
        """Return the average yards per punt return."""
        return self._average_punt_return_yards

    @int_property_decorator
    def extra_points_attempted(self) -> Optional[int]:
        """Return the number of extra points attempted."""
        return self._extra_points_attempted

    @float_property_decorator
    def extra_point_percentage(self) -> Optional[float]:
        """Return the extra point success percentage (0-100)."""
        return self._extra_point_percentage

    @int_property_decorator
    def field_goals_attempted(self) -> Optional[int]:
        """Return the number of field goals attempted."""
        return self._field_goals_attempted

    @float_property_decorator
    def field_goal_percentage(self) -> Optional[float]:
        """Return the field goal success percentage (0-100)."""
        return self._field_goal_percentage

    @int_property_decorator
    def points_kicking(self) -> Optional[int]:
        """Return the total points from kicking."""
        return self._points_kicking

    @int_property_decorator
    def punts(self) -> Optional[int]:
        """Return the number of punts."""
        return self._punts

    @int_property_decorator
    def punting_yards(self) -> Optional[int]:
        """Return the total punting yards."""
        return self._punting_yards

    @float_property_decorator
    def punting_yards_per_attempt(self) -> Optional[float]:
        """Return the average yards per punt."""
        return self._punting_yards_per_attempt

class Boxscore:
    """Detailed statistics for an NCAAF game.

    Stores game-level stats like points, first downs, and turnovers, plus player stats for both teams.

    Parameters
    ----------
    uri : str
        The boxscore URI (e.g., '2018-01-08-georgia').

    Attributes
    ----------
    date : str
        The game date.
    winner : str
        Constant indicating home or away team win.
    away_players : List[BoxscorePlayer]
        List of away team player instances.
    home_players : List[BoxscorePlayer]
        List of home team player instances.
    """
    def __init__(self, uri: str):
        self._uri: str = uri
        self._date: Optional[str] = None
        self._time: Optional[str] = None
        self._stadium: Optional[str] = None
        self._away_name: Optional[BeautifulSoup] = None
        self._home_name: Optional[BeautifulSoup] = None
        self._winner: Optional[str] = None
        self._winning_name: Optional[str] = None
        self._winning_abbr: Optional[str] = None
        self._losing_name: Optional[str] = None
        self._losing_abbr: Optional[str] = None
        self._summary: Optional[Dict[str, List[int]]] = None
        self._away_points: Optional[str] = None
        self._away_first_downs: Optional[str] = None
        self._away_rush_attempts: Optional[str] = None
        self._away_rush_yards: Optional[str] = None
        self._away_rush_touchdowns: Optional[str] = None
        self._away_pass_completions: Optional[str] = None
        self._away_pass_attempts: Optional[str] = None
        self._away_pass_yards: Optional[str] = None
        self._away_pass_touchdowns: Optional[str] = None
        self._away_interceptions: Optional[str] = None
        self._away_total_yards: Optional[str] = None
        self._away_fumbles: Optional[str] = None
        self._away_fumbles_lost: Optional[str] = None
        self._away_turnovers: Optional[str] = None
        self._away_penalties: Optional[str] = None
        self._away_yards_from_penalties: Optional[str] = None
        self._home_points: Optional[str] = None
        self._home_first_downs: Optional[str] = None
        self._home_rush_attempts: Optional[str] = None
        self._home_rush_yards: Optional[str] = None
        self._home_rush_touchdowns: Optional[str] = None
        self._home_pass_completions: Optional[str] = None
        self._home_pass_attempts: Optional[str] = None
        self._home_pass_yards: Optional[str] = None
        self._home_pass_touchdowns: Optional[str] = None
        self._home_interceptions: Optional[str] = None
        self._home_total_yards: Optional[str] = None
        self._home_fumbles: Optional[str] = None
        self._home_fumbles_lost: Optional[str] = None
        self._home_turnovers: Optional[str] = None
        self._home_penalties: Optional[str] = None
        self._home_yards_from_penalties: Optional[str] = None
        self._away_players: List[BoxscorePlayer] = []
        self._home_players: List[BoxscorePlayer] = []

        self._parse_game_data(uri)

    def __str__(self) -> str:
        """Return the string representation of the boxscore."""
        away = self._away_name.get_text(strip=True) if self._away_name else 'Unknown'
        home = self._home_name.get_text(strip=True) if self._home_name else 'Unknown'
        return f'Boxscore for {away} at {home} ({self.date})'

    def __repr__(self) -> str:
        """Return the string representation of the boxscore."""
        return self.__str__()

    def _parse_game_date_and_location(self, soup: BeautifulSoup) -> None:
        """Parse the game's date, time, and stadium."""
        if not soup:
            return
        items = soup.select(BOXSCORE_SCHEME['time'])
        if not items:
            return
        game_info = items[0].get_text().split('\n')
        time, date, stadium = '', '', ''
        for line in game_info:
            line = line.strip()
            if re.search(r'(\d:\d\d|\d\d:\d\d)', line.lower()):
                time = line
            if any(day in line.lower() for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']):
                date = line
            if ' - ' in line:
                stadium = line
        self._time = time
        self._date = date
        self._stadium = stadium

    def _parse_name(self, field: str, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """Parse team name tags."""
        if not soup or field not in BOXSCORE_SCHEME:
            return None
        return soup.select_one(BOXSCORE_SCHEME[field])

    def _parse_summary(self, soup: BeautifulSoup) -> Optional[Dict[str, List[Optional[int]]]]:
        """Parse quarter-by-quarter scores."""
        if not soup:
            return None
        summary = {'away': [], 'home': []}
        game_summary = soup.select_one(BOXSCORE_SCHEME['summary'])
        if not game_summary:
            return summary
        for i, row in enumerate(game_summary.select('tbody tr')):
            team = 'away' if i == 0 else 'home'
            for td in row.select('td.center')[:-1]:  # Skip final score
                if td.find('div'):
                    continue
                text = td.get_text(strip=True)
                summary[team].append(int(text) if text.isdigit() else None)
        return summary

    def _find_boxscore_tables(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        """Find tables containing player stats."""
        tables = []
        valid_tables = ['passing', 'rushing_and_receiving', 'defense', 'returns', 'kicking_and_punting']
        if not soup:
            return tables
        for table in soup.find_all('table'):
            if table.get('id') in valid_tables:
                tables.append(table)
        return tables

    def _find_player_id(self, row: BeautifulSoup) -> Optional[str]:
        """Find a player's ID."""
        th = row.find('th')
        return th.get('data-append-csv') if th else None

    def _find_player_name(self, row: BeautifulSoup) -> Optional[str]:
        """Find a player's full name."""
        a = row.find('a')
        return a.get_text(strip=True) if a else None

    def _find_home_or_away(self, row: BeautifulSoup) -> Optional[str]:
        """Determine if a player is on the home or away team."""
        team_a = row.find_all('a')[-1] if row.find_all('a') else None
        if not team_a or not self._home_name:
            return None
        team_name = team_a.get_text(strip=True)
        home_name = self._home_name.get_text(strip=True)
        return HOME if team_name == home_name else AWAY

    def _extract_player_stats(self, table: BeautifulSoup, player_dict: Dict) -> Dict:
        """Combine player stats from a table."""
        if not table:
            return player_dict
        for row in table.select('tbody tr'):
            player_id = self._find_player_id(row)
            if not player_id:
                continue
            name = self._find_player_name(row)
            home_or_away = self._find_home_or_away(row)
            if not name or not home_or_away:
                continue
            if player_id in player_dict:
                player_dict[player_id]['data'] += str(row).strip()
            else:
                player_dict[player_id] = {
                    'name': name,
                    'data': str(row).strip(),
                    'team': home_or_away
                }
        return player_dict

    def _instantiate_players(self, player_dict: Dict) -> Tuple[List[BoxscorePlayer], List[BoxscorePlayer]]:
        """Create player instances."""
        home_players, away_players = [], []
        for player_id, details in player_dict.items():
            player = BoxscorePlayer(player_id, details['name'], details['data'])
            if details['team'] == HOME:
                home_players.append(player)
            else:
                away_players.append(player)
        return away_players, home_players

    def _find_players(self, soup: BeautifulSoup) -> Tuple[List[BoxscorePlayer], List[BoxscorePlayer]]:
        """Find all players in the boxscore."""
        player_dict = {}
        for table in self._find_boxscore_tables(soup):
            player_dict = self._extract_player_stats(table, player_dict)
        return self._instantiate_players(player_dict)

    def _parse_game_data(self, uri: str) -> None:
        """Parse all game data."""
        soup = _fetch_html(BOXSCORE_URL % uri)
        if not soup:
            return
        for field in self.__dict__:
            short_field = field[1:] if field.startswith('_') else field
            if short_field in ['winner', 'winning_name', 'winning_abbr', 'losing_name', 'losing_abbr', 'uri', 'date', 'time', 'stadium']:
                continue
            if short_field in ['away_name', 'home_name']:
                self.__dict__[field] = self._parse_name(short_field, soup)
                continue
            if short_field == 'summary':
                self._summary = self._parse_summary(soup)
                continue
            index = BOXSCORE_ELEMENT_INDEX.get(short_field, 0)
            self.__dict__[field] = _parse_field(BOXSCORE_SCHEME, soup, short_field, index)
        self._parse_game_date_and_location(soup)
        self._away_players, self._home_players = self._find_players(soup)

    @property
    def dataframe(self) -> Optional[pd.DataFrame]:
        """Return a pandas DataFrame of game stats.

        Returns
        -------
        pd.DataFrame or None
            DataFrame indexed by uri, or None if no points scored.
        """
        if not self._away_points or not self._home_points:
            return None
        fields = {
            'away_first_downs': self.away_first_downs,
            'away_fumbles': self.away_fumbles,
            'away_fumbles_lost': self.away_fumbles_lost,
            'away_interceptions': self.away_interceptions,
            'away_pass_attempts': self.away_pass_attempts,
            'away_pass_completions': self.away_pass_completions,
            'away_pass_touchdowns': self.away_pass_touchdowns,
            'away_pass_yards': self.away_pass_yards,
            'away_penalties': self.away_penalties,
            'away_points': self.away_points,
            'away_rush_attempts': self.away_rush_attempts,
            'away_rush_touchdowns': self.away_rush_touchdowns,
            'away_rush_yards': self.away_rush_yards,
            'away_total_yards': self.away_total_yards,
            'away_turnovers': self.away_turnovers,
            'away_yards_from_penalties': self.away_yards_from_penalties,
            'date': self.date,
            'home_first_downs': self.home_first_downs,
            'home_fumbles': self.home_fumbles,
            'home_fumbles_lost': self.home_fumbles_lost,
            'home_interceptions': self.home_interceptions,
            'home_pass_attempts': self.home_pass_attempts,
            'home_pass_completions': self.home_pass_completions,
            'home_pass_touchdowns': self.home_pass_touchdowns,
            'home_pass_yards': self.home_pass_yards,
            'home_penalties': self.home_penalties,
            'home_points': self.home_points,
            'home_rush_attempts': self.home_rush_attempts,
            'home_rush_touchdowns': self.home_rush_touchdowns,
            'home_rush_yards': self.home_rush_yards,
            'home_total_yards': self.home_total_yards,
            'home_turnovers': self.home_turnovers,
            'home_yards_from_penalties': self.home_yards_from_penalties,
            'losing_abbr': self.losing_abbr,
            'losing_name': self.losing_name,
            'stadium': self.stadium,
            'time': self.time,
            'winner': self.winner,
            'winning_abbr': self.winning_abbr,
            'winning_name': self.winning_name
        }
        return pd.DataFrame([fields], index=[self._uri])

    @property
    def away_players(self) -> List[BoxscorePlayer]:
        """Return the list of away team players."""
        return self._away_players

    @property
    def home_players(self) -> List[BoxscorePlayer]:
        """Return the list of home team players."""
        return self._home_players

    @property
    def date(self) -> Optional[str]:
        """Return the game date."""
        return self._date

    @property
    def time(self) -> Optional[str]:
        """Return the game start time."""
        return self._time.replace('Start Time: ', '') if self._time else None

    @property
    def stadium(self) -> Optional[str]:
        """Return the stadium name."""
        return self._stadium.replace('Venue: ', '') if self._stadium else None

    @property
    def summary(self) -> Optional[Dict[str, List[Optional[int]]]]:
        """Return quarter-by-quarter scores."""
        return self._summary

    @property
    def winner(self) -> Optional[str]:
        """Return a constant indicating the winning team."""
        if self.home_points is not None and self.away_points is not None:
            return HOME if self.home_points > self.away_points else AWAY
        return None

    @property
    def winning_name(self) -> Optional[str]:
        """Return the winning team's name."""
        if self.winner == HOME and self._home_name:
            return self._home_name.get_text(strip=True)
        if self.winner == AWAY and self._away_name:
            return self._away_name.get_text(strip=True)
        return None

    @property
    def winning_abbr(self) -> Optional[str]:
        """Return the winning team's abbreviation."""
        if not self.winner:
            return None
        name = self._home_name if self.winner == HOME else self._away_name
        if not name:
            return None
        href = name.get('href', '')
        if 'cfb/schools' not in href:
            return name.get_text(strip=True)
        match = re.search(r'/schools/([^/]+)/', href)
        return match.group(1).upper() if match else None

    @property
    def losing_name(self) -> Optional[str]:
        """Return the losing team's name."""
        if self.winner == HOME and self._away_name:
            return self._away_name.get_text(strip=True)
        if self.winner == AWAY and self._home_name:
            return self._home_name.get_text(strip=True)
        return None

    @property
    def losing_abbr(self) -> Optional[str]:
        """Return the losing team's abbreviation."""
        if not self.winner:
            return None
        name = self._away_name if self.winner == HOME else self._home_name
        if not name:
            return None
        href = name.get('href', '')
        if 'cfb/schools' not in href:
            return name.get_text(strip=True)
        match = re.search(r'/schools/([^/]+)/', href)
        return match.group(1).upper() if match else None

    @int_property_decorator
    def away_points(self) -> Optional[int]:
        """Return the away team's points."""
        return self._away_points

    @int_property_decorator
    def away_first_downs(self) -> Optional[int]:
        """Return the away team's first downs."""
        return self._away_first_downs

    @sub_index_property_decorator(BOXSCORE_ELEMENT_SUB_INDEX)
    def away_rush_attempts(self) -> Optional[int]:
        """Return the away team's rush attempts."""
        return self._away_rush_attempts

    @sub_index_property_decorator(BOXSCORE_ELEMENT_SUB_INDEX)
    def away_rush_yards(self) -> Optional[int]:
        """Return the away team's rush yards."""
        return self._away_rush_yards

    @sub_index_property_decorator(BOXSCORE_ELEMENT_SUB_INDEX)
    def away_rush_touchdowns(self) -> Optional[int]:
        """Return the away team's rush touchdowns."""
        return self._away_rush_touchdowns

    @sub_index_property_decorator(BOXSCORE_ELEMENT_SUB_INDEX)
    def away_pass_completions(self) -> Optional[int]:
        """Return the away team's pass completions."""
        return self._away_pass_completions

    @sub_index_property_decorator(BOXSCORE_ELEMENT_SUB_INDEX)
    def away_pass_attempts(self) -> Optional[int]:
        """Return the away team's pass attempts."""
        return self._away_pass_attempts

    @sub_index_property_decorator(BOXSCORE_ELEMENT_SUB_INDEX)
    def away_pass_yards(self) -> Optional[int]:
        """Return the away team's pass yards."""
        return self._away_pass_yards

    @sub_index_property_decorator(BOXSCORE_ELEMENT_SUB_INDEX)
    def away_pass_touchdowns(self) -> Optional[int]:
        """Return the away team's pass touchdowns."""
        return self._away_pass_touchdowns

    @sub_index_property_decorator(BOXSCORE_ELEMENT_SUB_INDEX)
    def away_interceptions(self) -> Optional[int]:
        """Return the away team's interceptions thrown."""
        return self._away_interceptions

    @int_property_decorator
    def away_total_yards(self) -> Optional[int]:
        """Return the away team's total yards."""
        return self._away_total_yards

    @sub_index_property_decorator(BOXSCORE_ELEMENT_SUB_INDEX)
    def away_fumbles(self) -> Optional[int]:
        """Return the away team's fumbles."""
        return self._away_fumbles

    @sub_index_property_decorator(BOXSCORE_ELEMENT_SUB_INDEX)
    def away_fumbles_lost(self) -> Optional[int]:
        """Return the away team's fumbles lost."""
        return self._away_fumbles_lost

    @int_property_decorator
    def away_turnovers(self) -> Optional[int]:
        """Return the away team's turnovers."""
        return self._away_turnovers

    @sub_index_property_decorator(BOXSCORE_ELEMENT_SUB_INDEX)
    def away_penalties(self) -> Optional[int]:
        """Return the away team's penalties."""
        return self._away_penalties

    @sub_index_property_decorator(BOXSCORE_ELEMENT_SUB_INDEX)
    def away_yards_from_penalties(self) -> Optional[int]:
        """Return the away team's penalty yards."""
        return self._away_yards_from_penalties

    @int_property_decorator
    def home_points(self) -> Optional[int]:
        """Return the home team's points."""
        return self._home_points

    @int_property_decorator
    def home_first_downs(self) -> Optional[int]:
        """Return the home team's first downs."""
        return self._home_first_downs

    @sub_index_property_decorator(BOXSCORE_ELEMENT_SUB_INDEX)
    def home_rush_attempts(self) -> Optional[int]:
        """Return the home team's rush attempts."""
        return self._home_rush_attempts

    @sub_index_property_decorator(BOXSCORE_ELEMENT_SUB_INDEX)
    def home_rush_yards(self) -> Optional[int]:
        """Return the home team's rush yards."""
        return self._home_rush_yards

    @sub_index_property_decorator(BOXSCORE_ELEMENT_SUB_INDEX)
    def home_rush_touchdowns(self) -> Optional[int]:
        """Return the home team's rush touchdowns."""
        return self._home_rush_touchdowns

    @sub_index_property_decorator(BOXSCORE_ELEMENT_SUB_INDEX)
    def home_pass_completions(self) -> Optional[int]:
        """Return the home team's pass completions."""
        return self._home_pass_completions

    @sub_index_property_decorator(BOXSCORE_ELEMENT_SUB_INDEX)
    def home_pass_attempts(self) -> Optional[int]:
        """Return the home team's pass attempts."""
        return self._home_pass_attempts

    @sub_index_property_decorator(BOXSCORE_ELEMENT_SUB_INDEX)
    def home_pass_yards(self) -> Optional[int]:
        """Return the home team's pass yards."""
        return self._home_pass_yards

    @sub_index_property_decorator(BOXSCORE_ELEMENT_SUB_INDEX)
    def home_pass_touchdowns(self) -> Optional[int]:
        """Return the home team's pass touchdowns."""
        return self._home_pass_touchdowns

    @sub_index_property_decorator(BOXSCORE_ELEMENT_SUB_INDEX)
    def home_interceptions(self) -> Optional[int]:
        """Return the home team's interceptions thrown."""
        return self._home_interceptions

    @int_property_decorator
    def home_total_yards(self) -> Optional[int]:
        """Return the home team's total yards."""
        return self._home_total_yards

    @sub_index_property_decorator(BOXSCORE_ELEMENT_SUB_INDEX)
    def home_fumbles(self) -> Optional[int]:
        """Return the home team's fumbles."""
        return self._home_fumbles

    @sub_index_property_decorator(BOXSCORE_ELEMENT_SUB_INDEX)
    def home_fumbles_lost(self) -> Optional[int]:
        """Return the home team's fumbles lost."""
        return self._home_fumbles_lost

    @int_property_decorator
    def home_turnovers(self) -> Optional[int]:
        """Return the home team's turnovers."""
        return self._home_turnovers

    @sub_index_property_decorator(BOXSCORE_ELEMENT_SUB_INDEX)
    def home_penalties(self) -> Optional[int]:
        """Return the home team's penalties."""
        return self._home_penalties

    @sub_index_property_decorator(BOXSCORE_ELEMENT_SUB_INDEX)
    def home_yards_from_penalties(self) -> Optional[int]:
        """Return the home team's penalty yards."""
        return self._home_yards_from_penalties

class Boxscores:
    """Search for NCAAF games on a given day or date range.

    Retrieves games played on a specified date or range, including team names, scores, and boxscore URIs.

    Parameters
    ----------
    date : datetime
        The start date to search for games.
    end_date : datetime, optional
        The end date for the search range. Defaults to the start date.

    Attributes
    ----------
    games : Dict[str, List[Dict]]
        Dictionary of games by date, with each game containing team and score details.
    """
    def __init__(self, date: datetime, end_date: Optional[datetime] = None):
        self._boxscores: Dict[str, List[Dict]] = {}
        self._find_games(date, end_date)

    def __str__(self) -> str:
        """Return the string representation of the boxscores."""
        return f"NCAAF games for {', '.join(self._boxscores.keys())}"

    def __repr__(self) -> str:
        """Return the string representation of the boxscores."""
        return self.__str__()

    @property
    def games(self) -> Dict[str, List[Dict]]:
        """Return a dictionary of games by date."""
        return self._boxscores

    def _create_url(self, date: datetime) -> str:
        """Build the boxscores URL for a date."""
        return BOXSCORES_URL % (date.month, date.day, date.year)

    def _parse_abbreviation(self, tag: BeautifulSoup) -> Optional[str]:
        """Parse a team's abbreviation."""
        if not tag or 'cfb/schools' not in tag.get('href', ''):
            return None
        match = re.search(r'/schools/([^/]+)/', tag['href'])
        return match.group(1).upper() if match else None

    def _get_name(self, tag: BeautifulSoup) -> Tuple[Optional[str], Optional[str], bool]:
        """Get a team's name, abbreviation, and Division-I status."""
        if not tag:
            return None, None, True
        team_name = tag.get_text(strip=True)
        abbr = self._parse_abbreviation(tag)
        non_di = not bool(abbr)
        return team_name, abbr or team_name, non_di

    def _get_score(self, score_tag: str) -> Optional[int]:
        """Parse a team's score."""
        match = re.search(r'(\d+)', score_tag)
        return int(match.group(1)) if match else None

    def _get_rank(self, row: BeautifulSoup) -> Optional[int]:
        """Parse a team's rank."""
        span = row.find('span', class_='pollrank')
        if not span:
            return None
        match = re.search(r'\((\d+)\)', span.get_text(strip=True))
        return int(match.group(1)) if match else None

    def _get_team_names(self, game: BeautifulSoup) -> Tuple:
        """Parse team names, scores, and ranks."""
        rows = game.find_all('tr')
        away_row = rows[1] if len(rows) == 3 else rows[0]
        home_row = rows[-1]
        away_name, away_abbr, away_non_di = self._get_name(away_row.find('a'))
        home_name, home_abbr, home_non_di = self._get_name(home_row.find('a'))
        scores = game.find_all('td', class_='right')
        away_score = self._get_score(scores[0].get_text(strip=True)) if len(scores) > 0 else None
        home_score = self._get_score(scores[1].get_text(strip=True)) if len(scores) > 1 else None
        away_rank = self._get_rank(away_row)
        home_rank = self._get_rank(home_row)
        non_di = away_non_di or home_non_di
        top_25 = bool(away_rank or home_rank)
        return (away_name, away_abbr, away_score, away_rank, home_name, home_abbr, home_score, home_rank, non_di, top_25)

    def _get_team_results(self, away_name: str, away_abbr: str, away_score: Optional[int], home_name: str, home_abbr: str, home_score: Optional[int]) -> Tuple:
        """Determine the winner and loser."""
        if away_score is None or home_score is None:
            return None, None
        if away_score > home_score:
            return (away_name, away_abbr), (home_name, home_abbr)
        return (home_name, home_abbr), (away_name, away_abbr)

    def _extract_game_info(self, games: List[BeautifulSoup]) -> List[Dict]:
        """Parse game information from boxscores."""
        all_boxscores = []
        for game in games:
            names = self._get_team_names(game)
            away_name, away_abbr, away_score, away_rank, home_name, home_abbr, home_score, home_rank, non_di, top_25 = names
            link = game.find('td', class_='right gamelink')
            boxscore_uri = ''
            if link and link.find('a'):
                href = link.find('a').get('href', '')
                match = re.search(r'/boxscores/([^.]+)\.html', href)
                boxscore_uri = match.group(1) if match else ''
            winner, loser = self._get_team_results(away_name, away_abbr, away_score, home_name, home_abbr, home_score)
            game_info = {
                'boxscore': boxscore_uri,
                'away_name': away_name,
                'away_abbr': away_abbr,
                'away_score': away_score,
                'away_rank': away_rank,
                'home_name': home_name,
                'home_abbr': home_abbr,
                'home_score': home_score,
                'home_rank': home_rank,
                'non_di': non_di,
                'top_25': top_25,
                'winning_name': winner[0] if winner else None,
                'winning_abbr': winner[1] if winner else None,
                'losing_name': loser[0] if loser else None,
                'losing_abbr': loser[1] if loser else None
            }
            all_boxscores.append(game_info)
        return all_boxscores

    def _find_games(self, date: datetime, end_date: Optional[datetime]) -> None:
        """Retrieve games for a date range."""
        end_date = date if not end_date or date > end_date else end_date
        current_date = date
        while current_date <= end_date:
            url = self._create_url(current_date)
            soup = _fetch_html(url)
            if soup:
                games = soup.find_all('table', class_='teams')
                boxscores = self._extract_game_info(games)
                timestamp = f'{current_date.month}-{current_date.day}-{current_date.year}'
                self._boxscores[timestamp] = boxscores
            current_date += timedelta(days=1)