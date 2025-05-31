import pandas as pd
import re
from datetime import timedelta, datetime
from bs4 import BeautifulSoup
from urllib.error import HTTPError
import requests
from .. import utils
from ..constants import AWAY, HOME
from ..decorators import float_property_decorator, int_property_decorator
from .constants import (BOXSCORE_ELEMENT_INDEX,
                        BOXSCORE_SCHEME,
                        BOXSCORE_URL,
                        BOXSCORES_URL)
from .player import AbstractPlayer


def _int_property_decorator(func):
    """Convert a property to an integer, returning None if conversion fails.

    Parameters
    ----------
    func : callable
        The function to decorate, which retrieves a property value.

    Returns
    -------
    callable
        A wrapped property that converts the function's output to an integer.
    """
    @property
    @wraps(func)
    def wrapper(*args):
        index = args[0]._index
        prop = func(*args)
        try:
            value = _cleanup(prop[index])
            return int(value)
        except (TypeError, ValueError):
            return None
    return wrapper


def _cleanup(prop):
    """Remove unwanted characters from a property value and handle None cases.

    Parameters
    ----------
    prop : str or None
        The property value to clean, which may include characters like '%', '$', ',', or '+'.

    Returns
    -------
    str
        The cleaned property value with specified characters removed, or an empty string if prop is None.
    """
    try:
        prop = prop.replace('%', '')
        prop = prop.replace('$', '')
        prop = prop.replace(',', '')
        return prop.replace('+', '')
    except AttributeError:
        return ''


class BoxscorePlayer(AbstractPlayer):
    """Get player stats for an individual game.

    Given a player ID, such as 'hardeja01' for James Harden, their full name,
    and all associated stats from the Boxscore page in HTML format, parse the
    HTML and extract only the relevant stats for the specified player and
    assign them to readable properties.

    This class inherits the ``AbstractPlayer`` class. As a result, all
    properties associated with ``AbstractPlayer`` can also be read directly
    from this class.

    As this class is instantiated from within the Boxscore class, it should not
    be called directly and should instead be queried using the appropriate
    players properties from the Boxscore class.

    Parameters
    ----------
    player_id : str
        A player's ID according to basketball-reference.com, such as
        'hardeja01' for James Harden. The player ID can be found by navigating
        to the player's stats page and getting the string between the final
        slash and the '.html' in the URL. In general, the ID is in the format
        'LLLLLFFNN' where 'LLLLL' are the first 5 letters in the player's last
        name, 'FF', are the first 2 letters in the player's first name, and
        'NN' is a number starting at '01' for the first time that player ID has
        been used and increments by 1 for every successive player.
    player_name : str
        A string representing the player's first and last name, such as 'James
        Harden'.
    player_data : str
        A string representation of the player's HTML data from the Boxscore
        page. If the player appears in multiple tables, all of their
        information will appear in one single string concatenated together.
    """
    def __init__(self, player_id, player_name, player_data):
        self._index = 0
        self._player_id = player_id
        self._defensive_rating = None
        self._offensive_rating = None
        AbstractPlayer.__init__(self, player_id, player_name, player_data)

    @property
    def dataframe(self):
        """Return a pandas DataFrame of the player's stats for the game.

        Returns
        -------
        pandas.DataFrame
            A DataFrame containing all relevant class properties and values for
            the specified game, indexed by the player's ID.
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
        """Return the number of minutes the player was on the court.

        Returns
        -------
        float or None
            The number of game minutes the player was on the court, calculated
            as minutes plus seconds divided by 60. Returns None if not available.
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
        """Return the total number of two-point field goals made.

        Returns
        -------
        int or None
            The total number of two-point field goals made, calculated as total
            field goals minus three-pointers. Returns None if data is unavailable.
        """
        if self.field_goals and self.three_pointers:
            return int(self.field_goals - self.three_pointers)
        if self.field_goals:
            return int(self.field_goals)
        return None

    @property
    def two_point_attempts(self):
        """Return the total number of two-point field goal attempts.

        Returns
        -------
        int or None
            The total number of two-point field goal attempts, calculated as
            total field goal attempts minus three-point attempts. Returns None
            if data is unavailable.
        """
        if self.field_goal_attempts and self.three_point_attempts:
            return int(self.field_goal_attempts - self.three_point_attempts)
        if self.field_goal_attempts:
            return int(self.field_goal_attempts)
        return None

    @property
    def two_point_percentage(self):
        """Return the player's two-point field goal percentage.

        Returns
        -------
        float or None
            The player's two-point field goal percentage (0-1), rounded to three
            decimal places. Returns 0.0 if attempts exist but no shots were made,
            or None if no attempts were made.
        """
        if self.two_pointers and self.two_point_attempts:
            return round(float(self.two_pointers) / float(self.two_point_attempts), 3)
        if self.two_point_attempts:
            return 0.0
        return None

    @_int_property_decorator
    def offensive_rating(self):
        """Return the player's offensive rating.

        Returns
        -------
        int or None
            The player's offensive rating, measured as points produced per 100
            possessions. Returns None if conversion fails.
        """
        return self._offensive_rating

    @_int_property_decorator
    def defensive_rating(self):
        """Return the player's defensive rating.

        Returns
        -------
        int or None
            The player's defensive rating, measured as points allowed per 100
            possessions. Returns None if conversion fails.
        """
        return self._defensive_rating


class Boxscore:
    """Detailed information about the final statistics for a game.

    Stores all relevant metrics for a game such as the date, time, location,
    result, and advanced metrics like effective field goal percentage, true
    shooting percentage, game pace, and more.

    Parameters
    ----------
    uri : str
        The relative link to the boxscore HTML page, such as '201710310LAL'.
    """
    def __init__(self, uri):
        self._uri = uri
        self._date = None
        self._location = None
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
            A string describing the game, e.g., 'Boxscore for Los Angeles Lakers at Portland Trail Blazers (October 31, 2017)'.
        """
        if not self._away_name or not self._home_name:
            return f'Boxscore for {self._uri}'
        return f'Boxscore for {self._away_name.text} at {self._home_name.text} ({self.date})'

    def __repr__(self):
        """Return the string representation of the boxscore.

        Returns
        -------
        str
            A string describing the game, e.g., 'Boxscore for Los Angeles Lakers at Portland Trail Blazers (October 31, 2017)'.
        """
        return self.__str__()

    def _retrieve_html_page(self, uri):
        """Download the requested HTML page.

        Given a relative link, download the requested page and strip it of all
        comment tags before returning a BeautifulSoup object for parsing.

        Parameters
        ----------
        uri : str
            The relative link to the boxscore HTML page, such as '201710310LAL'.

        Returns
        -------
        BeautifulSoup or None
            A BeautifulSoup object containing the HTML data with comment tags
            removed, or None if the request fails.
        """
        url = BOXSCORE_URL % uri
        try:
            response = requests.get(url)
            response.raise_for_status()
            return BeautifulSoup(utils._remove_html_comment_tags(response.text), 'html.parser')
        except (HTTPError, requests.RequestException):
            return None

    def _parse_game_date_and_location(self, field, boxscore):
        """Retrieve the game's date and location.

        The date and location are embedded in a single field, separated by
        newline characters. The first line is the date, and the second is the
        location. Additional lines may exist for events like the NBA In-Season
        Tournament.

        Parameters
        ----------
        field : str
            The name of the attribute to parse ('date' or 'location').
        boxscore : BeautifulSoup object
            A BeautifulSoup object containing the HTML data from the boxscore.

        Returns
        -------
        str or None
            The parsed date or location, or None if not available.
        """
        scheme = BOXSCORE_SCHEME[field]
        items = boxscore.select(scheme)
        if not items:
            return None
        game_info = items[0].text.split('\n')
        game_info = [line.strip() for line in game_info if line.strip()]
        if 'AM' not in game_info[0] and 'PM' not in game_info[0]:
            game_info.pop(0) if game_info else None
        if len(game_info) < 2 and field == 'location':
            return None
        return game_info[BOXSCORE_ELEMENT_INDEX[field]]

    def _parse_name(self, field, boxscore):
        """Retrieve the team's complete name tag.

        The team's full name and abbreviation are stored in the name tag, which
        is used to parse the winning and losing team's information.

        Parameters
        ----------
        field : str
            The name of the attribute to parse ('away_name' or 'home_name').
        boxscore : BeautifulSoup object
            A BeautifulSoup object containing the HTML data from the boxscore.

        Returns
        -------
        BeautifulSoup object or None
            The tag containing the team's name and abbreviation, or None if not found.
        """
        scheme = BOXSCORE_SCHEME[field]
        items = boxscore.select(scheme)
        if not items:
            return None
        return items[BOXSCORE_ELEMENT_INDEX[field]]

    def _parse_summary(self, boxscore):
        """Parse the game summary including scores by quarter.

        The summary includes points scored each quarter, including overtime if
        applicable. The output is a dictionary with 'away' and 'home' keys,
        each mapping to a list of scores by quarter.

        Parameters
        ----------
        boxscore : BeautifulSoup object
            A BeautifulSoup object containing the HTML data from the boxscore.

        Returns
        -------
        dict
            A dictionary with 'away' and 'home' keys, each containing a list of
            scores by quarter, e.g., {'away': [23, 40, 23, 24], 'home': [30, 27, 34, 30]}.
        """
        summary = {'away': [], 'home': []}
        game_summary = boxscore.select_one(BOXSCORE_SCHEME['summary'])
        if not game_summary:
            return summary
        team = ['away', 'home']
        for ind, row in enumerate(game_summary.select('tr')):
            if ind < 2:  # Skip header rows
                continue
            cells = row.select('td.center, td.center ')[:-1]  # Exclude final score
            for quarter in cells:
                try:
                    summary[team[ind % 2]].append(int(quarter.text))
                except ValueError:
                    summary[team[ind % 2]].append(None)
        return summary

    def _find_boxscore_tables(self, boxscore):
        """Find all tables with boxscore information.

        Identify tables containing boxscore data by checking for IDs prefixed
        with 'box_' or 'box-'.

        Parameters
        ----------
        boxscore : BeautifulSoup object
            A BeautifulSoup object containing the HTML data from the boxscore.

        Returns
        -------
        list
            A list of BeautifulSoup objects, each representing a boxscore table.
        """
        return [table for table in boxscore.select('table')
                if table.get('id', '').startswith(('box_', 'box-'))]

    def _find_player_id(self, row):
        """Find the player's ID.

        Extract the player's ID from the 'data-append-csv' attribute.

        Parameters
        ----------
        row : BeautifulSoup object
            A BeautifulSoup object representing a single row in a boxscore table.

        Returns
        -------
        str or None
            The player's ID, e.g., 'hardeja01', or None if not found.
        """
        th = row.select_one('th')
        return th.get('data-append-csv') if th else None

    def _find_player_name(self, row):
        """Find the player's full name.

        Extract the player's full name from the link text in the row.

        Parameters
        ----------
        row : BeautifulSoup object
            A BeautifulSoup object representing a single row in a boxscore table.

        Returns
        -------
        str
            The player's full name, e.g., 'James Harden', or empty string if not found.
        """
        a = row.select_one('th a')
        return a.text if a else ''

    def _extract_player_stats(self, table, player_dict, home_or_away):
        """Combine all player stats into a single object.

        Aggregate player stats from a table, combining basic and advanced stats
        into a single dictionary entry per player.

        Parameters
        ----------
        table : BeautifulSoup object
            A BeautifulSoup object of a single boxscore table.
        player_dict : dict
            A dictionary where keys are player IDs and values are dictionaries
            containing player name, HTML data, and team.
        home_or_away : str
            A constant (HOME or AWAY) indicating the player's team.

        Returns
        -------
        dict
            The updated player_dict with aggregated stats.
        """
        for row in table.select('tbody tr'):
            player_id = self._find_player_id(row)
            if not player_id:
                continue
            name = self._find_player_name(row)
            try:
                player_dict[player_id]['data'] += str(row).strip()
            except KeyError:
                player_dict[player_id] = {
                    'name': name,
                    'data': str(row).strip(),
                    'team': home_or_away
                }
        return player_dict

    def _instantiate_players(self, player_dict):
        """Create a list of player instances for both teams.

        Instantiate BoxscorePlayer objects for each player and group them by team.

        Parameters
        ----------
        player_dict : dict
            A dictionary where keys are player IDs and values are dictionaries
            with player name, HTML data, and team.

        Returns
        -------
        tuple
            A tuple of (away_players, home_players), each a list of BoxscorePlayer instances.
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
        """Find all players for each team.

        Extract player data from boxscore tables and create BoxscorePlayer instances.

        Parameters
        ----------
        boxscore : BeautifulSoup object
            A BeautifulSoup object containing the HTML data from the boxscore.

        Returns
        -------
        tuple
            A tuple of (away_players, home_players), each a list of BoxscorePlayer instances.
        """
        player_dict = {}
        tables = self._find_boxscore_tables(boxscore)
        for i, table in enumerate(tables):
            home_or_away = AWAY if i < 2 else HOME
            player_dict = self._extract_player_stats(table, player_dict, home_or_away)
        return self._instantiate_players(player_dict)

    def _parse_game_data(self, uri):
        """Parse all game attributes from the boxscore page.

        Extract and set values for all boxscore attributes, including team and
        player stats.

        Parameters
        ----------
        uri : str
            The relative link to the boxscore HTML page, such as '201710310LAL'.
        """
        boxscore = self._retrieve_html_page(uri)
        if not boxscore:
            return

        for field in self.__dict__:
            if field in ('_winner', '_uri', '_away_players', '_home_players'):
                continue
            short_field = field[1:]
            if short_field in ('location', 'date'):
                value = self._parse_game_date_and_location(short_field, boxscore)
            elif short_field in ('away_name', 'home_name'):
                value = self._parse_name(short_field, boxscore)
            elif short_field == 'summary':
                value = self._parse_summary(boxscore)
            else:
                index = BOXSCORE_ELEMENT_INDEX.get(short_field, 0)
                strip = short_field == 'home_record'
                secondary_index = 1 if short_field in BOXSCORE_ELEMENT_INDEX else None
                value = utils._parse_field(BOXSCORE_SCHEME, boxscore, short_field,
                                         index, strip, secondary_index)
            setattr(self, field, value)
        self._away_players, self._home_players = self._find_players(boxscore)

    @property
    def dataframe(self):
        """Return a pandas DataFrame of the boxscore data.

        Returns
        -------
        pandas.DataFrame or None
            A DataFrame containing all class properties, indexed by the URI.
            Returns None if no points data is available.
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
        """Return the list of players for the away team.

        Returns
        -------
        list
            A list of BoxscorePlayer instances for each player on the away team.
        """
        return self._away_players

    @property
    def home_players(self):
        """Return the list of players for the home team.

        Returns
        -------
        list
            A list of BoxscorePlayer instances for each player on the home team.
        """
        return self._home_players

    @property
    def date(self):
        """Return the date of the game.

        Returns
        -------
        str or None
            The date the game took place, e.g., 'October 31, 2017'.
        """
        return self._date

    @property
    def location(self):
        """Return the venue where the game was played.

        Returns
        -------
        str or None
            The name of the venue, e.g., 'Moda Center'.
        """
        return self._location

    @property
    def summary(self):
        """Return the quarterly score summary.

        Returns
        -------
        dict
            A dictionary with 'away' and 'home' keys, each mapping to a list of
            scores by quarter, e.g., {'away': [23, 40, 23, 24], 'home': [30, 27, 34, 30]}.
        """
        return self._summary

    @property
    def winner(self):
        """Return the winning team.

        Returns
        -------
        str
            A constant (HOME or AWAY) indicating which team won.
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
            The winning team's name, e.g., 'Portland Trail Blazers'.
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
            The winning team's abbreviation, e.g., 'POR'.
        """
        if self.winner == HOME and self._home_name:
            return utils._parse_abbreviation(self._home_name)
        if self.winner == AWAY and self._away_name:
            return utils._parse_abbreviation(self._away_name)
        return None

    @property
    def losing_name(self):
        """Return the losing team's name.

        Returns
        -------
        str or None
            The losing team's name, e.g., 'Los Angeles Lakers'.
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
            The losing team's abbreviation, e.g., 'LAL'.
        """
        if self.winner == HOME and self._away_name:
            return utils._parse_abbreviation(self._away_name)
        if self.winner == AWAY and self._home_name:
            return utils._parse_abbreviation(self._home_name)
        return None

    @float_property_decorator
    def pace(self):
        """Return the game's pace.

        Returns
        -------
        float or None
            The game's pace, measured as possessions per 40 minutes.
        """
        return self._pace

    @int_property_decorator
    def away_wins(self):
        """Return the away team's wins after the game.

        Returns
        -------
        int
            The number of games the away team has won, or 0 if not available.
        """
        try:
            wins, _ = re.findall(r'\d+', self._away_record)
            return int(wins)
        except (ValueError, TypeError):
            return 0

    @int_property_decorator
    def away_losses(self):
        """Return the away team's losses after the game.

        Returns
        -------
        int
            The number of games the away team has lost, or 0 if not available.
        """
        try:
            _, losses = re.findall(r'\d+', self._away_record)
            return int(losses)
        except (ValueError, TypeError):
            return 0

    @int_property_decorator
    def away_minutes_played(self):
        """Return the total minutes played by the away team.

        Returns
        -------
        int or None
            The total number of minutes played by the away team.
        """
        return self._away_minutes_played

    @int_property_decorator
    def away_field_goals(self):
        """Return the total field goals made by the away team.

        Returns
        -------
        int or None
            The total number of field goals made by the away team.
        """
        return self._away_field_goals

    @int_property_decorator
    def away_field_goal_attempts(self):
        """Return the total field goal attempts by the away team.

        Returns
        -------
        int or None
            The total number of field goal attempts by the away team.
        """
        return self._away_field_goal_attempts

    @float_property_decorator
    def away_field_goal_percentage(self):
        """Return the away team's field goal percentage.

        Returns
        -------
        float or None
            The field goal percentage (0-1) for the away team.
        """
        return self._away_field_goal_percentage

    @int_property_decorator
    def away_three_point_field_goals(self):
        """Return the total three-point field goals made by the away team.

        Returns
        -------
        int or None
            The total number of three-point field goals made by the away team.
        """
        return self._away_three_point_field_goals

    @int_property_decorator
    def away_three_point_field_goal_attempts(self):
        """Return the total three-point field goal attempts by the away team.

        Returns
        -------
        int or None
            The total number of three-point field goal attempts by the away team.
        """
        return self._away_three_point_field_goal_attempts

    @float_property_decorator
    def away_three_point_field_goal_percentage(self):
        """Return the away team's three-point field goal percentage.

        Returns
        -------
        float or None
            The three-point field goal percentage (0-1) for the away team.
        """
        return self._away_three_point_field_goal_percentage

    @int_property_decorator
    def away_two_point_field_goals(self):
        """Return the total two-point field goals made by the away team.

        Returns
        -------
        int or None
            The total number of two-point field goals made by the away team.
        """
        try:
            return self.away_field_goals - self.away_three_point_field_goals
        except TypeError:
            return None

    @int_property_decorator
    def away_two_point_field_goal_attempts(self):
        """Return the total two-point field goal attempts by the away team.

        Returns
        -------
        int or None
            The total number of two-point field goal attempts by the away team.
        """
        try:
            return self.away_field_goal_attempts - self.away_three_point_field_goal_attempts
        except TypeError:
            return None

    @float_property_decorator
    def away_two_point_field_goal_percentage(self):
        """Return the away team's two-point field goal percentage.

        Returns
        -------
        float or None
            The two-point field goal percentage (0-1) for the away team, rounded to three decimal places.
        """
        try:
            return round(float(self.away_two_point_field_goals) / float(self.away_two_point_field_goal_attempts), 3)
        except (TypeError, ZeroDivisionError):
            return None

    @int_property_decorator
    def away_free_throws(self):
        """Return the total free throws made by the away team.

        Returns
        -------
        int or None
            The total number of free throws made by the away team.
        """
        return self._away_free_throws

    @int_property_decorator
    def away_free_throw_attempts(self):
        """Return the total free throw attempts by the away team.

        Returns
        -------
        int or None
            The total number of free throw attempts by the away team.
        """
        return self._away_free_throw_attempts

    @float_property_decorator
    def away_free_throw_percentage(self):
        """Return the away team's free throw percentage.

        Returns
        -------
        float or None
            The free throw percentage (0-1) for the away team.
        """
        return self._away_free_throw_percentage

    @int_property_decorator
    def away_offensive_rebounds(self):
        """Return the total offensive rebounds by the away team.

        Returns
        -------
        int or None
            The total number of offensive rebounds by the away team.
        """
        return self._away_offensive_rebounds

    @int_property_decorator
    def away_defensive_rebounds(self):
        """Return the total defensive rebounds by the away team.

        Returns
        -------
        int or None
            The total number of defensive rebounds by the away team.
        """
        return self._away_defensive_rebounds

    @int_property_decorator
    def away_total_rebounds(self):
        """Return the total rebounds by the away team.

        Returns
        -------
        int or None
            The total number of rebounds by the away team.
        """
        return self._away_total_rebounds

    @int_property_decorator
    def away_assists(self):
        """Return the total assists by the away team.

        Returns
        -------
        int or None
            The total number of assists by the away team.
        """
        return self._away_assists

    @int_property_decorator
    def away_steals(self):
        """Return the total steals by the away team.

        Returns
        -------
        int or None
            The total number of steals by the away team.
        """
        return self._away_steals

    @int_property_decorator
    def away_blocks(self):
        """Return the total blocks by the away team.

        Returns
        -------
        int or None
            The total number of blocks by the away team.
        """
        return self._away_blocks

    @int_property_decorator
    def away_turnovers(self):
        """Return the total turnovers by the away team.

        Returns
        -------
        int or None
            The total number of turnovers by the away team.
        """
        return self._away_turnovers

    @int_property_decorator
    def away_personal_fouls(self):
        """Return the total personal fouls by the away team.

        Returns
        -------
        int or None
            The total number of personal fouls by the away team.
        """
        return self._away_personal_fouls

    @int_property_decorator
    def away_points(self):
        """Return the total points scored by the away team.

        Returns
        -------
        int or None
            The number of points scored by the away team.
        """
        return self._away_points

    @float_property_decorator
    def away_true_shooting_percentage(self):
        """Return the away team's true shooting percentage.

        Returns
        -------
        float or None
            The true shooting percentage (0-1), considering free throws, 2-point,
            and 3-point field goals.
        """
        return self._away_true_shooting_percentage

    @float_property_decorator
    def away_effective_field_goal_percentage(self):
        """Return the away team's effective field goal percentage.

        Returns
        -------
        float or None
            The effective field goal percentage (0-1), weighting 3-point field goals.
        """
        return self._away_effective_field_goal_percentage

    @float_property_decorator
    def away_three_point_attempt_rate(self):
        """Return the away team's three-point attempt rate.

        Returns
        -------
        float or None
            The percentage of field goal attempts from 3-point range (0-1).
        """
        return self._away_three_point_attempt_rate

    @float_property_decorator
    def away_free_throw_attempt_rate(self):
        """Return the away team's free throw attempt rate.

        Returns
        -------
        float or None
            The average number of free throw attempts per field goal attempt.
        """
        return self._away_free_throw_attempt_rate

    @float_property_decorator
    def away_offensive_rebound_percentage(self):
        """Return the away team's offensive rebound percentage.

        Returns
        -------
        float or None
            The percentage of available offensive rebounds grabbed (0-100).
        """
        return self._away_offensive_rebound_percentage

    @float_property_decorator
    def away_defensive_rebound_percentage(self):
        """Return the away team's defensive rebound percentage.

        Returns
        -------
        float or None
            The percentage of available defensive rebounds grabbed (0-100).
        """
        return self._away_defensive_rebound_percentage

    @float_property_decorator
    def away_total_rebound_percentage(self):
        """Return the away team's total rebound percentage.

        Returns
        -------
        float or None
            The percentage of available rebounds grabbed (0-100).
        """
        return self._away_total_rebound_percentage

    @float_property_decorator
    def away_assist_percentage(self):
        """Return the away team's assist percentage.

        Returns
        -------
        float or None
            The percentage of field goals that were assisted (0-100).
        """
        return self._away_assist_percentage

    @float_property_decorator
    def away_steal_percentage(self):
        """Return the away team's steal percentage.

        Returns
        -------
        float or None
            The percentage of possessions ending in a steal (0-100).
        """
        return self._away_steal_percentage

    @float_property_decorator
    def away_block_percentage(self):
        """Return the away team's block percentage.

        Returns
        -------
        float or None
            The percentage of 2-point field goals blocked (0-100).
        """
        return self._away_block_percentage

    @float_property_decorator
    def away_turnover_percentage(self):
        """Return the away team's turnover percentage.

        Returns
        -------
        float or None
            The number of turnovers per 100 possessions.
        """
        return self._away_turnover_percentage

    @float_property_decorator
    def away_offensive_rating(self):
        """Return the away team's offensive rating.

        Returns
        -------
        float or None
            The average points scored per 100 possessions.
        """
        return self._away_offensive_rating

    @float_property_decorator
    def away_defensive_rating(self):
        """Return the away team's defensive rating.

        Returns
        -------
        float or None
            The average points allowed per 100 possessions.
        """
        return self._away_defensive_rating

    @int_property_decorator
    def home_wins(self):
        """Return the home team's wins after the game.

        Returns
        -------
        int
            The number of games the home team has won, or 0 if not available.
        """
        try:
            wins, _ = re.findall(r'\d+', self._home_record)
            return int(wins)
        except (ValueError, TypeError):
            return 0

    @int_property_decorator
    def home_losses(self):
        """Return the home team's losses after the game.

        Returns
        -------
        int
            The number of games the home team has lost, or 0 if not available.
        """
        try:
            _, losses = re.findall(r'\d+', self._home_record)
            return int(losses)
        except (ValueError, TypeError):
            return 0

    @int_property_decorator
    def home_minutes_played(self):
        """Return the total minutes played by the home team.

        Returns
        -------
        int or None
            The total number of minutes played by the home team.
        """
        return self._home_minutes_played

    @int_property_decorator
    def home_field_goals(self):
        """Return the total field goals made by the home team.

        Returns
        -------
        int or None
            The total number of field goals made by the home team.
        """
        return self._home_field_goals

    @int_property_decorator
    def home_field_goal_attempts(self):
        """Return the total field goal attempts by the home team.

        Returns
        -------
        int or None
            The total number of field goal attempts by the home team.
        """
        return self._home_field_goal_attempts

    @float_property_decorator
    def home_field_goal_percentage(self):
        """Return the home team's field goal percentage.

        Returns
        -------
        float or None
            The field goal percentage (0-1) for the home team.
        """
        return self._home_field_goal_percentage

    @int_property_decorator
    def home_three_point_field_goals(self):
        """Return the total three-point field goals made by the home team.

        Returns
        -------
        int or None
            The total number of three-point field goals made by the home team.
        """
        return self._home_three_point_field_goals

    @int_property_decorator
    def home_three_point_field_goal_attempts(self):
        """Return the total three-point field goal attempts by the home team.

        Returns
        -------
        int or None
            The total number of three-point field goal attempts by the home team.
        """
        return self._home_three_point_field_goal_attempts

    @float_property_decorator
    def home_three_point_field_goal_percentage(self):
        """Return the home team's three-point field goal percentage.

        Returns
        -------
        float or None
            The three-point field goal percentage (0-1) for the home team.
        """
        return self._home_three_point_field_goal_percentage

    @int_property_decorator
    def home_two_point_field_goals(self):
        """Return the total two-point field goals made by the home team.

        Returns
        -------
        int or None
            The total number of two-point field goals made by the home team.
        """
        try:
            return self.home_field_goals - self.home_three_point_field_goals
        except TypeError:
            return None

    @int_property_decorator
    def home_two_point_field_goal_attempts(self):
        """Return the total two-point field goal attempts by the home team.

        Returns
        -------
        int or None
            The total number of two-point field goal attempts by the home team.
        """
        try:
            return self.home_field_goal_attempts - self.home_three_point_field_goal_attempts
        except TypeError:
            return None

    @float_property_decorator
    def home_two_point_field_goal_percentage(self):
        """Return the home team's two-point field goal percentage.

        Returns
        -------
        float or None
            The two-point field goal percentage (0-1) for the home team, rounded to three decimal places.
        """
        try:
            return round(float(self.home_two_point_field_goals) / float(self.home_two_point_field_goal_attempts), 3)
        except (TypeError, ZeroDivisionError):
            return None

    @int_property_decorator
    def home_free_throws(self):
        """Return the total free throws made by the home team.

        Returns
        -------
        int or None
            The total number of free throws made by the home team.
        """
        return self._home_free_throws

    @int_property_decorator
    def home_free_throw_attempts(self):
        """Return the total free throw attempts by the home team.

        Returns
        -------
        int or None
            The total number of free throw attempts by the home team.
        """
        return self._home_free_throw_attempts

    @float_property_decorator
    def home_free_throw_percentage(self):
        """Return the home team percentage.

        Returns
        -------
        float or None
            The free throw percentage (0-1) for the home team.
        """
        return self._home_free_throw_percentage

    @int_property_decorator
    def home_offensive_rebounds(self):
        """Return the total offensive rebounds by the home team.

        Returns
        -------
        int or None
            The total number of offensive rebounds by the home team.
        """
        return self._home_offensive_rebounds

    @int_property_decorator
    def home_defensive_rebounds(self):
        """Return the total defensive rebounds by the home team.

        Returns
        -------
        int or None
            The total number of defensive rebounds by the home team.
        """
        return self._home_defensive_rebounds

    @int_property_decorator
    def home_total_rebounds(self):
        """Return the total rebounds by the home team.

        Returns
        -------
        int or None
            The total number of rebounds by the home team.
        """
        return self._home_total_rebounds

    @int_property_decorator
    def home_assists(self):
        """Return the total assists by the home team.

        Returns
        -------
        int or None
            The total number of assists by the home team.
        """
        return self._home_assists

    @int_property_decorator
    def home_steals(self):
        """Return the total steals by the home team.

        Returns
        -------
        int or None
            The total number of steals by the home team.
        """
        return self._home_steals

    @int_property_decorator
    def home_blocks(self):
        """Return the total blocks by the home team.

        Returns
        -------
        int or None
            The total number of blocks by the home team.
        """
        return self._home_blocks

    @int_property_decorator
    def home_turnovers(self):
        """Return the total turnovers by the home team.

        Returns
        -------
        int or None
            The total number of turnovers by the home team.
        """
        return self._home_turnovers

    @int_property_decorator
    def home_personal_fouls(self):
        """Return the total personal fouls by the home team.

        Returns
        -------
        int or None
            The total number of personal fouls by the home team.
        """
        return self._home_personal_fouls

    @int_property_decorator
    def home_points(self):
        """Return the total points scored by the home team.

        Returns
        -------
        int or None
            The number of points scored by the home team
        """
        return self._home_points

    @float_property_decorator
    def home_true_shooting_percentage(self):
        """Return the home team's true shooting percentage.

        Returns
        -------
        float or None
            The true shooting percentage (0-1), considering free throws, 2-point,
            and 3-point field goal.
        """
        return self._home_true_shooting_percentage

    @float_property_decorator
    def home_effective_field_goal_percentage(self):
        """Return the home team?s effective field goal percentage.

        Returns
        -------
        float or None
            The field goal percentage (0-1), weighting 3-point field goals.
        """
        return self._home_effective_field_goal_percentage

    @float_property_decorator
    def home_three_point_attempt_rate(self):
        """Return the home team?s three-point attempt rate.

        Returns
        -------
        float or None
            The percentage of field goal attempts from 3-point range.
        """
        return self._home_three_point_attempt_rate

    @float_property_decorator
    def home_free_throw_attempt_rate(self):
        """Return the home team?s free throw attempt rate.

        Returns
        -------
        float or None
            The average number of free throw attempts per field goal attempt.
        """
        return self._home_free_throw_attempt_rate

    @float_property_decorator
    def home_offensive_rebound_percentage(self):
        """Return the home team?s offensive rebound percentage.

        Returns
        -------
        float or None
            The percentage of available offensive rebounds (0-100).
        """
        return self._home_offensive_rebound_percentage

    @float_property_decorator
    def home_defensive_rebound_percentage(self):
        """Return the home team?s defensive rebound percentage.

        Returns
        -------
        float or None
            The percentage of available defensive rebounds (0-100).
        """
        return self._home_defensive_rebound_percentage

    @float_property_decorator
    def home_total_rebound_percentage(self):
        """Return the home team?s total rebound percentage.

        Returns
        -------
        float or None
            The percentage of available rebounds (0-100).
        """
        return self._home_total_rebound_percentage

    @float_property_decorator
    def home_assist_percentage(self):
        """Return the home team?s assist percentage.

        Returns
        -------
        float or None
            The percentage of field goals that were assisted (0-100).
        """
        return self._home_assist_percentage

    @float_property_decorator
    def home_steal_percentage(self):
        """Return the home team?s steal percentage.

        Returns
        -------
        float or None
            The percentage of possessions that ending in a steal (0-100).
        """
        return self._home_steal_percentage

    @float_property_decorator
    def home_block_percentage(self):
        """Return the home team?s block percentage.

        Returns
        -------
        float or None
            The percentage of 2-point field goals that were blocked (0-100).
        """
        return self._home_block_percentage

    @float_property_decorator
    def home_turnover_percentage(self):
        """Return the home team?s turnover percentage.

        Returns
        -------
        float or None
            The number of turnovers per 100 possessions.
        """
        return self._home_turnover_percentage

    @float_property_decorator
    def home_offensive_rating(self):
        """Return the home team?s offensive rating.

        Returns
        -------
        float or None
            The average points scored per 100 possessions.
        """
        return self._home_offensive_rating

    @float_property_decorator
    def home_defensive_rating(self):
        """Return the home team?s defensive rating.
        Returns
        -------
        float or None
            The average points allowed per 100 possessions.
        """
        return self._home_defensive_rating


class Boxscores:
    """Search for NBA games taking place on a particular day.

    Retrieve a dictionary containing a list of all games being played on a
    particular day.
 Output includes a link to the boxscore, and the names and
    abbreviations for both the home teams. If no games are played on a
    particular day, the list will be empty.

    Parameters
    ----------
    date : datetime
        The date to search for any matches. The month, day, and year are
        required for the search, but time is not factored into the search.
    end_date : datetime or None
        Optionally specify an end date to iterate until. All boxscores starting
        from the date specified in the 'date' parameter up to and including the
        boxscores specified in the 'end_date' parameter will be pulled. If left
        None, only the games from the day specified in the 'date' parameter will be saved.
    """
    def __init__(self, date, end_date=None):
        self._boxscores = {}

        self._find_games(date, end_date)

    def __str__(self):
        """Return the string representation of the class.

        Returns
        -------
        str
            A string listing the dates of the boxscores, e.g., 'NBA games for 01-15-2023'.
        """
        return f"NBA games for {', '.join(self._boxscores.keys())}"

    def __repr__(self):
        """Return the string representation of the class.

        Returns
        -------
        str
            A string listing the dates of the boxscores.
        """
        return self.__str__()

    @property
    def games(self):
        """Return all games played on the requested dates.

        Returns
        -------
        dict
            A dictionary with keys as dates (YYYY-MM-DD) and values as lists of
            game dictionaries containing home and away team details, boxscore URI,
            scores, and winner/loser information.
        """
        return self._boxscores

    def _create_url(self, date):
        """Build the URL for boxscores on a specific date.

        Parameters
        ----------
        date : datetime
            The date to search for boxscores (month, day, year required).

        Returns
        -------
        str
            The URL for the boxscores page for the specified date.
        """
        return BOXSCORES_URL % (date.month, date.day, date.year)

    def _get_requested_page(self, url):
        """Download the requested boxscores page.

        Parameters
        ----------
        url : str
            The URL of the boxscores page.

        Returns
        -------
        BeautifulSoup or None
            A BeautifulSoup object of the page's HTML, or None if the request fails.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except (HTTPError, requests.RequestException):
            return None

    def _get_boxscore_uri(self, link):
        """Extract the boxscore URI from a link.

        Parameters
        ----------
        link : BeautifulSoup object
            A BeautifulSoup object containing the boxscore link.

        Returns
        -------
        str or None
            The boxscore URI, e.g., '201710310LAL', or None if not found.
        """
        if link and link.get('href'):
            return re.sub(r'.*/boxscores/|\.html.*$', '', link['href']).strip()
        return None

    def _parse_abbreviation(self, link):
        """Parse a team's abbreviation from a link.

        Parameters
        ----------
        link : BeautifulSoup object
            A BeautifulSoup object containing the team's link.

        Returns
        -------
        str or None
            The team's abbreviation, e.g., 'POR', or None if not found.
        """
        if link and link.get('href'):
            return re.sub(r'.*/teams/|/\d+\.html$', '', link['href'])
        return None

    def _get_name(self, link):
        """Extract a team's name and abbreviation.

        Parameters
        ----------
        link : BeautifulSoup object
            A BeautifulSoup object containing the team's link.

        Returns
        -------
        tuple
            A tuple of (team_name, team_abbr), or (None, None) if not found.
        """
        if not link:
            return None, None
        team_name = link.text.strip()
        abbr = self._parse_abbreviation(link)
        return team_name, abbr

    def _get_score(self, cell):
        """Extract a team's score from a table cell.

        Parameters
        ----------
        cell : BeautifulSoup object
            A BeautifulSoup object containing the score.

        Returns
        -------
        int or None
            The team's score, or None if not available.
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
            A BeautifulSoup object representing a game row.

        Returns
        -------
        tuple
            A tuple of (away_name, away_abbr, away_score, home_name, home_abbr, home_score).
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
        """Extract the winning or losing team's name and abbreviation.

        Parameters
        ----------
        row : BeautifulSoup object
            A BeautifulSoup object representing the winner or loser row.

        Returns
        -------
        tuple or None
            A tuple of (name, abbreviation), or None if not found.
        """
        link = row.select_one('td a')
        return self._get_name(link) if link else None

    def _extract_game_info(self, games):
        """Parse game information from boxscores.

        Parameters
        ----------
        games : list
            A list of BeautifulSoup objects, each representing a game row.

        Returns
        -------
        list
            A list of dictionaries containing game details.
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
        """Retrieve all games played on the specified date range.

        Parameters
        ----------
        date : datetime
            The start date to search for games.
        end_date : datetime or None
            The end date to search up to, or None to search only the start date.
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