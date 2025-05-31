import pandas as pd
import re
from datetime import datetime
from ..base import AbstractParser, int_property_decorator, float_property_decorator, nfl_int_property_decorator, _fetch_html, _parse_field, _parse_game_metadata, _parse_game_summary, _parse_player_data, _parse_team_abbreviations, _parse_team_abbreviation
from ..constants import AWAY, HOME
from .constants import BOXSCORE_SCHEME, BOXSCORE_URL, BOXSCORES_URL
from .player import AbstractPlayer

class BoxscorePlayer(AbstractPlayer):
    """Player statistics for a single NFL game.

    Retrieves and stores detailed player statistics for an NFL game, such as passing yards,
    rushing touchdowns, and defensive stats, from a boxscore on pro-football-reference.com.
    Inherits from AbstractPlayer for shared parsing logic.

    Parameters
    ----------
    player_id : str
        The player's ID (e.g., 'BradTo00' for Tom Brady).
    player_name : str
        The player's full name (e.g., 'Tom Brady').
    player_data : str
        HTML string containing player stats from the boxscore page.

    Attributes
    ----------
    player_id : str
        The player's unique ID.
    name : str
        The player's full name.
    """
    def __init__(self, player_id, player_name, player_data):
        self._index = 0
        self._yards_lost_from_sacks = None
        self._fumbles_lost = None
        self._combined_tackles = None
        self._solo_tackles = None
        self._tackles_for_loss = None
        self._quarterback_hits = None
        self._average_kickoff_return_yards = None
        AbstractPlayer.__init__(self, player_id, player_name, player_data)

    @property
    def dataframe(self):
        """Return a pandas DataFrame of player statistics.

        Returns
        -------
        pandas.DataFrame
            DataFrame with player stats, indexed by player ID.
        """
        fields_to_include = {
            'completed_passes': self.completed_passes,
            'attempted_passes': self.attempted_passes,
            'passing_yards': self.passing_yards,
            'passing_touchdowns': self.passing_touchdowns,
            'interceptions_thrown': self.interceptions_thrown,
            'times_sacked': self.times_sacked,
            'yards_lost_from_sacks': self.yards_lost_from_sacks,
            'longest_pass': self.longest_pass,
            'quarterback_rating': self.quarterback_rating,
            'rush_attempts': self.rush_attempts,
            'rush_yards': self.rush_yards,
            'rush_touchdowns': self.rush_touchdowns,
            'longest_rush': self.longest_rush,
            'times_pass_target': self.times_pass_target,
            'receptions': self.receptions,
            'receiving_yards': self.receiving_yards,
            'receiving_touchdowns': self.receiving_touchdowns,
            'longest_reception': self.longest_reception,
            'fumbles': self.fumbles,
            'fumbles_lost': self.fumbles_lost,
            'interceptions': self.interceptions,
            'yards_returned_from_interception': self.yards_returned_from_interception,
            'interceptions_returned_for_touchdown': self.interceptions_returned_for_touchdown,
            'longest_interception_return': self.longest_interception_return,
            'passes_defended': self.passes_defended,
            'sacks': self.sacks,
            'combined_tackles': self.combined_tackles,
            'solo_tackles': self.solo_tackles,
            'assists_on_tackles': self.assists_on_tackles,
            'tackles_for_loss': self.tackles_for_loss,
            'quarterback_hits': self.quarterback_hits,
            'fumbles_recovered': self.fumbles_recovered,
            'yards_recovered_from_fumble': self.yards_recovered_from_fumble,
            'fumbles_recovered_for_touchdown': self.fumbles_recovered_for_touchdown,
            'fumbles_forced': self.fumbles_forced,
            'kickoff_returns': self.kickoff_returns,
            'kickoff_return_yards': self.kickoff_return_yards,
            'average_kickoff_return_yards': self.average_kickoff_return_yards,
            'kickoff_return_touchdown': self.kickoff_return_touchdown,
            'longest_kickoff_return': self.longest_kickoff_return,
            'punt_returns': self.punt_returns,
            'punt_return_yards': self.punt_return_yards,
            'yards_per_punt_return': self.yards_per_punt_return,
            'punt_return_touchdown': self.punt_return_touchdown,
            'longest_punt_return': self.longest_punt_return,
            'extra_points_made': self.extra_points_made,
            'extra_points_attempted': self.extra_points_attempted,
            'field_goals_made': self.field_goals_made,
            'field_goals_attempted': self.field_goals_attempted,
            'punts': self.punts,
            'total_punt_yards': self.total_punt_yards,
            'yards_per_punt': self.yards_per_punt,
            'longest_punt': self.longest_punt
        }
        return pd.DataFrame([fields_to_include], index=[self._player_id])

    @int_property_decorator
    def yards_lost_from_sacks(self):
        """Return yards lost from sacks.

        Returns
        -------
        int or None
            Total yards lost due to sacks.
        """
        return self._yards_lost_from_sacks

    @int_property_decorator
    def fumbles_lost(self):
        """Return fumbles lost.

        Returns
        -------
        int or None
        """
        return self._fumbles_lost

    @int_property_decorator
    def combined_tackles(self):
        """Return combined tackles.

        Returns
        -------
        int or None
            Total solo and assisted tackles.
        """
        return self._combined_tackles

    @int_property_decorator
    def solo_tackles(self):
        """Return solo tackles.

        Returns
        -------
        int or None
            Total solo tackles.
        """
        return self._solo_tackles

    @int_property_decorator
    def tackles_for_loss(self):
        """Return tackles for loss.

        Returns
        -------
        int or None
            Total tackles resulting in a loss of yardage.
        """
        return self._tackles_for_loss

    @int_property_decorator
    def quarterback_hits(self):
        """Return quarterback hits.

        Returns
        -------
        int or None
            Total hits on the quarterback.
        """
        return self._quarterback_hits

    @float_property_decorator
    def average_kickoff_return_yards(self):
        """Return average kickoff return yards.

        Returns
        -------
        float or None
            Average yards per kickoff return.
        """
        return self._average_kickoff_return_yards

class Boxscore(AbstractParser):
    """Game statistics for a single NFL game.

    Retrieves and stores detailed game statistics, such as team scores, player stats,
    and game metadata (e.g., date, stadium), from a boxscore on pro-football-reference.com.

    Parameters
    ----------
    uri : str
        The boxscore URI (e.g., '202309100buf') from pro-football-reference.com.

    Attributes
    ----------
    away_players : list
        List of BoxscorePlayer instances for the away team.
    home_players : list
        List of BoxscorePlayer instances for the home team.
    date : str
        The game date.
    winner : str
        The winning team ('home' or 'away').
    """
    def __init__(self, uri):
        self._uri = uri
        self._date = None
        self._time = None
        self._stadium = None
        self._attendance = None
        self._duration = None
        self._away_name = None
        self._home_name = None
        self._winner = None
        self._winning_name = None
        self._winning_abbr = None
        self._losing_name = None
        self._losing_abbr = None
        self._summary = None
        self._won_toss = None
        self._roof = None
        self._surface = None
        self._weather = None
        self._vegas_line = None
        self._over_under = None
        self._away_points = None
        self._away_first_downs = None
        self._away_rush_attempts = None
        self._away_rush_yards = None
        self._away_rush_touchdowns = None
        self._away_pass_completions = None
        self._away_pass_attempts = None
        self._away_pass_yards = None
        self._away_pass_touchdowns = None
        self._away_interceptions = None
        self._away_times_sacked = None
        self._away_yards_lost_from_sacks = None
        self._away_net_pass_yards = None
        self._away_total_yards = None
        self._away_fumbles = None
        self._away_fumbles_lost = None
        self._away_turnovers = None
        self._away_penalties = None
        self._away_yards_from_penalties = None
        self._away_third_down_conversions = None
        self._away_third_down_attempts = None
        self._away_fourth_down_conversions = None
        self._away_fourth_down_attempts = None
        self._away_time_of_possession = None
        self._home_points = None
        self._home_first_downs = None
        self._home_rush_attempts = None
        self._home_rush_yards = None
        self._home_rush_touchdowns = None
        self._home_pass_completions = None
        self._home_pass_attempts = None
        self._home_pass_yards = None
        self._home_pass_touchdowns = None
        self._home_interceptions = None
        self._home_times_sacked = None
        self._home_yards_lost_from_sacks = None
        self._home_net_pass_yards = None
        self._home_total_yards = None
        self._home_fumbles = None
        self._home_fumbles_lost = None
        self._home_turnovers = None
        self._home_penalties = None
        self._home_yards_from_penalties = None
        self._home_third_down_conversions = None
        self._home_third_down_attempts = None
        self._home_fourth_down_conversions = None
        self._home_fourth_down_attempts = None
        self._home_time_of_possession = None
        self._away_players = []
        self._home_players = []
        self._away_abbr = None
        self._home_abbr = None

        AbstractParser.__init__(self, '')
        self._parse_game_data()

    def __str__(self):
        """Return the string representation of the game.

        Returns
        -------
        str
            Away team at home team with date (e.g., 'Buffalo Bills at New York Jets (Sun Sep 10, 2023)').
        """
        away = self._away_name.text if self._away_name else 'Unknown'
        home = self._home_name.text if self._home_name else 'Unknown'
        return f'Boxscore for {away} at {home} ({self.date})'

    def __repr__(self):
        """Return the string representation of the game.

        Returns
        -------
        str
            Same as __str__.
        """
        return self.__str__()

    def _parse_game_data(self):
        """Parse all game data from the boxscore page."""
        url = BOXSCORE_URL % self._uri
        soup = _fetch_html(url)
        if not soup or '404 error' in soup.text.lower():
            return

        # Parse team names
        for field in ['away_name', 'home_name']:
            value = _parse_field(BOXSCORE_SCHEME, soup, field)
            setattr(self, f'_{field}', value)

        # Parse game metadata
        metadata = _parse_game_metadata(soup, BOXSCORE_SCHEME)
        for key, value in metadata.items():
            setattr(self, f'_{key}', value)

        # Parse game summary
        self._summary = _parse_game_summary(soup, BOXSCORE_SCHEME)

        # Parse team stats
        for field in self.__dict__:
            short_field = field.lstrip('_')
            if short_field in [
                'uri', 'date', 'time', 'stadium', 'attendance', 'duration',
                'away_name', 'home_name', 'winner', 'winning_name', 'winning_abbr',
                'losing_name', 'losing_abbr', 'summary', 'won_toss', 'roof',
                'surface', 'weather', 'vegas_line', 'over_under', 'away_players',
                'home_players', 'away_abbr', 'home_abbr'
            ]:
                continue
            value = _parse_field(BOXSCORE_SCHEME, soup, short_field)
            setattr(self, field, value)

        # Parse team abbreviations and players
        self._away_abbr, self._home_abbr = _parse_team_abbreviations(soup, BOXSCORE_SCHEME)
        self._away_players, self._home_players = _parse_player_data(soup, self._home_abbr, self._away_abbr)

    @property
    def dataframe(self):
        """Return a pandas DataFrame of game statistics.

        Returns
        -------
        pandas.DataFrame or None
            DataFrame with game stats, indexed by boxscore URI, or None if points data is missing.
        """
        if not all([self._away_points, self._home_points]):
            return None
        fields_to_include = {
            'attendance': self.attendance,
            'away_first_downs': self.away_first_downs,
            'away_fourth_down_attempts': self.away_fourth_down_attempts,
            'away_fourth_down_conversions': self.away_fourth_down_conversions,
            'away_fumbles': self.away_fumbles,
            'away_fumbles_lost': self.away_fumbles_lost,
            'away_interceptions': self.away_interceptions,
            'away_net_pass_yards': self.away_net_pass_yards,
            'away_pass_attempts': self.away_pass_attempts,
            'away_pass_completions': self.away_pass_completions,
            'away_pass_touchdowns': self.away_pass_touchdowns,
            'away_pass_yards': self.away_pass_yards,
            'away_penalties': self.away_penalties,
            'away_points': self.away_points,
            'away_rush_attempts': self.away_rush_attempts,
            'away_rush_touchdowns': self.away_rush_touchdowns,
            'away_rush_yards': self.away_rush_yards,
            'away_third_down_attempts': self.away_third_down_attempts,
            'away_third_down_conversions': self.away_third_down_conversions,
            'away_time_of_possession': self.away_time_of_possession,
            'away_times_sacked': self.away_times_sacked,
            'away_total_yards': self.away_total_yards,
            'away_turnovers': self.away_turnovers,
            'away_yards_from_penalties': self.away_yards_from_penalties,
            'away_yards_lost_from_sacks': self.away_yards_lost_from_sacks,
            'date': self.date,
            'datetime': self.datetime,
            'duration': self.duration,
            'home_first_downs': self.home_first_downs,
            'home_fourth_down_attempts': self.home_fourth_down_attempts,
            'home_fourth_down_conversions': self.home_fourth_down_conversions,
            'home_fumbles': self.home_fumbles,
            'home_fumbles_lost': self.home_fumbles_lost,
            'home_interceptions': self.home_interceptions,
            'home_net_pass_yards': self.home_net_pass_yards,
            'home_pass_attempts': self.home_pass_attempts,
            'home_pass_completions': self.home_pass_completions,
            'home_pass_touchdowns': self.home_pass_touchdowns,
            'home_pass_yards': self.home_pass_yards,
            'home_penalties': self.home_penalties,
            'home_points': self.home_points,
            'home_rush_attempts': self.home_rush_attempts,
            'home_rush_touchdowns': self.home_rush_touchdowns,
            'home_rush_yards': self.home_rush,
            'home_third_down_attempts': self.home_third_down,
            'home_conversions': self.home_conversions,
            'home_time_of_possession': self._home_time,
            'home_times_s': self._home_times_s,
            'home_total': self._home_total,
            'home_turnovers': self._home_overs,
            'home_yards_from': self._home_yards_from_penalties,
            'home_yards_lost_from_sacks': self.home_yards_lost_from_sacks,
            'losing_abbr': self.losing_abbr,
            'losing_name': self.losing_name,
            'over_under': self.over_under,
            'roof': self.roof,
            'stadium': self.stadium,
            'surface': self.surface,
            'time': self.time,
            'vegas_line': self.vegas_line,
            'weather': self.weather,
            'winner': self.winner,
            'winning_abbr': self.winning_abbr,
            'winning_name': self.winning_name,
            'won_toss': self.won_toss
        }
        return pd.DataFrame([fields_to_include], index=[self._uri])

    @property
    def away_players(self):
        """Return away team player statistics."""
        return self._away_players

    @property
    def home_players(self):
        """Return home team player statistics."""
        return self._home_players

    @property
    def away_abbreviation(self):
        """Return away team abbreviation."""
        return self._away_abbr

    @property
    def home_abbreviation(self):
        """Return home team abbreviation."""
        return self._home_abbr

    @property
    def date(self):
        """Return game date."""
        return self._date

    @property
    def time(self):
        """Return game start time."""
        return self._time

    @property
    def datetime(self):
        """Return game datetime."""
        if self._date and self._time:
            try:
                return datetime.strptime(f'{self._date} {self._time}', '%A %b %d, %Y %I:%M%p')
            except ValueError:
                pass
        if self._date:
            try:
                return datetime.strptime(self._date, '%A %b %d, %Y')
            except ValueError:
                pass
        return None

    @property
    def stadium(self):
        """Return stadium name."""
        return self._stadium

    @int_property_decorator
    def attendance(self):
        """Return game attendance."""
        return self._attendance

    @property
    def duration(self):
        """Return game duration."""
        return self._duration

    @property
    def won_toss(self):
        """Return team that won the toss."""
        return self._won_toss

    @property
    def roof(self):
        """Return roof type."""
        return self._roof

    @property
    def surface(self):
        """Return playing surface."""
        return self._surface

    @property
    def weather(self):
        """Return weather conditions."""
        return self._weather

    @property
    def vegas_line(self):
        """Return Vegas betting line."""
        return self._vegas_line

    @property
    def over_under(self):
        """Return over/under betting line."""
        return self._over_under

    @property
    def summary(self):
        """Return per-quarter scores."""
        return self._summary

    @property
    def winner(self):
        """Return winning team ('home' or 'away')."""
        if self.home_points is not None and self.away_points is not None:
            return HOME if self.home_points > self.away_points else AWAY
        return None

    @property
    def winning_name(self):
        """Return winning team name."""
        if self.winner == HOME and self._home_name:
            return self._home_name.text
        if self.winner == AWAY and self._away_name:
            return self._away_name.text
        return None

    @property
    def winning_abbr(self):
        """Return winning team abbreviation."""
        return self._home_abbr if self.winner == HOME else self._away_abbr

    @property
    def losing_name(self):
        """Return losing team name."""
        if self.winner == HOME and self._away_name:
            return self._away_name.text
        if self.winner == AWAY and self._home_name:
            return self._home_name.text
        return None

    @property
    def losing_abbr(self):
        """Return losing team abbreviation."""
        return self._away_abbr if self.winner == HOME else self._home_abbr

    @int_property_decorator
    def away_points(self):
        """Return away team points."""
        return self._away_points

    @int_property_decorator
    def away_first_downs(self):
        """Return away team first downs."""
        return self._away_first_downs

    @nfl_int_property_decorator
    def away_rush_attempts(self):
        """Return away team rush attempts."""
        return self._away_rush_attempts

    @nfl_int_property_decorator
    def away_rush_yards(self):
        """Return away team rush yards."""
        return self._away_rush_yards

    @nfl_int_property_decorator
    def away_rush_touchdowns(self):
        """Return away team rush touchdowns."""
        return self._away_rush_touchdowns

    @nfl_int_property_decorator
    def away_pass_completions(self):
        """Return away team pass completions."""
        return self._away_pass_completions

    @nfl_int_property_decorator
    def away_pass_attempts(self):
        """Return away team pass attempts."""
        return self._away_pass_attempts

    @nfl_int_property_decorator
    def away_pass_yards(self):
        """Return away team pass yards."""
        return self._away_pass_yards

    @nfl_int_property_decorator
    def away_pass_touchdowns(self):
        """Return away team pass touchdowns."""
        return self._away_pass_touchdowns

    @nfl_int_property_decorator
    def away_interceptions(self):
        """Return away team interceptions thrown."""
        return self._away_interceptions

    @nfl_int_property_decorator
    def away_times_sacked(self):
        """Return away team times sacked."""
        return self._away_times_sacked

    @nfl_int_property_decorator
    def away_yards_lost_from_sacks(self):
        """Return away team yards lost from sacks."""
        return self._away_yards_lost_from_sacks

    @int_property_decorator
    def away_net_pass_yards(self):
        """Return away team net pass yards."""
        return self._away_net_pass_yards

    @int_property_decorator
    def away_total_yards(self):
        """Return away team total yards."""
        return self._away_total_yards

    @nfl_int_property_decorator
    def away_fumbles(self):
        """Return away team fumbles."""
        return self._away_fumbles

    @nfl_int_property_decorator
    def away_fumbles_lost(self):
        """Return away team fumbles lost."""
        return self._away_fumbles_lost

    @int_property_decorator
    def away_turnovers(self):
        """Return away team turnovers."""
        return self._away_turnovers

    @nfl_int_property_decorator
    def away_penalties(self):
        """Return away team penalties."""
        return self._away_penalties

    @nfl_int_property_decorator
    def away_yards_from_penalties(self):
        """Return away team yards from penalties."""
        return self._away_yards_from_penalties

    @nfl_int_property_decorator
    def away_third_down_conversions(self):
        """Return away team third down conversions."""
        return self._away_third_down_conversions

    @nfl_int_property_decorator
    def away_third_down_attempts(self):
        """Return away team third down attempts."""
        return self._away_third_down_attempts

    @nfl_int_property_decorator
    def away_fourth_down_conversions(self):
        """Return away team fourth down conversions."""
        return self._away_fourth_down_conversions

    @nfl_int_property_decorator
    def away_fourth_down_attempts(self):
        """Return away team fourth down attempts."""
        return self._away_fourth_down_attempts

    @property
    def away_time_of_possession(self):
        """Return away team time of possession."""
        return self._away_time_of_possession

    @int_property_decorator
    def home_points(self):
        """Return home team points."""
        return self._home_points

    @int_property_decorator
    def home_first_downs(self):
        """Return home team first downs."""
        return self._home_first_downs

    @nfl_int_property_decorator
    def home_rush_attempts(self):
        """Return home team rush attempts."""
        return self._home_rush_attempts

    @nfl_int_property_decorator
    def home_rush_yards(self):
        """Return home team rush yards."""
        return self._home_rush_yards

    @nfl_int_property_decorator
    def home_rush_touchdowns(self):
        """Return home team rush touchdowns."""
        return self._home_rush_touchdowns

    @nfl_int_property_decorator
    def home_pass_completions(self):
        """Return home team pass completions."""
        return self._home_pass_completions

    @nfl_int_property_decorator
    def home_pass_attempts(self):
        """Return home team pass attempts."""
        return self._home_pass_attempts

    @nfl_int_property_decorator
    def home_pass_yards(self):
        """Return home team pass yards."""
        return self._home_pass_yards

    @nfl_int_property_decorator
    def home_pass_touchdowns(self):
        """Return home team pass touchdowns."""
        return self._home_pass_touchdowns

    @nfl_int_property_decorator
    def home_interceptions(self):
        """Return home team interceptions thrown."""
        return self._home_interceptions

    @nfl_int_property_decorator
    def home_times_sacked(self):
        """Return home team times sacked."""
        return self._home_times_sacked

    @nfl_int_property_decorator
    def home_yards_lost_from_sacks(self):
        """Return home team yards lost from sacks."""
        return self._home_yards_lost_from_sacks

    @int_property_decorator
    def home_net_pass_yards(self):
        """Return home team net pass yards."""
        return self._home_net_pass_yards

    @int_property_decorator
    def home_total_yards(self):
        """Return home team total yards."""
        return self._home_total_yards

    @nfl_int_property_decorator
    def home_fumbles(self):
        """Return home team fumbles."""
        return self._home_fumbles

    @nfl_int_property_decorator
    def home_fumbles_lost(self):
        """Return home team fumbles lost."""
        return self._home_fumbles_lost

    @int_property_decorator
    def home_turnovers(self):
        """Return home team turnovers."""
        return self._home_turnovers

    @nfl_int_property_decorator
    def home_penalties(self):
        """Return home team penalties."""
        return self._home_penalties

    @nfl_int_property_decorator
    def home_yards_from_penalties(self):
        """Return home team yards from penalties."""
        return self._home_yards_from_penalties

    @nfl_int_property_decorator
    def home_third_down_conversions(self):
        """Return home team third down conversions."""
        return self._home_third_down_conversions

    @nfl_int_property_decorator
    def home_third_down_attempts(self):
        """Return home team third down attempts."""
        return self._home_third_down_attempts

    @nfl_int_property_decorator
    def home_fourth_down_conversions(self):
        """Return home team fourth down conversions."""
        return self._home_fourth_down_conversions

    @nfl_int_property_decorator
    def home_fourth_down_attempts(self):
        """Return home team fourth down attempts."""
        return self._home_fourth_down_attempts

    @property
    def home_time_of_possession(self):
        """Return home team time of possession."""
        return self._home_time_of_possession

class Boxscores:
    """Collection of NFL game boxscores for a week or range of weeks.

    Retrieves and stores boxscore summaries for NFL games in a given week or range
    of weeks from pro-football-reference.com.

    Parameters
    ----------
    week : int
        The starting week number (e.g., 1 for the first week of the season).
    year : int
        The 4-digit year of the season (e.g., 2023).
    end_week : int, optional
        The ending week number (defaults to the starting week).

    Attributes
    ----------
    games : dict
        Dictionary mapping week-year timestamps to lists of game info dictionaries.
    """
    def __init__(self, week, year, end_week=None):
        self._boxscores = {}
        self._find_games(week, year, end_week)

    def __str__(self):
        """Return the string representation of the boxscores."""
        weeks = sorted(set(timestamp.split('-')[0] for timestamp in self._boxscores))
        if len(weeks) > 1:
            return f"NFL games for weeks {', '.join(weeks)}"
        return f"NFL games for week {weeks[0]}"

    def __repr__(self):
        """Return the string representation of the boxscores."""
        return self.__str__()

    @property
    def games(self):
        """Return the boxscores dictionary."""
        return self._boxscores

    def _find_games(self, week, year, end_week):
        """Fetch game data for the specified weeks."""
        end_week = week if not end_week or week > end_week else end_week
        while week <= end_week:
            url = BOXSCORES_URL % (year, week)
            soup = _fetch_html(url)
            if not soup:
                week += 1
                continue
            games = soup.select('table.teams')
            boxscores = []
            for game in games:
                # Parse team details
                links = game.select('td a')
                if len(links) < 2:
                    continue
                away_link, home_link = links[0], links[-1]
                away_name = away_link.text
                away_abbr = _parse_team_abbreviation(away_link)
                home_name = home_link.text
                home_abbr = _parse_team_abbreviation(home_link)

                # Parse scores
                scores = game.select('td.right')
                away_score = int(scores[0].text) if len(scores) >= 2 and scores[0].text.isdigit() else None
                home_score = int(scores[1].text) if len(scores) >= 2 and scores[1].text.isdigit() else None

                # Parse boxscore URI
                boxscore_link = game.select_one('td.right.gamelink a')
                boxscore_uri = re.sub(r'.*/boxscores/|\.htm.*', '', boxscore_link.get('href', '')) if boxscore_link else ''

                # Parse winner and loser
                winner_row = game.select_one('tr.winner')
                loser_row = game.select_one('tr.loser')
                winning_name = winning_abbr = losing_name = losing_abbr = None
                if winner_row:
                    winner_link = winner_row.select_one('td a')
                    if winner_link:
                        winning_name = winner_link.text
                        winning_abbr = _parse_team_abbreviation(winner_link)
                if loser_row:
                    loser_link = loser_row.select_one('td a')
                    if loser_link:
                        losing_name = loser_link.text
                        losing_abbr = _parse_team_abbreviation(loser_link)

                game_info = {
                    'boxscore': boxscore_uri,
                    'away_name': away_name,
                    'away_abbr': away_abbr,
                    'away_score': away_score,
                    'home_name': home_name,
                    'home_abbr': home_abbr,
                    'home_score': home_score,
                    'winning_name': winning_name,
                    'winning_abbr': winning_abbr,
                    'losing_name': losing_name,
                    'losing_abbr': losing_abbr
                }
                boxscores.append(game_info)
            self._boxscores[f'{week}-{year}'] = boxscores
            week += 1