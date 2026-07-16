import pandas as pd
import os

processed_dir = "data/processed"
df_players = pd.read_csv(os.path.join(processed_dir, "players.csv"))

check_names = [
    "Zinedine Zidane", "Thierry Henry", "Fabien Barthez", "Gregory Coupet", 
    "Hugo Lloris", "Miroslav Klose", "David Villa", "Romuald Peiser", 
    "Steve Mandanda", "Mickael Landreau"
]

print("Checking presence in players.csv:")
for name in check_names:
    matches = df_players[df_players['name'].str.contains(name, case=False, na=False)]
    if not matches.empty:
        print(f"[FOUND] {name}: player_id={matches['player_id'].iloc[0]}, position={matches['position'].iloc[0]}, birth={matches['date_of_birth'].iloc[0]}, market_value={matches['market_value_in_eur'].iloc[0]}")
    else:
        print(f"[MISSING] {name}")
