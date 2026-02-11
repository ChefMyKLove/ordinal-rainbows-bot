"""
BSV ORDINALS DISCORD GATING BOT
================================
Multi-wallet verification bot for BSV 1Sat Ordinals collections
Supports: Yours Wallet, MetaNet wallets, HandCash
Privacy-first: No server-side credential storage
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
import urllib.request
import urllib.error
from ecdsa import VerifyingKey, SECP256k1, BadSignatureError
from ecdsa.util import sigdecode_der
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Bot configuration - edit these values"""
    
    # Discord settings
    BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    GUILD_ID = int(os.getenv("GUILD_ID", "123456789"))  # Your server ID
    ADMIN_ROLE_ID = int(os.getenv("ADMIN_ROLE_ID", "987654321"))
    
    # API endpoints
    API_BASE = "https://ordinals.gorillapool.io/api"
    
    # Re-verification period (hours)
    REVERIFY_HOURS = 168  # 7 days
    
    # Rate limiting
    MAX_VERIFICATIONS_PER_HOUR = 5
    
    # Collection configuration
    COLLECTIONS = {
        "ORDINAL 🌈 RAINBOWS Vol. 1": {
            "collection_id": "ee4ae45304c28d0fa6_0",  # Your collection ID
            "roles": {
                "holder": None,  # Will be set via admin commands
                "legendary": None,
                "epic": None,
                "rare": None
            },
            "rarity_tiers": {
                "legendary": 2,   # Max count for legendary
                "epic": 5,        # Max count for epic
                "rare": 10,       # Max count for rare
                "common": 999     # Everything else
            }
        }
    }

config = Config()

# ============================================================================
# BOT INITIALIZATION
# ============================================================================

# Create bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="/", intents=intents)

# ============================================================================
# DATABASE SCHEMA
# ============================================================================

async def init_database():
    """Initialize SQLite database"""
    async with aiosqlite.connect("bot_data.db") as db:
        # User verifications
        await db.execute("""
            CREATE TABLE IF NOT EXISTS verifications (
                discord_id TEXT PRIMARY KEY,
                last_verified TIMESTAMP,
                assigned_roles TEXT,
                verification_count INTEGER DEFAULT 0
            )
        """)
        
        # Collection configurations
        await db.execute("""
            CREATE TABLE IF NOT EXISTS collections (
                collection_id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection_name TEXT UNIQUE,
                config TEXT
            )
        """)
        
        # Verification rate limiting
        await db.execute("""
            CREATE TABLE IF NOT EXISTS rate_limits (
                discord_id TEXT,
                timestamp TIMESTAMP,
                PRIMARY KEY (discord_id, timestamp)
            )
        """)
        
        await db.commit()

# ============================================================================
# BSV SIGNATURE VERIFICATION
# ============================================================================

class BSVVerifier:
    """Handles BSV message signature verification"""
    
    @staticmethod
    def verify_signature(message: str, address: str, signature_hex: str) -> bool:
        """
        Verify a BSV signed message
        
        Args:
            message: Original message that was signed
            address: BSV address of signer
            signature_hex: Hex-encoded signature
            
        Returns:
            True if signature is valid
        """
        try:
            # Bitcoin message magic
            magic = b"\x18Bitcoin Signed Message:\n"
            message_bytes = message.encode('utf-8')
            msg_len = len(message_bytes)
            
            # Construct full message
            full_message = magic + bytes([msg_len]) + message_bytes
            
            # Double SHA256 hash
            msg_hash = hashlib.sha256(hashlib.sha256(full_message).digest()).digest()
            
            # Decode signature
            sig_bytes = bytes.fromhex(signature_hex)
            if len(sig_bytes) < 65:
                return False
            
            # Recovery flag
            recovery_flag = sig_bytes[0] - 27
            if recovery_flag < 0 or recovery_flag > 7:
                return False
            
            # Extract r and s
            r = int.from_bytes(sig_bytes[1:33], 'big')
            s = int.from_bytes(sig_bytes[33:65], 'big')
            
            # Recover public key
            for i in range(2):
                try:
                    # Try to recover pubkey
                    x = r
                    if i == 1:
                        x += SECP256k1.generator.order()
                    
                    # Calculate y from x
                    y_squared = (pow(x, 3, SECP256k1.curve.p()) + 7) % SECP256k1.curve.p()
                    y = pow(y_squared, (SECP256k1.curve.p() + 1) // 4, SECP256k1.curve.p())
                    
                    if (recovery_flag & 1) == (y & 1):
                        point = (x, y)
                    else:
                        point = (x, SECP256k1.curve.p() - y)
                    
                    # Create verifying key
                    vk = VerifyingKey.from_public_point(
                        Point(point[0], point[1], SECP256k1.curve),
                        SECP256k1
                    )
                    
                    # Get public key bytes
                    pubkey_bytes = b'\x04' + vk.to_string()
                    
                    # Calculate address
                    sha256_hash = hashlib.sha256(pubkey_bytes).digest()
                    ripemd160_hash = hashlib.new('ripemd160', sha256_hash).digest()
                    
                    # P2PKH address (mainnet = 0x00)
                    derived_address = base58.b58encode_check(b'\x00' + ripemd160_hash).decode()
                    
                    if derived_address == address:
                        return True
                        
                except Exception:
                    continue
            
            return False
            
        except Exception as e:
            print(f"Signature verification error: {e}")
            return False

# Elliptic curve point class
class Point:
    def __init__(self, x, y, curve):
        self.x = x
        self.y = y
        self.curve = curve

# ============================================================================
# 1SAT ORDINALS API
# ============================================================================

class OrdinalsAPI:
    """Handles 1Sat Ordinals API calls"""
    
    @staticmethod
    async def _fetch_json(url: str) -> Optional[Dict]:
        """Fetch JSON from URL using urllib"""
        try:
            loop = asyncio.get_event_loop()
            def blocking_fetch():
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = response.read().decode('utf-8')
                    return json.loads(data)
            
            result = await loop.run_in_executor(None, blocking_fetch)
            return result
        except Exception as e:
            print(f"API fetch error: {e}")
            return None
    
    @staticmethod
    async def get_address_ordinals(address: str, collection_id: str = None) -> List[Dict]:
        """
        Fetch ordinals owned by an address
        
        Args:
            address: BSV address
            collection_id: Optional collection filter
            
        Returns:
            List of ordinal data
        """
        try:
            # Get all inscriptions for address
            url = f"{config.API_BASE}/txos/address/{address}/unspent?limit=1000"
            
            data = await OrdinalsAPI._fetch_json(url)
            if not data:
                return []
            
            ordinals = []
            
            for utxo in data:
                # Check if UTXO has inscription
                if 'origin' in utxo and utxo.get('satoshis') == 1:
                    ordinal_data = await OrdinalsAPI.get_inscription_data(utxo['origin'])
                    if ordinal_data:
                        # Filter by collection if specified
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
        """Get inscription metadata by origin"""
        try:
            url = f"{config.API_BASE}/inscriptions/origin/{origin}"
            return await OrdinalsAPI._fetch_json(url)
        except:
            pass
        return None
    
    @staticmethod
    async def get_collection_items(collection_id: str) -> List[Dict]:
        """Get all items in a collection"""
        try:
            # This would need collection-specific API endpoint
            # For now, return empty - admin will populate manually
            return []
        except:
            return []

# ============================================================================
# RARITY CALCULATOR
# ============================================================================

class RarityCalculator:
    """Calculate ordinal rarity based on scarcity"""
    
    @staticmethod
    async def calculate_rarity(ordinals: List[Dict], collection_config: Dict) -> str:
        """
        Determine highest rarity tier from ordinals
        
        Args:
            ordinals: List of ordinals owned
            collection_config: Collection configuration
            
        Returns:
            Rarity tier name
        """
        if not ordinals:
            return None
        
        # Extract names and count occurrences
        name_counts = {}
        for ordinal in ordinals:
            # Get name from inscription data
            name = ordinal.get('file', {}).get('name') or ordinal.get('map', {}).get('name', 'Unknown')
            
            # Parse name (e.g., "Hummingbow #1" -> "Hummingbow")
            base_name = name.split('#')[0].strip()
            if base_name not in name_counts:
                name_counts[base_name] = 0
            name_counts[base_name] += 1
        
        # Find rarest ordinal (lowest total count)
        # For now, use local counts - in production, query global counts
        min_count = min(name_counts.values())
        
        # Map to rarity tier
        tiers = collection_config.get('rarity_tiers', {})
        for tier, max_count in sorted(tiers.items(), key=lambda x: x[1]):
            if min_count <= max_count:
                return tier
        
        return 'common'

# ============================================================================
# VERIFICATION SESSIONS
# ============================================================================

# Verification sessions
verification_sessions = {}

@bot.event
async def on_ready():
    """Bot startup"""
    await init_database()
    print(f'✅ Bot logged in as {bot.user}')
    print(f'📊 Serving {len(bot.guilds)} servers')
    
    # Sync commands
    try:
        synced = await bot.tree.sync()
        print(f'✅ Synced {len(synced)} commands')
    except Exception as e:
        print(f'❌ Failed to sync commands: {e}')

# ============================================================================
# VERIFICATION COMMANDS
# ============================================================================

@bot.tree.command(name="verify", description="Verify your BSV ordinal ownership")
async def verify(interaction: discord.Interaction):
    """Start verification process"""
    
    # Check rate limit
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
    
    # Generate verification nonce
    nonce = secrets.token_hex(16)
    message = f"Discord_Verify_{int(datetime.now().timestamp())}_{nonce}"
    
    verification_sessions[interaction.user.id] = {
        'nonce': nonce,
        'message': message,
        'timestamp': datetime.now()
    }
    
    # Create a button that opens the wallet signing page
    class VerifyButton(discord.ui.View):
        @discord.ui.button(label="🔐 Sign with Wallet", style=discord.ButtonStyle.primary)
        async def sign_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            # Build the verification URL with message, user ID, and guild ID
            verify_url = f"https://rainbows-bot-224418446129.us-central1.run.app/verify.html?message={message}&user_id={interaction.user.id}&guild_id={interaction.guild_id}"
            
            embed = discord.Embed(
                title="🔗 Opening Wallet Signer",
                description=f"[Click here if it doesn't open automatically]({verify_url})",
                color=discord.Color.blue()
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
    embed = discord.Embed(
        title="🔐 BSV Ordinals Verification",
        description="Click the button to sign a message with your BSV wallet and verify ordinal ownership",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="📱 Supported Wallets",
        value="• Yours Wallet\n• Panda Wallet\n• HandCash",
        inline=False
    )
    
    embed.add_field(
        name="📝 What Happens",
        value="1. Click the button below\n2. Select your wallet\n3. Sign the verification message\n4. Get assigned a role automatically!",
        inline=False
    )
    
    embed.set_footer(text="⏰ This session expires in 10 minutes")
    
    await interaction.response.send_message(embed=embed, view=VerifyButton(), ephemeral=True)

@bot.tree.command(name="submit", description="Submit your signed message")
@app_commands.describe(
    address="Your BSV address",
    signature="Signature from your wallet (hex format)"
)
async def submit(interaction: discord.Interaction, address: str, signature: str):
    """Submit verification signature"""
    
    await interaction.response.defer(ephemeral=True)
    
    # Check if verification session exists
    if interaction.user.id not in verification_sessions:
        await interaction.followup.send(
            "❌ No verification session found. Please run `/verify` first.",
            ephemeral=True
        )
        return
    
    session = verification_sessions[interaction.user.id]
    
    # Check session expiry
    if datetime.now() - session['timestamp'] > timedelta(minutes=10):
        del verification_sessions[interaction.user.id]
        await interaction.followup.send(
            "⏰ Verification session expired. Please run `/verify` again.",
            ephemeral=True
        )
        return
    
    # Verify signature
    if not BSVVerifier.verify_signature(session['message'], address, signature):
        await interaction.followup.send(
            "❌ Invalid signature. Please ensure you signed the correct message.",
            ephemeral=True
        )
        return
    
    # Check ordinal ownership
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
    
    # Calculate rarity
    rarity = await RarityCalculator.calculate_rarity(
        ordinals,
        config.COLLECTIONS["ORDINAL 🌈 RAINBOWS Vol. 1"]
    )
    
    # Assign roles
    guild = bot.get_guild(config.GUILD_ID)
    member = guild.get_member(interaction.user.id)
    
    roles_to_assign = []
    role_config = config.COLLECTIONS["ORDINAL 🌈 RAINBOWS Vol. 1"]["roles"]
    
    # Holder role
    if role_config["holder"]:
        role = guild.get_role(role_config["holder"])
        if role:
            roles_to_assign.append(role)
    
    # Rarity role
    if rarity and role_config.get(rarity):
        role = guild.get_role(role_config[rarity])
        if role:
            roles_to_assign.append(role)
    
    await member.add_roles(*roles_to_assign)
    
    # Save to database
    async with aiosqlite.connect("bot_data.db") as db:
        await db.execute(
            """INSERT OR REPLACE INTO verifications 
               (discord_id, last_verified, assigned_roles, verification_count)
               VALUES (?, ?, ?, COALESCE((SELECT verification_count FROM verifications WHERE discord_id = ?) + 1, 1))""",
            (str(interaction.user.id), datetime.now(), json.dumps([r.id for r in roles_to_assign]), str(interaction.user.id))
        )
        
        # Rate limit tracking
        await db.execute(
            "INSERT INTO rate_limits (discord_id, timestamp) VALUES (?, ?)",
            (str(interaction.user.id), datetime.now())
        )
        
        await db.commit()
    
    # Cleanup session
    del verification_sessions[interaction.user.id]
    
    # Success message
    embed = discord.Embed(
        title="✅ Verification Successful!",
        description=f"You own **{len(ordinals)}** RAINBOW ordinals",
        color=discord.Color.green()
    )
    
    if rarity:
        embed.add_field(name="🏆 Highest Rarity", value=rarity.capitalize(), inline=False)
    
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
    """Check if user has admin role"""
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
    """Set role for collection tier"""
    
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
    """Show bot statistics"""
    
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
# RUN BOT
# ============================================================================

if __name__ == "__main__":
    print("🚀 Starting BSV Ordinals Discord Bot...")
    
    import asyncio
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import threading

    async def process_verification(bot, user_id, guild_id, address):
        """Process verification after signature is verified"""
        try:
            guild = bot.get_guild(guild_id)
            member = guild.get_member(user_id) if guild else None
            
            if not member:
                print(f"❌ Could not find user {user_id} in guild {guild_id}")
                return
            
            # Fetch ordinals for this address
            ordinals = await OrdinalsAPI.get_address_ordinals(
                address,
                config.COLLECTIONS["ORDINAL 🌈 RAINBOWS Vol. 1"]["collection_id"]
            )
            
            if not ordinals:
                print(f"⚠️ No ordinals found for {address}")
                return
            
            # Calculate rarity
            rarity = await RarityCalculator.calculate_rarity(
                ordinals,
                config.COLLECTIONS["ORDINAL 🌈 RAINBOWS Vol. 1"]
            )
            
            # Get role for this rarity tier
            collection = config.COLLECTIONS["ORDINAL 🌈 RAINBOWS Vol. 1"]
            role_id = collection["roles"].get(rarity) if rarity else None
            
            if role_id:
                role = guild.get_role(role_id)
                if role:
                    await member.add_roles(role)
                    print(f"✅ Assigned {rarity} role to {member}")
            
            # Update database
            async with aiosqlite.connect("bot_data.db") as db:
                await db.execute(
                    "INSERT OR REPLACE INTO verifications (discord_id, last_verified, assigned_roles) VALUES (?, ?, ?)",
                    (str(user_id), datetime.now(), rarity or "unverified")
                )
                await db.commit()
                
        except Exception as e:
            print(f"❌ Verification error: {e}")

    class HealthCheckHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            # Extract path without query string
            path = self.path.split('?')[0]
            
            if path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Bot is running')
            elif 'verify.html' in path:
                try:
                    # Try multiple possible paths
                    possible_paths = [
                        'verify.html',
                        '/app/verify.html',
                        os.path.join(os.path.dirname(__file__), 'verify.html')
                    ]
                    
                    html_content = None
                    for filepath in possible_paths:
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                html_content = f.read()
                                print(f"✅ Loaded verify.html from {filepath}")
                                break
                        except Exception as e:
                            print(f"❌ Failed to load {filepath}: {e}")
                            continue
                    
                    if html_content:
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html; charset=utf-8')
                        self.end_headers()
                        self.wfile.write(html_content.encode('utf-8'))
                    else:
                        print("❌ verify.html not found in any path")
                        self.send_response(404)
                        self.send_header('Content-type', 'text/plain')
                        self.end_headers()
                        self.wfile.write(b'verify.html not found')
                except Exception as e:
                    print(f"❌ Error serving verify.html: {e}")
                    self.send_response(500)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(f'Error: {str(e)}'.encode())
            else:
                self.send_response(404)
                self.end_headers()
        
        def do_POST(self):
            if self.path == '/api/verify':
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                
                try:
                    import json
                    data = json.loads(body.decode('utf-8'))
                    
                    # Verify the signature
                    address = data.get('address')
                    signature = data.get('signature')
                    user_id = int(data.get('user_id'))
                    guild_id = int(data.get('guild_id'))
                    message = data.get('message')
                    
                    # Verify BSV signature
                    if not BSVVerifier.verify_signature(message, address, signature):
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({'success': False, 'error': 'Invalid signature'}).encode())
                        return
                    
                    # Schedule verification task
                    asyncio.run_coroutine_threadsafe(
                        process_verification(bot, user_id, guild_id, address),
                        bot.loop
                    )
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'success': True, 'message': 'Verification processing'}).encode())
                    
                except Exception as e:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())
            else:
                self.send_response(404)
                self.end_headers()
        
        def log_message(self, format, *args):
            pass  # Suppress logs

    def run_http_server():
        server = HTTPServer(('0.0.0.0', 8080), HealthCheckHandler)
        server.serve_forever()

    # Start HTTP server in background thread
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()

    # Run Discord bot
    bot.run(config.BOT_TOKEN)
