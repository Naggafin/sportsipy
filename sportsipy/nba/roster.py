import pandas as pd
import re
import requests
from datetime import datetime
from functools import wraps
from lxml.etree import ParserError, XMLSyntaxError
from bs4 import BeautifulSoup
from urllib.error import HTTPError
from .. import utils
from .constants import NATIONALITY, PLAYER_SCHEME, PLAYER_URL, ROSTER_URL
from .player import AbstractPlayer


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


def _int_property_decorator_default_zero(func):
    """Convert a property to an integer, returning 0 if conversion fails.

    Parameters
    ----------
    func : callable
        The function to decorate, which retrieves a property value.

    Returns
    -------
    callable
        A wrapped property that converts the function's output to an integer, defaulting to 0.
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
            return 0
    return wrapper


def _float_property_decorator(func):
    """Convert a property to a float, returning None if conversion fails.

    Parameters
    ----------
    func : callable
        The function to decorate, which retrieves a property value.

    Returns
    -------
    callable
        A wrapped property that converts the function's output to a float.
    """
    @property
    @wraps(func)
    def wrapper(*args):
        index = args[0]._index
        prop = func(*args)
        try:
            value = _cleanup(prop[index])
            return float(value)
        except (TypeError, ValueError):
            return None
    return wrapper


def _most_recent_decorator(func):
    """Return the property value for the most recent season.

    Parameters
    ----------
    func : callable
        The function to decorate, which retrieves a property value.

    Returns
    -------
    callable
        A wrapped property that returns the value for the most recent season.
    """
    @property
    @wraps(func)
    def wrapper(*args):
        season = args[0]._most_recent_season
        seasons = args[0]._season
        index = seasons.index(season)
        prop = func(*args)
        return prop[index]
    return wrapper


class Player(AbstractPlayer):
    """Get player information and stats for all seasons.

    Given a player ID, such as 'hardeja01' for James Harden, capture all
    relevant stats and information like name, nationality, height/weight,
    career three-pointers, last season's offensive rebounds, salary, contract
    amount, and much more.

    By default, the class instance will return the player's career stats, but
    single-season stats can be found by calling the instance with the requested
    season as denoted on basketball-reference.com.

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
    """
    def __init__(self, player_id):
        self._most_recent_season = ''
        self._index = None
        self._player_id = player_id
        self._season = None
        self._name = None
        self._team_abbreviation = None
        self._position = None
        self._height = None
        self._weight = None
        self._birth_date = None
        self._nationality = None
        self._games_played = None
        self._games_started = None
        self._player_efficiency_rating = None
        self._offensive_win_shares = None
        self._defensive_win_shares = None
        self._win_shares = None
        self._win_shares_per_48_minutes = None
        self._offensive_box_plus_minus = None
        self._defensive_box_plus_minus = None
        self._box_plus_minus = None
        self._value_over_replacement_player = None
        self._shooting_distance = None
        self._percentage_shots_two_pointers = None
        self._percentage_zero_to_three_footers = None
        self._percentage_three_to_ten_footers = None
        self._percentage_ten_to_sixteen_footers = None
        self._percentage_sixteen_foot_plus_two_pointers = None
        self._percentage_shots_three_pointers = None
        self._field_goal_perc_zero_to_three_feet = None
        self._field_goal_perc_three_to_ten_feet = None
        self._field_goal_perc_ten_to_sixteen_feet = None
        self._field_goal_perc_sixteen_foot_plus_two_pointers = None
        self._two_pointers_assisted_percentage = None
        self._percentage_field_goals_as_dunks = None
        self._dunks = None
        self._three_pointers_assisted_percentage = None
        self._percentage_of_three_pointers_from_corner = None
        self._three_point_shot_percentage_from_corner = None
        self._half_court_heaves = None
        self._half_court_heaves_made = None
        self._point_guard_percentage = None
        self._shooting_guard_percentage = None
        self._small_forward_percentage = None
        self._power_forward_percentage = None
        self._center_percentage = None
        self._on_court_plus_minus = None
        self._net_plus_minus = None
        self._passing_turnovers = None
        self._lost_ball_turnovers = None
        self._other_turnovers = None
        self._shooting_fouls = None
        self._blocking_fouls = None
        self._offensive_fouls = None
        self._take_fouls = None
        self._points_generated_by_assists = None
        self._shooting_fouls_drawn = None
        self._and_ones = None
        self._shots_blocked = None
        self._salary = None
        self._contract = None
        self._field_goals_per_poss = None
        self._field_goal_attempts_per_poss = None
        self._three_pointers_per_poss = None
        self._three_point_attempts_per_poss = None
        self._two_pointers_per_poss = None
        self._two_point_attempts_per_poss = None
        self._free_throws_per_poss = None
        self._free_throw_attempts_per_poss = None
        self._offensive_rebounds_per_poss = None
        self._defensive_rebounds_per_poss = None
        self._total_rebounds_per_poss = None
        self._assists_per_poss = None
        self._steals_per_poss = None
        self._blocks_per_poss = None
        self._turnovers_per_poss = None
        self._personal_fouls_per_poss = None
        self._points_per_poss = None

        player_data = self._pull_player_data()
        AbstractPlayer.__init__(self, player_id, self._name, player_data)
        if not player_data:
            return
        self._find_initial_index()

    def __str__(self):
        """Return the string representation of the class.

        Returns
        -------
        str
            A string containing the player's name and ID, e.g., 'James Harden (hardeja01)'.
        """
        return f'{self.name} ({self.player_id})'

    def __repr__(self):
        """Return the string representation of the class.

        Returns
        -------
        str
            A string containing the player's name and ID, e.g., 'James Harden (hardeja01)'.
        """
        return self.__str__()

    def _build_url(self):
        """Create the player's URL to pull stats from.

        The player's URL requires the first letter of the player's last name
        followed by the player ID.

        Returns
        -------
        str
            The string URL for the player's stats page.
        """
        first_character = self._player_id[0]
        return PLAYER_URL % (first_character, self._player_id)

    def _retrieve_html_page(self):
        """Download the requested player's stats page.

        Download the requested page and strip all comment tags before
        returning a BeautifulSoup object for parsing the data.

        Returns
        -------
        BeautifulSoup object
            The requested page as a BeautifulSoup object with comment tags removed.
        """
        url = self._build_url()
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(utils._remove_html_comment_tags(response.text), 'html.parser')
            return soup
        except (HTTPError, requests.RequestException):
            return None

    def _parse_season(self, row):
        """Parse the season string from the table.

        The season is generally located in the first column of the stats tables
        and should be parsed to denote which season metrics are being pulled
        from.

        Parameters
        ----------
        row : BeautifulSoup object
            A BeautifulSoup object of a single row in a stats table.

        Returns
        -------
        str
            A string representation of the season in the format 'YYYY-YY', such
            as '2017-18'.
        """
        return utils._parse_field(PLAYER_SCHEME, row, 'season')

    def _combine_season_stats(self, table_rows, career_stats, all_stats_dict):
        """Combine all stats for each season.

        Since all stats are spread across multiple tables, they should
        be combined into a single field which can be used to easily query stats
        at once.

        Parameters
        ----------
        table_rows : list
            A list where each element is a row in a stats table.
        career_stats : list
            A list where each element is a row in the footer of a stats
            table. Career stats are kept in the footer, hence the usage.
        all_stats_dict : dict
            A dictionary of all stats separated by season where each key is the
            season string, such as '2017-18', and the value is a dictionary
            with a 'data' key containing all row data.

        Returns
        -------
        dict
            An updated version of all_stats_dict including metrics from the provided table.
        """
        most_recent_season = self._most_recent_season
        if not table_rows:
            table_rows = []
        for row in table_rows:
            season = self._parse_season(row)
            try:
                all_stats_dict[season]['data'] += str(row)
            except KeyError:
                all_stats_dict[season] = {'data': str(row)}
            most_recent_season = season
        self._most_recent_season = most_recent_season
        if not career_stats:
            return all_stats_dict
        try:
            all_stats_dict['Career']['data'] += str(next(iter(career_stats)))
        except KeyError:
            all_stats_dict['Career'] = {'data': str(next(iter(career_stats)))}
        return all_stats_dict

    def _combine_all_stats(self, player_info):
        """Pull stats from all tables into a single data structure.

        Pull stats from requested tables into a dictionary separated by season
        for easy querying of player stats for each season.

        Parameters
        ----------
        player_info : BeautifulSoup object
            A BeautifulSoup object containing all stats information for the player.

        Returns
        -------
        dict
            A dictionary where stats from each table are combined by season.
        """
        all_stats_dict = {}
        for table_id in ['totals', 'per_poss', 'advanced', 'shooting', 'advanced_pbp', 'all_salaries']:
            table_items = utils._get_stats_table(player_info, f'table#{table_id}')
            career_items = utils._get_stats_table(player_info, f'table#{table_id}', footer=True)
            all_stats_dict = self._combine_season_stats(table_items, career_items, all_stats_dict)
        return all_stats_dict

    def _parse_nationality(self, player_info):
        """Parse the player's nationality.

        The player's nationality is denoted by a flag in the information
        section with a country code. The code is matched to find the player's
        home country and set the '_nationality' attribute.

        Parameters
        ----------
        player_info : BeautifulSoup object
            A BeautifulSoup object containing the HTML from the player's stats page.
        """
        for span in player_info.find_all('span'):
            if 'f-i' in span.get('class', []):
                nationality = span.text
                nationality = NATIONALITY.get(nationality, nationality)
                setattr(self, '_nationality', nationality)
                break

    def _parse_player_information(self, player_info):
        """Parse general player information.

        Parse general player information such as height, weight, and name. The
        attribute for the requested field will be set with the value.

        Parameters
        ----------
        player_info : BeautifulSoup object
            A BeautifulSoup object containing the HTML from the player's stats page.
        """
        for field in ['_height', '_weight', '_name']:
            short_field = str(field)[1:]
            value = utils._parse_field(PLAYER_SCHEME, player_info, short_field)
            setattr(self, field, value)

    def _parse_birth_date(self, player_info):
        """Parse the player's birth date.

        Pull the player's birth date from the player information and set the
        '_birth_date' attribute.

        Parameters
        ----------
        player_info : BeautifulSoup object
            A BeautifulSoup object containing the HTML from the player's stats page.
        """
        span = player_info.find('span', itemprop='birthDate')
        if span:
            date = span.get('data-birth')
            if date:
                setattr(self, '_birth_date', date)

    def _parse_contract_headers(self, table):
        """Parse the years on the contract.

        The years are listed as headers on the contract table. The first header
        contains 'Team' and should not be included in the years.

        Parameters
        ----------
        table : BeautifulSoup object
            A BeautifulSoup object containing the contract table.

        Returns
        -------
        list
            A list where each element is a string denoting the season, such as '2017-18'.
        """
        years = [th.text for th in table.find_all('th')]
        years.remove('Team')
        return years

    def _parse_contract_wages(self, table):
        """Parse the wages on the contract.

        The wages are listed as data points in the contract table. Values not
        starting with a '$' are dropped as they are likely invalid.

        Parameters
        ----------
        table : BeautifulSoup object
            A BeautifulSoup object containing the contract table.

        Returns
        -------
        list
            A list of wages where each element is a string, such as '$40,000,000'.
        """
        wages = [td.text if td.text.startswith('$') else '' for td in table.find_all('td')]
        wages = [w for w in wages if w]
        return wages

    def _combine_contract(self, years, wages):
        """Combine contract wages and years.

        Match wages with years and add to a dictionary representing the player's contract.

        Parameters
        ----------
        years : list
            A list where each element is a string denoting the season, such as '2017-18'.
        wages : list
            A list of wages where each element is a string, such as '$40,000,000'.

        Returns
        -------
        dict
            A dictionary where each key is a season string and each value is the wage string.
        """
        contract = {}
        for i in range(len(years)):
            contract[years[i]] = wages[i]
        return contract

    def _parse_contract(self, player_info):
        """Parse the player's contract.

        If a contract table exists, create a dictionary of wages by season.

        Parameters
        ----------
        player_info : BeautifulSoup object
            A BeautifulSoup object containing the HTML from the player's stats page.
        """
        for table in player_info.find_all('table'):
            id_attr = table.get('id')
            if id_attr and id_attr.startswith('contracts_'):
                years = self._parse_contract_headers(table)
                wages = self._parse_contract_wages(table)
                contract = self._combine_contract(years, wages)
                if not contract:
                    contract = None
                setattr(self, '_contract', contract)
                break

    def _pull_player_data(self):
        """Pull and aggregate all player information.

        Pull the player's HTML stats page and parse unique properties, such as
        height, weight, and position. Combine all stats for all seasons plus
        career stats into a single object.

        Returns
        -------
        dict
            A dictionary of combined stats where each key is a season string
            and the value is the season's stats.
        """
        player_info = self._retrieve_html_page()
        if not player_info:
            return
        self._parse_player_information(player_info)
        self._parse_nationality(player_info)
        self._parse_birth_date(player_info)
        self._parse_contract(player_info)
        all_stats = self._combine_all_stats(player_info)
        setattr(self, '_season', all_stats.keys())
        return all_stats

    def _find_initial_index(self):
        """Find the index of career stats.

        Set the index to the 'Career' element when the Player class is instantiated.
        """
        index = 0
        for season in self._season:
            if season == 'Career':
                self._index = index
                break
            index += 1

    def __call__(self, requested_season=''):
        """Specify a different season to pull stats from.

        Parameters
        ----------
        requested_season : str, optional
            A string of the requested season, such as '2017-18'. If blank or
            'Career', career stats are used. Defaults to ''.

        Returns
        -------
        Player
            The class instance with updated stats reference.
        """
        if requested_season.lower() == 'career' or requested_season == '':
            requested_season = 'Career'
        index = 0
        for season in self._season:
            if season == requested_season:
                self._index = index
                break
            index += 1
        return self

    def _dataframe_fields(self):
        """Create a dictionary of fields for DataFrame.

        Regenerate the dictionary when the index changes to reflect the current
        season's stats.

        Returns
        -------
        dict
            A dictionary where keys are attribute names and values are attribute values
            for the specified index.
        """
        fields_to_include = {
            'and_ones': self.and_ones,
            'assist_percentage': self.assist_percentage,
            'assists': self.assists,
            'assists_per_poss': self.assists_per_poss,
            'block_percentage': self.block_percentage,
            'blocking_fouls': self.blocking_fouls,
            'blocks': self.blocks,
            'blocks_per_poss': self.blocks_per_poss,
            'box_plus_minus': self.box_plus_minus,
            'center_percentage': self.center_percentage,
            'defensive_box_plus_minus': self.defensive_box_plus_minus,
            'defensive_rebound_percentage': self.defensive_rebound_percentage,
            'defensive_rebounds': self.defensive_rebounds,
            'defensive_rebounds_per_poss': self.defensive_rebounds_per_poss,
            'defensive_win_shares': self.defensive_win_shares,
            'dunks': self.dunks,
            'effective_field_goal_percentage': self.effective_field_goal_percentage,
            'field_goal_attempts': self.field_goal_attempts,
            'field_goal_attempts_per_poss': self.field_goal_attempts_per_poss,
            'field_goal_perc_sixteen_foot_plus_two_pointers': self.field_goal_perc_sixteen_foot_plus_two_pointers,
            'field_goal_perc_ten_to_sixteen_feet': self.field_goal_perc_ten_to_sixteen_feet,
            'field_goal_perc_three_to_ten_feet': self.field_goal_perc_three_to_ten_feet,
            'field_goal_perc_zero_to_three_feet': self.field_goal_perc_zero_to_three_feet,
            'field_goal_percentage': self.field_goal_percentage,
            'field_goals': self.field_goals,
            'field_goals_per_poss': self.field_goals_per_poss,
            'free_throw_attempt_rate': self.free_throw_attempt_rate,
            'free_throw_attempts': self.free_throw_attempts,
            'free_throw_attempts_per_poss': self.free_throw_attempts_per_poss,
            'free_throw_percentage': self.free_throw_percentage,
            'free_throws': self.free_throws,
            'free_throws_per_poss': self.free_throws_per_poss,
            'games_played': self.games_played,
            'games_started': self.games_started,
            'half_court_heaves': self.half_court_heaves,
            'half_court_heaves_made': self.half_court_heaves_made,
            'height': self.height,
            'lost_ball_turnovers': self.lost_ball_turnovers,
            'minutes_played': self.minutes_played,
            'nationality': self.nationality,
            'net_plus_minus': self.net_plus_minus,
            'offensive_box_plus_minus': self.offensive_box_plus_minus,
            'offensive_fouls': self.offensive_fouls,
            'offensive_rebound_percentage': self.offensive_rebound_percentage,
            'offensive_rebounds': self.offensive_rebounds,
            'offensive_rebounds_per_poss': self.offensive_rebounds_per_poss,
            'offensive_win_shares': self.offensive_win_shares,
            'on_court_plus_minus': self.on_court_plus_minus,
            'other_turnovers': self.other_turnovers,
            'passing_turnovers': self.passing_turnovers,
            'percentage_field_goals_as_dunks': self.percentage_field_goals_as_dunks,
            'percentage_of_three_pointers_from_corner': self.percentage_of_three_pointers_from_corner,
            'percentage_shots_three_pointers': self.percentage_shots_three_pointers,
            'percentage_shots_two_pointers': self.percentage_shots_two_pointers,
            'percentage_sixteen_foot_plus_two_pointers': self.percentage_sixteen_foot_plus_two_pointers,
            'percentage_ten_to_sixteen_footers': self.percentage_ten_to_sixteen_footers,
            'percentage_three_to_ten_footers': self.percentage_three_to_ten_footers,
            'percentage_zero_to_three_footers': self.percentage_zero_to_three_footers,
            'personal_fouls': self.personal_fouls,
            'personal_fouls_per_poss': self.personal_fouls_per_poss,
            'player_efficiency_rating': self.player_efficiency_rating,
            'player_id': self.player_id,
            'point_guard_percentage': self.point_guard_percentage,
            'points': self.points,
            'points_per_poss': self.points_per_poss,
            'points_generated_by_assists': self.points_generated_by_assists,
            'position': self.position,
            'power_forward_percentage': self.power_forward_percentage,
            'salary': self.salary,
            'shooting_distance': self.shooting_distance,
            'shooting_fouls': self.shooting_fouls,
            'shooting_fouls_drawn': self.shooting_fouls_drawn,
            'shooting_guard_percentage': self.shooting_guard_percentage,
            'shots_blocked': self.shots_blocked,
            'small_forward_percentage': self.small_forward_percentage,
            'steal_percentage': self.steal_percentage,
            'steals': self.steals,
            'steals_per_poss': self.steals_per_poss,
            'take_fouls': self.take_fouls,
            'team_abbreviation': self.team_abbreviation,
            'three_point_attempt_rate': self.three_point_attempt_rate,
            'three_point_attempts': self.three_point_attempts,
            'three_point_attempts_per_poss': self.three_point_attempts_per_poss,
            'three_point_percentage': self.three_point_percentage,
            'three_point_shot_percentage_from_corner': self.three_point_shot_percentage_from_corner,
            'three_pointers': self.three_pointers,
            'three_pointers_assisted_percentage': self.three_pointers_assisted_percentage,
            'three_pointers_per_poss': self.three_pointers_per_poss,
            'total_rebound_percentage': self.total_rebound_percentage,
            'total_rebounds': self.total_rebounds,
            'total_rebounds_per_poss': self.total_rebounds_per_poss,
            'true_shooting_percentage': self.true_shooting_percentage,
            'turnover_percentage': self.turnover_percentage,
            'turnovers': self.turnovers,
            'turnovers_per_poss': self.turnovers_per_poss,
            'two_point_attempts': self.two_point_attempts,
            'two_point_attempts_per_poss': self.two_point_attempts_per_poss,
            'two_point_percentage': self.two_point_percentage,
            'two_pointers': self.two_pointers,
            'two_pointers_per_poss': self.two_pointers_per_poss,
            'two_pointers_assisted_percentage': self.two_pointers_assisted_percentage,
            'usage_percentage': self.usage_percentage,
            'value_over_replacement_player': self.value_over_replacement_player,
            'weight': self.weight,
            'win_shares': self.win_shares,
            'win_shares_per_48_minutes': self.win_shares_per_48_minutes
        }
        return fields_to_include

    @property
    def dataframe(self):
        """Return a pandas DataFrame of all seasons' stats.

        Returns
        -------
        pandas.DataFrame
            A DataFrame containing all class properties where each index is a
            different season plus career stats.
        """
        temp_index = self._index
        rows = []
        indices = []
        for season in self._season:
            self._index = self._season.index(season)
            rows.append(self._dataframe_fields())
            indices.append(season)
        self._index = temp_index
        return pd.DataFrame(rows, index=[indices])

    @property
    def season(self):
        """Return the current season string.

        Returns
        -------
        str
            The season in 'YYYY-YY' format, such as '2017-18', or 'Career' if
            no season is specified.
        """
        return self._season[self._index]

    @property
    def team_abbreviation(self):
        """Return the team's abbreviation.

        Returns
        -------
        str
            The abbreviation for the team the player plays for, e.g., 'HOU' for Houston Rockets.
        """
        return self._team_abbreviation[self._index]

    @_most_recent_decorator
    def position(self):
        """Return the player's primary position.

        Returns
        -------
        str
            A constant representing the player's primary position for the most recent season.
        """
        return self._position

    @property
    def height(self):
        """Return the player's height.

        Returns
        -------
        str
            The player's height in the format 'feet-inches'.
        """
        return self._height

    @property
    def weight(self):
        """Return the player's weight.

        Returns
        -------
        int or None
            The player's weight in pounds, or None if not available.
        """
        try:
            return int(self._weight.replace('lb', ''))
        except (ValueError, AttributeError):
            return None

    @property
    def birth_date(self):
        """Return the player's birth date.

        Returns
        -------
        datetime
            A datetime object of the player's birth date.
        """
        return datetime.strptime(self._birth_date, '%Y-%m-%d')

    @property
    def nationality(self):
        """Return the player's nationality.

        Returns
        -------
        str
            A constant denoting the player's country of origin.
        """
        return self._nationality

    @_int_property_decorator
    def games_played(self):
        """Return the number of games played.

        Returns
        -------
        int
            The number of games the player participated in.
        """
        return self._games_played

    @_int_property_decorator
    def games_started(self):
        """Return the number of games started.

        Returns
        -------
        int
            The number of games the player started.
        """
        return self._games_started

    @_float_property_decorator
    def field_goals_per_poss(self):
        """Return field goals per 100 possessions.

        Returns
        -------
        float
            The total number of field goals scored per 100 possessions.
        """
        return self._field_goals_per_poss

    @_float_property_decorator
    def field_goal_attempts_per_poss(self):
        """Return field goal attempts per 100 possessions.

        Returns
        -------
        float
            The total number of field goals attempted per 100 possessions.
        """
        return self._field_goal_attempts_per_poss

    @_float_property_decorator
    def three_pointers_per_poss(self):
        """Return three-pointers made per 100 possessions.

        Returns
        -------
        float
            The total number of three-point field goals made per 100 possessions.
        """
        return self._three_pointers_per_poss

    @_float_property_decorator
    def three_point_attempts_per_poss(self):
        """Return three-point attempts per 100 possessions.

        Returns
        -------
        float
            The total number of three-point field goals attempted per 100 possessions.
        """
        return self._three_point_attempts_per_poss

    @_int_property_decorator
    def two_pointers(self):
        """Return total two-point field goals made.

        Returns
        -------
        int
            The total number of two-point field goals made.
        """
        return self._two_pointers

    @_int_property_decorator
    def two_point_attempts(self):
        """Return total two-point field goal attempts.

        Returns
        -------
        int
            The total number of two-point field goals attempted.
        """
        return self._two_point_attempts

    @_float_property_decorator
    def two_pointers_per_poss(self):
        """Return two-point field goals per 100 possessions.

        Returns
        -------
        float
            The total number of two-point field goals made per 100 possessions.
        """
        return self._two_pointers_per_poss

    @_float_property_decorator
    def two_point_attempts_per_poss(self):
        """Return two-point attempts per 100 possessions.

        Returns
        -------
        float
            The total number of two-point field goals attempted per 100 possessions.
        """
        return self._two_point_attempts_per_poss

    @_float_property_decorator
    def two_point_percentage(self):
        """Return two-point field goal percentage.

        Returns
        -------
        float
            The player's two-point field goal percentage (0-1).
        """
        return self._two_point_percentage

    @_float_property_decorator
    def free_throws_per_poss(self):
        """Return free throws made per 100 possessions.

        Returns
        -------
        float
            The total number of free throws made per 100 possessions.
        """
        return self._free_throws_per_poss

    @_float_property_decorator
    def free_throw_attempts_per_poss(self):
        """Return free throw attempts per 100 possessions.

        Returns
        -------
        float
            The total number of free throws attempted per 100 possessions.
        """
        return self._free_throw_attempts_per_poss

    @_float_property_decorator
    def offensive_rebounds_per_poss(self):
        """Return offensive rebounds per 100 possessions.

        Returns
        -------
        float
            The total number of offensive rebounds grabbed per 100 possessions.
        """
        return self._offensive_rebounds_per_poss

    @_float_property_decorator
    def defensive_rebounds_per_poss(self):
        """Return defensive rebounds per 100 possessions.

        Returns
        -------
        float
            The total number of defensive rebounds grabbed per 100 possessions.
        """
        return self._defensive_rebounds_per_poss

    @_float_property_decorator
    def total_rebounds_per_poss(self):
        """Return total rebounds per 100 possessions.

        Returns
        -------
        float
            The total number of rebounds (offensive + defensive) per 100 possessions.
        """
        return self._total_rebounds_per_poss

    @_float_property_decorator
    def assists_per_poss(self):
        """Return assists per 100 possessions.

        Returns
        -------
        float
            The total number of assists tallied per 100 possessions.
        """
        return self._assists_per_per_poss

    @_float_property_decorator
    def steals_per_poss(self):
        """Return steals per 100 possessions.

        Returns
        -------
        float
            The total number of steals per 100 possessions.
        """
        return self._steals_per_poss

    @_float_property_decorator
    def blocks_per_poss(self):
        """Return blocks per 100 possessions.

        Returns
        -------
        float
            The total number of shots blocked per 100 possessions.
        """
        return self._blocks_per_poss

    @_float_property_decorator
    def turnovers_per_poss(self):
        """Return turnovers per 100 possessions.

        Returns
        -------
        float
            The total number of turnovers per 100 possessions.
        """
        return self._turnovers_per_poss

    @_float_property_decorator
    def personal_fouls_per_poss(self):
        """Return personal fouls per 100 possessions.

        Returns
        -------
        float
            The total number of personal fouls committed per 100 possessions.
        """
        return self._personal_fouls_per_poss

    @_float_property_decorator
    def points_per_poss):
        """Return points scored per 100 possessions.

        Returns
        -------
        float
            The total number of points scored per 100 possessions.
        """
        return self._points_per_poss

    @_float_property_decorator
    def player_efficiency_rating(self):
        """Return the player's efficiency rating.

        Returns
        -------
        float
            The player's efficiency rating, where an average player has a rating of 15.
        """
        return self._player_efficiency_rating

    @_float_property_decorator
    def offensive_win_shares(self):
        """Return offensive win shares.

        Returns
        -------
        float
            The number of wins contributed to the team due to offensive plays.
        """
        return self._offensive_win_shares

    @_float_property_decorator
    def defensive_win_shares(self):
        """Return defensive win shares.

        Returns
        -------
        float
            The number of wins contributed to the team due to defensive plays.
        """
        return self._defensive_win_shares

    @_float_property_decorator
    def win_shares(self):
        """Return total win shares.

        Returns
        -------
        float
            The total number of wins contributed by offensive and defensive plays.
        """
        return self._win_shares

    @_float_property_decorator
    def win_shares_per_48_minutes(self):
        """Return win shares per 48 minutes.

        Returns
        -------
        float
            The number of wins contributed per 48 minutes (average is 0.100).
        """
        return self._win_shares_per_48_minutes

    @_float_property_decorator
    def offensive_box_plus_minus(self):
        """Return offensive box plus/minus.

        Returns
        -------
        float
            The number of offensive points per 100 possessions compared to an average league player.
        """
        return self._offensive_box_plus_minus

    @_float_property_decorator
    def defensive_box_plus_minus(self):
        """Return defensive box plus minus.

        Returns
        -------
        float
            The number of defensive points per 100 possessions compared to an average league player.
        """
        return self._defensive_box_plus_minus

    @_float_property_decorator
    def value_over_replacement_player(self):
        """Return value over replacement player.

        Returns
        -------
        float
            The total points per 100 possessions compared to a replacement-level player (-2.0), prorated for 82 games.
        """
        return self._value_over_replacement_player

    @_float_property_decorator
    def shooting_distance(self):
        """Return average shooting distance.

        Returns
        -------
        float
            The average distance of shots taken in feet.
        """
        return self._shooting_distance

    @_float_property_decorator
    def percentage_shots_two_pointers(self):
        """Return percentage of shots that are two-pointers.

        Returns
        -------
        float
            The percentage of shots taken that are two-pointers (0-1).
        """
        return self._percentage_shots_two_pointers

    @_float_property_decorator
    def percentage_zero_to_three_footers(self):
        """Return percentage of shots from 0-3 feet.

        Returns
        -------
        float
            The percentage of shots taken from zero to three feet (0-1).
        """
        return self._percentage_zero_to_three_footers

    @_float_property_decorator
    def percentage_three_to_ten_footers(self):
        """Return percentage of shots from 3-10 feet.

        Returns
        -------
        float
            The percentage of shots taken from three to ten feet (0-1).
        """
        return self._percentage_three_to_ten_footers

    @_float_property_decorator
    def percentage_ten_to_sixteen_footers(self):
        """Return percentage of shots from 10-16 feet.

        Returns
        -------
        float
            The percentage of shots taken from ten to sixteen feet (0-1).
        """
        return self._percentage_ten_to_sixteen_footers

    @_float_property_decorator
    def percentage_sixteen_foot_plus_two_pointers(self):
        """Return percentage of shots from >16 feet (two-pointers).

        Returns
        -------
        float
            The percentage of two-point shots from beyond sixteen feet (0-1).
        """
        return self._percentage_sixteen_foot_plus_two_pointers

    @_float_property_decorator
    def percentage_shots_three_pointers(self):
        """Return percentage of shots that are three-pointers.

        Returns
        -------
        float
            The percentage of shots taken from beyond the three-point line (0-1).
        """
        return self._percentage_shots_three_pointers

    @_float_property_decorator
    def field_goal_percentage_zero_to_three_feet(self):
        """Return field goal percentage from 0-3 feet.

        Returns
        -------
        float
            The field goal percentage for shots from 0-3 feet (0-1).
        """
        return self._field_goal_percentage_zero_to_three_feet

    @_float_property_decorator
    def field_goal_percentage_three_to_ten_feet(self):
        """Return field goal percentage from 3-10 feet.

        Returns
        -------
        float
            The field goal percentage for shots from 3-10 feet (0-1).
        """
        return self._field_goal_percentage_three_to_ten_feet

    @_float_property_decorator
    def field_goal_percentage_ten_to_sixteen_feet(self):
        """Return field goal percentage from 10-16 feet.

        Returns
        -------
        float
            The field goal percentage for shots from 10-16 feet (0-1).
        """
        return self._field_goal_percentage_ten_to_sixteen_feet

    @_float_property_decorator
    def field_goal_percentage_sixteen_foot_plus_two_pointers(self):
        """Return field goal percentage for two-pointers from >16 feet.

        Returns
        -------
        float
            The field goal percentage for two-point shots from beyond 16 feet (0-1).
        """
        return self._field_goal_percentage_sixteen_to_two_pointers

    @_float_property_decorator
    def two_pointers_assisted_percentage(self):
        """Return percentage of assisted two-point field goals.

        Returns
        -------
        float
            The percentage of two-point field goals that were assisted (0-1).
        """
        return self._two_pointers_assisted_percentage

    @_float_property_decorator
    def percentage_field_goals_dunks(self):
        """Return percentage of field goals that are dunks.

        Returns
        -------
        float
            The percentage of shot attempts that were dunks (0-1).
        """
        return self._percentage_field_goals_dunks

    @_int_property_decorator
    def dunks(self):
        """Return total number of dunks.

        Returns
        -------
        int
            The total number of dunks made during the season.
        """
        return self._dunks

    @_float_property_decorator
    def three_pointers_assisted_percentage(self):
        """Return percentage of assisted three-point field goals.

        Returns
        -------
        float
            The percentage of three-point field goals that were assisted (0-1).
        """
        return self._three_pointers_assisted_percentage

    @_float_property_decorator
    def percentage_three_pointers_from_corner(self):
        """Return percentage of three-point shots from the corner.

        Returns
        -------
        float
            The percentage of three-point attempts from the corner (0-1).
        """
        return self._percentage_of_three_pointers_from_corner

    @_float_property_decorator
    def three_point_percentage_from_corner(self):
        """Return three-point percentage from the corner.

        Returns
        -------
        float
            The percentage of corner three-point shots made (0-1).
        """
        return self._three_point_percentage_from_corner

    @_int_property_decorator
    def half_court_heaves(self):
        """Return number of half-court shots attempted.

        Returns
        -------
        int
            The total number of shots taken from beyond mid-court.
        """
        return self._half_court_heaves

    @_int_property_decorator
    def half_court_made(self):
        """Return number of half-court shots made.

        Returns
        -------
        int
            The number of shots made from beyond mid-court.
        """
        return self._half_court_heaves_made

    @_int_property_decorator_default_zero
    def point_guard_percentage(self):
        """Return percentage of time spent as point guard.

        Returns
        -------
        int
            The percentage of time spent as a point guard (0-100).
        """
        return self._point_guard_percentage

    @_int_property_decorator_default_zero
    def shooting_guard_percentage(self):
        """Return percentage of time spent as shooting guard.

        Returns
        -------
        int
            The percentage of time spent as a shooting guard (0-100).
        """
        return self._shooting_guard_percentage

    @_int_property_decorator_default_zero
    def small_forward_percentage(self):
        """Return percentage of time spent as small forward.

        Returns
        -------
        int
            The percentage of time spent as a small forward (0-100).
        """
        return self._small_forward_percentage

    @_int_property_decorator_default_zero
    def power_forward_percentage(self):
        """Return percentage of time spent as power forward.

        Returns
        -------
        int
            The percentage of time spent as a power forward (0-100).
        """
        return self._power_forward_percentage

    @_int_property_decorator_default_zero
    def center_percentage(self):
        """Return percentage of time spent as center.

        Returns
        -------
        int
            The percentage of time spent as a center (0-100).
        """
        return self._center_percentage

    @_float_property_decorator
    def on_court_plus_minus(self):
        """Return points contributed per 100 possessions on court.

        Returns
        -------
        float
            The number of points contributed per 100 possessions while on the court.
        """
        return self._on_court_plus_minus

    @_float_property_decorator
    def net_plus_minus(self):
        """Return net points contributed per 100 possessions.

        Returns
        -------
        float
            The net points per 100 possessions, on or off the court.
        """
        return self._net_plus_minus

    @_int_property_decorator
    def passing_turnovers(self):
        """Return total number of passing turnovers.

        Returns
        -------
        int
            The total number of turnovers due to bad passes.
        """
        return self._passing_turnovers

    @_int_property_decorator
    def lost_ball_turnovers(self):
        """Return total number of lost-ball turnovers.

        Returns
        -------
        int
            The total number of turnovers due to losing the ball.
        """
        return self._lost_ball_turnovers

    @_int_property_decorator
    def other_turnovers(self):
        """Return total number of other turnovers.

        Returns
        -------
        int
            The total number of non-passing/dribbling turnovers.
        """
        return self._other_turnovers

    @_int_property_decorator
    def shooting_fouls(self):
        """Return total number of shooting fouls committed.

        Returns
        -------
        int
            The total number of shooting fouls committed.
        """
        return self._shooting_fouls

    @_int_property_decorator
    def blocking_fouls(self):
        """Return total number of blocking fouls committed.

        Returns
        -------
        int
            The total number of blocking fouls committed.
        """
        return self._blocking_fouls

    @_int_property_decorator
    def offensive_fouls(self):
        """Return total number of offensive fouls committed.

        Returns
        -------
        int
            The total number of offensive fouls committed.
        """
        return self._offensive_fouls

    @_int_property_decorator
    def take_fouls(self):
        """Return total number of take-fouls committed.

        Returns
        -------
        int
            The total number of take-fouls committed to stop a shooting motion.
        """
        return self._take_fouls

    @_int_property_decorator
    def points_generated_by_assists(self):
        """Return points generated by assists.

        Returns
        -------
        int
            Total points generated from the player's assists.
        """
        return self._points_generated_by_assists

    @_int_property_decorator shooting_fouls_drawn(self):
        """Return number of shooting fouls drawn.

        Returns
        -------
        int
            The total number of shooting fouls drawn during the season.
        """
        return self._shooting_fouls_drawn

    @_int_property_decorator
    def and_ones(self):
        """Return number of and-one plays.

        Returns
        -------
        int
            The total number of times fouled while making a basket.
        """
        return self._and_ones

    @_int_property_decorator
    def shots_blocked(self):
        """Return number of shots blocked by opponents.

        Returns
        -------
        int
            The total number of shots taken that were blocked.
        """
        return self._shots_blocked

    @_int_property_decorator
    def salary(self):
        """Return the player's annual salary.

        Returns
        -------
        int
            The player's annual salary, rounded down.
        """
        return self._salary

    @property
    def contract(self):
        """Return the player's contract details.

        Returns
        -------
        dict
            A dictionary where keys are season strings (e.g., '2018-19') and
            values are salary strings (e.g., '$40,000,000').
        """
        return self._contract


class Roster:
    """Get stats for all players on a roster.

    Request a team's roster for a given season and create instances of the
    Player class for each player, containing a detailed list of the players
    statistics and information.

    Parameters
    ----------
    team : str
        The team's 3-letter abbreviation, such as 'HOU' for the Houston Rockets.
    year : str, optional
        The 4-digit year to pull the roster from, such as '2023'. If blank,
        defaults to the most recent season.
    slim : bool, optional
        If True, returns a limited subset of player information (name and ID)
        instead of full stats, reducing response time. Defaults to False.
    """
    def __init__(self, team, year=None, slim=False):
        self._team = team
        self._slim = slim
        self._coach = None
        if slim:
            self._players = {}
        else:
            self._players = []
        self._find_players_with_coach(year)

    def __str__(self):
        """Return the string representation of the roster.

        Returns
        -------
        str
            A string listing each player with name and ID, one per line.
        """
        players = [f'{player.name} ({player.player_id})'.strip() for player in self._players]
        return '\n'.join(players)

    def __repr__(self):
        """Return the string representation of the roster.

        Returns
        -------
        str
            A string listing each player with name and ID, one per line.
        """
        return self.__str__()

    def _pull_team_page(self, url):
        """Download the team page.

        Download the requested team's season page and create a BeautifulSoup object.

        Parameters
        ----------
        url : str
            The URL for the requested team and season.

        Returns
        -------
        BeautifulSoup
            BeautifulSoup object of the team's HTML page.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except (HTTPError, requests.RequestException):
            return None

    def _create_url(self, year):
        """Build the team URL.

        Parameters
        ----------
        year : str
            The 4-digit string representing the year to pull the roster from.

        Returns
        -------
        str
            The URL for the team's season page.
        """
        return ROSTER_URL % (self._team.upper(), year)

    def _get_id(self, player):
        """Parse the player ID.

        Parameters
        ----------
        player : BeautifulSoup object
            A BeautifulSoup object representing player information from the roster table.

        Returns
        -------
        str
            The player's ID.
        """
        name_tag = player.find('td', {'data-stat': 'player'}).find('a')
        if name_tag:
            href = name_tag.get('href')
            return re.sub(r'.*/players/./|././html.*$', '', href)
        return ''

    def _get_name(self, player):
        """Parse the player's name.

        Parameters
        ----------
        player : BeautifulSoup object
            A BeautifulSoup object representing player information from the roster table.

        Returns
        -------
        str
            The player's name.
        """
        name_tag = player.find('td', {'data-stat': 'player'}).find('a')
        return name_tag.text if name_tag else ''

    def _parse_coach(self, page):
        """Parse the team's coach.

        Parameters
        ----------
        page : BeautifulSoup object
            A BeautifulSoup object representing the team's roster page.

        Returns
        -------
        str
            The coach's name.
        """
        for p in page.find_all('p'):
            strong = p.find('strong')
            if strong and strong.text.strip() == 'Coach:':
                a = p.find('a')
                return a.text if a else None
        return None

    def _find_players_with_coach(self, year):
        """Find all player IDs and coach for the team.

        Pull the roster table, parse player IDs, and create Player instances for
        each roster member. Set the coach attribute.

        Parameters
        ----------
        year : str
            The year to pull the team's roster from.
        """
        if not year:
            year = utils._find_year_for_season('nba')
            if year == 2021:
                try:
                    response = requests.get(self._create_url(year))
                    response.raise_for_status()
                except (HTTPError, requests.RequestException):
                    year = str(int(year) - 1)
            if not utils._url_exists(self._create_url(year)) and utils._url_exists(self._create_url(str(int(year) - 1))):
                year = str(int(year) - 1)
        url = self._create_url(year)
        page = self._pull_team_page(url)
        if not page:
            raise ValueError(f"Can't pull requested team page. Ensure the following URL exists: {url}")
        players = page.select('table#roster tbody tr')
        for player in players:
            player_id = self._get_id(player)
            if not player_id or player_id == '':
                continue
            if self._slim:
                name = self._get_name(player)
                self._players[player_id] = name
            else:
                player_instance = Player(player_id)
                self._players.append(player_instance)
        self._coach = self._parse_coach(page)

    @property
    def players(self):
        """Return the roster of players.

        Returns
        -------
        list or dict
            A list of Player instances if slim is False, or a dictionary of
            player IDs mapped to names if slim is True.
        """
        return self._players

    @property
    def coach(self):
        """Return the coach's name.

        Returns
        -------
        str
            The coach's name, e.g., "Mike D'Antoni".
        """
        return self._coach