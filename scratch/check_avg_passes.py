import sqlite3
import pandas as pd

conn = sqlite3.connect("database/fifa_worldcup.db")
query = """
SELECT p.position, 
       AVG(a.passes_completed) as avg_completed, 
       AVG(a.passes_attempted) as avg_attempted,
       COUNT(a.appearance_id) as count
FROM appearances a
JOIN players p ON a.player_id = p.player_id
GROUP BY p.position
"""
df = pd.read_sql_query(query, conn)
print("Average passes per position:")
print(df)
conn.close()
