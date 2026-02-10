"""
Collection Scraper for BSV 1Sat Ordinals
==========================================
Fetches all inscription origins from a collection

Usage:
    python fetch_collection.py <collection_id>
    python fetch_collection.py ee4ae45304c28d0fa6_0
"""

import asyncio
import aiohttp
import json
import sys
from typing import List, Dict

API_BASE = "https://ordinals.gorillapool.io/api"

async def fetch_collection_items(collection_id: str) -> List[Dict]:
    """
    Fetch all items in a collection
    
    Args:
        collection_id: Collection origin ID
        
    Returns:
        List of inscription data
    """
    print(f"🔍 Fetching collection: {collection_id}")
    print(f"📡 API: {API_BASE}")
    
    items = []
    
    try:
        async with aiohttp.ClientSession() as session:
            # Try to get collection data
            # Note: The exact endpoint may vary - adjust based on API
            
            # Method 1: Try collection endpoint
            url = f"{API_BASE}/inscriptions/collection/{collection_id}"
            print(f"\n📥 Trying: {url}")
            
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    items.extend(data if isinstance(data, list) else [data])
                    print(f"✅ Found {len(items)} items via collection endpoint")
                else:
                    print(f"❌ Collection endpoint returned {resp.status}")
            
            # Method 2: Try searching by collection ID in metadata
            if not items:
                print(f"\n📥 Trying search method...")
                url = f"{API_BASE}/inscriptions/search"
                
                # This is a placeholder - actual API may differ
                async with session.post(url, json={
                    "collectionId": collection_id,
                    "limit": 1000
                }) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        items.extend(data.get('inscriptions', []))
                        print(f"✅ Found {len(items)} items via search")
            
            # Method 3: Try getting the collection origin itself
            if not items:
                print(f"\n📥 Fetching collection origin inscription...")
                url = f"{API_BASE}/inscriptions/origin/{collection_id}"
                
                async with session.get(url) as resp:
                    if resp.status == 200:
                        collection_data = await resp.json()
                        print(f"✅ Collection data retrieved")
                        print(json.dumps(collection_data, indent=2)[:500])
                        
                        # Look for child inscriptions or collection members
                        if 'children' in collection_data:
                            items.extend(collection_data['children'])
                        elif 'members' in collection_data:
                            items.extend(collection_data['members'])
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return items

async def analyze_collection(items: List[Dict]):
    """Analyze and display collection statistics"""
    
    if not items:
        print("\n⚠️  No items found!")
        print("\n💡 Alternative Methods:")
        print("1. Check 1sat.market for your collection")
        print("2. Use Zoide.io collection page")
        print("3. Ask collection creator for origin list")
        print("4. Check GorillaPool explorer")
        return
    
    print(f"\n" + "="*60)
    print(f"📊 COLLECTION ANALYSIS")
    print("="*60)
    
    print(f"\n📈 Total Items: {len(items)}")
    
    # Extract origins
    origins = []
    names = {}
    
    for item in items:
        origin = item.get('origin')
        if origin:
            origins.append(origin)
            
            # Try to extract name
            name = (
                item.get('file', {}).get('name') or
                item.get('map', {}).get('name') or
                item.get('text', '').split('\n')[0] or
                'Unknown'
            )
            
            base_name = name.split('#')[0].strip()
            if base_name not in names:
                names[base_name] = 0
            names[base_name] += 1
    
    print(f"✅ Origins Found: {len(origins)}")
    
    # Name distribution
    if names:
        print(f"\n🎨 Name Distribution:")
        sorted_names = sorted(names.items(), key=lambda x: x[1])
        for name, count in sorted_names[:10]:
            rarity = "🏆 Legendary" if count <= 2 else "⭐ Epic" if count <= 5 else "💎 Rare" if count <= 10 else "🔵 Common"
            print(f"  {rarity} {name}: {count}")
        
        if len(sorted_names) > 10:
            print(f"  ... and {len(sorted_names) - 10} more")
    
    # Save to file
    output = {
        "collection_id": sys.argv[1] if len(sys.argv) > 1 else "unknown",
        "total_items": len(items),
        "origins": origins,
        "name_distribution": names,
        "sample_items": items[:5]  # First 5 items as examples
    }
    
    filename = "collection_data.json"
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 Saved to: {filename}")
    
    # Generate config snippet
    print(f"\n" + "="*60)
    print("📝 CONFIG SNIPPET FOR BOT.PY:")
    print("="*60)
    print(f"""
config.COLLECTIONS["ORDINAL 🌈 RAINBOWS Vol. 1"] = {{
    "collection_id": "{output['collection_id']}",
    "origins": {json.dumps(origins[:5], indent=8)},  # First 5 shown
    "roles": {{
        "holder": None,
        "legendary": None,
        "epic": None,
        "rare": None
    }},
    "rarity_tiers": {{
        "legendary": 2,
        "epic": 5,
        "rare": 10,
        "common": 999
    }}
}}
""")

async def main():
    if len(sys.argv) < 2:
        print("❌ Usage: python fetch_collection.py <collection_id>")
        print("\n📋 Example:")
        print("   python fetch_collection.py ee4ae45304c28d0fa6_0")
        print("\n💡 To find your collection ID:")
        print("   1. Go to 1sat.market or zoide.io")
        print("   2. Find your collection page")
        print("   3. Look for 'collectionId' or 'origin' in URL or metadata")
        sys.exit(1)
    
    collection_id = sys.argv[1]
    
    print("="*60)
    print("🌈 BSV ORDINALS COLLECTION SCRAPER")
    print("="*60)
    
    items = await fetch_collection_items(collection_id)
    await analyze_collection(items)
    
    print("\n" + "="*60)
    print("✅ COMPLETE")
    print("="*60)
    
    if not items:
        print("\n🔧 MANUAL METHOD:")
        print("="*60)
        print("""
If automated fetch failed, you can manually populate:

1. Visit your collection on 1sat.market or zoide.io
2. Open browser DevTools (F12)
3. Look for API calls containing inscription data
4. Copy the 'origin' values
5. Add them to bot.py config manually:

config.COLLECTIONS["Your Collection"]["origins"] = [
    "origin_1_abc123_0",
    "origin_2_def456_0",
    # ... etc
]
""")

if __name__ == "__main__":
    asyncio.run(main())