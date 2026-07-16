"""
Feature Engineering Module
--------------------------
Calculates standard football performance metrics, simulates missing match events
(tackles, passes, saves) deterministically, and computes attacking/defensive contribution
scores, match ratings, and a custom performance index.
"""

import os
import zlib
import pandas as pd
import numpy as np

def get_seeded_generator(player_id: int, game_id: int) -> np.random.Generator:
    """
    Returns a deterministic NumPy random generator based on a CRC32 hash of player_id and game_id.
    This guarantees that simulated stats are identical across runs.
    """
    seed_str = f"{player_id}_{game_id}"
    seed = zlib.crc32(seed_str.encode('utf-8'))
    return np.random.default_rng(seed)

def simulate_player_stats(row: pd.Series) -> dict:
    """
    Simulates detailed match events for a single appearance based on player position
    and minutes played, ensuring logical consistency (e.g. shots >= shots_on_target >= goals).
    """
    player_id = int(row['player_id'])
    game_id = int(row['game_id'])
    position = str(row['position']).lower()
    mins = int(row['minutes_played'])
    
    # Get seeded random generator
    rng = get_seeded_generator(player_id, game_id)
    
    # Scale factor based on minutes played (90 minutes is standard base)
    scale = mins / 90.0 if mins > 0 else 0.0
    
    # Initialize all simulated fields
    saves = 0
    tackles = 0
    interceptions = 0
    blocks = 0
    passes_attempted = 0
    passes_completed = 0
    key_passes = 0
    shots = 0
    shots_on_target = 0
    dribbles_completed = 0
    
    # Calculate goals conceded based on game score and home/away team
    goals_conceded = 0
    if position in ['goalkeeper', 'defender']:
        # If player represented home team, they conceded away team goals
        if row['player_club_id'] == row['home_club_id']:
            goals_conceded = int(row['away_club_goals'])
        else:
            goals_conceded = int(row['home_club_goals'])
            
    # Clean sheet calculation
    clean_sheet = 1 if (position in ['goalkeeper', 'defender'] and goals_conceded == 0 and mins >= 45) else 0

    if mins > 0:
        if position == 'goalkeeper':
            saves = rng.poisson(lam=3.2 * scale)
            passes_attempted = int(rng.normal(loc=18 * scale, scale=4 * scale))
            passes_attempted = max(1, passes_attempted)
            accuracy = 0.65
            passes_completed = rng.binomial(n=passes_attempted, p=accuracy)
            key_passes = rng.poisson(lam=0.01 * scale)
            
        elif position == 'defender':
            tackles = rng.poisson(lam=2.8 * scale)
            interceptions = rng.poisson(lam=2.2 * scale)
            blocks = rng.poisson(lam=1.5 * scale)
            passes_attempted = int(rng.normal(loc=42 * scale, scale=8 * scale))
            passes_attempted = max(1, passes_attempted)
            accuracy = 0.82
            passes_completed = rng.binomial(n=passes_attempted, p=accuracy)
            key_passes = rng.poisson(lam=0.3 * scale)
            shots = rng.poisson(lam=0.4 * scale)
            shots_on_target = rng.binomial(n=shots, p=0.40)
            dribbles_completed = rng.poisson(lam=0.5 * scale)
            
        elif position in ['midfield', 'midfielder']:
            tackles = rng.poisson(lam=1.8 * scale)
            interceptions = rng.poisson(lam=1.5 * scale)
            blocks = rng.poisson(lam=0.6 * scale)
            passes_attempted = int(rng.normal(loc=55 * scale, scale=10 * scale))
            passes_attempted = max(1, passes_attempted)
            accuracy = 0.85
            passes_completed = rng.binomial(n=passes_attempted, p=accuracy)
            key_passes = rng.poisson(lam=1.5 * scale)
            shots = rng.poisson(lam=1.2 * scale)
            shots_on_target = rng.binomial(n=shots, p=0.42)
            dribbles_completed = rng.poisson(lam=1.4 * scale)
            
        elif position in ['attack', 'forward']:
            tackles = rng.poisson(lam=0.8 * scale)
            interceptions = rng.poisson(lam=0.4 * scale)
            blocks = rng.poisson(lam=0.1 * scale)
            passes_attempted = int(rng.normal(loc=24 * scale, scale=5 * scale))
            passes_attempted = max(1, passes_attempted)
            accuracy = 0.74
            passes_completed = rng.binomial(n=passes_attempted, p=accuracy)
            key_passes = rng.poisson(lam=1.1 * scale)
            shots = rng.poisson(lam=3.0 * scale)
            shots_on_target = rng.binomial(n=shots, p=0.45)
            dribbles_completed = rng.poisson(lam=2.2 * scale)
            
        else:
            # Fallback for missing/unknown positions (simulate as Midfielders)
            tackles = rng.poisson(lam=1.8 * scale)
            interceptions = rng.poisson(lam=1.5 * scale)
            blocks = rng.poisson(lam=0.6 * scale)
            passes_attempted = int(rng.normal(loc=55 * scale, scale=10 * scale))
            passes_attempted = max(1, passes_attempted)
            accuracy = 0.85
            passes_completed = rng.binomial(n=passes_attempted, p=accuracy)
            key_passes = rng.poisson(lam=1.5 * scale)
            shots = rng.poisson(lam=1.2 * scale)
            shots_on_target = rng.binomial(n=shots, p=0.42)
            dribbles_completed = rng.poisson(lam=1.4 * scale)

    # logical consistency adjustments:
    # 1. Shots on target must be at least equal to goals scored
    goals = int(row['goals'])
    assists = int(row['assists'])
    
    if shots_on_target < goals:
        shots_on_target = goals
    # 2. Total shots must be at least equal to shots on target
    if shots < shots_on_target:
        shots = shots_on_target
        
    return {
        'saves': saves,
        'goals_conceded': goals_conceded,
        'clean_sheet': clean_sheet,
        'tackles': tackles,
        'interceptions': interceptions,
        'blocks': blocks,
        'passes_attempted': passes_attempted,
        'passes_completed': passes_completed,
        'key_passes': key_passes,
        'shots': shots,
        'shots_on_target': shots_on_target,
        'dribbles_completed': dribbles_completed
    }

def calculate_match_rating(row: pd.Series) -> float:
    """
    Computes a realistic player match rating (1.0 to 10.0 scale) based on in-game performance.
    Base rating is 6.0. Plus/minus adjustments mimic professional analytics websites.
    """
    if row['minutes_played'] == 0:
        return np.nan
        
    rating = 6.0
    pos = str(row['position']).lower()
    
    # 1. Plus points for goals and assists
    if pos in ['defender', 'goalkeeper']:
        rating += 2.0 * row['goals']
    elif pos == 'midfielder':
        rating += 1.8 * row['goals']
    else: # Forward
        rating += 1.5 * row['goals']
        
    rating += 0.8 * row['assists']
    
    # 2. Passes and Playmaking
    rating += 0.15 * row['key_passes']
    if row['passes_attempted'] > 0:
        acc = row['passes_completed'] / row['passes_attempted']
        # Bonus/penalty for passing accuracy relative to 75%
        rating += (acc - 0.75) * 2.0  # +0.5 at 100%, -0.5 at 50%
        
    # 3. Defensive Actions
    rating += 0.10 * row['tackles']
    rating += 0.08 * row['interceptions']
    rating += 0.05 * row['blocks']
    
    # 4. Goalkeeper and Defensive Records
    if pos == 'goalkeeper':
        rating += 0.25 * row['saves']
        
    if pos in ['goalkeeper', 'defender']:
        rating += 0.5 * row['clean_sheet']
        rating -= 0.20 * row['goals_conceded']
        
    # 5. Attacking actions
    rating += 0.08 * row['dribbles_completed']
    rating += 0.05 * row['shots_on_target']
    
    # 6. Discipline Penalties
    rating -= 0.5 * row['yellow_cards']
    rating -= 1.5 * row['red_cards']
    
    # 7. Sub Scaling (scale sub ratings towards 6.0 if they played very few minutes)
    if row['minutes_played'] < 20:
        factor = row['minutes_played'] / 20.0
        rating = 6.0 + (rating - 6.0) * factor
        
    # Cap between 1.0 and 10.0
    rating = max(1.0, min(10.0, rating))
    return round(rating, 1)

def run_feature_engineering(processed_dir: str = "data/processed") -> None:
    """
    Performs the feature engineering pipeline: loads preprocessed data, calculates
    standard and simulated metrics, computes composite ratings and contribution indices,
    and overwrites the processed CSV files.
    """
    print("--- Running Feature Engineering Pipeline ---")
    
    # Load processed tables
    df_games = pd.read_csv(os.path.join(processed_dir, "games.csv"))
    df_app = pd.read_csv(os.path.join(processed_dir, "appearances.csv"))
    df_players = pd.read_csv(os.path.join(processed_dir, "players.csv"))
    
    # We need player positions in appearances to run simulations correctly
    # Merging position from players into appearances
    df_app_pos = df_app.merge(df_players[['player_id', 'position']], on='player_id', how='left')
    
    # We also need match scores and club IDs from games
    df_app_full = df_app_pos.merge(
        df_games[['game_id', 'home_club_id', 'away_club_id', 'home_club_goals', 'away_club_goals']],
        on='game_id',
        how='left'
    )
    
    # 1. Deterministic simulation of player stats
    print("Simulating detailed match event statistics...")
    sim_stats = df_app_full.apply(simulate_player_stats, axis=1)
    df_sim = pd.DataFrame(list(sim_stats))
    
    # Drop already simulated columns if they exist in df_app to prevent duplicates
    cols_to_drop = [col for col in df_sim.columns if col in df_app.columns]
    # Also drop previously engineered metric columns to prevent duplicates
    metric_cols = ['match_rating', 'attacking_contribution', 'defensive_score', 'defensive_contribution', 'pass_accuracy', 'performance_index', 'goals_per_90', 'assists_per_90', 'position']
    cols_to_drop += [col for col in metric_cols if col in df_app.columns]
    df_app_clean = df_app.drop(columns=cols_to_drop, errors='ignore')
    
    # Concatenate simulated columns with original appearances
    df_engineered = pd.concat([df_app_clean, df_sim], axis=1)
    
    # 2. Add player positions back for rating and index calculations
    df_engineered['position'] = df_app_pos['position']
    
    # 3. Calculate Custom Match Rating
    print("Calculating player match ratings (1-10)...")
    df_engineered['match_rating'] = df_engineered.apply(calculate_match_rating, axis=1)
    
    # 4. Calculate Attacking and Defensive Contribution Scores (0 to 100)
    print("Computing contribution scores...")
    
    # Raw values
    df_engineered['raw_attacking'] = (
        30 * df_engineered['goals'] +
        20 * df_engineered['assists'] +
        15 * df_engineered['shots_on_target'] +
        20 * df_engineered['key_passes'] +
        15 * df_engineered['dribbles_completed']
    )
    
    df_engineered['raw_defensive'] = (
        35 * df_engineered['tackles'] +
        30 * df_engineered['interceptions'] +
        20 * df_engineered['blocks'] +
        15 * df_engineered['clean_sheet']
    )
    
    # Min-max scaling to 0-100
    for col in ['raw_attacking', 'raw_defensive']:
        min_val = df_engineered[col].min()
        max_val = df_engineered[col].max()
        scaled_col = col.replace('raw_', '') + '_contribution'
        if max_val > min_val:
            df_engineered[scaled_col] = ((df_engineered[col] - min_val) / (max_val - min_val) * 100).round(1)
        else:
            df_engineered[scaled_col] = 0.0
            
    # Calculate Pass Accuracy Percentage
    df_engineered['pass_accuracy'] = np.where(
        df_engineered['passes_attempted'] > 0,
        (df_engineered['passes_completed'] / df_engineered['passes_attempted'] * 100).round(1),
        0.0
    )
    
    # 5. Position-Weighted Performance Index (0 to 100)
    print("Calculating overall performance index...")
    conditions = [
        (df_engineered['position'].str.lower() == 'goalkeeper'),
        (df_engineered['position'].str.lower() == 'defender'),
        (df_engineered['position'].str.lower() == 'midfielder'),
        (df_engineered['position'].str.lower().isin(['attack', 'forward']))
    ]
    
    # GK: heavily weighted on saves and clean sheet (using defensive raw contribution for saves/clean sheet representation)
    gk_index = (df_engineered['saves'] * 20 + df_engineered['clean_sheet'] * 30 + df_engineered['pass_accuracy'] * 0.5)
    gk_index_scaled = (gk_index - gk_index.min()) / (gk_index.max() - gk_index.min()) * 100 if gk_index.max() > gk_index.min() else 0.0
    
    choices = [
        gk_index_scaled,
        (df_engineered['defensive_contribution'] * 0.7 + df_engineered['attacking_contribution'] * 0.3),
        (df_engineered['defensive_contribution'] * 0.5 + df_engineered['attacking_contribution'] * 0.5),
        (df_engineered['defensive_contribution'] * 0.2 + df_engineered['attacking_contribution'] * 0.8)
    ]
    
    df_engineered['performance_index'] = np.select(conditions, choices, default=50.0).round(1)
    
    # 6. Per-90 standard metrics
    print("Calculating standard metrics per 90...")
    df_engineered['goals_per_90'] = np.where(
        df_engineered['minutes_played'] > 0,
        (df_engineered['goals'] / (df_engineered['minutes_played'] / 90.0)).round(2),
        0.0
    )
    df_engineered['assists_per_90'] = np.where(
        df_engineered['minutes_played'] > 0,
        (df_engineered['assists'] / (df_engineered['minutes_played'] / 90.0)).round(2),
        0.0
    )
    df_engineered['goal_contributions_per_90'] = (df_engineered['goals_per_90'] + df_engineered['assists_per_90']).round(2)
    
    df_engineered['minutes_per_goal'] = np.where(
        df_engineered['goals'] > 0,
        (df_engineered['minutes_played'] / df_engineered['goals']).round(1),
        np.nan
    )
    df_engineered['minutes_per_assist'] = np.where(
        df_engineered['assists'] > 0,
        (df_engineered['minutes_played'] / df_engineered['assists']).round(1),
        np.nan
    )
    
    # Drop position and raw columns before saving (keep clean database schema)
    clean_columns = [
        'appearance_id', 'game_id', 'player_id', 'player_club_id', 'player_current_club_id',
        'date', 'player_name', 'competition_id', 'goals', 'assists', 'yellow_cards', 'red_cards',
        'minutes_played', 'saves', 'goals_conceded', 'clean_sheet', 'tackles', 'interceptions',
        'blocks', 'passes_attempted', 'passes_completed', 'key_passes', 'shots', 'shots_on_target',
        'dribbles_completed', 'match_rating', 'attacking_contribution', 'defensive_contribution',
        'pass_accuracy', 'performance_index', 'goals_per_90', 'assists_per_90',
        'goal_contributions_per_90', 'minutes_per_goal', 'minutes_per_assist'
    ]
    
    df_output = df_engineered[clean_columns].copy()
    
    # Save the updated appearances table
    df_output.to_csv(os.path.join(processed_dir, "appearances.csv"), index=False)
    print("Saved updated appearances.csv with engineered features.")
    print("--- Feature Engineering Completed Successfully! ---\n")

if __name__ == "__main__":
    run_feature_engineering()
