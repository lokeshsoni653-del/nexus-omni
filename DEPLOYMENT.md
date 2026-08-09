# OmniMind AI — Phase 6: Production DevOps & Cloud Deployment Guide

This guide provides step-by-step instructions for deploying **OmniMind AI** live on the internet using modern cloud infrastructure:

- **Frontend**: Next.js 15 App Router deployed to **Vercel**
- **Backend Services**: FastAPI core engine & Celery worker pool deployed to **Render** or **Railway**
- **Database**: Managed PostgreSQL provisioned on **Supabase**
- **In-Memory Cache & Task Queue**: Managed **Redis** (Render / Upstash / Railway)
- **Object Storage**: **Supabase Storage** or **AWS S3** for PDF documents & ReportLab executive reports

---

## 🏗️ Cloud Infrastructure Topology

```text
                                  ┌───────────────────────────────┐
                                  │   Vercel Next.js 15 Edge      │
                                  │   https://omnimind.vercel.app  │
                                  └───────────────┬───────────────┘
                                                  │ HTTPS / WSS
                                                  ▼
┌───────────────────────────────┐     ┌───────────────────────────────┐
│   Supabase Managed Postgres   │◄───►│  Render / Railway FastAPI Web │
│   postgresql://supabase...    │     │  https://omnimind.onrender.com│
└───────────────────────────────┘     └───────────────┬───────────────┘
                                                      │ Celery Task Handoff
                                                      ▼
┌───────────────────────────────┐     ┌───────────────────────────────┐     ┌───────────────────────────────┐
│  Supabase S3 Object Storage   │◄───►│ Render / Upstash Redis Broker │◄───►│  Render Celery Worker Pool    │
│  (PDF Documents & Reports)    │     │ rediss://...                  │     │  (Multi-Agent DAG Engine)     │
└───────────────────────────────┘     └───────────────────────────────┘     └───────────────────────────────┘
```

---

## 1. Local Containerized Execution (`docker-compose.yml`)

Before pushing to the cloud, run all 5 services together locally:

```bash
cd "C:\OmniMind AI"

# Build and start all 5 containers
docker-compose up -d --build
```

### Services Included in `docker-compose.yml`:
1. **`postgres`**: PostgreSQL 16 DB (`5432`)
2. **`redis`**: Redis 7 Cache & Broker (`6379`)
3. **`backend`**: FastAPI Server (`8000`)
4. **`worker`**: Celery Agent Execution Worker Pool
5. **`frontend`**: Next.js Visual Canvas UI (`3000`)

---

## 2. Deploy Managed PostgreSQL Database on Supabase

1. Go to [Supabase.com](https://supabase.com) and create a new project named `omnimind-db`.
2. In Project Settings -> **Database**, copy your Connection String:
   ```text
   postgresql+asyncpg://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   ```
3. Save this URL for your Render / Railway environment variables.

---

## 3. Deploy Backend Engine to Render or Railway

### Option A: Deploy via Render Blueprint (`render.yaml`)
1. Push your repository to GitHub / GitLab.
2. Log into [Render.com](https://render.com) and click **New -> Blueprint**.
3. Connect your repository. Render automatically reads `render.yaml` and provisions:
   - FastAPI Web Service
   - Celery Worker Pool
   - Managed Redis Service
   - PostgreSQL Database
4. In Environment Settings, set `DATABASE_URL` to your Supabase connection string.

### Option B: Deploy via Railway (`railway.json`)
1. Log into [Railway.app](https://railway.app) and create a new project from your GitHub repository.
2. Add **PostgreSQL** and **Redis** plugins from the Railway marketplace.
3. Deploy the backend repository. Railway automatically detects `Dockerfile` and `railway.json`.
4. Expose the web service and copy the public HTTPS domain (e.g. `https://omnimind-backend.up.railway.app`).

---

## 4. Deploy Next.js Frontend to Vercel

1. Log into [Vercel.com](https://vercel.com) and click **Add New -> Project**.
2. Import your `frontend` directory repository.
3. In **Framework Preset**, select **Next.js**.
4. Set **Root Directory** to `frontend`.
5. Add Environment Variables:
   - `NEXT_PUBLIC_API_URL` = `https://omnimind-backend.onrender.com`
   - `NEXT_PUBLIC_WS_URL` = `wss://omnimind-backend.onrender.com`
6. Click **Deploy**.

Vercel will build your Next.js app and assign a live production URL: **`https://omnimind-ai.vercel.app`**.

---

## 5. Deployment Verification Checklist

- [x] Run `python -m pytest tests/ -v` to ensure 32/32 tests pass.
- [x] Run `npm run build` inside `frontend/` to verify Next.js bundle compilation.
- [x] Confirm CORS is enabled in `omnimind/backend/api/main.py`.
- [x] Test live WebSocket connection `/ws/stream/{workflow_id}` over WSS protocol.
- [x] Download generated ReportLab PDF report to verify Cloud Storage URL resolution.
