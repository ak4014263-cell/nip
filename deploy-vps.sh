#!/bin/bash
# Swiply VPS Deployment Script
# Run this script on your VPS after cloning the repository

set -e  # Exit on error

echo "========================================"
echo "  Swiply VPS Deployment Script"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}This script needs sudo privileges. Please run with sudo.${NC}"
    exit 1
fi

# 1. Update system
echo -e "${GREEN}[1/7] Updating system...${NC}"
apt update && apt upgrade -y

# 2. Install Docker
echo -e "${GREEN}[2/7] Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    echo -e "${GREEN}✓ Docker installed${NC}"
else
    echo -e "${YELLOW}✓ Docker already installed${NC}"
fi

# 3. Install Docker Compose
echo -e "${GREEN}[3/7] Installing Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✓ Docker Compose installed${NC}"
else
    echo -e "${YELLOW}✓ Docker Compose already installed${NC}"
fi

# 4. Install Node.js
echo -e "${GREEN}[4/7] Installing Node.js...${NC}"
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt install -y nodejs
    echo -e "${GREEN}✓ Node.js installed${NC}"
else
    echo -e "${YELLOW}✓ Node.js already installed ($(node -v))${NC}"
fi

# 5. Set up environment files
echo -e "${GREEN}[5/7] Setting up environment files...${NC}"
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${YELLOW}⚠ Please edit .env with your production values!${NC}"
    else
        echo -e "${RED}✗ .env.example not found!${NC}"
    fi
else
    echo -e "${YELLOW}✓ .env already exists${NC}"
fi

if [ ! -f frontend/.env ]; then
    if [ -f frontend/.env.example ]; then
        cp frontend/.env.example frontend/.env
        echo -e "${YELLOW}⚠ Please edit frontend/.env with your production values!${NC}"
    fi
else
    echo -e "${YELLOW}✓ frontend/.env already exists${NC}"
fi

# 6. Install frontend dependencies
echo -e "${GREEN}[6/7] Installing frontend dependencies...${NC}"
cd frontend
npm install
cd ..
echo -e "${GREEN}✓ Frontend dependencies installed${NC}"

# 7. Start services with Docker Compose
echo -e "${GREEN}[7/7] Starting services with Docker Compose...${NC}"
docker-compose down 2>/dev/null || true
docker-compose up -d --build

echo ""
echo -e "${GREEN}========================================"
echo "  Deployment Complete!"
echo "========================================${NC}"
echo ""
echo "Your services are starting up. Please wait 1-2 minutes for everything to initialize."
echo ""
echo "Access your application at:"
echo "  Frontend: http://$(curl -s ifconfig.me):5173"
echo "  API:      http://$(curl -s ifconfig.me):8000"
echo "  API Docs: http://$(curl -s ifconfig.me):8000/docs"
echo ""
echo "Useful commands:"
echo "  View logs:        docker-compose logs -f"
echo "  Stop services:    docker-compose down"
echo "  Restart services: docker-compose restart"
echo ""
echo -e "${YELLOW}⚠ IMPORTANT:${NC}"
echo "1. Edit .env and frontend/.env with your production values"
echo "2. Set up firewall: ufw allow 5173/tcp && ufw allow 8000/tcp"
echo "3. Consider setting up Nginx reverse proxy and SSL (see VPS_DEPLOYMENT_GUIDE.md)"
echo ""
