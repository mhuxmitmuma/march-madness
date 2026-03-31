import numpy as np
import pickle
import copy
import simpy
import pandas as pd
from xgboost import XGBClassifier
from scipy.stats import norm
from collections import Counter
from db import insert_sim_run, insert_sim_results

# Load in the prediction models
with open('models/model.pkl', 'rb') as f:
    model = pickle.load(f)

def win_probability(team_a, team_b):
    # Calculate the team differentials
    feature = pd.DataFrame([{
        'oe_diff': team_a['adj_oe'] - team_b['adj_oe'],
        'de_diff': team_a['adj_de'] - team_b['adj_de'],
        'sos_diff': team_a['sos'] - team_b['sos'],
        'win_rate_diff': team_a['win_rate'] - team_b['win_rate'],
        'srs_diff': team_a['srs'] - team_b['srs'],
        'tov_rate_diff': team_a['tov_rate'] - team_b['tov_rate'],
        'orb_rate_diff': team_a['orb_rate'] - team_b['orb_rate'],
        # 'ft_pct_diff': team_a['ft_pct'] - team_b['ft_pct'],
        'pos_per_game_diff': team_a['possessions_per_game'] - team_b['possessions_per_game'],
        # 'fga_per_game_diff': team_a['fga_per_game'] - team_b['fga_per_game'],
        'three_pa_per_game_diff': team_a['three_pa_per_game'] - team_b['three_pa_per_game'],
        'fta_per_game_diff': team_a['fta_per_game'] - team_b['fta_per_game'],
        'seed_diff': team_a['seed'] - team_b['seed']
    }])

    # Return win probability
    prob = model.predict_proba(feature)[0][1]
    return max(0.15, min(0.80, prob))

# Find the outcome of a single game
def simulate_game(team_a, team_b):
    # Find Team A's win probability and random number
    win_prob_a = win_probability(team_a, team_b)
    result = np.random.random()

    # Return winner
    if result <= win_prob_a:
        return team_a
    else:
        return team_b

def sos_adjust(team, avg_sos, factor=60):
    sos_diff = team['sos'] - avg_sos
    adjustment = 1 + (sos_diff / factor)
    adj_oe = team['adj_oe'] * adjustment
    adj_de = team['adj_de'] / adjustment
    return {**team, 'adj_oe': adj_oe, 'adj_de': adj_de}

# Simulate a game with discrete events
def simulate_game_simpy(team_a, team_b, avg_off, avg_def):
    env = simpy.Environment()
    score = {'a': 0, 'b': 0}
    team_a_adj = sos_adjust(team_a, (team_a['sos'] + team_b['sos']) / 2)
    team_b_adj = sos_adjust(team_b, (team_a['sos'] + team_b['sos']) / 2)

    def team_possessions(env, team, key, score, opp_def_eff, avg_def):
        possession_duration = 40 / team['possessions_per_game']
        
        # Calculate adjusted offensive stats
        base_scoring_prob = (avg_off / 100) / 2
        scoring_prob = base_scoring_prob * (team['adj_oe'] / avg_off) * (opp_def_eff / avg_def)
        three_point_rate = team['three_pa_per_game'] / team['fga_per_game']
        adj_tov = team['tov_rate'] * (avg_def / opp_def_eff)
        pts_per_scoring_possession = team['adj_oe'] / (scoring_prob * 100)
        
        while True:
            yield env.timeout(possession_duration)
            if np.random.random() < adj_tov:
                continue
            while True:
                if np.random.random() < scoring_prob:
                    score[key] += round(pts_per_scoring_possession)
                    break
                else:
                    if np.random.random() < team['orb_rate']:
                        continue
                    else:
                        break

    env.process(team_possessions(env, team_a_adj, 'a', score, team_b_adj['adj_de'], avg_def))
    env.process(team_possessions(env, team_b_adj, 'b', score, team_a_adj['adj_de'], avg_def))
    env.run(until=40)
    
    if score['a'] > score['b']:
        return team_a
    elif score['b'] > score['a']:
        return team_b
    else:
        # overtime — just pick randomly for now
        return team_a if np.random.random() < 0.5 else team_b

# Generate a regional bracket
def build_bracket(teams, region):
    # Find teams in given region
    regional_teams = copy.deepcopy([team for team in teams if team['region'] == region])

    # Count seeds and find duplicates
    seed_counts = Counter(team['seed'] for team in regional_teams)
    duplicate_seeds = [seed for seed, count in seed_counts.items() if count > 1]

    # Iterate through duplicate seeds
    for seed in duplicate_seeds:
        # Create a pair and replace both instances in regional teams
        pair = [team for team in regional_teams if isinstance(team, dict) and team['seed'] == seed]
        regional_teams = [team for team in regional_teams if not (isinstance(team, dict) and team['seed'] == seed)]
        regional_teams.append(pair)

    # Check for seeds vs pair
    def get_seed(item):
        # Return seed pair to the position of the winner
        if isinstance(item, list):
            return item[0]['seed']
        return item['seed']

    # Run a final sort based on seed/pair checks
    regional_teams = sorted(regional_teams, key=get_seed)
    return regional_teams

# Simulate a region
def simulate_region(bracket):
    bracket = bracket.copy()

    # Initialize wins tracker
    rounds_won = {}
    for item in bracket:
        if isinstance(item, dict):
            rounds_won[item['team_id']] = 0
        elif isinstance(item, list):
            for team in item:
                rounds_won[team['team_id']] = 0

    # Iterate through bracket
    for i, item in enumerate(bracket):
        # Simulate any first four match up
        if isinstance(item, list):
            bracket[i] = simulate_game(item[0], item[1])

    # Loop through the bracket
    while len(bracket) > 1:
        winners = []

        # Loop through the pairings in the bracket
        for i in range(len(bracket) // 2):
            # Simulate the game and append the winner
            winner = simulate_game(bracket[i], bracket[len(bracket) - (1 + i)])
            winners.append(winner)
            rounds_won[winner['team_id']] = rounds_won[winner['team_id']] + 1

        bracket = winners
    return bracket[0], rounds_won

# Simulate 4 regions, 2 semi-finals, and a championship
def simulate_tournament(teams):
    # Build and simulate all four regions
    east = build_bracket(teams, 'East')
    east_champ, east_rounds = simulate_region(east)
    
    west = build_bracket(teams, 'West')
    west_champ, west_rounds = simulate_region(west)
    
    south = build_bracket(teams, 'South')
    south_champ, south_rounds = simulate_region(south)

    midwest = build_bracket(teams, 'Midwest')
    midwest_champ, midwest_rounds = simulate_region(midwest)

    # Merge round win trackers
    all_rounds = {**east_rounds, **west_rounds, **south_rounds, **midwest_rounds}

    # Simulate semi-finals
    eastsouth = simulate_game(east_champ, south_champ)
    all_rounds[eastsouth['team_id']] = all_rounds[eastsouth['team_id']] + 1

    westmidwest = simulate_game(west_champ, midwest_champ)
    all_rounds[westmidwest['team_id']] = all_rounds[westmidwest['team_id']] + 1

    # Simulate championship game and return results
    champion = simulate_game(eastsouth, westmidwest)
    all_rounds[champion['team_id']] = all_rounds[champion['team_id']] + 1
    return all_rounds, champion['team_id']

# Run Monte Carlo simulations
def run_monte_carlo(teams, n_iterations, year):
    # Get current run ID and initialize results array
    sim_run_id = insert_sim_run(year, n_iterations, 'monte carlo')
    all_results = []

    # Run through iterations
    for i in range(n_iterations):
        # Simulate each tournament
        rounds_won, champion_id = simulate_tournament(teams)

        # Append results for each team for each simulation
        for team_id, wins in rounds_won.items():
            all_results.append({
                'team_id': team_id,
                'rounds_won': wins,
                'champion': team_id == champion_id
            })

    # Send results to database
    insert_sim_results(sim_run_id, all_results)
