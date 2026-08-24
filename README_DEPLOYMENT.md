# 🚀 Swiply - VPS Deployment Instructions

Welcome! This guide will help you deploy Swiply to your VPS in minutes.

## 📋 What You Need

1. **VPS Server** 
   - Ubuntu 20.04+ 
   - 4GB RAM minimum
   - 20GB storage
   - Providers: DigitalOcean, AWS, Linode, Vultr, etc.

2. **OpenAI API Key** 
   - Get from: https://platform.openai.com/api-keys

3. **SSH Access** 
   - Root or sudo user access to your VPS

4. **(Optional) Domain Name**
   - For SSL/HTTPS setup

## ⚡ Quick Deploy (5 Minutes)

### Step 1: Connect to VPS
```bash
ssh root@YOUR_VPS_IP
```

### Step 2: Clone Repository
```bash
git clone https://github.com/yourusername/swiply.git
cd swiply
```

### Step 3: Run Deployment Script
```bash
chmod +x deploy-vps.sh
sudo ./deploy-vps.sh
```

### Step 4: Configure Environment
```bash
# Edit backend config
nano .env
```
Add your values:
```bash
OPENAI_API_KEY=sk-your-key-here
POSTGRES_PASSWORD=strong-password
ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
```

```bash
# Edit frontend config
nano frontend/.env
```
Add:
```bash
VITE_API_URL=http://YOUR_VPS_IP:8000
```

### Step 5: Restart Services
```bash
docker-compose down
docker-compose up -d
```

### Step 6: Access Application
Open browser: http://YOUR_VPS_IP:5173

**That's it! Your app is live! 🎉**

---

## 📚 Detailed Guides

Choose the guide that fits your needs:

### For Beginners
👉 **[QUICK_START_VPS.md](./QUICK_START_VPS.md)** - Step-by-step with screenshots

### For Advanced Users
👉 **[VPS_DEPLOYMENT_GUIDE.md](./VPS_DEPLOYMENT_GUIDE.md)** - Complete reference with all options

### Quick Reference
👉 **[VPS_DEPLOYMENT_SUMMARY.md](./VPS_DEPLOYMENT_SUMMARY.md)** - Commands cheat sheet

---

## 🎯 What Gets Deployed

### Frontend (React + Vite)
- Port: 5173
- User interface

### Backend Services
- **API Gateway** (8000) - Main API
- **Auth Service** (8001) - Authentication
- **Job Service** (8003) - Job management
- **Profile Service** (8004) - User profiles
- **Automation** (8006) - Browser automation
- **Email Service** (8007) - Email handling
- **Credential Service** (8009) - Secure credentials
- **AI Service** (8010) - AI features
- **WTTJ Service** (8012) - WTTJ integration

### Databases
- **PostgreSQL** - Main database
- **Redis** - Caching layer

---

## 🔧 Common Commands

```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f wttj

# Check service status
docker-compose ps

# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart wttj

# Stop all services
docker-compose down

# Start all services
docker-compose up -d

# Update application
git pull
docker-compose up -d --build

# Backup database
docker exec swiply-postgres pg_dump -U swiply swiply > backup.sql
```

---

## 🔒 Security Setup (Recommended)

### 1. Enable Firewall
```bash
sudo ufw allow OpenSSH
sudo ufw allow 5173/tcp
sudo ufw allow 8000/tcp
sudo ufw enable
```

### 2. Set Up Domain (Optional)
Point your domain A record to: `YOUR_VPS_IP`

### 3. Install SSL Certificate
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com
```

---

## 🐛 Troubleshooting

### Services won't start
```bash
docker-compose logs
```

### Port already in use
```bash
sudo lsof -i :8000
sudo kill -9 <PID>
docker-compose up -d
```

### Out of memory
```bash
free -h
# Add swap if low
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Firefox/Playwright errors
```bash
docker-compose exec wttj python -m playwright install firefox
docker-compose restart wttj
```

---

## 📊 Monitoring

### Check Health
```bash
# All services status
docker-compose ps

# Resource usage
docker stats

# Check logs for errors
docker-compose logs | grep ERROR
```

### Access Logs
```bash
# Real-time logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific service
docker-compose logs -f gateway
```

---

## 🎓 Architecture Overview

```
┌─────────────────────────────────────────┐
│           Frontend (React)              │
│         http://vps-ip:5173              │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│        API Gateway (FastAPI)            │
│         http://vps-ip:8000              │
└──────────┬──────────────────────────────┘
           │
           ├──► Auth Service (8001)
           ├──► Job Service (8003)
           ├──► Profile Service (8004)
           ├──► Automation (8006)
           ├──► Email Service (8007)
           ├──► Credential Service (8009)
           ├──► AI Service (8010)
           └──► WTTJ Service (8012)
                    │
                    ▼
           ┌────────────────┐
           │   PostgreSQL   │
           │     Redis      │
           └────────────────┘
```

---

## 📦 Deployment Files

| File | Purpose |
|------|---------|
| `deploy-vps.sh` | Automated deployment script |
| `docker-compose.yml` | Docker services configuration |
| `docker-compose.prod.yml` | Production configuration |
| `.env.production.example` | Environment variables template |
| `QUICK_START_VPS.md` | Beginner-friendly guide |
| `VPS_DEPLOYMENT_GUIDE.md` | Complete deployment manual |
| `VPS_DEPLOYMENT_SUMMARY.md` | Quick reference guide |

---

## 💡 Tips

1. **Use strong passwords** in production
2. **Enable firewall** immediately after deployment
3. **Set up backups** - automate daily database backups
4. **Monitor resources** - check `docker stats` regularly
5. **Use a domain** - it's more professional and enables SSL
6. **Keep updated** - `git pull && docker-compose up -d --build`
7. **Check logs** - when something goes wrong, logs are your friend

---

## 🆘 Need Help?

1. Check the logs: `docker-compose logs -f`
2. Read the detailed guides in this folder
3. Check service status: `docker-compose ps`
4. Verify configuration: `cat .env`

---

## 📈 Next Steps After Deployment

1. ✅ Test user registration
2. ✅ Test profile creation
3. ✅ Test WTTJ integration
4. ✅ Set up automated backups
5. ✅ Configure monitoring
6. ✅ Set up domain + SSL
7. ✅ Performance optimization

---

## 🎉 Success!

Your Swiply application should now be running!

- **Frontend**: http://YOUR_VPS_IP:5173
- **API Docs**: http://YOUR_VPS_IP:8000/docs
- **Database**: PostgreSQL (internal)
- **Cache**: Redis (internal)

---

**Happy deploying! 🚀**

*For questions or issues, check the detailed guides or review the logs.*
