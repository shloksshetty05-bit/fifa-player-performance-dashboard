import pandas as pd
import os

raw_dir = "data/raw"
df_games = pd.read_csv(os.path.join(raw_dir, "games.csv.gz"))
df_wc_games = df_games[df_games['competition_id'] == 'FIWC'].copy()
wc_game_ids = set(df_wc_games['game_id'].unique())

df_app = pd.read_csv(os.path.join(raw_dir, "appearances.csv.gz"))
df_wc_app = df_app[df_app['game_id'].isin(wc_game_ids)].copy()

q_apps = df_wc_app[df_wc_app['player_id'] == 632349]
print("Jarell Quansah (632349) raw appearances in World Cup matches:")
print(q_apps)

if not q_apps.empty:
    gids = q_apps['game_id'].unique()
    print("\nGames info:")
    print(df_wc_games[df_wc_games['game_id'].isin(gids)][['game_id', 'season', 'home_club_name', 'away_club_name']])
else:
    print("No raw appearances found!")
