#!/usr/bin/env python3
"""
Mega scraper: Given a browser-extracted cache, match products and download images.
Works for any brand using name -> image URL mapping.

Usage:
  python3 mega_scraper.py <brand-slug> [--dry-run]
  
Before running, populate scripts/{brand-slug}_cache.json with:
  { "Product Full Name": "https://cdn.example.com/image.jpg", ... }
"""
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from difflib import SequenceMatcher

BASE_DIR = Path('/Users/maurocastellanos/clawd/projects/luxury-catalog-web')
BRANDS_DIR = BASE_DIR / 'public' / 'brands'
IMAGES_DIR = BASE_DIR / 'public' / 'images'
SCRIPTS_DIR = BASE_DIR / 'scripts'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
}


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')[:80]


def normalize(s):
    """Normalize for comparison."""
    s = s.lower().strip()
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'[^\w\s]', '', s)
    return s


def download_image(url, filepath):
    """Download image, return True on success."""
    if os.path.exists(filepath) and os.path.getsize(filepath) > 3000:
        return True
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
            if len(data) < 1000:
                return False
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(data)
            return True
    except Exception:
        return False


def find_best_match(product_name, cache_normalized, threshold=0.55):
    """Find best matching cache entry for a product name."""
    norm = normalize(product_name)
    
    # Exact match
    if norm in cache_normalized:
        return cache_normalized[norm], 1.0
    
    # Check if product name is contained in any cache entry or vice versa
    for cn, url in cache_normalized.items():
        if norm in cn or cn in norm:
            return url, 0.9
    
    # Check individual important words
    # For products like "Do It All Sheer Tint Face Balm", 
    # the cache might have "IT Cosmetics Do It All Sheer Tint Face Balm"
    # So check if all significant words of our product appear in a cache entry
    product_words = set(norm.split()) - {'the', 'a', 'an', 'with', 'for', 'and', 'in', 'of', 'by'}
    if len(product_words) >= 3:
        best_overlap = 0
        best_url = None
        for cn, url in cache_normalized.items():
            cache_words = set(cn.split())
            overlap = len(product_words & cache_words) / len(product_words)
            if overlap > best_overlap:
                best_overlap = overlap
                best_url = url
        if best_overlap > 0.7:
            return best_url, best_overlap
    
    # Fuzzy match as last resort
    best = 0
    best_url = None
    for cn, url in cache_normalized.items():
        # Quick length filter
        if abs(len(cn) - len(norm)) > max(len(norm), len(cn)) * 0.5:
            continue
        r = SequenceMatcher(None, norm, cn).ratio()
        if r > best:
            best = r
            best_url = url
    
    if best >= threshold:
        return best_url, best
    
    return None, 0


def process_brand(brand_slug, dry_run=False):
    """Process a brand using its cache file."""
    cache_file = SCRIPTS_DIR / f'{brand_slug}_cache.json'
    brand_file = BRANDS_DIR / f'{brand_slug}.json'
    
    if not cache_file.exists():
        print(f"No cache file: {cache_file}")
        return
    
    with open(cache_file) as f:
        cache = json.load(f)
    
    with open(brand_file) as f:
        products = json.load(f)
    
    # Build normalized cache
    cache_normalized = {}
    for name, url in cache.items():
        n = normalize(name)
        cache_normalized[n] = url
    
    total = len(products)
    need = [(i, p) for i, p in enumerate(products) if not p.get('i')]
    
    print(f"\n{'='*60}")
    print(f"Brand: {brand_slug}")
    print(f"Total products: {total}")
    print(f"Need images: {len(need)}")
    print(f"Cache entries: {len(cache)}")
    print(f"{'='*60}\n")
    
    img_dir = IMAGES_DIR / brand_slug
    os.makedirs(img_dir, exist_ok=True)
    
    matched = 0
    downloaded = 0
    failed = 0
    unmatched = 0
    
    for idx, prod in need:
        name = prod['n']
        url, score = find_best_match(name, cache_normalized)
        
        if url is None:
            unmatched += 1
            if unmatched <= 10:
                print(f"  NO MATCH: {name[:70]}")
            continue
        
        matched += 1
        
        if dry_run:
            if matched <= 5:
                print(f"  MATCH [{score:.2f}]: {name[:50]} -> {url[-30:]}")
            continue
        
        slug = slugify(name)
        filename = f"{idx+1}-{slug}.jpg"
        filepath = str(img_dir / filename)
        
        if download_image(url, filepath):
            products[idx]['i'] = f"/images/{brand_slug}/{filename}"
            downloaded += 1
        else:
            failed += 1
        
        # Save + report progress
        if (downloaded + failed) % 100 == 0 and (downloaded + failed) > 0:
            with open(brand_file, 'w') as f:
                json.dump(products, f)
            print(f"  Progress: {downloaded + failed}/{matched} (ok={downloaded}, fail={failed})")
        
        # Small delay to not hammer CDN
        if (downloaded + failed) % 10 == 0:
            time.sleep(0.1)
    
    # Final save
    if not dry_run:
        with open(brand_file, 'w') as f:
            json.dump(products, f)
    
    print(f"\nResults for {brand_slug}:")
    print(f"  Matched: {matched}/{len(need)}")
    print(f"  Downloaded: {downloaded}")
    print(f"  Failed: {failed}")
    print(f"  Unmatched: {unmatched}")
    
    return downloaded


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 mega_scraper.py <brand-slug> [--dry-run]")
        sys.exit(1)
    
    brand = sys.argv[1]
    dry_run = '--dry-run' in sys.argv
    process_brand(brand, dry_run)
