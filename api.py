# Import libraries
import requests
import pandas as pd
from io import StringIO
from bs4 import BeautifulSoup
import time
import re

# Get tournament data from ESPN API
def get_tournament_data(year):
    # Pull correct data by year
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?groups=100&limit=200&dates={year}0301-{year}0410"

    # Access ESPN API and return data
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()

    data = response.json()
    return data

# Get region data separately
def get_team_regions(year):
    # Pull tournament data in
    data = get_tournament_data(year)
    results = []

    for event in data['events']:
        competition = event['competitions'][0]

        # Filter for first round games
        if '1st Round' in competition['notes'][0]['headline'] or 'First Four' in competition['notes'][0]['headline']:
            # Find each game's region
            region = competition['notes'][0]['headline'].split(' Region')[0].split('- ')[-1]
            
            # Iterate through both teams in each game
            for team in competition['competitors']:
                # Grab correct name format and return name and region
                team_name = team['team']['shortDisplayName']
                results.append((team_name, region))

    # Return fill list of teams and regions
    return results

# Get a game's results from a tournament
def get_game_results(year):
    # Pull tournament data in
    data = get_tournament_data(year)
    results = []
    
    for event in data['events']:
        competition = event['competitions'][0]
        teams = []

        if competition['status']['type']['completed']:
            # Return the headline containing the round
            round_name = competition['notes'][0]['headline']

            # Iterate through both teams in each game
            for team in competition['competitors']:
                # Grab correct name format and return name and region
                teams.append(normalize_name(team['team']['shortDisplayName']))

                # Check which team is the winner
                if team['winner']:
                    winner = normalize_name(team['team']['shortDisplayName'])

            # Track each team and append all data              
            team_a = teams[0]
            team_b = teams[1]
            results.append({
                'year': year,
                'round_name': round_name,
                'team_a': team_a,
                'team_b': team_b,
                'winner': winner
            }) 
    
    # Return fill list of teams and regions
    return results

# Get seed data from Kaggle CSV files
def get_seeds(year):
    # Read CSV files from Kaggle
    seeds = pd.read_csv('data/MNCAATourneySeeds.csv')
    teams = pd.read_csv('data/MTeams.csv')
    seeds = seeds[seeds['Season'] == year]

    # Merge on team ID
    df = pd.merge(teams, seeds, on='TeamID')
    df = df[['TeamName', 'Seed']]

    # Convert seeds to numbers
    df['Seed'] = df['Seed'].str[1:3]
    df['Seed'] = df['Seed'].astype(int)
    return df

# Get school statistics from Sports Reference
def get_school_stats(year):
    # Pull correct data by year
    url = f"https://www.sports-reference.com/cbb/seasons/men/{year}-school-stats.html"

    # Access SR API with time delay
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    time.sleep(3)

    # Convert scraped HTML data from correct div
    data = BeautifulSoup(response.text, 'lxml')
    table = data.find('table', {'id': 'basic_school_stats'})
    df = pd.read_html(StringIO(str(table)))[0]

    # Flatten columns and clean rows
    df.columns = df.columns.get_level_values(1)
    df = df[df['Rk'].notna()]
    df = df[df['Rk'] != 'Rk']

    # Remove non-tournament teams and remove extra string
    df = df[df['School'].str.contains('NCAA')]
    df['School'] = df['School'].str.replace('\xa0NCAA', '', regex=False)

    # Remove unnecessary columns
    df = df[['School', 'G', 'W-L%', 'SRS', 'SOS', 'Tm.', 'Opp.', 'FGA', 'ORB', 'TOV', 'FTA', 'FT%', '3PA']]

    # Convert scraped strings to numbers
    cols = ['G', 'W-L%', 'SRS', 'SOS', 'Tm.', 'Opp.', 'FGA', 'ORB', 'TOV', 'FTA', 'FT%', '3PA']
    df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
    
    # Create new columns for calculated stats
    df['possessions'] = df['FGA'] - df['ORB'] + df['TOV'] + (0.44 * df['FTA'])
    df['off_eff'] = df['Tm.'] / df['possessions'] * 100
    df['def_eff'] = df['Opp.'] / df['possessions'] * 100
    df['pos_per_game'] = df['possessions'] / df['G']
    df['tov_rate'] = df['TOV'] / df['possessions']
    df['orb_rate'] = df['ORB'] / df['possessions']
    df['fga_per_game'] = df['FGA'] / df['G']
    df['three_pa_per_game'] = df['3PA'] / df['G']
    df['fta_per_game'] = df['FTA'] / df['G']

    # Final trim to necessary columns and return
    df = df.rename(columns={'FT%': 'ft_pct', 'W-L%': 'win_rate'})
    df = df[['School', 'win_rate', 'SRS', 'SOS', 'off_eff', 'def_eff', 'pos_per_game', 'tov_rate', 'orb_rate', 'ft_pct', 'fga_per_game', 'three_pa_per_game', 'fta_per_game']]
    return df

# Normalize team names
def normalize_name(name):
    # Prepare the string
    name = name.lower()
    name = name.strip()

    # Unique names map
    manual_map = {
        'brigham young': 'byu',
        'western kentucky': 'wku',
        'w kentucky': 'wku',
        'f dickinson': 'fdu',
        'virginia commonwealth': 'vcu',
        'alabama birmingham': 'uab',
        'northern kentucky': 'n kentucky',
        'kent': 'kent st',
        'southeast missouri state': 'se missouri',
        'se missouri st': 'se missouri',
        'se missouri state': 'se missouri',
        'tam c. christi': 'texas a&m-cc',
        'texas a&m-corpus christi': 'texas a&m-cc',
        'miami fl': 'miami',
        'miami (fl)': 'miami',
        'southern california': 'usc',
        'kennesaw': 'kennesaw st',
        'cal state fullerton': 'fullerton',
        'cs fullerton': 'fullerton',
        'louisiana state': 'lsu',
        'loyola (il)': 'loyola chicago',
        'loyola-chicago': 'loyola chicago',
        'fl atlantic': 'fau',
        'florida atlantic': 'fau',
        'connecticut': 'uconn',
        'western ky': 'wku',
        'pittsburgh': 'pitt',
        'mcneese st': 'mcneese',
        'mcneese state': 'mcneese',
        'uc santa barbara': 'santa barbara',
        'jacksonville state': 'jax st',
        'jacksonville st': 'jax st',
        'abilene christian': 'abilene chrstn',
        'abilene chr': 'abilene chrstn',
        'ewu': 'e washington',
        'eastern washington': 'e washington',
        'appalachian st': 'app st',
        'appalachian state': 'app st',
        'mount st. mary\'s': 'mount st marys',
        'mt st mary\'s': 'mount st marys',
        'saint john\'s': 'saint johns',
        'st. john\'s (ny)': 'saint johns',
        'st. johns\'': 'saint johns',
        'saint joseph\'s': 'saint josephs',
        'florida gulf coast': 'fgcu',
        'north carolina central': 'nc central',
        'louisiana state': 'lsu',
        'middle tennessee': 'mtsu',
        'stephen f. austin': 'sf austin',
        'north dakota state': 'n dakota st',
        'mississippi': 'ole miss',
        'gardner webb': 'gardner-webb',
        'suny albany': 'ualbany',
        'east tennessee state': 'etsu',
        'southern methodist': 'smu',
        'southern univ': 'southern',
        'ark little rock': 'little rock',
        'hawaii': 'hawai\'i',
        'cs bakersfield': 'bakersfield',
        'cal state bakersfield': 'bakersfield',
        'wi green bay': 'green bay',
        'american univ': 'american',
        'western michigan': 'w michigan',
        'wi milwaukee': 'milwaukee',
        'eastern kentucky': 'e kentucky',
        'massachusetts': 'umass',
        'coastal car': 'coastal',
        'coastal carolina': 'coastal',
        'albany (ny)': 'ualbany',
        'st. bonaventure': 'saint bonaventure',
        'george washington': 'g washington',
        'north carolina a&t': 'nc a&t',
        'liu brooklyn': 'long island',
        'long island university': 'long island',
        'nevada-las vegas': 'unlv',
        'northwestern la': 'n\'western st',
        'northwestern state': 'n\'western st',
        'cs northridge': 'csu northridge',
        'cal state northridge': 'csu northridge',
        'ark pine bluff': 'ar-pine bluff',
        'arkansas-pine bluff': 'ar-pine bluff',
        'sam houston st': 'sam houston',
        'boston university': 'boston u',
        'boston univ': 'boston u',
        'ut san antonio': 'utsa',
        'northern colorado': 'n colorado',
        'saint josephs\'': 'saint josephs',
        'st joseph\'s pa': 'saint josephs',
        'maryland-baltimore county': 'umbc',
        'pennsylvania': 'penn',
        'ms valley st': 'miss valley st',
        'mississippi valley state': 'miss valley st',
        'loyola (md)': 'loyola md',
        'southern mississippi': 'southern miss',
        'detroit': 'detroit mercy',
        'siu edwardsville': 'siue',
        'st francis pa': 'saint francis',
        'saint francis (pa)': 'saint francis',
        'ne omaha': 'omaha',
        'prairie view a&m': 'prairie view',
        'miami (oh)': 'miami oh',
        'queens nc': 'queens',
        'queens (nc)': 'queens',
        'texas christian': 'tcu',
        'california baptist': 'c bapt',
        'cal baptist': 'c bapt',
        'ca baptist': 'c bapt'
    }

    # Check for unique names and replace
    if name in manual_map:
        return manual_map[name]

    # Common normalizations
    name = name.replace('college of ', '')
    name = name.replace('col ', '')
    name = name.replace('fl ', 'florida ')
    name = name.replace('tx ', 'texas ')
    name = name.replace(' (ca)', '')
    name = name.replace('', '')
    name = name.replace('south d', 's d')
    name = name.replace(' state', ' st')
    name = name.replace('st.', ' st')
    name = name.replace('john\'s', 'johns')
    name = name.replace('johns\'', 'johns')
    name = re.sub(r'^\bst\b', 'saint', name)
    name = re.sub(r'\bstate\b', 'st', name)
    name = re.sub(r'\bca\b', '', name)

    return name.strip()
