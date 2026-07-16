# World Cup Player Performance Dashboard

A dashboard for looking at player and team stats across different FIFA World Cups (2006 to 2022). It handles raw Transfermarkt data, does some basic cleaning, and provides an interactive Streamlit UI to check out player profiles and comparisons.

---

## 🏃 What it does

1. **Data Pipeline**: Downloads Transfermarkt player data, filters it down to World Cup games, cleans up names (remover of accents and diacritics), and handles missing values.
2. **Stat Simulations**: Fills in missing historical match stats (like passes, tackles, and saves for older cups) using a position-based simulation so we have complete records.
3. **Database**: Saves clean tables in a local SQLite file (`clubs`, `players`, `games`, `appearances`) using SQLAlchemy.
4. **Interactive Dashboard**:
    * **Home**: Tournament KPIs and overall top scorers.
    * **Player Analysis**: Profiles, rating charts, and Plotly radar charts to compare players.
    * **Team Analysis**: National team matchups and squad valuation charts.
    * **Position Analysis**: Compare match ratings and stat correlations by role.
    * **Tournament Look-up**: View stats, awards, and country rankings for specific World Cup years (2014, 2018, 2022).

---

## 🛠️ Tools Used

* **Language**: Python
* **Data Processing**: Pandas, NumPy
* **Database**: SQLite, SQLAlchemy
* **Visualizations**: Plotly, Matplotlib, Seaborn
* **App Framework**: Streamlit

---

## 📂 Folders

* `data/raw/` - Compressed Transfermarkt data subset
* `data/processed/` - Processed CSV files
* `database/` - SQLite database
* `src/` - Processing scripts (preprocessing, features, queries, charts)
* `app.py` - Streamlit application entry point
* `verify_pipeline.py` - Quick script to check if the database and queries work

---

## 🚀 Setting it up

### 1. Clone the project
```bash
git clone https://github.com/yourusername/fifa-player-performance-dashboard.git
cd fifa-player-performance-dashboard
```

### 2. Set up virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install requirements
```bash
pip install -r requirements.txt
```

### 4. Build database and run
```bash
# Run the pipeline scripts in order:
python src/preprocessing.py
python src/feature_engineering.py
python src/sql_queries.py

# Verify it works:
python verify_pipeline.py

# Launch the app:
streamlit run app.py
```
*(Note: If you run `streamlit run app.py` directly, it will detect if the database is missing and automatically build it).*

---

## 📄 License
MIT
