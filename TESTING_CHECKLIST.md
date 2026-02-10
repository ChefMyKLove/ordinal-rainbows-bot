# ✅ Bot Launch Checklist

Use this checklist before launching your bot to production.

## ⚙️ Configuration Checks

- [ ] Bot Token is valid (starts with YOUR_CLIENT_ID format)
- [ ] Guild ID is correct (1470638312812445707)
- [ ] Admin Role ID is correct (1438772393643348078)
- [ ] `.env` file exists with all values filled in
- [ ] `bot_data.db` doesn't exist yet (will auto-create on first run)

## 🎮 Discord Setup Checks

- [ ] Bot is invited to your server (use OAuth URL from QUICKSTART.md)
- [ ] Bot has these permissions:
  - [ ] Manage Roles
  - [ ] Send Messages
  - [ ] Use Slash Commands
  - [ ] Embed Links
- [ ] Privileged Intents enabled:
  - [ ] Server Members Intent
  - [ ] Message Content Intent
- [ ] Discord roles created:
  - [ ] Rainbow Holder
  - [ ] Legendary Rainbow
  - [ ] Epic Rainbow
  - [ ] Rare Rainbow
  - [ ] Common Rainbow
- [ ] Admin role ID matches your OrdinalsAdmin role

## 🤖 Bot Startup

- [ ] All dependencies installed: `pip list | grep discord`
- [ ] No syntax errors: `python -m py_compile bot.py`
- [ ] Bot module loads: `python -c "import bot; print('✅ OK')"`
- [ ] Start bot: `python bot.py`
- [ ] Bot shows login message: "✅ Bot logged in as RAINBOWS Bot"
- [ ] Bot syncs commands: "✅ Synced X commands"

## 🧪 First Verification Test

- [ ] Type `/verify` in Discord
- [ ] Bot responds with sign message
- [ ] Visit `verify.html` (locally or GitHub Pages)
- [ ] Sign message with your wallet
- [ ] Copy signature back to Discord
- [ ] Type `/submit YOUR_ADDRESS YOUR_SIGNATURE`
- [ ] Bot responds with success
- [ ] Roles are assigned to you

## 📊 Admin Commands Test

- [ ] `/stats` - Shows statistics
- [ ] `/setrole holder @Rainbow Holder` - Sets holder role
- [ ] `/setrole legendary @Legendary Rainbow` - Sets legendary role

## 🔐 Security Review

- [ ] .env file is NOT in version control
- [ ] Never share .env file contents
- [ ] Bot token never logged or displayed
- [ ] Only Discord IDs stored in database
- [ ] Signatures never stored, only verified

## 📱 Mobile Testing (Optional)

- [ ] Wallet works on phone/tablet
- [ ] Copy-paste of signature works
- [ ] Verification succeeds on mobile

## 🚀 Ready for Production?

If all checks pass above, you're ready to:
1. Announce bot in your Discord
2. Tell users to `/verify`
3. Put bot on persistent hosting (Google Cloud Run, Railway, etc.)
4. Monitor `/stats` for verification activity

---

## ⚠️ Known Issues & Fixes

### Issue: "Bot not responding to commands"
**Fix:**
1. Restart bot
2. Verify intents are enabled
3. Check bot has permission to send messages

### Issue: "Commands not showing in slash menu"
**Fix:**
1. Re-enable Message Content Intent
2. Restart bot
3. Type `/` and wait for command list to refresh

### Issue: "Roles not assigned"
**Fix:**
1. Check role IDs with `/stats`
2. Verify bot role is higher in hierarchy than assigned roles
3. Verify bot has Manage Roles permission

### Issue: "Database locked error"
**Fix:**
1. Delete `bot_data.db`
2. Restart bot (it will auto-create new database)

---

**Last Updated:** February 2026
**Status:** ✅ Ready for Launch
