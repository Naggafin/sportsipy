from functools import wraps
import re
import requests
from bs4 import BeautifulSoup
from urllib.error import HTTPError
import pandas as pd
from datetime import datetime
import logging
from functools import wraps
import re
import requests
from bs4 import BeautifulSoup
from urllib.error import HTTPError
import pandas as pd
from datetime import datetime
import logging

def int_property_decorator(func):
    """Convert a property to an integer, returning None if conversion fails.

    Parameters
    ----------
    func : callable
        The function to decorate, which retrieves a property value.

    Returns
    -------
    callable
        A wrapped property that converts the function's output to an integer.
    """
    @property
    @wraps(func)
    def wrapper(*args):
        try:
            value = func(*args)
            return int(value) if value else None
        except (ValueError, TypeError):
            return None
    return wrapper

def float_property_decorator(func):
    """Convert a property to a float, returning None if conversion fails.

    Parameters
    ----------
    func : callable
        The function to decorate, which retrieves a property value.

    Returns
    -------
    callable
        A wrapped property that converts the function's output to a float.
    """
    @property
    @wraps(func)
    def wrapper(*args):
        try:
            value = func(*args)
            return float(value) if value else None
        except (ValueError, TypeError):
            return None
    return wrapper

def indexed_int_property_decorator(func):
    """Convert an indexed property to an integer, returning None if conversion fails.

    Parameters
    ----------
    func : callable
        The function to decorate, which retrieves a property value.

    Returns
    -------
    callable
        A wrapped property that converts the indexed function's output to an integer.
    """
    @property
    @wraps(func)
    def wrapper(*args):
        index = args[0]._index
        prop = func(*args)
        try:
            value = _cleanup(prop[index])
            return int(value)
        except (TypeError, ValueError, IndexError):
            return None
    return wrapper

def int_property_decorator_default_zero(func):
    """Convert a property to an integer, returning 0 if conversion fails.

    Parameters
    ----------
    func : callable
        The function to decorate, which retrieves a property value.

    Returns
    -------
    callable
        A wrapped property that converts the function's output to an integer, defaulting to 0.
    """
    @property
    @wraps(func)
    def wrapper(*args):
        index = args[0]._index
        prop = func(*args)
        try:
            value = _cleanup(prop[index])
            return int(value)
        except (TypeError, ValueError, IndexError):
            return 0
    return wrapper

def most_recent_decorator(func):
    """Return the property value for the most recent season.

    Parameters
    ----------
    func : callable
        The function to decorate, which retrieves a property value.

    Returns
    -------
    callable
        A wrapped property that returns the value for the most recent season.
    """
    @property
    @wraps(func)
    def wrapper(*args):
        season = args[0]._most_recent_season
        seasons = args[0]._season
        if not season or not seasons:
            return None
        try:
            index = seasons.index(season)
            prop = func(*args)
            return prop[index]
        except (ValueError, IndexError):
            return None
    return wrapper

def _cleanup(prop):
    """Remove unwanted characters from a property value and handle None cases.

    Parameters
    ----------
    prop : str or None
        The property value to clean, which may include characters like '%', '$', ',', or '+'.

    Returns
    -------
    str
        The cleaned property value with specified characters removed, or an empty string if prop is None.
    """
    try:
        prop = prop.replace('%', '').replace('$', '').replace(',', '').replace('+', '')
        return prop
    except AttributeError:
        return ''

def _parse_entity_data(entity, data, scheme, fields_to_skip=None):
    """Parse entity data from HTML and set attributes.

    Parameters
    ----------
    entity : object
        The entity instance to set attributes on.
    data : dict or str
        If a dict, maps seasons to HTML data; if a str, represents single-game data.
    scheme : dict
        A dictionary mapping field names to CSS selectors.
    fields_to_skip : set, optional
        Field names to skip during parsing (default is None).

    Returns
    -------
    None
        Sets attributes on the entity instance.
    """
    fields_to_skip = fields_to_skip or set()
    for field in entity.__dict__:
        short_field = field.lstrip('_')
        if short_field in fields_to_skip:
            continue
        field_stats = []
        if isinstance(data, dict):
            for _, season_data in data.items():
                soup = BeautifulSoup(season_data['data'], 'html.parser')
                value = _parse_field(scheme, soup, short_field)
                field_stats.append(value)
        else:
            soup = BeautifulSoup(data, 'html.parser')
            adjusted_field = 'boxscore_box_plus_minus' if short_field == 'box_plus_minus' else short_field
            value = _parse_field(scheme, soup, adjusted_field)
            field_stats.append(value)
        setattr(entity, field, field_stats)

def _parse_field(scheme, data, field, index=0, strip=False, secondary_index=None):
    """Extract a field value from HTML data using a scheme.

    Parameters
    ----------
    scheme : dict
        A dictionary mapping field names to CSS selectors.
    data : BeautifulSoup object
        The HTML data to parse.
    field : str
        The field name to extract.
    index : int, optional
        The index of the element to select (default is 0).
    strip : bool, optional
        Whether to strip parentheses from the value (default is False).
    secondary_index : int, optional
        An optional secondary index for nested selections.

    Returns
    -------
    str or None
        The extracted field value, or None if not found.
    """
    if field not in scheme:
        return None
    selector = scheme[field]
    items = data.select(selector)
    if not items or len(items) <= index:
        return None
    value = items[index].text.strip()
    if secondary_index is not None:
        sub_items = items[index].select('td')
        if len(sub_items) > secondary_index:
            value = sub_items[secondary_index].text.strip()
    if strip:
        value = re.sub(r'\(.*\)', '', value).strip()
    return value if value else None

def _remove_html_comment_tags(html):
    """Remove HTML comment tags from a string.

    Parameters
    ----------
    html : str
        The HTML content to process.

    Returns
    -------
    str
        The HTML content with comment tags removed.
    """
    return re.sub(r'<!--|-->', '', html)

def _url_exists(url):
    """Check if a URL exists.

    Parameters
    ----------
    url : str
        The URL to check.

    Returns
    -------
    bool
        True if the URL exists, False otherwise.
    """
    try:
        response = requests.head(url)
        return response.status_code == 200
    except requests.RequestException:
        return False

def _fetch_html(url):
    """Fetch and parse HTML from a URL.

    Parameters
    ----------
    url : str
        The URL to fetch.

    Returns
    -------
    BeautifulSoup or None
        The parsed HTML, or None if the request fails.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return BeautifulSoup(_remove_html_comment_tags(response.text), 'html.parser')
    except (HTTPError, requests.RequestException):
        return None

# TODO: This needs to be updated for general use case, not just NBA
def _fetch_all_teams(year=None, season_file=None):
    """Fetch data for all teams in a given NBA season.

    Parameters
    ----------
    year : str, optional
        The 4-digit year for the season (e.g., '2023'). Defaults to the current season.
    season_file : str, optional
        Path to a local HTML file containing the season page data.

    Returns
    -------
    tuple
        A dictionary mapping team abbreviations to their data and rank, and the resolved year.
    """
    if not year:
        year = _find_year_for_season('nba')
    if season_file:
        with open(season_file, 'r', encoding='utf-8') as f:
            page = BeautifulSoup(f.read(), 'html.parser')
    else:
        url = f'https://www.basketball-reference.com/leagues/NBA_{year}.html'
        page = _fetch_html(url)
        if not page:
            return {}, year
    team_data_dict = {}
    for table in page.select('table[id$="_team-stats"]'):
        for row in table.select('tbody tr'):
            team_name = _parse_field({'abbreviation': 'th[data-stat="team_name"] a'}, row, 'abbreviation')
            if not team_name:
                continue
            abbr = re.search(r'/teams/(\w+)/', row.select_one('th[data-stat="team_name"] a')['href']).group(1)
            team_data_dict[abbr] = {
                'data': str(row),
                'rank': int(row.select_one('th[data-stat="rank_team"]').text) if row.select_one('th[data-stat="rank_team"]') else 0
            }
    return team_data_dict, year

def _get_stats_table(soup, table_id, footer=False):
    """Extract a stats table from HTML.

    Parameters
    ----------
    soup : BeautifulSoup object
        The HTML data to parse.
    table_id : str
        The ID of the table to extract.
    footer : bool, optional
        If True, extract the footer rows (default is False).

    Returns
    -------
    list
        A list of table rows, or empty list if not found.
    """
    table = soup.select_one(f'table#{table_id}')
    if not table:
        return []
    selector = 'tfoot tr' if footer else 'tbody tr'
    return table.select(selector)

def _no_data_found():
    """Handle cases where no data is found.

    Returns
    -------
    None
        Prints a warning message.
    """
    print('No data found.')

def _parse_abbreviation(link):
    """Extract a team abbreviation from a link.

    Parameters
    ----------
    link : BeautifulSoup object
        The link containing the team abbreviation.

    Returns
    -------
    str or None
        The team abbreviation, or None if not found.
    """
    if link and link.get('href'):
        return re.sub(r'.*/teams/|/\d+\.html$', '', link['href'])
    return None

def _find_year_for_season(league):
    """Determine the default season year for a league.

    Parameters
    ----------
    league : str
        The league identifier (e.g., 'nba').

    Returns
    -------
    str
        The default season year as a string.
    """
    current_year = datetime.now().year
    current_month = datetime.now().month
    if league.lower() == 'nba' and current_month >= 10:
        return str(current_year + 1)
    return str(current_year)

def _parse_multi_line_field(soup, selector, index):
    """Parse a field split across multiple lines in HTML.

    Parameters
    ----------
    soup : BeautifulSoup object
        The HTML data to parse.
    selector : str
        The CSS selector for the field.
    index : int
        The index of the line to extract.

    Returns
    -------
    str or None
        The extracted field value, or None if not found.
    """
    items = soup.select(selector)
    if not items:
        return None
    lines = [line.strip() for line in items[0].text.split('\n') if line.strip()]
    if 'AM' not in lines[0] and 'PM' not in lines[0]:
        lines.pop(0) if lines else None
    return lines[index] if len(lines) > index else None

def _parse_team_name(soup, selector, index=0):
    """Parse a team's name from HTML.

    Parameters
    ----------
    soup : BeautifulSoup object
        The HTML data to parse.
    selector : str
        The CSS selector for the team name.
    index : int, optional
        The index of the element to select (default is 0).

    Returns
    -------
    BeautifulSoup object or None
        The tag containing the team's name, or None if not found.
    """
    items = soup.select(selector)
    return items[index] if items and len(items) > index else None

def _extract_table_entities(table, entity_dict, key_attr, name_selector, team=None):
    """Extract entities (e.g., players) from a table.

    Parameters
    ----------
    table : BeautifulSoup object
        The table to parse.
    entity_dict : dict
        The dictionary to store entity data.
    key_attr : str
        The attribute containing the entity's ID (e.g., 'data-append-csv').
    name_selector : str
        The CSS selector for the entity's name.
    team : str, optional
        The team identifier to associate with the entity.

    Returns
    -------
    dict
        The updated entity dictionary.
    """
    for row in table.select('tbody tr'):
        key_elem = row.select_one(f'[{key_attr}]')
        if not key_elem:
            continue
        key = key_elem.get(key_attr)
        name_elem = row.select_one(name_selector)
        name = name_elem.text.strip() if name_elem else ''
        try:
            entity_dict[key]['data'] += str(row).strip()
        except KeyError:
            entity_dict[key] = {
                'name': name,
                'data': str(row).strip(),
                'team': team
            }
    return entity_dict

def _extract_entity_id(row, selector='td[data-stat="player"] a'):
    """Extract an entity ID from a table row.

    Parameters
    ----------
    row : BeautifulSoup object
        The table row to parse.
    selector : str, optional
        The CSS selector for the element containing the ID (default is 'td[data-stat="player"] a').

    Returns
    -------
    str or None
        The entity ID, or None if not found.
    """
    elem = row.select_one(selector)
    if elem and elem.get('href'):
        return re.sub(r'.*/players/./|././html.*$', '', elem['href'])
    return None

def _extract_entity_name(row, selector='td[data-stat="player"] a'):
    """Extract an entity name from a table row.

    Parameters
    ----------
    row : BeautifulSoup object
        The table row to parse.
    selector : str, optional
        The CSS selector for the element containing the name (default is 'td[data-stat="player"] a').

    Returns
    -------
    str or None
        The entity name, or None if not found.
    """
    elem = row.select_one(selector)
    return elem.text.strip() if elem else None

def _parse_attribute(soup, selector, attr=None, mapping=None):
    """Parse an attribute from HTML.

    Parameters
    ----------
    soup : BeautifulSoup object
        The HTML data to parse.
    selector : str
        The CSS selector for the attribute.
    attr : str, optional
        The attribute to extract (e.g., 'data-birth').
    mapping : dict, optional
        A dictionary to map parsed values (e.g., country codes to names).

    Returns
    -------
    str or None
        The parsed attribute value, or None if not found.
    """
    elem = soup.select_one(selector)
    if not elem:
        return None
    value = elem.get(attr) if attr else elem.text.strip()
    if mapping and value in mapping:
        value = mapping[value]
    return value if value else None

def _parse_table_dict(soup, table_selector, key_selector='th', value_selector='td', value_filter=lambda x: x.startswith('$')):
    """Parse a table into a dictionary.

    Parameters
    ----------
    soup : BeautifulSoup object
        The HTML data to parse.
    table_selector : str
        The CSS selector for the table.
    key_selector : str, optional
        The CSS selector for the keys (default is 'th').
    value_selector : str, optional
        The CSS selector for the values (default is 'td').
    value_filter : callable, optional
        A function to filter values (default filters for strings starting with '$').

    Returns
    -------
    dict or None
        A dictionary of key-value pairs, or None if not found.
    """
    table = soup.select_one(table_selector)
    if not table:
        return None
    keys = [elem.text.strip() for elem in table.select(key_selector) if elem.text.strip() != 'Team']
    values = [elem.text.strip() for elem in table.select(value_selector) if value_filter(elem.text.strip())]
    if len(keys) != len(values):
        return None
    return dict(zip(keys, values))

def _aggregate_table_data(soup, table_ids, season_parser, combine_func):
    """Aggregate data from multiple tables.

    Parameters
    ----------
    soup : BeautifulSoup object
        The HTML data to parse.
    table_ids : list
        List of table IDs to parse.
    season_parser : callable
        Function to parse the season from a row.
    combine_func : callable
        Function to combine row data into the result dictionary.

    Returns
    -------
    dict
        A dictionary of aggregated data, keyed by season.
    """
    result = {}
    most_recent_season = ''
    for table_id in table_ids:
        table_rows = _get_stats_table(soup, table_id)
        footer_rows = _get_stats_table(soup, table_id, footer=True)
        for row in table_rows:
            season = season_parser(row)
            result = combine_func(result, season, str(row))
            most_recent_season = season
        if footer_rows:
            result = combine_func(result, 'Career', str(footer_rows[0]))
    return result, most_recent_season

class AbstractGame:
    """Base class for game-related data.

    Parameters
    ----------
    boxscore_uri : str
        The URI for the game's boxscore.
    """
    def __init__(self, boxscore_uri):
        self._boxscore = boxscore_uri
        self._date = None
        self._location = None

    def __str__(self):
        """Return the string representation of the game.

        Returns
        -------
        str
            A string describing the game.
        """
        return f'Game on {self.date}'

    def __repr__(self):
        """Return the string representation of the game.

        Returns
        -------
        str
            A string describing the game.
        """
        return self.__str__()

    @property
    def boxscore_index(self):
        """Return the boxscore URI.

        Returns
        -------
        str
            The URI for the game's boxscore.
        """
        return self._boxscore

    @property
    def date(self):
        """Return the date of the game.

        Returns
        -------
        str or None
            The date the game took place.
        """
        return self._date

    @property
    def location(self):
        """Return the location of the game.

        Returns
        -------
        str or None
            The venue or location type (HOME/AWAY).
        """
        return self._location

def _parse_game_metadata(soup, scheme):
    """Parse game metadata (date, location, details).

    Parameters
    ----------
    soup : BeautifulSoup
        Parsed HTML of the boxscore page.
    scheme : dict
        Mapping of fields to CSS selectors.

    Returns
    -------
    dict
        Dictionary of parsed metadata.
    """
    metadata = {
        'date': None, 'time': None, 'attendance': None, 'duration': None, 'stadium': None,
        'won_toss': None, 'roof': None, 'surface': None, 'weather': None,
        'vegas_line': None, 'over_under': None
    }
    # Parse game info
    game_info = soup.select_one(scheme['game_info'])
    if game_info:
        info_lines = game_info.text.strip().split('\n')
        metadata['date'] = info_lines[0] if info_lines else None
        for line in info_lines:
            if 'Attendance' in line:
                metadata['attendance'] = line.replace('Attendance: ', '').replace(',', '')
            elif 'Time of Game' in line:
                metadata['duration'] = line.replace('Time of Game: ', '')
            elif 'Stadium' in line:
                metadata['stadium'] = line.replace('Stadium: ', '')
            elif 'Start Time' in line:
                metadata['time'] = line.replace('Start Time: ', '')

    # Parse game details
    details = soup.select(scheme['game_details'])
    for detail in details:
        detail_text = detail.text.lower()
        td_text = detail.select_one('td').text if detail.select_one('td') else ''
        if 'won toss' in detail_text:
            metadata['won_toss'] = td_text
        elif 'roof' in detail_text:
            metadata['roof'] = td_text.title()
        elif 'surface' in detail_text:
            metadata['surface'] = td_text.title()
        elif 'weather' in detail_text:
            metadata['weather'] = td_text
        elif 'vegas line' in detail_text:
            metadata['vegas_line'] = td_text
        elif 'over/under' in detail_text:
            metadata['over_under'] = td_text
    return metadata

def _parse_game_summary(soup, scheme):
    """Parse per-quarter game scores.

    Parameters
    ----------
    soup : BeautifulSoup
        Parsed HTML of the boxscore page.
    scheme : dict
        Mapping of fields to CSS selectors.

    Returns
    -------
    dict
        Dictionary with 'away' and 'home' keys mapping to lists of quarter scores.
    """
    summary = {'away': [], 'home': []}
    game_summary = soup.select_one(scheme['summary'])
    if game_summary:
        for ind, row in enumerate(game_summary.select('tbody tr')):
            team = 'away' if ind == 0 else 'home'
            for cell in row.select('td.center')[:-1]:
                if cell.select('div'):
                    continue
                try:
                    summary[team].append(int(cell.text))
                except ValueError:
                    summary[team].append(None)
    return summary

def _parse_player_data(soup, home_abbr, away_abbr):
    """Parse player statistics from boxscore tables.

    Parameters
    ----------
    soup : BeautifulSoup
        Parsed HTML of the boxscore page.
    home_abbr : str
        Home team abbreviation.
    away_abbr : str
        Away team abbreviation.

    Returns
    -------
    tuple
        Lists of away and home BoxscorePlayer instances.
    """
    player_dict = {}
    valid_tables = ['player_offense', 'player_defense', 'returns', 'kicking']
    for table in soup.select('table'):
        if table.get('id') not in valid_tables:
            continue
        for row in table.select('tbody tr'):
            player_id = row.select_one('th').get('data-append-csv') if row.select_one('th') else None
            if not player_id:
                continue
            name = row.select_one('a').text if row.select_one('a') else ''
            team_abbr = row.select_one('td[data-stat="team"]').text.upper() if row.select_one('td[data-stat="team"]') else ''
            team = 'home' if team_abbr == home_abbr.upper() else 'away'
            if player_id not in player_dict:
                player_dict[player_id] = {'name': name, 'data': '', 'team': team}
            player_dict[player_id]['data'] += str(row).strip()

    away_players = []
    home_players = []
    for player_id, details in player_dict.items():
        player = BoxscorePlayer(player_id, details['name'], details['data'])
        if details['team'] == 'home':
            home_players.append(player)
        else:
            away_players.append(player)
    return away_players, home_players

def _fetch_all_teams(year=None, season_page=None):
    """Fetch data for all NFL teams in a given year.

    Parameters
    ----------
    year : str, optional
        The 4-digit year of the season (e.g., '2023'). Defaults to the current or most recent season.
    season_page : str, optional
        Path to a local HTML file of the season page to parse instead of fetching online.

    Returns
    -------
    tuple
        A dictionary of team data (keyed by abbreviation) and the resolved year.
        Each team entry contains 'data' (BeautifulSoup row element) and 'rank' (int).
    """
    if not year:
        year = _get_default_year('nfl')

    team_data_dict = {}
    if season_page:
        with open(season_page, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'lxml')
    else:
        url = f'https://www.pro-football-reference.com/years/{year}/'
        soup = _fetch_html(url)
        if not soup:
            logging.warning(f"Failed to fetch team data for year {year}")
            return {}, year

    # Parse AFC and NFC tables
    for table_id in ['AFC', 'NFC']:
        table = soup.find('table', id=table_id)
        if not table:
            continue
        rows = table.select('tbody tr')
        for row in rows:
            # Skip header or empty rows
            if row.get('class') and 'thead' in row.get('class'):
                continue
            team_cell = row.find('th', {'data-stat': 'team'})
            if not team_cell or not team_cell.find('a'):
                continue
            # Extract abbreviation from team link
            team_link = team_cell.find('a')
            abbr = _parse_team_abbreviation(team_link)
            if not abbr:
                continue
            # Extract rank
            rank_cell = row.find('td', {'data-stat': 'rank_team'})
            rank = int(rank_cell.text) if rank_cell and rank_cell.text.isdigit() else None
            team_data_dict[abbr.upper()] = {'data': row, 'rank': rank}

    return team_data_dict, year
    
def nfl_int_property_decorator(func):
    """Decorator for NFL stats parsed from hyphen-separated fields.

    Parameters
    ----------
    func : callable
        The property method to decorate.

    Returns
    -------
    callable
        The decorated property method.
    """
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
            index_map = {
                'away_rush_attempts': 0, 'away_rush_yards': 1, 'away_rush_touchdowns': 2,
                'away_pass_completions': 0, 'away_pass_attempts': 1, 'away_pass_yards': 2,
                'away_pass_touchdowns': 3, 'away_interceptions': 4, 'away_times_sacked': 0,
                'away_yards_lost_from_sacks': 1, 'away_fumbles': 0, 'away_fumbles_lost': 1,
                'away_penalties': 0, 'away_yards_from_penalties': 1,
                'away_third_down_conversions': 0, 'away_third_down_attempts': 1,
                'away_fourth_down_conversions': 0, 'away_fourth_down_attempts': 1,
                'home_rush_attempts': 0, 'home_rush_yards': 1, 'home_rush_touchdowns': 2,
                'home_pass_completions': 0, 'home_pass_attempts': 1, 'home_pass_yards': 2,
                'home_pass_touchdowns': 3, 'home_interceptions': 4, 'home_times_sacked': 0,
                'home_yards_lost_from_sacks': 1, 'home_fumbles': 0, 'home_fumbles_lost': 1,
                'home_penalties': 0, 'home_yards_from_penalties': 1,
                'home_third_down_conversions': 0, 'home_third_down_attempts': 1,
                'home_fourth_down_conversions': 0, 'home_fourth_down_attempts': 1
            }
            return int(field_items[index_map[field]])
        except (TypeError, ValueError, IndexError, KeyError):
            return None
    return wrapper

def _clean_stat(value):
    """Clean a statistic value by removing unwanted characters.

    Parameters
    ----------
    value : str or None
        The raw statistic value to clean.

    Returns
    -------
    str
        The cleaned value, or empty string if input is None.
    """
    if value is None:
        return ''
    try:
        return value.replace('%', '').replace('$', '').replace(',', '').replace('+', '')
    except AttributeError:
        return ''

def _get_stats_table(soup, table_id, footer=False):
    """Extract a stats table from HTML.

    Parameters
    ----------
    soup : BeautifulSoup
        Parsed HTML content.
    table_id : str
        ID of the table to extract (e.g., 'passing').
    footer : bool, optional
        If True, extract the footer rows (e.g., career stats). Defaults to False.

    Returns
    -------
    list
        List of BeautifulSoup row elements.
    """
    table = soup.find('table', id=table_id)
    if not table:
        return []
    container = table.find('tfoot' if footer else 'tbody')
    if not container:
        return []
    return container.find_all('tr', recursive=False)

def _resolve_year(sport, base_year=None):
    """Resolve the year for a season, falling back to previous year if needed.

    Parameters
    ----------
    sport : str
        The sport identifier (e.g., 'nfl').
    base_year : str, optional
        The initial year to check. Defaults to current or most recent season.

    Returns
    -------
    str
        The resolved 4-digit year.
    """
    year = base_year or _get_default_year(sport)
    url_template = 'https://www.pro-football-reference.com/years/{}/'
    if not _url_exists(url_template.format(year)):
        prev_year = str(int(year) - 1)
        if _url_exists(url_template.format(prev_year)):
            return prev_year
    return year

def _url_exists(url):
    """Check if a URL exists.

    Parameters
    ----------
    url : str
        The URL to check.

    Returns
    -------
    bool
        True if the URL exists, False otherwise.
    """
    try:
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

def _parse_team_abbreviations(soup, scheme):
    """Parse team abbreviations from game stats.

    Parameters
    ----------
    soup : BeautifulSoup
        Parsed HTML of the boxscore page.
    scheme : dict
        Mapping of fields to CSS selectors.

    Returns
    -------
    tuple
        Away and home team abbreviations.
    """
    game_info = soup.select_one(scheme['team_stats'])
    abbreviations = [th.text for th in game_info.select('th') if th.text] if game_info else []
    return (abbreviations[0], abbreviations[1]) if len(abbreviations) >= 2 else (None, None)

def _parse_team_abbreviation(element):
    """Parse team abbreviation from HTML element.

    Parameters
    ----------
    element : BeautifulSoup element
        HTML element containing team link.

    Returns
    -------
    str
        Team abbreviation.
    """
    href = element.get('href', '')
    match = re.search(r'/teams/(\w+)/', href)
    return match.group(1) if match else ''
    
def _get_default_year(sport='nfl'):
    """Determine the default year for a given sport's season.

    Parameters
    ----------
    sport : str, optional
        The sport to determine the year for (default is 'nfl').

    Returns
    -------
    str
        The 4-digit year as a string for the current or most recent season.
    """
    current_year = datetime.now().year
    # NFL season typically starts in September, so if before September, use previous year
    if sport == 'nfl' and datetime.now().month < 9:
        return str(current_year - 1)
    return str(current_year)

def _url_exists(url):
    """Check if a URL is accessible.

    Parameters
    ----------
    url : str
        The URL to check.

    Returns
    -------
    bool
        True if the URL exists and is accessible, False otherwise.
    """
    try:
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

def _handle_no_data():
    """Log a warning when no data is found."""
    logging.warning("No data found for the requested resource.")

def _get_schedule_table(soup, table_id):
    """Extract schedule table rows from HTML.

    Parameters
    ----------
    soup : BeautifulSoup
        Parsed HTML of the page.
    table_id : str
        The ID of the schedule table (e.g., 'gamelog2023').

    Returns
    -------
    list
        List of BeautifulSoup row elements, or empty list if not found.
    """
    table = soup.find('table', id=table_id)
    if table:
        return table.select('tbody tr')
    return []

def _parse_boxscore_uri(row):
    """Parse boxscore URI from a schedule row.

    Parameters
    ----------
    row : BeautifulSoup element
        HTML row element containing game data.

    Returns
    -------
    str or None
        The boxscore URI (e.g., '202309100buf'), or None if not found.
    """
    boxscore_cell = row.find('td', attrs={'data-stat': 'boxscore_word'})
    if boxscore_cell and boxscore_cell.find('a'):
        href = boxscore_cell.find('a').get('href', '')
        match = re.search(r'/boxscores/(\w+)\.htm', href)
        return match.group(1) if match else None
    return None
    
class AbstractParser:
    """Base class for parsing HTML entities.

    Parameters
    ----------
    data : str
        The HTML data to parse.
    """
    def __init__(self, data):
        self._data = data
        self._soup = BeautifulSoup(data, 'html.parser') if data else None

    def _parse_field(self, scheme, field):
        """Parse a field from the entity's HTML data.

        Parameters
        ----------
        scheme : dict
            The scheme mapping field names to CSS selectors.
        field : str
            The field name to parse.

        Returns
        -------
        str or None
            The parsed field value, or None if not found.
        """
        return _parse_field(scheme, self._soup, field) if self._soup else None

from abc import ABC
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Tuple
from urllib.error import HTTPError
import pandas as pd
from bs4 import BeautifulSoup, Comment
import requests
from functools import wraps

class AbstractParser(ABC):
    """Abstract base class for parsing sports data."""
    def __init__(self):
        self._index: int = 0

    def dataframe(self) -> Optional[pd.DataFrame]:
        """Return a pandas DataFrame of relevant properties."""
        raise NotImplementedError

def int_property_decorator(func):
    """Decorator to convert a property to an integer."""
    @property
    @wraps(func)
    def wrapper(*args):
        instance = args[0]
        prop = func(*args)
        value = _clean_stat(prop[instance._index] if isinstance(prop, list) else prop)
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    return wrapper

def float_property_decorator(func):
    """Decorator to convert a property to a float."""
    @property
    @wraps(func)
    def wrapper(*args):
        instance = args[0]
        prop = func(*args)
        value = _clean_stat(prop[instance._index] if isinstance(prop, list) else prop)
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    return wrapper

def sub_index_property_decorator(index_dict: Dict[str, int]):
    """Decorator to parse a specific sub-index from a hyphen-separated string."""
    def decorator(func):
        @property
        @wraps(func)
        def wrapper(*args):
            instance = args[0]
            prop = func(*args)
            field = func.__name__
            value = _clean_stat(prop[instance._index] if isinstance(prop, list) else prop)
            if not value:
                return None
            try:
                items = value.replace('--', '-').split('-')
                index = index_dict.get(field, 0)
                return int(items[index])
            except (ValueError, IndexError, TypeError):
                return None
        return wrapper
    return decorator

def record_property_decorator(func):
    """Decorator to extract a specific record component (wins or losses)."""
    @property
    @wraps(func)
    def wrapper(*args):
        instance = args[0]
        prop = func(*args)
        field = func.__name__
        value = _clean_stat(prop)
        if not value:
            return None
        try:
            record = value.split('-')
            index = 0 if 'wins' in field.lower() else 1
            return int(record[index])
        except (ValueError, IndexError):
            return None
    return wrapper

def most_recent_decorator(func):
    """Decorator to extract the most recent season's value."""
    @property
    @wraps(func)
    def wrapper(*args):
        instance = args[0]
        season = instance._most_recent_season
        seasons = instance._season
        if not season or not seasons:
            return None
        try:
            index = seasons.index(season)
            prop = func(*args)
            value = prop[index] if isinstance(prop, list) else prop
            return _clean_stat(value)
        except (ValueError, IndexError):
            return None
    return wrapper

def _clean_stat(value: Any) -> str:
    """Clean a stat value by removing unwanted characters."""
    if value is None:
        return ''
    try:
        value = str(value).strip()
        value = value.replace('%', '').replace('$', '').replace(',', '').replace('+', '')
        return value
    except AttributeError:
        return ''

def _parse_field(scheme: Dict[str, str], soup: BeautifulSoup, field: str, index: int = 0) -> str:
    """Parse a field from HTML using a scheme."""
    if not soup or field not in scheme:
        return ''
    selector = scheme[field]
    try:
        elements = soup.select(selector)
        return elements[index].get_text(strip=True) if elements and len(elements) > index else ''
    except Exception:
        return ''

def _fetch_html(url: str) -> Optional[BeautifulSoup]:
    """Fetch and parse HTML content from a URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        return soup
    except (HTTPError, requests.RequestException):
        return None

def _get_stats_table(soup: BeautifulSoup, table_id: str) -> Optional[BeautifulSoup]:
    """Retrieve a specific stats table from HTML."""
    if not soup:
        return None
    table = soup.find('table', id=table_id)
    return table

def _resolve_year(year: Union[str, int]) -> str:
    """Resolve a year to a four-digit string."""
    year = str(year).strip()
    if len(year) == 2:
        year = f'20{year}' if int(year) <= 50 else f'19{year}'
    return year if year.isdigit() and len(year) == 4 else str(datetime.now().year)

def _parse_team_abbreviation(tag: BeautifulSoup) -> str:
    """Parse a team's abbreviation from an HTML tag."""
    if not tag or not tag.get('href'):
        return ''
    href = tag['href']
    match = re.search(r'/teams/([^/]+)/', href)
    return match.group(1) if match else ''

def _parse_inning_scores(row: BeautifulSoup) -> List[Optional[int]]:
    """Parse inning-by-inning scores from a table row."""
    scores = []
    for td in row.find_all('td', class_='center'):
        if td.find('div'):
            continue
        text = td.get_text(strip=True)
        try:
            scores.append(int(text))
        except ValueError:
            scores.append(None)
    return scores[:-3]  # Exclude runs, hits, errors

def _parse_game_info(soup: BeautifulSoup, selector: str) -> Dict[str, Optional[str]]:
    """Parse game meta information from HTML."""
    info = {
        'date': None,
        'time': None,
        'attendance': None,
        'venue': None,
        'duration': None,
        'time_of_day': None
    }
    element = soup.select_one(selector)
    if not element:
        return info
    lines = element.get_text().split('\n')
    if lines:
        info['date'] = lines[0].strip()
    for line in lines:
        line = line.strip()
        if 'Start Time:' in line:
            info['time'] = line.replace('Start Time:', '').strip()
        elif 'Attendance:' in line:
            info['attendance'] = line.replace('Attendance:', '').replace(',', '').strip()
        elif 'Venue:' in line:
            info['venue'] = line.replace('Venue:', '').strip()
        elif 'Game Duration:' in line:
            info['duration'] = line.replace('Game Duration:', '').strip()
        elif 'Night Game' in line or 'Day Game' in line:
            info['time_of_day'] = line.strip()
    return info

def _retrieve_team_data_dict(year: str, standings_url: str, league_url: str) -> Tuple[Dict, str]:
    """Retrieve all team data for a given year."""
    year = _resolve_year(year)
    team_data_dict = {}
    standings_soup = _fetch_html(standings_url % year)
    league_soup = _fetch_html(league_url % year)
    if not standings_soup or not league_soup:
        return team_data_dict, year
    standings_table = _get_stats_table(standings_soup, 'standings')
    league_table = _get_stats_table(league_soup, 'league')
    if not standings_table or not league_table:
        return team_data_dict, year
    for row in standings_table.find('tbody').find_all('tr'):
        th = row.find('th')
        if not th or not th.find('a'):
            continue
        team_link = th.find('a')
        abbr = _parse_team_abbreviation(team_link)
        if not abbr:
            continue
        rank = th.get('data-row')
        team_data_dict[abbr] = {'data': row, 'rank': rank}
    for row in league_table.find('tbody').find_all('tr'):
        th = row.find('th')
        if not th or not th.find('a'):
            continue
        team_link = th.find('a')
        abbr = _parse_team_abbreviation(team_link)
        if abbr in team_data_dict:
            team_data_dict[abbr]['data'] = str(team_data_dict[abbr]['data']) + str(row)
    return team_data_dict, year

def _parse_player_id(tag: BeautifulSoup) -> str:
    """Parse a player's ID from an HTML tag."""
    if not tag or not tag.get('href'):
        return ''
    href = tag['href']
    match = re.search(r'/players/./([^/]+)\.shtml', href)
    return match.group(1) if match else ''

def _parse_boxscore_uri(soup: BeautifulSoup) -> str:
    """Parse the boxscore URI from a schedule row."""
    if not soup:
        return ''
    boxscore = soup.find('td', {'data-stat': 'boxscore'})
    if not boxscore or not boxscore.find('a'):
        return ''
    href = boxscore.find('a').get('href', '')
    match = re.search(r'/boxes/([^.]+)\.shtml', href)
    return match.group(1) if match else ''