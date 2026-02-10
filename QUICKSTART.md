# 🚀 BSV Ordinals Bot - SETUP COMPLETE! ✅

## Your Bot is Ready!

All dependencies are installed and the bot is configured with your credentials:
- ✅ Bot Token: `YOUR_BOT_TOKEN` (configured in .env)
- ✅ Guild ID: `1470638312812445707`
- ✅ Admin Role ID: `1438772393643348078`

---

## 🎯 Next Steps

### Step 1: Add Bot to Your Server ✅
You need to invite the bot to your Discord server.

**URL**: 
```
https://discord.com/api/oauth2/authorize?client_id=1470638312812445707&permissions=268435456&scope=bot%20applications.commands
```

[Click here to invite the bot](https://discord.com/api/oauth2/authorize?client_id=1470638312812445707&permissions=268435456&scope=bot%20applications.commands)

### Step 2: Enable Privileged Intents ⚙️
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your "RAINBOWS Bot" application
3. Go to **Bot** tab
4. Under **Privileged Gateway Intents**, toggle ON:
   - ✅ `Server Members Intent`
   - ✅ `Message Content Intent`
5. Click **Save Changes**

### Step 3: Create Discord Roles 👥
In your Discord server, create these roles:
- `Rainbow Holder` - for users with any RAINBOWS ordinal
- `Legendary Rainbow` - for legendary tier holders
- `Epic Rainbow` - for epic tier holders  
- `Rare Rainbow` - for rare tier holders
- `Common Rainbow` - for common tier holders

### Step 4: Start the Bot 🤖

**Windows:**
```bash
# Double-click run_bot.bat
```
Or in command prompt:
```
cd C:\Users\micha\Desktop\ordinalrainbowsbot
python bot.py
```

**macOS/Linux:**
```bash
cd /path/to/ordinalrainbowsbot
python bot.py
```

### Step 5: Verify Bot is Running ✅
You should see:
```
✅ Bot logged in as RAINBOWS Bot
📊 Serving 1 servers
✅ Synced X commands
```

---

## 🔗 Configure Collection Roles

Once the bot is online, use these admin commands in Discord:

```
/setrole holder @Rainbow Holder
/setrole legendary @Legendary Rainbow
/setrole epic @Epic Rainbow
/setrole rare @Rare Rainbow
/setrole common @Common Rainbow
```

---

## 🧪 Test Verification Flow

### User Verification:
1. User types: `/verify`
2. Bot sends verification message with signing link
3. User visits `verify.html` and signs with wallet
4. User returns to Discord and types: `/submit ADDRESS SIGNATURE`
5. Bot verifies and assigns roles! 🎉

### Admin Check Statistics:
```
/stats
```
Shows total verified users and active sessions.

---

## 📁 Project Structure

```
ordinalrainbowsbot/
├── bot.py                 # Main bot code
├── verify.html            # Web verification page
├── requirements.txt       # Python dependencies
├── .env                   # Your credentials (KEEP SECRET!)
├── bot_data.db           # SQLite database (auto-created)
├── run_bot.bat           # Windows launcher
├── run_bot.sh            # macOS/Linux launcher
└── fetch_collection.py   # Collection scraper utility
```

---

## 🔧 Configuration

### Bot Settings (in `bot.py`)
Edit these if needed:
```python
MAX_VERIFICATIONS_PER_HOUR = 5      # Rate limit
REVERIFY_HOURS = 168                 # 7 days
```

### Collection Configuration (in `bot.py`)
```python
COLLECTIONS = {
    "ORDINAL 🌈 RAINBOWS Vol. 1": {
        "collection_id": "ee4ae45304c28d0fa6_0",
        "rarity_tiers": {
            "legendary": 2,   # 1-2 items
            "epic": 5,        # 3-5 items
            "rare": 10,       # 6-10 items
            "common": 999     # 11+ items
        }
    }
}
```

---

## 🪲 Troubleshooting

### Bot won't start?
1. Check `.env` file has correct token
2. Verify Python 3.12+ installed: `python --version`
3. Reinstall dependencies: `pip install -r requirements.txt`

### Commands not showing in Discord?
1. Enable Message Content Intent in Developer Portal
2. Give bot Manage Roles permission
3. Restart bot: stop and run again

### Verification fails?
1. Check bot has Manage Roles permission
2. Ensure role IDs match: `/stats` shows all roles
3. Check bot has higher role hierarchy than assigned roles

### Database issues?
Delete `bot_data.db` and restart bot - it will recreate the database

---

## 🌐 Web Verification Page

The `verify.html` file handles wallet signing. To use it:

1. **Local Testing:**
   - Open `verify.html` in your browser
   - Testing signing flow locally

2. **Production (GitHub Pages):**
   - Fork or create GitHub repo
   - Upload `verify.html` to repo root
   - Enable GitHub Pages
   - Update signing link in bot commands

**Example GitHub Pages URL:**
```
https://yourusername.github.io/ordinalrainbowsbot/verify.html?m=SIGNING_MESSAGE
```

---

## 🚀 Deployment Options

### Option 1: Keep Running Locally
- Simplest setup
- Bot only runs while script is active
- Good for testing

### Option 2: Google Cloud Run (FREE)
- [Complete guide in DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- 2M free requests/month
- Always-on bot
- Setup time: 30 mins

### Option 3: Railway.app ($5/month)
- One-click deployment
- Auto-deploy from GitHub
- Built-in monitoring

---

## 📊 Bot Commands

### User Commands
- `/verify` - Start verification process
- `/submit ADDRESS SIGNATURE` - Submit signed message

### Admin Commands
- `/setrole TIER @ROLE` - Set tier role (holder, legendary, epic, rare, common)
- `/stats` - View verification statistics

---

## 🔐 Privacy & Security

✅ **What's stored:**
- Discord user ID
- Verification timestamp
- Assigned roles

❌ **What's NOT stored:**
- BSV addresses
- Signatures
- Private keys
- Wallet info

All blockchain verification happens client-side!

---

## 📞 Support & Resources

- [1Sat Ordinals Docs](https://docs.1satordinals.com/)
- [Discord.py Docs](https://discordpy.readthedocs.io/)
- [Yours Wallet API](https://yours-wallet.gitbook.io/provider-api)
- [Discord Developer Portal](https://discord.com/developers/applications)

---

## 🎉 You're All Set!

Your bot is ready to go live! Here's what to do now:

1. **Invite bot to server** (link above)
2. **Enable intents** (Developer Portal)
3. **Create roles** (Discord server settings)
4. **Set role IDs** (`/setrole` commands)
5. **Run the bot** (`python bot.py`)

Then announce `/verify` to your community! 🚀

---

**Built for RAINBOWS Vol. 1 ordinals on BSV blockchain** 🌈
