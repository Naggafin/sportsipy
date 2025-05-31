
import pandas as pd
import re
from datetime import datetime
from pyquery import PyQuery as pq
from urllib.error import HTTPError
from .. import utils
from ..constants import AWAY, HOME
from ..decorators import int_property_decorator
from .constants import (BOXSCORE_ELEMENT_INDEX,
                        BOXSCORE_ELEMENT_SUB_INDEX,
                        BOXSCORE_SCHEME,
                        BOXSCORE_URL,
                        BOXSCORES_URL)
from .player import (AbstractPlayer,
                     _float_property_decorator,
                     _int_property_decorator)
from functools import wraps
from mock import Mock


def nfl_int_property_sub_index(func):
    @property
    @wraps(func)
    def wrapper(*args):
        value = func(*args)
        field = func.__name__
        try:
            field_items = value.replace('--', '-').split('-')
        except AttributeError:
            return None
        try:
            return int(field_items[BOXSCORE_ELEMENT_SUB_INDEX[field]])
        except (TypeError, ValueError, IndexError):
            return None
    return wrapper


class BoxscorePlayer(AbstractPlayer):
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

    @_int_property_decorator
    def yards_lost_from_sacks(self):
        return self._yards_lost_from_sacks

    @_int_property_decorator
    def fumbles_lost(self):
        return self._fumbles_lost

    @_int_property_decorator
    def combined_tackles(self):
        return self._combined_tackles

    @_int_property_decorator
    def solo_tackles(self):
        return self._solo_tackles

    @_int_property_decorator
    def tackles_for_loss(self):
        return self._tackles_for_loss

    @_int_property_decorator
    def quarterback_hits(self):
        return self._quarterback_hits

    @_float_property_decorator
    def average_kickoff_return_yards(self):
        return self._average_kickoff_return_yards


class Boxscore:
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

        self._parse_game_data(uri)

    def __str__(self):
        return f'Boxscore for {self._away_name.text()} at {self._home_name.text()} ({self.date})'

    def __repr__(self):
        return self.__str__()

    def _retrieve_html_page(self, uri):
        url = BOXSCORE_URL % uri
        try:
            url_data = pq(url=url)
        except (HTTPError, AttributeError):
            return None
        if '404 error' in str(url_data):
            return None
        return pq(utils._remove_html_comment_tags(url_data))

    def _parse_game_details(self, boxscore):
        scheme = BOXSCORE_SCHEME["game_details"]
        won_toss = None
        roof = None
        surface = None
        weather = None
        vegas_line = None
        over_under = None

        for line in boxscore(scheme).items():
            if 'won toss' in str(line).lower():
                won_toss = line('td').text()
            elif 'roof' in str(line).lower():
                roof = line('td').text().title()
            elif 'surface' in str(line).lower():
                surface = line('td').text().title()
            elif 'weather' in str(line).lower():
                weather = line('td').text()
            elif 'vegas line' in str(line).lower():
                vegas_line = line('td').text()
            elif 'over/under' in str(line).lower():
                over_under = line('td').text()
        setattr(self, '_won_toss', won_toss)
        setattr(self, '_roof', roof)
        setattr(self, '_surface', surface)
        setattr(self, '_weather', weather)
        setattr(self, '_vegas_line', vegas_line)
        setattr(self, '_over_under', over_under)

    def _parse_game_date_and_location(self, boxscore):
        scheme = BOXSCORE_SCHEME["game_info"]
        items = [i.text() for i in boxscore(scheme).items()]
        game_info = items[0].split('\n')
        attendance = None
        date = None
        duration = None
        stadium = None
        time = None
        date = game_info[0]
        for line in game_info:
            if 'Attendance' in line:
                attendance = line.replace('Attendance: ', '').replace(',', '')
            if 'Time of Game' in line:
                duration = line.replace('Time of Game: ', '')
            if 'Stadium' in line:
                stadium = line.replace('Stadium: ', '')
            if 'Start Time' in line:
                time = line.replace('Start Time: ', '')
        setattr(self, '_attendance', attendance)
        setattr(self, '_date', date)
        setattr(self, '_duration', duration)
        setattr(self, '_stadium', stadium)
        setattr(self, '_time', time)

    def _parse_name(self, field, boxscore):
        scheme = BOXSCORE_SCHEME[field]
        return pq(str(boxscore(scheme)).strip())

    def _parse_summary(self, boxscore):
        team = ['away', 'home']
        summary = {'away': [], 'home': []}
        game_summary = boxscore(BOXSCORE_SCHEME['summary'])
        for ind, team_info in enumerate(game_summary('tbody tr').items()):
            for quarter in list(team_info('td[class="center"]').items())[:-1]:
                if quarter('div'):
                    continue
                try:
                    summary[team[ind]].append(int(quarter.text()))
                except ValueError:
                    summary[team[ind]].append(None)
        return summary

    def _find_boxscore_tables(self, boxscore):
        tables = []
        valid_tables = ['player_offense', 'player_defense', 'returns', 'kicking']

        for table in boxscore('table').items():
            if table.attr['id'] in valid_tables:
                tables.append(table)
        return tables

    def _find_player_id(self, row):
        return row('th').attr('data-append-csv')

    def _find_player_name(self, row):
        return row('a:first').text()

    def _find_home_or_away(self, row):
        name = row('td[data-stat="team"]').text().upper()
        if self._home_abbr and name == self._home_abbr.upper():
            return HOME
        if self._away_abbr and name == self._away_abbr.upper():
            return AWAY
        if name == self.home_abbreviation.upper():
            return HOME
        else:
            return AWAY

    def _extract_player_stats(self, table, player_dict):
        for row in table('tbody tr').items():
            player_id = self._find_player_id(row)
            if not player_id:
                continue
            name = self._find_player_name(row)
            home_or_away = self._find_home_or_away(row)
            try:
                player_dict[player_id]['data'] += str(row).strip()
            except KeyError:
                player_dict[player_id] = {
                    'name': name,
                    'data': str(row).strip(),
                    'team': home_or_away
                }
        return player_dict

    def _instantiate_players(self, player_dict):
        home_players = []
        away_players = []
        for player_id, details in player_dict.items():
            player = BoxscorePlayer(player_id, details['name'], details['data'])
            if details['team'] == HOME:
                home_players.append(player)
            else:
                away_players.append(player)
        return away_players, home_players

    def _find_players(self, boxscore):
        player_dict = {}
        tables = self._find_boxscore_tables(boxscore)
        for table in tables:
            player_dict = self._extract_player_stats(table, player_dict)
        away_players, home_players = self._instantiate_players(player_dict)
        return away_players, home_players

    def _alt_abbreviations(self, boxscore):
        abbreviations = []
        game_info = boxscore(BOXSCORE_SCHEME['team_stats'])

        for column in game_info('th').items():
            if column.text():
                abbreviations.append(column.text())
        if not abbreviations:
            return None, None
        return abbreviations

    def _parse_game_data(self, uri):
        boxscore = self._retrieve_html_page(uri)
        if not boxscore:
            return

        for field in self.__dict__:
            short_field = str(field)[1:]
            if short_field in ['winner', 'winning_name', 'winning_abbr', 'losing_name', 'losing_abbr', 'uri', 'date', 'time', 'stadium', 'attendance', 'duration', 'won_toss', 'roof', 'surface', 'weather', 'vegas_line', 'over_under']:
                continue
            if short_field in ['away_name', 'home_name']:
                value = self._parse_name(short_field, boxscore)
                setattr(self, field, value)
                continue
            if short_field == 'summary':
                value = self._parse_summary(boxscore)
                setattr(self, field, value)
                continue
            index = BOXSCORE_ELEMENT_INDEX.get(short_field, 0)
            value = utils._parse_field(BOXSCORE_SCHEME, boxscore, short_field, index)
            setattr(self, field, value)
        self._parse_game_date_and_location(boxscore)
        self._parse_game_details(boxscore)
        self._away_abbr, self._home_abbr = self._alt_abbreviations(boxscore)
        self._away_players, self._home_players = self._find_players(boxscore)

    @property
    def dataframe(self):
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
            'home_rush_yards': self.home_rush_yards,
            'home_third_down_attempts': self.home_third_down_attempts,
            'home_third_down_conversions': self.home_third_down_conversions,
            'home_time_of_possession': self.home_time_of_possession,
            'home_times_sacked': self.home_times_sacked,
            'home_total_yards': self.home_total_yards,
            'home_turnovers': self.home_turnovers,
            'home_yards_from_penalties': self.home_yards_from_penalties,
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
        return self._away_players

    @property
    def home_players(self):
        return self._home_players

    @property
    def away_abbreviation(self):
        abbr = re.sub(r'.*/teams/', '', str(self._away_name))
        abbr = re.sub(r'/.*', '', abbr)
        return abbr

    @property
    def home_abbreviation(self):
        abbr = re.sub(r'.*/teams/', '', str(self._home_name))
        abbr = re.sub(r'/.*', '', abbr)
        return abbr

    @property
    def date(self):
        return self._date

    @property
    def time(self):
        return self._time

    @property
    def datetime(self):
        dt = None
        if self._date and self._time:
            date = '%s %s' % (self._date, self._time)
            dt = datetime.strptime(date, '%A %b %d, %Y %I:%M%p')
        elif self._date:
            dt = datetime.strptime(self._date, '%A %b %d, %Y')
        return dt

    @property
    def stadium(self):
        return self._stadium

    @int_property_decorator
    def attendance(self):
        return self._attendance

    @property
    def duration(self):
        return self._duration

    @property
    def won_toss(self):
        return self._won_toss

    @property
    def roof(self):
        return self._roof

    @property
    def surface(self):
        return self._surface

    @property
    def weather(self):
        return self._weather

    @property
    def vegas_line(self):
        return self._vegas_line

    @property
    def over_under(self):
        return self._over_under

    @property
    def summary(self):
        return self._summary

    @property
    def winner(self):
        if self.home_points > self.away_points:
            return HOME
        return AWAY

    @property
    def winning_name(self):
        if self.winner == HOME:
            return self._home_name.text()
        return self._away_name.text()

    @property
    def winning_abbr(self):
        if self.winner == HOME:
            return utils._parse_abbreviation(self._home_name)
        return utils._parse_abbreviation(self._away_name)

    @property
    def losing_name(self):
        if self.winner == HOME:
            return self._away_name.text()
        return self._home_name.text()

    @property
    def losing_abbr(self):
        if self.winner == HOME:
            return utils._parse_abbreviation(self._away_name)
        return utils._parse_abbreviation(self._home_name)

    @int_property_decorator
    def away_points(self):
        return self._away_points

    @int_property_decorator
    def away_first_downs(self):
        return self._away_first_downs

    @nfl_int_property_sub_index
    def away_rush_attempts(self):
        return self._away_rush_attempts

    @nfl_int_property_sub_index
    def away_rush_yards(self):
        return self._away_rush_yards

    @nfl_int_property_sub_index
    def away_rush_touchdowns(self):
        return self._away_rush_touchdowns

    @nfl_int_property_sub_index
    def away_pass_completions(self):
        return self._away_pass_completions

    @nfl_int_property_sub_index
    def away_pass_attempts(self):
        return self._away_pass_attempts

    @nfl_int_property_sub_index
    def away_pass_yards(self):
        return self._away_pass_yards

    @nfl_int_property_sub_index
    def away_pass_touchdowns(self):
        return self._away_pass_touchdowns

    @nfl_int_property_sub_index
    def away_interceptions(self):
        return self._away_interceptions

    @nfl_int_property_sub_index
    def away_times_sacked(self):
        return self._away_times_sacked

    @nfl_int_property_sub_index
    def away_yards_lost_from_sacks(self):
        return self._away_yards_lost_from_sacks

    @int_property_decorator
    def away_net_pass_yards(self):
        return self._away_net_pass_yards

    @int_property_decorator
    def away_total_yards(self):
        return self._away_total_yards

    @nfl_int_property_sub_index
    def away_fumbles(self):
        return self._away_fumbles

    @nfl_int_property_sub_index
    def away_fumbles_lost(self):
        return self._away_fumbles_lost

    @int_property_decorator
    def away_turnovers(self):
        return self._away_turnovers

    @nfl_int_property_sub_index
    def away_penalties(self):
        return self._away_penalties

    @nfl_int_property_sub_index
    def away_yards_from_penalties(self):
        return self._away_yards_from_penalties

    @nfl_int_property_sub_index
    def away_third_down_conversions(self):
        return self._away_third_down_conversions

    @nfl_int_property_sub_index
    def away_third_down_attempts(self):
        return self._away_third_down_attempts

    @nfl_int_property_sub_index
    def away_fourth_down_conversions(self):
        return self._away_fourth_down_conversions

    @nfl_int_property_sub_index
    def away_fourth_down_attempts(self):
        return self._away_fourth_down_attempts

    @property
    def away_time_of_possession(self):
        return self._away_time_of_possession

    @int_property_decorator
    def home_points(self):
        return self._home_points

    @int_property_decorator
    def home_first_downs(self):
        return self._home_first_downs

    @nfl_int_property_sub_index
    def home_rush_attempts(self):
        return self._home_rush_attempts

    @nfl_int_property_sub_index
    def home_rush_yards(self):
        return self._home_rush_yards

    @nfl_int_property_sub_index
    def home_rush_touchdowns(self):
        return self._home_rush_touchdowns

    @nfl_int_property_sub_index
    def home_pass_completions(self):
        return self._home_pass_completions

    @nfl_int_property_sub_index
    def home_pass_attempts(self):
        return self._home_pass_attempts

    @nfl_int_property_sub_index
    def home_pass_yards(self):
        return self._home_pass_yards

    @nfl_int_property_sub_index
    def home_pass_touchdowns(self):
        return self._home_pass_touchdowns

    @nfl_int_property_sub_index
    def home_interceptions(self):
        return self._home_interceptions

    @nfl_int_property_sub_index
    def home_times_sacked(self):
        return self._home_times_sacked

    @nfl_int_property_sub_index
    def home_yards_lost_from_sacks(self):
        return self._home_yards_lost_from_sacks

    @int_property_decorator
    def home_net_pass_yards(self):
        return self._home_net_pass_yards

    @int_property_decorator
    def home_total_yards(self):
        return self._home_total_yards

    @nfl_int_property_sub_index
    def home_fumbles(self):
        return self._home_fumbles

    @nfl_int_property_sub_index
    def home_fumbles_lost(self):
        return self._home_fumbles_lost

    @int_property_decorator
    def home_turnovers(self):
        return self._home_turnovers

    @nfl_int_property_sub_index
    def home_penalties(self):
        return self._home_penalties

    @nfl_int_property_sub_index
    def home_yards_from_penalties(self):
        return self._home_yards_from_penalties

    @nfl_int_property_sub_index
    def home_third_down_conversions(self):
        return self._home_third_down_conversions

    @nfl_int_property_sub_index
    def home_third_down_attempts(self):
        return self._home_third_down_attempts

    @nfl_int_property_sub_index
    def home_fourth_down_conversions(self):
        return self._home_fourth_down_conversions

    @nfl_int_property_sub_index
    def home_fourth_down_attempts(self):
        return self._home_fourth_down_attempts

    @property
    def home_time_of_possession(self):
        return self._home_time_of_possession


class Boxscores:
    def __init__(self, week, year, end_week=None):
        self._boxscores = {}
        self._find_games(week, year, end_week)

    def __str__(self):
        weeks = [week.split('-')[0] for week in sorted(self._boxscores.keys())]
        if len(weeks) > 1:
            return f"NFL games for weeks {', '.join(weeks)}"
        return f"NFL games for week {weeks[0]}"

    def __repr__(self):
        return self.__str__()

    @property
    def games(self):
        return self._boxscores

    def _create_url(self, week, year):
        return BOXSCORES_URL % (year, week)

    def _get_requested_page(self, url):
        return pq(url=url)

    def _get_boxscore_uri(self, url):
        uri = re.sub(r'.*/boxscores/', '', str(url))
        uri = re.sub(r'\.htm.*', '', uri).strip()
        return uri

    def _parse_abbreviation(self, abbr):
        abbr = re.sub(r'.*/teams/', '', str(abbr))
        abbr = re.sub(r'/.*', '', abbr)
        return abbr

    def _get_name(self, name):
        team_name = name.text()
        abbr = self._parse_abbreviation(name)
        return team_name, abbr

    def _get_score(self, score_link):
        score = score_link.replace('<td class="right">', '')
        score = score.replace('</td>', '')
        return int(score)

    def _get_team_details(self, game):
        links = [i for i in game('td a').items()]
        away = links[0]
        home = links[-1]
        scores = re.findall(r'<td class="right">\d+</td>', str(game))
        away_score = None
        home_score = None
        if len(scores) == 2:
            away_score = self._get_score(scores[0])
            home_score = self._get_score(scores[1])
        away_name, away_abbr = self._get_name(away)
        home_name, home_abbr = self._get_name(home)
        return away_name, away_abbr, away_score, home_name, home_abbr, home_score

    def _get_team_results(self, team_result_html):
        link = [i for i in team_result_html('td a').items()]
        if len(link) < 1:
            return None
        name, abbreviation = self._get_name(link[0])
        return name, abbreviation

    def _extract_game_info(self, games):
        all_boxscores = []

        for game in games:
            details = self._get_team_details(game)
            away_name, away_abbr, away_score, home_name, home_abbr, home_score = details
            boxscore_url = game('td[class="right gamelink"] a')
            boxscore_uri = self._get_boxscore_uri(boxscore_url)
            losers = [loser for loser in game('tr[class="loser"]').items()]
            winner = self._get_team_results(game('tr[class="winner"]'))
            loser = self._get_team_results(game('tr[class="loser"]'))
            if (len(losers) != 2 and loser and not winner) or (len(losers) != 2 and winner and not loser):
                continue
            winning_name = None
            winning_abbreviation = None
            if winner and len(losers) != 2:
                winning_name, winning_abbreviation = winner
            losing_name = None
            losing_abbreviation = None
            if loser and len(losers) != 2:
                losing_name, losing_abbreviation = loser
            game_info = {
                'boxscore': boxscore_uri,
                'away_name': away_name,
                'away_abbr': away_abbr,
                'away_score': away_score,
                'home_name': home_name,
                'home_abbr': home_abbr,
                'home_score': home_score,
                'winning_name': winning_name,
                'winning_abbr': winning_abbreviation,
                'losing_name': losing_name,
                'losing_abbr': losing_abbreviation
            }
            all_boxscores.append(game_info)
        return all_boxscores

    def _find_games(self, week, year, end_week):
        if not end_week or week > end_week:
            end_week = week
        while week <= end_week:
            url = self._create_url(week, year)
            page = self._get_requested_page(url)
            games = page('table[class="teams"]').items()
            boxscores = self._extract_game_info(games)
            timestamp = '%s-%s' % (week, year)
            self._boxscores[timestamp] = boxscores
            week += 1