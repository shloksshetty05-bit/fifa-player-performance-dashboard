import pandas as pd
import os

processed_dir = "data/processed"
df_players = pd.read_csv(os.path.join(processed_dir, "players.csv"))

check_names = ["Julio Cesar", "Dida", "Rogerio Ceni", "Jefferson", "Alisson", "Ederson", "Luciano"]

print("Checking Brazilian goalkeepers in players.csv:")
for name in check_names:
    matches = df_players[df_players['name'].str.contains(name, case=False, na=False)]
    if not matches.empty:
        print(f"[FOUND] {name}: player_id={matches['player_id'].iloc[0]}, position={matches['position'].iloc[0]}, birth={matches['date_of_birth'].iloc[0]}, citizenship={matches['country_of_citizenship'].iloc[0]}")
    else:
        print(f"[MISSING] {name}")
