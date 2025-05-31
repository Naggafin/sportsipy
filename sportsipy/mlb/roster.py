import pandas as pd
from typing import Optional, List, Dict, Union
from bs4 import BeautifulSoup
from datetime import datetime
from ..base import (int_property_decorator, float_property_decorator, most_recent_decorator,
                    _parse_field, _clean_stat, _fetch_html, _parse_player_id)
from .constants import (NATIONALITY, PLAYER_ELEMENT_INDEX, PLAYER_SCHEME, PLAYER_URL, ROSTER_URL)
from .player import AbstractPlayer

class Player(AbstractPlayer):
    """Player information and stats for all MLB seasons.

    Captures detailed stats and information for a player, such as name, nationality,
    height, weight, career home runs, batting average, salary, and contract details.
    By default, returns career stats, but specific seasons can be queried by calling
    the instance with a season year (e.g., '2023').

    Parameters
    ----------
    player_id : str
        A player's ID per baseball-reference.com (e.g., 'altuvjo01' for Jose Altuve).
        Typically in the format 'LLLLLFFNN' where 'LLLLL' are the first 5 letters of
        the last name, 'FF' are the first 2 letters of the first name, and 'NN' is a
        number starting at '01', incrementing for each player with the same initial
        letters.

    Attributes
    ----------
    player_id : str
        The player's unique ID.
    name : str
        The player's full name.
    season : str
        The currently queried season or 'Career' for career stats.
    contract : dict
        Dictionary of contract details by year, including age, team, and salary.
    """
    def __init__(self, player_id: str):
        self._most_recent_season: Optional[str] = ''
        self._index: Optional[int] = None
        self._player_id: str = player_id
        self._season: Optional[List[str]] = None
        self._name: Optional[str] = None
        self._team_abbreviation: Optional[str] = None
        self._position: Optional[str] = None
        self._height: Optional[str] = None
        self._weight: Optional[str] = None
        self._birth_date: Optional[str] = None
        self._nationality: Optional[str] = None
        self._contract: Optional[Dict] = None
        self._games: Optional[str] = None
        self._games_started: Optional[str] = None
        self._plate_appearances: Optional[str] = None
        self._at_bats: Optional[str] = None
        self._runs: Optional[str] = None
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
        self._complete_games: Optional[str] = None
        self._innings_played: Optional[str] = None
        self._defensive_chances: Optional[str] = None
        self._putouts: Optional[str] = None
        self._assists: Optional[str] = None
        self._errors: Optional[str] = None
        self._double_plays_turned: Optional[str] = None
        self._fielding_percentage: Optional[str] = None
        self._total_fielding_runs_above_average: Optional[str] = None
        self._defensive_runs_saved_above_average: Optional[str] = None
        self._total_fielding_runs_above_average_per_innings: Optional[str] = None
        self._defensive_runs_saved_above_average_per_innings: Optional[str] = None
        self._range_factor_per_nine_innings: Optional[str] = None
        self._range_factor_per_game: Optional[str] = None
        self._league_fielding_percentage: Optional[str] = None
        self._league_range_factor_per_nine_innings: Optional[str] = None
        self._league_range_factor_per_game: Optional[str] = None
        self._games_in_batting_order: Optional[str] = None
        self._games_in_defensive_lineup: Optional[str] = None
        self._games_pitcher: Optional[str] = None
        self._games_catcher: Optional[str] = None
        self._games_first_baseman: Optional[str] = None
        self._games_second_baseman: Optional[str] = None
        self._games_third_baseman: Optional[str] = None
        self._games_shortstop: Optional[str] = None
        self._games_left_fielder: Optional[str] = None
        self._games_center_fielder: Optional[str] = None
        self._games_right_fielder: Optional[str] = None
        self._games_outfielder: Optional[str] = None
        self._games_designated_hitter: Optional[str] = None
        self._games_pinch_hitter: Optional[str] = None
        self._games_pinch_runner: Optional[str] = None
        self._wins: Optional[str] = None
        self._losses: Optional[str] = None
        self._win_percentage: Optional[str] = None
        self._era: Optional[str] = None
        self._games_finished: Optional[str] = None
        self._shutouts: Optional[str] = None
        self._saves: Optional[str] = None
        self._hits_allowed: Optional[str] = None
        self._runs_allowed: Optional[str] = None
        self._earned_runs_allowed: Optional[str] = None
        self._home_runs_allowed: Optional[str] = None
        self._bases_on_balls_given: Optional[str] = None
        self._intentional_bases_on_balls_given: Optional[str] = None
        self._strikeouts: Optional[str] = None
        self._times_hit_player: Optional[str] = None
        self._balks: Optional[str] = None
        self._wild_pitches: Optional[str] = None
        self._batters_faced: Optional[str] = None
        self._era_plus: Optional[str] = None
        self._fielding_independent_pitching: Optional[str] = None
        self._whip: Optional[str] = None
        self._hits_against_per_nine_innings: Optional[str] = None
        self._home_runs_against_per_nine_innings: Optional[str] = None
        self._bases_on_balls_given_per_nine_innings: Optional[str] = None
        self._batters_struckout_per_nine_innings: Optional[str] = None
        self._strikeouts_thrown_per_walk: Optional[str] = None

        player_data = self._pull_player_data()
        self._find_initial_index()
        AbstractPlayer.__init__(self, player_id, self._name, player_data)

    def __str__(self) -> str:
        """Return the string representation of the player."""
        return f'{self.name} ({self.player_id})'

    def __repr__(self) -> str:
        """Return the string representation of the player."""
        return self.__str__()

    def _build_url(self) -> str:
        """Build the player's stats URL.

        Returns
        -------
        str
            URL for the player's stats page, using the first letter of their ID.
        """
        first_character = self._player_id[0]
        return PLAYER_URL % (first_character, self._player_id)

    def _retrieve_html_page(self) -> Optional[BeautifulSoup]:
        """Download the player's stats page.

        Returns
        -------
        BeautifulSoup or None
            Parsed HTML of the player's stats page or None if fetching fails.
        """
        url = self._build_url()
        return _fetch_html(url)

    def _parse_season(self, row: BeautifulSoup) -> str:
        """Parse the season from a stats table row.

        Parameters
        ----------
        row : BeautifulSoup
            A BeautifulSoup object of a single row in a stats table.

        Returns
        -------
        str
            Season in 'YYYY' format (e.g., '2023') or empty string if not found.
        """
        return _parse_field(PLAYER_SCHEME, row, 'season')

    def _combine_season_stats(self, table_rows: List[BeautifulSoup], career_stats: List[BeautifulSoup],
                             all_stats_dict: Dict) -> Dict:
        """Combine stats for each season from a table.

        Parameters
        ----------
        table_rows : List[BeautifulSoup]
            List of table rows containing season stats.
        career_stats : List[BeautifulSoup]
            List of footer rows containing career stats.
        all_stats_dict : Dict
            Dictionary mapping seasons to their HTML data.

        Returns
        -------
        Dict
            Updated dictionary with combined stats.
        """
        most_recent_season = self._most_recent_season
        for row in table_rows or []:
            if any(cls in row.get('class', []) for cls in ['minors_table', 'spacer', 'partial_table']):
                continue
            season = self._parse_season(row)
            all_stats_dict.setdefault(season, {'data': ''})['data'] += str(row)
            most_recent_season = season
        self._most_recent_season = most_recent_season
        if career_stats:
            all_stats_dict.setdefault('Career', {'data': ''})['data'] += str(career_stats[0])
        return all_stats_dict

    def _combine_all_stats(self, player_info: BeautifulSoup) -> Dict:
        """Combine stats from all tables by season.

        Parameters
        ----------
        player_info : BeautifulSoup
            Parsed HTML containing player stats.

        Returns
        -------
        Dict
            Dictionary mapping seasons to their combined HTML data.
        """
        all_stats_dict = {}
        for table_id in ['batting_standard', 'standard_fielding', 'appearances', 'pitching_standard']:
            table = player_info.find('table', id=table_id)
            table_rows = table.find('tbody').find_all('tr') if table else []
            career_rows = table.find('tfoot').find_all('tr') if table else []
            all_stats_dict = self._combine_season_stats(table_rows, career_rows, all_stats_dict)
        return all_stats_dict

    def _parse_nationality(self, player_info: BeautifulSoup) -> None:
        """Parse the player's nationality.

        Parameters
        ----------
        player_info : BeautifulSoup
            Parsed HTML containing player stats.
        """
        for span in player_info.find_all('span'):
            class_attr = span.get('class', [])
            if any('f-i' in cls for cls in class_attr):
                nationality_code = span.get_text(strip=True)
                nationality = NATIONALITY.get(nationality_code, '')
                setattr(self, '_nationality', nationality)
                break

    def _parse_player_information(self, player_info: BeautifulSoup) -> None:
        """Parse general player information.

        Parameters
        ----------
        player_info : BeautifulSoup
            Parsed HTML containing player stats.
        """
        for field in ['height', 'weight', 'name']:
            value = _parse_field(PLAYER_SCHEME, player_info, field)
            setattr(self, f'_{field}', value)

    def _parse_birth_date(self, player_info: BeautifulSoup) -> None:
        """Parse the player's birth date.

        Parameters
        ----------
        player_info : BeautifulSoup
            Parsed HTML containing player stats.
        """
        birth_date = player_info.find('span', {'itemprop': 'birthDate'})
        date = birth_date.get('data-birth', '') if birth_date else ''
        setattr(self, '_birth_date', date)

    def _parse_team_name(self, team_cell: BeautifulSoup) -> str:
        """Parse the team name from a contract table cell.

        Parameters
        ----------
        team_cell : BeautifulSoup
            Cell containing team name HTML.

        Returns
        -------
        str
            Team name (e.g., 'Houston Astros').
        """
        if not team_cell:
            return ''
        text = team_cell.get_text(strip=True).replace('\xa0', ' ')
        return text

    def _parse_contract(self, player_info: BeautifulSoup) -> None:
        """Parse the player's contract details.

        Parameters
        ----------
        player_info : BeautifulSoup
            Parsed HTML containing player stats.
        """
        contract = {}
        salary_table = player_info.find('table', id='br-salaries')
        if salary_table:
            for row in salary_table.find('tbody').find_all('tr'):
                if 'spacer' in row.get('class', []):
                    continue
                year = _parse_field(PLAYER_SCHEME, row, 'year_ID')
                if not year.strip():
                    continue
                age = _parse_field(PLAYER_SCHEME, row, 'age')
                team_cell = row.find('td', {'data-stat': 'team_name'})
                team = self._parse_team_name(team_cell)
                salary = _parse_field(PLAYER_SCHEME, row, 'Salary')
                contract[year] = {'age': age, 'team': team, 'salary': salary}
        setattr(self, '_contract', contract)

    def _parse_value(self, html_data: BeautifulSoup, field: str) -> Optional[List[str]]:
        """Parse a field's values from HTML.

        Parameters
        ----------
        html_data : BeautifulSoup
            Parsed HTML containing stats.
        field : str
            The field to parse, per PLAYER_SCHEME.

        Returns
        -------
        List[str] or None
            List of values for the field across seasons, or None if not found.
        """
        if field not in PLAYER_SCHEME:
            return None
        scheme = PLAYER_SCHEME[field]
        try:
            items = [elem.get_text(strip=True) for elem in html_data.select(scheme)]
            return items if items else None
        except Exception:
            return None

    def _pull_player_data(self) -> Dict:
        """Pull and aggregate all player information.

        Returns
        -------
        Dict
            Dictionary mapping seasons to their HTML data.
        """
        player_info = self._retrieve_html_page()
        if not player_info:
            return {}
        self._parse_player_information(player_info)
        self._parse_nationality(player_info)
        self._parse_birth_date(player_info)
        self._parse_contract(player_info)
        all_stats = self._combine_all_stats(player_info)
        setattr(self, '_season', list(all_stats.keys()))
        return all_stats

    def _find_initial_index(self) -> None:
        """Set the index to career stats."""
        for index, season in enumerate(self._season or []):
            if season == 'Career':
                self._index = index
                break
        else:
            self._index = 0

    def __call__(self, requested_season: str = '') -> 'Player':
        """Query stats for a specific season.

        Parameters
        ----------
        requested_season : str, optional
            Season in 'YYYY' format (e.g., '2023') or 'Career'. Defaults to 'Career'.

        Returns
        -------
        Player
            Self with updated index for the requested season.
        """
        requested_season = 'Career' if requested_season.lower() == 'career' or not requested_season else requested_season
        for index, season in enumerate(self._season or []):
            if season == requested_season:
                self._index = index
                break
        return self

    def _dataframe_fields(self) -> Dict:
        """Create a dictionary of fields for DataFrame.

        Returns
        -------
        Dict
            Dictionary of attribute names and their values for the current season.
        """
        return {
            'assists': self.assists,
            'at_bats': self.at_bats,
            'bases_on_balls': self.bases_on_balls,
            'batting_average': self.batting_average,
            'birth_date': self.birth_date,
            'complete_games': self.complete_games,
            'defensive_chances': self.defensive_chances,
            'defensive_runs_saved_above_average': self.defensive_runs_saved_above_average,
            'defensive_runs_saved_above_average_per_innings': self.defensive_runs_saved_above_average_per_innings,
            'double_plays_turned': self.double_plays_turned,
            'doubles': self.doubles,
            'errors': self.errors,
            'fielding_percentage': self.fielding_percentage,
            'games': self.games,
            'games_catcher': self.games_catcher,
            'games_center_fielder': self.games_center_fielder,
            'games_designated_hitter': self.games_designated_hitter,
            'games_first_baseman': self.games_first_baseman,
            'games_in_batting_order': self.games_in_batting_order,
            'games_in_defensive_lineup': self.games_in_defensive_lineup,
            'games_left_fielder': self.games_left_fielder,
            'games_outfielder': self.games_outfielder,
            'games_pinch_hitter': self.games_pinch_hitter,
            'games_pinch_runner': self.games_pinch_runner,
            'games_pitcher': self.games_pitcher,
            'games_right_fielder': self.games_right_fielder,
            'games_second_baseman': self.games_second_baseman,
            'games_shortstop': self.games_shortstop,
            'games_started': self.games_started,
            'games_third_baseman': self.games_third_baseman,
            'grounded_into_double_plays': self.grounded_into_double_plays,
            'height': self.height,
            'hits': self.hits,
            'home_runs': self.home_runs,
            'innings_played': self.innings_played,
            'intentional_bases_on_balls': self.intentional_bases_on_balls,
            'league_fielding_percentage': self.league_fielding_percentage,
            'league_range_factor_per_game': self.league_range_factor_per_game,
            'league_range_factor_per_nine_innings': self.league_range_factor_per_nine_innings,
            'name': self.name,
            'nationality': self.nationality,
            'on_base_percentage': self.on_base_percentage,
            'on_base_plus_slugging_percentage': self.on_base_plus_slugging_percentage,
            'on_base_plus_slugging_percentage_plus': self.on_base_plus_slugging_percentage_plus,
            'plate_appearances': self.plate_appearances,
            'player_id': self.player_id,
            'position': self.position,
            'putouts': self.putouts,
            'range_factor_per_game': self.range_factor_per_game,
            'range_factor_per_nine_innings': self.range_factor_per_nine_innings,
            'runs': self.runs,
            'runs_batted_in': self.runs_batted_in,
            'sacrifice_flies': self.sacrifice_flies,
            'sacrifice_hits': self.sacrifice_hits,
            'season': self.season,
            'slugging_percentage': self.slugging_percentage,
            'stolen_bases': self.stolen_bases,
            'team_abbreviation': self.team_abbreviation,
            'times_caught_stealing': self.times_caught_stealing,
            'times_hit_by_pitch': self.times_hit_by_pitch,
            'times_struck_out': self.times_struck_out,
            'total_bases': self.total_bases,
            'total_fielding_runs_above_average': self.total_fielding_runs_above_average,
            'total_fielding_runs_above_average_per_innings': self.total_fielding_runs_above_average_per_innings,
            'triples': self.triples,
            'weight': self.weight,
            'balks': self.balks,
            'bases_on_balls_given': self.bases_on_balls_given,
            'bases_on_balls_given_per_nine_innings': self.bases_on_balls_given_per_nine_innings,
            'batters_faced': self.batters_faced,
            'batters_struckout_per_nine_innings': self.batters_struckout_per_nine_innings,
            'earned_runs_allowed': self.earned_runs_allowed,
            'era': self.era,
            'era_plus': self.era_plus,
            'fielding_independent_pitching': self.fielding_independent_pitching,
            'games_finished': self.games_finished,
            'hits_against_per_nine_innings': self.hits_against_per_nine_innings,
            'hits_allowed': self.hits_allowed,
            'home_runs_against_per_nine_innings': self.home_runs_against_per_nine_innings,
            'home_runs_allowed': self.home_runs_allowed,
            'intentional_bases_on_balls_given': self.intentional_bases_on_balls_given,
            'losses': self.losses,
            'runs_allowed': self.runs_allowed,
            'saves': self.saves,
            'shutouts': self.shutouts,
            'strikeouts': self.strikeouts,
            'strikeouts_thrown_per_walk': self.strikeouts_thrown_per_walk,
            'times_hit_player': self.times_hit_player,
            'whip': self.whip,
            'wild_pitches': self.wild_pitches,
            'win_percentage': self.win_percentage,
            'wins': self.wins
        }

    @property
    def dataframe(self) -> Optional[pd.DataFrame]:
        """Return a pandas DataFrame of player stats.

        Returns
        -------
        pd.DataFrame or None
            DataFrame of stats for each season, indexed by season, or None if no data.
        """
        if not self._season:
            return None
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
    def season(self) -> Optional[str]:
        """Return the current season ('YYYY' or 'Career')."""
        return self._season[self._index] if self._season and self._index is not None else None

    @property
    def name(self) -> Optional[str]:
        """Return the player's full name (e.g., 'Jose Altuve')."""
        return self._name

    @most_recent_decorator
    def team_abbreviation(self) -> Optional[str]:
        """Return the team's abbreviation (e.g., 'HOU')."""
        return self._team_abbreviation

    @most_recent_decorator
    def position(self) -> Optional[str]:
        """Return the player's primary position."""
        return self._position

    @property
    def height(self) -> Optional[str]:
        """Return the player's height (e.g., '5-6')."""
        return self._height

    @property
    def weight(self) -> Optional[int]:
        """Return the player's weight in pounds."""
        if not self._weight:
            return None
        return int(self._weight.replace('lb', ''))

    @property
    def birth_date(self) -> Optional[str]:
        """Return the player's birth date."""
        return self._birth_date

    @property
    def nationality(self) -> Optional[str]:
        """Return the player's nationality."""
        return self._nationality

    @property
    def contract(self) -> Optional[Dict]:
        """Return the player's contract details by year."""
        return self._contract

    @int_property_decorator
    def games(self) -> Optional[int]:
        """Return the number of games played."""
        return self._games

    @int_property_decorator
    def games_started(self) -> Optional[int]:
        """Return the number of games started."""
        return self._games_started

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
    def doubles(self) -> Optional[int]:
        """Return the number of doubles."""
        return self._doubles

    @int_property_decorator
    def triples(self) -> Optional[int]:
        """Return the number of triples."""
        return self._triples

    @int_property_decorator
    def home_runs(self) -> Optional[int]:
        """Return the number of home runs."""
        return self._home_runs

    @int_property_decorator
    def runs_batted_in(self) -> Optional[int]:
        """Return the number of runs batted in."""
        return self._runs_batted_in

    @int_property_decorator
    def stolen_bases(self) -> Optional[int]:
        """Return the number of stolen bases."""
        return self._stolen_bases

    @int_property_decorator
    def times_caught_stealing(self) -> Optional[int]:
        """Return the number of times caught stealing."""
        return self._times_caught_stealing

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
    def on_base_plus_slugging_percentage(self) -> Optional[float]:
        """Return the on-base plus slugging percentage."""
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
        """Return the number of double plays grounded into."""
        return self._grounded_into_double_plays



    @int_property_decorator
    def times_hit_by_pitch(self):
        """Return the number of times hit by pitch."""
        return self._times_hit_by_pitch

    @int_property_decorator
    def sacrifice_hits(self):
        """Return the number of sacrifice hits."""
        return self._sacrifice_hits



    @int_property_decorator
    def sacrifice_flies(self):
        """Return the number of sacrifice flies."""
        return self._sac_flies



    @int_property
    def intentional_bases_on_balls(self):
        """Return the number of intentional walks."""
        return self._intentional_bases_on_balls



    @int_property
    def complete_games(self):
        """Return the number of complete games."""
        return self._complete_games



    @float_property
    def innings_played(self) -> Optional[float]:
        """Return the total innings played."""
        return self._innings_played



    @int_property_decorator
    def defensive_chances(self):
        """Return the number of defensive chances."""
        return self._defensive_chances



    @int_property
    def putouts(self):
        """Return the number of putouts."""
        return self._putouts



    @int_property
    def assists(self):
        """Return the number of assists."""
        return self._assists



    @int_property
    def errors(self):
        """Return the number of errors."""
        return self._errors



    @int_property_decorator
    def double_plays_turned(self):
        """Return the number of double plays turned."""
        return self._double_plays_turned

    @float_property_decorator
    def fielding_percentage(self) -> Optional[float]:
        """Return the fielding percentage (0-1)."""
        return self._fielding_percentage

    @int_property_decorator
    def total_fielding_runs_above_average(self):
        """Return the number of runs above average fielding."""
        return self._total_fielding_runs_above_average

    @int_property_decorator
    def defensive_runs_saved_above_average(self):
        """Return the number of defensive runs above average."""
        return self._defensive_runs_saved_above_average



    @float_property_decorator
    def total_fielding_runs_above_average_per_innings(self) -> Optional[float]:
        """Return the runs per 1,200 innings fielding."""
        return self._total_fielding_runs_above_average_per_innings



    @float_property_decorator
    def defensive_runs_saved_above_average_per_nine(self) -> Optional[float]:
        """Return the defensive runs per 1,200 innings."""
        return self._defensive_runs_saved_above_average_per_nine



    @float_property_decorator
    def range_factor_per_nine(self):
        """Return the range factor per nine innings."""
        return self._range_factor_per_nine



    @float_property_decorator
    def range_factor_per_game(self):
        """Return the range factor per game."""
        return self._range_factor_per_game



    @float_property_decorator
    def league_fielding_percentage(self):
        """Return the league average fielding percentage."""
        return self._league_fielding_percentage



    @float_property_decorator
    def league_range_factor_per_nine(self):
        """Return the league average range factor per nine innings."""
        return self._league_range_factor_per_nine



    @float_property_decorator
    def league_range_factor_per_game(self):
        """Return the league average range factor per game."""
        return self._league_range_factor_per_game



    @int_property_decorator
    def games_in_batting_order(self):
        """Return the number of games in batting order."""
        return self._games_in_batting_order



    @int_property_decorator
    def games_in_defensive_lineup(self):
        """Return the number of games in defensive lineup."""
        return self._games_in_defensive_lineup



    @int_property_decorator
    def games_pitcher(self):
        """Return the number of games as pitcher."""
        return self._games_pitcher



    @int_property_decorator
    def games_catcher(self):
        """Return the number of games as catcher."""
        return self._games_catcher



    @int_property_decorator
    def games_first_baseman(self):
        """Return the number of games as first baseman."""
        return self._games_first_baseman



    @int_property_decorator
    def games_second_baseman(self):
        """Return the number of games as second baseman."""
        return self._games_second_baseman



    @int_property_decorator
    def games_third_baseman(self):
        """Return the number of games as third baseman."""
        return self._games_third_baseman



    @int_property_decorator
    def games_shortstop(self):
        """Return the number of games as shortstop."""
        return self._games_shortstop



    @int_property_decorator
    def games_left_fielder(self):
        """Return the number of games as left fielder."""
        return self._games_left_fielder



    @int_property_decorator
    def games_center_fielder(self):
        """Return the number of games as center fielder."""
        return self._games_center_fielder



    @int_property_decorator
    def games_right_field(self):
        """Return the number of games as right fielder."""
        return self._games_right_fielder



    @int_property_decorator
    def games_outfielder(self):
        """Return the number of games as outfielder."""
        return self._games_outfielder



    @int_property_decorator
    def games_designated_hitter(self):
        """Return the number of games as designated hitter."""
        return self._games_designated_hitter



    @int_property_decoratoraz
    def games_pinch_hitter(self):
        """Return the number of games as pinch hitter."""
        return self._games_pinch_hitter



    @int_property_decorator
    def games_pinch_runner(self):
        """Return the number of games as pinch runner."""
        return self._games_pinch_runner



    @int_property_decorator
    def wins(self) -> Optional[int]:
        """Return the number of wins as a pitcher."""
        return self._wins



    @int_property_decorator
    def losses(self) -> Optional[int]:
        """Return the number of losses as a pitcher."""
        return self._losses



    @float_property_decorator
    def win_percentage(self) -> Optional[float]:
        """Return the win percentage as a pitcher (0-1)."""
        return self._win_percentage



    @float_property_decorator
    def era(self) -> Optional[float]:
        """Return the earned run average."""
        return self._era

    @int_property_decorator
    def games_finished(self) -> Optional[int]:
        """Return the number of games finished as a pitcher."""
        return self._games_finished

    @int_property_decorator
    def shutouts(self) -> Optional[int]:
        """Return the number of shutouts."""
        return self._shutouts

    @int_property_decorator
    def saves(self) -> Optional[int]:
        """Return the number of saves."""
        return self._saves

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
    def intentional_bases_on_balls_given(self) -> Optional[int]:
        """Return the number of intentional walks given."""
        return self._intentional_bases_on_balls_given

    @int_property_decorator
    def strikeouts(self) -> Optional[int]:
        """Return the number of strikeouts thrown as a pitcher."""
        return self._strikeouts

    @int_property_decorator
    def times_hit_player(self) -> Optional[int]:
        """Return the number of times a batter was hit."""
        return self._times_hit_player

    @int_property_decorator
    def balks(self) -> Optional[int]:
        """Return the number of balks."""
        return self._balks

    @int_property_decorator
    def wild_pitches(self) -> Optional[int]:
        """Return the number of wild pitches."""
        return self._wild_pitches

    @int_property_decorator
    def batters_faced(self) -> Optional[int]:
        """Return the number of batters faced."""
        return self._batters_faced

    @float_property_decorator
    def era_plus(self) -> Optional[float]:
        """Return the park-adjusted ERA."""
        return self._era_plus

    @float_property_decorator
    def fielding_independent_pitching(self) -> Optional[float]:
        """Return the fielding-independent pitching metric."""
        return self._fielding_independent_pitching

    @float_property_decorator
    def whip(self) -> Optional[float]:
        """Return the walks plus hits per inning pitched."""
        return self._whip

    @float_property_decorator
    def hits_against_per_nine_innings(self) -> Optional[float]:
        """Return the hits per nine innings allowed."""
        return self._hits_against_per_nine_innings

    @float_property_decorator
    def home_runs_against_per_nine_innings(self) -> Optional[float]:
        """Return the home runs per nine innings allowed."""
        return self._home_runs_against_per_nine_innings

    @float_property_decorator
    def bases_on_balls_given_per_nine_innings(self) -> Optional[float]:
        """Return the walks per nine innings given."""
        return self._bases_on_balls_given_per_nine_innings

    @float_property_decorator
    def batters_struckout_per_nine_innings(self) -> Optional[float]:
        """Return the strikeouts per nine innings."""
        return self._batters_struckout_per_nine_innings

    @float_property_decorator
    def strikeouts_thrown_per_walk(self) -> Optional[float]:
        """Return the strikeouts per walk ratio."""
        return self._strikeouts_thrown_per_walk

class Roster:
    """A collection of players on an MLB team for a given season.

    Fetches and stores player data for a team's roster, creating Player instances
    for each player with detailed stats, or a slimmed-down dictionary of player IDs
    and names if slim mode is enabled.

    Parameters
    ----------
    team : str
        The team's abbreviation (e.g., 'HOU' for Houston Astros).
    year : str, optional
        The 4-digit year (e.g., '2023'). Defaults to the current year.
    slim : bool, optional
        If True, returns only player IDs and names, improving performance. Defaults to False.

    Attributes
    ----------
    players : List[Player] or Dict[str, str]
        List of Player instances if slim=False, or dictionary of player IDs to names if slim=True.
    coach : str
        The team's coach's name.
    """
    def __init__(self, team: str, year: Optional[str] = None, slim: bool = False):
        self._team: str = team
        self._slim: bool = slim
        self._coach: Optional[str] = None
        self._players: Union[List[Player], Dict[str, str]] = {} if slim else []
        self._find_players_with_coach(year)

    def __str__(self) -> str:
        """Return the string representation of the roster."""
        if self._slim:
            return '\n'.join(f'{name} ({pid})'.strip() for pid, name in self._players.items())
        return '\n'.join(f'{player.name()} ({player.player_id})'.strip() for player in self._players)
    
    def __repr__(self) -> str:
        """Return the string representation of the roster."""
        return self.__str__()

    def _create_url(self) -> Optional[str]:
        """Build the roster URL for a given year.

        Parameters
        ----------
        year : str
            The 4-digit year.

        Returns
        -------
        str
            URL for the team's roster page.
        """
        return ROSTER_URL % (self._team.upper(), year)
    
    def _pull_team_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch the team's roster page.

        Parameters
        ----------
        url : str
            URL for the team's roster page.

        Returns
        -------
        BeautifulSoup or None
            Parsed HTML of the roster page, or None if fetching fails.
        """
        return _fetch_html(url)

    def _get_player_id(self, player: BeautifulSoup) -> str:
        """Parse a player's ID from a roster row."""
        """
        Parameters
        ----------
        player : BeautifulSoup
            HTML row for a player.

        Returns
        -------
        str
            The player's ID or empty string if none.
        """
        name_tag = player.find('td', {'data': 'player'}).find('a') if player else None
        return _parse_player_id(name_tag) if name_tag else ''

    def _get_name(self, player: BeautifulSoup) -> str:
        """Parse a player's name from a roster row."""
        """
        Parameters
        ----------
        player : BeautifulSoup
            HTML row for a player.

        Returns
        -------
        str
            The player's name or empty string if not found.
        """
        name_tag = player.find('td', {'data': 'player'}).find('a') if player else None
        return name_tag.get('a')_text(strip=True) if name_tag else ''

    def _parse_coach(self, soup: BeautifulSoup) -> Optional[str]:
        """Parse the team's coach."""
        """
        Parameters
        ----------
        soup : BeautifulSoup
            Parsed HTML of the roster page.

        Returns
        -------
        Optional[str]
            Coach's name or None if not found.
        """
        for p in soup.find('p').find('p') if soup else []):
            strong = p.find('strong')
            if strong and strong.get_text(strip=True) == 'Manager:':
                coach_tag = p.find('a')
                return coach_tag.get('a')_text(strip=True) if coach_tag else None
        return None

    def _find_players_with_coach(self, year: Optional[str]) -> None:
        """Fetch players and coach for the roster."""
        if not year:
            year = _resolve_year(year)
            test_url = self._create_url(year)
            if not _fetch_html(test_url):
                prev_year = str(int(year) - 1)
                if _fetch_html(self._create_url(prev_year)):
                    year = prev_year
        url = self._create_url(year)
        page = self._pull_team_page(url)
        if not page:
            raise ValueError(f"Cannot load team page: {url}")
        
        players_parsed = set()
        for table_id in ['team_batting', 'team_pitching']:
            table = page.find('table', id=table_id)
            if not table:
                continue
            for row in table.find('tbody').find_all('tr'):
                if 'thead' in row.get('class', []):
                    continue
                player_id = self._get_player_id(row)
                if not player_id or (table_id == 'team_pitching' and player_id in players):
                    continue
                if self._slim:
                    name = self._get_name(row)
                    self._players[player_id] = name
                else:
                    player = Player(player_id)
                    self._players.append(player)
                players.append(player_id)
        
        self._coach = self._parse_coach(page)

    @property
    def players(self) -> Union[List[Player], Dict[str, str]]:
        """Return the roster's players."""
        return self._players

    @property
    def coach(self) -> Optional[str]:
        """Return the coach's name."""
        return self._coach