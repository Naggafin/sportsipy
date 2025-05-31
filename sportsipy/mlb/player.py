from typing import Any, Dict, List, Optional, Union
from bs4 import BeautifulSoup
from ..base import AbstractParser, int_property_decorator, float_property_decorator, _parse_field, _clean_stat
from .constants import BOXSCORE_SCHEME, NATIONALITY, PLAYER_ELEMENT_INDEX, PLAYER_SCHEME

class AbstractPlayer(AbstractParser):
    """Abstract base class for MLB player information and stats.

    Captures essential player stats and information, such as name, plate appearances,
    batting average, and pitching stats, for either a season (via roster data) or a
    specific game (via boxscore data). Subclasses like `Player` (for roster data) or
    `BoxscorePlayer` (for game data) extend this class to provide detailed
    season-based or game-based statistics.

    Parameters
    ----------
    player_id : str
        A player's ID per baseball-reference.com (e.g., 'altuvjo01' for Jose Altuve).
        Typically in the format 'LLLLLFFNN' where 'LLLLL' are the first 5 letters of
        the last name, 'FF' are the first 2 letters of the first name, and 'NN' is a
        number starting at '01', incrementing for each player with the same initial
        letters.
    player_name : str
        The player's full name (e.g., 'Jose Altuve').
    player_data : Dict[str, Dict[str, str]] or str
        For season-based stats (e.g., in `Player`), a dictionary mapping seasons to
        HTML data strings. For game-based stats (e.g., in `BoxscorePlayer`), a string
        containing the player's HTML stats for a game.

    Attributes
    ----------
    player_id : str
        The player's unique ID.
    name : str
        The player's full name.
    """
    def __init__(self, player_id: str, player_name: str, player_data: Union[str, Dict[str, Dict]]):
        super().__init__()
        self._player_id: str = player_id.strip()
        self._name: Optional[str] = player_name.strip() if player_name else None
        self._plate_appearances: Optional[List[str]] = None
        self._at_bats: Optional[List[str]] = None
        self._runs: Optional[List[str]] = None
        self._hits: Optional[List[str]] = None
        self._runs_batted_in: Optional[List[str]] = None
        self._bases_on_balls: Optional[List[str]] = None
        self._times_struck_out: Optional[List[str]] = None
        self._batting_average: Optional[List[float]] = None
        self._on_base_percentage: Optional[List[float]] = None
        self._slugging_percentage: Optional[List[float]] = None
        self._on_base_plus_slugging: Optional[List[str]] = None
        self._putouts: Optional[List[str]] = None
        self._assists: Optional[List[str]] = None
        self._hits_allowed: Optional[List[str]] = None
        self._runs_allowed: Optional[List[str]] = None
        self._earned_runs_allowed: Optional[List[str]] = None
        self._home_runs_allowed: Optional[List[str]] = None
        self._bases_on_balls_given: Optional[List[str]] = None
        self._strikeouts: Optional[List[str]] = None
        self._batters_faced: Optional[List[str]] = None

        self._parse_player_data(player_data)

    def __str__(self) -> str:
        """Return the string representation of the player."""
        return f'{self.name} ({self.player_id})'

    def __repr__(self) -> str:
        """Return the string representation of the player."""
        return self.__str__()

    def _parse_value(self, soup: BeautifulSoup, field: str, is_boxscore: bool = False) -> Optional[List[str]]:
        """Parse a field's values from HTML.

        Parameters
        ----------
        soup : BeautifulSoup
            Parsed HTML containing player stats.
        field : str
            The field to parse, per PLAYER_SCHEME or BOXSCORE_SCHEME.
        is_boxscore : bool, optional
            If True, uses BOXSCORE_SCHEME; otherwise, uses PLAYER_SCHEME. Defaults to False.

        Returns
        -------
        List[str] or None
            List of values for the field, or None if not found.
        """
        scheme = BOXSCORE_SCHEME if is_boxscore else PLAYER_SCHEME
        if field not in scheme:
            return None
        try:
            items = [elem.get_text(strip=True) for elem in soup.select(scheme[field])]
            return items if items else None
        except Exception:
            return None

    def _parse_player_data(self, player_data: Union[str, Dict[str, Dict]]) -> None:
        """Parse player stats and set attributes.

        Iterates through class attributes to parse stats from HTML, setting each
        attribute with the parsed values. Supports both season-based (dictionary)
        and game-based (string) data.

        Parameters
        ----------
        player_data : Dict[str, Dict[str, str]] or str
            Dictionary of season data for roster-based stats, or HTML string for
            boxscore-based stats.
        """
        is_boxscore = isinstance(player_data, str)
        for field in self.__dict__:
            if field.startswith('_'):
                short_field = field[1:]
                if short_field in ['player_id', 'name', 'index'] or \
                   short_field in ['most_recent_season', 'season', 'weight', 'height',
                                   'nationality', 'birth_date', 'contract']:
                    continue
                field_stats = []
                if isinstance(player_data, dict):
                    for year, data in player_data.items():
                        soup = BeautifulSoup(data.get('data', ''), 'html.parser')
                        value = self._parse_value(soup, short_field, is_boxscore=False)
                        field_stats.append(value)
                else:
                    soup = BeautifulSoup(player_data, 'html.parser')
                    value = self._parse_value(soup, short_field, is_boxscore=True)
                    field_stats.append(value)
                setattr(self, field, field_stats)

    @property
    def player_id(self) -> str:
        """Return the player's ID (e.g., 'altuvjo01')."""
        return self._player_id

    @property
    def name(self) -> Optional[str]:
        """Return the player's full name (e.g., 'Jose Altuve')."""
        return self._name

    @int_property_decorator
    def plate_appearances(self) -> Optional[int]:
        """Return the number of plate appearances."""
        return self._plate_appearances

    @int_property_decorator
    def at_bats(self) -> Optional[int]:
        """Return the number of at-bats."""
        return self._at_bats

    @int_property_decorator
    def runs(self) -> Optional[int]:
        """Return the number of runs scored."""
        return self._runs

    @int_property_decorator
    def hits(self) -> Optional[int]:
        """Return the number of hits."""
        return self._hits

    @int_property_decorator
    def runs_batted_in(self) -> Optional[int]:
        """Return the number of runs batted in."""
        return self._runs_batted_in

    @int_property_decorator
    def bases_on_balls(self) -> Optional[int]:
        """Return the number of walks."""
        return self._bases_on_balls

    @int_property_decorator
    def times_struck_out(self) -> Optional[int]:
        """Return the number of strikeouts as a batter."""
        return self._times_struck_out

    @float_property_decorator
    def batting_average(self) -> Optional[float]:
        """Return the batting average (0-1 range)."""
        return self._batting_average

    @float_property_decorator
    def on_base_percentage(self) -> Optional[float]:
        """Return the on-base percentage."""
        return self._on_base_percentage

    @float_property_decorator
    def slugging_percentage(self) -> Optional[float]:
        """Return the slugging percentage."""
        return self._slugging_percentage

    @float_property_decorator
    def on_base_plus_slugging(self) -> Optional[float]:
        """Return the on-base plus slugging percentage."""
        return self._on_base_plus_slugging

    @int_property_decorator
    def putouts(self) -> Optional[int]:
        """Return the number of putouts."""
        return self._putouts

    @int_property_decorator
    def assists(self) -> Optional[int]:
        """Return the number of assists."""
        return self._assists

    @int_property_decorator
    def hits_allowed(self) -> Optional[int]:
        """Return the number of hits allowed as a pitcher."""
        return self._hits_allowed

    @int_property_decorator
    def runs_allowed(self) -> Optional[int]:
        """Return the number of runs allowed as a pitcher."""
        return self._runs_allowed

    @int_property_decorator
    def earned_runs_allowed(self) -> Optional[int]:
        """Return the number of earned runs allowed."""
        return self._earned_runs_allowed

    @int_property_decorator
    def home_runs_allowed(self) -> Optional[int]:
        """Return the number of home runs allowed."""
        return self._home_runs_allowed

    @int_property_decorator
    def bases_on_balls_given(self) -> Optional[int]:
        """Return the number of walks given as a pitcher."""
        return self._bases_on_balls_given

    @int_property_decorator
    def strikeouts(self) -> Optional[int]:
        """Return the number of strikeouts thrown as a pitcher."""
        return self._strikeouts

    @int_property_decorator
    def batters_faced(self) -> Optional[int]:
        """Return the number of batters faced."""
        return self._batters_faced

    def dataframe(self) -> None:
        """Abstract method for DataFrame representation.

        Subclasses must implement this to return a pandas DataFrame of player stats.

        Returns
        -------
        None
            Raises NotImplementedError.
        """
        raise NotImplementedError("DataFrame must be implemented in subclasses.")