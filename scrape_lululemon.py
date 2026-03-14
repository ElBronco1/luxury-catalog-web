#!/usr/bin/env python3
"""
Lululemon image scraper for 1,365 products.
Uses Google Image Search to find product images.
"""

import json
import os
import re
import time
import requests
from urllib.parse import quote_plus
from pathlib import Path

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

def google_image_search(product_name, retries=3):
    """
    Search Google Images for Lululemon product.
    Returns first image URL from lululemon.com domain if possible.
    """
    query = f"lululemon {product_name}"
    search_url = f"https://www.google.com/search?q={quote_plus(query)}&tbm=isch"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    for attempt in range(retries):
        try:
            resp = requests.get(search_url, headers=headers, timeout=10)
            resp.raise_for_status()
            
            # Extract image URLs from Google Images response
            # Look for images.lululemon.com URLs
            lulu_pattern = r'https://images\.lululemon\.com[^"\'<>\s]+'
            matches = re.findall(lulu_pattern, resp.text)
            
            if matches:
                return matches[0]
            
            # Fallback: any image URL
            img_pattern = r'https://[^"\'<>\s]+\.(jpg|jpeg|png|webp)'
            fallback = re.findall(img_pattern, resp.text)
            if fallback:
                return fallback[0]
                
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2)
    
    return None

def download_image(url, filepath, retries=3):
    """Download image from URL to filepath"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=headers, timeout=15, stream=True)
            resp.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
        except Exception as e:
            print(f"  Download attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2)
    
    return False

def main():
    # Load JSON
    print(f"Loading {JSON_FILE}...")
    with open(JSON_FILE, 'r') as f:
        products = json.load(f)
    
    total = len(products)
    print(f"Found {total} products to process\n")
    
    success_count = 0
    failed_products = []
    
    for idx, product in enumerate(products, 1):
        name = product.get('n', '')
        
        # Skip if already has image
        if product.get('i'):
            print(f"[{idx}/{total}] SKIP: {name[:50]} (already has image)")
            continue
        
        print(f"[{idx}/{total}] Processing: {name[:60]}")
        
        # Generate filename
        slug = slugify(name)
        filename = f"{idx}-{slug}.jpg"
        filepath = IMG_DIR / filename
        
        # Search for image
        print(f"  Searching Google Images...")
        image_url = google_image_search(name)
        
        if not image_url:
            print(f"  ❌ No image found")
            failed_products.append((idx, name))
            continue
        
        print(f"  Found: {image_url[:80]}")
        
        # Download image
        print(f"  Downloading to {filename}...")
        if download_image(image_url, filepath):
            # Update JSON
            product['i'] = f"/images/lululemon/{filename}"
            success_count += 1
            print(f"  ✅ Success ({success_count}/{total})")
            
            # Save JSON periodically (every 10 products)
            if idx % 10 == 0:
                print(f"\n  💾 Saving progress...")
                with open(JSON_FILE, 'w') as f:
                    json.dump(products, f, indent=2)
        else:
            print(f"  ❌ Download failed")
            failed_products.append((idx, name))
        
        # Rate limiting
        time.sleep(1.5)
    
    # Final save
    print(f"\n💾 Saving final results...")
    with open(JSON_FILE, 'w') as f:
        json.dump(products, f, indent=2)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"COMPLETE")
    print(f"{'='*60}")
    print(f"Total products: {total}")
    print(f"Successfully scraped: {success_count}")
    print(f"Failed: {len(failed_products)}")
    
    if failed_products:
        print(f"\nFailed products:")
        for idx, name in failed_products[:20]:  # Show first 20
            print(f"  [{idx}] {name[:60]}")

if __name__ == "__main__":
    main()
