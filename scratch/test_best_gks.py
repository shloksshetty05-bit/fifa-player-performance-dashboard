import sqlite3
import pandas as pd
from src.sql_queries import get_best_goalkeepers, get_best_midfielders, get_best_defenders, get_best_young_players
from sqlalchemy import create_engine

engine = create_engine("sqlite:///database/fifa_worldcup.db")

print("--- Best Goalkeepers ---")
print(get_best_goalkeepers(engine, limit=5))

print("\n--- Best Defenders ---")
print(get_best_defenders(engine, limit=5))

print("\n--- Best Midfielders ---")
print(get_best_midfielders(engine, limit=5))

print("\n--- Best Young Players ---")
print(get_best_young_players(engine, limit=5))
