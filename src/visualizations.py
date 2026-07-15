"""
Visualizations Module
---------------------
Contains drawing functions for static (Matplotlib/Seaborn) and interactive (Plotly) charts 
used across the Streamlit pages.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

def plot_radar_chart(player_stats: dict) -> go.Figure:
    """Generates an interactive Plotly radar chart comparing player performance parameters."""
    pass

def plot_performance_trend(df_appearances: pd.DataFrame) -> go.Figure:
    """Generates a line plot showing player match ratings over the course of a tournament."""
    pass

def plot_team_comparison(team1_stats: dict, team2_stats: dict) -> go.Figure:
    """Generates a comparison bar chart between two national teams."""
    pass
