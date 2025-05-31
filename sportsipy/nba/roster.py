import pandas as pd
import re
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.error import HTTPError
from ..base import (int_property_decorator, float_property_decorator, 
                    int_property_decorator_default_zero, most_recent_decorator,
                    _parse_field, _fetch_html, _parse_attribute, _parse_table_dict,
                    _aggregate_table_data, _extract_entity_id, _extract_entity_name,
                    _find_year_for_season, _url_exists, AbstractParser)
from .constants import NATIONALITY, PLAYER_SCHEME, PLAYER_URL, ROSTER_URL
from .player import AbstractPlayer

class Player(AbstractPlayer, AbstractParser):
    """Player information and statistics for all seasons.

    Retrieves and stores comprehensive player data, including personal details
    (name, nationality, height, weight) and season/career statistics (e.g., points,
    rebounds, advanced metrics) for a given player ID from basketball-reference.com.
    By default, returns career stats; call the instance with a season (e.g., '2017-18')
    to access specific season stats.

    Parameters
    ----------
    player_id : str
        The player's ID (e.g., 'hardeja01' for James Harden), typically in the format
        'LLLLLFFNN' where 'LLLLL' are the first 5 letters of the last name, 'FF' are
        the first 2 letters of the first name, and 'NN' is a number starting at '01'.
    """
    def __init__(self, player_id):
        self._most_recent_season = ''
        self._index = 0
        self._player_id = player_id
        self._season = []
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
        AbstractParser.__init__(self, player_data.get('Career', {}).get('data', ''))
        AbstractPlayer.__init__(self, player_id, self._name, player_data)
        if player_data:
            self._season = list(player_data.keys())
            self._find_initial_index()

    def __str__(self):
        """Return the string representation of the player.

        Returns
        -------
        str
            The player's name and ID (e.g., 'James Harden (hardeja01)').
        """
        return f'{self.name} ({self.player_id})'

    def __repr__(self):
        """Return the string representation of the player.

        Returns
        -------
        str
            The player's name and ID (e.g., 'James Harden (hardeja01)').
        """
        return self.__str__()

    def _build_url(self):
        """Build the player's stats page URL.

        Returns
        -------
        str
            The URL for the player's stats page, using the first letter of the player ID.
        """
        return PLAYER_URL % (self._player_id[0], self._player_id)

    def _parse_season(self, row):
        """Parse the season from a stats table row.

        Parameters
        ----------
        row : BeautifulSoup object
            A table row containing stats.

        Returns
        -------
        str
            The season in 'YYYY-YY' format (e.g., '2017-18').
        """
        return _parse_field(PLAYER_SCHEME, row, 'season')

    def _combine_stats(self, stats_dict, season, row_data):
        """Combine stats for a season.

        Parameters
        ----------
        stats_dict : dict
            Dictionary of stats by season.
        season : str
            The season to add stats for.
        row_data : str
            The HTML row data to append.

        Returns
        -------
        dict
            Updated stats dictionary.
        """
        if season in stats_dict:
            stats_dict[season]['data'] += row_data
        else:
            stats_dict[season] = {'data': row_data}
        return stats_dict

    def _pull_player_data(self):
        """Pull and aggregate player data.

        Returns
        -------
        dict
            A dictionary of stats by season, or None if data cannot be retrieved.
        """
        url = self._build_url()
        player_info = _fetch_html(url)
        if not player_info:
            return None
        self._name = _parse_field(PLAYER_SCHEME, player_info, 'name')
        self._height = _parse_field(PLAYER_SCHEME, player_info, 'height')
        self._weight = _parse_field(PLAYER_SCHEME, player_info, 'weight')
        self._nationality = _parse_attribute(player_info, 'span.f-i', mapping=NATIONALITY)
        self._birth_date = _parse_attribute(player_info, 'span[itemprop="birthDate"]', attr='data-birth')
        self._contract = _parse_table_dict(player_info, 'table[id^="contracts_"]')
        table_ids = ['totals', 'per_poss', 'advanced', 'shooting', 'advanced_pbp', 'all_salaries']
        all_stats, self._most_recent_season = _aggregate_table_data(player_info, table_ids, self._parse_season, self._combine_stats)
        return all_stats

    def _find_initial_index(self):
        """Set the index to career stats."""
        try:
            self._index = self._season.index('Career')
        except ValueError:
            self._index = 0

    def __call__(self, requested_season=''):
        """Switch to stats for a specific season.

        Parameters
        ----------
        requested_season : str, optional
            The season to retrieve stats for (e.g., '2017-18'). Defaults to 'Career'.

        Returns
        -------
        Player
            The instance with updated season index.
        """
        season = 'Career' if requested_season.lower() in ('career', '') else requested_season
        try:
            self._index = self._season.index(season)
        except ValueError:
            pass
        return self

    def _dataframe_fields(self):
        """Create a dictionary of fields for DataFrame.

        Returns
        -------
        dict
            A dictionary of attribute names and values for the current season.
        """
        return {
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

    @property
    def dataframe(self):
        """Return a pandas DataFrame of all seasons' statistics.

        Returns
        -------
        pandas.DataFrame
            A DataFrame with stats for each season, indexed by season ID.
        """
        temp_index = self._index
        rows = []
        indices = []
        for season in self._season:
            self._index = self._season.index(season)
            rows.append(self._dataframe_fields())
            indices.append(season)
        self._index = temp_index
        return pd.DataFrame(rows, index=indices)

    @property
    def season(self):
        """Return the current season.

        Returns
        -------
        str
            The season in 'YYYY-YY' format or 'Career'.
        """
        return self._season[self._index] if self._season else ''

    @property
    def team_abbreviation(self):
        """Return the team's abbreviation.

        Returns
        -------
        str or None
            The team's abbreviation (e.g., 'HOU').
        """
        return self._team_abbreviation[self._index] if self._team_abbreviation else None

    @most_recent_decorator
    def position(self):
        """Return the player's primary position.

        Returns
        -------
        str or None
            The player's primary position for the most recent season.
        """
        return self._position

    @property
    def height(self):
        """Return the player's height.

        Returns
        -------
        str or None
            The player's height (e.g., '6-10').
        """
        return self._height

    @property
    def weight(self):
        """Return the player's weight.

        Returns
        -------
        int or None
            The player's weight in pounds.
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
        datetime or None
            The player's birth date.
        """
        try:
            return datetime.strptime(self._birth_date, '%Y-%m-%d')
        except (ValueError, TypeError):
            return None

    @property
    def nationality(self):
        """Return the player's nationality.

        Returns
        -------
        str or None
            The player's country of origin.
        """
        return self._nationality

    @int_property_decorator
    def games_played(self):
        """Return the number of games played.

        Returns
        -------
        int or None
            The number of games played.
        """
        return self._games_played

    @int_property_decorator
    def games_started(self):
        """Return the number of games started.

        Returns
        -------
        int or None
            The number of games started.
        """
        return self._games_started

    @float_property_decorator
    def field_goals_per_poss(self):
        """Return field goals per 100 possessions.

        Returns
        -------
        float or None
            Field goals per 100 possessions.
        """
        return self._field_goals_per_poss

    @float_property_decorator
    def field_goal_attempts_per_poss(self):
        """Return field goal attempts per 100 possessions.

        Returns
        -------
        float or None
            Field goal attempts per 100 possessions.
        """
        return self._field_goal_attempts_per_poss

    @float_property_decorator
    def three_pointers_per_poss(self):
        """Return three-pointers per 100 possessions.

        Returns
        -------
        float or None
            Three-pointers made per 100 possessions.
        """
        return self._three_pointers_per_poss

    @float_property_decorator
    def three_point_attempts_per_poss(self):
        """Return three-point attempts per 100 possessions.

        Returns
        -------
        float or None
            Three-point attempts per 100 possessions.
        """
        return self._three_point_attempts_per_poss

    @int_property_decorator
    def two_pointers(self):
        """Return two-point field goals made.

        Returns
        -------
        int or None
            Two-point field goals made.
        """
        return self._two_pointers

    @int_property_decorator
    def two_point_attempts(self):
        """Return two-point field goal attempts.

        Returns
        -------
        int or None
            Two-point field goal attempts.
        """
        return self._two_point_attempts

    @float_property_decorator
    def two_pointers_per_poss(self):
        """Return two-pointers per 100 possessions.

        Returns
        -------
        float or None
            Two-pointers made per 100 possessions.
        """
        return self._two_pointers_per_poss

    @float_property_decorator
    def two_point_attempts_per_poss(self):
        """Return two-point attempts per 100 possessions.

        Returns
        -------
        float or None
            Two-point attempts per 100 possessions.
        """
        return self._two_point_attempts_per_poss

    @float_property_decorator
    def two_point_percentage(self):
        """Return two-point field goal percentage.

        Returns
        -------
        float or None
            Two-point field goal percentage (0-1).
        """
        return self._two_point_percentage

    @float_property_decorator
    def free_throws_per_poss(self):
        """Return free throws per 100 possessions.

        Returns
        -------
        float or None
            Free throws made per 100 possessions.
        """
        return self._free_throws_per_poss

    @float_property_decorator
    def free_throw_attempts_per_poss(self):
        """Return free throw attempts per 100 possessions.

        Returns
        -------
        float or None
            Free throw attempts per 100 possessions.
        """
        return self._free_throw_attempts_per_poss

    @float_property_decorator
    def offensive_rebounds_per_poss(self):
        """Return offensive rebounds per 100 possessions.

        Returns
        -------
        float or None
            Offensive rebounds per 100 possessions.
        """
        return self._offensive_rebounds_per_poss

    @float_property_decorator
    def defensive_rebounds_per_poss(self):
        """Return defensive rebounds per 100 possessions.

        Returns
        -------
        float or None
            Defensive rebounds per 100 possessions.
        """
        return self._defensive_rebounds_per_poss

    @float_property_decorator
    def total_rebounds_per_poss(self):
        """Return total rebounds per 100 possessions.

        Returns
        -------
        float or None
            Total rebounds per 100 possessions.
        """
        return self._total_rebounds_per_poss

    @float_property_decorator
    def assists_per_poss(self):
        """Return assists per 100 possessions.

        Returns
        -------
        float or None
            Assists per 100 possessions.
        """
        return self._assists_per_poss

    @float_property_decorator
    def steals_per_poss(self):
        """Return steals per 100 possessions.

        Returns
        -------
        float or None
            Steals per 100 possessions.
        """
        return self._steals_per_poss

    @float_property_decorator
    def blocks_per_poss(self):
        """Return blocks per 100 possessions.

        Returns
        -------
        float or None
            Blocks per 100 possessions.
        """
        return self._blocks_per_poss

    @float_property_decorator
    def turnovers_per_poss(self):
        """Return turnovers per 100 possessions.

        Returns
        -------
        float or None
            Turnovers per 100 possessions.
        """
        return self._turnovers_per_poss

    @float_property_decorator
    def personal_fouls_per_poss(self):
        """Return personal fouls per 100 possessions.

        Returns
        -------
        float or None
            Personal fouls per 100 possessions.
        """
        return self._personal_fouls_per_poss

    @float_property_decorator
    def points_per_poss(self):
        """Return points per 100 possessions.

        Returns
        -------
        float or None
            Points per 100 possessions.
        """
        return self._points_per_poss

    @float_property_decorator
    def player_efficiency_rating(self):
        """Return the efficiency rating.

        Returns
        -------
        float or None
            The player's efficiency rating (average is 15).
        """
        return self._player_efficiency_rating

    @float_property_decorator
    def offensive_win_shares(self):
        """Return offensive win shares.

 Moran        Returns
        -------
        float or None
            Wins contributed by offensive plays.
        """
        return self._offensive_win_shares

    @float_property_decorator
    def defensive_win_shares(self):
        """Return defensive win shares.

        Returns
        -------
        float or None
            Wins contributed by defensive plays.
        """
        return self._defensive_win_shares

    @float_property_decorator
    def win_shares(self):
        """Return total win shares.

        Returns
        -------
        float or None
            Total wins contributed by offensive and defensive plays.
        """
        return self._win_shares

    @float_property_decorator
    def win_shares_per_48_minutes(self):
        """Return win shares per 48 minutes.

        Returns
        -------
        float or None
            Wins contributed per 48 minutes (average is 0.100).
        """
        return self._win_shares_per_48_minutes

    @float_property_decorator
    def offensive_box_plus_minus(self):
        """Return offensive box plus/minus.

        Returns
        -------
        float or None
            Offensive points per 100 possessions compared to league average.
        """
        return self._offensive_box_plus_minus

    @float_property_decorator
    def defensive_box_plus_minus(self):
        """Return defensive box plus/minus.

        Returns
        -------
        float or None
            Defensive points per 100 possessions compared to league average.
        """
        return self._defensive_box_plus_minus

    @float_property_decorator
    def value_over_replacement_player(self):
        """Return value over replacement player.

        Returns
        -------
        float or None
            Points per 100 possessions compared to a replacement player, prorated for 82 games.
        """
        return self._value_over_replacement_player

    @float_property_decorator
    def shooting_distance(self):
        """Return average shooting distance.

        Returns
        -------
        float or None
            Average distance of shots in feet.
        """
        return self._shooting_distance

    @float_property_decorator
    def percentage_shots_two_pointers(self):
        """Return percentage of two-point shots.

        Returns
        -------
        float or None
            Percentage of shots that are two-pointers (0-1).
        """
        return self._percentage_shots_two_pointers

    @float_property_decorator
    def percentage_zero_to_three_footers(self):
        """Return percentage of shots from 0-3 feet.

        Returns
        -------
        float or None
            Percentage of shots from 0-3 feet (0-1).
        """
        return self._percentage_zero_to_three_footers

    @float_property_decorator
    def percentage_three_to_ten_footers(self):
        """Return percentage of shots from 3-10 feet.

        Returns
        -------
        float or None
            Percentage of shots from 3-10 feet (0-1).
        """
        return self._percentage_three_to_ten_footers

    @float_property_decorator
    def percentage_ten_to_sixteen_footers(self):
        """Return percentage of shots from 10-16 feet.

        Returns
        -------
        float or None
            Percentage of shots from 10-16 feet (0-1).
        """
        return self._percentage_ten_to_sixteen_footers

    @float_property_decorator
    def percentage_sixteen_foot_plus_two_pointers(self):
        """Return percentage of two-point shots from >16 feet.

        Returns
        -------
        float or None
            Percentage of two-point shots from beyond 16 feet (0-1).
        """
        return self._percentage_sixteen_foot_plus_two_pointers

    @float_property_decorator
    def percentage_shots_three_pointers(self):
        """Return percentage of three-point shots.

        Returns
        -------
        float or None
            Percentage of shots from three-point range (0-1).
        """
        return self._percentage_shots_three_pointers

    @float_property_decorator
    def field_goal_perc_zero_to_three_feet(self):
        """Return field goal percentage from 0-3 feet.

        Returns
        -------
        float or None
            Field goal percentage from 0-3 feet (0-1).
        """
        return self._field_goal_perc_zero_to_three_feet

    @float_property_decorator
    def field_goal_perc_three_to_ten_feet(self):
        """Return field goal percentage from 3-10 feet.

        Returns
        -------
        float or None
            Field goal percentage from 3-10 feet (0-1).
        """
        return self._field_goal_perc_three_to_ten_feet

    @float_property_decorator
    def field_goal_perc_ten_to_sixteen_feet(self):
        """Return field goal percentage from 10-16 feet.

        Returns
        -------
        float or None
            Field goal percentage from 10-16 feet (0-1).
        """
        return self._field_goal_perc_ten_to_sixteen_feet

    @float_property_decorator
    def field_goal_perc_sixteen_foot_plus_two_pointers(self):
        """Return field goal percentage for two-pointers from >16 feet.

        Returns
        -------
        float or None
            Field goal percentage for two-pointers from >16 feet (0-1).
        """
        return self._field_goal_perc_sixteen_foot_plus_two_pointers

    @float_property_decorator
    def two_pointers_assisted_percentage(self):
        """Return percentage of assisted two-pointers.

        Returns
        -------
        float or None
            Percentage of two-pointers that were assisted (0-1).
        """
        return self._two_pointers_assisted_percentage

    @float_property_decorator
    def percentage_field_goals_as_dunks(self):
        """Return percentage of field goals as dunks.

        Returns
        -------
        float or None
            Percentage of field goals that were dunks (0-1).
        """
        return self._percentage_field_goals_as_dunks

    @int_property_decorator
    def dunks(self):
        """Return total dunks.

        Returns
        -------
        int or None
            Total dunks made.
        """
        return self._dunks

    @float_property_decorator
    def three_pointers_assisted_percentage(self):
        """Return percentage of assisted three-pointers.

        Returns
        -------
        float or None
            Percentage of three-pointers that were assisted (0-1).
        """
        return self._three_pointers_assisted_percentage

    @float_property_decorator
    def percentage_of_three_pointers_from_corner(self):
        """Return percentage of corner three-pointers.

        Returns
        -------
        float or None
            Percentage of three-point attempts from the corner (0-1).
        """
        return self._percentage_of_three_pointers_from_corner

    @float_property_decorator
    def three_point_shot_percentage_from_corner(self):
        """Return three-point percentage from the corner.

        Returns
        -------
        float or None
            Three-point percentage from the corner (0-1).
        """
        return self._three_point_shot_percentage_from_corner

    @int_property_decorator
    def half_court_heaves(self):
        """Return half-court shot attempts.

        Returns
        -------
        int or None
            Total half-court shot attempts.
        """
        return self._half_court_heaves

    @int_property_decorator
    def half_court_heaves_made(self):
        """Return half-court shots made.

        Returns
        -------
        int or None
            Total half-court shots made.
        """
        return self._half_court_heaves_made

    @int_property_decorator_default_zero
    def point_guard_percentage(self):
        """Return percentage of time as point guard.

        Returns
        -------
        int
            Percentage of time as point guard (0-100).
        """
        return self._point_guard_percentage

    @int_property_decorator_default_zero
    def shooting_guard_percentage(self):
        """Return percentage of time as shooting guard.

        Returns
        -------
        int
            Percentage of time as shooting guard (0-100).
        """
        return self._shooting_guard_percentage

    @int_property_decorator_default_zero
    def small_forward_percentage(self):
        """Return percentage of time as small forward.

        Returns
        -------
        int
            Percentage of time as small forward (0-100).
        """
        return self._small_forward_percentage

    @int_property_decorator_default_zero
    def power_forward_percentage(self):
        """Return percentage of time as power forward.

        Returns
        -------
        int
            Percentage of time as power forward (0-100).
        """
        return self._power_forward_percentage

    @int_property_decorator_default_zero
    def center_percentage(self):
        """Return percentage of time as center.

        Returns
        -------
        int
            Percentage of time as center (0-100).
        """
        return self._center_percentage

    @float_property_decorator
    def on_court_plus_minus(self):
        """Return on-court plus/minus.

        Returns
        -------
        float or None
            Points contributed per 100 possessions on court.
        """
        return self._on_court_plus_minus

    @float_property_decorator
    def net_plus_minus(self):
        """Return net plus/minus.

        Returns
        -------
        float or None
            Net points per 100 possessions.
        """
        return self._net_plus_minus

    @int_property_decorator
    def passing_turnovers(self):
        """Return passing turnovers.

        Returns
        -------
        int or None
            Total turnovers due to bad passes.
        """
        return self._passing_turnovers

    @int_property_decorator
    def lost_ball_turnovers(self):
        """Return lost-ball turnovers.

        Returns
        -------
        int or None
            Total turnovers due to losing the ball.
        """
        return self._lost_ball_turnovers

    @int_property_decorator
    def other_turnovers(self):
        """Return other turnovers.

        Returns
        -------
        int or None
            Total non-passing/dribbling turnovers.
        """
        return self._other_turnovers

    @int_property_decorator
    def shooting_fouls(self):
        """Return shooting fouls committed.

        Returns
        -------
        int or None
            Total shooting fouls committed.
        """
        return self._shooting_fouls

    @int_property_decorator
    def blocking_fouls(self):
        """Return blocking fouls committed.

        Returns
        -------
        int or None
            Total blocking fouls committed.
        """
        return self._blocking_fouls

    @int_property_decorator
    def offensive_fouls(self):
        """Return offensive fouls committed.

        Returns
        -------
        int or None
            Total offensive fouls committed.
        """
        return self._offensive_fouls

    @int_property_decorator
    def take_fouls(self):
        """Return take-fouls committed.

        Returns
        -------
        int or None
            Total take-fouls committed.
        """
        return self._take_fouls

    @int_property_decorator
    def points_generated_by_assists(self):
        """Return points generated by assists.

        Returns
        -------
        int or None
            Total points from assists.
        """
        return self._points_generated_by_assists

    @int_property_decorator
    def shooting_fouls_drawn(self):
        """Return shooting fouls drawn.

        Returns
        -------
        int or None
            Total shooting fouls drawn.
        """
        return self._shooting_fouls_drawn

    @int_property_decorator
    def and_ones(self):
        """Return and-one plays.

        Returns
        -------
        int or None
            Total and-one plays.
        """
        return self._and_ones

    @int_property_decorator
    def shots_blocked(self):
        """Return shots blocked by opponents.

        Returns
        -------
        int or None
            Total shots blocked.
        """
        return self._shots_blocked

    @int_property_decorator
    def salary(self):
        """Return annual salary.

        Returns
        -------
        int or None
            Annual salary in dollars.
        """
        return self._salary

    @property
    def contract(self):
        """Return contract details.

        Returns
        -------
        dict or None
            Dictionary of seasons to salaries.
        """
        return self._contract

class Roster:
    """Statistics for all players on a team's roster.

    Retrieves player and coach information for a team's roster in a given season.
    Creates `Player` instances for each roster member, or a slim dictionary of
    player IDs and names if specified.

    Parameters
    ----------
    team : str
        The team's 3-letter abbreviation (e.g., 'HOU' for Houston Rockets).
    year : str, optional
        The 4-digit year for the roster (e.g., '2023'). Defaults to the most recent season.
    slim : bool, optional
        If True, returns only player IDs and names, reducing data retrieval time (default is False).
    """
    def __init__(self, team, year=None, slim=False):
        self._team = team.upper()
        self._slim = slim
        self._coach = None
        self._players = {} if slim else []
        self._find_players_with_coach(year)

    def __str__(self):
        """Return the string representation of the roster.

        Returns
        -------
        str
            A newline-separated list of players (name and ID).
        """
        if self._slim:
            players = [f'{name} ({pid})' for pid, name in self._players.items()]
        else:
            players = [f'{player.name} ({player.player_id})' for player in self._players]
        return '\n'.join(players)

    def __repr__(self):
        """Return the string representation of the roster.

        Returns
        -------
        str
            A newline-separated list of players (name and ID).
        """
        return self.__str__()

    def _create_url(self, year):
        """Build the roster URL.

        Parameters
        ----------
        year : str
            The 4-digit year for the roster.

        Returns
        -------
        str
            The URL for the team's roster page.
        """
        return ROSTER_URL % (self._team, year)

    def _parse_coach(self, page):
        """Parse the team's coach.

        Parameters
        ----------
        page : BeautifulSoup object
            The roster page HTML.

        Returns
        -------
        str or None
            The coach's name.
        """
        for p in page.select('p'):
            strong = p.find('strong')
            if strong and strong.text.strip() == 'Coach:':
                a = p.find('a')
                return a.text if a else None
        return None

    def _find_players_with_coach(self, year):
        """Find players and coach for the roster.

        Parameters
        ----------
        year : str, optional
            The year for the roster. Defaults to the most recent season.

        Raises
        ------
        ValueError
            If the team page cannot be retrieved.
        """
        if not year:
            year = _find_year_for_season('nba')
            if year == '2021' and not _url_exists(self._create_url(year)):
                year = str(int(year) - 1)
            elif not _url_exists(self._create_url(year)) and _url_exists(self._create_url(str(int(year) - 1))):
                year = str(int(year) - 1)
        url = self._create_url(year)
        page = _fetch_html(url)
        if not page:
            raise ValueError(f"Cannot retrieve team page: {url}")
        self._coach = self._parse_coach(page)
        for row in page.select('table#roster tbody tr'):
            player_id = _extract_entity_id(row)
            if not player_id:
                continue
            if self._slim:
                name = _extract_entity_name(row)
                self._players[player_id] = name
            else:
                self._players.append(Player(player_id))

    @property
    def players(self):
        """Return the roster of players.

        Returns
        -------
        list or dict
            List of `Player` instances if slim is False, else dictionary of player IDs to names.
        """
        return self._players

    @property
    def coach(self):
        """Return the coach's name.

        Returns
        -------
        str or None
            The coach's name (e.g., 'Mike D'Antoni').
        """
        return self._coach