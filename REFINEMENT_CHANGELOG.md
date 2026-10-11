# Refinement Branch Audit & Feature Changelog

This document tracks all changes made on the `refinement` branch. Any new client app (Mobile or Desktop) can consult this log to match features and API schemas.

---

## 1. Analytics & Reports Engine

### Backend Changes:
* **Endpoints added**:
  * `GET /api/reports/types`: Returns available report types (`completion_trends`, `tag_distribution`, `daily_velocity`, `task_creation_report`, etc.).
  * `POST /api/reports/generate`: Generates data breakdown, velocity metrics, KPI summaries, and chart datasets. Supports parameters:
    * `report_type` (string)
    * `account_id` (string)
    * `list_id` (string / 'all')
    * `tag` (string)
    * `start_date` (YYYY-MM-DD)
    * `end_date` (YYYY-MM-DD)
  * `POST /api/reports/export`: Exports report data in `csv`, `json`, or `txt` formats.
* **Core Logic**:
  * [task_creation_report.py](file:///run/media/sirus/workspace/projects/gtasks-terminal/gtasks_cli/src/gtasks_cli/reports/task_creation_report.py): Enhanced date window handling, timezone normalization, and velocity calculations.
  * [services/data_manager.py](file:///run/media/sirus/workspace/projects/gtasks-terminal/gtasks_dashboard/services/data_manager.py): Added report computation methods (`generate_report_data`, metric cards aggregation).

### Frontend Changes:
* **UI View**: Added dedicated Reports View section in [dashboard.html](file:///run/media/sirus/workspace/projects/gtasks-terminal/gtasks_dashboard/templates/dashboard.html).
* **Styles & Script**:
  * [static/css/reports.css](file:///run/media/sirus/workspace/projects/gtasks-terminal/gtasks_dashboard/static/css/reports.css)
  * [static/js/reports.js](file:///run/media/sirus/workspace/projects/gtasks-terminal/gtasks_dashboard/static/js/reports.js)
* **Metrics Cards**: Completed Tasks, Completion Rate, Daily Velocity, Days Analyzed.
* **Charts**: Trajectory & Velocity line chart, Task Distribution doughnut chart using Chart.js / canvas.
* **Export Actions**: Quick download buttons for CSV, JSON, TXT, and Copy to Clipboard.

---

## 2. Sync & Authentication Portability

### Google Tasks Token Fallback & Remote In-App OAuth:
* **Commit**: `b5e0f4d` and subsequent updates
* **Changes**:
  * Supports dual credential paths: `token.pickle` and `token.json`.
  * Enables headless / cloud portability without depending strictly on Python pickle serialization.
  * Added non-blocking background sync queue for task completion triggers from the web UI / REST API.
  * **Remote OAuth Start**: `POST /api/auth/google/start` dynamically resolves `redirect_uri` against the incoming request Host header (supports localhost, LAN IP, or public domain HTTPS).
  * **Remote OAuth Callback**: `GET /api/auth/google/callback` captures Google's authorization code, exchanges it on the server, provisions `token.json` and `tasks.db`, triggers initial sync, and renders a clean confirmation page.
  * **Direct Token Import**: `POST /api/auth/tokens/import` allows direct programmatic injection of token JSON over REST.

---

## 3. Data Schema & Date Handling Robustness

### Timestamp Fallbacks:
* When a task does not have explicit `updated` or `completed` timestamps from Google Tasks API, `data_manager.py` falls back gracefully to `created_at` or `due` date.
* Eliminates timezone conversion crashes (`TypeError` / `ValueError` on varying ISO formats).

---

## 4. UI Filters & Multi-Account Enhancements

### Sticky Sidebar & Filter Drawer:
* **Commit**: `08fd8b2` and `f39e6e6`
* **Changes**:
  * Responsive mobile top navigation and filter drawer.
  * Multiselect status filter with persistent settings in `localStorage`.
  * Default date window filter preset to past 31 days with instant reset button.
  * Fullscreen JSON viewing and editing modal (`88cf3a3`).
