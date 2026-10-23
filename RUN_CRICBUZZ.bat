@echo off
setlocal
cd /d "%~dp0"
echo ============================================
echo Cricbuzz LiveStats - clean local launch
echo ============================================
echo.
where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3.10 or newer and enable Add Python to PATH.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  python -m venv .venv
  if errorlevel 1 goto :error
)
echo Installing/updating dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :error
echo.
echo Starting Cricbuzz LiveStats at http://localhost:8505
echo Keep this window open while using the app.
echo If 8505 is occupied, close its existing server or edit this file's port.
start "" http://localhost:8505
".venv\Scripts\python.exe" -m streamlit run app.py --server.port 8505 --server.address 127.0.0.1
goto :end
:error
echo.
echo Setup failed. Read the error above.
pause
exit /b 1
:end
endlocal
