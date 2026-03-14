#!/usr/bin/env python3
"""
Lululemon image scraper - uses browser via OpenClaw to extract images
Then downloads them with curl.
"""

import json
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import quote_plus

# Paths
JSON_FILE = Path(__file__).parent / "public/brands/lululemon.json"
IMG_DIR = Path(__file__).parent / "public/images/lululemon"
IMG_DIR.mkdir(parents=True, exist_ok=True)

def slugify(text):
    """Convert product name to slug for filename"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

def download_with_curl(url, filepath):
    """Download image using curl"""
    try:
        cmd = [
            'curl', '-s', '-L', '-o', str(filepath),
            '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            url
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        
        # Check if file was created and has content
        if filepath.exists() and filepath.stat().st_size > 1000:
            return True
        return False
    except Exception as e:
        print(f"  Download error: {e}")
        return False

def construct_lululemon_image_url(product_name):
    """
    Attempt to construct a Lululemon CDN image URL.
    Format: https://images.lululemon.com/is/image/lululemon/[PRODUCT_CODE]
    
    This is a fallback strategy - we'll try common patterns.
    """
    # Remove special characters and create potential product code
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', product_name)
    
    # Common Lululemon image URL patterns
    patterns = [
        f"https://images.lululemon.com/is/image/lululemon/{clean_name}",
        f"https://images.lululemon.com/is/image/lululemon/{clean_name.lower()}",
    ]
    
    return patterns

def main():
    # Load JSON
    print(f"Loading {JSON_FILE}...")
    with open(JSON_FILE, 'r') as f:
        products = json.load(f)
    
    total = len(products)
    print(f"Found {total} products\n")
    print("⚠️  This script will attempt to construct Lululemon image URLs")
    print("⚠️  Success rate will be low without browser automation\n")
    
    # For demo, process first 20 products
    sample_size = 20
    print(f"Processing first {sample_size} products as test...\n")
    
    success_count = 0
    failed = []
    
    for idx in range(min(sample_size, total)):
        product = products[idx]
        name = product.get('n', '')
        
        if product.get('i'):
            print(f"[{idx+1}] SKIP: {name[:50]} (has image)")
            continue
        
        print(f"[{idx+1}] {name[:60]}")
        
        # Generate filename
        slug = slugify(name)
        filename = f"{idx+1}-{slug}.jpg"
        filepath = IMG_DIR / filename
        
        # Try constructed URLs
        attempted_urls = construct_lululemon_image_url(name)
        
        downloaded = False
        for url in attempted_urls:
            print(f"  Trying: {url[:70]}...")
            if download_with_curl(url, filepath):
                product['i'] = f"/images/lululemon/{filename}"
                success_count += 1
                print(f"  ✅ Success!")
                downloaded = True
                break
        
        if not downloaded:
            print(f"  ❌ Failed")
            failed.append((idx+1, name))
    
    # Save progress
    with open(JSON_FILE, 'w') as f:
        json.dump(products, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Test run complete:")
    print(f"Attempted: {sample_size}")
    print(f"Success: {success_count}")
    print(f"Failed: {len(failed)}")
    print(f"{'='*60}")
    
    if success_count == 0:
        print("\n⚠️  This approach has low success rate.")
        print("✅ Better strategy: Use browser automation to scrape from lululemon.com")
        print("\nNext steps:")
        print("1. Navigate to lululemon.com with browser tool")
        print("2. Extract product image URLs from the page")
        print("3. Match to JSON products by name")
        print("4. Download images with curl")

if __name__ == "__main__":
    main()
