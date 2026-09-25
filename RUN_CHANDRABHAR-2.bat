@echo off
REM CHANDRABHAR-2 -- Windows quick-start launcher
REM Installs/updates dependencies, then launches the Streamlit dashboard.
cd /d "%~dp0"
python -m pip install -r requirements.txt
python -m streamlit run dashboard.py
pause
