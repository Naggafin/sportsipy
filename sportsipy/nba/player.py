from ..base import AbstractParser, int_property_decorator, float_property_decorator, _parse_entity_data
from .constants import PLAYER_SCHEME

class AbstractPlayer(AbstractParser):
    """Abstract base class for player statistics.

    Retrieves and stores player statistics and information, such as name, field goals,
    rebounds, and advanced metrics, for a given player ID from basketball-reference.com.
    Designed to be inherited by `Player` (for season/career stats) or `BoxscorePlayer`
    (for single-game stats). By default, returns career stats for season-based classes;
    specific seasons can be accessed by calling the instance with a season ID.

    Parameters
    ----------
    player_id : str
        The player's ID (e.g., 'hardeja01' for James Harden), typically in the format
        'LLLLLFFNN' where 'LLLLL' are the first 5 letters of the last name, 'FF' are
        the first 2 letters of the first name, and 'NN' is a number starting at '01'.
    player_name : str
        The player's full name (e.g., 'James Harden').
    player_data : dict or str
        For season stats, a dictionary mapping seasons to HTML data; for game stats,
        a string of HTML data from the boxscore page.

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
        self._minutes_played = None
        self._field_goals = None
        self._field_goal_attempts = None
        self._field_goal_percentage = None
        self._three_pointers = None
        self._three_point_attempts = None
        self._three_point_percentage = None
        self._two_pointers = None
        self._two_point_attempts = None
        self._two_point_percentage = None
        self._effective_field_goal_percentage = None
        self._free_throws = None
        self._free_throw_attempts = None
        self._free_throw_percentage = None
        self._offensive_rebounds = None
        self._defensive_rebounds = None
        self._total_rebounds = None
        self._assists = None
        self._steals = None
        self._blocks = None
        self._turnovers = None
        self._personal_fouls = None
        self._points = None
        self._true_shooting_percentage = None
        self._three_point_attempt_rate = None
        self._free_throw_attempt_rate = None
        self._offensive_rebound_percentage = None
        self._defensive_rebound_percentage = None
        self._total_rebound_percentage = None
        self._assist_percentage = None
        self._steal_percentage = None
        self._block_percentage = None
        self._turnover_percentage = None
        self._usage_percentage = None
        self._box_plus_minus = None

        AbstractParser.__init__(self, player_data.get('Career', {}).get('data', '') if isinstance(player_data, dict) else player_data)
        if player_data:
            fields_to_skip = {
                'player_id', 'name', 'index', 'most_recent_season', 'contract',
                'height', 'weight', 'birth_date', 'nationality'
            }
            _parse_entity_data(self, player_data, PLAYER_SCHEME, fields_to_skip)

    @property
    def player_id(self):
        """Return the player's ID.

        Returns
        -------
        str
            The player's ID (e.g., 'hardeja01').
        """
        return self._player_id

    @property
    def name(self):
        """Return the player's name.

        Returns
        -------
        str
            The player's full name (e.g., 'James Harden').
        """
        return self._name

    @int_property_decorator
    def minutes_played(self):
        """Return total minutes played.

        Returns
        -------
        int or None
            Total minutes played.
        """
        return self._minutes_played

    @int_property_decorator
    def field_goals(self):
        """Return total field goals made.

        Returns
        -------
        int or None
            Total field goals scored.
        """
        return self._field_goals

    @int_property_decorator
    def field_goal_attempts(self):
        """Return total field goal attempts.

        Returns
        -------
        int or None
            Total field goals attempted.
        """
        return self._field_goal_attempts

    @float_property_decorator
    def field_goal_percentage(self):
        """Return field goal percentage.

        Returns
        -------
        float or None
            Field goal percentage (0-1).
        """
        return self._field_goal_percentage

    @int_property_decorator
    def three_pointers(self):
        """Return total three-point field goals made.

        Returns
        -------
        int or None
            Total three-pointers made.
        """
        return self._three_pointers

    @int_property_decorator
    def three_point_attempts(self):
        """Return total three-point field goal attempts.

        Returns
        -------
        int or None
            Total three-point attempts.
        """
        return self._three_point_attempts

    @float_property_decorator
    def three_point_percentage(self):
        """Return three-point field goal percentage.

        Returns
        -------
        float or None
            Three-point percentage (0-1).
        """
        return self._three_point_percentage

    @int_property_decorator
    def two_pointers(self):
        """Return total two-point field goals made.

        Returns
        -------
        int or None
            Total two-pointers made.
        """
        return self._two_pointers

    @int_property_decorator
    def two_point_attempts(self):
        """Return total two-point field goal attempts.

        Returns
        -------
        int or None
            Total two-point attempts.
        """
        return self._two_point_attempts

    @float_property_decorator
    def two_point_percentage(self):
        """Return two-point field goal percentage.

        Returns
        -------
        float or None
            Two-point percentage (0-1).
        """
        return self._two_point_percentage

    @float_property_decorator
    def effective_field_goal_percentage(self):
        """Return effective field goal percentage.

        Returns
        -------
        float or None
            Field goal percentage weighted for three-pointers (0-1).
        """
        return self._effective_field_goal_percentage

    @int_property_decorator
    def free_throws(self):
        """Return total free throws made.

        Returns
        -------
        int or None
            Total free throws made.
        """
        return self._free_throws

    @int_property_decorator
    def free_throw_attempts(self):
        """Return total free throw attempts.

        Returns
        -------
        int or None
            Total free throw attempts.
        """
        return self._free_throw_attempts

    @float_property_decorator
    def free_throw_percentage(self):
        """Return free throw percentage.

        Returns
        -------
        float or None
            Free throw percentage (0-1).
        """
        return self._free_throw_percentage

    @int_property_decorator
    def offensive_rebounds(self):
        """Return total offensive rebounds.

        Returns
        -------
        int or None
            Total offensive rebounds grabbed.
        """
        return self._offensive_rebounds

    @int_property_decorator
    def defensive_rebounds(self):
        """Return total defensive rebounds.

        Returns
        -------
        int or None
            Total defensive rebounds grabbed.
        """
        return self._defensive_rebounds

    @int_property_decorator
    def total_rebounds(self):
        """Return total rebounds.

        Returns
        -------
        int or None
            Total offensive and defensive rebounds.
        """
        return self._total_rebounds

    @int_property_decorator
    def assists(self):
        """Return total assists.

        Returns
        -------
        int or None
            Total assists tallied.
        """
        return self._assists

    @int_property_decorator
    def steals(self):
        """Return total steals.

        Returns
        -------
        int or None
            Total steals tallied.
        """
        return self._steals

    @int_property_decorator
    def blocks(self):
        """Return total blocks.

        Returns
        -------
        int or None
            Total shots blocked.
        """
        return self._blocks

    @int_property_decorator
    def turnovers(self):
        """Return total turnovers.

        Returns
        -------
        int or None
            Total turnovers committed.
        """
        return self._turnovers

    @int_property_decorator
    def personal_fouls(self):
        """Return total personal fouls.

        Returns
        -------
        int or None
            Total personal fouls committed.
        """
        return self._personal_fouls

    @int_property_decorator
    def points(self):
        """Return total points scored.

        Returns
        -------
        int or None
            Total points scored.
        """
        return self._points

    @float_property_decorator
    def true_shooting_percentage(self):
        """Return true shooting percentage.

        Returns
        -------
        float or None
            True shooting percentage accounting for two-pointers, three-pointers, and free throws (0-1).
        """
        return self._true_shooting_percentage

    @float_property_decorator
    def three_point_attempt_rate(self):
        """Return three-point attempt rate.

        Returns
        -------
        float or None
            Percentage of field goals from three-point range (0-1).
        """
        return self._three_point_attempt_rate

    @float_property_decorator
    def free_throw_attempt_rate(self):
        """Return free throw attempt rate.

        Returns
        -------
        float or None
            Free throw attempts per field goal attempt.
        """
        return self._free_throw_attempt_rate

    @float_property_decorator
    def offensive_rebound_percentage(self):
        """Return offensive rebound percentage.

        Returns
        -------
        float or None
            Percentage of available offensive rebounds grabbed (0-100).
        """
        return self._offensive_rebound_percentage

    @float_property_decorator
    def defensive_rebound_percentage(self):
        """Return defensive rebound percentage.

        Returns
        -------
        float or None
            Percentage of available defensive rebounds grabbed (0-100).
        """
        return self._defensive_rebound_percentage

    @float_property_decorator
    def total_rebound_percentage(self):
        """Return total rebound percentage.

        Returns
        -------
        float or None
            Percentage of available rebounds grabbed (0-100).
        """
        return self._total_rebound_percentage

    @float_property_decorator
    def assist_percentage(self):
        """Return assist percentage.

        Returns
        -------
        float or None
            Percentage of field goals assisted while on the floor (0-100).
        """
        return self._assist_percentage

    @float_property_decorator
    def steal_percentage(self):
        """Return steal percentage.

        Returns
        -------
        float or None
            Percentage of defensive possessions ending in a steal (0-100).
        """
        return self._steal_percentage

    @float_property_decorator
    def block_percentage(self):
        """Return block percentage.

        Returns
        -------
        float or None
            Percentage of opposing two-point shots blocked (0-100).
        """
        return self._block_percentage

    @float_property_decorator
    def turnover_percentage(self):
        """Return turnover percentage.

        Returns
        -------
        float or None
            Turnovers per 100 possessions.
        """
        return self._turnover_percentage

    @float_property_decorator
    def usage_percentage(self):
        """Return usage percentage.

        Returns
        -------
        float or None
            Percentage of plays involving the player (0-100).
        """
        return self._usage_percentage

    @float_property_decorator
    def box_plus_minus(self):
        """Return box plus/minus.

        Returns
        -------
        float or None
            Points per 100 possessions contributed compared to league average.
        """
        return self._box_plus_minus