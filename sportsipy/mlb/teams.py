import pandas as pd
from typing import Optional, List, Dict
from bs4 import BeautifulSoup
from ..base import (int_property_decorator, float_property_decorator, record_property_decorator,
                    _parse_field, _clean_stat, _fetch_html, _retrieve_team_data_dict)
from .constants import (ELEMENT_INDEX, PARSING_SCHEME, TEAM_ELEMENT, TEAM_STATS_URL,
                       STANDINGS_URL, LEAGUE_URL)
from .roster import Roster
from .schedule import Schedule

class Team:
    """An object containing all of a team's season information for MLB.

    Parses and stores team statistics and identifiers, such as rank, name, abbreviation,
    wins, losses, and advanced metrics like batting average and ERA, for a given season.
    Can be instantiated directly with a team abbreviation or via the Teams class.

    Parameters
    ----------
    team_name : str, optional
        The 3-letter abbreviation of the team (e.g., 'HOU' for Houston Astros).
    team_data : str, optional
        HTML string containing team stats, used when called from Teams class.
    rank : str, optional
        Team's league rank based on win percentage, used when called from Teams class.
    year : str, optional
        The year to pull stats for (e.g., '2023'). Defaults to current year if None.
    standings_file : str, optional
        Path to a local HTML file of the Standings page for the year.
    teams_file : str, optional
        Path to a local HTML file of the League page for the year.

    Attributes
    ----------
    abbreviation : str
        The team's 3-letter abbreviation (e.g., 'HOU').
    name : str
        The team's full name (e.g., 'Houston Astros').
    year : str
        The season year.
    roster : Roster
        The team's roster for the season.
    schedule : Schedule
        The team's game schedule for the season.
    """
    def __init__(self, team_name: Optional[str] = None, team_data: Optional[str] = None,
                 rank: Optional[str] = None, year: Optional[str] = None,
                 standings_file: Optional[str] = None, teams_file: Optional[str] = None):
        self._year = year
        self._rank = rank
        self._abbreviation: Optional[str] = None
        self._name: Optional[str] = None
        self._league: Optional[str] = None
        self._games: Optional[str] = None
        self._wins: Optional[str] = None
        self._losses: Optional[str] = None
        self._win_percentage: Optional[str] = None
        self._streak: Optional[str] = None
        self._runs: Optional[str] = None
        self._runs_against: Optional[str] = None
        self._run_difference: Optional[str] = None
        self._strength_of_schedule: Optional[str] = None
        self._simple_rating_system: Optional[str] = None
        self._pythagorean_win_loss: Optional[str] = None
        self._luck: Optional[str] = None
        self._interleague_record: Optional[str] = None
        self._home_record: Optional[str] = None
        self._away_record: Optional[str] = None
        self._extra_inning_record: Optional[str] = None
        self._single_run_record: Optional[str] = None
        self._record_vs_right_handed_pitchers: Optional[str] = None
        self._record_vs_left_handed_pitchers: Optional[str] = None
        self._record_vs_teams_over_500: Optional[str] = None
        self._record_vs_teams_under_500: Optional[str] = None
        self._last_ten_games_record: Optional[str] = None
        self._last_twenty_games_record: Optional[str] = None
        self._last_thirty_games_record: Optional[str] = None
        self._number_players_used: Optional[str] = None
        self._average_batter_age: Optional[str] = None
        self._plate_appearances: Optional[str] = None
        self._at_bats: Optional[str] = None
        self._total_runs: Optional[str] = None
        self._hits: Optional[str] = None
        self._doubles: Optional[str] = None
        self._triples: Optional[str] = None
        self._home_runs: Optional[str] = None
        self._runs_batted_in: Optional[str] = None
        self._stolen_bases: Optional[str] = None
        self._times_caught_stealing: Optional[str] = None
        self._bases_on_balls: Optional[str] = None
        self._times_struck_out: Optional[str] = None
        self._batting_average: Optional[str] = None
        self._on_base_percentage: Optional[str] = None
        self._slugging_percentage: Optional[str] = None
        self._on_base_plus_slugging_percentage: Optional[str] = None
        self._on_base_plus_slugging_percentage_plus: Optional[str] = None
        self._total_bases: Optional[str] = None
        self._grounded_into_double_plays: Optional[str] = None
        self._times_hit_by_pitch: Optional[str] = None
        self._sacrifice_hits: Optional[str] = None
        self._sacrifice_flies: Optional[str] = None
        self._intentional_bases_on_balls: Optional[str] = None
        self._runners_left_on_base: Optional[str] = None
        self._number_of_pitchers: Optional[str] = None
        self._average_pitcher_age: Optional[str] = None
        self._runs_allowed_per_game: Optional[str] = None
        self._earned_runs_against: Optional[str] = None
        self._games_finished: Optional[str] = None
        self._complete_games: Optional[str] = None
        self._shutouts: Optional[str] = None
        self._complete_game_shutouts: Optional[str] = None
        self._saves: Optional[str] = None
        self._innings_pitched: Optional[str] = None
        self._hits_allowed: Optional[str] = None
        self._home_runs_against: Optional[str] = None
        self._bases_on_walks_given: Optional[str] = None
        self._strikeouts: Optional[str] = None
        self._hit_pitcher: Optional[str] = None
        self._balks: Optional[str] = None
        self._wild_pitches: Optional[str] = None
        self._batters_faced: Optional[str] = None
        self._earned_runs_against_plus: Optional[str] = None
        self._fielding_independent_pitching: Optional[str] = None
        self._whip: Optional[str] = None
        self._hits_per_nine_innings: Optional[str] = None
        self._home_runs_per_nine_innings: Optional[str] = None
        self._bases_on_walks_given_per_nine_innings: Optional[str] = None
        self._strikeouts_per_nine_innings: Optional[str] = None
        self._strikeouts_per_base_on_balls: Optional[str] = None
        self._opposing_runners_left_on_base: Optional[str] = None

        if team_name:
            team_data = self._retrieve_team_data(year, team_name, standings_file, teams_file)

        self._parse_team_data(team_data)

    def __str__(self) -> str:
        """Return the string representation of the team."""
        return f'{self.name} ({self.abbreviation}) - {self._year}'

    def __repr__(self) -> str:
        """Return the string representation of the team."""
        return self.__str__()

    def _retrieve_team_data(self, year: Optional[str], team_name: str,
                            standings_file: Optional[str] = None,
                            teams_file: Optional[str] = None) -> Optional[BeautifulSoup]:
        """Pull all stats for a specific team.

        Parameters
        ----------
        year : str, optional
            The year to pull stats for.
        team_name : str
            The team's 3-letter abbreviation (e.g., 'HOU').
        standings_file : str, optional
            Path to a local Standings HTML file.
        teams_file : str, optional
            Path to a local League HTML file.

        Returns
        -------
        BeautifulSoup or None
            Parsed HTML containing team stats or None if fetching fails.
        """
        if standings_file and teams_file:
            with open(standings_file, 'r') as f:
                standings_soup = BeautifulSoup(f.read(), 'html.parser')
            with open(teams_file, 'r') as f:
                league_soup = BeautifulSoup(f.read(), 'html.parser')
            team_data_dict = {team_name: {'data': str(standings_soup) + str(league_soup), 'rank': None}}
            self._year = year or str(datetime.now().year)
        else:
            team_data_dict, year = _retrieve_team_data_dict(year, STANDINGS_URL, LEAGUE_URL)
            self._year = year
        if team_name not in team_data_dict:
            return None
        self._rank = team_data_dict[team_name]['rank']
        return BeautifulSoup(team_data_dict[team_name]['data'], 'html.parser')

    def _parse_name(self, soup: BeautifulSoup) -> None:
        """Parse the team's name from HTML.

        Parameters
        ----------
        soup : BeautifulSoup
            Parsed HTML containing team data.
        """
        if not soup:
            return
        name_tag = soup.select_one(PARSING_SCHEME.get('name'))
        name = name_tag.get('title', '').strip() if name_tag else None
        setattr(self, '_name', name)

    def _parse_abbreviation(self, soup: BeautifulSoup) -> None:
        """Parse the team's abbreviation from HTML.

        Parameters
        ----------
        soup : BeautifulSoup
            Parsed HTML containing team data.
        """
        if not soup:
            return
        name_tag = soup.select_one(PARSING_SCHEME.get('name'))
        abbr = name_tag.get('data-stat', '').strip() if name_tag else None
        setattr(self, '_abbreviation', abbr)

    def _parse_team_data(self, soup: Optional[BeautifulSoup]) -> None:
        """Parse all team data from HTML.

        Parameters
        ----------
        soup : BeautifulSoup, optional
            Parsed HTML containing team stats.
        """
        if not soup:
            return
        self._parse_name(soup)
        self._parse_abbreviation(soup)
        for field in self.__dict__:
            if field in ('_year', '_rank', '_name', '_abbreviation'):
                continue
            short_field = field.lstrip('_')
            index = ELEMENT_INDEX.get(short_field, 0)
            value = _clean_stat(_parse_field(PARSING_SCHEME, soup, short_field, index))
            setattr(self, field, value)

    @property
    def dataframe(self) -> Optional[pd.DataFrame]:
        """Return a pandas DataFrame of team stats.

        Returns
        -------
        pd.DataFrame or None
            DataFrame of team stats, indexed by abbreviation, or None if no data.
        """
        if not self._abbreviation:
            return None
        fields = {
            'abbreviation': self.abbreviation,
            'at_bats': self.at_bats,
            'average_batter_age': self.average_batter_age,
            'average_pitcher_age': self.average_pitcher_age,
            'away_losses': self.away_losses,
            'away_record': self.away_record,
            'away_wins': self.away_wins,
            'balks': self.balks,
            'bases_on_balls': self.bases_on_balls,
            'bases_on_walks_given': self.bases_on_walks_given,
            'bases_on_walks_given_per_nine_innings': self.bases_on_walks_given_per_nine_innings,
            'batters_faced': self.batters_faced,
            'batting_average': self.batting_average,
            'complete_game_shutouts': self.complete_game_shutouts,
            'complete_games': self.complete_games,
            'doubles': self.doubles,
            'earned_runs_against': self.earned_runs_against,
            'earned_runs_against_plus': self.earned_runs_against_plus,
            'extra_inning_losses': self.extra_inning_losses,
            'extra_inning_record': self.extra_inning_record,
            'extra_inning_wins': self.extra_inning_wins,
            'fielding_independent_pitching': self.fielding_independent_pitching,
            'games': self.games,
            'games_finished': self.games_finished,
            'grounded_into_double_plays': self.grounded_into_double_plays,
            'hit_pitcher': self.hit_pitcher,
            'hits': self.hits,
            'hits_allowed': self.hits_allowed,
            'hits_per_nine_innings': self.hits_per_nine_innings,
            'home_losses': self.home_losses,
            'home_record': self.home_record,
            'home_runs': self.home_runs,
            'home_runs_against': self.home_runs_against,
            'home_runs_per_nine_innings': self.home_runs_per_nine_innings,
            'home_wins': self.home_wins,
            'innings_pitched': self.innings_pitched,
            'intentional_bases_on_balls': self.intentional_bases_on_balls,
            'interleague_record': self.interleague_record,
            'last_ten_games_record': self.last_ten_games_record,
            'last_thirty_games_record': self.last_thirty_games_record,
            'last_twenty_games_record': self.last_twenty_games_record,
            'league': self.league,
            'losses': self.losses,
            'losses_last_ten_games': self.losses_last_ten_games,
            'losses_last_thirty_games': self.losses_last_thirty_games,
            'losses_last_twenty_games': self.losses_last_twenty_games,
            'losses_vs_left_handed_pitchers': self.losses_vs_left_handed_pitchers,
            'losses_vs_right_handed_pitchers': self.losses_vs_right_handed_pitchers,
            'losses_vs_teams_over_500': self.losses_vs_teams_over_500,
            'losses_vs_teams_under_500': self.losses_vs_teams_under_500,
            'luck': self.luck,
            'name': self.name,
            'number_of_pitchers': self.number_of_pitchers,
            'number_players_used': self.number_players_used,
            'on_base_percentage': self.on_base_percentage,
            'on_base_plus_slugging_percentage': self.on_base_plus_slugging_percentage,
            'on_base_plus_slugging_percentage_plus': self.on_base_plus_slugging_percentage_plus,
            'opposing_runners_left_on_base': self.opposing_runners_left_on_base,
            'plate_appearances': self.plate_appearances,
            'pythagorean_win_loss': self.pythagorean_win_loss,
            'rank': self.rank,
            'record_vs_left_handed_pitchers': self.record_vs_left_handed_pitchers,
            'record_vs_right_handed_pitchers': self.record_vs_right_handed_pitchers,
            'record_vs_teams_over_500': self.record_vs_teams_over_500,
            'record_vs_teams_under_500': self.record_vs_teams_under_500,
            'run_difference': self.run_difference,
            'runners_left_on_base': self.runners_left_on_base,
            'runs': self.runs,
            'runs_against': self.runs_against,
            'runs_allowed_per_game': self.runs_allowed_per_game,
            'runs_batted_in': self.runs_batted_in,
            'sacrifice_flies': self.sacrifice_flies,
            'sacrifice_hits': self.sacrifice_hits,
            'saves': self.saves,
            'shutouts': self.shutouts,
            'simple_rating_system': self.simple_rating_system,
            'single_run_losses': self.single_run_losses,
            'single_run_record': self.single_run_record,
            'single_run_wins': self.single_run_wins,
            'slugging_percentage': self.slugging_percentage,
            'stolen_bases': self.stolen_bases,
            'streak': self.streak,
            'strength_of_schedule': self.strength_of_schedule,
            'strikeouts': self.strikeouts,
            'strikeouts_per_base_on_balls': self.strikeouts_per_base_on_balls,
            'strikeouts_per_nine_innings': self.strikeouts_per_nine_innings,
            'times_caught_stealing': self.times_caught_stealing,
            'times_hit_by_pitch': self.times_hit_by_pitch,
            'times_struck_out': self.times_struck_out,
            'total_bases': self.total_bases,
            'total_runs': self.total_runs,
            'triples': self.triples,
            'whip': self.whip,
            'wild_pitches': self.wild_pitches,
            'win_percentage': self.win_percentage,
            'wins': self.wins,
            'wins_last_ten_games': self.wins_last_ten_games,
            'wins_last_thirty_games': self.wins_last_thirty_games,
            'wins_last_twenty_games': self.wins_last_twenty_games,
            'wins_vs_left_handed_pitchers': self.wins_vs_left_handed_pitchers,
            'wins_vs_right_handed_pitchers': self.wins_vs_right_handed_pitchers,
            'wins_vs_teams_over_500': self.wins_vs_teams_over_500,
            'wins_vs_teams_under_500': self.wins_vs_teams_under_500
        }
        return pd.DataFrame([fields], index=[self._abbreviation])

    @int_property_decorator
    def rank(self) -> Optional[int]:
        """Return the team's rank based on win percentage."""
        return self._rank

    @property
    def abbreviation(self) -> Optional[str]:
        """Return the team's 3-letter abbreviation (e.g., 'HOU')."""
        return self._abbreviation

    @property
    def schedule(self) -> Schedule:
        """Return the team's complete season schedule."""
        return Schedule(self._abbreviation, self._year)

    @property
    def roster(self) -> Roster:
        """Return the team's roster with all players' career stats."""
        return Roster(self._abbreviation, self._year)

    @property
    def name(self) -> Optional[str]:
        """Return the team's full name (e.g., 'Houston Astros')."""
        return self._name

    @property
    def league(self) -> Optional[str]:
        """Return the league abbreviation (e.g., 'AL' for American League)."""
        return self._league

    @int_property_decorator
    def games(self) -> Optional[int]:
        """Return the number of games played in the season."""
        return self._games

    @int_property_decorator
    def wins(self) -> Optional[int]:
        """Return the total number of wins in the season."""
        return self._wins

    @int_property_decorator
    def losses(self) -> Optional[int]:
        """Return the total number of losses in the season."""
        return self._losses

    @float_property_decorator
    def win_percentage(self) -> Optional[float]:
        """Return the win percentage (wins / games played, 0-1)."""
        return self._win_percentage

    @property
    def streak(self) -> Optional[str]:
        """Return the current win/loss streak (e.g., 'W 3')."""
        return self._streak

    @float_property_decorator
    def runs(self) -> Optional[float]:
        """Return the average runs scored per game."""
        return self._runs

    @float_property_decorator
    def runs_against(self) -> Optional[float]:
        """Return the average runs scored against per game."""
        return self._runs_against

    @float_property_decorator
    def run_difference(self) -> Optional[float]:
        """Return the difference between runs scored and allowed per game."""
        return self._run_difference

    @float_property_decorator
    def strength_of_schedule(self) -> Optional[float]:
        """Return the strength of schedule (0.0 is average)."""
        return self._strength_of_schedule

    @float_property_decorator
    def simple_rating_system(self) -> Optional[float]:
        """Return the simple rating system (runs above average per game)."""
        return self._simple_rating_system

    @property
    def pythagorean_win_loss(self) -> Optional[str]:
        """Return the expected win-loss record based on runs (e.g., '90-72')."""
        return self._pythagorean_win_loss

    @int_property_decorator
    def luck(self) -> Optional[int]:
        """Return the difference between actual and pythagorean wins."""
        return self._luck

    @property
    def interleague_record(self) -> Optional[str]:
        """Return the interleague record (e.g., '10-10')."""
        return self._interleague_record

    @property
    def home_record(self) -> Optional[str]:
        """Return the home record (e.g., '45-36')."""
        return self._home_record

    @record_property_decorator
    def home_wins(self) -> Optional[int]:
        """Return the number of home wins."""
        return self._home_record

    @record_property_decorator
    def home_losses(self) -> Optional[int]:
        """Return the number of home losses."""
        return self._home_record

    @property
    def away_record(self) -> Optional[str]:
        """Return the away record (e.g., '40-41')."""
        return self._away_record

    @record_property_decorator
    def away_wins(self) -> Optional[int]:
        """Return the number of away wins."""
        return self._away_record

    @record_property_decorator
    def away_losses(self) -> Optional[int]:
        """Return the number of away losses."""
        return self._away_record

    @property
    def extra_inning_record(self) -> Optional[str]:
        """Return the extra-inning record (e.g., '5-3')."""
        return self._extra_inning_record

    @record_property_decorator
    def extra_inning_wins(self) -> Optional[int]:
        """Return the number of extra-inning wins."""
        return self._extra_inning_record

    @record_property_decorator
    def extra_inning_losses(self) -> Optional[int]:
        """Return the number of extra-inning losses."""
        return self._extra_inning_record

    @property
    def single_run_record(self) -> Optional[str]:
        """Return the record in one-run games (e.g., '20-15')."""
        return self._single_run_record

    @record_property_decorator
    def single_run_wins(self) -> Optional[int]:
        """Return the number of one-run wins."""
        return self._single_run_record

    @record_property_decorator
    def single_run_losses(self) -> Optional[int]:
        """Return the number of one-run losses."""
        return self._single_run_record

    @property
    def record_vs_right_handed_pitchers(self) -> Optional[str]:
        """Return the record against right-handed pitchers (e.g., '60-50')."""
        return self._record_vs_right_handed_pitchers

    @record_property_decorator
    def wins_vs_right_handed_pitchers(self) -> Optional[int]:
        """Return the number of wins against right-handed pitchers."""
        return self._record_vs_right_handed_pitchers

    @record_property_decorator
    def losses_vs_right_handed_pitchers(self) -> Optional[int]:
        """Return the number of losses against right-handed pitchers."""
        return self._record_vs_right_handed_pitchers

    @property
    def record_vs_left_handed_pitchers(self) -> Optional[str]:
        """Return the record against left-handed pitchers (e.g., '25-20')."""
        return self._record_vs_left_handed_pitchers

    @record_property_decorator
    def wins_vs_left_handed_pitchers(self) -> Optional[int]:
        """Return the number of wins against left-handed pitchers."""
        return self._record_vs_left_handed_pitchers

    @record_property_decorator
    def losses_vs_left_handed_pitchers(self) -> Optional[int]:
        """Return the number of losses against left-handed pitchers."""
        return self._record_vs_left_handed_pitchers

    @property
    def record_vs_teams_over_500(self) -> Optional[str]:
        """Return the record against teams above .500 (e.g., '30-40')."""
        return self._record_vs_teams_over_500

    @record_property_decorator
    def wins_vs_teams_over_500(self) -> Optional[int]:
        """Return the number of wins against teams above .500."""
        return self._record_vs_teams_over_500

    @record_property_decorator
    def losses_vs_teams_over_500(self) -> Optional[int]:
        """Return the number of losses against teams above .500."""
        return self._record_vs_teams_over_500

    @property
    def record_vs_teams_under_500(self) -> Optional[str]:
        """Return the record against teams below .500 (e.g., '50-30')."""
        return self._record_vs_teams_under_500

    @record_property_decorator
    def wins_vs_teams_under_500(self) -> Optional[int]:
        """Return the number of wins against teams below .500."""
        return self._record_vs_teams_under_500

    @record_property_decorator
    def losses_vs_teams_under_500(self) -> Optional[int]:
        """Return the number of losses against teams below .500."""
        return self._record_vs_teams_under_500

    @property
    def last_ten_games_record(self) -> Optional[str]:
        """Return the record over the last 10 games (e.g., '7-3')."""
        return self._last_ten_games_record

    @record_property_decorator
    def wins_last_ten_games(self) -> Optional[int]:
        """Return the number of wins in the last 10 games."""
        return self._last_ten_games_record

    @record_property_decorator
    def losses_last_ten_games(self) -> Optional[int]:
        """Return the number of losses in the last 10 games."""
        return self._last_ten_games_record

    @property
    def last_twenty_games_record(self) -> Optional[str]:
        """Return the record over the last 20 games (e.g., '12-8')."""
        return self._last_twenty_games_record

    @record_property_decorator
    def wins_last_twenty_games(self) -> Optional[int]:
        """Return the number of wins in the last 20 games."""
        return self._last_twenty_games_record

    @record_property_decorator
    def losses_last_twenty_games(self) -> Optional[int]:
        """Return the number of losses in the last 20 games."""
        return self._last_twenty_games_record

    @property
    def last_thirty_games_record(self) -> Optional[str]:
        """Return the record over the last 30 games (e.g., '18-12')."""
        return self._last_thirty_games_record

    @record_property_decorator
    def wins_last_thirty_games(self) -> Optional[int]:
        """Return the number of wins in the last 30 games."""
        return self._last_thirty_games_record

    @record_property_decorator
    def losses_last_thirty_games(self) -> Optional[int]:
        """Return the number of losses in the last 30 games."""
        return self._last_thirty_games_record

    @int_property_decorator
    def number_players_used(self) -> Optional[int]:
        """Return the number of players used during the season."""
        return self._number_players_used

    @float_property_decorator
    def average_batter_age(self) -> Optional[float]:
        """Return the average batter age, weighted by at-bats and games."""
        return self._average_batter_age

    @int_property_decorator
    def plate_appearances(self) -> Optional[int]:
        """Return the total number of plate appearances."""
        return self._plate_appearances

    @int_property_decorator
    def at_bats(self) -> Optional[int]:
        """Return the total number of at-bats."""
        return self._at_bats

    @int_property_decorator
    def total_runs(self) -> Optional[int]:
        """Return the total number of runs scored."""
        return self._total_runs

    @int_property_decorator
    def hits(self) -> Optional[int]:
        """Return the total number of hits."""
        return self._hits

    @int_property_decorator
    def doubles(self) -> Optional[int]:
        """Return the total number of doubles."""
        return self._doubles

    @int_property_decorator
    def triples(self) -> Optional[int]:
        """Return the total number of triples."""
        return self._triples

    @int_property_decorator
    def home_runs(self) -> Optional[int]:
        """Return the total number of home runs."""
        return self._home_runs

    @int_property_decorator
    def runs_batted_in(self) -> Optional[int]:
        """Return the total number of runs batted in."""
        return self._runs_batted_in

    @int_property_decorator
    def stolen_bases(self) -> Optional[int]:
        """Return the total number of stolen bases."""
        return self._stolen_bases

    @int_property_decorator
    def times_caught_stealing(self) -> Optional[int]:
        """Return the number of times caught stealing."""
        return self._times_caught_stealing

    @int_property_decorator
    def bases_on_balls(self) -> Optional[int]:
        """Return the total number of walks."""
        return self._bases_on_balls

    @int_property_decorator
    def times_struck_out(self) -> Optional[int]:
        """Return the total number of strikeouts."""
        return self._times_struck_out

    @float_property_decorator
    def batting_average(self) -> Optional[float]:
        """Return the team's batting average (0-1)."""
        return self._batting_average

    @float_property_decorator
    def on_base_percentage(self) -> Optional[float]:
        """Return the team's on-base percentage (0-1)."""
        return self._on_base_percentage

    @float_property_decorator
    def slugging_percentage(self) -> Optional[float]:
        """Return the team's slugging percentage."""
        return self._slugging_percentage

    @float_property_decorator
    def on_base_plus_slugging_percentage(self) -> Optional[float]:
        """Return the team's on-base plus slugging percentage."""
        return self._on_base_plus_slugging_percentage

    @int_property_decorator
    def on_base_plus_slugging_percentage_plus(self) -> Optional[int]:
        """Return the park-adjusted on-base plus slugging percentage."""
        return self._on_base_plus_slugging_percentage_plus

    @int_property_decorator
    def total_bases(self) -> Optional[int]:
        """Return the total number of bases gained."""
        return self._total_bases

    @int_property_decorator
    def grounded_into_double_plays(self) -> Optional[int]:
        """Return the total number of double plays grounded into."""
        return self._grounded_into_double_plays

    @int_property_decorator
    def times_hit_by_pitch(self) -> Optional[int]:
        """Return the total number of times hit by pitch."""
        return self._times_hit_by_pitch

    @int_property_decorator
    def sacrifice_hits(self) -> Optional[int]:
        """Return the total number of sacrifice hits."""
        return self._sacrifice_hits

    @int_property_decorator
    def sacrifice_flies(self) -> Optional[int]:
        """Return the total number of sacrifice flies."""
        return self._sacrifice_flies

    @int_property_decorator
    def intentional_bases_on_balls(self) -> Optional[int]:
        """Return the total number of intentional walks."""
        return self._intentional_bases_on_balls

    @int_property_decorator
    def runners_left_on_base(self) -> Optional[int]:
        """Return the total number of runners left on base."""
        return self._runners_left_on_base

    @int_property_decorator
    def number_of_pitchers(self) -> Optional[int]:
        """Return the total number of pitchers used."""
        return self._number_of_pitchers

    @float_property_decorator
    def average_pitcher_age(self) -> Optional[float]:
        """Return the average pitcher age, weighted by games and saves."""
        return self._average_pitcher_age

    @float_property_decorator
    def runs_allowed_per_game(self) -> Optional[float]:
        """Return the average runs allowed per game."""
        return self._runs_allowed_per_game

    @float_property_decorator
    def earned_runs_against(self) -> Optional[float]:
        """Return the average earned runs against."""
        return self._earned_runs_against

    @int_property_decorator
    def games_finished(self) -> Optional[int]:
        """Return the number of games finished."""
        return self._games_finished

    @int_property_decorator
    def complete_games(self) -> Optional[int]:
        """Return the total number of complete games."""
        return self._complete_games

    @int_property_decorator
    def shutouts(self) -> Optional[int]:
        """Return the total number of shutouts."""
        return self._shutouts

    @int_property_decorator
    def complete_game_shutouts(self) -> Optional[int]:
        """Return the total number of complete game shutouts."""
        return self._complete_game_shutouts

    @int_property_decorator
    def saves(self) -> Optional[int]:
        """Return the total number of saves."""
        return self._saves

    @float_property_decorator
    def innings_pitched(self) -> Optional[float]:
        """Return the total innings pitched."""
        return self._innings_pitched

    @int_property_decorator
    def hits_allowed(self) -> Optional[int]:
        """Return the total number of hits allowed."""
        return self._hits_allowed

    @int_property_decorator
    def home_runs_against(self) -> Optional[int]:
        """Return the total number of home runs allowed."""
        return self._home_runs_against

    @int_property_decorator
    def bases_on_walks_given(self) -> Optional[int]:
        """Return the total number of walks given."""
        return self._bases_on_walks_given

    @int_property_decorator
    def strikeouts(self) -> Optional[int]:
        """Return the total number of strikeouts thrown."""
        return self._strikeouts

    @int_property_decorator
    def hit_pitcher(self) -> Optional[int]:
        """Return the total number of times a pitcher hit a batter."""
        return self._hit_pitcher

    @int_property_decorator
    def balks(self) -> Optional[int]:
        """Return the total number of balks."""
        return self._balks

    @int_property_decorator
    def wild_pitches(self) -> Optional[int]:
        """Return the total number of wild pitches."""
        return self._wild_pitches

    @int_property_decorator
    def batters_faced(self) -> Optional[int]:
        """Return the total number of batters faced."""
        return self._batters_faced

    @int_property_decorator
    def earned_runs_against_plus(self) -> Optional[int]:
        """Return the park-adjusted earned runs against."""
        return self._earned_runs_against_plus

    @float_property_decorator
    def fielding_independent_pitching(self) -> Optional[float]:
        """Return the fielding-independent pitching metric."""
        return self._fielding_independent_pitching

    @float_property_decorator
    def whip(self) -> Optional[float]:
        """Return the walks plus hits per inning pitched."""
        return self._whip

    @float_property_decorator
    def hits_per_nine_innings(self) -> Optional[float]:
        """Return the average hits per nine innings."""
        return self._hits_per_nine_innings

    @float_property_decorator
    def home_runs_per_nine_innings(self) -> Optional[float]:
        """Return the average home runs per nine innings."""
        return self._home_runs_per_nine_innings

    @float_property_decorator
    def bases_on_walks_given_per_nine_innings(self) -> Optional[float]:
        """Return the average walks per nine innings."""
        return self._bases_on_walks_given_per_nine_innings

    @float_property_decorator
    def strikeouts_per_nine_innings(self) -> Optional[float]:
        """Return the average strikeouts per nine innings."""
        return self._strikeouts_per_nine_innings

    @float_property_decorator
    def strikeouts_per_base_on_balls(self) -> Optional[float]:
        """Return the strikeouts per walk ratio."""
        return self._strikeouts_per_base_on_balls

    @int_property_decorator
    def opposing_runners_left_on_base(self) -> Optional[int]:
        """Return the total number of opponents left on base."""
        return self._opposing_runners_left_on_base

class Teams:
    """A collection of all MLB teams and their stats for a given year.

    Retrieves and stores a list of Team instances for all MLB teams in a specified
    year, providing access to team statistics and identifiers.

    Parameters
    ----------
    year : str, optional
        The year to pull stats for (e.g., '2023'). Defaults to current year if None.
    standings_file : str, optional
        Path to a local HTML file of the Standings page for the year.
    teams_file : str, optional
        Path to a local HTML file of the League page for the year.

    Attributes
    ----------
    dataframes : pd.DataFrame
        A DataFrame containing stats for all teams, indexed by abbreviation.
    """
    def __init__(self, year: Optional[str] = None, standings_file: Optional[str] = None,
                 teams_file: Optional[str] = None):
        self._teams: List[Team] = []
        team_data_dict, year = _retrieve_team_data_dict(year, STANDINGS_URL, LEAGUE_URL)
        self._instantiate_teams(team_data_dict, year)

    def __str__(self) -> str:
        """Return the string representation of all teams."""
        return '\n'.join(f'{team.name} ({team.abbreviation})'.strip() for team in self._teams)

    def __repr__(self) -> str:
        """Return the string representation of all teams."""
        return self.__str__()

    def __getitem__(self, abbreviation: str) -> Team:
        """Return a team by its abbreviation.

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
            If the abbreviation is not found.
        """
        for team in self._teams:
            if team.abbreviation and team.abbreviation.upper() == abbreviation.upper():
                return team
        raise ValueError(f'Team abbreviation {abbreviation} not found')

    def __call__(self, abbreviation: str) -> Team:
        """Return a team by its abbreviation.

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

    def __iter__(self):
        """Return an iterator over all teams."""
        return iter(self._teams)

    def __len__(self) -> int:
        """Return the number of teams."""
        return len(self._teams)

    def _instantiate_teams(self, team_data_dict: Dict, year: str) -> None:
        """Create Team instances for all teams.

        Parameters
        ----------
        team_data_dict : Dict
            Dictionary of team data, indexed by abbreviation.
        year : str
            The season year.
        """
        for team_data in team_data_dict.values():
            team = Team(team_data=str(team_data['data']), rank=team_data['rank'], year=year)
            self._teams.append(team)

    @property
    def dataframes(self) -> pd.DataFrame:
        """Return a DataFrame of all teams' stats.

        Returns
        -------
        pd.DataFrame
            DataFrame containing stats for all teams, indexed by abbreviation.
        """
        frames = [team.dataframe for team in self._teams if team.dataframe is not None]
        return pd.concat(frames) if frames else pd.DataFrame()