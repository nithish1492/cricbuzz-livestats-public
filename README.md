# Cricbuzz LiveStats: Real-Time Cricket Insights & SQL-Based Analytics

Built to follow the internship brief in `Cricbuzz.docx`: Python, SQL/SQLite, Streamlit, JSON, REST API integration, live matches, player stats, 25 SQL practice questions, CRUD, and documentation.

## Setup on Windows / VS Code

1. Extract the ZIP and open the extracted folder in VS Code.
2. In the terminal, run:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   Copy-Item .env.example .env
   ```
3. Open `.env`, paste your own RapidAPI key after `CRICBUZZ_API_KEY=`, and save. Never share the key or commit `.env`.
4. Run `python -m streamlit run app.py`.
5. In the sidebar, open **Live Matches** to verify API access.
6. Open **Data Import → Fetch & save live matches** to populate SQLite.
7. Select a match ID and try importing its scorecard; if the optional scorecard endpoint returns an error, verify the exact path in the RapidAPI Python snippet and update `CRICBUZZ_SCORECARD_PATH` in `.env`.
8. Use **Top Player Stats**, **SQL Queries Analytics**, **CRUD Operations**, **Series Explorer**, and **Database Explorer**.

## Verified routes

Verified using the user's RapidAPI responses:
- `GET /matches/v1/live` — HTTP 200.
- `GET /mcenter/v1/{match_id}/livescore` — HTTP 200.

The scorecard and series routes are configurable examples and must be verified in the RapidAPI playground for your subscription. The app reports errors rather than inventing results.

## Features
- Live match categories, teams, scores, status, venue, search and category filters.
- Match-detail live score request.
- SQLite schema for players, matches, venues, series, and player-match stats.
- Data import and database explorer.
- Top runs and wickets from imported scorecard rows.
- 25 SQL practice questions based on the supplied brief.
- Custom read-only SQL interface.
- Form-based CRUD for players and matches.
- API key safety, exception handling, indexes, comments and parser test.

## Data limitations
The current confirmed live endpoint does not supply a full career dataset. Player career totals, venue capacity, full historical results, toss outcomes and partnership-level analysis will only be accurate when the appropriate source data is imported. Queries dependent on unavailable fields may return no rows. No synthetic cricket results are included.

## Folder layout
`main.py`, `app.py`, `app_pages/`, `utils/`, `tests/`, `data/`, `notebooks/`, `.env.example`, `requirements.txt`.


## Troubleshooting: blank screen after selecting a sidebar page

1. Stop every Cricbuzz/Streamlit terminal with `Ctrl+C` (do not close the terminal before stopping it).
2. Close old tabs for `localhost:8501`, `localhost:8503`, and `localhost:8504`.
3. Double-click `RUN_CRICBUZZ.bat` in this project folder. It creates `.venv` if needed, installs the listed requirements, and starts a fresh server on port `8505`.
4. Use the newly opened `http://localhost:8505` tab. Keep the command window open.
5. If the page goes blank, press `Ctrl+Shift+R`. Do not use Back/Forward to return to the app while diagnosing; the browser console in the supplied screenshots reports that the page entered the Back-Forward Cache and the Streamlit WebSocket failed.
6. If it still blanks, in DevTools open **Network**, click the `stream` WebSocket request, and share its **Messages** and **Headers** tabs plus the last lines from the RUN_CRICBUZZ terminal. Do not share your `.env` file or API key.

The project sets WebSocket compression off in `.streamlit/config.toml` as a compatibility workaround. A successful `/_stcore/health` response only verifies that the HTTP health endpoint is up; it does not prove that the browser's Streamlit WebSocket connection is working.
