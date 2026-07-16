import pandas as pd
import os

processed_dir = "data/processed"
df_players = pd.read_csv(os.path.join(processed_dir, "players.csv"))
df_app = pd.read_csv(os.path.join(processed_dir, "appearances.csv"))

print("--- Unique positions in players.csv ---")
print(df_players['position'].unique())
print(df_players['position'].value_counts())

df_app_pos = df_app.merge(df_players[['player_id', 'position']], on='player_id', how='left')
print("\n--- Unique positions in merged appearances ---")
print(df_app_pos['position'].unique())
print(df_app_pos['position'].value_counts(dropna=False))
