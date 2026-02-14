"""
BSV ORDINALS DISCORD GATING BOT - CLOUD RUN VERSION
====================================================
"""

import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import asyncio
import json
import hashlib
import secrets
import base58
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import aiohttp
import os
from aiohttp import web

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    GUILD_ID = int(os.getenv("GUILD_ID", "0"))
    ADMIN_ROLE_ID = int(os.getenv("ADMIN_ROLE_ID", "0"))
    API_BASE = "https://ordinals.gorillapool.io/api"
    REVERIFY_HOURS = 168
    MAX_VERIFICATIONS_PER_HOUR = 5
    
    COLLECTIONS = {
        "ORDINAL 🌈 RAINBOWS Vol. 1": {
            "collection_id": "ee4ae45304c28d0fa6_0",
            "roles": {
                "holder": None,
                "legendary": None,
                "epic": None,
                "rare": None
            },
            "rarity_tiers": {
                "legendary": 2,
                "epic": 5,
                "rare": 10,
                "common": 999
            }
        }
    }

config = Config()

# ============================================================================
# DATABASE
# ============================================================================

async def init_database():
    async with aiosqlite.connect("bot_data.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS verifications (
                discord_id TEXT PRIMARY KEY,
                last_verified TIMESTAMP,
                assigned_roles TEXT,
                verification_count INTEGER DEFAULT 0
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS collections (
                collection_id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection_name TEXT UNIQUE,
                config TEXT
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS rate_limits (
                discord_id TEXT,
                timestamp TIMESTAMP,
                PRIMARY KEY (discord_id, timestamp)
            )
        """)
        
        await db.commit()

# ============================================================================
# BSV SIGNATURE VERIFICATION (Simplified)
# ============================================================================

class BSVVerifier:
    @staticmethod
    def verify_signature(message: str, address: str, signature_hex: str) -> bool:
        """Simplified BSV signature verification"""
        try:
            # For now, basic validation
            # In production, implement full ECDSA verification
            if len(signature_hex) < 130:  # Hex signature should be ~130 chars
                return False
            if not address.startswith('1'):  # P2PKH mainnet addresses start with 1
                return False
            return True
        except Exception as e:
            print(f"Signature verification error: {e}")
            return False

# ============================================================================
# 1SAT ORDINALS API
# ============================================================================

class OrdinalsAPI:
    @staticmethod
    async def get_address_ordinals(address: str, collection_id: str = None) -> List[Dict]:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{config.API_BASE}/txos/address/{address}/unspent?limit=1000"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status != 200:
                        return []
                    
                    data = await resp.json()
                    ordinals = []
                    
                    for utxo in data:
                        if 'origin' in utxo and utxo.get('satoshis') == 1:
                            ordinal_data = await OrdinalsAPI.get_inscription_data(utxo['origin'])
                            if ordinal_data:
                                if collection_id:
                                    inscription_collection = ordinal_data.get('map', {}).get('subTypeData', {}).get('collectionId')
                                    if inscription_collection == collection_id:
                                        ordinals.append(ordinal_data)
                                else:
                                    ordinals.append(ordinal_data)
                    
                    return ordinals
        except Exception as e:
            print(f"API error: {e}")
            return []
    
    @staticmethod
    async def get_inscription_data(origin: str) -> Optional[Dict]:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{config.API_BASE}/inscriptions/origin/{origin}"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except:
            pass
        return None

# ============================================================================
# RARITY CALCULATOR
# ============================================================================

class RarityCalculator:
    @staticmethod
    async def calculate_rarity(ordinals: List[Dict], collection_config: Dict) -> str:
        if not ordinals:
            return None
        
        name_counts = {}
        for ordinal in ordinals:
            name = ordinal.get('file', {}).get('name') or ordinal.get('map', {}).get('name', 'Unknown')
            base_name = name.split('#')[0].strip()
            if base_name not in name_counts:
                name_counts[base_name] = 0
            name_counts[base_name] += 1
        
        min_count = min(name_counts.values())
        
        tiers = collection_config.get('rarity_tiers', {})
        for tier, max_count in sorted(tiers.items(), key=lambda x: x[1]):
            if min_count <= max_count:
                return tier
        
        return 'common'

# ============================================================================
# DISCORD BOT
# ============================================================================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
verification_sessions = {}

@bot.event
async def on_ready():
    await init_database()
    print(f'✅ Bot logged in as {bot.user}')
    print(f'📊 Serving {len(bot.guilds)} servers')
    
    try:
        synced = await bot.tree.sync()
        print(f'✅ Synced {len(synced)} commands')
    except Exception as e:
        print(f'❌ Failed to sync commands: {e}')

# ============================================================================
# COMMANDS
# ============================================================================

@bot.tree.command(name="verify", description="Verify your BSV ordinal ownership")
async def verify(interaction: discord.Interaction):
    async with aiosqlite.connect("bot_data.db") as db:
        hour_ago = datetime.now() - timedelta(hours=1)
        cursor = await db.execute(
            "SELECT COUNT(*) FROM rate_limits WHERE discord_id = ? AND timestamp > ?",
            (str(interaction.user.id), hour_ago)
        )
        count = (await cursor.fetchone())[0]
        
        if count >= config.MAX_VERIFICATIONS_PER_HOUR:
            await interaction.response.send_message(
                "⏱️ Rate limit exceeded. Please try again later.",
                ephemeral=True
            )
            return
    
    nonce = secrets.token_hex(16)
    message = f"Discord_Verify_{int(datetime.now().timestamp())}_{nonce}"
    
    verification_sessions[interaction.user.id] = {
        'nonce': nonce,
        'message': message,
        'timestamp': datetime.now()
    }
    
    embed = discord.Embed(
        title="🔐 BSV Ordinals Verification",
        description="Sign this message with your BSV wallet to verify ownership",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="Message to Sign",
        value=f"```{message}```",
        inline=False
    )
    
    embed.add_field(
        name="📱 Supported Wallets",
        value="• Yours Wallet\n• Panda Wallet\n• HandCash",
        inline=False
    )
    
    embed.add_field(
        name="📝 Next Steps",
        value=(
            "1. Open your BSV wallet\n"
            "2. Find 'Sign Message' feature\n"
            "3. Sign the message above\n"
            "4. Use `/submit <address> <signature>`"
        ),
        inline=False
    )
    
    embed.set_footer(text="⏰ Expires in 10 minutes")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="submit", description="Submit your signed message")
@app_commands.describe(
    address="Your BSV address",
    signature="Signature from your wallet"
)
async def submit(interaction: discord.Interaction, address: str, signature: str):
    await interaction.response.defer(ephemeral=True)
    
    if interaction.user.id not in verification_sessions:
        await interaction.followup.send(
            "❌ No verification session found. Please run `/verify` first.",
            ephemeral=True
        )
        return
    
    session = verification_sessions[interaction.user.id]
    
    if datetime.now() - session['timestamp'] > timedelta(minutes=10):
        del verification_sessions[interaction.user.id]
        await interaction.followup.send(
            "⏰ Verification session expired. Please run `/verify` again.",
            ephemeral=True
        )
        return
    
    if not BSVVerifier.verify_signature(session['message'], address, signature):
        await interaction.followup.send(
            "❌ Invalid signature. Please ensure you signed the correct message.",
            ephemeral=True
        )
        return
    
    ordinals = await OrdinalsAPI.get_address_ordinals(
        address,
        config.COLLECTIONS["ORDINAL 🌈 RAINBOWS Vol. 1"]["collection_id"]
    )
    
    if not ordinals:
        await interaction.followup.send(
            "❌ No RAINBOW ordinals found at this address.",
            ephemeral=True
        )
        return
    
    rarity = await RarityCalculator.calculate_rarity(
        ordinals,
        config.COLLECTIONS["ORDINAL 🌈 RAINBOWS Vol. 1"]
    )
    
    guild = bot.get_guild(config.GUILD_ID)
    member = guild.get_member(interaction.user.id)
    
    roles_to_assign = []
    role_config = config.COLLECTIONS["ORDINAL 🌈 RAINBOWS Vol. 1"]["roles"]
    
    if role_config["holder"]:
        role = guild.get_role(role_config["holder"])
        if role:
            roles_to_assign.append(role)
    
    if rarity and role_config.get(rarity):
        role = guild.get_role(role_config[rarity])
        if role:
            roles_to_assign.append(role)
    
    await member.add_roles(*roles_to_assign)
    
    async with aiosqlite.connect("bot_data.db") as db:
        await db.execute(
            """INSERT OR REPLACE INTO verifications 
               (discord_id, last_verified, assigned_roles, verification_count)
               VALUES (?, ?, ?, COALESCE((SELECT verification_count FROM verifications WHERE discord_id = ?) + 1, 1))""",
            (str(interaction.user.id), datetime.now(), json.dumps([r.id for r in roles_to_assign]), str(interaction.user.id))
        )
        
        await db.execute(
            "INSERT INTO rate_limits (discord_id, timestamp) VALUES (?, ?)",
            (str(interaction.user.id), datetime.now())
        )
        
        await db.commit()
    
    del verification_sessions[interaction.user.id]
    
    embed = discord.Embed(
        title="✅ Verification Successful!",
        description=f"You own **{len(ordinals)}** RAINBOW ordinals",
        color=discord.Color.green()
    )
    
    if rarity:
        embed.add_field(name="🏆 Highest Rarity", value=rarity.capitalize(), inline=False)
    
    if roles_to_assign:
        embed.add_field(
            name="🎭 Roles Assigned",
            value="\n".join([f"• {role.mention}" for role in roles_to_assign]),
            inline=False
        )
    
    await interaction.followup.send(embed=embed, ephemeral=True)

# ============================================================================
# ADMIN COMMANDS
# ============================================================================

def is_admin():
    async def predicate(interaction: discord.Interaction) -> bool:
        return any(role.id == config.ADMIN_ROLE_ID for role in interaction.user.roles)
    return app_commands.check(predicate)

@bot.tree.command(name="setrole", description="[ADMIN] Set collection role")
@app_commands.describe(
    tier="Rarity tier or 'holder'",
    role="Discord role to assign"
)
@is_admin()
async def setrole(interaction: discord.Interaction, tier: str, role: discord.Role):
    if tier in ["holder", "legendary", "epic", "rare", "common"]:
        config.COLLECTIONS["ORDINAL 🌈 RAINBOWS Vol. 1"]["roles"][tier] = role.id
        await interaction.response.send_message(
            f"✅ Set {tier} role to {role.mention}",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "❌ Invalid tier. Use: holder, legendary, epic, rare, common",
            ephemeral=True
        )

@bot.tree.command(name="stats", description="[ADMIN] View verification statistics")
@is_admin()
async def stats(interaction: discord.Interaction):
    async with aiosqlite.connect("bot_data.db") as db:
        cursor = await db.execute("SELECT COUNT(*) FROM verifications")
        total_verified = (await cursor.fetchone())[0]
        
        cursor = await db.execute(
            "SELECT COUNT(*) FROM verifications WHERE last_verified > ?",
            (datetime.now() - timedelta(days=7),)
        )
        week_verified = (await cursor.fetchone())[0]
    
    embed = discord.Embed(
        title="📊 Bot Statistics",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="Total Verified Users", value=str(total_verified), inline=True)
    embed.add_field(name="Verified This Week", value=str(week_verified), inline=True)
    embed.add_field(name="Active Sessions", value=str(len(verification_sessions)), inline=True)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ============================================================================
# WEB SERVER FOR CLOUD RUN (CRITICAL!)
# ============================================================================

async def health_check(request):
    """Health check endpoint for Cloud Run"""
    return web.Response(text="Bot is running", status=200)

async def run_web_server():
    """Run HTTP server on port 8080 for Cloud Run"""
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    print(f"🌐 Web server running on port {port}")
    
    # Keep server running forever
    while True:
        await asyncio.sleep(3600)

# ============================================================================
# MAIN - RUN BOTH BOT AND WEB SERVER
# ============================================================================

async def main():
    """Run both Discord bot and web server concurrently"""
    await asyncio.gather(
        bot.start(config.BOT_TOKEN),
        run_web_server()
    )

if __name__ == "__main__":
    print("🚀 Starting BSV Ordinals Discord Bot...")
    asyncio.run(main())

    