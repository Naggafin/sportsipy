import pandas as pd
from ..base import AbstractParser, int_property_decorator, float_property_decorator, _parse_entity_data, _fetch_all_teams
from .constants import PARSING_SCHEME
from .roster import Roster
from .schedule import Schedule

class Team(AbstractParser):
    """Team statistics and information for an NBA season.

    Retrieves and stores comprehensive team statistics, such as wins, losses, field goal
    percentages, and opponent stats, for a given team and season from basketball-reference.com.
    Provides access to the team's roster and schedule via related classes.

    Parameters
    ----------
    team_name : str, optional
        The team's 3-letter abbreviation (e.g., 'HOU' for Houston Rockets). Required if called directly.
    team_data : str, optional
        HTML string containing team stats rows. Used when instantiated via the Teams class.
    rank : int, optional
        The team's league rank based on points scored per game. Used when instantiated via Teams.
    year : str, optional
        The 4-digit year for the season (e.g., '2023'). Defaults to the current season.
    season_file : str, optional
        Path to a local HTML file containing the season page data.

    Attributes
    ----------
    abbreviation : str
        The team's 3-letter abbreviation.
    name : str
        The team's full name.
    year : str
        The season year.
    rank : int
        The team's league rank.
    """
    def __init__(self, team_name=None, team_data=None, rank=None, year=None, season_file=None):
        self._year = year
        self._rank = rank
        self._abbreviation = None
        self._name = None
        self._games_played = None
        self._wins = None
        self._losses = None
        self._win_percentage = None
        self._minutes_played = None
        self._field_goals = None
        self._field_goal_attempts = None
        self._field_goal_percentage = None
        self._three_point_field_goals = None
        self._three_point_field_goal_attempts = None
        self._three_point_field_goal_percentage = None
        self._two_point_field_goals = None
        self._two_point_field_goal_attempts = None
        self._two_point_field_goal_percentage = None
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
        self._opp_field_goals = None
        self._opp_field_goal_attempts = None
        self._opp_field_goal_percentage = None
        self._opp_three_point_field_goals = None
        self._opp_three_point_field_goal_attempts = None
        self._opp_three_point_field_goal_percentage = None
        self._opp_two_point_field_goals = None
        self._opp_two_point_field_goal_attempts = None
        self._opp_two_point_field_goal_percentage = None
        self._opp_free_throws = None
        self._opp_free_throw_attempts = None
        self._opp_free_throw_percentage = None
        self._opp_offensive_rebounds = None
        self._opp_defensive_rebounds = None
        self._opp_total_rebounds = None
        self._opp_assists = None
        self._opp_steals = None
        self._opp_blocks = None
        self._opp_turnovers = None
        self._opp_personal_fouls = None
        self._opp_points = None

        AbstractParser.__init__(self, team_data)
        if team_name:
            team_data = self._retrieve_team_data(year, team_name, season_file)
        if team_data:
            fields_to_skip = {'year', 'rank'}
            _parse_entity_data(self, team_data, PARSING_SCHEME, fields_to_skip)

    def __str__(self):
        """Return the string representation of the team.

        Returns
        -------
        str
            Team name, abbreviation, and year (e.g., 'Houston Rockets (HOU) - 2023').
        """
        return f'{self.name} ({self.abbreviation}) - {self._year}'

    def __repr__(self):
        """Return the string representation of the team.

        Returns
        -------
        str
            Team name, abbreviation, and year.
        """
        return self.__str__()

    def _retrieve_team_data(self, year, team_name, season_file=None):
        """Retrieve stats for a specific team.

        Parameters
        ----------
        year : str
            The 4-digit year for the season.
        team_name : str
            The team's 3-letter abbreviation (e.g., 'HOU').
        season_file : str, optional
            Path to a local HTML file containing season data.

        Returns
        -------
        str
            HTML string containing team stats.

        Raises
        ------
        ValueError
            If the team data cannot be retrieved.
        """
        team_data_dict, year = _fetch_all_teams(year, season_file)
        self._year = year
        if team_name not in team_data_dict:
            raise ValueError(f'Team {team_name} not found for year {year}')
        self._rank = team_data_dict[team_name]['rank']
        return team_data_dict[team_name]['data']

    @property
    def dataframe(self):
        """Return a pandas DataFrame of team statistics.

        Returns
        -------
        pandas.DataFrame
            DataFrame with team stats, indexed by team abbreviation.
        """
        fields_to_include = {
            'abbreviation': self.abbreviation,
            'name': self.name,
            'year': self._year,
            'rank': self.rank,
            'games_played': self.games_played,
            'wins': self.wins,
            'losses': self.losses,
            'win_percentage': self.win_percentage,
            'minutes_played': self.minutes_played,
            'field_goals': self.field_goals,
            'field_goal_attempts': self.field_goal_attempts,
            'field_goal_percentage': self.field_goal_percentage,
            'three_point_field_goals': self.three_point_field_goals,
            'three_point_field_goal_attempts': self.three_point_field_goal_attempts,
            'three_point_field_goal_percentage': self.three_point_field_goal_percentage,
            'two_point_field_goals': self.two_point_field_goals,
            'two_point_field_goal_attempts': self.two_point_field_goal_attempts,
            'two_point_field_goal_percentage': self.two_point_field_goal_percentage,
            'free_throws': self.free_throws,
            'free_throw_attempts': self.free_throw_attempts,
            'free_throw_percentage': self.free_throw_percentage,
            'offensive_rebounds': self.offensive_rebounds,
            'defensive_rebounds': self.defensive_rebounds,
            'total_rebounds': self.total_rebounds,
            'assists': self.assists,
            'steals': self.steals,
            'blocks': self.blocks,
            'turnovers': self.turnovers,
            'personal_fouls': self.personal_fouls,
            'points': self.points,
            'opp_field_goals': self.opp_field_goals,
            'opp_field_goal_attempts': self.opp_field_goal_attempts,
            'opp_field_goal_percentage': self.opp_field_goal_percentage,
            'opp_three_point_field_goals': self.opp_three_point_field_goals,
            'opp_three_point_field_goal_attempts': self.opp_three_point_field_goal_attempts,
            'opp_three_point_field_goal_percentage': self.opp_three_point_field_goal_percentage,
            'opp_two_point_field_goals': self.opp_two_point_field_goals,
            'opp_two_point_field_goal_attempts': self.opp_two_point_field_goal_attempts,
            'opp_two_point_field_goal_percentage': self.opp_two_point_field_goal_percentage,
            'opp_free_throws': self.opp_free_throws,
            'opp_free_throw_attempts': self.opp_free_throw_attempts,
            'opp_free_throw_percentage': self.opp_free_throw_percentage,
            'opp_offensive_rebounds': self.opp_offensive_rebounds,
            'opp_defensive_rebounds': self.opp_defensive_rebounds,
            'opp_total_rebounds': self.opp_total_rebounds,
            'opp_assists': self.opp_assists,
            'opp_steals': self.opp_steals,
            'opp_blocks': self.opp_blocks,
            'opp_turnovers': self.opp_turnovers,
            'opp_personal_fouls': self.opp_personal_fouls,
            'opp_points': self.opp_points
        }
        return pd.DataFrame([fields_to_include], index=[self._abbreviation])

    @int_property_decorator
    def rank(self):
        """Return the team's league rank.

        Returns
        -------
        int
            Rank based on points scored per game.
        """
        return self._rank

    @property
    def abbreviation(self):
        """Return the team's abbreviation.

        Returns
        -------
        str
            The 3-letter abbreviation (e.g., 'HOU').
        """
        return self._abbreviation

    @property
    def name(self):
        """Return the team's full name.

        Returns
        -------
        str
            The full team name (e.g., 'Houston Rockets').
        """
        return self._name

    @property
    def schedule(self):
        """Return the team's season schedule.

        Returns
        -------
        Schedule
            An instance of the Schedule class for the team's season.
        """
        return Schedule(self._abbreviation, self._year)

    @property
    def roster(self):
        """Return the team's roster.

        Returns
        -------
        Roster
            An instance of the Roster class for the team's season.
        """
        return Roster(self._abbreviation, self._year)

    @int_property_decorator
    def games_played(self):
        """Return total games played.

        Returns
        -------
        int or None
            Total games played in the season.
        """
        return self._games_played

    @int_property_decorator
    def wins(self):
        """Return total wins.

        Returns
        -------
        int or None
            Total games won in the season.
        """
        return self._wins

    @int_property_decorator
    def losses(self):
        """Return total losses.

        Returns
        -------
        int or None
            Total games lost in the season.
        """
        return self._losses

    @float_property_decorator
    def win_percentage(self):
        """Return win percentage.

        Returns
        -------
        float or None
            Wins divided by games played (0-1).
        """
        return self._win_percentage

    @int_property_decorator
    def minutes_played(self):
        """Return total minutes played.

        Returns
        -------
        int or None
            Total minutes played by all players.
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
            Field goals made divided by attempts (0-1).
        """
        return self._field_goal_percentage

    @int_property_decorator
    def three_point_field_goals(self):
        """Return total three-point field goals made.

        Returns
        -------
        int or None
            Total three-pointers made.
        """
        return self._three_point_field_goals

    @int_property_decorator
    def three_point_field_goal_attempts(self):
        """Return total three-point field goal attempts.

        Returns
        -------
        int or None
            Total three-point attempts.
        """
        return self._three_point_field_goal_attempts

    @float_property_decorator
    def three_point_field_goal_percentage(self):
        """Return three-point field goal percentage.

        Returns
        -------
        float or None
            Three-pointers made divided by attempts (0-1).
        """
        return self._three_point_field_goal_percentage

    @int_property_decorator
    def two_point_field_goals(self):
        """Return total two-point field goals made.

        Returns
        -------
        int or None
            Total two-pointers made.
        """
        return self._two_point_field_goals

    @int_property_decorator
    def two_point_field_goal_attempts(self):
        """Return total two-point field goal attempts.

        Returns
        -------
        int or None
            Total two-point attempts.
        """
        return self._two_point_field_goal_attempts

    @float_property_decorator
    def two_point_field_goal_percentage(self):
        """Return two-point field goal percentage.

        Returns
        -------
        float or None
            Two-pointers made divided by attempts (0-1).
        """
        return self._two_point_field_goal_percentage

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
            Free throws made divided by attempts (0-1).
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
            Total field goals assisted.
        """
        return self._assists

    @int_property_decorator
    def steals(self):
        """Return total steals.

        Returns
        -------
        int or None
            Total steals from opponents.
        """
        return self._steals

    @int_property_decorator
    def blocks(self):
        """Return total blocks.

        Returns
        -------
        int or None
            Total opponent shots blocked.
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
            Total fouls committed.
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

    @int_property_decorator
    def opp_field_goals(self):
        """Return opponent's total field goals made.

        Returns
        -------
        int or None
            Total field goals by opponents.
        """
        return self._opp_field_goals

    @int_property_decorator
    def opp_field_goal_attempts(self):
        """Return opponent's total field goal attempts.

        Returns
        -------
        int or None
            Total field goals attempted by opponents.
        """
        return self._opp_field_goal_attempts

    @float_property_decorator
    def opp_field_goal_percentage(self):
        """Return opponent's field goal percentage.

        Returns
        -------
        float or None
            Opponent's field goals made divided by attempts (0-1).
        """
        return self._opp_field_goal_percentage

    @int_property_decorator
    def opp_three_point_field_goals(self):
        """Return opponent's three-point field goals made.

        Returns
        -------
        int or None
            Total three-pointers by opponents.
        """
        return self._opp_three_point_field_goals

    @int_property_decorator
    def opp_three_point_field_goal_attempts(self):
        """Return opponent's three-point field goal attempts.

        Returns
        -------
        int or None
            Total three-point attempts by opponents.
        """
        return self._opp_three_point_field_goal_attempts

    @float_property_decorator
    def opp_three_point_field_goal_percentage(self):
        """Return opponent's three-point field goal percentage.

        Returns
        -------
        float or None
            Opponent's three-pointers made divided by attempts (0-1).
        """
        return self._opp_three_point_field_goal_percentage

    @int_property_decorator
    def opp_two_point_field_goals(self):
        """Return opponent's two-point field goals made.

        Returns
        -------
        int or None
            Total two-pointers by opponents.
        """
        return self._opp_two_point_field_goals

    @int_property_decorator
    def opp_two_point_field_goal_attempts(self):
        """Return opponent's two-point field goal attempts.

        Returns
        -------
        int or None
            Total two-point attempts by opponents.
        """
        return self._opp_two_point_field_goal_attempts

    @float_property_decorator
    def opp_two_point_field_goal_percentage(self):
        """Return opponent's two-point field goal percentage.

        Returns
        -------
        float or None
            Opponent's two-pointers made divided by attempts (0-1).
        """
        return self._opp_two_point_field_goal_percentage

    @int_property_decorator
    def opp_free_throws(self):
        """Return opponent's free throws made.

        Returns
        -------
        int or None
            Total free throws by opponents.
        """
        return self._opp_free_throws

    @int_property_decorator
    def opp_free_throw_attempts(self):
        """Return opponent's free throw attempts.

        Returns
        -------
        int or None
            Total free throw attempts by opponents.
        """
        return self._opp_free_throw_attempts

    @float_property_decorator
    def opp_free_throw_percentage(self):
        """Return opponent's free throw percentage.

        Returns
        -------
        float or None
            Opponent's free throws made divided by attempts (0-1).
        """
        return self._opp_free_throw_percentage

    @int_property_decorator
    def opp_offensive_rebounds(self):
        """Return opponent's offensive rebounds.

        Returns
        -------
        int or None
            Total offensive rebounds by opponents.
        """
        return self._opp_offensive_rebounds

    @int_property_decorator
    def opp_defensive_rebounds(self):
        """Return opponent's defensive rebounds.

        Returns
        -------
        int or None
            Total defensive rebounds by opponents.
        """
        return self._opp_defensive_rebounds

    @int_property_decorator
    def opp_total_rebounds(self):
        """Return opponent's total rebounds.

        Returns
        -------
        int or None
            Total rebounds by opponents.
        """
        return self._opp_total_rebounds

    @int_property_decorator
    def opp_assists(self):
        """Return opponent's assists.

        Returns
        -------
        int or None
            Total field goals assisted by opponents.
        """
        return self._opp_assists

    @int_property_decorator
    def opp_steals(self):
        """Return opponent's steals.

        Returns
        -------
        int or None
            Total steals by opponents.
        """
        return self._opp_steals

    @int_property_decorator
    def opp_blocks(self):
        """Return opponent's blocks.

        Returns
        -------
        int or None
            Total shots blocked by opponents.
        """
        return self._opp_blocks

    @int_property_decorator
    def opp_turnovers(self):
        """Return opponent's turnovers.

        Returns
        -------
        int or None
            Total turnovers by opponents.
        """
        return self._opp_turnovers

    @int_property_decorator
    def opp_personal_fouls(self):
        """Return opponent's personal fouls.

        Returns
        -------
        int or None
            Total fouls committed by opponents.
        """
        return self._opp_personal_fouls

    @int_property_decorator
    def opp_points(self):
        """Return opponent's points scored.

        Returns
        -------
        int or None
            Total points scored by opponents.
        """
        return self._opp_points

class Teams:
    """Collection of NBA team statistics for a season.

    Manages a list of Team instances for all NBA teams in a given season, providing
    access to team statistics and information from basketball-reference.com.

    Parameters
    ----------
    year : str, optional
        The 4-digit year for the season (e.g., '2023'). Defaults to the current season.
    season_file : str, optional
        Path to a local HTML file containing the season page data.

    Attributes
    ----------
    dataframes : pandas.DataFrame
        A DataFrame containing all team statistics, indexed by team abbreviation.
    """
    def __init__(self, year=None, season_file=None):
        self._teams = []
        team_data_dict, year = _fetch_all_teams(year, season_file)
        self._instantiate_teams(team_data_dict, year)

    def __getitem__(self, abbreviation):
        """Access a Team instance by abbreviation.

        Parameters
        ----------
        abbreviation : str
            The team's 3-letter abbreviation (e.g., 'HOU').

        Returns
        -------
        Team
            The Team instance for the specified abbreviation.

        Raises
        ------
        ValueError
            If the team abbreviation is not found.
        """
        for team in self._teams:
            if team.abbreviation.upper() == abbreviation.upper():
                return team
        raise ValueError(f'Team abbreviation {abbreviation} not found')

    def __call__(self, abbreviation):
        """Access a Team instance by abbreviation.

        Parameters
        ----------
        abbreviation : str
            The team's 3-letter abbreviation (e.g., 'HOU').

        Returns
        -------
        Team
            The Team instance for the specified abbreviation.
        """
        return self.__getitem__(abbreviation)

    def __str__(self):
        """Return the string representation of the teams.

        Returns
        -------
        str
            Newline-separated list of team names and abbreviations.
        """
        return '\n'.join(f'{team.name} ({team.abbreviation})' for team in self._teams)

    def __repr__(self):
        """Return the string representation of the teams.

        Returns
        -------
        str
            Newline-separated list of team names and abbreviations.
        """
        return self.__str__()

    def __iter__(self):
        """Return an iterator over Team instances.

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
            Number of teams in the season.
        """
        return len(self._teams)

    def _instantiate_teams(self, team_data_dict, year):
        """Create Team instances for all teams.

        Parameters
        ----------
        team_data_dict : dict
            Dictionary mapping team abbreviations to their data and rank.
        year : str
            The season year.
        """
        for team_data in team_data_dict.values():
            team = Team(team_data=team_data['data'], rank=team_data['rank'], year=year)
            self._teams.append(team)

    @property
    def dataframes(self):
        """Return a DataFrame of all team statistics.

        Returns
        -------
        pandas.DataFrame
            DataFrame with each team's stats, indexed by team abbreviation.
        """
        return pd.concat([team.dataframe for team in self._teams])