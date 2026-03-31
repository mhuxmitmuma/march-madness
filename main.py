from db import (
    init_database,  truncate_tables,
    insert_teams, update_region, insert_game, delete_year,
    get_teams, get_team_id, get_db_connection
)
from api import get_seeds, get_school_stats, get_team_regions, get_game_results, normalize_name
from simulator import simulate_tournament, simulate_game
import pandas as pd
from collections import Counter
import time
from settings import testing_years, training_years, all_years


# Load in all team and game data
def load_all_data(years=training_years):
    # Reset tables
    truncate_tables()

    # Loop through all given years
    for year in years:
        time.sleep(2)

        # Load in seed/stat data
        seeds = get_seeds(year)
        stats = get_school_stats(year)

        # Normalize names
        seeds['TeamName'] = seeds['TeamName'].apply(normalize_name)
        stats['School'] = stats['School'].apply(normalize_name)

        # Merge team tables
        merged = pd.merge(seeds, stats, left_on='TeamName', right_on='School')
        merged = merged.drop(columns=['School'])
        merged = merged.rename(columns={'TeamName': 'team_name', 'Seed': 'seed'})
        merged['year'] = year

        # Check # of teams, should be 68 per year
        print(f"Inserting {len(merged)} rows for {year}")
        insert_teams(merged)

        # Update regions
        for team_name, region in get_team_regions(year):
            name = normalize_name(team_name)
            update_region(name, region, year)

        # Pull in game results
        games = get_game_results(year)

        # Loop through each game
        for game in games:
            # Find actual team IDs
            team_a_id = get_team_id(game['team_a'], year)
            team_b_id = get_team_id(game['team_b'], year)
            winner_id = get_team_id(game['winner'], year)

            # Check for none
            if team_a_id is None or team_b_id is None or winner_id is None:
                print(f"[SKIP] No match found for '{game}' in {year}")
                continue
                # Insert each game from year
            insert_game(game['year'], game['round_name'], team_a_id, team_b_id, winner_id)

# Load in year by year game data
def load_year(year):
    # Check if year already exists
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM teams WHERE year = %s", (year,))
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    
    #if count > 0:
    #    print(f"Year {year} already loaded, skipping")
    #    return
    
    # Delete current year
    delete_year(year)

    # Load in seed/stat data
    seeds = get_seeds(year)
    stats = get_school_stats(year)

    # Normalize names
    seeds['TeamName'] = seeds['TeamName'].apply(normalize_name)
    stats['School'] = stats['School'].apply(normalize_name)

    # Merge team tables
    merged = pd.merge(seeds, stats, left_on='TeamName', right_on='School')
    merged = merged.drop(columns=['School'])
    merged = merged.rename(columns={'TeamName': 'team_name', 'Seed': 'seed'})
    merged['year'] = year

    # Check # of teams, should be 68 per year
    print(f"Inserting {len(merged)} rows for {year}")
    insert_teams(merged)

    # Update regions
    for team_name, region in get_team_regions(year):
        name = normalize_name(team_name)
        update_region(name, region, year)

    # Pull in game results
    games = get_game_results(year)

    # Loop through each game
    for game in games:
        # Find actual team IDs
        team_a_id = get_team_id(game['team_a'], year)
        team_b_id = get_team_id(game['team_b'], year)
        winner_id = get_team_id(game['winner'], year)

        # Check for none
        if team_a_id is None or team_b_id is None or winner_id is None:
            print(f"[SKIP] No match found for '{game}' in {year}")
            continue
            # Insert each game from year
        insert_game(game['year'], game['round_name'], team_a_id, team_b_id, winner_id)

# 499 laps later...
def run_simulations(year, n):
    teams = get_teams(year)

    win_counts_total = Counter()
    final_four_total = Counter()
    champ_counts = Counter()

    for i in range(n):
        print(f"Running simulation #{i}")
        win_counts, champ_id = simulate_tournament(teams)
        for team_id, wins in win_counts.items():
            if wins >= 4:
                win_counts_total[team_id] += 1
            if wins >= 5:
                final_four_total[team_id] += 1
        champ_counts[champ_id] += 1

    team_lookup = {t['team_id']: t['name'] for t in teams}

    print("SimPy Top 10 (4+ wins):")
    for team_id, count in win_counts_total.most_common(20):
        name = team_lookup.get(team_id, f"Unknown ({team_id})")
        final_four_pct = final_four_total.get(team_id, 0) / 100
        champ_pct = champ_counts.get(team_id, 0) / 100
        print(f"  {name}: {count/100:.1f}% in final 4 - {final_four_pct:.1f}% in championship game - {champ_pct:.1f}% champions")

if __name__ == '__main__':
    test = 0

    # Initial new database once (for new computers)
    # init_database()

    # Load in data to existing database from scratch
    # load_all_data()
    # load_year(2026)

    # run_simulations(2022, 1000)
