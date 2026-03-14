#!/usr/bin/env python3
"""
Scrape product images for luxury catalog brands.
Strategy: Use brand CDN patterns + web scraping to find and download product images.
"""

import json
import os
import re
import sys
import time
import hashlib
import urllib.request
import urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = Path('/Users/maurocastellanos/clawd/projects/luxury-catalog-web')
BRANDS_DIR = BASE_DIR / 'public' / 'brands'
IMAGES_DIR = BASE_DIR / 'public' / 'images'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.google.com/',
}


def slugify(text):
    """Convert text to URL-friendly slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')[:80]


def download_image(url, filepath, headers=None):
    """Download an image from URL to filepath."""
    if os.path.exists(filepath) and os.path.getsize(filepath) > 5000:
        return True  # Already downloaded
    
    hdrs = dict(HEADERS)
    if headers:
        hdrs.update(headers)
    
    try:
        req = urllib.request.Request(url, headers=hdrs)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            if len(data) < 1000:  # Too small, likely an error page
                return False
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(data)
            return True
    except Exception as e:
        return False


def load_brand_json(brand_slug):
    """Load brand JSON file."""
    filepath = BRANDS_DIR / f'{brand_slug}.json'
    with open(filepath) as f:
        return json.load(f)


def save_brand_json(brand_slug, data):
    """Save brand JSON file."""
    filepath = BRANDS_DIR / f'{brand_slug}.json'
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def process_ulta():
    """Process Ulta products using media.ultainc.com CDN."""
    brand_slug = 'ulta'
    data = load_brand_json(brand_slug)
    img_dir = IMAGES_DIR / brand_slug
    os.makedirs(img_dir, exist_ok=True)
    
    print(f"Processing Ulta: {len(data)} products")
    
    # For Ulta, we can't easily map product names to SKUs without their search API
    # Instead, we'll try to find images via Google-style CDN search
    # Ulta CDN: https://media.ultainc.com/i/ulta/{SKU}?w=600&h=600&fmt=auto
    
    # We need SKU numbers. Let's try scraping categories...
    # For now, return count of products needing images
    need_images = sum(1 for p in data if not p.get('i'))
    print(f"  {need_images} products need images")
    return need_images


def process_brand_with_cdn(brand_slug, cdn_pattern_fn, search_url_fn=None):
    """Generic processor for brands with known CDN patterns."""
    data = load_brand_json(brand_slug)
    img_dir = IMAGES_DIR / brand_slug
    os.makedirs(img_dir, exist_ok=True)
    
    total = len(data)
    need_images = sum(1 for p in data if not p.get('i'))
    print(f"Processing {brand_slug}: {total} products, {need_images} need images")
    
    downloaded = 0
    failed = 0
    
    for i, product in enumerate(data):
        if product.get('i'):
            continue
        
        name = product['n']
        slug = slugify(name)
        filename = f"{i+1}-{slug}.jpg"
        filepath = str(img_dir / filename)
        
        # Try CDN pattern
        url = cdn_pattern_fn(name, i)
        if url and download_image(url, filepath):
            product['i'] = f"/images/{brand_slug}/{filename}"
            downloaded += 1
        else:
            failed += 1
        
        # Save progress every 50 products
        if (i + 1) % 50 == 0:
            save_brand_json(brand_slug, data)
            print(f"  Progress: {i+1}/{total} ({downloaded} downloaded, {failed} failed)")
    
    save_brand_json(brand_slug, data)
    print(f"  Final: {downloaded} downloaded, {failed} failed")
    return downloaded


if __name__ == '__main__':
    brand = sys.argv[1] if len(sys.argv) > 1 else 'all'
    
    if brand == 'ulta' or brand == 'all':
        process_ulta()
