# 🚀 BSV Ordinals Discord Bot - Complete Deployment Guide

## 📋 Table of Contents
1. [Discord Bot Setup](#discord-bot-setup)
2. [Local Testing](#local-testing)
3. [Google Cloud Run Deployment](#google-cloud-run-deployment)
4. [GitHub Pages for Web Verification](#github-pages-setup)
5. [Configuration](#configuration)
6. [Admin Commands](#admin-commands)
7. [Troubleshooting](#troubleshooting)

---

## 🤖 Discord Bot Setup

### Step 1: Create Discord Application

1. Go to https://discord.com/developers/applications
2. Click "New Application"
3. Name it "BSV Ordinals Gatekeeper" (or your choice)
4. Go to the "Bot" tab
5. Click "Add Bot"
6. **IMPORTANT:** Enable these Privileged Gateway Intents:
   - ✅ Server Members Intent
   - ✅ Message Content Intent
7. Copy your Bot Token (you'll need this later)

### Step 2: Set Bot Permissions

1. Go to OAuth2 → URL Generator
2. Select scopes:
   - ✅ `bot`
   - ✅ `applications.commands`
3. Select bot permissions:
   - ✅ Manage Roles
   - ✅ Read Messages/View Channels
   - ✅ Send Messages
   - ✅ Use Slash Commands
4. Copy the generated URL and open it to invite the bot to your server

### Step 3: Get Server & Role IDs

**Enable Developer Mode in Discord:**
- User Settings → Advanced → Developer Mode (toggle ON)

**Get Guild ID:**
- Right-click your server name → Copy Server ID

**Get Admin Role ID:**
- Server Settings → Roles → Right-click your admin role → Copy Role ID

---

## 💻 Local Testing

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)
- Git

### Step 1: Setup Project

```bash
# Create project directory
mkdir bsv-discord-bot
cd bsv-discord-bot

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment

Create a `.env` file:

```env
DISCORD_BOT_TOKEN=your_bot_token_from_discord
GUILD_ID=your_server_id
ADMIN_ROLE_ID=your_admin_role_id
```

### Step 3: Run Bot Locally

```bash
python bot.py
```

You should see:
```
🚀 Starting BSV Ordinals Discord Bot...
✅ Bot logged in as YourBotName#1234
✅ Synced 3 commands
```

### Step 4: Test Commands

In Discord:
1. `/verify` - Should show verification instructions
2. `/setrole holder @RoleHere` (as admin) - Set holder role
3. `/stats` (as admin) - View statistics

---

## ☁️ Google Cloud Run Deployment (FREE)

### Why Google Cloud Run?
- ✅ 2 million requests/month FREE
- ✅ Always-on (not serverless cold starts)
- ✅ Auto-scaling
- ✅ Easy deployment

### Step 1: Install Google Cloud SDK

**Option A: Cloud Shell (Easiest - Browser-based)**
1. Go to https://console.cloud.google.com
2. Click the terminal icon (top right) to activate Cloud Shell
3. Skip to Step 3

**Option B: Local Installation**

**Windows:**
```bash
# Download installer from:
https://cloud.google.com/sdk/docs/install
```

**macOS:**
```bash
# Using Homebrew
brew install --cask google-cloud-sdk
```

**Linux:**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

### Step 2: Initialize gcloud

```bash
# Login
gcloud auth login

# Create new project (or use existing)
gcloud projects create bsv-discord-bot-12345 --name="BSV Discord Bot"

# Set project
gcloud config set project bsv-discord-bot-12345

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### Step 3: Create Dockerfile

Create `Dockerfile` in your project:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .

# Create directory for database
RUN mkdir -p /app/data

CMD ["python", "bot.py"]
```

### Step 4: Create Cloud Build Configuration

Create `cloudbuild.yaml`:

```yaml
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/bsv-discord-bot', '.']
  
  # Push to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/bsv-discord-bot']
  
  # Deploy to Cloud Run
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'bsv-discord-bot'
      - '--image=gcr.io/$PROJECT_ID/bsv-discord-bot'
      - '--platform=managed'
      - '--region=us-central1'
      - '--allow-unauthenticated'
      - '--set-env-vars=DISCORD_BOT_TOKEN=${_BOT_TOKEN},GUILD_ID=${_GUILD_ID},ADMIN_ROLE_ID=${_ADMIN_ROLE_ID}'

images:
  - 'gcr.io/$PROJECT_ID/bsv-discord-bot'
```

### Step 5: Deploy to Cloud Run

```bash
# Deploy (replace with your actual values)
gcloud builds submit \
  --substitutions=_BOT_TOKEN="YOUR_BOT_TOKEN",_GUILD_ID="YOUR_GUILD_ID",_ADMIN_ROLE_ID="YOUR_ADMIN_ROLE_ID"
```

**Alternative: Manual Deployment**

```bash
# Build image
docker build -t gcr.io/YOUR_PROJECT_ID/bsv-discord-bot .

# Push to registry
docker push gcr.io/YOUR_PROJECT_ID/bsv-discord-bot

# Deploy
gcloud run deploy bsv-discord-bot \
  --image gcr.io/YOUR_PROJECT_ID/bsv-discord-bot \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DISCORD_BOT_TOKEN="YOUR_TOKEN",GUILD_ID="YOUR_GUILD_ID",ADMIN_ROLE_ID="YOUR_ADMIN_ROLE"
```

### Step 6: Keep Bot Running 24/7

Discord bots need a persistent connection. Use Cloud Scheduler:

```bash
# Create a scheduler job that pings your service
gcloud scheduler jobs create http keep-bot-alive \
  --schedule="*/5 * * * *" \
  --uri="https://bsv-discord-bot-xxxxx.run.app/health" \
  --http-method=GET
```

**Add health endpoint to bot.py:**

```python
from aiohttp import web

async def health_check(request):
    return web.Response(text="OK")

# After bot.run(), add:
async def run_web_server():
    app = web.Application()
    app.router.add_get('/health', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv('PORT', 8080)))
    await site.start()

# Run both bot and web server
async def main():
    await asyncio.gather(
        bot.start(config.BOT_TOKEN),
        run_web_server()
    )

asyncio.run(main())
```

### Step 7: Monitor & Logs

```bash
# View logs
gcloud run services logs read bsv-discord-bot --region us-central1 --limit 50

# Check service status
gcloud run services describe bsv-discord-bot --region us-central1
```

---

## 📄 GitHub Pages Setup

### Step 1: Create GitHub Repository

```bash
# Initialize git
git init
git add verify.html
git commit -m "Add verification page"

# Create GitHub repo (on github.com)
# Then push
git remote add origin https://github.com/YOUR_USERNAME/bsv-verify.git
git push -u origin main
```

### Step 2: Enable GitHub Pages

1. Go to your repo on GitHub
2. Settings → Pages
3. Source: Deploy from branch
4. Branch: `main` / `(root)`
5. Save

Your page will be live at:
```
https://YOUR_USERNAME.github.io/bsv-verify/verify.html
```

### Step 3: Update Bot Messages

In `bot.py`, update the verification embed:

```python
embed.add_field(
    name="🌐 Web Verification (Easier)",
    value=f"Visit: https://YOUR_USERNAME.github.io/bsv-verify/verify.html?m={message}",
    inline=False
)
```

---

## ⚙️ Configuration

### Setting Up Collection Roles

1. Create Discord roles:
   - `@Rainbow Holder` (any rainbow owner)
   - `@Legendary Rainbow` (1-2 of a kind)
   - `@Epic Rainbow` (3-5 of a kind)
   - `@Rare Rainbow` (6-10 of a kind)

2. Set roles via Discord commands:
```
/setrole holder @Rainbow Holder
/setrole legendary @Legendary Rainbow
/setrole epic @Epic Rainbow
/setrole rare @Rare Rainbow
```

### Updating Collection ID

If you get the full collection origin list:

```python
# In bot.py, update:
"ORDINAL 🌈 RAINBOWS Vol. 1": {
    "collection_id": "YOUR_COLLECTION_ID_HERE",
    # ... rest of config
}
```

### Adding New Collections

```python
config.COLLECTIONS["New Collection Name"] = {
    "collection_id": "collection_origin_id",
    "roles": {
        "holder": None,
        "legendary": None,
        # ...
    },
    "rarity_tiers": {
        "legendary": 2,
        "epic": 5,
        # ...
    }
}
```

---

## 🛠️ Admin Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/setrole <tier> <@role>` | Set role for a tier | `/setrole holder @RainbowHolder` |
| `/stats` | View verification stats | `/stats` |
| `/verify` | Start verification (any user) | `/verify` |
| `/submit <address> <sig>` | Submit signature (any user) | `/submit 1ABC... 3045...` |

---

## 🐛 Troubleshooting

### Bot Not Responding
```bash
# Check if bot is running
gcloud run services describe bsv-discord-bot --region us-central1

# View recent logs
gcloud run services logs read bsv-discord-bot --limit 100
```

### Commands Not Showing
- Wait 1 hour for Discord to sync globally
- Or kick and re-invite bot
- Check bot has `applications.commands` scope

### Signature Verification Failing
- Ensure user signed EXACT message (case-sensitive, no extra spaces)
- Signature should be hex format (no 0x prefix)
- Address should be P2PKH mainnet (starts with 1)

### Rate Limit Hit
- Default: 5 verifications per hour per user
- Adjust in `config.MAX_VERIFICATIONS_PER_HOUR`

### Database Issues
```bash
# Reset database
rm bot_data.db
# Bot will recreate on next startup
```

---

## 💰 Cost Monitoring

### Free Tier Limits
- **Cloud Run:** 2M requests/month
- **Cloud Build:** 120 build-minutes/day
- **Container Registry:** 5GB storage

### Check Usage
```bash
# View quotas
gcloud compute project-info describe --project YOUR_PROJECT_ID
```

### Set Budget Alerts
1. Go to https://console.cloud.google.com/billing
2. Budgets & alerts
3. Create budget: $5/month with 50%, 90%, 100% alerts

---

## 🔒 Security Best Practices

1. **Never commit .env files**
   - Add `.env` to `.gitignore`

2. **Rotate bot token** if exposed
   - Discord Developer Portal → Bot → Reset Token

3. **Limit admin commands**
   - Only give admin role to trusted users

4. **Monitor logs** for suspicious activity
   ```bash
   gcloud run services logs read bsv-discord-bot --filter="severity>=ERROR"
   ```

---

## 📞 Support

### Useful Links
- [1Sat Ordinals Discord](https://discord.gg/1satordinals)
- [Yours Wallet Docs](https://yours-wallet.gitbook.io/provider-api)
- [Google Cloud Run Docs](https://cloud.google.com/run/docs)

### Common Issues
- **"Bot offline"**: Check Cloud Run service status
- **"Invalid signature"**: Verify message format matches exactly
- **"No ordinals found"**: Confirm collection_id is correct

---

## 🎉 You're Done!

Your bot should now be:
✅ Running 24/7 on Google Cloud Run (FREE)  
✅ Verifying BSV ordinal ownership  
✅ Assigning roles based on rarity  
✅ Using privacy-first verification  

**Test it:** `/verify` in your Discord server!