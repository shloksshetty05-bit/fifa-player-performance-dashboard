# FIFA World Cup Player Performance Analytics Dashboard

An end-to-end data engineering and interactive analytics dashboard built to analyze player and team performance across FIFA World Cups. 

This project demonstrates strong capabilities in Python data pipelines, deterministic data simulation, SQLite relational database design using SQLAlchemy, raw SQL analytical reporting, and modern web application development with Streamlit.

---

## 🚀 Key Features

1.  **Automated Data Pipeline**: Download compressed Transfermarkt player datasets directly from source mirrors, filter for FIFA World Cups (`FIWC` competition ID), handle missing values, standardize names (strip accents/diacritics), and generate processed dataframes.
2.  **Deterministic Feature Engineering**:
    *   Calculates per-90 metrics (goals per 90, assists per 90, goal contributions).
    *   Simulates detailed in-game statistics (tackles, passes, saves, shots on target) tailored by player position. A custom seeding algorithm based on `player_id` and `game_id` ensures that simulated stats are identical across runs.
    *   Computes composite metrics: *Defensive Contribution Score*, *Attacking Contribution Score*, and a *Performance Index*.
    *   Generates a rule-based *Match Rating (1.0–10.0)* modeled after professional football scoring websites (e.g., SofaScore).
3.  **Relational SQL Database**: Stores clean tables in SQLite (`clubs`, `players`, `games`, `appearances`) mapped using SQLAlchemy ORM.
4.  **SQL Analytical Query Engine**: Uses raw SQL queries to pull high-level analytical reports for top scorers, top playmakers, position awards, and tournament stats.
5.  **Interactive Streamlit Dashboard**:
    *   **Home**: KPIs (Total Goals, Assists, MVP) and top scorers.
    *   **Player Analysis**: Search player logs, rating timeline trends, and interactive Plotly radar charts.
    *   **Team Analysis**: Head-to-head national team comparisons and squad valuation structure bubble charts.
    *   **Position Analysis**: Comparative boxplots and correlation matrices.
    *   **Tournament Deep-Dive**: Filter by World Cup year (2014, 2018, 2022) to view award winners and country stats.
    *   **Playing Style classification**: Custom rule-based classification explaining player types (Finisher, Winger, Box-to-Box, Defensive Rock, etc.).
    *   **Insights**: Summary of data anomalies and exceptional single-match performances.

---

## 🛠️ Tech Stack

*   **Language**: Python
*   **Data Analysis**: Pandas, NumPy
*   **Database & ORM**: SQLite, SQLAlchemy
*   **Visualizations**: Matplotlib, Seaborn, Plotly
*   **Web Framework**: Streamlit
*   **Text Cleaning**: Unidecode, unicodedata

---

## 📂 Project Directory Structure

```
fifa-player-performance-dashboard/
│
├── data/
│   ├── raw/                 # Downloaded raw CSV data (World Cup subset only)
│   └── processed/           # Processed and engineered datasets
│
├── database/
│   └── fifa_worldcup.db     # Clean SQLite database file
│
├── src/
│   ├── __init__.py          # Python package initializer
│   ├── preprocessing.py     # Stage 1: Data downloading, validation, cleaning
│   ├── feature_engineering.py # Stage 2: Metric calculations and simulations
│   ├── sql_queries.py       # Stage 3: Database creation and SQL query library
│   └── visualizations.py    # Stage 4: Matplotlib, Seaborn, and Plotly functions
│
├── app.py                   # Stage 5: Multi-page Streamlit Dashboard
├── verify_pipeline.py       # Pipeline verification checks and tests
├── requirements.txt         # Package dependencies
├── README.md                # Project documentation
├── LICENSE                  # MIT License
└── .gitignore               # Ignored venv, raw data, and DB binaries
```

---

## 📥 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/fifa-player-performance-dashboard.git
cd fifa-player-performance-dashboard
```

### 2. Set Up a Virtual Environment
Create and activate a Python virtual environment to keep dependencies isolated:
```bash
# On Windows (Command Prompt/PowerShell)
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Data Pipeline
Execute the pipeline stages to download data, engineer metrics, and populate the database:
```bash
# Run data preprocessing
python src/preprocessing.py

# Generate advanced metrics and simulations
python src/feature_engineering.py

# Create database and load records
python src/sql_queries.py
```

### 5. Verify the Pipeline
Run the verification check script to ensure all files, database tables, and analytical queries are set up correctly:
```bash
python verify_pipeline.py
```

### 6. Start the Dashboard
Launch the interactive Streamlit server:
```bash
streamlit run app.py
```
Open your browser and navigate to `http://localhost:8501` to view the dashboard.

*(Note: The application has a **self-healing** setup. If you run `streamlit run app.py` directly, it will detect if the SQLite database is missing and automatically run the full downloading/processing pipeline).*

---

## 📊 SQL Query Examples

Below are examples of raw SQL queries implemented in `src/sql_queries.py` to extract tournament metrics:

### 1. Top Scorers Query
```sql
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
GROUP BY a.player_id, a.player_name, c.name
ORDER BY goals DESC, assists DESC, minutes_played ASC
LIMIT 10;
```

### 2. Best Young Players Query (Aged 23 or under at tournament time)
```sql
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
WHERE (g.season - CAST(SUBSTR(p.date_of_birth, 1, 4) AS INTEGER)) <= 23
GROUP BY a.player_id, a.player_name, c.name, p.position
HAVING total_minutes >= 90
ORDER BY avg_rating DESC, goals DESC;
```

---

## 🔮 Future Improvements

*   **Machine Learning Integration**: Implement simple classification models (e.g., Decision Trees or Random Forests) to classify playing styles and compare them with the rule-based heuristic.
*   **Predictive Analytics**: Build basic models to forecast a team's probability of progression in knockout matches based on squad average age and performance indices.
*   **Expanded Datasets**: Incorporate other international tournaments (e.g., UEFA European Championship, Copa América) to compare national team profiles across continents.

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
