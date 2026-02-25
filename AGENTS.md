# AGENTS.md

## Cursor Cloud specific instructions

### Architecture overview

Mathipe UI is a **Frappe v15 / ERPNext custom app** for a printing company (Gráfica Mathipe). It has two layers:

- **Backend**: Frappe Framework (Python 3.10) + ERPNext, serving APIs at `localhost:8000`
- **Frontend SPA**: Vue 3 + Vite + Tailwind CSS in `frontend/`, proxying to the Frappe backend

The bench workspace lives at `~/frappe-bench` with the app symlinked from `/workspace`.

### Services required

| Service | Port | Notes |
|---------|------|-------|
| MariaDB | 3306 | `sudo mariadbd --user=mysql --datadir=/var/lib/mysql --socket=/run/mysqld/mysqld.sock &` (root pw: `root`) |
| Redis cache | 13000 | `redis-server --port 13000 --daemonize yes` |
| Redis queue | 11000 | `redis-server --port 11000 --daemonize yes` |
| Frappe backend | 8000 | `cd ~/frappe-bench && bench serve --port 8000` |
| Vite dev server | 5173 | `cd /workspace/frontend && npx vite --host 0.0.0.0 --port 5173` (optional, for frontend hot-reload) |

### Startup sequence

1. Start MariaDB: `sudo mkdir -p /run/mysqld && sudo chown mysql:mysql /run/mysqld && sudo mariadbd --user=mysql --datadir=/var/lib/mysql --socket=/run/mysqld/mysqld.sock &`
2. Start Redis: `redis-server --port 13000 --daemonize yes && redis-server --port 11000 --daemonize yes`
3. Start Frappe: `cd ~/frappe-bench && PATH="$HOME/.local/bin:$PATH" bench serve --port 8000 &`
4. (Optional) Start Vite: `cd /workspace/frontend && npx vite --host 0.0.0.0 --port 5173 &`

### Key commands

- **Lint (Python)**: `cd /workspace && ruff check mathipe_ui/`
- **Build SPA**: `cd /workspace/frontend && npm run build` (outputs to `mathipe_ui/public/spa/`)
- **Build bench assets**: `cd ~/frappe-bench && bench build --app mathipe_ui`
- **Run tests**: `cd ~/frappe-bench && bench --site test_site run-tests --app mathipe_ui` (currently 0 tests exist)
- **Migrate**: `cd ~/frappe-bench && bench --site test_site migrate`
- **Login**: Administrator / admin

### Gotchas

- The Frappe bench process (`bench serve`) must be started from `~/frappe-bench`, not `/workspace`.
- `vite.config.js` proxy targets should point to `http://localhost:8000` for local dev, not the production URL.
- Python 3.10 is required (Frappe v15 uses syntax incompatible with 3.12+). The bench virtualenv is at `~/frappe-bench/env/`.
- Node.js 18 is required (set via `nvm use 18`).
- MariaDB 10.11 works fine despite Frappe's warning about > 10.8.
- The SPA build output (`mathipe_ui/public/spa/`) is gitignored and must be rebuilt locally.
- `bench get-app` clones from `/workspace` — the app source lives at `~/frappe-bench/apps/mathipe_ui` (symlinked or copied).
- The `PATH` must include `$HOME/.local/bin` for the `bench` CLI.
