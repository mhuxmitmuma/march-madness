from db import get_teams
from simulator import win_probability, build_bracket, simulate_tournament
import numpy as np
import pandas as pd
from collections import defaultdict

def tournament_challenge(year, n):
    teams = get_teams(year)
    advance_counts = defaultdict(lambda: defaultdict(int))

    regions = {
        'east': build_bracket(teams, 'East'),
        'west': build_bracket(teams, 'West'),
        'midwest': build_bracket(teams, 'Midwest'),
        'south': build_bracket(teams, 'South')
    }
    
    for i in range(n):
        if i % 50 == 0:
            print(f"Running simulation #{i}...")
        win_counts, champ_id = simulate_tournament(teams)

        for team_id, wins in win_counts.items():
            for round_num in range(1, wins + 1):
                advance_counts[team_id][round_num] += 1

    for region_name, bracket in regions.items():
        resolved = []
        for item in bracket:
            if isinstance(item, list):
                resolved.append(item[0] if win_probability(item[0], item[1]) >= 0.5 else item[1])
            else:
                resolved.append(item)

        print(f"\n=== {region_name.upper()} ===")

        for i in range(len(resolved) // 2):
            team_a = resolved[i]
            team_b = resolved[len(resolved) - 1 - i]
            
            prob_a = win_probability(team_a, team_b)
            prob_b = 1 - prob_a
            print(f"{team_a['seed']} {team_a['name']} ({prob_a:.0%}) vs {team_b['seed']} {team_b['name']} ({prob_b:.0%})")

            print(team_a['name'])
            for round_num in range(1, 7):
                pct = advance_counts[team_a['team_id']][round_num] / n * 100
                print(f"{pct:.2f}%", end=" ")
            print()

            print(team_b['name'])
            for round_num in range(1, 7):
                pct = advance_counts[team_b['team_id']][round_num] / n * 100
                print(f"{pct:.2f}%", end=" ")
            print()

tournament_challenge(2026, 10)