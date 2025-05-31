import pandas as pd
from ..base import AbstractParser, int_property_decorator, float_property_decorator, _parse_field, _clean_stat
from .constants import PLAYER_SCHEME

class AbstractPlayer(AbstractParser):
    """Base class for NFL player statistics.

    Provides a framework for capturing player stats (e.g., passing, rushing, receiving)
    from pro-football-reference.com. Subclasses should implement data retrieval and
    parsing logic. Supports career and single-season stats via instance calls.

    Parameters
    ----------
    player_id : str
        The player's ID (e.g., 'BreeDr00' for Drew Brees), typically in the format
        'LlllFfNN' where 'Llll' is the first four letters of the last name,
        'Ff' is the first two letters of the first name, and 'NN' is a numeric suffix.
    player_name : str
        The player's full name (e.g., 'Drew Brees').
    player_data : str or dict
        HTML data for the player's stats. If a string, represents a single game's stats
        (e.g., from a boxscore). If a dict, maps seasons to HTML data for career stats.

    Attributes
    ----------
    player_id : str
        The player's unique ID.
    name : str
        The player's full name.
    """
    def __init__(self, player_id, player_name, player_data):
        self._player_id = player_id
        self._name = player_name
        # Passing-specific stats
        self._completed_passes = []
        self._attempted_passes = []
        self._passing_yards = []
        self._passing_touchdowns = []
        self._interceptions_thrown = []
        self._longest_pass = []
        self._quarterback_rating = []
        self._times_sacked = []
        # Rushing-specific stats
        self._rush_attempts = []
        self._rush_yards = []
        self._rush_touchdowns = []
        self._longest_rush = []
        # Receiving-specific stats
        self._times_pass_target = []
        self._receptions = []
        self._receiving_yards = []
        self._receiving_yards_per_reception = []
        self._receiving_touchdowns = []
        self._longest_reception = []
        # Combined receiving and rushing stats
        self._fumbles = []
        # Punt/Kick return stats
        self._punt_returns = []
        self._punt_return_yards = []
        self._punt_return_touchdown = []
        self._longest_punt_return = []
        self._yards_per_punt_return = []
        self._kickoff_returns = []
        self._kickoff_return_yards = []
        self._kickoff_return_touchdown = []
        self._longest_kickoff_return = []
        # Kicking-specific stats
        self._field_goals_attempted = []
        self._field_goals_made = []
        self._extra_points_attempted = []
        self._extra_points_made = []
        # Punting-specific stats
        self._punts = []
        self._total_punt_yards = []
        self._longest_punt = []
        self._yards_per_punt = []
        # Defensive-specific stats
        self._interceptions = []
        self._yards_returned_from_interception = []
        self._interceptions_returned_for_touchdown = []
        self._longest_interception_return = []
        self._passes_defended = []
        self._fumbles_forced = []
        self._fumbles_recovered = []
        self._yards_recovered_from_fumble = []
        self._fumbles_recovered_for_touchdown = []
        self._sacks = []
        self._assists_on_tackles = []
        AbstractParser.__init__(self)
        self._parse_player_data(player_data)

    def _parse_value(self, stats, field):
        """Parse a specific field from HTML stats.

        Parameters
        ----------
        stats : BeautifulSoup
            Parsed HTML containing player stats.
        field : str
            The field to extract (e.g., 'passing_yards').

        Returns
        -------
        str
            The parsed value, cleaned of unwanted characters.
        """
        return _clean_stat(_parse_field(PLAYER_SCHEME, stats, field))

    def _parse_player_data(self, player_data):
        """Parse player stats from HTML data.

        Iterates through attributes to extract stats from the provided HTML data,
        storing them in lists for each season or game.

        Parameters
        ----------
        player_data : str or dict
            If a string, HTML stats for a single game. If a dict, maps seasons
            (e.g., '2023') to HTML stats for career data.

        Raises
        ------
        ValueError
            If player_data is invalid or cannot be parsed.
        """
        for field in self.__dict__:
            if not field.startswith('_') or field in ['_player_id', '_name']:
                continue
            short_field = field.lstrip('_')
            field_stats = []
            if isinstance(player_data, dict):
                for year, data in player_data.items():
                    if not data:
                        field_stats.append(None)
                        continue
                    from bs4 import BeautifulSoup
                    stats = BeautifulSoup(data['data'], 'html.parser')
                    value = self._parse_value(stats, short_field)
                    field_stats.append(value)
            else:
                from bs4 import BeautifulSoup
                stats = BeautifulSoup(player_data, 'html.parser')
                value = self._parse_value(stats, short_field)
                field_stats.append(value)
            setattr(self, field, field_stats)

    @property
    def player_id(self):
        """Return the player's ID.

        Returns
        -------
        str
            Player ID (e.g., 'BreeDr00').
        """
        return self._player_id

    @property
    def name(self):
        """Return the player's name.

        Returns
        -------
        str
            Full name (e.g., 'Drew Brees').
        """
        return self._name

    @int_property_decorator
    def completed_passes(self):
        """Return the number of completed passes.

        Returns
        -------
        int or None
            Number of passes completed.
        """
        return self._completed_passes

    @int_property_decorator
    def attempted_passes(self):
        """Return the number of attempted passes.

        Returns
        -------
        int or None
            Number of passes attempted.
        """
        return self._attempted_passes

    @int_property_decorator
    def passing_yards(self):
        """Return the passing yards.

        Returns
        -------
        int or None
            Total yards from completed passes.
        """
        return self._passing_yards

    @int_property_decorator
    def passing_touchdowns(self):
        """Return the passing touchdowns.

        Returns
        -------
        int or None
            Number of touchdown passes.
        """
        return self._passing_touchdowns

    @int_property_decorator
    def interceptions_thrown(self):
        """Return the number of interceptions thrown.

        Returns
        -------
        int or None
            Number of interceptions.
        """
        return self._interceptions_thrown

    @int_property_decorator
    def longest_pass(self):
        """Return the longest pass.

        Returns
        -------
        int or None
            Yards of the longest completed pass.
        """
        return self._longest_pass

    @float_property_decorator
    def quarterback_rating(self):
        """Return the quarterback rating.

        Returns
        -------
        float or None
            Quarterback rating score.
        """
        return self._quarterback_rating

    @int_property_decorator
    def times_sacked(self):
        """Return the number of times sacked.

        Returns
        -------
        int or None
            Number of sacks as a quarterback.
        """
        return self._times_sacked

    @int_property_decorator
    def rush_attempts(self):
        """Return the number of rush attempts.

        Returns
        -------
        int or None
            Number of rushing plays attempted.
        """
        return self._rush_attempts

    @int_property_decorator
    def rush_yards(self):
        """Return the rushing yards.

        Returns
        -------
        int or None
            Total rushing yards.
        """
        return self._rush_yards

    @int_property_decorator
    def rush_touchdowns(self):
        """Return the rushing touchdowns.

        Returns
        -------
        int or None
            Number of rushing touchdowns.
        """
        return self._rush_touchdowns

    @int_property_decorator
    def longest_rush(self):
        """Return the longest rush.

        Returns
        -------
        int or None
            Yards of the longest rush.
        """
        return self._longest_rush

    @int_property_decorator
    def times_pass_target(self):
        """Return the number of times targeted.

        Returns
        -------
        int or None
            Number of times targeted as a receiver.
        """
        return self._times_pass_target

    @int_property_decorator
    def receptions(self):
        """Return the number of receptions.

        Returns
        -------
        int or None
            Number of receptions.
        """
        return self._receptions

    @int_property_decorator
    def receiving_yards(self):
        """Return the receiving yards.

        Returns
        -------
        int or None
            Total receiving yards.
        """
        return self._receiving_yards

    @float_property_decorator
    def receiving_yards_per_reception(self):
        """Return the yards per reception.

        Returns
        -------
        float or None
            Average yards per reception.
        """
        return self._receiving_yards_per_reception

    @int_property_decorator
    def receiving_touchdowns(self):
        """Return the receiving touchdowns.

        Returns
        -------
        int or None
            Number of receiving touchdowns.
        """
        return self._receiving_touchdowns

    @int_property_decorator
    def longest_reception(self):
        """Return the longest reception.

        Returns
        -------
        int or None
            Yards of the longest reception.
        """
        return self._longest_reception

    @int_property_decorator
    def fumbles(self):
        """Return the number of fumbles.

        Returns
        -------
        int or None
            Number of fumbles.
        """
        return self._fumbles

    @int_property_decorator
    def punt_returns(self):
        """Return the number of punt returns.

        Returns
        -------
        int or None
            Number of punt returns.
        """
        return self._punt_returns

    @int_property_decorator
    def punt_return_yards(self):
        """Return the punt return yards.

        Returns
        -------
        int or None
            Total punt return yards.
        """
        return self._punt_return_yards

    @int_property_decorator
    def punt_return_touchdown(self):
        """Return the punt return touchdowns.

        Returns
        -------
        int or None
            Number of punt return touchdowns.
        """
        return self._punt_return_touchdown

    @int_property_decorator
    def longest_punt_return(self):
        """Return the longest punt return.

        Returns
        -------
        int or None
            Yards of the longest punt return.
        """
        return self._longest_punt_return

    @float_property_decorator
    def yards_per_punt_return(self):
        """Return the yards per punt return.

        Returns
        -------
        float or None
            Average yards per punt return.
        """
        return self._yards_per_punt_return

    @int_property_decorator
    def kickoff_returns(self):
        """Return the number of kickoff returns.

        Returns
        -------
        int or None
            Number of kickoff returns.
        """
        return self._kickoff_returns

    @int_property_decorator
    def kickoff_return_yards(self):
        """Return the kickoff return yards.

        Returns
        -------
        int or None
            Total kickoff return yards.
        """
        return self._kickoff_return_yards

    @int_property_decorator
    def kickoff_return_touchdown(self):
        """Return the kickoff return touchdowns.

        Returns
        -------
        int or None
            Number of kickoff return touchdowns.
        """
        return self._kickoff_return_touchdown

    @int_property_decorator
    def longest_kickoff_return(self):
        """Return the longest kickoff return.

        Returns
        -------
        int or None
            Yards of the longest kickoff return.
        """
        return self._longest_kickoff_return

    @int_property_decorator
    def field_goals_attempted(self):
        """Return the total field goal attempts.

        Returns
        -------
        int or None
            Total field goal attempts.
        """
        return self._field_goals_attempted

    @int_property_decorator
    def field_goals_made(self):
        """Return the total field goals made.

        Returns
        -------
        int or None
            Total field goals made.
        """
        return self._field_goals_made

    @int_property_decorator
    def extra_points_attempted(self):
        """Return the number of extra point attempts.

        Returns
        -------
        int or None
            Number of extra points attempted.
        """
        return self._extra_points_attempted

    @int_property_decorator
    def extra_points_made(self):
        """Return the number of extra points made.

        Returns
        -------
        int or None
            Number of extra points made.
        """
        return self._extra_points_made

    @int_property_decorator
    def punts(self):
        """Return the number of punts.

        Returns
        -------
        int or None
            Number of punts.
        """
        return self._punts

    @int_property_decorator
    def total_punt_yards(self):
        """Return the total punt yards.

        Returns
        -------
        int or None
            Total yards punted.
        """
        return self._total_punt_yards

    @int_property_decorator
    def longest_punt(self):
        """Return the longest punt.

        Returns
        -------
        int or None
            Yards of the longest punt.
        """
        return self._longest_punt

    @float_property_decorator
    def yards_per_punt(self):
        """Return the yards per punt.

        Returns
        -------
        float or None
            Average yards per punt.
        """
        return self._yards_per_punt

    @int_property_decorator
    def interceptions(self):
        """Return the number of interceptions.

        Returns
        -------
        int or None
            Number of passes intercepted.
        """
        return self._interceptions

    @int_property_decorator
    def yards_returned_from_interception(self):
        """Return the interception return yards.

        Returns
        -------
        int or None
            Yards from interception returns.
        """
        return self._yards_returned_from_interception

    @int_property_decorator
    def interceptions_returned_for_touchdown(self):
        """Return the interception return touchdowns.

        Returns
        -------
        int or None
            Number of touchdowns from interceptions.
        """
        return self._interceptions_returned_for_touchdown

    @int_property_decorator
    def longest_interception_return(self):
        """Return the longest interception return.

        Returns
        -------
        int or None
            Yards of the longest interception return.
        """
        return self._longest_interception_return

    @int_property_decorator
    def passes_defended(self):
        """Return the number of passes defended.

        Returns
        -------
        int or None
            Number of passes defended.
        """
        return self._passes_defended

    @int_property_decorator
    def fumbles_forced(self):
        """Return the number of fumbles forced.

        Returns
        -------
        int or None
            Number of fumbles forced.
        """
        return self._fumbles_forced

    @int_property_decorator
    def fumbles_recovered(self):
        """Return the number of fumbles recovered.

        Returns
        -------
        int or None
            Number of fumbles recovered.
        """
        return self._fumbles_recovered

    @int_property_decorator
    def yards_recovered_from_fumble(self):
        """Return the fumble recovery yards.

        Returns
        -------
        int or None
            Yards from fumble recoveries.
        """
        return self._yards_recovered_from_fumble

    @int_property_decorator
    def fumbles_recovered_for_touchdown(self):
        """Return the fumble recovery touchdowns.

        Returns
        -------
        int or None
            Number of touchdowns from fumble recoveries.
        """
        return self._fumbles_recovered_for_touchdown

    @float_property_decorator
    def sacks(self):
        """Return the number of sacks.

        Returns
        -------
        float or None
            Number of sacks (can be fractional).
        """
        return self._sacks

    @int_property_decorator
    def assists_on_tackles(self):
        """Return the number of tackle assists.

        Returns
        -------
        int or None
            Number of tackle assists.
        """
        return self._assists_on_tackles