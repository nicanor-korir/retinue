# Deviant - Comprehensive Deployment Guide

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
   - [Option 5: Docker Compose (Self-Hosted)](#option-5-docker-compose-self-hosted)
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
3. Fork/push Deviant to your GitHub repo

### Step 2: Deploy PostgreSQL

1. In Render Dashboard, click **New +** → **PostgreSQL**
2. Configure:
   - **Name**: `Deviant-postgres`
   - **Database**: `ai_company`
   - **User**: `agent`
   - **Region**: Choose closest to you
   - **Plan**: Free
3. Click **Create Database**
4. **Save the Internal Database URL** (you'll need this)

### Step 3: Deploy Redis

1. Click **New +** → **Redis**
2. Configure:
   - **Name**: `Deviant-redis`
   - **Region**: Same as PostgreSQL
   - **Plan**: Free
3. Click **Create Redis**
4. **Save the Redis URL**

### Step 4: Deploy Backend

1. Click **New +** → **Web Service**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `Deviant-backend`
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
# In Render Dashboard: Deviant-backend → Shell

# Run migrations
alembic upgrade head

# Initialize agents
python -m app.scripts.init_agents
```

### Step 6: Deploy Frontend

1. Click **New +** → **Web Service**
2. Same repository
3. Configure:
   - **Name**: `Deviant-frontend`
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
   Example: `NEXT_PUBLIC_API_URL=https://Deviant-backend.onrender.com`

5. Click **Create Web Service**

### Step 7: Verify Deployment

Visit your frontend URL (e.g., `https://Deviant-frontend.onrender.com`)

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
cd Deviant

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
cd Deviant

# Create backend app
fly apps create Deviant-backend

# Create frontend app
fly apps create Deviant-frontend
```

### Step 3: Create PostgreSQL

```powershell
# Create PostgreSQL cluster
fly postgres create --name Deviant-postgres --region ord

# Attach to backend
fly postgres attach Deviant-postgres --app Deviant-backend
```

This automatically sets `DATABASE_URL`.

### Step 4: Create Redis (Using Upstash)

Since Fly.io doesn't have built-in Redis:

1. Go to https://upstash.com (Free tier: 10,000 commands/day)
2. Create Redis database
3. Copy connection URL

```powershell
# Set Redis URL
fly secrets set REDIS_URL=your-upstash-redis-url --app Deviant-backend
```

### Step 5: Deploy Backend

```powershell
# Set secrets
fly secrets set ANTHROPIC_API_KEY=your-key-here --app Deviant-backend
fly secrets set ENVIRONMENT=production --app Deviant-backend

# Deploy using fly.backend.toml
fly deploy --config fly.backend.toml --app Deviant-backend
```

### Step 6: Initialize Database

```powershell
# SSH into backend
fly ssh console --app Deviant-backend

# Run migrations
alembic upgrade head
python -m app.scripts.init_agents
exit
```

### Step 7: Deploy Frontend

```powershell
# Set backend URL
fly secrets set NEXT_PUBLIC_API_URL=https://Deviant-backend.fly.dev --app Deviant-frontend

# Deploy
fly deploy --config fly.frontend.toml --app Deviant-frontend
```

### Step 8: Configure Regions (Optional)

```powershell
# Add more regions for global coverage
fly regions add lhr  # London
fly regions add syd  # Sydney
fly regions add fra  # Frankfurt
```

**Done!** Access at `https://Deviant-frontend.fly.dev`

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

## Option 5: Docker Compose (Self-Hosted)

**Best for**: Full control, private servers

### Prerequisites

- VPS with Docker installed (DigitalOcean, Linode, AWS EC2, etc.)
- Domain name pointed to server IP
- SSH access

### Step 1: Server Setup

```bash
# SSH into server
ssh user@your-server-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify
docker --version
docker-compose --version
```

### Step 2: Clone Repository

```bash
# Clone your repo
git clone https://github.com/yourusername/Deviant.git
cd Deviant
```

### Step 3: Configure Environment

```bash
# Copy production env template
cp .env.production.example .env.production

# Edit with your values
nano .env.production
```

Add:
```env
DB_PASSWORD=your_secure_password
ANTHROPIC_API_KEY=your_key_here
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### Step 4: Deploy with Docker Compose

```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Step 5: Initialize Database

```bash
# Run migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Initialize agents
docker-compose -f docker-compose.prod.yml exec backend python -m app.scripts.init_agents
```

### Step 6: Setup Nginx Reverse Proxy

```bash
# Install Nginx
sudo apt update
sudo apt install nginx

# Create config
sudo nano /etc/nginx/sites-available/Deviant
```

Add:
```nginx
# Backend
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Frontend
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/Deviant /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 7: Setup SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificates
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com

# Auto-renewal is configured automatically
```

**Done!** Access at `https://yourdomain.com`

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
fly logs --app Deviant-backend
fly logs --app Deviant-frontend
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
fly postgres backup list --app Deviant-postgres
fly postgres backup create --app Deviant-postgres
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
fly scale count 2 --app Deviant-backend
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
fly status --app Deviant-postgres

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
fly ssh console --app Deviant-backend
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
