import pandas as pd
from ..base import AbstractParser, int_property_decorator, float_property_decorator, _parse_field, _fetch_all_teams
from ..constants import LOSS, WIN
from .constants import PARSING_SCHEME, WILD_CARD, DIVISION, CONF_CHAMPIONSHIP, SUPER_BOWL, WON_SUPER_BOWL, LOST_WILD_CARD, LOST_DIVISIONAL, LOST_CONF_CHAMPS, LOST_SUPER_BOWL
from .roster import Roster
from .schedule import Schedule

class Team(AbstractParser):
    """Representation of an NFL team's season statistics.

    Stores comprehensive team statistics and identifiers for a single NFL season,
    such as wins, losses, points scored, and advanced metrics, from pro-football-reference.com.

    Parameters
    ----------
    team_name : str, optional
        The team's 3-letter abbreviation (e.g., 'KAN' for Kansas City Chiefs) if called directly.
    team_data : BeautifulSoup element, optional
        HTML row element containing team stats, used when called from Teams.
    rank : int, optional
        The team's league rank based on points scored, used when called from Teams.
    year : str, optional
        The 4-digit year of the season (e.g., '2023').
    season_page : str, optional
        Path to a local HTML file of the season page to parse instead of fetching online.

    Attributes
    ----------
    abbreviation : str or None
        The team's 3-letter abbreviation (e.g., 'KAN').
    name : str or None
        The team's full name (e.g., 'Kansas City Chiefs').
    wins : int or None
        Number of games won in the season.
    schedule : Schedule
        The team's game schedule for the season.
    roster : Roster
        The team's player roster for the season.
    """
    def __init__(self, team_name=None, team_data=None, rank=None, year=None, season_page=None):
        self._year = year
        self._rank = rank
        self._abbreviation = None
        self._name = None
        self._wins = None
        self._losses = None
        self._win_percentage = None
        self._games_played = None
        self._points_for = None
        self._points_against = None
        self._points_difference = None
        self._margin_of_victory = None
        self._strength_of_schedule = None
        self._simple_rating_system = None
        self._offensive_simple_rating_system = None
        self._defensive_simple_rating_system = None
        self._yards = None
        self._plays = None
        self._yards_per_play = None
        self._turnovers = None
        self._fumbles = None
        self._first_downs = None
        self._pass_completions = None
        self._pass_attempts = None
        self._pass_yards = None
        self._pass_touchdowns = None
        self._interceptions = None
        self._pass_net_yards_per_attempt = None
        self._pass_first_downs = None
        self._rush_attempts = None
        self._rush_yards = None
        self._rush_touchdowns = None
        self._rush_yards_per_attempt = None
        self._rush_first_downs = None
        self._penalties = None
        self._yards_from_penalties = None
        self._first_downs_from_penalties = None
        self._percent_drives_with_points = None
        self._percent_drives_with_turnovers = None
        self._points_contributed_by_offense = None
        AbstractParser.__init__(self, team_data)
        if team_name:
            team_data = self._retrieve_team_data(year, team_name, season_page)
            self._element = team_data
        self._parse_team_data()

    def __str__(self):
        """Return string representation of the team.

        Returns
        -------
        str
            Team name, abbreviation, and year (e.g., 'Kansas City Chiefs (KAN) - 2023').
        """
        return f'{self.name} ({self.abbreviation}) - {self._year}'

    def __repr__(self):
        """Return string representation of the team."""
        return self.__str__()

    def _retrieve_team_data(self, year, team_name, season_page):
        """Fetch stats for a specific team.

        Parameters
        ----------
        year : str
            The 4-digit year of the season.
        team_name : str
            The team's 3-letter abbreviation.
        season_page : str, optional
            Path to a local season page HTML file.

        Returns
        -------
        BeautifulSoup element
            HTML row element containing team stats.

        Raises
        ------
        ValueError
            If the team abbreviation is not found.
        """
        team_data_dict, resolved_year = _fetch_all_teams(year, season_page)
        self._year = resolved_year
        team_name = team_name.upper()
        if team_name not in team_data_dict:
            raise ValueError(f'Team abbreviation {team_name} not found')
        self._rank = team_data_dict[team_name]['rank']
        return team_data_dict[team_name]['data']

    def _parse_team_data(self):
        """Parse team statistics from HTML data."""
        if not self._element:
            return
        for field in self.__dict__:
            if field in ['_rank', '_year', '_element']:
                continue
            short_field = field.lstrip('_')
            value = _parse_field(PARSING_SCHEME, self._element, short_field)
            setattr(self, field, value)

    @property
    def dataframe(self):
        """Return a pandas DataFrame of team statistics.

        Returns
        -------
        pandas.DataFrame
            DataFrame of team stats, indexed by team abbreviation.
        """
        fields_to_include = {
            'abbreviation': self.abbreviation,
            'name': self.name,
            'rank': self.rank,
            'wins': self.wins,
            'losses': self.losses,
            'win_percentage': self.win_percentage,
            'games_played': self.games_played,
            'points_for': self.points_for,
            'points_against': self.points_against,
            'points_difference': self.points_difference,
            'margin_of_victory': self.margin_of_victory,
            'strength_of_schedule': self.strength_of_schedule,
            'simple_rating_system': self.simple_rating_system,
            'offensive_simple_rating_system': self.offensive_simple_rating_system,
            'defensive_simple_rating_system': self.defensive_simple_rating_system,
            'yards': self.yards,
            'plays': self.plays,
            'yards_per_play': self.yards_per_play,
            'turnovers': self.turnovers,
            'fumbles': self.fumbles,
            'first_downs': self.first_downs,
            'pass_completions': self.pass_completions,
            'pass_attempts': self.pass_attempts,
            'pass_yards': self.pass_yards,
            'pass_touchdowns': self.pass_touchdowns,
            'interceptions': self.interceptions,
            'pass_net_yards_per_attempt': self.pass_net_yards_per_attempt,
            'pass_first_downs': self.pass_first_downs,
            'rush_attempts': self.rush_attempts,
            'rush_yards': self.rush_yards,
            'rush_touchdowns': self.rush_touchdowns,
            'rush_yards_per_attempt': self.rush_yards_per_attempt,
            'rush_first_downs': self.rush_first_downs,
            'penalties': self.penalties,
            'yards_from_penalties': self.yards_from_penalties,
            'first_downs_from_penalties': self.first_downs_from_penalties,
            'percent_drives_with_points': self.percent_drives_with_points,
            'percent_drives_with_turnovers': self.percent_drives_with_turnovers,
            'points_contributed_by_offense': self.points_contributed_by_offense,
            'post_season_result': self.post_season_result
        }
        return pd.DataFrame([fields_to_include], index=[self._abbreviation])

    @int_property_decorator
    def rank(self):
        """Return the team's league rank.

        Returns
        -------
        int or None
            Rank based on points scored.
        """
        return self._rank

    @property
    def abbreviation(self):
        """Return the team's abbreviation.

        Returns
        -------
        str or None
            3-letter abbreviation (e.g., 'KAN').
        """
        return self._abbreviation

    @property
    def name(self):
        """Return the team's full name.

        Returns
        -------
        str or None
            Full name (e.g., 'Kansas City Chiefs').
        """
        return self._name

    @property
    def schedule(self):
        """Return the team's schedule.

        Returns
        -------
        Schedule
            Schedule instance for the season.
        """
        return Schedule(self._abbreviation, self._year)

    @property
    def roster(self):
        """Return the team's roster.

        Returns
        -------
        Roster
            Roster instance for the season.
        """
        return Roster(self._abbreviation, self._year)

    @int_property_decorator
    def wins(self):
        """Return the number of wins.

        Returns
        -------
        int or None
            Number of games won.
        """
        return self._wins

    @int_property_decorator
    def losses(self):
        """Return the number of losses.

        Returns
        -------
        int or None
            Number of games lost.
        """
        return self._losses

    @float_property_decorator
    def win_percentage(self):
        """Return the win percentage.

        Returns
        -------
        float or None
            Wins divided by games played (0.0 to 1.0).
        """
        return self._win_percentage

    @int_property_decorator
    def games_played(self):
        """Return the number of games played.

        Returns
        -------
        int or None
            Total games played.
        """
        return self._games_played

    @property
    def post_season_result(self):
        """Return the postseason outcome.

        Returns
        -------
        str or None
            Constant indicating postseason result (e.g., WON_SUPER_BOWL) or None if no postseason.
        """
        if not self.schedule or len(self.schedule) == 0:
            return None
        final_game = self.schedule[-1]
        result = final_game.result
        week = final_game.week
        if result == LOSS and week in [WILD_CARD, 18]:
            return LOST_WILD_CARD
        if result == LOSS and week in [DIVISION, 19]:
            return LOST_DIVISIONAL
        if result == LOSS and week in [CONF_CHAMPIONSHIP, 20]:
            return LOST_CONF_CHAMPS
        if result == LOSS and week in [SUPER_BOWL, 21]:
            return LOST_SUPER_BOWL
        if result == WIN and week in [SUPER_BOWL, 21]:
            return WON_SUPER_BOWL
        return None

    @int_property_decorator
    def points_for(self):
        """Return total points scored.

        Returns
        -------
        int or None
            Points scored in the season.
        """
        return self._points_for

    @int_property_decorator
    def points_against(self):
        """Return total points allowed.

        Returns
        -------
        int or None
            Points allowed in the season.
        """
        return self._points_against

    @int_property_decorator
    def points_difference(self):
        """Return points differential.

        Returns
        -------
        int or None
            Points scored minus points allowed.
        """
        return self._points_difference

    @float_property_decorator
    def margin_of_victory(self):
        """Return average margin of victory.

        Returns
        -------
        float or None
            Average points difference per game.
        """
        return self._margin_of_victory

    @float_property_decorator
    def strength_of_schedule(self):
        """Return strength of schedule.

        Returns
        -------
        float or None
            Strength of schedule (0.0 average, negative is easier).
        """
        return self._strength_of_schedule

    @float_property_decorator
    def simple_rating_system(self):
        """Return simple rating system score.

        Returns
        -------
        float or None
            Team strength (0.0 average, negative is weaker).
        """
        return self._simple_rating_system

    @float_property_decorator
    def offensive_simple_rating_system(self):
        """Return offensive simple rating system score.

        Returns
        -------
        float or None
            Offensive strength (0.0 average, negative is weaker).
        """
        return self._offensive_simple_rating_system

    @float_property_decorator
    def defensive_simple_rating_system(self):
        """Return defensive simple rating system score.

        Returns
        -------
        float or None
            Defensive strength (0.0 average, negative is weaker).
        """
        return self._defensive_simple_rating_system

    @int_property_decorator
    def yards(self):
        """Return total yards gained.

        Returns
        -------
        int or None
            Total offensive yards.
        """
        return self._yards

    @int_property_decorator
    def plays(self):
        """Return total offensive plays.

        Returns
        -------
        int or None
            Number of offensive plays.
        """
        return self._plays

    @float_property_decorator
    def yards_per_play(self):
        """Return average yards per play.

        Returns
        -------
        float or None
            Average yards gained per play.
        """
        return self._yards_per_play

    @int_property_decorator
    def turnovers(self):
        """Return total turnovers.

        Returns
        -------
        int or None
            Number of turnovers committed.
        """
        return self._turnovers

    @int_property_decorator
    def fumbles(self):
        """Return total fumbles.

        Returns
        -------
        int or None
            Number of fumbles.
        """
        return self._fumbles

    @int_property_decorator
    def first_downs(self):
        """Return total first downs.

        Returns
        -------
        int or None
            Number of first downs achieved.
        """
        return self._first_downs

    @int_property_decorator
    def pass_completions(self):
        """Return total pass completions.

        Returns
        -------
        int or None
            Number of completed passes.
        """
        return self._pass_completions

    @int_property_decorator
    def pass_attempts(self):
        """Return total pass attempts.

        Returns
        -------
        int or None
            Number of passes attempted.
        """
        return self._pass_attempts

    @int_property_decorator
    def pass_yards(self):
        """Return total passing yards.

        Returns
        -------
        int or None
            Yards gained from passing.
        """
        return self._pass_yards

    @int_property_decorator
    def pass_touchdowns(self):
        """Return total passing touchdowns.

        Returns
        -------
        int or None
            Touchdowns scored from passing.
        """
        return self._pass_touchdowns

    @int_property_decorator
    def interceptions(self):
        """Return total interceptions.

        Returns
        -------
        int or None
            Number of interceptions thrown.
        """
        return self._interceptions

    @float_property_decorator
    def pass_net_yards_per_attempt(self):
        """Return net yards per pass attempt.

        Returns
        -------
        float or None
            Net yards per passing play, including sacks.
        """
        return self._pass_net_yards_per_attempt

    @int_property_decorator
    def pass_first_downs(self):
        """Return passing first downs.

        Returns
        -------
        int or None
            First downs from passing plays.
        """
        return self._pass_first_downs

    @int_property_decorator
    def rush_attempts(self):
        """Return total rushing attempts.

        Returns
        -------
        int or None
            Number of rushing plays attempted.
        """
        return self._rush_attempts

    @int_property_decorator
    def rush_yards(self):
        """Return total rushing yards.

        Returns
        -------
        int or None
            Yards gained from rushing.
        """
        return self._rush_yards

    @int_property_decorator
    def rush_touchdowns(self):
        """Return total rushing touchdowns.

        Returns
        -------
        int or None
            Touchdowns from rushing plays.
        """
        return self._rush_touchdowns

    @float_property_decorator
    def rush_yards_per_attempt(self):
        """Return average yards per rush.

        Returns
        -------
        float or None
            Average yards per rushing play.
        """
        return self._rush_yards_per_attempt

    @int_property_decorator
    def rush_first_downs(self):
        """Return rushing first downs.

        Returns
        -------
        int or None
            First downs from rushing plays.
        """
        return self._rush_first_downs

    @int_property_decorator
    def penalties(self):
        """Return total penalties.

        Returns
        -------
        int or None
            Number of penalties called.
        """
        return self._penalties

    @int_property_decorator
    def yards_from_penalties(self):
        """Return yards from penalties.

        Returns
        -------
        int or None
            Yards lost due to penalties.
        """
        return self._yards_from_penalties

    @int_property_decorator
    def first_downs_from_penalties(self):
        """Return first downs from penalties.

        Returns
        -------
        int or None
            First downs conceded due to penalties.
        """
        return self._first_downs_from_penalties

    @float_property_decorator
    def percent_drives_with_points(self):
        """Return percentage of drives with points.

        Returns
        -------
        float or None
            Percentage of drives resulting in points (0-100).
        """
        return self._percent_drives_with_points

    @float_property_decorator
    def percent_drives_with_turnovers(self):
        """Return percentage of drives with turnovers.

        Returns
        -------
        float or None
            Percentage of drives resulting in turnovers (0-100).
        """
        return self._percent_drives_with_turnovers

    @float_property_decorator
    def points_contributed_by_offense(self):
        """Return points contributed by offense.

        Returns
        -------
        float or None
            Expected points from offensive performance.
        """
        return self._points_contributed_by_offense

class Teams:
    """Collection of NFL teams and their statistics for a season.

    Retrieves and stores statistics for all NFL teams in a given season from
    pro-football-reference.com, creating a Team instance for each team.

    Parameters
    ----------
    year : str, optional
        The 4-digit year of the season (e.g., '2023'). Defaults to the current or most recent season.
    season_page : str, optional
        Path to a local HTML file of the season page to parse instead of fetching online.

    Attributes
    ----------
    teams : list
        List of Team instances for the season.
    """
    def __init__(self, year=None, season_page=None):
        self._teams = []
        self._instantiate_teams(year, season_page)

    def __getitem__(self, abbreviation):
        """Return a team by abbreviation.

        Parameters
        ----------
        abbreviation : str
            The team's 3-letter abbreviation (e.g., 'KAN').

        Returns
        -------
        Team
            The Team instance for the specified abbreviation.

        Raises
        ------
        ValueError
            If the abbreviation is not found.
        """
        abbreviation = abbreviation.upper()
        for team in self._teams:
            if team.abbreviation == abbreviation:
                return team
        raise ValueError(f'Team abbreviation {abbreviation} not found')

    def __call__(self, abbreviation):
        """Return a team by abbreviation.

        Parameters
        ----------
        abbreviation : str
            The team's 3-letter abbreviation.

        Returns
        -------
        Team
            The Team instance for the specified abbreviation.
        """
        return self.__getitem__(abbreviation)

    def __str__(self):
        """Return string representation of the teams.

        Returns
        -------
        str
            Newline-separated list of team names and abbreviations.
        """
        return '\n'.join(f'{team.name} ({team.abbreviation})' for team in self._teams)

    def __repr__(self):
        """Return string representation of the teams."""
        return self.__str__()

    def __iter__(self):
        """Return an iterator over the teams.

        Returns
        -------
        iterator
            Iterator of Team instances.
        """
        return iter(self._teams)

    def __len__(self):
        """Return the number of teams.

        Returns
        -------
        int
            Number of teams in the collection.
        """
        return len(self._teams)

    def _instantiate_teams(self, year, season_page):
        """Create Team instances for all teams.

        Parameters
        ----------
        year : str, optional
            The season year.
        season_page : str, optional
            Path to a local season page HTML file.
        """
        team_data_dict, resolved_year = _fetch_all_teams(year, season_page)
        for abbr, data in team_data_dict.items():
            team = Team(team_data=data['data'], rank=data['rank'], year=resolved_year)
            self._teams.append(team)

    @property
    def dataframes(self):
        """Return a pandas DataFrame of all teams.

        Returns
        -------
        pandas.DataFrame
            DataFrame of team statistics, indexed by team abbreviation.
        """
        return pd.concat([team.dataframe for team in self._teams]) if self._teams else pd.DataFrame()