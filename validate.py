from main import load_year
from settings import testing_years, training_years, all_years
from db import get_games_with_stats
from simulator import win_probability
from xgboost import XGBClassifier
from sklearn.metrics import log_loss

def validate_model(testing_years):
    for year in testing_years:
        load_year(year)
        games = get_games_with_stats(year=year)
        round_data = {}

        for game in games:
            # Get a clean round name and num per game
            round_name = game['round'].lower().split(' - ')[-1]
            round_name = ' '.join(round_name.split()[:2])
            
            # Add round list if not exists
            if round_name not in round_data:
                round_data[round_name] = {
                    'predictions': [],
                    'results': []
                }

            # Populate team data
            team_a = {
                'adj_oe': game['a_oe'],
                'adj_de': game['a_de'],
                'sos': game['a_sos'],
                'win_rate': game['a_win_rate'],
                'srs': game['a_srs'],
                'tov_rate': game['a_tov_rate'],
                'orb_rate': game['a_orb_rate'],
                # 'ft_pct': game['a_ft_pct'],
                'possessions_per_game': game['a_pos_per_game'],
                # 'fga_per_game': game['a_fga_per_game'],
                'three_pa_per_game': game['a_three_pa_per_game'],
                'fta_per_game': game['a_fta_per_game'],
                'seed': game['a_seed']
            }
            team_b = {
                'adj_oe': game['b_oe'],
                'adj_de': game['b_de'],
                'sos': game['b_sos'],
                'win_rate': game['b_win_rate'],
                'srs': game['b_srs'],
                'tov_rate': game['b_tov_rate'],
                'orb_rate': game['b_orb_rate'],
                # 'ft_pct': game['b_ft_pct'],
                'possessions_per_game': game['b_pos_per_game'],
                # 'fga_per_game': game['b_fga_per_game'],
                'three_pa_per_game': game['b_three_pa_per_game'],
                'fta_per_game': game['b_fta_per_game'],
                'seed': game['b_seed']
            }

            for key, val in team_a.items():
                if val is None:
                    print(f"[NaN] team_a missing {key} in game {game['game_id']}")
            for key, val in team_b.items():
                if val is None:
                    print(f"[NaN] team_b missing {key} in game {game['game_id']}")
            
            round_data[round_name]['predictions'].append(win_probability(team_a, team_b))
            round_data[round_name]['results'].append(game['team_a_won'])

        for round_name, data in round_data.items():
            ll = log_loss(data['results'], data['predictions'], labels=[0, 1])
            correct = sum(1 for p, r in zip(data['predictions'], data['results']) if (p > 0.5) == r)
            accuracy = correct / len(data['results'])
            print(f"  {round_name} - Log Loss: {ll:.4f} | Accuracy: {accuracy:.1%}")

        all_predictions = [p for d in round_data.values() for p in d['predictions']]
        all_results = [r for d in round_data.values() for r in d['results']]

        ll = log_loss(all_results, all_predictions, labels=[0, 1])
        correct = sum(1 for p, r in zip(all_predictions, all_results) if (p > 0.5) == r)
        accuracy = correct / len(all_results)
        print(f"\n{year} - Log Loss: {ll:.4f} | Accuracy: {accuracy:.1%}")

validate_model(testing_years)