#!/usr/bin/env python3
"""
Scrape Pandora product images and replace 16x16 placeholders
"""
import json
import os
import re
import time
import urllib.request
from pathlib import Path
from typing import Dict, List

# Paths
PROJECT_ROOT = Path(__file__).parent
JSON_FILE = PROJECT_ROOT / "public/brands/pandora.json"
IMAGE_DIR = PROJECT_ROOT / "public/images/pandora"

# Categories to scrape - map to URL paths
CATEGORIES = {
    "Charms": ["charms", "dangle-charms"],
    "Bracelets": ["bracelets", "charm-bracelets", "bangles"],
    "Rings": ["rings", "statement-rings", "promise-rings"],
    "Necklaces": ["necklaces", "pendants"],
    "Earrings": ["earrings", "stud-earrings", "hoop-earrings"],
}

def load_products():
    """Load products from JSON"""
    with open(JSON_FILE, 'r') as f:
        return json.load(f)

def extract_sku_from_name(name: str) -> str:
    """Try to extract SKU-like pattern from product name"""
    # Pandora SKUs are usually like: 794461C01, 764369C01, etc.
    # Pattern: 6-7 digits + letter + 2 digits
    match = re.search(r'(\d{6,7}[A-Z]\d{2})', name.upper())
    return match.group(1) if match else None

def construct_cdn_url(sku: str, size: str = "600") -> str:
    """Construct Pandora CDN URL from SKU"""
    if not sku:
        return None
    
    # Format: https://us.pandora.net/dw/image/v2/AAVX_PRD/on/demandware.static/-/Sites-pandora-master-catalog/default/{hash}/productimages/singlepackshot/{SKU}_RGB.jpg?sw=600&sh=600
    # We don't have the hash, so we'll try common patterns
    return f"https://us.pandora.net/dw/image/v2/AAVX_PRD/on/demandware.static/-/Sites-pandora-master-catalog/default/dw{sku[:2]}/{sku}_RGB.jpg?sw={size}&sh={size}"

def download_image(url: str, filepath: Path, retries: int = 3) -> bool:
    """Download image from URL to filepath"""
    for attempt in range(retries):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Referer': 'https://us.pandora.net/'
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    data = response.read()
                    # Check if it's a valid image (not 16x16 placeholder)
                    if len(data) > 1000:  # 16x16 placeholders are ~869 bytes
                        with open(filepath, 'wb') as f:
                            f.write(data)
                        return True
            time.sleep(0.5)
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            time.sleep(1)
    return False

def main():
    print("Loading products...")
    products = load_products()
    print(f"Found {len(products)} products")
    
    # Create output directory
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    
    successful = 0
    failed = []
    
    for idx, product in enumerate(products, 1):
        name = product.get('n', '')
        image_path = product.get('i', '')
        
        if not image_path:
            continue
            
        # Full filesystem path
        full_path = PROJECT_ROOT / image_path.lstrip('/')
        
        # Check if it's a placeholder (869 bytes, 16x16)
        if full_path.exists():
            size = full_path.stat().st_size
            if size > 1000:  # Already has real image
                if idx % 100 == 0:
                    print(f"Progress: {idx}/{len(products)} - Already has image")
                continue
        
        # Try to construct CDN URL
        sku = extract_sku_from_name(name)
        if not sku:
            # Try common Pandora URL patterns
            # We'll need to search for the product
            print(f"[{idx}/{len(products)}] No SKU found for: {name}")
            failed.append(name)
            continue
        
        cdn_url = construct_cdn_url(sku)
        print(f"[{idx}/{len(products)}] Downloading: {name}")
        print(f"  SKU: {sku}")
        print(f"  URL: {cdn_url}")
        
        if download_image(cdn_url, full_path):
            successful += 1
            print(f"  ✓ Downloaded successfully")
        else:
            failed.append(name)
            print(f"  ✗ Failed to download")
        
        # Rate limiting
        time.sleep(0.5)
        
        # Progress update every 50 products
        if idx % 50 == 0:
            print(f"\n=== Progress: {idx}/{len(products)} | Success: {successful} | Failed: {len(failed)} ===\n")
    
    print(f"\n{'='*60}")
    print(f"FINAL RESULTS:")
    print(f"  Total products: {len(products)}")
    print(f"  Successfully downloaded: {successful}")
    print(f"  Failed: {len(failed)}")
    print(f"{'='*60}")
    
    if failed:
        print("\nFailed products:")
        for name in failed[:20]:  # Show first 20
            print(f"  - {name}")
        if len(failed) > 20:
            print(f"  ... and {len(failed) - 20} more")

if __name__ == "__main__":
    main()
