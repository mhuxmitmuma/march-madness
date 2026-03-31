from db import get_games_with_stats
from settings import testing_years, training_years, all_years
import pandas as pd
import os
import pickle
import matplotlib.pyplot as plt
import seaborn as sns
from xgboost import XGBClassifier, plot_importance
from sklearn.model_selection import GridSearchCV, GroupKFold
from sklearn.calibration import CalibratedClassifierCV

refresh_cache = False
cache_path = os.path.join('data', 'training_cache.csv')

param_grid = {
    'n_estimators': [100, 200, 300, 400, 500],
    'max_depth': [2, 3, 4],
    'learning_rate': [0.01, 0.025, 0.05, 0.075, 0.1]
}

if os.path.exists(cache_path) and not refresh_cache:
    df = pd.read_csv(cache_path)
    print("Loaded from cache")
else:
    training_data = get_games_with_stats(testing_years)
    df = pd.DataFrame(training_data)
    df.to_csv(cache_path, index=False)
    print("Loaded from database and cached")

def load_features(df):
    features = pd.DataFrame()
    features['oe_diff'] = df['a_oe'] - df['b_oe']
    features['de_diff'] = df['a_de'] - df['b_de']
    features['sos_diff'] = df['a_sos'] - df['b_sos']
    features['win_rate_diff'] = df['a_win_rate'] - df['b_win_rate']
    features['srs_diff'] = df['a_srs'] - df['b_srs']
    features['tov_rate_diff'] = df['a_tov_rate'] - df['b_tov_rate']
    features['orb_rate_diff'] = df['a_orb_rate'] - df['b_orb_rate']
    # features['ft_pct_diff'] = df['a_ft_pct'] - df['b_ft_pct']
    features['pos_per_game_diff'] = df['a_pos_per_game'] - df['b_pos_per_game']
    # features['fga_per_game_diff'] = df['a_fga_per_game'] - df['b_fga_per_game']
    features['three_pa_per_game_diff'] = df['a_three_pa_per_game'] - df['b_three_pa_per_game']
    features['fta_per_game_diff'] = df['a_fta_per_game'] - df['b_fta_per_game']
    features['seed_diff'] = df['a_seed'] - df['b_seed']

    x = features
    y = df['team_a_won']
    return x, y

x, y = load_features(df)

sns.heatmap(x.corr(), annot=True, fmt='.2f')
plt.show()

model = XGBClassifier(
    subsample=0.8,
    colsample_bytree=0.8,
    eval_metric='logloss'
)

group_kfold = GroupKFold(n_splits=5)
groups = df['year']

grid_search = GridSearchCV(
    estimator=model,
    param_grid=param_grid,
    cv=group_kfold,
    scoring='neg_log_loss',
    verbose=1
)

grid_search.fit(x, y, groups=groups)

print("Best parameters:", grid_search.best_params_)
print("Best log loss:", -grid_search.best_score_)

best_model = grid_search.best_estimator_
calibrated_model = CalibratedClassifierCV(best_model, method='sigmoid')
calibrated_model.fit(x, y)
with open('models/model.pkl', 'wb') as f:
    pickle.dump(calibrated_model, f)

plot_importance(best_model)
plt.show()