import pandas as pd
import re
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.error import HTTPError
from ..base import (int_property_decorator, float_property_decorator, _parse_field,
                    _cleanup, _remove_html_comment_tags, _url_exists, _get_stats_table,
                    _no_data_found, _parse_abbreviation, _find_year_for_season, AbstractGame)
from ..constants import AWAY, HOME, WIN, LOSS, REGULAR_SEASON, CONFERENCE_TOURNAMENT
from .constants import SCHEDULE_SCHEME, SCHEDULE_URL
from .boxscore import Boxscore
import requests


class Game(AbstractGame):
    """A representation of a matchup between two NBA teams.

    Stores all relevant high-level match information for a game in a team's
    schedule, including date, time, opponent, result, and boxscore details.

    Parameters
    ----------
    game_data : BeautifulSoup object
        The HTML row containing the specified game information.
    playoffs : bool, optional
        Indicates if the game is a playoff game (default is False).
    """
    def __init__(self, game_data, playoffs=False):
        super().__init__(boxscore_uri=None)  # Boxscore URI set in _parse_boxscore
        self._game = None
        self._time = None
        self._datetime = None
        self._opponent_abbr = None
        self._opponent_name = None
        self._result = None
        self._points_scored = None
        self._points_allowed = None
        self._wins = None
        self._losses = None
        self._streak = None
        self._playoffs = playoffs

        self._parse_game_data(game_data)

    def __str__(self):
        """Return the string representation of the game.

        Returns
        -------
        str
            A string in the format 'date - opponent_abbr', e.g., 'Wed, Oct 18, 2017 - CHI'.
        """
        return f'{self.date} - {self.opponent_abbr}'

    def __repr__(self):
        """Return the string representation of the game.

        Returns
        -------
        str
            A string in the format 'date - opponent_abbr'.
        """
        return self.__str__()

    def _parse_boxscore(self, game_data):
        """Parse the boxscore URI for the game.

        Extracts the boxscore URI from the HTML data, which is embedded within
        a specific table cell.

        Parameters
        ----------
        game_data : BeautifulSoup object
            A BeautifulSoup object containing the game-specific HTML data.
        """
        boxscore_cell = game_data.select_one('td[data-stat="box_score_text"]')
        if boxscore_cell and boxscore_cell.a:
            boxscore = boxscore_cell.a['href']
            boxscore = re.sub(r'.*/boxscores/|\.html.*$', '', boxscore)
            self._boxscore = boxscore
        else:
            self._boxscore = None

    def _parse_opponent_abbr(self, game_data):
        """Parse the opponent's abbreviation for the game.

        Extracts the opponent's 3-letter abbreviation from the HTML data.

        Parameters
        ----------
        game_data : BeautifulSoup object
            A BeautifulSoup object containing the game-specific HTML data.
        """
        opponent_cell = game_data.select_one('td[data-stat="opp_name"]')
        if opponent_cell and opponent_cell.a:
            opponent = opponent_cell.a['href']
            opponent = re.sub(r'.*/teams/|/\d+\.html.*$', '', opponent)
            self._opponent_abbr = opponent
        else:
            self._opponent_abbr = None

    def _parse_game_data(self, game_data):
        """Parse all attributes from the game data.

        Iterates through all class attributes (except those explicitly skipped)
        and extracts their values from the provided HTML data using the
        SCHEDULE_SCHEME. Updates the instance attributes with the parsed values.

        Parameters
        ----------
        game_data : BeautifulSoup object
            A BeautifulSoup object containing all stats for a given game.
        """
        for field in self.__dict__:
            short_name = field[1:]  # Remove leading '_'
            if short_name in ('datetime', 'playoffs', 'boxscore_index'):
                continue
            if short_name == 'boxscore':
                self._parse_boxscore(game_data)
                continue
            if short_name == 'opponent_abbr':
                self._parse_opponent_abbr(game_data)
                continue
            value = _parse_field(SCHEDULE_SCHEME, game_data, short_name)
            setattr(self, field, value)

    @property
    def dataframe(self):
        """Return a pandas DataFrame of the game's stats.

        Returns
        -------
        pandas.DataFrame or None
            A DataFrame containing all class properties, indexed by the boxscore
            URI. Returns None if points data is unavailable.
        """
        if self._points_allowed is None and self._points_scored is None:
            return None
        fields_to_include = {
            'boxscore_index': self.boxscore_index,
            'date': self.date,
            'datetime': self.datetime,
            'game': self.game,
            'location': self.location,
            'losses': self.losses,
            'opponent_abbr': self.opponent_abbr,
            'opponent_name': self.opponent_name,
            'playoffs': self.playoffs,
            'points_allowed': self.points_allowed,
            'points_scored': self.points_scored,
            'result': self.result,
            'streak': self.streak,
            'time': self.time,
            'wins': self.wins
        }
        return pd.DataFrame([fields_to_include], index=[self._boxscore])

    @property
    def dataframe_extended(self):
        """Return a pandas DataFrame of the game's detailed boxscore stats.

        Provides richer context by returning the Boxscore class's DataFrame for
        the game, but is slower than the `dataframe` property.

        Returns
        -------
        pandas.DataFrame or None
            A DataFrame of the boxscore stats, indexed by the boxscore URI.
            Returns None if no boxscore data is available.
        """
        return self.boxscore.dataframe if self.boxscore else None

    @int_property_decorator
    def game(self):
        """Return the game's number in the season.

        Returns
        -------
        int or None
            The game number in the season (1 for the first game), or None if unavailable.
        """
        return self._game

    @property
    def time(self):
        """Return the game's start time.

        Returns
        -------
        str or None
            The time the game started in Eastern Time, e.g., '8:01p'.
        """
        return self._time

    @property
    def datetime(self):
        """Return the game's date as a datetime object.

        Returns
        -------
        datetime or None
            A datetime object representing the game's date, or None if parsing fails.
        """
        try:
            return datetime.strptime(self._date, '%a, %b %d, %Y')
        except (ValueError, TypeError):
            return None

    @property
    def boxscore(self):
        """Return the game's boxscore details.

        Returns
        -------
        Boxscore or None
            An instance of the Boxscore class for the game, or None if no boxscore URI is available.
        """
        return Boxscore(self._boxscore) if self._boxscore else None

    @property
    def location(self):
        """Return the game's location type.

        Returns
        -------
        str
            A constant (HOME or AWAY) indicating whether the game was played at
            home or away.
        """
        return AWAY if self._location and self._location.lower() == '@' else HOME

    @property
    def opponent_abbr(self):
        """Return the opponent's abbreviation.

        Returns
        -------
        str or None
            The opponent's 3-letter abbreviation, e.g., 'CHI' for Chicago Bulls.
        """
        return self._opponent_abbr

    @property
    def opponent_name(self):
        """Return the opponent's full name.

        Returns
        -------
        str or None
            The opponent's full name, e.g., 'Chicago Bulls'.
        """
        return self._opponent_name

    @property
    def result(self):
        """Return the game's result.

        Returns
        -------
        str
            A constant (WIN or LOSS) indicating whether the team won or lost.
        """
        return LOSS if self._result and self._result.lower() == 'l' else WIN

    @int_property_decorator
    def points_scored(self):
        """Return the points scored by the team.

        Returns
        -------
        int or None
            The number of points scored by the team.
        """
        return self._points_scored

    @int_property_decorator
    def points_allowed(self):
        """Return the points allowed by the team.

        Returns
        -------
        int or None
            The number of points allowed by the team.
        """
        return self._points_allowed

    @int_property_decorator
    def wins(self):
        """Return the team's wins after the game.

        Returns
        -------
        int or None
            The number of wins the team has after the game.
        """
        return self._wins

    @int_property_decorator
    def losses(self):
        """Return the team's losses after the game.

        Returns
        -------
        int or None
            The number of losses the team has after the game.
        """
        return self._losses

    @property
    def streak(self):
        """Return the team's current streak.

        Returns
        -------
        str or None
            The team's streak, e.g., 'W 3' for a 3-game winning streak.
        """
        return self._streak

    @property
    def playoffs(self):
        """Return whether the game is a playoff game.

        Returns
        -------
        bool
            True if the game is a playoff game, False otherwise.
        """
        return self._playoffs

class Schedule:
    """A team's NBA season schedule.

    Generates a team's schedule for a given season, including wins, losses,
    scores, and game details.

    Parameters
    ----------
    abbreviation : str
        The team's 3-letter abbreviation, e.g., 'PHO' for Phoenix Suns.
    year : str, optional
        The season year to pull stats from (e.g., '2023'). If None, defaults to
        the current or most recent season.
    """
    def __init__(self, abbreviation, year=None):
        self._games = []
        self._pull_schedule(abbreviation, year)

    def __getitem__(self, index):
        """Return a game by index.

        Parameters
        ----------
        index : int
            The 0-based index of the game to return.

        Returns
        -------
        Game
            The Game instance at the specified index.

        Raises
        ------
        IndexError
            If the index is out of range.
        """
        return self._games[index]

    def __call__(self, date):
        """Return a game by date.

        Parameters
        ----------
        date : datetime
            A datetime object specifying the date of the game to return.

        Returns
        -------
        Game
            The Game instance for the specified date.

        Raises
        ------
        ValueError
            If no game is found for the specified date.
        """
        for game in self._games:
            if (game.datetime and
                game.datetime.year == date.year and
                game.datetime.month == date.month and
                game.datetime.day == date.day):
                return game
        raise ValueError('No games found for requested date')

    def __str__(self):
        """Return the string representation of the schedule.

        Returns
        -------
        str
            A string listing all games in the format 'date - opponent_abbr'.
        """
        return '\n'.join(f'{game.date} - {game.opponent_abbr}'.strip() for game in self._games)

    def __repr__(self):
        """Return the string representation of the schedule.

        Returns
        -------
        str
            A string listing all games in the format 'date - opponent_abbr'.
        """
        return self.__str__()

    def __iter__(self):
        """Return an iterator over the games in the schedule.

        Returns
        -------
        iterator
            An iterator of Game instances.
        """
        return iter(self._games)

    def __len__(self):
        """Return the number of games in the schedule.

        Returns
        -------
        int
            The number of games.
        """
        return len(self._games)

    def _add_games_to_schedule(self, schedule, playoff=False):
        """Add games to the schedule.

        Creates Game instances for each game in the provided HTML data and adds
        them to the schedule.

        Parameters
        ----------
        schedule : list
            A list of BeautifulSoup objects representing game rows.
        playoff : bool, optional
            Indicates if the games are playoff games (default is False).
        """
        for item in schedule:
            if 'thead' in item.get('class', []):
                continue
            game = Game(item, playoff)
            self._games.append(game)

    def _pull_schedule(self, abbreviation, year):
        """Download and parse the team's schedule.

        Retrieves the team's schedule page, parses it with BeautifulSoup, and
        creates Game instances for each game, including regular season and
        playoff games.

        Parameters
        ----------
        abbreviation : str
            The team's 3-letter abbreviation, e.g., 'DET' for Detroit Pistons.
        year : str
            The season year to pull stats from.
        """
        if not year:
            year = _find_year_for_season('nba')
            # Handle 2020 season delay
            if year == '2021':
                try:
                    response = requests.get(SCHEDULE_URL % (abbreviation.lower(), year))
                    response.raise_for_status()
                except HTTPError:
                    year = str(int(year) - 1)
            # Fallback to previous year if current season data is unavailable
            if not _url_exists(SCHEDULE_URL % (abbreviation.lower(), year)):
                prev_year = str(int(year) - 1)
                if _url_exists(SCHEDULE_URL % (abbreviation.lower(), prev_year)):
                    year = prev_year

        url = SCHEDULE_URL % (abbreviation.lower(), year)
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(_remove_html_comment_tags(response.text), 'html.parser')
        except (HTTPError, requests.RequestException):
            _no_data_found()
            return

        schedule = _get_stats_table(soup, 'games')
        if not schedule:
            _no_data_found()
            return
        self._add_games_to_schedule(schedule)

        if soup.select_one('table#games_playoffs'):
            playoffs = _get_stats_table(soup, 'games_playoffs')
            self._add_games_to_schedule(playoffs, True)

    @property
    def dataframe(self):
        """Return a pandas DataFrame of the schedule.

        Returns
        -------
        pandas.DataFrame or None
            A DataFrame where each row represents a Game, indexed by boxscore
            URI. Returns None if no games have valid data.
        """
        frames = [game.dataframe for game in self if game.dataframe is not None]
        return pd.concat(frames) if frames else None

    @property
    def dataframe_extended(self):
        """Return a pandas DataFrame of detailed boxscore stats for all games.

        Returns
        -------
        pandas.DataFrame or None
            A DataFrame where each row represents a Boxscore, indexed by
            boxscore URI. Returns None if no games have valid boxscore data.
        """
        frames = [game.dataframe_extended for game in self if game.dataframe_extended is not None]
        return pd.concat(frames) if frames else None