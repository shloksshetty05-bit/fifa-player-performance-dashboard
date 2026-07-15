"""
Streamlit Dashboard Entrypoint
------------------------------
Configures the dashboard layout, sidebar navigation, and routes to individual analysis pages.
"""

import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="FIFA World Cup Player Performance Analytics",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.sidebar.title("🏆 FIFA World Cup Analytics")
    st.sidebar.write("Player Performance Dashboard")
    
    # Navigation Selection
    page = st.sidebar.radio(
        "Navigate",
        ["Home", "Player Analysis", "Team Analysis", "Position Analysis", "Tournament Analysis", "Playing Style Analysis", "Insights"]
    )
    
    st.title(f"FIFA World Cup Analytics - {page}")
    st.write("Welcome to the Player Performance Dashboard. This section is currently under development.")

if __name__ == "__main__":
    main()
