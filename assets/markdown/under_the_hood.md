### Under the Hood

This dashboard was built to showcase a scalable, SQL-driven BI workflow on the Chinook music-store dataset. While the Chinook dataset contains only hundreds of records, the app is designed to handle much larger volumes with reactive filters, modular architecture, and optimized SQL queries.

#### Data Pipeline & ETL

- **Source:** A static DuckDB file (`/data/chinook.duckdb`) stored in the repo and opened in read-only mode.  
- **Commit Tracking:** `last_commit_cache.json` holds the timestamp of the latest GitHub commit, refreshed via a GitHub API call.  
- **ETL Logic:** SQL queries use joins, CTEs, and window functions to compute KPIs like revenue, customer retention, and genre performance.
- **Filter Validation:** All filters (date range, genre, artist, country, metric) are reactive and validated. No selection defaults to the full dataset.
- **Filter Staging:**  
  - Services in `services/sql_filters.py` build a temporary `filtered_invoices` table (filtered by genre, artist, country but not date) to shrink downstream query scopes.  
  - A date-range filter is applied later in each query to preserve temporal integrity.  
- **Catalog Mapping:** A pre-joined reference table of the full genre/artist catalog is used to annotate filtered results with metadata like track counts and artist scope.
- **Caching & Debounce:** 
  - Flask-caching is configured in `services/cache_config.py`.  
  - Heavy functions are memoized in `services/cached_funs.py` to eliminate redundant SQL executions.  

#### KPI & Visualization Engine

- **KPI Cards:** Each module begins with a row of KPI cards, built using reusable helper functions in `services/display_utils.py` and styled dynamically through Dash Mantine's theming system. 
- **Plots:** Visualizations include time-series trends, stacked bar plots, choropleths, and retention curves, all rendered with Plotly.
- **Tables:** Scrollable data tables are paired with download buttons for CSV export, enabling deeper exploration and reporting.

#### Modular Architecture

- `app.py` & `config.py`: Launch point and environment setup (e.g., GitHub token, demo mode).  
- `/assets.py`: Hosts custom JavaScript (clientside callbacks, theme toggle) and global CSS.  
- `/callbacks`: Application-wide callbacks (e.g., theme switch, page routing, and shared data callbacks).  
- `/components`: Reusable building blocks—filters, header, layout, sidebar.  
- `/pages`: Each dashboard tab lives here with its own `helpers.py`, `layout.py`, and `callbacks.py`.  
  - The group module handles both genre- and artist-level performance using shared routines.  
- `/services`: Shared utilities for DB connection (`db.py`), SQL assembly, metadata enrichment, logging, display formatting, and caching.  

#### Theming & UX

- **Dash Mantine Components:** Unified light/dark themes via a `MantineProvider`.  
- **Auto-Detect & Toggle:** Respects system preference; manual switch stored in clientside state (`assets/themes.js`).  
- **Loaders & Skeletons:** Mantine spinners and skeleton loaders provide graceful feedback during data fetch and rerender.  
- **CSS Transitions:** Smooth animations for theme switching and layout changes.  

#### Deployment & Hosting

- **Platform:** Render (free tier) with GitHub integration.  
- **Server:** Gunicorn orchestrates app processes.  
- **Environment Variables:** 
  - `GITHUB_TOKEN` for commit-date API calls  
  - `PYTHON_VERSION` sets the full python version for the application in Render 

#### Ideas for Further Development

This dashboard was designed to be lightweight, responsive, and modular, but there are several areas where deeper functionality could be added if needed:

- Toggle between absolute and normalized metrics (e.g., revenue per customer).  
- Narrative module to auto-generate textual summaries of filtered KPIs.  
- Alerting and anomaly detection on KPI thresholds.  
- Dynamic data partitioning (by time/region) for multi-user and high-volume scaling.  
- Enhanced mobile responsiveness and animated transitions.  

While this project is scoped for portfolio clarity, it’s designed with scalability in mind, offering room to grow if new datasets, use cases, or audience needs arise.

---

This dashboard was built by a healthcare researcher with a background in bioinformatics and nursing, applying analytical rigor and storytelling to a business context. It’s a demonstration of SQL fluency, ETL design, and interactive data visualization, with a focus on clarity, performance, and real-world relevance.
