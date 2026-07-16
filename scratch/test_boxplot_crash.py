import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from src.visualizations import plot_position_rating_boxplot

conn = sqlite3.connect("database/fifa_worldcup.db")
df_all_app = pd.read_sql_query("SELECT * FROM appearances", conn)
print("Appearances unique positions (raw):")
print(df_all_app['position'].unique() if 'position' in df_all_app.columns else "position not in appearances!")

# Let's join with players if position is not in appearances
if 'position' not in df_all_app.columns:
    df_all_app = df_all_app.merge(
        pd.read_sql_query("SELECT player_id, position FROM players", conn),
        on='player_id',
        how='left'
    )

print("\nMerged unique positions:")
print(df_all_app['position'].unique())
print(df_all_app['position'].value_counts(dropna=False))

# Run plot
try:
    fig = plot_position_rating_boxplot(df_all_app)
    print("\n[PASS] Boxplot plotted successfully!")
except Exception as e:
    print("\n[FAIL] Boxplot failed with:")
    import traceback
    traceback.print_exc()

conn.close()
