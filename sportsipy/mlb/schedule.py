import pandas as pd
import re
from datetime import datetime
from typing import List, Optional, Iterator
from bs4 import BeautifulSoup
from ..base import int_property_decorator, float_property_decorator, _parse_field, _fetch_html, _get_stats_table, _resolve_year, _parse_boxscore_uri
from .constants import DAY, NIGHT, SCHEDULE_SCHEME, SCHEDULE_URL, WIN, LOSS, HOME, AWAY
from .boxscore import Boxscore

class Game:
    """A matchup between two MLB teams.

    Stores high-level match information for a game in a team's schedule, including
    date, time, opponent, result, and boxscore details.

    Parameters
    ----------
    game_data : BeautifulSoup
        A BeautifulSoup object containing the HTML row for the game.
    year : str
        The 4-digit year of the season (e.g., '2023').

    Attributes
    ----------
    boxscore_index : str
        The URI for the game's boxscore.
    date : str
        The date the game was played.
    opponent_abbr : str
        The opponent's 3-letter abbreviation (e.g., 'NYY').
    result : str
        The game result ('Win' or 'Loss').
    """
    def __init__(self, game_data: BeautifulSoup, year: str):
        self._game: Optional[str] = None
        self._date: Optional[str] = None
        self._datetime: Optional[datetime] = None
        self._boxscore: Optional[str] = None
        self._location: Optional[str] = None
        self._opponent_abbr: Optional[str] = None
        self._result: Optional[str] = None
        self._runs_scored: Optional[str] = None
        self._runs_allowed: Optional[str] = None
        self._innings: Optional[str] = None
        self._record: Optional[str] = None
        self._rank: Optional[str] = None
        self._games_behind: Optional[str] = None
        self._winner: Optional[str] = None
        self._loser: Optional[str] = None
        self._save: Optional[str] = None
        self._game_duration: Optional[str] = None
        self._day_or_night: Optional[str] = None
        self._attendance: Optional[str] = None
        self._streak: Optional[str] = None
        self._year: str = year

        self._parse_game_data(game_data)

    def __str__(self) -> str:
        """Return the string representation of the game."""
        return f'{self.date} - {self.opponent_abbr}'

    def __repr__(self) -> str:
        """Return the string representation of the game."""
        return self.__str__()

    def _parse_game_data(self, game_data: BeautifulSoup) -> None:
        """Parse all game attributes from HTML.

        Parameters
        ----------
        game_data : BeautifulSoup
            A BeautifulSoup object containing the HTML row for the game.
        """
        for field in self.__dict__:
            short_field = field[1:] if field.startswith('_') else field
            if short_field in ['datetime', 'year', 'boxscore']:
                continue
            value = _parse_field(SCHEDULE_SCHEME, game_data, short_field)
            setattr(self, f'_{short_field}', value)
        self._boxscore = _parse_boxscore_uri(game_data)

    @property
    def dataframe(self) -> Optional[pd.DataFrame]:
        """Return a pandas DataFrame of game properties.

        Returns
        -------
        pd.DataFrame or None
            DataFrame indexed by boxscore_index, or None if the game hasn't been played.
        """
        if self._runs_allowed is None and self._runs_scored is None:
            return None
        fields = {
            'attendance': self.attendance,
            'boxscore_index': self.boxscore_index,
            'date': self.date,
            'datetime': self.datetime,
            'game_number_for_day': self.game_number_for_day,
            'day_or_night': self.day_or_night,
            'game': self.game,
            'game_duration': self.game_duration,
            'games_behind': self.games_behind,
            'innings': self.innings,
            'location': self.location,
            'loser': self.loser,
            'opponent_abbr': self.opponent_abbr,
            'rank': self.rank,
            'record': self.record,
            'result': self.result,
            'runs_allowed': self.runs_allowed,
            'runs_scored': self.runs_scored,
            'save': self.save,
            'streak': self.streak,
            'winner': self.winner
        }
        return pd.DataFrame([fields], index=[self._boxscore])

    @property
    def dataframe_extended(self) -> Optional[pd.DataFrame]:
        """Return a pandas DataFrame of the game's Boxscore.

        Returns
        -------
        pd.DataFrame or None
            DataFrame from the Boxscore class, or None if the game hasn't been played.
        """
        if self._runs_allowed is None and self._runs_scored is None:
            return None
        return self.boxscore.dataframe

    @int_property_decorator
    def game(self) -> Optional[int]:
        """Return the game number in the season (1 is the first game)."""
        return self._game

    @property
    def date(self) -> Optional[str]:
        """Return the date the game was played."""
        return self._date

    @property
    def datetime(self) -> Optional[datetime]:
        """Return a datetime object of the game's date."""
        if not self._date:
            return None
        date_string = f'{self._date} {self._year}'
        date_string = re.sub(r' \(\d+\)', '', date_string)
        try:
            return datetime.strptime(date_string, '%A, %b %d %Y')
        except ValueError:
            return None

    @property
    def game_number_for_day(self) -> int:
        """Return the game number for the day (e.g., 2 for the second game of a doubleheader)."""
        if not self._date:
            return 1
        match = re.findall(r'\(\d+\)', self._date)
        if not match:
            return 1
        number = re.findall(r'\d+', match[0])
        return int(number[0]) if number else 1

    @property
    def boxscore(self) -> Boxscore:
        """Return a Boxscore instance for the game."""
        return Boxscore(self._boxscore)

    @property
    def boxscore_index(self) -> Optional[str]:
        """Return the boxscore URI."""
        return self._boxscore

    @property
    def location(self) -> Optional[str]:
        """Return a constant indicating home or away."""
        return AWAY if self._location == '@' else HOME

    @property
    def opponent_abbr(self) -> Optional[str]:
        """Return the opponent's 3-letter abbreviation (e.g., 'NYY')."""
        return self._opponent_abbr

    @property
    def result(self) -> Optional[str]:
        """Return a constant indicating win or loss."""
        return WIN if self._result and self._result.lower() == 'w' else LOSS

    @int_property_decorator
    def runs_scored(self) -> Optional[int]:
        """Return the number of runs scored."""
        return self._runs_scored

    @int_property_decorator
    def runs_allowed(self) -> Optional[int]:
        """Return the number of runs allowed."""
        return self._runs_allowed

    @int_property_decorator
    def innings(self) -> Optional[int]:
        """Return the number of innings played (defaults to 9)."""
        return 9 if not self._innings else self._innings

    @property
    def record(self) -> Optional[str]:
        """Return the team's record (e.g., 'W-L')."""
        return self._record

    @int_property_decorator
    def rank(self) -> Optional[int]:
        """Return the team's league rank (1 is best)."""
        return self._rank

    @float_property_decorator
    def games_behind(self) -> Optional[float]:
        """Return the number of games behind the leader."""
        if not self._games_behind:
            return None
        if 'up' in self._games_behind.lower():
            games = re.sub(r'up *', '', self._games_behind.lower())
            try:
                return float(games) * -1.0
            except ValueError:
                return None
        if 'tied' in self._games_behind.lower():
            return 0.0
        try:
            return float(self._games_behind)
        except ValueError:
            return None

    @property
    def winner(self) -> Optional[str]:
        """Return the name of the winning pitcher."""
        return self._winner

    @property
    def loser(self) -> Optional[str]:
        """Return the name of the losing pitcher."""
        return self._loser

    @property
    def save(self) -> Optional[str]:
        """Return the name of the pitcher credited with the save."""
        return None if not self._save or self._save == '' else self._save

    @property
    def game_duration(self) -> Optional[str]:
        """Return the game duration (e.g., 'H:MM')."""
        return self._game_duration

    @property
    def day_or_night(self) -> Optional[str]:
        """Return a constant indicating day or night game."""
        return NIGHT if self._day_or_night and self._day_or_night.lower() == 'n' else DAY

    @int_property_decorator
    def attendance(self) -> Optional[int]:
        """Return the total attendance."""
        return self._attendance

    @property
    def streak(self) -> Optional[str]:
        """Return the team's streak (e.g., '++' for two wins)."""
        return self._streak

class Schedule:
    """A team's MLB season schedule.

    Stores a list of games for a team's season, including wins, losses, and scores.

    Parameters
    ----------
    abbreviation : str
        The team's 3-letter abbreviation (e.g., 'HOU' for Houston Astros).
    year : str, optional
        The 4-digit year (e.g., '2023'). Defaults to the current year.

    Attributes
    ----------
    games : List[Game]
        List of Game instances for the season.
    """
    def __init__(self, abbreviation: str, year: Optional[str] = None):
        self._games: List[Game] = []
        self._pull_schedule(abbreviation, year)

    def __getitem__(self, index: int) -> Game:
        """Return a game by index.

        Parameters
        ----------
        index : int
            The 0-based index of the game.

        Returns
        -------
        Game
            The requested game.
        """
        return self._games[index]

    def __call__(self, date: datetime, game_number: int = 1) -> Game:
        """Return a game by date and game number.

        Parameters
        ----------
        date : datetime
            The date of the game.
        game_number : int, optional
            The game number for the day (e.g., 2 for the second game of a doubleheader). Defaults to 1.

        Returns
        -------
        Game
            The matching game.

        Raises
        ------
        ValueError
            If no game matches the date and game number.
        """
        for game in self._games:
            if (game.datetime and
                game.datetime.year == date.year and
                game.datetime.month == date.month and
                game.datetime.day == date.day and
                game.game_number_for_day == game_number):
                return game
        raise ValueError('No games found for requested date')

    def __str__(self) -> str:
        """Return the string representation of the schedule."""
        return '\n'.join(f'{game.date} - {game.opponent_abbr}'.strip() for game in self._games)

    def __repr__(self) -> str:
        """Return the string representation of the schedule."""
        return self.__str__()

    def __iter__(self) -> Iterator[Game]:
        """Return an iterator of all games."""
        return iter(self._games)

    def __len__(self) -> int:
        """Return the number of games."""
        return len(self._games)

    def _pull_schedule(self, abbreviation: str, year: Optional[str]) -> None:
        """Fetch and parse the team's schedule.

        Parameters
        ----------
        abbreviation : str
            The team's 3-letter abbreviation.
        year : str, optional
            The 4-digit year.
        """
        if not year:
            year = _resolve_year(datetime.now().year)
            test_url = SCHEDULE_URL % (abbreviation.upper(), year)
            if not _fetch_html(test_url):
                prev_year = str(int(year) - 1)
                if _fetch_html(SCHEDULE_URL % (abbreviation.upper(), prev_year)):
                    year = prev_year
        url = SCHEDULE_URL % (abbreviation.upper(), year)
        soup = _fetch_html(url)
        if not soup:
            return
        schedule = _get_stats_table(soup, 'team_schedule')
        if not schedule:
            return
        for row in schedule.find('tbody').find_all('tr'):
            if 'thead' in row.get('class', []):
                continue
            self._games.append(Game(row, year))

    @property
    def dataframe(self) -> Optional[pd.DataFrame]:
        """Return a pandas DataFrame of all games.

        Returns
        -------
        pd.DataFrame or None
            DataFrame of played games, indexed by boxscore_index, or None if no games.
        """
        frames = [game.dataframe for game in self._games if game.dataframe is not None]
        return pd.concat(frames) if frames else None

    @property
    def dataframe_extended(self) -> Optional[pd.DataFrame]:
        """Return a pandas DataFrame of all games' Boxscore data.

        Returns
        -------
        pd.DataFrame or None
            DataFrame of played games' boxscores, or None if no games.
        """
        frames = [game.dataframe_extended for game in self._games if game.dataframe_extended is not None]
        return pd.concat(frames) if frames else None