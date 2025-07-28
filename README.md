# Chinook Dashboard — SQL-Driven Business Intelligence in Dash

An interactive dashboard that surfaces revenue insights, retention patterns, and genre/artist performance from the [Chinook](https://github.com/lerocha/chinook-database) music-store dataset. Built with Python, Dash, DuckDB, and Plotly to illustrate a scalable analytics workflow.

## Key Features

- SQL-powered KPIs via DuckDB (joins, CTEs, windows)  
- Reactive filters: date range, genre, artist, country  
- Query staging with temporary tables for reduced compute load  
- Metadata enrichment through pre-built artist/genre catalogs  
- Modular Dash pages—each with KPI cards, plots, tables, downloads  
- Light/dark theming via Dash Mantine Components  
- Retention decay curves and cohort heatmaps  
- Narrative Insights panel for executive summaries  

## Tech Stack

| Tool                          | Purpose                                        |
|-------------------------------|------------------------------------------------|
| Python 3.11.8                 | Core language                                 |
| Dash 3.1.1                    | Web framework for interactive UI              |
| dash_mantine_components 2.1.0 | Theming, layout, and UI components            |
| DuckDB 1.3.2                  | Embedded SQL OLAP engine (read-only mode)     |
| Plotly 6.2.0                  | Interactive visualizations                     |
| Flask-Caching                 | Function memoization and result caching        |
| Gunicorn                      | WSGI HTTP server for deployment                |
| Render                        | Cloud hosting (free tier)   

## Repository Structure
```
├── app.py
├── config.py
├── assets/
│   ├── styles.css
│   ├── theme.js
│   └── markdown/
│   │   ├── executive_summary.md
│   │   ├── next_steps.md
│   │   ├── strategic_opportunities.md
│   │   └── under_the_hood.md
├── data/
│   ├──chinook.duckdb
│   └── last_commit_cache.json
├── callbacks/
│   ├── data_callbacks.py
│   ├── filter_callbacks.py
│   ├── layout_callbacks.py
│   ├── routing_callbacks.py
│   ├── sidebar_callbacks.py
│   └── theme_callbacks.py
├── components/
│   ├── __init__.py
│   ├── filters.py
│   ├── header.py
│   ├── layout.py
│   └── sidebar.py
├── pages/
│   ├── timeseries/
│   │   ├── __init__.py
│   │   ├── helpers.py
│   │   ├── layout.py
│   │   └── callbacks.py
│   ├── geo/
│   │   ├── __init__.py
│   │   ├── helpers.py
│   │   ├── layout.py
│   │   └── callbacks.py
│   ├── group/
│   │   ├── __init__.py
│   │   ├── helpers.py
│   │   ├── layout.py
│   │   └── callbacks.py
│   ├── retention/
│   │   ├── __init__.py
│   │   ├── helpers.py
│   │   ├── layout.py
│   │   └── callbacks.py
│   ├── insights/
│   │   ├── __init__.py
│   │   ├── helpers.py
│   │   ├── layout.py
│   │   └── callbacks.py
│   ├── overview/
│   │   ├── __init__.py
│   │   ├── helpers.py
│   │   ├── layout.py
│   │   └── callbacks.py
│   └── coming_soon.py
├── services/
│   ├── db.py
│   ├── sql_filters.py
│   ├── sql_core.py
│   ├── metadata.py
│   ├── logging_utils.py
│   ├── display_utils.py
│   ├── cache_config.py
│   ├── cached_funs.py
│   └── kpis/
│   │   ├── __init__.py
│   │   ├── core.py
│   │   ├── group.py
│   │   ├── retention.py
│   │   └── shared.py
├── requirements.txt
├── LICENSE
└── README.md
```
## Installation

Clone the repo and install dependencies:

```bash
git clone https://github.com/corvidfox/chinook-dashboard-pydash.git
cd chinook-dashboard-pydash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Create a `.env` file or set these environment variables:

- `GITHUB_TOKEN` — GitHub API token for commit-date retrieval  
- `DEMO` — `true` for demo mode, `false` for local development  
- `PYTHON_VERSION` — should match `3.11.8`  

## Running Locally

```bash
export FLASK_ENV=development
gunicorn app:server --reload --workers 1
```

Then open <http://localhost:8000> in your browser.

## Deployment

This app is configured to run on Render with Gunicorn:

1. Connect the GitHub repository in your Render dashboard.  
2. Set environment variables (`GITHUB_TOKEN`, `DEMO`, `PYTHON_VERSION`).  
3. Use the start command in Render (or a `Procfile`):
   ```bash
   gunicorn app:server --workers=4 --threads=2 --timeout=120
    ```

## Future Development

- Toggle between absolute and normalized metrics (e.g., revenue per customer)  
- Automated narrative summaries of filtered data  
- KPI alerting and anomaly detection  
- Data partitioning for high-volume scaling  
- Enhanced mobile responsiveness and animated transitions  

## License

This project is licensed under the MIT License.

## Author

Developed by a healthcare researcher and bioinformatician, applying analytical rigor and storytelling to business intelligence workflows.  
For more projects, visit [CorvidFox.github.io](https://corvidfox.github.io/)
