#!/usr/bin/env python3
"""
Scrape Michael Kors product images using DuckDuckGo Image Search.
No API key required, more lenient than Google.
"""

import json
import os
import re
import time
import requests
from pathlib import Path
from ddgs import DDGS

# Paths
JSON_FILE = Path("public/brands/michael-kors.json")
OUTPUT_DIR = Path("public/images/michael-kors")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load products
with open(JSON_FILE, 'r') as f:
    products = json.load(f)

print(f"📦 Loaded {len(products)} Michael Kors products\n")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
}

def clean_name(name):
    """Clean product name"""
    return name.strip().strip('-').strip()

def search_product_image(product_name, category):
    """Search for product image using DuckDuckGo"""
    query = f"Michael Kors {product_name} {category} product"
    
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(
                query=query,
                max_results=5
            ))
            
            # Filter for reasonable image sizes (prefer larger images)
            valid_results = []
            for r in results:
                # DDG returns images with 'image' and 'thumbnail' URLs
                if r.get('image') and not r.get('image', '').endswith('.svg'):
                    valid_results.append(r)
            
            return valid_results
    
    except Exception as e:
        print(f"  ⚠️  Search error: {e}")
        return []

def download_image(url, output_path, max_size_mb=10):
    """Download image from URL"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=20, stream=True)
        if response.status_code == 200:
            # Check content type
            content_type = response.headers.get('content-type', '')
            if 'image' not in content_type:
                print(f"  ⚠️  Not an image: {content_type}")
                return False
            
            # Download with size limit
            size = 0
            max_bytes = max_size_mb * 1024 * 1024
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(8192):
                    size += len(chunk)
                    if size > max_bytes:
                        print(f"  ⚠️  Image too large (>{max_size_mb}MB)")
                        return False
                    f.write(chunk)
            
            # Check final size
            file_size_kb = output_path.stat().st_size / 1024
            if file_size_kb < 5:
                print(f"  ⚠️  Too small ({file_size_kb:.1f}KB)")
                output_path.unlink()
                return False
            
            return True
        else:
            print(f"  ⚠️  HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ Download error: {str(e)[:60]}")
        if output_path.exists():
            output_path.unlink()
        return False

# Stats
success = 0
failed = 0
skipped = 0

# Process products
for idx, product in enumerate(products, 1):
    name = clean_name(product['n'])
    category = product['c']
    output_filename = Path(product['i']).name
    output_path = OUTPUT_DIR / output_filename
    
    # Skip if already exists and is good size
    if output_path.exists():
        size_kb = output_path.stat().st_size / 1024
        if size_kb > 30:
            skipped += 1
            if idx % 100 == 0:
                print(f"[{idx}/{len(products)}] ⏭️  Already good: {name[:50]}")
            continue
    
    print(f"\n[{idx}/{len(products)}] 🔍 {name[:60]}")
    
    # Search for images
    results = search_product_image(name, category)
    
    if not results:
        print(f"  ❌ No results")
        failed += 1
        continue
    
    # Try each result
    downloaded = False
    for i, result in enumerate(results, 1):
        img_url = result.get('image')
        if not img_url:
            continue
        
        print(f"  📥 [{i}/{len(results)}] Trying {img_url[:70]}...")
        
        if download_image(img_url, output_path):
            size_kb = output_path.stat().st_size / 1024
            print(f"  ✅ Success! {size_kb:.1f}KB")
            success += 1
            downloaded = True
            break
    
    if not downloaded:
        failed += 1
        print(f"  ❌ All attempts failed")
    
    # Rate limiting
    time.sleep(1.5)
    
    # Progress checkpoints
    if idx % 50 == 0:
        print(f"\n{'='*60}")
        print(f"📊 PROGRESS: {success} ✅  {failed} ❌  {skipped} ⏭️")
        print(f"{'='*60}\n")
    
    # Periodic save checkpoint
    if idx % 100 == 0:
        print(f"\n💾 Checkpoint: Processed {idx}/{len(products)} products\n")

# Final report
print(f"\n{'='*70}")
print(f"🏁 FINAL RESULTS:")
print(f"  ✅ Downloaded:     {success:4d}")
print(f"  ❌ Failed:         {failed:4d}")
print(f"  ⏭️  Already Existed: {skipped:4d}")
print(f"  📊 Total Products: {len(products):4d}")
print(f"  📁 Output: {OUTPUT_DIR}")
print(f"{'='*70}")
