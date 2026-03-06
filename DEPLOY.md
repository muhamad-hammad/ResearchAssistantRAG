# Deploy to AWS EC2

## Step 1: Launch EC2 Instance
1. Go to **AWS Console → EC2 → Launch Instance**
2. Choose **Ubuntu Server 22.04 LTS**
3. Instance type: **t3.medium** (2 vCPU, 4GB RAM)
4. Create or use an existing key pair (`.pem` file — keep it safe!)
5. **Security Group** — open these ports:
   | Port | Source | Purpose |
   |------|--------|---------|
   | 22 | Your IP | SSH |
   | 80 | 0.0.0.0/0 | HTTP (App) |
6. Launch the instance, note the **Public IPv4 address**

---

## Step 2: Install Docker on the Instance
SSH into your EC2 instance:
```bash
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>
```

Install Docker & Docker Compose:
```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu
# Log out and back in for group to take effect
exit
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>
```

---

## Step 3: Deploy the Application
Clone your repository and configure:
```bash
git clone https://github.com/YOUR_USERNAME/ResearchAssistantRAG.git
cd ResearchAssistantRAG

# Create production .env file
cp .env.example .env
nano .env
```

Update `.env` for production (especially `SECRET_KEY` and LLM settings):
```env
SECRET_KEY=your-very-long-random-secret-key
LLM_PROVIDER=grok
GROK_API_KEY=xai-your-grok-api-key-here
```

Build and start all containers:
```bash
docker compose up -d --build
```

---

## Step 4: Run Database Migrations
```bash
docker compose exec backend alembic upgrade head
```

---

## Step 5: Access the App
Open your browser and go to:
```
http://<EC2_PUBLIC_IP>
```

---

## Useful Commands
```bash
# View logs
docker compose logs -f backend

# Stop all services
docker compose down

# Rebuild after code changes
docker compose up -d --build

# Check container status
docker compose ps
```
