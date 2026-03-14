#!/usr/bin/env python3
"""
Master scraper for all luxury catalog brands.
Downloads product images using brand CDN patterns.
Designed to be run in stages - saves progress frequently.
"""
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = Path('/Users/maurocastellanos/clawd/projects/luxury-catalog-web')
BRANDS_DIR = BASE_DIR / 'public' / 'brands'
IMAGES_DIR = BASE_DIR / 'public' / 'images'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')[:80]


def download_image(url, filepath, extra_headers=None):
    """Download image. Returns True on success."""
    if os.path.exists(filepath) and os.path.getsize(filepath) > 3000:
        return True
    
    hdrs = dict(HEADERS)
    if extra_headers:
        hdrs.update(extra_headers)
    
    try:
        req = urllib.request.Request(url, headers=hdrs)
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
            if len(data) < 1000:
                return False
            if len(data) > 25 * 1024 * 1024:  # 25MB limit
                return False
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(data)
            return True
    except Exception:
        return False


def load_json(brand_slug):
    with open(BRANDS_DIR / f'{brand_slug}.json') as f:
        return json.load(f)


def save_json(brand_slug, data):
    with open(BRANDS_DIR / f'{brand_slug}.json', 'w') as f:
        json.dump(data, f)


def download_batch(items, brand_slug, products, save_every=50):
    """Download a batch of (index, url) tuples."""
    img_dir = IMAGES_DIR / brand_slug
    os.makedirs(img_dir, exist_ok=True)
    
    ok = 0
    fail = 0
    
    for idx, url in items:
        name = products[idx]['n']
        slug = slugify(name)
        filename = f"{idx+1}-{slug}.jpg"
        filepath = str(img_dir / filename)
        
        if download_image(url, filepath):
            products[idx]['i'] = f"/images/{brand_slug}/{filename}"
            ok += 1
        else:
            fail += 1
        
        if (ok + fail) % save_every == 0 and (ok + fail) > 0:
            save_json(brand_slug, products)
            print(f"  [{brand_slug}] {ok + fail}/{len(items)} done ({ok} ok, {fail} fail)")
    
    save_json(brand_slug, products)
    return ok, fail


def process_with_cache(brand_slug, cache):
    """Process brand using a pre-built name->URL cache with fuzzy matching."""
    from difflib import SequenceMatcher
    
    products = load_json(brand_slug)
    need = [(i, p) for i, p in enumerate(products) if not p.get('i')]
    print(f"\n{'='*60}")
    print(f"Processing {brand_slug}: {len(products)} total, {len(need)} need images")
    print(f"Cache has {len(cache)} entries")
    
    if not need or not cache:
        return 0, 0
    
    def normalize(s):
        return re.sub(r'[^\w\s]', '', s.lower()).strip()
    
    cache_norm = {normalize(k): v for k, v in cache.items()}
    
    items = []
    for idx, prod in need:
        name = prod['n']
        norm = normalize(name)
        
        # Exact match
        if norm in cache_norm:
            items.append((idx, cache_norm[norm]))
            continue
        
        # Fuzzy match
        best = 0
        best_url = None
        for cn, url in cache_norm.items():
            r = SequenceMatcher(None, norm, cn).ratio()
            if r > best:
                best = r
                best_url = url
        
        if best > 0.70:
            items.append((idx, best_url))
    
    print(f"  Matched {len(items)}/{len(need)} products")
    
    if items:
        ok, fail = download_batch(items, brand_slug, products)
        print(f"  Downloaded: {ok}, Failed: {fail}")
        return ok, fail
    
    return 0, 0


if __name__ == '__main__':
    brand = sys.argv[1] if len(sys.argv) > 1 else 'test'
    
    if brand == 'test':
        # Quick test: try downloading one Ulta image
        url = 'https://media.ultainc.com/i/ulta/2651984?w=600&h=600&fmt=auto'
        test_path = '/tmp/ulta_test.jpg'
        if download_image(url, test_path):
            size = os.path.getsize(test_path)
            print(f"Test download OK: {size} bytes")
        else:
            print("Test download FAILED")
