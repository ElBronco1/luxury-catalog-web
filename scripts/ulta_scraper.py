#!/usr/bin/env python3
"""
Ulta image scraper using their internal search/catalog system.
Uses the Ulta website's internal product search to find product images.
"""
import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from difflib import SequenceMatcher

BASE_DIR = Path('/Users/maurocastellanos/clawd/projects/luxury-catalog-web')
BRANDS_DIR = BASE_DIR / 'public' / 'brands'
IMAGES_DIR = BASE_DIR / 'public' / 'images'
CACHE_FILE = BASE_DIR / 'scripts' / 'ulta_product_cache.json'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
}


def slugify(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')[:80]


def download_image(url, filepath):
    """Download image, return True if successful."""
    if os.path.exists(filepath) and os.path.getsize(filepath) > 5000:
        return True
    
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            if len(data) < 1000:
                return False
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(data)
            return True
    except Exception as e:
        return False


def normalize_name(name):
    """Normalize product name for matching."""
    name = name.lower()
    name = re.sub(r'\s+', ' ', name)
    name = re.sub(r'[^\w\s]', '', name)
    return name.strip()


def similarity(a, b):
    """Calculate similarity ratio between two strings."""
    return SequenceMatcher(None, normalize_name(a), normalize_name(b)).ratio()


def main():
    """Main entry: download Ulta images from the cached product mapping."""
    brand_slug = 'ulta'
    
    # Load brand JSON
    with open(BRANDS_DIR / f'{brand_slug}.json') as f:
        products = json.load(f)
    
    print(f"Total Ulta products: {len(products)}")
    need_images = [i for i, p in enumerate(products) if not p.get('i')]
    print(f"Products needing images: {len(need_images)}")
    
    # Load cached product mappings (name -> image URL)
    if CACHE_FILE.exists():
        with open(CACHE_FILE) as f:
            cache = json.load(f)
        print(f"Loaded {len(cache)} cached product mappings")
    else:
        print("No cache file found. Run browser scraping first to build the cache.")
        cache = {}
    
    if not cache:
        print("Cache is empty. Exiting.")
        return
    
    img_dir = IMAGES_DIR / brand_slug
    os.makedirs(img_dir, exist_ok=True)
    
    downloaded = 0
    matched = 0
    failed = 0
    skipped = 0
    
    # Match products to cached images
    cache_names = list(cache.keys())
    cache_normalized = {normalize_name(k): k for k in cache_names}
    
    for idx in need_images:
        product = products[idx]
        name = product['n']
        norm_name = normalize_name(name)
        
        # Try exact match first
        img_url = None
        if norm_name in cache_normalized:
            img_url = cache[cache_normalized[norm_name]]
        else:
            # Try fuzzy match
            best_score = 0
            best_key = None
            for cache_norm, cache_orig in cache_normalized.items():
                score = similarity(norm_name, cache_norm)
                if score > best_score:
                    best_score = score
                    best_key = cache_orig
            
            if best_score > 0.75:
                img_url = cache[best_key]
                matched += 1
        
        if not img_url:
            skipped += 1
            continue
        
        # Download image
        slug = slugify(name)
        filename = f"{idx+1}-{slug}.jpg"
        filepath = str(img_dir / filename)
        
        if download_image(img_url, filepath):
            products[idx]['i'] = f"/images/{brand_slug}/{filename}"
            downloaded += 1
        else:
            failed += 1
        
        # Save progress every 100
        if (downloaded + failed) % 100 == 0:
            with open(BRANDS_DIR / f'{brand_slug}.json', 'w') as f:
                json.dump(products, f, indent=2)
            print(f"Progress: {downloaded} downloaded, {matched} fuzzy matched, {failed} failed, {skipped} skipped")
    
    # Final save
    with open(BRANDS_DIR / f'{brand_slug}.json', 'w') as f:
        json.dump(products, f, indent=2)
    
    print(f"\nFinal: {downloaded} downloaded, {matched} fuzzy, {failed} failed, {skipped} no match")


if __name__ == '__main__':
    main()
