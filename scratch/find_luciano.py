import sqlite3
import pandas as pd

conn = sqlite3.connect("database/fifa_worldcup.db")

# Search for Luciano
print("Searching for Luciano in players:")
lucianos = pd.read_sql_query("SELECT player_id, name, position, is_verified, current_club_name, date_of_birth FROM players WHERE name LIKE '%Luciano%'", conn)
print(lucianos)

# Search for Peiser
print("\nSearching for Romuald Peiser in players:")
peiser = pd.read_sql_query("SELECT player_id, name, position, is_verified, current_club_name, date_of_birth FROM players WHERE name LIKE '%Peiser%'", conn)
print(peiser)

# Show best goalkeepers from database
print("\nBest Goalkeepers from database:")
best_gk = pd.read_sql_query("""
    SELECT p.player_id, p.name, p.is_verified, COUNT(a.appearance_id) as matches, SUM(a.saves) as saves
    FROM appearances a
    JOIN players p ON a.player_id = p.player_id
    WHERE p.position = 'Goalkeeper'
    GROUP BY p.player_id, p.name, p.is_verified
    ORDER BY matches DESC
    LIMIT 10
""", conn)
print(best_gk)

conn.close()
