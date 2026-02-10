# 🚀 Deployment Guide - Get Your Bot Online

Choose your deployment option below!

---

## ☁️ Option 1: Google Cloud Run (RECOMMENDED - FREE)

**Cost:** FREE (2M requests/month)  
**Uptime:** 24/7  
**Setup Time:** 30 minutes  
**Difficulty:** Medium

### Requirements:
- Google account
- `Dockerfile` (already created) ✅
- GitHub repo with your code ✅

### Step-by-Step:

#### 1. Enable Google Cloud APIs
```bash
# Install Google Cloud CLI: https://cloud.google.com/sdk/docs/install

gcloud auth login
gcloud config set project YOUR-PROJECT-ID
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

#### 2. Deploy to Cloud Run
```bash
cd C:\Users\micha\Desktop\ordinalrainbowsbot

gcloud run deploy rainbows-bot ^
  --source . ^
  --platform managed ^
  --region us-central1 ^
  --allow-unauthenticated ^
  --memory 512Mi ^
  --timeout 3600
```

#### 3. Configure Environment Variables
```bash
gcloud run update rainbows-bot ^
  --region us-central1 ^
  --update-env-vars "DISCORD_BOT_TOKEN=YOUR_TOKEN,GUILD_ID=YOUR_GUILD_ID,ADMIN_ROLE_ID=YOUR_ADMIN_ID"
```

Done! Your bot is now running 24/7 ✅

---

## 🚂 Option 2: Railway.app (EASY - $5/month)

**Cost:** $5/month  
**Uptime:** 24/7  
**Setup Time:** 5 minutes  
**Difficulty:** Easy ⭐

### Step-by-Step:

#### 1. Sign up
- Go to https://railway.app
- Sign up with GitHub

#### 2. Create New Project
- Click "New Project"
- Select "Deploy from GitHub repo"
- Select `ordinal-rainbows-bot` repo
- Click Deploy

#### 3. Add Environment Variables
In Railway dashboard:
- Go to **Variables**
- Add:
  - `DISCORD_BOT_TOKEN=YOUR_TOKEN`
  - `GUILD_ID=YOUR_GUILD_ID`
  - `ADMIN_ROLE_ID=YOUR_ADMIN_ID`
- Click Deploy

Done! Bot deploys automatically when you push to GitHub ✅

---

## 🦅 Option 3: Oracle Cloud (FREE - Always Free Tier)

**Cost:** FREE (forever)  
**Uptime:** 24/7  
**Setup Time:** 45 minutes  
**Difficulty:** Hard

### Requirements:
- Oracle account
- Credit card (for verification, not charged)

### Step-by-Step:

#### 1. Create VM Instance
- Go to https://cloud.oracle.com
- Create Free Tier account
- Create Compute Instance:
  - Image: Ubuntu 22.04
  - Shape: Ampere (ARM, always free)
  - Storage: 200GB
  - Create

#### 2. SSH into Instance
```bash
ssh ubuntu@YOUR_INSTANCE_IP
```

#### 3. Install Python & Bot
```bash
sudo apt update && sudo apt install python3-pip git
git clone https://github.com/YOUR_USERNAME/ordinal-rainbows-bot.git
cd ordinal-rainbows-bot
pip3 install -r requirements.txt
```

#### 4. Create .env File
```bash
nano .env
# Add your credentials
```

#### 5. Run with PM2 (keeps running)
```bash
sudo apt install npm
sudo npm install -g pm2
pm2 start bot.py --name "rainbows-bot"
pm2 startup
pm2 save
```

Done! Bot runs forever on free tier ✅

---

## 📤 GitHub Pages (For verify.html)

Deploy your verification page on GitHub Pages:

#### 1. Push verify.html to GitHub
Already done - it's in your repo! ✅

#### 2. Enable GitHub Pages
- Go to your repo settings
- Scroll to "GitHub Pages"
- Select `main` branch as source
- Save

#### 3. Your URL will be:
```
https://YOUR_USERNAME.github.io/ordinal-rainbows-bot/verify.html
```

Update your bot's verification link to use this URL!

---

## 🔄 Auto-Deploy from GitHub

### For Google Cloud Run:
1. Connect GitHub in Cloud Console
2. Select your repo
3. Setup automatic deploys on push

### For Railway:
Automatic! ✅ Every push to GitHub = auto-deploy

### For Oracle Cloud:
Setup GitHub Actions (advanced) or manual push

---

## 🎯 My Recommendation

### For Beginners:
→ **Railway.app** ($5/month)
- Easiest setup
- No credit card for free tier
- Auto-deploys from GitHub
- Best for starting out

### For Free (Budget):
→ **Google Cloud Run** (FREE)
- Zero cost for typical usage
- More features
- Bit more setup

### For Maximum Uptime:
→ **Oracle Cloud** (FREE forever)
- Never stops
- Free tier never expires
- Most setup required

---

## 📝 Environment Variables Checklist

Make sure these are set in your deployment:

```
DISCORD_BOT_TOKEN=YOUR_BOT_TOKEN
GUILD_ID=1470638312812445707
ADMIN_ROLE_ID=1438772393643348078
```

⚠️ **NEVER commit `.env` to GitHub!** Use deployment platform's environment variables instead.

---

## ✅ Testing After Deployment

1. Your bot should be online 24/7
2. Check `/verify` command works
3. Monitor logs for errors
4. Use `/stats` to see activity

---

## 💡 Pro Tips

1. **Use GitHub Actions** for automated testing
2. **Monitor logs** regularly
3. **Set up alerts** for errors
4. **Backup database** periodically
5. **Keep bot updated** with new features

---

## 🆘 Troubleshooting

### Bot not starting?
- Check logs in deployment platform
- Verify environment variables set correctly
- Check token is valid

### Connection errors?
- Verify discord.py can import
- Check internet connection
- Verify API endpoints accessible

### Database locked?
- Delete `bot_data.db` in deployment
- Bot will recreate it automatically

---

## 🎉 Congratulations!

Your bot is now running 24/7 in the cloud! 🚀

**Next:**
- Pin the `/verify` command in Discord
- Announce to your community
- Monitor activity with `/stats`
- Enjoy your verified RAINBOWS community!

---

**Happy deploying!** 🌈✨
