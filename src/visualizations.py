"""
Visualizations Module
---------------------
This module creates all the charts for the dashboard.
It uses Plotly for interactive web charts, and Matplotlib/Seaborn for clean static plots.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# Set up Seaborn's theme for clean, white background plots
sns.set_theme(style="whitegrid")
plt.rcParams['figure.facecolor'] = '#ffffff'
plt.rcParams['axes.facecolor'] = '#ffffff'

def get_val(d: dict, key: str, default: float = 0.0) -> float:
    """
    Safely retrieves a numeric value from a dictionary.
    If the value is missing, None, or NaN (Not a Number), it returns the default value (0.0).
    This keeps the charts from crashing if some player stats are missing.
    """
    val = d.get(key)
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return default
    try:
        return float(val)
    except:
        return default

# ----------------- Plotly Interactive Visualizations -----------------

def plot_player_radar(player_data: dict, player_name: str, comparison_data: dict = None, comparison_name: str = None) -> go.Figure:
    """
    Draws an interactive radar (spider) chart to compare player stats.
    Each stat is scaled between 0 and 100 so they fit nicely on the same circular grid.
    """
    categories = [
        'Goals per 90', 'Assists per 90', 'Key Passes', 
        'Dribbles Completed', 'Pass Accuracy %', 'Defensive Actions'
    ]
    
    fig = go.Figure()
    
    # --- Primary Player Data Extraction ---
    # We sum tackles, interceptions, and blocks to get the total 'Defensive Actions'
    tackles1 = get_val(player_data, 'tackles')
    interceptions1 = get_val(player_data, 'interceptions')
    blocks1 = get_val(player_data, 'blocks')
    def_actions1 = tackles1 + interceptions1 + blocks1
    
    # Calculate average per-game stats by dividing totals by the number of matches played
    matches1 = max(1.0, get_val(player_data, 'matches'))
    avg_kp1 = get_val(player_data, 'key_passes') / matches1
    avg_drib1 = get_val(player_data, 'dribbles_completed') / matches1
    avg_def1 = def_actions1 / matches1
    
    # Build the 6-dimension stats array scaled to a 0-100 range
    val1 = [
        min(100.0, get_val(player_data, 'goals_per_90') * 100),
        min(100.0, get_val(player_data, 'assists_per_90') * 100),
        min(100.0, (avg_kp1 / 4.0) * 100),
        min(100.0, (avg_drib1 / 4.0) * 100),
        get_val(player_data, 'pass_accuracy'),
        min(100.0, (avg_def1 / 6.0) * 100)
    ]
    
    # Close the radar loop
    val1_closed = val1 + [val1[0]]
    categories_closed = categories + [categories[0]]
    
    # Add primary player with Custom dark Cyan
    fig.add_trace(go.Scatterpolar(
        r=val1_closed,
        theta=categories_closed,
        fill='toself',
        fillcolor='rgba(0, 240, 255, 0.15)',
        line=dict(color='#00F0FF', width=3),
        name=player_name
    ))
    
    # Add comparison player if provided
    if comparison_data and comparison_name:
        tackles2 = get_val(comparison_data, 'tackles')
        interceptions2 = get_val(comparison_data, 'interceptions')
        blocks2 = get_val(comparison_data, 'blocks')
        def_actions2 = tackles2 + interceptions2 + blocks2
        
        matches2 = max(1.0, get_val(comparison_data, 'matches'))
        avg_kp2 = get_val(comparison_data, 'key_passes') / matches2
        avg_drib2 = get_val(comparison_data, 'dribbles_completed') / matches2
        avg_def2 = def_actions2 / matches2
        
        val2 = [
            min(100.0, get_val(comparison_data, 'goals_per_90') * 100),
            min(100.0, get_val(comparison_data, 'assists_per_90') * 100),
            min(100.0, (avg_kp2 / 4.0) * 100),
            min(100.0, (avg_drib2 / 4.0) * 100),
            get_val(comparison_data, 'pass_accuracy'),
            min(100.0, (avg_def2 / 6.0) * 100)
        ]
        val2_closed = val2 + [val2[0]]
        
        # Add comparison player with Premium Neon Rose
        fig.add_trace(go.Scatterpolar(
            r=val2_closed,
            theta=categories_closed,
            fill='toself',
            fillcolor='rgba(255, 0, 127, 0.15)',
            line=dict(color='#FF007F', width=3),
            name=comparison_name
        ))
        
    fig.update_layout(
        polar=dict(
            bgcolor='rgba(255, 255, 255, 0.03)',
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                showticklabels=True,
                tickfont=dict(size=8, color='#888888'),
                gridcolor='rgba(128, 128, 128, 0.15)',
                linecolor='rgba(128, 128, 128, 0.15)'
            ),
            angularaxis=dict(
                tickfont=dict(size=9, color='#a0a0a0', weight='bold'),
                gridcolor='rgba(128, 128, 128, 0.15)',
                linecolor='rgba(128, 128, 128, 0.15)'
            )
        ),
        showlegend=True,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=60, r=60, t=50, b=40),
        height=380,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.1,
            xanchor="center",
            x=0.5,
            font=dict(size=10, color='#888888')
        )
    )
    return fig

def plot_player_trend(game_log_df: pd.DataFrame, player_name: str) -> go.Figure:
    """
    Generates a line plot showing player match ratings over matches.
    """
    fig = go.Figure()
    
    # Add match rating line
    fig.add_trace(go.Scatter(
        x=game_log_df['match_name'],
        y=game_log_df['match_rating'],
        mode='lines+markers',
        line=dict(color='#2ca02c', width=3),
        marker=dict(size=8, symbol='circle'),
        name='Match Rating',
        hovertemplate='Match: %{x}<br>Rating: %{y:.1f}<extra></extra>'
    ))
    
    # Add annotation for goals/assists
    for idx, row in game_log_df.iterrows():
        contrib = []
        if row['goals'] > 0:
            contrib.append(f"{int(row['goals'])}G")
        if row['assists'] > 0:
            contrib.append(f"{int(row['assists'])}A")
            
        if contrib:
            fig.add_annotation(
                x=row['match_name'],
                y=row['match_rating'] + 0.2,
                text="+".join(contrib),
                showarrow=False,
                font=dict(size=10, color="white"),
                bgcolor="#1f77b4",
                borderpad=4
            )
            
    fig.update_layout(
        title=f"Match Rating Trend for {player_name}",
        xaxis_title="Match",
        yaxis_title="Match Rating (1-10)",
        yaxis=dict(range=[1.0, 10.5]),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=40, t=50, b=40),
        height=300
    )
    return fig

def plot_team_comparison(team1_df: pd.DataFrame, team2_df: pd.DataFrame, t1_name: str, t2_name: str) -> go.Figure:
    """
    Plots a dual bar chart comparing two national teams across key aggregates.
    """
    metrics = ['Squad Size', 'Average Age', 'Total Goals', 'Total Assists', 'Average Match Rating']
    
    # Gather metrics safely
    t1_vals = [
        int(team1_df['squad_size'].iloc[0]) if 'squad_size' in team1_df.columns else 23,
        float(team1_df['average_age'].iloc[0]),
        int(team1_df['goals'].iloc[0]) if 'goals' in team1_df.columns else 0,
        int(team1_df['assists'].iloc[0]) if 'assists' in team1_df.columns else 0,
        float(team1_df['avg_rating'].iloc[0])
    ]
    
    t2_vals = [
        int(team2_df['squad_size'].iloc[0]) if 'squad_size' in team2_df.columns else 23,
        float(team2_df['average_age'].iloc[0]),
        int(team2_df['goals'].iloc[0]) if 'goals' in team2_df.columns else 0,
        int(team2_df['assists'].iloc[0]) if 'assists' in team2_df.columns else 0,
        float(team2_df['avg_rating'].iloc[0])
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=metrics,
        y=t1_vals,
        name=t1_name,
        marker_color='#1f77b4',
        text=[f"{v:.1f}" if isinstance(v, float) else str(v) for v in t1_vals],
        textposition='auto'
    ))
    
    fig.add_trace(go.Bar(
        x=metrics,
        y=t2_vals,
        name=t2_name,
        marker_color='#d62728',
        text=[f"{v:.1f}" if isinstance(v, float) else str(v) for v in t2_vals],
        textposition='auto'
    ))
    
    fig.update_layout(
        title=f"National Team Comparison: {t1_name} vs {t2_name}",
        barmode='group',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=40, t=50, b=40),
        height=350
    )
    return fig

def plot_squad_bubble_chart(players_df: pd.DataFrame, team_name: str) -> go.Figure:
    """
    Creates an interactive squad bubble chart.
    X-axis: Age, Y-axis: Market Value, Size: Performance Index, Color: Position.
    """
    # Clean market value for display (in Millions)
    players_df['value_m'] = players_df['market_value_in_eur'] / 1_000_000.0
    
    fig = px.scatter(
        players_df,
        x='age',
        y='value_m',
        size='performance_index',
        color='position',
        hover_name='name',
        hover_data={
            'age': True,
            'value_m': ':.1f',
            'position': True,
            'performance_index': ':.1f'
        },
        labels={
            'age': 'Age',
            'value_m': 'Market Value (M EUR)',
            'position': 'Position',
            'performance_index': 'Performance Index'
        },
        title=f"Squad Structure & Valuations - {team_name}"
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=40, t=50, b=40),
        height=380
    )
    return fig

# ----------------- Matplotlib / Seaborn Static Visualizations -----------------

def plot_position_rating_boxplot(appearances_df: pd.DataFrame) -> plt.Figure:
    """
    Plots a boxplot/violin plot showing the distribution of match ratings by player position.
    """
    fig, ax = plt.subplots(figsize=(8, 4))
    
    # Standard color palette for valid football positions
    colors = {
        "Goalkeeper": "#ff7f0e", 
        "Defender": "#1f77b4", 
        "Midfield": "#2ca02c", 
        "Attack": "#d62728"
    }
    
    # Capitalize positions and standardise names
    df_plot = appearances_df.copy()
    df_plot['position'] = df_plot['position'].fillna('Unknown').str.capitalize()
    df_plot['position'] = df_plot['position'].replace({
        "Midfielder": "Midfield", 
        "Forward": "Attack"
    })
    
    # Keep only standard positions (excluding any Missing or Unknown values)
    df_plot = df_plot[df_plot['position'].isin(colors.keys())].copy()
    
    sns.boxplot(
        data=df_plot,
        x='position',
        y='match_rating',
        hue='position',
        palette=colors,
        ax=ax,
        legend=False
    )
    
    ax.set_title("Match Rating Distribution by Player Position", fontsize=12, fontweight='bold', pad=12)
    ax.set_xlabel("Position", fontsize=10)
    ax.set_ylabel("Match Rating (1-10)", fontsize=10)
    ax.set_ylim(4.0, 10.2)
    
    plt.tight_layout()
    return fig

def plot_metrics_correlation(appearances_df: pd.DataFrame) -> plt.Figure:
    """
    Generates a correlation matrix heatmap of player actions and ratings.
    """
    fig, ax = plt.subplots(figsize=(9, 6))
    
    cols_to_correlate = [
        'goals', 'assists', 'minutes_played', 'saves', 'tackles', 
        'interceptions', 'passes_attempted', 'pass_accuracy', 
        'key_passes', 'shots_on_target', 'dribbles_completed', 'match_rating'
    ]
    
    # Filter to columns that exist
    cols = [col for col in cols_to_correlate if col in appearances_df.columns]
    
    corr = appearances_df[cols].corr()
    
    # Rename columns to look professional on the axis labels
    labels = [c.replace('_', ' ').title() for c in cols]
    
    sns.heatmap(
        corr,
        annot=True,
        cmap="coolwarm",
        fmt=".2f",
        vmin=-1,
        vmax=1,
        square=True,
        linewidths=0.5,
        xticklabels=labels,
        yticklabels=labels,
        ax=ax,
        cbar_kws={"shrink": 0.8}
    )
    
    ax.set_title("Performance Metrics Correlation Matrix", fontsize=12, fontweight='bold', pad=15)
    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    return fig

if __name__ == "__main__":
    print("FIFA Visualizations module initialized.")
