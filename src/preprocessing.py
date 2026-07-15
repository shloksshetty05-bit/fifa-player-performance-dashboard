"""
Preprocessing Module
--------------------
Downloads, cleans, and filters the Transfermarkt dataset to isolate FIFA World Cup matches,
teams, players, and player appearances.
"""

import os
import requests
import pandas as pd
import numpy as np
import unicodedata
from datetime import datetime

# Data URLs (using the public R2 storage mirror of the transfermarkt-datasets project)
BASE_URL = "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data"
DATA_FILES = {
    "competitions.csv.gz": f"{BASE_URL}/competitions.csv.gz",
    "games.csv.gz": f"{BASE_URL}/games.csv.gz",
    "players.csv.gz": f"{BASE_URL}/players.csv.gz",
    "appearances.csv.gz": f"{BASE_URL}/appearances.csv.gz",
    "clubs.csv.gz": f"{BASE_URL}/clubs.csv.gz"
}

def remove_diacritics(text: str) -> str:
    """
    Removes accents and diacritics from a string (e.g., converts 'Luka Modrić' to 'Luka Modric').
    Uses python's standard unicodedata library to keep dependencies low.
    """
    if not isinstance(text, str):
        return text
    normalized = unicodedata.normalize('NFKD', text)
    return "".join(c for c in normalized if not unicodedata.combining(c))

def download_raw_data(raw_dir: str = "data/raw") -> None:
    """
    Downloads the compressed Transfermarkt CSV files if they do not already exist.
    """
    os.makedirs(raw_dir, exist_ok=True)
    print("--- Starting Data Download ---")
    
    for filename, url in DATA_FILES.items():
        filepath = os.path.join(raw_dir, filename)
        if os.path.exists(filepath):
            print(f"File already exists locally: {filename}. Skipping download.")
            continue
            
        print(f"Downloading {filename} from {url}...")
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f"Successfully downloaded {filename}.")
        except Exception as e:
            print(f"Error downloading {filename}: {e}")
            raise e
    print("--- Download Complete ---\n")

def process_world_cup_data(raw_dir: str = "data/raw", processed_dir: str = "data/processed") -> None:
    """
    Reads the downloaded raw data files, filters them for the FIFA World Cup (FIWC),
    cleans missing values, standardizes names, and saves the outputs.
    """
    os.makedirs(processed_dir, exist_ok=True)
    print("--- Processing and Cleaning Datasets ---")
    
    # 1. Load competitions to verify the code
    print("Loading competitions data...")
    df_competitions = pd.read_csv(os.path.join(raw_dir, "competitions.csv.gz"))
    
    wc_exists = df_competitions[df_competitions['competition_id'] == 'FIWC']
    if wc_exists.empty:
        print("Warning: competition_id 'FIWC' not found in competitions.csv!")
    else:
        print(f"Found competition: {wc_exists.iloc[0]['name']} (ID: FIWC)")

    # 2. Load and filter Games
    print("Loading games data...")
    df_games = pd.read_csv(os.path.join(raw_dir, "games.csv.gz"))
    df_wc_games = df_games[df_games['competition_id'] == 'FIWC'].copy()
    print(f"Filtered {len(df_wc_games)} World Cup matches.")
    
    if len(df_wc_games) == 0:
        raise ValueError("No games found for competition_id 'FIWC'. Preprocessing aborted.")
        
    # Clean games
    # Fill missing attendance with the median attendance for that season
    df_wc_games['attendance'] = df_wc_games.groupby('season')['attendance'].transform(
        lambda x: x.fillna(x.median() if not x.isna().all() else 30000)
    )
    df_wc_games['referee'] = df_wc_games['referee'].fillna("Unknown Referee")
    
    # Standardize home/away club names
    df_wc_games['home_club_name'] = df_wc_games['home_club_name'].apply(remove_diacritics).str.strip()
    df_wc_games['away_club_name'] = df_wc_games['away_club_name'].apply(remove_diacritics).str.strip()

    # 3. Load and filter Appearances
    print("Loading appearances data...")
    wc_game_ids = set(df_wc_games['game_id'].unique())
    df_app = pd.read_csv(os.path.join(raw_dir, "appearances.csv.gz"))
    df_wc_app = df_app[df_app['game_id'].isin(wc_game_ids)].copy()
    print(f"Filtered {len(df_wc_app)} player appearances in World Cup matches.")
    
    # Standardize player names in appearances
    df_wc_app['player_name'] = df_wc_app['player_name'].apply(remove_diacritics).str.strip()
    
    # Handle missing performance metrics
    metrics = ['goals', 'assists', 'yellow_cards', 'red_cards', 'minutes_played']
    for metric in metrics:
        df_wc_app[metric] = df_wc_app[metric].fillna(0).astype(int)

    # 4. Load and filter Players
    print("Loading players data...")
    df_players = pd.read_csv(os.path.join(raw_dir, "players.csv.gz"))
    wc_player_ids = set(df_wc_app['player_id'].unique())
    df_wc_players = df_players[df_players['player_id'].isin(wc_player_ids)].copy()
    print(f"Filtered {len(df_wc_players)} players who participated in the World Cups.")
    
    # Clean player details
    df_wc_players['name'] = df_wc_players['name'].apply(remove_diacritics).str.strip()
    df_wc_players['first_name'] = df_wc_players['first_name'].apply(remove_diacritics).str.strip()
    df_wc_players['last_name'] = df_wc_players['last_name'].apply(remove_diacritics).str.strip()
    df_wc_players['country_of_citizenship'] = df_wc_players['country_of_citizenship'].apply(remove_diacritics).str.strip()
    
    # Fill missing heights
    df_wc_players['height_in_cm'] = df_wc_players.groupby('position')['height_in_cm'].transform(
        lambda x: x.fillna(x.median() if not x.isna().all() else 180)
    )
    
    # Standardize and impute market value
    df_wc_players['market_value_in_eur'] = df_wc_players.groupby('position')['market_value_in_eur'].transform(
        lambda x: x.fillna(x.median() if not x.isna().all() else 1000000)
    )
    df_wc_players['highest_market_value_in_eur'] = df_wc_players['highest_market_value_in_eur'].fillna(df_wc_players['market_value_in_eur'])

    # 5. Synthesize Clubs/Teams data (since national teams are not in raw clubs.csv)
    print("Synthesizing national team profiles...")
    
    # Map club_id to name from games
    home_teams = df_wc_games[['home_club_id', 'home_club_name']].rename(columns={'home_club_id': 'club_id', 'home_club_name': 'name'})
    away_teams = df_wc_games[['away_club_id', 'away_club_name']].rename(columns={'away_club_id': 'club_id', 'away_club_name': 'name'})
    teams_map = pd.concat([home_teams, away_teams]).drop_duplicates(subset=['club_id']).dropna()
    
    # Map player to national team using appearances
    player_to_team = df_wc_app[['player_id', 'player_club_id']].drop_duplicates(subset=['player_id'])
    player_team_dict = dict(zip(player_to_team['player_id'], player_to_team['player_club_id']))
    
    # Add national team ID to players
    df_wc_players['national_team_id'] = df_wc_players['player_id'].map(player_team_dict)
    
    # Calculate age for players to aggregate
    current_year = datetime.now().year
    df_wc_players['year_of_birth'] = pd.to_datetime(df_wc_players['date_of_birth'], errors='coerce').dt.year
    df_wc_players['age'] = current_year - df_wc_players['year_of_birth']
    df_wc_players['age'] = df_wc_players['age'].fillna(df_wc_players['age'].median() if not df_wc_players['age'].isna().all() else 27)
    
    # Calculate team aggregates
    team_stats = df_wc_players.groupby('national_team_id').agg(
        squad_size=('player_id', 'nunique'),
        average_age=('age', 'mean'),
        total_market_value=('market_value_in_eur', 'sum')
    ).reset_index().rename(columns={'national_team_id': 'club_id'})
    
    # Merge names and stats
    df_wc_clubs = teams_map.merge(team_stats, on='club_id', how='left')
    df_wc_clubs['squad_size'] = df_wc_clubs['squad_size'].fillna(0).astype(int)
    df_wc_clubs['average_age'] = df_wc_clubs['average_age'].fillna(27.0).round(1)
    df_wc_clubs['total_market_value'] = df_wc_clubs['total_market_value'].fillna(0)
    
    print(f"Synthesized {len(df_wc_clubs)} national team profiles.")

    # 6. Save processed datasets
    print("Saving processed datasets to data/processed/...")
    df_wc_games.to_csv(os.path.join(processed_dir, "games.csv"), index=False)
    df_wc_app.to_csv(os.path.join(processed_dir, "appearances.csv"), index=False)
    df_wc_players.to_csv(os.path.join(processed_dir, "players.csv"), index=False)
    df_wc_clubs.to_csv(os.path.join(processed_dir, "clubs.csv"), index=False)
    
    print("--- Preprocessing & Filtering Completed Successfully! ---")

if __name__ == "__main__":
    download_raw_data()
    process_world_cup_data()
