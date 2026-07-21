# Joyeuse's Restaurant Order System

Real-time restaurant order management: Front-of-House ordering (POS) + live Kitchen
Display System (KDS), built with Flask, SQLAlchemy, and Socket.IO.

## Features
- **Front of House** (`/front`): menu browsing by category with search, tap-to-add cart,
  table & order-type selection, order notes, one-tap "Send to Kitchen", and a live
  recent-orders strip that updates as the kitchen works.
- **Kitchen Display** (`/kitchen`): active orders appear instantly (no refresh),
  per-item Start / Ready / Served buttons, special-instruction callouts, cards clear
  automatically when everything is served.
- **Admin** (`/admin/dashboard`): staff account management (create/update/delete users).
- **Role-based access**: `front`, `kitchen`, `admin` roles with per-route enforcement.
- **REST API** + Socket.IO events (`order_new`, `order_update`, `order_replaced`,
  `order_delete`) for real-time sync between screens.

## Quick start (local development)
```bash
cd restaurant-system
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # defaults to SQLite dev.db
python scripts/seed_demo.py                            # creates staff logins + demo menu
python run.py                                          # http://localhost:8000
```
Log in with `front1` / `ChangeMe-Front1!` (front) or `kitchen1` / `ChangeMe-Kitchen1!`
(kitchen) — change these in `scripts/seed_demo.py` before real use.

## Deploying for a real restaurant (Render, ~$7–14/month)

Render is the cheapest low-maintenance host that keeps Socket.IO connections alive
24/7 (kitchen screens must never sleep, which rules out free tiers).

### One-time setup
1. Push this repo to GitHub (**make sure `.env` is NOT committed** — see Security).
2. Create a free account at https://render.com and connect your GitHub.
3. **New → Web Service** → pick this repo. Render auto-detects the `Dockerfile`.
4. Choose the **Starter** instance ($7/mo — always on).
5. Set environment variables under the service's **Environment** tab:
   - `SECRET_KEY` → generate with `python -c "import secrets; print(secrets.token_hex(32))"`
   - `DATABASE_URL` → see database options below
   - `FLASK_ENV` → `production`
   - `GUNICORN_WORKERS` → `1` (required for SQLite; `2` is fine for MySQL/Postgres)
6. Deploy. Render gives you a free HTTPS URL like `https://joyeuses-orders.onrender.com`.
7. Open a Render **Shell** for the service and run `python scripts/seed_demo.py`
   (after editing it with the real menu + strong passwords).

### Database options (pick one)
| Option | Cost | Notes |
|---|---|---|
| **A. Render persistent disk + SQLite** | +$1/mo | Cheapest. Add a 1 GB disk mounted at `/data`, set `DATABASE_URL=sqlite:////data/restaurant.db`, keep `GUNICORN_WORKERS=1`. Perfect for one restaurant. |
| **B. Render managed Postgres** | +$6/mo | Set `DATABASE_URL` to the Internal Database URL Render provides, and add `psycopg2-binary` to requirements.txt. Automatic backups. |
| **C. Existing AWS RDS MySQL** | ~$15+/mo | Keep current data; just set `DATABASE_URL=mysql+pymysql://...`. Most expensive — fine if the RDS instance already exists for other reasons. |

### In the restaurant
- **Order-taking device** (tablet/phone/register PC): bookmark `https://<your-app>/front`,
  log in as a `front` user.
- **Kitchen screen** (any tablet or cheap Android TV stick + monitor): open
  `https://<your-app>/kitchen`, log in as a `kitchen` user, set the device to
  never sleep and enable browser full-screen/kiosk mode.
- Optional: buy a domain (~$10/yr) and add it under Render → Custom Domains.

## Security notes
- **Never commit `.env`.** It is gitignored; keep it that way. If real credentials were
  ever committed, rotate them (change the DB password) — removing the file later does
  not remove it from git history.
- `SECRET_KEY` must be a long random value in production (the app refuses obvious
  placeholder values when `Config.validate_production()` is called).
- All staff passwords are stored hashed (Werkzeug). Use strong, unique passwords.

## Project layout
```
restaurant-system/
├── app/
│   ├── __init__.py      # app factory, blueprint registration
│   ├── config.py        # env-driven config (SQLite fallback for dev)
│   ├── models.py        # Employee, Customer, Product, Orders, Order_Line
│   ├── routes.py        # pages (/front, /kitchen) + JSON API (/api/…)
│   ├── auth.py          # login/logout
│   ├── admin.py         # admin dashboard + user management API
│   ├── sockets.py       # Socket.IO setup (eventlet/gevent/threading fallback)
│   ├── validators.py    # request payload validation
│   └── utils.py         # roles_required decorator
├── templates/           # base, front (POS), kitchen (KDS), login, admin
├── static/design.css    # brand design system
├── scripts/seed_demo.py # first-run staff + menu seeding
├── Dockerfile           # production image (gunicorn + eventlet, Python 3.11)
└── deploy/              # gunicorn config, systemd unit (for VPS installs)
```

## API summary
| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/api/products` | any | menu items |
| GET | `/api/orders?active=1` | any | orders (active filter optional) |
| POST | `/api/orders` | front/admin | create order (lines, table, type) |
| PUT | `/api/orders/<id>/lines` | front/admin | atomically replace an order's lines |
| PATCH | `/api/order_lines/<id>/status` | kitchen/front/admin | update line status |
| DELETE | `/api/orders/<id>` | admin | delete order |
| GET/POST/PUT/DELETE | `/admin/api/users…` | admin | staff management |
