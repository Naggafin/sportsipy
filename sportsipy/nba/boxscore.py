import pandas as pd
import re
from datetime import timedelta, datetime
from bs4 import BeautifulSoup
from urllib.error import HTTPError
import requests
from ..base import (int_property_decorator, float_property_decorator, indexed_int_property_decorator,
                    _parse_field, _cleanup, _remove_html_comment_tags, _parse_abbreviation,
                    _parse_multi_line_field, _parse_team_name, _extract_table_entities,
                    AbstractGame, AbstractParser)
from ..constants import AWAY, HOME
from .constants import (BOXSCORE_ELEMENT_INDEX, BOXSCORE_SCHEME, BOXSCORE_URL, BOXSCORES_URL)
from .player import AbstractPlayer

class BoxscorePlayer(AbstractPlayer, AbstractParser):
    """Player statistics for an individual NBA game.

    Parses and stores player statistics for a specific game, given a player ID,
    name, and HTML data from the boxscore page. Inherits from `AbstractPlayer`
    for shared player attributes and `AbstractParser` for HTML parsing utilities.

    Parameters
    ----------
    player_id : str
        The player's ID (e.g., 'hardeja01' for James Harden).
    player_name : str
        The player's full name (e.g., 'James Harden').
    player_data : str
        The HTML data containing the player's stats from the boxscore page.
    """
    def __init__(self, player_id, player_name, player_data):
        AbstractParser.__init__(self, player_data)
        AbstractPlayer.__init__(self, player_id, player_name, player_data)
        self._index = 0
        self._player_id = player_id
        self._defensive_rating = None
        self._offensive_rating = None

    @property
    def dataframe(self):
        """Return a pandas DataFrame of the player's game stats.

        Returns
        -------
        pandas.DataFrame
            A DataFrame of all player stats, indexed by player ID.
        """
        fields_to_include = {
            'assist_percentage': self.assist_percentage,
            'assists': self.assists,
            'block_percentage': self.block_percentage,
            'blocks': self.blocks,
            'box_plus_minus': self.box_plus_minus,
            'defensive_rating': self.defensive_rating,
            'defensive_rebound_percentage': self.defensive_rebound_percentage,
            'defensive_rebounds': self.defensive_rebounds,
            'effective_field_goal_percentage': self.effective_field_goal_percentage,
            'field_goal_attempts': self.field_goal_attempts,
            'field_goal_percentage': self.field_goal_percentage,
            'field_goals': self.field_goals,
            'free_throw_attempt_rate': self.free_throw_attempt_rate,
            'free_throw_attempts': self.free_throw_attempts,
            'free_throw_percentage': self.free_throw_percentage,
            'free_throws': self.free_throws,
            'minutes_played': self.minutes_played,
            'offensive_rating': self.offensive_rating,
            'offensive_rebound_percentage': self.offensive_rebound_percentage,
            'offensive_rebounds': self.offensive_rebounds,
            'personal_fouls': self.personal_fouls,
            'points': self.points,
            'steal_percentage': self.steal_percentage,
            'steals': self.steals,
            'three_point_attempt_rate': self.three_point_attempt_rate,
            'three_point_attempts': self.three_point_attempts,
            'three_point_percentage': self.three_point_percentage,
            'three_pointers': self.three_pointers,
            'total_rebound_percentage': self.total_rebound_percentage,
            'total_rebounds': self.total_rebounds,
            'true_shooting_percentage': self.true_shooting_percentage,
            'turnover_percentage': self.turnover_percentage,
            'turnovers': self.turnovers,
            'two_point_attempts': self.two_point_attempts,
            'two_point_percentage': self.two_point_percentage,
            'two_pointers': self.two_pointers,
            'usage_percentage': self.usage_percentage
        }
        return pd.DataFrame([fields_to_include], index=[self._player_id])

    @property
    def minutes_played(self):
        """Return the player's minutes played.

        Returns
        -------
        float or None
            The total minutes played, calculated as minutes plus seconds/60.
        """
        if self._minutes_played and self._minutes_played[self._index]:
            try:
                minutes, seconds = self._minutes_played[self._index].split(':')
                return float(minutes) + float(seconds) / 60
            except ValueError:
                return None
        return None

    @property
    def two_pointers(self):
        """Return the number of two-point field goals made.

        Returns
        -------
        int or None
            The number of two-point field goals, calculated as field goals minus three-pointers.
        """
        if self.field_goals and self.three_pointers:
            return int(self.field_goals - self.three_pointers)
        return int(self.field_goals) if self.field_goals else None

    @property
    def two_point_attempts(self):
        """Return the number of two-point field goal attempts.

        Returns
        -------
        int or None
            The number of two-point attempts, calculated as field goal attempts minus three-point attempts.
        """
        if self.field_goal_attempts and self.three_point_attempts:
            return int(self.field_goal_attempts - self.three_point_attempts)
        return int(self.field_goal_attempts) if self.field_goal_attempts else None

    @property
    def two_point_percentage(self):
        """Return the two-point field goal percentage.

        Returns
        -------
        float or None
            The two-point shooting percentage (0-1), rounded to three decimals.
            Returns 0.0 if attempts exist but no shots were made.
        """
        if self.two_pointers and self.two_point_attempts:
            return round(float(self.two_pointers) / float(self.two_point_attempts), 3)
        return 0.0 if self.two_point_attempts else None

    @indexed_int_property_decorator
    def offensive_rating(self):
        """Return the player's offensive rating.

        Returns
        -------
        int or None
            The points produced per 100 possessions.
        """
        return self._offensive_rating

    @indexed_int_property_decorator
    def defensive_rating(self):
        """Return the player's defensive rating.

        Returns
        -------
        int or None
            The points allowed per 100 possessions.
        """
        return self._defensive_rating

class Boxscore(AbstractGame):
    """Detailed statistics for an NBA game.

    Stores comprehensive game metrics, including date, location, team and player
    stats, and advanced metrics like pace and shooting percentages.

    Parameters
    ----------
    uri : str
        The boxscore URI (e.g., '201710310LAL').
    """
    def __init__(self, uri):
        super().__init__(boxscore_uri=uri)
        self._uri = uri
        self._home_name = None
        self._away_name = None
        self._winner = None
        self._winning_name = None
        self._winning_abbr = None
        self._losing_name = None
        self._losing_abbr = None
        self._pace = None
        self._summary = None
        self._away_record = None
        self._away_minutes_played = None
        self._away_field_goals = None
        self._away_field_goal_attempts = None
        self._away_field_goal_percentage = None
        self._away_three_point_field_goals = None
        self._away_three_point_field_goal_attempts = None
        self._away_three_point_field_goal_percentage = None
        self._away_free_throws = None
        self._away_free_throw_attempts = None
        self._away_free_throw_percentage = None
        self._away_offensive_rebounds = None
        self._away_defensive_rebounds = None
        self._away_total_rebounds = None
        self._away_assists = None
        self._away_steals = None
        self._away_blocks = None
        self._away_turnovers = None
        self._away_personal_fouls = None
        self._away_points = None
        self._away_true_shooting_percentage = None
        self._away_effective_field_goal_percentage = None
        self._away_three_point_attempt_rate = None
        self._away_free_throw_attempt_rate = None
        self._away_offensive_rebound_percentage = None
        self._away_defensive_rebound_percentage = None
        self._away_total_rebound_percentage = None
        self._away_assist_percentage = None
        self._away_steal_percentage = None
        self._away_block_percentage = None
        self._away_turnover_percentage = None
        self._away_offensive_rating = None
        self._away_defensive_rating = None
        self._home_record = None
        self._home_minutes_played = None
        self._home_field_goals = None
        self._home_field_goal_attempts = None
        self._home_field_goal_percentage = None
        self._home_three_point_field_goals = None
        self._home_three_point_field_goal_attempts = None
        self._home_three_point_field_goal_percentage = None
        self._home_free_throws = None
        self._home_free_throw_attempts = None
        self._home_free_throw_percentage = None
        self._home_offensive_rebounds = None
        self._home_defensive_rebounds = None
        self._home_total_rebounds = None
        self._home_assists = None
        self._home_steals = None
        self._home_blocks = None
        self._home_turnovers = None
        self._home_personal_fouls = None
        self._home_points = None
        self._home_true_shooting_percentage = None
        self._home_effective_field_goal_percentage = None
        self._home_three_point_attempt_rate = None
        self._home_free_throw_attempt_rate = None
        self._home_offensive_rebound_percentage = None
        self._home_defensive_rebound_percentage = None
        self._home_total_rebound_percentage = None
        self._home_assist_percentage = None
        self._home_steal_percentage = None
        self._home_block_percentage = None
        self._home_turnover_percentage = None
        self._home_offensive_rating = None
        self._home_defensive_rating = None
        self._away_players = []
        self._home_players = []

        self._parse_game_data(uri)

    def __str__(self):
        """Return the string representation of the boxscore.

        Returns
        -------
        str
            A string describing the game (e.g., 'Boxscore for Lakers at Trail Blazers (October 31, 2017)').
        """
        if not self._away_name or not self._home_name:
            return f'Boxscore for {self._uri}'
        return f'Boxscore for {self._away_name.text} at {self._home_name.text} ({self.date})'

    def _retrieve_html_page(self, uri):
        """Retrieve the boxscore HTML page.

        Parameters
        ----------
        uri : str
            The boxscore URI (e.g., '201710310LAL').

        Returns
        -------
        BeautifulSoup or None
            The parsed HTML page with comments removed.
        """
        url = BOXSCORE_URL % uri
        try:
            response = requests.get(url)
            response.raise_for_status()
            return BeautifulSoup(_remove_html_comment_tags(response.text), 'html.parser')
        except (HTTPError, requests.RequestException):
            return None

    def _parse_summary(self, boxscore):
        """Parse quarterly scores.

        Returns
        -------
        dict
            A dictionary with 'away' and 'home' keys, each mapping to a list of quarterly scores.
        """
        summary = {'away': [], 'home': []}
        game_summary = boxscore.select_one(BOXSCORE_SCHEME['summary'])
        if not game_summary:
            return summary
        team = ['away', 'home']
        for ind, row in enumerate(game_summary.select('tr')):
            if ind < 2:  # Skip headers
                continue
            cells = row.select('td.center, td.center ')[:-1]  # Exclude final score
            for quarter in cells:
                try:
                    summary[team[ind % 2]].append(int(quarter.text))
                except ValueError:
                    summary[team[ind % 2]].append(None)
        return summary

    def _find_boxscore_tables(self, boxscore):
        """Find boxscore tables.

        Returns
        -------
        list
            A list of BeautifulSoup objects for tables with IDs starting with 'box_' or 'box-'.
        """
        return [table for table in boxscore.select('table')
                if table.get('id', '').startswith(('box_', 'box-'))]

    def _instantiate_players(self, player_dict):
        """Create player instances.

        Parameters
        ----------
        player_dict : dict
            A dictionary of player IDs to their name, data, and team.

        Returns
        -------
        tuple
            Lists of away and home BoxscorePlayer instances.
        """
        home_players = []
        away_players = []
        for player_id, details in player_dict.items():
            player = BoxscorePlayer(player_id, details['name'], details['data'])
            if details['team'] == HOME:
                home_players.append(player)
            else:
                away_players.append(player)
        return away_players, home_players

    def _find_players(self, boxscore):
        """Extract player data.

        Parameters
        ----------
        boxscore : BeautifulSoup object
            The boxscore HTML.

        Returns
        -------
        tuple
            Lists of away and home BoxscorePlayer instances.
        """
        player_dict = {}
        tables = self._find_boxscore_tables(boxscore)
        for i, table in enumerate(tables):
            home_or_away = AWAY if i < 2 else HOME
            player_dict = _extract_table_entities(table, player_dict, 'data-append-csv', 'th a', home_or_away)
        return self._instantiate_players(player_dict)

    def _parse_game_data(self, uri):
        """Parse all game attributes.

        Parameters
        ----------
        uri : str
            The boxscore URI.
        """
        boxscore = self._retrieve_html_page(uri)
        if not boxscore:
            return

        for field in self.__dict__:
            if field in ('_uri', '_winner', '_away_players', '_home_players', '_boxscore'):
                continue
            short_field = field[1:]
            if short_field == 'date':
                value = _parse_multi_line_field(boxscore, BOXSCORE_SCHEME['date'], BOXSCORE_ELEMENT_INDEX['date'])
            elif short_field == 'location':
                value = _parse_multi_line_field(boxscore, BOXSCORE_SCHEME['location'], BOXSCORE_ELEMENT_INDEX['location'])
            elif short_field in ('away_name', 'home_name'):
                value = _parse_team_name(boxscore, BOXSCORE_SCHEME[short_field], BOXSCORE_ELEMENT_INDEX[short_field])
            elif short_field == 'summary':
                value = self._parse_summary(boxscore)
            else:
                index = BOXSCORE_ELEMENT_INDEX.get(short_field, 0)
                strip = short_field == 'home_record'
                secondary_index = 1 if short_field in BOXSCORE_ELEMENT_INDEX else None
                value = _parse_field(BOXSCORE_SCHEME, boxscore, short_field, index, strip, secondary_index)
            setattr(self, field, value)
        self._away_players, self._home_players = self._find_players(boxscore)

    @property
    def dataframe(self):
        """Return a pandas DataFrame of boxscore stats.

        Returns
        -------
        pandas.DataFrame or None
            A DataFrame of all game stats, indexed by URI.
        """
        if self._away_points is None and self._home_points is None:
            return None
        fields_to_include = {
            'away_assist_percentage': self.away_assist_percentage,
            'away_assists': self.away_assists,
            'away_block_percentage': self.away_block_percentage,
            'away_blocks': self.away_blocks,
            'away_defensive_rating': self.away_defensive_rating,
            'away_defensive_rebound_percentage': self.away_defensive_rebound_percentage,
            'away_defensive_rebounds': self.away_defensive_rebounds,
            'away_effective_field_goal_percentage': self.away_effective_field_goal_percentage,
            'away_field_goal_attempts': self.away_field_goal_attempts,
            'away_field_goal_percentage': self.away_field_goal_percentage,
            'away_field_goals': self.away_field_goals,
            'away_free_throw_attempt_rate': self.away_free_throw_attempt_rate,
            'away_free_throw_attempts': self.away_free_throw_attempts,
            'away_free_throw_percentage': self.away_free_throw_percentage,
            'away_free_throws': self.away_free_throws,
            'away_losses': self.away_losses,
            'away_minutes_played': self.away_minutes_played,
            'away_offensive_rating': self.away_offensive_rating,
            'away_offensive_rebound_percentage': self.away_offensive_rebound_percentage,
            'away_offensive_rebounds': self.away_offensive_rebounds,
            'away_personal_fouls': self.away_personal_fouls,
            'away_points': self.away_points,
            'away_steal_percentage': self.away_steal_percentage,
            'away_steals': self.away_steals,
            'away_three_point_attempt_rate': self.away_three_point_attempt_rate,
            'away_three_point_field_goal_attempts': self.away_three_point_field_goal_attempts,
            'away_three_point_field_goal_percentage': self.away_three_point_field_goal_percentage,
            'away_three_point_field_goals': self.away_three_point_field_goals,
            'away_total_rebound_percentage': self.away_total_rebound_percentage,
            'away_total_rebounds': self.away_total_rebounds,
            'away_true_shooting_percentage': self.away_true_shooting_percentage,
            'away_turnover_percentage': self.away_turnover_percentage,
            'away_turnovers': self.away_turnovers,
            'away_two_point_field_goal_attempts': self.away_two_point_field_goal_attempts,
            'away_two_point_field_goal_percentage': self.away_two_point_field_goal_percentage,
            'away_two_point_field_goals': self.away_two_point_field_goals,
            'away_wins': self.away_wins,
            'date': self.date,
            'home_assist_percentage': self.home_assist_percentage,
            'home_assists': self.home_assists,
            'home_block_percentage': self.home_block_percentage,
            'home_blocks': self.home_blocks,
            'home_defensive_rating': self.home_defensive_rating,
            'home_defensive_rebound_percentage': self.home_defensive_rebound_percentage,
            'home_defensive_rebounds': self.home_defensive_rebounds,
            'home_effective_field_goal_percentage': self.home_effective_field_goal_percentage,
            'home_field_goal_attempts': self.home_field_goal_attempts,
            'home_field_goal_percentage': self.home_field_goal_percentage,
            'home_field_goals': self.home_field_goals,
            'home_free_throw_attempt_rate': self.home_free_throw_attempt_rate,
            'home_free_throw_attempts': self.home_free_throw_attempts,
            'home_free_throw_percentage': self.home_free_throw_percentage,
            'home_free_throws': self.home_free_throws,
            'home_losses': self.home_losses,
            'home_minutes_played': self.home_minutes_played,
            'home_offensive_rating': self.home_offensive_rating,
            'home_offensive_rebound_percentage': self.home_offensive_rebound_percentage,
            'home_offensive_rebounds': self.home_offensive_rebounds,
            'home_personal_fouls': self.home_personal_fouls,
            'home_points': self.home_points,
            'home_steal_percentage': self.home_steal_percentage,
            'home_steals': self.home_steals,
            'home_three_point_attempt_rate': self.home_three_point_attempt_rate,
            'home_three_point_field_goal_attempts': self.home_three_point_field_goal_attempts,
            'home_three_point_field_goal_percentage': self.home_three_point_field_goal_percentage,
            'home_three_point_field_goals': self.home_three_point_field_goals,
            'home_total_rebound_percentage': self.home_total_rebound_percentage,
            'home_total_rebounds': self.home_total_rebounds,
            'home_true_shooting_percentage': self.home_true_shooting_percentage,
            'home_turnover_percentage': self.home_turnover_percentage,
            'home_turnovers': self.home_turnovers,
            'home_two_point_field_goal_attempts': self.home_two_point_field_goal_attempts,
            'home_two_point_field_goal_percentage': self.home_two_point_field_goal_percentage,
            'home_two_point_field_goals': self.home_two_point_field_goals,
            'home_wins': self.home_wins,
            'location': self.location,
            'losing_abbr': self.losing_abbr,
            'losing_name': self.losing_name,
            'pace': self.pace,
            'winner': self.winner,
            'winning_abbr': self.winning_abbr,
            'winning_name': self.winning_name
        }
        return pd.DataFrame([fields_to_include], index=[self._uri])

    @property
    def away_players(self):
        """Return the away team's players.

        Returns
        -------
        list
            A list of BoxscorePlayer instances.
        """
        return self._away_players

    @property
    def home_players(self):
        """Return the home team's players.

        Returns
        -------
        list
            A list of BoxscorePlayer instances.
        """
        return self._home_players

    @property
    def summary(self):
        """Return the quarterly score summary.

        Returns
        -------
        dict
            A dictionary of 'away' and 'home' quarterly scores.
        """
        return self._summary

    @property
    def winner(self):
        """Return the winning team.

        Returns
        -------
        str or None
            A constant (HOME or AWAY) indicating the winner.
        """
        try:
            if int(self.home_points) > int(self.away_points):
                return HOME
            return AWAY
        except (TypeError, ValueError):
            return None

    @property
    def winning_name(self):
        """Return the winning team's name.

        Returns
        -------
        str or None
            The winning team's name.
        """
        if self.winner == HOME and self._home_name:
            return self._home_name.text
        if self.winner == AWAY and self._away_name:
            return self._away_name.text
        return None

    @property
    def winning_abbr(self):
        """Return the winning team's abbreviation.

        Returns
        -------
        str or None
            The winning team's abbreviation.
        """
        if self.winner == HOME and self._home_name:
            return _parse_abbreviation(self._home_name)
        if self.winner == AWAY and self._away_name:
            return _parse_abbreviation(self._away_name)
        return None

    @property
    def losing_name(self):
        """Return the losing team's name.

        Returns
        -------
        str or None
            The losing team's name.
        """
        if self.winner == HOME and self._away_name:
            return self._away_name.text
        if self.winner == AWAY and self._home_name:
            return self._home_name.text
        return None

    @property
    def losing_abbr(self):
        """Return the losing team's abbreviation.

        Returns
        -------
        str or None
            The losing team's abbreviation.
        """
        if self.winner == HOME and self._away_name:
            return _parse_abbreviation(self._away_name)
        if self.winner == AWAY and self._home_name:
            return _parse_abbreviation(self._home_name)
        return None

    @float_property_decorator
    def pace(self):
        """Return the game pace.

        Returns
        -------
        float or None
            Possessions per 40 minutes.
        """
        return self._pace

    @int_property_decorator
    def away_wins(self):
        """Return the away team's wins.

        Returns
        -------
        int
            The number of wins, or 0 if unavailable.
        """
        try:
            wins, _ = re.findall(r'\d+', self._away_record)
            return int(wins)
        except (ValueError, TypeError):
            return 0

    @int_property_decorator
    def away_losses(self):
        """Return the away team's losses.

        Returns
        -------
        int
            The number of losses, or 0 if unavailable.
        """
        try:
            _, losses = re.findall(r'\d+', self._away_record)
            return int(losses)
        except (ValueError, TypeError):
            return 0

    @int_property_decorator
    def away_minutes_played(self):
        """Return the away team's minutes played.

        Returns
        -------
        int or None
            Total minutes played.
        """
        return self._away_minutes_played

    @int_property_decorator
    def away_field_goals(self):
        """Return the away team's field goals made.

        Returns
        -------
        int or None
            Total field goals made.
        """
        return self._away_field_goals

    @int_property_decorator
    def away_field_goal_attempts(self):
        """Return the away team's field goal attempts.

        Returns
        -------
        int or None
            Total field goal attempts.
        """
        return self._away_field_goal_attempts

    @float_property_decorator
    def away_field_goal_percentage(self):
        """Return the away team's field goal percentage.

        Returns
        -------
        float or None
            Field goal percentage (0-1).
        """
        return self._away_field_goal_percentage

    @int_property_decorator
    def away_three_point_field_goals(self):
        """Return the away team's three-point field goals.

        Returns
        -------
        int or None
            Total three-point field goals made.
        """
        return self._away_three_point_field_goals

    @int_property_decorator
    def away_three_point_field_goal_attempts(self):
        """Return the away team's three-point attempts.

        Returns
        -------
        int or None
            Total three-point field goal attempts.
        """
        return self._away_three_point_field_goal_attempts

    @float_property_decorator
    def away_three_point_field_goal_percentage(self):
        """Return the away team's three-point percentage.

        Returns
        -------
        float or None
            Three-point field goal percentage (0-1).
        """
        return self._away_three_point_field_goal_percentage

    @int_property_decorator
    def away_two_point_field_goals(self):
        """Return the away team's two-point field goals.

        Returns
        -------
        int or None
            Total two-point field goals made.
        """
        try:
            return self.away_field_goals - self.away_three_point_field_goals
        except TypeError:
            return None

    @int_property_decorator
    def away_two_point_field_goal_attempts(self):
        """Return the away team's two-point attempts.

        Returns
        -------
        int or None
            Total two-point field goal attempts.
        """
        try:
            return self.away_field_goal_attempts - self.away_three_point_field_goal_attempts
        except TypeError:
            return None

    @float_property_decorator
    def away_two_point_field_goal_percentage(self):
        """Return the away team's two-point percentage.

        Returns
        -------
        float or None
            Two-point field goal percentage (0-1).
        """
        try:
            return round(float(self.away_two_point_field_goals) / float(self.away_two_point_field_goal_attempts), 3)
        except (TypeError, ZeroDivisionError):
            return None

    @int_property_decorator
    def away_free_throws(self):
        """Return the away team's free throws made.

        Returns
        -------
        int or None
            Total free throws made.
        """
        return self._away_free_throws

    @int_property_decorator
    def away_free_throw_attempts(self):
        """Return the away team's free throw attempts.

        Returns
        -------
        int or None
            Total free throw attempts.
        """
        return self._away_free_throw_attempts

    @float_property_decorator
    def away_free_throw_percentage(self):
        """Return the away team's free throw percentage.

        Returns
        -------
        float or None
            Free throw percentage (0-1).
        """
        return self._away_free_throw_percentage

    @int_property_decorator
    def away_offensive_rebounds(self):
        """Return the away team's offensive rebounds.

        Returns
        -------
        int or None
            Total offensive rebounds.
        """
        return self._away_offensive_rebounds

    @int_property_decorator
    def away_defensive_rebounds(self):
        """Return the away team's defensive rebounds.

        Returns
        -------
        int or None
            Total defensive rebounds.
        """
        return self._away_defensive_rebounds

    @int_property_decorator
    def away_total_rebounds(self):
        """Return the away team's total rebounds.

        Returns
        -------
        int or None
            Total rebounds.
        """
        return self._away_total_rebounds

    @int_property_decorator
    def away_assists(self):
        """Return the away team's assists.

        Returns
        -------
        int or None
            Total assists.
        """
        return self._away_assists

    @int_property_decorator
    def away_steals(self):
        """Return the away team's steals.

        Returns
        -------
        int or None
            Total steals.
        """
        return self._away_steals

    @int_property_decorator
    def away_blocks(self):
        """Return the away team's blocks.

        Returns
        -------
        int or None
            Total blocks.
        """
        return self._away_blocks

    @int_property_decorator
    def away_turnovers(self):
        """Return the away team's turnovers.

        Returns
        -------
        int or None
            Total turnovers.
        """
        return self._away_turnovers

    @int_property_decorator
    def away_personal_fouls(self):
        """Return the away team's personal fouls.

        Returns
        -------
        int or None
            Total personal fouls.
        """
        return self._away_personal_fouls

    @int_property_decorator
    def away_points(self):
        """Return the away team's points.

        Returns
        -------
        int or None
            Total points scored.
        """
        return self._away_points

    @float_property_decorator
    def away_true_shooting_percentage(self):
        """Return the away team's true shooting percentage.

        Returns
        -------
        float or None
            True shooting percentage (0-1).
        """
        return self._away_true_shooting_percentage

    @float_property_decorator
    def away_effective_field_goal_percentage(self):
        """Return the away team's effective field goal percentage.

        Returns
        -------
        float or None
            Effective field goal percentage (0-1).
        """
        return self._away_effective_field_goal_percentage

    @float_property_decorator
    def away_three_point_attempt_rate(self):
        """Return the away team's three-point attempt rate.

        Returns
        -------
        float or None
            Percentage of field goal attempts from three-point range (0-1).
        """
        return self._away_three_point_attempt_rate

    @float_property_decorator
    def away_free_throw_attempt_rate(self):
        """Return the away team's free throw attempt rate.

        Returns
        -------
        float or None
            Average free throw attempts per field goal attempt.
        """
        return self._away_free_throw_attempt_rate

    @float_property_decorator
    def away_offensive_rebound_percentage(self):
        """Return the away team's offensive rebound percentage.

        Returns
        -------
        float or None
            Percentage of available offensive rebounds (0-100).
        """
        return self._away_offensive_rebound_percentage

    @float_property_decorator
    def away_defensive_rebound_percentage(self):
        """Return the away team's defensive rebound percentage.

        Returns
        -------
        float or None
            Percentage of available defensive rebounds (0-100).
        """
        return self._away_defensive_rebound_percentage

    @float_property_decorator
    def away_total_rebound_percentage(self):
        """Return the away team's total rebound percentage.

        Returns
        -------
        float or None
            Percentage of available rebounds (0-100).
        """
        return self._away_total_rebound_percentage

    @float_property_decorator
    def away_assist_percentage(self):
        """Return the away team's assist percentage.

        Returns
        -------
        float or None
            Percentage of field goals assisted (0-100).
        """
        return self._away_assist_percentage

    @float_property_decorator
    def away_steal_percentage(self):
        """Return the away team's steal percentage.

        Returns
        -------
        float or None
            Percentage of possessions ending in a steal (0-100).
        """
        return self._away_steal_percentage

    @float_property_decorator
    def away_block_percentage(self):
        """Return the away team's block percentage.

        Returns
        -------
        float or None
            Percentage of 2-point field goals blocked (0-100).
        """
        return self._away_block_percentage

    @float_property_decorator
    def away_turnover_percentage(self):
        """Return the away team's turnover percentage.

        Returns
        -------
        float or None
            Turnovers per 100 possessions.
        """
        return self._away_turnover_percentage

    @float_property_decorator
    def away_offensive_rating(self):
        """Return the away team's offensive rating.

        Returns
        -------
        float or None
            Points scored per 100 possessions.
        """
        return self._away_offensive_rating

    @float_property_decorator
    def away_defensive_rating(self):
        """Return the away team's defensive rating.

        Returns
        -------
        float or None
            Points allowed per 100 possessions.
        """
        return self._away_defensive_rating

    @int_property_decorator
    def home_wins(self):
        """Return the home team's wins.

        Returns
        -------
        int
            The number of wins, or 0 if unavailable.
        """
        try:
            wins, _ = re.findall(r'\d+', self._home_record)
            return int(wins)
        except (ValueError, TypeError):
            return 0

    @int_property_decorator
    def home_losses(self):
        """Return the home team's losses.

        Returns
        -------
        int
            The number of losses, or 0 if unavailable.
        """
        try:
            _, losses = re.findall(r'\d+', self._home_record)
            return int(losses)
        except (ValueError, TypeError):
            return 0

    @int_property_decorator
    def home_minutes_played(self):
        """Return the home team's minutes played.

        Returns
        -------
        int or None
            Total minutes played.
        """
        return self._home_minutes_played

    @int_property_decorator
    def home_field_goals(self):
        """Return the home team's field goals made.

        Returns
        -------
        int or None
            Total field goals made.
        """
        return self._home_field_goals

    @int_property_decorator
    def home_field_goal_attempts(self):
        """Return the home team's field goal attempts.

        Returns
        -------
        int or None
            Total field goal attempts.
        """
        return self._home_field_goal_attempts

    @float_property_decorator
    def home_field_goal_percentage(self):
        """Return the home team's field goal percentage.

        Returns
        -------
        float or None
            Field goal percentage (0-1).
        """
        return self._home_field_goal_percentage

    @int_property_decorator
    def home_three_point_field_goals(self):
        """Return the home team's three-point field goals.

        Returns
        -------
        int or None
            Total three-point field goals made.
        """
        return self._home_three_point_field_goals

    @int_property_decorator
    def home_three_point_field_goal_attempts(self):
        """Return the home team's three-point attempts.

        Returns
        -------
        int or None
            Total three-point field goal attempts.
        """
        return self._home_three_point_field_goal_attempts

    @float_property_decorator
    def home_three_point_field_goal_percentage(self):
        """Return the home team's three-point percentage.

        Returns
        -------
        float or None
            Three-point field goal percentage (0-1).
        """
        return self._home_three_point_field_goal_percentage

    @int_property_decorator
    def home_two_point_field_goals(self):
        """Return the home team's two-point field goals.

        Returns
        -------
        int or None
            Total two-point field goals made.
        """
        try:
            return self.home_field_goals - self.home_three_point_field_goals
        except TypeError:
            return None

    @int_property_decorator
    def home_two_point_field_goal_attempts(self):
        """Return the home team's two-point attempts.

        Returns
        -------
        int or None
            Total two-point field goal attempts.
        """
        try:
            return self.home_field_goal_attempts - self.home_three_point_field_goal_attempts
        except TypeError:
            return None

    @float_property_decorator
    def home_two_point_field_goal_percentage(self):
        """Return the home team's two-point percentage.

        Returns
        -------
        float or None
            Two-point field goal percentage (0-1).
        """
        try:
            return round(float(self.home_two_point_field_goals) / float(self.home_two_point_field_goal_attempts), 3)
        except (TypeError, ZeroDivisionError):
            return None

    @int_property_decorator
    def home_free_throws(self):
        """Return the home team's free throws made.

        Returns
        -------
        int or None
            Total free throws made.
        """
        return self._home_free_throws

    @int_property_decorator
    def home_free_throw_attempts(self):
        """Return the home team's free throw attempts.

        Returns
        -------
        int or None
            Total free throw attempts.
        """
        return self._home_free_throw_attempts

    @float_property_decorator
    def home_free_throw_percentage(self):
        """Return the home team's free throw percentage.

        Returns
        -------
        float or None
            Free throw percentage (0-1).
        """
        return self._home_free_throw_percentage

    @int_property_decorator
    def home_offensive_rebounds(self):
        """Return the home team's offensive rebounds.

        Returns
        -------
        int or None
            Total offensive rebounds.
        """
        return self._home_offensive_rebounds

    @int_property_decorator
    def home_defensive_rebounds(self):
        """Return the home team's defensive rebounds.

        Returns
        -------
        int or None
            Total defensive rebounds.
        """
        return self._home_defensive_rebounds

    @int_property_decorator
    def home_total_rebounds(self):
        """Return the home team's total rebounds.

        Returns
        -------
        int or None
            Total rebounds.
        """
        return self._home_total_rebounds

    @int_property_decorator
    def home_assists(self):
        """Return the home team's assists.

        Returns
        -------
        int or None
            Total assists.
        """
        return self._home_assists

    @int_property_decorator
    def home_steals(self):
        """Return the home team's steals.

        Returns
        -------
        int or None
            Total steals.
        """
        return self._home_steals

    @int_property_decorator
    def home_blocks(self):
        """Return the home team's blocks.

        Returns
        -------
        int or None
            Total blocks.
        """
        return self._home_blocks

    @int_property_decorator
    def home_turnovers(self):
        """Return the home team's turnovers.

        Returns
        -------
        int or None
            Total turnovers.
        """
        return self._home_turnovers

    @int_property_decorator
    def home_personal_fouls(self):
        """Return the home team's personal fouls.

        Returns
        -------
        int or None
            Total personal fouls.
        """
        return self._home_personal_fouls

    @int_property_decorator
    def home_points(self):
        """Return the home team's points.

        Returns
        -------
        int or None
            Total points scored.
        """
        return self._home_points

    @float_property_decorator
    def home_true_shooting_percentage(self):
        """Return the home team's true shooting percentage.

        Returns
        -------
        float or None
            True shooting percentage (0-1).
        """
        return self._home_true_shooting_percentage

    @float_property_decorator
    def home_effective_field_goal_percentage(self):
        """Return the home team's effective field goal percentage.

        Returns
        -------
        float or None
            Effective field goal percentage (0-1).
        """
        return self._home_effective_field_goal_percentage

    @float_property_decorator
    def home_three_point_attempt_rate(self):
        """Return the home team's three-point attempt rate.

        Returns
        -------
        float or None
            Percentage of field goal attempts from three-point range (0-1).
        """
        return self._home_three_point_attempt_rate

    @float_property_decorator
    def home_free_throw_attempt_rate(self):
        """Return the home team's free throw attempt rate.

        Returns
        -------
        float or None
            Average free throw attempts per field goal attempt.
        """
        return self._home_free_throw_attempt_rate

    @float_property_decorator
    def home_offensive_rebound_percentage(self):
        """Return the home team's offensive rebound percentage.

        Returns
        -------
        float or None
            Percentage of available offensive rebounds (0-100).
        """
        return self._home_offensive_rebound_percentage

    @float_property_decorator
    def home_defensive_rebound_percentage(self):
        """Return the home team's defensive rebound percentage.

        Returns
        -------
        float or None
            Percentage of available defensive rebounds (0-100).
        """
        return self._home_defensive_rebound_percentage

    @float_property_decorator
    def home_total_rebound_percentage(self):
        """Return the home team's total rebound percentage.

        Returns
        -------
        float or None
            Percentage of available rebounds (0-100).
        """
        return self._home_total_rebound_percentage

    @float_property_decorator
    def home_assist_percentage(self):
        """Return the home team's assist percentage.

        Returns
        -------
        float or None
            Percentage of field goals assisted (0-100).
        """
        return self._home_assist_percentage

    @float_property_decorator
    def home_steal_percentage(self):
        """Return the home team's steal percentage.

        Returns
        -------
        float or None
            Percentage of possessions ending in a steal (0-100).
        """
        return self._home_steal_percentage

    @float_property_decorator
    def home_block_percentage(self):
        """Return the home team's block percentage.

        Returns
        -------
        float or None
            Percentage of 2-point field goals blocked (0-100).
        """
        return self._home_block_percentage

    @float_property_decorator
    def home_turnover_percentage(self):
        """Return the home team's turnover percentage.

        Returns
        -------
        float or None
            Turnovers per 100 possessions.
        """
        return self._home_turnover_percentage

    @float_property_decorator
    def home_offensive_rating(self):
        """Return the home team's offensive rating.

        Returns
        -------
        float or None
            Points scored per 100 possessions.
        """
        return self._home_offensive_rating

    @float_property_decorator
    def home_defensive_rating(self):
        """Return the home team's defensive rating.

        Returns
        -------
        float or None
            Points allowed per 100 possessions.
        """
        return self._home_defensive_rating

class Boxscores:
    """NBA games for a specific date range.

    Retrieves games played on a given date or date range, including boxscore URIs,
    team names, abbreviations, scores, and results.

    Parameters
    ----------
    date : datetime
        The start date to search for games (month, day, year required).
    end_date : datetime, optional
        The end date to search up to (inclusive). If None, only the start date is searched.
    """
    def __init__(self, date, end_date=None):
        self._boxscores = {}
        self._find_games(date, end_date)

    def __str__(self):
        """Return the string representation of the boxscores.

        Returns
        -------
        str
            A string listing the dates of the boxscores.
        """
        return f"NBA games for {', '.join(self._boxscores.keys())}"

    def __repr__(self):
        """Return the string representation of the boxscores.

        Returns
        -------
        str
            A string listing the dates of the boxscores.
        """
        return self.__str__()

    @property
    def games(self):
        """Return all games in the date range.

        Returns
        -------
        dict
            A dictionary of dates (YYYY-MM-DD) to lists of game details.
        """
        return self._boxscores

    def _create_url(self, date):
        """Create the boxscores URL for a date.

        Parameters
        ----------
        date : datetime
            The date to create the URL for.

        Returns
        -------
        str
            The URL for the boxscores page.
        """
        return BOXSCORES_URL % (date.month, date.day, date.year)

    def _get_requested_page(self, url):
        """Retrieve the boxscores page.

        Parameters
        ----------
        url : str
            The URL of the boxscores page.

        Returns
        -------
        BeautifulSoup or None
            The parsed HTML page.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except (HTTPError, requests.RequestException):
            return None

    def _get_boxscore_uri(self, link):
        """Extract the boxscore URI.

        Parameters
        ----------
        link : BeautifulSoup object
            The link to the boxscore.

        Returns
        -------
        str or None
            The boxscore URI.
        """
        if link and link.get('href'):
            return re.sub(r'.*/boxscores/|\.html.*$', '', link['href']).strip()
        return None

    def _get_name(self, link):
        """Extract team name and abbreviation.

        Parameters
        ----------
        link : BeautifulSoup object
            The team link.

        Returns
        -------
        tuple
            (team_name, team_abbr) or (None, None).
        """
        if not link:
            return None, None
        team_name = link.text.strip()
        abbr = _parse_abbreviation(link)
        return team_name, abbr

    def _get_score(self, cell):
        """Extract a team's score.

        Parameters
        ----------
        cell : BeautifulSoup object
            The score cell.

        Returns
        -------
        int or None
            The score.
        """
        try:
            return int(cell.text)
        except (ValueError, TypeError):
            return None

    def _get_team_details(self, game):
        """Extract team details from a game row.

        Parameters
        ----------
        game : BeautifulSoup object
            The game row.

        Returns
        -------
        tuple
            (away_name, away_abbr, away_score, home_name, home_abbr, home_score).
        """
        links = game.select('td a')
        scores = game.select('td.right')
        away_link = links[0] if links else None
        home_link = links[-1] if len(links) > 1 else None
        away_score = self._get_score(scores[0]) if len(scores) > 1 else None
        home_score = self._get_score(scores[1]) if len(scores) > 1 else None
        away_name, away_abbr = self._get_name(away_link)
        home_name, home_abbr = self._get_name(home_link)
        return away_name, away_abbr, away_score, home_name, home_abbr, home_score

    def _get_team_results(self, row):
        """Extract winning or losing team details.

        Parameters
        ----------
        row : BeautifulSoup object
            The winner or loser row.

        Returns
        -------
        tuple or None
            (name, abbreviation) or None.
        """
        link = row.select_one('td a')
        return self._get_name(link) if link else None

    def _extract_game_info(self, games):
        """Parse game information.

        Parameters
        ----------
        games : list
            List of game rows.

        Returns
        -------
        list
            List of game detail dictionaries.
        """
        all_boxscores = []
        for game in games:
            details = self._get_team_details(game)
            away_name, away_abbr, away_score, home_name, home_abbr, home_score = details
            boxscore_link = game.select_one('td.right.gamelink a')
            boxscore_uri = self._get_boxscore_uri(boxscore_link)
            winner_row = game.select_one('tr.winner')
            loser_row = game.select_one('tr.loser')
            winner = self._get_team_results(winner_row) if winner_row else None
            loser = self._get_team_results(loser_row) if loser_row else None
            losers = game.select('tr.loser')
            if (len(losers) != 2 and loser and not winner) or (len(losers) != 2 and winner and not loser):
                continue
            winning_name, winning_abbr = winner if winner and len(losers) != 2 else (None, None)
            losing_name, losing_abbr = loser if loser and len(losers) != 2 else (None, None)
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

    def _find_games(self, date, end_date):
        """Retrieve games for the date range.

        Parameters
        ----------
        date : datetime
            Start date.
        end_date : datetime or None
            End date.
        """
        if not end_date or date > end_date:
            end_date = date
        date_step = date
        while date_step <= end_date:
            url = self._create_url(date_step)
            page = self._get_requested_page(url)
            if not page:
                date_step += timedelta(days=1)
                continue
            games = page.select('table.teams tbody tr')
            boxscores = self._extract_game_info(games)
            timestamp = f'{date_step.month:02d}-{date_step.day:02d}-{date_step.year}'
            self._boxscores[timestamp] = boxscores
            date_step += timedelta(days=1)