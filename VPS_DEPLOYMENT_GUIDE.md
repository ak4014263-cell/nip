# Swiply VPS Deployment Guide

## Prerequisites

### VPS Requirements
- **OS**: Ubuntu 20.04 LTS or newer
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: 20GB minimum
- **CPU**: 2 cores minimum
- **Ports**: 80, 443, 5173, 8000-8013 open

### What You'll Need
- SSH access to your VPS
- Domain name (optional, but recommended)
- Root or sudo access

## Quick Deployment Steps

### 1. Connect to Your VPS
```bash
ssh root@your-vps-ip
# or
ssh username@your-vps-ip
```

### 2. Install Required Software
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Git
sudo apt install git -y

# Install Node.js and npm (for frontend)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Log out and back in for docker group to take effect
exit
```

### 3. Clone Your Repository
```bash
# Re-login to VPS
ssh username@your-vps-ip

# Clone the project
cd ~
git clone <your-repo-url> swiply
cd swiply
```

### 4. Set Up Environment Variables
```bash
# Copy environment files
cp .env.example .env
cp frontend/.env.example frontend/.env

# Edit .env files with production values
nano .env
```

**Important environment variables to set:**
```bash
# .env (backend)
DATABASE_URL=postgresql://swiply:swiply123@postgres:5432/swiply
REDIS_URL=redis://redis:6379/0
OPENAI_API_KEY=your-openai-api-key-here
ENCRYPTION_KEY=your-32-byte-encryption-key-here
```

```bash
# frontend/.env
VITE_API_URL=http://your-vps-ip:8000
# or with domain:
VITE_API_URL=https://api.yourdomain.com
```

### 5. Deploy with Docker Compose
```bash
# Build and start all services
docker-compose up -d --build

# Check logs
docker-compose logs -f

# Check running containers
docker ps
```

### 6. Verify Deployment
```bash
# Check if all services are running
docker-compose ps

# Test API Gateway
curl http://localhost:8000/docs

# Test Frontend
curl http://localhost:5173
```

## Access Your Application

- **Frontend**: http://your-vps-ip:5173
- **API Gateway**: http://your-vps-ip:8000
- **API Docs**: http://your-vps-ip:8000/docs

## Production Configuration (Optional)

### Set Up Nginx Reverse Proxy
```bash
# Install Nginx
sudo apt install nginx -y

# Create Nginx configuration
sudo nano /etc/nginx/sites-available/swiply
```

**Nginx configuration:**
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/swiply /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Set Up SSL with Let's Encrypt
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal is set up automatically
sudo certbot renew --dry-run
```

### Set Up Firewall
```bash
# Enable UFW
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable

# If not using Nginx, allow specific ports
sudo ufw allow 5173/tcp
sudo ufw allow 8000/tcp
```

## Management Commands

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f gateway
docker-compose logs -f frontend
docker-compose logs -f wttj
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart wttj
docker-compose restart gateway
```

### Update Application
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

### Database Backup
```bash
# Backup database
docker exec swiply-postgres pg_dump -U swiply swiply > backup_$(date +%Y%m%d).sql

# Restore database
cat backup_20240101.sql | docker exec -i swiply-postgres psql -U swiply swiply
```

### Clean Up Docker
```bash
# Remove stopped containers
docker container prune -f

# Remove unused images
docker image prune -a -f

# Remove unused volumes
docker volume prune -f

# Full cleanup
docker system prune -a --volumes -f
```

## Monitoring

### Check Service Health
```bash
# Check all container status
docker-compose ps

# Check resource usage
docker stats

# Check specific service logs
docker-compose logs wttj | grep ERROR
```

### System Resources
```bash
# Check disk space
df -h

# Check memory
free -h

# Check CPU
top
```

## Troubleshooting

### Services Won't Start
```bash
# Check Docker daemon
sudo systemctl status docker

# Check logs for errors
docker-compose logs

# Check port conflicts
sudo netstat -tulpn | grep LISTEN
```

### Database Connection Issues
```bash
# Check PostgreSQL container
docker exec -it swiply-postgres psql -U swiply

# Reset database
docker-compose down -v
docker-compose up -d
```

### Firefox/Playwright Issues
```bash
# The WTTJ service needs additional setup for headless Firefox
# Make sure the container has necessary dependencies

# Check WTTJ service logs
docker-compose logs wttj

# Install Playwright browsers in container
docker-compose exec wttj python -m playwright install firefox
docker-compose exec wttj python -m playwright install-deps
```

### Out of Memory
```bash
# Check memory usage
free -h
docker stats

# Add swap space
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Port Already in Use
```bash
# Find process using port
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>
```

## Security Recommendations

1. **Change Default Passwords**
   - Database password in docker-compose.yml
   - Any default credentials

2. **Use Environment Variables**
   - Never commit .env files
   - Use strong passwords and keys

3. **Enable Firewall**
   - Only open necessary ports
   - Use Nginx as reverse proxy

4. **Regular Updates**
   - Keep system updated: `sudo apt update && sudo apt upgrade`
   - Update Docker images regularly

5. **SSL Certificate**
   - Always use HTTPS in production
   - Use Let's Encrypt for free SSL

6. **Database Security**
   - Don't expose PostgreSQL port externally
   - Regular backups

## Performance Optimization

### PostgreSQL Tuning
```bash
# Edit PostgreSQL config in docker-compose.yml
services:
  postgres:
    command: 
      - "postgres"
      - "-c"
      - "max_connections=200"
      - "-c"
      - "shared_buffers=256MB"
```

### Redis Configuration
```bash
# Add to docker-compose.yml redis service
command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

### Frontend Production Build
```bash
# Build optimized production frontend
cd frontend
npm run build

# Serve with Nginx instead of Vite dev server
# Update docker-compose.yml frontend service to serve dist folder
```

## Support and Resources

- Check logs first: `docker-compose logs -f`
- Monitor resources: `docker stats`
- Database status: `docker exec swiply-postgres psql -U swiply -c "SELECT version();"`

## Common Commands Cheat Sheet

```bash
# Deploy
docker-compose up -d --build

# Stop
docker-compose down

# Logs
docker-compose logs -f [service-name]

# Restart
docker-compose restart [service-name]

# Update
git pull && docker-compose up -d --build

# Backup DB
docker exec swiply-postgres pg_dump -U swiply swiply > backup.sql

# Clean up
docker system prune -a --volumes -f
```

## Next Steps

1. Set up monitoring (Prometheus, Grafana)
2. Configure automated backups
3. Set up CI/CD pipeline
4. Configure log aggregation
5. Set up alerting system
