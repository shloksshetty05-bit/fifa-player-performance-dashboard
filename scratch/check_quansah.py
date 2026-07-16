import pandas as pd
import os
import sqlite3

raw_dir = "data/raw"
processed_dir = "data/processed"

df_games = pd.read_csv(os.path.join(raw_dir, "games.csv.gz"))
df_wc_games = df_games[df_games['competition_id'] == 'FIWC'].copy()
wc_game_ids = set(df_wc_games['game_id'].unique())

df_app = pd.read_csv(os.path.join(raw_dir, "appearances.csv.gz"))
df_wc_app = df_app[df_app['game_id'].isin(wc_game_ids)].copy()

df_players = pd.read_csv(os.path.join(raw_dir, "players.csv.gz"))

# Let's inspect Jarell Quansah
quansah = df_players[df_players['name'].str.contains("Quansah", case=False, na=False)]
print("Quansah players info:")
print(quansah[['player_id', 'name', 'country_of_citizenship']])

if not quansah.empty:
    qid = quansah['player_id'].iloc[0]
    # Check if he has raw appearances in df_wc_app
    q_apps = df_wc_app[df_wc_app['player_id'] == qid]
    print(f"\nRaw appearances for player {qid} in World Cup games:")
    print(q_apps)
    
    # Check what games those are
    if not q_apps.empty:
        gids = q_apps['game_id'].unique()
        print("\nGames info:")
        print(df_wc_games[df_wc_games['game_id'].isin(gids)][['game_id', 'season', 'home_club_name', 'away_club_name']])

conn = sqlite3.connect("database/fifa_worldcup.db")
print("\nIs Jarell Quansah in the SQLite players table?")
res = pd.read_sql_query("SELECT player_id, name, is_verified FROM players WHERE name LIKE '%Quansah%'", conn)
print(res)
conn.close()
