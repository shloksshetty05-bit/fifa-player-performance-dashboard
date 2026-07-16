"""
FIFA World Cup Player Performance Analytics Dashboard
------------------------------------------------------
A production-quality multi-page Streamlit application for analyzing player
and team performance across recent FIFA World Cups using SQL, Pandas, and Plotly.
"""

import os
import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import datetime

# Import project modules
import importlib
import src.sql_queries as db
import src.visualizations as viz
importlib.reload(db)
importlib.reload(viz)

# Page config (must be the first Streamlit command)
st.set_page_config(
    page_title="FIFA World Cup Player Performance Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Season mapping for Transfermarkt cataloging conventions
# (e.g. World Cup 2022 calendar year is cataloged under season 2021)
SEASON_MAP = {
    2022: 2021,
    2018: 2017,
    2014: 2013,
    2010: 2009,
    2006: 2005
}

# ----------------- Database Setup & Self-Healing -----------------

DB_PATH = "database/fifa_worldcup.db"

@st.cache_resource
def initialize_app_database():
    """Checks for database presence and runs preprocessing if missing."""
    if not os.path.exists(DB_PATH):
        st.warning("Database not found. Generating data pipelines... Please wait.")
        from src.preprocessing import download_raw_data, process_world_cup_data
        from src.feature_engineering import run_feature_engineering
        
        # Run pipeline
        download_raw_data()
        process_world_cup_data()
        run_feature_engineering()
        db.load_data_to_sqlite()
        st.success("Database generated successfully!")
    return db.get_db_engine(DB_PATH)

engine = initialize_app_database()

# ----------------- Playing Style Classifier -----------------

def classify_player_style(stats: dict, position: str, height: float) -> dict:
    """
    Classifies a player into a playing style based on their match statistics.
    Returns a dictionary with the Style name and the match criteria details.
    """
    position = str(position).lower()
    goals = stats.get('goals', 0)
    assists = stats.get('assists', 0)
    minutes = stats.get('minutes', 1)
    
    goals_per_90 = (goals * 90.0) / minutes
    assists_per_90 = (assists * 90.0) / minutes
    key_passes_per_90 = (stats.get('key_passes', 0) * 90.0) / minutes
    tackles_per_90 = (stats.get('tackles', 0) * 90.0) / minutes
    interceptions_per_90 = (stats.get('interceptions', 0) * 90.0) / minutes
    dribbles_per_90 = (stats.get('dribbles_completed', 0) * 90.0) / minutes
    
    if position == 'goalkeeper':
        return {"style": "Goalkeeper", "desc": "Traditional GK: Focuses on shot stopping, saves, and clean sheets."}
        
    if position == 'defender':
        if tackles_per_90 >= 2.0 or stats.get('blocks', 0) >= 1.0:
            return {"style": "Defensive Rock", "desc": "Defensive Rock: Highly active in blocks, tackles, and clearances. Excellent in clean sheets."}
        else:
            return {"style": "Ball Playing Defender", "desc": "Ball Playing Defender: High pass accuracy and distributed play starting from the back."}
            
    if 'midfield' in position:
        if tackles_per_90 >= 1.5 and key_passes_per_90 >= 0.8:
            return {"style": "Box-to-Box Midfielder", "desc": "Box-to-Box Midfielder: High work-rate player contributing significantly in both attacking key passes and defensive tackles."}
        elif tackles_per_90 >= 2.0:
            return {"style": "Ball Winner", "desc": "Ball Winner: Specialized in breaking down opponent plays. High volume of tackles and interceptions."}
        elif assists_per_90 >= 0.25 or key_passes_per_90 >= 1.5:
            return {"style": "Playmaker", "desc": "Playmaker: The creative hub. Dominates key passes, assists, and chances created."}
        else:
            return {"style": "Creator", "desc": "Creator: Creative midfielder with high pass accuracy and progressive play."}
            
    if position in ['attack', 'forward']:
        if goals_per_90 >= 0.4:
            return {"style": "Finisher", "desc": "Finisher: Lethal goalscorer. High conversion rates and goals per 90."}
        elif dribbles_per_90 >= 1.8:
            return {"style": "Winger", "desc": "Winger: Flank specialist. Uses dribbling speed and ball progression to beat defenders."}
        elif height >= 185:
            return {"style": "Target Man", "desc": "Target Man: Physical focal point. High stature, shielding play, and active shot selection."}
        else:
            return {"style": "Creator", "desc": "Creator: Dynamic forward active in key passes, assists, and creating chances."}
            
    return {"style": "Balanced Player", "desc": "Balanced Player: Versatile player with balanced stats across categories."}

# ----------------- Dashboard Main Application -----------------

def main():
    # Sidebar styling and Navigation
    st.sidebar.markdown(
        "<h1 style='text-align: center; color: #1f77b4;'>🏆 FIFA World Cup</h1>", 
        unsafe_allow_html=True
    )
    st.sidebar.markdown("<h3 style='text-align: center;'>Analytics Dashboard</h3>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "Select Page",
        ["Home", "Player Analysis", "Team Analysis", "Position Analysis", "Tournament Analysis", "Playing Style Analysis", "Insights"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.caption("Data source: Transfermarkt Database")
    st.sidebar.caption("Mentored Portfolio Project")

    # 1. HOME PAGE
    if page == "Home":
        st.title("⚽ FIFA World Cup Player Performance Analytics")
        st.markdown(
            "Welcome to the **FIFA World Cup Player Performance Analytics Dashboard**. "
            "This project analyzes player metrics, match events, and national team structures across recent FIFA World Cups."
        )
        
        # Season Selector
        seasons = ["All World Cups", 2014, 2018, 2022]
        selected_season = st.selectbox("Select Tournament Year", seasons)
        
        # Build filter parameter
        # Map user selected calendar year to database season
        season_filter = None if selected_season == "All World Cups" else SEASON_MAP.get(selected_season, selected_season)
        
        # Fetch KPIs using SQL
        if season_filter:
            kpi_query = """
            SELECT 
                COUNT(DISTINCT a.player_id) as players,
                COUNT(DISTINCT a.player_club_id) as teams,
                SUM(a.goals) as goals,
                SUM(a.assists) as assists,
                ROUND(AVG(a.match_rating), 2) as avg_rating
            FROM appearances a
            JOIN games g ON a.game_id = g.game_id
            JOIN players p ON a.player_id = p.player_id
            WHERE g.season = :season AND p.is_verified = 1
            """
            kpi_df = db.run_query(engine, kpi_query, {"season": season_filter})
            
            # Fetch MVP
            mvp_query = """
            SELECT a.player_name, c.name as country, ROUND(AVG(a.match_rating), 2) as rating
            FROM appearances a
            JOIN games g ON a.game_id = g.game_id
            JOIN clubs c ON a.player_club_id = c.club_id
            JOIN players p ON a.player_id = p.player_id
            WHERE g.season = :season AND p.is_verified = 1
            GROUP BY a.player_id, a.player_name
            HAVING COUNT(a.appearance_id) >= 4
            ORDER BY rating DESC LIMIT 1
            """
            mvp_df = db.run_query(engine, mvp_query, {"season": season_filter})
        else:
            kpi_query = """
            SELECT 
                (SELECT COUNT(*) FROM players WHERE is_verified = 1) as players,
                (SELECT COUNT(*) FROM clubs) as teams,
                SUM(a.goals) as goals,
                SUM(a.assists) as assists,
                ROUND(AVG(a.match_rating), 2) as avg_rating
            FROM appearances a
            JOIN players p ON a.player_id = p.player_id
            WHERE p.is_verified = 1
            """
            kpi_df = db.run_query(engine, kpi_query)
            
            # Fetch MVP
            mvp_query = """
            SELECT a.player_name, c.name as country, ROUND(AVG(a.match_rating), 2) as rating
            FROM appearances a
            JOIN clubs c ON a.player_club_id = c.club_id
            JOIN players p ON a.player_id = p.player_id
            WHERE p.is_verified = 1
            GROUP BY a.player_id, a.player_name
            HAVING COUNT(a.appearance_id) >= 10
            ORDER BY rating DESC LIMIT 1
            """
            mvp_df = db.run_query(engine, mvp_query)
            
        # Draw KPIs
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        col1.metric("Total Players", int(kpi_df['players'].iloc[0]))
        col2.metric("Total Teams", int(kpi_df['teams'].iloc[0]))
        col3.metric("Total Goals", int(kpi_df['goals'].iloc[0]))
        col4.metric("Total Assists", int(kpi_df['assists'].iloc[0]))
        col5.metric("Avg Match Rating", f"{kpi_df['avg_rating'].iloc[0]:.2f}")
        
        if not mvp_df.empty:
            col6.metric("Tournament MVP", mvp_df['player_name'].iloc[0], f"{mvp_df['rating'].iloc[0]} Rating")
        else:
            col6.metric("Tournament MVP", "N/A")
            
        st.markdown("---")
        
        # Display top scorer and assist tables side by side
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("🔥 Top Goalscorers")
            df_scorers = db.get_top_scorers(engine, season=season_filter, limit=5)
            st.dataframe(df_scorers, use_container_width=True, hide_index=True)
            
        with col_right:
            st.subheader("🎯 Playmakers (Top Assists)")
            df_assists = db.get_top_assists(engine, season=season_filter, limit=5)
            st.dataframe(df_assists, use_container_width=True, hide_index=True)
            
        st.subheader("🌍 National Team Rankings (by Goals)")
        df_rankings = db.get_country_rankings(engine, season=season_filter)
        st.dataframe(df_rankings.head(10), use_container_width=True, hide_index=True)

    # 2. PLAYER ANALYSIS
    elif page == "Player Analysis":
        st.title("👤 Player Performance Analysis")
        st.markdown("Search and select a player to view their profile, detailed statistics, match ratings, and visual radar charts.")
        
        # Get list of players for dropdown
        players_list_df = db.run_query(engine, "SELECT player_id, name FROM players WHERE is_verified = 1 ORDER BY name")
        player_names = players_list_df['name'].tolist()
        
        selected_player_name = st.selectbox("Search Player", player_names)
        
        # Get ID
        selected_player_id = int(players_list_df[players_list_df['name'] == selected_player_name]['player_id'].iloc[0])
        
        # Query player details
        player_details = db.run_query(engine, "SELECT * FROM players WHERE player_id = :pid", {"pid": selected_player_id})
        
        # Query player stats
        stats_query = """
        SELECT 
            COUNT(appearance_id) as matches,
            SUM(goals) as goals,
            SUM(assists) as assists,
            SUM(minutes_played) as minutes,
            ROUND(AVG(match_rating), 2) as avg_rating,
            ROUND(AVG(pass_accuracy), 1) as pass_accuracy,
            SUM(passes_completed) as passes_completed,
            SUM(passes_attempted) as passes_attempted,
            SUM(key_passes) as key_passes,
            SUM(dribbles_completed) as dribbles_completed,
            SUM(tackles) as tackles,
            SUM(interceptions) as interceptions,
            SUM(blocks) as blocks,
            SUM(saves) as saves,
            ROUND(SUM(goals) * 90.0 / SUM(minutes_played), 2) as goals_per_90,
            ROUND(SUM(assists) * 90.0 / SUM(minutes_played), 2) as assists_per_90
        FROM appearances
        WHERE player_id = :pid
        """
        player_stats_df = db.run_query(engine, stats_query, {"pid": selected_player_id})
        
        if not player_details.empty and player_stats_df['matches'].iloc[0] > 0:
            row_det = player_details.iloc[0]
            row_stats = player_stats_df.iloc[0]
            
            # Display Player Card Info
            col_info1, col_info2, col_info3 = st.columns(3)
            with col_info1:
                st.markdown(f"### **{row_det['name']}**")
                st.write(f"**Citizenship**: {row_det['country_of_citizenship']}")
                st.write(f"**Position**: {row_det['position']} ({row_det['sub_position']})")
                st.write(f"**Height**: {int(row_det['height_in_cm'])} cm")
                
            with col_info2:
                st.markdown("### **Market Value**")
                st.write(f"**Current Value**: €{row_det['market_value_in_eur']/1000000:.1f}M")
                st.write(f"**Highest Value**: €{row_det['highest_market_value_in_eur']/1000000:.1f}M")
                st.write(f"**Preferred Foot**: {str(row_det['foot']).capitalize()}")
                
            with col_info3:
                # Classify Playing Style
                style_dict = classify_player_style(dict(row_stats), row_det['position'], row_det['height_in_cm'])
                st.markdown(f"### **Playing Style: {style_dict['style']}**")
                st.caption(style_dict['desc'])
                st.metric("Avg Match Rating", f"{row_stats['avg_rating']:.2f}")

            st.markdown("---")
            
            # Show stats KPIs
            col_kpi1, col_kpi2, col_kpi3, col_kpi4, col_kpi5 = st.columns(5)
            col_kpi1.metric("Matches Played", int(row_stats['matches']))
            col_kpi2.metric("Minutes Played", int(row_stats['minutes']))
            col_kpi3.metric("Goals / Assists", f"{int(row_stats['goals'])} / {int(row_stats['assists'])}")
            col_kpi4.metric("Goals per 90", f"{row_stats['goals_per_90']:.2f}")
            col_kpi5.metric("Pass Accuracy", f"{row_stats['pass_accuracy']:.1f}%", f"{int(row_stats['passes_completed'])}/{int(row_stats['passes_attempted'])} Passes", delta_color="off")
            
            st.markdown("---")
            
            # Radar & Trend side-by-side
            col_plot1, col_plot2 = st.columns([1, 1])
            with col_plot1:
                st.subheader("📊 Performance Radar")
                fig_radar = viz.plot_player_radar(dict(row_stats), row_det['name'])
                st.plotly_chart(fig_radar, use_container_width=True)
                
            with col_plot2:
                st.subheader("📈 Performance Trend")
                game_log_df = db.get_player_game_log(engine, selected_player_id)
                fig_trend = viz.plot_player_trend(game_log_df, row_det['name'])
                st.plotly_chart(fig_trend, use_container_width=True)
                
            st.subheader("📅 Match Game Log")
            st.dataframe(game_log_df, use_container_width=True, hide_index=True)
        else:
            st.error("No World Cup appearance records found for this player.")

    # 3. TEAM ANALYSIS
    elif page == "Team Analysis":
        st.title("⚔️ National Team Comparison")
        st.markdown("Compare the rosters, valuation, age profile, and goals performance of two national teams side-by-side.")
        
        # Get team lists
        teams_df = db.run_query(engine, "SELECT club_id, name FROM clubs ORDER BY name")
        team_names = teams_df['name'].tolist()
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            team1_name = st.selectbox("Select Team 1", team_names, index=0)
            t1_id = int(teams_df[teams_df['name'] == team1_name]['club_id'].iloc[0])
        with col_t2:
            # Default to second index if available
            team2_name = st.selectbox("Select Team 2", team_names, index=min(1, len(team_names)-1))
            t2_id = int(teams_df[teams_df['name'] == team2_name]['club_id'].iloc[0])
            
        # Get aggregate data for both teams
        team1_agg = db.run_query(engine, """
            SELECT 
                c.squad_size, c.average_age, c.total_market_value,
                SUM(a.goals) as goals, SUM(a.assists) as assists, AVG(a.match_rating) as avg_rating
            FROM clubs c
            LEFT JOIN appearances a ON c.club_id = a.player_club_id
            WHERE c.club_id = :id
            GROUP BY c.club_id
        """, {"id": t1_id})
        
        team2_agg = db.run_query(engine, """
            SELECT 
                c.squad_size, c.average_age, c.total_market_value,
                SUM(a.goals) as goals, SUM(a.assists) as assists, AVG(a.match_rating) as avg_rating
            FROM clubs c
            LEFT JOIN appearances a ON c.club_id = a.player_club_id
            WHERE c.club_id = :id
            GROUP BY c.club_id
        """, {"id": t2_id})
        
        if not team1_agg.empty and not team2_agg.empty:
            st.markdown("---")
            # Plot comparisons
            fig_compare = viz.plot_team_comparison(team1_agg, team2_agg, team1_name, team2_name)
            st.plotly_chart(fig_compare, use_container_width=True)
            st.markdown("---")
            
            # Bubble chart squad profile for Team 1
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                t1_players = db.run_query(engine, """
                    SELECT 
                        p.name, 
                        COALESCE(2026 - CAST(SUBSTR(p.date_of_birth, 1, 4) AS INTEGER), 27) AS age, 
                        p.position, 
                        p.market_value_in_eur, 
                        AVG(a.performance_index) as performance_index
                    FROM players p
                    JOIN appearances a ON p.player_id = a.player_id
                    WHERE p.national_team_id = :tid AND p.is_verified = 1
                    GROUP BY p.player_id, p.name, p.date_of_birth, p.position, p.market_value_in_eur
                """, {"tid": t1_id})
                if not t1_players.empty:
                    fig_bubble1 = viz.plot_squad_bubble_chart(t1_players, team1_name)
                    st.plotly_chart(fig_bubble1, use_container_width=True)
                else:
                    st.warning(f"No squad details found for {team1_name}")
                    
            with col_b2:
                t2_players = db.run_query(engine, """
                    SELECT 
                        p.name, 
                        COALESCE(2026 - CAST(SUBSTR(p.date_of_birth, 1, 4) AS INTEGER), 27) AS age, 
                        p.position, 
                        p.market_value_in_eur, 
                        AVG(a.performance_index) as performance_index
                    FROM players p
                    JOIN appearances a ON p.player_id = a.player_id
                    WHERE p.national_team_id = :tid AND p.is_verified = 1
                    GROUP BY p.player_id, p.name, p.date_of_birth, p.position, p.market_value_in_eur
                """, {"tid": t2_id})
                if not t2_players.empty:
                    fig_bubble2 = viz.plot_squad_bubble_chart(t2_players, team2_name)
                    st.plotly_chart(fig_bubble2, use_container_width=True)
                else:
                    st.warning(f"No squad details found for {team2_name}")
        else:
            st.error("Error retrieving metrics for selected teams.")

    # 4. POSITION ANALYSIS
    elif page == "Position Analysis":
        st.title("🏃 Player Position Comparative Analysis")
        st.markdown("Compare statistics, overall match ratings, and performance spreads across different roles.")
        
        # Load all appearances to generate position rating plots
        app_full_query = """
        SELECT a.match_rating, p.position, a.goals, a.assists, a.tackles, a.interceptions, a.blocks, a.saves, a.pass_accuracy, a.key_passes, a.dribbles_completed
        FROM appearances a
        JOIN players p ON a.player_id = p.player_id
        WHERE p.position IN ('Goalkeeper', 'Defender', 'Midfield', 'Attack') AND p.is_verified = 1
        """
        df_all_app = db.run_query(engine, app_full_query)
        
        if not df_all_app.empty:
            col_v1, col_v2 = st.columns([1, 1.2])
            with col_v1:
                st.pyplot(viz.plot_position_rating_boxplot(df_all_app))
            with col_v2:
                st.pyplot(viz.plot_metrics_correlation(df_all_app))
                
            st.markdown("---")
            st.subheader("🏆 Top Performers by Position")
            
            col_pos1, col_pos2 = st.columns(2)
            with col_pos1:
                st.markdown("#### **Best Goalkeepers**")
                st.dataframe(db.get_best_goalkeepers(engine, limit=5), use_container_width=True, hide_index=True)
                
                st.markdown("#### **Best Midfielders**")
                st.dataframe(db.get_best_midfielders(engine, limit=5), use_container_width=True, hide_index=True)
                
            with col_pos2:
                st.markdown("#### **Best Defenders**")
                st.dataframe(db.get_best_defenders(engine, limit=5), use_container_width=True, hide_index=True)
                
                st.markdown("#### **Best Forwards**")
                forwards_query = """
                SELECT 
                    a.player_name, 
                    c.name AS country, 
                    SUM(a.minutes_played) AS total_minutes,
                    SUM(a.goals) AS goals,
                    SUM(a.assists) AS assists,
                    ROUND(AVG(a.match_rating), 2) AS avg_rating
                FROM appearances a
                JOIN clubs c ON a.player_club_id = c.club_id
                JOIN players p ON a.player_id = p.player_id
                WHERE p.position = 'Attack' AND p.is_verified = 1
                GROUP BY a.player_id, a.player_name, c.name
                HAVING total_minutes >= 180
                ORDER BY avg_rating DESC
                LIMIT 5
                """
                df_forwards = db.run_query(engine, forwards_query)
                st.dataframe(df_forwards, use_container_width=True, hide_index=True)

    # 5. TOURNAMENT ANALYSIS
    elif page == "Tournament Analysis":
        st.title("📅 FIFA World Cup Tournament Analysis")
        st.markdown("Select a specific FIFA World Cup tournament year to analyze and compare aggregates.")
        
        # Tournament details
        tournaments = [2014, 2018, 2022]
        selected_year = st.selectbox("Select World Cup Year", tournaments)
        db_season = SEASON_MAP.get(selected_year, selected_year)
        
        # SQL queries for selected season
        tourney_agg = db.run_query(engine, """
            SELECT 
                COUNT(DISTINCT game_id) as matches,
                SUM(home_club_goals + away_club_goals) as goals,
                SUM(attendance) as attendance
            FROM games
            WHERE season = :season
        """, {"season": db_season})
        
        row_agg = tourney_agg.iloc[0]
        
        col_t1, col_t2, col_t3, col_t4 = st.columns(4)
        col_t1.metric("World Cup Edition", f"{selected_year}")
        col_t2.metric("Total Matches", int(row_agg['matches']))
        col_t3.metric("Goals Scored", int(row_agg['goals']), f"{row_agg['goals']/row_agg['matches']:.2f} per match")
        col_t4.metric("Total Attendance", f"{row_agg['attendance'] / 1000000:.2f}M", f"{int(row_agg['attendance']/row_agg['matches'])} avg")
        
        st.markdown("---")
        
        # Display season stats side by side
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.subheader(f"🔥 Top Goalscorers ({selected_year})")
            st.dataframe(db.get_top_scorers(engine, season=db_season, limit=5), use_container_width=True, hide_index=True)
            
            st.subheader(f"👶 Best Young Players ({selected_year})")
            st.dataframe(db.get_best_young_players(engine, season=db_season, limit=5), use_container_width=True, hide_index=True)
            
        with col_s2:
            st.subheader(f"🎯 Playmakers ({selected_year})")
            st.dataframe(db.get_top_assists(engine, season=db_season, limit=5), use_container_width=True, hide_index=True)
            
            st.subheader(f"🌍 Country Performance ({selected_year})")
            st.dataframe(db.get_country_rankings(engine, season=db_season).head(5), use_container_width=True, hide_index=True)

    # 6. PLAYING STYLE ANALYSIS
    elif page == "Playing Style Analysis":
        st.title("🎭 Player Playing Style Analysis (Rule-Based)")
        st.markdown("This page dynamically classifies players into playing styles based on their World Cup stats.")
        
        # Display rule breakdown
        with st.expander("ℹ️ Read Playing Style Rules and Heuristic Logic"):
            st.markdown("""
            Instead of black-box Machine Learning algorithms (which are hard to explain during job interviews), this system classifies players using **clear, transparent, rule-based football logic**:
            
            *   **Finisher**: Strikers (Attackers) with a lethal scoring rate (`goals_per_90 >= 0.4`).
            *   **Target Man**: Statured attackers (`height >= 185 cm`) who play as physical focal points.
            *   **Winger**: Attackers specialized in progression (`dribbles_completed_per_90 >= 1.8`).
            *   **Playmaker**: Midfielders who dominate playmaking (`assists_per_90 >= 0.25` or `key_passes_per_90 >= 1.5`).
            *   **Box-to-Box Midfielder**: Midfielders who do it all: key passes (`key_passes_per_90 >= 0.8`) and tackles (`tackles_per_90 >= 1.5`).
            *   **Ball Winner**: Midfielders specialized in defensive work (`tackles_per_90 >= 2.0`).
            *   **Defensive Rock**: Defenders highly active in defensive parameters (`tackles_per_90 >= 2.0` or `blocks >= 1.0`).
            *   **Ball Playing Defender**: Defenders with clean distribution from the back.
            *   **Traditional Goalkeeper**: Specialized shot stopper.
            """)
            
        # Select player to classify
        players_list_df = db.run_query(engine, "SELECT player_id, name FROM players WHERE is_verified = 1 ORDER BY name")
        player_names = players_list_df['name'].tolist()
        selected_p = st.selectbox("Select Player to Classify", player_names)
        
        pid = int(players_list_df[players_list_df['name'] == selected_p]['player_id'].iloc[0])
        
        # Fetch stats
        p_details = db.run_query(engine, "SELECT * FROM players WHERE player_id = :pid", {"pid": pid}).iloc[0]
        p_stats = db.run_query(engine, """
            SELECT 
                SUM(goals) as goals, SUM(assists) as assists, SUM(minutes_played) as minutes,
                SUM(key_passes) as key_passes, SUM(tackles) as tackles, 
                SUM(interceptions) as interceptions, SUM(blocks) as blocks, 
                SUM(dribbles_completed) as dribbles_completed
            FROM appearances WHERE player_id = :pid
        """, {"pid": pid}).iloc[0]
        
        style = classify_player_style(dict(p_stats), p_details['position'], p_details['height_in_cm'])
        
        # Display results
        st.markdown(f"## **Playing Style: {style['style']}**")
        st.info(style['desc'])
        
        # Show metrics used in decision
        mins = int(p_stats['minutes'])
        col_r1, col_r2, col_r3, col_r4, col_r5 = st.columns(5)
        col_r1.metric("Goals / 90", f"{(p_stats['goals']*90.0)/mins:.2f}" if mins > 0 else "0.00")
        col_r2.metric("Assists / 90", f"{(p_stats['assists']*90.0)/mins:.2f}" if mins > 0 else "0.00")
        col_r3.metric("Key Passes / 90", f"{(p_stats['key_passes']*90.0)/mins:.2f}" if mins > 0 else "0.00")
        col_r4.metric("Tackles / 90", f"{(p_stats['tackles']*90.0)/mins:.2f}" if mins > 0 else "0.00")
        col_r5.metric("Dribbles / 90", f"{(p_stats['dribbles_completed']*90.0)/mins:.2f}" if mins > 0 else "0.00")

    # 7. INSIGHTS
    elif page == "Insights":
        st.title("💡 Analytical Insights")
        st.markdown("Advanced analytical findings extracted from the FIFA World Cup database.")
        
        col_ins1, col_ins2 = st.columns(2)
        
        with col_ins1:
            st.markdown("### 🏆 Top Stats Insights")
            
            # Highest scoring country
            hsc = db.run_query(engine, """
                SELECT c.name, SUM(a.goals) AS total_goals 
                FROM appearances a 
                JOIN clubs c ON a.player_club_id = c.club_id 
                GROUP BY c.club_id, c.name 
                ORDER BY total_goals DESC LIMIT 1
            """).iloc[0]
            st.write(f"🌐 **Highest Scoring Country**: **{hsc['name']}** with **{int(hsc['total_goals'])} goals**.")
            
            # Most efficient striker (goals per shot)
            mes = db.run_query(engine, """
                SELECT a.player_name, c.name AS country, SUM(a.goals) AS goals, SUM(a.shots) AS shots, 
                       ROUND(SUM(a.goals) * 1.0 / SUM(a.shots), 2) AS efficiency 
                FROM appearances a 
                JOIN clubs c ON a.player_club_id = c.club_id 
                JOIN players p ON a.player_id = p.player_id
                WHERE p.is_verified = 1
                GROUP BY a.player_id, a.player_name, c.name 
                HAVING SUM(a.shots) >= 8
                ORDER BY efficiency DESC LIMIT 1
            """)
            if not mes.empty:
                st.write(f"🎯 **Most Efficient Attacker**: **{mes['player_name'].iloc[0]}** ({mes['country'].iloc[0]}) "
                         f"with **{mes['efficiency'].iloc[0]} goals per shot** ({int(mes['goals'].iloc[0])} goals from {int(mes['shots'].iloc[0])} shots).")
            
            # Value player (Performance index to Market value ratio)
            mvp_val = db.run_query(engine, """
                SELECT p.name, c.name as country, p.market_value_in_eur, ROUND(AVG(a.performance_index), 1) as avg_index, 
                       ROUND(AVG(a.performance_index) * 1000000.0 / p.market_value_in_eur, 2) as value_ratio 
                FROM players p 
                JOIN appearances a ON p.player_id = a.player_id 
                JOIN clubs c ON a.player_club_id = c.club_id 
                WHERE p.market_value_in_eur > 0 AND p.is_verified = 1
                GROUP BY p.player_id, p.name, c.name, p.market_value_in_eur 
                HAVING SUM(a.minutes_played) >= 180 
                ORDER BY value_ratio DESC LIMIT 1
            """)
            if not mvp_val.empty:
                st.write(f"💎 **Best Value-for-Money Player**: **{mvp_val['name'].iloc[0]}** ({mvp_val['country'].iloc[0]}). "
                         f"Market Value: €{mvp_val['market_value_in_eur'].iloc[0]/1000000:.2f}M, "
                         f"Avg Performance Index: **{mvp_val['avg_index'].iloc[0]}**.")
                
            # Squad age records
            youngest_s = db.run_query(engine, "SELECT name, average_age FROM clubs WHERE squad_size > 0 ORDER BY average_age ASC LIMIT 1").iloc[0]
            oldest_s = db.run_query(engine, "SELECT name, average_age FROM clubs WHERE squad_size > 0 ORDER BY average_age DESC LIMIT 1").iloc[0]
            st.write(f"👶 **Youngest Squad**: **{youngest_s['name']}** (Average Age: {youngest_s['average_age']:.1f} years).")
            st.write(f"🧓 **Oldest Squad**: **{oldest_s['name']}** (Average Age: {oldest_s['average_age']:.1f} years).")
            
            # Highest rated position
            hrp = db.run_query(engine, """
                SELECT p.position, ROUND(AVG(a.match_rating), 2) as avg_rating 
                FROM appearances a 
                JOIN players p ON a.player_id = p.player_id 
                WHERE p.is_verified = 1
                GROUP BY p.position 
                ORDER BY avg_rating DESC
            """)
            st.write(f"⚡ **Highest Rated Position Overall**: **{hrp['position'].iloc[0]}** (Average Rating: {hrp['avg_rating'].iloc[0]}/10.0).")
            
        with col_ins2:
            st.markdown("### ⭐ Exceptional Single-Match Performances")
            exceptional = db.run_query(engine, """
                SELECT a.player_name, c.name as country, g.home_club_name || ' vs ' || g.away_club_name as match_name, 
                       a.goals, a.assists, a.match_rating 
                FROM appearances a 
                JOIN games g ON a.game_id = g.game_id 
                JOIN clubs c ON a.player_club_id = c.club_id 
                JOIN players p ON a.player_id = p.player_id
                WHERE p.is_verified = 1
                ORDER BY a.match_rating DESC, a.goals DESC LIMIT 5
            """)
            st.dataframe(exceptional, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()
