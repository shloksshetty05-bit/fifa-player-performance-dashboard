@echo off
echo Starting FIFA World Cup Performance Dashboard...
cd /d "c:\Users\shlok\OneDrive\Desktop\data analysis\player performance dashboard\fifa-player-performance-dashboard"
call venv\Scripts\activate.bat
python -m streamlit run app.py
pause
