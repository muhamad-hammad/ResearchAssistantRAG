# Deploy to AWS EC2 (Free Tier) — Windows Guide

> **Free Tier:** 750 hrs/month of `t3.micro` + 30GB storage + 15GB bandwidth = **runs 24/7 free for 12 months**

---

## What You Need Before Starting
- [ ] AWS account (free tier activated)
- [ ] Grok API key from [console.x.ai](https://console.x.ai)
- [ ] Your project code on GitHub

---

## Step 1: Create Your EC2 Instance on AWS

1. Go to [AWS Console → EC2](https://console.aws.amazon.com/ec2) → click **Launch Instance**
2. Fill in:
   - **Name:** `research-assistant`
   - **AMI (Operating System):** `Ubuntu Server 22.04 LTS` *(scroll down, tick "Free tier eligible")*
   - **Instance type:** `t3.micro` *(Free tier eligible)*
3. **Key pair (for SSH login):**
   - Click **Create new key pair**
   - Name it anything (e.g. `my-key`)
   - Type: `RSA`, Format: `.pem`
   - Click **Create** → it auto-downloads `my-key.pem` to your Downloads folder
   - **⚠️ Keep this file safe — you can't re-download it!**
4. **Storage:** Click **Configure storage** → change `8 GiB` → `30 GiB`
5. **Security Group (Firewall):** Click **Edit** → Add these rules:

   | Type | Port | Source | Why |
   |------|------|--------|-----|
   | SSH | 22 | My IP | So only YOU can log in |
   | HTTP | 80 | 0.0.0.0/0 | So anyone can access the website |

6. Click **Launch Instance** → wait 60 seconds → click the instance → copy its **Public IPv4 address** (e.g. ``)

---

## Step 2: Connect to Your Server from Windows

> Open **PowerShell** (search in Start menu). Replace `your-key.pem` with your file name and `<IP>` with your server IP.

```powershell
# Move to where your .pem file is (usually Downloads)
cd $HOME\Downloads

# Fix file permissions (SSH requires this)
icacls mk1.pem /inheritance:r /grant:r "$($env:USERNAME):R"

# Connect to your server
```powershell
ssh -i mk1.pem ubuntu@[IP]
```
```

> You'll see `ubuntu@ip-xxx:~$` — you're now inside your server!

---

## Step 3: Prevent Out-of-Memory Crashes (Swap File)

> `t3.micro` only has 1GB RAM. The AI model needs ~400MB. This creates extra "virtual RAM" from disk.

```markdown
Paste this into your SSH session:

```bash
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## Step 4: Install Docker on the Server

Paste all of this at once:

```bash
sudo apt-get update -y
sudo apt-get install -y docker.io docker-compose-plugin
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu
```

Then **disconnect and reconnect** so the Docker permission takes effect:

```bash
exit
```

```powershell
# Back in PowerShell — reconnect
ssh -i 3350c794-717c-4240-bf1e-f289c6ff4cfb.pem ubuntu@<IP>
```

Check Docker works:
```bash
docker --version
# Should print: Docker version 24.x.x...
```

---

## Step 5: Upload Your Code to the Server

### Option A: From GitHub (Recommended)

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/ResearchAssistantRAG.git
cd ResearchAssistantRAG
```

### Option B: Copy files from your Windows PC

Back in PowerShell (new window), run:

```powershell
scp -i $HOME\Downloads\3350c794-717c-4240-bf1e-f289c6ff4cfb.pem -r D:\selfLearning\ResearchAssistantRAG ubuntu@<IP>:~/ResearchAssistantRAG
```

Then SSH back in and:
```bash
cd ResearchAssistantRAG
```

---

## Step 6: Configure the App

Create the production settings file:

```bash
cp .env.example .env
nano .env
```

Inside `nano`, edit these values (use arrow keys to move, Ctrl+O to save, Ctrl+X to exit):

```env
DATABASE_URL=postgresql://myuser:mypassword@db:5432/research_rag
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword
POSTGRES_DB=research_rag
REDIS_URL=redis://redis:6379/0
SECRET_KEY=paste-a-long-random-string-here
LLM_PROVIDER=grok
GROK_API_KEY=xai-your-actual-grok-key-here
```

> **Tip:** Generate a random SECRET_KEY with: `python3 -c "import secrets; print(secrets.token_hex(32))"`

---

## Step 7: Build and Start Everything

```bash
docker compose up -d --build
```

> ⏳ First build takes **10–15 minutes** (downloading Python packages). Go make a coffee ☕  
> Subsequent starts take ~30 seconds.

Watch the progress:
```bash
docker compose logs -f backend
# Press Ctrl+C to stop watching logs
```

---

## Step 8: Set Up the Database

```bash
docker compose exec backend alembic upgrade head
# Should print: INFO [alembic.runtime.migration] Running upgrade ...
```

---

## Step 9: Open the App 🎉

In your browser:
```
http://<EC2_PUBLIC_IP>
```

Register a new account, upload a PDF, and test the Chat!

---

## Keeping It Free

| Resource | Free Tier Limit | This App Uses |
|---|---|---|
| EC2 hours | 750 hrs/month | ~744 hrs (24/7) ✅ |
| EBS storage | 30GB | ~8GB ✅ |
| Data transfer | 15GB out/month | Typical usage ✅ |

> **💡 Save hours:** Stop the instance when not using it → AWS Console → EC2 → Select instance → **Instance State → Stop**

---

## Useful Commands (SSH Session)

```bash
# Check all containers are running
docker compose ps

# View live backend logs
docker compose logs -f backend

# Stop the app
docker compose down

# Update the app after code changes
git pull && docker compose up -d --build
```
