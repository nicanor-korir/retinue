# Retinue - Comprehensive Deployment Guide

**Deploy your AI Agent Company to production on free/cheap platforms**

This guide covers deployment to multiple platforms with free tiers or trials.

---

## Table of Contents

1. [Platform Comparison](#platform-comparison)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Deployment Options](#deployment-options)
   - [Option 1: Render.com (Easiest, Free Tier)](#option-1-rendercom-easiest-free-tier)
   - [Option 2: Railway.app (Great DX, $5 Free Trial)](#option-2-railwayapp-great-dx-5-free-trial)
   - [Option 3: Fly.io (Global CDN, Free Tier)](#option-3-flyio-global-cdn-free-tier)
   - [Option 4: Vercel + Separate Backend (Best for Frontend)](#option-4-vercel--separate-backend)
   - [Option 5: Docker Compose on a shared VPS (Hetzner, self-hosted)](#option-5-docker-compose-on-a-shared-vps-hetzner-self-hosted)
4. [Post-Deployment Setup](#post-deployment-setup)
5. [Monitoring & Maintenance](#monitoring--maintenance)
6. [Troubleshooting](#troubleshooting)
7. [Cost Optimization](#cost-optimization)

---

## Platform Comparison

| Platform | Backend | Frontend | Database | Free Tier | Pros | Cons |
|----------|---------|----------|----------|-----------|------|------|
| **Render.com** | ✅ | ✅ | ✅ PostgreSQL | Yes | Easy setup, all-in-one | Slower cold starts |
| **Railway.app** | ✅ | ✅ | ✅ PostgreSQL | $5 trial | Fast, great DX | Trial only |
| **Fly.io** | ✅ | ✅ | ⚠️ Ext. only | Yes | Global CDN, fast | Complex setup |
| **Vercel** | ❌ | ✅ | ❌ | Yes | Best for Next.js | Frontend only |
| **Heroku** | ✅ | ✅ | ✅ PostgreSQL | Limited | Well-documented | Expensive after free |
| **DigitalOcean** | ✅ | ✅ | ✅ | $200 credit | Full control | Requires DevOps |

### Recommended for Beginners: **Render.com**
### Recommended for Production: **Railway.app** or **Fly.io**

---

## Pre-Deployment Checklist

Before deploying, ensure you have:

- [ ] **Anthropic API Key** - Required for AI agents
- [ ] **GitHub Account** - For code hosting
- [ ] **Git Repository** - Code pushed to GitHub
- [ ] **Domain Name** (Optional) - For custom domains
- [ ] **Environment Variables** - Documented in `.env.production.example`

### Get Your Anthropic API Key

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys
4. Create a new key
5. Copy and save it securely

**Important**: Never commit API keys to Git!

---

## Deployment Options

## Option 1: Render.com (Easiest, Free Tier)

**Best for**: Beginners, quick deployments, prototypes

**Free Tier Includes**:
- 750 hours/month web service
- 1GB PostgreSQL database
- 512MB RAM per service
- Automatic SSL certificates

### Step 1: Prerequisites

1. Create account at https://render.com
2. Connect your GitHub account
3. Fork/push Retinue to your GitHub repo

### Step 2: Deploy PostgreSQL

1. In Render Dashboard, click **New +** → **PostgreSQL**
2. Configure:
   - **Name**: `Retinue-postgres`
   - **Database**: `ai_company`
   - **User**: `agent`
   - **Region**: Choose closest to you
   - **Plan**: Free
3. Click **Create Database**
4. **Save the Internal Database URL** (you'll need this)

### Step 3: Deploy Redis

1. Click **New +** → **Redis**
2. Configure:
   - **Name**: `Retinue-redis`
   - **Region**: Same as PostgreSQL
   - **Plan**: Free
3. Click **Create Redis**
4. **Save the Redis URL**

### Step 4: Deploy Backend

1. Click **New +** → **Web Service**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `Retinue-backend`
   - **Environment**: Docker
   - **Region**: Same as database
   - **Branch**: main
   - **Dockerfile Path**: `backend/Dockerfile.prod`
   - **Plan**: Free
4. **Add Environment Variables**:
   ```
   DATABASE_URL=[Your PostgreSQL Internal URL]
   REDIS_URL=[Your Redis URL]
   ANTHROPIC_API_KEY=[Your Anthropic API Key]
   ENVIRONMENT=production
   PORT=8000
   ```
5. Click **Create Web Service**

Wait for deployment to complete (~5-10 minutes).

### Step 5: Initialize Database

Once backend is running:

```powershell
# Get shell access to your backend service
# In Render Dashboard: Retinue-backend → Shell

# Run migrations
alembic upgrade head

# Initialize agents
python -m app.scripts.init_agents
```

### Step 6: Deploy Frontend

1. Click **New +** → **Web Service**
2. Same repository
3. Configure:
   - **Name**: `Retinue-frontend`
   - **Environment**: Docker
   - **Region**: Same as others
   - **Branch**: main
   - **Dockerfile Path**: `frontend/Dockerfile.prod`
   - **Plan**: Free
4. **Add Environment Variables**:
   ```
   NEXT_PUBLIC_API_URL=[Your Backend URL]
   PORT=3000
   ```
   Example: `NEXT_PUBLIC_API_URL=https://Retinue-backend.onrender.com`

5. Click **Create Web Service**

### Step 7: Verify Deployment

Visit your frontend URL (e.g., `https://Retinue-frontend.onrender.com`)

You should see the dashboard!

**⏱️ Note**: Free tier services sleep after 15 min of inactivity. First request will take ~30s to wake up.

---

## Option 2: Railway.app (Great DX, $5 Free Trial)

**Best for**: Fast iteration, great developer experience

**Free Trial**: $5 credit (~500 hours)

### Step 1: Prerequisites

1. Create account at https://railway.app
2. Connect GitHub account
3. Install Railway CLI (optional but recommended):
   ```powershell
   npm install -g @railway/cli
   railway login
   ```

### Step 2: Create New Project

```powershell
# Navigate to project
cd Retinue

# Create new Railway project
railway init

# Link to your project
railway link
```

### Step 3: Add PostgreSQL

```powershell
# Add PostgreSQL plugin
railway add --plugin postgresql

# Railway automatically creates DATABASE_URL
```

### Step 4: Add Redis

```powershell
# Add Redis plugin
railway add --plugin redis

# Railway automatically creates REDIS_URL
```

### Step 5: Deploy Backend

```powershell
# Set environment variables
railway variables set ANTHROPIC_API_KEY=your-key-here
railway variables set ENVIRONMENT=production

# Deploy backend
cd backend
railway up
```

Railway will:
- Detect Dockerfile.prod
- Build and deploy automatically
- Generate a URL

### Step 6: Initialize Database

```powershell
# Run migrations
railway run alembic upgrade head

# Initialize agents
railway run python -m app.scripts.init_agents
```

### Step 7: Deploy Frontend

```powershell
# Create new service for frontend
railway add --service frontend

# Set backend URL
railway variables set NEXT_PUBLIC_API_URL=https://your-backend.railway.app

# Deploy
cd ../frontend
railway up
```

### Step 8: Configure Custom Domains (Optional)

In Railway dashboard:
1. Click on service → Settings
2. Scroll to Domains
3. Add custom domain
4. Update DNS records

**Done!** Visit your Railway URL.

---

## Option 3: Fly.io (Global CDN, Free Tier)

**Best for**: Global deployments, low latency

**Free Tier Includes**:
- 3 shared-cpu VMs
- 3GB persistent volumes
- 160GB outbound data transfer

### Step 1: Prerequisites

```powershell
# Install Fly CLI
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"

# Login
fly auth login

# Verify
fly version
```

### Step 2: Create Apps

```powershell
cd Retinue

# Create backend app
fly apps create Retinue-backend

# Create frontend app
fly apps create Retinue-frontend
```

### Step 3: Create PostgreSQL

```powershell
# Create PostgreSQL cluster
fly postgres create --name Retinue-postgres --region ord

# Attach to backend
fly postgres attach Retinue-postgres --app Retinue-backend
```

This automatically sets `DATABASE_URL`.

### Step 4: Create Redis (Using Upstash)

Since Fly.io doesn't have built-in Redis:

1. Go to https://upstash.com (Free tier: 10,000 commands/day)
2. Create Redis database
3. Copy connection URL

```powershell
# Set Redis URL
fly secrets set REDIS_URL=your-upstash-redis-url --app Retinue-backend
```

### Step 5: Deploy Backend

```powershell
# Set secrets
fly secrets set ANTHROPIC_API_KEY=your-key-here --app Retinue-backend
fly secrets set ENVIRONMENT=production --app Retinue-backend

# Deploy using fly.backend.toml
fly deploy --config fly.backend.toml --app Retinue-backend
```

### Step 6: Initialize Database

```powershell
# SSH into backend
fly ssh console --app Retinue-backend

# Run migrations
alembic upgrade head
python -m app.scripts.init_agents
exit
```

### Step 7: Deploy Frontend

```powershell
# Set backend URL
fly secrets set NEXT_PUBLIC_API_URL=https://Retinue-backend.fly.dev --app Retinue-frontend

# Deploy
fly deploy --config fly.frontend.toml --app Retinue-frontend
```

### Step 8: Configure Regions (Optional)

```powershell
# Add more regions for global coverage
fly regions add lhr  # London
fly regions add syd  # Sydney
fly regions add fra  # Frankfurt
```

**Done!** Access at `https://Retinue-frontend.fly.dev`

---

## Option 4: Vercel + Separate Backend

**Best for**: Optimal frontend performance, existing backend

### Deploy Frontend to Vercel

1. Go to https://vercel.com
2. Import GitHub repository
3. Configure:
   - **Framework**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
4. **Environment Variables**:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-url.com
   ```
5. Click **Deploy**

Vercel will:
- Build and deploy automatically
- Generate preview URLs for PRs
- Auto-deploy on push to main

### Deploy Backend Separately

Choose one of the above options for backend:
- Render.com
- Railway.app
- Fly.io

Then update Vercel environment variable with backend URL.

---

## Option 5: Docker Compose on a shared VPS (Hetzner, self-hosted)

**Best for**: full control, predictable cost, and running alongside services you already host.

This is the reference self-hosted setup. It assumes you already have a VPS running other things, and deliberately reuses what's there rather than duplicating it:

| Concern | Approach |
|---|---|
| Reverse proxy + TLS | **Your existing Caddy** — Retinue adds two site blocks |
| Database | **Your existing PostgreSQL** — Retinue gets its own database and role |
| Image builds | **GitHub Actions → GHCR** — the server only pulls, never builds |
| Retinue's own services | `backend`, `frontend`, `redis` |

Steady-state cost is roughly **350–550 MB of RAM**, which fits comfortably on a 4 GB server alongside other workloads.

The worked example uses `retinue.nicanor.xyz` (frontend) and `api.retinue.nicanor.xyz` (backend). Substitute your own.

### Why not build on the server

`next build` peaks at **1.5–2.5 GB**. On a box already running other services that will OOM — and worse, it can take *those* services down with it. Building in CI removes the spike entirely, makes deploys a fast `pull`, and means a broken build can never affect what's already running.

### What it looks like

```
                     Internet
                        │
              ┌─────────┴──────────┐
              │  YOUR existing     │  ← already owns :80/:443
              │  Caddy             │
              └─────────┬──────────┘
           ┌────────────┴────────────┐
   retinue.nicanor.xyz      api.retinue.nicanor.xyz
           │                         │
    ┌──────▼──────┐          ┌───────▼──────┐
    │  frontend   │          │   backend    │
    │   :3000     │          │    :8000     │
    └─────────────┘          └──────┬───────┘
                            ┌───────┴────────┐
                     ┌──────▼─────┐   ┌──────▼──────────┐
                     │   redis    │   │ YOUR existing   │
                     │  (Retinue) │   │  PostgreSQL     │
                     └────────────┘   └─────────────────┘
```

Nothing Retinue runs binds to a host port. Everything is reached through your Caddy.

---

### Step 1: DNS

Certificates cannot be issued until DNS resolves, so do this **before** reloading Caddy:

| Type | Name | Value |
|---|---|---|
| A | `retinue` | your server's IPv4 |
| A | `api.retinue` | your server's IPv4 |
| AAAA | `retinue` | your server's IPv6 (optional) |
| AAAA | `api.retinue` | your server's IPv6 (optional) |

```bash
dig +short retinue.nicanor.xyz
dig +short api.retinue.nicanor.xyz
```

Both must return your server's IP before continuing.

### Step 2: Publish images from CI

`.github/workflows/ci-cd.yml` already tests, builds, and pushes both images to GHCR on every push to `main`.

The frontend bakes its API URLs in at build time, so set these as **repository variables** (Settings → Secrets and variables → Actions → **Variables** — they're public URLs, not secrets):

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://api.retinue.nicanor.xyz` |
| `NEXT_PUBLIC_WS_URL` | `wss://api.retinue.nicanor.xyz` |

Also add `ANTHROPIC_API_KEY` as a repository **secret** — the backend test job needs it.

Push to `main`, then confirm both packages appear under your repo's Packages tab. If the repo is private, the server needs a read token:

```bash
echo <github-pat-with-read:packages> | docker login ghcr.io -u <your-github-username> --password-stdin
```

### Step 3: Provision the database

Retinue gets its own database and role inside your existing PostgreSQL, so it stays isolated from your other apps.

Edit the password in `deploy/postgres-setup.sql`, then:

```bash
# Postgres on the host
psql -U postgres -f deploy/postgres-setup.sql

# Postgres in a container
docker exec -i <postgres-container> psql -U postgres < deploy/postgres-setup.sql
```

**If PostgreSQL runs on the host**, it must accept connections from the Docker bridge — the most common first-deploy failure. In `postgresql.conf`:

```
listen_addresses = 'localhost,172.17.0.1'
```

In `pg_hba.conf`, scoped to just this database and role:

```
host    retinue    retinue    172.16.0.0/12    scram-sha-256
```

Then `sudo systemctl reload postgresql`. Confirm your bridge address with `ip addr show docker0`.

> Keep port 5432 closed in the Hetzner Cloud Firewall. Only local containers should reach Postgres.

### Step 4: Connect the proxy network

Your Caddy needs to resolve `frontend` and `backend` by name:

```bash
docker network create proxy                        # once, if it doesn't exist
docker network connect proxy <your-caddy-container>
```

If your Caddy runs on the host rather than in a container, keep the bundled proxy approach instead — or publish the two services on localhost-only ports (`127.0.0.1:3000:3000`) and point Caddy at those.

### Step 5: Configure

```bash
git clone https://github.com/yourusername/retinue.git
cd retinue
cp .env.production.example .env.production
nano .env.production
```

Fill in the image names, `DATABASE_URL` (matching the password from Step 3), `ANTHROPIC_API_KEY`, and `JWT_SECRET` (`openssl rand -hex 32`).

### Step 6: Deploy

```bash
C="docker compose -f docker-compose.prod.yml --env-file .env.production"

$C pull
$C up -d
$C ps
```

Migrations run in a dedicated `migrate` service that must exit successfully before the backend starts, so the API never comes up against a stale schema.

### Step 7: Seed the agents

```bash
$C exec backend python -m app.scripts.init_agents
$C exec backend python -m app.scripts.seed_agent_expertise
$C exec backend python -m app.scripts.init_knowledge_system   # optional
$C exec backend python -m app.scripts.verify_database
```

### Step 8: Add the Caddy site blocks

Append the two blocks from **`deploy/Caddyfile.snippet`** to your existing Caddyfile, then reload:

```bash
docker exec <your-caddy-container> caddy reload --config /etc/caddy/Caddyfile
# or, for host-installed Caddy:
sudo systemctl reload caddy
```

### Step 9: Verify

```bash
curl https://api.retinue.nicanor.xyz/health
curl https://api.retinue.nicanor.xyz/api/v1/agents/status
```

Then open `https://retinue.nicanor.xyz` and check:

- Valid certificates on **both** hostnames
- The dashboard loads data (CORS is right)
- A task's activity stream connects (WebSockets are proxying)
- Your **other sites still work** (`docker ps`, and load one of them)

---

### Where the database lives

In **your existing PostgreSQL instance**, in a dedicated `retinue` database owned by a dedicated `retinue` role. It shares your existing backup routine — but confirm that routine actually covers all databases, not just the one you set it up for:

```bash
# per-database dump
pg_dump -U postgres retinue | gzip > retinue-$(date +%F).sql.gz

# or cluster-wide
pg_dumpall -U postgres | gzip > all-$(date +%F).sql.gz
```

Restore:

```bash
gunzip -c retinue-2026-08-15.sql.gz | psql -U postgres -d retinue
```

**Redis** stays in its own container with the `redis_data` volume. It holds cache and the event bus, not durable state, so it doesn't need backing up — a cold start rebuilds it.

### Resource limits

The compose file caps each service (`backend` 768 MB, `frontend` 384 MB, `redis` 320 MB) so a runaway Retinue process can't starve your other workloads. Watch actual usage with:

```bash
docker stats --no-stream
```

If the backend is regularly near its ceiling, raise the limit rather than removing it — an unbounded container on a shared box is what takes neighbours down.

### Updating

```bash
git pull                 # only needed if compose/env changed
$C pull && $C up -d
```

CI rebuilds images on push to `main`; the server just pulls. Migrations reapply automatically.

**Changing either domain requires a CI rebuild**, not just a restart — update the repository variables from Step 2 and push, because the frontend bakes those URLs into its bundle.

### Rollback

Images are tagged with the commit SHA, so pin a known-good one in `.env.production`:

```env
BACKEND_IMAGE=ghcr.io/owner/repo/backend:main-a1b2c3d
FRONTEND_IMAGE=ghcr.io/owner/repo/frontend:main-a1b2c3d
```

Then `$C up -d`. Note that migrations do not auto-revert — roll the schema back deliberately with `alembic downgrade` if a release changed it.

### Troubleshooting

**`connection refused` to Postgres.** The host instance isn't listening on the Docker bridge, or `pg_hba.conf` doesn't allow it. Re-check Step 3, then test from inside a container:

```bash
$C exec backend python -c "import socket;print(socket.create_connection(('host.docker.internal',5432),5))"
```

**Caddy returns 502.** It can't resolve the container names — confirm your Caddy is attached to the `proxy` network (`docker network inspect proxy`) and that both containers are running.

**Certificate issuance fails.** DNS or firewall. Both names must resolve to this server and ports 80/443 must be open. Let's Encrypt rate-limits failures, so fix DNS before retrying.

**Frontend loads but shows no data.** CORS or a wrong baked-in API URL. Check `$C exec backend env | grep CORS`, and confirm the repository variables from Step 2 matched at build time.

**Live activity streams never connect.** The image was built with `ws://` instead of `wss://`. Fix `NEXT_PUBLIC_WS_URL` and rebuild.

**Your other services slowed down after deploying.** Check `docker stats`. Retinue's limits cap it, but the Claude API calls are I/O-heavy and Postgres now serves an extra database — consider raising `shared_buffers` if the instance is under pressure.
---

## Post-Deployment Setup

### 1. Test Health Endpoints

```powershell
# Backend health
Invoke-RestMethod https://your-backend-url.com/health

# Should return:
# {
#   "status": "healthy",
#   "agents_count": 7,
#   "agents": {...}
# }
```

### 2. Create Your First Project

1. Visit your frontend URL
2. Click "Projects" → "New Project"
3. Fill in details
4. Submit and monitor progress

### 3. Monitor Agent Activity

Check that agents are running:

```powershell
# Get agent status
Invoke-RestMethod https://your-backend-url.com/api/v1/agents/status
```

### 4. Setup Monitoring (Recommended)

#### Option A: Sentry for Error Tracking

1. Create account at https://sentry.io (free tier available)
2. Create new project
3. Get DSN
4. Add to environment variables:
   ```
   SENTRY_DSN=your-sentry-dsn
   ```

#### Option B: UptimeRobot for Uptime Monitoring

1. Create account at https://uptimerobot.com (free tier: 50 monitors)
2. Add monitors for:
   - Backend health endpoint
   - Frontend homepage
3. Get alerts via email/SMS

---

## Monitoring & Maintenance

### Logs

**Render.com**:
```
Dashboard → Service → Logs tab
```

**Railway.app**:
```powershell
railway logs
```

**Fly.io**:
```powershell
fly logs --app Retinue-backend
fly logs --app Retinue-frontend
```

**Docker Compose**:
```bash
docker-compose -f docker-compose.prod.yml logs -f [service]
```

### Database Backups

**Render.com**:
- Automatic daily backups on paid plans
- Manual backup: Dashboard → Database → Backups

**Railway.app**:
```powershell
railway run pg_dump > backup.sql
```

**Fly.io**:
```powershell
fly postgres backup list --app Retinue-postgres
fly postgres backup create --app Retinue-postgres
```

**Self-Hosted**:
```bash
# Backup
docker-compose exec postgres pg_dump -U agent ai_company > backup.sql

# Restore
docker-compose exec -T postgres psql -U agent ai_company < backup.sql
```

### Scaling

**Horizontal Scaling** (More instances):

**Render.com**: Dashboard → Service → Settings → Instance Count

**Railway.app**:
```powershell
railway scale --replicas 2
```

**Fly.io**:
```powershell
fly scale count 2 --app Retinue-backend
```

**Vertical Scaling** (More resources):

Upgrade to paid plans for more RAM/CPU.

---

## Troubleshooting

### Issue: "Cannot connect to database"

**Check**:
1. DATABASE_URL is set correctly
2. Database service is running
3. Network connectivity

**Fix**:
```powershell
# Render/Railway: Check dashboard
# Fly.io:
fly status --app Retinue-postgres

# Self-hosted:
docker-compose ps
```

### Issue: "Agents not responding"

**Check**:
1. ANTHROPIC_API_KEY is valid
2. Check logs for API errors
3. Verify agents initialized

**Fix**:
```powershell
# Re-initialize agents
# Render: Use Shell in dashboard
# Railway:
railway run python -m app.scripts.init_agents

# Fly.io:
fly ssh console --app Retinue-backend
python -m app.scripts.init_agents
```

### Issue: "Frontend shows 'Cannot connect to backend'"

**Check**:
1. NEXT_PUBLIC_API_URL is correct
2. Backend is running
3. CORS is configured

**Fix**:
Update environment variable with correct backend URL and redeploy.

### Issue: "Out of memory"

Free tiers have limited RAM (256-512MB).

**Solutions**:
1. Reduce number of workers (Gunicorn -w 2)
2. Optimize database queries
3. Upgrade to paid plan
4. Use external Redis (Upstash free tier)

---

## Cost Optimization

### Free Tier Limits

**Render.com**:
- Services sleep after 15 min inactivity
- 750 hours/month (enough for 1 service)
- 1GB database storage

**Railway.app**:
- $5 credit (~500 hours)
- Pay-as-you-go after

**Fly.io**:
- 3 VMs (256MB each)
- 3GB storage
- 160GB bandwidth

### Tips to Stay Free

1. **Use External Services**:
   - PostgreSQL: ElephantSQL (free 20MB)
   - Redis: Upstash (free 10K commands/day)

2. **Optimize Agent Check Intervals**:
   ```env
   AGENT_CHECK_INTERVAL=1800  # 30 min instead of 15
   ```

3. **Auto-Sleep Inactive Services**:
   - Keep only essential services running
   - Use "wake-up" pings for on-demand

4. **Combine Services**:
   - Run backend + frontend in single container
   - Use SQLite for dev/small deployments

---

## Production Checklist

Before going live:

- [ ] All environment variables set correctly
- [ ] Database migrations run successfully
- [ ] All 7 agents initialized
- [ ] Health endpoint returns healthy status
- [ ] Frontend connects to backend
- [ ] HTTPS/SSL certificates configured
- [ ] Custom domain configured (if applicable)
- [ ] Monitoring/alerts set up
- [ ] Database backups configured
- [ ] Error tracking (Sentry) configured
- [ ] Rate limiting enabled
- [ ] Security headers configured
- [ ] API key rotated from test key
- [ ] Documentation updated with URLs

---

## Next Steps

1. **Monitor**: Watch logs and metrics
2. **Test**: Create projects and verify agents work
3. **Optimize**: Tune performance based on usage
4. **Scale**: Upgrade plans as needed
5. **Backup**: Regular database backups
6. **Update**: Keep dependencies up to date

---

## Platform-Specific Quick Reference

### Render.com
- **Dashboard**: https://dashboard.render.com
- **Docs**: https://render.com/docs
- **Pricing**: https://render.com/pricing

### Railway.app
- **Dashboard**: https://railway.app/dashboard
- **Docs**: https://docs.railway.app
- **Pricing**: https://railway.app/pricing

### Fly.io
- **Dashboard**: https://fly.io/dashboard
- **Docs**: https://fly.io/docs
- **Pricing**: https://fly.io/docs/about/pricing

### Vercel
- **Dashboard**: https://vercel.com/dashboard
- **Docs**: https://vercel.com/docs
- **Pricing**: https://vercel.com/pricing

---

**🎉 Congratulations! Your AI Agent Company is now live in production!**

For support and updates, see the main [README.md](README.md).
