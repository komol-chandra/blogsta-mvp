# Blogsta — MVP "Instagram for Blog Posts"

FastAPI + MySQL backend, React (Vite) frontend. Users register/login, write posts, get a
timeline, react and comment on posts, and repost.

## Docs
- [`docs/database-plan.md`](docs/database-plan.md) — ER diagram + table definitions
- [`docs/api-plan.md`](docs/api-plan.md) — every endpoint, method, body, response
- [`docs/ui-plan.md`](docs/ui-plan.md) — pages, component tree, wireframes

## Project layout
```
backend/    FastAPI app (SQLAlchemy models, JWT auth, routers per resource)
frontend/   React app (Vite, react-router, axios)
docs/       Planning docs
```

## Backend setup

1. Create a MySQL database and user:
   ```sql
   CREATE DATABASE blogsta CHARACTER SET utf8mb4;
   CREATE USER 'blogsta_user'@'%' IDENTIFIED BY 'blogsta_pass';
   GRANT ALL PRIVILEGES ON blogsta.* TO 'blogsta_user'@'%';
   FLUSH PRIVILEGES;
   ```
2. ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env       # edit DATABASE_URL / SECRET_KEY if needed
   uvicorn app.main:app --reload
   ```
   Tables are auto-created on first run (`Base.metadata.create_all`). Swap in Alembic
   migrations once the schema stabilizes.
3. API docs at `http://localhost:8000/docs` (Swagger UI).

## Frontend setup

```bash
cd frontend
npm install
cp .env.example .env   # points at http://localhost:8000/api/v1 by default
npm run dev
```
App runs at `http://localhost:5173`.

## Quick test flow
1. Register a user at `/register`.
2. You're redirected to the timeline — write a post.
3. Open the post, add a comment, like it.
4. Register a second user, visit the first user's profile (`/u/<username>`), follow them,
   and repost one of their posts.

## What's intentionally left out of this MVP (natural next steps)
- Alembic migrations (currently `create_all`)
- Image upload (currently just an `image_url` text field — plug in S3/Cloudinary later)
- Follow-based (vs. global) timeline filtering — the `follows` table and endpoints already
  exist, `/feed` just needs a `WHERE user_id IN (following...)` clause
- Notifications, search, direct messages
- Refresh tokens / rate limiting / email verification
