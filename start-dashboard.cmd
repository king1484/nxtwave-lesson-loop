@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m streamlit run app.py
) else (
    python -m streamlit run app.py
)
if errorlevel 1 (
    echo.
    echo Install the dashboard requirements in your Python environment:
    echo python -m pip install -r requirements-ui.txt
    echo.
    pause
)
