"""
SQL Queries & Database Module
-----------------------------
Defines the SQLite database schema using SQLAlchemy, handles loading processed CSV data
into the database, and provides a library of analytical SQL queries to fetch dashboard data.
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, Float, Date
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

# ----------------- Database Schema Definitions -----------------

class Team(Base):
    __tablename__ = 'clubs'  # Map to clubs table
    club_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    squad_size = Column(Integer)
    average_age = Column(Float)
    total_market_value = Column(Float)

class Player(Base):
    __tablename__ = 'players'
    player_id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    name = Column(String, nullable=False)
    last_season = Column(Integer)
    current_club_id = Column(Integer)
    player_code = Column(String)
    country_of_birth = Column(String)
    city_of_birth = Column(String)
    country_of_citizenship = Column(String)
    date_of_birth = Column(String)
    sub_position = Column(String)
    position = Column(String)
    foot = Column(String)
    height_in_cm = Column(Float)
    market_value_in_eur = Column(Float)
    highest_market_value_in_eur = Column(Float)
    contract_expiration_date = Column(String)
    agent_name = Column(String)
    image_url = Column(String)
    url = Column(String)
    current_club_domestic_league_id = Column(String)
    current_club_name = Column(String)
    national_team_id = Column(Integer)
    is_verified = Column(Integer, default=0)

class Game(Base):
    __tablename__ = 'games'
    game_id = Column(Integer, primary_key=True)
    competition_id = Column(String)
    season = Column(Integer)
    round = Column(String)
    date = Column(String)
    home_club_id = Column(Integer)
    away_club_id = Column(Integer)
    home_club_goals = Column(Integer)
    away_club_goals = Column(Integer)
    home_club_position = Column(Float)
    away_club_position = Column(Float)
    home_club_manager_name = Column(String)
    away_club_manager_name = Column(String)
    stadium = Column(String)
    attendance = Column(Integer)
    referee = Column(String)
    url = Column(String)
    home_club_formation = Column(String)
    away_club_formation = Column(String)
    home_club_name = Column(String)
    away_club_name = Column(String)
    aggregate = Column(String)
    competition_type = Column(String)

class Appearance(Base):
    __tablename__ = 'appearances'
    appearance_id = Column(String, primary_key=True)
    game_id = Column(Integer)
    player_id = Column(Integer)
    player_club_id = Column(Integer)
    player_current_club_id = Column(Integer)
    date = Column(String)
    player_name = Column(String)
    competition_id = Column(String)
    goals = Column(Integer)
    assists = Column(Integer)
    yellow_cards = Column(Integer)
    red_cards = Column(Integer)
    minutes_played = Column(Integer)
    saves = Column(Integer)
    goals_conceded = Column(Integer)
    clean_sheet = Column(Integer)
    tackles = Column(Integer)
    interceptions = Column(Integer)
    blocks = Column(Integer)
    passes_attempted = Column(Integer)
    passes_completed = Column(Integer)
    key_passes = Column(Integer)
    shots = Column(Integer)
    shots_on_target = Column(Integer)
    dribbles_completed = Column(Integer)
    match_rating = Column(Float)
    attacking_contribution = Column(Float)
    defensive_contribution = Column(Float)
    pass_accuracy = Column(Float)
    performance_index = Column(Float)
    goals_per_90 = Column(Float)
    assists_per_90 = Column(Float)
    goal_contributions_per_90 = Column(Float)
    minutes_per_goal = Column(Float)
    minutes_per_assist = Column(Float)

# ----------------- Database Management Helper Functions -----------------

def get_db_engine(db_path: str = "database/fifa_worldcup.db") -> create_engine:
    """Creates and returns a SQLAlchemy connection engine."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return create_engine(f"sqlite:///{db_path}")

def load_data_to_sqlite(db_path: str = "database/fifa_worldcup.db", processed_dir: str = "data/processed") -> None:
    """
    Creates SQLite tables according to declarative schema and imports processed CSV data,
    filtering columns to match schema definitions exactly.
    """
    engine = get_db_engine(db_path)
    
    # Drop and recreate tables to ensure schema is clean
    print("Recreating database tables...")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    
    # Map CSV files to SQLAlchemy models and tables
    model_mappings = {
        "clubs.csv": (Team, "clubs"),
        "players.csv": (Player, "players"),
        "games.csv": (Game, "games"),
        "appearances.csv": (Appearance, "appearances")
    }
    
    print("Loading data from processed CSVs...")
    for csv_file, (model_class, table_name) in model_mappings.items():
        filepath = os.path.join(processed_dir, csv_file)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Processed file {csv_file} not found. Run preprocessing and feature engineering first.")
            
        df = pd.read_csv(filepath)
        
        # Get target columns from SQLAlchemy model table
        table_columns = [c.name for c in model_class.__table__.columns]
        
        # Filter dataframe columns to only keep those defined in SQLAlchemy model
        df_filtered = df[[col for col in table_columns if col in df.columns]].copy()
        
        # Import to SQL
        df_filtered.to_sql(table_name, con=engine, if_exists="append", index=False)
        print(f"Loaded {len(df_filtered)} records into table '{table_name}' (Matched columns: {df_filtered.shape[1]}/{len(table_columns)}).")
        
    print("Database initialization complete.")

def run_query(engine, sql_string: str, params: dict = None) -> pd.DataFrame:
    """Executes a raw SQL query and returns results in a Pandas DataFrame."""
    with engine.connect() as conn:
        result = conn.execute(text(sql_string), params or {})
        return pd.DataFrame(result.all(), columns=result.keys())

# ----------------- SQL Analytical Queries -----------------

def get_top_scorers(engine, season: int = None, limit: int = 10) -> pd.DataFrame:
    """Fetches top goalscorers. Optionally filters by World Cup season."""
    query = """
    SELECT 
        a.player_name, 
        c.name AS country, 
        SUM(a.goals) AS goals, 
        SUM(a.assists) AS assists, 
        SUM(a.minutes_played) AS minutes_played,
        ROUND(SUM(a.goals) * 90.0 / SUM(a.minutes_played), 2) AS goals_per_90
    FROM appearances a
    JOIN games g ON a.game_id = g.game_id
    JOIN clubs c ON a.player_club_id = c.club_id
    JOIN players p ON a.player_id = p.player_id
    WHERE p.is_verified = 1
    """
    params = {"limit": limit}
    
    if season:
        query += " AND g.season = :season "
        params["season"] = season
        
    query += """
    GROUP BY a.player_id, a.player_name, c.name
    ORDER BY goals DESC, assists DESC, minutes_played ASC
    LIMIT :limit
    """
    return run_query(engine, query, params)

def get_top_assists(engine, season: int = None, limit: int = 10) -> pd.DataFrame:
    """Fetches top assist providers. Optionally filters by season."""
    query = """
    SELECT 
        a.player_name, 
        c.name AS country, 
        SUM(a.assists) AS assists, 
        SUM(a.goals) AS goals, 
        SUM(a.minutes_played) AS minutes_played,
        ROUND(SUM(a.assists) * 90.0 / SUM(a.minutes_played), 2) AS assists_per_90
    FROM appearances a
    JOIN games g ON a.game_id = g.game_id
    JOIN clubs c ON a.player_club_id = c.club_id
    JOIN players p ON a.player_id = p.player_id
    WHERE p.is_verified = 1
    """
    params = {"limit": limit}
    
    if season:
        query += " AND g.season = :season "
        params["season"] = season
        
    query += """
    GROUP BY a.player_id, a.player_name, c.name
    ORDER BY assists DESC, goals DESC, minutes_played ASC
    LIMIT :limit
    """
    return run_query(engine, query, params)

def get_highest_rated_players(engine, season: int = None, min_minutes: int = 180, limit: int = 10) -> pd.DataFrame:
    """Fetches the highest rated players who meet a minimum minutes threshold."""
    query = """
    SELECT 
        a.player_name, 
        c.name AS country, 
        p.position,
        COUNT(a.appearance_id) AS matches,
        SUM(a.minutes_played) AS total_minutes,
        ROUND(AVG(a.match_rating), 2) AS avg_rating,
        ROUND(AVG(a.performance_index), 1) AS avg_performance_index
    FROM appearances a
    JOIN games g ON a.game_id = g.game_id
    JOIN clubs c ON a.player_club_id = c.club_id
    JOIN players p ON a.player_id = p.player_id
    WHERE p.is_verified = 1
    """
    params = {"limit": limit, "min_minutes": min_minutes}
    
    if season:
        query += " AND g.season = :season "
        params["season"] = season
        
    query += """
    GROUP BY a.player_id, a.player_name, c.name, p.position
    HAVING total_minutes >= :min_minutes
    ORDER BY avg_rating DESC, avg_performance_index DESC
    LIMIT :limit
    """
    return run_query(engine, query, params)

def get_best_goalkeepers(engine, season: int = None, limit: int = 10) -> pd.DataFrame:
    """Fetches top goalkeepers based on clean sheets, saves, and rating."""
    query = """
    SELECT 
        a.player_name, 
        c.name AS country, 
        SUM(a.minutes_played) AS total_minutes,
        SUM(a.saves) AS total_saves,
        SUM(a.goals_conceded) AS goals_conceded,
        SUM(a.clean_sheet) AS clean_sheets,
        ROUND(AVG(a.match_rating), 2) AS avg_rating
    FROM appearances a
    JOIN games g ON a.game_id = g.game_id
    JOIN clubs c ON a.player_club_id = c.club_id
    JOIN players p ON a.player_id = p.player_id
    WHERE p.position = 'Goalkeeper' AND p.is_verified = 1
    """
    params = {"limit": limit}
    
    if season:
        query += " AND g.season = :season "
        params["season"] = season
        
    query += """
    GROUP BY a.player_id, a.player_name, c.name
    ORDER BY clean_sheets DESC, total_saves DESC, avg_rating DESC
    LIMIT :limit
    """
    return run_query(engine, query, params)

def get_best_defenders(engine, season: int = None, limit: int = 10) -> pd.DataFrame:
    """Fetches top defenders based on defensive contribution score and clean sheets."""
    query = """
    SELECT 
        a.player_name, 
        c.name AS country, 
        SUM(a.minutes_played) AS total_minutes,
        SUM(a.tackles) AS tackles,
        SUM(a.interceptions) AS interceptions,
        SUM(a.blocks) AS blocks,
        SUM(a.clean_sheet) AS clean_sheets,
        ROUND(AVG(a.defensive_contribution), 1) AS defensive_score,
        ROUND(AVG(a.match_rating), 2) AS avg_rating
    FROM appearances a
    JOIN games g ON a.game_id = g.game_id
    JOIN clubs c ON a.player_club_id = c.club_id
    JOIN players p ON a.player_id = p.player_id
    WHERE p.position = 'Defender' AND p.is_verified = 1
    """
    params = {"limit": limit}
    
    if season:
        query += " AND g.season = :season "
        params["season"] = season
        
    query += """
    GROUP BY a.player_id, a.player_name, c.name
    ORDER BY defensive_score DESC, avg_rating DESC
    LIMIT :limit
    """
    return run_query(engine, query, params)

def get_best_midfielders(engine, season: int = None, limit: int = 10) -> pd.DataFrame:
    """Fetches top midfielders based on key passes, pass accuracy, and rating."""
    query = """
    SELECT 
        a.player_name, 
        c.name AS country, 
        SUM(a.minutes_played) AS total_minutes,
        SUM(a.passes_attempted) AS passes_attempted,
        SUM(a.passes_completed) AS passes_completed,
        ROUND(SUM(a.passes_completed) * 100.0 / SUM(a.passes_attempted), 1) AS pass_accuracy_pct,
        SUM(a.key_passes) AS key_passes,
        SUM(a.assists) AS assists,
        ROUND(AVG(a.match_rating), 2) AS avg_rating
    FROM appearances a
    JOIN games g ON a.game_id = g.game_id
    JOIN clubs c ON a.player_club_id = c.club_id
    JOIN players p ON a.player_id = p.player_id
    WHERE p.position IN ('Midfield', 'Midfielder') AND p.is_verified = 1
    """
    params = {"limit": limit}
    
    if season:
        query += " AND g.season = :season "
        params["season"] = season
        
    query += """
    GROUP BY a.player_id, a.player_name, c.name
    ORDER BY key_passes DESC, pass_accuracy_pct DESC, avg_rating DESC
    LIMIT :limit
    """
    return run_query(engine, query, params)

def get_best_young_players(engine, season: int = None, limit: int = 10) -> pd.DataFrame:
    """Fetches top players aged 23 or under during the tournament."""
    query = """
    SELECT 
        a.player_name, 
        c.name AS country, 
        p.position,
        (g.season - CAST(SUBSTR(p.date_of_birth, 1, 4) AS INTEGER)) AS age_at_tournament,
        SUM(a.minutes_played) AS total_minutes,
        SUM(a.goals) AS goals,
        SUM(a.assists) AS assists,
        ROUND(AVG(a.match_rating), 2) AS avg_rating
    FROM appearances a
    JOIN games g ON a.game_id = g.game_id
    JOIN clubs c ON a.player_club_id = c.club_id
    JOIN players p ON a.player_id = p.player_id
    WHERE (g.season - CAST(SUBSTR(p.date_of_birth, 1, 4) AS INTEGER)) <= 23 AND p.is_verified = 1
    """
    params = {"limit": limit}
    
    if season:
        query += " AND g.season = :season "
        params["season"] = season
        
    query += """
    GROUP BY a.player_id, a.player_name, c.name, p.position
    HAVING total_minutes >= 90
    ORDER BY avg_rating DESC, goals DESC
    LIMIT :limit
    """
    return run_query(engine, query, params)

def get_country_rankings(engine, season: int = None) -> pd.DataFrame:
    """Aggregates World Cup statistics by country (wins, goals, average ratings)."""
    query = """
    SELECT 
        c.name AS country,
        c.squad_size,
        c.average_age,
        c.total_market_value,
        SUM(a.goals) AS goals,
        SUM(a.assists) AS assists,
        ROUND(AVG(a.match_rating), 2) AS avg_rating
    FROM clubs c
    JOIN appearances a ON c.club_id = a.player_club_id
    JOIN games g ON a.game_id = g.game_id
    """
    params = {}
    if season:
        query += " WHERE g.season = :season "
        params["season"] = season
        
    query += """
    GROUP BY c.club_id, c.name, c.squad_size, c.average_age, c.total_market_value
    ORDER BY goals DESC, avg_rating DESC
    """
    return run_query(engine, query, params)

def get_tournament_stats(engine) -> pd.DataFrame:
    """Returns summarized stats for each World Cup season."""
    query = """
    SELECT 
        g.season,
        COUNT(DISTINCT g.game_id) AS total_matches,
        SUM(g.home_club_goals + g.away_club_goals) AS total_goals,
        ROUND(AVG(g.home_club_goals + g.away_club_goals), 2) AS avg_goals_per_match,
        SUM(g.attendance) AS total_attendance,
        ROUND(AVG(g.attendance), 0) AS avg_attendance
    FROM games g
    GROUP BY g.season
    ORDER BY g.season DESC
    """
    return run_query(engine, query)

def get_player_game_log(engine, player_id: int) -> pd.DataFrame:
    """Gets game-by-game statistics for a specific player."""
    query = """
    SELECT 
        g.date,
        g.season,
        g.home_club_name || ' vs ' || g.away_club_name AS match_name,
        a.goals,
        a.assists,
        a.minutes_played,
        a.shots,
        a.passes_completed || '/' || a.passes_attempted AS passes,
        a.tackles,
        a.saves,
        a.match_rating
    FROM appearances a
    JOIN games g ON a.game_id = g.game_id
    WHERE a.player_id = :player_id
    ORDER BY g.date ASC
    """
    return run_query(engine, query, {"player_id": player_id})

if __name__ == "__main__":
    load_data_to_sqlite()
    # Basic verification test
    engine = get_db_engine()
    df = get_top_scorers(engine, limit=5)
    print("\nSample SQL Output (Top 5 Scorers overall):")
    print(df)
