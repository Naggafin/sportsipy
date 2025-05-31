import pandas as pd
from ..base import AbstractParser, int_property_decorator, float_property_decorator, _fetch_html, _parse_field, _clean_stat, _get_stats_table, _resolve_year
from .constants import PLAYER_SCHEME, PLAYER_URL, ROSTER_URL, DETAILED_STATS
from .player import AbstractPlayer

class Player(AbstractPlayer):
    """Representation of an NFL player's statistics across seasons.

    Retrieves comprehensive player statistics from pro-football-reference.com
    for a given player ID, including passing, rushing, receiving, and defensive stats.
    Supports querying stats for specific seasons or career totals.

    Parameters
    ----------
    player_id : str
        The player's ID (e.g., 'BreeDr00' for Drew Brees), typically in the format
        'LlllFfNN' where 'Llll' is the first four letters of the last name,
        'Ff' is the first two letters of the first name, and 'NN' is a numeric suffix.

    Attributes
    ----------
    name : str or None
        The player's full name.
    player_id : str
        The player's unique ID.
    season : str
        The current season being queried ('YYYY' or 'Career').
    team_abbreviation : str or None
        The team's 3-letter abbreviation (e.g., 'NOR').
    """
    def __init__(self, player_id):
        self._most_recent_season = ''
        self._detailed_stats_seasons = []
        self._index = 0
        self._detailed_stats_index = 0
        self._player_id = player_id
        self._season = []
        self._name = None
        self._team_abbreviation = []
        self._position = []
        self._height = None
        self._weight = None
        self._birth_date = None
        self._games = []
        self._games_started = []
        self._approximate_value = []
        # Passing-specific stats
        self._qb_record = []
        self._completed_passes = []
        self._attempted_passes = []
        self._passing_completion = []
        self._passing_yards = []
        self._passing_touchdowns = []
        self._passing_touchdown_percentage = []
        self._interceptions_thrown = []
        self._interception_percentage = []
        self._longest_pass = []
        self._passing_yards_per_attempt = []
        self._adjusted_yards_per_attempt = []
        self._yards_per_completed_pass = []
        self._yards_per_game_played = []
        self._quarterback_rating = []
        self._espn_qbr = []
        self._times_sacked = []
        self._yards_lost_to_sacks = []
        self._net_yards_per_pass_attempt = []
        self._adjusted_net_yards_per_pass_attempt = []
        self._sack_percentage = []
        self._fourth_quarter_comebacks = []
        self._game_winning_drives = []
        self._yards_per_attempt_index = []
        self._net_yards_per_attempt_index = []
        self._adjusted_yards_per_attempt_index = []
        self._adjusted_net_yards_per_attempt_index = []
        self._completion_percentage_index = []
        self._touchdown_percentage_index = []
        self._interception_percentage_index = []
        self._sack_percentage_index = []
        self._passer_rating_index = []
        # Rushing-specific stats
        self._rush_attempts = []
        self._rush_yards = []
        self._rush_touchdowns = []
        self._longest_rush = []
        self._rush_yards_per_attempt = []
        self._rush_yards_per_game = []
        self._rush_attempts_per_game = []
        # Advanced rushing stats
        self._first_downs_rushing = []
        self._rush_yards_before_contact = []
        self._rush_yards_before_contact_per_attempt = []
        self._rush_yards_after_contact = []
        self._rush_yards_after_contact_per_attempt = []
        self._rush_broken_tackles = []
        self._rush_attempts_per_broken_tackle = []
        # Receiving-specific stats
        self._times_pass_target = []
        self._receptions = []
        self._receiving_yards = []
        self._receiving_yards_per_reception = []
        self._receiving_touchdowns = []
        self._longest_reception = []
        self._receptions_per_game = []
        self._receiving_yards_per_game = []
        self._catch_percentage = []
        # Advanced receiving stats
        self._first_downs_receiving = []
        self._receiving_yards_before_catch = []
        self._receiving_yards_before_catch_per_reception = []
        self._receiving_yards_after_catch = []
        self._receiving_yards_after_catch_per_reception = []
        self._receiving_broken_tackles = []
        self._receptions_per_broken_tackle = []
        self._dropped_passes = []
        self._drop_percentage = []
        # Combined receiving and rushing stats
        self._touches = []
        self._yards_per_touch = []
        self._yards_from_scrimmage = []
        self._rushing_and_receiving_touchdowns = []
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
        self._yards_per_kickoff_return = []
        self._all_purpose_yards = []
        # Kicking-specific stats
        self._less_than_nineteen_yards_field_goal_attempts = []
        self._less_than_nineteen_yards_field_goals_made = []
        self._twenty_to_twenty_nine_yard_field_goal_attempts = []
        self._twenty_to_twenty_nine_yard_field_goals_made = []
        self._thirty_to_thirty_nine_yard_field_goal_attempts = []
        self._thirty_to_thirty_nine_yard_field_goals_made = []
        self._forty_to_forty_nine_yard_field_goal_attempts = []
        self._forty_to_forty_nine_yard_field_goals_made = []
        self._fifty_plus_yard_field_goal_attempts = []
        self._fifty_plus_yard_field_goals_made = []
        self._field_goals_attempted = []
        self._field_goals_made = []
        self._longest_field_goal_made = []
        self._field_goal_percentage = []
        self._extra_points_attempted = []
        self._extra_points_made = []
        self._extra_point_percentage = []
        # Punting-specific stats
        self._punts = []
        self._total_punt_yards = []
        self._longest_punt = []
        self._blocked_punts = []
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
        self._tackles = []
        self._assists_on_tackles = []
        self._safeties = []
        AbstractPlayer.__init__(self, player_id)
        self._pull_player_data()

    def __str__(self):
        """Return string representation of the player.

        Returns
        -------
        str
            Player name and ID (e.g., 'Drew Brees (BreeDr00)').
        """
        return f'{self.name} ({self.player_id})'

    def __repr__(self):
        """Return string representation of the player."""
        return self.__str__()

    def _build_url(self):
        """Build the player's stats page URL.

        Returns
        -------
        str
            URL for the player's stats page.
        """
        first_char = self._player_id[0].lower()
        return PLAYER_URL % (first_char, self._player_id)

    def _parse_season(self, row):
        """Parse the season from a stats table row.

        Parameters
        ----------
        row : BeautifulSoup element
            A table row containing player stats.

        Returns
        -------
        str
            The season in 'YYYY' format, cleaned of extra characters.
        """
        season = _parse_field(PLAYER_SCHEME, row, 'season') or ''
        return season.replace('*', '').replace('+', '')

    def _combine_season_stats(self, table_rows, career_stats, all_stats_dict, detailed):
        """Combine stats from a table into the stats dictionary.

        Parameters
        ----------
        table_rows : list
            List of BeautifulSoup row elements from a stats table.
        career_stats : list
            List of BeautifulSoup row elements from the table footer.
        all_stats_dict : dict
            Dictionary of stats by season.
        detailed : bool
            True if the table contains advanced stats.

        Returns
        -------
        dict
            Updated stats dictionary.
        """
        most_recent_season = self._most_recent_season
        detailed_stats_seasons = self._detailed_stats_seasons
        for row in table_rows:
            season = self._parse_season(row)
            if not season:
                continue
            all_stats_dict.setdefault(season, {'data': ''})['data'] += str(row)
            if detailed:
                detailed_stats_seasons.append(season)
            else:
                most_recent_season = season
        self._most_recent_season = most_recent_season
        if detailed:
            self._detailed_stats_seasons = list(set(detailed_stats_seasons))
        if career_stats:
            all_stats_dict.setdefault('Career', {'data': ''})['data'] += str(career_stats[0])
        return all_stats_dict

    def _combine_all_stats(self, soup):
        """Combine stats from all tables.

        Parameters
        ----------
        soup : BeautifulSoup
            Parsed HTML of the player's stats page.

        Returns
        -------
        dict
            Dictionary of stats by season.
        """
        all_stats_dict = {}
        table_ids = [
            'passing', 'passing_advanced', 'rushing_and_receiving',
            'receiving_and_rushing', 'detailed_rushing_and_receiving',
            'detailed_receiving_and_rushing', 'defense', 'returns', 'kicking'
        ]
        for table_id in table_ids:
            table_rows = _get_stats_table(soup, table_id)
            career_stats = _get_stats_table(soup, table_id, footer=True)
            all_stats_dict = self._combine_season_stats(
                table_rows, career_stats, all_stats_dict, 'detailed' in table_id
            )
        return all_stats_dict

    def _parse_player_information(self, soup):
        """Parse general player information.

        Parameters
        ----------
        soup : BeautifulSoup
            Parsed HTML of the player's stats page.
        """
        for field in ['name', 'height', 'weight']:
            value = _parse_field(PLAYER_SCHEME, soup, field)
            setattr(self, f'_{field}', value)

    def _parse_birth_date(self, soup):
        """Parse the player's birth date.

        Parameters
        ----------
        soup : BeautifulSoup
            Parsed HTML of the player's stats page.
        """
        birth_span = soup.find('span', id='necro-birth')
        birth_date = birth_span['data-birth'] if birth_span and 'data-birth' in birth_span.attrs else None
        self._birth_date = birth_date

    def _pull_player_data(self):
        """Pull and aggregate player data.

        Returns
        -------
        dict or None
            Dictionary of player stats by season, or None if data cannot be fetched.
        """
        url = self._build_url()
        soup = _fetch_html(url)
        if not soup or 'Page Not Found (404 error)' in str(soup):
            return None
        all_stats = self._combine_all_stats(soup)
        if not all_stats:
            return None
        self._parse_player_information(soup)
        self._parse_birth_date(soup)
        seasons = sorted([s for s in all_stats if s != 'Career'] + ['Career'])
        self._season = seasons
        self._index = seasons.index('Career') if 'Career' in seasons else 0
        for season in seasons:
            row = BeautifulSoup(all_stats[season]['data'], 'lxml').find('tr')
            if not row:
                continue
            for field in self.__dict__:
                if not field.startswith('_') or field in ['_index', '_detailed_stats_index', '_most_recent_season', '_detailed_stats_seasons', '_player_id', '_season', '_name', '_height', '_weight', '_birth_date']:
                    continue
                short_field = field.lstrip('_')
                value = _parse_field(PLAYER_SCHEME, row, short_field)
                getattr(self, field).append(value)
        return all_stats

    def __call__(self, requested_season=''):
        """Query stats for a specific season.

        Parameters
        ----------
        requested_season : str, optional
            The season to query ('YYYY' or 'Career'). Defaults to 'Career'.

        Returns
        -------
        Player
            Self, with updated index for the requested season.
        """
        requested_season = 'Career' if requested_season.lower() == 'career' or not requested_season else requested_season
        if requested_season in self._season:
            self._index = self._season.index(requested_season)
        if requested_season in self._detailed_stats_seasons:
            self._detailed_stats_index = self._detailed_stats_seasons.index(requested_season)
        return self

    def _dataframe_fields(self):
        """Create dictionary of fields for DataFrame.

        Returns
        -------
        dict
            Dictionary of attribute names and values for the current season.
        """
        fields = {
            'player_id': self.player_id,
            'name': self.name,
            'season': self.season,
            'team_abbreviation': self.team_abbreviation,
            'position': self.position,
            'height': self.height,
            'weight': self.weight,
            'birth_date': self.birth_date,
            'games': self.games,
            'games_started': self.games_started,
            'approximate_value': self.approximate_value,
            'qb_record': self.qb_record,
            'completed_passes': self.completed_passes,
            'attempted_passes': self.attempted_passes,
            'passing_completion': self.passing_completion,
            'passing_yards': self.passing_yards,
            'passing_touchdowns': self.passing_touchdowns,
            'passing_touchdown_percentage': self.passing_touchdown_percentage,
            'interceptions_thrown': self.interceptions_thrown,
            'interception_percentage': self.interception_percentage,
            'longest_pass': self.longest_pass,
            'passing_yards_per_attempt': self.passing_yards_per_attempt,
            'adjusted_yards_per_attempt': self.adjusted_yards_per_attempt,
            'yards_per_completed_pass': self.yards_per_completed_pass,
            'yards_per_game_played': self.yards_per_game_played,
            'quarterback_rating': self.quarterback_rating,
            'espn_qbr': self.espn_qbr,
            'times_sacked': self.times_sacked,
            'yards_lost_to_sacks': self.yards_lost_to_sacks,
            'net_yards_per_pass_attempt': self.net_yards_per_pass_attempt,
            'adjusted_net_yards_per_pass_attempt': self.adjusted_net_yards_per_pass_attempt,
            'sack_percentage': self.sack_percentage,
            'fourth_quarter_comebacks': self.fourth_quarter_comebacks,
            'game_winning_drives': self.game_winning_drives,
            'yards_per_attempt_index': self.yards_per_attempt_index,
            'net_yards_per_attempt_index': self.net_yards_per_attempt_index,
            'adjusted_yards_per_attempt_index': self.adjusted_yards_per_attempt_index,
            'adjusted_net_yards_per_attempt_index': self.adjusted_net_yards_per_attempt_index,
            'completion_percentage_index': self.completion_percentage_index,
            'touchdown_percentage_index': self.touchdown_percentage_index,
            'interception_percentage_index': self.interception_percentage_index,
            'sack_percentage_index': self.sack_percentage_index,
            'passer_rating_index': self.passer_rating_index,
            'rush_attempts': self.rush_attempts,
            'rush_yards': self.rush_yards,
            'rush_touchdowns': self.rush_touchdowns,
            'longest_rush': self.longest_rush,
            'rush_yards_per_attempt': self.rush_yards_per_attempt,
            'rush_yards_per_game': self.rush_yards_per_game,
            'rush_attempts_per_game': self.rush_attempts_per_game,
            'first_downs_rushing': self.first_downs_rushing,
            'rush_yards_before_contact': self.rush_yards_before_contact,
            'rush_yards_before_contact_per_attempt': self.rush_yards_before_contact_per_attempt,
            'rush_yards_after_contact': self.rush_yards_after_contact,
            'rush_yards_after_contact_per_attempt': self.rush_yards_after_contact_per_attempt,
            'rush_broken_tackles': self.rush_broken_tackles,
            'rush_attempts_per_broken_tackle': self.rush_attempts_per_broken_tackle,
            'times_pass_target': self.times_pass_target,
            'receptions': self.receptions,
            'receiving_yards': self.receiving_yards,
            'receiving_yards_per_reception': self.receiving_yards_per_reception,
            'receiving_touchdowns': self.receiving_touchdowns,
            'longest_reception': self.longest_reception,
            'receptions_per_game': self.receptions_per_game,
            'receiving_yards_per_game': self.receiving_yards_per_game,
            'catch_percentage': self.catch_percentage,
            'first_downs_receiving': self.first_downs_receiving,
            'receiving_yards_before_catch': self.receiving_yards_before_catch,
            'receiving_yards_before_catch_per_reception': self.receiving_yards_before_catch_per_reception,
            'receiving_yards_after_catch': self.receiving_yards_after_catch,
            'receiving_yards_after_catch_per_reception': self.receiving_yards_after_catch_per_reception,
            'receiving_broken_tackles': self.receiving_broken_tackles,
            'receptions_per_broken_tackle': self.receptions_per_broken_tackle,
            'dropped_passes': self.dropped_passes,
            'drop_percentage': self.drop_percentage,
            'touches': self.touches,
            'yards_per_touch': self.yards_per_touch,
            'yards_from_scrimmage': self.yards_from_scrimmage,
            'rushing_and_receiving_touchdowns': self.rushing_and_receiving_touchdowns,
            'fumbles': self.fumbles,
            'punt_returns': self.punt_returns,
            'punt_return_yards': self.punt_return_yards,
            'punt_return_touchdown': self.punt_return_touchdown,
            'longest_punt_return': self.longest_punt_return,
            'yards_per_punt_return': self.yards_per_punt_return,
            'kickoff_returns': self.kickoff_returns,
            'kickoff_return_yards': self.kickoff_return_yards,
            'kickoff_return_touchdown': self.kickoff_return_touchdown,
            'longest_kickoff_return': self.longest_kickoff_return,
            'yards_per_kickoff_return': self.yards_per_kickoff_return,
            'all_purpose_yards': self.all_purpose_yards,
            'less_than_nineteen_yards_field_goal_attempts': self.less_than_nineteen_yards_field_goal_attempts,
            'less_than_nineteen_yards_field_goals_made': self.less_than_nineteen_yards_field_goals_made,
            'twenty_to_twenty_nine_yard_field_goal_attempts': self.twenty_to_twenty_nine_yard_field_goal_attempts,
            'twenty_to_twenty_nine_yard_field_goals_made': self.twenty_to_twenty_nine_yard_field_goals_made,
            'thirty_to_thirty_nine_yard_field_goal_attempts': self.thirty_to_thirty_nine_yard_field_goal_attempts,
            'thirty_to_thirty_nine_yard_field_goals_made': self.thirty_to_thirty_nine_yard_field_goals_made,
            'forty_to_forty_nine_yard_field_goal_attempts': self.forty_to_forty_nine_yard_field_goal_attempts,
            'forty_to_forty_nine_yard_field_goals_made': self.forty_to_forty_nine_yard_field_goals_made,
            'fifty_plus_yard_field_goal_attempts': self.fifty_plus_yard_field_goal_attempts,
            'fifty_plus_yard_field_goals_made': self.fifty_plus_yard_field_goals_made,
            'field_goals_attempted': self.field_goals_attempted,
            'field_goals_made': self.field_goals_made,
            'longest_field_goal_made': self.longest_field_goal_made,
            'field_goal_percentage': self.field_goal_percentage,
            'extra_points_attempted': self.extra_points_attempted,
            'extra_points_made': self.extra_points_made,
            'extra_point_percentage': self.extra_point_percentage,
            'punts': self.punts,
            'total_punt_yards': self.total_punt_yards,
            'longest_punt': self.longest_punt,
            'blocked_punts': self.blocked_punts,
            'interceptions': self.interceptions,
            'yards_returned_from_interception': self.yards_returned_from_interception,
            'interceptions_returned_for_touchdown': self.interceptions_returned_for_touchdown,
            'longest_interception_return': self.longest_interception_return,
            'passes_defended': self.passes_defended,
            'fumbles_forced': self.fumbles_forced,
            'fumbles_recovered': self.fumbles_recovered,
            'yards_recovered_from_fumble': self.yards_recovered_from_fumble,
            'fumbles_recovered_for_touchdown': self.fumbles_recovered_for_touchdown,
            'sacks': self.sacks,
            'tackles': self.tackles,
            'assists_on_tackles': self.assists_on_tackles,
            'safeties': self.safeties
        }
        return fields

    @property
    def dataframe(self):
        """Return a pandas DataFrame of player stats.

        Returns
        -------
        pandas.DataFrame or None
            DataFrame of stats for all seasons, indexed by season, or None if no seasons.
        """
        if not self._season:
            return None
        rows = []
        indices = []
        temp_index = self._index
        for season in self._season:
            self._index = self._season.index(season)
            rows.append(self._dataframe_fields())
            indices.append(season)
        self._index = temp_index
        return pd.DataFrame(rows, index=indices)

    @property
    def season(self):
        """Return the current season.

        Returns
        -------
        str
            Season in 'YYYY' format or 'Career'.
        """
        return self._season[self._index] if self._season else 'Career'

    @property
    def team_abbreviation(self):
        """Return the team abbreviation.

        Returns
        -------
        str or None
            Team's 3-letter abbreviation (e.g., 'NOR').
        """
        return self._team_abbreviation[self._index] if self._team_abbreviation else None

    @property
    def position(self):
        """Return the player's primary position.

        Returns
        -------
        str or None
            Primary position.
        """
        return self._position[self._index] if self._position else None

    @property
    def height(self):
        """Return the player's height.

        Returns
        -------
        str or None
            Height in 'feet-inches' format.
        """
        return self._height

    @property
    def weight(self):
        """Return the player's weight.

        Returns
        -------
        int or None
            Weight in pounds.
        """
        return int(self._weight.replace('lb', '')) if self._weight else None

    @property
    def birth_date(self):
        """Return the player's birth date.

        Returns
        -------
        str or None
            Birth date in 'YYYY-MM-DD' format.
        """
        return self._birth_date

    @int_property_decorator
    def games(self):
        """Return the number of games played.

        Returns
        -------
        int or None
            Number of games participated in.
        """
        return self._games

    @int_property_decorator
    def games_started(self):
        """Return the number of games started.

        Returns
        -------
        int or None
            Number of games started.
        """
        return self._games_started

    @int_property_decorator
    def approximate_value(self):
        """Return the approximate value.

        Returns
        -------
        int or None
            Approximate value score.
        """
        return self._approximate_value

    @property
    def qb_record(self):
        """Return the quarterback record.

        Returns
        -------
        str or None
            Record in 'W-L-T' format.
        """
        return self._qb_record[self._index] if self._qb_record else None

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

    @float_property_decorator
    def passing_completion(self):
        """Return the passing completion percentage.

        Returns
        -------
        float or None
            Percentage of passes completed (0-100).
        """
        return self._passing_completion

    @int_property_decorator
    def passing_yards(self):
        """Return the passing yards.

        Returns
        -------
        int or None
            Total passing yards.
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

    @float_property_decorator
    def passing_touchdown_percentage(self):
        """Return the passing touchdown percentage.

        Returns
        -------
        float or None
            Percentage of passes resulting in touchdowns (0-100).
        """
        return self._passing_touchdown_percentage

    @int_property_decorator
    def interceptions_thrown(self):
        """Return the number of interceptions thrown.

        Returns
        -------
        int or None
            Number of interceptions.
        """
        return self._interceptions_thrown

    @float_property_decorator
    def interception_percentage(self):
        """Return the interception percentage.

        Returns
        -------
        float or None
            Percentage of passes intercepted (0-100).
        """
        return self._interception_percentage

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
    def passing_yards_per_attempt(self):
        """Return the yards per pass attempt.

        Returns
        -------
        float or None
            Average yards per pass attempt.
        """
        return self._passing_yards_per_attempt

    @float_property_decorator
    def adjusted_yards_per_attempt(self):
        """Return the adjusted yards per attempt.

        Returns
        -------
        float or None
            Adjusted yards per pass attempt.
        """
        return self._adjusted_yards_per_attempt

    @float_property_decorator
    def yards_per_completed_pass(self):
        """Return the yards per completed pass.

        Returns
        -------
        float or None
            Average yards per completed pass.
        """
        return self._yards_per_completed_pass

    @float_property_decorator
    def yards_per_game_played(self):
        """Return the passing yards per game.

        Returns
        -------
        float or None
            Average passing yards per game.
        """
        return self._yards_per_game_played

    @float_property_decorator
    def quarterback_rating(self):
        """Return the quarterback rating.

        Returns
        -------
        float or None
            Quarterback rating score.
        """
        return self._quarterback_rating

    @float_property_decorator
    def espn_qbr(self):
        """Return the ESPN QBR.

        Returns
        -------
        float or None
            ESPN Total Quarterback Rating.
        """
        return self._espn_qbr

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
    def yards_lost_to_sacks(self):
        """Return the yards lost to sacks.

        Returns
        -------
        int or None
            Yards lost due to sacks.
        """
        return self._yards_lost_to_sacks

    @float_property_decorator
    def net_yards_per_pass_attempt(self):
        """Return the net yards per pass attempt.

        Returns
        -------
        float or None
            Net yards per pass attempt, including sacks.
        """
        return self._net_yards_per_pass_attempt

    @float_property_decorator
    def adjusted_net_yards_per_pass_attempt(self):
        """Return the adjusted net yards per pass attempt.

        Returns
        -------
        float or None
            Adjusted net yards per pass attempt.
        """
        return self._adjusted_net_yards_per_pass_attempt

    @float_property_decorator
    def sack_percentage(self):
        """Return the sack percentage.

        Returns
        -------
        float or None
            Percentage of pass attempts resulting in sacks (0-100).
        """
        return self._sack_percentage

    @int_property_decorator
    def fourth_quarter_comebacks(self):
        """Return the number of fourth-quarter comebacks.

        Returns
        -------
        int or None
            Number of comebacks led in the fourth quarter.
        """
        return self._fourth_quarter_comebacks

    @int_property_decorator
    def game_winning_drives(self):
        """Return the number of game-winning drives.

        Returns
        -------
        int or None
            Number of game-winning drives led.
        """
        return self._game_winning_drives

    @int_property_decorator
    def yards_per_attempt_index(self):
        """Return the yards per attempt index.

        Returns
        -------
        int or None
            Index comparing yards per attempt (100 is average).
        """
        return self._yards_per_attempt_index

    @int_property_decorator
    def net_yards_per_attempt_index(self):
        """Return the net yards per attempt index.

        Returns
        -------
        int or None
            Index comparing net yards per attempt.
        """
        return self._net_yards_per_attempt_index

    @int_property_decorator
    def adjusted_yards_per_attempt_index(self):
        """Return the adjusted yards per attempt index.

        Returns
        -------
        int or None
            Index comparing adjusted yards per attempt.
        """
        return self._adjusted_yards_per_attempt_index

    @int_property_decorator
    def adjusted_net_yards_per_attempt_index(self):
        """Return the adjusted net yards per attempt index.

        Returns
        -------
        int or None
            Index comparing adjusted net yards per attempt.
        """
        return self._adjusted_net_yards_per_attempt_index

    @int_property_decorator
    def completion_percentage_index(self):
        """Return the completion percentage index.

        Returns
        -------
        int or None
            Index comparing completion percentage.
        """
        return self._completion_percentage_index

    @int_property_decorator
    def touchdown_percentage_index(self):
        """Return the touchdown percentage index.

        Returns
        -------
        int or None
            Index comparing touchdown percentage.
        """
        return self._touchdown_percentage_index

    @int_property_decorator
    def interception_percentage_index(self):
        """Return the interception percentage index.

        Returns
        -------
        int or None
            Index comparing interception percentage.
        """
        return self._interception_percentage_index

    @int_property_decorator
    def sack_percentage_index(self):
        """Return the sack percentage index.

        Returns
        -------
        int or None
            Index comparing sack percentage.
        """
        return self._sack_percentage_index

    @int_property_decorator
    def passer_rating_index(self):
        """Return the passer rating index.

        Returns
        -------
        int or None
            Index comparing quarterback rating.
        """
        return self._passer_rating_index

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

    @float_property_decorator
    def rush_yards_per_attempt(self):
        """Return the yards per rush attempt.

        Returns
        -------
        float or None
            Average yards per rush.
        """
        return self._rush_yards_per_attempt

    @float_property_decorator
    def rush_yards_per_game(self):
        """Return the rushing yards per game.

        Returns
        -------
        float or None
            Average rushing yards per game.
        """
        return self._rush_yards_per_game

    @float_property_decorator
    def rush_attempts_per_game(self):
        """Return the rush attempts per game.

        Returns
        -------
        float or None
            Average rush attempts per game.
        """
        return self._rush_attempts_per_game

    @int_property_decorator
    def first_downs_rushing(self):
        """Return the rushing first downs.

        Returns
        -------
        int or None
            Number of first downs from rushing.
        """
        return self._first_downs_rushing

    @int_property_decorator
    def rush_yards_before_contact(self):
        """Return the yards before contact on rushes.

        Returns
        -------
        int or None
            Total yards before contact.
        """
        return self._rush_yards_before_contact

    @float_property_decorator
    def rush_yards_before_contact_per_attempt(self):
        """Return the yards before contact per rush.

        Returns
        -------
        float or None
            Average yards before contact per rush.
        """
        return self._rush_yards_before_contact_per_attempt

    @int_property_decorator
    def rush_yards_after_contact(self):
        """Return the yards after contact on rushes.

        Returns
        -------
        int or None
            Total yards after contact.
        """
        return self._rush_yards_after_contact

    @float_property_decorator
    def rush_yards_after_contact_per_attempt(self):
        """Return the yards after contact per rush.

        Returns
        -------
        float or None
            Average yards after contact per rush.
        """
        return self._rush_yards_after_contact_per_attempt

    @int_property_decorator
    def rush_broken_tackles(self):
        """Return the number of broken tackles on rushes.

        Returns
        -------
        int or None
            Number of tackles broken.
        """
        return self._rush_broken_tackles

    @float_property_decorator
    def rush_attempts_per_broken_tackle(self):
        """Return the rushes per broken tackle.

        Returns
        -------
        float or None
            Average rushes per broken tackle.
        """
        return self._rush_attempts_per_broken_tackle

    @int_property_decorator
    def times_pass_target(self):
        """Return the number of times targeted.

        Returns
        -------
        return self._times_pass_target
    """
        return self._times_pass_target

    @int_property_decorator
    def receptions(self):
        """Return the number of receptions.

        Returns
        -------
        int or float
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

    @float_property_decorator
    def receptions_per_game(self):
        """Return the receptions per game.

        Returns
        -------
        float or None
        Average receptions per game.
        """
        return self._receptions_per_game

    @float_property_decorator
    def receiving_yards_per_game(self):
        """Return the receiving yards per game.

        Returns
        -------
        float or None
        Average receiving yards per game.
        
        """
        return self._receiving_yards_per_game

    @float_property_decorator
    def catch_percentage(self):
        """
        Return the catch percentage.

        Returns
        return
            float or None
            Percentage of passes caught (0-100).
        """
        return self._catch_percentage

    @int_property_decorator
    def first_downs_receiving(self):
        """
        Return the receiving first downs.

        Returns
        -------
        int or None
        Number of first downs from receiving.
        """
        return self._first_downs_receiving

    @int_property_decorator
    def receiving_yards_before_catch(self):
        """
        Return the yards before catch on receptions.

        Returns
        -------
        int or None
        Total yards before catch.
        """
        return self._receiving_yards_before_catch

    @float_property_decorator
    def receiving_yards_before_catch_per_reception(self):
        """
        Return the yards before catch per reception.

        Returns
        -------
        float or None
        Average yards before catch per reception.
        """
        return self._receiving_yards_before_catch_per_reception

    @int_property_decorator
    def receiving_yards_after_catch(self):
        """
        Return the yards after catch on receptions.

        Returns
        -------
        int or None
        Total yards after catch.
        """
        return self._receiving_yards_after_catch

    @float_property_decorator
    def receiving_yards_after_catch_per_reception(self):
        """
        Return the yards after catch per reception.

        Returns
        -------
        float or None
        Average yards after catch per reception.
        """
        return self._receiving_yards_after_catch_per_reception

    @int_property_decorator
    def receiving_broken_tackles(self):
        """
        Return a number of broken tackles on receptions.
        Returns
        -------
        int or None
        Number of tackles broken.
        """
        return self._receiving_broken_tackles

    @float_property_decorator
    def receptions_per_broken_tackle(self):
        """
        Return the receptions per broken tackle.

        Returns
        -------
        float or None
        Number of receptions per broken tackle.
        """
        return self._receptions_per_broken_tackle

    @int_property_decorator
    def dropped_passes(self):
        """
        Return a number of dropped passes.

        Returns
        -------
        int or None
        Number of passes dropped.
        """
        return self._dropped_passes

    @float_property_decorator
    def drop_percentage(self):
        """
        Return the drop percentage.

        Returns
        -------
        float or None
        Percentage of passes dropped (0-100).
        """
        return self._drop_percentage

    @int_property_decorator
    def touches(self):
        """
        Return a number of touches (rushes + receptions).

        Returns
        -------
        int or None
        Total touches.
        """
        return self._touches

    @float_property_decorator
    def yards_per_touch(self):
        """
        Return a yards per touch.

        Returns
        -------
        float or None
        Average yards per touch.
        """
        return self._yards_per_touch

    @int_property_decorator
    def yards_from_scrimmage(self):
        """
        Return a yards from scrimmage.

        Returns
        -------
        int or None
        Total yards from rushing and receiving.
        """
        return self._yards_from_scrimmage

    @int_property_decorator
    def rushing_and_receiving_touchdowns(self):
        """
        Return a rushing and receiving touchdowns.

        Returns
        -------
        int or None
        Total rushing and receiving touchdowns.
        """
        return self._rushing_and_receiving_touchdowns

    @int_property_decorator
    def fumbles(self):
        """
        Return a number of fumbles.

        Returns
        -------
        int or None
        Number of fumbles.
        """
        return self._fumbles

    @int_property_decorator
    def punt_punt_returns(self):
        """
        Return a number of punt returns.

        Returns
        -------
        int or None
        Number of punt returns.
        """
        return self._punt_returns

    @int_property_decorator
    def punt_return_yards(self):
        """
        Return a punt return yards.

        Returns
        -------
        int or None
        Total punt return yards.
        """
        return self._punt_return_yards

    @int_property_decorator
    def punt_return_touchdown(self):
        """
        Return a punt return touchdowns.

        Returns
        -------
        int or None
        Number of punt return touchdowns.
        """
        return self._return_touchdown

    @int_property_decorator
    def longest_punt_return(self):
        """
        Return a longest punt return.

        Returns
        -------
        int or None
        Yards of longest punt return.
        """
        return self._longest_punt_return

    @float_property_decorator
    def yards_per_punt_return(self):
        """
        Return a yards per punt return.

        Returns
        -------
        float or None
        Average yards per punt return.
        """
        return self._yards_per_punt_return

    @int_property_decorator
    def kickoff_returns(self):
        """
        Return a number of kickoff returns.

        Returns
        -------
        int or None
        Number of kickoff returns.
        """
        return self._kickoff_returns

    @int_property_decorator
    def kickoff_return_yards(self):
        """
        Return a kickoff return yards.

        Returns
        -------
        int or None
        Total kickoff return yards.
        """
        return self._kickoff_return_yards

    @int_property_decorator
    def kickoff_return_touchdown(self):
        """
        Return a kickoff return touchdowns.

        Returns
        -------
        int or None
        Number of kickoff return touchdowns.
        """
        return self._kickoff_return_touchdown

    @int_property_decorator
    def longest_kickoff_return(self):
        """
        Return the longest kickoff return.

        Returns
        -------
            int or None
            Yards of longest kickoff return.
        """
        return self._longest_kickoff_return

    @float_property_decorator
    def yards_per_kickoff_return(self):
        """
        Return the yards per kickoff return.

        Returns
        -------
            float or None
            Average yards per kickoff return.
        """
        return self._yards_per_kickoff_return

    @int_property_decorator
    def all_purpose_yards(self):
        """
        Return the all-purpose yards.

        Returns
        -------
        int or None
        Total yards from receptions, rushes, and returns.
        """
        return self._all_purpose_yards

    @int_property_decorator
    less_than_nineteen_yards_field_goal_attempts(self):
        """
        Returns the number of field goal attempts from <19 yards.
        Returns
        -------
            int or None
            Number of field goal attempts from <19 yards.
        """
        return self._less_than_nineteen_yards_field_goal_attempts

    @int_property_decorator
    def less_than_nineteen_yards_field_goals_made(self):
        """
        Return the field goals made from <19 yards.

        Returns
        -------
        int or None
        Number of field goals made from <19 yards.
        """
        return self._less_than_nineteen_yards_field_goals_made

    @int_property_decorator
    def twenty_to_twenty_nine_yard_field_goal_attempts(self):
        """
        Return a number of field goal attempts from 20-29 yards.

        Returns
        -------
        int or None
        Number of field goal attempts from 20-29 yards.
        """
        return self._twenty_to_twenty_nine_yard_field_goal_attempts

    @int_property_decorator
    def twenty_to_twenty_nine_yard_field_goals_made(self):
        """
        Return a number of field goals made from 20-29 yards.

        Returns
        -------
        int or None
        Number of field goals made from 20-29 yards.
        """
        return self._twenty_to_twenty_nine_yard_field_goals_made

    @int_property_decorator
    def thirty_to_thirty_nine_yard_field_goal_attempts(self):
        """
        Return a number of field goal attempts from 30-39 yards.

        Returns
        -------
        int or None
        Number of field goal attempts from 30-39 yards.
        """
        return self._thirty_to_thirty_nine_yard_field_goal_attempts

    @int_property_decorator
    def thirty_to_thirty_nine_yard_field_goals_made(self):
        """
        Return a number of field goals made from 30-39 yards.

        Returns
        -------
        int or None
        Number of field goals made from 30-39 yards.
        """
        return self._thirty_to_thirty_nine_yard_field_goals_made

    @int_property_decorator
    def forty_to_forty_nine_yard_field_goal_attempts(self):
        """
        Return a number of field goal attempts from 40-49 yards.

        Returns
        -------
        int or None
        Number of field goal attempts from 40-49 yards.
        """
        return self._forty_to_forty_nine_yard_field_goal_attempts

    @int_property_decorator
    def forty_to_forty_nine_yard_field_goals_made(self):
        """
        Return a number of field goals made from 40-49 yards.

        Returns
        -------
        int or None
        Number of field goals made from 40-49 yards.
        """
        return self._forty_to_forty_nine_yard_field_goals_made

    @int_property_decorator
    def fifty_plus_yard_field_goal_attempts(self):
        """
        Return a number of field goal attempts from 50+ yards.

        Returns
        -------
        int or None
        Number of field goal attempts from 50+ yards.
        """
        return self._fifty_plus_yard_field_goal_attempts

    @int_property_decorator
    def fifty_plus_yards_field_goals_made(self):
        """
        Return a number of field goals made from 50+ yards.

        Returns
        -------
        int or None
        Number of field goals made from 50+ yards.
        """
        return self._fifty_plus_yard_field_goals_made

    @int_property_decorator
    def field_goals_attempted(self):
        """
        Return a total number of field goal attempts.

        Returns
        -------
        int or None
        Total field goal attempts.
        """
        return self._field_goals_attempted

    @int_property_decorator
    def field_goals_made(self):
        """
        Return a total number of field goals made.

        Returns
        -------
        int or None
        Total field goals made.
        """
        return self._field_goals_made

    @int_property_decorator
    def longest_field_goal_made(self):
        """
        Return a longest field goal made.

        Returns
        -------
        int or None
        Yards of longest field goal made.
        """
        return self._longest_field_goal_made

    @float_property_decorator
    def field_goal_percentage(self):
        """
        Return a field goal percentage.

        Returns
        -------
        float or None
        Percentage of field goals made (0-100).
        """
        return self._field_goal_percentage

    @int_property_decorator
    def extra_points_attempted(self):
        """
        Return a number of extra point attempts.

        Returns
        -------
        int or None
        Number of extra points attempted.
        """
        return self._extra_points_attempted

    @int_property_decorator
    def extra_points_made(self):
        """
        Return a number of extra points made.

        Returns
        -------
        int or None
        Number of extra points made.
        """
        return self._extra_points_made

    @float_property_decorator
    def extra_point_percentage(self):
        """
        Return a extra point percentage.

        Returns
        -------
        float or None
        Percentage of extra points made (0-100).
        """
        return self._extra_point_percentage

    @int_property_decorator
    def punts(self):
        """
        Return a number of punts.

        Returns
        -------
        int or None
        Number of punts.
        """
        return self._punts

    @int_property_decorator
    def total_punt_yards(self):
        """
        Return a total punt yards.

        Returns
        -------
        int or None
        Total yards punted.
        """
        return self._total_punt_yards

    @int_property_decorator
    def longest_punt(self):
        """
        Return a longest punt.

        Returns
        -------
        int or None
        Yards of longest punt.
        """
        return self._longest_punt

    @int_property_decorator
    def blocked_punts(self):
        """
        Return a number of blocked punts.

        Returns
        -------
        int or None
        Number of punts blocked.
        """
        return self._blocked_punts

    @int_property_decorator
    def interceptions(self):
        """
        Return a number of interceptions.

        Returns
        -------
        int or None
        Number of passes intercepted.
        """
        return self._interceptions

    @int_property_decorator
    def yards_returned_from_interception(self):
        """
        Return a interception return yards.

        Returns
        -------
        int or None
        Yards from interception returns.
        """
        return self._yards_returned_from_interception

    @int_property_decorator
    def interceptions_returned_for_touchdown(self):
        """
        Return a number of interception return touchdowns.

        Returns
        -------
        int or None
        Number of touchdowns from interceptions.
        """
        return self._interceptions_returned_for_touchdown

    @int_property_decorator
    def longest_interception_return(self):
        """
        Return a longest interception return.

        Returns
        -------
        int or None
        Yards of longest interception return.
        """
        return self._longest_interception_return

    @int_property_decorator
    def passes_defended(self):
        """
        Return a number of passes defended.

        Returns
        -------
        int or None
        Number of passes defended.
        """
        return self._passes_defended

    @int_property_decorator
    def fumbles_forced(self):
        """
        Return a number of fumbles forced.

        Returns
        -------
        int or None
        Number of fumbles forced.
        """
        return self._fumbles_forced

    @int_property_decorator
    def fumbles_recovered(self):
        """
        Return a number of fumbles recovered.

        Returns
        -------
        int or None
        Number of fumbles recovered.
        """
        return self._fumbles_recovered

    @int_property_decorator
    def yards_recovered_from_fumble(self):
        """
        Return a fumble recovery yards.

        Returns
        -------
        int or None
        Yards from fumble recoveries.
        """
        return self._yards_recovered_from_fumble

    @int_property_decorator
    def fumbles_recovered_for_touchdown(self):
        """
        Return the number of fumble recovery touchdowns.

        Returns
        -------
        int or None
            Number of touchdowns from fumble recoveries.
        """
        return self._fumbles_recovered_for_touchdown

    @float_property_decorator
    def sacks(self):
        """
        Return the number of sacks.

        Returns
        -------
        float or None
        Number of sacks (can be fractional).
        """
        return self._sacks

    @int_property_decorator
    def tackles(self):
        """
        Return the number of tackles.

        Returns
        -------
        int or None
        Number of tackles.
        """
        return self._tackles

    @int_property_decorator
    def assists_on_tackles(self):
        """
        Return the number of tackle assists.

        Returns
        -------
        int or None
        Number of tackle assists.
        """
        return self._assists_on_tackles

    @int_property_decorator
    def safeties(self):
        """
        Return the number of safeties.

        Returns
        -------
        int or None
        Number of safeties scored.
        """
        return self._safeties

class Roster:
    """
    Representation of an NFL team's roster for a season.

    Retrieves player and coach information for a team's roster from pro-football-reference.com.

    Parameters
    ----------
    team : str
        The team's 3-letter abbreviation (e.g., 'KAN' for Kansas City Chiefs).
    year : str or int, optional
        The 4-digit year to check.
 (e.g., '2023'). Defaults to the current or most recent season.
    slim : bool, optional
        If True, returns only player IDs and names. Defaults to False.

    Attributes
    ----------
    team : str
        The team's abbreviation.
    players : list or dict
        List of Player instances (if slim=False) or dict of player IDs to names (if slim=True).
    coach : str or None
        The head coach's name.
    """
    def __init__(self, team, year=None):
, slim=False):
        self._team = team.upper()
        self._slim = slim
        self._coach = None
        self._players = {} if slim else []
        self._find_players(year)

    def __str__(self):
        """
        Return a string representation of the roster.

        Returns
        -------
        str
            Newline-separated list of player names and IDs.
        """
        if self._slim:
            return '\n'.join(f'{name} ({pid})' for pid, name in self._players.items())
        return '\n'.join(str(player) for player in self._players)

    def __repr__(self):
        """
        Return string representation of the roster.
        """
        return self.__str__()

    def _create_url(self, year):
        """
        Build the roster URL.

        Parameters
        ----------
        year : str
            The 4-digit year.

        Returns
        -------
        str
            URL for the team's roster page.
        """
        return ROSTER_URL % (self._team.lower(), year)

    def _get_id(self, player):
        """
        Parse a player's ID from a roster row.

        Parameters
        ----------
        player : BeautifulSoup element
            A row from the roster table.

        Returns
        -------
        str or None
            The player's ID.
        """
        link = player.find('td', {'data-stat': 'player'}).find('a')
        if not link or not link.get('href'):
            return None
        return link['href'].rpartition('/')[1].replace('.htm', '')

    def _get_name(self, player):
        """
        Parse a player's name from a row.

        Parameters
        ----------
        player : BeautifulSoup element
            A row from the roster table.

        Returns
        -------
        str or None
            The player's name.
        """
        link = player.find('td', {'data-stat': 'player'}).find('a')
        return link.text if link else None

    def _parse_coach(self, soup):
        """
        Parse the team's coach.

        Parameters
        ----------
        soup : BeautifulSoup
            Parsed HTML of the roster page.

        Returns
        -------
        str or None
            The coach's name.
        """
        for p in soup.find_all('p'):
            strong = p.find('strong')
            if strong and strong.text.strip() == 'Coach:':
                a = p.find('a')
                return a.text.strip() if a else None
        return None

    def _find_players(self, year):
        """
        Fetch and populate the roster.

        Parameters
        ----------
        year : str or None
            The year to fetch the roster for.

        Raises
        ------
        ValueError
            If the roster page cannot be retrieved.
        """
        year = _resolve_year('nfl', year)
        url = self._create_url(year)
        soup = _fetch_html(url)
        if not soup:
            raise ValueError(f"Cannot retrieve roster for {self._team} in {year}. Check URL: {url}")
        table = soup.find('table', id='roster')
        if table:
            for row in table.find('tbody').find_all('tr', recursive=False):
                player_id = self._get_id(row)
                if not player_id:
                    continue
                if self._slim:
                    name = self._get_name(row)
                    if name:
                        self._players[player_id] = name
                else:
                    self._players.append(Player(player_id))
        self._coach = self._parse_coach(soup)

    @property
    def players(self):
        """
        Return the roster of players.

        Returns
        -------
        list or dict
            List of Player instances (if slim=False) or dict of IDs to names (if slim=True).
        """
        return self._players

    @property
    def coach(self):
        """
        Return the coach's name.

        Returns
        -------
        str or None
            Name of the head coach.
        """
        return self._coach