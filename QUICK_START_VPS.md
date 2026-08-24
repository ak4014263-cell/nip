# Quick Start - VPS Deployment

## 1. Prepare Your VPS

**Recommended VPS Providers:**
- DigitalOcean (Droplet)
- AWS EC2
- Google Cloud Compute Engine
- Linode
- Vultr
- Hetzner

**Minimum Requirements:**
- 4GB RAM, 2 CPU cores, 20GB storage
- Ubuntu 20.04 LTS or newer
- Open ports: 22 (SSH), 80 (HTTP), 443 (HTTPS), 5173, 8000

## 2. Connect to Your VPS

```bash
ssh root@YOUR_VPS_IP
```

## 3. Run One-Command Deployment

```bash
# Clone the repository
git clone https://github.com/yourusername/swiply.git
cd swiply

# Make deployment script executable
chmod +x deploy-vps.sh

# Run deployment
sudo ./deploy-vps.sh
```

## 4. Configure Environment

```bash
# Edit backend environment
nano .env
```

**Required changes in .env:**
```bash
POSTGRES_PASSWORD=your-strong-password-here
OPENAI_API_KEY=sk-your-api-key-here
ENCRYPTION_KEY=your-32-byte-key-here
```

Generate encryption key:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

```bash
# Edit frontend environment
nano frontend/.env
```

**Required changes in frontend/.env:**
```bash
VITE_API_URL=http://YOUR_VPS_IP:8000
```

## 5. Restart Services

```bash
docker-compose down
docker-compose up -d --build
```

## 6. Verify Deployment

```bash
# Check all services are running
docker-compose ps

# Check logs
docker-compose logs -f

# Test API
curl http://localhost:8000/docs
```

## 7. Access Your Application

Open in browser:
- **Frontend**: http://YOUR_VPS_IP:5173
- **API Docs**: http://YOUR_VPS_IP:8000/docs

## 8. Set Up Firewall (Optional but Recommended)

```bash
# Enable firewall
sudo ufw allow OpenSSH
sudo ufw allow 5173/tcp
sudo ufw allow 8000/tcp
sudo ufw enable

# Check status
sudo ufw status
```

## 9. Set Up Domain (Optional)

### A. Point Domain to VPS

In your domain registrar (GoDaddy, Namecheap, etc.):
- Add A record: `@` → `YOUR_VPS_IP`
- Add A record: `www` → `YOUR_VPS_IP`
- Add CNAME record: `api` → `@`

### B. Install Nginx

```bash
sudo apt install nginx -y
```

### C. Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/swiply
```

Paste this configuration:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}

server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/swiply /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### D. Get SSL Certificate (HTTPS)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com

# Update firewall
sudo ufw allow 'Nginx Full'
sudo ufw delete allow 5173/tcp
sudo ufw delete allow 8000/tcp
```

### E. Update Frontend Environment

```bash
nano frontend/.env
```

Change to:
```bash
VITE_API_URL=https://api.yourdomain.com
```

Restart:
```bash
docker-compose restart frontend
```

## 10. Maintenance Commands

```bash
# View logs
docker-compose logs -f

# Restart a service
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

## Troubleshooting

### Services won't start
```bash
docker-compose logs
docker-compose ps
```

### Port already in use
```bash
sudo lsof -i :8000
sudo kill -9 <PID>
```

### Out of memory
```bash
free -h
# Add swap if needed
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Firefox automation not working
```bash
docker-compose exec wttj python -m playwright install firefox
docker-compose exec wttj python -m playwright install-deps
docker-compose restart wttj
```

## Need Help?

1. Check logs: `docker-compose logs -f [service-name]`
2. Check service status: `docker-compose ps`
3. Check system resources: `docker stats`
4. Read full guide: `VPS_DEPLOYMENT_GUIDE.md`

## Security Checklist

- [ ] Changed default database password
- [ ] Set strong ENCRYPTION_KEY
- [ ] Added valid OPENAI_API_KEY
- [ ] Enabled firewall (ufw)
- [ ] Set up SSL certificate
- [ ] Configured Nginx reverse proxy
- [ ] Regular backups scheduled
- [ ] Monitoring set up

## Success!

Your Swiply application is now running on your VPS!

- Frontend: https://yourdomain.com (or http://YOUR_VPS_IP:5173)
- API: https://api.yourdomain.com (or http://YOUR_VPS_IP:8000)
