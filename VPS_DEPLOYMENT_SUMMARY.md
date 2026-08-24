# Swiply VPS Deployment - Quick Reference

## 📦 Files Created for Deployment

1. **VPS_DEPLOYMENT_GUIDE.md** - Complete deployment guide with all details
2. **QUICK_START_VPS.md** - Quick start guide for fast deployment
3. **deploy-vps.sh** - Automated deployment script
4. **docker-compose.prod.yml** - Production Docker Compose configuration
5. **.env.production.example** - Production environment variables template

## 🚀 Deployment Methods

### Method 1: Automated Script (Recommended)
```bash
ssh root@YOUR_VPS_IP
git clone YOUR_REPO_URL swiply
cd swiply
chmod +x deploy-vps.sh
sudo ./deploy-vps.sh
```

### Method 2: Manual Docker Deployment
```bash
# Install Docker & Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Clone and configure
git clone YOUR_REPO_URL swiply
cd swiply
cp .env.production.example .env
nano .env  # Edit with your values

# Deploy
docker-compose up -d --build
```

### Method 3: Without Docker (Not Recommended for Production)
Use the existing services structure, but you'll need to:
- Install Python 3.12
- Install PostgreSQL
- Install Redis
- Install Node.js
- Run all services manually

## 🔧 Essential Configuration

### 1. Backend (.env)
```bash
POSTGRES_PASSWORD=strong_password_here
OPENAI_API_KEY=sk-your-key-here
ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
```

### 2. Frontend (frontend/.env)
```bash
VITE_API_URL=http://YOUR_VPS_IP:8000
# or with domain:
VITE_API_URL=https://api.yourdomain.com
```

## 🌐 Access Points

After deployment, your application will be available at:

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://YOUR_VPS_IP:5173 | React application |
| API Gateway | http://YOUR_VPS_IP:8000 | Main API endpoint |
| API Docs | http://YOUR_VPS_IP:8000/docs | Swagger documentation |
| Auth Service | http://YOUR_VPS_IP:8001 | Authentication |
| Job Service | http://YOUR_VPS_IP:8003 | Job management |
| Profile Service | http://YOUR_VPS_IP:8004 | User profiles |
| Automation | http://YOUR_VPS_IP:8006 | Browser automation |
| Email Service | http://YOUR_VPS_IP:8007 | Email handling |
| Credential Service | http://YOUR_VPS_IP:8009 | Credential storage |
| AI Service | http://YOUR_VPS_IP:8010 | AI features |
| WTTJ Service | http://YOUR_VPS_IP:8012 | WTTJ automation |

## 🔒 Security Setup

### 1. Firewall
```bash
sudo ufw allow OpenSSH
sudo ufw allow 5173/tcp
sudo ufw allow 8000/tcp
sudo ufw enable
```

### 2. SSL Certificate (with domain)
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 3. Nginx Reverse Proxy
See QUICK_START_VPS.md for full Nginx configuration

## 📊 Monitoring & Management

### View Logs
```bash
docker-compose logs -f              # All services
docker-compose logs -f wttj         # Specific service
docker-compose logs -f | grep ERROR # Only errors
```

### Check Status
```bash
docker-compose ps     # Container status
docker stats          # Resource usage
systemctl status docker
```

### Restart Services
```bash
docker-compose restart              # All services
docker-compose restart wttj         # Specific service
docker-compose down && docker-compose up -d  # Full restart
```

### Update Application
```bash
git pull origin main
docker-compose down
docker-compose up -d --build
```

## 💾 Backup & Restore

### Backup Database
```bash
docker exec swiply-postgres pg_dump -U swiply swiply > backup_$(date +%Y%m%d).sql
```

### Restore Database
```bash
cat backup_20240101.sql | docker exec -i swiply-postgres psql -U swiply swiply
```

### Backup All Data
```bash
# Stop services
docker-compose down

# Backup volumes
sudo tar -czf swiply_backup.tar.gz postgres_data redis_data uploads screenshots

# Restart services
docker-compose up -d
```

## 🐛 Common Issues & Solutions

### Issue: Services won't start
```bash
# Check logs
docker-compose logs

# Check ports
sudo netstat -tulpn | grep LISTEN

# Rebuild
docker-compose down
docker-compose up -d --build
```

### Issue: Out of memory
```bash
# Check memory
free -h

# Add swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Issue: Firefox automation fails
```bash
docker-compose exec wttj python -m playwright install firefox
docker-compose exec wttj python -m playwright install-deps
docker-compose restart wttj
```

### Issue: Database connection error
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check connection string in .env
docker-compose logs postgres

# Reset database (WARNING: deletes data)
docker-compose down -v
docker-compose up -d
```

## 📈 Performance Optimization

### 1. Increase PostgreSQL Performance
Edit docker-compose.yml:
```yaml
postgres:
  command: 
    - "postgres"
    - "-c"
    - "max_connections=200"
    - "-c"
    - "shared_buffers=256MB"
```

### 2. Frontend Production Build
```bash
cd frontend
npm run build
# Update Dockerfile to serve dist folder with nginx
```

### 3. Enable Redis Caching
Already configured in docker-compose.yml with:
```yaml
command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

## 🔄 CI/CD Setup (Optional)

### GitHub Actions Example
Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to VPS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to VPS
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.VPS_IP }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd swiply
            git pull
            docker-compose down
            docker-compose up -d --build
```

## 📞 Support Resources

- **Full Deployment Guide**: VPS_DEPLOYMENT_GUIDE.md
- **Quick Start**: QUICK_START_VPS.md
- **Docker Compose**: docker-compose.yml / docker-compose.prod.yml
- **Environment Config**: .env.production.example

## ✅ Pre-Deployment Checklist

Before deploying to production:

- [ ] VPS provisioned (4GB RAM minimum)
- [ ] Domain purchased and DNS configured (optional)
- [ ] SSH access to VPS working
- [ ] OpenAI API key obtained
- [ ] Strong passwords generated
- [ ] Environment files configured
- [ ] Firewall rules planned
- [ ] Backup strategy decided
- [ ] Monitoring plan in place

## ✅ Post-Deployment Checklist

After deploying:

- [ ] All services running (`docker-compose ps`)
- [ ] Frontend accessible
- [ ] API responding (`curl http://YOUR_VPS_IP:8000/docs`)
- [ ] Database connected
- [ ] Redis working
- [ ] Firewall enabled
- [ ] SSL certificate installed (if using domain)
- [ ] First backup completed
- [ ] Monitoring configured
- [ ] User registration tested
- [ ] WTTJ automation tested

## 🎯 Next Steps

1. **Test the application** - Register, create profile, test features
2. **Set up monitoring** - Prometheus, Grafana, or basic logging
3. **Configure backups** - Automated daily backups
4. **Set up domain** - Point domain and configure SSL
5. **Performance tuning** - Monitor and optimize based on usage
6. **Security hardening** - Regular updates, security scans
7. **Documentation** - Document any custom configurations

---

**Deployment Time Estimate:**
- Automated: ~15-20 minutes
- Manual: ~30-45 minutes
- With domain + SSL: +15 minutes

**Monthly Costs Estimate:**
- VPS: $5-20 (DigitalOcean, Linode, etc.)
- Domain: $10-15/year
- SSL: Free (Let's Encrypt)
- OpenAI API: Pay-as-you-go

---

Good luck with your deployment! 🚀
