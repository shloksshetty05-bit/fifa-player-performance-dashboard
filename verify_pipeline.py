"""
Verification Pipeline
---------------------
Tests the data preprocessing, feature engineering, and database tables
to ensure data integrity, relational consistency, and query stability.
"""

import os
import pandas as pd
from sqlalchemy import text
import src.sql_queries as db

def verify_files() -> bool:
    """Verifies that processed CSV files exist and are populated."""
    print("\n[1/3] Verifying processed CSV files...")
    files = ["games.csv", "appearances.csv", "players.csv", "clubs.csv"]
    success = True
    
    for f in files:
        path = os.path.join("data/processed", f)
        if not os.path.exists(path):
            print(f"[FAIL] Processed file {f} is missing.")
            success = False
        else:
            size = os.path.getsize(path)
            rows = len(pd.read_csv(path))
            print(f"[PASS] {f} exists ({rows} rows, {size/1024:.1f} KB).")
            
    return success

def verify_database() -> bool:
    """Verifies that SQLite database exists and contains expected record counts."""
    print("\n[2/3] Verifying SQLite database...")
    db_path = "database/fifa_worldcup.db"
    
    if not os.path.exists(db_path):
        print("[FAIL] SQLite database file is missing.")
        return False
        
    engine = db.get_db_engine(db_path)
    success = True
    
    tables = {
        "clubs": 70,
        "players": 987,
        "games": 392,
        "appearances": 2251
    }
    
    with engine.connect() as conn:
        for table, expected_min in tables.items():
            try:
                res = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                if res >= expected_min:
                    print(f"[PASS] Table '{table}' verified with {res} records (Expected >= {expected_min}).")
                else:
                    print(f"[FAIL] Table '{table}' has only {res} records (Expected >= {expected_min}).")
                    success = False
            except Exception as e:
                print(f"[FAIL] Error reading table '{table}': {e}")
                success = False
                
    return success

def verify_queries() -> bool:
    """Tests the execution of analytical SQL reporting queries."""
    print("\n[3/3] Testing SQL reporting queries...")
    engine = db.get_db_engine()
    success = True
    
    queries = {
        "Top Scorers": lambda: db.get_top_scorers(engine, limit=3),
        "Top Playmakers": lambda: db.get_top_assists(engine, limit=3),
        "Highest Rated": lambda: db.get_highest_rated_players(engine, limit=3),
        "Best Goalkeepers": lambda: db.get_best_goalkeepers(engine, limit=3),
        "Best Defenders": lambda: db.get_best_defenders(engine, limit=3),
        "Best Midfielders": lambda: db.get_best_midfielders(engine, limit=3),
        "Best Young Players": lambda: db.get_best_young_players(engine, limit=3),
        "Country Rankings": lambda: db.get_country_rankings(engine)
    }
    
    for name, query_func in queries.items():
        try:
            df = query_func()
            if not df.empty and len(df) > 0:
                print(f"[PASS] Query '{name}' completed successfully (Returned {len(df)} records).")
            else:
                print(f"[FAIL] Query '{name}' returned empty result.")
                success = False
        except Exception as e:
            print(f"[FAIL] Query '{name}' threw exception: {e}")
            success = False
            
    return success

def main():
    print("==================================================")
    print("  FIFA World Cup Dashboard - Verification Pipeline  ")
    print("==================================================")
    
    f_ok = verify_files()
    db_ok = verify_database()
    q_ok = verify_queries()
    
    print("\n==================================================")
    if f_ok and db_ok and q_ok:
        print("  VERIFICATION SUCCESS: All checks passed! Ready for production.  ")
    else:
        print("  VERIFICATION FAILURE: Some checks failed. Inspect logs.  ")
    print("==================================================")

if __name__ == "__main__":
    main()
